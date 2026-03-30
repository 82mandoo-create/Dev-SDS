from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from app.models.certificate import CertificateType, CertificateStatus


class VendorBase(BaseModel):
    name: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(VendorBase):
    name: Optional[str] = None


class VendorResponse(VendorBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CertificateBase(BaseModel):
    name: str
    description: Optional[str] = None
    cert_type: CertificateType = CertificateType.SSL_TLS
    domain: Optional[str] = None
    serial_number: Optional[str] = None
    issuer: Optional[str] = None
    subject: Optional[str] = None
    issued_date: Optional[date] = None
    expiry_date: date
    renewal_reminder_days: int = 30
    auto_renewal: bool = False
    renewal_cost: Optional[float] = None
    vendor_id: Optional[int] = None
    responsible_employee_id: Optional[int] = None
    purchase_date: Optional[date] = None
    purchase_price: Optional[float] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class CertificateCreate(CertificateBase):
    pass


class CertificateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CertificateStatus] = None
    domain: Optional[str] = None
    expiry_date: Optional[date] = None
    renewal_reminder_days: Optional[int] = None
    auto_renewal: Optional[bool] = None
    renewal_cost: Optional[float] = None
    vendor_id: Optional[int] = None
    responsible_employee_id: Optional[int] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class CertificateResponse(CertificateBase):
    id: int
    status: CertificateStatus
    fingerprint: Optional[str] = None
    last_renewed_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    days_until_expiry: Optional[int] = None
    
    class Config:
        from_attributes = True
