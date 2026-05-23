"""Vertex Gemini section extractor factory for Requirements Agent."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from backend.agents.requirements_agent.pipeline.llm_adapter import (
    DEFAULT_EXTRACTOR_PROMPT,
    LLM_MODE_VERTEX,
    LLMConfig,
    LLMInvoker,
    build_section_extractor,
)

JsonObject = dict[str, Any]


def build_vertex_requirements_extractor(
    *,
    config: LLMConfig | None = None,
    prompt_path: str | Path = DEFAULT_EXTRACTOR_PROMPT,
    invoker: LLMInvoker | None = None,
) -> Callable[[Mapping[str, Any]], Mapping[str, Any]]:
    """Create a Vertex-backed SectionExtractor callable.

    Tests may pass ``invoker`` to verify the contract without calling the
    network. Production/local finish runs should rely on env-backed config.
    """

    return build_section_extractor(
        mode=LLM_MODE_VERTEX,
        config=config,
        prompt_path=prompt_path,
        invoker=invoker,
    )
