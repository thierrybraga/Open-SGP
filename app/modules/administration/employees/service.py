"""
Arquivo: app/modules/administration/employees/service.py

Responsabilidade:
Lógica de negócio para Employees.
"""

from sqlalchemy.orm import Session
from datetime import date

from .models import Employee
from .schemas import EmployeeCreate, EmployeeUpdate


def create_employee(db: Session, data: EmployeeCreate) -> Employee:
    """
    Cria um funcionário.
    """
    employee = Employee(**data.dict())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def update_employee(db: Session, employee: Employee, data: EmployeeUpdate) -> Employee:
    """
    Atualiza um funcionário.
    """
    for field, value in data.dict(exclude_none=True).items():
        setattr(employee, field, value)

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def terminate_employee(db: Session, employee: Employee, termination_date: date, reason: str = None) -> Employee:
    """
    Desliga um funcionário.
    """
    employee.termination_date = termination_date
    employee.status = "terminated"
    employee.is_active = False

    if reason:
        notes = employee.notes or ""
        employee.notes = f"{notes}\n\nTermination: {termination_date.isoformat()} - {reason}".strip()

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def reactivate_employee(db: Session, employee: Employee) -> Employee:
    """
    Reativa um funcionário desligado.
    """
    employee.termination_date = None
    employee.status = "active"
    employee.is_active = True

    notes = employee.notes or ""
    employee.notes = f"{notes}\n\nReactivated: {date.today().isoformat()}".strip()

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def get_active_employees(db: Session) -> list[Employee]:
    """
    Retorna funcionários ativos.
    """
    return db.query(Employee).filter(
        Employee.is_active == True,
        Employee.status == "active"
    ).all()


def get_employees_by_department(db: Session, department: str) -> list[Employee]:
    """
    Retorna funcionários de um departamento.
    """
    return db.query(Employee).filter(
        Employee.department == department,
        Employee.is_active == True
    ).all()
