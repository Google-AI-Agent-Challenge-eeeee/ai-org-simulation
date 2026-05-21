"""GithubActivity Pydantic schema.

직원 한 명 × 측정 구간(`measured_from` ~ `measured_to`) 한 줄.
CSV(`datasets/raw/github/`)와 향후 ORM에서 동일한 형태로 검증된다.

CSV 특이사항:
    - ``contributed_repositories``는 ``;``로 구분된 문자열로 들어온다. ``BeforeValidator``로
      자동으로 ``list[str]``으로 분해하고, 양쪽 공백은 제거한다.
    - ``error_message``는 성공 시 빈 문자열이라 ``None``으로 정규화.
    - ``fetched_at``은 타임존 포함 ISO8601 (`...+09:00`). Pydantic이 자동 파싱한다.
"""

from datetime import date, datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from backend.core.schemas.enums import FetchStatus


def _empty_to_none(value: Any) -> Any:  # noqa: ANN401
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _split_repositories(value: Any) -> Any:  # noqa: ANN401
    """Accept ``"a;b;c"`` or ``["a", "b"]``; emit clean ``list[str]``."""

    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if not value.strip():
            return []
        return [part.strip() for part in value.split(";") if part.strip()]
    raise TypeError(f"Cannot coerce {type(value).__name__} into repository list")


OptionalStr = Annotated[str | None, BeforeValidator(_empty_to_none)]
RepositoryList = Annotated[list[str], BeforeValidator(_split_repositories)]


class GithubActivity(BaseModel):
    """A single GitHub activity snapshot for one employee over one window."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
        extra="forbid",
    )

    github_id: str

    measured_from: date
    measured_to: date

    commit_count_3m: int = Field(ge=0)
    pr_count_3m: int = Field(ge=0)
    merged_pr_count_3m: int = Field(ge=0)
    closed_unmerged_pr_count_3m: int = Field(ge=0)
    repository_contribution_count: int = Field(ge=0)
    contributed_repositories: RepositoryList = []

    fetched_at: datetime
    fetch_status: FetchStatus
    error_message: OptionalStr = None
