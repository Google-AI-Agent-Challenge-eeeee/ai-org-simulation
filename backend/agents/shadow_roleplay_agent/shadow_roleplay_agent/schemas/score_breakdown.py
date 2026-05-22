"""Phase 9 산출물 스키마 — Score Breakdown

Score_Calculator가 생성하는 차원별 점수 및 overall_project_fit.
Score_Breakdown.json의 루트 모델.

rules.md §5 가중치 공식:
  overall_project_fit =
    schedule_stability    * 0.20
  + role_clarity          * 0.15
  + technical_risk_control* 0.15
  + integration_readiness * 0.15
  + collaboration_quality * 0.15
  + qa_release_readiness  * 0.10
  + workload_balance      * 0.10

rules.md §6 Verdict Rule:
  proceed                 | overall 높고 unresolved high issue 없음
  proceed_with_conditions | 진행 가능, must-fix action 존재
  needs_rebalancing       | role/workload/ownership 재조정 필요
  not_recommended         | critical issue 또는 release_blocker 미해소
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Verdict(StrEnum):
    PROCEED                = "proceed"
    PROCEED_WITH_CONDITIONS = "proceed_with_conditions"
    NEEDS_REBALANCING      = "needs_rebalancing"
    NOT_RECOMMENDED        = "not_recommended"


class ScoreDimension(BaseModel):
    """단일 평가 차원의 점수와 근거."""

    model_config = ConfigDict(extra="forbid")

    dimension:      str                    # e.g. "schedule_stability"
    weight:         float = Field(ge=0.0, le=1.0)
    raw_score:      float = Field(ge=0.0, le=1.0)
    weighted_score: float = Field(ge=0.0, le=1.0)

    # 점수 근거 추적
    deducted_by:    list[str] = Field(
        default_factory=list,
        description="이 차원 점수를 낮춘 issue_id 목록",
    )
    penalty_detail: list[str] = Field(
        default_factory=list,
        description="페널티 설명 (issue_category + status + severity)",
    )
    phase_signal:   str = ""


class ScoreBreakdown(BaseModel):
    """Score_Breakdown.json 전체 구조.

    Phase 10 Recommendation Adjuster의 직접 입력.
    guardrails §6 준수: 사람 점수 아님, 팀 조합 프로젝트 적합도.
    """

    model_config = ConfigDict(extra="forbid")

    simulation_id:       str
    team_id:             str

    dimensions:          list[ScoreDimension]
    overall_project_fit: float = Field(ge=0.0, le=1.0)
    verdict:             Verdict

    # Phase 9 진단 요약
    top_risk_dimensions:  list[str] = Field(
        default_factory=list,
        description="raw_score 하위 3개 차원",
    )
    must_fix_categories:  list[str] = Field(
        default_factory=list,
        description="CONFIRMED HIGH issue의 issue_category 목록 (릴리즈 전 필수 해결)",
    )
    score_note: str = Field(
        default="",
        description="guardrails §6 권장 표현 준수 설명문",
    )
