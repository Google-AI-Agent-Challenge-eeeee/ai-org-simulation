from copy import deepcopy
from pathlib import Path

from backend.agents.requirements_agent.modules.human_confirm import (
    build_human_confirm_result,
    build_review_packet,
    merge_project_specific_mapping,
)
from backend.agents.requirements_agent.modules.taxonomy_matcher import load_json
from backend.agents.requirements_agent.pipeline.requirements_pipeline import (
    RequirementsPipelineConfig,
    run_requirements_pipeline,
)

ROOT = Path("backend/agents/requirements_agent")


def _generated_outputs_exist() -> bool:
    return any(path.name != ".gitkeep" for path in (ROOT / "outputs").iterdir())


def _review_item(item_id, text, item_type="feature"):
    return {
        "item_id": item_id,
        "text": text,
        "item_type": item_type,
        "source_evidence": [
            {
                "evidence_id": f"{item_id}_ev_001",
                "document_id": "prd_human_confirm",
                "section_id": "sec_001",
                "text": text,
            }
        ],
        "confidence": 0.42,
        "reason": "Needs Human Confirm.",
        "status": "manual_review_required",
        "suggested_mapping": None,
    }


def _mapped_requirements():
    return {
        "_meta": {
            "mapped_requirements_id": "mapped_human_confirm",
            "pipeline_phase": "taxonomy_matching",
            "status": "needs_human_confirm",
        },
        "mapped_features": [],
        "constraints": [],
        "risk_factors": [],
        "required_roles": [],
        "required_skills": [],
        "unknown_requirements": [
            _review_item("unknown_ar", "AR product preview"),
        ],
        "conflict_items": [],
        "low_confidence_items": [
            _review_item("low_conf_feature", "Maybe support lightweight notifications"),
        ],
    }


def _validation_result():
    return {
        "_meta": {
            "validation_id": "validation_human_confirm",
            "pipeline_phase": "validation",
            "status": "needs_human_confirm",
        },
        "missing_extractions": [
            _review_item("missing_refund", "Refunds must be supported."),
        ],
        "invalid_items": [
            _review_item("invalid_fabricated", "Fabricated requirement"),
        ],
        "low_confidence_items": [
            _review_item("low_conf_constraint", "Budget is probably small", "constraint"),
        ],
        "missing_fields": [
            {
                "field": "budget",
                "reason": "Project budget is missing.",
                "severity": "info",
                "suggested_question": "Is there a fixed budget or cost limit?",
            }
        ],
        "project_fields": {
            "project_name": "Human Confirm MVP",
            "project_goal": "Test review decisions.",
            "duration_weeks": 6,
            "budget": None,
        },
    }


def _column_selection_draft():
    return {
        "_meta": {
            "draft_id": "column_selection_human_confirm",
            "pipeline_phase": "column_selection_draft",
        },
        "selected_employee_columns": [
            {
                "source": "employee",
                "name": "base_salary_krw",
                "column_key": "employee.base_salary_krw",
                "rule_key": "cost_budget",
                "reason": "Restricted salary proxy.",
                "selection_stage": "draft",
                "restricted": True,
                "requires_human_confirm": True,
            }
        ],
        "restricted_columns_needing_human_confirm": [
            {
                "source": "employee",
                "name": "base_salary_krw",
                "column_key": "employee.base_salary_krw",
                "rule_key": "cost_budget",
                "reason": "Restricted salary proxy.",
                "selection_stage": "draft",
                "restricted": True,
                "requires_human_confirm": True,
            }
        ],
    }


def test_build_review_packet_collects_all_human_confirm_buckets() -> None:
    packet = build_review_packet(
        validation_result=_validation_result(),
        mapped_requirements=_mapped_requirements(),
        column_selection_draft=_column_selection_draft(),
    )

    assert packet["status"] == "needs_human_confirm"
    assert packet["review_counts"]["unknown_requirement_count"] == 1
    assert packet["review_counts"]["missing_extraction_count"] == 1
    assert packet["review_counts"]["invalid_item_count"] == 1
    assert packet["review_counts"]["low_confidence_count"] == 2
    assert packet["review_counts"]["missing_field_count"] == 1
    assert packet["review_counts"]["restricted_column_count"] == 1
    assert "project_specific_mapping" in packet["decision_template"]


