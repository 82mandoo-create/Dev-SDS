from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum


class NotificationType(str, enum.Enum):
    CERTIFICATE_EXPIRY = "certificate_expiry"
    SECURITY_ALERT = "security_alert"
    PC_OFFLINE = "pc_offline"
    SYSTEM_UPDATE = "system_update"
    USER_LOGIN = "user_login"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    UNAUTHORIZED_APP = "unauthorized_app"
    GENERAL = "general"
    AI_INSIGHT = "ai_insight"


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    POPUP = "popup"
    SYSTEM = "system"


class NotificationPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    type = Column(Enum(NotificationType), default=NotificationType.GENERAL)
    channel = Column(Enum(NotificationChannel), default=NotificationChannel.SYSTEM)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Related resources
    related_type = Column(String(50), nullable=True)  # certificate, pc, employee
    related_id = Column(Integer, nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Email specific
    email_subject = Column(String(200), nullable=True)
    email_body = Column(Text, nullable=True)
    
    extra_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    
    subject_template = Column(String(500), nullable=True)
    body_template = Column(Text, nullable=False)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
