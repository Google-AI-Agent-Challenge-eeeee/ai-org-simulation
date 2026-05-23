"""Build Shadow RolePlay handoff inputs from Requirements Agent output."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    RequirementsList as RoleplayRequirementsList,
)

JsonObject = dict[str, Any]

ROLEPLAY_ROLE_ALIASES = {
    "Product Manager": "PM",
    "Product Lead": "PM",
    "Backend Engineer": "Backend Developer",
    "Backend Lead": "Backend Developer",
    "Web Frontend Engineer": "Frontend Developer",
    "Frontend Lead": "Frontend Developer",
    "Infrastructure Engineer": "DevOps Engineer",
    "Data Engineer": "Backend Developer",
}

DEFAULT_PROJECT_ID = "requirements_project"
DEFAULT_TOTAL_SPRINT_DAYS = 10
DEFAULT_ASSIGNED_ROLE = "PM"


def build_roleplay_requirements_input(
    requirements_list: Mapping[str, Any],
) -> JsonObject:
    """Convert final Requirements_List into Shadow RolePlay RequirementsList input."""

    required_features = list(requirements_list.get("required_features", []))
    feature_keys = [
        _feature_id(feature, index)
        for index, feature in enumerate(required_features, start=1)
    ]
    total_sprint_days = _total_sprint_days(requirements_list, len(required_features))
    estimated_days_by_feature = _estimated_days_by_feature(
        required_features,
        total_sprint_days=total_sprint_days,
    )
    role_names = _role_names(requirements_list.get("required_roles", []))
    skill_names = _skill_names(requirements_list.get("required_skills", []))
    roles_by_feature = _roles_by_feature(requirements_list.get("required_roles", []))
    skills_by_feature = _skills_by_feature(requirements_list.get("required_skills", []))
    risks_by_feature = _risks_by_feature(requirements_list.get("risk_factors", []))

    features: list[JsonObject] = []
    milestones: list[JsonObject] = []
    cumulative_due_day = 0
    for index, feature in enumerate(required_features, start=1):
        feature_id = _feature_id(feature, index)
        assigned_role = _first_or_default(
            roles_by_feature.get(feature.get("feature_key"), []),
            _first_or_default(role_names, DEFAULT_ASSIGNED_ROLE),
        )
        tech_requirements = skills_by_feature.get(feature.get("feature_key"), [])
        if not tech_requirements:
            tech_requirements = skill_names[:5]
        estimated_days = estimated_days_by_feature.get(feature_id, 1)
        cumulative_due_day = min(total_sprint_days, max(1, cumulative_due_day + estimated_days))
        feature_name = str(feature.get("standard_name") or feature.get("feature_key") or feature_id)

        features.append(
            {
                "feature_id": feature_id,
                "feature_name": feature_name,
                "priority": _feature_priority(feature, index),
                "assigned_role": assigned_role,
                "tech_requirements": tech_requirements,
                "dependencies": _feature_dependencies(feature_id, feature_keys, index),
                "estimated_days": estimated_days,
                "risk_notes": _risk_notes(risks_by_feature.get(feature.get("feature_key"), [])),
            }
        )
        milestones.append(
            {
                "name": f"{feature_name} complete",
                "due_day": cumulative_due_day,
                "owner_role": assigned_role,
            }
        )

    if not milestones:
        milestones.append(
            {
                "name": "Requirements review complete",
                "due_day": max(1, min(total_sprint_days, 1)),
                "owner_role": _first_or_default(role_names, DEFAULT_ASSIGNED_ROLE),
            }
        )
    release_owner = "PM" if "PM" in role_names else _first_or_default(role_names, DEFAULT_ASSIGNED_ROLE)
    if milestones[-1]["due_day"] < total_sprint_days:
        milestones.append(
            {
                "name": "Release readiness review",
                "due_day": total_sprint_days,
                "owner_role": release_owner,
            }
        )

    payload = {
        "project_id": _project_id(requirements_list),
        "project_name": _project_name(requirements_list),
        "project_summary": _project_summary(requirements_list, role_names, skill_names),
        "required_roles": role_names,
        "required_skills": skill_names,
        "features": features,
        "timeline": {
            "total_sprint_days": total_sprint_days,
            "milestones": milestones,
        },
        "constraints": _constraint_texts(requirements_list.get("constraints", [])),
        "risk_flags": _risk_flags(requirements_list.get("risk_factors", [])),
    }
    RoleplayRequirementsList.model_validate(payload)
    return payload


def build_roleplay_handoff_manifest(
    requirements_list: Mapping[str, Any],
    roleplay_requirements_input: Mapping[str, Any],
) -> JsonObject:
    """Describe which handoff inputs are ready and which must be produced later."""

    review_counts = {
        "unknown_requirements": len(requirements_list.get("unknown_requirements", [])),
        "missing_extractions": len(requirements_list.get("missing_extractions", [])),
        "missing_fields": len(requirements_list.get("missing_fields", [])),
        "low_confidence_items": len(requirements_list.get("low_confidence_items", [])),
        "invalid_items": len(requirements_list.get("invalid_items", [])),
    }
    return {
        "_meta": {
            "handoff_type": "requirements_agent_to_shadow_roleplay_agent",
            "created_at": datetime.now(UTC).isoformat(),
            "source_requirements_list_id": requirements_list.get("_meta", {}).get(
                "requirements_list_id"
            ),
            "source_requirements_status": requirements_list.get("_meta", {}).get("status"),
        },
        "handoff_status": (
            "ready_with_review_items"
            if any(review_counts.values())
            else "requirements_context_ready"
        ),
        "provided_inputs": [
            {
                "input_name": "requirements",
                "target_schema": "shadow_roleplay_agent.schemas.simulation_input.RequirementsList",
                "output_key": "roleplay_requirements_input",
                "recommended_filename": "Roleplay_Requirements_Input.json",
                "description": "Project context for Shadow RolePlay scenario planning.",
            }
        ],
        "required_downstream_inputs": [
            {
                "input_name": "selected_team",
                "target_schema": "SelectedTeamRecord",
                "producer": "team_builder_or_employee_fit_agent",
                "blocking_for_roleplay_execution": True,
            },
            {
                "input_name": "member_snapshots",
                "target_schema": "list[EmployeeFitProfileSnapshot]",
                "producer": "employee_fit_agent",
                "blocking_for_roleplay_execution": True,
            },
            {
                "input_name": "team_risk_summary",
                "target_schema": "TeamRiskSummary",
                "producer": "team_builder_or_risk_summary_agent",
                "blocking_for_roleplay_execution": True,
            },
            {
                "input_name": "evidence_metadata",
                "target_schema": "list[EvidenceMetadata]",
                "producer": "employee_fit_agent",
                "blocking_for_roleplay_execution": True,
            },
        ],
        "roleplay_requirements_summary": {
            "project_id": roleplay_requirements_input.get("project_id"),
            "project_name": roleplay_requirements_input.get("project_name"),
            "feature_count": len(roleplay_requirements_input.get("features", [])),
            "required_role_count": len(roleplay_requirements_input.get("required_roles", [])),
            "required_skill_count": len(roleplay_requirements_input.get("required_skills", [])),
            "risk_flag_count": len(roleplay_requirements_input.get("risk_flags", [])),
            "total_sprint_days": roleplay_requirements_input.get("timeline", {}).get(
                "total_sprint_days"
            ),
        },
        "review_counts": review_counts,
        "selected_employee_columns": list(requirements_list.get("selected_employee_columns", [])),
        "column_weights": dict(requirements_list.get("column_weights", {})),
        "column_priority_order": list(requirements_list.get("column_priority_order", [])),
    }


def _project_id(requirements_list: Mapping[str, Any]) -> str:
    project_id = requirements_list.get("_meta", {}).get("project_id")
    if project_id:
        return str(project_id)
    requirements_list_id = requirements_list.get("_meta", {}).get("requirements_list_id")
    if requirements_list_id:
        return str(requirements_list_id)
    project_name = _slug(_project_name(requirements_list))
    return project_name or DEFAULT_PROJECT_ID


def _project_name(requirements_list: Mapping[str, Any]) -> str:
    return str(requirements_list.get("project_name") or "Untitled Requirements Project").strip()


def _project_summary(
    requirements_list: Mapping[str, Any],
    role_names: list[str],
    skill_names: list[str],
) -> str:
    goal = str(requirements_list.get("project_goal") or "").strip()
    if goal:
        return goal
    feature_names = [
        str(feature.get("standard_name") or feature.get("feature_key"))
        for feature in requirements_list.get("required_features", [])[:3]
        if feature.get("standard_name") or feature.get("feature_key")
    ]
    parts = []
    if feature_names:
        parts.append(f"Core features: {', '.join(feature_names)}")
    if role_names:
        parts.append(f"Required roles: {', '.join(role_names[:5])}")
    if skill_names:
        parts.append(f"Key skills: {', '.join(skill_names[:8])}")
    return ". ".join(parts) or "Requirements context generated from PRD analysis."


def _role_names(required_roles: Iterable[Mapping[str, Any]]) -> list[str]:
    roles = [
        _roleplay_role_name(role.get("role"))
        for role in required_roles
        if role.get("role") and _is_staffing_role(role)
    ]
    if "PM" not in roles:
        roles.insert(0, "PM")
    return _unique_strings(roles)


def _is_staffing_role(role: Mapping[str, Any]) -> bool:
    role_type = str(role.get("role_type") or "staffing")
    role_name = str(role.get("role") or "")
    if role_name in {"Product Manager", "Product Lead", "PM"}:
        return True
    return role_type != "stakeholder"


def _skill_names(required_skills: Iterable[Mapping[str, Any]]) -> list[str]:
    return _unique_strings(
        str(skill.get("skill", "")).strip()
        for skill in required_skills
        if skill.get("skill")
    )


def _roles_by_feature(required_roles: Iterable[Mapping[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for role in required_roles:
        if not _is_staffing_role(role):
            continue
        role_name = _roleplay_role_name(role.get("role"))
        for feature_key in role.get("source_feature_keys", []):
            result.setdefault(str(feature_key), [])
            if role_name not in result[str(feature_key)]:
                result[str(feature_key)].append(role_name)
    return result


def _skills_by_feature(required_skills: Iterable[Mapping[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for skill in required_skills:
        skill_name = str(skill.get("skill", "")).strip()
        if not skill_name:
            continue
        for feature_key in skill.get("source_feature_keys", []):
            result.setdefault(str(feature_key), [])
            if skill_name not in result[str(feature_key)]:
                result[str(feature_key)].append(skill_name)
    return result


def _risks_by_feature(risk_factors: Iterable[Mapping[str, Any]]) -> dict[str, list[JsonObject]]:
    result: dict[str, list[JsonObject]] = {}
    for risk in risk_factors:
        for feature_key in risk.get("source_feature_keys", []):
            result.setdefault(str(feature_key), []).append(dict(risk))
    return result


def _feature_id(feature: Mapping[str, Any], index: int) -> str:
    value = str(feature.get("feature_key") or "").strip()
    return value or f"feat_{index:03d}"


def _feature_priority(feature: Mapping[str, Any], index: int) -> str:
    text = " ".join(
        [
            str(feature.get("feature_key", "")),
            str(feature.get("standard_name", "")),
            " ".join(str(raw) for raw in feature.get("raw_texts", [])),
            " ".join(str(req_type) for req_type in feature.get("requirement_types", [])),
        ]
    ).casefold()
    if any(marker in text for marker in ("p0", "must", "critical", "blocker", "필수", "핵심")):
        return "P0"
    if any(marker in text for marker in ("p2", "future", "optional", "nice to have", "추후")):
        return "P2"
    if any(marker in text for marker in ("p1", "should", "권장")):
        return "P1"
    confidence = _float(feature.get("confidence"), default=0.0)
    if confidence >= 0.9 or index <= 3:
        return "P0"
    if confidence >= 0.75 or index <= 6:
        return "P1"
    return "P2"


def _total_sprint_days(requirements_list: Mapping[str, Any], feature_count: int) -> int:
    duration_weeks = requirements_list.get("duration_weeks")
    if isinstance(duration_weeks, int | float) and duration_weeks > 0:
        return max(1, round(float(duration_weeks) * 5))
    if isinstance(duration_weeks, Mapping):
        values = [
            _float(duration_weeks.get(key), default=0.0)
            for key in ("max", "maximum", "upper", "to")
        ]
        selected = max(values, default=0.0)
        if selected > 0:
            return max(1, round(selected * 5))
    return max(DEFAULT_TOTAL_SPRINT_DAYS, feature_count * 2)


def _estimated_days_by_feature(
    required_features: list[Mapping[str, Any]],
    *,
    total_sprint_days: int,
) -> dict[str, int]:
    if not required_features:
        return {}
    base_days = max(1, total_sprint_days // max(1, len(required_features)))
    result: dict[str, int] = {}
    for index, feature in enumerate(required_features, start=1):
        feature_id = _feature_id(feature, index)
        priority = _feature_priority(feature, index)
        if priority == "P0":
            result[feature_id] = max(1, base_days)
        elif priority == "P1":
            result[feature_id] = max(1, base_days - 1)
        else:
            result[feature_id] = max(1, min(base_days, 2))
    return result


def _feature_dependencies(feature_id: str, feature_keys: list[str], index: int) -> list[str]:
    if index <= 1:
        return []
    lowered = feature_id.casefold()
    if any(marker in lowered for marker in ("integration", "dashboard", "analytics", "lms")):
        return feature_keys[: min(index - 1, 2)]
    return []


def _risk_notes(risks: Iterable[Mapping[str, Any]]) -> str:
    notes = []
    for risk in risks:
        text = str(risk.get("text") or risk.get("risk_key") or "").strip()
        reason = str(risk.get("reason") or "").strip()
        note = text if not reason else f"{text}: {reason}"
        if note:
            notes.append(note)
    return " | ".join(_unique_strings(notes)[:3])


def _constraint_texts(constraints: Iterable[Mapping[str, Any]]) -> list[str]:
    return _unique_strings(
        str(constraint.get("text") or constraint.get("constraint_key") or "").strip()
        for constraint in constraints
        if constraint.get("text") or constraint.get("constraint_key")
    )


def _risk_flags(risk_factors: Iterable[Mapping[str, Any]]) -> list[str]:
    return _unique_strings(
        str(risk.get("risk_key") or _slug(str(risk.get("text") or ""))).strip()
        for risk in risk_factors
        if risk.get("risk_key") or risk.get("text")
    )


def _roleplay_role_name(value: Any) -> str:
    role = str(value or "").strip()
    return ROLEPLAY_ROLE_ALIASES.get(role, role or DEFAULT_ASSIGNED_ROLE)


def _first_or_default(values: Iterable[str], default: str) -> str:
    for value in values:
        if value:
            return value
    return default


def _unique_strings(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = str(value or "").strip()
        if not item:
            continue
        marker = item.casefold()
        if marker in seen:
            continue
        seen.add(marker)
        result.append(item)
    return result


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").casefold()
    return slug


def _float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
