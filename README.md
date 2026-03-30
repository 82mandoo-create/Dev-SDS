# 🛡️ AssetGuard Enterprise - 기업 자산 관리 시스템

## 📋 시스템 개요

AssetGuard Enterprise는 기업의 디지털 자산을 통합 관리하는 엔터프라이즈 솔루션입니다.

### 주요 기능

| 기능 | 설명 |
|------|------|
| **1. 직원 관리** | 부서별 직원 정보, 재직 상태, 연락처 관리 |
| **2. 인증서 관리** | SSL/TLS, 코드서명 등 인증서 도입/갱신/만료 알림 |
| **3. PC 관리** | 에이전트 기반 PC 상태 수집 (로그인, 절전, 앱, 보안) |
| **4. 대시보드** | 실시간 현황 차트 및 조회 서비스 |
| **5. AI 분석** | 보안 위협 자동 감지, 인증서 갱신 예측 |
| **6. 알림 서비스** | PC 팝업 알림, 이메일 알림, 시스템 알림 |

---

## 🚀 시작하기

### 사전 요구사항

- Python 3.10+
- Node.js 18+

### 백엔드 실행

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

### 기본 접속 정보

| 역할 | 이메일 | 비밀번호 |
|------|--------|----------|
| 관리자 | admin@company.com | Admin@123456 |
| 매니저 | manager@company.com | Manager@123 |
| 사용자 | user@company.com | User@123456 |

---

## 🖥️ PC 에이전트 설치 가이드

### Windows 설치

```powershell
# 1. Python 설치 확인
python --version

# 2. 에이전트 파일 복사
# agent/ 폴더를 C:\AssetGuard\ 에 복사

# 3. 의존성 설치
cd C:\AssetGuard
pip install requests psutil win10toast

# 4. 서버 설정
# agent_config.json 에서 server_url 수정:
# { "server_url": "http://YOUR_SERVER_IP:8000" }

# 5. 에이전트 등록 및 실행
python agent.py register
python agent.py

# 6. Windows 서비스로 등록 (선택)
sc create AssetGuardAgent binPath= "python C:\AssetGuard\agent.py"
sc start AssetGuardAgent
```

### Linux/macOS 설치

```bash
# 1. 의존성 설치
pip3 install requests psutil

# 2. 서버 설정
nano agent_config.json
# server_url을 실제 서버 주소로 변경

# 3. 실행
python3 agent.py register
python3 agent.py

# 4. 서비스 등록 (systemd)
sudo tee /etc/systemd/system/assetguard.service << EOF
[Unit]
Description=AssetGuard Agent
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/assetguard/agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable assetguard
sudo systemctl start assetguard
```

### 에이전트 설정 파일 (agent_config.json)

```json
{
  "server_url": "http://YOUR_SERVER_IP:8000",
  "agent_secret": "agent-secret-key-2024",
  "heartbeat_interval": 60,
  "activity_report_interval": 300,
  "app_scan_interval": 3600,
  "log_level": "INFO"
}
```

---

## 🏗️ 기술 스택

### 백엔드
- **FastAPI** - REST API 서버
- **SQLAlchemy** - ORM (SQLite/PostgreSQL)
- **JWT** - 인증/인가
- **APScheduler** - 자동 작업 스케줄러
- **SMTP** - 이메일 알림

### 프론트엔드
- **React 18** + **TypeScript**
- **Vite** - 빌드 도구
- **TailwindCSS** - UI 스타일링
- **Recharts** - 데이터 시각화
- **TanStack Query** - 서버 상태 관리
- **Zustand** - 클라이언트 상태 관리

### PC 에이전트
- **Python** - 멀티플랫폼 지원
- **psutil** - 시스템 모니터링
- **requests** - API 통신
- **win10toast** - Windows 팝업 알림

---

## 📡 API 문서

서버 실행 후 접속: http://localhost:8000/docs

### 주요 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | /api/v1/auth/login | 로그인 |
| GET | /api/v1/dashboard/summary | 대시보드 요약 |
| GET | /api/v1/employees | 직원 목록 |
| GET | /api/v1/certificates | 인증서 목록 |
| GET | /api/v1/pcs | PC 목록 |
| POST | /api/v1/pcs/agent/register | 에이전트 등록 |
| POST | /api/v1/pcs/agent/heartbeat | 에이전트 하트비트 |
| GET | /api/v1/notifications | 알림 목록 |
| GET | /api/v1/dashboard/ai-insights | AI 인사이트 |

---

## 🔒 보안 기능

- **JWT 인증** (Access Token + Refresh Token)
- **2단계 인증** (TOTP - Google Authenticator 호환)
- **이메일 인증** (신규 가입 시)
- **로그인 실패 잠금** (5회 실패 시 30분 잠금)
- **감사 로그** (모든 중요 작업 기록)
- **역할 기반 접근 제어** (Admin / Manager / User)

---

## 🤖 AI 기능

1. **보안 점수 자동 계산** - PC 보안 설정 기반
2. **이상 행동 감지** - 비업무 시간 로그인 탐지
3. **인증서 갱신 우선순위 예측** - 만료일 기반 AI 분류
4. **보안 인사이트 생성** - 전체 현황 자동 분석
5. **OpenAI 연동** (선택) - OPENAI_API_KEY 설정 시 GPT 기반 고급 분석

---

## 📧 이메일 알림 설정

backend/.env 파일 생성:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=noreply@yourcompany.com
```

---

## 📊 수집 정보

### PC 활동 수집 항목
- 로그인/로그아웃 시간 및 사용자
- 절전 모드 시작/해제
- 설치된 애플리케이션 목록
- 실행 중인 프로세스
- 보안 상태 (안티바이러스, 방화벽, 디스크 암호화)
- 네트워크 IP 주소

---

*AssetGuard Enterprise v1.0.0 | 2024*
