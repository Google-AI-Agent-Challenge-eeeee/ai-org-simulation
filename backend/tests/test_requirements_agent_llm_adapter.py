import pytest

from backend.agents.requirements_agent.pipeline.extraction_runner import (
    build_section_extraction_payload,
)
from backend.agents.requirements_agent.pipeline.llm_adapter import (
    LLM_MODE_GEMINI_API,
    LLM_MODE_STUB,
    LLM_MODE_VERTEX,
    LLMConfig,
    LLMConfigurationError,
    build_section_extractor,
    call_llm_for_json,
    normalize_llm_mode,
    parse_json_object,
)
from backend.agents.requirements_agent.pipeline.section_splitter import (
    prepare_document_sections,
)


def test_parse_json_object_accepts_fenced_llm_response() -> None:
    parsed = parse_json_object(
        """
        The answer is:

        ```json
        {"section_id": "sec_001", "raw_features": [], "confidence": 0.91}
        ```
        """
    )

    assert parsed["section_id"] == "sec_001"
    assert parsed["confidence"] == 0.91


def test_stub_section_extractor_uses_rule_based_bootstrap() -> None:
    prepared = prepare_document_sections(
        "# Notification Center MVP\n\n"
        "## Functional Requirements\n"
        "Users need push notification and notification preferences.",
        document_id="prd_llm_stub",
    )
    payload = build_section_extraction_payload(prepared["document"], prepared["sections"][1])
    extractor = build_section_extractor(
        config=LLMConfig(mode=LLM_MODE_STUB),
        rulebase={
            "aliases": {
                "push notification": {
                    "feature_key": "notification_center",
                    "confidence": 0.97,
                }
            }
        },
    )

    result = extractor(payload)

    assert result["raw_features"]
    assert result["confidence"] > 0


def test_call_llm_for_json_uses_fake_invoker_without_network() -> None:
    def fake_invoker(prompt, payload, config):
        assert "SECTION_PAYLOAD_JSON" in prompt
        assert payload["section"]["section_id"] == "sec_001"
        assert config.mode == LLM_MODE_VERTEX
        return {
            "section_id": "sec_001",
            "section_title": "Functional Requirements",
            "raw_features": [],
            "raw_roles": [],
            "raw_skills": [],
            "raw_constraints": [],
            "raw_risk_candidates": [],
            "confidence": 0.9,
        }

    result = call_llm_for_json(
        "SECTION_PAYLOAD_JSON:\n{}",
        {"section": {"section_id": "sec_001"}},
        LLMConfig(mode=LLM_MODE_VERTEX, project_id="project"),
        invoker=fake_invoker,
    )

    assert result["section_id"] == "sec_001"


def test_vertex_mode_requires_project_id_before_network_call() -> None:
    with pytest.raises(LLMConfigurationError):
        call_llm_for_json(
            "prompt",
            {},
            LLMConfig(mode=LLM_MODE_VERTEX, project_id=None),
        )


def test_gemini_api_mode_requires_api_key_before_network_call() -> None:
    with pytest.raises(LLMConfigurationError):
        call_llm_for_json(
            "prompt",
            {},
            LLMConfig(mode=LLM_MODE_GEMINI_API, gemini_api_key=None),
        )


def test_llm_mode_aliases() -> None:
    assert normalize_llm_mode("stub") == LLM_MODE_STUB
    assert normalize_llm_mode("vertex") == LLM_MODE_VERTEX
    assert normalize_llm_mode("gemini") == LLM_MODE_GEMINI_API
    assert normalize_llm_mode("api_key") == LLM_MODE_GEMINI_API
