"""Employee repository — CRUD over the ``employees`` table.

Intentionally minimal in Phase 2. Once the API layer needs filtering /
pagination / bulk upsert, add purpose-built methods here instead of pushing
query logic into routes.
"""

from collections.abc import Iterable, Sequence

from sqlalchemy import select
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

    def count(self) -> int:
        stmt = select(Employee)
        return len(self._session.execute(stmt).scalars().all())

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
