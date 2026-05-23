"""Session-level orchestration facade for the frontend-facing simulation flow.

This module keeps the current sample/stub behavior, but moves it out of the
HTTP router so future DB-backed matching and agent adapters can replace the
internals without changing the API contract.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.agents.report_agent import ReportAgent
from backend.agents.requirements_agent.pipeline.llm_adapter import (
    LLM_MODE_STUB,
    LLMConfig,
    build_section_extractor,
)
from backend.agents.requirements_agent.pipeline.local_input_loader import (
    DEFAULT_EMPLOYEE_DATA_DIR,
    build_local_project_fields,
    read_employee_data_headers,
    validate_employee_column_rules_against_headers,
)
from backend.agents.requirements_agent.pipeline.requirements_pipeline import (
    DEFAULT_REFERENCE_DIR,
    RequirementsPipelineConfig,
    load_references,
    run_requirements_pipeline,
)
from backend.core.config import get_settings
from backend.services.team_ranking import (
    RequirementsAgentTeamRankingAdapter,
    TeamRankingAdapterResult,
)

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

PHASE_MAP: dict[str, str] = {
    "Kickoff Meeting": "kickoff",
    "Design Phase": "design",
    "Development Phase": "development",
    "Integration Phase": "integration",
    "QA / Release Phase": "qa_release",
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

REPO_ROOT = Path(__file__).resolve().parents[2]
SHADOW_AGENT_ROOT = REPO_ROOT / "backend/agents/shadow_roleplay_agent/shadow_roleplay_agent"
SHADOW_AGENT_SAMPLES = SHADOW_AGENT_ROOT / "samples"

DEFAULT_PRD_TEXT = """# 결제 및 사용자 관리 플랫폼 v1.0

Goal: 이메일 기반 인증, 결제 API 연동, 메인 대시보드를 포함하는 14일 스프린트 MVP.

## Functional Requirements
- 이메일 로그인
- 결제 API 연동
- 메인 대시보드 UI

