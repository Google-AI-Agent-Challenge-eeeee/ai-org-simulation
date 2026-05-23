"""Phase 4 — Scenario Phase Planner

RequirementsList + TeamRiskSummary + EvidenceMetadata를 기반으로
5개 고정 phase 각각의 agenda와 scenario_event를 생성한다.

설계:
- 각 phase는 관찰해야 할 risk 카테고리가 다르다.
- 팀의 실제 risk_tag가 phase별 카테고리에 매핑될 때만 scenario_event를 생성한다.
- trigger_source는 해당 risk를 뒷받침하는 evidence_ref를 자동으로 연결한다.
- LLM 없이 규칙 기반으로 동작한다 (stub 모드 기본 원칙).
"""

from __future__ import annotations

import logging
from pathlib import Path

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


# ──────────────────────────────────────────────
# 1. Phase별 고정 정의
#    (objective, risk 카테고리, 기본 agenda)
# ──────────────────────────────────────────────

_PHASE_DEFINITIONS: dict[PhaseName, dict] = {
    PhaseName.KICKOFF: {
        "objective": "프로젝트 목표·R&R·owner·일정 공유. 역할/책임 불명확성과 일정 인식 차이를 조기 발견한다.",
        "focus_categories": {
            "pm_low_sprint_velocity",
            "backend_workload_concentration",
            "unclear_ownership",
            "role_conflict",
        },
        "base_agenda": [
            AgendaItem(topic="프로젝트 목표 및 MVP 범위 공유", owner_role="PM"),
            AgendaItem(topic="역할별 책임(R&R) 및 기능 owner 확정", owner_role="PM"),
            AgendaItem(topic="전체 일정 및 마일스톤 검토", owner_role="PM"),
            AgendaItem(topic="알려진 리스크 및 제약 공유", owner_role="PM"),
        ],
    },
    PhaseName.DESIGN: {
        "objective": "API 스펙·DB 스키마·외부 의존성·기술 선택 검토. 기술 복잡성과 설계 공백을 확인한다.",
        "focus_categories": {
            "payment_api_integration_risk",
            "devops_gcp_experience_gap",
            "technical_dependency_risk",
            "missing_skill",
        },
        "base_agenda": [
            AgendaItem(topic="DB 스키마 및 데이터 모델 확정", owner_role="Backend Developer"),
            AgendaItem(topic="API 엔드포인트 스펙 초안 공유", owner_role="Backend Developer"),
            AgendaItem(
                topic="외부 API(결제 PG) sandbox 환경 확보 계획", owner_role="Backend Developer"
            ),
            AgendaItem(topic="GCP Cloud Run 배포 아키텍처 설계", owner_role="DevOps Engineer"),
            AgendaItem(
                topic="FE 디자인 시안 및 컴포넌트 구조 공유", owner_role="Frontend Developer"
            ),
        ],
    },
    PhaseName.DEVELOPMENT: {
        "objective": "업무 분배·구현 병목·PR 리뷰 흐름 확인. 일정/업무 집중 리스크를 점검한다.",
        "focus_categories": {
            "backend_workload_concentration",
            "pm_low_sprint_velocity",
            "fe_scope_instability",
            "workload_concentration",
            "schedule_risk",
        },
        "base_agenda": [
            AgendaItem(topic="P0 기능 진척 현황 공유", owner_role="PM"),
            AgendaItem(
                topic="BE P0 기능(인증·결제 API) 구현 상태 점검", owner_role="Backend Developer"
            ),
            AgendaItem(
                topic="FE 컴포넌트 개발 현황 및 API mock 사용 여부 확인",
                owner_role="Frontend Developer",
            ),
            AgendaItem(
                topic="DevOps CI/CD 파이프라인 구성 진행 상황", owner_role="DevOps Engineer"
            ),
            AgendaItem(topic="PR 리뷰 병목 및 업무 집중 여부 점검", owner_role="PM"),
        ],
    },
    PhaseName.INTEGRATION: {
        "objective": "FE/BE/API/DB 연동·스펙 불일치 확인. 실제 충돌이 가장 많이 드러나는 구간을 집중 관찰한다.",
        "focus_categories": {
            "fe_be_api_dependency",
            "payment_api_integration_risk",
            "fe_scope_instability",
            "devops_gcp_experience_gap",
            "integration_risk",
        },
        "base_agenda": [
            AgendaItem(
                topic="BE API 완료 여부 및 FE 연동 착수 조건 확인", owner_role="Backend Developer"
            ),
            AgendaItem(
                topic="결제 API schema 확정 및 FE 연동 테스트", owner_role="Backend Developer"
            ),
            AgendaItem(topic="FE-BE 연동 이슈 목록 공유", owner_role="Frontend Developer"),
            AgendaItem(
                topic="Cloud Run 스테이징 환경 배포 완료 확인", owner_role="DevOps Engineer"
            ),
            AgendaItem(topic="연동 단계 미해결 이슈 owner 지정", owner_role="PM"),
        ],
    },
    PhaseName.QA_RELEASE: {
        "objective": "테스트 범위·결함·release blocker 확인. QA 커버리지 갭과 릴리즈 리스크를 집중 점검한다.",
        "focus_categories": {
            "qa_communication_gap",
            "qa_coverage_gap",
            "release_blocker",
            "communication_delay",
        },
        "base_agenda": [
            AgendaItem(topic="전체 테스트 케이스 커버리지 리뷰", owner_role="QA Engineer"),
            AgendaItem(topic="결제 흐름 E2E 테스트 계획 및 실행 현황", owner_role="QA Engineer"),
            AgendaItem(topic="High severity 버그 목록 및 owner 확인", owner_role="PM"),
            AgendaItem(topic="릴리즈 blocker 이슈 해소 상태 점검", owner_role="PM"),
            AgendaItem(topic="배포 최종 체크리스트 확인", owner_role="DevOps Engineer"),
        ],
    },
}

