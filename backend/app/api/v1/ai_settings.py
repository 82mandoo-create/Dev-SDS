from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.models.user import User
from app.models.ai_config import AIConfig, AIProvider, AIConfigStatus
from app.utils.deps import get_current_active_user, require_admin

router = APIRouter(prefix="/ai-settings", tags=["AI Settings"])


# ─────────────────────── Schemas ───────────────────────

class AIConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider: AIProvider
    model_name: str = Field(..., min_length=1, max_length=100)
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    api_version: Optional[str] = None
    deployment_name: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    max_tokens: int = Field(default=2000, ge=100, le=32000)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    use_for_pc_analysis: bool = True
    use_for_cert_prediction: bool = True
    use_for_security_insights: bool = True
    use_for_anomaly_detection: bool = True
    description: Optional[str] = None


class AIConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    api_version: Optional[str] = None
    deployment_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    max_tokens: Optional[int] = Field(None, ge=100, le=32000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    use_for_pc_analysis: Optional[bool] = None
    use_for_cert_prediction: Optional[bool] = None
    use_for_security_insights: Optional[bool] = None
    use_for_anomaly_detection: Optional[bool] = None
    description: Optional[str] = None


def _mask_api_key(key: Optional[str]) -> Optional[str]:
    """API 키의 중간 부분을 마스킹하여 반환"""
    if not key:
        return None
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def _config_to_dict(cfg: AIConfig, mask_key: bool = True) -> dict:
    return {
        "id": cfg.id,
        "name": cfg.name,
        "provider": cfg.provider,
        "model_name": cfg.model_name,
        "api_key": _mask_api_key(cfg.api_key) if mask_key else cfg.api_key,
        "api_key_set": bool(cfg.api_key),
        "api_base_url": cfg.api_base_url,
        "api_version": cfg.api_version,
        "deployment_name": cfg.deployment_name,
        "is_active": cfg.is_active,
        "is_default": cfg.is_default,
        "status": cfg.status,
        "max_tokens": cfg.max_tokens,
        "temperature": cfg.temperature,
        "use_for_pc_analysis": cfg.use_for_pc_analysis,
        "use_for_cert_prediction": cfg.use_for_cert_prediction,
        "use_for_security_insights": cfg.use_for_security_insights,
        "use_for_anomaly_detection": cfg.use_for_anomaly_detection,
        "last_test_at": cfg.last_test_at.isoformat() if cfg.last_test_at else None,
        "last_test_result": cfg.last_test_result,
        "last_test_success": cfg.last_test_success,
        "total_requests": cfg.total_requests,
        "failed_requests": cfg.failed_requests,
        "last_used_at": cfg.last_used_at.isoformat() if cfg.last_used_at else None,
        "description": cfg.description,
        "created_at": cfg.created_at.isoformat() if cfg.created_at else None,
        "updated_at": cfg.updated_at.isoformat() if cfg.updated_at else None,
    }


# ─────────────────────── Endpoints ───────────────────────

@router.get("/")
async def list_ai_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """등록된 AI 설정 목록 조회 (admin 전용)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")
    configs = db.query(AIConfig).order_by(AIConfig.is_default.desc(), AIConfig.created_at.desc()).all()
    return {
        "total": len(configs),
        "data": [_config_to_dict(c) for c in configs],
    }


@router.get("/providers")
async def get_provider_info(
    current_user: User = Depends(get_current_active_user),
):
    """지원 AI 제공자 목록 및 모델 정보 반환"""
    return {
        "providers": [
            {
                "key": "openai",
                "label": "OpenAI (ChatGPT)",
                "icon": "🤖",
                "color": "#10a37f",
                "description": "OpenAI GPT-4, GPT-4o, GPT-3.5 Turbo 등",
                "requires_api_key": True,
                "requires_base_url": False,
                "models": [
                    {"id": "gpt-4o", "label": "GPT-4o (최신, 고성능)"},
                    {"id": "gpt-4o-mini", "label": "GPT-4o Mini (빠르고 저렴)"},
                    {"id": "gpt-4-turbo", "label": "GPT-4 Turbo"},
                    {"id": "gpt-4", "label": "GPT-4"},
                    {"id": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo (경제적)"},
                ],
                "api_key_placeholder": "sk-proj-...",
                "base_url_placeholder": None,
                "docs_url": "https://platform.openai.com/api-keys",
            },
            {
                "key": "gemini",
                "label": "Google Gemini",
                "icon": "✨",
                "color": "#4285f4",
                "description": "Google의 최신 멀티모달 AI 모델",
                "requires_api_key": True,
                "requires_base_url": False,
                "models": [
                    {"id": "gemini-2.0-flash", "label": "Gemini 2.0 Flash (최신, 빠름)"},
                    {"id": "gemini-2.0-flash-lite", "label": "Gemini 2.0 Flash-Lite (초경량)"},
                    {"id": "gemini-1.5-pro", "label": "Gemini 1.5 Pro (고성능)"},
                    {"id": "gemini-1.5-flash", "label": "Gemini 1.5 Flash (균형)"},
                    {"id": "gemini-1.5-flash-8b", "label": "Gemini 1.5 Flash-8B (경량)"},
                ],
                "api_key_placeholder": "AIza...",
                "base_url_placeholder": None,
                "docs_url": "https://aistudio.google.com/app/apikey",
            },
            {
                "key": "claude",
                "label": "Anthropic Claude",
                "icon": "🧠",
                "color": "#d97706",
                "description": "Anthropic Claude 3.x 시리즈 - 안전하고 정확한 분석",
                "requires_api_key": True,
                "requires_base_url": False,
                "models": [
                    {"id": "claude-opus-4-5", "label": "Claude Opus 4.5 (최고 성능)"},
                    {"id": "claude-sonnet-4-5", "label": "Claude Sonnet 4.5 (균형)"},
                    {"id": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet"},
                    {"id": "claude-3-5-haiku-20241022", "label": "Claude 3.5 Haiku (빠름)"},
                    {"id": "claude-3-opus-20240229", "label": "Claude 3 Opus"},
                    {"id": "claude-3-haiku-20240307", "label": "Claude 3 Haiku (경제적)"},
                ],
                "api_key_placeholder": "sk-ant-...",
                "base_url_placeholder": None,
                "docs_url": "https://console.anthropic.com/settings/keys",
            },
            {
                "key": "ollama",
                "label": "Ollama (로컬 AI)",
                "icon": "🖥️",
                "color": "#7c3aed",
                "description": "로컬 서버에 자체 구축한 오픈소스 AI 모델",
                "requires_api_key": False,
                "requires_base_url": True,
                "models": [
                    {"id": "llama3.2", "label": "Llama 3.2 (Meta)"},
                    {"id": "llama3.1", "label": "Llama 3.1 (Meta)"},
                    {"id": "qwen2.5", "label": "Qwen 2.5 (Alibaba)"},
                    {"id": "mistral", "label": "Mistral 7B"},
                    {"id": "gemma2", "label": "Gemma 2 (Google)"},
                    {"id": "phi3", "label": "Phi-3 (Microsoft)"},
                    {"id": "deepseek-r1", "label": "DeepSeek-R1"},
                    {"id": "custom", "label": "직접 입력 (커스텀 모델명)"},
                ],
                "api_key_placeholder": None,
                "base_url_placeholder": "http://localhost:11434",
                "docs_url": "https://ollama.com",
            },
            {
                "key": "azure_openai",
                "label": "Azure OpenAI",
                "icon": "☁️",
                "color": "#0078d4",
                "description": "Microsoft Azure에서 호스팅하는 OpenAI 서비스",
                "requires_api_key": True,
                "requires_base_url": True,
                "models": [
                    {"id": "gpt-4o", "label": "GPT-4o (Azure 배포)"},
                    {"id": "gpt-4", "label": "GPT-4 (Azure 배포)"},
                    {"id": "gpt-35-turbo", "label": "GPT-3.5 Turbo (Azure 배포)"},
                ],
                "api_key_placeholder": "Azure API Key",
                "base_url_placeholder": "https://<resource>.openai.azure.com",
                "docs_url": "https://portal.azure.com",
            },
            {
                "key": "custom",
                "label": "커스텀 (OpenAI 호환)",
                "icon": "⚙️",
                "color": "#6b7280",
                "description": "OpenAI API 형식을 지원하는 커스텀 엔드포인트",
                "requires_api_key": True,
                "requires_base_url": True,
                "models": [
                    {"id": "custom", "label": "직접 입력"},
                ],
                "api_key_placeholder": "API Key (없으면 빈칸))",
                "base_url_placeholder": "http://your-server/v1",
                "docs_url": None,
            },
        ]
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_ai_config(
    data: AIConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """AI 설정 등록 (admin 전용)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")

    # is_default = True 설정 시 기존 default 해제
    if data.is_default:
        db.query(AIConfig).filter(AIConfig.is_default == True).update({"is_default": False})

    cfg = AIConfig(
        **data.model_dump(),
        status=AIConfigStatus.INACTIVE,
        created_by=current_user.id,
    )
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return _config_to_dict(cfg)


@router.get("/{config_id}")
async def get_ai_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """AI 설정 단건 조회"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")
    cfg = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="설정을 찾을 수 없습니다.")
    return _config_to_dict(cfg)


@router.put("/{config_id}")
async def update_ai_config(
    config_id: int,
    data: AIConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """AI 설정 수정 (admin 전용)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")
    cfg = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="설정을 찾을 수 없습니다.")

    update_data = data.model_dump(exclude_unset=True)

    # is_default = True 설정 시 기존 default 해제
    if update_data.get("is_default"):
        db.query(AIConfig).filter(
            AIConfig.is_default == True,
            AIConfig.id != config_id
        ).update({"is_default": False})

    for key, value in update_data.items():
        setattr(cfg, key, value)

    cfg.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cfg)
    return _config_to_dict(cfg)


