from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.notification import NotificationType, NotificationChannel, NotificationPriority


class NotificationResponse(BaseModel):
    id: int
    type: NotificationType
    channel: NotificationChannel
    priority: NotificationPriority
    title: str
    message: str
    related_type: Optional[str] = None
    related_id: Optional[int] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    user_id: Optional[int] = None
    type: NotificationType = NotificationType.GENERAL
    channel: NotificationChannel = NotificationChannel.SYSTEM
    priority: NotificationPriority = NotificationPriority.MEDIUM
    title: str
    message: str
    related_type: Optional[str] = None
    related_id: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None


class SendEmailRequest(BaseModel):
    recipient_email: str
    subject: str
    body: str
