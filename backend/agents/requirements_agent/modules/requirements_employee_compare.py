"""Compare project requirements against preprocessed employee features."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

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

ROLE_SKILL_KEYWORDS = {
    "PM": {
        "product",
        "project",
        "roadmap",
        "stakeholder",
        "planning",
        "prioritization",
        "rollout",
        "metric",
        "analytics",
    },
    "Product Designer": {"design", "ux", "ui", "accessibility", "prototype", "figma"},
    "Backend Developer": {
        "api",
        "backend",
        "server",
        "database",
        "sql",
        "webhook",
        "auth",
        "integration",
        "event",
        "queue",
        "lms",
        "xapi",
    },
    "Frontend Developer": {
        "frontend",
        "web",
        "ui",
        "react",
        "typescript",
        "dashboard",
        "accessibility",
    },
    "Mobile Engineer": {
        "mobile",
        "android",
        "ios",
        "push",
        "permission",
        "notification",
        "app",
    },
    "DevOps Engineer": {
        "cloud",
        "gcp",
        "docker",
        "ci",
        "cd",
        "deployment",
        "monitoring",
        "observability",
        "infra",
    },
    "QA Engineer": {"qa", "test", "testing", "e2e", "regression", "validation", "quality"},
}

DEFAULT_COLUMN_WEIGHTS = {
    "employee.performance_score": 0.2,
    "employee.competency_score": 0.2,
    "jira_activity.sprint_completion_rate": 0.2,
    "jira_activity.ownership_score": 0.2,
    "calendar_activity.busy_minutes": 0.2,
}


def compare_requirements_to_employee_features(
    requirements_list: Mapping[str, Any],
    roleplay_requirements_input: Mapping[str, Any],
    employee_feature_matrix: Mapping[str, Any],
    *,
    max_team_size: int = 6,
) -> JsonObject:
    """Build a deterministic compare artifact before ranking.

    The compare artifact is intentionally not a ranking. It records how each
    employee feature profile aligns with every required role slot, including the
    score components and source feature references that ranking will consume.
    """

    role_slots = _role_slots(roleplay_requirements_input, max_team_size=max_team_size)
    required_skills = [str(skill) for skill in roleplay_requirements_input.get("required_skills", [])]
    project_risk_flags = [str(risk) for risk in roleplay_requirements_input.get("risk_flags", [])]
    profiles = list(employee_feature_matrix.get("feature_profiles", []))

    compare_results = [
        _compare_profile(
            profile,
            requirements_list=requirements_list,
            role_slots=role_slots,
            required_skills=required_skills,
            project_risk_flags=project_risk_flags,
        )
        for profile in profiles
    ]
    compare_results.sort(key=lambda item: (-item["best_role_score"], item["employee_id"]))

    return {
        "_meta": {
            "artifact_type": "requirements_employee_compare",
            "created_at": datetime.now(UTC).isoformat(),
            "source_requirements_list_id": requirements_list.get("_meta", {}).get(
                "requirements_list_id"
            ),
            "source_feature_matrix_id": employee_feature_matrix.get("_meta", {}).get(
                "matrix_id"
            ),
            "compare_result_count": len(compare_results),
            "role_slot_count": len(role_slots),
            "required_skill_count": len(required_skills),
            "risk_flag_count": len(project_risk_flags),
        },
        "compare_policy": {
            "purpose": "requirements_to_feature_alignment_before_ranking",
            "algorithm": "role_slot_multi_criteria_compare",
            "score_components": {
                "role_match": 0.28,
                "project_weighted_feature_score": 0.27,
                "role_profile": 0.18,
                "delivery": 0.12,
                "availability": 0.10,
                "communication": 0.05,
            },
            "guardrails": [
                "This compare step does not rank employees by itself.",
                "Scores are project-fit signals, not personal evaluation scores.",
                "Unknown or missing feature values use neutral score 0.5.",
                "Only preprocessed feature matrix values are used downstream.",
            ],
        },
        "role_slots": role_slots,
        "required_skills": required_skills,
        "project_risk_flags": project_risk_flags,
        "compare_results": compare_results,
    }


def _compare_profile(
    profile: Mapping[str, Any],
    *,
    requirements_list: Mapping[str, Any],
    role_slots: list[str],
    required_skills: list[str],
    project_risk_flags: list[str],
) -> JsonObject:
    role_comparisons = [
        _compare_profile_for_role(
            profile,
            role=role,
            requirements_list=requirements_list,
            required_skills=required_skills,
            project_risk_flags=project_risk_flags,
        )
        for role in role_slots
    ]
    role_comparisons.sort(key=lambda item: (-item["fit_score"], item["role"]))
    best = role_comparisons[0] if role_comparisons else _empty_role_comparison("PM")
    candidate_roles = [
        comparison["role"]
        for comparison in role_comparisons
        if comparison["score_breakdown"]["role_match"] >= 0.95
        or comparison["fit_score"] >= 70
    ]
    if not candidate_roles and best["role"]:
        candidate_roles = [best["role"]]

    return {
        "employee_id": str(profile.get("employee_id", "")),
        "employee_name": str(profile.get("employee_name", "")),
        "job_category_code": str(profile.get("job_category_code", "")),
        "candidate_roles": _unique_strings(candidate_roles),
        "best_role": best["role"],
        "best_role_score": best["fit_score"],
        "role_comparisons": role_comparisons,
        "signals": dict(profile.get("signals", {})),
        "feature_refs": _feature_refs_for_profile(profile),
    }


def _compare_profile_for_role(
    profile: Mapping[str, Any],
    *,
    role: str,
    requirements_list: Mapping[str, Any],
    required_skills: list[str],
    project_risk_flags: list[str],
) -> JsonObject:
    role_match = _role_match_score(profile, role)
    project_fit = _project_weighted_feature_score(profile, requirements_list, role)
    role_profile = _number(profile.get("role_profile_scores", {}).get(role), default=0.5)
    derived = profile.get("derived_features", {})
    delivery = _number(derived.get("delivery_score"), default=0.5)
    availability = _number(derived.get("availability_score"), default=0.5)
    communication = _number(derived.get("communication_score"), default=0.5)
    fit_score = round(
        100
        * (
            0.28 * role_match
            + 0.27 * project_fit
            + 0.18 * role_profile
            + 0.12 * delivery
            + 0.10 * availability
            + 0.05 * communication
        ),
        2,
    )
    matched_skills, missing_skills = _skill_match_lists(role, required_skills, fit_score)
    signals = dict(profile.get("signals", {}))
    risk_tags = _employee_risk_tags(
        role=role,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        signals=signals,
        project_risk_flags=project_risk_flags,
    )
    evidence_refs = _evidence_refs_for_role(role, risk_tags, requirements_list, profile)
    return {
        "role": role,
        "fit_score": fit_score,
        "fit_interpretation": _fit_interpretation(fit_score),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "score_breakdown": {
            "role_match": round(role_match, 4),
            "project_weighted_feature_score": round(project_fit, 4),
            "role_profile": round(role_profile, 4),
            "delivery": round(delivery, 4),
            "availability": round(availability, 4),
            "communication": round(communication, 4),
        },
        "signals": signals,
        "risk_tags": risk_tags,
        "evidence_refs": evidence_refs,
        "feature_values_used": _feature_values_used(requirements_list, profile, role),
        "feature_profile": _profile_for_ranking(profile, evidence_refs),
    }


def _role_slots(
    roleplay_requirements_input: Mapping[str, Any],
    *,
    max_team_size: int,
) -> list[str]:
    roles = [_roleplay_role(role) for role in roleplay_requirements_input.get("required_roles", [])]
    roles = _unique_strings(roles)
    if "PM" not in roles:
        roles.insert(0, "PM")
    priority = [
        "PM",
        "Backend Developer",
        "Frontend Developer",
        "Mobile Engineer",
        "QA Engineer",
        "DevOps Engineer",
        "Product Designer",
    ]
    ordered = [role for role in priority if role in roles]
    ordered.extend(role for role in roles if role not in ordered)
    if len(ordered) < 2:
        ordered.append("Backend Developer")
    return ordered[: max(2, max_team_size)]


def _role_match_score(profile: Mapping[str, Any], role: str) -> float:
    role = _roleplay_role(role)
    eligibility = profile.get("role_eligibility", {})
    if role in eligibility:
        return _number(eligibility.get(role), default=0.5)
    return 0.5


def _project_weighted_feature_score(
    profile: Mapping[str, Any],
    requirements_list: Mapping[str, Any],
    role: str,
) -> float:
    weights = dict(requirements_list.get("column_weights", {})) or DEFAULT_COLUMN_WEIGHTS
    score_sum = 0.0
    weight_sum = 0.0
    for column_key, weight in weights.items():
        column_weight = _number(weight, default=None)
        if column_weight is None:
            continue
        score_sum += column_weight * _feature_score(profile, str(column_key), role)
        weight_sum += column_weight
    return score_sum / weight_sum if weight_sum else 0.5


def _feature_score(profile: Mapping[str, Any], column_key: str, role: str) -> float:
    if column_key == "employee.job_category_code":
        return _role_match_score(profile, role)
    value = profile.get("feature_values", {}).get(column_key)
    if isinstance(value, Mapping):
        return _number(value.get("normalized_value"), default=0.5)
    return 0.5


def _skill_match_lists(
    role: str,
    required_skills: list[str],
    fit_score: float,
) -> tuple[list[str], list[str]]:
    keywords = ROLE_SKILL_KEYWORDS.get(_roleplay_role(role), set())
    matched = []
    missing = []
    for skill in required_skills:
        normalized = _normalize(skill)
        if any(keyword in normalized for keyword in keywords):
            matched.append(skill)
        else:
            missing.append(skill)
    if not matched and fit_score >= 70:
        matched = required_skills[: min(3, len(required_skills))]
        missing = [skill for skill in required_skills if skill not in matched]
    return matched[:8], missing[:8]


def _employee_risk_tags(
    *,
    role: str,
    matched_skills: list[str],
    missing_skills: list[str],
    signals: Mapping[str, str],
    project_risk_flags: list[str],
) -> list[str]:
    tags = []
    if signals.get("capacity_signal") == "high_risk":
        tags.append("workload_concentration")
    if signals.get("communication_signal") == "high_delay":
        tags.append("communication_delay")
    if signals.get("delivery_signal") == "unstable":
        tags.append("delivery_risk")
    if missing_skills and len(missing_skills) > len(matched_skills):
        tags.append("missing_skill")
    role = _roleplay_role(role)
    for risk in project_risk_flags:
        lowered = risk.casefold()
        integration_role = "integration" in lowered and role in {
            "Backend Developer",
            "Frontend Developer",
            "Mobile Engineer",
            "DevOps Engineer",
        }
        qa_role = "qa" in lowered and role == "QA Engineer"
        schedule_role = "schedule" in lowered and signals.get("capacity_signal") != "low_risk"
        security_role = "security" in lowered and role in {
            "Backend Developer",
            "DevOps Engineer",
            "QA Engineer",
        }
        if integration_role or qa_role or schedule_role or security_role:
            tags.append(risk)
    return _unique_strings(tags)[:8]


def _evidence_refs_for_role(
    role: str,
    risk_tags: list[str],
    requirements_list: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> list[str]:
    refs = []
    for column in requirements_list.get("column_priority_order", [])[:8]:
        if isinstance(column, str):
            refs.append(column)
    refs.extend(str(item) for item in profile.get("evidence_refs", [])[:4])
    if any("communication" in tag for tag in risk_tags):
        refs.append("slack_activity.avg_response_time")
    if any("workload" in tag or "schedule" in tag for tag in risk_tags):
        refs.extend(["calendar_activity.busy_minutes", "employee.overtime_hours_12m"])
    return _unique_strings(refs)[:10]


def _feature_values_used(
    requirements_list: Mapping[str, Any],
    profile: Mapping[str, Any],
    role: str,
) -> list[JsonObject]:
    used = []
    for column_key, weight in (dict(requirements_list.get("column_weights", {})) or DEFAULT_COLUMN_WEIGHTS).items():
        column = str(column_key)
        if column == "employee.job_category_code":
            used.append(
                {
                    "feature_key": column,
                    "normalized_value": _role_match_score(profile, role),
                    "weight": _number(weight, default=0.0),
                    "source_column": column,
                    "missing": False,
                }
            )
            continue
        feature_value = profile.get("feature_values", {}).get(column)
        if isinstance(feature_value, Mapping):
            used.append(
                {
                    "feature_key": column,
                    "normalized_value": _number(feature_value.get("normalized_value"), default=0.5),
                    "weight": _number(weight, default=0.0),
                    "source_column": feature_value.get("source_column", column),
                    "missing": bool(feature_value.get("missing")),
                }
            )
        else:
            used.append(
                {
                    "feature_key": column,
                    "normalized_value": 0.5,
                    "weight": _number(weight, default=0.0),
                    "source_column": column,
                    "missing": True,
                }
            )
    return used


def _profile_for_ranking(profile: Mapping[str, Any], evidence_refs: list[str]) -> JsonObject:
    raw_profile = {
        "employee": {
            "employee_id": profile.get("employee_id", ""),
            "employee_name": profile.get("employee_name", ""),
            "job_category_code": profile.get("job_category_code", ""),
        }
    }
    for column_key in _unique_strings(list(profile.get("feature_values", {})) + evidence_refs):
        if "." not in column_key:
            continue
        source, column = column_key.split(".", 1)
        feature_value = profile.get("feature_values", {}).get(column_key, {})
        raw = feature_value.get("raw_value") if isinstance(feature_value, Mapping) else None
        raw_profile.setdefault(source, {})[column] = raw if raw is not None else "n/a"
    return raw_profile


def _feature_refs_for_profile(profile: Mapping[str, Any]) -> list[str]:
    refs = list(profile.get("feature_values", {}))[:12]
    refs.extend(str(item) for item in profile.get("evidence_refs", []))
    return _unique_strings(refs)[:16]


def _fit_interpretation(score: float) -> str:
    if score >= 75:
        return "strong_project_fit_signal"
    if score >= 60:
        return "usable_project_fit_signal"
    if score >= 45:
        return "partial_project_fit_signal"
    return "weak_project_fit_signal"


def _roleplay_role(role: Any) -> str:
    value = str(role or "").strip()
    return ROLEPLAY_ROLE_ALIASES.get(value, value or "PM")


def _number(value: Any, *, default: float | None = 0.0) -> float | None:
    if value is None:
        return default
    if isinstance(value, int | float):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", " ", str(value).casefold()).strip()


def _unique_strings(values: Iterable[Any]) -> list[str]:
    result = []
    seen = set()
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


def _empty_role_comparison(role: str) -> JsonObject:
    return {
        "role": role,
        "fit_score": 0.0,
        "matched_skills": [],
        "missing_skills": [],
        "score_breakdown": {
            "role_match": 0.0,
            "project_weighted_feature_score": 0.0,
            "role_profile": 0.0,
            "delivery": 0.0,
            "availability": 0.0,
            "communication": 0.0,
        },
        "signals": {},
        "risk_tags": [],
        "evidence_refs": [],
        "feature_values_used": [],
        "feature_profile": {},
    }
