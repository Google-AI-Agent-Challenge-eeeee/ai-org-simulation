"""시뮬레이션 SSE 스트리밍 API

GET  /api/sessions/{session_id}/stream
  → SSE 스트림으로 시뮬레이션 진행 상황을 실시간 전송

현재 구조: sample JSON을 고정으로 읽어 파이프라인 실행.
추후 session_id → DB에서 팀/요구사항 조회로 교체.

SSE 이벤트 포맷 (frontend useSimulation.ts 와 1:1 대응):
  event: status      → { stage, text, phase?, phaseIndex? }
  event: backend_log → { text }
  event: message     → { persona, token, messageId, turnType? }
  event: done        → {}
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/sessions", tags=["simulation"])

# ── 역할 매핑 (backend assigned_role → frontend RoleType) ─────────────────
_ROLE_MAP: dict[str, str] = {
    "PM": "PM",
    "Backend Developer": "BE",
    "Frontend Developer": "WEB",
    "DevOps Engineer": "Infra",
    "QA Engineer": "QA",
    "iOS Developer": "iOS",
    "Android Developer": "Android",
    "Data Scientist": "DS",
}

# ── Phase 이름 매핑 (backend → frontend SimulationPhase) ──────────────────
_PHASE_MAP: dict[str, str] = {
    "Kickoff Meeting": "kickoff",
    "Design Phase": "design",
    "Development Phase": "development",
    "Integration Phase": "integration",
    "QA / Release Phase": "qa_release",
}

# ── 색상 (frontend ROLE_COLORS 와 동일) ──────────────────────────────────
_ROLE_COLORS: dict[str, str] = {
    "PM": "bg-purple-500",
    "BE": "bg-blue-600",
    "WEB": "bg-cyan-500",
    "iOS": "bg-slate-500",
    "Android": "bg-green-600",
    "Infra": "bg-orange-500",
    "QA": "bg-amber-600",
    "DS": "bg-pink-500",
}

# 샘플 데이터 경로 (추후 session → DB 조회로 교체)
_SAMPLES = (
    Path(__file__).resolve().parent.parent
    / "agents/shadow_roleplay_agent/shadow_roleplay_agent/samples"
)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _make_persona(agent_id: str, assigned_role: str) -> dict:
    role_key = _ROLE_MAP.get(assigned_role, "BE")
    initials = agent_id[:2] if len(agent_id) >= 2 else agent_id
    return {
        "id": agent_id,
        "name": agent_id,
        "role": role_key,
        "color": _ROLE_COLORS.get(role_key, "bg-zinc-500"),
        "initials": initials,
    }


def _turn_type(turn_dict: dict) -> str:
    """concern > dependency > proposed_action > observation 순으로 turnType 결정."""
    if turn_dict.get("concern"):
        return "concern"
    if turn_dict.get("dependency") and "단독 처리" not in turn_dict["dependency"]:
        return "dependency"
    if turn_dict.get("proposed_action"):
        return "proposed_action"
    return "observation"


def _pipeline_stream(llm_mode: str):
    """파이프라인을 실행하며 SSE 청크를 순서대로 yield하는 동기 Generator."""
    # .env 로드 (FastAPI 프로세스 환경변수가 이미 설정돼 있으면 skip)
    env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

    import sys

    root = Path(__file__).resolve().parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    import json as _json

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

    # Phase 1-4: 데이터 준비
    yield _sse("status", {"stage": "analyzing", "text": "시뮬레이션 입력 데이터 구성 중…"})
    yield _sse("backend_log", {"text": "Simulation_Input_Packet 병합 중…"})

    builder = SimulationInputBuilder()
    packet, evidence_index = builder.build(
        requirements=_SAMPLES / "sample_requirements_list.json",
        team_record=_SAMPLES / "sample_selected_team_record.json",
        snapshots=_SAMPLES / "sample_employee_fit_profile_snapshots.json",
        risk_summary=_SAMPLES / "sample_team_risk_summary.json",
        evidence_metadata=_SAMPLES / "sample_evidence_metadata.json",
    )

    requirements_full = RequirementsList.model_validate(
        _json.loads((_SAMPLES / "sample_requirements_list.json").read_text(encoding="utf-8"))
    )
    risk_summary = TeamRiskSummary.model_validate(
        _json.loads((_SAMPLES / "sample_team_risk_summary.json").read_text(encoding="utf-8"))
    )

    yield _sse("backend_log", {"text": "PrivacyColumnFilter · PII 컬럼 제거 완료"})
    result = PrivacyColumnFilter().filter(packet)

    yield _sse(
        "backend_log",
        {"text": f"AgentCardBuilder · {len(result.sanitized_snapshots)}명 Agent Card 생성"},
    )
    cards = AgentCardBuilder().build(result.sanitized_snapshots, requirements_full)

    plan = ScenarioPhasePlanner().plan(
        requirements_full, risk_summary, evidence_index, simulation_id="sim_stream"
    )
    total_events = sum(len(p.scenario_events) for p in plan.phases)
    yield _sse(
        "backend_log",
        {"text": f"ScenarioPhasePlanner · 리스크 기반 시나리오 {total_events}개 배치"},
    )

    # Phase 5/6: 시뮬레이션 실행 + 실시간 스트리밍
    yield _sse(
        "status",
        {"stage": "meeting", "text": "시뮬레이션 진행 중", "phase": "kickoff", "phaseIndex": 0},
    )

    orchestrator = SimulationOrchestrator(llm_mode=llm_mode)
    msg_counter = 0

    for chunk in orchestrator.run_stream(plan, cards):
        ctype = chunk["type"]

        if ctype == "phase_start":
            fe_phase = _PHASE_MAP.get(chunk["phase"], "kickoff")
            phase_idx = chunk["phase_index"]
            yield _sse(
                "status",
                {
                    "stage": "meeting",
                    "text": f"시뮬레이션 진행 중 — {chunk['phase']}",
                    "phase": fe_phase,
                    "phaseIndex": phase_idx,
                },
            )

        elif ctype == "backend_log":
            yield _sse("backend_log", {"text": chunk["text"]})

        elif ctype == "agent_turn":
            turn = chunk["turn"]
            persona = _make_persona(chunk["agent_id"], chunk["role"])

            # observation → concern → dependency → proposed_action 순으로 4개 메시지
            for field, t_type in [
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
                # 토큰 단위 스트리밍 (단어별 split)
                tokens = text.split(" ")
                for i, token in enumerate(tokens):
                    space = "" if i == 0 else " "
                    yield _sse(
                        "message",
                        {
                            "persona": persona,
                            "token": space + token,
                            "messageId": msg_id,
                            "turnType": t_type,
                        },
                    )

        elif ctype == "event_start":
            yield _sse(
                "event_start",
                {
                    "eventId": chunk["event_id"],
                    "description": chunk["description"],
                },
            )

        elif ctype == "event_end":
            yield _sse("event_end", {"eventId": chunk["event_id"]})

        elif ctype == "done":
            yield _sse("status", {"stage": "done", "text": "시뮬레이션 완료 → 리포트 생성 중"})
            yield _sse("done", {})


@router.get("/{session_id}/stream")
async def simulation_stream(session_id: str, mode: str | None = None):
    """SSE 스트림 — 시뮬레이션 실시간 진행 상황 전송.

    ?mode=stub  → 강제 stub 모드 (빠른 테스트용)
    ?mode=vertex → 강제 vertex 모드
    기본값: .env LLM_MODE 설정 따름
    """
    from backend.core.config import get_settings

    settings = get_settings()
    llm_mode = mode if mode in ("stub", "vertex") else settings.llm_mode.value

    async def event_generator():
        loop = asyncio.get_event_loop()
        gen = _pipeline_stream(llm_mode)
        _STOP = object()

        def _next_or_stop(g):
            try:
                return next(g)
            except StopIteration:
                return _STOP

        while True:
            chunk = await loop.run_in_executor(None, _next_or_stop, gen)
            if chunk is _STOP:
                break
            yield chunk
            # message 토큰 사이에만 딜레이 → 타이핑 효과
            if isinstance(chunk, str) and chunk.startswith("event: message"):
                await asyncio.sleep(0.028)
            else:
                await asyncio.sleep(0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ──────────────────────────────────────────────────────────────────
# Stub 엔드포인트 (세션 생성 / 요구사항 / 팀 선택)
# 추후 실제 DB + Agent 연동으로 교체 예정
# ──────────────────────────────────────────────────────────────────


@router.post("")
async def create_session(body: dict = None):
    """세션 생성 stub — 고정 session_id 반환."""
    session_id = f"sim_{uuid.uuid4().hex[:8]}"
    return {"session_id": session_id}


@router.get("/{session_id}/requirements")
async def get_requirements(session_id: str):
    """요구사항 stub — sample requirements_list 기반 응답."""
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


@router.post("/{session_id}/requirements/accept")
async def accept_requirements(session_id: str, body: dict = None):
    return {"ok": True}


@router.post("/{session_id}/requirements/revise")
async def revise_requirements(session_id: str, body: dict = None):
    return await get_requirements(session_id)


@router.get("/{session_id}/teams")
async def get_teams(session_id: str):
    """팀 목록 stub — 고정 3팀 반환."""

    def color(role: str) -> str:
        c = {
            "PM": "bg-purple-500",
            "Backend Developer": "bg-blue-600",
            "Frontend Developer": "bg-cyan-500",
            "QA Engineer": "bg-amber-600",
            "DevOps Engineer": "bg-orange-500",
        }
        return c.get(role, "bg-zinc-500")

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
            "badges": ["실제 시뮬레이션 팀", "Gemini 검증"],
            "rationale": "실제 직원 데이터(sample) 기반 Gemini 시뮬레이션 팀. overall_project_fit=0.84 (조건부 진행).",
            "skill_gaps": ["Payment API SDK", "GCP Cloud Run 실운영"],
            "members": [
                {
                    "employee_id": "E011",
                    "employee_name": "권원솔",
                    "assigned_role": "PM",
                    "initials": "권원",
                    "color": color("PM"),
                },
                {
                    "employee_id": "E012",
                    "employee_name": "안우빈",
                    "assigned_role": "Backend Developer",
                    "initials": "안우",
                    "color": color("Backend Developer"),
                },
                {
                    "employee_id": "E013",
                    "employee_name": "심예린",
                    "assigned_role": "Frontend Developer",
                    "initials": "심예",
                    "color": color("Frontend Developer"),
                },
                {
                    "employee_id": "E014",
                    "employee_name": "송다원",
                    "assigned_role": "QA Engineer",
                    "initials": "송다",
                    "color": color("QA Engineer"),
                },
                {
                    "employee_id": "E015",
                    "employee_name": "박라경",
                    "assigned_role": "DevOps Engineer",
                    "initials": "박라",
                    "color": color("DevOps Engineer"),
                },
            ],
        },
    ]
    return {"totalCombinations": 1247, "teams": teams}


@router.post("/{session_id}/teams/select")
async def select_team(session_id: str, body: dict = None):
    return {"ok": True}


@router.get("/{session_id}/report")
async def get_report(session_id: str):
    """리포트 stub — Simulation_OUTPUT.json 기반 응답."""
    output_path = (
        Path(__file__).resolve().parent.parent
        / "agents/shadow_roleplay_agent/shadow_roleplay_agent/outputs/Simulation_OUTPUT.json"
    )
    if output_path.exists():
        data = json.loads(output_path.read_text(encoding="utf-8"))
        overall = data.get("overall_project_fit", 0.84)
        verdict = data.get("simulation_verdict", "proceed_with_conditions")
        score_note = data.get("score_note", "")
        top_risks = data.get("top_risks", [])
        must_fix = data.get("must_fix_before_start", [])
    else:
        overall = 0.84
        verdict = "proceed_with_conditions"
        score_note = ""
        top_risks = []
        must_fix = []

    risk_level = "High" if overall < 0.6 else ("Mid" if overall < 0.8 else "Low")

    return {
        "id": session_id,
        "createdAt": "2026-05-23T03:00:00Z",
        "team": [
            {
                "id": "권원솔",
                "name": "권원솔",
                "role": "PM",
                "color": "bg-purple-500",
                "initials": "권원",
            },
            {
                "id": "안우빈",
                "name": "안우빈",
                "role": "BE",
                "color": "bg-blue-600",
                "initials": "안우",
            },
            {
                "id": "심예린",
                "name": "심예린",
                "role": "WEB",
                "color": "bg-cyan-500",
                "initials": "심예",
            },
            {
                "id": "송다원",
                "name": "송다원",
                "role": "QA",
                "color": "bg-amber-600",
                "initials": "송다",
            },
            {
                "id": "박라경",
                "name": "박라경",
                "role": "Infra",
                "color": "bg-orange-500",
                "initials": "박라",
            },
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
            "discussions": [score_note] if score_note else ["Gemini 시뮬레이션 기반 분석 완료"],
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
            {"phase": "kickoff", "score": 0.68, "summary": "R&R 불명확성·일정 리스크 초기 발견"},
            {"phase": "design", "score": 0.53, "summary": "기술 의존성·스펙 변동 리스크 확인"},
            {
                "phase": "development",
                "score": 0.52,
                "summary": "업무 과부하·스프린트 속도 저하 관찰",
            },
            {"phase": "integration", "score": 0.04, "summary": "FE-BE 연동 블로킹 이슈 집중 발생"},
            {"phase": "qa_release", "score": 0.61, "summary": "QA 커버리지 갭·릴리즈 리스크 잔존"},
        ],
    }
