"""``/employees/{id}/profile`` — HR + 4 activity domains in one response.

Done as 4 sequential lookups instead of one JOIN: the dataset is small (5
tables x 100 rows), JOINs across array/JSONB columns add noise, and the
per-domain repositories are already battle-tested. Revisit when QPS demands.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.deps import DbSession
from backend.core.schemas import (
    CalendarActivity as CalendarActivitySchema,
)
from backend.core.schemas import (
    Employee as EmployeeSchema,
)
from backend.core.schemas import (
    GithubActivity as GithubActivitySchema,
)
from backend.core.schemas import (
    JiraActivity as JiraActivitySchema,
)
from backend.core.schemas import (
    SlackActivity as SlackActivitySchema,
)
from backend.db.repositories.calendar_activity import CalendarActivityRepository
from backend.db.repositories.employee import EmployeeRepository
from backend.db.repositories.github_activity import GithubActivityRepository
from backend.db.repositories.jira_activity import JiraActivityRepository
from backend.db.repositories.slack_activity import SlackActivityRepository

router = APIRouter(prefix="/employees", tags=["employees"])


class EmployeeProfile(BaseModel):
    """Aggregated HR + activity view for one employee.

    Activity sections are nullable / list-valued depending on each domain's
    cardinality:

    - ``github`` / ``calendar``: a user can have multiple rows (history /
      multiple calendars) -> list
    - ``slack`` / ``jira``: at most one current-snapshot row per user -> nullable single

    Missing external IDs on the employee (e.g. ``github_id is None``) skip
    that domain entirely (returns ``[]`` or ``None``) — no error.
    """

    employee: EmployeeSchema
    github: list[GithubActivitySchema] = Field(default_factory=list)
    slack: SlackActivitySchema | None = None
    jira: JiraActivitySchema | None = None
    calendar: list[CalendarActivitySchema] = Field(default_factory=list)


@router.get(
    "/{employee_id}/profile",
    response_model=EmployeeProfile,
    summary="Aggregated profile: HR + GitHub + Slack + Jira + Calendar",
    responses={404: {"description": "Employee not found"}},
)
def get_employee_profile(employee_id: str, db: DbSession) -> EmployeeProfile:
    employee = EmployeeRepository(db).get(employee_id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"employee_id {employee_id!r} not found",
        )

    github_rows = (
        GithubActivityRepository(db).list_for_user(employee.github_id)
        if employee.github_id is not None
        else []
    )
    slack_row = (
        SlackActivityRepository(db).get(employee.slack_user_id)
        if employee.slack_user_id is not None
        else None
    )
    jira_row = (
        JiraActivityRepository(db).get(employee.jira_account_id)
        if employee.jira_account_id is not None
        else None
    )
    calendar_rows = (
        CalendarActivityRepository(db).list_for_user(employee.google_email)
        if employee.google_email is not None
        else []
    )

    return EmployeeProfile(
        employee=EmployeeSchema.model_validate(employee),
        github=[GithubActivitySchema.model_validate(r) for r in github_rows],
        slack=SlackActivitySchema.model_validate(slack_row) if slack_row else None,
        jira=JiraActivitySchema.model_validate(jira_row) if jira_row else None,
        calendar=[CalendarActivitySchema.model_validate(r) for r in calendar_rows],
    )
