from copy import deepcopy
from pathlib import Path

import pytest

from backend.agents.requirements_agent.modules.taxonomy_matcher import load_json
from backend.agents.requirements_agent.pipeline.local_input_loader import (
    DEFAULT_EMPLOYEE_DATA_DIR,
    LocalInputError,
    build_local_project_fields,
    load_local_prd_input,
    read_employee_data_headers,
    validate_employee_column_rules_against_headers,
)

ROOT = Path("backend/agents/requirements_agent")


def test_load_local_prd_input_preserves_raw_markdown(tmp_path) -> None:
    prd = tmp_path / "Notification Center PRD.md"
    raw_text = "# Notification Center MVP\n\nGoal: Build notifications.\n"
    prd.write_text(raw_text, encoding="utf-8")

    loaded = load_local_prd_input(prd)

    assert loaded.raw_text == raw_text
    assert loaded.document_id == "notification_center_prd"
    assert loaded.document_type == "prd"
    assert loaded.source_uri.startswith("file:")
    assert loaded.raw_text_ref.endswith("#raw_text")
    assert loaded.extraction["method"] == "plain_text"


def test_read_employee_data_headers_loads_all_raw_sources() -> None:
    headers = read_employee_data_headers(DEFAULT_EMPLOYEE_DATA_DIR)

    assert set(headers) == {
        "employee",
        "github_activity",
        "slack_activity",
        "jira_activity",
        "calendar_activity",
    }
    assert "employee_id" in headers["employee"]["columns"]
    assert "commit_count_3m" in headers["github_activity"]["columns"]
    assert "message_count" in headers["slack_activity"]["columns"]
    assert "completed_issue_count" in headers["jira_activity"]["columns"]
    assert "busy_minutes" in headers["calendar_activity"]["columns"]


def test_employee_column_rules_match_local_csv_headers() -> None:
    rules = load_json(ROOT / "references/employee_column_rules.json")
    headers = read_employee_data_headers(DEFAULT_EMPLOYEE_DATA_DIR)

    result = validate_employee_column_rules_against_headers(rules, headers)

    assert result["status"] == "passed"
    assert result["missing_required_columns"] == []
    assert result["unknown_sources"] == []
    assert result["checked_column_count"] > 0


def test_employee_column_rule_validation_reports_missing_csv_column() -> None:
    rules = deepcopy(load_json(ROOT / "references/employee_column_rules.json"))
    rules["requirement_type_rules"]["technical_execution"]["columns"].append(
        {
            "source": "employee",
            "name": "missing_skill_stack",
            "reason": "Intentional test-only missing column.",
        }
    )
    headers = read_employee_data_headers(DEFAULT_EMPLOYEE_DATA_DIR)

    result = validate_employee_column_rules_against_headers(rules, headers)

    assert result["status"] == "failed"
    assert result["missing_required_columns"][0]["column_key"] == "employee.missing_skill_stack"


def test_build_local_project_fields_reuses_pipeline_inference() -> None:
    fields = build_local_project_fields(
        "# Notification Center MVP\n\n"
        "Goal: Build a notification center.\n\n"
        "The MVP must ship in 6 weeks with budget 50000 USD."
    )

    assert fields["project_name"] == "Notification Center MVP"
    assert fields["duration_weeks"] == 6
    assert fields["budget"] == 50000


def test_missing_prd_input_reports_clear_error(tmp_path) -> None:
    with pytest.raises(LocalInputError):
        load_local_prd_input(tmp_path / "missing.md")
