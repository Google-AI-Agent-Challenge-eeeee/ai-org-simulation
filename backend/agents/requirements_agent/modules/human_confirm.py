"""Human Confirm layer for Requirements Agent.

This module prepares review packets and applies user decisions for one project.
It never mutates global taxonomy or rulebase references.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

JsonObject = dict[str, Any]

REVIEW_BUCKETS = (
    "unknown_requirements",
    "missing_extractions",
    "low_confidence_items",
    "invalid_items",
    "missing_fields",
    "restricted_columns_needing_human_confirm",
)


def merge_project_specific_mapping(
    existing_mapping: Mapping[str, str] | None,
    human_confirm_decisions: Mapping[str, Any] | None,
) -> dict[str, str]:
    """Merge request-level and Human Confirm project-only mappings."""

    merged = dict(existing_mapping or {})
    decisions = human_confirm_decisions or {}
    for raw_text, feature_key in decisions.get("project_specific_mapping", {}).items():
        if raw_text and feature_key:
            merged[str(raw_text)] = str(feature_key)
    return merged


def build_human_confirm_result(
    *,
    validation_result: Mapping[str, Any],
    mapped_requirements: Mapping[str, Any],
    column_selection_draft: Mapping[str, Any],
    human_confirm_complete: bool = False,
    human_confirm_decisions: Mapping[str, Any] | None = None,
    project_specific_mapping: Mapping[str, str] | None = None,
    human_confirm_id: str = "human_confirm_result",
) -> JsonObject:
    """Build Human Confirm packet and apply one-project user decisions."""

    decisions = normalize_human_confirm_decisions(human_confirm_decisions)
    review_packet = build_review_packet(
        validation_result=validation_result,
        mapped_requirements=mapped_requirements,
        column_selection_draft=column_selection_draft,
    )
    applied = apply_human_confirm_decisions(
        validation_result=validation_result,
        mapped_requirements=mapped_requirements,
        column_selection_draft=column_selection_draft,
        decisions=decisions,
    )
    review_counts = review_packet["review_counts"]
    remaining_review_counts = _review_counts(
        validation_result=applied["validation_result"],
        mapped_requirements=applied["mapped_requirements"],
        column_selection_draft=applied["column_selection_draft"],
    )
    pending_count = sum(remaining_review_counts.values())
    requested_complete = bool(human_confirm_complete or decisions.get("human_confirm_complete"))
    is_complete = requested_complete and pending_count == 0

    return {
        "_meta": {
            "human_confirm_id": human_confirm_id,
            "pipeline_phase": "human_confirm",
            "status": "completed" if is_complete else "needs_human_confirm",
            "created_at": datetime.now(UTC).isoformat(),
        },
        "human_confirm_complete": is_complete,
        "review_packet": review_packet,
        "review_counts": review_counts,
        "remaining_review_counts": remaining_review_counts,
        "project_specific_mapping": dict(project_specific_mapping or {}),
        "removed_items": decisions["removed_items"],
        "updated_project_fields": decisions["updated_project_fields"],
        "confirmed_restricted_column_keys": decisions["confirmed_restricted_column_keys"],
        "applied": applied,
        "decision_template": decision_template(),
        "policy": {
            "taxonomy_auto_update": False,
            "mapping_scope": "project_specific_only",
            "removed_items_scope": "current_project_only",
            "column_weighting_requires_completed_human_confirm": True,
        },
        "notes": _notes(
            pending_count=pending_count,
            decisions=decisions,
            project_specific_mapping=project_specific_mapping or {},
        ),
    }


def build_review_packet(
    *,
    validation_result: Mapping[str, Any],
    mapped_requirements: Mapping[str, Any],
    column_selection_draft: Mapping[str, Any],
) -> JsonObject:
    """Collect review buckets for UI/API presentation."""

    buckets = {
        "unknown_requirements": list(mapped_requirements.get("unknown_requirements", [])),
        "missing_extractions": list(validation_result.get("missing_extractions", [])),
        "low_confidence_items": _dedupe_items(
            [
                *mapped_requirements.get("low_confidence_items", []),
                *validation_result.get("low_confidence_items", []),
            ]
        ),
        "invalid_items": list(validation_result.get("invalid_items", [])),
        "missing_fields": list(validation_result.get("missing_fields", [])),
        "restricted_columns_needing_human_confirm": list(
            column_selection_draft.get("restricted_columns_needing_human_confirm", [])
        ),
    }
    return {
        "status": "needs_human_confirm" if any(buckets.values()) else "ready_to_confirm",
        "review_items": buckets,
        "review_counts": _review_counts(
            validation_result=validation_result,
            mapped_requirements=mapped_requirements,
            column_selection_draft=column_selection_draft,
        ),
        "decision_template": decision_template(),
    }


def decision_template() -> JsonObject:
    """Return the MVP API request shape expected from a Human Confirm UI."""

    return {
        "human_confirm_complete": False,
        "project_specific_mapping": {
            "<raw requirement text>": "<taxonomy feature_key for this project only>"
        },
        "removed_items": [
            {
                "item_id": "<item_id/candidate_id/field/column_key/text>",
                "reason": "Why this item should be removed for this project.",
            }
        ],
        "updated_project_fields": {
            "project_name": "",
            "project_goal": "",
            "duration_weeks": None,
            "budget": None,
        },
        "confirmed_restricted_column_keys": ["employee.base_salary_krw"],
    }


def normalize_human_confirm_decisions(
    human_confirm_decisions: Mapping[str, Any] | None,
) -> JsonObject:
    """Normalize permissive API input into a stable internal shape."""

    decisions = dict(human_confirm_decisions or {})
    return {
        "human_confirm_complete": bool(decisions.get("human_confirm_complete", False)),
        "project_specific_mapping": {
            str(raw_text): str(feature_key)
            for raw_text, feature_key in decisions.get("project_specific_mapping", {}).items()
            if raw_text and feature_key
        },
        "removed_items": list(decisions.get("removed_items", [])),
        "updated_project_fields": dict(decisions.get("updated_project_fields", {})),
        "confirmed_restricted_column_keys": [
            str(key) for key in decisions.get("confirmed_restricted_column_keys", []) if key
        ],
    }


def apply_human_confirm_decisions(
    *,
    validation_result: Mapping[str, Any],
    mapped_requirements: Mapping[str, Any],
    column_selection_draft: Mapping[str, Any],
    decisions: Mapping[str, Any],
) -> JsonObject:
    """Apply user decisions to project-local intermediate outputs."""

    normalized_decisions = normalize_human_confirm_decisions(decisions)
    removed_keys = _removed_item_keys(normalized_decisions.get("removed_items", []))
    mapped_copy = deepcopy(dict(mapped_requirements))
    validation_copy = deepcopy(dict(validation_result))
    column_selection_copy = deepcopy(dict(column_selection_draft))

    for key in ("unknown_requirements", "conflict_items", "low_confidence_items"):
        mapped_copy[key] = _filter_removed(mapped_copy.get(key, []), removed_keys)
    for key in ("missing_extractions", "invalid_items", "low_confidence_items"):
        validation_copy[key] = _filter_removed(validation_copy.get(key, []), removed_keys)
    validation_copy["missing_fields"] = _filter_missing_fields(
        validation_copy.get("missing_fields", []),
        removed_keys=removed_keys,
        updated_project_fields=normalized_decisions["updated_project_fields"],
    )
    validation_copy["project_fields"] = {
        **dict(validation_copy.get("project_fields", {})),
        **normalized_decisions["updated_project_fields"],
    }
    column_selection_copy["restricted_columns_needing_human_confirm"] = [
        {
            **column,
            "human_confirmed": column.get("column_key")
            in normalized_decisions["confirmed_restricted_column_keys"],
        }
        for column in column_selection_copy.get("restricted_columns_needing_human_confirm", [])
        if not _item_matches_removed_keys(column, removed_keys)
    ]
    column_selection_copy["selected_employee_columns"] = [
        {
            **column,
            "human_confirmed": column.get("column_key")
            in normalized_decisions["confirmed_restricted_column_keys"],
        }
        for column in column_selection_copy.get("selected_employee_columns", [])
        if not _item_matches_removed_keys(column, removed_keys)
    ]

    return {
        "mapped_requirements": mapped_copy,
        "validation_result": validation_copy,
        "column_selection_draft": column_selection_copy,
    }


def _review_counts(
    *,
    validation_result: Mapping[str, Any],
    mapped_requirements: Mapping[str, Any],
    column_selection_draft: Mapping[str, Any],
) -> dict[str, int]:
    return {
        "unknown_requirement_count": len(mapped_requirements.get("unknown_requirements", [])),
        "conflict_count": len(mapped_requirements.get("conflict_items", [])),
        "missing_extraction_count": len(validation_result.get("missing_extractions", [])),
        "invalid_item_count": len(validation_result.get("invalid_items", [])),
        "low_confidence_count": len(
            _dedupe_items(
                [
                    *mapped_requirements.get("low_confidence_items", []),
                    *validation_result.get("low_confidence_items", []),
                ]
            )
        ),
        "missing_field_count": len(validation_result.get("missing_fields", [])),
        "restricted_column_count": len(
            [
                column
                for column in column_selection_draft.get(
                    "restricted_columns_needing_human_confirm",
                    [],
                )
                if not column.get("human_confirmed")
            ]
        ),
    }


def _filter_removed(
    items: Iterable[Mapping[str, Any]],
    removed_keys: set[str],
) -> list[JsonObject]:
    return [dict(item) for item in items if not _item_matches_removed_keys(item, removed_keys)]


def _filter_missing_fields(
    items: Iterable[Mapping[str, Any]],
    *,
    removed_keys: set[str],
    updated_project_fields: Mapping[str, Any],
) -> list[JsonObject]:
    return [
        dict(item)
        for item in items
        if not _item_matches_removed_keys(item, removed_keys)
        and item.get("field") not in updated_project_fields
    ]


def _removed_item_keys(removed_items: Iterable[Any]) -> set[str]:
    keys: set[str] = set()
    for item in removed_items:
        if isinstance(item, str):
            keys.add(_normalize_key(item))
            continue
        if not isinstance(item, Mapping):
            continue
        for field in ("item_id", "candidate_id", "field", "column_key", "text"):
            if item.get(field):
                keys.add(_normalize_key(str(item[field])))
    return keys


def _item_matches_removed_keys(item: Mapping[str, Any], removed_keys: set[str]) -> bool:
    if not removed_keys:
        return False
    candidate_keys = {
        _normalize_key(str(item.get(field, "")))
        for field in (
            "item_id",
            "candidate_id",
            "field",
            "column_key",
            "text",
            "feature_key",
            "constraint_key",
            "risk_key",
            "name",
        )
        if item.get(field)
    }
    return bool(candidate_keys & removed_keys)


def _dedupe_items(items: Iterable[Mapping[str, Any]]) -> list[JsonObject]:
    deduped: dict[tuple[str, str], JsonObject] = {}
    for item in items:
        key = (
            str(item.get("item_id") or item.get("candidate_id") or item.get("text") or ""),
            str(item.get("reason") or ""),
        )
        deduped[key] = dict(item)
    return list(deduped.values())


def _normalize_key(value: str) -> str:
    return " ".join(value.casefold().split())


def _notes(
    *,
    pending_count: int,
    decisions: Mapping[str, Any],
    project_specific_mapping: Mapping[str, str],
) -> list[str]:
    notes = [
        "Unknown requirements are not added to taxonomy automatically.",
        "Project-specific mappings apply only to this Requirements Agent run.",
        "Final column weighting is blocked until Human Confirm is complete.",
    ]
    if project_specific_mapping:
        notes.append(
            "Project-specific mappings were provided to taxonomy matching for this project."
        )
    if decisions.get("project_specific_mapping"):
        notes.append(
            "Human Confirm submitted project-specific mapping; rerun or pipeline pre-application is required for taxonomy promotion."
        )
    if pending_count:
        notes.append(f"{pending_count} Human Confirm item(s) remain pending.")
    return notes
