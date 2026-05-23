"""Shared risk taxonomy bridge for Requirements -> Shadow RolePlay.

Requirements Agent can emit project-specific risk tags. Shadow RolePlay
operates on a smaller official issue taxonomy, so this module keeps the
normalization logic in one place for planning and evaluation.
"""

from __future__ import annotations

from collections.abc import Iterable

OFFICIAL_ISSUE_CATEGORIES = frozenset(
    {
        "role_conflict",
        "unclear_ownership",
        "schedule_risk",
        "workload_concentration",
        "technical_dependency_risk",
        "integration_risk",
        "communication_delay",
        "qa_coverage_gap",
        "release_blocker",
    }
)

TAG_TO_CATEGORY: dict[str, str] = {
    "app_store_review_delay": "release_blocker",
    "backend_workload_concentration": "workload_concentration",
    "communication_delay": "communication_delay",
    "delivery_delay": "schedule_risk",
    "delivery_risk": "schedule_risk",
    "device-specific_ui_bugs": "qa_coverage_gap",
    "devops_gcp_experience_gap": "technical_dependency_risk",
    "duplicate_notifications": "integration_risk",
    "fe_be_api_dependency": "integration_risk",
    "fe_scope_instability": "schedule_risk",
    "integration_risk": "integration_risk",
    "missing_skill": "technical_dependency_risk",
    "mobile_permission_handling_issues": "technical_dependency_risk",
    "notification_fatigue": "unclear_ownership",
    "offline_or_background_sync_issue": "integration_risk",
    "os_permission_edge_cases": "technical_dependency_risk",
    "payment_api_integration_risk": "integration_risk",
    "pm_low_sprint_velocity": "schedule_risk",
    "qa_communication_gap": "communication_delay",
    "qa_coverage_gap": "qa_coverage_gap",
    "read_state_synchronization_bugs": "integration_risk",
    "release_blocker": "release_blocker",
    "schedule_risk": "schedule_risk",
    "security_and_compliance_issues": "technical_dependency_risk",
    "security_regression": "qa_coverage_gap",
    "workload_concentration": "workload_concentration",
}

CATEGORY_PHASES: dict[str, tuple[str, ...]] = {
    "role_conflict": ("Kickoff Meeting", "Design Phase"),
    "unclear_ownership": ("Kickoff Meeting",),
    "schedule_risk": ("Kickoff Meeting", "Development Phase"),
    "workload_concentration": ("Development Phase",),
    "technical_dependency_risk": ("Design Phase", "Development Phase"),
    "integration_risk": ("Integration Phase",),
    "communication_delay": ("QA / Release Phase", "Kickoff Meeting"),
    "qa_coverage_gap": ("QA / Release Phase",),
    "release_blocker": ("QA / Release Phase",),
}

CATEGORY_DEFAULT_ROLES: dict[str, tuple[str, ...]] = {
    "role_conflict": ("PM", "Backend Developer", "Frontend Developer"),
    "unclear_ownership": ("PM", "Backend Developer"),
    "schedule_risk": ("PM", "Backend Developer"),
    "workload_concentration": ("PM", "Backend Developer"),
    "technical_dependency_risk": (
        "Backend Developer",
        "DevOps Engineer",
        "Mobile Engineer",
        "QA Engineer",
        "PM",
    ),
    "integration_risk": (
        "Backend Developer",
        "Frontend Developer",
        "Mobile Engineer",
        "PM",
    ),
    "communication_delay": ("PM", "QA Engineer", "Backend Developer"),
    "qa_coverage_gap": ("QA Engineer", "Backend Developer", "PM"),
    "release_blocker": ("PM", "QA Engineer", "DevOps Engineer"),
}


def canonical_issue_category(risk_tag: str) -> str:
    """Return the official issue category for a raw project risk tag."""

    normalized = str(risk_tag or "").strip().casefold()
    if not normalized:
        return "technical_dependency_risk"
    if normalized in OFFICIAL_ISSUE_CATEGORIES:
        return normalized
    if normalized in TAG_TO_CATEGORY:
        return TAG_TO_CATEGORY[normalized]

    token_text = normalized.replace("-", "_").replace(" ", "_")
    keyword_map: tuple[tuple[tuple[str, ...], str], ...] = (
        (("role_conflict", "conflict", "raci"), "role_conflict"),
        (("owner", "ownership", "fatigue", "scope_gap"), "unclear_ownership"),
        (("schedule", "delay", "timeline", "deadline", "delivery"), "schedule_risk"),
        (("workload", "capacity", "bottleneck", "overload"), "workload_concentration"),
        (
            ("security", "permission", "compliance", "technical", "dependency", "sdk", "external"),
            "technical_dependency_risk",
        ),
        (("integration", "sync", "duplicate", "api", "webhook", "contract"), "integration_risk"),
        (("communication", "response", "slack", "handoff"), "communication_delay"),
        (("qa", "test", "bug", "regression", "coverage", "device"), "qa_coverage_gap"),
        (("release", "store", "blocker", "launch"), "release_blocker"),
    )
    for keywords, category in keyword_map:
        if any(keyword in token_text for keyword in keywords):
            return category
    return "technical_dependency_risk"


def phases_for_category(category: str) -> tuple[str, ...]:
    """Return phase names where the category should be simulated."""

    return CATEGORY_PHASES.get(canonical_issue_category(category), ("Design Phase",))


def default_roles_for_category(
    category: str,
    available_roles: Iterable[str],
) -> list[str]:
    """Pick involved roles that exist in the current project/team."""

    available = list(dict.fromkeys(str(role) for role in available_roles if str(role).strip()))
    if not available:
        return ["PM"]

    preferred = CATEGORY_DEFAULT_ROLES.get(
        canonical_issue_category(category),
        CATEGORY_DEFAULT_ROLES["technical_dependency_risk"],
    )
    selected = [role for role in preferred if role in available]
    if selected:
        return selected[:3]
    if "PM" in available:
        return ["PM", *available[:2]][:3]
    return available[:3]
