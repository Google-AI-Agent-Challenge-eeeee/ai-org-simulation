"""Employee and team ranking bridge for Requirements Agent outputs."""

from __future__ import annotations

import csv
import itertools
import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.agents.requirements_agent.modules.employee_feature_preprocessing import (
    build_employee_feature_preprocessing_outputs,
)
from backend.agents.requirements_agent.modules.requirements_employee_compare import (
    compare_requirements_to_employee_features,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.risk_taxonomy_bridge import (
    canonical_issue_category,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    EmployeeFitProfileSnapshot,
    EvidenceMetadata,
    SelectedTeamRecord,
    SimulationInputPacket,
    TeamRiskSummary,
)

JsonObject = dict[str, Any]

SOURCE_FILES = {
    "employee": Path("hr") / "employee_dummy_100.csv",
    "github_activity": Path("github") / "github_activity_dummy_100.csv",
    "slack_activity": Path("slack") / "slack_activity_dummy_100.csv",
    "jira_activity": Path("jira") / "jira_activity_dummy_100.csv",
    "calendar_activity": Path("calendar") / "google_calendar_activity_dummy_100.csv",
}

ROLE_CODE_MAP = {
    "PM": [],
    "Product Manager": [],
    "Product Lead": [],
    "Product Designer": ["DS"],
    "Backend Developer": ["BE"],
    "Backend Engineer": ["BE"],
    "Backend Lead": ["BE"],
    "Frontend Developer": ["WEB"],
    "Web Frontend Engineer": ["WEB"],
    "Frontend Lead": ["WEB"],
    "Mobile Engineer": ["Mobile", "Android", "iOS"],
    "Mobile Lead": ["Mobile", "Android", "iOS"],
    "DevOps Engineer": ["Infra"],
    "Infrastructure Engineer": ["Infra"],
    "IT Administrator": ["Infra"],
    "QA Engineer": ["QA"],
    "Data Engineer": ["BE"],
    "Engineering Lead": ["BE", "WEB", "Mobile", "Android", "iOS", "Infra"],
}

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

POSITIVE_COLUMNS = {
    "employee.tenure_years",
    "employee.performance_score",
    "employee.kpi_score",
    "employee.competency_score",
    "employee.peer_review_score",
    "employee.manager_review_score",
    "employee.engagement_score",
    "employee.training_hours_12m",
    "employee.certifications_count",
    "github_activity.commit_count_3m",
    "github_activity.pr_count_3m",
    "github_activity.merged_pr_count_3m",
    "github_activity.repository_contribution_count",
    "slack_activity.message_count",
    "slack_activity.thread_replies",
    "slack_activity.collaboration_frequency",
    "slack_activity.leadership_score",
    "slack_activity.autonomy_score",
    "jira_activity.completed_issue_count",
    "jira_activity.estimation_accuracy",
    "jira_activity.comment_count",
    "jira_activity.collaboration_touchpoints",
    "jira_activity.status_transition_count",
    "jira_activity.task_breakdown_count",
    "jira_activity.sprint_completion_rate",
    "jira_activity.autonomy_score",
    "jira_activity.ownership_score",
    "calendar_activity.focus_time_count",
    "calendar_activity.focus_time_minutes",
    "calendar_activity.no_meeting_block_count",
    "calendar_activity.organizer_event_count",
    "calendar_activity.organizer_ratio",
}

NEGATIVE_COLUMNS = {
    "employee.absence_days_12m",
    "employee.overtime_hours_12m",
    "employee.disciplinary_actions_12m",
    "employee.turnover_risk_score",
    "github_activity.closed_unmerged_pr_count_3m",
    "slack_activity.avg_response_time",
    "slack_activity.night_activity_ratio",
    "slack_activity.multitasking_score",
    "slack_activity.dependency_score",
    "slack_activity.bottleneck_risk",
    "slack_activity.burnout_risk",
    "slack_activity.decision_latency",
    "jira_activity.avg_cycle_time",
    "jira_activity.overdue_issue_count",
    "jira_activity.avg_comment_response_time",
    "jira_activity.avg_time_in_status",
    "jira_activity.reopened_issue_count",
    "jira_activity.scope_change_count",
    "jira_activity.context_switching_score",
    "jira_activity.bottleneck_risk",
    "calendar_activity.total_meeting_minutes",
    "calendar_activity.early_late_meeting_ratio",
    "calendar_activity.weekend_meeting_ratio",
    "calendar_activity.fragmented_calendar_score",
    "calendar_activity.large_meeting_ratio",
    "calendar_activity.external_meeting_ratio",
    "calendar_activity.no_response_ratio",
    "calendar_activity.busy_minutes",
    "calendar_activity.event_update_count",
}

DEFAULT_EMPLOYEE_DATA_DIR = Path("datasets/raw")
DEFAULT_TOP_CANDIDATES_PER_ROLE = 5
DEFAULT_MAX_TEAM_SIZE = 6
DEFAULT_MAX_RANKED_TEAMS = 20
DEFAULT_PROXY_ROLE_CANDIDATE_LIMIT = 12


def build_employee_team_rankings(
    requirements_list: Mapping[str, Any],
    roleplay_requirements_input: Mapping[str, Any],
    *,
    employee_data_dir: str | Path = DEFAULT_EMPLOYEE_DATA_DIR,
    employee_feature_matrix: Mapping[str, Any] | None = None,
    employee_feature_metadata: Mapping[str, Any] | None = None,
    requirements_employee_compare: Mapping[str, Any] | None = None,
    max_team_size: int = DEFAULT_MAX_TEAM_SIZE,
    top_candidates_per_role: int = DEFAULT_TOP_CANDIDATES_PER_ROLE,
    max_ranked_teams: int = DEFAULT_MAX_RANKED_TEAMS,
    simulation_id: str | None = None,
) -> JsonObject:
    """Rank employees and teams, then build Shadow RolePlay-ready inputs.

    The scoring strategy is deterministic and evidence-backed:
    - Requirements Agent ``column_weights`` define project-specific comparison criteria.
    - Numeric CSV values are normalized against the current dataset distribution.
    - Team score combines employee fit, role coverage, skill coverage, availability,
      and risk concentration instead of averaging personal scores only.
    """

    if employee_feature_matrix is None or employee_feature_metadata is None:
        feature_outputs = build_employee_feature_preprocessing_outputs(employee_data_dir)
        employee_feature_matrix = feature_outputs["employee_feature_matrix"]
        employee_feature_metadata = feature_outputs["employee_feature_metadata"]

    role_slots = _role_slots(roleplay_requirements_input, max_team_size=max_team_size)
    required_skills = list(roleplay_requirements_input.get("required_skills", []))
    project_risk_flags = list(roleplay_requirements_input.get("risk_flags", []))
    if requirements_employee_compare is None:
        requirements_employee_compare = compare_requirements_to_employee_features(
            requirements_list,
            roleplay_requirements_input,
            employee_feature_matrix,
            max_team_size=max_team_size,
        )

    all_ranked_employees = _rank_employees_from_compare(requirements_employee_compare)
    candidate_pool_by_role = _candidate_pool_by_role(
        all_ranked_employees,
        role_slots=role_slots,
        proxy_role_candidate_limit=max(
            DEFAULT_PROXY_ROLE_CANDIDATE_LIMIT,
            top_candidates_per_role * 3,
        ),
    )
    ranked_employees = _rank_project_candidates(
        all_ranked_employees,
        role_slots=role_slots,
        candidate_pool_by_role=candidate_pool_by_role,
    )
    teams = _rank_teams(
        ranked_employees,
        role_slots=role_slots,
        required_skills=required_skills,
        project_risk_flags=project_risk_flags,
        max_ranked_teams=max_ranked_teams,
        top_candidates_per_role=top_candidates_per_role,
    )
    selected_team = teams[0] if teams else _fallback_team(ranked_employees, role_slots)
    selected_team_record = _selected_team_record(selected_team)
    snapshots = _snapshots_for_team(selected_team)
    team_risk_summary = _team_risk_summary(selected_team, roleplay_requirements_input)
    evidence_metadata = _evidence_metadata_for_team(
        selected_team,
        team_risk_summary=team_risk_summary,
        roleplay_requirements_input=roleplay_requirements_input,
    )

    SelectedTeamRecord.model_validate(selected_team_record)
    snapshot_models = [EmployeeFitProfileSnapshot.model_validate(snapshot) for snapshot in snapshots]
    risk_model = TeamRiskSummary.model_validate(team_risk_summary)
    evidence_models = [EvidenceMetadata.model_validate(item) for item in evidence_metadata]
    packet = SimulationInputPacket(
        simulation_id=simulation_id or f"sim_{selected_team_record['team_id']}",
        project_context=roleplay_requirements_input,
        selected_team=selected_team_record,
        member_snapshots=snapshot_models,
        team_risk_summary=risk_model,
        evidence_metadata=evidence_models,
    )

    return {
        "employee_feature_matrix": dict(employee_feature_matrix),
        "employee_feature_metadata": dict(employee_feature_metadata),
        "requirements_employee_compare": dict(requirements_employee_compare),
        "employee_fit_ranking": _employee_fit_ranking_payload(
            ranked_employees,
            role_slots=role_slots,
            requirements_list=requirements_list,
            candidate_pool_by_role=candidate_pool_by_role,
            source_employee_count=len(all_ranked_employees),
        ),
        "team_composition_candidates": _team_candidates_payload(
            teams,
            role_slots=role_slots,
            required_skills=required_skills,
        ),
        "team_composition_ranking": _team_ranking_payload(
            teams,
            role_slots=role_slots,
            required_skills=required_skills,
            roleplay_requirements_input=roleplay_requirements_input,
        ),
        "roleplay_selected_team_record": selected_team_record,
        "roleplay_employee_fit_profile_snapshots": snapshots,
        "roleplay_team_risk_summary": team_risk_summary,
        "roleplay_evidence_metadata": evidence_metadata,
        "roleplay_simulation_input_packet": packet.model_dump(mode="json"),
        "roleplay_handoff_manifest": _completed_handoff_manifest(
            requirements_list,
            roleplay_requirements_input,
            selected_team_record,
            ranked_employee_count=len(ranked_employees),
            ranked_team_count=len(teams),
        ),
    }


def _rank_employees_from_compare(requirements_employee_compare: Mapping[str, Any]) -> list[JsonObject]:
    rankings = []
    for item in requirements_employee_compare.get("compare_results", []):
        role_scores = [
            _role_score_from_compare(comparison)
            for comparison in item.get("role_comparisons", [])
            if isinstance(comparison, Mapping)
        ]
        role_scores.sort(key=lambda score: (-score["fit_score"], score["role"]))
        best = role_scores[0] if role_scores else _empty_role_score("PM")
        rankings.append(
            {
                "employee_id": str(item.get("employee_id", "")),
                "employee_name": str(item.get("employee_name", "")),
                "job_category_code": str(item.get("job_category_code", "")),
                "best_role": best["role"],
                "best_role_score": best["fit_score"],
                "role_scores": role_scores,
                "signals": best["signals"],
                "risk_tags": best["risk_tags"],
                "evidence_refs": best["evidence_refs"],
            }
        )
    rankings.sort(key=lambda item: (-item["best_role_score"], item["employee_id"]))
    for index, item in enumerate(rankings, start=1):
        item["rank"] = index
    return rankings


def _role_score_from_compare(comparison: Mapping[str, Any]) -> JsonObject:
    breakdown = dict(comparison.get("score_breakdown", {}))
    if "availability" not in breakdown:
        breakdown["availability"] = 0.5
    if "project_weighted_fit" not in breakdown:
        breakdown["project_weighted_fit"] = breakdown.get(
            "project_weighted_feature_score",
            0.5,
        )
    return {
        "role": _roleplay_role(comparison.get("role", "PM")),
        "fit_score": float(comparison.get("fit_score", 0.0)),
        "matched_skills": list(comparison.get("matched_skills", [])),
        "missing_skills": list(comparison.get("missing_skills", [])),
        "score_breakdown": breakdown,
        "signals": dict(comparison.get("signals", {})),
        "risk_tags": list(comparison.get("risk_tags", [])),
        "evidence_refs": list(comparison.get("evidence_refs", [])),
        "_profile": dict(comparison.get("feature_profile", {})),
    }


def load_employee_dataset(employee_data_dir: str | Path = DEFAULT_EMPLOYEE_DATA_DIR) -> JsonObject:
    """Load local CSV datasets needed for fit and team ranking."""

    root = Path(employee_data_dir)
    if not root.exists():
        raise FileNotFoundError(f"Employee data directory does not exist: {root}")
    result: JsonObject = {}
    for source, relative_path in SOURCE_FILES.items():
        path = root / relative_path
        if not path.exists():
            raise FileNotFoundError(f"Missing employee ranking CSV source: {path}")
        with path.open(newline="", encoding="utf-8-sig") as f:
            result[source] = list(csv.DictReader(f))
    return result


def _joined_employee_profiles(dataset: Mapping[str, list[JsonObject]]) -> list[JsonObject]:
    github_by_id = {
        row.get("github_id"): row for row in dataset.get("github_activity", []) if row.get("github_id")
    }
    slack_by_id = {
        row.get("slack_user_id"): row
        for row in dataset.get("slack_activity", [])
        if row.get("slack_user_id")
    }
    jira_by_id = {
        row.get("jira_account_id"): row
        for row in dataset.get("jira_activity", [])
        if row.get("jira_account_id")
    }
    calendar_by_email = {
        row.get("google_email"): row
        for row in dataset.get("calendar_activity", [])
        if row.get("google_email")
    }

    profiles = []
    for employee in dataset.get("employee", []):
        profiles.append(
            {
                "employee": employee,
                "github_activity": github_by_id.get(employee.get("github_id"), {}),
                "slack_activity": slack_by_id.get(employee.get("slack_user_id"), {}),
                "jira_activity": jira_by_id.get(employee.get("jira_account_id"), {}),
                "calendar_activity": calendar_by_email.get(employee.get("google_email"), {}),
            }
        )
    return profiles


def _rank_employees(
    profiles: list[JsonObject],
    *,
    requirements_list: Mapping[str, Any],
    role_slots: list[str],
    required_skills: list[str],
    project_risk_flags: list[str],
    stats: Mapping[str, tuple[float, float]],
) -> list[JsonObject]:
    rankings = []
    for profile in profiles:
        role_scores = [
            _score_employee_for_role(
                profile,
                role=role,
                requirements_list=requirements_list,
                required_skills=required_skills,
                project_risk_flags=project_risk_flags,
                stats=stats,
            )
            for role in role_slots
        ]
        role_scores.sort(key=lambda item: (-item["fit_score"], item["role"]))
        best = role_scores[0] if role_scores else _empty_role_score("PM")
        rankings.append(
            {
                "employee_id": _value(profile, "employee.employee_id"),
                "employee_name": _value(profile, "employee.employee_name"),
                "job_category_code": _value(profile, "employee.job_category_code"),
                "best_role": best["role"],
                "best_role_score": best["fit_score"],
                "role_scores": role_scores,
                "signals": best["signals"],
                "risk_tags": best["risk_tags"],
                "evidence_refs": best["evidence_refs"],
            }
        )
    rankings.sort(key=lambda item: (-item["best_role_score"], item["employee_id"]))
    for index, item in enumerate(rankings, start=1):
        item["rank"] = index
    return rankings


def _candidate_pool_by_role(
    ranked_employees: list[JsonObject],
    *,
    role_slots: list[str],
    proxy_role_candidate_limit: int,
) -> dict[str, list[JsonObject]]:
    pools = {}
    for role in role_slots:
        exact_candidates = [
            employee
            for employee in ranked_employees
            if _is_exact_role_candidate(employee, role)
        ]
        source = exact_candidates or ranked_employees
        limit = len(source) if exact_candidates else proxy_role_candidate_limit
        pools[role] = _sort_employees_for_role(source, role)[:limit]
    return pools


def _rank_project_candidates(
    ranked_employees: list[JsonObject],
    *,
    role_slots: list[str],
    candidate_pool_by_role: Mapping[str, list[JsonObject]],
) -> list[JsonObject]:
    roles_by_employee: dict[str, list[str]] = {}
    for role in role_slots:
        for employee in candidate_pool_by_role.get(role, []):
            roles_by_employee.setdefault(employee["employee_id"], []).append(role)

    candidates = []
    for employee in ranked_employees:
        candidate_roles = [
            role for role in role_slots if role in roles_by_employee.get(employee["employee_id"], [])
        ]
        if not candidate_roles:
            continue
        role_scores = [
            score for score in employee["role_scores"] if score["role"] in candidate_roles
        ]
        role_scores.sort(key=lambda item: (-item["fit_score"], item["role"]))
        best = role_scores[0] if role_scores else _empty_role_score(candidate_roles[0])
        candidates.append(
            {
                **employee,
                "candidate_roles": candidate_roles,
                "best_role": best["role"],
                "best_role_score": best["fit_score"],
                "role_scores": role_scores,
                "signals": best["signals"],
                "risk_tags": best["risk_tags"],
                "evidence_refs": best["evidence_refs"],
            }
        )

    candidates.sort(key=lambda item: (-item["best_role_score"], item["employee_id"]))
    for index, item in enumerate(candidates, start=1):
        item["rank"] = index
    return candidates


def _score_employee_for_role(
    profile: Mapping[str, Mapping[str, Any]],
    *,
    role: str,
    requirements_list: Mapping[str, Any],
    required_skills: list[str],
    project_risk_flags: list[str],
    stats: Mapping[str, tuple[float, float]],
) -> JsonObject:
    role_match = _role_match_score(profile, role)
    project_fit = _project_weighted_score(profile, requirements_list, stats, role)
    delivery = _delivery_score(profile, stats)
    availability = _availability_score(profile, stats)
    communication = _communication_score(profile, stats)
    role_profile = _role_profile_score(profile, role, stats)

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
    signals = {
        "capacity_signal": _capacity_signal(profile, stats),
        "communication_signal": _communication_signal(profile, stats),
        "delivery_signal": _delivery_signal(profile, stats),
        "collaboration_signal": _collaboration_signal(profile),
    }
    risk_tags = _employee_risk_tags(
        role=role,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        signals=signals,
        project_risk_flags=project_risk_flags,
    )
    evidence_refs = _evidence_refs_for_role(role, risk_tags, requirements_list)
    return {
        "role": role,
        "fit_score": fit_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "score_breakdown": {
            "role_match": round(role_match, 4),
            "project_weighted_fit": round(project_fit, 4),
            "role_profile": round(role_profile, 4),
            "delivery": round(delivery, 4),
            "availability": round(availability, 4),
            "communication": round(communication, 4),
        },
        "signals": signals,
        "risk_tags": risk_tags,
        "evidence_refs": evidence_refs,
        "_profile": profile,
    }


def _rank_teams(
    ranked_employees: list[JsonObject],
    *,
    role_slots: list[str],
    required_skills: list[str],
    project_risk_flags: list[str],
    max_ranked_teams: int,
    top_candidates_per_role: int,
) -> list[JsonObject]:
    candidates_by_role = {
        role: _top_role_candidates(ranked_employees, role, top_candidates_per_role)
        for role in role_slots
    }
    combinations = itertools.product(*(candidates_by_role[role] for role in role_slots))
    teams: list[JsonObject] = []
    seen_team_keys: set[tuple[str, ...]] = set()
    for combination in combinations:
        if not _unique_employees(combination):
            continue
        team_key = tuple(sorted(member["employee_id"] for member in combination))
        if team_key in seen_team_keys:
            continue
        seen_team_keys.add(team_key)
        teams.append(
            _score_team(
                list(combination),
                required_skills=required_skills,
                project_risk_flags=project_risk_flags,
                role_slots=role_slots,
            )
        )
    teams.sort(key=lambda item: (-item["team_fit_score"], item["team_id"]))
    for index, team in enumerate(teams[:max_ranked_teams], start=1):
        team["team_rank"] = index
        team["team_id"] = f"team_{index:03d}"
    return teams[:max_ranked_teams]


def _score_team(
    members: list[JsonObject],
    *,
    required_skills: list[str],
    project_risk_flags: list[str],
    role_slots: list[str],
) -> JsonObject:
    role_coverage = len({member["assigned_role"] for member in members}) / max(len(role_slots), 1)
    matched_skill_set = {
        skill for member in members for skill in member["matched_skills"] if skill in required_skills
    }
    skill_coverage = len(matched_skill_set) / max(len(set(required_skills)), 1)
    availability = _average(member["availability_score"] for member in members)
    avg_fit = _average(member["fit_score"] for member in members) / 100
    diversity = len({member["job_category_code"] for member in members}) / max(len(members), 1)
    risk_count = sum(len(member["risk_tags"]) for member in members)
    risk_penalty = min(0.18, risk_count * 0.018)
    project_risk_bonus = 0.03 if project_risk_flags and matched_skill_set else 0.0
    team_score = round(
        100
        * max(
            0.0,
            min(
                1.0,
                0.34 * avg_fit
                + 0.22 * role_coverage
                + 0.18 * skill_coverage
                + 0.16 * availability
                + 0.07 * diversity
                + project_risk_bonus
                - risk_penalty,
            ),
        ),
        2,
    )
    return {
        "team_id": "team_pending_rank",
        "team_rank": 0,
        "team_fit_score": team_score,
        "members": members,
        "role_coverage_score": round(role_coverage, 4),
        "skill_coverage_score": round(skill_coverage, 4),
        "availability_score": round(availability, 4),
        "team_risk_flags": _unique_strings(
            [tag for member in members for tag in member["risk_tags"]] + project_risk_flags
        )[:12],
        "role_slot_coverage": {
            "role_slots": list(role_slots),
            "assigned_roles": _unique_strings(member["assigned_role"] for member in members),
            "uncovered_role_slots": [
                role
                for role in role_slots
                if role not in {member["assigned_role"] for member in members}
            ],
        },
        "bottleneck_members": [
            member["employee_name"]
            for member in members
            if member["signals"]["capacity_signal"] == "high_risk"
            or "workload_concentration" in member["risk_tags"]
        ],
        "critical_dependencies": _critical_dependencies(members),
        "score_breakdown": {
            "avg_employee_fit": round(avg_fit, 4),
            "role_coverage": round(role_coverage, 4),
            "skill_coverage": round(skill_coverage, 4),
            "availability": round(availability, 4),
            "job_category_diversity": round(diversity, 4),
            "risk_penalty": round(risk_penalty, 4),
        },
    }


def _employee_fit_ranking_payload(
    ranked_employees: list[JsonObject],
    *,
    role_slots: list[str],
    requirements_list: Mapping[str, Any],
    candidate_pool_by_role: Mapping[str, list[JsonObject]],
    source_employee_count: int,
) -> JsonObject:
    sanitized = []
    for employee in ranked_employees:
        role_scores = [
            _sanitize_role_score(score)
            for score in employee["role_scores"]
            if score["role"] in role_slots
        ]
        sanitized.append(
            {
                "rank": employee["rank"],
                "employee_id": employee["employee_id"],
                "employee_name": employee["employee_name"],
                "job_category_code": employee["job_category_code"],
                "candidate_roles": list(employee.get("candidate_roles", [])),
                "best_role": employee["best_role"],
                "best_role_score": employee["best_role_score"],
                "role_scores": role_scores,
                "signals": employee["signals"],
                "risk_tags": employee["risk_tags"],
                "evidence_refs": employee["evidence_refs"],
            }
        )
    return {
        "_meta": {
            "ranking_type": "employee_fit_ranking",
            "created_at": datetime.now(UTC).isoformat(),
            "source_requirements_list_id": requirements_list.get("_meta", {}).get(
                "requirements_list_id"
            ),
            "scoring_version": "0.1.0",
            "candidate_scope": "project_required_role_candidates_only",
            "source_employee_count": source_employee_count,
            "candidate_employee_count": len(sanitized),
            "excluded_employee_count": max(0, source_employee_count - len(sanitized)),
            "role_candidate_counts": {
                role: len(candidate_pool_by_role.get(role, []))
                for role in role_slots
            },
        },
        "scoring_policy": {
            "algorithm": "weighted_multi_criteria_scoring",
            "inputs": [
                "requirements_list.column_weights",
                "Employee_Feature_Matrix.json",
                "Requirements_Employee_Compare.json",
                "required_roles",
                "required_skills",
                "risk_factors",
            ],
            "score_components": {
                "role_match": 0.28,
                "project_weighted_fit": 0.27,
                "role_profile": 0.18,
                "delivery": 0.12,
                "availability": 0.10,
                "communication": 0.05,
            },
            "guardrails": [
                "Employees outside PRD-required role candidate pools are excluded.",
                "Excluded sensitive personal columns are not used.",
                "Scores are project-fit estimates, not personal performance judgments.",
                "Missing skill_stack columns are treated as proxy signals, not direct skill proof.",
            ],
            "used_employee_columns": _used_employee_column_keys(requirements_list, role_slots),
        },
        "role_slots": role_slots,
        "employee_rankings": sanitized,
        "shortlisted_candidates_by_role": {
            role: [
                {
                    "employee_id": candidate["employee_id"],
                    "employee_name": candidate["employee_name"],
                    "job_category_code": candidate["job_category_code"],
                    "candidate_pool_reason": _candidate_pool_reason(candidate, role),
                    "fit_score": candidate["fit_score"],
                    "matched_skills": candidate["matched_skills"],
                    "missing_skills": candidate["missing_skills"],
                    "risk_tags": candidate["risk_tags"],
                    "evidence_refs": candidate["evidence_refs"],
                }
                for candidate in _top_role_candidates(ranked_employees, role, 5)
            ]
            for role in role_slots
        },
        "ranking_by_role": {
            role: [
                {
                    "employee_id": candidate["employee_id"],
                    "employee_name": candidate["employee_name"],
                    "job_category_code": candidate["job_category_code"],
                    "candidate_pool_reason": _candidate_pool_reason(candidate, role),
                    "fit_score": candidate["fit_score"],
                    "matched_skills": candidate["matched_skills"],
                    "missing_skills": candidate["missing_skills"],
                }
                for candidate in _top_role_candidates(ranked_employees, role, 10)
            ]
            for role in role_slots
        },
    }


def _team_ranking_payload(
    teams: list[JsonObject],
    *,
    role_slots: list[str],
    required_skills: list[str],
    roleplay_requirements_input: Mapping[str, Any],
) -> JsonObject:
    required_roles = _required_role_set(roleplay_requirements_input)
    return {
        "_meta": {
            "ranking_type": "team_composition_ranking",
            "created_at": datetime.now(UTC).isoformat(),
            "scoring_version": "0.1.0",
        },
        "scoring_policy": {
            "algorithm": "role-constrained_cartesian_search_with_multi_criteria_team_score",
            "candidate_pool_constraint": (
                "Teams are generated only from employee candidates already admitted to "
                "PRD-required role pools."
            ),
            "team_score_components": {
                "avg_employee_fit": 0.34,
                "role_coverage": 0.22,
                "skill_coverage": 0.18,
                "availability": 0.16,
                "job_category_diversity": 0.07,
                "project_risk_alignment_bonus": 0.03,
                "risk_penalty_cap": 0.18,
            },
        },
        "role_slots": role_slots,
        "required_roles": required_roles,
        "required_skills": required_skills,
        "role_coverage_policy": {
            "team_generation_scope": "ranked_candidates_for_required_role_slots",
            "uncovered_required_roles_are_kept_as_handoff_risk": True,
        },
        "team_rankings": [_sanitize_team(team) for team in teams],
    }


def _team_candidates_payload(
    teams: list[JsonObject],
    *,
    role_slots: list[str],
    required_skills: list[str],
) -> JsonObject:
    return {
        "_meta": {
            "artifact_type": "team_composition_candidates",
            "created_at": datetime.now(UTC).isoformat(),
            "candidate_count": len(teams),
            "source": "compare_based_employee_fit_ranking",
        },
        "generation_policy": {
            "role_slots": role_slots,
            "required_skills": required_skills,
            "candidate_constraint": (
                "Only candidates admitted through project-required role pools are used."
            ),
            "duplicate_employee_policy": "one employee can appear at most once per team",
        },
        "team_candidates": [_sanitize_team(team) for team in teams],
    }


def _selected_team_record(team: Mapping[str, Any]) -> JsonObject:
    return {
        "team_id": team["team_id"],
        "team_rank": int(team["team_rank"]),
        "team_fit_score": float(team["team_fit_score"]),
        "members": [
            {
                "employee_id": member["employee_id"],
                "employee_name": member["employee_name"],
                "assigned_role": member["assigned_role"],
            }
            for member in team["members"]
        ],
        "role_coverage_score": float(team["role_coverage_score"]),
        "skill_coverage_score": float(team["skill_coverage_score"]),
        "availability_score": float(team["availability_score"]),
        "team_risk_flags": list(team["team_risk_flags"]),
    }


def _snapshots_for_team(team: Mapping[str, Any]) -> list[JsonObject]:
    snapshots = []
    for member in team["members"]:
        snapshots.append(
            {
                "employee_id": member["employee_id"],
                "employee_name": member["employee_name"],
                "assigned_role": member["assigned_role"],
                "matched_skills": list(member["matched_skills"]),
                "missing_skills": list(member["missing_skills"]),
                "capacity_signal": member["signals"]["capacity_signal"],
                "communication_signal": member["signals"]["communication_signal"],
                "delivery_signal": member["signals"]["delivery_signal"],
                "collaboration_signal": member["signals"]["collaboration_signal"],
                "risk_tags": list(member["risk_tags"]),
                "evidence_refs": list(member["evidence_refs"]),
            }
        )
    return snapshots


def _team_risk_summary(
    team: Mapping[str, Any],
    roleplay_requirements_input: Mapping[str, Any],
) -> JsonObject:
    raw_risk_tags = _unique_strings(list(team["team_risk_flags"]))
    canonical_tags = [canonical_issue_category(tag) for tag in raw_risk_tags]
    role_gap = _role_coverage_gap(roleplay_requirements_input, team)
    gap_risk_tags = ["unclear_ownership"] if role_gap["uncovered_required_roles"] else []
    risk_tags = _unique_strings(raw_risk_tags + canonical_tags + gap_risk_tags)
    risk_prior_scores = {}
    for tag in risk_tags:
        matching_raw_scores = [
            _risk_prior_score(raw_tag, team)
            for raw_tag in raw_risk_tags
            if canonical_issue_category(raw_tag) == tag
        ]
        risk_prior_scores[tag] = max([_risk_prior_score(tag, team), *matching_raw_scores])
    if role_gap["uncovered_required_roles"]:
        risk_prior_scores["unclear_ownership"] = max(
            risk_prior_scores.get("unclear_ownership", 0.0),
            0.62,
        )
    return {
        "team_id": team["team_id"],
        "risk_tags": risk_tags,
        "risk_prior_scores": risk_prior_scores,
        "bottleneck_members": list(team["bottleneck_members"]),
        "critical_dependencies": _unique_strings(
            list(team["critical_dependencies"])
            + _feature_dependency_descriptions(roleplay_requirements_input)
            + [
                f"Uncovered required role: {role}"
                for role in role_gap["uncovered_required_roles"]
            ]
        )[:12],
    }


def _evidence_metadata_for_team(
    team: Mapping[str, Any],
    *,
    team_risk_summary: Mapping[str, Any],
    roleplay_requirements_input: Mapping[str, Any],
) -> list[JsonObject]:
    evidence = []
    counter = 1
    for member in team["members"]:
        profile = member["_profile"]
        for risk_tag in member["risk_tags"][:4]:
            refs = member["evidence_refs"] or _default_evidence_refs_for_risk(risk_tag)
            for source_column in refs[:2]:
                evidence.append(
                    {
                        "evidence_id": f"ev_fit_{counter:03d}",
                        "employee_name": member["employee_name"],
                        "risk_tag": risk_tag,
                        "source_column": source_column,
                        "signal_value": str(_value(profile, source_column, default="n/a")),
                        "interpretation": (
                            f"{member['assigned_role']} candidate signal used for {risk_tag}. "
                            "This is a project-fit proxy grounded in the source column."
                        ),
                    }
                )
                counter += 1
    covered_risks = {item["risk_tag"] for item in evidence}
    anchor_member = team["members"][0] if team["members"] else {}
    for risk_tag in team_risk_summary.get("risk_tags", []):
        if risk_tag in covered_risks:
            continue
        source_column = _default_evidence_refs_for_risk(risk_tag)[0]
        signal_value = "project_requirement"
        if risk_tag == "unclear_ownership":
            source_column = "requirements.required_roles"
            gap = _role_coverage_gap(roleplay_requirements_input, team)
            signal_value = ", ".join(gap["uncovered_required_roles"]) or "covered"
        evidence.append(
            {
                "evidence_id": f"ev_fit_{counter:03d}",
                "employee_name": str(anchor_member.get("employee_name", "team")),
                "risk_tag": str(risk_tag),
                "source_column": source_column,
                "signal_value": signal_value,
                "interpretation": (
                    f"{risk_tag} is carried from Requirements Agent project risks or "
                    "team coverage analysis for downstream RolePlay validation."
                ),
            }
        )
        counter += 1
    return evidence


def _completed_handoff_manifest(
    requirements_list: Mapping[str, Any],
    roleplay_requirements_input: Mapping[str, Any],
    selected_team_record: Mapping[str, Any],
    *,
    ranked_employee_count: int,
    ranked_team_count: int,
) -> JsonObject:
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
        "handoff_status": "roleplay_input_packet_ready",
        "provided_inputs": [
            {
                "input_name": "requirements",
                "output_key": "roleplay_requirements_input",
                "recommended_filename": "Roleplay_Requirements_Input.json",
            },
            {
                "input_name": "selected_team",
                "output_key": "roleplay_selected_team_record",
                "recommended_filename": "Roleplay_Selected_Team_Record.json",
            },
            {
                "input_name": "member_snapshots",
                "output_key": "roleplay_employee_fit_profile_snapshots",
                "recommended_filename": "Roleplay_Employee_Fit_Profile_Snapshots.json",
            },
            {
                "input_name": "team_risk_summary",
                "output_key": "roleplay_team_risk_summary",
                "recommended_filename": "Roleplay_Team_Risk_Summary.json",
            },
            {
                "input_name": "evidence_metadata",
                "output_key": "roleplay_evidence_metadata",
                "recommended_filename": "Roleplay_Evidence_Metadata.json",
            },
            {
                "input_name": "simulation_input_packet",
                "output_key": "roleplay_simulation_input_packet",
                "recommended_filename": "Roleplay_Simulation_Input_Packet.json",
            },
        ],
        "required_downstream_inputs": [],
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
        "ranking_summary": {
            "ranked_employee_count": ranked_employee_count,
            "ranked_team_count": ranked_team_count,
            "selected_team_id": selected_team_record.get("team_id"),
            "selected_team_fit_score": selected_team_record.get("team_fit_score"),
            "role_coverage_gap": _role_coverage_gap(
                roleplay_requirements_input,
                selected_team_record,
            ),
        },
        "review_counts": review_counts,
        "selected_employee_columns": list(requirements_list.get("selected_employee_columns", [])),
        "column_weights": dict(requirements_list.get("column_weights", {})),
        "column_priority_order": list(requirements_list.get("column_priority_order", [])),
    }


