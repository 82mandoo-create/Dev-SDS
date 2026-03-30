from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta, date
from app.core.database import get_db
from app.models.user import User
from app.models.employee import Employee, EmploymentStatus
from app.models.certificate import Certificate, CertificateStatus
from app.models.pc import PCAsset, PCActivity, PCSecurityEvent, PCStatus
from app.models.notification import Notification
from app.models.activity import AuditLog
from app.utils.deps import get_current_active_user
from app.services.ai_service import generate_security_insights_local

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """전체 대시보드 요약"""
    # Update PC online status
    threshold = datetime.utcnow() - timedelta(minutes=5)
    db.query(PCAsset).filter(
        PCAsset.last_heartbeat < threshold,
        PCAsset.is_online == True
    ).update({"is_online": False})
    db.commit()
    
    today = date.today()
    
    # Employees
    total_employees = db.query(Employee).filter(Employee.employment_status == EmploymentStatus.ACTIVE).count()
    
    # Certificates
    total_certs = db.query(Certificate).count()
    expiring_certs = db.query(Certificate).filter(
        Certificate.expiry_date <= today + timedelta(days=30),
        Certificate.expiry_date >= today
    ).count()
    expired_certs = db.query(Certificate).filter(Certificate.expiry_date < today).count()
    critical_certs = db.query(Certificate).filter(
        Certificate.expiry_date <= today + timedelta(days=7),
        Certificate.expiry_date >= today
    ).count()
    
    # PCs
    total_pcs = db.query(PCAsset).count()
    online_pcs = db.query(PCAsset).filter(PCAsset.is_online == True).count()
    
    # Security
    unresolved_events = db.query(PCSecurityEvent).filter(
        PCSecurityEvent.is_resolved == False
    ).count()
    
    avg_security = db.query(func.avg(PCAsset.security_score)).scalar() or 0
    
    # Users
    total_users = db.query(User).count()
    
    # Notifications
    unread_notifications = db.query(Notification).filter(
        (Notification.user_id == current_user.id) | (Notification.user_id == None),
        Notification.is_read == False
    ).count()
    
    return {
        "employees": {
            "total": total_employees
        },
        "certificates": {
            "total": total_certs,
            "expiring_soon": expiring_certs,
            "expired": expired_certs,
            "critical": critical_certs
        },
        "pcs": {
            "total": total_pcs,
            "online": online_pcs,
            "offline": total_pcs - online_pcs,
            "online_rate": round((online_pcs / total_pcs * 100) if total_pcs > 0 else 0, 1)
        },
        "security": {
            "unresolved_events": unresolved_events,
            "avg_security_score": round(float(avg_security), 1)
        },
        "users": {
            "total": total_users
        },
        "notifications": {
            "unread": unread_notifications
        }
    }


@router.get("/recent-activities")
async def get_recent_activities(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """최근 활동 로그"""
    logs = db.query(AuditLog).options(
    ).order_by(desc(AuditLog.created_at)).limit(limit).all()
    
    result = []
    for log in logs:
        user_name = "시스템"
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            if user:
                user_name = user.full_name
        
        result.append({
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "description": log.description,
            "user_name": user_name,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat()
        })
    
    return result


@router.get("/security-events")
async def get_recent_security_events(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """최근 보안 이벤트"""
    events = db.query(PCSecurityEvent).filter(
        PCSecurityEvent.is_resolved == False
    ).order_by(desc(PCSecurityEvent.occurred_at)).limit(limit).all()
    
    result = []
    for event in events:
        pc = db.query(PCAsset).filter(PCAsset.id == event.pc_asset_id).first()
        result.append({
            "id": event.id,
            "pc_id": event.pc_asset_id,
            "pc_name": pc.hostname if pc else "Unknown",
            "event_type": event.event_type,
            "severity": event.severity,
            "title": event.title,
            "description": event.description,
            "occurred_at": event.occurred_at.isoformat()
        })
    
    return result


@router.get("/expiring-certificates")
async def get_expiring_certificates(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """만료 예정 인증서"""
    today = date.today()
    certs = db.query(Certificate).filter(
        Certificate.expiry_date <= today + timedelta(days=days),
        Certificate.expiry_date >= today
    ).order_by(Certificate.expiry_date).all()
    
    result = []
    for cert in certs:
        days_left = (cert.expiry_date - today).days
        result.append({
            "id": cert.id,
            "name": cert.name,
            "domain": cert.domain,
            "expiry_date": cert.expiry_date.isoformat(),
            "days_left": days_left,
            "status": "critical" if days_left <= 7 else "warning"
        })
    
    return result


@router.get("/pc-activity-chart")
async def get_pc_activity_chart(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """PC 활동 차트 데이터"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    activities = db.query(
        func.date(PCActivity.started_at).label("date"),
        PCActivity.activity_type,
        func.count(PCActivity.id).label("count")
    ).filter(
        PCActivity.started_at >= start_date
    ).group_by(
        func.date(PCActivity.started_at),
        PCActivity.activity_type
    ).all()
    
    chart_data = {}
    for activity in activities:
        date_str = str(activity.date)
        if date_str not in chart_data:
            chart_data[date_str] = {}
        chart_data[date_str][activity.activity_type] = activity.count
    
    dates = [(datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days, -1, -1)]
    result = []
    for d in dates:
        row = {"date": d}
        row.update(chart_data.get(d, {}))
        result.append(row)
    
    return result


@router.get("/security-score-distribution")
async def get_security_score_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """보안 점수 분포"""
    pcs = db.query(PCAsset.security_score).all()
    
    distribution = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for pc in pcs:
        score = pc[0] or 0
        if score <= 20:
            distribution["0-20"] += 1
        elif score <= 40:
            distribution["21-40"] += 1
        elif score <= 60:
            distribution["41-60"] += 1
        elif score <= 80:
            distribution["61-80"] += 1
        else:
            distribution["81-100"] += 1
    
    return [{"range": k, "count": v} for k, v in distribution.items()]


@router.get("/ai-insights")
async def get_ai_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """AI 인사이트"""
    today = date.today()
    
    total_pcs = db.query(PCAsset).count()
    online_pcs = db.query(PCAsset).filter(PCAsset.is_online == True).count()
    expiring_certs = db.query(Certificate).filter(
        Certificate.expiry_date <= today + timedelta(days=30),
        Certificate.expiry_date >= today
    ).count()
    unresolved_events = db.query(PCSecurityEvent).filter(
        PCSecurityEvent.is_resolved == False
    ).count()
    avg_score = db.query(func.avg(PCAsset.security_score)).scalar() or 0
    inactive_employees = db.query(Employee).filter(
        Employee.employment_status != EmploymentStatus.ACTIVE
    ).count()
    
    stats = {
        "total_pcs": total_pcs,
        "online_pcs": online_pcs,
        "expiring_certs_30days": expiring_certs,
        "unresolved_security_events": unresolved_events,
        "avg_security_score": float(avg_score),
        "inactive_employees": inactive_employees
    }
    
    insights = generate_security_insights_local(stats)
    return insights
