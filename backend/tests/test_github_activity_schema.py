"""Validate the dummy GitHub activity CSV against the Pydantic schema.

Mirrors ``test_employee_schema.py``: every row must parse, IDs must be
join-compatible with the HR dataset, and CSV-specific quirks
(semicolon-separated lists, empty error strings) must be normalized.
"""

from __future__ import annotations

import csv
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.core.schemas import Employee, FetchStatus, GithubActivity
from backend.db.models import GithubActivity as GithubActivityOrm

GH_CSV_PATH = Path("datasets/raw/github/github_activity_dummy_100.csv")
HR_CSV_PATH = Path("datasets/raw/hr/employee_dummy_100.csv")
CSV_ENCODING = "utf-8-sig"


def _read_github_rows() -> list[dict[str, str]]:
    with GH_CSV_PATH.open(encoding=CSV_ENCODING) as f:
        return list(csv.DictReader(f))


def test_csv_exists() -> None:
    assert GH_CSV_PATH.exists(), f"missing fixture: {GH_CSV_PATH}"


def test_all_rows_parse_successfully() -> None:
    rows = _read_github_rows()
    assert rows, "github CSV is empty"

    parsed = [GithubActivity.model_validate(row) for row in rows]
    assert len(parsed) == len(rows)


def test_contributed_repositories_split_on_semicolon() -> None:
    rows = _read_github_rows()
    multi_repo = next(row for row in rows if ";" in row["contributed_repositories"])
    parsed = GithubActivity.model_validate(multi_repo)

    assert isinstance(parsed.contributed_repositories, list)
    assert len(parsed.contributed_repositories) >= 2
    assert all(isinstance(r, str) and r for r in parsed.contributed_repositories)


def test_empty_error_message_becomes_none() -> None:
    rows = _read_github_rows()
    success_row = next(row for row in rows if row["fetch_status"] == "success")

    parsed = GithubActivity.model_validate(success_row)
    assert parsed.fetch_status is FetchStatus.SUCCESS
    assert parsed.error_message is None


def test_github_ids_join_with_hr_dataset() -> None:
    """Every GitHub row's ``github_id`` must point to a real employee."""

    with HR_CSV_PATH.open(encoding=CSV_ENCODING) as f:
        hr_github_ids = {Employee.model_validate(row).github_id for row in csv.DictReader(f)}

    github_ids = {row["github_id"] for row in _read_github_rows()}
    orphans = github_ids - hr_github_ids
    assert not orphans, f"GitHub rows reference unknown employees: {orphans}"


def test_extra_column_rejected() -> None:
    sample = _read_github_rows()[0].copy()
    sample["unexpected_column"] = "boom"

    with pytest.raises(ValidationError):
        GithubActivity.model_validate(sample)


def test_orm_to_pydantic_conversion() -> None:
    """ORM instance must round-trip cleanly into the Pydantic schema."""

    orm = GithubActivityOrm(
        github_id="gh-test",
        measured_from=date(2026, 1, 1),
        measured_to=date(2026, 3, 31),
        commit_count_3m=12,
        pr_count_3m=4,
        merged_pr_count_3m=3,
        closed_unmerged_pr_count_3m=1,
        repository_contribution_count=2,
        contributed_repositories=["company/a", "company/b"],
        fetched_at=datetime(2026, 5, 22, 9, 0, tzinfo=UTC),
        fetch_status="success",
        error_message=None,
    )

    parsed = GithubActivity.model_validate(orm)
    assert parsed.github_id == "gh-test"
    assert parsed.contributed_repositories == ["company/a", "company/b"]
    assert parsed.fetch_status is FetchStatus.SUCCESS
    assert parsed.error_message is None
