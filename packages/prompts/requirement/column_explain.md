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
| `department` | enum `디자인`/`개발`/`QA 테스트` | 한국어 본부/부서명 (조직도 단위) |
| `job_category_code` | enum `DS`/`BE`/`WEB`/`Android`/`iOS`/`Mobile`/`Infra`/`QA` | 실 업무 직무 코드. `department`보다 한 단계 세분화 (예: `department=개발` AND `job_category_code∈{BE, WEB, Android, iOS, Mobile, Infra}`) |
| `manager_id` | `str?` (FK → `employee_id`) | 상위 관리자의 `employee_id`. **CEO/최상위 직급은 null** |

`job_category_code` 의미:

- `DS` — Design System / 디자인
- `BE` — Backend
- `WEB` — Web frontend
- `Android` / `iOS` — 네이티브 모바일
- `Mobile` — 모바일 공통/교차 영역
- `Infra` — Infrastructure / DevOps / SRE
- `QA` — Quality Assurance

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
| `google_email` | `str?` | Google 계정 이메일 — `datasets/raw/calendar/` 데이터와 조인 |

## GitHub 활동 데이터 (`datasets/raw/github/`)

직원 한 명당 **측정 기간(`measured_from` ~ `measured_to`) 한 구간 = 1행**. 같은 직원의 다른 분기는 행이 늘어난다(append-only). HR 데이터와는 `github_id`로 조인한다.

### 식별자 / 측정 구간

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `github_id` | `str` (예: `gh-emp-0008`) | GitHub 핸들 — HR `employees.github_id`와 조인 키 |
| `measured_from` | `date` (YYYY-MM-DD) | 활동 집계 시작일 (구간의 시작, 포함) |
| `measured_to` | `date` (YYYY-MM-DD) | 활동 집계 종료일 (구간의 끝, 포함) |

### 활동 메트릭 (집계 구간 = 직전 90일)

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `commit_count_3m` | `int ≥ 0` | 구간 내 작성한 커밋 수 (저자 기준) |
| `pr_count_3m` | `int ≥ 0` | 구간 내 생성한 Pull Request 수 |
| `merged_pr_count_3m` | `int ≥ 0` | 그중 머지된 PR 수 |
| `closed_unmerged_pr_count_3m` | `int ≥ 0` | 그중 머지되지 않고 닫힌 PR 수 |
| `repository_contribution_count` | `int ≥ 0` | 구간 내 commit/PR을 남긴 고유 repo 수 |
| `contributed_repositories` | `list[str]` | 활동한 repo 풀네임 목록 (CSV에서는 `;` 구분 문자열) |

### 수집 메타데이터

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `fetched_at` | `datetime` (tz-aware ISO8601) | GitHub API 조회 시각 |
| `fetch_status` | enum `success`/`failed` | 조회 성공 여부 |
| `error_message` | `str?` | 실패 시 사유, 성공 시 `None` (CSV 빈 문자열은 `None`으로 정규화) |

### 도메인 어휘 (LLM 매핑용)

- **"활발한 개발자"** → `commit_count_3m`, `pr_count_3m` 상위
- **"코드 리뷰 통과율 높음"** → `merged_pr_count_3m / pr_count_3m` 비율 높음
- **"여러 프로젝트 기여"** → `repository_contribution_count` 큰 값
- **"GitHub 활동 없음"** → 해당 직원의 행이 없거나 모든 카운트가 0
- **"수집 실패 직원"** → `fetch_status = "failed"` (지표로 쓰면 안 되는 행)

## Slack 활동 데이터 (`datasets/raw/slack/`)

직원 한 명당 **현재 측정 구간 한 줄 = 1행** (PK는 `slack_user_id`). HR 데이터와는 `slack_user_id`로 조인한다. GitHub와 달리 append-only가 아니고 "최신 스냅샷"이며, 미래에 시계열로 바꾸려면 PK를 (`slack_user_id`, `measured_from`)로 확장하면 된다.

