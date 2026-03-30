from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, Float
from datetime import datetime
from app.core.database import Base
import enum


class AIProvider(str, enum.Enum):
    OPENAI = "openai"           # GPT-4, GPT-4o, GPT-3.5
    GEMINI = "gemini"           # Google Gemini
    CLAUDE = "claude"           # Anthropic Claude
    OLLAMA = "ollama"           # Local Ollama (self-hosted)
    CUSTOM = "custom"           # Custom OpenAI-compatible endpoint
    AZURE_OPENAI = "azure_openai"  # Azure OpenAI Service


class AIConfigStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"


class AIConfig(Base):
    __tablename__ = "ai_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)           # 사용자 지정 이름 (예: "GPT-4 운영용")
    provider = Column(Enum(AIProvider), nullable=False)  # AI 제공자
    model_name = Column(String(100), nullable=False)     # 모델명 (예: gpt-4o-mini)
    
    # API 키 및 연결 정보 (암호화 저장 권장 - 현재는 평문)
    api_key = Column(Text, nullable=True)                # API Key
    api_base_url = Column(String(500), nullable=True)    # Base URL (Ollama/Custom/Azure용)
    api_version = Column(String(50), nullable=True)      # API 버전 (Azure용)
    deployment_name = Column(String(100), nullable=True) # Azure 배포명
    
    # 설정
    is_active = Column(Boolean, default=True)            # 활성화 여부
    is_default = Column(Boolean, default=False)          # 기본 AI로 사용
    status = Column(Enum(AIConfigStatus), default=AIConfigStatus.INACTIVE)
    
    # 파라미터
    max_tokens = Column(Integer, default=2000)
    temperature = Column(Float, default=0.3)
    
    # 사용 범위 설정
    use_for_pc_analysis = Column(Boolean, default=True)     # PC 보안 분석
    use_for_cert_prediction = Column(Boolean, default=True)  # 인증서 갱신 예측
    use_for_security_insights = Column(Boolean, default=True) # 보안 인사이트
    use_for_anomaly_detection = Column(Boolean, default=True) # 이상행동 탐지
    
    # 연결 테스트 결과
    last_test_at = Column(DateTime, nullable=True)
    last_test_result = Column(Text, nullable=True)       # 테스트 응답 메시지
    last_test_success = Column(Boolean, nullable=True)
    
    # 사용 통계
    total_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # 메모
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)  # User ID
