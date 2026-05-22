import pytest

from backend.agents.requirements_agent.pipeline.extraction_runner import (
    SectionExtractionError,
    build_section_extraction_payload,
    extract_single_section,
    merge_section_results,
    run_section_extraction,
)
from backend.agents.requirements_agent.pipeline.section_splitter import (
    prepare_document_sections,
)


def test_build_section_extraction_payload_uses_one_raw_section() -> None:
    prepared = prepare_document_sections(
        "# Notification Center MVP\n\n"
        "## Functional Requirements\n"
        "Users need push notification and read state sync.",
        document_id="prd_001",
    )
    section = prepared["sections"][1]

    payload = build_section_extraction_payload(prepared["document"], section)

    assert payload["document"]["raw_text_ref"] == "memory://requirements_agent/prd_001/raw_text"
    assert payload["section"]["section_text"] == section["section_text"]
    assert payload["output_schema_hint"] == (
        "extracted_requirements_draft_schema.section_extraction_result"
    )
    assert payload["phase_boundaries"]["build_requirements_list"] is False
    assert "Requirements_List" not in payload


def test_extract_single_section_normalizes_llm_candidates_with_source_evidence() -> None:
    prepared = prepare_document_sections(
        "# Notification Center MVP\n\n"
        "## Functional Requirements\n"
        "Users need push notification. OAuth login is required. "
        "Duplicate notification delivery is a risk.",
        document_id="prd_002",
    )
    section = prepared["sections"][1]

    def fake_llm(payload):
        return {
            "section_id": payload["section"]["section_id"],
            "section_title": payload["section"]["section_title"],
            "raw_features": [
                {
                    "text": "Users need push notification.",
                    "item_type": "feature",
                    "source_evidence": [
                        {
                            "evidence_id": "ev_001",
                            "text": "Users need push notification.",
                        }
                    ],
                    "confidence": 0.94,
                }
            ],
            "raw_skills": [{"text": "OAuth", "confidence": 0.9}],
            "constraints": [],
            "risk_candidates": [
                {
                    "text": "Duplicate notification delivery is a risk.",
                    "confidence": 0.82,
                }
            ],
            "confidence": 0.9,
        }

    result = extract_single_section(prepared["document"], section, extractor=fake_llm)

    assert result["raw_features"][0]["candidate_id"].startswith("sec_002_feature_")
    assert result["raw_features"][0]["source_evidence"][0]["document_id"] == "prd_002"
    assert result["raw_skills"][0]["source_evidence"][0]["text"] == "OAuth login is required."
    assert result["raw_risk_candidates"][0]["item_type"] == "risk"
    assert result["confidence"] > 0.8


def test_run_section_extraction_creates_draft_only_not_requirements_list() -> None:
    prepared = prepare_document_sections(
        "# Notification Center MVP\n\n"
        "## Functional Requirements\n"
        "Users need push notification and notification preferences. "
        "The MVP must ship in 6 weeks. Duplicate notification delivery is a risk.",
        document_id="prd_003",
    )
    rulebase = {
        "aliases": {
            "push notification": {"feature_key": "notification_center", "confidence": 0.97}
        },
        "constraint_aliases": {"MVP": {"constraint_key": "short_timeline", "confidence": 0.76}},
    }

    draft = run_section_extraction(prepared, rulebase=rulebase)

    assert draft["_meta"]["pipeline_phase"] == "chunk_result_merge"
    assert "required_features" not in draft
    assert "project_name" not in draft
    assert len(draft["section_results"]) == len(prepared["sections"])
    assert draft["merged_requirement_candidates"]
    assert all(candidate["source_evidence"] for candidate in draft["merged_requirement_candidates"])


def test_section_extractor_rejects_final_requirements_list_fields() -> None:
    prepared = prepare_document_sections(
        "# Notification Center MVP\n\n## Functional Requirements\nUsers need notification.",
        document_id="prd_004",
    )

    def invalid_llm(_payload):
        return {
            "section_id": "sec_002",
            "required_features": [],
            "project_name": "Notification Center MVP",
        }

    with pytest.raises(SectionExtractionError):
        run_section_extraction(prepared, extractor=invalid_llm)


