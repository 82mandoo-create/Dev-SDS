from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import Optional, List
from datetime import datetime, date, timedelta
from app.core.database import get_db
from app.models.certificate import Certificate, CertificateVendor, CertificateStatus, CertificateType
from app.models.user import User
from app.models.activity import AuditLog
from app.schemas.certificate import (
    CertificateCreate, CertificateUpdate, CertificateResponse,
    VendorCreate, VendorUpdate, VendorResponse
)
from app.utils.deps import get_current_active_user, require_manager, require_admin
from app.services.ai_service import predict_certificate_renewals

router = APIRouter(prefix="/certificates", tags=["Certificates"])


def calculate_status(expiry_date: date, reminder_days: int = 30) -> CertificateStatus:
    today = date.today()
    if expiry_date < today:
        return CertificateStatus.EXPIRED
    elif expiry_date <= today + timedelta(days=reminder_days):
        return CertificateStatus.EXPIRING_SOON
    return CertificateStatus.ACTIVE


# Vendor endpoints
@router.get("/vendors", response_model=List[VendorResponse])
async def get_vendors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return db.query(CertificateVendor).all()


@router.post("/vendors", response_model=VendorResponse)
async def create_vendor(
    data: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    vendor = CertificateVendor(**data.model_dump())
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.put("/vendors/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: int,
    data: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    vendor = db.query(CertificateVendor).filter(CertificateVendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="업체를 찾을 수 없습니다.")
    
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(vendor, key, value)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.delete("/vendors/{vendor_id}")
async def delete_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    vendor = db.query(CertificateVendor).filter(CertificateVendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="업체를 찾을 수 없습니다.")
    db.delete(vendor)
    db.commit()
    return {"message": "업체가 삭제되었습니다."}


# Certificate endpoints
@router.get("", response_model=dict)
async def get_certificates(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    cert_type: Optional[CertificateType] = None,
    status: Optional[CertificateStatus] = None,
    expiring_days: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Certificate)
    
    if search:
        query = query.filter(
            or_(
                Certificate.name.ilike(f"%{search}%"),
                Certificate.domain.ilike(f"%{search}%"),
                Certificate.issuer.ilike(f"%{search}%")
            )
        )
    
    if cert_type:
        query = query.filter(Certificate.cert_type == cert_type)
    
    if status:
        query = query.filter(Certificate.status == status)
    
    if expiring_days:
        cutoff = date.today() + timedelta(days=expiring_days)
        query = query.filter(Certificate.expiry_date <= cutoff)
    
    total = query.count()
    certs = query.offset((page - 1) * limit).limit(limit).all()
    
    result = []
    for cert in certs:
        cert_data = CertificateResponse.model_validate(cert)
        if cert.expiry_date:
            days_until = (cert.expiry_date - date.today()).days
            cert_data.days_until_expiry = days_until
            cert.status = calculate_status(cert.expiry_date, cert.renewal_reminder_days)
        result.append(cert_data)
    
    db.commit()
    
    return {"total": total, "page": page, "limit": limit, "items": result}


@router.post("", response_model=CertificateResponse)
async def create_certificate(
    data: CertificateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    cert_dict = data.model_dump()
    cert_dict["status"] = calculate_status(data.expiry_date, data.renewal_reminder_days)
    
    cert = Certificate(**cert_dict)
    db.add(cert)
    db.commit()
    db.refresh(cert)
    
    log = AuditLog(
        user_id=current_user.id,
        action="CREATE_CERTIFICATE",
        resource_type="certificate",
        resource_id=cert.id,
        description=f"인증서 등록: {cert.name}"
    )
    db.add(log)
    db.commit()
    
    cert_data = CertificateResponse.model_validate(cert)
    cert_data.days_until_expiry = (cert.expiry_date - date.today()).days
    return cert_data


@router.get("/{cert_id}", response_model=CertificateResponse)
async def get_certificate(
    cert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="인증서를 찾을 수 없습니다.")
    
    cert_data = CertificateResponse.model_validate(cert)
    if cert.expiry_date:
        cert_data.days_until_expiry = (cert.expiry_date - date.today()).days
    return cert_data


@router.put("/{cert_id}", response_model=CertificateResponse)
async def update_certificate(
    cert_id: int,
    data: CertificateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="인증서를 찾을 수 없습니다.")
    
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(cert, key, value)
    
    if cert.expiry_date:
        cert.status = calculate_status(cert.expiry_date, cert.renewal_reminder_days)
    
    db.commit()
    db.refresh(cert)
    
    cert_data = CertificateResponse.model_validate(cert)
    if cert.expiry_date:
        cert_data.days_until_expiry = (cert.expiry_date - date.today()).days
    return cert_data


@router.delete("/{cert_id}")
async def delete_certificate(
    cert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="인증서를 찾을 수 없습니다.")
    db.delete(cert)
    db.commit()
    return {"message": "인증서가 삭제되었습니다."}


@router.get("/stats/summary")
async def get_certificate_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    today = date.today()
    total = db.query(Certificate).count()
    active = db.query(Certificate).filter(Certificate.status == CertificateStatus.ACTIVE).count()
    expired = db.query(Certificate).filter(Certificate.status == CertificateStatus.EXPIRED).count()
    
    expiring_7 = db.query(Certificate).filter(
        Certificate.expiry_date <= today + timedelta(days=7),
        Certificate.expiry_date >= today
    ).count()
    
    expiring_30 = db.query(Certificate).filter(
        Certificate.expiry_date <= today + timedelta(days=30),
        Certificate.expiry_date >= today
    ).count()
    
    by_type = db.query(
        Certificate.cert_type, func.count(Certificate.id).label("count")
    ).group_by(Certificate.cert_type).all()
    
    return {
        "total": total,
        "active": active,
        "expired": expired,
        "expiring_7_days": expiring_7,
        "expiring_30_days": expiring_30,
        "by_type": [{"type": t[0], "count": t[1]} for t in by_type]
    }


@router.get("/ai/renewal-predictions")
async def get_renewal_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """AI 기반 인증서 갱신 예측"""
    certs = db.query(Certificate).filter(
        Certificate.status != CertificateStatus.EXPIRED
    ).all()
    
    cert_list = [
        {"id": c.id, "name": c.name, "expiry_date": str(c.expiry_date)}
        for c in certs
    ]
    
    predictions = predict_certificate_renewals(cert_list)
    return {"predictions": predictions, "total": len(predictions)}
