import csv
import pathlib

base = pathlib.Path("c:/workspace/ai-org-simulation/datasets/raw")
target_ids = {"E20260014", "E20260037", "E20260038", "E20260087", "E20260040"}


def load_by_key(path, key_col):
    with open(path, encoding="utf-8-sig") as f:
        return {r[key_col]: r for r in csv.DictReader(f)}


hr_map = load_by_key(base / "hr/employee_dummy_100.csv", "employee_id")
gh_map = load_by_key(base / "github/github_activity_dummy_100.csv", "github_id")
jira_map = load_by_key(base / "jira/jira_activity_dummy_100.csv", "jira_account_id")
slack_map = load_by_key(base / "slack/slack_activity_dummy_100.csv", "slack_user_id")
cal_map = load_by_key(base / "calendar/google_calendar_activity_dummy_100.csv", "google_email")

for eid in sorted(target_ids):
    hr = hr_map[eid]
    gh = gh_map.get(hr["github_id"], {})
    ji = jira_map.get(hr["jira_account_id"], {})
    sl = slack_map.get(hr["slack_user_id"], {})
    ca = cal_map.get(hr["google_email"], {})

    name = hr["employee_name"]
    code = hr["job_category_code"]
    print(f"=== {eid} {name} ({code}) ===")
    print(
        f"  github_id={hr['github_id']}  slack_user_id={hr['slack_user_id']}  jira_account_id={hr['jira_account_id']}"
    )
    print(
        f"  hr        : performance={hr['performance_score']}, turnover_risk={hr['turnover_risk_score']}, overtime={hr['overtime_hours_12m']}"
    )
    print(
        f"  jira      : overdue={ji.get('overdue_issue_count')}, worklog={ji.get('worklog_hours')}, sprint_rate={ji.get('sprint_completion_rate')}, autonomy={ji.get('autonomy_score')}, reopened={ji.get('reopened_issue_count')}, scope_change={ji.get('scope_change_count')}, avg_cycle={ji.get('avg_cycle_time')}, bottleneck={ji.get('bottleneck_risk')}"
    )
    print(
        f"  github    : pr={gh.get('pr_count_3m')}, merged={gh.get('merged_pr_count_3m')}, repos={gh.get('repository_contribution_count')}, contributed={gh.get('contributed_repositories')}"
    )
    print(
        f"  slack     : msg={sl.get('message_count')}, response_time={sl.get('avg_response_time')}, style={sl.get('collaboration_style')}, leadership={sl.get('leadership_score')}, bottleneck={sl.get('bottleneck_risk')}"
    )
    print(
        f"  calendar  : busy={ca.get('busy_minutes')}, focus={ca.get('focus_time_minutes')}, avg_meeting={ca.get('avg_meeting_duration_minutes')}, total_meeting={ca.get('total_meeting_minutes')}"
    )
    print()
