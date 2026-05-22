"""Draft employee-column selection for Requirements Agent.

The functions here select comparison criteria only. They do not evaluate
individual employees and they do not finalize weights.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]

MAPPED_STATUSES = {"mapped", "confirmed", "human_confirmed", "system_confirmed"}

CONSTRAINT_RULE_MAPPING = {
    "short_timeline": ["availability_schedule", "delivery_reliability", "risk_stability"],
    "budget_limited": ["cost_budget"],
    "high_reliability": ["delivery_reliability", "quality_assurance", "risk_stability"],
    "performance_target": ["delivery_reliability", "quality_assurance", "technical_execution"],
    "availability_target": ["delivery_reliability", "risk_stability"],
    "security_privacy_requirement": ["technical_execution", "quality_assurance", "risk_stability"],
    "retention_data_policy": ["technical_execution", "quality_assurance", "risk_stability"],
    "business_rule_constraint": ["technical_execution", "quality_assurance", "risk_stability"],
    "platform_guideline_constraint": ["technical_execution", "quality_assurance"],
    "rollout_release_constraint": [
        "availability_schedule",
        "delivery_reliability",
        "risk_stability",
    ],
    "external_dependency": ["collaboration_communication", "delivery_reliability", "risk_stability"],
    "open_question": ["collaboration_communication", "delivery_reliability"],
    "scope_exclusion": ["delivery_reliability"],
    "priority_requirement": ["delivery_reliability"],
}


def load_json(path: str | Path) -> JsonObject:
    """Load a JSON reference file as a dictionary."""

    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def select_columns_draft(
    mapped_requirements: Mapping[str, Any],
    employee_column_rules: Mapping[str, Any],
    *,
    draft_id: str = "column_selection_draft",
) -> JsonObject:
    """Select draft employee/activity columns from mapped requirements.

    This phase only chooses candidate comparison columns and explains why they
    were selected. It intentionally does not emit column weights, priority
    order, or final weighting reasons.
    """

    selected_by_key: dict[str, JsonObject] = {}
    selection_by_rule: dict[str, JsonObject] = {}
    rule_validation_warnings = validate_employee_column_rules(employee_column_rules)
    notes: list[str] = []
    selected_feature_keys: list[str] = []
    selected_constraint_keys: list[str] = []

    for feature in mapped_requirements.get("mapped_features", []):
        if feature.get("status") not in MAPPED_STATUSES:
            continue
        feature_key = feature.get("feature_key")
        if feature_key:
            selected_feature_keys.append(feature_key)
        rule_keys = _rules_for_feature(feature_key, employee_column_rules)
        if feature_key and not rule_keys:
            notes.append(f"No column rules are configured for feature '{feature_key}'.")
        for rule_key in _rules_for_feature(feature_key, employee_column_rules):
            _add_rule_columns(
                selected_by_key,
                selection_by_rule,
                employee_column_rules,
                rule_key=rule_key,
                source_feature_key=feature_key,
                warnings=rule_validation_warnings,
            )

    for constraint in mapped_requirements.get("constraints", []):
        if constraint.get("status") not in MAPPED_STATUSES:
            continue
        constraint_key = constraint.get("constraint_key")
        if constraint_key:
            selected_constraint_keys.append(constraint_key)
        rule_keys = CONSTRAINT_RULE_MAPPING.get(constraint_key, [])
        if constraint_key and not rule_keys:
            notes.append(f"No column rules are configured for constraint '{constraint_key}'.")
        for rule_key in rule_keys:
            _add_rule_columns(
                selected_by_key,
                selection_by_rule,
                employee_column_rules,
                rule_key=rule_key,
                source_constraint_key=constraint_key,
                warnings=rule_validation_warnings,
            )

    selected_columns = list(selected_by_key.values())
    restricted_columns = [
        column
        for column in selected_columns
        if column.get("restricted") or column.get("requires_human_confirm")
    ]
    excluded_columns = _excluded_columns(employee_column_rules)
    data_gap_columns = _data_gap_columns(employee_column_rules)

    if not selected_columns:
        notes.append(
            "No columns were selected because no mapped features or constraints were provided."
        )
    if mapped_requirements.get("unknown_requirements"):
        notes.append(
            "Unknown requirements were ignored for column selection until Human Confirm maps them."
        )
    rule_validation_warnings = _dedupe_warnings(rule_validation_warnings)

    return {
        "_meta": {
            "draft_id": draft_id,
            "mapped_requirements_id": mapped_requirements.get("_meta", {}).get(
                "mapped_requirements_id"
            ),
            "pipeline_phase": "column_selection_draft",
            "status": "draft",
            "column_rules_version": employee_column_rules.get("_meta", {}).get(
                "version",
                "unknown",
            ),
            "created_at": datetime.now(UTC).isoformat(),
        },
        "status": "draft",
        "selected_employee_columns": selected_columns,
        "selection_by_requirement_type": list(selection_by_rule.values()),
        "restricted_columns_needing_human_confirm": restricted_columns,
        "excluded_columns": excluded_columns,
        "data_gap_columns": data_gap_columns,
        "rule_validation_warnings": rule_validation_warnings,
        "selection_stats": {
            "mapped_feature_count": len(_unique_strings(selected_feature_keys)),
            "mapped_constraint_count": len(_unique_strings(selected_constraint_keys)),
            "selected_column_count": len(selected_columns),
            "restricted_column_count": len(restricted_columns),
            "excluded_column_count": len(excluded_columns),
            "data_gap_column_count": len(data_gap_columns),
            "unknown_requirement_count": len(mapped_requirements.get("unknown_requirements", [])),
            "rule_warning_count": len(rule_validation_warnings),
            "column_weight_finalized": False,
        },
        "notes": notes,
    }


def validate_employee_column_rules(employee_column_rules: Mapping[str, Any]) -> list[JsonObject]:
    """Return non-blocking validation warnings for employee column rules."""

    warnings: list[JsonObject] = []
    for rule_key, rule in employee_column_rules.get("requirement_type_rules", {}).items():
        for column in rule.get("columns", []):
            source = column.get("source")
            name = column.get("name")
            if not source or not name:
                warnings.append(
                    {
                        "rule_key": rule_key,
                        "column_key": "",
                        "reason": "Rule column must include both source and name.",
                    }
                )
                continue
            column_key = f"{source}.{name}"
            policy = _column_policy(employee_column_rules, source, name)
            if policy in {"unknown_source", "unknown_column", "excluded", "unavailable"}:
                warnings.append(
                    {
                        "rule_key": rule_key,
                        "column_key": column_key,
                        "reason": f"Rule references a {policy.replace('_', ' ')}.",
                    }
                )
    return _dedupe_warnings(warnings)


def _rules_for_feature(
    feature_key: str | None, employee_column_rules: Mapping[str, Any]
) -> list[str]:
    if not feature_key:
        return []
    return list(employee_column_rules.get("feature_rule_mapping", {}).get(feature_key, []))


def _add_rule_columns(
    selected_by_key: dict[str, JsonObject],
    selection_by_rule: dict[str, JsonObject],
    employee_column_rules: Mapping[str, Any],
    *,
    rule_key: str,
    source_feature_key: str | None = None,
    source_constraint_key: str | None = None,
    warnings: list[JsonObject],
) -> None:
    rule = employee_column_rules.get("requirement_type_rules", {}).get(rule_key)
    if not rule:
        warnings.append(
            {
                "rule_key": rule_key,
                "column_key": "",
                "reason": "Mapped requirement references a missing column rule.",
            }
        )
        return
    for column in rule.get("columns", []):
        source = column.get("source")
        name = column.get("name")
        if not source or not name:
            continue
        column_key = f"{source}.{name}"
        policy = _column_policy(employee_column_rules, source, name)
        if policy in {"unknown_source", "unknown_column", "excluded", "unavailable"}:
            continue
        restricted = policy == "restricted"
        requires_human_confirm = bool(rule.get("requires_human_confirm")) or restricted
        reason = _selection_reason(
            rule_key,
            rule,
            column,
            source_feature_key=source_feature_key,
            source_constraint_key=source_constraint_key,
        )
        if column_key not in selected_by_key:
            selected_by_key[column_key] = {
                "source": source,
                "name": name,
                "column_key": column_key,
                "rule_key": rule_key,
                "source_feature_keys": [],
                "source_constraint_keys": [],
                "reason": reason,
                "selection_stage": "draft",
                "restricted": restricted,
                "requires_human_confirm": requires_human_confirm,
            }
        entry = selected_by_key[column_key]
        entry["rule_key"] = _join_unique_rule_keys(entry["rule_key"], rule_key)
        if source_feature_key and source_feature_key not in entry["source_feature_keys"]:
            entry["source_feature_keys"].append(source_feature_key)
        if source_constraint_key and source_constraint_key not in entry["source_constraint_keys"]:
            entry["source_constraint_keys"].append(source_constraint_key)
        if reason not in entry["reason"]:
            entry["reason"] = f"{entry['reason']} | {reason}"
        entry["restricted"] = entry["restricted"] or restricted
        entry["requires_human_confirm"] = entry["requires_human_confirm"] or requires_human_confirm
        _record_selection_by_rule(
            selection_by_rule,
            rule_key,
            rule,
            column_key=column_key,
            source_feature_key=source_feature_key,
            source_constraint_key=source_constraint_key,
        )


def _selection_reason(
    rule_key: str,
    rule: Mapping[str, Any],
    column: Mapping[str, Any],
    *,
    source_feature_key: str | None,
    source_constraint_key: str | None,
) -> str:
    reason = column.get("reason") or rule.get("description") or "Selected by requirement rule."
    source_parts = []
    if source_feature_key:
        source_parts.append(f"feature={source_feature_key}")
    if source_constraint_key:
        source_parts.append(f"constraint={source_constraint_key}")
    source_text = f" ({', '.join(source_parts)})" if source_parts else ""
    return f"{rule_key}: {reason}{source_text}"


def _record_selection_by_rule(
    selection_by_rule: dict[str, JsonObject],
    rule_key: str,
    rule: Mapping[str, Any],
    *,
    column_key: str,
    source_feature_key: str | None,
    source_constraint_key: str | None,
) -> None:
    entry = selection_by_rule.setdefault(
        rule_key,
        {
            "rule_key": rule_key,
            "description": rule.get("description", ""),
            "source_feature_keys": [],
            "source_constraint_keys": [],
            "column_keys": [],
        },
    )
    if source_feature_key and source_feature_key not in entry["source_feature_keys"]:
        entry["source_feature_keys"].append(source_feature_key)
    if source_constraint_key and source_constraint_key not in entry["source_constraint_keys"]:
        entry["source_constraint_keys"].append(source_constraint_key)
    if column_key not in entry["column_keys"]:
        entry["column_keys"].append(column_key)


def _join_unique_rule_keys(existing_rule_key: str, new_rule_key: str) -> str:
    return "+".join(_unique_strings([*existing_rule_key.split("+"), new_rule_key]))


def _column_policy(
    employee_column_rules: Mapping[str, Any],
    source: str,
    name: str,
) -> str:
    source_config = employee_column_rules.get("column_sources", {}).get(source)
    if not source_config:
        return "unknown_source"
    if _is_unavailable_column(employee_column_rules, source, name):
        return "unavailable"
    if name in set(source_config.get("excluded_by_default_columns", [])):
        return "excluded"
    if name in set(source_config.get("restricted_columns", [])):
        return "restricted"
    if name in set(source_config.get("safe_default_columns", [])):
        return "safe_default"
    return "unknown_column"


def _is_restricted_column(
    employee_column_rules: Mapping[str, Any],
    source: str,
    name: str,
) -> bool:
    source_config = employee_column_rules.get("column_sources", {}).get(source, {})
    return name in set(source_config.get("restricted_columns", []))


def _is_unavailable_column(
    employee_column_rules: Mapping[str, Any],
    source: str,
    name: str,
) -> bool:
    names = {
        str(column.get("column", ""))
        for column in employee_column_rules.get("not_available_columns", [])
    }
    return name in names or f"{source}.{name}" in names


def _excluded_columns(employee_column_rules: Mapping[str, Any]) -> list[JsonObject]:
    excluded: list[JsonObject] = []
    for source, source_config in employee_column_rules.get("column_sources", {}).items():
        for name in source_config.get("excluded_by_default_columns", []):
            excluded.append(
                {
                    "column_key": f"{source}.{name}",
                    "reason": "Excluded by default by employee_column_rules reference.",
                }
            )
    return excluded


def _data_gap_columns(employee_column_rules: Mapping[str, Any]) -> list[JsonObject]:
    gaps: list[JsonObject] = []
    for column in employee_column_rules.get("not_available_columns", []):
        gaps.append(
            {
                "column_key": column.get("column", ""),
                "reason": column.get("reason", "Column is not available in current data."),
            }
        )
    return gaps


def selected_column_keys(column_selection_draft: Mapping[str, Any]) -> list[str]:
    """Return selected column keys in draft order."""

    return [
        column["column_key"]
        for column in column_selection_draft.get("selected_employee_columns", [])
        if column.get("column_key")
    ]


def iter_selected_columns(column_selection_draft: Mapping[str, Any]) -> Iterable[JsonObject]:
    """Yield selected employee columns as dictionaries."""

    for column in column_selection_draft.get("selected_employee_columns", []):
        yield dict(column)


def _dedupe_warnings(warnings: Iterable[Mapping[str, Any]]) -> list[JsonObject]:
    deduped: dict[tuple[str, str, str], JsonObject] = {}
    for warning in warnings:
        key = (
            str(warning.get("rule_key", "")),
            str(warning.get("column_key", "")),
            str(warning.get("reason", "")),
        )
        deduped[key] = dict(warning)
    return list(deduped.values())


def _unique_strings(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
