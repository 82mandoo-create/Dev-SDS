from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import Optional, List
from app.core.database import get_db
from app.core.security import get_password_hash, generate_random_password
from app.models.employee import Employee, Department, EmploymentStatus
from app.models.user import User, UserRole, UserStatus
from app.models.activity import AuditLog
from app.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    DepartmentCreate, DepartmentUpdate, DepartmentResponse
)
from app.utils.deps import get_current_active_user, require_manager, require_admin
from app.services.email_service import send_welcome_email
from app.core.config import settings

router = APIRouter(prefix="/employees", tags=["Employees"])


# Department endpoints
@router.get("/departments", response_model=List[DepartmentResponse])
async def get_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return db.query(Department).all()


@router.post("/departments", response_model=DepartmentResponse)
async def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    existing = db.query(Department).filter(Department.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 존재하는 부서명입니다.")
    
    dept = Department(**data.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.put("/departments/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(dept, key, value)
    db.commit()
    db.refresh(dept)
    return dept


@router.delete("/departments/{dept_id}")
async def delete_department(
    dept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    
    has_employees = db.query(Employee).filter(Employee.department_id == dept_id).first()
    if has_employees:
        raise HTTPException(status_code=400, detail="해당 부서에 직원이 있습니다. 먼저 직원을 이동하세요.")
    
    db.delete(dept)
    db.commit()
    return {"message": "부서가 삭제되었습니다."}


# Employee endpoints
@router.get("", response_model=dict)
async def get_employees(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    status: Optional[EmploymentStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Employee).options(joinedload(Employee.department))
    
    if search:
        query = query.filter(
            or_(
                Employee.full_name.ilike(f"%{search}%"),
                Employee.email.ilike(f"%{search}%"),
                Employee.employee_number.ilike(f"%{search}%"),
                Employee.position.ilike(f"%{search}%")
            )
        )
    
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    
    if status:
        query = query.filter(Employee.employment_status == status)
    
    total = query.count()
    employees = query.offset((page - 1) * limit).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [EmployeeResponse.model_validate(e) for e in employees]
    }


@router.post("", response_model=EmployeeResponse)
async def create_employee(
    data: EmployeeCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    existing = db.query(Employee).filter(
        or_(Employee.email == data.email, Employee.employee_number == data.employee_number)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 등록된 직원 정보입니다.")
    
    employee_data = data.model_dump(exclude={"create_user_account"})
    
    if data.create_user_account:
        temp_password = generate_random_password()
        user = User(
            email=data.email,
            hashed_password=get_password_hash(temp_password),
            full_name=data.full_name,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            email_verified=True
        )
        db.add(user)
        db.flush()
        employee_data["user_id"] = user.id
        
        background_tasks.add_task(
            send_welcome_email, data.email, data.full_name, temp_password,
            f"{settings.FRONTEND_URL}/login"
        )
    
    employee = Employee(**employee_data)
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    log = AuditLog(
        user_id=current_user.id,
        action="CREATE_EMPLOYEE",
        resource_type="employee",
        resource_id=employee.id,
        description=f"직원 등록: {employee.full_name}"
    )
    db.add(log)
    db.commit()
    
    return EmployeeResponse.model_validate(employee)


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    employee = db.query(Employee).options(joinedload(Employee.department)).filter(
        Employee.id == employee_id
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.")
    return EmployeeResponse.model_validate(employee)


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.")
    
    old_data = {k: str(v) for k, v in employee.__dict__.items() if not k.startswith('_')}
    
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(employee, key, value)
    db.commit()
    db.refresh(employee)
    
    log = AuditLog(
        user_id=current_user.id,
        action="UPDATE_EMPLOYEE",
        resource_type="employee",
        resource_id=employee.id,
        description=f"직원 정보 수정: {employee.full_name}",
        old_values=old_data
    )
    db.add(log)
    db.commit()
    
    return EmployeeResponse.model_validate(employee)


@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.")
    
    employee.employment_status = EmploymentStatus.RESIGNED
    db.commit()
    
    return {"message": "직원이 퇴직 처리되었습니다."}


@router.get("/stats/summary")
async def get_employee_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    total = db.query(Employee).count()
    active = db.query(Employee).filter(Employee.employment_status == EmploymentStatus.ACTIVE).count()
    on_leave = db.query(Employee).filter(Employee.employment_status == EmploymentStatus.ON_LEAVE).count()
    resigned = db.query(Employee).filter(Employee.employment_status == EmploymentStatus.RESIGNED).count()
    
    dept_stats = db.query(
        Department.name, func.count(Employee.id).label("count")
    ).join(Employee, Employee.department_id == Department.id, isouter=True).group_by(Department.id).all()
    
    return {
        "total": total,
        "active": active,
        "on_leave": on_leave,
        "resigned": resigned,
        "by_department": [{"name": d[0], "count": d[1]} for d in dept_stats]
    }
