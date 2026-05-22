import type { RequirementsSummary } from "../types"

export const MOCK_REQUIREMENTS: RequirementsSummary = {
  project_name: "결제 및 사용자 관리 플랫폼 v1.0",
  project_summary:
    "이메일 기반 인증, 결제 API 연동, 메인 대시보드를 포함하는 14일 스프린트 MVP. " +
    "외부 결제 API(PG사) 의존성이 높고 GCP Cloud Run 배포가 필수다.",
  required_roles: ["PM", "Backend Developer", "Frontend Developer", "QA Engineer", "DevOps Engineer"],
  required_skills: ["Python", "FastAPI", "PostgreSQL", "React", "TypeScript", "Payment API", "GCP Cloud Run", "Docker", "Pytest", "CI/CD"],
  features: [
    {
      feature_id: "feat_001",
      feature_name: "이메일 로그인",
      priority: "P0",
      assigned_role: "Backend Developer",
      estimated_days: 3,
      dependencies: [],
      risk_notes: "인증 플로우 미확정 시 FE 연동 블로킹",
    },
    {
      feature_id: "feat_002",
      feature_name: "결제 API 연동",
      priority: "P0",
      assigned_role: "Backend Developer",
      estimated_days: 4,
      dependencies: ["feat_001"],
      risk_notes: "외부 PG사 sandbox 응답 지연 가능성",
    },
    {
      feature_id: "feat_003",
      feature_name: "메인 대시보드 UI",
      priority: "P0",
      assigned_role: "Frontend Developer",
      estimated_days: 3,
      dependencies: ["feat_001"],
    },
    {
      feature_id: "feat_004",
      feature_name: "사용자 프로필 편집",
      priority: "P1",
      assigned_role: "Frontend Developer",
      estimated_days: 2,
      dependencies: ["feat_001"],
    },
    {
      feature_id: "feat_005",
      feature_name: "알림 시스템",
      priority: "P1",
      assigned_role: "Backend Developer",
      estimated_days: 2,
      dependencies: ["feat_001"],
    },
    {
      feature_id: "feat_006",
      feature_name: "로그 내보내기",
      priority: "P2",
      assigned_role: "Backend Developer",
      estimated_days: 1,
    },
    {
      feature_id: "feat_007",
      feature_name: "다크모드 토글",
      priority: "P2",
      assigned_role: "Frontend Developer",
      estimated_days: 1,
    },
  ],
  timeline_days: 14,
  milestones: [
    { label: "Kickoff",     day: 1  },
    { label: "Design",      day: 3  },
    { label: "Development", day: 10 },
    { label: "QA",          day: 14 },
  ],
  risk_flags: [
    "외부 PG API 의존",
    "14일 일정 촉박",
    "FE-BE 스펙 동기화",
    "GCP Cloud Run 경험 부족",
  ],
  confidence: 92,
}
