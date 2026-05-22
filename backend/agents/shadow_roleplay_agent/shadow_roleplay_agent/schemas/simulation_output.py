"""Phase 10 산출물 스키마 — Simulation Output

Output_Builder가 생성하는 최종 통합 산출물.
Score_Breakdown + Issue_Risk_Summary + Team_Simulation_Log → Simulation_OUTPUT.json

guardrails.md §7 최종 output 필수 포함:
  simulation_verdict, overall_project_fit, score_breakdown,
  top_risks, must_fix_before_start, evidence_summary

guardrails.md §6 금지 표현:
  직원 개인 성격 단정 / 사람 평가 점수 표현 금지.
  "이 팀 조합은 해당 프로젝트 조건에서 ~" 형태 권장.
"""

from pydantic import BaseModel, ConfigDict, Field

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.score_breakdown import (
    Verdict,
)


class DimensionSummary(BaseModel):
    """최종 output에 포함되는 차원별 점수 요약."""

    model_config = ConfigDict(extra="forbid")

    dimension:      str
    raw_score:      float
    weighted_score: float
    weight:         float
    status:         str   # good / warning / critical


class TopRisk(BaseModel):
    """상위 risk 요약 — 개인정보 없이 카테고리 + 근거만 포함."""

    model_config = ConfigDict(extra="forbid")

    rank:               int
    issue_category:     str
    severity:           str
    status:             str   # confirmed / candidate
    observed_in_phases: list[str]
    suggested_action:   str
    evidence_refs:      list[str] = Field(default_factory=list)


class MustFixItem(BaseModel):
    """시작 전 필수 해결 항목."""

    model_config = ConfigDict(extra="forbid")

    issue_category:  str
    severity:        str
    suggested_action: str
    affected_roles:  list[str] = Field(default_factory=list)


class EvidenceSummary(BaseModel):
    """simulation에서 사용된 evidence 통계."""

    model_config = ConfigDict(extra="forbid")

    total_evidence_refs:     int = 0
    total_confirmed_issues:  int = 0
    total_candidate_issues:  int = 0
    total_unresolved_turns:  int = 0
    phases_with_high_risk:   list[str] = Field(default_factory=list)


class SimulationOutput(BaseModel):
    """Simulation_OUTPUT.json 루트 모델.

    guardrails §6: 사람 점수 아님.
    "해당 프로젝트 조건에서의 팀 조합 안정성 점수" 표현 사용.
    """

    model_config = ConfigDict(extra="forbid")

    simulation_id:        str
    team_id:              str
    project_name:         str

    # 핵심 결과
    simulation_verdict:   Verdict
    overall_project_fit:  float = Field(ge=0.0, le=1.0)
    score_note:           str   = Field(
        description="guardrails §6 권장 표현 준수 진단 요약"
    )

    # 차원별 점수
    score_breakdown:      list[DimensionSummary]

    # 리스크 요약
    top_risks:            list[TopRisk]
    must_fix_before_start: list[MustFixItem]

    # evidence 통계
    evidence_summary:     EvidenceSummary

    # phase 안정성 요약
    phase_stability_summary: dict[str, float] = Field(
        default_factory=dict,
        description="phase_name → phase_stability_score 요약",
    )