def _top_role_candidates(
    ranked_employees: list[JsonObject],
    role: str,
    limit: int,
) -> list[JsonObject]:
    candidates = []
    for employee in ranked_employees:
        candidate_roles = employee.get("candidate_roles")
        if candidate_roles is not None and role not in candidate_roles:
            continue
        score = next(
            (role_score for role_score in employee["role_scores"] if role_score["role"] == role),
            None,
        )
        if not score:
            continue
        candidates.append(
            {
                "employee_id": employee["employee_id"],
                "employee_name": employee["employee_name"],
                "job_category_code": employee["job_category_code"],
                "assigned_role": role,
                "fit_score": score["fit_score"],
                "matched_skills": score["matched_skills"],
                "missing_skills": score["missing_skills"],
                "score_breakdown": score["score_breakdown"],
                "signals": score["signals"],
                "risk_tags": score["risk_tags"],
                "evidence_refs": score["evidence_refs"],
                "availability_score": score["score_breakdown"]["availability"],
                "_profile": score["_profile"],
            }
        )
    candidates.sort(key=lambda item: (-item["fit_score"], item["employee_id"]))
    return candidates[:limit]


def _sort_employees_for_role(ranked_employees: list[JsonObject], role: str) -> list[JsonObject]:
    return sorted(
        ranked_employees,
        key=lambda employee: (
            -_fit_score_for_role(employee, role),
            employee["employee_id"],
        ),
    )


