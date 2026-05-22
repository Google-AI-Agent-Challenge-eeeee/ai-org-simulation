"""Integration tests for ``GET /employees/{id}/profile`` aggregate view.

``client`` fixture is provided by :mod:`backend.tests.conftest`.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestEmployeeProfile:
    def test_existing_employee_returns_all_sections(self, client: TestClient) -> None:
        response = client.get("/employees/E20260001/profile")
        assert response.status_code == 200

        body = response.json()
        assert set(body.keys()) == {"employee", "github", "slack", "jira", "calendar"}

        # Employee section
        assert body["employee"]["employee_id"] == "E20260001"

        # E20260001 in the dummy CSVs has every external ID populated.
        assert len(body["github"]) >= 1
        assert body["slack"] is not None
        assert body["jira"] is not None
        assert len(body["calendar"]) >= 1

        # Cross-domain consistency: external IDs in the activity rows must
        # match what the Employee section advertises.
        emp = body["employee"]
        assert all(row["github_id"] == emp["github_id"] for row in body["github"])
        assert body["slack"]["slack_user_id"] == emp["slack_user_id"]
        assert body["jira"]["jira_account_id"] == emp["jira_account_id"]
        assert all(row["google_email"] == emp["google_email"] for row in body["calendar"])

    def test_missing_employee_returns_404(self, client: TestClient) -> None:
        response = client.get("/employees/E99999999/profile")
        assert response.status_code == 404