@router.delete("/{config_id}")
async def delete_ai_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """AI 설정 삭제 (admin 전용)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")
    cfg = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="설정을 찾을 수 없습니다.")
    db.delete(cfg)
    db.commit()
    return {"message": "삭제되었습니다."}


@router.post("/{config_id}/test")
async def test_ai_connection(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """AI API 연결 테스트"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")
    cfg = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="설정을 찾을 수 없습니다.")

    cfg.status = AIConfigStatus.TESTING
    db.commit()

    result = await _run_connection_test(cfg)

    cfg.last_test_at = datetime.utcnow()
    cfg.last_test_success = result["success"]
    cfg.last_test_result = result["message"]
    cfg.status = AIConfigStatus.ACTIVE if result["success"] else AIConfigStatus.ERROR
    db.commit()
    db.refresh(cfg)

    return {
        "success": result["success"],
        "message": result["message"],
        "response_preview": result.get("preview"),
        "latency_ms": result.get("latency_ms"),
        "config": _config_to_dict(cfg),
    }


@router.post("/{config_id}/set-default")
async def set_default_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """기본 AI 설정 변경"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")
    cfg = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="설정을 찾을 수 없습니다.")
    if not cfg.is_active:
        raise HTTPException(status_code=400, detail="비활성화된 설정은 기본으로 설정할 수 없습니다.")

    db.query(AIConfig).filter(AIConfig.is_default == True).update({"is_default": False})
    cfg.is_default = True
    db.commit()
    return {"message": f"'{cfg.name}'이(가) 기본 AI로 설정되었습니다."}


@router.get("/stats/summary")
async def get_ai_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """AI 설정 통계 요약"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")
    
    total = db.query(AIConfig).count()
    active = db.query(AIConfig).filter(AIConfig.is_active == True).count()
    by_provider = {}
    for cfg in db.query(AIConfig).all():
        p = cfg.provider
        if p not in by_provider:
            by_provider[p] = 0
        by_provider[p] += 1

    default_cfg = db.query(AIConfig).filter(AIConfig.is_default == True).first()

    return {
        "total": total,
        "active": active,
        "inactive": total - active,
        "by_provider": by_provider,
        "default": _config_to_dict(default_cfg) if default_cfg else None,
    }


