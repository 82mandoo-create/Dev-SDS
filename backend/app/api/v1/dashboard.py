from fastapi import APIRouter, Depends, Query
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

# ──────────────────────────────────────────────────────────────────────
# 활동 유형 한글 매핑
# ──────────────────────────────────────────────────────────────────────
ACTION_LABEL: dict[str, str] = {
    "LOGIN":            "로그인",
    "LOGOUT":           "로그아웃",
    "CREATE":           "생성",
    "UPDATE":           "수정",
    "DELETE":           "삭제",
    "VIEW":             "조회",
    "REGISTER":         "등록",
    "HEARTBEAT":        "하트비트",
    "RESOLVE":          "해결",
    "LOCK":             "잠금",
    "UNLOCK":           "잠금해제",
    "PASSWORD_CHANGE":  "비밀번호변경",
    "EXPORT":           "내보내기",
    "IMPORT":           "가져오기",
}

RESOURCE_LABEL: dict[str, str] = {
    "user":          "사용자",
    "employee":      "직원",
    "certificate":   "인증서",
    "pc":            "PC",
    "pc_asset":      "PC",
    "notification":  "알림",
    "department":    "부서",
    "security_event":"보안이벤트",
    "audit_log":     "감사로그",
    "vendor":        "업체",
}

# 보안 점수 범위별 위험도 색상 (프론트에서 사용)
SCORE_RANGE_COLOR: dict[str, str] = {
    "0-20":   "critical",   # 빨강
    "21-40":  "high",       # 주황
    "41-60":  "medium",     # 노랑
    "61-80":  "low",        # 하늘
    "81-100": "safe",       # 초록
}


