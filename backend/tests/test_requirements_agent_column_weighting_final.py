from pathlib import Path

from backend.agents.requirements_agent.modules.column_weighting_final import (
    calculate_column_weights,
    load_json,
)
from backend.agents.requirements_agent.pipeline.requirements_pipeline import (
    RequirementsPipelineConfig,
    run_requirements_pipeline,
)

ROOT = Path("backend/agents/requirements_agent")


def _employee_column_rules():
    return load_json(ROOT / "references/employee_column_rules.json")


def _column(
    column_key,
    rule_key,
    *,
    source_feature_keys=None,
    source_constraint_keys=None,
    restricted=False,
    human_confirmed=False,
):
    source, name = column_key.split(".", 1)
    return {
        "source": source,
        "name": name,
        "column_key": column_key,
        "rule_key": rule_key,
        "source_feature_keys": list(source_feature_keys or []),
        "source_constraint_keys": list(source_constraint_keys or []),
        "reason": f"{rule_key}: selected for project comparison.",
        "selection_stage": "draft",
        "restricted": restricted,
        "requires_human_confirm": restricted,
        "human_confirmed": human_confirmed,
    }


def _selection(columns):
    return {
        "_meta": {
            "draft_id": "column_selection_for_weighting",
            "pipeline_phase": "column_selection_draft",
        },
        "selected_employee_columns": list(columns),
    }


def test_column_weighting_is_blocked_before_human_confirm_complete() -> None:
    result = calculate_column_weights(
        _selection(
            [
                _column(
                    "employee.job_category_code",
                    "role_match",
                    source_feature_keys=["notification_center"],
                )
            ]
        ),
        _employee_column_rules(),
        human_confirm_complete=False,
    )

    assert result["status"] == "needs_human_confirm"
    assert result["column_weights"] == {}
    assert result["column_priority_order"] == []


def test_column_weighting_blocks_unconfirmed_restricted_columns() -> None:
    result = calculate_column_weights(
        _selection(
            [
                _column(
                    "employee.base_salary_krw",
                    "cost_budget",
                    source_constraint_keys=["budget_limited"],
                    restricted=True,
                    human_confirmed=False,
                )
            ]
        ),
        _employee_column_rules(),
        human_confirm_complete=True,
    )

    assert result["status"] == "needs_human_confirm"
    assert result["pending_restricted_columns"][0]["column_key"] == "employee.base_salary_krw"
    assert result["column_weights"] == {}


def test_column_weighting_calculates_normalized_project_comparison_weights() -> None:
    result = calculate_column_weights(
        _selection(
            [
                _column(
                    "employee.job_category_code",
                    "role_match+quality_assurance",
                    source_feature_keys=["notification_center"],
                ),
                _column(
                    "github_activity.commit_count_3m",
                    "technical_execution",
                    source_feature_keys=["notification_center"],
                ),
                _column(
                    "calendar_activity.busy_minutes",
                    "availability_schedule",
                    source_constraint_keys=["short_timeline"],
                ),
                _column(
                    "employee.base_salary_krw",
                    "cost_budget",
                    source_constraint_keys=["budget_limited"],
                    restricted=True,
                    human_confirmed=True,
                ),
            ]
        ),
        _employee_column_rules(),
        human_confirm_complete=True,
    )

    assert result["status"] == "completed"
    assert result["weighting_stats"]["comparison_scope"] == (
        "project_requirements_to_employee_db_columns"
    )
    assert result["weighting_stats"]["weight_sum"] == 1.0
    assert result["column_priority_order"][0] == "employee.job_category_code"
    assert (
        result["column_weights"]["employee.job_category_code"]
        > result["column_weights"]["employee.base_salary_krw"]
    )
    assert (
        "not an employee performance"
        in result["weighting_reason"]["employee.job_category_code"]["reason"]
    )
    assert result["weighting_reason"]["employee.base_salary_krw"]["source_constraint_keys"] == [
        "budget_limited"
    ]


def test_column_weighting_distributes_rule_weight_across_columns_in_same_rule() -> None:
    result = calculate_column_weights(
        _selection(
            [
                _column(
                    "github_activity.commit_count_3m",
                    "technical_execution",
                    source_feature_keys=["notification_center"],
                ),
                _column(
                    "github_activity.pr_count_3m",
                    "technical_execution",
                    source_feature_keys=["notification_center"],
                ),
            ]
        ),
        _employee_column_rules(),
        human_confirm_complete=True,
    )

    breakdown_by_column = {item["column_key"]: item for item in result["weighting_breakdown"]}

    assert result["column_weights"]["github_activity.commit_count_3m"] == 0.5
    assert result["column_weights"]["github_activity.pr_count_3m"] == 0.5
    assert (
        breakdown_by_column["github_activity.commit_count_3m"]["rule_contributions"][0][
            "rule_column_count"
        ]
        == 2
    )


def test_pipeline_connects_phase_nine_after_human_confirm_without_output_files() -> None:
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

    weighting = result["outputs"]["column_weighting_result"]

    assert before == after
    assert weighting["status"] == "completed"
    assert weighting["column_weights"]
    assert weighting["column_priority_order"]
    assert weighting["weighting_reason"]
    assert weighting["weighting_stats"]["weight_sum"] == 1.0