def _fit_score_for_role(employee: Mapping[str, Any], role: str) -> float:
    score = next(
        (role_score for role_score in employee.get("role_scores", []) if role_score["role"] == role),
        None,
    )
    return float(score.get("fit_score", 0.0)) if score else 0.0


def _is_exact_role_candidate(employee: Mapping[str, Any], role: str) -> bool:
    target_codes = _role_target_codes(role)
    return bool(target_codes and employee.get("job_category_code") in target_codes)


def _role_target_codes(role: str) -> list[str]:
    role = _roleplay_role(role)
    return list(ROLE_CODE_MAP.get(role, []))


def _candidate_pool_reason(candidate: Mapping[str, Any], role: str) -> str:
    target_codes = _role_target_codes(role)
    if target_codes and candidate.get("job_category_code") in target_codes:
        return "job_category_match"
    return "role_proxy_score"


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


def _required_role_set(roleplay_requirements_input: Mapping[str, Any]) -> list[str]:
    roles = [_roleplay_role(role) for role in roleplay_requirements_input.get("required_roles", [])]
    if "PM" not in roles:
        roles.insert(0, "PM")
    return _unique_strings(roles)


def _role_coverage_gap(
    roleplay_requirements_input: Mapping[str, Any],
    team: Mapping[str, Any],
) -> JsonObject:
    required_roles = _required_role_set(roleplay_requirements_input)
    assigned_roles = _unique_strings(
        _roleplay_role(member.get("assigned_role"))
        for member in team.get("members", [])
        if isinstance(member, Mapping)
    )
    uncovered = [role for role in required_roles if role not in assigned_roles]
    return {
        "required_roles": required_roles,
        "assigned_roles": assigned_roles,
        "uncovered_required_roles": uncovered,
        "is_complete": not uncovered,
    }


