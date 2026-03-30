from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime
from app.core.database import get_db
from app.models.notification import Notification, NotificationType, NotificationChannel, NotificationPriority
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationCreate, SendEmailRequest
from app.utils.deps import get_current_active_user, require_admin
from app.services.email_service import send_email

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=dict)
async def get_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    is_read: Optional[bool] = None,
    notification_type: Optional[NotificationType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Notification).filter(
        (Notification.user_id == current_user.id) | (Notification.user_id == None)
    )
    
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    
    if notification_type:
        query = query.filter(Notification.type == notification_type)
    
    query = query.order_by(desc(Notification.created_at))
    total = query.count()
    notifications = query.offset((page - 1) * limit).limit(limit).all()
    unread_count = db.query(Notification).filter(
        (Notification.user_id == current_user.id) | (Notification.user_id == None),
        Notification.is_read == False
    ).count()
    
    return {
        "total": total,
        "unread_count": unread_count,
        "page": page,
        "items": [NotificationResponse.model_validate(n) for n in notifications]
    }


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")
    
    notif.is_read = True
    notif.read_at = datetime.utcnow()
    db.commit()
    return {"message": "읽음 처리되었습니다."}


@router.post("/read-all")
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db.query(Notification).filter(
        (Notification.user_id == current_user.id) | (Notification.user_id == None),
        Notification.is_read == False
    ).update({"is_read": True, "read_at": datetime.utcnow()})
    db.commit()
    return {"message": "모든 알림이 읽음 처리되었습니다."}


@router.post("", response_model=NotificationResponse)
async def create_notification(
    data: NotificationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    notif = Notification(**data.model_dump())
    db.add(notif)
    db.commit()
    db.refresh(notif)
    
    if data.channel == NotificationChannel.EMAIL and data.user_id:
        user = db.query(User).filter(User.id == data.user_id).first()
        if user:
            background_tasks.add_task(
                send_email, user.email, data.title, data.message, user.full_name
            )
    
    return NotificationResponse.model_validate(notif)


@router.post("/send-email")
async def send_email_notification(
    data: SendEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin)
):
    background_tasks.add_task(send_email, data.recipient_email, data.subject, data.body)
    return {"message": "이메일이 발송됩니다."}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")
    db.delete(notif)
    db.commit()
    return {"message": "알림이 삭제되었습니다."}
