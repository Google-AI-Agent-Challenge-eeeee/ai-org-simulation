import type { TeamCandidate } from "../types"

const ROLE_COLORS: Record<string, string> = {
  PM: "bg-purple-500",
  "Backend Developer": "bg-blue-600",
  "Frontend Developer": "bg-cyan-500",
  "QA Engineer": "bg-amber-600",
  "DevOps Engineer": "bg-orange-500",
  "iOS Developer": "bg-slate-500",
}

function color(role: string) {
  return ROLE_COLORS[role] ?? "bg-zinc-500"
}

export const MOCK_TEAMS: TeamCandidate[] = [
  {
    team_id: "team_001",
    team_name: "알파 포메이션",
    team_rank: 1,
    team_fit_score: 94.2,
    role_coverage_score: 0.95,
    skill_coverage_score: 0.88,
    availability_score: 1.0,
    team_risk_flags: ["최유니: 일정 일부 충돌"],
    badges: ["최적 밸런스", "PM 추천"],
    rationale:
      "요구사항 대비 기술 스택 커버리지가 가장 우수합니다. 이전 유사 프로젝트에서 협업 경험이 있는 멤버(박준서, 이민수)가 포함되어 초기 지급 기간 단축이 예상됩니다.",
    skill_gaps: ["최유니: 일정 일부 충돌"],
    members: [
      { employee_id: "E001", employee_name: "김지은",  assigned_role: "PM",                 initials: "김지", color: color("PM") },
      { employee_id: "E002", employee_name: "박준서",  assigned_role: "Backend Developer",  initials: "박준", color: color("Backend Developer") },
      { employee_id: "E003", employee_name: "이민수",  assigned_role: "Frontend Developer", initials: "이민", color: color("Frontend Developer") },
      { employee_id: "E004", employee_name: "최유니",  assigned_role: "QA Engineer",        initials: "최유", color: color("QA Engineer") },
      { employee_id: "E005", employee_name: "청우진",  assigned_role: "DevOps Engineer",    initials: "청우", color: color("DevOps Engineer") },
    ],
  },
  {
    team_id: "team_002",
    team_name: "베타 신디케이트",
    team_rank: 2,
    team_fit_score: 88.5,
    role_coverage_score: 0.90,
    skill_coverage_score: 0.83,
    availability_score: 0.92,
    team_risk_flags: ["payment_api_integration_risk"],
    members: [
      { employee_id: "E011", employee_name: "권원솔",  assigned_role: "PM",                 initials: "권원", color: color("PM") },
      { employee_id: "E012", employee_name: "안우빈",  assigned_role: "Backend Developer",  initials: "안우", color: color("Backend Developer") },
      { employee_id: "E013", employee_name: "심예린",  assigned_role: "Frontend Developer", initials: "심예", color: color("Frontend Developer") },
      { employee_id: "E014", employee_name: "송다원",  assigned_role: "QA Engineer",        initials: "송다", color: color("QA Engineer") },
      { employee_id: "E015", employee_name: "박라경",  assigned_role: "DevOps Engineer",    initials: "박라", color: color("DevOps Engineer") },
    ],
  },
  {
    team_id: "team_003",
    team_name: "감마 코어",
    team_rank: 3,
    team_fit_score: 84.1,
    role_coverage_score: 0.88,
    skill_coverage_score: 0.79,
    availability_score: 0.71,
    team_risk_flags: ["가용성 리스크", "fe_scope_instability"],
    badges: ["가용성 리스크"],
    members: [
      { employee_id: "E021", employee_name: "이하준",  assigned_role: "PM",                 initials: "이하", color: color("PM") },
      { employee_id: "E022", employee_name: "정수빈",  assigned_role: "Backend Developer",  initials: "정수", color: color("Backend Developer") },
      { employee_id: "E023", employee_name: "윤채은",  assigned_role: "Frontend Developer", initials: "윤채", color: color("Frontend Developer") },
      { employee_id: "E024", employee_name: "김태양",  assigned_role: "QA Engineer",        initials: "김태", color: color("QA Engineer") },
      { employee_id: "E025", employee_name: "조민서",  assigned_role: "DevOps Engineer",    initials: "조민", color: color("DevOps Engineer") },
    ],
  },
  {
    team_id: "team_004",
    team_name: "델타 스쿼드",
    team_rank: 4,
    team_fit_score: 81.3,
    role_coverage_score: 0.85,
    skill_coverage_score: 0.77,
    availability_score: 0.88,
    team_risk_flags: ["backend_workload_concentration"],
    members: [
      { employee_id: "E031", employee_name: "나다운",  assigned_role: "PM",                 initials: "나다", color: color("PM") },
      { employee_id: "E032", employee_name: "오세준",  assigned_role: "Backend Developer",  initials: "오세", color: color("Backend Developer") },
      { employee_id: "E033", employee_name: "류지아",  assigned_role: "Frontend Developer", initials: "류지", color: color("Frontend Developer") },
      { employee_id: "E034", employee_name: "한소윤",  assigned_role: "QA Engineer",        initials: "한소", color: color("QA Engineer") },
      { employee_id: "E035", employee_name: "문기원",  assigned_role: "DevOps Engineer",    initials: "문기", color: color("DevOps Engineer") },
    ],
  },
  {
    team_id: "team_005",
    team_name: "엡실론 유닛",
    team_rank: 5,
    team_fit_score: 78.9,
    role_coverage_score: 0.82,
    skill_coverage_score: 0.74,
    availability_score: 0.85,
    team_risk_flags: ["pm_low_sprint_velocity"],
    members: [
      { employee_id: "E041", employee_name: "백서현",  assigned_role: "PM",                 initials: "백서", color: color("PM") },
      { employee_id: "E042", employee_name: "임재혁",  assigned_role: "Backend Developer",  initials: "임재", color: color("Backend Developer") },
      { employee_id: "E043", employee_name: "신유진",  assigned_role: "Frontend Developer", initials: "신유", color: color("Frontend Developer") },
      { employee_id: "E044", employee_name: "황지호",  assigned_role: "QA Engineer",        initials: "황지", color: color("QA Engineer") },
      { employee_id: "E045", employee_name: "고아름",  assigned_role: "DevOps Engineer",    initials: "고아", color: color("DevOps Engineer") },
    ],
  },
  ...Array.from({ length: 5 }, (_, i) => ({
    team_id: `team_00${6 + i}`,
    team_name: ["제타 클러스터", "에타 브리게이드", "세타 포스", "이오타 팀", "카파 그룹"][i],
    team_rank: 6 + i,
    team_fit_score: parseFloat((76.2 - i * 1.8).toFixed(1)),
    role_coverage_score: 0.80 - i * 0.02,
    skill_coverage_score: 0.72 - i * 0.02,
    availability_score: 0.80 - i * 0.03,
    team_risk_flags: ["skill_gap"],
    members: [
      { employee_id: `E0${5+i}1`, employee_name: `PM${6+i}`, assigned_role: "PM", initials: `P${6+i}`, color: color("PM") },
      { employee_id: `E0${5+i}2`, employee_name: `BE${6+i}`, assigned_role: "Backend Developer", initials: `B${6+i}`, color: color("Backend Developer") },
      { employee_id: `E0${5+i}3`, employee_name: `FE${6+i}`, assigned_role: "Frontend Developer", initials: `F${6+i}`, color: color("Frontend Developer") },
      { employee_id: `E0${5+i}4`, employee_name: `QA${6+i}`, assigned_role: "QA Engineer", initials: `Q${6+i}`, color: color("QA Engineer") },
      { employee_id: `E0${5+i}5`, employee_name: `DO${6+i}`, assigned_role: "DevOps Engineer", initials: `D${6+i}`, color: color("DevOps Engineer") },
    ],
  })),
]
