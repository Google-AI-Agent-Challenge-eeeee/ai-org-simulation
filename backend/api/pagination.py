"""``?limit=&offset=`` pagination — query params + generic response wrapper.

Keep it dead simple: offset/limit is cheap to reason about, and 100~500 row
datasets don't justify cursor-based paging yet. Revisit when a domain grows
past ~10k rows or needs stable ordering across concurrent writes.
"""

from typing import Annotated, Generic, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Pagination(BaseModel):
    """Request-side params. Caps ``limit`` at 200 to bound query cost."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


def pagination_params(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Pagination:
    return Pagination(limit=limit, offset=offset)


PaginationParams = Annotated[Pagination, Depends(pagination_params)]


class Paginated(BaseModel, Generic[T]):
    """Response wrapper carrying enough metadata for clients to fetch next page.

    ``total`` is the filtered count (not the table count) so UIs can show
    "1-50 of 87".
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    items: list[T]
