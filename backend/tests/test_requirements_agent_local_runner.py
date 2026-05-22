from pathlib import Path

from backend.agents.requirements_agent.pipeline.run_requirements_agent_local import (
    build_run_summary,
    run_local_requirements_agent,
)


def test_run_local_requirements_agent_stub_mode_without_writing_outputs(tmp_path) -> None:
    prd = tmp_path / "notification_prd.md"
    prd.write_text(
        "# Notification Center MVP\n\n"
        "Goal: Build notification center.\n\n"
        "## Functional Requirements\n"
        "- Users need push notification and in-app notification preferences.\n\n"
        "## Constraints\n"
        "- Duration: 6 weeks.\n"
        "- Budget: 50000 USD.\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "outputs"

    result = run_local_requirements_agent(
        prd_path=prd,
        employee_data_dir=Path("datasets/raw"),
        llm_mode="stub",
        write_outputs=False,
        output_dir=output_dir,
    )

    summary = result["local_run"]["summary"]
    assert summary["write_outputs"] is False
    assert summary["selected_column_count"] > 0
    assert result["local_run"]["column_validation"]["status"] == "passed"
    assert not output_dir.exists()


def test_run_local_requirements_agent_writes_outputs_when_requested(tmp_path) -> None:
    prd = tmp_path / "notification_prd.md"
    prd.write_text(
        "# Notification Center MVP\n\n"
        "Goal: Build notification center.\n\n"
        "## Functional Requirements\n"
        "- Users need push notification.\n"
        "- The MVP must ship in 6 weeks with budget 50000 USD.\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "outputs"

    result = run_local_requirements_agent(
        prd_path=prd,
        employee_data_dir=Path("datasets/raw"),
        llm_mode="stub",
        write_outputs=True,
        output_dir=output_dir,
    )

    assert len(result["written_files"]) == 10
    assert (output_dir / "Requirements_List.json").exists()
    assert build_run_summary(result)["written_file_count"] == 10

