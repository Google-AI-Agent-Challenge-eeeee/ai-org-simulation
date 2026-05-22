"""``/slack`` HTTP routes."""

from fastapi import APIRouter, Query

from backend.api.deps import DbSession
from backend.api.pagination import Paginated, PaginationParams
from backend.core.schemas import SlackActivity as SlackActivitySchema
from backend.db.repositories.slack_activity import SlackActivityRepository

router = APIRouter(prefix="/slack", tags=["slack"])


@router.get(
    "/activities",
    response_model=Paginated[SlackActivitySchema],
    summary="List Slack activity rows (paginated, optional slack_user_id filter)",
)
def list_slack_activities(
    db: DbSession,
    page: PaginationParams,
    slack_user_id: str | None = Query(
        default=None,
        description="HR ``employees.slack_user_id``과 동일. 지정 시 해당 사용자 1행 반환.",
    ),
) -> Paginated[SlackActivitySchema]:
    repo = SlackActivityRepository(db)
    total = repo.count_filtered(slack_user_id=slack_user_id)
    rows = repo.list_paged(limit=page.limit, offset=page.offset, slack_user_id=slack_user_id)
    return Paginated[SlackActivitySchema](
        total=total,
        limit=page.limit,
        offset=page.offset,
        items=[SlackActivitySchema.model_validate(row) for row in rows],
    )