대다수 컬럼은 LLM 평가 모델/룰 기반으로 산출되는 **파생 지표**다. 컬럼 설명 옆 `derived`는 "원본 이벤트가 아니라 가공된 점수"라는 의미.

### 식별자 / 측정 구간

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `slack_user_id` | `str` (예: `U00000008`) | Slack 사용자 ID, **PK** — HR `employees.slack_user_id`와 조인 키 |
| `measured_from` | `date` | 활동 집계 시작일 |
| `measured_to` | `date` | 활동 집계 종료일 |

### 대화/메시지 활동

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `accessible_conversations` | `int ≥ 0` | 앱이 접근 가능한 채널/DM 수 |
| `user_conversations` | `list[str]` | 사용자가 속한 채널 ID 목록 (CSV는 `;` 구분) |
| `conversation_members` | `int ≥ 0` | 사용자가 속한 대화의 멤버 수 요약값 |
| `message_count` | `int ≥ 0` | 집계 기간 메시지 수 |
| `message_events` | `int ≥ 0` | 원천 이벤트 수 (현재 더미는 `message_count`와 동일, 실제 수집 시 분리 가능) |
| `thread_replies` | `int ≥ 0` | 스레드 답글 수 |
| `mention_count` | `int ≥ 0` | 타인 멘션 횟수 |

### 상호작용 / 협업

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `collaboration_frequency` | `int ≥ 0` | 멘션·답글·공동 스레드 기반 협업 빈도 (derived) |
| `top_collaborators` | `list[str]` | 가장 자주 협업한 사용자 ID 목록 (CSV는 `;` 구분) |
| `avg_response_time` | `float` (분) | 평균 응답 시간 (derived) |
| `communication_balance` | `float` | 질문/응답 비율 — 1.0 부근이면 균형, 낮을수록 일방향 (derived) |

### 시간/리듬

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `active_hours` | `str` (`HH:MM-HH:MM`) | 주 활동 시간대 범위 (단순 문자열, 두 개 구간은 미지원) |
| `night_activity_ratio` | `float` 0~1 | 야간(22~06시) 메시지 비율 |

### 업무 스타일 / 네트워크 점수 (derived)

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `multitasking_score` | `float` | 여러 채널에서 동시에 활동하는 정도 |
| `leadership_score` | `float` | 커뮤니케이션 네트워크 중심성 점수 (평가용 직접 사용은 주의) |
| `dependency_score` | `float` | 특정 사용자에게 의존되는 정도 |
| `bottleneck_risk` | `float` | 요청 집중·응답 지연 기반 병목 가능성 |
| `collaboration_style` | enum (아래) | 메시지 패턴 기반 협업 성향 분류 |
| `autonomy_score` | `float` | 독립적으로 일하는 성향 추정 점수 |
| `burnout_risk` | `float` | 야간·장시간 활동 기반 번아웃 위험 (민감 지표 — UI 노출 시 careful) |
| `decision_latency` | `float` (시간) | 논의 시작부터 결정까지 소요 시간 (NLP/룰 기반) |

`collaboration_style` 값:

- `rapid_responder` — 답장이 빠르고 짧은 단편 위주
- `focused_individual` — 메시지가 적고 깊이 있는 응답
- `connector` — 멘션·답글 네트워크가 넓음
- `review_hub` — 리뷰/피드백을 자주 주고받음
- `async_deep_worker` — 야간·비동기 응답 비중이 높음

### 사용자 / 워크스페이스 컨텍스트

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `slack_user_profile` | `str` | `id=...;name=...;email=...` 형식 inline 프로필. 현 단계는 원문 보존, 필요 시 dict로 파싱 |
| `slack_users` | `int` | Slack 워크스페이스 전체 사용자 수 (정규화 시 분리 가능) |

### 수집 메타데이터

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `fetched_at` | `datetime` (tz-aware) | Slack API 조회 시각 |
| `fetch_status` | enum `success`/`failed` | 조회 성공 여부 — GitHub과 동일한 `FetchStatus` 재사용 |
| `error_message` | `str?` | 실패 시 사유, 성공 시 `None` |

