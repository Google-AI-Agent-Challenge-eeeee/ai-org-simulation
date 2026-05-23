"""Frontend report assembly from Shadow RolePlay outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

JsonObject = dict[str, Any]


PHASE_MAP: dict[str, str] = {
    "Kickoff Meeting": "kickoff",
    "Design Phase": "design",
    "Development Phase": "development",
    "Integration Phase": "integration",
    "QA / Release Phase": "qa_release",
}

ROLE_MAP: dict[str, str] = {
    "PM": "PM",
    "Backend Developer": "BE",
    "Frontend Developer": "WEB",
    "DevOps Engineer": "Infra",
    "QA Engineer": "QA",
    "iOS Developer": "iOS",
    "Android Developer": "Android",
    "Data Scientist": "DS",
}

ROLE_COLORS: dict[str, str] = {
    "PM": "bg-purple-500",
    "BE": "bg-blue-600",
    "WEB": "bg-cyan-500",
    "iOS": "bg-slate-500",
    "Android": "bg-green-600",
    "Infra": "bg-orange-500",
    "QA": "bg-amber-600",
    "DS": "bg-pink-500",
}

TECHNICAL_RISK_CATEGORIES = {
    "technical_dependency_risk",
    "integration_risk",
    "qa_coverage_gap",
    "release_blocker",
}
RESOURCE_RISK_CATEGORIES = {
    "workload_concentration",
    "role_conflict",
    "unclear_ownership",
    "communication_delay",
}
TIMELINE_RISK_CATEGORIES = {"schedule_risk"}


@dataclass(frozen=True)
class ReportAgentInputs:
    session_id: str
    created_at: str
    selected_team: JsonObject | None
    pm_persona: JsonObject | None
    requirements_summary: JsonObject | None
    roleplay_outputs: JsonObject


class ReportAgent:
    """Build the web/PDF report contract from every roleplay output artifact."""

    def build(
        self,
        *,
        session_id: str,
        created_at: str,
        selected_team: JsonObject | None,
        pm_persona: JsonObject | None,
        requirements_summary: JsonObject | None,
        roleplay_outputs: JsonObject,
    ) -> JsonObject:
        inputs = ReportAgentInputs(
            session_id=session_id,
            created_at=created_at,
            selected_team=selected_team,
            pm_persona=pm_persona,
            requirements_summary=requirements_summary,
            roleplay_outputs=roleplay_outputs,
        )
        simulation_output = _artifact(inputs, "simulation_output")
        team_log = _artifact(inputs, "team_simulation_log")
        issue_summary = _artifact(inputs, "issue_risk_summary")
        score_breakdown = _artifact(inputs, "score_breakdown")

        overall = _as_float(
            simulation_output.get("overall_project_fit"),
            _as_float(score_breakdown.get("overall_project_fit"), 0.84),
        )
        verdict = str(
            simulation_output.get("simulation_verdict")
            or score_breakdown.get("verdict")
            or "proceed_with_conditions"
        )
        project_name = str(
            simulation_output.get("project_name")
            or team_log.get("project_name")
            or (requirements_summary or {}).get("project_name")
            or "Untitled project"
        )
        phase_details = _phase_details(team_log, simulation_output)
        top_risks = _top_risks(simulation_output, issue_summary)
        must_fix = _must_fix(simulation_output)
        score_details = _score_details(simulation_output, score_breakdown)
        evidence_summary = dict(simulation_output.get("evidence_summary") or {})

        return {
            "id": session_id,
            "createdAt": created_at,
            "team": _team_personas(selected_team),
            "pmPersona": pm_persona or None,
            **_selected_team_summary(selected_team),
            "metrics": _metrics(overall, verdict, top_risks, evidence_summary),
            "requirementsSummary": _requirements_summary(requirements_summary, created_at),
            "meetingSummary": _meeting_summary(team_log, top_risks, must_fix, simulation_output),
            "phaseSummaries": _phase_summaries(phase_details),
            "recommendations": _recommendations(must_fix, top_risks),
            "reportSummary": {
                "projectName": project_name,
                "verdict": verdict,
                "scoreNote": str(simulation_output.get("score_note") or ""),
                "generatedFrom": [
                    name
                    for name in (
                        "Simulation_OUTPUT",
                        "Team_Simulation_Log",
                        "Issue_Risk_Summary",
                        "Score_Breakdown",
                    )
                    if roleplay_outputs.get(_artifact_key(name))
                ],
                "outputCoverage": {
                    "phaseCount": len(phase_details),
                    "topRiskCount": len(top_risks),
                    "mustFixCount": len(must_fix),
                    "scoreDimensionCount": len(score_details),
                },
            },
            "scoreBreakdown": score_details,
            "topRisks": top_risks,
            "mustFixBeforeStart": must_fix,
            "evidenceSummary": evidence_summary,
            "phaseDetails": phase_details,
            "issueSummary": _issue_summary(issue_summary),
        }


def _artifact(inputs: ReportAgentInputs, key: str) -> JsonObject:
    value = inputs.roleplay_outputs.get(key)
    return value if isinstance(value, dict) else {}


def _artifact_key(label: str) -> str:
    return {
        "Simulation_OUTPUT": "simulation_output",
        "Team_Simulation_Log": "team_simulation_log",
        "Issue_Risk_Summary": "issue_risk_summary",
        "Score_Breakdown": "score_breakdown",
    }[label]


def _metrics(
    overall: float,
    verdict: str,
    top_risks: list[JsonObject],
    evidence_summary: JsonObject,
) -> JsonObject:
    fit_score = round(overall * 100, 1)
    risk_index = round((1 - overall) * 100, 1)
    if risk_index >= 45:
        risk_level = "High"
    elif risk_index >= 25:
        risk_level = "Mid"
    else:
        risk_level = "Low"

    confidence_level = "High"
    if _as_int(evidence_summary.get("total_unresolved_turns"), 0) > 2:
        confidence_level = "Mid"
    if _as_int(evidence_summary.get("total_evidence_refs"), 0) == 0 and top_risks:
        confidence_level = "Low"

    return {
        "teamFitScore": fit_score,
        "riskIndex": risk_index,
        "riskLevel": risk_level,
        "completionRate": fit_score,
        "completionLabel": verdict.replace("_", " "),
        "riskDistribution": _risk_distribution(top_risks),
        "confidenceLevel": confidence_level,
    }


def _risk_distribution(top_risks: list[JsonObject]) -> JsonObject:
    buckets = {"technical": 0.0, "resource": 0.0, "timeline": 0.0}
    for risk in top_risks:
        category = str(risk.get("issueCategory") or risk.get("issue_category") or "")
        weight = 2.0 if risk.get("severity") == "high" else 1.0
        if category in TECHNICAL_RISK_CATEGORIES:
            buckets["technical"] += weight
        elif category in RESOURCE_RISK_CATEGORIES:
            buckets["resource"] += weight
        elif category in TIMELINE_RISK_CATEGORIES:
            buckets["timeline"] += weight
    if sum(buckets.values()) <= 0:
        return {"technical": 34, "resource": 33, "timeline": 33}
    total = sum(buckets.values())
    return {key: round(value / total * 100) for key, value in buckets.items()}


def _team_personas(selected_team: JsonObject | None) -> list[JsonObject]:
    members = selected_team.get("members", []) if selected_team else []
    if not isinstance(members, list) or not members:
        return []
    return [
        {
            "id": str(member.get("employee_id") or member.get("employee_name") or index),
            "name": str(member.get("employee_name") or member.get("employee_id") or "Team Member"),
            "role": _ui_role(str(member.get("assigned_role") or "Team Member")),
            "color": ROLE_COLORS.get(
                _ui_role(str(member.get("assigned_role") or "Team Member")), "bg-zinc-500"
            ),
            "initials": str(member.get("initials") or _initials(str(member.get("employee_name")))),
        }
        for index, member in enumerate(members)
        if isinstance(member, dict)
    ]


def _selected_team_summary(team: JsonObject | None) -> JsonObject:
    if not team:
        return {}
    return {
        "selectedTeam": {
            "rank": team.get("team_rank", 1),
            "teamFitScore": team.get("team_fit_score", 0),
            "teamId": team.get("team_id", ""),
            "teamName": team.get("team_name", ""),
        }
    }


def _requirements_summary(summary: JsonObject | None, created_at: str) -> JsonObject | None:
    if not summary:
        return None
    roles = ", ".join(str(role) for role in summary.get("required_roles", [])[:5])
    skills = ", ".join(str(skill) for skill in summary.get("required_skills", [])[:6])
    risks = [str(risk) for risk in summary.get("risk_flags", [])[:3]]
    bullets = [
        str(summary.get("project_summary") or "Requirement extraction completed."),
        f"Required roles: {roles}" if roles else "",
        f"Required skills: {skills}" if skills else "",
        *risks,
    ]
    return {"acceptedAt": created_at, "bullets": [item for item in bullets if item]}


def _meeting_summary(
    team_log: JsonObject,
    top_risks: list[JsonObject],
    must_fix: list[JsonObject],
    simulation_output: JsonObject,
) -> JsonObject:
    phase_logs = _list(team_log.get("phase_logs"))
    decisions = [
        str(decision.get("summary"))
        for phase in phase_logs
        for decision in _list(phase.get("decisions"))
        if isinstance(decision, dict) and decision.get("summary")
    ]
    issues = [
        f"{risk.get('issueCategory')} ({risk.get('severity')}/{risk.get('status')})"
        for risk in top_risks
    ]
    discussions = [
        str(phase.get("conversation_summary"))
        for phase in phase_logs
        if isinstance(phase, dict) and phase.get("conversation_summary")
    ]
    if not decisions:
        decisions = [str(item.get("suggestedAction") or item.get("suggested_action")) for item in must_fix]
    if not discussions and simulation_output.get("score_note"):
        discussions = [str(simulation_output["score_note"])]
    return {
        "decisions": decisions[:6] or ["No explicit phase decisions were produced."],
        "issues": issues[:6] or ["No top risk was produced."],
        "discussions": discussions[:6] or ["No phase discussion summary was produced."],
    }


def _phase_details(team_log: JsonObject, simulation_output: JsonObject) -> list[JsonObject]:
    stability = simulation_output.get("phase_stability_summary")
    stability_by_phase = stability if isinstance(stability, dict) else {}
    details = []
    for phase in _list(team_log.get("phase_logs")):
        if not isinstance(phase, dict):
            continue
        phase_name = str(phase.get("phase_name") or "Phase")
        phase_scores = phase.get("phase_scores") if isinstance(phase.get("phase_scores"), dict) else {}
        score = _as_float(
            stability_by_phase.get(phase_name),
            _as_float(phase_scores.get("phase_stability_score"), 0.0),
        )
        details.append(
            {
                "phase": PHASE_MAP.get(phase_name, "kickoff"),
                "phaseName": phase_name,
                "phaseObjective": str(phase.get("phase_objective") or ""),
                "conversationSummary": str(phase.get("conversation_summary") or ""),
                "score": round(score * 100),
                "triggerSources": [str(item) for item in _list(phase.get("trigger_sources"))],
                "participantTurns": _participant_turns(phase),
                "detectedIssues": _detected_issues(phase),
                "decisions": _compact_items(phase.get("decisions"), "summary"),
                "actionItems": _action_items(phase),
                "unresolvedQuestions": _compact_items(phase.get("unresolved_questions"), "description"),
            }
        )
    if details:
        return details
    return _phase_details_from_stability(stability_by_phase)


def _phase_details_from_stability(stability_by_phase: JsonObject) -> list[JsonObject]:
    return [
        {
            "phase": PHASE_MAP.get(str(name), "kickoff"),
            "phaseName": str(name),
            "phaseObjective": "",
            "conversationSummary": "Phase stability score is available, but phase log was not found.",
            "score": round(_as_float(score, 0.0) * 100),
            "triggerSources": [],
            "participantTurns": [],
            "detectedIssues": [],
            "decisions": [],
            "actionItems": [],
            "unresolvedQuestions": [],
        }
        for name, score in stability_by_phase.items()
    ]


def _phase_summaries(phase_details: list[JsonObject]) -> list[JsonObject]:
    return [
        {
            "phase": detail.get("phase", "kickoff"),
            "score": detail.get("score", 0),
            "summary": detail.get("conversationSummary") or detail.get("phaseObjective") or "",
        }
        for detail in phase_details
    ]


def _participant_turns(phase: JsonObject) -> list[JsonObject]:
    return [
        {
            "agentId": str(turn.get("agent_id") or ""),
            "role": str(turn.get("role") or ""),
            "observation": str(turn.get("observation") or ""),
            "concern": str(turn.get("concern") or ""),
            "dependency": str(turn.get("dependency") or ""),
            "proposedAction": str(turn.get("proposed_action") or ""),
            "evidenceRefsUsed": [str(item) for item in _list(turn.get("evidence_refs_used"))],
            "isValid": bool(turn.get("is_valid", True)),
        }
        for turn in _list(phase.get("participant_turns"))
        if isinstance(turn, dict)
    ]


def _detected_issues(phase: JsonObject) -> list[JsonObject]:
    return [
        {
            "issueId": str(issue.get("issue_id") or ""),
            "issueCategory": str(issue.get("issue_category") or ""),
            "description": str(issue.get("description") or ""),
            "raisedBy": str(issue.get("raised_by") or ""),
            "severity": str(issue.get("severity") or ""),
            "status": str(issue.get("status") or ""),
            "evidenceRefs": [str(item) for item in _list(issue.get("evidence_refs"))],
        }
        for issue in _list(phase.get("detected_issues"))
        if isinstance(issue, dict)
    ]


def _action_items(phase: JsonObject) -> list[JsonObject]:
    return [
        {
            "actionId": str(item.get("action_id") or ""),
            "description": str(item.get("description") or ""),
            "ownerRole": str(item.get("owner_role") or ""),
            "priority": str(item.get("priority") or ""),
            "evidenceRefs": [str(ref) for ref in _list(item.get("evidence_refs"))],
        }
        for item in _list(phase.get("action_items"))
        if isinstance(item, dict)
    ]


def _compact_items(value: Any, text_key: str) -> list[JsonObject]:
    return [
        {
            "id": str(item.get("decision_id") or item.get("question_id") or ""),
            "text": str(item.get(text_key) or ""),
            "phase": str(item.get("phase") or ""),
        }
        for item in _list(value)
        if isinstance(item, dict)
    ]


def _top_risks(simulation_output: JsonObject, issue_summary: JsonObject) -> list[JsonObject]:
    source = _list(simulation_output.get("top_risks"))
    if not source:
        source = _list(issue_summary.get("confirmed_issues")) + _list(issue_summary.get("candidate_issues"))
        source.sort(key=lambda item: _as_float(item.get("final_issue_score"), 0.0), reverse=True)
    risks = []
    for index, risk in enumerate(source, start=1):
        if not isinstance(risk, dict):
            continue
        risks.append(
            {
                "rank": _as_int(risk.get("rank"), index),
                "issueCategory": str(risk.get("issue_category") or ""),
                "severity": str(risk.get("severity") or ""),
                "status": str(risk.get("status") or ""),
                "observedInPhases": [str(item) for item in _list(risk.get("observed_in_phases"))],
                "suggestedAction": str(risk.get("suggested_action") or ""),
                "evidenceRefs": [str(item) for item in _list(risk.get("evidence_refs"))],
                "rootCause": str(risk.get("root_cause") or ""),
                "finalIssueScore": _as_float(risk.get("final_issue_score"), 0.0),
            }
        )
    return risks


def _must_fix(simulation_output: JsonObject) -> list[JsonObject]:
    return [
        {
            "issueCategory": str(item.get("issue_category") or ""),
            "severity": str(item.get("severity") or ""),
            "suggestedAction": str(item.get("suggested_action") or ""),
            "affectedRoles": [str(role) for role in _list(item.get("affected_roles"))],
        }
        for item in _list(simulation_output.get("must_fix_before_start"))
        if isinstance(item, dict)
    ]


def _score_details(simulation_output: JsonObject, score_breakdown: JsonObject) -> list[JsonObject]:
    source = _list(simulation_output.get("score_breakdown")) or _list(score_breakdown.get("dimensions"))
    return [
        {
            "dimension": str(item.get("dimension") or ""),
            "rawScore": round(_as_float(item.get("raw_score"), 0.0) * 100, 1),
            "weightedScore": round(_as_float(item.get("weighted_score"), 0.0) * 100, 1),
            "weight": round(_as_float(item.get("weight"), 0.0) * 100, 1),
            "status": str(item.get("status") or ""),
            "deductedBy": [str(ref) for ref in _list(item.get("deducted_by"))],
            "penaltyDetail": [str(detail) for detail in _list(item.get("penalty_detail"))],
            "phaseSignal": str(item.get("phase_signal") or ""),
        }
        for item in source
        if isinstance(item, dict)
    ]


def _issue_summary(issue_summary: JsonObject) -> JsonObject:
    confirmed = _normalized_issues(issue_summary.get("confirmed_issues"))
    candidate = _normalized_issues(issue_summary.get("candidate_issues"))
    invalid = _normalized_issues(issue_summary.get("invalid_issues"))
    return {
        "confirmedCount": _as_int(issue_summary.get("total_confirmed"), len(confirmed)),
        "candidateCount": _as_int(issue_summary.get("total_candidate"), len(candidate)),
        "invalidCount": _as_int(issue_summary.get("total_invalid"), len(invalid)),
        "confirmedIssues": confirmed,
        "candidateIssues": candidate,
        "invalidIssues": invalid,
    }


def _normalized_issues(value: Any) -> list[JsonObject]:
    return [
        {
            "issueId": str(item.get("issue_id") or ""),
            "issueCategory": str(item.get("issue_category") or ""),
            "preSimulationRisk": _as_float(item.get("pre_simulation_risk"), 0.0),
            "observedSimulationRisk": _as_float(item.get("observed_simulation_risk"), 0.0),
            "finalIssueScore": _as_float(item.get("final_issue_score"), 0.0),
            "severity": str(item.get("severity") or ""),
            "status": str(item.get("status") or ""),
            "rootCause": str(item.get("root_cause") or ""),
            "affectedRoles": [str(role) for role in _list(item.get("affected_roles"))],
            "suggestedAction": str(item.get("suggested_action") or ""),
            "evidenceRefs": [str(ref) for ref in _list(item.get("evidence_refs"))],
            "observedInPhases": [str(phase) for phase in _list(item.get("observed_in_phases"))],
        }
        for item in _list(value)
        if isinstance(item, dict)
    ]


def _recommendations(must_fix: list[JsonObject], top_risks: list[JsonObject]) -> list[JsonObject]:
    source = must_fix or top_risks[:4]
    return [
        {
            "type": _recommendation_type(str(item.get("issueCategory") or "")),
            "title": str(item.get("issueCategory") or "risk").replace("_", " ").title(),
            "body": str(item.get("suggestedAction") or "Review this risk before project start."),
        }
        for item in source[:4]
    ]


def _recommendation_type(category: str) -> str:
    if category == "workload_concentration":
        return "burnout"
    if category in {"technical_dependency_risk", "qa_coverage_gap", "release_blocker"}:
        return "security"
    if category == "communication_delay":
        return "turnover"
    return "bottleneck"


def _ui_role(role: str) -> str:
    return ROLE_MAP.get(role, "BE")


def _initials(name: str) -> str:
    if not name or name == "None":
        return "TM"
    parts = name.split()
    if len(parts) <= 1:
        return name[:2]
    return "".join(part[:1] for part in parts[:2])


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_float(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _as_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback
