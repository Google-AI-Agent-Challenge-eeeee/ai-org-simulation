"""Phase 8 산출물 스키마 — Issue/Risk Summary

Issue_Risk_Evaluator가 생성하는 최종 issue 확정 결과.
Issue_Risk_Summary.json의 루트 모델.

rules.md §3 확정 규칙:
  final_issue_score = 0.4 * pre_simulation_risk
                    + 0.6 * observed_simulation_risk

guardrails.md §5:
  Team_Risk_Summary 또는 Evidence_Metadata에 근거가 있고
  simulation log에서 concern/dependency/unresolved로 관찰된 경우에만 CONFIRMED.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EvaluationStatus(StrEnum):
    CONFIRMED = "confirmed"   # 근거 + 관찰 모두 확인 → 확정 issue
    CANDIDATE = "candidate"   # 관찰만 있음 / 근거 없음 → Phase 9에서 재심사
    INVALID   = "invalid"     # 근거 없는 우려 → 기각


class ConfirmedIssue(BaseModel):
    """단일 확정/후보 이슈.

    rules.md §4 분석 기준을 따라 root_cause, affected_roles, suggested_action을
    도출하며 guardrails §6 금지 표현을 준수한다.
    """

    model_config = ConfigDict(extra="forbid")

    issue_id:   str
    issue_category: str        # rules.md §2 9개 카테고리 중 하나

    # 점수 구성
    pre_simulation_risk:       float = Field(ge=0.0, le=1.0, default=0.0)
    observed_simulation_risk:  float = Field(ge=0.0, le=1.0, default=0.0)
    final_issue_score:         float = Field(ge=0.0, le=1.0, default=0.0)

    severity:        str        # high / medium / low
    status:          EvaluationStatus

    # 분석 내용
    root_cause:      str        = ""
    affected_roles:  list[str]  = Field(default_factory=list)
    suggested_action: str       = ""

    # 근거 추적
    evidence_refs:         list[str] = Field(default_factory=list)
    observed_in_phases:    list[str] = Field(default_factory=list)
    source_risk_tags:      list[str] = Field(
        default_factory=list,
        description="이 issue를 트리거한 Team_Risk_Summary risk_tags",
    )
    unresolved_question_ids: list[str] = Field(default_factory=list)


class IssueRiskSummary(BaseModel):
    """Issue_Risk_Summary.json 전체 구조.

    Phase 9 Score Calculator의 직접 입력.
    guardrails §7: 직원 실명·개인정보·원천 메시지 미포함.
    """

    model_config = ConfigDict(extra="forbid")

    simulation_id: str
    team_id:       str

    confirmed_issues: list[ConfirmedIssue] = Field(default_factory=list)
    candidate_issues: list[ConfirmedIssue] = Field(default_factory=list)
    invalid_issues:   list[ConfirmedIssue] = Field(default_factory=list)

    # 통계 (model_post_init에서 자동 계산)
    total_confirmed:  int = 0
    total_candidate:  int = 0
    total_invalid:    int = 0
    high_count:       int = 0
    medium_count:     int = 0
    low_count:        int = 0

    def model_post_init(self, __context) -> None:
        all_issues = self.confirmed_issues + self.candidate_issues
        object.__setattr__(self, "total_confirmed", len(self.confirmed_issues))
        object.__setattr__(self, "total_candidate",  len(self.candidate_issues))
        object.__setattr__(self, "total_invalid",    len(self.invalid_issues))
        object.__setattr__(self, "high_count",   sum(1 for i in all_issues if i.severity == "high"))
        object.__setattr__(self, "medium_count", sum(1 for i in all_issues if i.severity == "medium"))
        object.__setattr__(self, "low_count",    sum(1 for i in all_issues if i.severity == "low"))