# ──────────────────────────────────────────────
# 2. risk_tag → scenario_event 템플릿 매핑
#    각 tag에 대한 이벤트 설명, 관련 역할, issue 카테고리를 정의한다.
# ──────────────────────────────────────────────

_RISK_EVENT_TEMPLATES: dict[str, dict] = {
    "pm_low_sprint_velocity": {
        "description": "PM의 최근 스프린트 완료율(29.1%)이 낮아 일정 관리에 대한 우려가 제기됨. 팀 전체 속도와 마일스톤 달성 가능성을 재확인해야 함.",
        "involved_roles": ["PM", "Backend Developer"],
        "expected_issue_category": "schedule_risk",
    },
    "backend_workload_concentration": {
        "description": "BE 담당자에게 P0 기능(인증·결제 API)이 집중되고 미완료 이슈(6건)가 누적. 업무 과부하로 인한 일정 지연 가능성 확인 필요.",
        "involved_roles": ["Backend Developer", "PM"],
        "expected_issue_category": "workload_concentration",
    },
    "payment_api_integration_risk": {
        "description": "외부 결제 PG API SDK 경험이 없고 최근 scope change 5회 발생. sandbox 환경 미확보 또는 스펙 변경 시 FE 연동 블로킹 위험.",
        "involved_roles": ["Backend Developer", "Frontend Developer", "PM"],
        "expected_issue_category": "technical_dependency_risk",
    },
    "fe_scope_instability": {
        "description": "FE 담당자의 최근 scope change 10회, 재오픈 이슈 3건 발생. 요구사항 변동 반복 패턴으로 구현 완성도 저하 우려.",
        "involved_roles": ["Frontend Developer", "PM"],
        "expected_issue_category": "schedule_risk",
    },
    "fe_be_api_dependency": {
        "description": "FE 이슈 평균 사이클 타임 8.4일로 팀 내 최고. BE API 완료 전 FE 연동 착수 불가 구조로 Integration 단계 블로킹 가능성.",
        "involved_roles": ["Frontend Developer", "Backend Developer"],
        "expected_issue_category": "integration_risk",
    },
    "devops_gcp_experience_gap": {
        "description": "DevOps 담당자의 GCP Cloud Run 실운영 경험 없음. 초기 IAM 설정 및 Cloud Run 구성 지연 시 전체 배포 파이프라인 블로킹.",
        "involved_roles": ["DevOps Engineer", "PM"],
        "expected_issue_category": "technical_dependency_risk",
    },
    "qa_communication_gap": {
        "description": "QA 담당자의 슬랙 메시지 수(85건)가 팀 평균(172건) 대비 낮고 집중 작업 시간(515분)도 부족. 버그 리포트 지연 및 이슈 소통 단절 위험.",
        "involved_roles": ["QA Engineer", "PM"],
        "expected_issue_category": "communication_delay",
    },
    "qa_coverage_gap": {
        "description": "Playwright E2E 스킬 미보유 및 결제 도메인 테스트 케이스 경험 없음. 결제 실패·예외 케이스 테스트 누락으로 release blocker 가능성.",
        "involved_roles": ["QA Engineer", "Backend Developer"],
        "expected_issue_category": "qa_coverage_gap",
    },
}


