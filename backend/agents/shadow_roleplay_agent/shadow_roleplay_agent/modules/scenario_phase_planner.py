"""Build five Shadow RolePlay phases from project risks.

The planner accepts raw risk tags from Requirements Agent, normalizes them to
the official RolePlay issue taxonomy, and creates scenario events even when a
project-specific tag has no handwritten template.
"""

from __future__ import annotations

import logging
from pathlib import Path

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.risk_taxonomy_bridge import (
    canonical_issue_category,
    default_roles_for_category,
    phases_for_category,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.simulation_input_builder import (
    EvidenceIndex,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.phase_plan import (
    AgendaItem,
    PhaseName,
    ScenarioEvent,
    SimulationPhase,
    SimulationPhasePlan,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    RequirementsList,
    TeamRiskSummary,
)

logger = logging.getLogger(__name__)

MAX_EVENTS_PER_PHASE = 8

_PHASE_DEFINITIONS: dict[PhaseName, dict] = {
    PhaseName.KICKOFF: {
        "objective": (
            "Align project goals, R&R, owners, and schedule assumptions before execution."
        ),
        "focus_categories": {
            "pm_low_sprint_velocity",
            "backend_workload_concentration",
            "unclear_ownership",
            "role_conflict",
            "schedule_risk",
        },
        "base_agenda": [
            AgendaItem(topic="Share project goal and MVP scope", owner_role="PM"),
            AgendaItem(topic="Confirm role responsibilities and feature owners", owner_role="PM"),
            AgendaItem(topic="Review milestone and delivery assumptions", owner_role="PM"),
            AgendaItem(topic="Confirm known constraints and high-priority risks", owner_role="PM"),
        ],
    },
    PhaseName.DESIGN: {
        "objective": (
            "Validate architecture, API contracts, dependencies, and technical gaps early."
        ),
        "focus_categories": {
            "payment_api_integration_risk",
            "devops_gcp_experience_gap",
            "technical_dependency_risk",
            "missing_skill",
        },
        "base_agenda": [
            AgendaItem(topic="Confirm data model and API boundaries", owner_role="Backend Developer"),
            AgendaItem(topic="Review external APIs and sandbox readiness", owner_role="Backend Developer"),
            AgendaItem(topic="Review deployment and observability design", owner_role="DevOps Engineer"),
            AgendaItem(topic="Review UX/component assumptions", owner_role="Frontend Developer"),
        ],
    },
    PhaseName.DEVELOPMENT: {
        "objective": (
            "Track implementation ownership, workload balance, delivery pace, and blocking risks."
        ),
        "focus_categories": {
            "backend_workload_concentration",
            "pm_low_sprint_velocity",
            "fe_scope_instability",
            "workload_concentration",
            "schedule_risk",
        },
        "base_agenda": [
            AgendaItem(topic="Review P0 feature progress", owner_role="PM"),
            AgendaItem(topic="Review backend implementation status", owner_role="Backend Developer"),
            AgendaItem(topic="Review frontend implementation status", owner_role="Frontend Developer"),
            AgendaItem(topic="Review CI/CD readiness", owner_role="DevOps Engineer"),
            AgendaItem(topic="Review PR, issue, and workload bottlenecks", owner_role="PM"),
        ],
    },
    PhaseName.INTEGRATION: {
        "objective": (
            "Expose cross-system API, data, client, and environment mismatches before release."
        ),
        "focus_categories": {
            "fe_be_api_dependency",
            "payment_api_integration_risk",
            "fe_scope_instability",
            "devops_gcp_experience_gap",
            "integration_risk",
        },
        "base_agenda": [
            AgendaItem(topic="Confirm API completion and client integration entry criteria", owner_role="Backend Developer"),
            AgendaItem(topic="Review integration issue list and owners", owner_role="Frontend Developer"),
            AgendaItem(topic="Confirm staging deployment readiness", owner_role="DevOps Engineer"),
            AgendaItem(topic="Resolve unresolved integration owners", owner_role="PM"),
        ],
    },
    PhaseName.QA_RELEASE: {
        "objective": (
            "Validate QA coverage, release blockers, unresolved risks, and launch readiness."
        ),
        "focus_categories": {
            "qa_communication_gap",
            "qa_coverage_gap",
            "release_blocker",
            "communication_delay",
        },
        "base_agenda": [
            AgendaItem(topic="Review test coverage and high-risk cases", owner_role="QA Engineer"),
            AgendaItem(topic="Review high-severity defects and owners", owner_role="PM"),
            AgendaItem(topic="Confirm release checklist and rollback readiness", owner_role="DevOps Engineer"),
            AgendaItem(topic="Confirm final go/no-go conditions", owner_role="PM"),
        ],
    },
}

_RISK_EVENT_TEMPLATES: dict[str, dict] = {
    "pm_low_sprint_velocity": {
        "description": (
            "PM delivery history suggests schedule coordination may be slow. The team must "
            "confirm whether milestones and owner follow-up are realistic."
        ),
        "involved_roles": ["PM", "Backend Developer"],
        "expected_issue_category": "schedule_risk",
    },
    "backend_workload_concentration": {
        "description": (
            "Backend-critical work appears concentrated on one role. The team must decide "
            "whether ownership or scope needs rebalancing before development starts."
        ),
        "involved_roles": ["Backend Developer", "PM"],
        "expected_issue_category": "workload_concentration",
    },
    "payment_api_integration_risk": {
        "description": (
            "External API integration risk can block frontend/backend work if contract or "
            "sandbox readiness is unclear."
        ),
        "involved_roles": ["Backend Developer", "Frontend Developer", "PM"],
        "expected_issue_category": "technical_dependency_risk",
    },
    "fe_scope_instability": {
        "description": (
            "Frontend scope appears unstable. The team must check whether repeated changes "
            "could affect delivery and integration timing."
        ),
        "involved_roles": ["Frontend Developer", "PM"],
        "expected_issue_category": "schedule_risk",
    },
    "fe_be_api_dependency": {
        "description": (
            "Frontend depends on backend API readiness. The team must surface integration "
            "entry criteria and fallback plans."
        ),
        "involved_roles": ["Frontend Developer", "Backend Developer"],
        "expected_issue_category": "integration_risk",
    },
    "devops_gcp_experience_gap": {
        "description": (
            "Infrastructure experience gap can delay environment setup and release. The team "
            "must confirm deployment ownership and early spike needs."
        ),
        "involved_roles": ["DevOps Engineer", "PM"],
        "expected_issue_category": "technical_dependency_risk",
    },
    "qa_communication_gap": {
        "description": (
            "QA communication risk can delay defect triage. The team must confirm response "
            "expectations and review cadence."
        ),
        "involved_roles": ["QA Engineer", "PM"],
        "expected_issue_category": "communication_delay",
    },
    "qa_coverage_gap": {
        "description": (
            "QA coverage gap can hide release-blocking defects. The team must confirm high-risk "
            "test scenarios and ownership."
        ),
        "involved_roles": ["QA Engineer", "Backend Developer"],
        "expected_issue_category": "qa_coverage_gap",
    },
}

_PHASE_DAY_RANGES: dict[PhaseName, tuple[int, int]] = {
    PhaseName.KICKOFF: (1, 2),
    PhaseName.DESIGN: (2, 4),
    PhaseName.DEVELOPMENT: (4, 10),
    PhaseName.INTEGRATION: (10, 13),
    PhaseName.QA_RELEASE: (13, 14),
}



class ScenarioPhasePlanner:
    """Create a five-phase simulation plan."""

    def plan(
        self,
        requirements: RequirementsList,
        risk_summary: TeamRiskSummary,
        evidence_index: EvidenceIndex,
        simulation_id: str,
    ) -> SimulationPhasePlan:
        phases: list[SimulationPhase] = []
        event_counter = 1

        for phase_name in PhaseName:
            defn = _PHASE_DEFINITIONS[phase_name]
            focus_categories: set[str] = defn["focus_categories"]
            active_risks = _active_risk_pairs(
                risk_summary.risk_tags,
                phase_name=phase_name,
                focus_categories=focus_categories,
            )
            if not active_risks:
                active_risks = [_baseline_risk_pair(phase_name)]
            agenda = list(defn["base_agenda"]) + _feature_agenda(requirements, phase_name)
            events: list[ScenarioEvent] = []

            for risk_tag, category in active_risks[:MAX_EVENTS_PER_PHASE]:
                events.append(
                    _scenario_event_for_risk(
                        event_id=f"evt_{event_counter:03d}",
                        risk_tag=risk_tag,
                        category=category,
                        requirements=requirements,
                        evidence_index=evidence_index,
                    )
                )
                event_counter += 1

            phases.append(
                SimulationPhase(
                    phase_name=phase_name,
                    phase_objective=defn["objective"],
                    agenda=agenda,
                    scenario_events=events,
                    focus_risk_tags=_unique_strings(
                        [risk_tag for risk_tag, _ in active_risks]
                        + [category for _, category in active_risks]
                    ),
                )
            )
            logger.info(
                "[Planner] %s | agenda=%d events=%d focus_risks=%s",
                phase_name.value,
                len(agenda),
                len(events),
                [risk_tag for risk_tag, _ in active_risks],
            )

        plan = SimulationPhasePlan(
            simulation_id=simulation_id,
            project_name=requirements.project_name,
            phases=phases,
        )
        logger.info("[Planner] complete | total_events=%d", event_counter - 1)
        return plan

    @staticmethod
    def to_json(plan: SimulationPhasePlan, path: Path | str) -> None:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        logger.info("[Planner] saved -> %s", out)


def _active_risk_pairs(
    risk_tags: list[str],
    *,
    phase_name: PhaseName,
    focus_categories: set[str],
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for raw_tag in risk_tags:
        risk_tag = str(raw_tag or "").strip()
        if not risk_tag:
            continue
        category = canonical_issue_category(risk_tag)
        should_include = (
            risk_tag in focus_categories
            or category in focus_categories
            or phase_name.value in phases_for_category(category)
        )
        if not should_include:
            continue
        if risk_tag == category and any(existing_category == category for _, existing_category in pairs):
            continue
        marker = f"{risk_tag.casefold()}::{category}::{phase_name.value}"
        if marker in seen:
            continue
        seen.add(marker)
        pairs.append((risk_tag, category))
    return pairs


def _baseline_risk_pair(phase_name: PhaseName) -> tuple[str, str]:
    return {
        PhaseName.KICKOFF: ("unclear_ownership", "unclear_ownership"),
        PhaseName.DESIGN: ("technical_dependency_risk", "technical_dependency_risk"),
        PhaseName.DEVELOPMENT: ("schedule_risk", "schedule_risk"),
        PhaseName.INTEGRATION: ("integration_risk", "integration_risk"),
        PhaseName.QA_RELEASE: ("qa_coverage_gap", "qa_coverage_gap"),
    }[phase_name]


def _scenario_event_for_risk(
    *,
    event_id: str,
    risk_tag: str,
    category: str,
    requirements: RequirementsList,
    evidence_index: EvidenceIndex,
) -> ScenarioEvent:
    template = _RISK_EVENT_TEMPLATES.get(risk_tag)
    available_roles = requirements.required_roles
    if template:
        involved_roles = _roles_available(template["involved_roles"], available_roles)
        if not involved_roles:
            involved_roles = default_roles_for_category(category, available_roles)
        expected_category = template["expected_issue_category"]
        description = template["description"]
    else:
        involved_roles = default_roles_for_category(category, available_roles)
        expected_category = category
        description = _fallback_event_description(risk_tag, category, requirements)

    return ScenarioEvent(
        event_id=event_id,
        description=description,
        trigger_source=_trigger_sources(risk_tag, category, evidence_index),
        involved_roles=involved_roles,
        expected_issue_category=expected_category,
    )


def _fallback_event_description(
    risk_tag: str,
    category: str,
    requirements: RequirementsList,
) -> str:
    project_name = requirements.project_name or requirements.project_id
    feature_names = ", ".join(feature.feature_name for feature in requirements.features[:3])
    feature_hint = f" Related features: {feature_names}." if feature_names else ""
    return (
        f"{project_name} has project-specific risk '{risk_tag}', normalized as "
        f"'{category}'. The team must validate ownership, evidence, dependency impact, "
        f"and mitigation before this phase can be considered stable.{feature_hint}"
    )


def _trigger_sources(
    risk_tag: str,
    category: str,
    evidence_index: EvidenceIndex,
) -> list[str]:
    sources = [risk_tag, category]
    for tag in (risk_tag, category):
        for evidence in evidence_index.for_risk(tag):
            sources.extend([evidence.evidence_id, evidence.source_column])
    return _unique_strings(sources)


def _roles_available(
    preferred_roles: list[str],
    available_roles: list[str],
) -> list[str]:
    available = set(available_roles)
    return [role for role in preferred_roles if role in available]


def _feature_agenda(req: RequirementsList, phase: PhaseName) -> list[AgendaItem]:
    start, end = _PHASE_DAY_RANGES[phase]
    items: list[AgendaItem] = []
    for feature in req.features:
        if start <= feature.estimated_days <= end:
            items.append(
                AgendaItem(
                    topic=f"[Feature] {feature.feature_name} ({feature.priority.value}) progress check",
                    owner_role=feature.assigned_role,
                    related_features=[feature.feature_id],
                )
            )
    return items


def _unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
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
