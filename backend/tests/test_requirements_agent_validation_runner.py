from pathlib import Path

from backend.agents.requirements_agent.modules.coverage_check import check_coverage
from backend.agents.requirements_agent.pipeline.extraction_runner import build_evidence_map
from backend.agents.requirements_agent.pipeline.requirements_pipeline import (
    RequirementsPipelineConfig,
    run_requirements_pipeline,
)
from backend.agents.requirements_agent.pipeline.section_splitter import prepare_document_sections
from backend.agents.requirements_agent.pipeline.validation_runner import (
    build_prd_evidence_map,
    build_validation_payload,
    extract_project_fields,
    run_validation,
)

ROOT = Path("backend/agents/requirements_agent")


def _project_fields():
    return {
        "project_name": "Validator MVP",
        "project_goal": "Validate Requirements Agent output.",
        "duration_weeks": 6,
        "budget": 50000,
    }


def _evidence(section, text, evidence_id="ev_001"):
    return {
        "evidence_id": evidence_id,
        "document_id": "prd_validation",
        "section_id": section["section_id"],
        "section_title": section["section_title"],
        "chunk_id": section.get("chunk_id"),
        "source_range": section["source_range"],
        "text": text,
    }


def _candidate(candidate_id, section, text, *, confidence=0.92, source_evidence=None):
    return {
        "candidate_id": candidate_id,
        "item_type": "feature",
        "text": text,
        "normalized_text": text.casefold(),
        "source_evidence": (
            source_evidence if source_evidence is not None else [_evidence(section, text)]
        ),
        "confidence": confidence,
        "status": "candidate",
    }


def test_extract_project_fields_handles_korean_prd_meta_goal_duration_and_no_budget() -> None:
    fields = extract_project_fields(
        """
        PRD:
        실시간
        실시간
        알림
        알림
        센터
        센터

        0. Document Meta
        제목
        실시간
        알림
        센터 PRD
        작성자 PM 이지은

        1. TL;DR
        모바일 앱 사용자가 중요한 이벤트를 놓치는 문제를 앱 내 통합 알림 센터와
        푸시 알림 연동으로 해결하여 알림 열람율 +35%, CS 인입 -40% 달성을 목표로 합니다.

        11. 가정 · 제약
        기간: 6주 (1 스프린트 = 2주, 3 스프린트)
        예산: 별도 추가 인프라 비용 없음
        """
    )

    assert fields["project_name"] == "실시간 알림 센터 PRD"
    assert "알림 열람율" in fields["project_goal"]
    assert fields["duration_weeks"] == 6
    assert fields["budget"] is None
    assert fields["budget_status"] == "explicit_no_additional_budget"


def test_validation_does_not_mark_explicit_no_additional_budget_as_missing() -> None:
    prepared = prepare_document_sections(
        """
        # 실시간 알림 센터 PRD

        ## TL;DR
        알림 열람율 개선을 목표로 합니다.

        ## Constraints
        - 기간: 6주
        - 예산: 별도 추가 인프라 비용 없음
        """,
        document_id="prd_validation",
    )
    draft = _draft([])
    mapped = _mapped_requirements()
    coverage = check_coverage(prepared["sections"])

    result = run_validation(
        prepared_document=prepared,
        extracted_requirements_draft=draft,
        mapped_requirements=mapped,
        coverage_check=coverage,
        project_fields=extract_project_fields(prepared["raw_text"]),
    )

    missing_fields = {item["field"] for item in result["missing_fields"]}
    assert "budget" not in missing_fields


def _draft(candidates):
    return {
        "_meta": {
            "draft_id": "draft_validation",
            "pipeline_phase": "chunk_result_merge",
        },
        "merged_requirement_candidates": list(candidates),
        "low_confidence_items": [],
        "evidence_map": build_evidence_map(candidates),
    }


def _mapped_requirements(*, feature=None, constraints=None, risks=None):
    return {
        "_meta": {
            "mapped_requirements_id": "mapped_validation",
            "pipeline_phase": "taxonomy_matching",
            "status": "completed",
        },
        "mapped_features": [feature] if feature else [],
        "constraints": list(constraints or []),
        "risk_factors": list(risks or []),
        "required_roles": [],
        "required_skills": [],
        "unknown_requirements": [],
        "conflict_items": [],
        "low_confidence_items": [],
    }


def test_validator_finds_missing_requirement_like_prd_evidence_without_deleting_items() -> None:
    prepared = prepare_document_sections(
        """
        # Validator MVP

        Goal: Validate Requirements Agent output.

        ## Functional Requirements
        - Users need push notification.
        - Refunds must be supported.

        ## Constraints
        - Duration: 6 weeks.
        - Budget: 50000 USD.
        """,
        document_id="prd_validation",
    )
    section = next(
        item for item in prepared["sections"] if item["section_title"] == "Functional Requirements"
    )
    candidate = _candidate("feature_push", section, "Users need push notification.")
    draft = _draft([candidate])
    mapped = _mapped_requirements(
        feature={
            "candidate_id": "feature_push",
            "feature_key": "notification_center",
            "standard_name": "Notification Center",
            "raw_text": "Users need push notification.",
            "confidence": 0.94,
            "source_evidence": candidate["source_evidence"],
            "status": "mapped",
        }
    )
    coverage = check_coverage(
        prepared["sections"],
        mapped_requirements=mapped,
        extracted_requirements_draft=draft,
    )

    result = run_validation(
        prepared_document=prepared,
        extracted_requirements_draft=draft,
        mapped_requirements=mapped,
        coverage_check=coverage,
        project_fields=_project_fields(),
    )

    assert any(
        "Refunds must be supported" in item["text"] for item in result["missing_extractions"]
    )
    assert draft["merged_requirement_candidates"] == [candidate]
    assert result["_meta"]["status"] == "needs_human_confirm"


