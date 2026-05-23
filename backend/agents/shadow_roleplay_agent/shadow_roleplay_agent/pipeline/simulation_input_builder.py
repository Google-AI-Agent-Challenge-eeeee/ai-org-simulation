"""Phase 1 — Simulation Input Builder

5개 input을 하나의 SimulationInputPacket으로 병합하고,
각 risk·Agent 발언이 어떤 evidence에서 왔는지 역추적할 수 있는
EvidenceIndex를 생성한다.

설계 원칙:
- 원천 DB 데이터를 추가로 읽지 않는다.
- 입력 간 정합성(member ID, risk_tag 연결)을 검증한 뒤에만 패킷을 생성한다.
- 파일 경로(Path/str) 또는 이미 파싱된 Pydantic 모델 모두 수용한다.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    EmployeeFitProfileSnapshot,
    EvidenceMetadata,
    RequirementsList,
    SelectedTeamRecord,
    SimulationInputPacket,
    TeamRiskSummary,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Evidence Index — risk / evidence 역추적
# ──────────────────────────────────────────────


@dataclass
class EvidenceIndex:
    """risk_tag 또는 employee_name 기준으로 evidence를 빠르게 역추적한다.

    Phase 6 Role Agent 발언 생성 및 Phase 8 Issue/Risk 판단 시
    Orchestrator가 "이 발언의 근거가 되는 evidence가 있는가"를 확인하는 데 사용된다.
    """

    # risk_tag → [EvidenceMetadata]
    by_risk_tag: dict[str, list[EvidenceMetadata]] = field(default_factory=dict)

    # employee_name → [EvidenceMetadata]
    by_employee: dict[str, list[EvidenceMetadata]] = field(default_factory=dict)

    # evidence_id → EvidenceMetadata (단건 조회)
    by_id: dict[str, EvidenceMetadata] = field(default_factory=dict)

    @classmethod
    def build(cls, evidence_list: list[EvidenceMetadata]) -> EvidenceIndex:
        idx = cls()
        for ev in evidence_list:
            idx.by_id[ev.evidence_id] = ev
            idx.by_risk_tag.setdefault(ev.risk_tag, []).append(ev)
            idx.by_employee.setdefault(ev.employee_name, []).append(ev)
        return idx

    def for_risk(self, risk_tag: str) -> list[EvidenceMetadata]:
        return self.by_risk_tag.get(risk_tag, [])

    def for_employee(self, employee_name: str) -> list[EvidenceMetadata]:
        return self.by_employee.get(employee_name, [])

    def for_employee_and_risk(self, employee_name: str, risk_tag: str) -> list[EvidenceMetadata]:
        return [ev for ev in self.by_employee.get(employee_name, []) if ev.risk_tag == risk_tag]

    def has_evidence_for(self, risk_tag: str) -> bool:
        return bool(self.by_risk_tag.get(risk_tag))


# ──────────────────────────────────────────────
# 입력 타입 — 파일 경로 또는 파싱된 모델 모두 허용
# ──────────────────────────────────────────────

InputSource = Path | str | dict


def _load(source: InputSource) -> dict:
    if isinstance(source, dict):
        return source
    path = Path(source)
    return json.loads(path.read_text(encoding="utf-8"))


# ──────────────────────────────────────────────
# Simulation Input Builder
# ──────────────────────────────────────────────


class SimulationInputBuilder:
    """5개 input을 하나의 SimulationInputPacket으로 병합한다.

    사용 방법:
        builder = SimulationInputBuilder()
        packet, index = builder.build(
            requirements=Path("samples/sample_requirements_list.json"),
            team_record=Path("samples/sample_selected_team_record.json"),
            snapshots=Path("samples/sample_employee_fit_profile_snapshots.json"),
            risk_summary=Path("samples/sample_team_risk_summary.json"),
            evidence_metadata=Path("samples/sample_evidence_metadata.json"),
        )
    """

    def build(
        self,
        requirements: InputSource,
        team_record: InputSource,
        snapshots: InputSource,
        risk_summary: InputSource,
        evidence_metadata: InputSource,
        simulation_id: str | None = None,
    ) -> tuple[SimulationInputPacket, EvidenceIndex]:
        """5개 input을 로드·검증 후 SimulationInputPacket과 EvidenceIndex를 반환한다."""

        req = RequirementsList.model_validate(_load(requirements))
        team = SelectedTeamRecord.model_validate(_load(team_record))
        snaps = self._load_snapshots(snapshots)
        risk = TeamRiskSummary.model_validate(_load(risk_summary))
        evs = self._load_evidence(evidence_metadata)

        self._validate(req, team, snaps, risk, evs)

        sim_id = simulation_id or f"sim_{uuid.uuid4().hex[:8]}"

        packet = SimulationInputPacket(
            simulation_id=sim_id,
            project_context=req,
            selected_team=team,
            member_snapshots=snaps,
            team_risk_summary=risk,
            evidence_metadata=evs,
        )

        evidence_index = EvidenceIndex.build(evs)

        logger.info(
            "[SimulationInputBuilder] packet built | sim_id=%s, team=%s, members=%d",
            sim_id,
            team.team_id,
            len(snaps),
        )
        return packet, evidence_index

    # ── 로더 ──────────────────────────────────

    @staticmethod
    def _load_snapshots(source: InputSource) -> list[EmployeeFitProfileSnapshot]:
        raw = _load(source)
        if isinstance(raw, list):
            return [EmployeeFitProfileSnapshot.model_validate(s) for s in raw]
        # 단건 dict인 경우도 허용
        return [EmployeeFitProfileSnapshot.model_validate(raw)]

    @staticmethod
    def _load_evidence(source: InputSource) -> list[EvidenceMetadata]:
        raw = _load(source)
        if isinstance(raw, list):
            return [EvidenceMetadata.model_validate(e) for e in raw]
        return [EvidenceMetadata.model_validate(raw)]

    # ── 정합성 검증 ───────────────────────────

    @staticmethod
    def _validate(
        req: RequirementsList,
        team: SelectedTeamRecord,
        snaps: list[EmployeeFitProfileSnapshot],
        risk: TeamRiskSummary,
        evs: list[EvidenceMetadata],
    ) -> None:
        """입력 간 정합성을 검증한다. 문제가 있으면 ValueError를 발생시킨다."""

        team_names = {m.employee_name for m in team.members}
        snap_names = {s.employee_name for s in snaps}

        # 1. 팀 멤버와 snapshot 커버리지 검증
        missing_snaps = team_names - snap_names
        if missing_snaps:
            raise ValueError(
                f"[InputBuilder] snapshot 누락 팀원: {missing_snaps}. "
                "모든 팀원의 EmployeeFitProfileSnapshot이 있어야 합니다."
            )

        extra_snaps = snap_names - team_names
        if extra_snaps:
            logger.warning("[InputBuilder] 팀 멤버에 없는 snapshot 발견 (무시됨): %s", extra_snaps)

        # 2. team_id 일치 검증
        if risk.team_id != team.team_id:
            raise ValueError(
                f"[InputBuilder] team_id 불일치 — team_record={team.team_id}, "
                f"risk_summary={risk.team_id}"
            )

        # 3. evidence employee_name 검증 (팀 외 인원 경고)
        ev_names = {ev.employee_name for ev in evs}
        unknown_ev = ev_names - team_names
        if unknown_ev:
            logger.warning(
                "[InputBuilder] 팀 멤버에 없는 evidence 항목 (확인 필요): %s", unknown_ev
            )

        # 4. team risk_tags 중 evidence 미확보 항목 경고
        ev_risk_tags = {ev.risk_tag for ev in evs}
        uncovered_risks = set(risk.risk_tags) - ev_risk_tags
        if uncovered_risks:
            logger.warning(
                "[InputBuilder] evidence가 없는 risk_tag (Phase 8 판단 시 주의): %s",
                uncovered_risks,
            )

        # 5. required_roles ↔ team assigned_roles 커버리지 검증
        required_roles = set(req.required_roles)
        assigned_roles = {m.assigned_role for m in team.members}
        uncovered_roles = required_roles - assigned_roles
        if uncovered_roles:
            logger.warning("[InputBuilder] 요구사항 역할 미충족: %s", uncovered_roles)

        logger.info("[InputBuilder] 정합성 검증 통과")

    # ── 출력 유틸 ─────────────────────────────

    @staticmethod
    def to_json(packet: SimulationInputPacket, path: Path | str) -> None:
        """패킷을 JSON 파일로 저장한다."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            packet.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logger.info("[SimulationInputBuilder] 패킷 저장 완료 → %s", out)
