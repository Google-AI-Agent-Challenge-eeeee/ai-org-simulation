from pathlib import Path
from typing import Any

import backend.services.team_ranking.adapter as adapter_module
from backend.services.team_ranking import RequirementsAgentTeamRankingAdapter


def _roleplay_requirements_input() -> dict[str, Any]:
    return {
        "project_id": "old_project",
        "project_name": "Pinned PM Project",
        "project_summary": "Build an MVP.",
        "required_roles": ["PM", "Backend Developer"],
        "required_skills": ["API Design"],
        "features": [
            {
                "feature_id": "api",
                "feature_name": "API",
                "priority": "P0",
                "assigned_role": "Backend Developer",
                "tech_requirements": ["API Design"],
                "dependencies": [],
                "estimated_days": 3,
                "risk_notes": "",
            }
        ],
        "timeline": {
            "total_sprint_days": 10,
            "milestones": [{"name": "API complete", "due_day": 5, "owner_role": "Backend Developer"}],
        },
        "constraints": [],
        "risk_flags": [],
    }


def _snapshot(
    employee_id: str,
    employee_name: str,
    assigned_role: str,
) -> dict[str, Any]:
    return {
        "employee_id": employee_id,
        "employee_name": employee_name,
        "assigned_role": assigned_role,
        "matched_skills": ["API Design"],
        "missing_skills": [],
        "capacity_signal": "low_risk",
        "communication_signal": "low_delay",
        "delivery_signal": "stable",
        "collaboration_signal": "connector",
        "risk_tags": [],
        "evidence_refs": [],
    }


def test_team_ranking_adapter_maps_requirements_ranking_to_frontend_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, Any] = {}

    def fake_build_employee_team_rankings(
        requirements_list: dict[str, Any],
        roleplay_requirements_input: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        captured["requirements_list"] = requirements_list
        captured["roleplay_requirements_input"] = roleplay_requirements_input
        captured["kwargs"] = kwargs
        return {
            "employee_fit_ranking": {
                "_meta": {
                    "role_candidate_counts": {
                        "PM": 2,
                        "Backend Developer": 4,
                    }
                }
            },
            "team_composition_ranking": {
                "team_rankings": [
                    {
                        "team_id": "team_001",
                        "team_rank": 1,
                        "team_fit_score": 91.25,
                        "role_coverage_score": 1.0,
                        "skill_coverage_score": 0.8,
                        "availability_score": 0.9,
                        "team_risk_flags": ["integration_risk"],
                        "members": [
                            {
                                "employee_id": "E_BE",
                                "employee_name": "Backend One",
                                "assigned_role": "Backend Developer",
                                "missing_skills": ["API contract sync"],
                            },
                            {
                                "employee_id": "E_PM",
                                "employee_name": "Project Lead",
                                "assigned_role": "PM",
                                "missing_skills": [],
                            },
                        ],
                    }
                ]
            },
            "roleplay_simulation_input_packet": {"simulation_id": "sim_test"},
        }

    monkeypatch.setattr(
        adapter_module,
        "build_employee_team_rankings",
        fake_build_employee_team_rankings,
    )

    adapter = RequirementsAgentTeamRankingAdapter(
        employee_data_dir=tmp_path,
        top_candidates_per_role=3,
        max_ranked_teams=1,
    )
    result = adapter.build(
        session_id="sim_adapter",
        requirements_list={"_meta": {"requirements_list_id": "req_001"}},
        roleplay_requirements_input={"project_id": "old_project"},
    )

    assert captured["roleplay_requirements_input"]["project_id"] == "sim_adapter"
    assert captured["kwargs"]["employee_data_dir"] == tmp_path
    assert captured["kwargs"]["top_candidates_per_role"] == 3
    assert result.roleplay_requirements_input["project_id"] == "sim_adapter"
    assert result.ranking_result["roleplay_requirements_input"]["project_id"] == "sim_adapter"
    assert result.total_combinations == 6
    assert result.teams[0]["team_fit_score"] == 91.2
    assert result.teams[0]["badges"] == ["Requirements Agent", "Rule-based", "Top 1"]
    assert result.teams[0]["skill_gaps"] == ["Backend Developer: API contract sync"]
    assert result.teams[0]["members"][0]["color"] == "bg-blue-600"


def test_team_ranking_adapter_pins_requester_pm_across_outputs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_build_employee_team_rankings(
        _requirements_list: dict[str, Any],
        roleplay_requirements_input: dict[str, Any],
        **_kwargs: Any,
    ) -> dict[str, Any]:
        selected_team = {
            "team_id": "team_001",
            "team_rank": 1,
            "team_fit_score": 90.0,
            "role_coverage_score": 1.0,
            "skill_coverage_score": 1.0,
            "availability_score": 0.9,
            "team_risk_flags": [],
            "members": [
                {"employee_id": "E_PM", "employee_name": "Generated PM", "assigned_role": "PM"},
                {
                    "employee_id": "E_BE",
                    "employee_name": "Backend One",
                    "assigned_role": "Backend Developer",
                },
            ],
        }
        snapshots = [
            _snapshot("E_PM", "Generated PM", "PM"),
            _snapshot("E_BE", "Backend One", "Backend Developer"),
        ]
        return {
            "employee_fit_ranking": {
                "_meta": {
                    "role_candidate_counts": {
                        "PM": 3,
                        "Backend Developer": 4,
                    }
                }
            },
            "team_composition_ranking": {
                "team_rankings": [
                    {
                        **selected_team,
                        "members": [
                            {
                                **member,
                                "fit_score": 90.0,
                                "matched_skills": ["API Design"],
                                "missing_skills": [],
                            }
                            for member in selected_team["members"]
                        ],
                    }
                ]
            },
            "roleplay_selected_team_record": selected_team,
            "roleplay_employee_fit_profile_snapshots": snapshots,
            "roleplay_team_risk_summary": {
                "team_id": "team_001",
                "risk_tags": [],
                "risk_prior_scores": {},
                "bottleneck_members": [],
                "critical_dependencies": [],
            },
            "roleplay_evidence_metadata": [],
            "roleplay_simulation_input_packet": {
                "simulation_id": "sim_pm",
                "project_context": roleplay_requirements_input,
                "selected_team": selected_team,
                "member_snapshots": snapshots,
                "team_risk_summary": {
                    "team_id": "team_001",
                    "risk_tags": [],
                    "risk_prior_scores": {},
                    "bottleneck_members": [],
                    "critical_dependencies": [],
                },
                "evidence_metadata": [],
            },
        }

    monkeypatch.setattr(
        adapter_module,
        "build_employee_team_rankings",
        fake_build_employee_team_rankings,
    )

    result = RequirementsAgentTeamRankingAdapter(
        employee_data_dir=tmp_path,
        top_candidates_per_role=3,
    ).build(
        session_id="sim_pm",
        requirements_list={},
        roleplay_requirements_input=_roleplay_requirements_input(),
        requester_pm={"name": "김PM", "preset": "speed"},
    )

    assert result.total_combinations == 3
    assert result.teams[0]["members"][0]["employee_name"] == "김PM"
    assert result.teams[0]["members"][0]["employee_id"] == "requester_pm"
    packet = result.roleplay_packet
    assert packet.selected_team.members[0].employee_name == "김PM"
    assert packet.member_snapshots[0].employee_name == "김PM"
    assert packet.member_snapshots[0].matched_skills[-1] == "speed PM style"