def _project_weighted_score(
    profile: Mapping[str, Mapping[str, Any]],
    requirements_list: Mapping[str, Any],
    stats: Mapping[str, tuple[float, float]],
    role: str,
) -> float:
    weights = dict(requirements_list.get("column_weights", {}))
    if not weights:
        weights = {
            "employee.performance_score": 0.2,
            "employee.competency_score": 0.2,
            "jira_activity.sprint_completion_rate": 0.2,
            "jira_activity.ownership_score": 0.2,
            "calendar_activity.busy_minutes": 0.2,
        }
    score_sum = 0.0
    weight_sum = 0.0
    for column_key, weight in weights.items():
        try:
            column_weight = float(weight)
        except (TypeError, ValueError):
            continue
        score_sum += column_weight * _column_score(profile, column_key, stats, role)
        weight_sum += column_weight
    return score_sum / weight_sum if weight_sum else 0.5


def _column_score(
    profile: Mapping[str, Mapping[str, Any]],
    column_key: str,
    stats: Mapping[str, tuple[float, float]],
    role: str,
) -> float:
    if column_key == "employee.job_category_code":
        return _role_match_score(profile, role)
    if column_key == "employee.employment_status":
        return 1.0 if _value(profile, column_key) == "재직" else 0.0
    if column_key == "employee.department":
        return _department_role_score(str(_value(profile, column_key)), role)
    if column_key.endswith(".fetch_status"):
        return 1.0 if _value(profile, column_key) == "success" else 0.2
    if column_key.endswith(".collaboration_style"):
        return _collaboration_style_score(str(_value(profile, column_key)), role)
    if column_key.endswith(".contributed_repositories"):
        return _repository_role_score(str(_value(profile, column_key)), role)
    numeric = _number(_value(profile, column_key))
    if numeric is None:
        return 0.5
    low, high = stats.get(column_key, (numeric, numeric))
    normalized = 0.5 if high <= low else (numeric - low) / (high - low)
    if column_key in NEGATIVE_COLUMNS:
        return 1 - normalized
    return normalized


