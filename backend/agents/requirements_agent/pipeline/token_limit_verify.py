"""Token budget checks for Requirements Agent pipeline.

This module uses a deterministic token estimate so the pipeline can gate each
agent call before execution. It never summarizes or rewrites source text.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

JsonObject = dict[str, Any]

DEFAULT_RECOMMENDED_TOKEN_LIMIT = 4_000
DEFAULT_HARD_TOKEN_LIMIT = 5_000
DEFAULT_RESERVED_OUTPUT_TOKENS = 1_000


def estimate_tokens(text: str) -> int:
    """Return a conservative token estimate for mixed Korean/English text."""

    if not text:
        return 0
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return 0
    word_like_count = len(re.findall(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", normalized))
    char_based_count = math.ceil(len(normalized) / 4)
    non_ascii_count = sum(1 for char in normalized if ord(char) > 127)
    cjk_guard_count = math.ceil(non_ascii_count / 2)
    return max(word_like_count, char_based_count, cjk_guard_count)


def verify_token_budget(
    text: str,
    *,
    verify_id: str | None = None,
    target_agent: str = "Requirements_Agent",
    phase_name: str = "section_extraction",
    target_phase: str | None = None,
    recommended_limit: int = DEFAULT_RECOMMENDED_TOKEN_LIMIT,
    hard_limit: int = DEFAULT_HARD_TOKEN_LIMIT,
    reserved_output_tokens: int = DEFAULT_RESERVED_OUTPUT_TOKENS,
    included_context: Iterable[str] | None = None,
    excluded_context: Iterable[str] | None = None,
    source_ref: str | None = None,
) -> JsonObject:
    """Check whether input can be processed directly or needs chunking."""

    estimated_tokens = estimate_tokens(text)
    if estimated_tokens == 0:
        status = "empty_input"
        action = "reject_empty"
        notes = ["Input text is empty."]
    elif estimated_tokens <= recommended_limit:
        status = "within_recommended"
        action = "proceed"
        notes = ["Input is within the recommended token budget."]
    elif estimated_tokens <= hard_limit:
        status = "near_limit"
        action = "proceed_with_context_trim"
        notes = ["Input is above the recommended budget but below the hard limit."]
    else:
        status = "over_limit"
        action = "split_required"
        notes = ["Input exceeds the hard budget and must be split without summarizing."]

    target_phase = target_phase or phase_name
    included_context = list(included_context or ["section_text", "agent_instruction"])
    excluded_context = list(
        excluded_context or ["full_taxonomy", "full_rulebase", "raw_employee_db"]
    )
    return {
        "verify_id": verify_id or f"token_verify_{target_phase}",
        "target_agent": target_agent,
        "target_phase": target_phase,
        "estimated_input_tokens": estimated_tokens,
        "recommended_limit": recommended_limit,
        "hard_limit": hard_limit,
        "budget_status": status,
        "action": action,
        "included_context": included_context,
        "excluded_context": excluded_context,
        "source_ref": source_ref,
        "_meta": {
            "pipeline_phase": "token_limit_verify",
            "phase_name": phase_name,
            "status": status,
            "created_at": datetime.now(UTC).isoformat(),
        },
        "token_budget": {
            "estimated_tokens": estimated_tokens,
            "recommended_limit": recommended_limit,
            "hard_limit": hard_limit,
            "reserved_output_tokens": reserved_output_tokens,
            "available_input_tokens": hard_limit,
        },
        "preservation_policy": "preserve_raw_text_no_summary",
        "notes": notes,
    }


def verify_sections(
    sections: Iterable[Mapping[str, Any]],
    *,
    recommended_limit: int = DEFAULT_RECOMMENDED_TOKEN_LIMIT,
    hard_limit: int = DEFAULT_HARD_TOKEN_LIMIT,
    reserved_output_tokens: int = DEFAULT_RESERVED_OUTPUT_TOKENS,
) -> list[JsonObject]:
    """Run token budget verification for section dictionaries."""

    results: list[JsonObject] = []
    for section in sections:
        text = str(section.get("section_text", ""))
        section_id = str(section.get("section_id", ""))
        result = verify_token_budget(
            text,
            verify_id=f"token_verify_{section_id or 'section'}",
            phase_name="section_extraction",
            target_phase="Section Extractor",
            recommended_limit=recommended_limit,
            hard_limit=hard_limit,
            reserved_output_tokens=reserved_output_tokens,
            source_ref=section_id,
        )
        result["section_id"] = section_id
        result["section_title"] = section.get("section_title", "")
        result["chunk_id"] = section.get("chunk_id")
        results.append(result)
    return results


def requires_chunking(token_check: Mapping[str, Any]) -> bool:
    """Return True when a token check requires lossless chunking."""

    return (
        token_check.get("action") in {"chunk_required", "split_required"}
        or token_check.get("budget_status") == "over_limit"
    )
