"""``/employees`` HTTP routes — read-only HR queries.

Phase 3 scope: list (filterable, paginated), get-by-id. The profile aggregate
(``/employees/{id}/profile``) lives in :mod:`backend.api.routes.profile`.
"""

from fastapi import APIRouter, HTTPException, Query, status

from backend.api.deps import DbSession
from backend.api.pagination import Paginated, PaginationParams
from backend.core.schemas import Employee as EmployeeSchema
from backend.core.schemas.enums import Department, JobCategoryCode
from backend.db.repositories.employee import EmployeeRepository

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get(
    "",
    response_model=Paginated[EmployeeSchema],
    summary="List employees (filterable, paginated)",
)
def list_employees(
    db: DbSession,
    page: PaginationParams,
    department: Department | None = Query(default=None, description="본부/부서 정확 일치 필터"),
    job_category_code: JobCategoryCode | None = Query(
        default=None, description="직무 카테고리 정확 일치 필터"
    ),
) -> Paginated[EmployeeSchema]:
    repo = EmployeeRepository(db)
    department_value = department.value if department is not None else None
    job_category_value = job_category_code.value if job_category_code is not None else None

    total = repo.count_filtered(
        department=department_value,
        job_category_code=job_category_value,
    )
    rows = repo.list_paged(
        limit=page.limit,
        offset=page.offset,
        department=department_value,
        job_category_code=job_category_value,
    )
    return Paginated[EmployeeSchema](
        total=total,
        limit=page.limit,
        offset=page.offset,
        items=[EmployeeSchema.model_validate(row) for row in rows],
    )


@router.get(
    "/{employee_id}",
    response_model=EmployeeSchema,
    summary="Get one employee by employee_id",
    responses={404: {"description": "Employee not found"}},
)
def get_employee(employee_id: str, db: DbSession) -> EmployeeSchema:
    repo = EmployeeRepository(db)
    employee = repo.get(employee_id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"employee_id {employee_id!r} not found",
        )
    return EmployeeSchema.model_validate(employee)