def _role_match_score(profile: Mapping[str, Mapping[str, Any]], role: str) -> float:
    job_code = str(_value(profile, "employee.job_category_code"))
    target_codes = ROLE_CODE_MAP.get(role, ROLE_CODE_MAP.get(_roleplay_role(role), []))
    if target_codes:
        if job_code in target_codes:
            return 1.0
        if role in {"Mobile Engineer", "Mobile Lead"} and job_code in {"Android", "iOS", "Mobile"}:
            return 1.0
        return 0.15
    if _roleplay_role(role) == "PM":
        leadership = _number(_value(profile, "slack_activity.leadership_score")) or 50
        ownership = _number(_value(profile, "jira_activity.ownership_score")) or 50
        performance = _number(_value(profile, "employee.performance_score")) or 50
        return _clamp01((leadership + ownership + performance) / 300)
    return 0.5


def _role_profile_score(
    profile: Mapping[str, Mapping[str, Any]],
    role: str,
    stats: Mapping[str, tuple[float, float]],
) -> float:
    columns = _role_profile_columns(role)
    return _average(_column_score(profile, column, stats, role) for column in columns)


def _role_profile_columns(role: str) -> list[str]:
    role = _roleplay_role(role)
    if role == "PM":
        return [
            "slack_activity.leadership_score",
            "jira_activity.ownership_score",
            "jira_activity.task_breakdown_count",
            "slack_activity.decision_latency",
            "jira_activity.sprint_completion_rate",
        ]
    if role == "Backend Developer":
        return [
            "employee.competency_score",
            "github_activity.pr_count_3m",
            "jira_activity.completed_issue_count",
            "jira_activity.ownership_score",
            "jira_activity.overdue_issue_count",
        ]
    if role == "Frontend Developer":
        return [
            "employee.competency_score",
            "github_activity.pr_count_3m",
            "jira_activity.avg_cycle_time",
            "jira_activity.scope_change_count",
            "slack_activity.collaboration_frequency",
        ]
    if role == "Mobile Engineer":
        return [
            "employee.competency_score",
            "github_activity.repository_contribution_count",
            "jira_activity.completed_issue_count",
            "calendar_activity.focus_time_minutes",
        ]
    if role == "DevOps Engineer":
        return [
            "employee.competency_score",
            "github_activity.repository_contribution_count",
            "jira_activity.ownership_score",
            "jira_activity.bottleneck_risk",
            "calendar_activity.busy_minutes",
        ]
    if role == "QA Engineer":
        return [
            "employee.competency_score",
            "jira_activity.completed_issue_count",
            "jira_activity.reopened_issue_count",
            "jira_activity.overdue_issue_count",
            "slack_activity.avg_response_time",
        ]
    return ["employee.performance_score", "employee.competency_score"]


