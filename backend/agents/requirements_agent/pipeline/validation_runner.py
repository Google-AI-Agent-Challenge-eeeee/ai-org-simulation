"""Validation runner for Requirements Agent pipeline."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

JsonObject = dict[str, Any]
Validator = Callable[[Mapping[str, Any]], Mapping[str, Any]]

DEFAULT_LOW_CONFIDENCE_THRESHOLD = 0.75
REVIEW_LIST_KEYS = (
    "missing_extractions",
    "invalid_items",
    "low_confidence_items",
)
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
    "제목",
    "목표",
)
GENERIC_PROJECT_NAME_LINES = {
    "prd",
    "prd:",
    "product requirements document",
    "document meta",
    "0. document meta",
    "문서",
    "문서 메타",
}
NO_ADDITIONAL_BUDGET_MARKERS = (
    "별도 추가 인프라 비용 없음",
    "추가 인프라 비용 없음",
    "별도 추가 비용 없음",
    "추가 비용 없음",
    "예산 없음",
    "no additional budget",
    "no additional cost",
    "within existing plan",
    "within existing budget",
)


def run_validation(
    *,
    prepared_document: Mapping[str, Any],
    extracted_requirements_draft: Mapping[str, Any],
    mapped_requirements: Mapping[str, Any],
    coverage_check: Mapping[str, Any],
    project_fields: Mapping[str, Any] | None = None,
    validator: Validator | None = None,
    validation_id: str = "validation_result",
) -> JsonObject:
    """Validate extraction/mapping outputs and separate review buckets."""

    inferred_project_fields = extract_project_fields(str(prepared_document.get("raw_text", "")))
    merged_project_fields = {**inferred_project_fields, **(project_fields or {})}
    prd_evidence_map = build_prd_evidence_map(prepared_document)
    default_result = _default_validation(
        prepared_document=prepared_document,
        extracted_requirements_draft=extracted_requirements_draft,
        mapped_requirements=mapped_requirements,
        coverage_check=coverage_check,
        prd_evidence_map=prd_evidence_map,
        project_fields=merged_project_fields,
    )
    external_result = {}
    if validator is not None:
        external_result = dict(
            validator(
                build_validation_payload(
                    prepared_document=prepared_document,
                    extracted_requirements_draft=extracted_requirements_draft,
                    mapped_requirements=mapped_requirements,
                    coverage_check=coverage_check,
                    project_fields=merged_project_fields,
                    prd_evidence_map=prd_evidence_map,
                )
            )
        )

    result = _merge_validation_results(default_result, external_result)
    result["_meta"] = {
        "validation_id": validation_id,
        "pipeline_phase": "validation",
        "status": "needs_human_confirm" if _has_review_items(result) else "completed",
        "created_at": datetime.now(UTC).isoformat(),
    }
    result["project_fields"] = merged_project_fields
    result["prd_evidence_map"] = prd_evidence_map
    result["validation_stats"] = {
        "prd_evidence_count": len(prd_evidence_map["by_evidence_id"]),
        "missing_extraction_count": len(result.get("missing_extractions", [])),
        "invalid_item_count": len(result.get("invalid_items", [])),
        "low_confidence_count": len(result.get("low_confidence_items", [])),
        "missing_field_count": len(result.get("missing_fields", [])),
    }
    return result


def build_validation_payload(
    *,
    prepared_document: Mapping[str, Any],
    extracted_requirements_draft: Mapping[str, Any],
    mapped_requirements: Mapping[str, Any],
    coverage_check: Mapping[str, Any],
    project_fields: Mapping[str, Any],
    prd_evidence_map: Mapping[str, Any] | None = None,
    low_confidence_below: float = DEFAULT_LOW_CONFIDENCE_THRESHOLD,
) -> JsonObject:
    """Build the payload for an injected Validator Agent call."""

    prd_evidence_map = prd_evidence_map or build_prd_evidence_map(prepared_document)
    return {
        "document": dict(prepared_document.get("document", {})),
        "sections": list(prepared_document.get("sections", [])),
        "prd_evidence_map": dict(prd_evidence_map),
        "extracted_requirements_draft": dict(extracted_requirements_draft),
        "mapped_requirements": dict(mapped_requirements),
        "coverage_check": dict(coverage_check),
        "project_fields": dict(project_fields),
        "validation_thresholds": {
            "low_confidence_below": low_confidence_below,
            "required_project_fields": [
                "project_name",
                "project_goal",
                "duration_weeks",
            ],
            "optional_project_fields": ["budget"],
        },
        "phase_boundaries": {
            "delete_items": False,
            "mutate_taxonomy": False,
            "finalize_column_weights": False,
            "route_review_items_to_human_confirm": True,
        },
    }


def build_prd_evidence_map(prepared_document: Mapping[str, Any]) -> JsonObject:
    """Build requirement-like evidence units from lossless PRD sections."""

    by_evidence_id: dict[str, JsonObject] = {}
    by_section_id: dict[str, list[str]] = {}
    for section in prepared_document.get("sections", []):
        section_id = str(section.get("section_id", "section"))
        by_section_id.setdefault(section_id, [])
        for index, text in enumerate(_requirement_like_segments(section), start=1):
            evidence_id = f"{section_id}_prd_evidence_{index:03d}"
            evidence = {
                "evidence_id": evidence_id,
                "document_id": prepared_document.get("document", {}).get("document_id", ""),
                "document_type": prepared_document.get("document", {}).get("document_type", "prd"),
                "section_id": section_id,
                "section_title": section.get("section_title", ""),
                "chunk_id": section.get("chunk_id"),
                "source_range": dict(section.get("source_range", {})),
                "text": text,
            }
            by_evidence_id[evidence_id] = evidence
            by_section_id[section_id].append(evidence_id)
    return {
        "by_evidence_id": by_evidence_id,
        "by_section_id": by_section_id,
    }


def extract_project_fields(raw_text: str) -> JsonObject:
    """Extract simple project fields without summarizing source text."""

    budget_value, budget_status = _budget_with_status(raw_text)
    return {
        "project_name": _project_name(raw_text),
        "project_goal": _project_goal(raw_text),
        "duration_weeks": _duration_weeks(raw_text),
        "budget": budget_value,
        "budget_status": budget_status,
    }


def _default_validation(
    *,
    prepared_document: Mapping[str, Any],
    extracted_requirements_draft: Mapping[str, Any],
    mapped_requirements: Mapping[str, Any],
    coverage_check: Mapping[str, Any],
    prd_evidence_map: Mapping[str, Any],
    project_fields: Mapping[str, Any],
) -> JsonObject:
    invalid_items = [
        *_items_without_source_evidence(extracted_requirements_draft),
        *_mapped_items_without_valid_evidence(
            prepared_document=prepared_document,
            extracted_requirements_draft=extracted_requirements_draft,
            mapped_requirements=mapped_requirements,
        ),
    ]
    missing_extractions = [
        *_missing_extractions_from_coverage(coverage_check),
        *_missing_extractions_from_prd_evidence(
            prd_evidence_map=prd_evidence_map,
            extracted_requirements_draft=extracted_requirements_draft,
            mapped_requirements=mapped_requirements,
        ),
    ]
    low_confidence_items = _low_confidence_review_items(
        extracted_requirements_draft,
        mapped_requirements,
        threshold=DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    )
    missing_fields = _missing_fields(project_fields)
    return {
        "missing_extractions": _dedupe_review_items(missing_extractions),
        "invalid_items": _dedupe_review_items(invalid_items),
        "low_confidence_items": _dedupe_review_items(low_confidence_items),
        "missing_fields": missing_fields,
        "coverage_findings": list(coverage_check.get("notes", [])),
        "validator_notes": [
            "Default deterministic validation completed.",
            "Unknown, missing, and low-confidence items are kept in separate buckets.",
            "Validator does not delete extracted or mapped items; review items are routed to Human Confirm.",
        ],
    }


def _merge_validation_results(
    default_result: Mapping[str, Any],
    external_result: Mapping[str, Any],
) -> JsonObject:
    result = dict(default_result)
    for key in (
        "missing_extractions",
        "invalid_items",
        "low_confidence_items",
        "missing_fields",
        "coverage_findings",
        "validator_notes",
    ):
        merged = [*result.get(key, []), *external_result.get(key, [])]
        result[key] = (
            _dedupe_by_repr(merged)
            if key not in REVIEW_LIST_KEYS
            else (_dedupe_review_items(_normalize_review_items(merged)))
        )
    return result


def _items_without_source_evidence(
    extracted_requirements_draft: Mapping[str, Any],
) -> list[JsonObject]:
    invalid_items: list[JsonObject] = []
    for candidate in extracted_requirements_draft.get("merged_requirement_candidates", []):
        if candidate.get("source_evidence"):
            continue
        invalid_items.append(
            {
                "item_id": candidate.get("candidate_id", ""),
                "text": candidate.get("text", ""),
                "item_type": candidate.get("item_type", "other"),
                "source_evidence": [],
                "confidence": candidate.get("confidence", 0.0),
                "reason": "Candidate has no source_evidence and cannot be finalized.",
                "status": "manual_review_required",
                "suggested_mapping": None,
            }
        )
    return invalid_items


def _mapped_items_without_valid_evidence(
    *,
    prepared_document: Mapping[str, Any],
    extracted_requirements_draft: Mapping[str, Any],
    mapped_requirements: Mapping[str, Any],
) -> list[JsonObject]:
    invalid_items: list[JsonObject] = []
    extracted_evidence_ids = set(
        extracted_requirements_draft.get("evidence_map", {}).get("by_evidence_id", {})
    )
    mapped_feature_keys = {
        feature.get("feature_key")
        for feature in mapped_requirements.get("mapped_features", [])
        if feature.get("feature_key")
    }

    for feature in mapped_requirements.get("mapped_features", []):
        invalid_items.extend(
            _invalid_when_evidence_is_missing_or_ungrounded(
                item=feature,
                item_id=str(feature.get("candidate_id") or feature.get("feature_key") or ""),
                item_type="feature",
                text=str(feature.get("raw_text") or feature.get("standard_name") or ""),
                reason_prefix="Mapped feature",
                prepared_document=prepared_document,
                extracted_evidence_ids=extracted_evidence_ids,
                suggested_mapping={"feature_key": feature.get("feature_key")},
            )
        )

    for constraint in mapped_requirements.get("constraints", []):
        invalid_items.extend(
            _invalid_when_evidence_is_missing_or_ungrounded(
                item=constraint,
                item_id=str(constraint.get("constraint_key") or ""),
                item_type="constraint",
                text=str(constraint.get("text") or constraint.get("constraint_key") or ""),
                reason_prefix="Mapped constraint",
                prepared_document=prepared_document,
                extracted_evidence_ids=extracted_evidence_ids,
                suggested_mapping={"constraint_key": constraint.get("constraint_key")},
            )
        )

    for risk in mapped_requirements.get("risk_factors", []):
        risk_key = str(risk.get("risk_key") or "")
        source_type = risk.get("source_type")
        source_feature_keys = set(risk.get("source_feature_keys", []))
        if source_type == "extracted":
            invalid_items.extend(
                _invalid_when_evidence_is_missing_or_ungrounded(
                    item=risk,
                    item_id=risk_key,
                    item_type="risk",
                    text=str(risk.get("text") or risk_key),
                    reason_prefix="Extracted risk",
                    prepared_document=prepared_document,
                    extracted_evidence_ids=extracted_evidence_ids,
                    suggested_mapping=None,
                )
            )
        elif source_type == "taxonomy" and not source_feature_keys <= mapped_feature_keys:
            invalid_items.append(
                _review_item(
                    item_id=risk_key,
                    text=str(risk.get("text") or risk_key),
                    item_type="risk",
                    source_evidence=list(risk.get("source_evidence", [])),
                    confidence=0.0,
                    reason="Taxonomy risk expansion references no valid mapped feature.",
                    suggested_mapping=None,
                )
            )

    invalid_items.extend(
        _taxonomy_expansion_support_issues(
            mapped_requirements.get("required_roles", []),
            mapped_feature_keys=mapped_feature_keys,
            item_type="role",
        )
    )
    invalid_items.extend(
        _taxonomy_expansion_support_issues(
            mapped_requirements.get("required_skills", []),
            mapped_feature_keys=mapped_feature_keys,
            item_type="skill",
        )
    )
    return invalid_items


def _invalid_when_evidence_is_missing_or_ungrounded(
    *,
    item: Mapping[str, Any],
    item_id: str,
    item_type: str,
    text: str,
    reason_prefix: str,
    prepared_document: Mapping[str, Any],
    extracted_evidence_ids: set[str],
    suggested_mapping: Mapping[str, Any] | None,
) -> list[JsonObject]:
    evidence = list(item.get("source_evidence", []))
    if not evidence:
        return [
            _review_item(
                item_id=item_id,
                text=text,
                item_type=item_type,
                source_evidence=[],
                confidence=float(item.get("confidence", 0.0) or 0.0),
                reason=f"{reason_prefix} has no source_evidence and cannot be finalized.",
                suggested_mapping=suggested_mapping,
            )
        ]
    ungrounded = [
        evidence_item
        for evidence_item in evidence
        if not _evidence_is_grounded(evidence_item, prepared_document, extracted_evidence_ids)
    ]
    if not ungrounded:
        return []
    return [
        _review_item(
            item_id=item_id,
            text=text,
            item_type=item_type,
            source_evidence=ungrounded,
            confidence=float(item.get("confidence", 0.0) or 0.0),
            reason=f"{reason_prefix} source_evidence was not found in PRD evidence map.",
            suggested_mapping=suggested_mapping,
        )
    ]


def _taxonomy_expansion_support_issues(
    items: Iterable[Mapping[str, Any]],
    *,
    mapped_feature_keys: set[str],
    item_type: str,
) -> list[JsonObject]:
    invalid_items: list[JsonObject] = []
    for item in items:
        source_feature_keys = set(item.get("source_feature_keys", []))
        if source_feature_keys and source_feature_keys <= mapped_feature_keys:
            continue
        name = str(item.get("name") or "")
        invalid_items.append(
            _review_item(
                item_id=name,
                text=name,
                item_type=item_type,
                source_evidence=[],
                confidence=0.0,
                reason=f"Taxonomy {item_type} expansion references no valid mapped feature.",
                suggested_mapping=None,
            )
        )
    return invalid_items


def _missing_extractions_from_coverage(coverage_check: Mapping[str, Any]) -> list[JsonObject]:
    missing: list[JsonObject] = []
    for section in coverage_check.get("sections", []):
        if section.get("status") != "missing":
            continue
        missing.append(
            {
                "item_id": f"{section.get('section_id', 'section')}_missing_extraction",
                "text": section.get("section_title", ""),
                "item_type": "other",
                "source_evidence": [],
                "confidence": 0.0,
                "reason": section.get("reason", "Section has no extracted requirement evidence."),
                "status": "manual_review_required",
                "suggested_mapping": None,
            }
        )
    return missing


def _missing_extractions_from_prd_evidence(
    *,
    prd_evidence_map: Mapping[str, Any],
    extracted_requirements_draft: Mapping[str, Any],
    mapped_requirements: Mapping[str, Any],
) -> list[JsonObject]:
    missing: list[JsonObject] = []
    compared_items = [
        *_all_extracted_candidates(extracted_requirements_draft),
        *_all_mapped_or_review_items(mapped_requirements),
    ]
    for evidence in prd_evidence_map.get("by_evidence_id", {}).values():
        if _evidence_is_represented(evidence, compared_items):
            continue
        missing.append(
            _review_item(
                item_id=f"{evidence.get('evidence_id', 'evidence')}_missing",
                text=str(evidence.get("text", "")),
                item_type=_infer_item_type(str(evidence.get("text", ""))),
                source_evidence=[dict(evidence)],
                confidence=0.0,
                reason="PRD evidence appears requirement-like but is absent from extraction and mapping outputs.",
                suggested_mapping=None,
            )
        )
    return missing


def _low_confidence_review_items(
    extracted_requirements_draft: Mapping[str, Any],
    mapped_requirements: Mapping[str, Any],
    *,
    threshold: float,
) -> list[JsonObject]:
    items: list[JsonObject] = []
    for candidate in extracted_requirements_draft.get("low_confidence_items", []):
        items.append(
            _review_item_from_candidate(
                candidate,
                reason="Extraction confidence is below Validator threshold.",
            )
        )
    for item in mapped_requirements.get("low_confidence_items", []):
        items.append(_review_item_from_candidate(item, reason=item.get("reason")))
    for candidate in _all_extracted_candidates(extracted_requirements_draft):
        if float(candidate.get("confidence", 1.0) or 0.0) < threshold:
            items.append(
                _review_item_from_candidate(
                    candidate,
                    reason="Candidate confidence is below Validator threshold.",
                )
            )
    for item in _all_mapped_primary_items(mapped_requirements):
        if float(item.get("confidence", 1.0) or 0.0) < threshold:
            items.append(
                _review_item_from_candidate(
                    item,
                    reason="Mapped item confidence is below Validator threshold.",
                )
            )
    return _dedupe_review_items(items)


def _missing_fields(project_fields: Mapping[str, Any]) -> list[JsonObject]:
    fields = [
        (
            "project_name",
            "Project name is missing.",
            "warning",
            "What is the project name?",
        ),
        (
            "project_goal",
            "Project goal is missing.",
            "warning",
            "What primary outcome should the team optimize for?",
        ),
        (
            "duration_weeks",
            "Project duration is missing.",
            "info",
            "What is the expected project duration in weeks?",
        ),
        (
            "budget",
            "Project budget is missing.",
            "info",
            "Is there a fixed budget or cost limit?",
        ),
    ]
    missing = []
    for field, reason, severity, question in fields:
        if field == "budget" and _budget_is_validly_absent(project_fields):
            continue
        value = project_fields.get(field)
        if value not in ("", None):
            continue
        missing.append(
            {
                "field": field,
                "reason": reason,
                "severity": severity,
                "suggested_question": question,
            }
        )
    return missing


def _budget_is_validly_absent(project_fields: Mapping[str, Any]) -> bool:
    return str(project_fields.get("budget_status") or "") in {
        "explicit_no_additional_budget",
        "not_specified_but_allowed",
    }


def _has_review_items(validation_result: Mapping[str, Any]) -> bool:
    return any(
        validation_result.get(key)
        for key in (
            "missing_extractions",
            "invalid_items",
            "low_confidence_items",
            "missing_fields",
        )
    )


def _requirement_like_segments(section: Mapping[str, Any]) -> list[str]:
    segments: list[str] = []
    for line in str(section.get("section_text", "")).splitlines():
        clean = _clean_segment_text(line)
        if not _is_requirement_like(clean):
            continue
        segments.append(clean)
    if segments:
        return _unique_strings(segments)

    section_text = str(section.get("section_text", ""))
    for sentence in _sentence_segments(section_text):
        clean = _clean_segment_text(sentence)
        if _is_requirement_like(clean):
            segments.append(clean)
    return _unique_strings(segments)


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


def _all_extracted_candidates(
    extracted_requirements_draft: Mapping[str, Any],
) -> list[JsonObject]:
    candidates = [
        dict(candidate)
        for candidate in extracted_requirements_draft.get(
            "merged_requirement_candidates",
            [],
        )
    ]
    if candidates:
        return candidates
    for result in extracted_requirements_draft.get("section_results", []):
        for group_name in (
            "raw_features",
            "raw_roles",
            "raw_skills",
            "raw_constraints",
            "raw_risk_candidates",
        ):
            candidates.extend(dict(candidate) for candidate in result.get(group_name, []))
    return candidates


def _all_mapped_primary_items(mapped_requirements: Mapping[str, Any]) -> list[JsonObject]:
    items: list[JsonObject] = []
    for group_name in ("mapped_features", "constraints", "risk_factors"):
        items.extend(dict(item) for item in mapped_requirements.get(group_name, []))
    return items


def _all_mapped_or_review_items(mapped_requirements: Mapping[str, Any]) -> list[JsonObject]:
    items = _all_mapped_primary_items(mapped_requirements)
    for group_name in ("unknown_requirements", "conflict_items", "low_confidence_items"):
        items.extend(dict(item) for item in mapped_requirements.get(group_name, []))
    return items


def _evidence_is_represented(
    evidence: Mapping[str, Any],
    items: Iterable[Mapping[str, Any]],
) -> bool:
    evidence_text = str(evidence.get("text", ""))
    evidence_section_id = evidence.get("section_id")
    for item in items:
        item_texts = [
            str(item.get("text") or item.get("raw_text") or item.get("standard_name") or "")
        ]
        item_texts.extend(str(value.get("text", "")) for value in item.get("source_evidence", []))
        item_sections = {
            value.get("section_id") for value in item.get("source_evidence", []) if value
        }
        if evidence_section_id and item_sections and evidence_section_id not in item_sections:
            continue
        if any(_text_match_score(evidence_text, item_text) >= 0.5 for item_text in item_texts):
            return True
    return False


def _evidence_is_grounded(
    evidence: Mapping[str, Any],
    prepared_document: Mapping[str, Any],
    extracted_evidence_ids: set[str],
) -> bool:
    evidence_id = str(evidence.get("evidence_id") or "")
    if evidence_id and evidence_id in extracted_evidence_ids:
        return True
    evidence_text = str(evidence.get("text", "")).strip()
    if not evidence_text:
        return False
    section_text = _section_text_by_id(prepared_document).get(str(evidence.get("section_id")), "")
    if evidence_text and evidence_text in section_text:
        return True
    raw_text = str(prepared_document.get("raw_text", ""))
    return bool(evidence_text and evidence_text in raw_text)


def _section_text_by_id(prepared_document: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(section.get("section_id", "")): str(section.get("section_text", ""))
        for section in prepared_document.get("sections", [])
    }


def _review_item(
    *,
    item_id: str,
    text: str,
    item_type: str,
    source_evidence: list[JsonObject],
    confidence: float,
    reason: str,
    suggested_mapping: Mapping[str, Any] | None,
) -> JsonObject:
    return {
        "item_id": item_id,
        "text": text,
        "item_type": item_type if item_type else "other",
        "source_evidence": source_evidence,
        "confidence": max(0.0, min(float(confidence), 1.0)),
        "reason": reason,
        "status": "manual_review_required",
        "suggested_mapping": dict(suggested_mapping) if suggested_mapping else None,
    }


def _review_item_from_candidate(
    candidate: Mapping[str, Any],
    *,
    reason: str | None,
) -> JsonObject:
    candidate_id = str(candidate.get("candidate_id") or candidate.get("item_id") or "")
    text = str(
        candidate.get("text")
        or candidate.get("raw_text")
        or candidate.get("standard_name")
        or candidate.get("constraint_key")
        or candidate.get("risk_key")
        or ""
    )
    item_type = str(candidate.get("item_type") or _infer_item_type(text))
    return _review_item(
        item_id=candidate_id,
        text=text,
        item_type=item_type,
        source_evidence=[dict(item) for item in candidate.get("source_evidence", [])],
        confidence=float(candidate.get("confidence", 0.0) or 0.0),
        reason=reason or "Item requires Human Confirm.",
        suggested_mapping=candidate.get("suggested_mapping"),
    )


def _normalize_review_items(items: Iterable[Mapping[str, Any]]) -> list[JsonObject]:
    return [
        _review_item_from_candidate(
            item,
            reason=str(item.get("reason") or "Item requires Human Confirm."),
        )
        for item in items
    ]


def _dedupe_review_items(items: Iterable[Mapping[str, Any]]) -> list[JsonObject]:
    result: dict[tuple[str, str, str], JsonObject] = {}
    for item in items:
        normalized = _review_item_from_candidate(
            item,
            reason=str(item.get("reason") or "Item requires Human Confirm."),
        )
        key = (
            normalized.get("item_id", ""),
            normalized.get("text", ""),
            normalized.get("reason", ""),
        )
        result[key] = normalized
    return list(result.values())


def _dedupe_by_repr(items: Iterable[Any]) -> list[Any]:
    result: dict[str, Any] = {}
    for item in items:
        result[repr(item)] = item
    return list(result.values())


def _infer_item_type(text: str) -> str:
    normalized = _normalize_text(text)
    if any(word in normalized for word in ("budget", "cost", "usd", "krw", "won")):
        return "constraint"
    if any(word in normalized for word in ("week", "deadline", "launch date", "mvp")):
        return "constraint"
    if any(word in normalized for word in ("risk", "delay", "failure", "bottleneck")):
        return "risk"
    return "feature"


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


def _project_name(raw_text: str) -> str:
    flattened = _flatten_project_text(raw_text)
    meta_match = re.search(
        r"(?:^|\s)(?:제목|title)\s*[:：|]?\s+(.+?)\s+(?:작성자|author|dri|상태|status|버전|version)",
        flattened,
        re.I,
    )
    if meta_match:
        title = _clean_project_field_value(meta_match.group(1))
        if _is_meaningful_project_name(title):
            return title

    for line in raw_text.splitlines():
        clean = line.strip().strip("# ")
        if not clean:
            continue
        label_match = re.match(r"^(project|name|title|제목)\s*[:：|]\s*(.+)$", clean, re.I)
        if label_match:
            title = _clean_project_field_value(label_match.group(2))
            if _is_meaningful_project_name(title):
                return title
        if clean.startswith("#"):
            title = _clean_project_field_value(clean)
            if _is_meaningful_project_name(title):
                return title

    header_title = _title_after_prd_marker(raw_text)
    if header_title:
        return header_title

    for line in raw_text.splitlines():
        clean = _clean_project_field_value(line.strip().strip("# "))
        if _is_meaningful_project_name(clean):
            return clean
    return ""


def _project_goal(raw_text: str) -> str:
    for line in raw_text.splitlines():
        clean = line.strip()
        match = re.match(r"^(goal|objective|purpose|목표|목적)\s*[:：]\s*(.+)$", clean, re.I)
        if match:
            return _clean_project_field_value(match.group(2))
    tl_dr = _section_after_heading(raw_text, ("tl;dr", "tldr", "요약"), max_chars=700)
    if tl_dr:
        goal_sentence = _first_goal_sentence(tl_dr)
        if goal_sentence:
            return goal_sentence
    business_goal = _section_after_heading(
        raw_text,
        ("비즈니스 목표", "business goal", "business goals", "목표와"),
        max_chars=900,
    )
    if business_goal:
        lines = [
            _clean_project_field_value(line)
            for line in business_goal.splitlines()
            if re.search(r"(^|\s)G\d+\.|목표|달성|개선|감소|증가|target|goal", line, re.I)
        ]
        if lines:
            return _join_goal_lines(lines[:3])
    return ""


def _duration_weeks(raw_text: str) -> int | None:
    search_text = re.sub(r"\s+", " ", raw_text)
    labelled_week_match = re.search(
        r"(?:기간|일정|duration|timeline|schedule)"
        r"(?:\s+(?:기간|일정|duration|timeline|schedule))?"
        r"\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:주|week|weeks|wk|wks)",
        search_text,
        re.I,
    )
    if labelled_week_match:
        return int(float(labelled_week_match.group(1)))

    range_match = re.search(r"\bW\s*(\d+)\s*[-~–]\s*W\s*(\d+)\b", search_text, re.I)
    if range_match:
        return max(1, int(range_match.group(2)) - int(range_match.group(1)) + 1)

    sprint_week = re.search(
        r"1\s*(?:스프린트|sprint)\s*=\s*(\d+(?:\.\d+)?)\s*(?:주|week|weeks)",
        search_text,
        re.I,
    )
    sprint_counts = re.findall(
        r"(\d+(?:\.\d+)?)\s*(?:스프린트|sprints?)(?!\s*=)",
        search_text,
        re.I,
    )
    if sprint_counts and sprint_week:
        return max(1, int(float(sprint_counts[-1]) * float(sprint_week.group(1))))

    korean_match = re.search(r"(\d+(?:\.\d+)?)\s*주\b", search_text)
    if korean_match:
        return int(float(korean_match.group(1)))

    match = re.search(r"(\d+(?:\.\d+)?)\s*(week|weeks|wk|wks)", search_text, re.I)
    if match:
        return int(float(match.group(1)))
    match = re.search(r"(\d+(?:\.\d+)?)\s*(month|months)", search_text, re.I)
    if match:
        return int(float(match.group(1)) * 4)
    return None


def _budget(raw_text: str) -> float | None:
    value, _status = _budget_with_status(raw_text)
    return value


def _budget_with_status(raw_text: str) -> tuple[float | None, str]:
    normalized = _normalize_text(raw_text)
    if any(marker in normalized for marker in NO_ADDITIONAL_BUDGET_MARKERS):
        return None, "explicit_no_additional_budget"
    for match in re.finditer(
        r"\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(usd|krw|won)?",
        raw_text,
        re.I,
    ):
        following_unit = raw_text[match.end() : match.end() + 16].casefold()
        if re.match(r"\s*(week|weeks|wk|wks|month|months)\b", following_unit):
            continue
        if _budget_context(raw_text, match.start()):
            return float(match.group(1).replace(",", "")), "explicit_budget"
    return None, "not_specified_but_allowed"


def _budget_context(raw_text: str, start: int) -> bool:
    context = raw_text[max(0, start - 40) : start + 40].casefold()
    if any(word in context for word in ("절감", "saving", "savings", "처리비용")):
        return False
    return any(word in context for word in ("budget", "cost", "usd", "krw", "won"))


def _flatten_project_text(raw_text: str) -> str:
    return _clean_project_field_value(raw_text.replace("|", " "))


def _clean_project_field_value(value: str) -> str:
    clean = re.sub(r"^#{1,6}\s*", "", value or "").strip()
    clean = re.sub(r"\s+", " ", clean)
    clean = clean.strip(" -:：|")
    return _dedupe_adjacent_tokens(clean)


def _dedupe_adjacent_tokens(value: str) -> str:
    tokens = value.split()
    deduped: list[str] = []
    for token in tokens:
        if deduped and normalize_for_project_token(deduped[-1]) == normalize_for_project_token(token):
            continue
        deduped.append(token)
    return " ".join(deduped).strip()


def normalize_for_project_token(token: str) -> str:
    return re.sub(r"[^\w가-힣]+", "", token.casefold())


def _is_meaningful_project_name(value: str) -> bool:
    normalized = _normalize_text(value).strip(" :：")
    if not normalized or normalized in GENERIC_PROJECT_NAME_LINES:
        return False
    if len(normalized) < 3 or len(normalized) > 120:
        return False
    return bool(re.search(r"[a-zA-Z가-힣]", normalized))


def _title_after_prd_marker(raw_text: str) -> str:
    lines = [_clean_project_field_value(line) for line in raw_text.splitlines()]
    for index, line in enumerate(lines):
        if _normalize_text(line).strip(" :：") != "prd":
            continue
        fragments = []
        for next_line in lines[index + 1 : index + 12]:
            if not next_line:
                continue
            if re.match(r"^\d+(\.\d+)*\b", next_line) or next_line.casefold() in {
                "document meta",
                "tl;dr",
            }:
                break
            if _is_meaningful_project_name(next_line):
                fragments.append(next_line)
        title = _clean_project_field_value(" ".join(fragments[:5]))
        if _is_meaningful_project_name(title):
            return title
    return ""


def _section_after_heading(raw_text: str, headings: tuple[str, ...], *, max_chars: int) -> str:
    lines = raw_text.splitlines()
    for index, line in enumerate(lines):
        clean = _clean_project_field_value(line).casefold()
        if not any(heading in clean for heading in headings):
            continue
        collected = []
        for next_line in lines[index + 1 :]:
            if re.match(r"^\s*\d+(\.\d+)*\s+\S+", next_line) and collected:
                break
            collected.append(next_line)
            if len("\n".join(collected)) >= max_chars:
                break
        return "\n".join(collected)[:max_chars]
    return ""


def _first_goal_sentence(text: str) -> str:
    cleaned = _clean_project_field_value(text)
    sentences = re.split(r"(?<=[.!?。])\s+|(?<=합니다)\s*", cleaned)
    for sentence in sentences:
        sentence = _clean_project_field_value(sentence)
        if any(marker in sentence for marker in ("목표", "달성", "해결", "개선", "감소")):
            return sentence
    return _clean_project_field_value(sentences[0]) if sentences else ""


def _join_goal_lines(lines: list[str]) -> str:
    return " ".join(line for line in lines if line).strip()
