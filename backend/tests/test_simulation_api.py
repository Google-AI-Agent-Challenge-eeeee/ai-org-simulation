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


def test_team_select_returns_ok() -> None:
    client = TestClient(app)

    response = client.post("/api/sessions/sim_test/teams/select", json={"teamId": "team_001"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


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


def test_stream_endpoint_uses_sse_media_type(monkeypatch) -> None:
    def fake_stream(llm_mode: str) -> Iterator[str]:
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
