from pathlib import Path
from typing import Any

import backend.services.team_ranking.adapter as adapter_module
from backend.services.team_ranking import RequirementsAgentTeamRankingAdapter


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
