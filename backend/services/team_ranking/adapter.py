"""Adapter for Requirements Agent team ranking outputs.

The current ranking implementation is still CSV-backed. Keeping that detail
behind this adapter makes the API orchestration stable while we later replace
the source with Postgres-backed employee/activity data.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.agents.requirements_agent.modules.employee_team_ranking import (
    DEFAULT_EMPLOYEE_DATA_DIR,
    build_employee_team_rankings,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    SimulationInputPacket,
)

JsonObject = dict[str, Any]

DEFAULT_MAX_TEAM_SIZE = 6
DEFAULT_TOP_CANDIDATES_PER_ROLE = 5
DEFAULT_MAX_RANKED_TEAMS = 1

ROLE_COLORS: dict[str, str] = {
    "PM": "bg-purple-500",
    "BE": "bg-blue-600",
    "WEB": "bg-cyan-500",
    "iOS": "bg-slate-500",
    "Android": "bg-green-600",
    "Infra": "bg-orange-500",
    "QA": "bg-amber-600",
    "DS": "bg-pink-500",
}

ROLE_KEYS: dict[str, str] = {
    "PM": "PM",
    "Product Manager": "PM",
    "Backend Developer": "BE",
    "Backend Engineer": "BE",
    "Frontend Developer": "WEB",
    "Web Frontend Engineer": "WEB",
    "DevOps Engineer": "Infra",
    "Infrastructure Engineer": "Infra",
    "QA Engineer": "QA",
    "iOS Developer": "iOS",
    "Android Developer": "Android",
    "Data Scientist": "DS",
    "Product Designer": "DS",
}


@dataclass(frozen=True)
class TeamRankingAdapterResult:
    ranking_result: JsonObject
    roleplay_requirements_input: JsonObject
    total_combinations: int
    teams: list[JsonObject]

    @property
    def roleplay_packet(self) -> SimulationInputPacket:
        return SimulationInputPacket.model_validate(
            self.ranking_result["roleplay_simulation_input_packet"]
        )


class RequirementsAgentTeamRankingAdapter:
    """Build frontend and RolePlay inputs from Requirements Agent ranking outputs."""

    def __init__(
        self,
        *,
        employee_data_dir: str | Path = DEFAULT_EMPLOYEE_DATA_DIR,
        max_team_size: int = DEFAULT_MAX_TEAM_SIZE,
        top_candidates_per_role: int = DEFAULT_TOP_CANDIDATES_PER_ROLE,
        max_ranked_teams: int = DEFAULT_MAX_RANKED_TEAMS,
    ) -> None:
        self.employee_data_dir = employee_data_dir
        self.max_team_size = max_team_size
        self.top_candidates_per_role = top_candidates_per_role
        self.max_ranked_teams = max_ranked_teams

    def build(
        self,
        *,
        session_id: str,
        requirements_list: Mapping[str, Any],
        roleplay_requirements_input: Mapping[str, Any],
        requester_pm: Mapping[str, Any] | None = None,
    ) -> TeamRankingAdapterResult:
        roleplay_input = dict(roleplay_requirements_input)
        roleplay_input["project_id"] = session_id
        roleplay_input["required_roles"] = _required_roles_with_pm(
            roleplay_input.get("required_roles")
        )
        ranking_result = build_employee_team_rankings(
            requirements_list,
            roleplay_input,
            employee_data_dir=self.employee_data_dir,
            max_team_size=self.max_team_size,
            top_candidates_per_role=self.top_candidates_per_role,
            max_ranked_teams=self.max_ranked_teams,
            simulation_id=session_id,
        )
        ranking_result["roleplay_requirements_input"] = roleplay_input
        ranking_result = _pin_requester_pm(ranking_result, requester_pm)
        teams = _frontend_team_candidates_from_ranking(
            ranking_result,
            max_ranked_teams=self.max_ranked_teams,
        )
        return TeamRankingAdapterResult(
            ranking_result=ranking_result,
            roleplay_requirements_input=roleplay_input,
            total_combinations=_ranking_total_combinations(
                ranking_result,
                team_count=len(teams),
                top_candidates_per_role=self.top_candidates_per_role,
                fixed_roles={"PM"} if _requester_pm_member(requester_pm) is not None else set(),
            ),
            teams=teams,
        )


def _pin_requester_pm(
    ranking_result: JsonObject,
    requester_pm: Mapping[str, Any] | None,
) -> JsonObject:
    pm_member = _requester_pm_member(requester_pm)
    if pm_member is None:
        return ranking_result

    result = dict(ranking_result)
    for ranking_key, teams_key in (
        ("team_composition_ranking", "team_rankings"),
        ("team_composition_candidates", "team_candidates"),
    ):
        ranking = result.get(ranking_key)
        if isinstance(ranking, Mapping):
            ranking_copy = dict(ranking)
            ranking_copy[teams_key] = [
                _pin_pm_to_ranked_team(team, pm_member)
                for team in ranking.get(teams_key, [])
                if isinstance(team, Mapping)
            ]
            result[ranking_key] = ranking_copy

    selected_team = result.get("roleplay_selected_team_record")
    if isinstance(selected_team, Mapping):
        result["roleplay_selected_team_record"] = _pin_pm_to_selected_team(
            selected_team,
            pm_member,
        )

    pm_snapshot = _requester_pm_snapshot(pm_member, requester_pm)
    snapshots = result.get("roleplay_employee_fit_profile_snapshots")
    if isinstance(snapshots, list):
        result["roleplay_employee_fit_profile_snapshots"] = _pin_pm_snapshot(
            snapshots,
            pm_snapshot,
        )

    packet = result.get("roleplay_simulation_input_packet")
    if isinstance(packet, Mapping):
        packet_copy = dict(packet)
        selected_from_packet = packet_copy.get("selected_team")
        if isinstance(selected_from_packet, Mapping):
            packet_copy["selected_team"] = _pin_pm_to_selected_team(
                selected_from_packet,
                pm_member,
            )
        elif isinstance(result.get("roleplay_selected_team_record"), Mapping):
            packet_copy["selected_team"] = result["roleplay_selected_team_record"]

        packet_snapshots = packet_copy.get("member_snapshots")
        if isinstance(packet_snapshots, list):
            packet_copy["member_snapshots"] = _pin_pm_snapshot(
                packet_snapshots,
                pm_snapshot,
            )
        else:
            packet_copy["member_snapshots"] = result.get(
                "roleplay_employee_fit_profile_snapshots",
                [pm_snapshot],
            )
        result["roleplay_simulation_input_packet"] = packet_copy

    return result


def _requester_pm_member(requester_pm: Mapping[str, Any] | None) -> JsonObject | None:
    if requester_pm is None:
        return None
    name = str(requester_pm.get("name") or "").strip()
    if not name:
        return None
    return {
        "employee_id": str(requester_pm.get("employee_id") or "pm_persona"),
        "employee_name": name,
        "assigned_role": "PM",
        "fit_score": 100.0,
        "matched_skills": _requester_pm_skills(requester_pm),
        "missing_skills": [],
    }


def _requester_pm_skills(requester_pm: Mapping[str, Any] | None) -> list[str]:
    skills = ["project ownership", "requirements clarification", "stakeholder alignment"]
    if requester_pm is None:
        return skills
    preset = str(requester_pm.get("preset") or "").strip()
    persona = str(requester_pm.get("persona") or "").strip()
    priority = str(requester_pm.get("priority") or "").strip()
    if preset:
        skills.append(f"{preset} PM style")
    if persona:
        skills.append(f"PM persona input: {_truncate(persona, 220)}")
    if priority:
        skills.append(f"PM operating priority: {_truncate(priority, 160)}")
    return _unique_strings(skills)


def _pin_pm_to_ranked_team(team: Mapping[str, Any], pm_member: Mapping[str, Any]) -> JsonObject:
    team_copy = dict(team)
    team_copy["members"] = _pin_pm_member(team.get("members", []), pm_member)
    return team_copy


def _pin_pm_to_selected_team(
    selected_team: Mapping[str, Any],
    pm_member: Mapping[str, Any],
) -> JsonObject:
    team_copy = dict(selected_team)
    team_copy["members"] = [
        {
            "employee_id": member["employee_id"],
            "employee_name": member["employee_name"],
            "assigned_role": member["assigned_role"],
        }
        for member in _pin_pm_member(selected_team.get("members", []), pm_member)
    ]
    return team_copy


def _pin_pm_member(
    members: Any,
    pm_member: Mapping[str, Any],
) -> list[JsonObject]:
    normalized = [dict(member) for member in members if isinstance(member, Mapping)]
    pinned = False
    result = []
    for member in normalized:
        if _is_pm_role(member.get("assigned_role")):
            result.append({**member, **pm_member})
            pinned = True
        else:
            result.append(member)
    if not pinned:
        result.insert(0, dict(pm_member))
    return result


def _requester_pm_snapshot(
    pm_member: Mapping[str, Any],
    requester_pm: Mapping[str, Any] | None,
) -> JsonObject:
    return {
        "employee_id": pm_member["employee_id"],
        "employee_name": pm_member["employee_name"],
        "assigned_role": "PM",
        "matched_skills": list(pm_member.get("matched_skills", [])),
        "missing_skills": _requester_pm_constraints(requester_pm),
        "capacity_signal": "low_risk",
        "communication_signal": "low_delay",
        "delivery_signal": "stable",
        "collaboration_signal": "connector",
        "risk_tags": ["pm_persona_input"],
        "evidence_refs": ["pm.persona_input"],
    }


def _pin_pm_snapshot(snapshots: list[Any], pm_snapshot: Mapping[str, Any]) -> list[JsonObject]:
    normalized = [dict(snapshot) for snapshot in snapshots if isinstance(snapshot, Mapping)]
    pinned = False
    result = []
    for snapshot in normalized:
        if _is_pm_role(snapshot.get("assigned_role")):
            result.append({**snapshot, **pm_snapshot})
            pinned = True
        else:
            result.append(snapshot)
    if not pinned:
        result.insert(0, dict(pm_snapshot))
    return result


def _is_pm_role(role: Any) -> bool:
    return str(role or "").strip() in {"PM", "Product Manager", "Product Lead"}


def _required_roles_with_pm(raw_roles: Any) -> list[str]:
    roles = [str(role) for role in raw_roles] if isinstance(raw_roles, list) else []
    without_pm = [role for role in roles if not _is_pm_role(role)]
    return ["PM", *without_pm]


def _requester_pm_constraints(requester_pm: Mapping[str, Any] | None) -> list[str]:
    if requester_pm is None:
        return []
    constraints = str(requester_pm.get("constraints") or "").strip()
    if not constraints:
        return []
    return [f"PM user constraint: {_truncate(constraints, 220)}"]


def _truncate(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "..."


def _frontend_team_candidates_from_ranking(
    ranking_result: Mapping[str, Any],
    *,
    max_ranked_teams: int,
) -> list[JsonObject]:
    teams = (
        ranking_result.get("team_composition_ranking", {}).get("team_rankings")
        or ranking_result.get("team_composition_candidates", {}).get("team_candidates")
        or []
    )
    return [_frontend_team_candidate(team) for team in teams[:max_ranked_teams]]


def _frontend_team_candidate(team: Mapping[str, Any]) -> JsonObject:
    members = [
        _team_member(
            str(member.get("employee_id", "")),
            str(member.get("employee_name", "")),
            str(member.get("assigned_role", "Team Member")),
        )
        for member in team.get("members", [])
    ]
    return {
        "team_id": str(team.get("team_id", "team_001")),
        "team_name": _team_name(team),
        "team_rank": int(team.get("team_rank") or 1),
        "team_fit_score": round(float(team.get("team_fit_score") or 0.0), 1),
        "role_coverage_score": float(team.get("role_coverage_score") or 0.0),
        "skill_coverage_score": float(team.get("skill_coverage_score") or 0.0),
        "availability_score": float(team.get("availability_score") or 0.0),
        "team_risk_flags": [str(flag) for flag in team.get("team_risk_flags", [])],
        "badges": ["Requirements Agent", "Rule-based", "Top 1"],
        "rationale": (
            "Selected by Requirements Agent ranking from PRD-required roles, "
            "dataset-backed employee signals, and team-level risk coverage."
        ),
        "skill_gaps": _skill_gaps_from_ranked_team(team),
        "members": members,
    }


def _team_member(employee_id: str, name: str, assigned_role: str) -> JsonObject:
    role_key = ROLE_KEYS.get(assigned_role, assigned_role)
    return {
        "employee_id": employee_id,
        "employee_name": name,
        "assigned_role": assigned_role,
        "initials": _initials(name),
        "color": ROLE_COLORS.get(role_key, "bg-zinc-500"),
    }


def _team_name(team: Mapping[str, Any]) -> str:
    rank = int(team.get("team_rank") or 1)
    return f"Recommended Team #{rank}"


def _skill_gaps_from_ranked_team(team: Mapping[str, Any]) -> list[str]:
    gaps = []
    for member in team.get("members", []):
        role = str(member.get("assigned_role", "Team Member"))
        for skill in member.get("missing_skills", []):
            gaps.append(f"{role}: {skill}")
    return _unique_strings(gaps)[:6]


def _ranking_total_combinations(
    ranking_result: Mapping[str, Any],
    *,
    team_count: int,
    top_candidates_per_role: int,
    fixed_roles: set[str],
) -> int:
    role_counts = (
        ranking_result.get("employee_fit_ranking", {})
        .get("_meta", {})
        .get("role_candidate_counts", {})
    )
    total = 1
    for role, raw_count in role_counts.items():
        if role in fixed_roles:
            continue
        try:
            count = int(raw_count)
        except (TypeError, ValueError):
            count = 0
        total *= max(1, min(count, top_candidates_per_role))
    return max(team_count, total)


def _initials(name: str) -> str:
    parts = name.split()
    if len(parts) <= 1:
        return name[:2]
    return "".join(part[:1] for part in parts[:2])


def _unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = value.strip()
        if not item:
            continue
        marker = item.casefold()
        if marker in seen:
            continue
        seen.add(marker)
        result.append(item)
    return result