def test_validator_flags_invalid_extracted_and_mapped_items_without_evidence() -> None:
    prepared = prepare_document_sections(
        """
        # Validator MVP

        Goal: Validate Requirements Agent output.

        ## Functional Requirements
        - Users need push notification.
        """,
        document_id="prd_validation",
    )
    section = prepared["sections"][-1]
    candidate = _candidate(
        "feature_without_evidence",
        section,
        "Users need push notification.",
        source_evidence=[],
    )
    draft = _draft([candidate])
    mapped = _mapped_requirements(
        feature={
            "candidate_id": "fabricated_feature",
            "feature_key": "notification_center",
            "standard_name": "Notification Center",
            "raw_text": "Push notification",
            "confidence": 0.91,
            "source_evidence": [
                {
                    "evidence_id": "fabricated_ev",
                    "document_id": "prd_validation",
                    "section_id": section["section_id"],
                    "text": "This sentence does not exist in the PRD.",
                }
            ],
            "status": "mapped",
        }
    )
    coverage = check_coverage(
        prepared["sections"],
        mapped_requirements=mapped,
        extracted_requirements_draft=draft,
    )

    result = run_validation(
        prepared_document=prepared,
        extracted_requirements_draft=draft,
        mapped_requirements=mapped,
        coverage_check=coverage,
        project_fields=_project_fields(),
    )

    invalid_ids = {item["item_id"] for item in result["invalid_items"]}
    assert "feature_without_evidence" in invalid_ids
    assert "fabricated_feature" in invalid_ids
    assert all(item["status"] == "manual_review_required" for item in result["invalid_items"])


def test_validator_routes_low_confidence_items_to_human_confirm_bucket() -> None:
    prepared = prepare_document_sections(
        """
        # Validator MVP

        Goal: Validate Requirements Agent output.

        ## Functional Requirements
        - Users should maybe support lightweight notification preferences.
        """,
        document_id="prd_validation",
    )
    section = prepared["sections"][-1]
    candidate = _candidate(
        "feature_low_confidence",
        section,
        "Users should maybe support lightweight notification preferences.",
        confidence=0.62,
    )
    draft = _draft([candidate])
    mapped = _mapped_requirements()
    coverage = check_coverage(
        prepared["sections"],
        mapped_requirements=mapped,
        extracted_requirements_draft=draft,
    )

    result = run_validation(
        prepared_document=prepared,
        extracted_requirements_draft=draft,
        mapped_requirements=mapped,
        coverage_check=coverage,
        project_fields=_project_fields(),
    )

    assert result["low_confidence_items"][0]["item_id"] == "feature_low_confidence"
    assert result["low_confidence_items"][0]["status"] == "manual_review_required"
    assert draft["merged_requirement_candidates"][0]["confidence"] == 0.62


def test_validation_payload_contains_prd_evidence_map_and_guardrails() -> None:
    prepared = prepare_document_sections(
        "# Validator MVP\n\n## Functional Requirements\nUsers need push notification.",
        document_id="prd_validation",
    )
    draft = _draft([])
    mapped = _mapped_requirements()
    coverage = check_coverage(prepared["sections"])

    payload = build_validation_payload(
        prepared_document=prepared,
        extracted_requirements_draft=draft,
        mapped_requirements=mapped,
        coverage_check=coverage,
        project_fields=_project_fields(),
        prd_evidence_map=build_prd_evidence_map(prepared),
    )

    assert payload["prd_evidence_map"]["by_evidence_id"]
    assert payload["phase_boundaries"]["delete_items"] is False
    assert payload["phase_boundaries"]["route_review_items_to_human_confirm"] is True


def test_pipeline_connects_phase_six_without_writing_output_files() -> None:
    before = {path.name for path in (ROOT / "outputs").iterdir()}
    result = run_requirements_pipeline(
        """
        # Notification Center MVP

        Goal: Build a lightweight notification center.

        ## Functional Requirements
        - Support push notification and in-app notification preferences.

        ## Constraints
        - Duration: 6 weeks.
        - Budget: 50000 USD.
        """,
        project_fields={
            "project_name": "Notification Center MVP",
            "project_goal": "Build a lightweight notification center.",
            "duration_weeks": 6,
            "budget": 50000,
        },
        config=RequirementsPipelineConfig(write_outputs=False),
    )
    after = {path.name for path in (ROOT / "outputs").iterdir()}

    validation = result["outputs"]["validation_result"]

    assert before == after
    assert validation["_meta"]["pipeline_phase"] == "validation"
    assert validation["prd_evidence_map"]["by_evidence_id"]
    assert "validation_stats" in validation
