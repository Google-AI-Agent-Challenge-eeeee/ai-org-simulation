import json

from backend.agents.requirements_agent.pipeline.local_input_loader import (
    DEFAULT_EMPLOYEE_DATA_DIR,
    read_employee_data_headers,
    validate_employee_column_rules_against_headers,
)
from backend.agents.requirements_agent.pipeline.requirements_pipeline import (
    OUTPUT_FILENAMES,
    RequirementsPipelineConfig,
    load_references,
    run_requirements_pipeline,
)


def test_finish_outputs_are_written_only_when_explicitly_requested(tmp_path) -> None:
    raw_text = (
        "# Notification Center MVP\n\n"
        "Goal: Build notification center.\n\n"
        "## Functional Requirements\n"
        "- Users need push notification and notification preferences.\n\n"
        "## Constraints\n"
        "- Duration: 6 weeks.\n"
        "- Budget: 50000 USD.\n"
    )
    no_write_dir = tmp_path / "no_write"

    no_write = run_requirements_pipeline(
        raw_text,
        document_id="finish_no_write",
        config=RequirementsPipelineConfig(write_outputs=False, output_dir=no_write_dir),
    )

    assert no_write["_meta"]["write_outputs"] is False
    assert "written_files" not in no_write
    assert not no_write_dir.exists()

    write_dir = tmp_path / "write"
    written = run_requirements_pipeline(
        raw_text,
        document_id="finish_write",
        config=RequirementsPipelineConfig(write_outputs=True, output_dir=write_dir),
    )

    assert len(written["written_files"]) == len(OUTPUT_FILENAMES)
    assert {path.name for path in write_dir.iterdir()} == set(OUTPUT_FILENAMES.values())
    for filename in OUTPUT_FILENAMES.values():
        payload = json.loads((write_dir / filename).read_text(encoding="utf-8"))
        assert payload


def test_finish_selected_columns_exist_in_local_csv_headers() -> None:
    references = load_references()
    headers = read_employee_data_headers(DEFAULT_EMPLOYEE_DATA_DIR)
    validation = validate_employee_column_rules_against_headers(
        references["employee_column_rules"],
        headers,
    )

    assert validation["status"] == "passed"