# ─────────────────────── Connection Test Logic ───────────────────────

async def _run_connection_test(cfg: AIConfig) -> dict:
    """실제 AI 제공자에 테스트 요청 전송"""
    import time
    start = time.time()
    test_prompt = "AssetGuard 시스템 연결 테스트입니다. '연결 성공'이라고 한국어로 짧게 답하세요."

    try:
        if cfg.provider == AIProvider.OPENAI:
            result = await _test_openai(cfg, test_prompt)
        elif cfg.provider == AIProvider.GEMINI:
            result = await _test_gemini(cfg, test_prompt)
        elif cfg.provider == AIProvider.CLAUDE:
            result = await _test_claude(cfg, test_prompt)
        elif cfg.provider == AIProvider.OLLAMA:
            result = await _test_ollama(cfg, test_prompt)
        elif cfg.provider == AIProvider.AZURE_OPENAI:
            result = await _test_azure_openai(cfg, test_prompt)
        elif cfg.provider == AIProvider.CUSTOM:
            result = await _test_custom(cfg, test_prompt)
        else:
            result = {"success": False, "message": "지원하지 않는 제공자입니다."}

        result["latency_ms"] = round((time.time() - start) * 1000)
        return result
    except Exception as e:
        return {
            "success": False,
            "message": f"연결 테스트 중 오류 발생: {str(e)}",
            "latency_ms": round((time.time() - start) * 1000),
        }


