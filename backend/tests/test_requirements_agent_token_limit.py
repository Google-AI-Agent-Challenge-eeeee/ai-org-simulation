from pathlib import Path

from backend.agents.requirements_agent.pipeline.section_splitter import (
    prepare_document_sections,
)

OUTPUT_DIR = Path("backend/agents/requirements_agent/outputs")


def _generated_outputs_exist() -> bool:
    return any(path.name != ".gitkeep" for path in OUTPUT_DIR.iterdir())


def test_prepare_document_sections_preserves_raw_text_and_refs() -> None:
    raw_text = (
        "# Notification Center MVP\r\n"
        "Goal: Validate notification delivery.\r\n\r\n"
        "## Functional Requirements\r\n"
        "- Users receive push notifications.\r\n"
        "- Users can mark notifications as read.\r\n\r\n"
        "## Budget\r\n"
        "Budget: 50000 USD\r\n"
    )

    prepared = prepare_document_sections(raw_text, document_id="prd_001")

    assert prepared["raw_text"] == raw_text
    assert prepared["document"]["raw_text_ref"] == "memory://requirements_agent/prd_001/raw_text"
    assert prepared["preservation_policy"] == "raw_text_is_preserved_and_not_summarized"
    assert len(prepared["semantic_sections"]) == 3
    assert all(
        section["source_range"]["start_char"] is not None for section in prepared["sections"]
    )


def test_long_sections_are_split_with_overlap_without_output_files() -> None:
    repeated_requirements = "\n\n".join(
        f"Requirement {index}: Users need push notification workflow and read state sync."
        for index in range(1, 31)
    )
    raw_text = f"# Notification Center MVP\n\n## Functional Requirements\n{repeated_requirements}"

    prepared = prepare_document_sections(
        raw_text,
        document_id="long_prd",
        recommended_limit=80,
        hard_limit=140,
        overlap_tokens=20,
    )
    chunks = [
        section for section in prepared["sections"] if section["parent_section_id"] == "sec_002"
    ]

    assert len(chunks) > 1
    assert chunks[0]["overlap_with_previous"] is False
    assert chunks[1]["overlap_with_previous"] is True
    assert chunks[0]["section_text"].split("\n\n")[-1] in chunks[1]["section_text"]
    assert all(check["budget_status"] != "over_limit" for check in prepared["section_token_checks"])
    assert not _generated_outputs_exist()
