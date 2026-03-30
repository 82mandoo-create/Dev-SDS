from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from app.models.employee import EmploymentStatus


class DepartmentBase(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(DepartmentBase):
    name: Optional[str] = None
    manager_id: Optional[int] = None


class DepartmentResponse(DepartmentBase):
    id: int
    manager_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmployeeBase(BaseModel):
    employee_number: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    department_id: Optional[int] = None
    position: Optional[str] = None
    job_title: Optional[str] = None
    hire_date: Optional[date] = None
    birth_date: Optional[date] = None
    employment_status: EmploymentStatus = EmploymentStatus.ACTIVE
    notes: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    user_id: Optional[int] = None
    create_user_account: bool = False


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department_id: Optional[int] = None
    position: Optional[str] = None
    job_title: Optional[str] = None
    hire_date: Optional[date] = None
    employment_status: Optional[EmploymentStatus] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    notes: Optional[str] = None


class EmployeeResponse(EmployeeBase):
    id: int
    user_id: Optional[int] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    department: Optional[DepartmentResponse] = None
    
    class Config:
        from_attributes = True
