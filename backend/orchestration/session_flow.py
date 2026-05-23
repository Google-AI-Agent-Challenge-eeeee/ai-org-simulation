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
SHADOW_AGENT_OUTPUTS = SHADOW_AGENT_ROOT / "outputs"

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
    team_candidates: list[dict[str, Any]] | None = None
    requirements_accepted: bool = False
    selected_team_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


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
        agent_result = _run_requirements_agent(record)
        record.requirements_agent_result = agent_result
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
    record.requirements_accepted = False
    return get_requirements_summary(session_id)


def get_team_candidates(session_id: str) -> dict[str, Any]:
    record = _get_or_create_session(session_id)
    if record.team_candidates is None:
        record.team_candidates = _load_sample_team_candidates()
    return {"totalCombinations": 1247, "teams": record.team_candidates}


def select_team(session_id: str, team_id: str | None = None) -> dict[str, bool]:
    record = _get_or_create_session(session_id)
    teams = get_team_candidates(session_id)["teams"]
    selected_id = team_id or (teams[0]["team_id"] if teams else None)
    if selected_id and any(team["team_id"] == selected_id for team in teams):
        record.selected_team_id = selected_id
    return {"ok": True}


def get_report(session_id: str) -> dict[str, Any]:
    record = _get_or_create_session(session_id)
    selected_team = _selected_team(record)
    return ReportAgent().build(
        session_id=session_id,
        created_at=record.created_at,
        selected_team=selected_team,
        pm_persona=record.pm_persona,
        requirements_summary=record.requirements_summary,
        roleplay_outputs=_roleplay_outputs_for_report(record),
    )
    overall, verdict, score_note, top_risks, must_fix = _load_simulation_output()
    risk_level = "High" if overall < 0.6 else ("Mid" if overall < 0.8 else "Low")

    return {
        "id": session_id,
        "createdAt": "2026-05-23T03:00:00Z",
        **_selected_team_summary(selected_team),
        "team": [
            _persona("권원솔", "PM"),
            _persona("안우빈", "BE"),
            _persona("심예린", "WEB"),
            _persona("송다원", "QA"),
            _persona("박라경", "Infra"),
        ],
        "metrics": {
            "teamFitScore": round(overall * 100, 1),
            "riskIndex": round((1 - overall) * 100, 1),
            "riskLevel": risk_level,
            "completionRate": round(overall * 100, 1),
            "completionLabel": verdict.replace("_", " "),
            "riskDistribution": {"technical": 45, "resource": 35, "timeline": 20},
            "confidenceLevel": "Mid",
        },
        "meetingSummary": {
            "decisions": [r.get("suggested_action", "") for r in must_fix[:3]],
            "issues": [r.get("issue_category", "") for r in top_risks[:3]],
            "discussions": [score_note] if score_note else ["시뮬레이션 기반 분석 완료"],
        },
        "recommendations": [
            {
                "type": "bottleneck",
                "title": r.get("issue_category", "risk"),
                "body": r.get("suggested_action", ""),
            }
            for r in must_fix[:3]
        ],
        "phaseSummaries": [
            {
                "phase": "kickoff",
                "score": 0.68,
                "summary": "R&R 불명확성·일정 리스크 초기 발견",
            },
            {"phase": "design", "score": 0.53, "summary": "기술 의존성·스펙 변동 리스크 확인"},
            {
                "phase": "development",
                "score": 0.52,
                "summary": "업무 과부하·스프린트 속도 저하 관찰",
            },
            {
                "phase": "integration",
                "score": 0.04,
                "summary": "FE-BE 연동 블로킹 이슈 집중 발생",
            },
            {"phase": "qa_release", "score": 0.61, "summary": "QA 커버리지 갭·릴리즈 리스크 잔존"},
        ],
    }


def sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def iter_pipeline_sse(session_id: str, llm_mode: str) -> Iterator[str]:
    _load_env_file()
    record = _get_or_create_session(session_id)

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
        SimulationInputBuilder,
        SimulationOrchestrator,
    )
    from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
        EvidenceMetadata,
        RequirementsList,
        SelectedTeamRecord,
        TeamRiskSummary,
    )

    yield sse("status", {"stage": "analyzing", "text": "시뮬레이션 입력 데이터 구성 중"})
    yield sse("backend_log", {"text": "Simulation_Input_Packet 병합 중"})

    requirements_payload = _shadow_requirements_payload(record)
    team_record = _shadow_selected_team_record(record)
    risk_summary_payload = _shadow_team_risk_summary_payload(team_record["team_id"])

    builder = SimulationInputBuilder()
    packet, evidence_index = builder.build(
        requirements=requirements_payload,
        team_record=team_record,
        snapshots=SHADOW_AGENT_SAMPLES / "sample_employee_fit_profile_snapshots.json",
        risk_summary=risk_summary_payload,
        evidence_metadata=SHADOW_AGENT_SAMPLES / "sample_evidence_metadata.json",
        simulation_id=session_id,
    )

    requirements_full = RequirementsList.model_validate(requirements_payload)
    risk_summary = TeamRiskSummary.model_validate(risk_summary_payload)

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

    orchestrator = SimulationOrchestrator(llm_mode=llm_mode)
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
                    team = SelectedTeamRecord.model_validate(team_record)
                    evidence_list = [
                        EvidenceMetadata.model_validate(item)
                        for item in _load_json_list(
                            SHADOW_AGENT_SAMPLES / "sample_evidence_metadata.json"
                        )
                    ]
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
                    record.metadata["roleplay_outputs"] = {
                        "team_simulation_log": _model_dump_jsonable(sim_log),
                        "issue_risk_summary": _model_dump_jsonable(issue_summary),
                        "score_breakdown": _model_dump_jsonable(score_breakdown),
                        "simulation_output": _model_dump_jsonable(simulation_output),
                    }
                    yield sse(
                        "backend_log",
                        {"text": "ReportAgent inputs finalized from live roleplay outputs"},
                    )
            except Exception as exc:
                record.metadata["report_generation_error"] = str(exc)
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
        for i, token in enumerate(text.split(" ")):
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


def _roleplay_outputs_for_report(record: SessionRecord) -> dict[str, Any]:
    outputs = record.metadata.get("roleplay_outputs")
    if isinstance(outputs, dict):
        return outputs
    return _load_roleplay_output_artifacts()


def _load_roleplay_output_artifacts() -> dict[str, Any]:
    return {
        "simulation_output": _load_json_if_exists(SHADOW_AGENT_OUTPUTS / "Simulation_OUTPUT.json"),
        "team_simulation_log": _load_json_if_exists(
            SHADOW_AGENT_OUTPUTS / "Team_Simulation_Log.json"
        ),
        "issue_risk_summary": _load_json_if_exists(
            SHADOW_AGENT_OUTPUTS / "Issue_Risk_Summary.json"
        ),
        "score_breakdown": _load_json_if_exists(SHADOW_AGENT_OUTPUTS / "Score_Breakdown.json"),
    }


def _model_dump_jsonable(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    return {}


def _load_simulation_output() -> tuple[float, str, str, list[dict[str, Any]], list[dict[str, Any]]]:
    output_path = SHADOW_AGENT_OUTPUTS / "Simulation_OUTPUT.json"
    if not output_path.exists():
        return 0.84, "proceed_with_conditions", "", [], []

    data = _load_json(output_path)
    return (
        data.get("overall_project_fit", 0.84),
        data.get("simulation_verdict", "proceed_with_conditions"),
        data.get("score_note", ""),
        data.get("top_risks", []),
        data.get("must_fix_before_start", []),
    )


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
    teams = record.team_candidates or _load_sample_team_candidates()
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


def _shadow_requirements_payload(record: SessionRecord) -> dict[str, Any]:
    summary = record.requirements_summary or get_requirements_summary(record.session_id)
    sample = _load_json(SHADOW_AGENT_SAMPLES / "sample_requirements_list.json")
    required_roles = summary.get("required_roles") or sample.get("required_roles", [])
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


def _shadow_team_risk_summary_payload(team_id: str) -> dict[str, Any]:
    risk_summary = _load_json(SHADOW_AGENT_SAMPLES / "sample_team_risk_summary.json")
    risk_summary["team_id"] = team_id
    return risk_summary


def _get_or_create_session(session_id: str) -> SessionRecord:
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = SessionRecord(session_id=session_id, prd_text=DEFAULT_PRD_TEXT)
    return _SESSIONS[session_id]


def _run_requirements_agent(record: SessionRecord) -> dict[str, Any]:
    references = load_references(DEFAULT_REFERENCE_DIR)
    headers = read_employee_data_headers(DEFAULT_EMPLOYEE_DATA_DIR)
    column_validation = validate_employee_column_rules_against_headers(
        references["employee_column_rules"],
        headers,
    )
    if column_validation["status"] != "passed":
        raise RuntimeError("employee_column_rules.json conflicts with datasets/raw CSV headers.")

    llm_config = LLMConfig.from_env(mode="stub")
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
    result["session"] = {
        "session_id": record.session_id,
        "column_validation": column_validation,
        "llm": llm_config.safe_summary(),
    }
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
