from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text, Date, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum


class CertificateType(str, enum.Enum):
    SSL_TLS = "ssl_tls"
    CODE_SIGNING = "code_signing"
    EMAIL = "email"
    CLIENT = "client"
    WILDCARD = "wildcard"
    EV = "ev"
    OV = "ov"
    DV = "dv"
    CUSTOM = "custom"


class CertificateStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    EXPIRING_SOON = "expiring_soon"
    REVOKED = "revoked"
    PENDING = "pending"


class CertificateVendor(Base):
    __tablename__ = "certificate_vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    contact_name = Column(String(100), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    certificates = relationship("Certificate", back_populates="vendor")


class Certificate(Base):
    __tablename__ = "certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    cert_type = Column(Enum(CertificateType), default=CertificateType.SSL_TLS)
    status = Column(Enum(CertificateStatus), default=CertificateStatus.ACTIVE)
    
    # Certificate details
    domain = Column(String(255), nullable=True)
    serial_number = Column(String(100), nullable=True)
    issuer = Column(String(255), nullable=True)
    subject = Column(String(255), nullable=True)
    fingerprint = Column(String(100), nullable=True)
    
    # Dates
    issued_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=False)
    
    # Renewal info
    renewal_reminder_days = Column(Integer, default=30)
    last_renewed_date = Column(Date, nullable=True)
    auto_renewal = Column(Boolean, default=False)
    renewal_cost = Column(Float, nullable=True)
    
    # Relations
    vendor_id = Column(Integer, ForeignKey("certificate_vendors.id"), nullable=True)
    responsible_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    
    # Purchase info
    purchase_date = Column(Date, nullable=True)
    purchase_price = Column(Float, nullable=True)
    invoice_number = Column(String(100), nullable=True)
    
    # File attachments
    cert_file_path = Column(String(500), nullable=True)
    key_file_path = Column(String(500), nullable=True)
    
    notes = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vendor = relationship("CertificateVendor", back_populates="certificates")
    responsible_employee = relationship("Employee", back_populates="certificates")
