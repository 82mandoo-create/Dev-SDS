from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import auth, employees, certificates, pcs, notifications, dashboard, users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / Shutdown events"""
    logger.info("🚀 AssetGuard Enterprise starting...")
    init_db()
    await create_initial_data()
    start_scheduler()
    logger.info("✅ Server ready!")
    yield
    logger.info("👋 Server shutting down...")


async def create_initial_data():
    """Create initial admin user and sample data"""
    from app.core.database import SessionLocal
    from app.core.security import get_password_hash
    from app.models.user import User, UserRole, UserStatus
    from app.models.employee import Department, Employee
    from app.models.certificate import Certificate, CertificateVendor, CertificateType, CertificateStatus
    from app.models.pc import PCAsset, PCActivity, PCSecurityEvent, PCStatus, SecurityLevel
    from app.models.notification import Notification, NotificationType, NotificationChannel, NotificationPriority
    from datetime import date, timedelta, datetime
    import secrets
    
    db = SessionLocal()
    try:
        # Create admin user
        admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if not admin:
            admin = User(
                email=settings.ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                full_name="시스템 관리자",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                email_verified=True
            )
            db.add(admin)
            db.flush()
            
            # Demo manager
            manager = User(
                email="manager@company.com",
                hashed_password=get_password_hash("Manager@123"),
                full_name="김매니저",
                role=UserRole.MANAGER,
                status=UserStatus.ACTIVE,
                email_verified=True
            )
            db.add(manager)
            
            # Demo user
            demo_user = User(
                email="user@company.com",
                hashed_password=get_password_hash("User@123456"),
                full_name="이직원",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                email_verified=True
            )
            db.add(demo_user)
            db.flush()
            
            # Departments
            depts = ["개발팀", "인프라팀", "보안팀", "기획팀", "영업팀", "경영지원팀"]
            dept_objects = {}
            for dept_name in depts:
                dept = Department(name=dept_name, code=dept_name[:2])
                db.add(dept)
                db.flush()
                dept_objects[dept_name] = dept
            
            # Employees
            employees_data = [
                {"employee_number": "EMP001", "full_name": "김철수", "email": "kim@company.com", "position": "팀장", "dept": "개발팀"},
                {"employee_number": "EMP002", "full_name": "이영희", "email": "lee@company.com", "position": "시니어 개발자", "dept": "개발팀"},
                {"employee_number": "EMP003", "full_name": "박지민", "email": "park@company.com", "position": "인프라 엔지니어", "dept": "인프라팀"},
                {"employee_number": "EMP004", "full_name": "최보안", "email": "choi@company.com", "position": "보안 분석가", "dept": "보안팀"},
                {"employee_number": "EMP005", "full_name": "정기획", "email": "jung@company.com", "position": "기획자", "dept": "기획팀"},
                {"employee_number": "EMP006", "full_name": "강영업", "email": "kang@company.com", "position": "영업 매니저", "dept": "영업팀"},
                {"employee_number": "EMP007", "full_name": "윤지원", "email": "yoon@company.com", "position": "HR 담당자", "dept": "경영지원팀"},
                {"employee_number": "EMP008", "full_name": "조개발", "email": "jo@company.com", "position": "주니어 개발자", "dept": "개발팀"},
            ]
            
            for emp_data in employees_data:
                emp = Employee(
                    employee_number=emp_data["employee_number"],
                    full_name=emp_data["full_name"],
                    email=emp_data["email"],
                    position=emp_data["position"],
                    department_id=dept_objects[emp_data["dept"]].id,
                    hire_date=date(2020, 1, 1)
                )
                db.add(emp)
            db.flush()
            
            # Certificate vendors
            vendors = [
                CertificateVendor(name="DigiCert Korea", contact_email="support@digicert.co.kr", contact_phone="02-1234-5678"),
                CertificateVendor(name="Let's Encrypt", website="https://letsencrypt.org"),
                CertificateVendor(name="Comodo", contact_email="ssl@comodo.com"),
            ]
            for v in vendors:
                db.add(v)
            db.flush()
            
            # Certificates
            certs_data = [
                {"name": "www.company.com SSL", "domain": "www.company.com", "cert_type": CertificateType.SSL_TLS, "expiry": date.today() + timedelta(days=5)},
                {"name": "api.company.com SSL", "domain": "api.company.com", "cert_type": CertificateType.SSL_TLS, "expiry": date.today() + timedelta(days=25)},
                {"name": "mail.company.com SSL", "domain": "mail.company.com", "cert_type": CertificateType.SSL_TLS, "expiry": date.today() + timedelta(days=90)},
                {"name": "*.company.com Wildcard", "domain": "*.company.com", "cert_type": CertificateType.WILDCARD, "expiry": date.today() + timedelta(days=180)},
                {"name": "코드 서명 인증서", "domain": None, "cert_type": CertificateType.CODE_SIGNING, "expiry": date.today() - timedelta(days=10)},
                {"name": "내부 CA 인증서", "domain": "internal.company.com", "cert_type": CertificateType.SSL_TLS, "expiry": date.today() + timedelta(days=365)},
            ]
            
            for cert_data in certs_data:
                expiry = cert_data["expiry"]
                today = date.today()
                if expiry < today:
                    status = CertificateStatus.EXPIRED
                elif expiry <= today + timedelta(days=30):
                    status = CertificateStatus.EXPIRING_SOON
                else:
                    status = CertificateStatus.ACTIVE
                
                cert = Certificate(
                    name=cert_data["name"],
                    domain=cert_data.get("domain"),
                    cert_type=cert_data["cert_type"],
                    status=status,
                    expiry_date=expiry,
                    issued_date=expiry - timedelta(days=365),
                    vendor_id=vendors[0].id,
                    renewal_reminder_days=30
                )
                db.add(cert)
            db.flush()
            
            # PC Assets
            pc_data_list = [
                {"asset_tag": "PC-2024-001", "hostname": "WIN-DEV001", "computer_name": "개발PC-김철수", "os_name": "Windows 11 Pro", "manufacturer": "Dell", "model": "Latitude 5520", "security_score": 85, "antivirus_installed": True, "firewall_enabled": True, "disk_encrypted": True},
                {"asset_tag": "PC-2024-002", "hostname": "WIN-DEV002", "computer_name": "개발PC-이영희", "os_name": "Windows 11 Pro", "manufacturer": "HP", "model": "EliteBook 840", "security_score": 70, "antivirus_installed": True, "firewall_enabled": True, "disk_encrypted": False},
                {"asset_tag": "PC-2024-003", "hostname": "WIN-INF001", "computer_name": "인프라PC-박지민", "os_name": "Windows 10 Pro", "manufacturer": "Lenovo", "model": "ThinkPad T14", "security_score": 45, "antivirus_installed": False, "firewall_enabled": True, "disk_encrypted": False},
                {"asset_tag": "PC-2024-004", "hostname": "WIN-SEC001", "computer_name": "보안PC-최보안", "os_name": "Windows 11 Pro", "manufacturer": "Dell", "model": "Precision 5560", "security_score": 95, "antivirus_installed": True, "firewall_enabled": True, "disk_encrypted": True},
                {"asset_tag": "PC-2024-005", "hostname": "WIN-PLAN001", "computer_name": "기획PC-정기획", "os_name": "Windows 11 Home", "manufacturer": "Samsung", "model": "Galaxy Book3", "security_score": 60, "antivirus_installed": True, "firewall_enabled": False, "disk_encrypted": False},
            ]
            
            for pc_info in pc_data_list:
                pc = PCAsset(
                    agent_token=secrets.token_urlsafe(32),
                    last_heartbeat=datetime.utcnow() - timedelta(minutes=2),
                    is_online=True,
                    cpu_info="Intel Core i7-1165G7",
                    ram_gb=16.0,
                    ip_address=f"192.168.1.{100 + pc_data_list.index(pc_info)}",
                    mac_address=f"00:1A:2B:{pc_data_list.index(pc_info):02d}:3C:4D",
                    status=PCStatus.ACTIVE,
                    **pc_info
                )
                db.add(pc)
                db.flush()
                
                # Add activities
                for i in range(5):
                    act = PCActivity(
                        pc_asset_id=pc.id,
                        activity_type="login",
                        user_account="administrator",
                        started_at=datetime.utcnow() - timedelta(hours=i*2),
                        ended_at=datetime.utcnow() - timedelta(hours=i*2-1),
                        duration_seconds=3600
                    )
                    db.add(act)
            
            # Security events
            security_events = [
                PCSecurityEvent(pc_asset_id=1, event_type="unauthorized_software", severity=SecurityLevel.HIGH, title="미승인 소프트웨어 감지", description="BitTorrent 클라이언트가 감지되었습니다."),
                PCSecurityEvent(pc_asset_id=3, event_type="no_antivirus", severity=SecurityLevel.CRITICAL, title="안티바이러스 미설치", description="안티바이러스 소프트웨어가 설치되어 있지 않습니다."),
                PCSecurityEvent(pc_asset_id=5, event_type="firewall_disabled", severity=SecurityLevel.HIGH, title="방화벽 비활성화", description="Windows 방화벽이 비활성화되어 있습니다."),
            ]
            for event in security_events:
                db.add(event)
            
            # Notifications
            notifs = [
                Notification(type=NotificationType.CERTIFICATE_EXPIRY, priority=NotificationPriority.CRITICAL, title="긴급: 인증서 5일 내 만료", message="www.company.com SSL 인증서가 5일 후 만료됩니다.", channel=NotificationChannel.SYSTEM),
                Notification(type=NotificationType.SECURITY_ALERT, priority=NotificationPriority.HIGH, title="보안 경고: 미승인 소프트웨어", message="WIN-DEV001에서 미승인 소프트웨어가 감지되었습니다.", channel=NotificationChannel.SYSTEM),
                Notification(type=NotificationType.PC_OFFLINE, priority=NotificationPriority.MEDIUM, title="PC 오프라인 감지", message="WIN-INF002가 24시간 이상 오프라인 상태입니다.", channel=NotificationChannel.SYSTEM),
            ]
            for notif in notifs:
                db.add(notif)
            
            db.commit()
            logger.info("✅ Initial data created successfully!")
    except Exception as e:
        logger.error(f"Error creating initial data: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Start background scheduler for periodic tasks"""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(
        check_certificate_expiry,
        trigger=IntervalTrigger(hours=24),
        id="cert_check",
        name="Certificate Expiry Check",
        replace_existing=True
    )
    
    scheduler.add_job(
        check_pc_offline,
        trigger=IntervalTrigger(minutes=10),
        id="pc_offline_check",
        name="PC Offline Check",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("📅 Scheduler started")


async def check_certificate_expiry():
    """Check and notify certificate expiry"""
    from app.core.database import SessionLocal
    from app.models.certificate import Certificate
    from app.models.notification import Notification, NotificationType, NotificationChannel, NotificationPriority
    from datetime import date, timedelta
    
    db = SessionLocal()
    try:
        today = date.today()
        expiring = db.query(Certificate).filter(
            Certificate.expiry_date <= today + timedelta(days=30),
            Certificate.expiry_date >= today
        ).all()
        
        for cert in expiring:
            days_left = (cert.expiry_date - today).days
            priority = NotificationPriority.CRITICAL if days_left <= 7 else NotificationPriority.HIGH
            
            existing = db.query(Notification).filter(
                Notification.related_id == cert.id,
                Notification.related_type == "certificate",
                Notification.type == NotificationType.CERTIFICATE_EXPIRY,
                Notification.created_at >= (datetime.utcnow() - timedelta(days=1)).replace(hour=0, minute=0)
            ).first()
            
            if not existing:
                notif = Notification(
                    type=NotificationType.CERTIFICATE_EXPIRY,
                    priority=priority,
                    title=f"인증서 만료 {days_left}일 전: {cert.name}",
                    message=f"{cert.domain or cert.name} 인증서가 {days_left}일 후 만료됩니다.",
                    related_type="certificate",
                    related_id=cert.id,
                    channel=NotificationChannel.SYSTEM
                )
                db.add(notif)
        
        db.commit()
    except Exception as e:
        logger.error(f"Certificate check error: {e}")
        db.rollback()
    finally:
        db.close()


async def check_pc_offline():
    """Check and notify offline PCs"""
    from app.core.database import SessionLocal
    from app.models.pc import PCAsset
    from app.models.notification import Notification, NotificationType, NotificationChannel, NotificationPriority
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        threshold = datetime.utcnow() - timedelta(hours=24)
        
        db.query(PCAsset).filter(
            PCAsset.last_heartbeat < datetime.utcnow() - timedelta(minutes=5),
            PCAsset.is_online == True
        ).update({"is_online": False})
        db.commit()
    except Exception as e:
        logger.error(f"PC offline check error: {e}")
        db.rollback()
    finally:
        db.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="기업 자산 관리 시스템 API",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(certificates.router, prefix="/api/v1")
app.include_router(pcs.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "AssetGuard Enterprise API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


from datetime import datetime
