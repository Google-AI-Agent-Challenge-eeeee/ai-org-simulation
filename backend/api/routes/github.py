"""``/github`` HTTP routes."""

from fastapi import APIRouter, Query

from backend.api.deps import DbSession
from backend.api.pagination import Paginated, PaginationParams
from backend.core.schemas import GithubActivity as GithubActivitySchema
from backend.db.repositories.github_activity import GithubActivityRepository

router = APIRouter(prefix="/github", tags=["github"])


@router.get(
    "/activities",
    response_model=Paginated[GithubActivitySchema],
    summary="List GitHub activity rows (paginated, optional github_id filter)",
)
def list_github_activities(
    db: DbSession,
    page: PaginationParams,
    github_id: str | None = Query(
        default=None,
        description="HR ``employees.github_id``과 동일. 지정 시 해당 사용자의 모든 측정 기간을 반환.",
    ),
) -> Paginated[GithubActivitySchema]:
    repo = GithubActivityRepository(db)
    total = repo.count_filtered(github_id=github_id)
    rows = repo.list_paged(limit=page.limit, offset=page.offset, github_id=github_id)
    return Paginated[GithubActivitySchema](
        total=total,
        limit=page.limit,
        offset=page.offset,
        items=[GithubActivitySchema.model_validate(row) for row in rows],
    )
