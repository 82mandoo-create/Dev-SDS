from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, desc
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import secrets
import json
from app.core.database import get_db
from app.models.pc import PCAsset, PCActivity, PCApplication, PCSecurityEvent, PCStatus, SecurityLevel
from app.models.user import User
from app.models.activity import AuditLog
from app.schemas.pc import (
    PCAssetCreate, PCAssetUpdate, PCAssetResponse,
    AgentRegisterRequest, AgentHeartbeatRequest, AgentActivityReport, AgentAppReport,
    PCActivityResponse, SecurityEventResponse
)
from app.utils.deps import get_current_active_user, require_manager, require_admin
from app.services.ai_service import analyze_pc_security_local, detect_anomalies
from app.core.config import settings

router = APIRouter(prefix="/pcs", tags=["PC Assets"])

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, pc_id: str):
        await websocket.accept()
        self.active_connections[pc_id] = websocket
    
    def disconnect(self, pc_id: str):
        self.active_connections.pop(pc_id, None)
    
    async def send_message(self, pc_id: str, message: dict):
        if pc_id in self.active_connections:
            try:
                await self.active_connections[pc_id].send_json(message)
            except Exception:
                self.disconnect(pc_id)
    
    async def broadcast(self, message: dict):
        for pc_id, connection in list(self.active_connections.items()):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(pc_id)


manager = ConnectionManager()


# Agent endpoints (no auth - uses agent token)
@router.post("/agent/register")
async def register_agent(
    data: AgentRegisterRequest,
    db: Session = Depends(get_db)
):
    """에이전트 등록"""
    if data.agent_secret != settings.AGENT_SECRET_KEY:
        raise HTTPException(status_code=401, detail="유효하지 않은 에이전트 키입니다.")
    
    pc = db.query(PCAsset).filter(
        or_(
            PCAsset.hostname == data.hostname,
            PCAsset.serial_number == data.serial_number if data.serial_number else False
        )
    ).first()
    
    if not pc:
        import re
        asset_tag = f"PC-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
        pc = PCAsset(
            asset_tag=asset_tag,
            hostname=data.hostname,
            computer_name=data.computer_name,
            serial_number=data.serial_number,
            mac_address=data.mac_address,
            os_name=data.os_name,
            os_version=data.os_version,
            os_build=data.os_build,
            os_architecture=data.os_architecture,
            cpu_info=data.cpu_info,
            ram_gb=data.ram_gb,
            manufacturer=data.manufacturer,
            model=data.model,
            agent_token=secrets.token_urlsafe(32),
            last_heartbeat=datetime.utcnow(),
            is_online=True,
            status=PCStatus.ACTIVE
        )
        db.add(pc)
        db.commit()
        db.refresh(pc)
    else:
        pc.hostname = data.hostname
        pc.computer_name = data.computer_name
        pc.os_name = data.os_name
        pc.os_version = data.os_version
        pc.os_build = data.os_build
        pc.cpu_info = data.cpu_info
        pc.ram_gb = data.ram_gb
        pc.last_heartbeat = datetime.utcnow()
        pc.is_online = True
        if not pc.agent_token:
            pc.agent_token = secrets.token_urlsafe(32)
        db.commit()
    
    return {"agent_token": pc.agent_token, "pc_id": pc.id, "asset_tag": pc.asset_tag}


