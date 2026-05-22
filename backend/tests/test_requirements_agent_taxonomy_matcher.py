from copy import deepcopy
from pathlib import Path

from backend.agents.requirements_agent.modules.taxonomy_matcher import (
    load_json,
    match_requirements,
)

ROOT = Path("backend/agents/requirements_agent")


def _references():
    return (
        load_json(ROOT / "references/taxonomy.json"),
        load_json(ROOT / "references/rulebase.json"),
    )


def _candidate(
    candidate_id: str,
    item_type: str,
    text: str,
    *,
    confidence: float = 0.92,
    status: str = "candidate",
):
    return {
        "candidate_id": candidate_id,
        "item_type": item_type,
        "text": text,
        "normalized_text": text.casefold(),
        "source_evidence": [
            {
                "evidence_id": f"{candidate_id}_ev_001",
                "document_id": "prd_taxonomy",
                "section_id": "sec_001",
                "text": text,
            }
        ],
        "confidence": confidence,
        "status": status,
    }


def _draft(candidates, conflict_items=None):
    return {
        "_meta": {
            "draft_id": "draft_taxonomy",
            "project_id": "project_taxonomy",
        },
        "merged_requirement_candidates": list(candidates),
        "conflict_items": list(conflict_items or []),
    }


def test_match_requirements_maps_feature_and_expands_taxonomy_items() -> None:
    taxonomy, rulebase = _references()
    result = match_requirements(
        _draft([_candidate("feature_001", "feature", "push notification")]),
        taxonomy,
        rulebase,
    )

    assert result["_meta"]["pipeline_phase"] == "taxonomy_matching"
    assert result["mapped_features"][0]["feature_key"] == "notification_center"
    assert any(role["name"] == "Backend Engineer" for role in result["required_roles"])
    assert any(skill["name"] == "Push Notification" for skill in result["required_skills"])
    assert result["unknown_requirements"] == []


def test_match_requirements_sends_unmatched_feature_to_unknown_without_mutating_taxonomy() -> None:
    taxonomy, rulebase = _references()
    original_taxonomy = deepcopy(taxonomy)

    result = match_requirements(
        _draft([_candidate("feature_unknown", "feature", "AR product preview")]),
        taxonomy,
        rulebase,
    )

    assert result["mapped_features"] == []
    assert result["unknown_requirements"][0]["text"] == "AR product preview"
    assert result["unknown_requirements"][0]["status"] == "manual_review_required"
    assert taxonomy == original_taxonomy


def test_match_requirements_does_not_map_conflict_candidates() -> None:
    taxonomy, rulebase = _references()
    result = match_requirements(
        _draft(
            [_candidate("feature_conflict", "feature", "push notification", status="conflict")],
            conflict_items=[
                {
                    "candidate_ids": ["feature_conflict", "feature_other"],
                    "reason": "Opposite requirement polarity.",
                    "status": "manual_review_required",
                    "source_evidence_ids": ["feature_conflict_ev_001"],
                }
            ],
        ),
        taxonomy,
        rulebase,
    )

    assert result["mapped_features"] == []
    assert result["conflict_items"]
    assert result["_meta"]["status"] == "needs_human_confirm"


def test_match_requirements_maps_explicit_standard_role_and_skill() -> None:
    taxonomy, rulebase = _references()
    result = match_requirements(
        _draft(
            [
                _candidate("role_001", "role", "Backend Engineer"),
                _candidate("skill_001", "skill", "OAuth"),
            ]
        ),
        taxonomy,
        rulebase,
    )

    assert any(role["name"] == "Backend Engineer" for role in result["required_roles"])
    assert any(role.get("job_category_codes") == ["BE"] for role in result["required_roles"])
    assert any(skill["name"] == "OAuth" for skill in result["required_skills"])
    assert result["unknown_requirements"] == []


def test_match_requirements_maps_role_and_skill_aliases() -> None:
    taxonomy, rulebase = _references()
    result = match_requirements(
        _draft(
            [
                _candidate("role_001", "role", "Backend Lead"),
                _candidate("role_002", "role", "PM"),
                _candidate("skill_001", "skill", "FCM/APNs 발송"),
                _candidate("skill_002", "skill", "비동기 큐 (Kafka) 처리"),
            ]
        ),
        taxonomy,
        rulebase,
    )

    role_names = {role["name"] for role in result["required_roles"]}
    skill_names = {skill["name"] for skill in result["required_skills"]}

    assert {"Backend Lead", "Product Manager"} <= role_names
    assert {"Push Delivery", "Kafka"} <= skill_names
    assert result["unknown_requirements"] == []


def test_match_requirements_maps_expanded_notification_features_and_constraints() -> None:
    taxonomy, rulebase = _references()
    result = match_requirements(
        _draft(
            [
                _candidate("feature_001", "feature", "카테고리별 수신 설정 API"),
                _candidate("feature_002", "feature", "일괄 읽음 API"),
                _candidate("feature_003", "feature", "푸시 발송 서비스 연동 (FCM/APNs)"),
                _candidate("constraint_001", "constraint", "알림 목록 로딩 p95 ≤ 500ms"),
                _candidate("constraint_002", "constraint", "웹(PC) 알림 센터 Out of Scope"),
            ]
        ),
        taxonomy,
        rulebase,
    )

    feature_keys = {feature["feature_key"] for feature in result["mapped_features"]}
    constraint_keys = {constraint["constraint_key"] for constraint in result["constraints"]}

    assert {
        "notification_preferences",
        "notification_read_state",
        "notification_delivery_integration",
    } <= feature_keys
    assert {"performance_target", "scope_exclusion"} <= constraint_keys
    assert result["unknown_requirements"] == []


def test_match_requirements_merges_duplicate_constraint_aliases_by_standard_key() -> None:
    taxonomy, rulebase = _references()
    result = match_requirements(
        _draft(
            [
                _candidate("constraint_001", "constraint", "MVP"),
                _candidate("constraint_002", "constraint", "Duration: 6 weeks"),
                _candidate("constraint_003", "constraint", "Budget: 50000 USD"),
                _candidate("constraint_004", "constraint", "USD"),
            ]
        ),
        taxonomy,
        rulebase,
    )

    constraint_keys = {constraint["constraint_key"] for constraint in result["constraints"]}
    assert constraint_keys == {"short_timeline", "budget_limited"}
    assert len(result["constraints"]) == 2
    assert result["unknown_requirements"] == []


def test_match_requirements_keeps_unstandardized_skill_as_unknown() -> None:
    taxonomy, rulebase = _references()
    result = match_requirements(
        _draft([_candidate("skill_unknown", "skill", "WebXR shader tuning")]),
        taxonomy,
        rulebase,
    )

    assert result["required_skills"] == []
    assert result["unknown_requirements"][0]["item_type"] == "skill"
    assert "did not match taxonomy standard names" in result["unknown_requirements"][0]["reason"]
