from pathlib import Path

import pytest

from backend.agents.requirements_agent.modules.requirements_list_builder import (
    RequirementsSchemaValidationError,
    build_requirements_list,
    ensure_valid_requirements_list,
    load_json,
)
from backend.agents.requirements_agent.pipeline.requirements_pipeline import (
    RequirementsPipelineConfig,
    run_requirements_pipeline,
)

ROOT = Path("backend/agents/requirements_agent")


def _schema():
    return load_json(ROOT / "schemas/requirements_schema.json")


def _evidence(text="Users need push notification."):
    return [
        {
            "evidence_id": "ev_001",
            "document_id": "prd_builder",
            "document_type": "prd",
            "section_id": "sec_001",
            "section_title": "Functional Requirements",
            "chunk_id": None,
            "source_range": {
                "page": None,
                "start_char": 0,
                "end_char": len(text),
                "start_line": 1,
                "end_line": 1,
            },
            "text": text,
        }
    ]


def _mapped_requirements():
    return {
        "_meta": {
            "project_id": "project_builder",
            "taxonomy_version": "0.1.0",
            "rulebase_version": "0.1.0",
        },
        "mapped_features": [
            {
                "candidate_id": "feature_confirmed",
                "feature_key": "notification_center",
                "standard_name": "Notification Center",
                "category": "engagement",
                "raw_text": "Users need push notification.",
                "source_evidence": _evidence(),
                "confidence": 0.94,
                "status": "mapped",
            },
            {
                "candidate_id": "feature_low",
                "feature_key": "file_upload_media",
                "standard_name": "File Upload",
                "raw_text": "Maybe file uploads.",
                "source_evidence": _evidence("Maybe file uploads."),
                "confidence": 0.4,
                "status": "low_confidence",
            },
        ],
        "required_roles": [
            {
                "name": "Backend Engineer",
                "job_category_codes": ["BE"],
                "source_feature_keys": ["notification_center"],
                "reason": "Expanded from taxonomy roles.",
            },
            {
                "name": "Infrastructure Engineer",
                "source_feature_keys": ["file_upload_media"],
                "reason": "Should not be promoted when source feature is not confirmed.",
            },
        ],
        "required_skills": [
            {
                "name": "Push Notification",
                "source_feature_keys": ["notification_center"],
                "reason": "Expanded from taxonomy skills.",
            }
        ],
        "constraints": [
            {
                "constraint_key": "short_timeline",
                "text": "Duration: 6 weeks.",
                "constraint_type": "schedule",
                "source_evidence": _evidence("Duration: 6 weeks."),
                "confidence": 0.88,
                "status": "mapped",
            }
        ],
        "risk_factors": [
            {
                "risk_key": "delivery_delay",
                "text": "Delivery delay",
                "source_feature_keys": ["notification_center"],
                "severity": "medium",
                "reason": "Expanded from matched taxonomy feature.",
            },
            {
                "risk_key": "unconfirmed_feature_risk",
                "text": "Unconfirmed feature risk",
                "source_feature_keys": ["file_upload_media"],
                "severity": "medium",
                "reason": "Should not be promoted.",
            },
        ],
        "unknown_requirements": [
            {
                "item_id": "unknown_ar",
                "candidate_id": "internal_candidate_should_be_stripped",
                "text": "AR product preview",
                "item_type": "feature",
                "source_evidence": _evidence("AR product preview"),
                "confidence": 0.7,
                "reason": "No confident taxonomy match.",
                "status": "manual_review_required",
                "suggested_mapping": {"feature_key": "mobile_app_experience"},
            }
        ],
        "conflict_items": [],
        "low_confidence_items": [],
    }


def _column_selection():
    return {
        "_meta": {
            "column_rules_version": "0.1.0",
        },
        "selected_employee_columns": [
            {
                "source": "employee",
                "name": "job_category_code",
                "column_key": "employee.job_category_code",
                "rule_key": "role_match",
                "source_feature_keys": ["notification_center"],
                "reason": "Primary role matching field.",
                "selection_stage": "draft",
                "restricted": False,
                "requires_human_confirm": False,
                "human_confirmed": True,
            }
        ],
    }