def test_human_confirm_decisions_remove_items_update_fields_and_confirm_restricted_columns() -> (
    None
):
    mapped = _mapped_requirements()
    validation = _validation_result()
    columns = _column_selection_draft()
    mapped_before = deepcopy(mapped)

    result = build_human_confirm_result(
        validation_result=validation,
        mapped_requirements=mapped,
        column_selection_draft=columns,
        human_confirm_decisions={
            "human_confirm_complete": True,
            "removed_items": [
                {"item_id": "unknown_ar", "reason": "Out of scope for this project."},
                {"item_id": "missing_refund", "reason": "Not part of MVP."},
                {"item_id": "invalid_fabricated", "reason": "No evidence."},
                {"item_id": "low_conf_feature", "reason": "Too vague."},
                {"item_id": "low_conf_constraint", "reason": "Too vague."},
            ],
            "updated_project_fields": {"budget": 50000},
            "confirmed_restricted_column_keys": ["employee.base_salary_krw"],
        },
        project_specific_mapping={},
    )

    applied = result["applied"]

    assert result["human_confirm_complete"] is True
    assert result["remaining_review_counts"]["unknown_requirement_count"] == 0
    assert result["remaining_review_counts"]["missing_extraction_count"] == 0
    assert result["remaining_review_counts"]["invalid_item_count"] == 0
    assert result["remaining_review_counts"]["low_confidence_count"] == 0
    assert result["remaining_review_counts"]["missing_field_count"] == 0
    assert result["remaining_review_counts"]["restricted_column_count"] == 0
    assert applied["validation_result"]["project_fields"]["budget"] == 50000
    assert applied["column_selection_draft"]["selected_employee_columns"][0]["human_confirmed"]
    assert mapped == mapped_before


def test_merge_project_specific_mapping_is_project_only_decision_shape() -> None:
    merged = merge_project_specific_mapping(
        {"AR product preview": "file_upload_media"},
        {
            "project_specific_mapping": {
                "virtual try-on": "mobile_app_experience",
            }
        },
    )

    assert merged == {
        "AR product preview": "file_upload_media",
        "virtual try-on": "mobile_app_experience",
    }


def test_pipeline_applies_project_specific_mapping_without_mutating_taxonomy() -> None:
    taxonomy_path = ROOT / "references/taxonomy.json"
    taxonomy_before = load_json(taxonomy_path)

    def extractor(payload):
        if "AR product preview" not in payload["section"]["section_text"]:
            return {
                "section_id": payload["section"]["section_id"],
                "section_title": payload["section"]["section_title"],
                "raw_features": [],
                "raw_roles": [],
                "raw_skills": [],
                "raw_constraints": [],
                "raw_risk_candidates": [],
                "confidence": 0.9,
            }
        return {
            "section_id": payload["section"]["section_id"],
            "section_title": payload["section"]["section_title"],
            "raw_features": [
                {
                    "text": "AR product preview",
                    "confidence": 0.95,
                }
            ],
            "raw_roles": [],
            "raw_skills": [],
            "raw_constraints": [],
            "raw_risk_candidates": [],
            "confidence": 0.95,
        }

    result = run_requirements_pipeline(
        """
        # Human Confirm MVP

        Goal: Build project-specific AR preview flow.

        ## Functional Requirements
        - Users need AR product preview.
        """,
        project_fields={
            "project_name": "Human Confirm MVP",
            "project_goal": "Build project-specific AR preview flow.",
            "duration_weeks": 6,
            "budget": 50000,
        },
        extractor=extractor,
        human_confirm_decisions={
            "human_confirm_complete": True,
            "project_specific_mapping": {
                "AR product preview": "file_upload_media",
            },
        },
        config=RequirementsPipelineConfig(write_outputs=False),
    )

    mapped = result["outputs"]["mapped_requirements"]
    taxonomy_after = load_json(taxonomy_path)

    assert mapped["mapped_features"][0]["feature_key"] == "file_upload_media"
    assert mapped["unknown_requirements"] == []
    assert result["outputs"]["human_confirm_result"]["project_specific_mapping"] == {
        "AR product preview": "file_upload_media"
    }
    assert taxonomy_after == taxonomy_before
    assert not _generated_outputs_exist()
