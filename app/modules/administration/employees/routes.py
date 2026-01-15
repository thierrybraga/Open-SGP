"""
Arquivo: app/modules/administration/employees/routes.py

Responsabilidade:
Rotas REST para Employees.

Integrações:
- core.dependencies
- modules.administration.employees.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from datetime import date

from ....core.dependencies import get_db, require_permissions
from .models import Employee
from .schemas import EmployeeCreate, EmployeeUpdate, EmployeeOut
from .service import (
    create_employee,
    update_employee,
    terminate_employee,
    reactivate_employee,
    get_active_employees,
    get_employees_by_department
)


router = APIRouter()


@router.get("/", response_model=List[EmployeeOut])
def list_employees(
    department: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    is_active: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista funcionários.
    """
    q = db.query(Employee)

    if department:
        q = q.filter(Employee.department == department)
    if status_filter:
        q = q.filter(Employee.status == status_filter)
    if is_active is not None:
        q = q.filter(Employee.is_active == is_active)

    employees = q.order_by(Employee.full_name.asc()).all()
    return [EmployeeOut(**e.__dict__) for e in employees]


@router.post("/", response_model=EmployeeOut, dependencies=[Depends(require_permissions("administration.employees.create"))])
def create_employee_endpoint(data: EmployeeCreate, db: Session = Depends(get_db)):
    """
    Cria funcionário.
    """
    # Verificar se documento já existe
    existing = db.query(Employee).filter(Employee.document == data.document).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee with this document already exists"
        )

    employee = create_employee(db, data)
    return EmployeeOut(**employee.__dict__)


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    """
    Busca funcionário por ID.
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    return EmployeeOut(**employee.__dict__)


@router.put("/{employee_id}", response_model=EmployeeOut, dependencies=[Depends(require_permissions("administration.employees.update"))])
def update_employee_endpoint(
    employee_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza funcionário.
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    employee = update_employee(db, employee, data)
    return EmployeeOut(**employee.__dict__)


@router.delete("/{employee_id}", dependencies=[Depends(require_permissions("administration.employees.delete"))])
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    """
    Remove funcionário.
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    db.delete(employee)
    db.commit()

    return {"message": "Employee deleted successfully"}


@router.post("/{employee_id}/terminate", response_model=EmployeeOut, dependencies=[Depends(require_permissions("administration.employees.terminate"))])
def terminate_employee_endpoint(
    employee_id: int,
    termination_date: date = Body(...),
    reason: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Desliga funcionário.
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if employee.status == "terminated":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee is already terminated"
        )

    employee = terminate_employee(db, employee, termination_date, reason)
    return EmployeeOut(**employee.__dict__)


@router.post("/{employee_id}/reactivate", response_model=EmployeeOut, dependencies=[Depends(require_permissions("administration.employees.update"))])
def reactivate_employee_endpoint(employee_id: int, db: Session = Depends(get_db)):
    """
    Reativa funcionário desligado.
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if employee.status != "terminated":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee is not terminated"
        )

    employee = reactivate_employee(db, employee)
    return EmployeeOut(**employee.__dict__)


@router.get("/active/list", response_model=List[EmployeeOut])
def get_active_employees_endpoint(db: Session = Depends(get_db)):
    """
    Retorna funcionários ativos.
    """
    employees = get_active_employees(db)
    return [EmployeeOut(**e.__dict__) for e in employees]


@router.get("/department/{department}", response_model=List[EmployeeOut])
def get_employees_by_department_endpoint(department: str, db: Session = Depends(get_db)):
    """
    Retorna funcionários de um departamento.
    """
    employees = get_employees_by_department(db, department)
    return [EmployeeOut(**e.__dict__) for e in employees]
