"""Rule-based section coverage checks for Requirements Agent."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

JsonObject = dict[str, Any]

REQUIREMENT_MARKERS = (
    "must",
    "should",
    "need",
    "needs",
    "required",
    "requirement",
    "support",
    "include",
    "allow",
    "enable",
    "provide",
    "build",
    "implement",
    "deliver",
    "budget",
    "cost",
    "usd",
    "krw",
    "won",
    "week",
    "weeks",
    "deadline",
    "launch date",
    "mvp",
    "risk",
    "delay",
    "failure",
    "duplicate",
    "bottleneck",
    "security",
    "privacy",
    "compliance",
)
PROJECT_FIELD_PREFIXES = (
    "project",
    "name",
    "title",
    "goal",
    "objective",
    "purpose",
)


def check_coverage(
    sections: Iterable[Mapping[str, Any]],
    *,
    mapped_requirements: Mapping[str, Any] | None = None,
    extracted_requirements_draft: Mapping[str, Any] | None = None,
) -> JsonObject:
    """Calculate section coverage from section map and extraction evidence.

    This function is deterministic and does not summarize PRD text. It compares
    requirement-like lines/sentences in each section with extracted candidates,
    then uses mapped/review items only as additional downstream signals.
    """

    mapped_requirements = mapped_requirements or {}
    extracted_requirements_draft = extracted_requirements_draft or {}
    mapped_by_section = _evidence_items_by_section(_mapped_items(mapped_requirements))
    review_by_section = _evidence_items_by_section(_review_items(mapped_requirements))
    extracted_candidates = list(_draft_candidates(extracted_requirements_draft))
    extracted_by_section = _evidence_items_by_section(extracted_candidates)
    extracted_items_by_section = _items_by_section(extracted_candidates)
    mapped_items_by_section = _items_by_section(
        [*_mapped_items(mapped_requirements), *_review_items(mapped_requirements)]
    )

    section_results: list[JsonObject] = []
    for section in sections:
        section_id = section.get("section_id", "")
        mapped_ids = mapped_by_section.get(section_id, [])
        review_ids = review_by_section.get(section_id, [])
        extracted_ids = extracted_by_section.get(section_id, [])
        requirement_segments = _requirement_like_segments(section)
        represented_count = _represented_segment_count(
            requirement_segments,
            [
                *extracted_items_by_section.get(section_id, []),
                *mapped_items_by_section.get(section_id, []),
            ],
        )
        status = _section_status(
            requirement_segments=requirement_segments,
            represented_count=represented_count,
            mapped_ids=mapped_ids,
            review_ids=review_ids,
            extracted_ids=extracted_ids,
        )
        section_results.append(
            {
                "section_id": section_id,
                "section_title": section.get("section_title", ""),
                "status": status,
                "mapped_item_ids": _unique_strings([*mapped_ids, *extracted_ids, *review_ids]),
                "reason": _coverage_reason(
                    status=status,
                    requirement_segment_count=len(requirement_segments),
                    represented_count=represented_count,
                    mapped_ids=mapped_ids,
                    review_ids=review_ids,
                    extracted_ids=extracted_ids,
                ),
            }
        )

    return {
        "overall_status": _overall_status(section_results),
        "sections": section_results,
        "notes": _coverage_notes(section_results),
    }


def _mapped_items(mapped_requirements: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    groups = ("mapped_features", "constraints", "risk_factors")
    for group in groups:
        yield from mapped_requirements.get(group, [])


def _review_items(mapped_requirements: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    groups = ("unknown_requirements", "conflict_items", "low_confidence_items")
    for group in groups:
        yield from mapped_requirements.get(group, [])


def _draft_candidates(draft: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    merged_candidates = list(draft.get("merged_requirement_candidates", []))
    if merged_candidates:
        yield from merged_candidates
        return
    for result in draft.get("section_results", []):
        for group in (
            "raw_features",
            "raw_roles",
            "raw_skills",
            "raw_constraints",
            "raw_risk_candidates",
        ):
            yield from result.get(group, [])


def _evidence_items_by_section(items: Iterable[Mapping[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for item in items:
        item_id = _item_id(item)
        for evidence in item.get("source_evidence", []):
            section_id = evidence.get("section_id")
            if section_id and item_id not in result[section_id]:
                result[section_id].append(item_id)
    return dict(result)


def _items_by_section(items: Iterable[Mapping[str, Any]]) -> dict[str, list[JsonObject]]:
    result: dict[str, list[JsonObject]] = defaultdict(list)
    for item in items:
        normalized_item = dict(item)
        for evidence in item.get("source_evidence", []):
            section_id = evidence.get("section_id")
            if section_id:
                result[section_id].append(normalized_item)
    return dict(result)


def _item_id(item: Mapping[str, Any]) -> str:
    return str(
        item.get("candidate_id")
        or item.get("item_id")
        or item.get("feature_key")
        or item.get("risk_key")
        or item.get("text")
        or "unknown_item"
    )


def _section_status(
    *,
    requirement_segments: list[str],
    represented_count: int,
    mapped_ids: list[str],
    review_ids: list[str],
    extracted_ids: list[str],
) -> str:
    if not requirement_segments:
        return "partial" if extracted_ids or mapped_ids or review_ids else "covered"
    if represented_count == 0 and not (mapped_ids or review_ids or extracted_ids):
        return "missing"
    if represented_count >= len(requirement_segments) and not review_ids:
        return "covered"
    if represented_count or mapped_ids or review_ids or extracted_ids:
        return "partial"
    return "missing"


def _coverage_reason(
    *,
    status: str,
    requirement_segment_count: int,
    represented_count: int,
    mapped_ids: list[str],
    review_ids: list[str],
    extracted_ids: list[str],
) -> str:
    prefix = (
        f"{represented_count}/{requirement_segment_count} requirement-like "
        "section signal(s) are reflected."
    )
    if requirement_segment_count == 0:
        if status == "covered":
            return "Section has no requirement-like signals; no extraction was required."
        return "Section has extraction or mapping evidence but no requirement-like section signal."
    if status == "covered":
        if mapped_ids:
            return f"{prefix} Section has mapped requirements with source evidence."
        return f"{prefix} Section has extracted requirement evidence."
    if status == "partial":
        if review_ids:
            return (
                f"{prefix} Section has requirements that need Human Confirm or conflict resolution."
            )
        if extracted_ids and not mapped_ids:
            return (
                f"{prefix} Section has extracted candidates but no confirmed taxonomy mapping yet."
            )
        return f"{prefix} Section is only partially represented by extraction or mapping evidence."
    if extracted_ids:
        return (
            f"{prefix} Section has extraction evidence but requirement signals are still missing."
        )
    return f"{prefix} No mapped or extracted requirement evidence found for this section."


def _overall_status(section_results: list[JsonObject]) -> str:
    if not section_results:
        return "missing"
    statuses = {section["status"] for section in section_results}
    if statuses == {"covered"}:
        return "covered"
    if statuses == {"missing"}:
        return "missing"
    return "partial"


def _coverage_notes(section_results: list[JsonObject]) -> list[str]:
    missing_count = sum(1 for section in section_results if section["status"] == "missing")
    partial_count = sum(1 for section in section_results if section["status"] == "partial")
    notes: list[str] = []
    if missing_count:
        notes.append(f"{missing_count} section(s) have no mapped or extracted evidence.")
    if partial_count:
        notes.append(f"{partial_count} section(s) require additional validation or Human Confirm.")
    if not notes:
        notes.append("All sections are covered by mapped requirements.")
    return notes


def _requirement_like_segments(section: Mapping[str, Any]) -> list[str]:
    segments: list[str] = []
    for line in str(section.get("section_text", "")).splitlines():
        clean = _clean_segment_text(line)
        if _is_requirement_like(clean):
            segments.append(clean)
    if segments:
        return _unique_strings(segments)

    for sentence in _sentence_segments(str(section.get("section_text", ""))):
        clean = _clean_segment_text(sentence)
        if _is_requirement_like(clean):
            segments.append(clean)
    return _unique_strings(segments)


def _represented_segment_count(
    requirement_segments: Iterable[str],
    items: Iterable[Mapping[str, Any]],
) -> int:
    item_texts = _item_texts(items)
    return sum(
        1
        for segment in requirement_segments
        if any(_text_match_score(segment, item_text) >= 0.5 for item_text in item_texts)
    )


def _item_texts(items: Iterable[Mapping[str, Any]]) -> list[str]:
    texts: list[str] = []
    for item in items:
        for key in ("text", "raw_text", "standard_name", "constraint_key", "risk_key"):
            if item.get(key):
                texts.append(str(item[key]))
        for evidence in item.get("source_evidence", []):
            if evidence.get("text"):
                texts.append(str(evidence["text"]))
    return _unique_strings(texts)


def _sentence_segments(text: str) -> list[str]:
    matches = re.findall(r"[^.!?\n]+(?:[.!?]|$)", text)
    return [match.strip() for match in matches if match.strip()]


def _clean_segment_text(text: str) -> str:
    clean = text.strip()
    clean = re.sub(r"^#{1,6}\s+", "", clean)
    clean = re.sub(r"^[-*]\s+", "", clean)
    clean = re.sub(r"^\d+(\.\d+)*[.)]\s+", "", clean)
    return clean.strip()


def _is_requirement_like(text: str) -> bool:
    if not text or len(text) < 8:
        return False
    normalized = _normalize_text(text)
    if _is_heading_like(text):
        return False
    if any(normalized.startswith(f"{prefix}:") for prefix in PROJECT_FIELD_PREFIXES):
        return False
    return any(marker in normalized for marker in REQUIREMENT_MARKERS)


def _is_heading_like(text: str) -> bool:
    if text.endswith(":") and len(text) <= 80:
        return True
    return len(text.split()) <= 4 and not re.search(r"\d", text) and not re.search(r"[.!?]$", text)


def _text_match_score(left: str, right: str) -> float:
    left_normalized = _normalize_text(left)
    right_normalized = _normalize_text(right)
    if not left_normalized or not right_normalized:
        return 0.0
    if left_normalized in right_normalized or right_normalized in left_normalized:
        return 1.0
    left_tokens = _meaningful_tokens(left_normalized)
    right_tokens = _meaningful_tokens(right_normalized)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _meaningful_tokens(text: str) -> set[str]:
    stopwords = {
        "a",
        "an",
        "and",
        "are",
        "be",
        "for",
        "from",
        "in",
        "is",
        "it",
        "must",
        "need",
        "needs",
        "of",
        "or",
        "required",
        "should",
        "support",
        "the",
        "to",
        "users",
        "with",
    }
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9_]+", text)
        if len(token) > 2 and token not in stopwords
    }


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def _unique_strings(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
