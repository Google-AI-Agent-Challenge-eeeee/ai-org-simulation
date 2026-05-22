"""Integration tests for activity routes (GitHub/Slack/Jira/Calendar).

All four follow the same shape — ``Paginated[Schema]`` response with an
optional ID filter — so the tests stay parametrised where possible.
``client`` fixture comes from :mod:`backend.tests.conftest`.
"""

import pytest
from fastapi.testclient import TestClient

# (endpoint, filter_param, sample_value)
# Sample values come from the dummy CSVs in ``datasets/raw/`` and follow
# the deterministic ``XXX-0001`` / ``U00000001`` patterns the seed script uses.
DOMAIN_CASES = [
    ("/github/activities", "github_id", "gh-emp-0001"),
    ("/slack/activities", "slack_user_id", "U00000001"),
    ("/jira/activities", "jira_account_id", "jira-0001"),
    ("/calendar/activities", "google_email", "emp0001@company.example"),
]


@pytest.mark.integration
@pytest.mark.parametrize(("endpoint", "filter_param", "sample_value"), DOMAIN_CASES)
class TestActivityList:
    def test_default_page_returns_paginated_payload(
        self,
        client: TestClient,
        endpoint: str,
        filter_param: str,  # noqa: ARG002 — parametrised fixture
        sample_value: str,  # noqa: ARG002
    ) -> None:
        response = client.get(endpoint)
        assert response.status_code == 200

        body = response.json()
        assert body["limit"] == 50
        assert body["offset"] == 0
        # Each domain has 100 seeded rows.
        assert body["total"] == 100
        assert len(body["items"]) == 50

    def test_filter_returns_only_matching_rows(
        self,
        client: TestClient,
        endpoint: str,
        filter_param: str,
        sample_value: str,
    ) -> None:
        response = client.get(endpoint, params={filter_param: sample_value})
        assert response.status_code == 200

        body = response.json()
        assert body["total"] >= 1
        for row in body["items"]:
            assert row[filter_param] == sample_value

    def test_unknown_filter_value_returns_empty_page(
        self,
        client: TestClient,
        endpoint: str,
        filter_param: str,
        sample_value: str,  # noqa: ARG002
    ) -> None:
        response = client.get(endpoint, params={filter_param: "does-not-exist-xyz"})
        assert response.status_code == 200

        body = response.json()
        assert body["total"] == 0
        assert body["items"] == []