def test_merge_section_results_deduplicates_and_preserves_evidence_map() -> None:
    section_results = [
        {
            "section_id": "sec_001_chunk_001",
            "section_title": "Functional Requirements / Chunk 1",
            "raw_features": [
                {
                    "candidate_id": "c_001",
                    "item_type": "feature",
                    "text": "Users need push notification.",
                    "normalized_text": "users need push notification.",
                    "source_evidence": [
                        {
                            "evidence_id": "ev_001",
                            "document_id": "prd_merge",
                            "section_id": "sec_001_chunk_001",
                            "text": "Users need push notification.",
                        }
                    ],
                    "confidence": 0.92,
                }
            ],
            "raw_roles": [],
            "raw_skills": [],
            "raw_constraints": [],
            "raw_risk_candidates": [],
            "confidence": 0.92,
        },
        {
            "section_id": "sec_001_chunk_002",
            "section_title": "Functional Requirements / Chunk 2",
            "raw_features": [
                {
                    "candidate_id": "c_002",
                    "item_type": "feature",
                    "text": "Users need push notification.",
                    "normalized_text": "users need push notification.",
                    "source_evidence": [
                        {
                            "evidence_id": "ev_002",
                            "document_id": "prd_merge",
                            "section_id": "sec_001_chunk_002",
                            "text": "Push notification workflow continues in the next chunk.",
                        }
                    ],
                    "confidence": 0.9,
                }
            ],
            "raw_roles": [],
            "raw_skills": [],
            "raw_constraints": [],
            "raw_risk_candidates": [],
            "confidence": 0.9,
        },
    ]

    merge_result = merge_section_results(section_results)

    assert merge_result["candidate_count"] == 2
    assert len(merge_result["merged_requirement_candidates"]) == 1
    merged = merge_result["merged_requirement_candidates"][0]
    assert merged["status"] == "merged"
    assert {item["evidence_id"] for item in merged["source_evidence"]} == {"ev_001", "ev_002"}
    assert merge_result["duplicate_items"] == [
        {
            "kept_candidate_id": "c_001",
            "merged_candidate_ids": ["c_002"],
            "reason": "Same normalized text and item_type across sections/chunks.",
        }
    ]
    assert merge_result["evidence_map"]["by_candidate_id"]["c_001"] == ["ev_001", "ev_002"]
    assert merge_result["evidence_map"]["by_section_id"]["sec_001_chunk_002"] == ["ev_002"]


def test_merge_section_results_keeps_conflicts_for_human_confirm() -> None:
    section_results = [
        {
            "section_id": "sec_001",
            "section_title": "Functional Requirements",
            "raw_features": [
                {
                    "candidate_id": "c_positive",
                    "item_type": "feature",
                    "text": "Users must support push notification.",
                    "source_evidence": [
                        {
                            "evidence_id": "ev_positive",
                            "section_id": "sec_001",
                            "text": "Users must support push notification.",
                        }
                    ],
                    "confidence": 0.91,
                },
                {
                    "candidate_id": "c_negative",
                    "item_type": "feature",
                    "text": "Push notification is out of scope.",
                    "source_evidence": [
                        {
                            "evidence_id": "ev_negative",
                            "section_id": "sec_001",
                            "text": "Push notification is out of scope.",
                        }
                    ],
                    "confidence": 0.9,
                },
            ],
            "raw_roles": [],
            "raw_skills": [],
            "raw_constraints": [],
            "raw_risk_candidates": [],
            "confidence": 0.9,
        }
    ]

    merge_result = merge_section_results(section_results)

    assert len(merge_result["merged_requirement_candidates"]) == 2
    assert len(merge_result["conflict_items"]) == 1
    assert merge_result["conflict_items"][0]["status"] == "manual_review_required"
    assert set(merge_result["conflict_items"][0]["candidate_ids"]) == {
        "c_positive",
        "c_negative",
    }
    assert {item["status"] for item in merge_result["merged_requirement_candidates"]} == {
        "conflict"
    }
