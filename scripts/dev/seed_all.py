"""Wipe + repopulate every raw table from ``datasets/raw/*/*.csv``.

Idempotent: each run TRUNCATEs the target tables then re-inserts from CSV,
so devs always get a clean known-good dataset. Order matters because some
domains carry external IDs that must match HR (the dataset is consistent
by construction, but loading employees first keeps logs readable).

Flow per domain:
    1. read CSV (utf-8-sig — handles Excel BOM)
    2. validate every row through Pydantic (catches schema drift early)
    3. build ORM instance from Pydantic dump
    4. bulk insert in one transaction per domain

Run::

    just seed
"""

from __future__ import annotations

import csv
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.schemas import (
    CalendarActivity as CalendarActivityPydantic,
)
from backend.core.schemas import (
    Employee as EmployeePydantic,
)
from backend.core.schemas import (
    GithubActivity as GithubActivityPydantic,
)
from backend.core.schemas import (
    JiraActivity as JiraActivityPydantic,
)
from backend.core.schemas import (
    SlackActivity as SlackActivityPydantic,
)
from backend.db.models import (
    Base,
    CalendarActivity,
    Employee,
    GithubActivity,
    JiraActivity,
    SlackActivity,
)
from backend.db.session import get_session_factory

CSV_ENCODING = "utf-8-sig"
DATASETS_ROOT = Path("datasets/raw")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding=CSV_ENCODING) as f:
        return list(csv.DictReader(f))


def _build_orm(
    rows: Iterable[dict[str, str]],
    pydantic_cls: type[BaseModel],
    orm_cls: type[Any],
) -> list[Any]:
    """CSV rows → validated Pydantic models → ORM instances ready to insert."""

    instances: list[Any] = []
    for row in rows:
        validated = pydantic_cls.model_validate(row)
        # ``mode='python'`` keeps enums as StrEnum subclasses (still ``str``-compatible
        # for SQLAlchemy String columns) and dates/datetimes as native types.
        payload = validated.model_dump(mode="python")
        instances.append(orm_cls(**payload))
    return instances


def _truncate_then_load(
    session: Session,
    *,
    label: str,
    csv_path: Path,
    pydantic_cls: type[BaseModel],
    orm_cls: type[Any],
    pre_truncate: Callable[[Session], None] | None = None,
) -> int:
    """Common pattern: TRUNCATE target table(s), then insert from CSV."""

    print(f"[seed] {label}: loading {csv_path}")
    rows = _read_csv(csv_path)
    instances = _build_orm(rows, pydantic_cls, orm_cls)

    table_name = orm_cls.__tablename__
    if pre_truncate is not None:
        pre_truncate(session)
    # ``RESTART IDENTITY CASCADE`` resets auto-increment IDs and clears any
    # dependent rows in one shot — safe because we wipe the whole raw set.
    session.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))
    session.add_all(instances)
    session.commit()

    print(f"[seed] {label}: inserted {len(instances)} rows into {table_name}")
    return len(instances)


def _sort_employees_by_hierarchy(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Topological sort so every manager is inserted before their reports.

    Postgres checks FK ``employees.manager_id → employees.employee_id`` at
    each statement, not at commit, so insertion order must respect the
    hierarchy. The dummy CSV interleaves rows freely.
    """

    pending = list(rows)
    seen: set[str] = set()
    ordered: list[dict[str, str]] = []

    while pending:
        made_progress = False
        for row in list(pending):
            manager_id = (row.get("manager_id") or "").strip()
            if not manager_id or manager_id in seen:
                ordered.append(row)
                seen.add(row["employee_id"])
                pending.remove(row)
                made_progress = True
        if not made_progress:
            stuck = [r["employee_id"] for r in pending[:5]]
            raise RuntimeError(f"Cyclic or dangling manager hierarchy detected near: {stuck}")

    return ordered


def seed_employees(session: Session) -> int:
    csv_path = DATASETS_ROOT / "hr" / "employee_dummy_100.csv"
    print(f"[seed] HR: loading {csv_path}")

    rows = _sort_employees_by_hierarchy(_read_csv(csv_path))
    instances = _build_orm(rows, EmployeePydantic, Employee)

    session.execute(text("TRUNCATE TABLE employees RESTART IDENTITY CASCADE"))
    session.add_all(instances)
    session.commit()

    print(f"[seed] HR: inserted {len(instances)} rows into employees")
    return len(instances)


def seed_github(session: Session) -> int:
    return _truncate_then_load(
        session,
        label="GitHub",
        csv_path=DATASETS_ROOT / "github" / "github_activity_dummy_100.csv",
        pydantic_cls=GithubActivityPydantic,
        orm_cls=GithubActivity,
    )


def seed_slack(session: Session) -> int:
    return _truncate_then_load(
        session,
        label="Slack",
        csv_path=DATASETS_ROOT / "slack" / "slack_activity_dummy_100.csv",
        pydantic_cls=SlackActivityPydantic,
        orm_cls=SlackActivity,
    )


def seed_jira(session: Session) -> int:
    return _truncate_then_load(
        session,
        label="Jira",
        csv_path=DATASETS_ROOT / "jira" / "jira_activity_dummy_100.csv",
        pydantic_cls=JiraActivityPydantic,
        orm_cls=JiraActivity,
    )


def seed_calendar(session: Session) -> int:
    return _truncate_then_load(
        session,
        label="Calendar",
        csv_path=DATASETS_ROOT / "calendar" / "google_calendar_activity_dummy_100.csv",
        pydantic_cls=CalendarActivityPydantic,
        orm_cls=CalendarActivity,
    )


def main() -> int:
    # Touch ``Base.metadata`` so static analyzers see ``models`` is in use even if
    # tree-shaking trims unused imports. Functional purpose: failing fast if a
    # model import is broken.
    assert Base.metadata.tables  # noqa: S101 — dev script, fail-fast is fine

    factory = get_session_factory()
    with factory() as session:
        # Employees first so logs make sense — the dataset is internally consistent
        # so loading order is informational, not a hard requirement.
        total = sum(
            [
                seed_employees(session),
                seed_github(session),
                seed_slack(session),
                seed_jira(session),
                seed_calendar(session),
            ]
        )

    print(f"\n[seed] done. {total} rows across 5 tables.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
