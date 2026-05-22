from copy import deepcopy
from pathlib import Path

from backend.agents.requirements_agent.modules.column_selection_draft import (
    load_json,
    select_columns_draft,
    selected_column_keys,
    validate_employee_column_rules,
)
from backend.agents.requirements_agent.pipeline.requirements_pipeline import (
    RequirementsPipelineConfig,
    run_requirements_pipeline,
)

ROOT = Path("backend/agents/requirements_agent")


def _employee_column_rules():
    return load_json(ROOT / "references/employee_column_rules.json")


def _mapped_requirements(
    *,
    feature_keys=None,
    constraint_keys=None,
    unknown_requirements=None,
):
    return {
        "_meta": {
            "mapped_requirements_id": "mapped_for_column_selection",
            "pipeline_phase": "taxonomy_matching",
        },
        "mapped_features": [
            {
                "feature_key": feature_key,
                "status": "mapped",
                "source_evidence": [
                    {
                        "evidence_id": f"{feature_key}_ev_001",
                        "section_id": "sec_001",
                        "text": feature_key,
                    }
                ],
            }
            for feature_key in (feature_keys or [])
        ],
        "constraints": [
            {
                "constraint_key": constraint_key,
                "status": "mapped",
                "source_evidence": [
                    {
                        "evidence_id": f"{constraint_key}_ev_001",
                        "section_id": "sec_002",
                        "text": constraint_key,
                    }
                ],
            }
            for constraint_key in (constraint_keys or [])
        ],
        "unknown_requirements": list(unknown_requirements or []),
    }


def test_select_columns_draft_selects_candidates_and_does_not_finalize_weights() -> None:
    result = select_columns_draft(
        _mapped_requirements(
            feature_keys=["notification_center"],
            constraint_keys=["short_timeline", "budget_limited"],
        ),
        _employee_column_rules(),
    )

    keys = selected_column_keys(result)

    assert result["_meta"]["pipeline_phase"] == "column_selection_draft"
    assert result["status"] == "draft"
    assert result["selection_stats"]["column_weight_finalized"] is False
    assert "column_weights" not in result
    assert "column_priority_order" not in result
    assert "weighting_reason" not in result
    assert "employee.job_category_code" in keys
    assert "github_activity.commit_count_3m" in keys
    assert "calendar_activity.busy_minutes" in keys
    assert "employee.base_salary_krw" in keys

    salary_column = next(
        column
        for column in result["selected_employee_columns"]
        if column["column_key"] == "employee.base_salary_krw"
    )
    assert salary_column["selection_stage"] == "draft"
    assert salary_column["restricted"] is True
    assert salary_column["requires_human_confirm"] is True
    assert salary_column["source_constraint_keys"] == ["budget_limited"]
    assert "cost_budget" in salary_column["rule_key"]
    assert (
        "feature=notification_center"
        in next(
            column
            for column in result["selected_employee_columns"]
            if column["column_key"] == "employee.job_category_code"
        )["reason"]
    )

    by_rule = {
        selection["rule_key"]: selection for selection in result["selection_by_requirement_type"]
    }
    assert "notification_center" in by_rule["technical_execution"]["source_feature_keys"]
    assert "short_timeline" in by_rule["availability_schedule"]["source_constraint_keys"]


def test_unknown_requirements_do_not_select_columns_until_confirmed_mapping() -> None:
    result = select_columns_draft(
        _mapped_requirements(
            unknown_requirements=[
                {
                    "text": "AR product preview",
                    "reason": "No confident taxonomy or rulebase match.",
                    "status": "manual_review_required",
                }
            ],
        ),
        _employee_column_rules(),
    )

    assert result["selected_employee_columns"] == []
    assert result["selection_stats"]["unknown_requirement_count"] == 1
    assert any("Unknown requirements were ignored" in note for note in result["notes"])


def test_stale_or_excluded_rule_columns_are_reported_and_not_selected() -> None:
    rules = deepcopy(_employee_column_rules())
    rules["requirement_type_rules"]["technical_execution"]["columns"].extend(
        [
            {
                "source": "employee",
                "name": "skill_stack",
                "reason": "Planning-only skill column that is not available.",
            },
            {
                "source": "employee",
                "name": "gender",
                "reason": "Excluded personal column must not be used.",
            },
        ]
    )

    warnings = validate_employee_column_rules(rules)
    warning_columns = {warning["column_key"] for warning in warnings}
    result = select_columns_draft(
        _mapped_requirements(feature_keys=["notification_center"]),
        rules,
    )

    assert "employee.skill_stack" in warning_columns
    assert "employee.gender" in warning_columns
    assert "employee.skill_stack" not in selected_column_keys(result)
    assert "employee.gender" not in selected_column_keys(result)
    assert result["selection_stats"]["rule_warning_count"] >= 2


def test_pipeline_connects_phase_five_without_writing_output_files() -> None:
    before = {path.name for path in (ROOT / "outputs").iterdir()}
    result = run_requirements_pipeline(
        """
        # Notification Center MVP

        Goal: Build a lightweight notification center for web and mobile users.

        Functional Requirements:
        - Support push notification and in-app notification preferences.

        Constraints:
        - Duration: 6 weeks.
        - Budget: 50000 USD.

        Risks:
        - Delivery delay and duplicate notifications are key risks.
        """,
        project_fields={
            "project_name": "Notification Center MVP",
            "project_goal": "Build a lightweight notification center.",
        },
        config=RequirementsPipelineConfig(write_outputs=False),
    )
    after = {path.name for path in (ROOT / "outputs").iterdir()}

    draft = result["outputs"]["column_selection_draft"]
    keys = selected_column_keys(draft)

    assert before == after
    assert draft["status"] == "draft"
    assert "employee.job_category_code" in keys
    assert "column_weights" not in draft