### 도메인 어휘 (LLM 매핑용)

- **"커뮤니케이션 허브"** → `leadership_score`, `collaboration_frequency` 상위
- **"번아웃 위험"** → `burnout_risk` 상위 또는 `night_activity_ratio > 0.2`
- **"비동기 워커"** → `collaboration_style = "async_deep_worker"`
- **"빠른 응답자"** → `avg_response_time` 하위 또는 `collaboration_style = "rapid_responder"`
- **"병목 인물"** → `bottleneck_risk` 상위 + `dependency_score` 상위

## Jira 활동 데이터 (`datasets/raw/jira/`)

직원 한 명당 **현재 측정 구간 한 줄 = 1행** (Slack과 동일한 current-snapshot 패턴). HR 데이터와는 `jira_account_id`로 조인한다.

PK는 surrogate `id`, 외부 식별자 `jira_account_id`는 UNIQUE+INDEX. 시계열로 가고 싶다면 UNIQUE를 `(jira_account_id, measured_from)`으로 확장.

### 식별자 / 측정 구간

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `jira_account_id` | `str` (예: `jira-0008`) | Jira account ID — HR `employees.jira_account_id`와 조인 키 |
| `measured_from` | `date` | 활동 집계 시작일 |
| `measured_to` | `date` | 활동 집계 종료일 |

### 이슈 활동

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `assigned_issue_count` | `int ≥ 0` | 담당자로 배정된 이슈 수 |
| `reported_issue_count` | `int ≥ 0` | 요청자/보고자로 생성한 이슈 수 |
| `completed_issue_count` | `int ≥ 0` | 완료한 이슈 수 |
| `issue_type_mix` | `dict[str, float]` | 이슈 유형 분포 (값은 0~1 비율). CSV는 `"Type:48%;..."` 형식, 파싱 시 `{"Type": 0.48, ...}` |
| `priority_mix` | `dict[str, float]` | 우선순위 분포 (`Highest`/`High`/`Medium`/`Low` 키, 값 0~1) |

### 딜리버리 / 플래닝

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `avg_cycle_time` | `float` (일) | 이슈 생성부터 완료까지 평균 시간 |
| `overdue_issue_count` | `int ≥ 0` | 마감 초과 이슈 수 |
| `estimation_accuracy` | `float` (비율) | 추정 시간 ÷ 실제 시간. `1.0`이면 정확, `>1`이면 과대추정, `<1`이면 과소추정 |
| `worklog_hours` | `float` (시간) | worklog 기록 누적 (worklog 문화 있는 팀에서만 의미 있음) |

### 협업

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `comment_count` | `int ≥ 0` | 이슈 댓글 수 |
| `avg_comment_response_time` | `float` (시간) | 댓글 응답 평균 시간 |
| `collaboration_touchpoints` | `int ≥ 0` | 같은 이슈에서 협업한 고유 사용자 수 |

### 워크플로우

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `status_transition_count` | `int ≥ 0` | 이슈 상태 변경 횟수 |
| `avg_time_in_status` | `float` (시간) | 상태별 평균 체류 시간 |
| `reopened_issue_count` | `int ≥ 0` | 완료 후 재오픈된 이슈 수 (품질/명세 정확도 시그널) |
| `scope_change_count` | `int ≥ 0` | 주요 필드 변경 기반 범위 변경 횟수 |
| `task_breakdown_count` | `int ≥ 0` | 하위 작업으로 쪼갠 업무 수 |

### Agile / Sprint

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `sprint_participation` | `list[str]` | 참여 스프린트 ID 목록 (CSV는 `;` 구분) |
| `sprint_completion_rate` | `float` 0~1 | 스프린트 내 담당 이슈 완료율 |

### 업무 스타일 / 리스크 (derived)

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `context_switching_score` | `float` | 여러 이슈를 동시에 전환하는 정도 |
| `autonomy_score` | `float` | 단독 진행 비율 기반 독립 작업 성향 (Slack의 동명 컬럼과 의미 다름 — 도메인 격리됨) |
| `ownership_score` | `float` | 배정→완료까지 담당 유지율 + 완료율 기반 소유도 |
| `bottleneck_risk` | `float` | 미완료·고우선순위·체류 시간 기반 병목 가능성 |

