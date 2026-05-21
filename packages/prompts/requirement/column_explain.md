# Column Dictionary — HR Database

이 문서는 우리 시스템에서 사용하는 직원 데이터 컬럼의 **의미와 도메인 어휘**를 정의합니다.

- 모든 LLM 에이전트(`requirement-agent`, `persona-agent`, `team-builder-agent` 등)는 이 어휘로 PRD/요청을 해석해야 합니다.
- DB 컬럼, Pydantic 스키마, 프롬프트가 **동일한 단어**를 사용하도록 강제하기 위한 단일 진실 공급원(SSOT)입니다.
- 다른 데이터셋(GitHub/Slack/Jira/Calendar)이 추가되면 같은 형식으로 별도 섹션을 만듭니다.

## HR 데이터 (`datasets/raw/hr/`)

### 식별자

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `employee_id` | `str` (예: `E20260008`) | 직원 고유 ID, **PK** |

### 기본 정보

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `employee_name` | `str` | 직원 이름 |
| `gender` | enum `F`/`M`/`Non-disclosed` | 성별 (`Non-disclosed`는 응답 거부) |
| `birth_date` | `date` (YYYY-MM-DD) | 생년월일 |
| `age` | `int` | 나이 — `birth_date`에서 파생되지만 데이터 일관성 검증용으로 함께 저장 |

### 재직 정보

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `hire_date` | `date` | 입사일 |
| `tenure_years` | `float` | 근속연수 — `hire_date`에서 파생 |
| `employment_status` | enum `재직`/`휴직`/`퇴직예정`/`퇴직` | 재직 상태 |
| `employment_type` | enum `정규직`/`계약직`/`인턴` | 고용 형태 |

### 조직/직무

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `department` | enum `디자인`/`개발`/`QA 테스트` | 한국어 부서명 |
| `team` | `str` | 자유 텍스트 (예: `UI디자인`, `모바일개발`, `서비스QA`) |
| `job_family` | enum `Design`/`Software Engineering`/`QA Engineering`/`Infrastructure` | 영문 직무군 (LLM 매칭/표준화용) |
| `job_title` | `str` | 직책/직급명 (예: `리드`, `시니어매니저`, `사원`, `UI 디자이너`) |
| `job_level` | enum `L1`~`L6` | 내부 직급 레벨 (L1이 가장 낮고 L6이 가장 높음) |
| `manager_id` | `str?` (FK → `employee_id`) | 상위 관리자의 `employee_id`. **CEO/최상위 직급은 null** |

### 근무 정보

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `work_location` | `str` | 주 근무 장소 (예: `서울 본사`, `판교 오피스`, `원격`, `부산 지사`) |
| `remote_work_days_12m` | `int` | 최근 12개월 재택근무 일수 |

### 역량/배경

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `education_level` | enum `전문학사`/`학사`/`석사`/`박사` | 최종 학력 |
| `training_hours_12m` | `int` | 최근 12개월 사내/사외 교육 이수 시간 |
| `certifications_count` | `int` | 보유 자격증 개수 |

### 보상

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `base_salary_krw` | `int` | 연봉 (KRW, 세전) |
| `bonus_krw` | `int` | 직전 사이클 성과금 (KRW) |

### 성과/평가

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `last_performance_rating` | enum `S`/`A`/`B`/`C`/`D` | 최근 성과 등급 (S가 최상) |
| `performance_score` | `float` | 종합 성과 점수 (0~100) |
| `kpi_score` | `float` | KPI 목표 달성률 점수 |
| `okr` | `str` | 분기 OKR 핵심 목표 (자유 텍스트) |
| `competency_score` | `float` | 역량 평가 점수 |
| `peer_review_score` | `float` | 동료 평가 점수 |
| `manager_review_score` | `float` | 관리자 평가 점수 |
| `self_review_score` | `float` | 자기 평가 점수 |

### 승진

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `promotion_eligible` | `bool` (CSV: `Y`/`N`) | 다음 사이클 승진 대상 여부 |
| `promotion_recommended` | `bool` (CSV: `Y`/`N`) | 매니저 승진 추천 여부 |
| `last_promotion_date` | `date?` | 최근 승진일. 입사 후 한 번도 승진 없으면 null |

### 조직 상태 / 근태 / 리스크

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `engagement_score` | `float` | 직원 몰입도(Engagement) 점수 |
| `absence_days_12m` | `int` | 최근 12개월 결근 일수 |
| `overtime_hours_12m` | `int` | 최근 12개월 초과 근무 시간 |
| `disciplinary_actions_12m` | `int` | 최근 12개월 징계 횟수 |
| `turnover_risk_score` | `float` | 이직 위험 점수 (높을수록 이탈 가능성↑) |

### 외부 툴 계정 ID (다른 DB와의 조인 키)

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `github_id` | `str?` | GitHub 사용자 핸들 — `datasets/raw/github/` 데이터와 조인 |
| `slack_user_id` | `str?` | Slack 사용자 ID — `datasets/raw/slack/` 데이터와 조인 |
| `jira_account_id` | `str?` | Jira 계정 ID — `datasets/raw/jira/` 데이터와 조인 |
| `google_calendar_id` | `str?` | Calendar 계정/이메일 — `datasets/raw/calendar/` 데이터와 조인 |

## 도메인 어휘 가이드

LLM 에이전트가 PRD/요청에서 사용자 표현을 표준 컬럼으로 매핑할 때 참고할 동의어/연관어:

- **"시니어 백엔드"** → `job_family = "Software Engineering"` AND `job_level >= L4`
- **"리더십"** → `job_title` 또는 `team` 내 리드/매니저/시니어매니저 직책
- **"안정적인 사람"** → `turnover_risk_score` 낮음, `tenure_years` 김, `disciplinary_actions_12m = 0`
- **"성과가 높은 사람"** → `last_performance_rating ∈ {S, A}` AND `performance_score` 상위
- **"협업이 좋은 사람"** → `peer_review_score`, `engagement_score` 상위
- **"몰입도 낮음"** → `engagement_score` 하위 또는 `absence_days_12m` 높음
- **"재택 가능 인원"** → `work_location = "원격"` 또는 `remote_work_days_12m` 상위
