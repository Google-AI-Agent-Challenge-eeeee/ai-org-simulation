"""Employee repository — CRUD over the ``employees`` table.

Intentionally minimal in Phase 2. Once the API layer needs filtering /
pagination / bulk upsert, add purpose-built methods here instead of pushing
query logic into routes.
"""

from collections.abc import Iterable, Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from backend.db.models.employee import Employee


class EmployeeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, employee_id: str) -> Employee | None:
        return self._session.get(Employee, employee_id)

    def list_all(self) -> Sequence[Employee]:
        stmt = select(Employee).order_by(Employee.employee_id)
        return self._session.execute(stmt).scalars().all()

    def list_paged(
        self,
        *,
        limit: int,
        offset: int,
        department: str | None = None,
        job_category_code: str | None = None,
    ) -> Sequence[Employee]:
        """Page of employees, optionally filtered by department / job category.

        Both filters are exact-match string comparisons (Pydantic enum values
        round-trip cleanly to the DB's String columns).
        """

        stmt = self._filtered_select(department, job_category_code)
        stmt = stmt.order_by(Employee.employee_id).limit(limit).offset(offset)
        return self._session.execute(stmt).scalars().all()

    def count_filtered(
        self,
        *,
        department: str | None = None,
        job_category_code: str | None = None,
    ) -> int:
        """Total rows matching the same filters as :py:meth:`list_paged`."""

        stmt = self._filtered_select(department, job_category_code)
        # COUNT(*) over the filtered subquery — cheap and avoids materialising rows.
        return self._session.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    @staticmethod
    def _filtered_select(
        department: str | None,
        job_category_code: str | None,
    ) -> Select[tuple[Employee]]:
        stmt = select(Employee)
        if department is not None:
            stmt = stmt.where(Employee.department == department)
        if job_category_code is not None:
            stmt = stmt.where(Employee.job_category_code == job_category_code)
        return stmt

    def count(self) -> int:
        return self._session.execute(select(func.count()).select_from(Employee)).scalar_one()

    def add(self, employee: Employee) -> Employee:
        self._session.add(employee)
        self._session.flush()
        return employee

    def add_many(self, employees: Iterable[Employee]) -> None:
        self._session.add_all(list(employees))
        self._session.flush()

    def delete(self, employee_id: str) -> bool:
        instance = self.get(employee_id)
        if instance is None:
            return False
        self._session.delete(instance)
        self._session.flush()
        return True
