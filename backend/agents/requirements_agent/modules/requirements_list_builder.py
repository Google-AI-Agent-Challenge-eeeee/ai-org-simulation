"""Final Requirements_List builder for Requirements Agent."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]

REQUIRED_FIELDS = (
    "project_name",
    "project_goal",
    "required_features",
    "required_roles",
    "required_skills",
    "duration_weeks",
    "budget",
    "constraints",
    "risk_factors",
    "selected_employee_columns",
    "column_weights",
    "column_priority_order",
    "weighting_reason",
    "unknown_requirements",
    "missing_extractions",
    "missing_fields",
    "low_confidence_items",
    "coverage_check",
)
FINAL_FEATURE_STATUSES = {"mapped", "confirmed", "human_confirmed", "system_confirmed"}
FINAL_REVIEW_STATUSES = {
    "manual_review_required",
    "needs_user_input",
    "removed",
    "accepted",
    "rejected",
}
REVIEW_ITEM_KEYS = {
    "item_id",
    "text",
    "item_type",
    "source_evidence",
    "confidence",
    "reason",
    "status",
    "suggested_mapping",
}
MISSING_FIELD_KEYS = {"field", "reason", "severity", "suggested_question"}
SELECTED_COLUMN_KEYS = {
    "source",
    "name",
    "column_key",
    "rule_key",
    "source_feature_keys",
    "source_constraint_keys",
    "reason",
    "selection_stage",
    "restricted",
    "requires_human_confirm",
}


class RequirementsSchemaValidationError(ValueError):
    """Raised when Requirements_List does not satisfy the local JSON schema."""


def load_json(path: str | Path) -> JsonObject:
    """Load a JSON reference or schema file as a dictionary."""

    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def build_requirements_list(
    *,
    mapped_requirements: Mapping[str, Any],
    column_selection_draft: Mapping[str, Any],
    column_weighting_result: Mapping[str, Any],
    coverage_check: Mapping[str, Any],
    project_fields: Mapping[str, Any] | None = None,
    validation_result: Mapping[str, Any] | None = None,
    requirements_list_id: str = "requirements_list_draft",
) -> JsonObject:
    """Build the final Requirements_List-compatible dictionary.

    Final requirement fields only contain confirmed/system-confirmed data.
    Unknown, invalid, missing, or low-confidence items stay in review buckets
    and are never promoted into required_features/roles/skills/constraints.
    """

    project_fields = project_fields or {}
    validation_result = validation_result or {}
    status = _status(mapped_requirements, validation_result, column_weighting_result)
    meta = {
        "requirements_list_id": requirements_list_id,
        "project_id": mapped_requirements.get("_meta", {}).get("project_id"),
        "pipeline_version": "0.1.0",
        "status": status,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "taxonomy_version": mapped_requirements.get("_meta", {}).get("taxonomy_version"),
        "rulebase_version": mapped_requirements.get("_meta", {}).get("rulebase_version"),
        "column_rules_version": column_selection_draft.get("_meta", {}).get("column_rules_version"),
    }
    result: JsonObject = {
        "_meta": {key: value for key, value in meta.items() if value is not None},
        "project_name": project_fields.get("project_name", ""),
        "project_goal": project_fields.get("project_goal", ""),
        "required_features": _required_features(mapped_requirements),
        "required_roles": _required_roles(mapped_requirements),
        "required_skills": _required_skills(mapped_requirements),
        "duration_weeks": project_fields.get("duration_weeks"),
        "budget": project_fields.get("budget"),
        "constraints": _constraints(mapped_requirements),
        "risk_factors": _risk_factors(mapped_requirements),
        "selected_employee_columns": _selected_employee_columns(column_selection_draft),
        "column_weights": dict(column_weighting_result.get("column_weights", {})),
        "column_priority_order": list(column_weighting_result.get("column_priority_order", [])),
        "weighting_reason": _weighting_reason(column_weighting_result),
        "unknown_requirements": _review_items(mapped_requirements.get("unknown_requirements", [])),
        "missing_extractions": _review_items(validation_result.get("missing_extractions", [])),
        "missing_fields": _missing_fields(validation_result.get("missing_fields", [])),
        "low_confidence_items": _low_confidence_items(mapped_requirements, validation_result),
        "coverage_check": _coverage_check(coverage_check),
    }
    invalid_items = _review_items(validation_result.get("invalid_items", []))
    if invalid_items and status != "completed":
        result["invalid_items"] = invalid_items
    return result


def validate_required_fields(
    requirements_list: Mapping[str, Any],
    schema: Mapping[str, Any] | None = None,
) -> list[str]:
    """Return missing required fields using the local schema contract."""

    required = tuple(schema.get("required", REQUIRED_FIELDS)) if schema else REQUIRED_FIELDS
    return [field for field in required if field not in requirements_list]


def ensure_valid_requirements_list(
    requirements_list: Mapping[str, Any],
    schema: Mapping[str, Any] | None = None,
) -> None:
    """Raise ValueError when required fields or schema contracts are invalid."""

    missing = validate_required_fields(requirements_list, schema)
    if missing:
        raise ValueError(f"Requirements_List is missing required fields: {', '.join(missing)}")
    if schema:
        validate_against_schema(requirements_list, schema)


def validate_against_schema(
    value: Any,
    schema: Mapping[str, Any],
) -> None:
    """Validate Requirements_List against the bundled JSON schema subset."""

    _validate_schema_node(value, schema, root_schema=schema, path="$")


def _status(
    mapped_requirements: Mapping[str, Any],
    validation_result: Mapping[str, Any],
    column_weighting_result: Mapping[str, Any],
) -> str:
    if column_weighting_result.get("status") == "needs_human_confirm":
        return "needs_human_confirm"
    review_groups = (
        mapped_requirements.get("unknown_requirements", []),
        mapped_requirements.get("conflict_items", []),
        mapped_requirements.get("low_confidence_items", []),
        validation_result.get("missing_extractions", []),
        validation_result.get("invalid_items", []),
        validation_result.get("low_confidence_items", []),
        validation_result.get("missing_fields", []),
    )
    if any(review_groups):
        return "needs_human_confirm"
    return "completed"


def _required_features(mapped_requirements: Mapping[str, Any]) -> list[JsonObject]:
    features: list[JsonObject] = []
    for feature in mapped_requirements.get("mapped_features", []):
        if feature.get("status") not in FINAL_FEATURE_STATUSES:
            continue
        source_evidence = _source_evidence_items(feature.get("source_evidence", []))
        if not source_evidence:
            continue
        features.append(
            {
                "feature_key": feature.get("feature_key", ""),
                "standard_name": feature.get("standard_name", ""),
                "category": feature.get("category"),
                "raw_texts": [feature.get("raw_text", "")] if feature.get("raw_text") else [],
                "requirement_types": [],
                "source_evidence": source_evidence,
                "confidence": float(feature.get("confidence", 0.0)),
                "status": (
                    "human_confirmed"
                    if feature.get("status") == "human_confirmed"
                    else "system_confirmed"
                ),
            }
        )
    return features


def _required_roles(mapped_requirements: Mapping[str, Any]) -> list[JsonObject]:
    roles: list[JsonObject] = []
    confirmed_feature_keys = _confirmed_feature_keys(mapped_requirements)
    for role in mapped_requirements.get("required_roles", []):
        source_feature_keys = list(role.get("source_feature_keys", []))
        if source_feature_keys and not set(source_feature_keys) & confirmed_feature_keys:
            continue
        roles.append(
            {
                "role": role.get("name", ""),
                "job_category_codes": list(role.get("job_category_codes", [])),
                "role_type": role.get("role_type", "staffing"),
                "source_feature_keys": source_feature_keys,
                "reason": role.get("reason", ""),
            }
        )
    return roles


def _required_skills(mapped_requirements: Mapping[str, Any]) -> list[JsonObject]:
    skills: list[JsonObject] = []
    confirmed_feature_keys = _confirmed_feature_keys(mapped_requirements)
    for skill in mapped_requirements.get("required_skills", []):
        source_feature_keys = list(skill.get("source_feature_keys", []))
        if source_feature_keys and not set(source_feature_keys) & confirmed_feature_keys:
            continue
        skills.append(
            {
                "skill": skill.get("name", ""),
                "source_feature_keys": source_feature_keys,
                "reason": skill.get("reason", ""),
            }
        )
    return skills


def _constraints(mapped_requirements: Mapping[str, Any]) -> list[JsonObject]:
    constraints: list[JsonObject] = []
    for constraint in mapped_requirements.get("constraints", []):
        if constraint.get("status") not in FINAL_FEATURE_STATUSES:
            continue
        source_evidence = _source_evidence_items(constraint.get("source_evidence", []))
        if not source_evidence:
            continue
        constraints.append(
            {
                "constraint_key": constraint.get("constraint_key", ""),
                "text": constraint.get("text", ""),
                "constraint_type": constraint.get("constraint_type", "other"),
                "source_evidence": source_evidence,
                "confidence": float(constraint.get("confidence", 0.0)),
                "status": (
                    "human_confirmed"
                    if constraint.get("status") == "human_confirmed"
                    else "system_confirmed"
                ),
            }
        )
    return constraints


def _risk_factors(mapped_requirements: Mapping[str, Any]) -> list[JsonObject]:
    risks: list[JsonObject] = []
    confirmed_feature_keys = _confirmed_feature_keys(mapped_requirements)
    for risk in mapped_requirements.get("risk_factors", []):
        source_feature_keys = list(risk.get("source_feature_keys", []))
        if source_feature_keys and not set(source_feature_keys) & confirmed_feature_keys:
            continue
        risks.append(
            {
                "risk_key": risk.get("risk_key", ""),
                "text": risk.get("text", ""),
                "source_feature_keys": source_feature_keys,
                "severity": risk.get("severity", "medium"),
                "reason": risk.get("reason", ""),
            }
        )
    return risks


def _low_confidence_items(
    mapped_requirements: Mapping[str, Any],
    validation_result: Mapping[str, Any],
) -> list[JsonObject]:
    return _review_items(
        [
            *mapped_requirements.get("low_confidence_items", []),
            *validation_result.get("low_confidence_items", []),
        ]
    )


def _confirmed_feature_keys(mapped_requirements: Mapping[str, Any]) -> set[str]:
    return {
        str(feature.get("feature_key"))
        for feature in mapped_requirements.get("mapped_features", [])
        if feature.get("feature_key") and feature.get("status") in FINAL_FEATURE_STATUSES
    }


def _selected_employee_columns(column_selection_draft: Mapping[str, Any]) -> list[JsonObject]:
    columns: list[JsonObject] = []
    for column in column_selection_draft.get("selected_employee_columns", []):
        normalized = {key: column[key] for key in SELECTED_COLUMN_KEYS if key in column}
        normalized["selection_stage"] = "final"
        columns.append(normalized)
    return columns


def _weighting_reason(column_weighting_result: Mapping[str, Any]) -> JsonObject:
    return {
        column_key: {
            "weight": reason.get("weight", 0.0),
            "reason": reason.get("reason", ""),
            "source_feature_keys": list(reason.get("source_feature_keys", [])),
            "source_constraint_keys": list(reason.get("source_constraint_keys", [])),
        }
        for column_key, reason in column_weighting_result.get("weighting_reason", {}).items()
    }


def _review_items(items: Iterable[Mapping[str, Any]]) -> list[JsonObject]:
    result: list[JsonObject] = []
    for item in items:
        normalized = {key: item[key] for key in REVIEW_ITEM_KEYS if key in item}
        if not normalized.get("text"):
            continue
        normalized["reason"] = normalized.get("reason", "Requires Human Confirm.")
        normalized["status"] = (
            normalized.get("status")
            if normalized.get("status") in FINAL_REVIEW_STATUSES
            else "manual_review_required"
        )
        if "source_evidence" in normalized:
            normalized["source_evidence"] = _source_evidence_items(normalized["source_evidence"])
        if "confidence" in normalized:
            normalized["confidence"] = _confidence(normalized["confidence"])
        result.append(normalized)
    return result


def _missing_fields(items: Iterable[Mapping[str, Any]]) -> list[JsonObject]:
    return [
        {key: item[key] for key in MISSING_FIELD_KEYS if key in item}
        for item in items
        if item.get("field") and item.get("reason")
    ]


def _coverage_check(coverage_check: Mapping[str, Any]) -> JsonObject:
    return {
        "overall_status": coverage_check.get("overall_status", "missing"),
        "sections": [
            {
                "section_id": section.get("section_id", ""),
                "section_title": section.get("section_title", ""),
                "status": section.get("status", "missing"),
                "mapped_item_ids": list(section.get("mapped_item_ids", [])),
                "reason": section.get("reason", ""),
            }
            for section in coverage_check.get("sections", [])
        ],
        "notes": list(coverage_check.get("notes", [])),
    }


def _source_evidence_items(items: Iterable[Mapping[str, Any]]) -> list[JsonObject]:
    return [_source_evidence_item(item) for item in items if item.get("text")]


def _source_evidence_item(item: Mapping[str, Any]) -> JsonObject:
    allowed_keys = {
        "evidence_id",
        "document_id",
        "document_type",
        "section_id",
        "section_title",
        "chunk_id",
        "source_range",
        "text",
    }
    normalized = {key: item[key] for key in allowed_keys if key in item and item[key] is not None}
    normalized["evidence_id"] = str(normalized.get("evidence_id") or normalized.get("text", ""))
    normalized["text"] = str(normalized.get("text", ""))
    if "source_range" in normalized:
        normalized["source_range"] = _source_range(normalized["source_range"])
    return normalized


def _source_range(source_range: Mapping[str, Any]) -> JsonObject:
    allowed = {"page", "start_char", "end_char", "start_line", "end_line"}
    return {key: source_range[key] for key in allowed if key in source_range}


def _confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(confidence, 1.0))


def _validate_schema_node(
    value: Any,
    schema: Mapping[str, Any],
    *,
    root_schema: Mapping[str, Any],
    path: str,
) -> None:
    if "$ref" in schema:
        return _validate_schema_node(
            value,
            _resolve_ref(str(schema["$ref"]), root_schema),
            root_schema=root_schema,
            path=path,
        )
    if "oneOf" in schema:
        errors = []
        for option in schema["oneOf"]:
            try:
                _validate_schema_node(value, option, root_schema=root_schema, path=path)
                return
            except RequirementsSchemaValidationError as exc:
                errors.append(str(exc))
        raise RequirementsSchemaValidationError(f"{path} did not match oneOf: {errors[:3]}")
    if "const" in schema and value != schema["const"]:
        raise RequirementsSchemaValidationError(f"{path} must be {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise RequirementsSchemaValidationError(f"{path} must be one of {schema['enum']!r}")

    expected_type = schema.get("type")
    if expected_type is not None:
        _validate_type(value, expected_type, path)

    if isinstance(value, dict):
        _validate_object(value, schema, root_schema=root_schema, path=path)
    elif isinstance(value, list):
        _validate_array(value, schema, root_schema=root_schema, path=path)
    elif isinstance(value, str):
        _validate_string(value, schema, path)
    elif isinstance(value, int | float) and not isinstance(value, bool):
        _validate_number(value, schema, path)


def _validate_object(
    value: Mapping[str, Any],
    schema: Mapping[str, Any],
    *,
    root_schema: Mapping[str, Any],
    path: str,
) -> None:
    required = schema.get("required", [])
    missing = [key for key in required if key not in value]
    if missing:
        raise RequirementsSchemaValidationError(f"{path} missing required keys: {missing}")
    properties = schema.get("properties", {})
    additional = schema.get("additionalProperties", True)
    for key, item in value.items():
        child_path = f"{path}.{key}"
        if key in properties:
            _validate_schema_node(
                item,
                properties[key],
                root_schema=root_schema,
                path=child_path,
            )
        elif additional is False:
            raise RequirementsSchemaValidationError(f"{child_path} is not allowed by schema")
        elif isinstance(additional, Mapping):
            _validate_schema_node(
                item,
                additional,
                root_schema=root_schema,
                path=child_path,
            )


def _validate_array(
    value: list[Any],
    schema: Mapping[str, Any],
    *,
    root_schema: Mapping[str, Any],
    path: str,
) -> None:
    if "minItems" in schema and len(value) < int(schema["minItems"]):
        raise RequirementsSchemaValidationError(
            f"{path} must contain at least {schema['minItems']} item(s)"
        )
    if schema.get("uniqueItems"):
        serialized = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
        if len(serialized) != len(set(serialized)):
            raise RequirementsSchemaValidationError(f"{path} contains duplicate items")
    if "items" not in schema:
        return
    for index, item in enumerate(value):
        _validate_schema_node(
            item,
            schema["items"],
            root_schema=root_schema,
            path=f"{path}[{index}]",
        )


def _validate_string(value: str, schema: Mapping[str, Any], path: str) -> None:
    if "minLength" in schema and len(value) < int(schema["minLength"]):
        raise RequirementsSchemaValidationError(f"{path} is shorter than minLength")
    if "pattern" in schema and not re.match(str(schema["pattern"]), value):
        raise RequirementsSchemaValidationError(
            f"{path} does not match pattern {schema['pattern']!r}"
        )


def _validate_number(value: int | float, schema: Mapping[str, Any], path: str) -> None:
    if "minimum" in schema and value < float(schema["minimum"]):
        raise RequirementsSchemaValidationError(f"{path} must be >= {schema['minimum']}")
    if "maximum" in schema and value > float(schema["maximum"]):
        raise RequirementsSchemaValidationError(f"{path} must be <= {schema['maximum']}")
    if "exclusiveMinimum" in schema and value <= float(schema["exclusiveMinimum"]):
        raise RequirementsSchemaValidationError(f"{path} must be > {schema['exclusiveMinimum']}")


def _validate_type(value: Any, expected_type: str | list[str], path: str) -> None:
    expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
    if any(_matches_type(value, item_type) for item_type in expected_types):
        return
    raise RequirementsSchemaValidationError(
        f"{path} expected type {expected_types}, got {type(value).__name__}"
    )


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "null":
        return value is None
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    return True


def _resolve_ref(ref: str, root_schema: Mapping[str, Any]) -> Mapping[str, Any]:
    if not ref.startswith("#/"):
        raise RequirementsSchemaValidationError(f"Unsupported schema ref: {ref}")
    node: Any = root_schema
    for part in ref[2:].split("/"):
        node = node[part]
    return node
