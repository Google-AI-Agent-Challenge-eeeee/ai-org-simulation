"""Phase 6 — Role Agent Execution

각 AgentCard와 PhaseContext를 기반으로
구조화 발언(observation / concern / dependency / proposed_action)을 생성한다.

llm_mode="stub"  → 규칙 기반 발언 생성 (LLM 불필요)
llm_mode="vertex" → Vertex AI Gemini 호출

PhaseContext가 주입되면 Agent는:
  - current_event에서 상황을 인식한다.
  - phase_agenda에서 자신의 역할 범위를 확인한다.
  - peer_roles에서 의존 대상 역할을 파악한다.
  - available_evidence_refs 바깥의 사실을 생성하지 않는다.

guardrails §3 준수:
  - evidence_refs 밖의 사실 생성 금지
  - 역할 범위(assigned_role) 밖의 주장 금지
  - 개인 성격·감정·사생활 묘사 금지
  - 4개 필드 모두 반드시 채움
"""

from __future__ import annotations

import json
import logging
import os

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.agent_card import (
    AgentCard,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.orchestrator import (
    AgentTurn,
    LLMMode,
    ValidationResult,
    ValidationStatus,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.phase_context import (
    PhaseContext,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.phase_plan import (
    ScenarioEvent,
)

logger = logging.getLogger(__name__)


class RoleAgent:
    """단일 AgentCard + PhaseContext를 기반으로 구조화 발언을 생성한다.

    speak_with_context()  : PhaseContext를 사용한 컨텍스트 인식 발언 (권장)
    speak()               : 이전 인터페이스 호환용 — context 없이 event만 사용
    """

    def __init__(self, card: AgentCard, llm_mode: LLMMode = LLMMode.STUB) -> None:
        self.card     = card
        self.llm_mode = llm_mode

    # ── 권장 인터페이스 ────────────────────────
    def speak_with_context(self, ctx: PhaseContext) -> AgentTurn:
        """PhaseContext를 사용해 역할 인식 구조화 발언을 생성한다."""
        if self.llm_mode == LLMMode.STUB:
            turn = self._speak_context_stub(ctx)
        else:
            turn = self._speak_llm(ctx)
        validation = _validate(turn, self.card)
        return turn.model_copy(update={"validation": validation})

    # ── 하위 호환 인터페이스 ───────────────────
    def speak(self, event: ScenarioEvent, phase_name: str) -> AgentTurn:
        """이전 Orchestrator 호환용 — event + phase_name만 사용."""
        if self.llm_mode == LLMMode.STUB:
            turn = self._speak_stub(event, phase_name)
        else:
            # speak()는 context가 없어서 LLM 모드에서도 stub 사용
            turn = self._speak_stub(event, phase_name)
        validation = _validate(turn, self.card)
        return turn.model_copy(update={"validation": validation})

    # ── Vertex AI Gemini LLM 발언 ──────────────
    def _speak_llm(self, ctx: PhaseContext) -> AgentTurn:
        """Vertex AI Gemini를 호출해 구조화 발언을 생성한다.

        google-genai SDK (v1+) 사용 — vertexai=True로 Vertex AI 엔드포인트 연결.

        guardrails §3 준수:
          - evidence_refs 범위 내 사실만 사용
          - 4개 필드(observation/concern/dependency/proposed_action) 필수
          - JSON 응답 파싱 실패 시 stub으로 fallback
        """
        from google import genai
        from google.genai import types

        project  = os.environ.get("GCP_PROJECT_ID", "")
        location = os.environ.get("VERTEX_LOCATION", "asia-northeast3")
        model_id = os.environ.get("VERTEX_MODEL", "gemini-2.5-flash")

        if not project:
            logger.warning("GCP_PROJECT_ID not set — falling back to stub")
            return self._speak_context_stub(ctx)

        client = genai.Client(vertexai=True, project=project, location=location)

        system_prompt = _build_system_prompt(self.card)
        user_prompt   = _build_user_prompt(self.card, ctx)

        try:
            response = client.models.generate_content(
                model=model_id,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,
                    response_mime_type="application/json",
                ),
            )
            raw  = response.text.strip()
            data = json.loads(raw)

            return AgentTurn(
                agent_id=self.card.agent_id,
                assigned_role=self.card.assigned_role,
                observation=data.get("observation", ""),
                concern=data.get("concern", ""),
                dependency=data.get("dependency", ""),
                proposed_action=data.get("proposed_action", ""),
                evidence_refs_used=data.get("evidence_refs_used", []),
                llm_mode=LLMMode.VERTEX,
                validation=ValidationResult(status=ValidationStatus.VALID),
            )
        except Exception as exc:
            logger.warning("Gemini call failed (%s) — falling back to stub", exc)
            return self._speak_context_stub(ctx)

    # ── Context 기반 Stub 발언 ─────────────────
    def _speak_context_stub(self, ctx: PhaseContext) -> AgentTurn:
        card  = self.card

        observation     = _ctx_observation(card, ctx)
        concern, ev_used = _ctx_concern(card, ctx)
        dependency      = _ctx_dependency(card, ctx)
        proposed_action = _ctx_proposed_action(card, ctx)

        return AgentTurn(
            agent_id=card.agent_id,
            assigned_role=card.assigned_role,
            observation=observation,
            concern=concern,
            dependency=dependency,
            proposed_action=proposed_action,
            evidence_refs_used=ev_used,
            validation=ValidationResult(status=ValidationStatus.VALID),
            llm_mode=self.llm_mode,
        )

    # ── 하위 호환 Stub 발언 ───────────────────
    def _speak_stub(self, event: ScenarioEvent, phase_name: str) -> AgentTurn:
        card = self.card

        observation     = _build_observation(card, event, phase_name)
        concern, ev_used = _build_concern(card, event)
        dependency      = _build_dependency(card, event)
        proposed_action = _build_proposed_action(card, event)

        return AgentTurn(
            agent_id=card.agent_id,
            assigned_role=card.assigned_role,
            observation=observation,
            concern=concern,
            dependency=dependency,
            proposed_action=proposed_action,
            evidence_refs_used=ev_used,
            validation=ValidationResult(status=ValidationStatus.VALID),
            llm_mode=self.llm_mode,
        )


# ──────────────────────────────────────────────
# PhaseContext 기반 발언 생성 헬퍼
# ──────────────────────────────────────────────

def _ctx_observation(card: AgentCard, ctx: PhaseContext) -> str:
    """역할 관점에서 현재 phase + event 상황을 관찰한다.

    - phase_objective로 어떤 관점에서 볼지 설정
    - agenda에서 자신 담당 항목 추출
    - event 설명 요약
    """
    my_agenda = [
        a.topic for a in ctx.phase_agenda
        if a.owner_role == card.assigned_role
    ]
    agenda_text = f" 담당 agenda: [{', '.join(my_agenda[:2])}]." if my_agenda else ""

    event_summary = ctx.current_event.description[:70]

    return (
        f"[{card.assigned_role} / {card.agent_id}] "
        f"{ctx.phase_name.value} — {ctx.phase_objective[:50]}. "
        f"현재 이벤트: '{event_summary}...'.{agenda_text}"
    )


def _ctx_concern(
    card: AgentCard, ctx: PhaseContext
) -> tuple[str, list[str]]:
    """risk_tags + constraints 중 event trigger_source와 연관된 항목으로 우려를 표현한다."""
    event    = ctx.current_event
    triggers = set(event.trigger_source)

    matched_risks = [r for r in card.risk_tags if r in triggers]
    matched_evs   = [e for e in ctx.available_evidence_refs if e in triggers]
    matched_consts = [
        c for c in card.constraints
        if any(kw in c.lower() for kw in
               " ".join(triggers).replace("_", " ").split())
    ][:1]

    if matched_risks or matched_evs or matched_consts:
        risk_text  = f" (risk: {matched_risks})" if matched_risks else ""
        ev_text    = f" (evidence: {matched_evs})" if matched_evs else ""
        const_text = f" | 제약: {matched_consts[0]}" if matched_consts else ""
        concern = (
            f"[{card.assigned_role}] 이 이벤트는 "
            f"'{event.expected_issue_category}' 유형 이슈 가능성이 있음."
            f"{risk_text}{ev_text}{const_text}"
        )
        return concern, matched_evs
    else:
        concern = (
            f"[{card.assigned_role}] 직접적 리스크 참조는 없으나, "
            f"'{event.expected_issue_category}'가 팀 일정 전체에 영향을 줄 수 있음. "
            f"모니터링 필요."
        )
        return concern, []


def _ctx_dependency(card: AgentCard, ctx: PhaseContext) -> str:
    """peer_roles 중 자신 외 역할에 대한 의존성을 역할 + risk_tags와 함께 표현한다."""
    others = [
        p for p in ctx.peer_roles
        if p.assigned_role != card.assigned_role
    ]
    if not others:
        return (
            f"[{card.assigned_role}] 이 이벤트 내 의존 역할 없음. "
            f"단독 처리 가능한 항목으로 분류."
        )

    dep_parts = []
    for peer in others:
        risk_hint = f" (risk: {peer.risk_tags[:1]})" if peer.risk_tags else ""
        dep_parts.append(f"{peer.assigned_role}{risk_hint}")

    return (
        f"[{card.assigned_role}] 해소를 위해 {', '.join(dep_parts)}의 "
        f"선행 작업 또는 협의가 필요함. 블로킹 전 사전 조율 권장."
    )


def _ctx_proposed_action(card: AgentCard, ctx: PhaseContext) -> str:
    """자신의 strengths + phase_objective 맥락에서 구체적 완화 제안을 생성한다."""
    event = ctx.current_event

    # strengths 중 event 키워드와 가장 관련 있는 항목 선택
    event_words = set(
        event.description.lower().replace(".", " ")
        .replace("(", " ").replace(")", " ").split()[:8]
    )
    best_strength = next(
        (s for s in card.strengths
         if any(w in s.lower() for w in event_words)),
        card.strengths[0] if card.strengths else None,
    )

    # agenda 중 자신 담당 항목에서 action 힌트 추출
    my_agenda = [a.topic for a in ctx.phase_agenda if a.owner_role == card.assigned_role]
    agenda_hint = f" Agenda 항목 '{my_agenda[0][:40]}'에서 즉시 착수 가능." if my_agenda else ""

    if best_strength:
        return (
            f"[{card.assigned_role}] '{best_strength}'를 활용해 "
            f"'{event.expected_issue_category}' 완화 조치 가능."
            f"{agenda_hint}"
        )
    return (
        f"[{card.assigned_role}] '{event.expected_issue_category}' 해소를 위해 "
        f"관련 팀원과 조기 협의 및 action item 지정 권고."
        f"{agenda_hint}"
    )


# ──────────────────────────────────────────────
# 하위 호환 발언 생성 헬퍼 (context 없을 때)
# ──────────────────────────────────────────────

def _build_observation(card: AgentCard, event: ScenarioEvent, phase_name: str) -> str:
    relevant_resp = [r for r in card.responsibilities if "P0" in r or "P1" in r]
    resp_text = f" 담당 기능: {', '.join(relevant_resp[:2])}." if relevant_resp else ""
    return (
        f"[{card.assigned_role}] {phase_name} — "
        f"'{event.description[:60]}...'.{resp_text}"
    )


def _build_concern(card: AgentCard, event: ScenarioEvent) -> tuple[str, list[str]]:
    matched_risks = [r for r in card.risk_tags if r in event.trigger_source]
    matched_evs   = [e for e in card.evidence_refs if e in event.trigger_source]
    trigger_kws   = set(" ".join(event.trigger_source).replace("_", " ").split())
    matched_consts = [c for c in card.constraints if any(kw in c.lower() for kw in trigger_kws)][:1]

    if matched_risks or matched_consts:
        return (
            f"[{card.assigned_role}] '{event.expected_issue_category}' 유형 이슈 가능성."
            + (f" risk={matched_risks}" if matched_risks else "")
            + (f" | {matched_consts[0]}" if matched_consts else ""),
            matched_evs,
        )
    return (
        f"[{card.assigned_role}] 직접적 리스크 없으나 '{event.expected_issue_category}'가 팀 일정 영향 가능.",
        [],
    )


def _build_dependency(card: AgentCard, event: ScenarioEvent) -> str:
    others = [r for r in event.involved_roles if r != card.assigned_role]
    if others:
        return f"[{card.assigned_role}] {', '.join(others)}의 선행 작업에 의존. 사전 조율 필요."
    return f"[{card.assigned_role}] 단독 처리 가능 항목."


def _build_proposed_action(card: AgentCard, event: ScenarioEvent) -> str:
    event_words = set(event.description.lower().split()[:6])
    best = next(
        (s for s in card.strengths if any(w in s.lower() for w in event_words)),
        card.strengths[0] if card.strengths else None,
    )
    if best:
        return f"[{card.assigned_role}] '{best}'로 '{event.expected_issue_category}' 완화 가능. 즉시 검토 필요."
    return f"[{card.assigned_role}] '{event.expected_issue_category}' 해소를 위한 조기 협의 권고."


# ──────────────────────────────────────────────
# 발언 검증
# ──────────────────────────────────────────────

def _validate(turn: AgentTurn, card: AgentCard) -> ValidationResult:
    """guardrails §3 규칙을 기반으로 AgentTurn을 검증한다."""
    failed: list[str] = []

    for field_name in ("observation", "concern", "dependency", "proposed_action"):
        if not getattr(turn, field_name, "").strip():
            failed.append(f"empty_field:{field_name}")

    if failed:
        return ValidationResult(
            status=ValidationStatus.INVALID,
            failed_checks=failed,
            reason="필수 발언 필드 중 빈 항목 존재. 재질문 필요.",
        )

    concern_has_evidence = (
        any(r in turn.concern for r in card.risk_tags)
        or bool(turn.evidence_refs_used)
        or "직접적 리스크" in turn.concern
        or "모니터링" in turn.concern
    )
    if not concern_has_evidence:
        return ValidationResult(
            status=ValidationStatus.NEEDS_RETRY,
            failed_checks=["concern_no_evidence"],
            reason="concern이 risk_tags 또는 evidence_refs와 연결되지 않음. 재질문 대상.",
        )

    pii_keywords = ["나이", "성별", "주소", "학교", "성격", "개인 사정"]
    if any(kw in turn.concern for kw in pii_keywords):
        return ValidationResult(
            status=ValidationStatus.INVALID,
            failed_checks=["pii_in_concern"],
            reason="concern에 개인정보 키워드 포함. guardrails §2 위반.",
        )

    if "단독 처리 가능" in turn.dependency:
        return ValidationResult(
            status=ValidationStatus.WARNING,
            failed_checks=["no_dependency_declared"],
            reason="dependency 없음 — 단독 처리 분류. 검토 권장.",
        )

    return ValidationResult(status=ValidationStatus.VALID)


# ──────────────────────────────────────────────
# Vertex AI 프롬프트 빌더
# ──────────────────────────────────────────────

# ── AgentCard 신호값 → 행동 성향 설명 변환 ──────────────

_COLLAB_DESC: dict[str, str] = {
    "rapid_responder":    "즉각적으로 반응하고 소통 속도가 빠른 편",
    "review_hub":         "다른 팀원의 작업을 검토·연결하는 허브 역할",
    "focused_individual": "독립적으로 깊이 집중하며 외부 소통이 적은 편",
    "connector":          "팀 간 연결과 조율을 담당하는 브릿지 역할",
    "async_deep_worker":  "비동기 방식으로 깊이 몰입하며 작업하는 편",
}

_DELIVERY_DESC: dict[str, str] = {
    "stable":   "납기 이력이 안정적",
    "variable": "납기 일정이 불안정한 편 (재작업 발생 이력 있음)",
    "unstable": "납기 이력이 불안정하고 재작업이 잦음",
}


def _persona_from_card(card: AgentCard) -> str:
    """AgentCard의 실제 신호 필드로부터 페르소나 단락을 생성한다.

    판단 근거 변수 목록:
      - agent_id          : 이 사람의 이름 (호칭·1인칭 기준)
      - assigned_role     : 역할 (발언 범위 결정)
      - collaboration_signal : 협업 스타일 (소통 속도·말투)
      - delivery_signal   : 납기 안정성 (불안/자신감 수준)
      - constraints       : capacity/communication signal 경고 (긴장·부담감)
      - risk_tags         : 민감하게 반응해야 할 사안
      - strengths         : 자신 있는 영역 (자신감 표현)
      - missing_skills    : 모르는 영역 (솔직한 불안 표현)
    """
    collab   = _COLLAB_DESC.get(card.collaboration_signal.value, card.collaboration_signal.value)
    delivery = _DELIVERY_DESC.get(card.delivery_signal.value, card.delivery_signal.value)

    signal_constraints = [c for c in card.constraints if "signal" in c.lower()]
    signal_str = (" " + " ".join(signal_constraints) + ".") if signal_constraints else ""

    missing = [c.replace("스킬 부재: ", "") for c in card.constraints if c.startswith("스킬 부재:")]
    missing_str = (
        f" {', '.join(missing)} 쪽은 솔직히 자신 없다고 표현해도 된다." if missing else ""
    )

    risk_hint = ""
    if card.risk_tags:
        risk_hint = (
            f" 리스크 태그 [{', '.join(card.risk_tags)}]에 해당하는 상황이 나오면"
            " 직접적으로 민감하게 반응한다."
        )

    return (
        f"당신은 {card.agent_id}입니다. {card.assigned_role}로 이 프로젝트에 참여하고 있습니다.\n"
        f"협업 스타일: {collab}. 납기 성향: {delivery}.{signal_str}{missing_str}{risk_hint}\n"
        f"동료를 부를 때는 반드시 이름을 사용한다 (예: '권원솔 씨', '안우빈 씨').\n"
        f"자신의 상황에 맞는 감정·개인 의견을 자유롭게 표현할 수 있다."
    )


def _build_system_prompt(card: AgentCard) -> str:
    strengths_str     = ", ".join(card.strengths)
    constraints_str   = ", ".join(card.constraints)
    risk_tags_str     = ", ".join(card.risk_tags)
    evidence_refs_str = ", ".join(card.evidence_refs)
    responsibilities  = "\n  - ".join(card.responsibilities)

    persona_desc = _persona_from_card(card)

    return f"""당신은 AI 조직 시뮬레이션에 참여하는 프로젝트 팀원입니다.

{persona_desc}

담당 업무:
  - {responsibilities}

강점: {strengths_str}
제약/리스크: {constraints_str}
리스크 태그: {risk_tags_str}
인용 가능한 evidence: {evidence_refs_str}

[필수 규칙 — guardrails §3]
1. evidence_refs에 있는 사실만 인용한다. 없는 사실을 만들지 않는다.
2. 자신의 역할({card.assigned_role}) 관점에서 발언하되, 감정·개인 의견 표현은 허용된다.
3. 나이·성별·주소·학교 등 PII는 절대 언급하지 않는다.
4. 4개 필드(observation, concern, dependency, proposed_action) 모두 반드시 채운다.
5. 각 필드는 한국어로 1~3문장. 위 협업·납기·제약 성향이 자연스럽게 드러나는 말투로 쓴다.
6. JSON 오브젝트만 반환. 마크다운 코드 블록·추가 키 금지.

반환 JSON 형식:
{{
  "observation":      "<현재 상황에서 내가 직접 관찰한 사실>",
  "concern":          "<내 역할 관점에서 우려되는 리스크나 이슈>",
  "dependency":       "<내가 의존하는 역할·산출물, 없으면 'none'>",
  "proposed_action":  "<내가 제안하는 구체적 행동>",
  "evidence_refs_used": ["<ev_id_1>", ...]
}}"""


def _build_user_prompt(
    card: AgentCard,
    ctx: PhaseContext,
    prior_turns: list | None = None,
) -> str:
    event      = ctx.current_event
    peers_str  = (
        ", ".join(f"{p.agent_id}({p.assigned_role})" for p in ctx.peer_roles)
        if ctx.peer_roles else "none"
    )
    agenda_str = "; ".join(a.topic for a in ctx.phase_agenda)
    history_str = ""
    if prior_turns:
        lines = []
        for t in (prior_turns[-4:]):
            lines.append(
                f"[{t.agent_id}] obs={t.observation[:60]}... / concern={t.concern[:60]}..."
            )
        history_str = "\n".join(lines)

    return f"""=== 현재 단계: {ctx.phase_name} ===
단계 목표  : {ctx.phase_objective}
단계 안건  : {agenda_str}
팀원 역할  : {peers_str}

=== 현재 이벤트 ===
이벤트 ID  : {event.event_id}
설명       : {event.description}
예상 이슈  : {event.expected_issue_category}
트리거 원인: {event.trigger_source}

=== 최근 대화 (최대 4턴) ===
{history_str if history_str else "(이전 발언 없음)"}

=== 지시 ===
당신은 {card.agent_id}입니다.
위 이벤트에 대해 당신 자신의 관점과 감정으로 반응하세요.
동료를 언급할 때는 반드시 이름으로 부르세요 (위 팀원 목록 참고).
다른 사람이 이미 말한 내용을 반복하지 말고, {card.agent_id}만이 할 수 있는 발언을 하세요.
시스템 지시의 JSON 형식으로만 응답하세요."""
