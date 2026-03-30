from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum


class EmploymentStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    RESIGNED = "resigned"
    RETIRED = "retired"


class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=True)
    description = Column(Text, nullable=True)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employees = relationship("Employee", back_populates="department", foreign_keys="Employee.department_id")
    manager = relationship("Employee", foreign_keys=[manager_id])
    children = relationship("Department", foreign_keys=[parent_id])


class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    employee_number = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    position = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)
    
    hire_date = Column(Date, nullable=True)
    birth_date = Column(Date, nullable=True)
    employment_status = Column(Enum(EmploymentStatus), default=EmploymentStatus.ACTIVE)
    
    # Emergency contact
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="employee")
    department = relationship("Department", back_populates="employees", foreign_keys=[department_id])
    pc_assets = relationship("PCAsset", back_populates="assigned_employee")
    certificates = relationship("Certificate", back_populates="responsible_employee")