def _weighting():
    return {
        "status": "completed",
        "column_weights": {"employee.job_category_code": 1.0},
        "column_priority_order": ["employee.job_category_code"],
        "weighting_reason": {
            "employee.job_category_code": {
                "weight": 1.0,
                "reason": "Project comparison criterion, not employee score.",
                "source_feature_keys": ["notification_center"],
                "source_constraint_keys": [],
                "extra_internal_detail": "should be stripped",
            }
        },
    }


def _coverage():
    return {
        "overall_status": "covered",
        "sections": [
            {
                "section_id": "sec_001",
                "section_title": "Functional Requirements",
                "status": "covered",
                "mapped_item_ids": ["feature_confirmed"],
                "reason": "1/1 requirement-like section signal is reflected.",
                "extra_internal_detail": "should be stripped",
            }
        ],
        "notes": ["All sections are covered by mapped requirements."],
    }


def test_builder_promotes_only_confirmed_requirements_and_strips_internal_fields() -> None:
    result = build_requirements_list(
        mapped_requirements=_mapped_requirements(),
        column_selection_draft=_column_selection(),
        column_weighting_result=_weighting(),
        coverage_check=_coverage(),
        project_fields={
            "project_name": "Builder MVP",
            "project_goal": "Build final Requirements_List.",
            "duration_weeks": 6,
            "budget": 50000,
        },
        validation_result={
            "missing_extractions": [],
            "missing_fields": [],
            "low_confidence_items": [],
            "invalid_items": [],
        },
    )

    assert [item["feature_key"] for item in result["required_features"]] == ["notification_center"]
    assert [item["role"] for item in result["required_roles"]] == ["Backend Engineer"]
    assert [item["risk_key"] for item in result["risk_factors"]] == ["delivery_delay"]
    assert result["selected_employee_columns"][0]["selection_stage"] == "final"
    assert "human_confirmed" not in result["selected_employee_columns"][0]
    assert "candidate_id" not in result["unknown_requirements"][0]
    assert "extra_internal_detail" not in result["weighting_reason"]["employee.job_category_code"]
    assert "extra_internal_detail" not in result["coverage_check"]["sections"][0]


def test_builder_schema_validation_passes_for_sanitized_requirements_list() -> None:
    result = build_requirements_list(
        mapped_requirements=_mapped_requirements(),
        column_selection_draft=_column_selection(),
        column_weighting_result=_weighting(),
        coverage_check=_coverage(),
        project_fields={
            "project_name": "Builder MVP",
            "project_goal": "Build final Requirements_List.",
            "duration_weeks": 6,
            "budget": 50000,
        },
        validation_result={
            "missing_extractions": [],
            "missing_fields": [],
            "low_confidence_items": [],
            "invalid_items": [],
        },
    )

    ensure_valid_requirements_list(result, _schema())


def test_builder_schema_validation_rejects_unexpected_nested_fields() -> None:
    result = build_requirements_list(
        mapped_requirements=_mapped_requirements(),
        column_selection_draft=_column_selection(),
        column_weighting_result=_weighting(),
        coverage_check=_coverage(),
        project_fields={
            "project_name": "Builder MVP",
            "project_goal": "Build final Requirements_List.",
            "duration_weeks": 6,
            "budget": 50000,
        },
        validation_result={},
    )
    result["selected_employee_columns"][0]["human_confirmed"] = True

    with pytest.raises(RequirementsSchemaValidationError):
        ensure_valid_requirements_list(result, _schema())


def test_pipeline_runs_phase_one_to_ten_and_validates_requirements_schema() -> None:
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
        human_confirm_decisions={
            "human_confirm_complete": True,
            "confirmed_restricted_column_keys": [
                "employee.base_salary_krw",
                "employee.bonus_krw",
            ],
        },
        config=RequirementsPipelineConfig(write_outputs=False),
    )
    after = {path.name for path in (ROOT / "outputs").iterdir()}

    requirements_list = result["outputs"]["requirements_list"]

    assert before == after
    assert result["_meta"]["status"] == "completed"
    assert requirements_list["_meta"]["status"] == "completed"
    assert requirements_list["required_features"]
    assert requirements_list["column_weights"]
    assert requirements_list["unknown_requirements"] == []
    assert "invalid_items" not in requirements_list
    ensure_valid_requirements_list(requirements_list, _schema())