## Constraints
- Duration: 2 weeks
- Deploy on GCP Cloud Run
- Frontend/backend API contract must stay synchronized.
"""


@dataclass
class SessionRecord:
    session_id: str
    prd_text: str
    created_at: str = field(default_factory=lambda: _utc_now_iso())
    pm_persona: dict[str, Any] | None = None
    pm_priority: str | None = None
    requirements_agent_result: dict[str, Any] | None = None
    requirements_summary: dict[str, Any] | None = None
    team_ranking_result: TeamRankingAdapterResult | None = None
    team_candidates: list[dict[str, Any]] | None = None
    team_candidates_total: int | None = None
    requirements_accepted: bool = False
    selected_team_id: str | None = None
    roleplay_outputs: dict[str, Any] | None = None
    report_generation_error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ReportNotReadyError(RuntimeError):
    def __init__(self, session_id: str, *, generation_error: str | None = None) -> None:
        self.session_id = session_id
        self.generation_error = generation_error
        super().__init__("Report is not ready. Run the simulation stream first.")


_SESSIONS: dict[str, SessionRecord] = {}


def create_session(body: dict[str, Any] | None = None) -> dict[str, str]:
    payload = body or {}
    session_id = f"sim_{uuid.uuid4().hex[:8]}"
    _SESSIONS[session_id] = SessionRecord(
        session_id=session_id,
        prd_text=_extract_prd_text(payload),
        pm_persona=_dict_or_none(payload.get("pmPersona")),
        pm_priority=_string_or_none(payload.get("pmPriority")),
    )
    return {"session_id": session_id}


def get_requirements_summary(session_id: str) -> dict[str, Any]:
    record = _get_or_create_session(session_id)
    if record.requirements_summary is None:
        agent_result = _ensure_requirements_agent_result(record)
        record.requirements_summary = _to_requirements_summary(
            agent_result["outputs"]["requirements_list"]
        )
    return record.requirements_summary


def accept_requirements(session_id: str) -> dict[str, bool]:
    _get_or_create_session(session_id).requirements_accepted = True
    return {"ok": True}


def revise_requirements(session_id: str) -> dict[str, Any]:
    record = _get_or_create_session(session_id)
    record.requirements_agent_result = None
    record.requirements_summary = None
    record.team_ranking_result = None
    record.team_candidates = None
    record.team_candidates_total = None
    record.selected_team_id = None
    record.roleplay_outputs = None
    record.report_generation_error = None
    record.requirements_accepted = False
    return get_requirements_summary(session_id)


def get_team_candidates(session_id: str) -> dict[str, Any]:
    record = _get_or_create_session(session_id)
    if record.team_candidates is None:
        ranking_result = _load_requirements_agent_team_candidates(record)
        if ranking_result is None:
            record.team_candidates = _teams_with_pm_persona(
                record,
                _load_sample_team_candidates(),
            )
            record.team_candidates_total = 1247
        else:
            record.team_candidates = _teams_with_pm_persona(record, ranking_result["teams"])
            record.team_candidates_total = ranking_result["total_combinations"]
    return {"totalCombinations": record.team_candidates_total or 0, "teams": record.team_candidates}


def select_team(session_id: str, team_id: str | None = None) -> dict[str, bool]:
    record = _get_or_create_session(session_id)
    teams = get_team_candidates(session_id)["teams"]
    selected_id = team_id or (teams[0]["team_id"] if teams else None)
    if selected_id and any(team["team_id"] == selected_id for team in teams):
        record.selected_team_id = selected_id
    return {"ok": True}


def get_report(session_id: str) -> dict[str, Any]:
    record = _get_or_create_session(session_id)
    roleplay_outputs = _roleplay_outputs_for_report(record)
    selected_team = _selected_team(record)
    return ReportAgent().build(
        session_id=session_id,
        created_at=record.created_at,
        selected_team=selected_team,
        pm_persona=record.pm_persona,
        requirements_summary=record.requirements_summary,
        roleplay_outputs=roleplay_outputs,
    )


def sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def iter_pipeline_sse(session_id: str, llm_mode: str) -> Iterator[str]:
    _load_env_file()
    settings = get_settings()
    record = _get_or_create_session(session_id)
    if isinstance(record.roleplay_outputs, dict):
        yield sse("backend_log", {"text": "Using cached roleplay report outputs"})
        yield sse("status", {"stage": "done", "text": "시뮬레이션 완료"})
        yield sse("done", {})
        return

    from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules import (
        AgentCardBuilder,
        IssueRiskEvaluator,
        OutputBuilder,
        PhaseLogCollector,
        PrivacyColumnFilter,
        ScenarioPhasePlanner,
        ScoreCalculator,
    )
    from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline import (
        SimulationOrchestrator,
    )
    from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.simulation_input_builder import (
        EvidenceIndex,
    )

    yield sse("status", {"stage": "analyzing", "text": "시뮬레이션 입력 데이터 구성 중"})
    yield sse("backend_log", {"text": "Simulation_Input_Packet 병합 중"})

    packet = _roleplay_packet(record)
    evidence_index = EvidenceIndex.build(packet.evidence_metadata)
    requirements_full = packet.project_context
    risk_summary = packet.team_risk_summary

    yield sse("backend_log", {"text": "PrivacyColumnFilter · PII 컬럼 제거 완료"})
    result = PrivacyColumnFilter().filter(packet)

    yield sse(
        "backend_log",
        {"text": f"AgentCardBuilder · {len(result.sanitized_snapshots)}명 Agent Card 생성"},
    )
    cards = AgentCardBuilder().build(result.sanitized_snapshots, requirements_full)

    plan = ScenarioPhasePlanner().plan(
        requirements_full,
        risk_summary,
        evidence_index,
        simulation_id=session_id,
    )
    total_events = sum(len(p.scenario_events) for p in plan.phases)
    yield sse(
        "backend_log",
        {"text": f"ScenarioPhasePlanner · 리스크 기반 시나리오 {total_events}개 배치"},
    )

    yield sse(
        "status",
        {"stage": "meeting", "text": "시뮬레이션 진행 중", "phase": "kickoff", "phaseIndex": 0},
    )

    yield sse(
        "backend_log",
        {
            "text": (
                f"Shadow RolePlay Agent LLM mode: {llm_mode} "
                f"(strict={settings.roleplay_strict_llm})"
            )
        },
    )

    orchestrator = SimulationOrchestrator(
        llm_mode=llm_mode,
        strict_llm=settings.roleplay_strict_llm,
    )
    msg_counter = 0

    for chunk in orchestrator.run_stream(plan, cards):
        ctype = chunk["type"]
        if ctype == "phase_start":
            yield sse(
                "status",
                {
                    "stage": "meeting",
                    "text": f"시뮬레이션 진행 중 - {chunk['phase']}",
                    "phase": PHASE_MAP.get(chunk["phase"], "kickoff"),
                    "phaseIndex": chunk["phase_index"],
                },
            )
        elif ctype == "backend_log":
            yield sse("backend_log", {"text": chunk["text"]})
        elif ctype == "agent_turn":
            msg_counter = yield from iter_agent_turn_sse(chunk, msg_counter)
        elif ctype == "event_start":
            yield sse(
                "event_start",
                {"eventId": chunk["event_id"], "description": chunk["description"]},
            )
        elif ctype == "event_end":
            yield sse("event_end", {"eventId": chunk["event_id"]})
        elif ctype == "done":
            try:
                orchestrator_output = chunk.get("output")
                if orchestrator_output is not None:
                    yield sse(
                        "backend_log",
                        {
                            "text": (
                                "Shadow RolePlay Agent actual LLM mode: "
                                f"{orchestrator_output.actual_llm_mode} "
                                f"(vertex_turns={orchestrator_output.vertex_turn_count}, "
                                f"fallbacks={orchestrator_output.fallback_count})"
                            )
                        },
                    )
                    team = packet.selected_team
                    evidence_list = list(packet.evidence_metadata)
                    sim_log = PhaseLogCollector().collect(
                        orchestrator_output,
                        plan,
                        requirements_full,
                        team,
                    )
                    issue_summary = IssueRiskEvaluator().evaluate(
                        sim_log,
                        risk_summary,
                        evidence_list,
                    )
                    score_breakdown = ScoreCalculator().calculate(issue_summary, sim_log)
                    simulation_output = OutputBuilder().build(
                        score_breakdown,
                        issue_summary,
                        sim_log,
                        requirements_full.project_name,
                    )
                    record.roleplay_outputs = {
                        "team_simulation_log": _model_dump_jsonable(sim_log),
                        "issue_risk_summary": _model_dump_jsonable(issue_summary),
                        "score_breakdown": _model_dump_jsonable(score_breakdown),
                        "simulation_output": _model_dump_jsonable(simulation_output),
                    }
                    record.report_generation_error = None
                    yield sse(
                        "backend_log",
                        {"text": "ReportAgent inputs finalized from live roleplay outputs"},
                    )
            except Exception as exc:
                record.report_generation_error = str(exc)
                yield sse(
                    "backend_log",
                    {"text": f"ReportAgent input finalize failed: {exc}"},
                )
            yield sse("status", {"stage": "done", "text": "시뮬레이션 완료"})
            yield sse("done", {})


def iter_agent_turn_sse(chunk: dict[str, Any], msg_counter: int) -> Iterator[str]:
    turn = chunk["turn"]
    persona = _persona(chunk["agent_id"], ROLE_MAP.get(chunk["role"], "BE"))

    for turn_field, turn_type in [
        ("observation", "observation"),
        ("concern", "concern"),
        ("dependency", "dependency"),
        ("proposed_action", "proposed_action"),
    ]:
        text = turn.get(turn_field, "").strip()
        if not text:
            continue
        msg_id = f"msg_{msg_counter}_{turn_field}"
        msg_counter += 1
        for i, token in enumerate(_chunk_text_for_sse(text)):
            space = "" if i == 0 else " "
            yield sse(
                "message",
                {
                    "persona": persona,
                    "token": space + token,
                    "messageId": msg_id,
                    "turnType": turn_type,
                },
            )
    return msg_counter


def _chunk_text_for_sse(text: str, words_per_chunk: int = 12) -> Iterator[str]:
    words = text.split(" ")
    for start in range(0, len(words), words_per_chunk):
        yield " ".join(words[start : start + words_per_chunk])


def _roleplay_outputs_for_report(record: SessionRecord) -> dict[str, Any]:
    if isinstance(record.roleplay_outputs, dict):
        return record.roleplay_outputs
    raise ReportNotReadyError(
        record.session_id,
        generation_error=record.report_generation_error,
    )


def _model_dump_jsonable(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    return {}


def _load_sample_team_candidates() -> list[dict[str, Any]]:
    team = _load_json(SHADOW_AGENT_SAMPLES / "sample_selected_team_record.json")
    snapshots = _load_json_list(SHADOW_AGENT_SAMPLES / "sample_employee_fit_profile_snapshots.json")
    snapshot_by_employee_id = {snapshot.get("employee_id"): snapshot for snapshot in snapshots}
    members = [
        _team_member_from_sample(member, snapshot_by_employee_id.get(member.get("employee_id"), {}))
        for member in team.get("members", [])
    ]
    skill_gaps = sorted(
        {
            skill
            for snapshot in snapshot_by_employee_id.values()
            for skill in snapshot.get("missing_skills", [])
        }
    )

    return [
        {
            "team_id": team.get("team_id", "team_001"),
            "team_name": "알파 포메이션",
            "team_rank": team.get("team_rank", 1),
            "team_fit_score": round(float(team.get("team_fit_score", 84.0)), 1),
            "role_coverage_score": team.get("role_coverage_score", 0.0),
            "skill_coverage_score": team.get("skill_coverage_score", 0.0),
            "availability_score": team.get("availability_score", 0.0),
            "team_risk_flags": team.get("team_risk_flags", []),
            "badges": ["Shadow sample", "Session selectable"],
            "rationale": "Shadow Roleplay sample team record를 프론트 팀 선택 계약으로 변환한 후보입니다.",
            "skill_gaps": skill_gaps[:6],
            "members": members,
        }
    ]


def _load_requirements_agent_team_candidates(record: SessionRecord) -> dict[str, Any] | None:
    team_ranking_result = _get_or_build_team_ranking(record)
    if not team_ranking_result.teams:
        return None
    return {
        "total_combinations": team_ranking_result.total_combinations,
        "teams": team_ranking_result.teams,
    }


def _get_or_build_team_ranking(record: SessionRecord) -> TeamRankingAdapterResult:
    if record.team_ranking_result is not None:
        return record.team_ranking_result

    outputs = _ensure_requirements_agent_result(record)["outputs"]
    result = RequirementsAgentTeamRankingAdapter().build(
        session_id=record.session_id,
        requirements_list=outputs["requirements_list"],
        roleplay_requirements_input=outputs["roleplay_requirements_input"],
        requester_pm=_requester_pm_payload(record),
    )
    outputs["roleplay_requirements_input"] = result.roleplay_requirements_input
    outputs.update(result.ranking_result)
    record.team_ranking_result = result
    return result


def _roleplay_packet(record: SessionRecord):
    return _get_or_build_team_ranking(record).roleplay_packet


def _requester_pm_payload(record: SessionRecord) -> dict[str, Any] | None:
    if not _has_pm_persona_input(record):
        return None

    payload = dict(record.pm_persona) if isinstance(record.pm_persona, dict) else {}
    payload["name"] = _pm_persona_name(record)
    if record.pm_priority:
        payload["priority"] = record.pm_priority
    return payload


def _team_member_from_sample(
    member: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[str, str]:
    assigned_role = str(
        member.get("assigned_role") or snapshot.get("assigned_role") or "Team Member"
    )
    employee_name = str(member.get("employee_name") or snapshot.get("employee_name") or "Unknown")
    return _team_member(
        str(member.get("employee_id") or snapshot.get("employee_id") or ""),
        employee_name,
        assigned_role,
    )


def _selected_team(record: SessionRecord) -> dict[str, Any] | None:
    teams = record.team_candidates
    if teams is None:
        teams = get_team_candidates(record.session_id)["teams"]
    else:
        teams = _teams_with_pm_persona(record, teams)
    record.team_candidates = teams
    selected_id = record.selected_team_id or (teams[0]["team_id"] if teams else None)
    return next((team for team in teams if team["team_id"] == selected_id), None)


def _selected_team_summary(team: dict[str, Any] | None) -> dict[str, Any]:
    if team is None:
        return {}
    return {
        "selectedTeam": {
            "rank": team.get("team_rank", 1),
            "teamFitScore": team.get("team_fit_score", 0),
            "teamId": team.get("team_id", ""),
            "teamName": team.get("team_name", ""),
        }
    }


def _team_personas(team: dict[str, Any] | None) -> list[dict[str, str]]:
    if team is None:
        return [
            _persona("권원솔", "PM"),
            _persona("안우빈", "BE"),
            _persona("심예린", "WEB"),
            _persona("송다원", "QA"),
            _persona("박라경", "Infra"),
        ]
    return [
        _persona(
            str(member.get("employee_name", "")),
            ROLE_MAP.get(
                str(member.get("assigned_role", "")), str(member.get("assigned_role", ""))
            ),
        )
        for member in team.get("members", [])
    ]


def _teams_with_pm_persona(
    record: SessionRecord,
    teams: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not _has_pm_persona_input(record):
        return teams
    return [_team_with_pm_persona(record, team) for team in teams]


def _team_with_pm_persona(record: SessionRecord, team: dict[str, Any]) -> dict[str, Any]:
    members = [
        member
        for member in team.get("members", [])
        if not _is_pm_role(member.get("assigned_role"))
    ]
    badges = list(team.get("badges", []))
    if "PM persona" not in badges:
        badges.append("PM persona")
    return {
        **team,
        "badges": badges,
        "members": [_pm_persona_member(record), *members],
    }


def _pm_persona_member(record: SessionRecord) -> dict[str, str]:
    return _team_member("pm_persona", _pm_persona_name(record), "PM")


def _pm_persona_name(record: SessionRecord) -> str:
    name = (record.pm_persona or {}).get("name")
    return name.strip() if isinstance(name, str) and name.strip() else "PM"


def _has_pm_persona_input(record: SessionRecord) -> bool:
    if record.pm_priority and record.pm_priority.strip():
        return True
    if not isinstance(record.pm_persona, dict):
        return False
    return any(
        isinstance(record.pm_persona.get(key), str) and record.pm_persona[key].strip()
        for key in ("name", "preset", "persona", "constraints")
    )


def _is_pm_role(role: Any) -> bool:
    if not isinstance(role, str):
        return False
    return role.strip().casefold() in {"pm", "project manager", "product manager"}


def _shadow_requirements_payload(record: SessionRecord) -> dict[str, Any]:
    if record.team_ranking_result is not None:
        return dict(record.team_ranking_result.roleplay_requirements_input)

    agent_outputs = _ensure_requirements_agent_result(record)["outputs"]
    roleplay_input = agent_outputs.get("roleplay_requirements_input")
    if isinstance(roleplay_input, dict):
        payload = dict(roleplay_input)
        payload["project_id"] = record.session_id
        return payload

    summary = record.requirements_summary or get_requirements_summary(record.session_id)
    sample = _load_json(SHADOW_AGENT_SAMPLES / "sample_requirements_list.json")
    required_roles = _shadow_required_roles(summary, sample)
    required_skills = summary.get("required_skills") or sample.get("required_skills", [])
    features = _shadow_feature_payloads(summary, required_skills, sample)

    return {
        "project_id": record.session_id,
        "project_name": summary.get("project_name") or sample.get("project_name", "Untitled"),
        "project_summary": summary.get("project_summary")
        or sample.get("project_summary", "No project summary."),
        "required_roles": required_roles,
        "required_skills": required_skills,
        "features": features,
        "timeline": _shadow_timeline_payload(summary, required_roles, sample),
        "constraints": _shadow_constraints(record, sample),
        "risk_flags": summary.get("risk_flags") or sample.get("risk_flags", []),
    }


def _shadow_required_roles(summary: dict[str, Any], sample: dict[str, Any]) -> list[str]:
    roles = [
        str(role)
        for role in (summary.get("required_roles") or sample.get("required_roles", []))
    ]
    without_pm = [role for role in roles if not _is_pm_role(role)]
    return ["PM", *without_pm]


def _shadow_feature_payloads(
    summary: dict[str, Any],
    required_skills: list[str],
    sample: dict[str, Any],
) -> list[dict[str, Any]]:
    sample_features = sample.get("features", [])
    features = summary.get("features") or sample_features
    payloads = []
    for index, feature in enumerate(features):
        sample_feature = sample_features[index] if index < len(sample_features) else {}
        payloads.append(
            {
                "feature_id": str(
                    feature.get("feature_id")
                    or sample_feature.get("feature_id")
                    or f"feat_{index + 1:03d}"
                ),
                "feature_name": str(
                    feature.get("feature_name")
                    or sample_feature.get("feature_name")
                    or f"Feature {index + 1}"
                ),
                "priority": _shadow_priority(feature, sample_feature),
                "assigned_role": str(
                    feature.get("assigned_role")
                    or sample_feature.get("assigned_role")
                    or "Team Member"
                ),
                "tech_requirements": _shadow_tech_requirements(
                    feature,
                    sample_feature,
                    required_skills,
                ),
                "dependencies": [str(item) for item in feature.get("dependencies", [])],
                "estimated_days": max(
                    1,
                    int(feature.get("estimated_days") or sample_feature.get("estimated_days") or 1),
                ),
                "risk_notes": str(
                    feature.get("risk_notes") or sample_feature.get("risk_notes") or ""
                ),
            }
        )
    return payloads


def _shadow_priority(feature: dict[str, Any], sample_feature: dict[str, Any]) -> str:
    priority = feature.get("priority") or sample_feature.get("priority") or "P1"
    return priority if priority in {"P0", "P1", "P2"} else "P1"


def _shadow_tech_requirements(
    feature: dict[str, Any],
    sample_feature: dict[str, Any],
    required_skills: list[str],
) -> list[str]:
    tech_requirements = feature.get("tech_requirements") or sample_feature.get("tech_requirements")
    if isinstance(tech_requirements, list) and tech_requirements:
        return [str(item) for item in tech_requirements]
    return [str(skill) for skill in required_skills[:3]] or ["General implementation"]


def _shadow_timeline_payload(
    summary: dict[str, Any],
    required_roles: list[str],
    sample: dict[str, Any],
) -> dict[str, Any]:
    sample_timeline = sample.get("timeline", {})
    timeline_days = int(
        summary.get("timeline_days") or sample_timeline.get("total_sprint_days") or 14
    )
    owner_role = required_roles[0] if required_roles else "PM"
    milestones = [
        {
            "name": str(milestone.get("label") or milestone.get("name") or "Milestone"),
            "due_day": max(1, int(milestone.get("day") or milestone.get("due_day") or 1)),
            "owner_role": str(milestone.get("owner_role") or owner_role),
        }
        for milestone in summary.get("milestones", [])
    ]
    if not milestones:
        milestones = sample_timeline.get("milestones", [])
    return {"total_sprint_days": max(1, timeline_days), "milestones": milestones}


def _shadow_constraints(record: SessionRecord, sample: dict[str, Any]) -> list[str]:
    requirements = (
        (record.requirements_agent_result or {})
        .get("outputs", {})
        .get(
            "requirements_list",
            {},
        )
    )
    constraints = requirements.get("constraints")
    if isinstance(constraints, list) and constraints:
        return [str(item) for item in constraints]
    return sample.get("constraints", [])


def _shadow_selected_team_record(record: SessionRecord) -> dict[str, Any]:
    if record.team_ranking_result is not None:
        selected = record.team_ranking_result.ranking_result.get("roleplay_selected_team_record")
        if isinstance(selected, dict):
            return dict(selected)

    selected_team = _selected_team(record) or _load_sample_team_candidates()[0]
    sample = _load_json(SHADOW_AGENT_SAMPLES / "sample_selected_team_record.json")
    members = [
        {
            "employee_id": str(member.get("employee_id", "")),
            "employee_name": str(member.get("employee_name", "")),
            "assigned_role": str(member.get("assigned_role", "Team Member")),
        }
        for member in selected_team.get("members", [])
    ]
    if len(members) < 2:
        members = sample.get("members", [])

    return {
        "team_id": str(selected_team.get("team_id") or sample.get("team_id", "team_001")),
        "team_rank": int(selected_team.get("team_rank") or sample.get("team_rank") or 1),
        "team_fit_score": float(
            selected_team.get("team_fit_score") or sample.get("team_fit_score") or 0
        ),
        "members": members,
        "role_coverage_score": float(
            selected_team.get("role_coverage_score") or sample.get("role_coverage_score") or 0
        ),
        "skill_coverage_score": float(
            selected_team.get("skill_coverage_score") or sample.get("skill_coverage_score") or 0
        ),
        "availability_score": float(
            selected_team.get("availability_score") or sample.get("availability_score") or 0
        ),
        "team_risk_flags": selected_team.get("team_risk_flags")
        or sample.get("team_risk_flags", []),
    }


def _shadow_member_snapshots_payload(
    team_record: dict[str, Any],
    record: SessionRecord | None = None,
) -> list[dict[str, Any]]:
    risk_flags = team_record.get("team_risk_flags", [])
    snapshots = []
    for index, member in enumerate(team_record.get("members", [])):
        assigned_role = str(member.get("assigned_role", "Team Member"))
        is_pm = _is_pm_role(assigned_role)
        snapshots.append(
            {
                "employee_id": str(member.get("employee_id", "")),
                "employee_name": str(member.get("employee_name", "")),
                "assigned_role": assigned_role,
                "matched_skills": _shadow_matched_skills(assigned_role, record),
                "missing_skills": _shadow_missing_skills(
                    assigned_role,
                    risk_flags,
                    record,
                ),
                "capacity_signal": (
                    "low_risk" if is_pm else _shadow_capacity_signal(index, risk_flags)
                ),
                "communication_signal": "low_delay" if is_pm else "medium_delay",
                "delivery_signal": "stable" if is_pm else ("variable" if risk_flags else "stable"),
                "collaboration_signal": _shadow_collaboration_signal(assigned_role),
                "risk_tags": _shadow_risk_tags(assigned_role, risk_flags),
                "evidence_refs": _shadow_evidence_refs(assigned_role),
            }
        )
    return snapshots


def _shadow_risk_tags(assigned_role: str, risk_flags: list[str]) -> list[str]:
    if _is_pm_role(assigned_role):
        return ["pm_persona_input"]
    return risk_flags[:2]


def _shadow_evidence_refs(assigned_role: str) -> list[str]:
    if _is_pm_role(assigned_role):
        return ["pm.persona_input"]
    return [
        "employee.job_category_code",
        "employee.performance_score",
        "employee.engagement_score",
    ]


def _shadow_matched_skills(
    assigned_role: str,
    record: SessionRecord | None = None,
) -> list[str]:
    role_key = ROLE_MAP.get(assigned_role, assigned_role)
    if _is_pm_role(assigned_role):
        return _shadow_pm_matched_skills(record)
    return {
        "PM": ["planning", "stakeholder alignment"],
        "BE": ["api design", "backend implementation"],
        "WEB": ["frontend implementation", "api integration"],
        "Infra": ["deployment", "ci/cd"],
        "QA": ["test planning", "quality validation"],
        "DS": ["analysis", "requirements interpretation"],
    }.get(role_key, ["general execution"])


def _shadow_pm_matched_skills(record: SessionRecord | None) -> list[str]:
    skills = ["planning", "stakeholder alignment", "risk triage"]
    persona = _string_from_pm_persona(record, "persona")
    preset = _string_from_pm_persona(record, "preset")
    if persona:
        skills.append(f"PM persona input: {_truncate(persona, 220)}")
    if preset:
        skills.append(f"PM style preset: {preset}")
    if record and record.pm_priority:
        skills.append(f"PM operating priority: {_truncate(record.pm_priority, 160)}")
    return skills


def _shadow_missing_skills(
    assigned_role: str,
    risk_flags: list[str],
    record: SessionRecord | None = None,
) -> list[str]:
    if _is_pm_role(assigned_role):
        constraint = _string_from_pm_persona(record, "constraints")
        return [f"PM user constraint: {_truncate(constraint, 220)}"] if constraint else []
    if "role_gap" in risk_flags:
        return [f"{assigned_role} exact job-category coverage"]
    if "workload_risk" in risk_flags:
        return ["workload buffer"]
    return []


def _string_from_pm_persona(record: SessionRecord | None, key: str) -> str:
    if record is None or not isinstance(record.pm_persona, dict):
        return ""
    value = record.pm_persona.get(key)
    return value.strip() if isinstance(value, str) else ""


def _truncate(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "..."


def _shadow_capacity_signal(index: int, risk_flags: list[str]) -> str:
    if "workload_risk" in risk_flags and index == 0:
        return "high_risk"
    if "availability_risk" in risk_flags:
        return "medium_risk"
    return "low_risk"


def _shadow_collaboration_signal(assigned_role: str) -> str:
    role_key = ROLE_MAP.get(assigned_role, assigned_role)
    return {
        "PM": "connector",
        "BE": "review_hub",
        "WEB": "focused_individual",
        "Infra": "connector",
        "QA": "review_hub",
        "DS": "async_deep_worker",
    }.get(role_key, "async_deep_worker")


def _shadow_team_risk_summary_payload(team_id: str) -> dict[str, Any]:
    risk_summary = _load_json(SHADOW_AGENT_SAMPLES / "sample_team_risk_summary.json")
    risk_summary["team_id"] = team_id
    return risk_summary


def _get_or_create_session(session_id: str) -> SessionRecord:
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = SessionRecord(session_id=session_id, prd_text=DEFAULT_PRD_TEXT)
    return _SESSIONS[session_id]


def _ensure_requirements_agent_result(record: SessionRecord) -> dict[str, Any]:
    if record.requirements_agent_result is None:
        record.requirements_agent_result = _run_requirements_agent(record)
    return record.requirements_agent_result


def _run_requirements_agent(record: SessionRecord) -> dict[str, Any]:
    references = load_references(DEFAULT_REFERENCE_DIR)
    headers = read_employee_data_headers(DEFAULT_EMPLOYEE_DATA_DIR)
    column_validation = validate_employee_column_rules_against_headers(
        references["employee_column_rules"],
        headers,
    )
    if column_validation["status"] != "passed":
        raise RuntimeError("employee_column_rules.json conflicts with datasets/raw CSV headers.")

    settings = get_settings()
    requested_mode = (settings.requirements_llm_mode or settings.llm_mode).value
    llm_config = LLMConfig.from_env(mode=requested_mode)
    actual_config = llm_config
    fallback_error = None

    try:
        result = _run_requirements_pipeline_for_record(record, references, llm_config)
    except Exception as exc:
        if llm_config.mode == LLM_MODE_STUB or settings.requirements_strict_llm:
            raise
        fallback_error = f"{type(exc).__name__}: {exc}"
        actual_config = LLMConfig.from_env(mode=LLM_MODE_STUB)
        result = _run_requirements_pipeline_for_record(record, references, actual_config)

    llm_summary = actual_config.safe_summary()
    llm_summary.update(
        {
            "requested_mode": llm_config.mode,
            "actual_mode": actual_config.mode,
            "fallback_error": fallback_error,
            "strict": settings.requirements_strict_llm,
        }
    )
    record.metadata["requirements_llm"] = llm_summary
    result["session"] = {
        "session_id": record.session_id,
        "column_validation": column_validation,
        "llm": llm_summary,
    }
    return result


def _run_requirements_pipeline_for_record(
    record: SessionRecord,
    references: dict[str, Any],
    llm_config: LLMConfig,
) -> dict[str, Any]:
    extractor = build_section_extractor(config=llm_config, rulebase=references["rulebase"])
    result = run_requirements_pipeline(
        record.prd_text,
        document_id=record.session_id,
        document_type="prd",
        source_uri=f"memory://sessions/{record.session_id}/prd",
        project_fields=build_local_project_fields(record.prd_text),
        extractor=extractor,
        config=RequirementsPipelineConfig(write_outputs=False, human_confirm_complete=True),
    )
    return result


def _to_requirements_summary(requirements_list: dict[str, Any]) -> dict[str, Any]:
    features = requirements_list.get("required_features", [])
    roles = requirements_list.get("required_roles", [])
    skills = requirements_list.get("required_skills", [])
    risks = requirements_list.get("risk_factors", [])
    timeline_days = _duration_to_days(requirements_list.get("duration_weeks"))

    return {
        "project_name": requirements_list.get("project_name") or "Untitled project",
        "project_summary": requirements_list.get("project_goal") or "No project goal extracted.",
        "required_roles": [_role_name(role) for role in roles],
        "required_skills": [_skill_name(skill) for skill in skills],
        "features": [
            {
                "feature_id": f"feat_{index + 1:03d}",
                "feature_name": feature.get("standard_name")
                or feature.get("feature_key")
                or f"Feature {index + 1}",
                "priority": _priority_for_index(index),
                "assigned_role": _assigned_role_for_feature(feature, roles),
                "estimated_days": _estimated_days_for_feature(index, timeline_days),
                "dependencies": [],
                **_feature_risk_note(feature, risks),
            }
            for index, feature in enumerate(features)
        ],
        "timeline_days": timeline_days,
        "milestones": _milestones(timeline_days),
        "risk_flags": [_risk_text(risk) for risk in risks[:6]],
        "confidence": _requirements_confidence(requirements_list),
    }


def _duration_to_days(value: Any) -> int:
    if isinstance(value, int | float) and value > 0:
        return max(1, round(float(value) * 7))
    if isinstance(value, dict):
        candidates = [
            value.get("max"),
            value.get("maximum"),
            value.get("to"),
            value.get("min"),
            value.get("minimum"),
            value.get("from"),
        ]
        for candidate in candidates:
            if isinstance(candidate, int | float) and candidate > 0:
                return max(1, round(float(candidate) * 7))
    return 14


def _role_name(role: dict[str, Any]) -> str:
    return str(role.get("role") or role.get("standard_name") or "Team Member")


def _skill_name(skill: dict[str, Any]) -> str:
    return str(skill.get("skill") or skill.get("standard_name") or "General")


def _priority_for_index(index: int) -> str:
    if index < 3:
        return "P0"
    if index < 6:
        return "P1"
    return "P2"


def _assigned_role_for_feature(feature: dict[str, Any], roles: list[dict[str, Any]]) -> str:
    source_key = feature.get("feature_key")
    for role in roles:
        if source_key in role.get("source_feature_keys", []):
            return _role_name(role)
    return _role_name(roles[0]) if roles else "Team Member"


def _estimated_days_for_feature(index: int, timeline_days: int) -> int:
    if timeline_days <= 7:
        return 1
    if index < 3:
        return max(2, min(4, timeline_days // 5))
    return max(1, min(3, timeline_days // 7))


def _feature_risk_note(feature: dict[str, Any], risks: list[dict[str, Any]]) -> dict[str, str]:
    source_key = feature.get("feature_key")
    for risk in risks:
        if source_key in risk.get("source_feature_keys", []):
            return {"risk_notes": _risk_text(risk)}
    return {}


def _risk_text(risk: dict[str, Any]) -> str:
    return str(risk.get("text") or risk.get("risk_key") or "Risk")


def _milestones(timeline_days: int) -> list[dict[str, int | str]]:
    return [
        {"label": "Kickoff", "day": 1},
        {"label": "Design", "day": max(2, round(timeline_days * 0.2))},
        {"label": "Development", "day": max(3, round(timeline_days * 0.7))},
        {"label": "QA", "day": timeline_days},
    ]


def _requirements_confidence(requirements_list: dict[str, Any]) -> int:
    review_count = sum(
        len(requirements_list.get(key, []))
        for key in ("unknown_requirements", "missing_extractions", "low_confidence_items")
    )
    status = requirements_list.get("_meta", {}).get("status")
    base = 92 if status == "completed" else 84
    return max(50, base - min(review_count * 4, 30))


def _extract_prd_text(payload: dict[str, Any]) -> str:
    prd = payload.get("prd")
    if isinstance(prd, str) and prd.strip():
        return prd.strip()
    return DEFAULT_PRD_TEXT


def _dict_or_none(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _string_or_none(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _team_member(employee_id: str, name: str, assigned_role: str) -> dict[str, str]:
    role_key = ROLE_MAP.get(assigned_role, "BE")
    return {
        "employee_id": employee_id,
        "employee_name": name,
        "assigned_role": assigned_role,
        "initials": _initials(name),
        "color": ROLE_COLORS.get(role_key, "bg-zinc-500"),
    }


def _persona(name: str, role_key: str) -> dict[str, str]:
    return {
        "id": name,
        "name": name,
        "role": role_key,
        "color": ROLE_COLORS.get(role_key, "bg-zinc-500"),
        "initials": _initials(name),
    }


def _initials(name: str) -> str:
    parts = name.split()
    if len(parts) <= 1:
        return name[:2]
    return "".join(part[:1] for part in parts[:2])


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _load_json_list(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load_env_file() -> None:
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())
