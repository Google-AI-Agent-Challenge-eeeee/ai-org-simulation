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
from pathlib import Path
from typing import Any

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


def create_session() -> dict[str, str]:
    return {"session_id": f"sim_{uuid.uuid4().hex[:8]}"}


def get_requirements_summary(session_id: str) -> dict[str, Any]:
    return {
        "project_name": "결제 및 사용자 관리 플랫폼 v1.0",
        "project_summary": (
            "이메일 기반 인증, 결제 API 연동, 메인 대시보드를 포함하는 14일 스프린트 MVP. "
            "외부 결제 API(PG사) 의존성이 높고 GCP Cloud Run 배포가 필수다."
        ),
        "required_roles": [
            "PM",
            "Backend Developer",
            "Frontend Developer",
            "QA Engineer",
            "DevOps Engineer",
        ],
        "required_skills": [
            "Python",
            "FastAPI",
            "PostgreSQL",
            "React",
            "TypeScript",
            "Payment API",
            "GCP Cloud Run",
            "Docker",
            "Pytest",
            "CI/CD",
        ],
        "features": [
            {
                "feature_id": "feat_001",
                "feature_name": "이메일 로그인",
                "priority": "P0",
                "assigned_role": "Backend Developer",
                "estimated_days": 3,
                "dependencies": [],
                "risk_notes": "인증 플로우 미확정 시 FE 연동 블로킹",
            },
            {
                "feature_id": "feat_002",
                "feature_name": "결제 API 연동",
                "priority": "P0",
                "assigned_role": "Backend Developer",
                "estimated_days": 4,
                "dependencies": ["feat_001"],
                "risk_notes": "외부 PG사 sandbox 응답 지연 가능성",
            },
            {
                "feature_id": "feat_003",
                "feature_name": "메인 대시보드 UI",
                "priority": "P0",
                "assigned_role": "Frontend Developer",
                "estimated_days": 3,
                "dependencies": ["feat_001"],
            },
            {
                "feature_id": "feat_004",
                "feature_name": "사용자 프로필 편집",
                "priority": "P1",
                "assigned_role": "Frontend Developer",
                "estimated_days": 2,
                "dependencies": ["feat_001"],
            },
            {
                "feature_id": "feat_005",
                "feature_name": "알림 시스템",
                "priority": "P1",
                "assigned_role": "Backend Developer",
                "estimated_days": 2,
                "dependencies": ["feat_001"],
            },
            {
                "feature_id": "feat_006",
                "feature_name": "로그 내보내기",
                "priority": "P2",
                "assigned_role": "Backend Developer",
                "estimated_days": 1,
            },
            {
                "feature_id": "feat_007",
                "feature_name": "다크모드 토글",
                "priority": "P2",
                "assigned_role": "Frontend Developer",
                "estimated_days": 1,
            },
        ],
        "timeline_days": 14,
        "milestones": [
            {"label": "Kickoff", "day": 1},
            {"label": "Design", "day": 3},
            {"label": "Development", "day": 10},
            {"label": "QA", "day": 14},
        ],
        "risk_flags": [
            "외부 PG API 의존",
            "14일 일정 촉박",
            "FE-BE 스펙 동기화",
            "GCP Cloud Run 경험 부족",
        ],
        "confidence": 92,
    }


def accept_requirements(session_id: str) -> dict[str, bool]:
    return {"ok": True}


def revise_requirements(session_id: str) -> dict[str, Any]:
    return get_requirements_summary(session_id)


def get_team_candidates(session_id: str) -> dict[str, Any]:
    teams = [
        {
            "team_id": "team_001",
            "team_name": "알파 포메이션",
            "team_rank": 1,
            "team_fit_score": 84.0,
            "role_coverage_score": 0.95,
            "skill_coverage_score": 0.88,
            "availability_score": 1.0,
            "team_risk_flags": ["backend_workload_concentration", "pm_low_sprint_velocity"],
            "badges": ["실제 시뮬레이션 팀", "Agent sample verified"],
            "rationale": (
                "실제 직원 데이터(sample) 기반 시뮬레이션 팀. backend workload와 "
                "Cloud Run 경험 부족이 주요 리스크다."
            ),
            "skill_gaps": ["Payment API SDK", "GCP Cloud Run 실운영"],
            "members": [
                _team_member("E011", "권원솔", "PM"),
                _team_member("E012", "안우빈", "Backend Developer"),
                _team_member("E013", "심예린", "Frontend Developer"),
                _team_member("E014", "송다원", "QA Engineer"),
                _team_member("E015", "박라경", "DevOps Engineer"),
            ],
        }
    ]
    return {"totalCombinations": 1247, "teams": teams}


def select_team(session_id: str, team_id: str | None = None) -> dict[str, bool]:
    return {"ok": True}


def get_report(session_id: str) -> dict[str, Any]:
    overall, verdict, score_note, top_risks, must_fix = _load_simulation_output()
    risk_level = "High" if overall < 0.6 else ("Mid" if overall < 0.8 else "Low")

    return {
        "id": session_id,
        "createdAt": "2026-05-23T03:00:00Z",
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


def iter_pipeline_sse(llm_mode: str) -> Iterator[str]:
    _load_env_file()

    from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules import (
        AgentCardBuilder,
        PrivacyColumnFilter,
        ScenarioPhasePlanner,
    )
    from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline import (
        SimulationInputBuilder,
        SimulationOrchestrator,
    )
    from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
        RequirementsList,
        TeamRiskSummary,
    )

    yield sse("status", {"stage": "analyzing", "text": "시뮬레이션 입력 데이터 구성 중"})
    yield sse("backend_log", {"text": "Simulation_Input_Packet 병합 중"})

    builder = SimulationInputBuilder()
    packet, evidence_index = builder.build(
        requirements=SHADOW_AGENT_SAMPLES / "sample_requirements_list.json",
        team_record=SHADOW_AGENT_SAMPLES / "sample_selected_team_record.json",
        snapshots=SHADOW_AGENT_SAMPLES / "sample_employee_fit_profile_snapshots.json",
        risk_summary=SHADOW_AGENT_SAMPLES / "sample_team_risk_summary.json",
        evidence_metadata=SHADOW_AGENT_SAMPLES / "sample_evidence_metadata.json",
    )

    requirements_full = RequirementsList.model_validate(
        _load_json(SHADOW_AGENT_SAMPLES / "sample_requirements_list.json")
    )
    risk_summary = TeamRiskSummary.model_validate(
        _load_json(SHADOW_AGENT_SAMPLES / "sample_team_risk_summary.json")
    )

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
        simulation_id="sim_stream",
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
            yield sse("status", {"stage": "done", "text": "시뮬레이션 완료"})
            yield sse("done", {})


def iter_agent_turn_sse(chunk: dict[str, Any], msg_counter: int) -> Iterator[str]:
    turn = chunk["turn"]
    persona = _persona(chunk["agent_id"], ROLE_MAP.get(chunk["role"], "BE"))

    for field, turn_type in [
        ("observation", "observation"),
        ("concern", "concern"),
        ("dependency", "dependency"),
        ("proposed_action", "proposed_action"),
    ]:
        text = turn.get(field, "").strip()
        if not text:
            continue
        msg_id = f"msg_{msg_counter}_{field}"
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


def _load_env_file() -> None:
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())
