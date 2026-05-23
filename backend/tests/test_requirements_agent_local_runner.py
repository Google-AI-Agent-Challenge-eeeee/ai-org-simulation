from pathlib import Path

from backend.agents.requirements_agent.pipeline.requirements_pipeline import (
    OUTPUT_FILENAMES as REQUIREMENTS_OUTPUT_FILENAMES,
)
from backend.agents.requirements_agent.pipeline.run_requirements_agent_local import (
    LOCAL_RANKING_OUTPUT_FILENAMES,
    build_run_summary,
    run_local_requirements_agent,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.run_shadow_roleplay_local import (
    OUTPUT_FILENAMES as ROLEPLAY_OUTPUT_FILENAMES,
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

    expected_written_count = len(
        set(REQUIREMENTS_OUTPUT_FILENAMES.values()) | set(LOCAL_RANKING_OUTPUT_FILENAMES.values())
    )
    assert len(result["written_files"]) == expected_written_count
    assert (output_dir / "Requirements_List.json").exists()
    assert (output_dir / "Roleplay_Requirements_Input.json").exists()
    assert (output_dir / "Roleplay_Handoff_Manifest.json").exists()
    assert (output_dir / "Employee_Feature_Matrix.json").exists()
    assert (output_dir / "Employee_Feature_Metadata.json").exists()
    assert (output_dir / "Requirements_Employee_Compare.json").exists()
    assert (output_dir / "Employee_Fit_Ranking.json").exists()
    assert (output_dir / "Team_Composition_Candidates.json").exists()
    assert (output_dir / "Team_Composition_Ranking.json").exists()
    assert (output_dir / "Roleplay_Simulation_Input_Packet.json").exists()
    assert build_run_summary(result)["written_file_count"] == expected_written_count
    assert build_run_summary(result)["feature_preprocessing_ready"] is True
    assert build_run_summary(result)["compare_result_count"] == 100
    assert build_run_summary(result)["roleplay_simulation_input_ready"] is True


def test_run_local_requirements_agent_can_run_roleplay_in_one_command(tmp_path) -> None:
    prd = tmp_path / "notification_prd.md"
    prd.write_text(
        "# Notification Center MVP\n\n"
        "Goal: Build notification center.\n\n"
        "## Functional Requirements\n"
        "- Users need push notification.\n"
        "- The MVP must ship in 6 weeks with budget 50000 USD.\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "requirements_outputs"
    roleplay_output_dir = tmp_path / "roleplay_outputs"

    result = run_local_requirements_agent(
        prd_path=prd,
        employee_data_dir=Path("datasets/raw"),
        llm_mode="stub",
        write_outputs=True,
        output_dir=output_dir,
        run_roleplay=True,
        roleplay_llm_mode="stub",
        roleplay_output_dir=roleplay_output_dir,
    )

    expected_written_count = len(
        set(REQUIREMENTS_OUTPUT_FILENAMES.values()) | set(LOCAL_RANKING_OUTPUT_FILENAMES.values())
    ) + len(ROLEPLAY_OUTPUT_FILENAMES)
    summary = build_run_summary(result)

    assert len(result["written_files"]) == expected_written_count
    assert summary["shadow_roleplay_executed"] is True
    assert summary["shadow_roleplay_status"] == "completed"
    assert summary["shadow_roleplay_output_ready"] is True
    assert summary["shadow_roleplay_written_file_count"] == len(ROLEPLAY_OUTPUT_FILENAMES)
    assert summary["shadow_roleplay_verdict"]
    assert (output_dir / "Roleplay_Simulation_Input_Packet.json").exists()
    assert (roleplay_output_dir / "Simulation_OUTPUT.json").exists()
