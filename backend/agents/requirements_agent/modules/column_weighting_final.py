"""Final column weighting for Requirements Agent."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]
DEFAULT_RULE_WEIGHT = 0.05


def load_json(path: str | Path) -> JsonObject:
    """Load a JSON reference file as a dictionary."""

    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def calculate_column_weights(
    column_selection_draft: Mapping[str, Any],
    employee_column_rules: Mapping[str, Any],
    *,
    human_confirm_complete: bool,
    weighting_id: str = "column_weighting_result",
) -> JsonObject:
    """Calculate final project comparison weights from confirmed column selections.

    Weights describe how strongly each employee DB/activity column should be
    used as a comparison criterion for this project. They are not employee
    scores, performance ratings, or person-level evaluations.
    """

    if not human_confirm_complete:
        return {
            "_meta": _meta(weighting_id, employee_column_rules, status="needs_human_confirm"),
            "status": "needs_human_confirm",
            "column_weights": {},
            "column_priority_order": [],
            "weighting_reason": {},
            "notes": ["Final weighting is blocked until Human Confirm is complete."],
        }

    selected_columns = list(column_selection_draft.get("selected_employee_columns", []))
    pending_restricted_columns = _pending_restricted_columns(selected_columns)
    if pending_restricted_columns:
        return {
            "_meta": _meta(weighting_id, employee_column_rules, status="needs_human_confirm"),
            "status": "needs_human_confirm",
            "column_weights": {},
            "column_priority_order": [],
            "weighting_reason": {},
            "pending_restricted_columns": pending_restricted_columns,
            "notes": [
                "Final weighting is blocked because restricted columns still need Human Confirm."
            ],
        }

    eligible_columns = _eligible_columns(selected_columns)
    if not eligible_columns:
        return {
            "_meta": _meta(weighting_id, employee_column_rules, status="completed"),
            "status": "completed",
            "column_weights": {},
            "column_priority_order": [],
            "weighting_reason": {},
            "weighting_breakdown": [],
            "weighting_stats": {
                "selected_column_count": 0,
                "weighted_column_count": 0,
                "weight_sum": 0.0,
                "comparison_scope": "project_requirements_to_employee_db_columns",
            },
            "notes": ["No confirmed selected employee columns were available for weighting."],
        }

    rule_configs = employee_column_rules.get("requirement_type_rules", {})
    columns_by_rule = _columns_by_rule(eligible_columns)
    raw_scores, breakdown_by_column = _raw_scores_by_column(
        eligible_columns,
        columns_by_rule=columns_by_rule,
        rule_configs=rule_configs,
    )

    normalized = _normalize_scores(raw_scores)
    ordered_keys = sorted(normalized, key=lambda key: (-normalized[key], key))
    reasons = {
        column_key: _weight_reason(
            column=_column_by_key(eligible_columns)[column_key],
            weight=normalized[column_key],
            contributions=breakdown_by_column[column_key],
        )
        for column_key in ordered_keys
    }
    weighting_breakdown = [
        _column_breakdown(
            column=_column_by_key(eligible_columns)[column_key],
            raw_score=raw_scores[column_key],
            normalized_weight=normalized[column_key],
            contributions=breakdown_by_column[column_key],
        )
        for column_key in ordered_keys
    ]

    return {
        "_meta": _meta(weighting_id, employee_column_rules, status="completed"),
        "status": "completed",
        "column_weights": normalized,
        "column_priority_order": ordered_keys,
        "weighting_reason": {key: reasons[key] for key in ordered_keys},
        "weighting_breakdown": weighting_breakdown,
        "weighting_stats": {
            "selected_column_count": len(selected_columns),
            "weighted_column_count": len(eligible_columns),
            "rule_count": len(columns_by_rule),
            "weight_sum": round(sum(normalized.values()), 6),
            "comparison_scope": "project_requirements_to_employee_db_columns",
        },
        "notes": [
            "Column weights rank project-specific employee DB comparison criteria.",
            "Column weights are not employee personal evaluation scores.",
        ],
    }


def _meta(
    weighting_id: str,
    employee_column_rules: Mapping[str, Any],
    *,
    status: str,
) -> JsonObject:
    return {
        "weighting_id": weighting_id,
        "pipeline_phase": "column_weighting_final",
        "status": status,
        "column_rules_version": employee_column_rules.get("_meta", {}).get("version", "unknown"),
        "created_at": datetime.now(UTC).isoformat(),
    }


def _eligible_columns(selected_columns: Iterable[Mapping[str, Any]]) -> list[JsonObject]:
    return [
        dict(column)
        for column in selected_columns
        if column.get("column_key")
        and not column.get("excluded")
        and not (
            column.get("requires_human_confirm")
            and not column.get("human_confirmed")
            and column.get("restricted")
        )
    ]


def _pending_restricted_columns(selected_columns: Iterable[Mapping[str, Any]]) -> list[JsonObject]:
    return [
        {
            "column_key": column.get("column_key", ""),
            "reason": "Restricted column requires Human Confirm before final weighting.",
        }
        for column in selected_columns
        if column.get("column_key")
        and column.get("restricted")
        and column.get("requires_human_confirm")
        and not column.get("human_confirmed")
    ]


def _columns_by_rule(columns: Iterable[Mapping[str, Any]]) -> dict[str, list[JsonObject]]:
    result: dict[str, list[JsonObject]] = {}
    for column in columns:
        for rule_key in _rule_keys(column):
            result.setdefault(rule_key, [])
            if column not in result[rule_key]:
                result[rule_key].append(dict(column))
    return result


def _raw_scores_by_column(
    columns: Iterable[Mapping[str, Any]],
    *,
    columns_by_rule: Mapping[str, list[JsonObject]],
    rule_configs: Mapping[str, Any],
) -> tuple[dict[str, float], dict[str, list[JsonObject]]]:
    raw_scores: dict[str, float] = {}
    breakdown_by_column: dict[str, list[JsonObject]] = {}
    for column in columns:
        column_key = str(column.get("column_key", ""))
        if not column_key:
            continue
        raw_scores.setdefault(column_key, 0.0)
        breakdown_by_column.setdefault(column_key, [])
        for rule_key in _rule_keys(column):
            rule_weight = float(
                rule_configs.get(rule_key, {}).get("default_weight", DEFAULT_RULE_WEIGHT)
            )
            rule_column_count = max(len(columns_by_rule.get(rule_key, [])), 1)
            score_share = rule_weight / rule_column_count
            raw_scores[column_key] += score_share
            breakdown_by_column[column_key].append(
                {
                    "rule_key": rule_key,
                    "rule_default_weight": rule_weight,
                    "rule_column_count": rule_column_count,
                    "score_share": round(score_share, 8),
                    "description": rule_configs.get(rule_key, {}).get("description", ""),
                }
            )
    return raw_scores, breakdown_by_column


def _rule_keys(column: Mapping[str, Any]) -> list[str]:
    return _unique_strings(str(column.get("rule_key", "")).split("+"))


def _column_by_key(columns: Iterable[Mapping[str, Any]]) -> dict[str, JsonObject]:
    return {
        str(column["column_key"]): dict(column) for column in columns if column.get("column_key")
    }


def _weight_reason(
    *,
    column: Mapping[str, Any],
    weight: float,
    contributions: Iterable[Mapping[str, Any]],
) -> JsonObject:
    rule_keys = [str(item.get("rule_key", "")) for item in contributions if item.get("rule_key")]
    return {
        "weight": weight,
        "reason": (
            "Project comparison criterion selected after Human Confirm. "
            f"Rule contribution(s): {', '.join(rule_keys)}. "
            "This weight ranks employee DB comparison criteria for this project; "
            "it is not an employee performance or personal evaluation score. "
            f"Selection reason: {column.get('reason', 'Selected by confirmed requirement rules.')}"
        ),
        "source_feature_keys": list(column.get("source_feature_keys", [])),
        "source_constraint_keys": list(column.get("source_constraint_keys", [])),
    }


def _column_breakdown(
    *,
    column: Mapping[str, Any],
    raw_score: float,
    normalized_weight: float,
    contributions: list[JsonObject],
) -> JsonObject:
    return {
        "column_key": column.get("column_key", ""),
        "source": column.get("source", ""),
        "name": column.get("name", ""),
        "raw_score": round(raw_score, 8),
        "normalized_weight": normalized_weight,
        "rule_contributions": contributions,
        "source_feature_keys": list(column.get("source_feature_keys", [])),
        "source_constraint_keys": list(column.get("source_constraint_keys", [])),
        "restricted": bool(column.get("restricted")),
        "human_confirmed": bool(column.get("human_confirmed")),
        "comparison_scope": "project_requirements_to_employee_db_columns",
    }


def _normalize_scores(raw_scores: Mapping[str, float]) -> dict[str, float]:
    total = sum(raw_scores.values())
    if total <= 0:
        return {}
    normalized = {
        column_key: round(score / total, 6) for column_key, score in sorted(raw_scores.items())
    }
    if normalized:
        highest_key = max(normalized, key=normalized.get)
        normalized[highest_key] = round(
            normalized[highest_key] + (1.0 - sum(normalized.values())),
            6,
        )
    return normalized


def _unique_strings(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
