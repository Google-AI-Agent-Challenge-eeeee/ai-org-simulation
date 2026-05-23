"""Employee feature preprocessing before requirements comparison.

This module turns local HR/GitHub/Slack/Jira/Calendar CSVs into a project-safe
feature matrix. The output is intended for compare/ranking modules, not for
direct RolePlay use.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]

DEFAULT_EMPLOYEE_DATA_DIR = Path("datasets/raw")

SOURCE_FILES = {
    "employee": Path("hr") / "employee_dummy_100.csv",
    "github_activity": Path("github") / "github_activity_dummy_100.csv",
    "slack_activity": Path("slack") / "slack_activity_dummy_100.csv",
    "jira_activity": Path("jira") / "jira_activity_dummy_100.csv",
    "calendar_activity": Path("calendar") / "google_calendar_activity_dummy_100.csv",
}

IDENTITY_COLUMNS = {
    "employee.employee_id",
    "employee.employee_name",
    "employee.job_category_code",
}

RESTRICTED_KEYWORDS = {
    "address",
    "birth",
    "birthday",
    "email",
    "gender",
    "github_id",
    "google_email",
    "phone",
    "salary",
    "slack_user_id",
    "ssn",
    "주민",
}

POSITIVE_COLUMNS = {
    "employee.tenure_years",
    "employee.performance_score",
    "employee.kpi_score",
    "employee.competency_score",
    "employee.peer_review_score",
    "employee.manager_review_score",
    "employee.engagement_score",
    "employee.training_hours_12m",
    "employee.certifications_count",
    "github_activity.commit_count_3m",
    "github_activity.pr_count_3m",
    "github_activity.merged_pr_count_3m",
    "github_activity.repository_contribution_count",
    "slack_activity.message_count",
    "slack_activity.thread_replies",
    "slack_activity.collaboration_frequency",
    "slack_activity.leadership_score",
    "slack_activity.autonomy_score",
    "jira_activity.completed_issue_count",
    "jira_activity.estimation_accuracy",
    "jira_activity.comment_count",
    "jira_activity.collaboration_touchpoints",
    "jira_activity.status_transition_count",
    "jira_activity.task_breakdown_count",
    "jira_activity.sprint_completion_rate",
    "jira_activity.autonomy_score",
    "jira_activity.ownership_score",
    "calendar_activity.focus_time_count",
    "calendar_activity.focus_time_minutes",
    "calendar_activity.no_meeting_block_count",
    "calendar_activity.organizer_event_count",
    "calendar_activity.organizer_ratio",
}

NEGATIVE_COLUMNS = {
    "employee.absence_days_12m",
    "employee.overtime_hours_12m",
    "employee.disciplinary_actions_12m",
    "employee.turnover_risk_score",
    "github_activity.closed_unmerged_pr_count_3m",
    "slack_activity.avg_response_time",
    "slack_activity.night_activity_ratio",
    "slack_activity.multitasking_score",
    "slack_activity.dependency_score",
    "slack_activity.bottleneck_risk",
    "slack_activity.burnout_risk",
    "slack_activity.decision_latency",
    "jira_activity.avg_cycle_time",
    "jira_activity.overdue_issue_count",
    "jira_activity.avg_comment_response_time",
    "jira_activity.avg_time_in_status",
    "jira_activity.reopened_issue_count",
    "jira_activity.scope_change_count",
    "jira_activity.context_switching_score",
    "jira_activity.bottleneck_risk",
    "calendar_activity.total_meeting_minutes",
    "calendar_activity.early_late_meeting_ratio",
    "calendar_activity.weekend_meeting_ratio",
    "calendar_activity.fragmented_calendar_score",
    "calendar_activity.large_meeting_ratio",
    "calendar_activity.external_meeting_ratio",
    "calendar_activity.no_response_ratio",
    "calendar_activity.busy_minutes",
    "calendar_activity.event_update_count",
}

ROLE_CODE_MAP = {
    "PM": [],
    "Product Designer": ["DS"],
    "Backend Developer": ["BE"],
    "Frontend Developer": ["WEB"],
    "Mobile Engineer": ["Mobile", "Android", "iOS"],
    "DevOps Engineer": ["Infra"],
    "QA Engineer": ["QA"],
}

ROLE_PROFILE_COLUMNS = {
    "PM": [
        "slack_activity.leadership_score",
        "jira_activity.ownership_score",
        "jira_activity.task_breakdown_count",
        "slack_activity.decision_latency",
        "jira_activity.sprint_completion_rate",
    ],
    "Backend Developer": [
        "employee.competency_score",
        "github_activity.pr_count_3m",
        "jira_activity.completed_issue_count",
        "jira_activity.ownership_score",
        "jira_activity.overdue_issue_count",
    ],
    "Frontend Developer": [
        "employee.competency_score",
        "github_activity.pr_count_3m",
        "jira_activity.avg_cycle_time",
        "jira_activity.scope_change_count",
        "slack_activity.collaboration_frequency",
    ],
    "Mobile Engineer": [
        "employee.competency_score",
        "github_activity.repository_contribution_count",
        "jira_activity.completed_issue_count",
        "calendar_activity.focus_time_minutes",
    ],
    "DevOps Engineer": [
        "employee.competency_score",
        "github_activity.repository_contribution_count",
        "jira_activity.ownership_score",
        "jira_activity.bottleneck_risk",
        "calendar_activity.busy_minutes",
    ],
    "QA Engineer": [
        "employee.competency_score",
        "jira_activity.completed_issue_count",
        "jira_activity.reopened_issue_count",
        "jira_activity.overdue_issue_count",
        "slack_activity.avg_response_time",
    ],
}


def build_employee_feature_preprocessing_outputs(
    employee_data_dir: str | Path = DEFAULT_EMPLOYEE_DATA_DIR,
) -> JsonObject:
    """Build feature matrix and metadata outputs from local CSV sources."""

    dataset = load_employee_dataset(employee_data_dir)
    profiles = joined_employee_profiles(dataset)
    stats = column_stats(profiles)
    feature_keys = sorted(
        column
        for column in set(POSITIVE_COLUMNS) | set(NEGATIVE_COLUMNS)
        if not _is_restricted_column(column)
    )
    feature_metadata = _feature_metadata(feature_keys, stats, employee_data_dir)
    matrix = {
        "_meta": {
            "matrix_id": "employee_feature_matrix",
            "created_at": datetime.now(UTC).isoformat(),
            "source": "datasets/raw",
            "employee_count": len(profiles),
            "feature_key_count": len(feature_keys),
            "normalization_policy": "min_max; negative columns are inverse-normalized",
            "missing_value_policy": "missing numeric values use neutral normalized value 0.5",
            "restricted_column_policy": "restricted/system identifier columns are excluded from feature_values",
        },
        "feature_profiles": [
            _feature_profile(profile, feature_keys, stats)
            for profile in profiles
        ],
    }
    return {
        "employee_feature_matrix": matrix,
        "employee_feature_metadata": feature_metadata,
    }


def load_employee_dataset(employee_data_dir: str | Path = DEFAULT_EMPLOYEE_DATA_DIR) -> JsonObject:
    """Load local employee-related CSV sources."""

    root = Path(employee_data_dir)
    if not root.exists():
        raise FileNotFoundError(f"Employee data directory does not exist: {root}")
    result: JsonObject = {}
    for source, relative_path in SOURCE_FILES.items():
        path = root / relative_path
        if not path.exists():
            raise FileNotFoundError(f"Missing employee source CSV: {path}")
        with path.open(newline="", encoding="utf-8-sig") as f:
            result[source] = list(csv.DictReader(f))
    return result


def joined_employee_profiles(dataset: Mapping[str, list[JsonObject]]) -> list[JsonObject]:
    """Join source rows around the HR employee row."""

    github_by_id = {
        row.get("github_id"): row
        for row in dataset.get("github_activity", [])
        if row.get("github_id")
    }
    slack_by_id = {
        row.get("slack_user_id"): row
        for row in dataset.get("slack_activity", [])
        if row.get("slack_user_id")
    }
    jira_by_id = {
        row.get("jira_account_id"): row
        for row in dataset.get("jira_activity", [])
        if row.get("jira_account_id")
    }
    calendar_by_email = {
        row.get("google_email"): row
        for row in dataset.get("calendar_activity", [])
        if row.get("google_email")
    }

    profiles = []
    for employee in dataset.get("employee", []):
        profiles.append(
            {
                "employee": employee,
                "github_activity": github_by_id.get(employee.get("github_id"), {}),
                "slack_activity": slack_by_id.get(employee.get("slack_user_id"), {}),
                "jira_activity": jira_by_id.get(employee.get("jira_account_id"), {}),
                "calendar_activity": calendar_by_email.get(employee.get("google_email"), {}),
            }
        )
    return profiles


def column_stats(profiles: list[JsonObject]) -> dict[str, tuple[float, float]]:
    """Compute numeric min/max stats used for deterministic normalization."""

    values_by_column: dict[str, list[float]] = {}
    for profile in profiles:
        for source, row in profile.items():
            for column, value in row.items():
                column_key = f"{source}.{column}"
                if _is_restricted_column(column_key):
                    continue
                numeric = number(value)
                if numeric is None:
                    continue
                values_by_column.setdefault(column_key, []).append(numeric)
    return {
        key: (min(values), max(values))
        for key, values in values_by_column.items()
        if values
    }


def normalized_column_score(
    profile: Mapping[str, Mapping[str, Any]],
    column_key: str,
    stats: Mapping[str, tuple[float, float]],
) -> float:
    """Return a 0..1 normalized feature value for a source column."""

    if column_key == "employee.job_category_code":
        return 0.5
    if _is_restricted_column(column_key):
        return 0.5
    numeric = number(value_at(profile, column_key))
    if numeric is None:
        return 0.5
    low, high = stats.get(column_key, (numeric, numeric))
    normalized = 0.5 if high <= low else (numeric - low) / (high - low)
    if column_key in NEGATIVE_COLUMNS:
        return round(1 - normalized, 4)
    return round(normalized, 4)


def value_at(
    profile: Mapping[str, Mapping[str, Any]],
    column_key: str,
    *,
    default: Any = "",
) -> Any:
    if "." not in column_key:
        return default
    source, column = column_key.split(".", 1)
    return profile.get(source, {}).get(column, default)


def number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _feature_profile(
    profile: Mapping[str, Mapping[str, Any]],
    feature_keys: list[str],
    stats: Mapping[str, tuple[float, float]],
) -> JsonObject:
    feature_values = {
        column_key: _feature_value(profile, column_key, stats)
        for column_key in feature_keys
    }
    role_eligibility = {
        role: _role_eligibility_score(profile, role)
        for role in ROLE_CODE_MAP
    }
    role_profile_scores = {
        role: round(
            _average(
                normalized_column_score(profile, column, stats)
                for column in ROLE_PROFILE_COLUMNS.get(role, [])
            ),
            4,
        )
        for role in ROLE_CODE_MAP
    }
    derived_features = {
        "delivery_score": round(
            _average(
                normalized_column_score(profile, column, stats)
                for column in [
                    "jira_activity.sprint_completion_rate",
                    "jira_activity.completed_issue_count",
                    "jira_activity.estimation_accuracy",
                    "jira_activity.reopened_issue_count",
                    "employee.performance_score",
                ]
            ),
            4,
        ),
        "availability_score": round(
            _average(
                normalized_column_score(profile, column, stats)
                for column in [
                    "calendar_activity.busy_minutes",
                    "employee.overtime_hours_12m",
                    "slack_activity.burnout_risk",
                    "jira_activity.bottleneck_risk",
                    "calendar_activity.focus_time_minutes",
                ]
            ),
            4,
        ),
        "communication_score": round(
            _average(
                normalized_column_score(profile, column, stats)
                for column in [
                    "slack_activity.avg_response_time",
                    "slack_activity.decision_latency",
                    "slack_activity.collaboration_frequency",
                    "slack_activity.communication_balance",
                    "jira_activity.avg_comment_response_time",
                ]
            ),
            4,
        ),
    }
    return {
        "employee_id": str(value_at(profile, "employee.employee_id")),
        "employee_name": str(value_at(profile, "employee.employee_name")),
        "job_category_code": str(value_at(profile, "employee.job_category_code")),
        "feature_values": feature_values,
        "derived_features": derived_features,
        "role_eligibility": role_eligibility,
        "role_profile_scores": role_profile_scores,
        "signals": {
            "capacity_signal": _capacity_signal(derived_features["availability_score"]),
            "communication_signal": _communication_signal(derived_features["communication_score"]),
            "delivery_signal": _delivery_signal(derived_features["delivery_score"]),
            "collaboration_signal": _collaboration_signal(profile),
        },
        "evidence_refs": _unique_strings(feature_keys[:12]),
    }


def _feature_value(
    profile: Mapping[str, Mapping[str, Any]],
    column_key: str,
    stats: Mapping[str, tuple[float, float]],
) -> JsonObject:
    raw = value_at(profile, column_key, default="")
    low, high = stats.get(column_key, (None, None))
    return {
        "normalized_value": normalized_column_score(profile, column_key, stats),
        "raw_value": raw if raw != "" else None,
        "source_column": column_key,
        "feature_type": "numeric",
        "direction": "negative" if column_key in NEGATIVE_COLUMNS else "positive",
        "normalization": "min_max_inverse" if column_key in NEGATIVE_COLUMNS else "min_max",
        "missing": number(raw) is None,
        "source_min": low,
        "source_max": high,
    }


def _feature_metadata(
    feature_keys: list[str],
    stats: Mapping[str, tuple[float, float]],
    employee_data_dir: str | Path,
) -> JsonObject:
    return {
        "_meta": {
            "metadata_id": "employee_feature_metadata",
            "created_at": datetime.now(UTC).isoformat(),
            "employee_data_dir": str(Path(employee_data_dir)),
            "feature_key_count": len(feature_keys),
        },
        "source_files": {
            source: str(relative_path)
            for source, relative_path in SOURCE_FILES.items()
        },
        "excluded_columns": sorted(
            column for column in set(POSITIVE_COLUMNS) | set(NEGATIVE_COLUMNS)
            if _is_restricted_column(column)
        ),
        "features": {
            column_key: {
                "source_column": column_key,
                "feature_type": "numeric",
                "normalization": (
                    "min_max_inverse" if column_key in NEGATIVE_COLUMNS else "min_max"
                ),
                "direction": "negative" if column_key in NEGATIVE_COLUMNS else "positive",
                "missing_value_policy": "neutral_0.5",
                "source_min": stats.get(column_key, (None, None))[0],
                "source_max": stats.get(column_key, (None, None))[1],
            }
            for column_key in feature_keys
        },
        "derived_features": {
            "delivery_score": {"source": "jira + employee performance normalized features"},
            "availability_score": {"source": "calendar + overtime + bottleneck normalized features"},
            "communication_score": {"source": "slack + jira response normalized features"},
            "role_eligibility": {"source": "job_category_code and PM proxy signals"},
            "role_profile_scores": {"source": "role-specific normalized feature groups"},
        },
    }


def _role_eligibility_score(profile: Mapping[str, Mapping[str, Any]], role: str) -> float:
    job_code = str(value_at(profile, "employee.job_category_code"))
    target_codes = ROLE_CODE_MAP.get(role, [])
    if target_codes:
        return 1.0 if job_code in target_codes else 0.15
    leadership = number(value_at(profile, "slack_activity.leadership_score")) or 50
    ownership = number(value_at(profile, "jira_activity.ownership_score")) or 50
    performance = number(value_at(profile, "employee.performance_score")) or 50
    return round(_clamp01((leadership + ownership + performance) / 300), 4)


def _capacity_signal(availability_score: float) -> str:
    risk_score = 1 - availability_score
    if risk_score >= 0.66:
        return "high_risk"
    if risk_score >= 0.4:
        return "medium_risk"
    return "low_risk"


def _communication_signal(communication_score: float) -> str:
    if communication_score >= 0.66:
        return "low_delay"
    if communication_score >= 0.4:
        return "medium_delay"
    return "high_delay"


def _delivery_signal(delivery_score: float) -> str:
    if delivery_score >= 0.66:
        return "stable"
    if delivery_score >= 0.4:
        return "variable"
    return "unstable"


def _collaboration_signal(profile: Mapping[str, Mapping[str, Any]]) -> str:
    value = str(value_at(profile, "slack_activity.collaboration_style", default="focused_individual"))
    allowed = {
        "async_deep_worker",
        "connector",
        "focused_individual",
        "rapid_responder",
        "review_hub",
    }
    return value if value in allowed else "focused_individual"


def _is_restricted_column(column_key: str) -> bool:
    normalized = column_key.casefold()
    return (
        column_key not in IDENTITY_COLUMNS
        and any(keyword in normalized for keyword in RESTRICTED_KEYWORDS)
    )


def _average(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _unique_strings(values: Iterable[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        item = str(value or "").strip()
        if not item:
            continue
        marker = item.casefold()
        if marker in seen:
            continue
        seen.add(marker)
        result.append(item)
    return result
