from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum


class PCStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"
    STOLEN = "stolen"


class SecurityLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CRITICAL = "critical"


class PCAsset(Base):
    __tablename__ = "pc_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_tag = Column(String(50), unique=True, nullable=False)
    hostname = Column(String(100), unique=True, nullable=True)
    computer_name = Column(String(100), nullable=True)
    
    # Hardware info
    manufacturer = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), unique=True, nullable=True)
    cpu_info = Column(String(200), nullable=True)
    ram_gb = Column(Float, nullable=True)
    storage_info = Column(Text, nullable=True)
    
    # OS info
    os_name = Column(String(100), nullable=True)
    os_version = Column(String(100), nullable=True)
    os_build = Column(String(50), nullable=True)
    os_architecture = Column(String(20), nullable=True)
    
    # Network
    mac_address = Column(String(20), nullable=True)
    ip_address = Column(String(45), nullable=True)
    last_ip_address = Column(String(45), nullable=True)
    
    # Agent info
    agent_version = Column(String(20), nullable=True)
    agent_token = Column(String(200), unique=True, nullable=True)
    last_heartbeat = Column(DateTime, nullable=True)
    is_online = Column(Boolean, default=False)
    
    # Assignment
    assigned_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    
    # Status
    status = Column(Enum(PCStatus), default=PCStatus.ACTIVE)
    security_level = Column(Enum(SecurityLevel), default=SecurityLevel.MEDIUM)
    
    # Security
    antivirus_installed = Column(Boolean, default=False)
    antivirus_name = Column(String(100), nullable=True)
    antivirus_updated = Column(DateTime, nullable=True)
    firewall_enabled = Column(Boolean, default=False)
    disk_encrypted = Column(Boolean, default=False)
    windows_defender = Column(Boolean, default=False)
    auto_update_enabled = Column(Boolean, default=False)
    last_security_scan = Column(DateTime, nullable=True)
    security_score = Column(Integer, default=0)
    
    # Purchase info
    purchase_date = Column(DateTime, nullable=True)
    warranty_expiry = Column(DateTime, nullable=True)
    purchase_price = Column(Float, nullable=True)
    
    notes = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_employee = relationship("Employee", back_populates="pc_assets")
    activities = relationship("PCActivity", back_populates="pc_asset", cascade="all, delete-orphan")
    applications = relationship("PCApplication", back_populates="pc_asset", cascade="all, delete-orphan")
    security_events = relationship("PCSecurityEvent", back_populates="pc_asset", cascade="all, delete-orphan")


class PCActivity(Base):
    __tablename__ = "pc_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    pc_asset_id = Column(Integer, ForeignKey("pc_assets.id"), nullable=False)
    
    activity_type = Column(String(50), nullable=False)  # login, logout, sleep, wake, lock, unlock
    user_account = Column(String(100), nullable=True)
    
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    details = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    pc_asset = relationship("PCAsset", back_populates="activities")


class PCApplication(Base):
    __tablename__ = "pc_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    pc_asset_id = Column(Integer, ForeignKey("pc_assets.id"), nullable=False)
    
    app_name = Column(String(200), nullable=False)
    app_version = Column(String(50), nullable=True)
    publisher = Column(String(200), nullable=True)
    install_date = Column(DateTime, nullable=True)
    install_path = Column(String(500), nullable=True)
    
    # Usage tracking
    last_used = Column(DateTime, nullable=True)
    total_usage_seconds = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    
    # Category
    category = Column(String(50), nullable=True)  # productivity, security, browser, development, etc.
    is_approved = Column(Boolean, nullable=True)  # None = unknown, True = approved, False = blacklisted
    is_running = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    pc_asset = relationship("PCAsset", back_populates="applications")


class PCSecurityEvent(Base):
    __tablename__ = "pc_security_events"
    
    id = Column(Integer, primary_key=True, index=True)
    pc_asset_id = Column(Integer, ForeignKey("pc_assets.id"), nullable=False)
    
    event_type = Column(String(100), nullable=False)  # unauthorized_software, failed_login, etc.
    severity = Column(Enum(SecurityLevel), default=SecurityLevel.MEDIUM)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    raw_data = Column(JSON, nullable=True)
    
    occurred_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    pc_asset = relationship("PCAsset", back_populates="security_events")
