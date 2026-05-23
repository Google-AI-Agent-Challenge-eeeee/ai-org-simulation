from collections.abc import Iterator

from fastapi.testclient import TestClient

from backend.main import app
from backend.orchestration import session_flow


def test_create_session_returns_generated_session_id() -> None:
    client = TestClient(app)

    response = client.post("/api/sessions", json={"prd": "sample"})

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"].startswith("sim_")


def test_requirements_review_contract_matches_frontend_shape() -> None:
    client = TestClient(app)

    response = client.get("/api/sessions/sim_test/requirements")

    assert response.status_code == 200
    body = response.json()
    assert body["project_name"]
    assert body["required_roles"]
    assert body["required_skills"]
    assert body["features"]
    assert body["timeline_days"] > 0
    assert 0 <= body["confidence"] <= 100


def test_requirements_review_uses_session_prd_input() -> None:
    client = TestClient(app)
    session_response = client.post(
        "/api/sessions",
        json={
            "prd": (
                "# Inventory Control MVP\n\n"
                "Goal: Build an inventory control dashboard in 4 weeks.\n\n"
                "## Functional Requirements\n"
                "- Dashboard analytics\n"
            )
        },
    )
    session_id = session_response.json()["session_id"]

    response = client.get(f"/api/sessions/{session_id}/requirements")

    assert response.status_code == 200
    body = response.json()
    assert body["project_name"] == "Inventory Control MVP"
    assert "inventory control dashboard" in body["project_summary"]


def test_requirements_accept_and_revise_contracts() -> None:
    client = TestClient(app)

    accept_response = client.post(
        "/api/sessions/sim_test/requirements/accept",
        json={"feedback": "ok"},
    )
    revise_response = client.post(
        "/api/sessions/sim_test/requirements/revise",
        json={"feedback": "recheck risks"},
    )

    assert accept_response.status_code == 200
    assert accept_response.json() == {"ok": True}
    assert revise_response.status_code == 200
    assert revise_response.json()["features"]


def test_team_selection_contract_matches_frontend_shape() -> None:
    client = TestClient(app)

    response = client.get("/api/sessions/sim_test/teams")

    assert response.status_code == 200
    body = response.json()
    assert body["totalCombinations"] >= len(body["teams"])
    assert body["teams"]
    team = body["teams"][0]
    assert team["team_id"]
    assert team["members"]
    assert 0 <= team["team_fit_score"] <= 100


def test_team_selection_pins_session_pm_persona() -> None:
    client = TestClient(app)
    session_id = client.post(
        "/api/sessions",
        json={
            "prd": "# Team Ops MVP\n\nGoal: Build a team ops dashboard in 2 weeks.",
            "pmPersona": {
                "name": "김PM",
                "preset": "speed",
                "persona": "Fast decision maker",
            },
            "pmPriority": "speed",
        },
    ).json()["session_id"]

    response = client.get(f"/api/sessions/{session_id}/teams")

    assert response.status_code == 200
    team = response.json()["teams"][0]
    assert team["members"][0]["employee_name"] == "김PM"
    assert team["members"][0]["assigned_role"] == "PM"


def test_team_selection_uses_requirements_agent_ranking(monkeypatch) -> None:
    from backend.services.team_ranking import TeamRankingAdapterResult

    def fake_team_ranking(_record: object) -> TeamRankingAdapterResult:
        ranking_result = {
            "employee_fit_ranking": {
                "_meta": {
                    "role_candidate_counts": {
                        "PM": 2,
                        "Backend Developer": 3,
                    }
                }
            },
            "team_composition_ranking": {
                "team_rankings": [
                    {
                        "team_id": "team_001",
                        "team_rank": 1,
                        "team_fit_score": 91.2,
                        "role_coverage_score": 1.0,
                        "skill_coverage_score": 0.8,
                        "availability_score": 0.9,
                        "team_risk_flags": ["integration_risk"],
                        "members": [
                            {
                                "employee_id": "E_RA_001",
                                "employee_name": "Ranked Member",
                                "assigned_role": "Backend Developer",
                                "missing_skills": ["API contract sync"],
                            },
                            {
                                "employee_id": "E_RA_002",
                                "employee_name": "Ranked PM",
                                "assigned_role": "PM",
                                "missing_skills": [],
                            },
                        ],
                    }
                ]
            },
        }
        return TeamRankingAdapterResult(
            ranking_result=ranking_result,
            roleplay_requirements_input={"project_id": "sim_ranked"},
            total_combinations=6,
            teams=[
                {
                    "team_id": "team_001",
                    "team_name": "Recommended Team #1",
                    "team_rank": 1,
                    "team_fit_score": 91.2,
                    "role_coverage_score": 1.0,
                    "skill_coverage_score": 0.8,
                    "availability_score": 0.9,
                    "team_risk_flags": ["integration_risk"],
                    "badges": ["Requirements Agent", "Rule-based", "Top 1"],
                    "skill_gaps": ["Backend Developer: API contract sync"],
                    "members": [
                        {
                            "employee_id": "E_RA_001",
                            "employee_name": "Ranked Member",
                            "assigned_role": "Backend Developer",
                            "initials": "RM",
                            "color": "bg-blue-600",
                        },
                        {
                            "employee_id": "E_RA_002",
                            "employee_name": "Ranked PM",
                            "assigned_role": "PM",
                            "initials": "RP",
                            "color": "bg-purple-500",
                        },
                    ],
                }
            ],
        )

    monkeypatch.setattr(session_flow, "_get_or_build_team_ranking", fake_team_ranking)
    client = TestClient(app)

    response = client.get("/api/sessions/sim_ranked/teams")

    assert response.status_code == 200
    body = response.json()
    assert body["totalCombinations"] == 6
    assert body["teams"][0]["team_id"] == "team_001"
    assert body["teams"][0]["badges"] == ["Requirements Agent", "Rule-based", "Top 1"]
    assert body["teams"][0]["skill_gaps"] == ["Backend Developer: API contract sync"]


