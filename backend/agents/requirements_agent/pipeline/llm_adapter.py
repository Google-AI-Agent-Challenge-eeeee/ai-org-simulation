"""LLM adapter boundary for Requirements Agent local finish runs."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from backend.agents.requirements_agent.pipeline.extraction_runner import (
    rule_based_bootstrap_extractor,
)

JsonObject = dict[str, Any]
LLMInvoker = Callable[[str, Mapping[str, Any], "LLMConfig"], str | Mapping[str, Any]]

REQUIREMENTS_AGENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXTRACTOR_PROMPT = REQUIREMENTS_AGENT_ROOT / "prompts" / "requirements_extractor_prompt.md"
DEFAULT_MAPPING_PROMPT = REQUIREMENTS_AGENT_ROOT / "prompts" / "requirements_mapping_prompt.md"

LLM_MODE_STUB = "stub"
LLM_MODE_VERTEX = "vertex"
LLM_MODE_GEMINI_API = "gemini_api"
SUPPORTED_LLM_MODES = {LLM_MODE_STUB, LLM_MODE_VERTEX, LLM_MODE_GEMINI_API}


class LLMAdapterError(RuntimeError):
    """Base error for LLM adapter failures."""


class LLMConfigurationError(LLMAdapterError):
    """Raised when LLM mode or credentials are not configured."""


class LLMResponseError(LLMAdapterError):
    """Raised when the LLM response cannot be parsed as the expected JSON object."""


@dataclass(frozen=True)
class LLMConfig:
    """Runtime LLM settings. Secret values must never be logged."""

    mode: str = LLM_MODE_STUB
    project_id: str | None = None
    google_application_credentials: str | None = None
    vertex_location: str = "asia-northeast3"
    vertex_model: str = "gemini-2.5-pro"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-pro"
    temperature: float = 0.0

    @classmethod
    def from_env(cls, *, mode: str | None = None) -> LLMConfig:
        load_dotenv()
        env_mode = mode or os.getenv("LLM_MODE", LLM_MODE_STUB)
        return cls(
            mode=normalize_llm_mode(env_mode),
            project_id=_empty_to_none(os.getenv("GCP_PROJECT_ID")),
            google_application_credentials=_empty_to_none(
                os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            ),
            vertex_location=os.getenv("VERTEX_LOCATION", "asia-northeast3"),
            vertex_model=os.getenv("VERTEX_MODEL", "gemini-2.5-pro"),
            gemini_api_key=_empty_to_none(os.getenv("GEMINI_API_KEY")),
            gemini_model=os.getenv("GEMINI_MODEL", os.getenv("VERTEX_MODEL", "gemini-2.5-pro")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
        )

    def safe_summary(self) -> JsonObject:
        return {
            "mode": self.mode,
            "project_id_configured": bool(self.project_id),
            "google_application_credentials_configured": bool(self.google_application_credentials),
            "vertex_location": self.vertex_location,
            "vertex_model": self.vertex_model,
            "gemini_api_key_configured": bool(self.gemini_api_key),
            "gemini_model": self.gemini_model,
            "temperature": self.temperature,
        }


def normalize_llm_mode(mode: str) -> str:
    normalized = str(mode or LLM_MODE_STUB).strip().casefold()
    aliases = {
        "gemini": LLM_MODE_GEMINI_API,
        "google_genai": LLM_MODE_GEMINI_API,
        "api_key": LLM_MODE_GEMINI_API,
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in SUPPORTED_LLM_MODES:
        raise LLMConfigurationError(
            f"Unsupported LLM mode '{mode}'. Use one of: {', '.join(sorted(SUPPORTED_LLM_MODES))}."
        )
    return normalized


def build_section_extractor(
    *,
    mode: str | None = None,
    config: LLMConfig | None = None,
    prompt_path: str | Path = DEFAULT_EXTRACTOR_PROMPT,
    rulebase: Mapping[str, Any] | None = None,
    invoker: LLMInvoker | None = None,
) -> Callable[[Mapping[str, Any]], Mapping[str, Any]]:
    """Build a SectionExtractor callable for the pipeline."""

    resolved_config = config or LLMConfig.from_env(mode=mode)
    if resolved_config.mode == LLM_MODE_STUB:
        return lambda payload: rule_based_bootstrap_extractor(payload, rulebase=rulebase or {})

    prompt_template = load_prompt(prompt_path)

    def extractor(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        prompt = render_section_extraction_prompt(prompt_template, payload)
        return call_llm_for_json(prompt, payload, resolved_config, invoker=invoker)

    return extractor


def build_mapping_suggester(
    *,
    config: LLMConfig,
    prompt_path: str | Path = DEFAULT_MAPPING_PROMPT,
    invoker: LLMInvoker | None = None,
) -> Callable[[Mapping[str, Any]], Mapping[str, Any]] | None:
    """Build an LLM-assisted taxonomy mapping suggester.

    The suggester proposes mappings only. The taxonomy matcher remains the
    validator and rejects suggestions that do not match existing reference keys.
    """

    if config.mode == LLM_MODE_STUB:
        return None

    prompt_template = load_prompt(prompt_path)

    def suggester(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        prompt = render_mapping_prompt(prompt_template, payload)
        return call_llm_for_json(prompt, payload, config, invoker=invoker)

    return suggester


def call_llm_for_json(
    prompt: str,
    payload: Mapping[str, Any],
    config: LLMConfig,
    *,
    invoker: LLMInvoker | None = None,
) -> JsonObject:
    """Call the configured LLM and parse a JSON object response."""

    if invoker is not None:
        raw_response = invoker(prompt, payload, config)
    elif config.mode == LLM_MODE_VERTEX:
        raw_response = _call_vertex(prompt, config)
    elif config.mode == LLM_MODE_GEMINI_API:
        raw_response = _call_gemini_api(prompt, config)
    else:
        raise LLMConfigurationError(f"LLM mode '{config.mode}' cannot call a remote model.")

    if isinstance(raw_response, Mapping):
        return dict(raw_response)
    if not isinstance(raw_response, str):
        raise LLMResponseError("LLM response must be a JSON string or mapping.")
    return parse_json_object(raw_response)


def load_prompt(prompt_path: str | Path) -> str:
    path = Path(prompt_path)
    if not path.exists():
        raise LLMConfigurationError(f"Prompt file does not exist: {path}")
    return path.read_text(encoding="utf-8")


def render_section_extraction_prompt(
    prompt_template: str,
    payload: Mapping[str, Any],
) -> str:
    """Render the extractor prompt with the one-section payload."""

    return (
        prompt_template.rstrip()
        + "\n\n"
        + "SECTION_PAYLOAD_JSON:\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n\n"
        + "Return only one JSON object that matches the section extraction contract."
    )


def render_mapping_prompt(
    prompt_template: str,
    payload: Mapping[str, Any],
) -> str:
    """Render the suggested-mapping prompt with unresolved candidates."""

    return (
        prompt_template.rstrip()
        + "\n\n"
        + "MAPPING_PAYLOAD_JSON:\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n\n"
        + "Return only one JSON object with a suggested_mappings array."
    )


def parse_json_object(raw_response: str) -> JsonObject:
    """Parse JSON from a plain or fenced LLM response."""

    text = raw_response.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMResponseError(f"LLM response was not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise LLMResponseError("LLM response JSON must be an object.")
    return payload


def _call_vertex(prompt: str, config: LLMConfig) -> str:
    if not config.project_id:
        raise LLMConfigurationError("GCP_PROJECT_ID is required for LLM_MODE=vertex.")
    if config.google_application_credentials:
        credentials_path = Path(config.google_application_credentials)
        if not credentials_path.exists():
            raise LLMConfigurationError("GOOGLE_APPLICATION_CREDENTIALS points to a missing file.")

    try:
        import vertexai
        from vertexai.generative_models import GenerationConfig, GenerativeModel
    except ModuleNotFoundError as exc:
        raise LLMConfigurationError(
            "Vertex AI dependencies are not installed. Install google-cloud-aiplatform "
            "before running LLM_MODE=vertex."
        ) from exc

    vertexai.init(project=config.project_id, location=config.vertex_location)
    model = GenerativeModel(config.vertex_model)
    response = model.generate_content(
        prompt,
        generation_config=GenerationConfig(
            temperature=config.temperature,
            response_mime_type="application/json",
        ),
    )
    return str(getattr(response, "text", "") or "")


def _call_gemini_api(prompt: str, config: LLMConfig) -> str:
    if not config.gemini_api_key:
        raise LLMConfigurationError("GEMINI_API_KEY is required for LLM_MODE=gemini_api.")
    try:
        from google import genai
    except ModuleNotFoundError as exc:
        raise LLMConfigurationError(
            "Google GenAI dependencies are not installed. Install google-genai "
            "before running LLM_MODE=gemini_api."
        ) from exc

    client = genai.Client(api_key=config.gemini_api_key)
    response = client.models.generate_content(
        model=config.gemini_model,
        contents=prompt,
        config={
            "temperature": config.temperature,
            "response_mime_type": "application/json",
        },
    )
    return str(getattr(response, "text", "") or "")


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