async def _test_openai(cfg: AIConfig, prompt: str) -> dict:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=cfg.api_key)
        resp = await client.chat.completions.create(
            model=cfg.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0,
        )
        preview = resp.choices[0].message.content
        return {"success": True, "message": f"OpenAI 연결 성공 (모델: {cfg.model_name})", "preview": preview}
    except Exception as e:
        return {"success": False, "message": f"OpenAI 연결 실패: {str(e)}"}


async def _test_gemini(cfg: AIConfig, prompt: str) -> dict:
    try:
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{cfg.model_name}:generateContent"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 50}
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                json=payload,
                params={"key": cfg.api_key},
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            preview = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"success": True, "message": f"Gemini 연결 성공 (모델: {cfg.model_name})", "preview": preview}
    except Exception as e:
        return {"success": False, "message": f"Gemini 연결 실패: {str(e)}"}


async def _test_claude(cfg: AIConfig, prompt: str) -> dict:
    try:
        import httpx
        headers = {
            "x-api-key": cfg.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": cfg.model_name,
            "max_tokens": 50,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            preview = data["content"][0]["text"]
        return {"success": True, "message": f"Claude 연결 성공 (모델: {cfg.model_name})", "preview": preview}
    except Exception as e:
        return {"success": False, "message": f"Claude 연결 실패: {str(e)}"}


async def _test_ollama(cfg: AIConfig, prompt: str) -> dict:
    try:
        import httpx
        base_url = (cfg.api_base_url or "http://localhost:11434").rstrip("/")
        payload = {
            "model": cfg.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            preview = data["message"]["content"]
        return {"success": True, "message": f"Ollama 연결 성공 (모델: {cfg.model_name})", "preview": preview}
    except Exception as e:
        return {"success": False, "message": f"Ollama 연결 실패: {str(e)} (서버가 실행 중인지 확인하세요)"}


async def _test_azure_openai(cfg: AIConfig, prompt: str) -> dict:
    try:
        from openai import AsyncAzureOpenAI
        client = AsyncAzureOpenAI(
            api_key=cfg.api_key,
            azure_endpoint=cfg.api_base_url,
            api_version=cfg.api_version or "2024-02-01",
        )
        deployment = cfg.deployment_name or cfg.model_name
        resp = await client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0,
        )
        preview = resp.choices[0].message.content
        return {"success": True, "message": f"Azure OpenAI 연결 성공 (배포: {deployment})", "preview": preview}
    except Exception as e:
        return {"success": False, "message": f"Azure OpenAI 연결 실패: {str(e)}"}


async def _test_custom(cfg: AIConfig, prompt: str) -> dict:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=cfg.api_key or "dummy",
            base_url=cfg.api_base_url,
        )
        resp = await client.chat.completions.create(
            model=cfg.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0,
        )
        preview = resp.choices[0].message.content
        return {"success": True, "message": f"커스텀 엔드포인트 연결 성공 (모델: {cfg.model_name})", "preview": preview}
    except Exception as e:
        return {"success": False, "message": f"커스텀 엔드포인트 연결 실패: {str(e)}"}