def _delivery_score(profile: Mapping[str, Mapping[str, Any]], stats: Mapping[str, tuple[float, float]]) -> float:
    columns = [
        "jira_activity.sprint_completion_rate",
        "jira_activity.completed_issue_count",
        "jira_activity.estimation_accuracy",
        "jira_activity.reopened_issue_count",
        "employee.performance_score",
    ]
    return _average(_column_score(profile, column, stats, "Backend Developer") for column in columns)


def _availability_score(
    profile: Mapping[str, Mapping[str, Any]],
    stats: Mapping[str, tuple[float, float]],
) -> float:
    columns = [
        "calendar_activity.busy_minutes",
        "employee.overtime_hours_12m",
        "slack_activity.burnout_risk",
        "jira_activity.bottleneck_risk",
        "calendar_activity.focus_time_minutes",
    ]
    return _average(_column_score(profile, column, stats, "PM") for column in columns)


def _communication_score(
    profile: Mapping[str, Mapping[str, Any]],
    stats: Mapping[str, tuple[float, float]],
) -> float:
    columns = [
        "slack_activity.avg_response_time",
        "slack_activity.decision_latency",
        "slack_activity.collaboration_frequency",
        "slack_activity.communication_balance",
        "jira_activity.avg_comment_response_time",
    ]
    return _average(_column_score(profile, column, stats, "PM") for column in columns)


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
    if signals["capacity_signal"] == "high_risk":
        tags.append("workload_concentration")
    if signals["communication_signal"] == "high_delay":
        tags.append("communication_delay")
    if signals["delivery_signal"] == "unstable":
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
        schedule_role = "schedule" in lowered and signals["capacity_signal"] != "low_risk"
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
) -> list[str]:
    refs = []
    for column in requirements_list.get("column_priority_order", [])[:8]:
        if isinstance(column, str):
            refs.append(column)
    role = _roleplay_role(role)
    if role == "PM":
        refs.extend(["slack_activity.leadership_score", "jira_activity.task_breakdown_count"])
    elif role == "Backend Developer":
        refs.extend(["github_activity.pr_count_3m", "jira_activity.completed_issue_count"])
    elif role == "Frontend Developer":
        refs.extend(["github_activity.contributed_repositories", "jira_activity.avg_cycle_time"])
    elif role == "Mobile Engineer":
        refs.extend(["github_activity.contributed_repositories", "calendar_activity.focus_time_minutes"])
    elif role == "DevOps Engineer":
        refs.extend(["github_activity.repository_contribution_count", "jira_activity.ownership_score"])
    elif role == "QA Engineer":
        refs.extend(["jira_activity.reopened_issue_count", "jira_activity.overdue_issue_count"])
    if any("communication" in tag for tag in risk_tags):
        refs.append("slack_activity.avg_response_time")
    if any("workload" in tag or "schedule" in tag for tag in risk_tags):
        refs.extend(["calendar_activity.busy_minutes", "employee.overtime_hours_12m"])
    return _unique_strings(refs)[:10]


