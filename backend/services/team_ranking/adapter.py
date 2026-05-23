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
    ) -> TeamRankingAdapterResult:
        roleplay_input = dict(roleplay_requirements_input)
        roleplay_input["project_id"] = session_id
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
            ),
            teams=teams,
        )


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
) -> int:
    role_counts = (
        ranking_result.get("employee_fit_ranking", {})
        .get("_meta", {})
        .get("role_candidate_counts", {})
    )
    total = 1
    for raw_count in role_counts.values():
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