# ──────────────────────────────────────────────
# 3. Planner 클래스
# ──────────────────────────────────────────────


class ScenarioPhasePlanner:
    """RequirementsList + TeamRiskSummary를 기반으로 5개 phase 계획을 생성한다.

    사용 방법:
        planner = ScenarioPhasePlanner()
        plan = planner.plan(requirements, risk_summary, evidence_index, simulation_id)
        ScenarioPhasePlanner.to_json(plan, path)
    """

    def plan(
        self,
        requirements: RequirementsList,
        risk_summary: TeamRiskSummary,
        evidence_index: EvidenceIndex,
        simulation_id: str,
    ) -> SimulationPhasePlan:
        """5개 phase SimulationPhasePlan을 생성하고 반환한다."""
        phases: list[SimulationPhase] = []
        event_counter = 1

        for phase_name in PhaseName:
            defn = _PHASE_DEFINITIONS[phase_name]
            focus_categories: set[str] = defn["focus_categories"]

            # 이 phase에서 활성화되는 risk_tag 필터링
            active_risk_tags = [tag for tag in risk_summary.risk_tags if tag in focus_categories]

            # agenda: 기본 agenda + 해당 phase의 features
            agenda = list(defn["base_agenda"]) + _feature_agenda(requirements, phase_name)

            # scenario_events: 활성 risk_tag마다 이벤트 생성
            events: list[ScenarioEvent] = []
            for risk_tag in active_risk_tags:
                tmpl = _RISK_EVENT_TEMPLATES.get(risk_tag)
                if tmpl is None:
                    logger.warning("[Planner] risk_tag=%s 템플릿 없음 (스킵)", risk_tag)
                    continue

                # evidence_refs 자동 연결
                trigger_sources = [risk_tag] + [
                    ev.source_column for ev in evidence_index.for_risk(risk_tag)
                ]

                events.append(
                    ScenarioEvent(
                        event_id=f"evt_{event_counter:03d}",
                        description=tmpl["description"],
                        trigger_source=trigger_sources,
                        involved_roles=tmpl["involved_roles"],
                        expected_issue_category=tmpl["expected_issue_category"],
                    )
                )
                event_counter += 1

            phases.append(
                SimulationPhase(
                    phase_name=phase_name,
                    phase_objective=defn["objective"],
                    agenda=agenda,
                    scenario_events=events,
                    focus_risk_tags=active_risk_tags,
                )
            )

            logger.info(
                "[Planner] %s | agenda=%d, events=%d, focus_risks=%s",
                phase_name.value,
                len(agenda),
                len(events),
                active_risk_tags,
            )

        plan = SimulationPhasePlan(
            simulation_id=simulation_id,
            project_name=requirements.project_name,
            phases=phases,
        )
        logger.info("[Planner] 완료 | 총 event=%d", event_counter - 1)
        return plan

    @staticmethod
    def to_json(plan: SimulationPhasePlan, path: Path | str) -> None:
        """Simulation_Phase_Plan.json으로 저장한다."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            plan.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logger.info("[Planner] 저장 완료 -> %s", out)


# ──────────────────────────────────────────────
# 4. 헬퍼 — phase 타임라인 기반 feature agenda 추출
# ──────────────────────────────────────────────

# 각 phase가 커버하는 스프린트 day 범위 (14일 기준)
_PHASE_DAY_RANGES: dict[PhaseName, tuple[int, int]] = {
    PhaseName.KICKOFF: (1, 2),
    PhaseName.DESIGN: (2, 4),
    PhaseName.DEVELOPMENT: (4, 10),
    PhaseName.INTEGRATION: (10, 13),
    PhaseName.QA_RELEASE: (13, 14),
}


def _feature_agenda(req: RequirementsList, phase: PhaseName) -> list[AgendaItem]:
    """RequirementsList.features 중 이 phase 타임라인에 해당하는 항목을 agenda로 변환한다."""
    start, end = _PHASE_DAY_RANGES[phase]
    items: list[AgendaItem] = []

    for feat in req.features:
        if start <= feat.estimated_days <= end:
            items.append(
                AgendaItem(
                    topic=f"[기능] {feat.feature_name} ({feat.priority.value}) 진행 확인",
                    owner_role=feat.assigned_role,
                    related_features=[feat.feature_id],
                )
            )
    return items
