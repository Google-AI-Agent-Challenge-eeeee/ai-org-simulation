"""Integration tests for ``/employees`` routes.

Marked ``integration`` because they hit a real Postgres seeded by ``just seed``.
Run with ``uv run pytest -m integration`` locally, or rely on CI's integration
job. Unit-only runs (``-m "not integration"``) skip these.

The ``client`` fixture and seed guard live in :mod:`backend.tests.conftest`.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestListEmployees:
    def test_default_page(self, client: TestClient) -> None:
        response = client.get("/employees")
        assert response.status_code == 200

        body = response.json()
        assert body["limit"] == 50
        assert body["offset"] == 0
        # Dummy dataset has exactly 100 rows.
        assert body["total"] == 100
        assert len(body["items"]) == 50

        # Spot-check first row shape — Pydantic ``Employee`` keys.
        first = body["items"][0]
        for required in ("employee_id", "employee_name", "department", "job_category_code"):
            assert required in first

    def test_pagination(self, client: TestClient) -> None:
        page1 = client.get("/employees", params={"limit": 10, "offset": 0}).json()
        page2 = client.get("/employees", params={"limit": 10, "offset": 10}).json()

        assert len(page1["items"]) == 10
        assert len(page2["items"]) == 10

        ids_page1 = {row["employee_id"] for row in page1["items"]}
        ids_page2 = {row["employee_id"] for row in page2["items"]}
        assert ids_page1.isdisjoint(ids_page2), "pages should not overlap"

    def test_filter_by_department(self, client: TestClient) -> None:
        response = client.get("/employees", params={"department": "디자인"})
        assert response.status_code == 200

        body = response.json()
        assert body["total"] > 0
        assert all(row["department"] == "디자인" for row in body["items"])

    def test_filter_by_job_category_code(self, client: TestClient) -> None:
        response = client.get("/employees", params={"job_category_code": "BE"})
        assert response.status_code == 200

        body = response.json()
        assert body["total"] > 0
        assert all(row["job_category_code"] == "BE" for row in body["items"])

    def test_invalid_department_returns_422(self, client: TestClient) -> None:
        response = client.get("/employees", params={"department": "not-a-real-dept"})
        assert response.status_code == 422


@pytest.mark.integration
class TestGetEmployee:
    def test_existing_employee(self, client: TestClient) -> None:
        response = client.get("/employees/E20260001")
        assert response.status_code == 200

        body = response.json()
        assert body["employee_id"] == "E20260001"

    def test_missing_employee_returns_404(self, client: TestClient) -> None:
        response = client.get("/employees/E99999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
