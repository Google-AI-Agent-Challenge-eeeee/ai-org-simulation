"""``/calendar`` HTTP routes."""

from fastapi import APIRouter, Query

from backend.api.deps import DbSession
from backend.api.pagination import Paginated, PaginationParams
from backend.core.schemas import CalendarActivity as CalendarActivitySchema
from backend.db.repositories.calendar_activity import CalendarActivityRepository

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get(
    "/activities",
    response_model=Paginated[CalendarActivitySchema],
    summary="List Calendar activity rows (paginated, optional google_email filter)",
)
def list_calendar_activities(
    db: DbSession,
    page: PaginationParams,
    google_email: str | None = Query(
        default=None,
        description=(
            "HR ``employees.google_email``과 동일. 지정 시 해당 사용자가 가진 "
            "모든 캘린더 행을 반환."
        ),
    ),
) -> Paginated[CalendarActivitySchema]:
    repo = CalendarActivityRepository(db)
    total = repo.count_filtered(google_email=google_email)
    rows = repo.list_paged(limit=page.limit, offset=page.offset, google_email=google_email)
    return Paginated[CalendarActivitySchema](
        total=total,
        limit=page.limit,
        offset=page.offset,
        items=[CalendarActivitySchema.model_validate(row) for row in rows],
    )