### 수집 메타데이터

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `fetched_at` | `datetime` (tz-aware) | Jira API 조회 시각 |
| `fetch_status` | enum `success`/`failed` | `FetchStatus` 재사용 |
| `error_message` | `str?` | 실패 시 사유, 성공 시 `None` |

### 도메인 어휘 (LLM 매핑용)

- **"완료율 높은 사람"** → `completed_issue_count / assigned_issue_count` 상위
- **"버그 많이 잡는 사람"** → `issue_type_mix["Bug"]` 상위
- **"고난도 업무"** → `priority_mix["Highest"] + priority_mix["High"]` 상위
- **"마감 잘 지킴"** → `overdue_issue_count = 0` AND `sprint_completion_rate > 0.8`
- **"멀티태스킹 과한 사람"** → `context_switching_score` 상위
- **"오너십 강함"** → `ownership_score` 상위 AND `reopened_issue_count` 낮음
- **"병목"** → `bottleneck_risk` 상위 (Slack `bottleneck_risk`와 함께 보면 더 신뢰도)

## Google Calendar 활동 데이터 (`datasets/raw/calendar/`)

직원 한 명의 **특정 캘린더(보통 `primary`) × 측정 구간 = 1행**. HR 데이터와는 `google_email`로 조인한다.

PK는 surrogate `id`. 유니크 키는 `(google_email, calendar_id)` 복합 — 한 사람이 여러 캘린더(`primary` + 공유 캘린더)를 가질 수 있어 단일 컬럼이 아님.

### 식별자 / 측정 구간

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `google_email` | `str` | Google Workspace 이메일 — HR `employees.google_email`과 조인 키 |
| `calendar_id` | `str` | 분석 대상 캘린더 ID. 기본은 `"primary"` |
| `measured_from` | `date` | 활동 집계 시작일 |
| `measured_to` | `date` | 활동 집계 종료일 |

### 이벤트 활동

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `event_count` | `int ≥ 0` | 전체 일정 수 |
| `meeting_count` | `int ≥ 0` | 참석자/화상회의 정보 있는 회의성 일정 수 |
| `total_meeting_minutes` | `int ≥ 0` | 회의에 잡힌 총 시간 (분) |
| `avg_meeting_duration_minutes` | `float ≥ 0` | 평균 회의 길이 (분) |
| `all_day_event_count` | `int ≥ 0` | 종일 일정 수 |

### 스케줄 패턴

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `active_hours` | `str` (`HH:MM-HH:MM`) | 일정이 많이 잡히는 주 활동 시간대 |
| `early_late_meeting_ratio` | `float` 0~1 | 09시 이전 또는 18시 이후 회의 비율 |
| `weekend_meeting_ratio` | `float` 0~1 | 주말 회의 비율 |

### 집중 시간

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `focus_time_count` | `int ≥ 0` | 집중 시간 일정 수 (`eventType=focusTime`) |
| `focus_time_minutes` | `int ≥ 0` | 집중 시간 총량 (분) |
| `fragmented_calendar_score` | `float ≥ 0` | 일정이 잘게 쪼개진 정도 (derived) |
| `no_meeting_block_count` | `int ≥ 0` | 회의 없는 긴 작업 블록 수 (FreeBusy API 기반) |

### 협업

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `organizer_event_count` | `int ≥ 0` | 본인이 주최한 일정 수 |
| `attendee_event_count` | `int ≥ 0` | 본인이 참석자로 포함된 일정 수 |
| `organizer_ratio` | `float` 0~1 | 전체 회의 중 본인이 주최한 회의 비율 |
| `attendee_count_avg` | `float ≥ 0` | 회의별 평균 참석자 수 |
| `large_meeting_ratio` | `float` 0~1 | 대규모 회의 비율 (대규모 기준은 별도 정의) |
| `external_meeting_ratio` | `float` 0~1 | 외부 도메인 참석자 포함 회의 비율 |

