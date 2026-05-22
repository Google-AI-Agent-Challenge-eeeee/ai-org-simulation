"""Section Requirements Extractor runner for Requirements Agent.

The real LLM call is injected as a callable. This module owns the phase
contract around that call: each input is one raw PRD section/chunk, each output
is a section-level candidate result, and no final Requirements_List fields are
allowed at this stage.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

JsonObject = dict[str, Any]
SectionExtractor = Callable[[Mapping[str, Any]], Mapping[str, Any]]
ProgressLogger = Callable[[str, Mapping[str, Any]], None]

CANDIDATE_GROUPS = (
    "raw_features",
    "raw_roles",
    "raw_skills",
    "raw_constraints",
    "raw_risk_candidates",
)
ITEM_TYPE_BY_GROUP = {
    "raw_features": "feature",
    "raw_roles": "role",
    "raw_skills": "skill",
    "raw_constraints": "constraint",
    "raw_risk_candidates": "risk",
}
ALIASED_GROUPS = {
    "features": "raw_features",
    "skills": "raw_skills",
    "constraints": "raw_constraints",
    "risk_candidates": "raw_risk_candidates",
    "risks": "raw_risk_candidates",
    "roles": "raw_roles",
}
FINAL_OUTPUT_KEYS = {
    "project_name",
    "project_goal",
    "required_features",
    "required_roles",
    "required_skills",
    "selected_employee_columns",
    "column_weights",
    "column_priority_order",
    "weighting_reason",
    "coverage_check",
}
SKILL_TERMS = (
    "OAuth",
    "JWT",
    "API integration",
    "external API",
    "webhook",
    "payment API",
    "push notification",
    "database",
    "security",
    "privacy",
    "monitoring",
    "logging",
    "accessibility",
    "performance testing",
    "mobile",
    "responsive",
    "object storage",
    "CI/CD",
)
ROLE_TERMS = (
    "backend engineer",
    "frontend engineer",
    "web frontend engineer",
    "mobile engineer",
    "qa engineer",
    "designer",
    "product designer",
    "infrastructure engineer",
    "project manager",
)
RISK_TERMS = (
    "risk",
    "delay",
    "failure",
    "duplicate",
    "bottleneck",
    "permission bypass",
    "data loss",
    "outage",
    "regression",
    "missing stakeholder",
)
CONSTRAINT_PATTERNS = (
    r"\b\d+\s*(?:week|weeks|wk|wks|month|months)\b",
    r"\b(?:budget|cost|usd|krw|won)\b",
    r"\b(?:deadline|launch date|fixed date|mvp|compliance|privacy|security)\b",
)


class SectionExtractionError(ValueError):
    """Raised when an extractor response violates the Phase 2 contract."""


def run_section_extraction(
    prepared_document: Mapping[str, Any],
    *,
    extractor: SectionExtractor | None = None,
    rulebase: Mapping[str, Any] | None = None,
    draft_id: str = "extracted_requirements_draft",
    project_id: str | None = None,
    extractor_prompt_version: str = "requirements_extractor_prompt.md@0.1.0",
    low_confidence_threshold: float = 0.7,
    progress_logger: ProgressLogger | None = None,
) -> JsonObject:
    """Run Section Requirements Extraction and merge raw candidates.

    This returns the Extracted_Requirements_Draft object used by the next
    phases. It does not build Requirements_List.json and it does not write any
    output files.
    """

    extractor = extractor or (
        lambda payload: rule_based_bootstrap_extractor(payload, rulebase=rulebase or {})
    )
    document = dict(prepared_document.get("document", {}))
    sections = list(prepared_document.get("sections", []))
    section_results = []
    _log_progress(
        progress_logger,
        "section_extraction_start",
        section_count=len(sections),
        document_id=document.get("document_id", ""),
    )
    for index, section in enumerate(sections, start=1):
        section_started_at = time.perf_counter()
        _log_progress(
            progress_logger,
            "section_extraction_item_start",
            index=index,
            total=len(sections),
            section_id=section.get("section_id", ""),
            section_title=section.get("section_title", ""),
            chunk_id=section.get("chunk_id"),
            estimated_tokens=section.get("estimated_tokens", 0),
        )
        payload = build_section_extraction_payload(document, section)
        try:
            raw_result = dict(extractor(payload))
            _ensure_not_final_output(raw_result)
            normalized_result = _normalize_section_result(raw_result, section, document)
        except Exception as exc:
            _log_progress(
                progress_logger,
                "section_extraction_item_failed",
                index=index,
                total=len(sections),
                section_id=section.get("section_id", ""),
                elapsed_seconds=round(time.perf_counter() - section_started_at, 2),
                error=type(exc).__name__,
            )
            raise
        section_results.append(normalized_result)
        _log_progress(
            progress_logger,
            "section_extraction_item_done",
            index=index,
            total=len(sections),
            section_id=section.get("section_id", ""),
            elapsed_seconds=round(time.perf_counter() - section_started_at, 2),
            candidate_count=_section_candidate_count(normalized_result),
            confidence=normalized_result.get("confidence", 0.0),
        )

    _log_progress(progress_logger, "section_extraction_merge_start", section_count=len(sections))
    merge_result = merge_section_results(
        section_results,
        low_confidence_threshold=low_confidence_threshold,
    )
    candidates = merge_result["merged_requirement_candidates"]
    status = "completed" if candidates else "draft"
    result = {
        "_meta": {
            "draft_id": draft_id,
            "project_id": project_id,
            "pipeline_phase": "chunk_result_merge",
            "status": status,
            "created_at": datetime.now(UTC).isoformat(),
            "extractor_prompt_version": extractor_prompt_version,
        },
        "document": {
            "document_id": document.get("document_id", ""),
            "document_type": document.get("document_type", "prd"),
            "source_uri": document.get("source_uri"),
            "raw_text_ref": document.get("raw_text_ref", ""),
            "clean_text_ref": document.get("clean_text_ref"),
            "cleaning_notes": list(document.get("cleaning_notes", [])),
        },
        "sections": list(prepared_document.get("sections", [])),
        "section_results": section_results,
        "merged_requirement_candidates": candidates,
        "duplicate_items": merge_result["duplicate_items"],
        "conflict_items": merge_result["conflict_items"],
        "low_confidence_items": merge_result["low_confidence_items"],
        "evidence_map": merge_result["evidence_map"],
        "extraction_stats": {
            "section_count": len(section_results),
            "candidate_count": merge_result["candidate_count"],
            "merged_candidate_count": len(candidates),
            "low_confidence_count": len(merge_result["low_confidence_items"]),
            "conflict_count": len(merge_result["conflict_items"]),
            "evidence_count": merge_result["evidence_count"],
        },
    }
    _log_progress(
        progress_logger,
        "section_extraction_done",
        section_count=len(section_results),
        candidate_count=merge_result["candidate_count"],
        merged_candidate_count=len(candidates),
        low_confidence_count=len(merge_result["low_confidence_items"]),
        conflict_count=len(merge_result["conflict_items"]),
    )
    return result


def build_section_extraction_payload(
    document: Mapping[str, Any],
    section: Mapping[str, Any],
) -> JsonObject:
    """Build the one-section LLM input payload for Phase 2."""

    return {
        "document": {
            "document_id": document.get("document_id", ""),
            "document_type": document.get("document_type", "prd"),
            "raw_text_ref": document.get("raw_text_ref", ""),
        },
        "section": {
            "section_id": section.get("section_id", ""),
            "section_title": section.get("section_title", ""),
            "chunk_id": section.get("chunk_id"),
            "section_text": section.get("section_text", ""),
            "source_range": dict(section.get("source_range", {})),
            "estimated_tokens": section.get("estimated_tokens", 0),
            "overlap_with_previous": section.get("overlap_with_previous", False),
        },
        "prompt_name": "requirements_extractor_prompt.md",
        "output_schema_hint": ("extracted_requirements_draft_schema.section_extraction_result"),
        "expected_output_groups": list(CANDIDATE_GROUPS),
        "phase_boundaries": {
            "build_requirements_list": False,
            "taxonomy_matching": False,
            "employee_column_selection": False,
            "column_weighting": False,
        },
    }


def extract_single_section(
    document: Mapping[str, Any],
    section: Mapping[str, Any],
    *,
    extractor: SectionExtractor,
) -> JsonObject:
    """Extract and normalize candidates for one section."""

    payload = build_section_extraction_payload(document, section)
    raw_result = dict(extractor(payload))
    _ensure_not_final_output(raw_result)
    return _normalize_section_result(raw_result, section, document)


def merge_section_results(
    section_results: Iterable[Mapping[str, Any]],
    *,
    low_confidence_threshold: float = 0.7,
) -> JsonObject:
    """Merge section/chunk extraction results for Phase 3.

    Exact duplicates are merged without losing source evidence. Conflicting
    candidates are kept in the merged list and also copied to ``conflict_items``
    for Human Confirm.
    """

    candidates_by_key: dict[str, JsonObject] = {}
    duplicate_items: list[JsonObject] = []
    low_confidence_items: list[JsonObject] = []
    candidate_count = 0
    for result in section_results:
        for group_name in CANDIDATE_GROUPS:
            for candidate in result.get(group_name, []):
                candidate_count += 1
                normalized = _normalized_candidate(candidate, group_name)
                key = _candidate_key(normalized)
                if normalized["confidence"] < low_confidence_threshold:
                    normalized["status"] = "low_confidence"
                    low_confidence_items.append(normalized)
                if key not in candidates_by_key:
                    candidates_by_key[key] = normalized
                    continue
                kept = candidates_by_key[key]
                kept["source_evidence"] = _merge_evidence(
                    kept.get("source_evidence", []),
                    normalized.get("source_evidence", []),
                )
                kept["confidence"] = max(kept["confidence"], normalized["confidence"])
                kept["status"] = (
                    "low_confidence" if kept["status"] == "low_confidence" else "merged"
                )
                _append_duplicate_item(
                    duplicate_items,
                    kept_candidate_id=kept["candidate_id"],
                    merged_candidate_id=normalized["candidate_id"],
                    reason="Same normalized text and item_type across sections/chunks.",
                )
    merged_candidates = list(candidates_by_key.values())
    conflict_items = detect_conflicts(merged_candidates)
    _mark_conflicting_candidates(merged_candidates, conflict_items)
    evidence_map = build_evidence_map(merged_candidates)
    return {
        "merged_requirement_candidates": merged_candidates,
        "duplicate_items": duplicate_items,
        "conflict_items": conflict_items,
        "evidence_map": evidence_map,
        "low_confidence_items": low_confidence_items,
        "candidate_count": candidate_count,
        "evidence_count": len(evidence_map["by_evidence_id"]),
    }


def build_evidence_map(candidates: Iterable[Mapping[str, Any]]) -> JsonObject:
    """Build evidence lookup maps for Validator and Human Confirm."""

    by_evidence_id: dict[str, JsonObject] = {}
    by_candidate_id: dict[str, list[str]] = {}
    by_section_id: dict[str, list[str]] = {}
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id", ""))
        by_candidate_id.setdefault(candidate_id, [])
        for evidence in candidate.get("source_evidence", []):
            evidence_id = str(evidence.get("evidence_id") or evidence.get("text", ""))
            if not evidence_id:
                continue
            normalized_evidence = dict(evidence)
            by_evidence_id[evidence_id] = normalized_evidence
            if evidence_id not in by_candidate_id[candidate_id]:
                by_candidate_id[candidate_id].append(evidence_id)
            section_id = str(evidence.get("section_id", ""))
            if section_id:
                by_section_id.setdefault(section_id, [])
                if evidence_id not in by_section_id[section_id]:
                    by_section_id[section_id].append(evidence_id)
    return {
        "by_evidence_id": by_evidence_id,
        "by_candidate_id": by_candidate_id,
        "by_section_id": by_section_id,
    }


def detect_conflicts(candidates: Iterable[Mapping[str, Any]]) -> list[JsonObject]:
    """Detect conservative conflict candidates without deleting any item."""

    candidates_list = list(candidates)
    conflicts: list[JsonObject] = []
    for index, left in enumerate(candidates_list):
        for right in candidates_list[index + 1 :]:
            reason = _conflict_reason(left, right)
            if reason is None:
                continue
            conflicts.append(
                {
                    "candidate_ids": [left.get("candidate_id", ""), right.get("candidate_id", "")],
                    "reason": reason,
                    "status": "manual_review_required",
                    "source_evidence_ids": _candidate_evidence_ids(left)
                    + _candidate_evidence_ids(right),
                }
            )
    return _dedupe_conflicts(conflicts)


def rule_based_bootstrap_extractor(
    section_payload: Mapping[str, Any],
    *,
    rulebase: Mapping[str, Any],
) -> JsonObject:
    """Conservative local extractor for tests and offline wiring checks.

    Production should inject an LLM extractor. This fallback only extracts
    terms explicitly present in the section text.
    """

    section = section_payload["section"]
    document = section_payload["document"]
    section_text = str(section.get("section_text", ""))
    result: JsonObject = {
        "section_id": section.get("section_id", ""),
        "section_title": section.get("section_title", ""),
        "chunk_id": section.get("chunk_id"),
        "raw_features": [],
        "raw_roles": [],
        "raw_skills": [],
        "raw_constraints": [],
        "raw_risk_candidates": [],
        "confidence": 0.5,
        "extractor_notes": [
            "Rule-based bootstrap extractor used. Replace with LLM extractor in production."
        ],
    }
    seen_aliases: set[str] = set()
    for alias, info in rulebase.get("aliases", {}).items():
        if not _contains_phrase(section_text, alias):
            continue
        key = _normalize_text(alias)
        if key in seen_aliases:
            continue
        seen_aliases.add(key)
        candidate_id = _candidate_id(section, "feature", len(result["raw_features"]) + 1)
        result["raw_features"].append(
            _candidate(
                candidate_id=candidate_id,
                item_type="feature",
                text=alias,
                confidence=float(info.get("confidence", 0.75)),
                section=section,
                document=document,
            )
        )

    for alias, info in rulebase.get("constraint_aliases", {}).items():
        if not _contains_phrase(section_text, alias):
            continue
        candidate_id = _candidate_id(
            section,
            "constraint",
            len(result["raw_constraints"]) + 1,
        )
        result["raw_constraints"].append(
            _candidate(
                candidate_id=candidate_id,
                item_type="constraint",
                text=alias,
                confidence=float(info.get("confidence", 0.75)),
                section=section,
                document=document,
            )
        )
    if result["raw_features"] or result["raw_constraints"]:
        result["confidence"] = 0.75
    _append_term_candidates(
        result,
        section=section,
        document=document,
        group_name="raw_skills",
        terms=SKILL_TERMS,
        confidence=0.86,
    )
    _append_term_candidates(
        result,
        section=section,
        document=document,
        group_name="raw_roles",
        terms=ROLE_TERMS,
        confidence=0.86,
    )
    _append_term_candidates(
        result,
        section=section,
        document=document,
        group_name="raw_risk_candidates",
        terms=RISK_TERMS,
        confidence=0.78,
        evidence_sentence=True,
    )
    _append_constraint_patterns(result, section=section, document=document)
    if any(result[group_name] for group_name in CANDIDATE_GROUPS):
        result["confidence"] = max(float(result["confidence"]), 0.75)
    return result


def _normalize_section_result(
    raw_result: Mapping[str, Any],
    section: Mapping[str, Any],
    document: Mapping[str, Any],
) -> JsonObject:
    raw_result = _canonicalize_group_aliases(raw_result)
    result: JsonObject = {
        "section_id": str(raw_result.get("section_id") or section.get("section_id", "")),
        "section_title": str(raw_result.get("section_title") or section.get("section_title", "")),
        "chunk_id": raw_result.get("chunk_id", section.get("chunk_id")),
        "confidence": _clamp_confidence(raw_result.get("confidence", 0.0)),
        "extractor_notes": list(raw_result.get("extractor_notes", [])),
    }
    for group_name in CANDIDATE_GROUPS:
        normalized_candidates = []
        for index, candidate in enumerate(raw_result.get(group_name, []), start=1):
            normalized_candidates.append(
                _normalized_candidate(
                    candidate,
                    group_name,
                    fallback_id=_candidate_id(section, ITEM_TYPE_BY_GROUP[group_name], index),
                    section=section,
                    document=document,
                )
            )
        result[group_name] = normalized_candidates
    result["confidence"] = _section_confidence(result, fallback=result["confidence"])
    return result


def _normalized_candidate(
    candidate: Mapping[str, Any],
    group_name: str,
    *,
    fallback_id: str | None = None,
    section: Mapping[str, Any] | None = None,
    document: Mapping[str, Any] | None = None,
) -> JsonObject:
    text = str(candidate.get("text", "")).strip()
    item_type = str(candidate.get("item_type") or ITEM_TYPE_BY_GROUP[group_name])
    candidate_id = str(candidate.get("candidate_id") or fallback_id or _safe_id(text))
    evidence = [
        _normalize_evidence_item(evidence_item, section=section, document=document)
        for evidence_item in candidate.get("source_evidence", [])
    ]
    if not evidence and section is not None and document is not None and text:
        evidence = [
            _evidence(
                evidence_id=f"{candidate_id}_evidence_001",
                text=_evidence_text(section, text),
                section=section,
                document=document,
            )
        ]
    return {
        "candidate_id": candidate_id,
        "item_type": item_type,
        "text": text,
        "normalized_text": str(candidate.get("normalized_text") or _normalize_text(text)),
        "source_evidence": evidence,
        "confidence": _clamp_confidence(candidate.get("confidence", 0.0)),
        "inference_level": candidate.get("inference_level", "explicit"),
        "status": candidate.get("status", "candidate"),
    }


def _candidate(
    *,
    candidate_id: str,
    item_type: str,
    text: str,
    confidence: float,
    section: Mapping[str, Any],
    document: Mapping[str, Any],
) -> JsonObject:
    return {
        "candidate_id": candidate_id,
        "item_type": item_type,
        "text": text,
        "normalized_text": _normalize_text(text),
        "source_evidence": [
            _evidence(
                evidence_id=f"{candidate_id}_evidence_001",
                text=_evidence_text(section, text),
                section=section,
                document=document,
            )
        ],
        "confidence": confidence,
        "inference_level": "explicit",
        "status": "candidate",
    }


def _evidence(
    *,
    evidence_id: str,
    text: str,
    section: Mapping[str, Any],
    document: Mapping[str, Any],
) -> JsonObject:
    return {
        "evidence_id": evidence_id,
        "document_id": document.get("document_id", ""),
        "section_id": section.get("section_id", ""),
        "section_title": section.get("section_title", ""),
        "chunk_id": section.get("chunk_id"),
        "source_range": dict(section.get("source_range", {})),
        "text": text,
    }


def _normalize_evidence_item(
    evidence_item: Mapping[str, Any],
    *,
    section: Mapping[str, Any] | None,
    document: Mapping[str, Any] | None,
) -> JsonObject:
    section = section or {}
    document = document or {}
    return {
        "evidence_id": str(
            evidence_item.get("evidence_id") or f"{section.get('section_id', 'section')}_evidence"
        ),
        "document_id": evidence_item.get("document_id", document.get("document_id", "")),
        "section_id": evidence_item.get("section_id", section.get("section_id", "")),
        "section_title": evidence_item.get(
            "section_title",
            section.get("section_title", ""),
        ),
        "chunk_id": evidence_item.get("chunk_id", section.get("chunk_id")),
        "source_range": dict(evidence_item.get("source_range", section.get("source_range", {}))),
        "text": str(evidence_item.get("text", "")).strip(),
    }


def _evidence_text(section: Mapping[str, Any], alias: str) -> str:
    section_text = str(section.get("section_text", ""))
    pattern = re.escape(alias)
    match = re.search(pattern, section_text, flags=re.IGNORECASE)
    if not match:
        return alias
    return _sentence_around(section_text, match.start(), match.end())


def _append_term_candidates(
    result: JsonObject,
    *,
    section: Mapping[str, Any],
    document: Mapping[str, Any],
    group_name: str,
    terms: Iterable[str],
    confidence: float,
    evidence_sentence: bool = False,
) -> None:
    seen = {candidate["normalized_text"] for candidate in result[group_name]}
    for term in terms:
        if not _contains_phrase(str(section.get("section_text", "")), term):
            continue
        normalized = _normalize_text(term)
        if normalized in seen:
            continue
        seen.add(normalized)
        item_type = ITEM_TYPE_BY_GROUP[group_name]
        candidate_id = _candidate_id(section, item_type, len(result[group_name]) + 1)
        text = _evidence_text(section, term) if evidence_sentence else term
        result[group_name].append(
            _candidate(
                candidate_id=candidate_id,
                item_type=item_type,
                text=text,
                confidence=confidence,
                section=section,
                document=document,
            )
        )


def _append_constraint_patterns(
    result: JsonObject,
    *,
    section: Mapping[str, Any],
    document: Mapping[str, Any],
) -> None:
    section_text = str(section.get("section_text", ""))
    seen = {candidate["normalized_text"] for candidate in result["raw_constraints"]}
    for pattern in CONSTRAINT_PATTERNS:
        for match in re.finditer(pattern, section_text, flags=re.IGNORECASE):
            text = _sentence_around(section_text, match.start(), match.end())
            normalized = _normalize_text(text)
            if normalized in seen:
                continue
            seen.add(normalized)
            candidate_id = _candidate_id(
                section,
                "constraint",
                len(result["raw_constraints"]) + 1,
            )
            result["raw_constraints"].append(
                _candidate(
                    candidate_id=candidate_id,
                    item_type="constraint",
                    text=text,
                    confidence=0.82,
                    section=section,
                    document=document,
                )
            )


def _sentence_around(section_text: str, start: int, end: int) -> str:
    left = max(
        section_text.rfind("\n", 0, start),
        section_text.rfind(".", 0, start),
        section_text.rfind("!", 0, start),
        section_text.rfind("?", 0, start),
    )
    right_candidates = [
        index
        for index in (
            section_text.find("\n", end),
            section_text.find(".", end),
            section_text.find("!", end),
            section_text.find("?", end),
        )
        if index != -1
    ]
    right = min(right_candidates) + 1 if right_candidates else len(section_text)
    return section_text[left + 1 : right].strip()


def _canonicalize_group_aliases(raw_result: Mapping[str, Any]) -> JsonObject:
    result = dict(raw_result)
    for alias, canonical in ALIASED_GROUPS.items():
        if alias in result and canonical not in result:
            result[canonical] = result[alias]
    return result


def _ensure_not_final_output(raw_result: Mapping[str, Any]) -> None:
    final_keys = sorted(FINAL_OUTPUT_KEYS & set(raw_result))
    if final_keys:
        raise SectionExtractionError(
            "Section extractor returned final Requirements_List fields: " + ", ".join(final_keys)
        )


def _section_confidence(section_result: Mapping[str, Any], *, fallback: float) -> float:
    confidences = [
        float(candidate.get("confidence", 0.0))
        for group_name in CANDIDATE_GROUPS
        for candidate in section_result.get(group_name, [])
    ]
    if not confidences:
        return _clamp_confidence(fallback)
    return _clamp_confidence(sum(confidences) / len(confidences))


def _clamp_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(confidence, 1.0))


def _append_duplicate_item(
    duplicate_items: list[JsonObject],
    *,
    kept_candidate_id: str,
    merged_candidate_id: str,
    reason: str,
) -> None:
    for item in duplicate_items:
        if item["kept_candidate_id"] != kept_candidate_id:
            continue
        if merged_candidate_id not in item["merged_candidate_ids"]:
            item["merged_candidate_ids"].append(merged_candidate_id)
        return
    duplicate_items.append(
        {
            "kept_candidate_id": kept_candidate_id,
            "merged_candidate_ids": [merged_candidate_id],
            "reason": reason,
        }
    )


def _mark_conflicting_candidates(
    candidates: list[JsonObject],
    conflict_items: Iterable[Mapping[str, Any]],
) -> None:
    conflict_ids = {
        candidate_id
        for conflict in conflict_items
        for candidate_id in conflict.get("candidate_ids", [])
    }
    for candidate in candidates:
        if candidate.get("candidate_id") in conflict_ids:
            candidate["status"] = "conflict"


def _conflict_reason(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> str | None:
    if left.get("item_type") != right.get("item_type"):
        return None
    if _candidate_key(left) == _candidate_key(right):
        return None
    numeric_reason = _numeric_conflict_reason(left, right)
    if numeric_reason:
        return numeric_reason
    left_polarity = _requirement_polarity(str(left.get("text", "")))
    right_polarity = _requirement_polarity(str(right.get("text", "")))
    if left_polarity == right_polarity or "unknown" in {left_polarity, right_polarity}:
        return None
    if _token_overlap_score(str(left.get("text", "")), str(right.get("text", ""))) < 0.35:
        return None
    return (
        "Candidate requirements appear to describe the same subject with "
        "opposite inclusion/exclusion or requirement polarity."
    )


def _numeric_conflict_reason(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> str | None:
    if left.get("item_type") != "constraint" or right.get("item_type") != "constraint":
        return None
    left_signature = _numeric_constraint_signature(str(left.get("text", "")))
    right_signature = _numeric_constraint_signature(str(right.get("text", "")))
    if not left_signature or not right_signature:
        return None
    if left_signature[0] != right_signature[0] or left_signature[1] == right_signature[1]:
        return None
    return f"Conflicting {left_signature[0]} constraint values require Human Confirm."


def _numeric_constraint_signature(text: str) -> tuple[str, str] | None:
    normalized = _normalize_text(text)
    duration_match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*(week|weeks|wk|wks|month|months)\b", normalized
    )
    if duration_match:
        return ("duration", f"{duration_match.group(1)} {duration_match.group(2)}")
    budget_match = re.search(
        r"(?:budget|cost|usd|krw|won|\$)\D{0,20}(\d+(?:,\d{3})*(?:\.\d+)?)",
        normalized,
    )
    if budget_match:
        return ("budget", budget_match.group(1).replace(",", ""))
    return None


def _requirement_polarity(text: str) -> str:
    normalized = _normalize_text(text)
    negative_markers = (
        "must not",
        "do not",
        "does not",
        "not support",
        "not required",
        "without",
        "exclude",
        "out of scope",
        "defer",
        "disable",
        "disabled",
        "no ",
    )
    positive_markers = (
        "must",
        "should",
        "required",
        "support",
        "include",
        "enable",
        "allow",
        "need",
    )
    if any(marker in normalized for marker in negative_markers):
        return "negative"
    if any(marker in normalized for marker in positive_markers):
        return "positive"
    return "unknown"


def _token_overlap_score(left: str, right: str) -> float:
    left_tokens = _meaningful_tokens(left)
    right_tokens = _meaningful_tokens(right)
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
        "can",
        "for",
        "in",
        "is",
        "it",
        "must",
        "need",
        "needs",
        "not",
        "of",
        "or",
        "required",
        "should",
        "support",
        "the",
        "to",
        "users",
        "with",
        "without",
    }
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9_]+", _normalize_text(text))
        if len(token) > 2 and token not in stopwords
    }


def _candidate_evidence_ids(candidate: Mapping[str, Any]) -> list[str]:
    return [
        str(evidence.get("evidence_id"))
        for evidence in candidate.get("source_evidence", [])
        if evidence.get("evidence_id")
    ]


def _dedupe_conflicts(conflicts: Iterable[Mapping[str, Any]]) -> list[JsonObject]:
    result: dict[tuple[str, ...], JsonObject] = {}
    for conflict in conflicts:
        key = tuple(sorted(str(candidate_id) for candidate_id in conflict.get("candidate_ids", [])))
        if key:
            result[key] = dict(conflict)
    return list(result.values())


def _section_candidate_count(section_result: Mapping[str, Any]) -> int:
    return sum(len(section_result.get(group_name, [])) for group_name in CANDIDATE_GROUPS)


def _log_progress(
    progress_logger: ProgressLogger | None,
    event: str,
    **details: Any,
) -> None:
    if progress_logger is None:
        return
    progress_logger(event, details)


def _candidate_id(section: Mapping[str, Any], item_type: str, index: int) -> str:
    return f"{section.get('section_id', 'section')}_{item_type}_{index:03d}"


def _candidate_key(candidate: Mapping[str, Any]) -> str:
    return f"{candidate.get('item_type')}::{candidate.get('normalized_text')}"


def _contains_phrase(text: str, phrase: str) -> bool:
    if not phrase:
        return False
    return _normalize_text(phrase) in _normalize_text(text)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def _safe_id(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", value.casefold()).strip("_")
    return slug or "candidate"


def _merge_evidence(
    left: Iterable[Mapping[str, Any]],
    right: Iterable[Mapping[str, Any]],
) -> list[JsonObject]:
    merged: dict[str, JsonObject] = {}
    for evidence in [*left, *right]:
        key = str(evidence.get("evidence_id") or evidence.get("text"))
        merged[key] = dict(evidence)
    return list(merged.values())
