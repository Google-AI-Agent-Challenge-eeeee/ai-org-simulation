"""Shared pytest fixtures for the backend test suite.

Test layering policy (Phase 3):

- **unit tests** (default): no Postgres, no FastAPI app. Run with ``just test``.
  Use in-memory SQLite (see ``test_db_models.py``) or pure Pydantic checks.

- **integration tests** (``@pytest.mark.integration``): hit the real local
  Postgres seeded by ``just seed``. Run with ``uv run pytest -m integration``
  or CI's integration job.

Why dev DB instead of a dedicated test DB or per-test transactions:

- Dataset is tiny (5 tables x 100 rows) and read-only from the API surface,
  so cross-test pollution risk is near zero.
- One ``just seed`` makes both dev and tests work the same way — no extra
  step to remember.
- CI overrides ``DATABASE_URL`` to point at a throwaway service container,
  same fixtures, same code path. (Phase 3 CI workflow.)

If we ever need true isolation (mutating endpoints, parallel test runs),
switch ``_verify_seeded`` to a transactional fixture that rolls back after
each test. Keep that for when there's actual pain.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.db.session import get_session_factory
from backend.main import app

# Minimum row counts the integration tests assume. Seed script writes exactly
# 100 rows per table — anything less means the seed hasn't been run yet.
_MIN_SEED_ROWS = {
    "employees": 100,
    "github_activities": 100,
    "slack_activities": 100,
    "jira_activities": 100,
    "calendar_activities": 100,
}


@pytest.fixture(scope="session")
def _verify_seeded() -> None:
    """Guard: integration tests must see ``just seed`` data.

    Runs once per session, before any integration test setup. If the DB is
    unreachable or under-seeded, fail with a clear remediation hint instead
    of cryptic 500s downstream.
    """

    try:
        factory = get_session_factory()
        with factory() as session:
            for table, min_count in _MIN_SEED_ROWS.items():
                actual = session.execute(
                    text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608 — table names are literal constants
                ).scalar_one()
                if actual < min_count:
                    pytest.fail(
                        f"Integration tests need seeded data: ``{table}`` has "
                        f"{actual} rows, expected >= {min_count}. "
                        f"Run ``just seed`` first."
                    )
    except Exception as exc:  # noqa: BLE001 — re-raise as pytest.fail for clarity
        pytest.fail(
            "Cannot reach the integration DB. Make sure ``just db-up`` is "
            f"running and ``just seed`` was executed. Original error: {exc}"
        )


@pytest.fixture(scope="module")
def client(_verify_seeded: None) -> Iterator[TestClient]:  # noqa: ARG001
    """FastAPI test client backed by the seeded Postgres.

    Module-scoped so we share a single ASGI lifespan across all tests in one
    file — meaningful for `lifespan` hooks but cheap either way.
    """

    with TestClient(app) as test_client:
        yield test_client
