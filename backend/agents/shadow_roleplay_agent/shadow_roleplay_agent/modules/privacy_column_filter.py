"""Phase 2 — Privacy & Column Filter

guardrails.md §2 기준으로 EmployeeFitProfileSnapshot에서
개인정보와 원천 DB 식별자를 제거하고 업무 signal만 남긴다.

제거 대상 (금지 input):
  - employee_id        : HR DB PK
  - cross-system IDs   : 시스템 식별자 (github_id, slack_user_id 등)
  - 개인정보           : 나이, 성별, 주소, 학교, 개인 프로필

유지 대상 (허용 input):
  employee_name, assigned_role, matched_skills, missing_skills,
  capacity_signal, communication_signal, delivery_signal,
  collaboration_signal, risk_tags, evidence_refs
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.sanitized_snapshot import (
    FilterAuditLog,
    SanitizedProfileSnapshot,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    EmployeeFitProfileSnapshot,
    SimulationInputPacket,
)

logger = logging.getLogger(__name__)

# guardrails §2 허용 필드 목록 (고정)
_ALLOWED_FIELDS: frozenset[str] = frozenset({
    "employee_name",
    "assigned_role",
    "matched_skills",
    "missing_skills",
    "capacity_signal",
    "communication_signal",
    "delivery_signal",
    "collaboration_signal",
    "risk_tags",
    "evidence_refs",
})

# EmployeeFitProfileSnapshot의 전체 필드 집합
_ALL_SNAPSHOT_FIELDS: frozenset[str] = frozenset(
    EmployeeFitProfileSnapshot.model_fields.keys()
)

# 제거 대상 필드 = 전체 - 허용
_REMOVED_FIELDS: frozenset[str] = _ALL_SNAPSHOT_FIELDS - _ALLOWED_FIELDS


@dataclass
class FilterResult:
    """Privacy_and_Column_Filter 실행 결과."""

    sanitized_snapshots: list[SanitizedProfileSnapshot]
    audit_logs: list[FilterAuditLog] = field(default_factory=list)

    @property
    def member_count(self) -> int:
        return len(self.sanitized_snapshots)


class PrivacyColumnFilter:
    """guardrails §2 기준으로 snapshot을 sanitize한다.

    사용 방법:
        f = PrivacyColumnFilter()
        result = f.filter(packet)
        PrivacyColumnFilter.to_json(result.sanitized_snapshots, path)
    """

    def filter(self, packet: SimulationInputPacket) -> FilterResult:
        """패킷의 member_snapshots를 필터링하고 FilterResult를 반환한다."""
        sanitized: list[SanitizedProfileSnapshot] = []
        logs: list[FilterAuditLog] = []

        for snap in packet.member_snapshots:
            s, log = self._sanitize_one(snap)
            sanitized.append(s)
            logs.append(log)
            logger.info(
                "[PrivacyFilter] %s | 제거=%s",
                snap.employee_name,
                log.removed_fields,
            )

        logger.info(
            "[PrivacyFilter] 완료 | %d명 sanitized | 제거 필드: %s",
            len(sanitized),
            sorted(_REMOVED_FIELDS),
        )
        return FilterResult(sanitized_snapshots=sanitized, audit_logs=logs)

    @staticmethod
    def _sanitize_one(
        snap: EmployeeFitProfileSnapshot,
    ) -> tuple[SanitizedProfileSnapshot, FilterAuditLog]:
        """단일 snapshot을 필터링한다."""
        sanitized = SanitizedProfileSnapshot(
            employee_name=snap.employee_name,
            assigned_role=snap.assigned_role,
            matched_skills=snap.matched_skills,
            missing_skills=snap.missing_skills,
            capacity_signal=snap.capacity_signal,
            communication_signal=snap.communication_signal,
            delivery_signal=snap.delivery_signal,
            collaboration_signal=snap.collaboration_signal,
            risk_tags=snap.risk_tags,
            evidence_refs=snap.evidence_refs,
        )

        actually_removed = sorted(_REMOVED_FIELDS & _ALL_SNAPSHOT_FIELDS)
        retained = sorted(_ALLOWED_FIELDS & _ALL_SNAPSHOT_FIELDS)

        log = FilterAuditLog(
            employee_name=snap.employee_name,
            removed_fields=actually_removed,
            retained_fields=retained,
        )
        return sanitized, log

    @staticmethod
    def to_json(
        snapshots: list[SanitizedProfileSnapshot],
        path: Path | str,
    ) -> None:
        """Sanitized_Profile_Snapshot.json으로 저장한다."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        data = [s.model_dump() for s in snapshots]
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("[PrivacyFilter] 저장 완료 -> %s", out)

    @staticmethod
    def removed_fields() -> list[str]:
        """제거되는 필드 목록을 반환한다 (테스트/문서 용도)."""
        return sorted(_REMOVED_FIELDS)

    @staticmethod
    def retained_fields() -> list[str]:
        """유지되는 필드 목록을 반환한다 (테스트/문서 용도)."""
        return sorted(_ALLOWED_FIELDS & _ALL_SNAPSHOT_FIELDS)