@router.post("/agent/heartbeat")
async def agent_heartbeat(
    data: AgentHeartbeatRequest,
    db: Session = Depends(get_db)
):
    """에이전트 하트비트"""
    pc = db.query(PCAsset).filter(PCAsset.agent_token == data.agent_token).first()
    if not pc:
        raise HTTPException(status_code=401, detail="유효하지 않은 에이전트 토큰입니다.")
    
    pc.last_heartbeat = datetime.utcnow()
    pc.is_online = data.is_online
    if data.ip_address:
        pc.last_ip_address = pc.ip_address
        pc.ip_address = data.ip_address
    if data.antivirus_installed is not None:
        pc.antivirus_installed = data.antivirus_installed
    if data.firewall_enabled is not None:
        pc.firewall_enabled = data.firewall_enabled
    if data.disk_encrypted is not None:
        pc.disk_encrypted = data.disk_encrypted
    if data.windows_defender is not None:
        pc.windows_defender = data.windows_defender
    if data.security_score is not None:
        pc.security_score = data.security_score
    
    db.commit()
    
    # Check for pending popup notifications for this PC
    from app.models.notification import Notification, NotificationChannel
    pending_notifs_query = db.query(Notification).filter(
        Notification.is_read == False,
        Notification.channel == NotificationChannel.POPUP,
        (Notification.related_type == "pc") & (Notification.related_id == pc.id) | (Notification.related_type == None)
    ).limit(5).all()
    
    pending_notifs = []
    for n in pending_notifs_query:
        pending_notifs.append({"title": n.title, "message": n.message, "priority": n.priority})
        n.is_read = True
    
    if pending_notifs:
        db.commit()
    
    # Auto-detect security issues and create security events
    security_issues = []
    if data.antivirus_installed == False:
        existing = db.query(PCSecurityEvent).filter(
            PCSecurityEvent.pc_asset_id == pc.id,
            PCSecurityEvent.event_type == "no_antivirus",
            PCSecurityEvent.is_resolved == False
        ).first()
        if not existing:
            security_issues.append(PCSecurityEvent(
                pc_asset_id=pc.id,
                event_type="no_antivirus",
                severity=SecurityLevel.CRITICAL,
                title="안티바이러스 미설치",
                description="안티바이러스 소프트웨어가 설치되어 있지 않습니다."
            ))
    
    if data.firewall_enabled == False:
        existing = db.query(PCSecurityEvent).filter(
            PCSecurityEvent.pc_asset_id == pc.id,
            PCSecurityEvent.event_type == "firewall_disabled",
            PCSecurityEvent.is_resolved == False
        ).first()
        if not existing:
            security_issues.append(PCSecurityEvent(
                pc_asset_id=pc.id,
                event_type="firewall_disabled",
                severity=SecurityLevel.HIGH,
                title="방화벽 비활성화",
                description="시스템 방화벽이 비활성화되어 있습니다."
            ))
    
    for issue in security_issues:
        db.add(issue)
    if security_issues:
        db.commit()
    
    return {"status": "ok", "notifications": pending_notifs}


@router.post("/agent/activities")
async def report_activities(
    data: AgentActivityReport,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """활동 보고"""
    pc = db.query(PCAsset).filter(PCAsset.agent_token == data.agent_token).first()
    if not pc:
        raise HTTPException(status_code=401, detail="유효하지 않은 에이전트 토큰입니다.")
    
    for activity_data in data.activities:
        started_at = activity_data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        
        ended_at = activity_data.get("ended_at")
        if isinstance(ended_at, str):
            ended_at = datetime.fromisoformat(ended_at)
        
        duration = None
        if started_at and ended_at:
            duration = int((ended_at - started_at).total_seconds())
        
        activity = PCActivity(
            pc_asset_id=pc.id,
            activity_type=activity_data.get("activity_type", "unknown"),
            user_account=activity_data.get("user_account"),
            started_at=started_at or datetime.utcnow(),
            ended_at=ended_at,
            duration_seconds=duration,
            details=activity_data.get("details")
        )
        db.add(activity)
    
    db.commit()
    return {"status": "ok", "recorded": len(data.activities)}


@router.post("/agent/applications")
async def report_applications(
    data: AgentAppReport,
    db: Session = Depends(get_db)
):
    """설치 앱 보고"""
    pc = db.query(PCAsset).filter(PCAsset.agent_token == data.agent_token).first()
    if not pc:
        raise HTTPException(status_code=401, detail="유효하지 않은 에이전트 토큰입니다.")
    
    for app_data in data.applications:
        existing = db.query(PCApplication).filter(
            PCApplication.pc_asset_id == pc.id,
            PCApplication.app_name == app_data.get("app_name")
        ).first()
        
        if existing:
            if app_data.get("last_used"):
                lu = app_data["last_used"]
                if isinstance(lu, str):
                    lu = datetime.fromisoformat(lu)
                existing.last_used = lu
            existing.is_running = app_data.get("is_running", False)
            if app_data.get("total_usage_seconds"):
                existing.total_usage_seconds += app_data["total_usage_seconds"]
                existing.usage_count += 1
        else:
            install_date = app_data.get("install_date")
            if isinstance(install_date, str):
                try:
                    install_date = datetime.fromisoformat(install_date)
                except:
                    install_date = None
            
            last_used = app_data.get("last_used")
            if isinstance(last_used, str):
                try:
                    last_used = datetime.fromisoformat(last_used)
                except:
                    last_used = None
            
            app = PCApplication(
                pc_asset_id=pc.id,
                app_name=app_data.get("app_name", "Unknown"),
                app_version=app_data.get("app_version"),
                publisher=app_data.get("publisher"),
                install_date=install_date,
                install_path=app_data.get("install_path"),
                last_used=last_used,
                category=app_data.get("category"),
                is_running=app_data.get("is_running", False)
            )
            db.add(app)
    
    db.commit()
    return {"status": "ok"}


@router.post("/agent/security-event")
async def report_security_event(
    agent_token: str,
    event_type: str,
    severity: str,
    title: str,
    description: str,
    db: Session = Depends(get_db)
):
    """보안 이벤트 보고"""
    pc = db.query(PCAsset).filter(PCAsset.agent_token == agent_token).first()
    if not pc:
        raise HTTPException(status_code=401, detail="유효하지 않은 에이전트 토큰입니다.")
    
    event = PCSecurityEvent(
        pc_asset_id=pc.id,
        event_type=event_type,
        severity=severity,
        title=title,
        description=description
    )
    db.add(event)
    db.commit()
    return {"status": "ok"}


# Admin/Manager PC endpoints
@router.get("", response_model=dict)
async def get_pcs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[PCStatus] = None,
    is_online: Optional[bool] = None,
    assigned_employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Update online status based on heartbeat
    threshold = datetime.utcnow() - timedelta(minutes=5)
    db.query(PCAsset).filter(
        PCAsset.last_heartbeat < threshold,
        PCAsset.is_online == True
    ).update({"is_online": False})
    db.commit()
    
    query = db.query(PCAsset)
    
    if search:
        query = query.filter(
            or_(
                PCAsset.hostname.ilike(f"%{search}%"),
                PCAsset.computer_name.ilike(f"%{search}%"),
                PCAsset.asset_tag.ilike(f"%{search}%"),
                PCAsset.ip_address.ilike(f"%{search}%")
            )
        )
    
    if status:
        query = query.filter(PCAsset.status == status)
    
    if is_online is not None:
        query = query.filter(PCAsset.is_online == is_online)
    
    if assigned_employee_id:
        query = query.filter(PCAsset.assigned_employee_id == assigned_employee_id)
    
    total = query.count()
    pcs = query.offset((page - 1) * limit).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [PCAssetResponse.model_validate(pc) for pc in pcs]
    }