def _used_employee_column_keys(
    requirements_list: Mapping[str, Any],
    role_slots: list[str],
) -> list[str]:
    columns = []
    for item in requirements_list.get("selected_employee_columns", []):
        if isinstance(item, Mapping):
            columns.append(item.get("column_key", ""))
        elif isinstance(item, str):
            columns.append(item)
    columns.extend(str(column) for column in requirements_list.get("column_weights", {}))
    columns.extend(
        str(column)
        for column in requirements_list.get("column_priority_order", [])
        if isinstance(column, str)
    )
    for role in role_slots:
        columns.extend(_role_profile_columns(role))
    columns.extend(
        [
            "employee.employee_id",
            "employee.employee_name",
            "employee.job_category_code",
            "employee.performance_score",
            "employee.competency_score",
            "employee.overtime_hours_12m",
            "employee.turnover_risk_score",
            "github_activity.pr_count_3m",
            "github_activity.repository_contribution_count",
            "slack_activity.avg_response_time",
            "slack_activity.collaboration_frequency",
            "slack_activity.collaboration_style",
            "slack_activity.leadership_score",
            "slack_activity.burnout_risk",
            "jira_activity.completed_issue_count",
            "jira_activity.sprint_completion_rate",
            "jira_activity.ownership_score",
            "jira_activity.reopened_issue_count",
            "jira_activity.overdue_issue_count",
            "calendar_activity.busy_minutes",
            "calendar_activity.focus_time_minutes",
        ]
    )
    return _unique_strings(column for column in columns if "." in str(column))


def _column_stats(profiles: list[JsonObject]) -> dict[str, tuple[float, float]]:
    values_by_column: dict[str, list[float]] = {}
    for profile in profiles:
        for source, row in profile.items():
            for column, value in row.items():
                numeric = _number(value)
                if numeric is None:
                    continue
                values_by_column.setdefault(f"{source}.{column}", []).append(numeric)
    return {
        key: (min(values), max(values))
        for key, values in values_by_column.items()
        if values
    }


def _capacity_signal(profile: Mapping[str, Mapping[str, Any]], stats: Mapping[str, tuple[float, float]]) -> str:
    risk_score = 1 - _availability_score(profile, stats)
    if risk_score >= 0.66:
        return "high_risk"
    if risk_score >= 0.4:
        return "medium_risk"
    return "low_risk"


def _communication_signal(
    profile: Mapping[str, Mapping[str, Any]],
    stats: Mapping[str, tuple[float, float]],
) -> str:
    score = _communication_score(profile, stats)
    if score >= 0.66:
        return "low_delay"
    if score >= 0.4:
        return "medium_delay"
    return "high_delay"


def _delivery_signal(profile: Mapping[str, Mapping[str, Any]], stats: Mapping[str, tuple[float, float]]) -> str:
    score = _delivery_score(profile, stats)
    if score >= 0.66:
        return "stable"
    if score >= 0.4:
        return "variable"
    return "unstable"


def _collaboration_signal(profile: Mapping[str, Mapping[str, Any]]) -> str:
    value = str(_value(profile, "slack_activity.collaboration_style", default="focused_individual"))
    allowed = {
        "async_deep_worker",
        "connector",
        "focused_individual",
        "rapid_responder",
        "review_hub",
    }
    return value if value in allowed else "focused_individual"


def _fallback_team(ranked_employees: list[JsonObject], role_slots: list[str]) -> JsonObject:
    members = []
    used: set[str] = set()
    for role in role_slots:
        for candidate in _top_role_candidates(ranked_employees, role, 20):
            if candidate["employee_id"] in used:
                continue
            used.add(candidate["employee_id"])
            members.append(candidate)
            break
    return _score_team(
        members,
        required_skills=[],
        project_risk_flags=[],
        role_slots=role_slots,
    ) | {"team_id": "team_001", "team_rank": 1}