def test_pm_persona_is_used_as_roleplay_pm(monkeypatch) -> None:
    import backend.services.team_ranking.adapter as adapter_module

    roleplay_input = {
        "project_id": "old_project",
        "project_name": "PM Persona E2E",
        "project_summary": "Verify PM input is used.",
        "required_roles": ["Backend Developer"],
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
            "milestones": [
                {"name": "API complete", "due_day": 5, "owner_role": "Backend Developer"}
            ],
        },
        "constraints": [],
        "risk_flags": [],
    }

    def fake_requirements_result(_record: object) -> dict[str, object]:
        return {
            "outputs": {
                "requirements_list": {"project_name": "PM Persona E2E"},
                "roleplay_requirements_input": dict(roleplay_input),
            }
        }

    def fake_build_employee_team_rankings(
        _requirements_list: dict[str, object],
        roleplay_requirements_input: dict[str, object],
        **_kwargs: object,
    ) -> dict[str, object]:
        selected_team = {
            "team_id": "team_db_top_001",
            "team_rank": 1,
            "team_fit_score": 90.0,
            "role_coverage_score": 1.0,
            "skill_coverage_score": 1.0,
            "availability_score": 0.9,
            "team_risk_flags": ["availability_risk"],
            "members": [
                {"employee_id": "E_DB_PM", "employee_name": "DB Manager", "assigned_role": "PM"},
                {
                    "employee_id": "E_DB_BE",
                    "employee_name": "DB Backend",
                    "assigned_role": "Backend Developer",
                },
            ],
        }
        snapshots = [
            {
                "employee_id": "E_DB_PM",
                "employee_name": "DB Manager",
                "assigned_role": "PM",
                "matched_skills": ["planning"],
                "missing_skills": [],
                "capacity_signal": "low_risk",
                "communication_signal": "low_delay",
                "delivery_signal": "stable",
                "collaboration_signal": "connector",
                "risk_tags": [],
                "evidence_refs": [],
            },
            {
                "employee_id": "E_DB_BE",
                "employee_name": "DB Backend",
                "assigned_role": "Backend Developer",
                "matched_skills": ["API Design"],
                "missing_skills": [],
                "capacity_signal": "low_risk",
                "communication_signal": "low_delay",
                "delivery_signal": "stable",
                "collaboration_signal": "review_hub",
                "risk_tags": [],
                "evidence_refs": [],
            },
        ]
        risk_summary = {
            "team_id": "team_db_top_001",
            "risk_tags": [],
            "risk_prior_scores": {},
            "bottleneck_members": [],
            "critical_dependencies": [],
        }
        return {
            "employee_fit_ranking": {
                "_meta": {"role_candidate_counts": {"PM": 1, "Backend Developer": 1}}
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
            "roleplay_team_risk_summary": risk_summary,
            "roleplay_evidence_metadata": [],
            "roleplay_simulation_input_packet": {
                "simulation_id": "sim_pm_persona",
                "project_context": roleplay_requirements_input,
                "selected_team": selected_team,
                "member_snapshots": snapshots,
                "team_risk_summary": risk_summary,
                "evidence_metadata": [],
            },
        }

    monkeypatch.setattr(session_flow, "_ensure_requirements_agent_result", fake_requirements_result)
    monkeypatch.setattr(
        adapter_module,
        "build_employee_team_rankings",
        fake_build_employee_team_rankings,
    )
    client = TestClient(app)
    session_id = client.post(
        "/api/sessions",
        json={
            "prd": "# PM Persona E2E\n\nGoal: verify PM input is used.",
            "pmPersona": {
                "name": "Input PM",
                "preset": "quality",
                "persona": "Risk-aware PM who asks for explicit mitigation plans.",
                "constraints": "Keep budget and compliance constraints visible.",
            },
            "pmPriority": "quality / protect release confidence",
        },
    ).json()["session_id"]

    teams = client.get(f"/api/sessions/{session_id}/teams").json()["teams"]
    members = teams[0]["members"]
    pm_members = [member for member in members if member["assigned_role"] == "PM"]

    assert pm_members == [
        {
            "employee_id": "pm_persona",
            "employee_name": "Input PM",
            "assigned_role": "PM",
            "initials": "IP",
            "color": "bg-purple-500",
        }
    ]
    assert all(member["employee_id"] != "E_DB_PM" for member in members)

    record = session_flow._get_or_create_session(session_id)
    packet = session_flow._roleplay_packet(record)
    pm_snapshot = next(item for item in packet.member_snapshots if item.assigned_role == "PM")

    assert packet.project_context.required_roles[0] == "PM"
    assert packet.selected_team.members[0].employee_name == "Input PM"
    assert pm_snapshot.employee_name == "Input PM"
    assert pm_snapshot.capacity_signal == "low_risk"
    assert any("Risk-aware PM" in skill for skill in pm_snapshot.matched_skills)
    assert any("protect release confidence" in skill for skill in pm_snapshot.matched_skills)
    assert pm_snapshot.missing_skills == [
        "PM user constraint: Keep budget and compliance constraints visible."
    ]


def test_team_select_returns_ok() -> None:
    client = TestClient(app)

    response = client.post("/api/sessions/sim_test/teams/select", json={"teamId": "team_001"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_selected_team_is_reflected_in_report() -> None:
    client = TestClient(app)
    session_id = client.post("/api/sessions", json={"prd": "sample"}).json()["session_id"]
    teams = client.get(f"/api/sessions/{session_id}/teams").json()["teams"]

    select_response = client.post(
        f"/api/sessions/{session_id}/teams/select",
        json={"teamId": teams[0]["team_id"]},
    )
    list(session_flow.iter_pipeline_sse(session_id, "stub"))
    report_response = client.get(f"/api/sessions/{session_id}/report")

    assert select_response.status_code == 200
    assert report_response.status_code == 200
    assert report_response.json()["selectedTeam"]["teamId"] == teams[0]["team_id"]


def test_report_returns_not_ready_before_stream() -> None:
    client = TestClient(app)
    session_id = client.post(
        "/api/sessions",
        json={"prd": "# Report Pending\n\nGoal: do not use sample output."},
    ).json()["session_id"]

    response = client.get(f"/api/sessions/{session_id}/report")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "REPORT_NOT_READY"


def test_report_contract_returns_selected_session_result() -> None:
    client = TestClient(app)
    session_id = client.post(
        "/api/sessions",
        json={"prd": "# Session Report\n\nGoal: build a session-scoped report."},
    ).json()["session_id"]
    list(session_flow.iter_pipeline_sse(session_id, "stub"))

    response = client.get(f"/api/sessions/{session_id}/report")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == session_id
    assert body["team"]
    assert body["metrics"]["teamFitScore"] >= 0
    assert body["meetingSummary"]
    assert body["phaseSummaries"]
    assert body["reportSummary"]["generatedFrom"] == [
        "Simulation_OUTPUT",
        "Team_Simulation_Log",
        "Issue_Risk_Summary",
        "Score_Breakdown",
    ]
    assert body["scoreBreakdown"]
    assert body["topRisks"]
    assert body["phaseDetails"]


def test_stream_endpoint_uses_sse_media_type(monkeypatch) -> None:
    def fake_stream(session_id: str, llm_mode: str) -> Iterator[str]:
        assert session_id == "sim_test"
        assert llm_mode == "stub"
        yield session_flow.sse("status", {"stage": "done", "text": "ok"})
        yield session_flow.sse("done", {})

    monkeypatch.setattr(session_flow, "iter_pipeline_sse", fake_stream)
    client = TestClient(app)

    with client.stream("GET", "/api/sessions/sim_test/stream?mode=stub") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = response.read().decode("utf-8")

    assert "event: status" in body
    assert "event: done" in body


def test_stream_endpoint_uses_simulation_llm_mode_env(monkeypatch) -> None:
    from backend.core.config import get_settings

    def fake_stream(session_id: str, llm_mode: str) -> Iterator[str]:
        assert session_id == "sim_vertex"
        assert llm_mode == "vertex"
        yield session_flow.sse("status", {"stage": "done", "text": "ok"})
        yield session_flow.sse("done", {})

    monkeypatch.setenv("SIMULATION_LLM_MODE", "vertex")
    get_settings.cache_clear()
    monkeypatch.setattr(session_flow, "iter_pipeline_sse", fake_stream)
    client = TestClient(app)

    with client.stream("GET", "/api/sessions/sim_vertex/stream") as response:
        assert response.status_code == 200
        body = response.read().decode("utf-8")

    assert "event: done" in body
    get_settings.cache_clear()


def test_requirements_agent_vertex_failure_falls_back_to_stub(monkeypatch) -> None:
    from backend.core.config import get_settings

    original_build_section_extractor = session_flow.build_section_extractor

    def fake_build_section_extractor(*, config, **kwargs):
        if config.mode == "vertex":
            raise RuntimeError("vertex unavailable")
        return original_build_section_extractor(config=config, **kwargs)

    monkeypatch.setenv("REQUIREMENTS_LLM_MODE", "vertex")
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    get_settings.cache_clear()
    monkeypatch.setattr(
        session_flow,
        "build_section_extractor",
        fake_build_section_extractor,
    )
    record = session_flow.SessionRecord(
        session_id="sim_requirements_vertex_fallback",
        prd_text="# Vertex Fallback Demo\n\nGoal: Build a demo dashboard.",
    )

    result = session_flow._run_requirements_agent(record)

    llm = result["session"]["llm"]
    assert llm["requested_mode"] == "vertex"
    assert llm["actual_mode"] == "stub"
    assert "vertex unavailable" in llm["fallback_error"]
    assert record.metadata["requirements_llm"]["actual_mode"] == "stub"
    get_settings.cache_clear()


def test_roleplay_stream_populates_report_agent_outputs() -> None:
    client = TestClient(app)
    session_id = client.post(
        "/api/sessions",
        json={"prd": "# Report Pipeline E2E\n\nGoal: verify roleplay to report output."},
    ).json()["session_id"]

    chunks = list(session_flow.iter_pipeline_sse(session_id, "stub"))
    report = session_flow.get_report(session_id)
    record = session_flow._get_or_create_session(session_id)

    assert any("ReportAgent inputs finalized" in chunk for chunk in chunks)
    assert isinstance(record.roleplay_outputs, dict)
    assert report["reportSummary"]["generatedFrom"] == [
        "Simulation_OUTPUT",
        "Team_Simulation_Log",
        "Issue_Risk_Summary",
        "Score_Breakdown",
    ]
    assert len(report["scoreBreakdown"]) == 7
    assert len(report["phaseDetails"]) == 5
    assert report["phaseDetails"][0]["participantTurns"]
    assert report["topRisks"]


def test_shadow_requirements_payload_uses_session_prd_input() -> None:
    client = TestClient(app)
    session_response = client.post(
        "/api/sessions",
        json={
            "prd": (
                "# Billing Automation MVP\n\n"
                "Goal: Build a billing automation dashboard in 3 weeks.\n\n"
                "## Functional Requirements\n"
                "- Invoice workflow\n"
            )
        },
    )
    session_id = session_response.json()["session_id"]
    session_flow.get_requirements_summary(session_id)

    record = session_flow._get_or_create_session(session_id)
    payload = session_flow._shadow_requirements_payload(record)

    assert payload["project_id"] == session_id
    assert payload["project_name"] == "Billing Automation MVP"
    assert "billing automation dashboard" in payload["project_summary"]
    assert payload["features"][0]["tech_requirements"]
    assert payload["timeline"]["total_sprint_days"] > 0


def test_shadow_stream_payloads_build_simulation_input_packet() -> None:
    client = TestClient(app)
    session_id = client.post("/api/sessions", json={"prd": "# Team Ops MVP"}).json()["session_id"]
    client.get(f"/api/sessions/{session_id}/requirements")
    client.get(f"/api/sessions/{session_id}/teams")

    record = session_flow._get_or_create_session(session_id)
    packet = session_flow._roleplay_packet(record)

    assert packet.simulation_id == session_id
    assert packet.project_context.project_id == session_id
    assert packet.selected_team.team_id == record.team_candidates[0]["team_id"]
    assert packet.member_snapshots
    assert packet.team_risk_summary.team_id == packet.selected_team.team_id