@router.post("", response_model=PCAssetResponse)
async def create_pc(
    data: PCAssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    existing = db.query(PCAsset).filter(PCAsset.asset_tag == data.asset_tag).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 등록된 자산 태그입니다.")
    
    pc = PCAsset(**data.model_dump(), agent_token=secrets.token_urlsafe(32))
    db.add(pc)
    db.commit()
    db.refresh(pc)
    return PCAssetResponse.model_validate(pc)


@router.get("/{pc_id}", response_model=PCAssetResponse)
async def get_pc(
    pc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    pc = db.query(PCAsset).filter(PCAsset.id == pc_id).first()
    if not pc:
        raise HTTPException(status_code=404, detail="PC를 찾을 수 없습니다.")
    return PCAssetResponse.model_validate(pc)


@router.put("/{pc_id}", response_model=PCAssetResponse)
async def update_pc(
    pc_id: int,
    data: PCAssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    pc = db.query(PCAsset).filter(PCAsset.id == pc_id).first()
    if not pc:
        raise HTTPException(status_code=404, detail="PC를 찾을 수 없습니다.")
    
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(pc, key, value)
    db.commit()
    db.refresh(pc)
    return PCAssetResponse.model_validate(pc)


@router.get("/{pc_id}/activities", response_model=dict)
async def get_pc_activities(
    pc_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    activity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    pc = db.query(PCAsset).filter(PCAsset.id == pc_id).first()
    if not pc:
        raise HTTPException(status_code=404, detail="PC를 찾을 수 없습니다.")
    
    query = db.query(PCActivity).filter(PCActivity.pc_asset_id == pc_id)
    if activity_type:
        query = query.filter(PCActivity.activity_type == activity_type)
    
    query = query.order_by(desc(PCActivity.started_at))
    total = query.count()
    activities = query.offset((page - 1) * limit).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "items": [PCActivityResponse.model_validate(a) for a in activities]
    }


@router.get("/{pc_id}/applications", response_model=dict)
async def get_pc_applications(
    pc_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(PCApplication).filter(PCApplication.pc_asset_id == pc_id)
    if search:
        query = query.filter(PCApplication.app_name.ilike(f"%{search}%"))
    
    total = query.count()
    apps = query.offset((page - 1) * limit).limit(limit).all()
    
    return {"total": total, "page": page, "items": apps}


@router.get("/{pc_id}/security-events", response_model=dict)
async def get_pc_security_events(
    pc_id: int,
    resolved: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(PCSecurityEvent).filter(PCSecurityEvent.pc_asset_id == pc_id)
    if resolved is not None:
        query = query.filter(PCSecurityEvent.is_resolved == resolved)
    
    query = query.order_by(desc(PCSecurityEvent.occurred_at))
    events = query.all()
    
    return {"total": len(events), "items": [SecurityEventResponse.model_validate(e) for e in events]}


@router.post("/{pc_id}/security-events/{event_id}/resolve")
async def resolve_security_event(
    pc_id: int,
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    event = db.query(PCSecurityEvent).filter(
        PCSecurityEvent.id == event_id,
        PCSecurityEvent.pc_asset_id == pc_id
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="이벤트를 찾을 수 없습니다.")
    
    event.is_resolved = True
    event.resolved_at = datetime.utcnow()
    event.resolved_by = current_user.id
    db.commit()
    return {"message": "이벤트가 해결 처리되었습니다."}


@router.get("/{pc_id}/ai-analysis")
async def get_pc_ai_analysis(
    pc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """AI 보안 분석"""
    pc = db.query(PCAsset).filter(PCAsset.id == pc_id).first()
    if not pc:
        raise HTTPException(status_code=404, detail="PC를 찾을 수 없습니다.")
    
    pc_data = {
        "antivirus_installed": pc.antivirus_installed,
        "firewall_enabled": pc.firewall_enabled,
        "disk_encrypted": pc.disk_encrypted,
        "windows_defender": pc.windows_defender,
        "auto_update_enabled": pc.auto_update_enabled,
        "last_heartbeat": pc.last_heartbeat.isoformat() if pc.last_heartbeat else None,
        "security_score": pc.security_score
    }
    
    recent_activities = db.query(PCActivity).filter(
        PCActivity.pc_asset_id == pc_id
    ).order_by(desc(PCActivity.started_at)).limit(100).all()
    
    activity_list = [
        {"activity_type": a.activity_type, "started_at": a.started_at.isoformat(), "user_account": a.user_account}
        for a in recent_activities
    ]
    
    analysis = analyze_pc_security_local(pc_data)
    anomalies = detect_anomalies(activity_list)
    
    return {
        "pc_id": pc_id,
        "hostname": pc.hostname,
        "security_analysis": analysis,
        "anomalies": anomalies,
        "recommendations_count": len(analysis.get("recommendations", []))
    }


@router.get("/stats/summary")
async def get_pc_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Update online status
    threshold = datetime.utcnow() - timedelta(minutes=5)
    db.query(PCAsset).filter(
        PCAsset.last_heartbeat < threshold,
        PCAsset.is_online == True
    ).update({"is_online": False})
    db.commit()
    
    total = db.query(PCAsset).count()
    online = db.query(PCAsset).filter(PCAsset.is_online == True).count()
    active = db.query(PCAsset).filter(PCAsset.status == PCStatus.ACTIVE).count()
    
    unresolved_events = db.query(PCSecurityEvent).filter(
        PCSecurityEvent.is_resolved == False
    ).count()
    
    avg_score_result = db.query(func.avg(PCAsset.security_score)).scalar()
    avg_score = float(avg_score_result) if avg_score_result else 0
    
    no_antivirus = db.query(PCAsset).filter(PCAsset.antivirus_installed == False).count()
    no_firewall = db.query(PCAsset).filter(PCAsset.firewall_enabled == False).count()
    
    return {
        "total": total,
        "online": online,
        "offline": total - online,
        "active": active,
        "unresolved_security_events": unresolved_events,
        "avg_security_score": round(avg_score, 1),
        "no_antivirus": no_antivirus,
        "no_firewall": no_firewall
    }


@router.websocket("/ws/{pc_id}")
async def websocket_endpoint(websocket: WebSocket, pc_id: str, db: Session = Depends(get_db)):
    """WebSocket for real-time PC monitoring"""
    await manager.connect(websocket, pc_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(pc_id)