def _sanitize_role_score(role_score: Mapping[str, Any]) -> JsonObject:
    return {
        "role": role_score["role"],
        "fit_score": role_score["fit_score"],
        "matched_skills": list(role_score["matched_skills"]),
        "missing_skills": list(role_score["missing_skills"]),
        "score_breakdown": dict(role_score["score_breakdown"]),
        "signals": dict(role_score["signals"]),
        "risk_tags": list(role_score["risk_tags"]),
        "evidence_refs": list(role_score["evidence_refs"]),
    }


def _sanitize_team(team: Mapping[str, Any]) -> JsonObject:
    return {
        "team_id": team["team_id"],
        "team_rank": team["team_rank"],
        "team_fit_score": team["team_fit_score"],
        "members": [
            {
                "employee_id": member["employee_id"],
                "employee_name": member["employee_name"],
                "assigned_role": member["assigned_role"],
                "fit_score": member["fit_score"],
                "matched_skills": list(member["matched_skills"]),
                "missing_skills": list(member["missing_skills"]),
            }
            for member in team["members"]
        ],
        "role_coverage_score": team["role_coverage_score"],
        "skill_coverage_score": team["skill_coverage_score"],
        "availability_score": team["availability_score"],
        "team_risk_flags": list(team["team_risk_flags"]),
        "role_slot_coverage": dict(team.get("role_slot_coverage", {})),
        "bottleneck_members": list(team["bottleneck_members"]),
        "critical_dependencies": list(team["critical_dependencies"]),
        "score_breakdown": dict(team["score_breakdown"]),
    }


def _roleplay_role(role: Any) -> str:
    value = str(role or "").strip()
    return ROLEPLAY_ROLE_ALIASES.get(value, value or "PM")


def _department_role_score(department: str, role: str) -> float:
    role = _roleplay_role(role)
    if role == "Product Designer" and "디자인" in department:
        return 1.0
    if role == "QA Engineer" and "QA" in department:
        return 1.0
    if role in {
        "Backend Developer",
        "Frontend Developer",
        "Mobile Engineer",
        "DevOps Engineer",
    } and "개발" in department:
        return 0.8
    return 0.5


def _collaboration_style_score(style: str, role: str) -> float:
    role = _roleplay_role(role)
    preferred = {
        "PM": {"connector", "rapid_responder"},
        "Backend Developer": {"review_hub", "async_deep_worker"},
        "Frontend Developer": {"connector", "focused_individual", "rapid_responder"},
        "Mobile Engineer": {"focused_individual", "review_hub"},
        "DevOps Engineer": {"connector", "review_hub"},
        "QA Engineer": {"review_hub", "connector"},
    }
    return 1.0 if style in preferred.get(role, set()) else 0.55


def _repository_role_score(repositories: str, role: str) -> float:
    text = repositories.casefold()
    role = _roleplay_role(role)
    role_markers = {
        "Backend Developer": ("api", "server", "backend", "platform"),
        "Frontend Developer": ("frontend", "web", "design-system"),
        "Mobile Engineer": ("mobile", "android", "ios"),
        "DevOps Engineer": ("infra", "platform", "release"),
        "QA Engineer": ("qa", "automation", "release"),
        "Product Designer": ("design", "prototype", "ux"),
    }
    markers = role_markers.get(role, ())
    if not markers:
        return 0.55
    return 1.0 if any(marker in text for marker in markers) else 0.35


def _unique_employees(members: Iterable[Mapping[str, Any]]) -> bool:
    ids = [member["employee_id"] for member in members]
    return len(ids) == len(set(ids))


def _critical_dependencies(members: list[JsonObject]) -> list[str]:
    by_role = {member["assigned_role"]: member["employee_name"] for member in members}
    dependencies = []
    if "Backend Developer" in by_role and "Frontend Developer" in by_role:
        dependencies.append(
            f"{by_role['Backend Developer']} Backend API readiness -> "
            f"{by_role['Frontend Developer']} Frontend integration"
        )
    if "Backend Developer" in by_role and "Mobile Engineer" in by_role:
        dependencies.append(
            f"{by_role['Backend Developer']} notification API contract -> "
            f"{by_role['Mobile Engineer']} mobile delivery"
        )
    if "DevOps Engineer" in by_role:
        dependencies.append(
            f"{by_role['DevOps Engineer']} deployment readiness -> full team release path"
        )
    if "QA Engineer" in by_role:
        dependencies.append(f"{by_role['QA Engineer']} QA coverage -> release decision")
    return dependencies


def _feature_dependency_descriptions(roleplay_requirements_input: Mapping[str, Any]) -> list[str]:
    descriptions = []
    feature_name_by_id = {
        feature.get("feature_id"): feature.get("feature_name")
        for feature in roleplay_requirements_input.get("features", [])
    }
    for feature in roleplay_requirements_input.get("features", []):
        for dependency in feature.get("dependencies", []):
            if dependency in feature_name_by_id:
                descriptions.append(
                    f"{feature_name_by_id[dependency]} -> {feature.get('feature_name')}"
                )
    return descriptions


def _risk_prior_score(tag: str, team: Mapping[str, Any]) -> float:
    member_hits = sum(1 for member in team["members"] if tag in member["risk_tags"])
    base = 0.28 + 0.12 * member_hits
    category = canonical_issue_category(tag)
    if tag in team.get("bottleneck_members", []):
        base += 0.1
    if "integration" in tag or category == "integration_risk":
        base += 0.12
    if "schedule" in tag or "workload" in tag or category in {
        "schedule_risk",
        "workload_concentration",
    }:
        base += 0.1
    if "missing" in tag or category == "technical_dependency_risk":
        base += 0.08
    return round(_clamp01(base), 4)


def _default_evidence_refs_for_risk(risk_tag: str) -> list[str]:
    category = canonical_issue_category(risk_tag)
    if "communication" in risk_tag or category == "communication_delay":
        return ["slack_activity.avg_response_time"]
    if "workload" in risk_tag or "schedule" in risk_tag or category in {
        "schedule_risk",
        "workload_concentration",
    }:
        return ["calendar_activity.busy_minutes", "employee.overtime_hours_12m"]
    if "delivery" in risk_tag:
        return ["jira_activity.sprint_completion_rate"]
    if category == "integration_risk":
        return ["requirements.risk_flags"]
    if category == "qa_coverage_gap":
        return ["requirements.features"]
    if category == "technical_dependency_risk":
        return ["requirements.constraints"]
    if category == "release_blocker":
        return ["requirements.timeline"]
    if category == "unclear_ownership":
        return ["requirements.required_roles"]
    return ["employee.job_category_code"]


def _value(
    profile: Mapping[str, Mapping[str, Any]],
    column_key: str,
    *,
    default: Any = "",
) -> Any:
    if "." not in column_key:
        return default
    source, column = column_key.split(".", 1)
    return profile.get(source, {}).get(column, default)


def _number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", " ", str(value).casefold()).strip()


def _average(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _unique_strings(values: Iterable[str]) -> list[str]:
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


def _empty_role_score(role: str) -> JsonObject:
    return {
        "role": role,
        "fit_score": 0.0,
        "matched_skills": [],
        "missing_skills": [],
        "score_breakdown": {},
        "signals": {
            "capacity_signal": "medium_risk",
            "communication_signal": "medium_delay",
            "delivery_signal": "variable",
            "collaboration_signal": "focused_individual",
        },
        "risk_tags": [],
        "evidence_refs": [],
        "_profile": {},
    }
