"""``/jira`` HTTP routes."""

from fastapi import APIRouter, Query

from backend.api.deps import DbSession
from backend.api.pagination import Paginated, PaginationParams
from backend.core.schemas import JiraActivity as JiraActivitySchema
from backend.db.repositories.jira_activity import JiraActivityRepository

router = APIRouter(prefix="/jira", tags=["jira"])


@router.get(
    "/activities",
    response_model=Paginated[JiraActivitySchema],
    summary="List Jira activity rows (paginated, optional jira_account_id filter)",
)
def list_jira_activities(
    db: DbSession,
    page: PaginationParams,
    jira_account_id: str | None = Query(
        default=None,
        description="HR ``employees.jira_account_id``과 동일. 지정 시 해당 사용자 1행 반환.",
    ),
) -> Paginated[JiraActivitySchema]:
    repo = JiraActivityRepository(db)
    total = repo.count_filtered(jira_account_id=jira_account_id)
    rows = repo.list_paged(limit=page.limit, offset=page.offset, jira_account_id=jira_account_id)
    return Paginated[JiraActivitySchema](
        total=total,
        limit=page.limit,
        offset=page.offset,
        items=[JiraActivitySchema.model_validate(row) for row in rows],
    )
