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


def test_team_selection_prefers_db_candidates(monkeypatch) -> None:
    from backend.services.team_selector import TeamSelectionResult

    def fake_db_candidates(_record: object) -> TeamSelectionResult:
        return TeamSelectionResult(
            total_combinations=5,
            teams=[
                {
                    "team_id": "team_db_top_001",
                    "team_name": "DB Top Recommendation",
                    "team_rank": 1,
                    "team_fit_score": 91.2,
                    "role_coverage_score": 1.0,
                    "skill_coverage_score": 1.0,
                    "availability_score": 0.9,
                    "team_risk_flags": [],
                    "members": [
                        {
                            "employee_id": "E_DB_001",
                            "employee_name": "DB Member",
                            "assigned_role": "Backend Developer",
                            "initials": "DB",
                            "color": "bg-blue-600",
                        },
                        {
                            "employee_id": "E_DB_002",
                            "employee_name": "DB QA",
                            "assigned_role": "QA Engineer",
                            "initials": "DQ",
                            "color": "bg-amber-600",
                        },
                    ],
                }
            ],
        )

    monkeypatch.setattr(session_flow, "_load_db_team_candidates", fake_db_candidates)
    client = TestClient(app)

    response = client.get("/api/sessions/sim_db/teams")

    assert response.status_code == 200
    body = response.json()
    assert body["totalCombinations"] == 5
    assert body["teams"][0]["team_id"] == "team_db_top_001"


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
    report_response = client.get(f"/api/sessions/{session_id}/report")

    assert select_response.status_code == 200
    assert report_response.status_code == 200
    assert report_response.json()["selectedTeam"]["teamId"] == teams[0]["team_id"]


def test_report_contract_returns_selected_session_id() -> None:
    client = TestClient(app)

    response = client.get("/api/sessions/sim_test/report")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "sim_test"
    assert body["team"]
    assert body["metrics"]["teamFitScore"] >= 0
    assert body["meetingSummary"]
    assert body["phaseSummaries"]
    assert body["reportSummary"]["generatedFrom"]
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
    from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline import (
        SimulationInputBuilder,
    )

    client = TestClient(app)
    session_id = client.post("/api/sessions", json={"prd": "# Team Ops MVP"}).json()["session_id"]
    client.get(f"/api/sessions/{session_id}/requirements")
    client.get(f"/api/sessions/{session_id}/teams")

    record = session_flow._get_or_create_session(session_id)
    team_record = session_flow._shadow_selected_team_record(record)
    packet, _ = SimulationInputBuilder().build(
        requirements=session_flow._shadow_requirements_payload(record),
        team_record=team_record,
        snapshots=session_flow._shadow_member_snapshots_payload(team_record),
        risk_summary=session_flow._shadow_team_risk_summary_payload(team_record["team_id"]),
        evidence_metadata=session_flow.SHADOW_AGENT_SAMPLES / "sample_evidence_metadata.json",
        simulation_id=session_id,
    )

    assert packet.simulation_id == session_id
    assert packet.project_context.project_id == session_id
    assert packet.selected_team.team_id == team_record["team_id"]
