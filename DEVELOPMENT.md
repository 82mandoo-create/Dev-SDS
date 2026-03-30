# Development Notes - AssetGuard Enterprise

## Changes from Main Branch

### Fixed Issues
1. **Vite allowedHosts**: Changed from `'all'` string to `true` boolean in `vite.config.ts`
   - This fixed the 403 Forbidden errors for external domain access in Vite 5.x
   
2. **Agent Secret Key**: Fixed `agent_config.json` to use `agent-secret-key-2024`
   - Previously had `agent-communication-secret-key-2024` which caused 401 Unauthorized
   
3. **PC Heartbeat Security Events**: Backend automatically creates security events when
   heartbeat reports missing antivirus or disabled firewall

### System Architecture

```
AssetGuard Enterprise
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/v1/            # REST API endpoints
│   │   │   ├── auth.py        # Authentication & TOTP
│   │   │   ├── employees.py   # Employee & department management
│   │   │   ├── certificates.py # Certificate lifecycle
│   │   │   ├── pcs.py         # PC asset & agent endpoints
│   │   │   ├── notifications.py # Notification management
│   │   │   ├── dashboard.py   # Dashboard & AI insights
│   │   │   └── users.py       # User management
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── ai_service.py  # Local AI analysis (rule-based)
│   │   │   └── email_service.py # SMTP email notifications
│   │   └── core/              # Config, database, security utils
│   └── requirements.txt
│
├── frontend/                  # React 18 + TypeScript
│   ├── src/
│   │   ├── pages/             # 10 application pages
│   │   ├── components/        # Layout component
│   │   ├── api/client.ts      # Axios client with auth interceptors
│   │   └── stores/authStore.ts # Zustand auth state
│   └── vite.config.ts         # allowedHosts: true (critical fix)
│
└── agent/                     # PC monitoring agent
    ├── agent.py               # Cross-platform Python agent
    └── agent_config.json      # Config with correct secret key
```

### API Endpoints Summary
- 16 admin/auth endpoints tested and working
- 5 agent endpoints (register, heartbeat, activities, applications, security-event)
- WebSocket endpoint for real-time PC monitoring

### Demo Data Seeded on Startup
- 3 users (admin, manager, user)
- 6 departments
- 8 employees
- 3 certificate vendors + 6 certificates
- 5 PC assets with activities
- 3 security events
- 3 notifications
