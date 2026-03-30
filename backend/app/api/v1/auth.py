from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import pyotp
import qrcode
import io
import base64
from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    decode_token, generate_verification_code, generate_random_password
)
from app.core.config import settings
from app.models.user import User, UserStatus, UserRole
from app.models.activity import AuditLog
from app.schemas.user import (
    UserCreate, UserResponse, LoginRequest, TokenResponse,
    EmailVerifyRequest, PasswordResetRequest, PasswordResetConfirm,
    ChangePasswordRequest, TOTPSetupResponse, TOTPVerifyRequest
)
from app.utils.deps import get_current_user, get_current_active_user
from app.services.email_service import send_verification_email, send_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """사용자 등록"""
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    
    code = generate_verification_code()
    expires = datetime.utcnow() + timedelta(minutes=10)
    
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        status=UserStatus.PENDING,
        verification_code=code,
        verification_expires=expires
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    background_tasks.add_task(send_verification_email, user.email, user.full_name, code)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """로그인"""
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.status = UserStatus.LOCKED
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            db.commit()
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    
    if user.status == UserStatus.LOCKED:
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(status_code=403, detail=f"계정이 잠겨있습니다. {user.locked_until.strftime('%H:%M')}에 잠금이 해제됩니다.")
        else:
            user.status = UserStatus.ACTIVE
            user.failed_login_attempts = 0
    
    if user.status == UserStatus.INACTIVE:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다.")
    
    if user.status == UserStatus.PENDING:
        raise HTTPException(status_code=403, detail="이메일 인증이 필요합니다.")
    
    if user.totp_enabled:
        if not login_data.totp_code:
            raise HTTPException(status_code=400, detail="2단계 인증 코드가 필요합니다.")
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(login_data.totp_code):
            raise HTTPException(status_code=401, detail="2단계 인증 코드가 올바르지 않습니다.")
    
    user.last_login = datetime.utcnow()
    user.failed_login_attempts = 0
    
    log = AuditLog(
        user_id=user.id,
        action="LOGIN",
        description=f"로그인 성공",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500]
    )
    db.add(log)
    db.commit()
    
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/verify-email")
async def verify_email(verify_data: EmailVerifyRequest, db: Session = Depends(get_db)):
    """이메일 인증"""
    user = db.query(User).filter(User.email == verify_data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    if user.email_verified:
        return {"message": "이미 인증된 이메일입니다."}
    
    if not user.verification_code or user.verification_code != verify_data.code:
        raise HTTPException(status_code=400, detail="인증 코드가 올바르지 않습니다.")
    
    if user.verification_expires and user.verification_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="인증 코드가 만료되었습니다. 재발송해주세요.")
    
    user.email_verified = True
    user.status = UserStatus.ACTIVE
    user.verification_code = None
    user.verification_expires = None
    db.commit()
    
    return {"message": "이메일 인증이 완료되었습니다."}


@router.post("/resend-verification")
async def resend_verification(
    data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """인증 코드 재발송"""
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        return {"message": "인증 코드를 발송했습니다."}
    
    if user.email_verified:
        return {"message": "이미 인증된 이메일입니다."}
    
    code = generate_verification_code()
    user.verification_code = code
    user.verification_expires = datetime.utcnow() + timedelta(minutes=10)
    db.commit()
    
    background_tasks.add_task(send_verification_email, user.email, user.full_name, code)
    return {"message": "인증 코드를 발송했습니다."}


@router.post("/forgot-password")
async def forgot_password(
    data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """비밀번호 재설정 요청"""
    user = db.query(User).filter(User.email == data.email).first()
    if user:
        import secrets
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        subject = "[AssetGuard] 비밀번호 재설정"
        body = f"""
        <p>비밀번호 재설정을 요청하셨습니다.</p>
        <p><a href="{reset_url}">여기를 클릭하여 비밀번호를 재설정하세요.</a></p>
        <p>이 링크는 1시간 후 만료됩니다.</p>
        """
        background_tasks.add_task(send_email, user.email, subject, body, user.full_name)
    
    return {"message": "비밀번호 재설정 이메일을 발송했습니다."}


@router.post("/reset-password")
async def reset_password(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    """비밀번호 재설정"""
    user = db.query(User).filter(User.reset_token == data.token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="유효하지 않거나 만료된 토큰입니다.")
    
    user.hashed_password = get_password_hash(data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    return {"message": "비밀번호가 변경되었습니다."}


@router.post("/refresh")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """토큰 갱신"""
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
    
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """현재 사용자 정보"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """현재 사용자 정보 수정"""
    allowed = ["full_name", "phone"]
    for key, value in data.items():
        if key in allowed:
            setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """비밀번호 변경"""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다.")
    
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"message": "비밀번호가 변경되었습니다."}


@router.post("/setup-totp", response_model=TOTPSetupResponse)
async def setup_totp(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """TOTP 2단계 인증 설정"""
    secret = pyotp.random_base32()
    
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="AssetGuard Enterprise"
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_code_b64 = base64.b64encode(buffer.getvalue()).decode()
    
    import secrets
    backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
    
    current_user.totp_secret = secret
    db.commit()
    
    return TOTPSetupResponse(
        secret=secret,
        qr_code=f"data:image/png;base64,{qr_code_b64}",
        backup_codes=backup_codes
    )


@router.post("/verify-totp")
async def verify_totp(
    data: TOTPVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """TOTP 인증 확인 및 활성화"""
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="TOTP 설정이 필요합니다.")
    
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(data.code):
        raise HTTPException(status_code=400, detail="인증 코드가 올바르지 않습니다.")
    
    current_user.totp_enabled = True
    db.commit()
    
    return {"message": "2단계 인증이 활성화되었습니다."}


@router.post("/disable-totp")
async def disable_totp(
    data: TOTPVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """TOTP 비활성화"""
    if not current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="2단계 인증이 활성화되어 있지 않습니다.")
    
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(data.code):
        raise HTTPException(status_code=400, detail="인증 코드가 올바르지 않습니다.")
    
    current_user.totp_enabled = False
    current_user.totp_secret = None
    db.commit()
    
    return {"message": "2단계 인증이 비활성화되었습니다."}
