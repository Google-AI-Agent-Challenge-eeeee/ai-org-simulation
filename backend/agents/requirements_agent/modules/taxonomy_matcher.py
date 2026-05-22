"""Rule-based taxonomy matching for Requirements Agent.

This module intentionally performs no LLM calls. It maps raw extraction candidates
to the static taxonomy/rulebase references and separates weak or unmatched items
for Human Confirm.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]

FEATURE_GROUPS = ("raw_features",)
CONSTRAINT_GROUPS = ("raw_constraints",)
RISK_GROUPS = ("raw_risk_candidates",)
ROLE_GROUPS = ("raw_roles",)
SKILL_GROUPS = ("raw_skills",)


def load_json(path: str | Path) -> JsonObject:
    """Load a JSON reference file as a dictionary."""

    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def normalize_text(value: str) -> str:
    """Normalize text for conservative alias matching."""

    return re.sub(r"\s+", " ", value.casefold()).strip()


def match_requirements(
    extracted_requirements_draft: Mapping[str, Any],
    taxonomy: Mapping[str, Any],
    rulebase: Mapping[str, Any],
    *,
    project_specific_mapping: Mapping[str, str] | None = None,
    mapped_requirements_id: str = "mapped_requirements_draft",
) -> JsonObject:
    """Map raw extraction candidates to taxonomy features and review buckets.

    Unknown requirements remain review items. This function never mutates the
    taxonomy or rulebase dictionaries.
    """

    project_specific_mapping = project_specific_mapping or {}
    feature_candidates = list(_iter_candidates(extracted_requirements_draft, FEATURE_GROUPS))
    constraint_candidates = list(_iter_candidates(extracted_requirements_draft, CONSTRAINT_GROUPS))
    risk_candidates = list(_iter_candidates(extracted_requirements_draft, RISK_GROUPS))
    role_candidates = list(_iter_candidates(extracted_requirements_draft, ROLE_GROUPS))
    skill_candidates = list(_iter_candidates(extracted_requirements_draft, SKILL_GROUPS))

    mapped_features: list[JsonObject] = []
    unknown_requirements: list[JsonObject] = []
    low_confidence_items: list[JsonObject] = []
    conflict_items: list[JsonObject] = []
    conflict_items.extend(_conflicts_from_draft(extracted_requirements_draft))

    for candidate in feature_candidates:
        if _is_conflict_candidate(candidate):
            conflict_items.append(_conflict_item_from_candidate(candidate))
            continue
        conflict = _find_ambiguous_conflict(candidate, rulebase)
        match = _match_feature(candidate, taxonomy, rulebase, project_specific_mapping)
        if _is_low_confidence_candidate(candidate):
            low_confidence_items.append(
                _review_item(
                    candidate,
                    "Extraction confidence is too low for automatic taxonomy mapping.",
                    suggested_mapping=(
                        {"feature_key": match["feature_key"]} if match is not None else None
                    ),
                )
            )
            continue
        if conflict and not _is_strong_exact_match(match):
            conflict_items.append(conflict)
            low_confidence_items.append(
                _review_item(candidate, "Ambiguous alias requires Human Confirm.")
            )
            continue
        if match is None:
            unknown_requirements.append(
                _review_item(candidate, "No confident taxonomy or rulebase match.")
            )
            continue
        if match["confidence"] < _minimum_confidence(taxonomy, rulebase):
            low_confidence_items.append(
                _review_item(
                    candidate,
                    "Matched below automatic confidence threshold.",
                    suggested_mapping={"feature_key": match["feature_key"]},
                )
            )
            continue
        mapped_features.append(_mapped_feature(candidate, match, taxonomy))

    mapped_features = _merge_mapped_features(mapped_features)
    constraints = _map_constraints(
        constraint_candidates,
        rulebase,
        unknown_requirements,
        low_confidence_items,
        conflict_items,
    )
    risk_factors = _map_risk_candidates(risk_candidates, low_confidence_items, conflict_items)

    roles = _expand_taxonomy_items(
        mapped_features,
        taxonomy,
        rulebase,
        item_key="roles",
        direct_candidates=role_candidates,
        unknown_requirements=unknown_requirements,
    )
    skills = _expand_taxonomy_items(
        mapped_features,
        taxonomy,
        rulebase,
        item_key="skills",
        direct_candidates=skill_candidates,
        unknown_requirements=unknown_requirements,
    )
    risk_factors.extend(_expand_risks(mapped_features, taxonomy))

    conflict_items = _dedupe_conflict_items(conflict_items)
    status = (
        "needs_human_confirm"
        if (unknown_requirements or low_confidence_items or conflict_items)
        else "completed"
    )

    return {
        "_meta": {
            "mapped_requirements_id": mapped_requirements_id,
            "draft_id": extracted_requirements_draft.get("_meta", {}).get("draft_id"),
            "project_id": extracted_requirements_draft.get("_meta", {}).get("project_id"),
            "pipeline_phase": "taxonomy_matching",
            "status": status,
            "taxonomy_version": taxonomy.get("_meta", {}).get("version", "unknown"),
            "rulebase_version": rulebase.get("_meta", {}).get("version", "unknown"),
            "created_at": datetime.now(UTC).isoformat(),
        },
        "mapped_features": mapped_features,
        "required_roles": roles,
        "required_skills": skills,
        "constraints": constraints,
        "risk_factors": _dedupe_by_key(risk_factors, "risk_key"),
        "unknown_requirements": unknown_requirements,
        "conflict_items": conflict_items,
        "low_confidence_items": low_confidence_items,
        "mapping_stats": {
            "input_candidate_count": (
                len(feature_candidates)
                + len(constraint_candidates)
                + len(risk_candidates)
                + len(role_candidates)
                + len(skill_candidates)
            ),
            "mapped_feature_count": len(mapped_features),
            "unknown_count": len(unknown_requirements),
            "conflict_count": len(conflict_items),
            "low_confidence_count": len(low_confidence_items),
        },
        "source_trace": _collect_source_trace(
            feature_candidates
            + constraint_candidates
            + risk_candidates
            + role_candidates
            + skill_candidates
        ),
    }


def _iter_candidates(
    draft: Mapping[str, Any],
    group_names: Iterable[str],
) -> Iterable[JsonObject]:
    merged_candidates = list(draft.get("merged_requirement_candidates", []))
    if merged_candidates:
        for candidate in merged_candidates:
            if candidate.get("item_type") in _item_types_for_groups(group_names):
                yield dict(candidate)
        return

    for result in draft.get("section_results", []):
        for group_name in group_names:
            for candidate in result.get(group_name, []):
                yield dict(candidate)


def _item_types_for_groups(group_names: Iterable[str]) -> set[str]:
    item_types: set[str] = set()
    mapping = {
        "raw_features": "feature",
        "raw_constraints": "constraint",
        "raw_risk_candidates": "risk",
        "raw_roles": "role",
        "raw_skills": "skill",
    }
    for group_name in group_names:
        item_types.add(mapping[group_name])
    return item_types


def _is_conflict_candidate(candidate: Mapping[str, Any]) -> bool:
    return candidate.get("status") == "conflict"


def _is_low_confidence_candidate(candidate: Mapping[str, Any]) -> bool:
    return (
        candidate.get("status") == "low_confidence"
        or float(candidate.get("confidence", 1.0) or 0.0) < 0.7
    )


def _match_feature(
    candidate: Mapping[str, Any],
    taxonomy: Mapping[str, Any],
    rulebase: Mapping[str, Any],
    project_specific_mapping: Mapping[str, str],
) -> JsonObject | None:
    raw_text = str(candidate.get("normalized_text") or candidate.get("text") or "")
    normalized = normalize_text(raw_text)
    if normalized in {normalize_text(k) for k in project_specific_mapping}:
        feature_key = _lookup_casefold(project_specific_mapping, normalized)
        if _feature_exists(feature_key, taxonomy):
            return {
                "feature_key": feature_key,
                "matched_alias": raw_text,
                "match_method": "manual_project_mapping",
                "confidence": 1.0,
            }

    alias_match = _best_alias_match(normalized, rulebase)
    if alias_match and _feature_exists(alias_match["feature_key"], taxonomy):
        return alias_match

    feature_match = _feature_name_match(normalized, taxonomy)
    if feature_match:
        return feature_match
    return None


def _lookup_casefold(mapping: Mapping[str, str], normalized_key: str) -> str:
    for key, value in mapping.items():
        if normalize_text(key) == normalized_key:
            return value
    raise KeyError(normalized_key)


def _best_alias_match(normalized_text: str, rulebase: Mapping[str, Any]) -> JsonObject | None:
    matches: list[JsonObject] = []
    for alias, alias_info in rulebase.get("aliases", {}).items():
        normalized_alias = normalize_text(alias)
        if not normalized_alias:
            continue
        if normalized_text == normalized_alias or normalized_alias in normalized_text:
            matches.append(
                {
                    "feature_key": alias_info["feature_key"],
                    "matched_alias": alias,
                    "match_method": (
                        "alias_exact" if normalized_text == normalized_alias else "alias_contains"
                    ),
                    "confidence": float(alias_info.get("confidence", 0.0)),
                    "_alias_length": len(normalized_alias),
                }
            )
    if not matches:
        return None
    matches.sort(key=lambda item: (item["confidence"], item["_alias_length"]), reverse=True)
    best = matches[0]
    best.pop("_alias_length", None)
    return best


def _feature_name_match(normalized_text: str, taxonomy: Mapping[str, Any]) -> JsonObject | None:
    for feature_key, feature in taxonomy.get("features", {}).items():
        names = [feature_key, feature.get("standard_name", "")]
        if any(normalize_text(name) == normalized_text for name in names if name):
            return {
                "feature_key": feature_key,
                "matched_alias": feature.get("standard_name", feature_key),
                "match_method": "taxonomy_exact",
                "confidence": 1.0,
            }
    return None


def _feature_exists(feature_key: str, taxonomy: Mapping[str, Any]) -> bool:
    return feature_key in taxonomy.get("features", {})


def _minimum_confidence(taxonomy: Mapping[str, Any], rulebase: Mapping[str, Any]) -> float:
    taxonomy_threshold = taxonomy.get("matching_policy", {}).get("minimum_taxonomy_confidence", 0.8)
    rulebase_threshold = rulebase.get("matching_policy", {}).get(
        "minimum_confidence_for_auto_match",
        0.75,
    )
    return min(float(taxonomy_threshold), float(rulebase_threshold))


def _find_ambiguous_conflict(
    candidate: Mapping[str, Any],
    rulebase: Mapping[str, Any],
) -> JsonObject | None:
    normalized = normalize_text(
        str(candidate.get("normalized_text") or candidate.get("text") or "")
    )
    for alias, info in rulebase.get("ambiguous_aliases", {}).items():
        normalized_alias = normalize_text(alias)
        if normalized_alias and normalized_alias in normalized:
            return {
                "text": candidate.get("text", ""),
                "candidate_feature_keys": list(info.get("candidate_feature_keys", [])),
                "source_evidence": candidate.get("source_evidence", []),
                "reason": info.get("reason", "Ambiguous alias requires review."),
                "status": "manual_review_required",
            }
    return None


def _is_strong_exact_match(match: Mapping[str, Any] | None) -> bool:
    if match is None:
        return False
    return match.get("match_method") == "alias_exact" and float(match.get("confidence", 0)) >= 0.9


def _mapped_feature(
    candidate: Mapping[str, Any],
    match: Mapping[str, Any],
    taxonomy: Mapping[str, Any],
) -> JsonObject:
    feature = taxonomy["features"][match["feature_key"]]
    return {
        "candidate_id": candidate.get("candidate_id", ""),
        "feature_key": match["feature_key"],
        "standard_name": feature.get("standard_name", match["feature_key"]),
        "category": feature.get("category"),
        "raw_text": candidate.get("text", ""),
        "matched_alias": match.get("matched_alias"),
        "match_method": match.get("match_method", "alias_contains"),
        "confidence": float(match.get("confidence", candidate.get("confidence", 0.0))),
        "source_evidence": candidate.get("source_evidence", []),
        "roles": list(feature.get("roles", [])),
        "skills": list(feature.get("skills", [])),
        "risks": list(feature.get("risks", [])),
        "weight_hints": list(feature.get("weight_hints", [])),
        "status": "mapped",
    }


def _merge_mapped_features(mapped_features: list[JsonObject]) -> list[JsonObject]:
    merged_by_key: dict[str, JsonObject] = {}
    for feature in mapped_features:
        feature_key = feature.get("feature_key", "")
        if feature_key not in merged_by_key:
            merged_by_key[feature_key] = dict(feature)
            continue
        merged = merged_by_key[feature_key]
        merged["candidate_id"] = _join_unique(
            [merged.get("candidate_id", ""), feature.get("candidate_id", "")]
        )
        merged["raw_text"] = _join_unique([merged.get("raw_text", ""), feature.get("raw_text", "")])
        merged["confidence"] = max(
            float(merged.get("confidence", 0.0)),
            float(feature.get("confidence", 0.0)),
        )
        merged["source_evidence"] = _merge_source_evidence(
            merged.get("source_evidence", []),
            feature.get("source_evidence", []),
        )
        merged["roles"] = _unique_strings([*merged.get("roles", []), *feature.get("roles", [])])
        merged["skills"] = _unique_strings([*merged.get("skills", []), *feature.get("skills", [])])
        merged["risks"] = _unique_strings([*merged.get("risks", []), *feature.get("risks", [])])
        merged["weight_hints"] = _unique_strings(
            [*merged.get("weight_hints", []), *feature.get("weight_hints", [])]
        )
    return list(merged_by_key.values())


def _map_constraints(
    candidates: list[JsonObject],
    rulebase: Mapping[str, Any],
    unknown_requirements: list[JsonObject],
    low_confidence_items: list[JsonObject],
    conflict_items: list[JsonObject],
) -> list[JsonObject]:
    constraints: list[JsonObject] = []
    for candidate in candidates:
        if _is_conflict_candidate(candidate):
            conflict_items.append(_conflict_item_from_candidate(candidate))
            continue
        normalized = normalize_text(
            str(candidate.get("normalized_text") or candidate.get("text") or "")
        )
        match = None
        for alias, info in rulebase.get("constraint_aliases", {}).items():
            normalized_alias = normalize_text(alias)
            if normalized_alias and normalized_alias in normalized:
                match = {"alias": alias, **dict(info)}
                break
        if match is None:
            unknown_requirements.append(
                _review_item(
                    candidate,
                    "Constraint could not be mapped to a known constraint profile.",
                )
            )
            continue
        if _is_low_confidence_candidate(candidate):
            low_confidence_items.append(
                _review_item(
                    candidate,
                    "Extraction confidence is too low for automatic constraint mapping.",
                    suggested_mapping={"constraint_key": match["constraint_key"]},
                )
            )
            continue
        if match.get("action") == "low_confidence_items":
            low_confidence_items.append(
                _review_item(
                    candidate,
                    "Constraint wording is qualitative and needs Human Confirm.",
                    suggested_mapping={"constraint_key": match["constraint_key"]},
                )
            )
            continue
        constraints.append(
            {
                "constraint_key": match["constraint_key"],
                "text": candidate.get("text", ""),
                "constraint_type": _constraint_type(match["constraint_key"]),
                "confidence": float(match.get("confidence", candidate.get("confidence", 0.0))),
                "source_evidence": candidate.get("source_evidence", []),
                "status": "mapped",
            }
        )
    return _merge_constraints(constraints)


def _merge_constraints(constraints: Iterable[Mapping[str, Any]]) -> list[JsonObject]:
    merged_by_key: dict[str, JsonObject] = {}
    for constraint in constraints:
        constraint_key = str(constraint.get("constraint_key", ""))
        if not constraint_key:
            continue
        if constraint_key not in merged_by_key:
            merged_by_key[constraint_key] = dict(constraint)
            continue
        merged = merged_by_key[constraint_key]
        merged["text"] = _join_unique([merged.get("text", ""), constraint.get("text", "")])
        merged["confidence"] = max(
            float(merged.get("confidence", 0.0)),
            float(constraint.get("confidence", 0.0)),
        )
        merged["source_evidence"] = _merge_source_evidence(
            merged.get("source_evidence", []),
            constraint.get("source_evidence", []),
        )
    return list(merged_by_key.values())


def _constraint_type(constraint_key: str) -> str:
    if "timeline" in constraint_key:
        return "schedule"
    if "budget" in constraint_key:
        return "budget"
    if "reliability" in constraint_key:
        return "operation"
    return "other"


def _map_risk_candidates(
    candidates: list[JsonObject],
    low_confidence_items: list[JsonObject],
    conflict_items: list[JsonObject],
) -> list[JsonObject]:
    risks: list[JsonObject] = []
    for index, candidate in enumerate(candidates, start=1):
        if _is_conflict_candidate(candidate):
            conflict_items.append(_conflict_item_from_candidate(candidate))
            continue
        if _is_low_confidence_candidate(candidate):
            low_confidence_items.append(
                _review_item(
                    candidate,
                    "Risk candidate confidence is too low for automatic risk factor promotion.",
                )
            )
            continue
        risk_key = f"extracted_risk_{index:03d}"
        risks.append(
            {
                "risk_key": risk_key,
                "text": candidate.get("text", ""),
                "source_type": "extracted",
                "source_feature_keys": [],
                "source_evidence": candidate.get("source_evidence", []),
                "reason": "Risk candidate was explicitly extracted from source evidence.",
            }
        )
    return risks


def _expand_taxonomy_items(
    mapped_features: list[JsonObject],
    taxonomy: Mapping[str, Any],
    rulebase: Mapping[str, Any],
    *,
    item_key: str,
    direct_candidates: list[JsonObject],
    unknown_requirements: list[JsonObject],
) -> list[JsonObject]:
    items_by_name: dict[str, JsonObject] = {}
    for feature in mapped_features:
        taxonomy_feature = taxonomy["features"].get(feature["feature_key"], {})
        for name in taxonomy_feature.get(item_key, []):
            entry = items_by_name.setdefault(
                name,
                {
                    "name": name,
                    "source_feature_keys": [],
                    "reason": f"Expanded from taxonomy {item_key}.",
                },
            )
            entry["source_feature_keys"].append(feature["feature_key"])
    for candidate in direct_candidates:
        if _is_conflict_candidate(candidate):
            unknown_requirements.append(
                _review_item(
                    candidate,
                    f"Conflicting {item_key} candidate requires Human Confirm.",
                )
            )
            continue
        if _is_low_confidence_candidate(candidate):
            unknown_requirements.append(
                _review_item(
                    candidate,
                    f"{item_key.title()} candidate confidence is too low for automatic mapping.",
                )
            )
            continue
        mapped_item = _map_direct_taxonomy_item(
            candidate,
            taxonomy,
            rulebase,
            item_key=item_key,
        )
        if mapped_item is None:
            unknown_requirements.append(
                _review_item(
                    candidate,
                    f"Explicit {item_key} candidate did not match taxonomy standard names.",
                )
            )
            continue
        entry = items_by_name.setdefault(
            mapped_item["name"],
            {
                "name": mapped_item["name"],
                "source_feature_keys": list(mapped_item.get("source_feature_keys", [])),
                "reason": f"Explicitly mentioned and matched taxonomy {item_key}.",
            },
        )
        entry["source_feature_keys"] = _unique_strings(
            [*entry.get("source_feature_keys", []), *mapped_item.get("source_feature_keys", [])]
        )
        if item_key == "roles" and mapped_item.get("job_category_codes"):
            entry["job_category_codes"] = list(mapped_item["job_category_codes"])
    return list(items_by_name.values())


def _map_direct_taxonomy_item(
    candidate: Mapping[str, Any],
    taxonomy: Mapping[str, Any],
    rulebase: Mapping[str, Any],
    *,
    item_key: str,
) -> JsonObject | None:
    text = str(candidate.get("normalized_text") or candidate.get("text") or "")
    normalized = normalize_text(text)
    if item_key == "roles":
        alias_match = _map_direct_role_alias(normalized, taxonomy, rulebase)
        if alias_match is not None:
            return alias_match
        for role_name, role in taxonomy.get("standard_roles", {}).items():
            if normalize_text(role_name) == normalized or normalize_text(role_name) in normalized:
                return {
                    "name": role_name,
                    "source_feature_keys": [],
                    "job_category_codes": list(role.get("job_category_codes", [])),
                }
        return None

    if item_key == "skills":
        alias_match = _map_direct_skill_alias(normalized, taxonomy, rulebase)
        if alias_match is not None:
            return alias_match
        skill_sources: dict[str, list[str]] = {}
        for feature_key, feature in taxonomy.get("features", {}).items():
            for skill_name in feature.get("skills", []):
                skill_sources.setdefault(skill_name, []).append(feature_key)
        for skill_name, source_feature_keys in skill_sources.items():
            normalized_skill = normalize_text(skill_name)
            if normalized_skill == normalized or normalized_skill in normalized:
                return {
                    "name": skill_name,
                    "source_feature_keys": source_feature_keys,
                }
    return None


def _map_direct_role_alias(
    normalized_text: str,
    taxonomy: Mapping[str, Any],
    rulebase: Mapping[str, Any],
) -> JsonObject | None:
    matches: list[JsonObject] = []
    for alias, info in rulebase.get("role_aliases", {}).items():
        normalized_alias = normalize_text(alias)
        if not normalized_alias:
            continue
        if normalized_text != normalized_alias and normalized_alias not in normalized_text:
            continue
        role_name = str(info.get("role_name", ""))
        role = taxonomy.get("standard_roles", {}).get(role_name)
        if role is None:
            continue
        matches.append(
            {
                "name": role_name,
                "source_feature_keys": [],
                "job_category_codes": list(role.get("job_category_codes", [])),
                "_confidence": float(info.get("confidence", 0.0)),
                "_alias_length": len(normalized_alias),
            }
        )
    if not matches:
        return None
    matches.sort(key=lambda item: (item["_alias_length"], item["_confidence"]), reverse=True)
    best = matches[0]
    best.pop("_confidence", None)
    best.pop("_alias_length", None)
    return best


def _map_direct_skill_alias(
    normalized_text: str,
    taxonomy: Mapping[str, Any],
    rulebase: Mapping[str, Any],
) -> JsonObject | None:
    skill_sources = _skill_sources(taxonomy)
    matches: list[JsonObject] = []
    for alias, info in rulebase.get("skill_aliases", {}).items():
        normalized_alias = normalize_text(alias)
        if not normalized_alias:
            continue
        if normalized_text != normalized_alias and normalized_alias not in normalized_text:
            continue
        skill_name = str(info.get("skill_name", ""))
        source_feature_keys = skill_sources.get(skill_name)
        if not source_feature_keys:
            continue
        matches.append(
            {
                "name": skill_name,
                "source_feature_keys": source_feature_keys,
                "_confidence": float(info.get("confidence", 0.0)),
                "_alias_length": len(normalized_alias),
            }
        )
    if not matches:
        return None
    matches.sort(key=lambda item: (item["_alias_length"], item["_confidence"]), reverse=True)
    best = matches[0]
    best.pop("_confidence", None)
    best.pop("_alias_length", None)
    return best


def _skill_sources(taxonomy: Mapping[str, Any]) -> dict[str, list[str]]:
    skill_sources: dict[str, list[str]] = {}
    for feature_key, feature in taxonomy.get("features", {}).items():
        for skill_name in feature.get("skills", []):
            skill_sources.setdefault(skill_name, []).append(feature_key)
    return skill_sources


def _expand_risks(
    mapped_features: list[JsonObject], taxonomy: Mapping[str, Any]
) -> list[JsonObject]:
    risks: list[JsonObject] = []
    for feature in mapped_features:
        taxonomy_feature = taxonomy["features"].get(feature["feature_key"], {})
        for risk in taxonomy_feature.get("risks", []):
            risks.append(
                {
                    "risk_key": normalize_text(risk).replace(" ", "_")[:80],
                    "text": risk,
                    "source_type": "taxonomy",
                    "source_feature_keys": [feature["feature_key"]],
                    "source_evidence": feature.get("source_evidence", []),
                    "reason": "Expanded from matched taxonomy feature.",
                }
            )
    return risks


def _review_item(
    candidate: Mapping[str, Any],
    reason: str,
    *,
    suggested_mapping: Mapping[str, Any] | None = None,
) -> JsonObject:
    return {
        "item_id": candidate.get("candidate_id", ""),
        "candidate_id": candidate.get("candidate_id", ""),
        "text": candidate.get("text", ""),
        "item_type": candidate.get("item_type", "other"),
        "source_evidence": candidate.get("source_evidence", []),
        "confidence": float(candidate.get("confidence", 0.0)),
        "reason": reason,
        "status": "manual_review_required",
        "suggested_mapping": dict(suggested_mapping) if suggested_mapping else None,
    }


def _conflicts_from_draft(extracted_requirements_draft: Mapping[str, Any]) -> list[JsonObject]:
    conflicts: list[JsonObject] = []
    for conflict in extracted_requirements_draft.get("conflict_items", []):
        conflicts.append(
            {
                "text": " / ".join(
                    str(candidate_id) for candidate_id in conflict.get("candidate_ids", [])
                ),
                "candidate_ids": list(conflict.get("candidate_ids", [])),
                "candidate_feature_keys": [],
                "source_evidence": [],
                "source_evidence_ids": list(conflict.get("source_evidence_ids", [])),
                "reason": conflict.get(
                    "reason",
                    "Chunk result merge marked these candidates as conflicting.",
                ),
                "status": "manual_review_required",
            }
        )
    return conflicts


def _conflict_item_from_candidate(candidate: Mapping[str, Any]) -> JsonObject:
    return {
        "text": candidate.get("text", ""),
        "candidate_ids": [candidate.get("candidate_id", "")],
        "candidate_feature_keys": [],
        "source_evidence": list(candidate.get("source_evidence", [])),
        "reason": "Candidate was marked as conflict during chunk result merge.",
        "status": "manual_review_required",
    }


def _dedupe_conflict_items(conflict_items: Iterable[Mapping[str, Any]]) -> list[JsonObject]:
    result: dict[str, JsonObject] = {}
    for conflict in conflict_items:
        key_parts = [
            str(value)
            for value in (
                conflict.get("text"),
                conflict.get("reason"),
                tuple(conflict.get("candidate_ids", [])),
                tuple(conflict.get("candidate_feature_keys", [])),
            )
            if value
        ]
        key = "::".join(key_parts)
        if key:
            result[key] = dict(conflict)
    return list(result.values())


def _collect_source_trace(candidates: Iterable[Mapping[str, Any]]) -> list[JsonObject]:
    evidence_by_id: dict[str, JsonObject] = {}
    for candidate in candidates:
        for evidence in candidate.get("source_evidence", []):
            evidence_id = evidence.get("evidence_id")
            if evidence_id:
                evidence_by_id[evidence_id] = dict(evidence)
    return list(evidence_by_id.values())


def _dedupe_by_key(items: Iterable[JsonObject], key: str) -> list[JsonObject]:
    result: dict[str, JsonObject] = {}
    for item in items:
        item_key = str(item.get(key, ""))
        if not item_key:
            continue
        if item_key in result:
            result[item_key]["source_feature_keys"] = sorted(
                set(result[item_key].get("source_feature_keys", []))
                | set(item.get("source_feature_keys", []))
            )
            continue
        result[item_key] = dict(item)
    return list(result.values())


def _merge_source_evidence(
    left: Iterable[Mapping[str, Any]],
    right: Iterable[Mapping[str, Any]],
) -> list[JsonObject]:
    evidence_by_id: dict[str, JsonObject] = {}
    for evidence in [*left, *right]:
        evidence_id = str(evidence.get("evidence_id") or evidence.get("text", ""))
        if evidence_id:
            evidence_by_id[evidence_id] = dict(evidence)
    return list(evidence_by_id.values())


def _join_unique(values: Iterable[str]) -> str:
    return " | ".join(_unique_strings(values))


def _unique_strings(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
