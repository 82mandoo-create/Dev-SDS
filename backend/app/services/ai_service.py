import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)


def analyze_pc_security_local(pc_data: Dict[str, Any]) -> Dict[str, Any]:
    """Local rule-based security analysis without AI"""
    score = 100
    issues = []
    recommendations = []
    risk_level = "low"
    
    if not pc_data.get("antivirus_installed"):
        score -= 25
        issues.append("안티바이러스 미설치")
        recommendations.append("즉시 안티바이러스 소프트웨어를 설치하세요.")
    
    if not pc_data.get("firewall_enabled"):
        score -= 15
        issues.append("방화벽 비활성화")
        recommendations.append("Windows 방화벽을 활성화하세요.")
    
    if not pc_data.get("disk_encrypted"):
        score -= 20
        issues.append("디스크 암호화 미적용")
        recommendations.append("BitLocker 또는 유사 솔루션으로 디스크를 암호화하세요.")
    
    if not pc_data.get("auto_update_enabled"):
        score -= 10
        issues.append("자동 업데이트 비활성화")
        recommendations.append("Windows 자동 업데이트를 활성화하세요.")
    
    last_heartbeat = pc_data.get("last_heartbeat")
    if last_heartbeat:
        try:
            if isinstance(last_heartbeat, str):
                last_heartbeat = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
            diff = datetime.utcnow() - last_heartbeat.replace(tzinfo=None)
            if diff > timedelta(days=7):
                score -= 10
                issues.append("7일 이상 오프라인")
                recommendations.append("에이전트 연결 상태를 확인하세요.")
        except Exception:
            pass
    
    score = max(0, min(100, score))
    
    if score >= 80:
        risk_level = "low"
    elif score >= 60:
        risk_level = "medium"
    elif score >= 40:
        risk_level = "high"
    else:
        risk_level = "critical"
    
    return {
        "security_score": score,
        "risk_level": risk_level,
        "issues": issues,
        "recommendations": recommendations,
        "analyzed_at": datetime.utcnow().isoformat()
    }


def generate_security_insights_local(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Generate security insights from statistics"""
    insights = []
    alerts = []
    
    total_pcs = stats.get("total_pcs", 0)
    online_pcs = stats.get("online_pcs", 0)
    
    if total_pcs > 0:
        online_rate = (online_pcs / total_pcs) * 100
        if online_rate < 50:
            alerts.append({
                "type": "warning",
                "message": f"전체 PC 중 {online_rate:.0f}%만 온라인 상태입니다. 에이전트 연결을 확인하세요."
            })
    
    expiring_certs = stats.get("expiring_certs_30days", 0)
    if expiring_certs > 0:
        alerts.append({
            "type": "critical" if expiring_certs > 3 else "warning",
            "message": f"{expiring_certs}개의 인증서가 30일 내 만료 예정입니다."
        })
    
    security_events = stats.get("unresolved_security_events", 0)
    if security_events > 0:
        alerts.append({
            "type": "warning",
            "message": f"미해결 보안 이벤트 {security_events}건이 있습니다."
        })
    
    avg_score = stats.get("avg_security_score", 0)
    if avg_score < 60:
        insights.append({
            "category": "보안 점수",
            "message": f"평균 보안 점수({avg_score:.0f}점)가 낮습니다. 전반적인 보안 설정을 점검하세요."
        })
    elif avg_score >= 80:
        insights.append({
            "category": "보안 점수",
            "message": f"평균 보안 점수({avg_score:.0f}점)가 양호합니다."
        })
    
    inactive_employees = stats.get("inactive_employees", 0)
    if inactive_employees > 0:
        insights.append({
            "category": "직원 관리",
            "message": f"비활성 직원 {inactive_employees}명의 계정 및 자산 접근 권한을 검토하세요."
        })
    
    return {
        "insights": insights,
        "alerts": alerts,
        "summary": f"총 {total_pcs}대 PC 중 {online_pcs}대 온라인, 보안 이벤트 {security_events}건 미해결",
        "generated_at": datetime.utcnow().isoformat()
    }


def predict_certificate_renewals(certificates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Predict certificate renewal priorities"""
    today = datetime.utcnow().date()
    predictions = []
    
    for cert in certificates:
        try:
            expiry = cert.get("expiry_date")
            if isinstance(expiry, str):
                expiry = datetime.fromisoformat(expiry).date()
            
            days_left = (expiry - today).days if expiry else None
            
            if days_left is not None:
                if days_left <= 7:
                    priority = "critical"
                    action = "즉시 갱신 필요"
                elif days_left <= 30:
                    priority = "high"
                    action = "1주일 내 갱신 권장"
                elif days_left <= 60:
                    priority = "medium"
                    action = "갱신 준비 시작"
                else:
                    priority = "low"
                    action = "정기 모니터링"
                
                predictions.append({
                    "cert_id": cert.get("id"),
                    "cert_name": cert.get("name"),
                    "days_left": days_left,
                    "priority": priority,
                    "recommended_action": action,
                    "estimated_renewal_date": (today + timedelta(days=max(0, days_left - 14))).isoformat()
                })
        except Exception as e:
            logger.error(f"Error predicting certificate renewal: {e}")
    
    return sorted(predictions, key=lambda x: x.get("days_left", 9999))


async def analyze_with_openai(prompt: str, context: Dict[str, Any]) -> str:
    """Use OpenAI API for advanced analysis if configured"""
    if not settings.OPENAI_API_KEY:
        return generate_fallback_analysis(context)
    
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        context_str = json.dumps(context, ensure_ascii=False, default=str)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """당신은 기업 IT 자산 관리 전문가 AI입니다. 
                    한국어로 응답하며, 보안 위협을 분석하고 실행 가능한 조치를 제안합니다.
                    응답은 JSON 형식으로 반환하세요."""
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\n데이터: {context_str}"
                }
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return generate_fallback_analysis(context)


def generate_fallback_analysis(context: Dict[str, Any]) -> str:
    """Generate analysis without AI"""
    return json.dumps({
        "status": "local_analysis",
        "message": "AI 분석 서비스가 설정되지 않았습니다. 로컬 분석 결과를 사용합니다.",
        "context_keys": list(context.keys())
    }, ensure_ascii=False)


def detect_anomalies(activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect anomalies in PC activities"""
    anomalies = []
    
    login_times = []
    for activity in activities:
        if activity.get("activity_type") == "login":
            try:
                login_time = activity.get("started_at")
                if isinstance(login_time, str):
                    login_time = datetime.fromisoformat(login_time)
                login_times.append(login_time)
            except Exception:
                pass
    
    unusual_hours = []
    for login_time in login_times:
        hour = login_time.hour
        if hour < 6 or hour >= 22:
            unusual_hours.append({
                "type": "unusual_login_time",
                "severity": "medium",
                "message": f"비업무 시간 로그인 감지: {login_time.strftime('%Y-%m-%d %H:%M')}",
                "details": {"hour": hour, "datetime": login_time.isoformat()}
            })
    
    anomalies.extend(unusual_hours[:5])
    return anomalies