### 응답 패턴

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `accepted_attendee_count` | `int ≥ 0` | 수락한 일정 수 |
| `declined_attendee_count` | `int ≥ 0` | 거절한 일정 수 |
| `tentative_attendee_count` | `int ≥ 0` | 미정으로 응답한 일정 수 |
| `no_response_ratio` | `float` 0~1 | 초대에 응답하지 않은 비율 |

### 반복 일정 / 가용성

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `recurring_event_count` | `int ≥ 0` | 반복 일정 수 |
| `recurring_meeting_ratio` | `float` 0~1 | 전체 회의 중 반복 회의 비율 |
| `busy_minutes` | `int ≥ 0` | 바쁨으로 잡힌 총 시간 (분, FreeBusy 기반) |

### 근무 위치

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `working_location_count` | `int ≥ 0` | 근무 위치 등록 횟수 |
| `working_location_mix` | `dict[str, float]` | 위치별 비율 (`home`/`office`/`other` 등 키, 값 0~1). CSV는 `"home:30%;..."` 형식 |

### 메타데이터

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `event_update_count` | `int ≥ 0` | 일정 수정 빈도 |
| `meeting_provider_mix` | `dict[str, float]` | 회의 도구 분포 (`Google Meet`/`Zoom`/`Microsoft Teams`/`In-person`/`Other` 등 키, 값 0~1) |

### 수집 메타데이터

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `fetched_at` | `datetime` (tz-aware) | Google Calendar API 조회 시각 |
| `fetch_status` | enum `success`/`failed` | `FetchStatus` 재사용 |
| `error_message` | `str?` | 실패 시 사유, 성공 시 `None` |

### 도메인 어휘 (LLM 매핑용)

- **"회의 많은 사람"** → `meeting_count` 상위 또는 `total_meeting_minutes` 상위
- **"회의에 시달리는 사람"** → `total_meeting_minutes` 상위 AND `focus_time_minutes` 하위
- **"집중 시간 잘 확보"** → `focus_time_minutes` 상위 또는 `no_meeting_block_count` 상위
- **"회의 주최자형"** → `organizer_ratio > 0.5`
- **"새벽/야간 회의 많음"** → `early_late_meeting_ratio` 상위 (Slack `night_activity_ratio`와 함께 보면 워라밸 시그널)
- **"주말 근무 잦음"** → `weekend_meeting_ratio > 0`
- **"외부 미팅 많음"** → `external_meeting_ratio` 상위 (영업/PM/리더십 시그널)
- **"재택 위주"** → `working_location_mix["home"] > 0.5`
- **"파편화된 일정"** → `fragmented_calendar_score` 상위 (생산성 저하 신호)

## 도메인 어휘 가이드

LLM 에이전트가 PRD/요청에서 사용자 표현을 표준 컬럼으로 매핑할 때 참고할 동의어/연관어:

- **"백엔드 개발자"** → `job_category_code = "BE"`
- **"프론트엔드 개발자"** → `job_category_code = "WEB"`
- **"모바일 개발자"** → `job_category_code ∈ {Android, iOS, Mobile}`
- **"시니어급"** → `tenure_years >= 5` 또는 `last_performance_rating ∈ {S, A}` (현재 스키마에는 명시적 레벨 컬럼 없음)
- **"리더십"** → 부하 직원이 있음 (`manager_id`로 본인을 가리키는 행이 존재)
- **"안정적인 사람"** → `turnover_risk_score` 낮음, `tenure_years` 김, `disciplinary_actions_12m = 0`
- **"성과가 높은 사람"** → `last_performance_rating ∈ {S, A}` AND `performance_score` 상위
- **"협업이 좋은 사람"** → `peer_review_score`, `engagement_score` 상위
- **"몰입도 낮음"** → `engagement_score` 하위 또는 `absence_days_12m` 높음
- **"재택 가능 인원"** → `work_location = "원격"` 또는 `remote_work_days_12m` 상위