@router.get("/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """전체 대시보드 요약 – 하드코딩 없이 DB에서 실시간 집계"""
    # ── PC 온라인 상태 갱신 (5분 이상 무응답 → 오프라인)
    threshold = datetime.utcnow() - timedelta(minutes=5)
    db.query(PCAsset).filter(
        PCAsset.last_heartbeat < threshold,
        PCAsset.is_online == True
    ).update({"is_online": False})
    db.commit()

    today = date.today()

    # ── 직원
    total_employees  = db.query(Employee).count()
    active_employees = db.query(Employee).filter(
        Employee.employment_status == EmploymentStatus.ACTIVE
    ).count()

    # ── 인증서
    total_certs    = db.query(Certificate).count()
    active_certs   = db.query(Certificate).filter(
        Certificate.expiry_date >= today
    ).count()
    expired_certs  = db.query(Certificate).filter(
        Certificate.expiry_date < today
    ).count()
    expiring_30    = db.query(Certificate).filter(
        Certificate.expiry_date >= today,
        Certificate.expiry_date <= today + timedelta(days=30)
    ).count()
    critical_certs = db.query(Certificate).filter(
        Certificate.expiry_date >= today,
        Certificate.expiry_date <= today + timedelta(days=7)
    ).count()

    # ── PC
    total_pcs   = db.query(PCAsset).filter(
        PCAsset.status == PCStatus.ACTIVE
    ).count()
    online_pcs  = db.query(PCAsset).filter(
        PCAsset.is_online == True
    ).count()
    offline_pcs = total_pcs - online_pcs

    no_antivirus = db.query(PCAsset).filter(
        PCAsset.status == PCStatus.ACTIVE,
        PCAsset.antivirus_installed == False
    ).count()
    no_firewall  = db.query(PCAsset).filter(
        PCAsset.status == PCStatus.ACTIVE,
        PCAsset.firewall_enabled == False
    ).count()
    not_encrypted = db.query(PCAsset).filter(
        PCAsset.status == PCStatus.ACTIVE,
        PCAsset.disk_encrypted == False
    ).count()

    avg_score_raw = db.query(func.avg(PCAsset.security_score)).filter(
        PCAsset.status == PCStatus.ACTIVE
    ).scalar()
    avg_security_score = round(float(avg_score_raw or 0), 1)

    # ── 보안 이벤트
    unresolved_events = db.query(PCSecurityEvent).filter(
        PCSecurityEvent.is_resolved == False
    ).count()

    # ── 사용자
    total_users = db.query(User).count()

    # ── 알림
    unread_notifications = db.query(Notification).filter(
        (Notification.user_id == current_user.id) | (Notification.user_id == None),
        Notification.is_read == False
    ).count()

    return {
        "employees": {
            "total":  total_employees,
            "active": active_employees,
        },
        "certificates": {
            "total":         total_certs,
            "active":        active_certs,
            "expired":       expired_certs,
            "expiring_soon": expiring_30,
            "critical":      critical_certs,
        },
        "pcs": {
            "total":         total_pcs,
            "online":        online_pcs,
            "offline":       offline_pcs,
            "online_rate":   round((online_pcs / total_pcs * 100) if total_pcs > 0 else 0, 1),
            "no_antivirus":  no_antivirus,
            "no_firewall":   no_firewall,
            "not_encrypted": not_encrypted,
        },
        "security": {
            "unresolved_events":  unresolved_events,
            "avg_security_score": avg_security_score,
        },
        "users": {
            "total": total_users,
        },
        "notifications": {
            "unread": unread_notifications,
        },
    }


@router.get("/recent-activities")
async def get_recent_activities(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """최근 활동 로그 – action/resource_type 한글 레이블 포함"""
    logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit).all()

    # user_id → full_name 캐시 (N+1 방지)
    user_ids = {log.user_id for log in logs if log.user_id}
    users = {u.id: u.full_name for u in db.query(User).filter(User.id.in_(user_ids)).all()}

    result = []
    for log in logs:
        action_raw = (log.action or "").upper()
        resource_raw = (log.resource_type or "").lower()
        result.append({
            "id":             log.id,
            "action":         action_raw,
            "action_label":   ACTION_LABEL.get(action_raw, action_raw),
            "resource_type":  resource_raw,
            "resource_label": RESOURCE_LABEL.get(resource_raw, resource_raw) if resource_raw else None,
            "description":    log.description,
            "user_name":      users.get(log.user_id, "시스템"),
            "ip_address":     log.ip_address,
            "created_at":     log.created_at.isoformat() if log.created_at else None,
        })

    return result


@router.get("/security-events")
async def get_recent_security_events(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """최근 미해결 보안 이벤트"""
    events = db.query(PCSecurityEvent).filter(
        PCSecurityEvent.is_resolved == False
    ).order_by(desc(PCSecurityEvent.occurred_at)).limit(limit).all()

    pc_ids = {e.pc_asset_id for e in events}
    pcs = {p.id: p for p in db.query(PCAsset).filter(PCAsset.id.in_(pc_ids)).all()}

    result = []
    for event in events:
        pc = pcs.get(event.pc_asset_id)
        result.append({
            "id":          event.id,
            "pc_id":       event.pc_asset_id,
            "pc_name":     pc.hostname if pc else "Unknown",
            "asset_tag":   pc.asset_tag if pc else None,
            "event_type":  event.event_type,
            "severity":    event.severity,
            "title":       event.title,
            "description": event.description,
            "occurred_at": event.occurred_at.isoformat() if event.occurred_at else None,
        })

    return result


@router.get("/expiring-certificates")
async def get_expiring_certificates(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """만료 예정 인증서 – 업체 정보 포함"""
    today = date.today()
    certs = db.query(Certificate).filter(
        Certificate.expiry_date >= today,
        Certificate.expiry_date <= today + timedelta(days=days)
    ).order_by(Certificate.expiry_date).all()

    result = []
    for cert in certs:
        days_left = (cert.expiry_date - today).days
        result.append({
            "id":          cert.id,
            "name":        cert.name,
            "domain":      cert.domain,
            "cert_type":   cert.cert_type,
            "expiry_date": cert.expiry_date.isoformat(),
            "days_left":   days_left,
            "status":      "critical" if days_left <= 7 else "warning",
            "vendor_name": cert.vendor.name if cert.vendor else None,
        })

    return result


@router.get("/pc-activity-chart")
async def get_pc_activity_chart(
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """PC 활동 차트 – 모든 날짜에 login/sleep/wakeup 기본값 0 보장"""
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

    # 날짜별 집계 맵
    chart_map: dict[str, dict] = {}
    for row in activities:
        d = str(row.date)
        if d not in chart_map:
            chart_map[d] = {}
        chart_map[d][row.activity_type] = row.count

    # 과거 days일 ~ 오늘까지 모든 날짜 순서대로, 누락 키는 0
    result = []
    for i in range(days, -1, -1):
        d = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_data = chart_map.get(d, {})
        result.append({
            "date":   d,
            "login":  int(day_data.get("login",  0)),
            "sleep":  int(day_data.get("sleep",  0)),
            "wakeup": int(day_data.get("wakeup", 0)),
        })

    return result


@router.get("/security-score-distribution")
async def get_security_score_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """보안 점수 분포 – 위험도 레이블·색상 포함"""
    scores = db.query(PCAsset.security_score).filter(
        PCAsset.status == PCStatus.ACTIVE
    ).all()

    distribution: dict[str, int] = {k: 0 for k in SCORE_RANGE_COLOR}
    for (score,) in scores:
        s = score or 0
        if s <= 20:
            distribution["0-20"]   += 1
        elif s <= 40:
            distribution["21-40"]  += 1
        elif s <= 60:
            distribution["41-60"]  += 1
        elif s <= 80:
            distribution["61-80"]  += 1
        else:
            distribution["81-100"] += 1

    return [
        {
            "range":       k,
            "count":       v,
            "risk_level":  SCORE_RANGE_COLOR[k],   # critical/high/medium/low/safe
        }
        for k, v in distribution.items()
    ]


@router.get("/ai-insights")
async def get_ai_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """AI 인사이트 – 최신 DB 수치를 기반으로 생성"""
    today = date.today()

    total_pcs          = db.query(PCAsset).filter(PCAsset.status == PCStatus.ACTIVE).count()
    online_pcs         = db.query(PCAsset).filter(PCAsset.is_online == True).count()
    expiring_certs     = db.query(Certificate).filter(
        Certificate.expiry_date >= today,
        Certificate.expiry_date <= today + timedelta(days=30)
    ).count()
    unresolved_events  = db.query(PCSecurityEvent).filter(
        PCSecurityEvent.is_resolved == False
    ).count()
    avg_score_raw      = db.query(func.avg(PCAsset.security_score)).filter(
        PCAsset.status == PCStatus.ACTIVE
    ).scalar()
    inactive_employees = db.query(Employee).filter(
        Employee.employment_status != EmploymentStatus.ACTIVE
    ).count()
    no_antivirus       = db.query(PCAsset).filter(
        PCAsset.status == PCStatus.ACTIVE,
        PCAsset.antivirus_installed == False
    ).count()

    stats = {
        "total_pcs":                   total_pcs,
        "online_pcs":                  online_pcs,
        "expiring_certs_30days":       expiring_certs,
        "unresolved_security_events":  unresolved_events,
        "avg_security_score":          float(avg_score_raw or 0),
        "inactive_employees":          inactive_employees,
        "no_antivirus_pcs":            no_antivirus,
    }

    return generate_security_insights_local(stats)
