from pathlib import Path

from backend.agents.requirements_agent.modules.coverage_check import check_coverage
from backend.agents.requirements_agent.pipeline.requirements_pipeline import (
    RequirementsPipelineConfig,
    run_requirements_pipeline,
)
from backend.agents.requirements_agent.pipeline.section_splitter import prepare_document_sections

ROOT = Path("backend/agents/requirements_agent")


def _evidence(section, text, evidence_id):
    return {
        "evidence_id": evidence_id,
        "document_id": "prd_coverage",
        "section_id": section["section_id"],
        "section_title": section["section_title"],
        "chunk_id": section.get("chunk_id"),
        "source_range": section["source_range"],
        "text": text,
    }


def _candidate(candidate_id, section, text, item_type="feature"):
    return {
        "candidate_id": candidate_id,
        "item_type": item_type,
        "text": text,
        "normalized_text": text.casefold(),
        "source_evidence": [_evidence(section, text, f"{candidate_id}_ev_001")],
        "confidence": 0.92,
        "status": "candidate",
    }


def _draft(candidates):
    return {
        "_meta": {
            "draft_id": "draft_coverage",
            "pipeline_phase": "chunk_result_merge",
        },
        "merged_requirement_candidates": list(candidates),
        "conflict_items": [],
        "low_confidence_items": [],
    }


def test_check_coverage_marks_section_covered_when_all_signals_are_extracted() -> None:
    prepared = prepare_document_sections(
        """
        # Coverage MVP

        ## Functional Requirements
        - Users need push notification.
        """,
        document_id="prd_coverage",
    )
    section = prepared["sections"][-1]
    draft = _draft([_candidate("feature_push", section, "Users need push notification.")])

    result = check_coverage(
        prepared["sections"],
        extracted_requirements_draft=draft,
    )
    functional = next(
        item for item in result["sections"] if item["section_id"] == section["section_id"]
    )

    assert functional["status"] == "covered"
    assert functional["mapped_item_ids"] == ["feature_push"]
    assert "1/1 requirement-like" in functional["reason"]


def test_check_coverage_marks_section_partial_when_some_signals_are_missing() -> None:
    prepared = prepare_document_sections(
        """
        # Coverage MVP

        ## Functional Requirements
        - Users need push notification.
        - Refunds must be supported.
        """,
        document_id="prd_coverage",
    )
    section = prepared["sections"][-1]
    draft = _draft([_candidate("feature_push", section, "Users need push notification.")])

    result = check_coverage(
        prepared["sections"],
        extracted_requirements_draft=draft,
    )
    functional = next(
        item for item in result["sections"] if item["section_id"] == section["section_id"]
    )

    assert functional["status"] == "partial"
    assert "1/2 requirement-like" in functional["reason"]
    assert result["overall_status"] == "partial"


def test_check_coverage_marks_requirement_section_missing_when_no_extraction_exists() -> None:
    prepared = prepare_document_sections(
        """
        # Coverage MVP

        ## Risks
        - Duplicate notifications are a risk.
        """,
        document_id="prd_coverage",
    )

    result = check_coverage(
        prepared["sections"],
        extracted_requirements_draft=_draft([]),
    )
    risks = next(
        item for item in result["sections"] if "Duplicate notifications" in item["section_title"]
    )

    assert risks["status"] == "missing"
    assert risks["mapped_item_ids"] == []
    assert "0/1 requirement-like" in risks["reason"]


def test_check_coverage_uses_review_items_as_partial_human_confirm_signal() -> None:
    prepared = prepare_document_sections(
        """
        # Coverage MVP

        ## Functional Requirements
        - Users need AR product preview.
        """,
        document_id="prd_coverage",
    )
    section = prepared["sections"][-1]
    unknown = {
        "item_id": "unknown_ar_preview",
        "text": "Users need AR product preview.",
        "item_type": "feature",
        "source_evidence": [_evidence(section, "Users need AR product preview.", "unknown_ev_001")],
        "confidence": 0.8,
        "reason": "No confident taxonomy or rulebase match.",
        "status": "manual_review_required",
    }

    result = check_coverage(
        prepared["sections"],
        extracted_requirements_draft=_draft([]),
        mapped_requirements={
            "mapped_features": [],
            "constraints": [],
            "risk_factors": [],
            "unknown_requirements": [unknown],
            "conflict_items": [],
            "low_confidence_items": [],
        },
    )
    functional = next(
        item for item in result["sections"] if item["section_id"] == section["section_id"]
    )

    assert functional["status"] == "partial"
    assert functional["mapped_item_ids"] == ["unknown_ar_preview"]
    assert "Human Confirm" in functional["reason"]


def test_pipeline_connects_phase_seven_without_writing_output_files() -> None:
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

    coverage = result["outputs"]["coverage_check_result"]

    assert before == after
    assert coverage["overall_status"] in {"covered", "partial", "missing"}
    assert coverage["sections"]
    assert all(
        section["status"] in {"covered", "partial", "missing"} for section in coverage["sections"]
    )
