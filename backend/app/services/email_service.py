import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from jinja2 import Template
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


EMAIL_TEMPLATES = {
    "verification": {
        "subject": "[AssetGuard] 이메일 인증 코드",
        "body": """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🔐 AssetGuard Enterprise</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0 0;">기업 자산 관리 시스템</p>
    </div>
    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #eee;">
        <h2 style="color: #333;">이메일 인증 코드</h2>
        <p style="color: #666;">안녕하세요, <strong>{{name}}</strong>님!</p>
        <p style="color: #666;">아래 인증 코드를 입력하여 이메일을 인증해 주세요:</p>
        <div style="background: white; border: 2px dashed #667eea; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0;">
            <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #667eea;">{{code}}</span>
        </div>
        <p style="color: #999; font-size: 14px;">⏰ 이 코드는 <strong>10분</strong> 후 만료됩니다.</p>
        <p style="color: #999; font-size: 14px;">본인이 요청하지 않은 경우 이 이메일을 무시하세요.</p>
    </div>
</body>
</html>
        """
    },
    "certificate_expiry": {
        "subject": "[AssetGuard] ⚠️ 인증서 만료 알림 - {{cert_name}}",
        "body": """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #f6d365 0%, #fda085 100%); padding: 30px; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">⚠️ 인증서 만료 알림</h1>
    </div>
    <div style="background: #fff9f0; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #fda085;">
        <h2 style="color: #e07b39;">{{cert_name}}</h2>
        <p style="color: #666;">인증서가 <strong style="color: #e53e3e;">{{days_left}}일</strong> 후 만료됩니다.</p>
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr><td style="padding: 8px; background: #f9f9f9; font-weight: bold;">도메인</td><td style="padding: 8px;">{{domain}}</td></tr>
            <tr><td style="padding: 8px; background: #f9f9f9; font-weight: bold;">만료일</td><td style="padding: 8px; color: #e53e3e;">{{expiry_date}}</td></tr>
            <tr><td style="padding: 8px; background: #f9f9f9; font-weight: bold;">담당자</td><td style="padding: 8px;">{{responsible}}</td></tr>
            <tr><td style="padding: 8px; background: #f9f9f9; font-weight: bold;">업체</td><td style="padding: 8px;">{{vendor}}</td></tr>
        </table>
        <p style="color: #666;">즉시 갱신 조치를 취해주세요.</p>
    </div>
</body>
</html>
        """
    },
    "security_alert": {
        "subject": "[AssetGuard] 🚨 보안 이벤트 발생 - {{pc_name}}",
        "body": """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%); padding: 30px; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🚨 보안 이벤트 발생</h1>
    </div>
    <div style="background: #fff5f5; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e53e3e;">
        <h2 style="color: #c53030;">{{event_title}}</h2>
        <p style="color: #666;"><strong>PC:</strong> {{pc_name}}</p>
        <p style="color: #666;"><strong>심각도:</strong> <span style="color: #e53e3e; font-weight: bold;">{{severity}}</span></p>
        <p style="color: #666;"><strong>설명:</strong> {{description}}</p>
        <p style="color: #666;"><strong>발생 시간:</strong> {{occurred_at}}</p>
        <p style="margin-top: 20px;"><a href="{{dashboard_url}}" style="background: #e53e3e; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none;">대시보드에서 확인하기</a></p>
    </div>
</body>
</html>
        """
    },
    "welcome": {
        "subject": "[AssetGuard] 환영합니다! 계정이 생성되었습니다",
        "body": """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🎉 AssetGuard Enterprise</h1>
    </div>
    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #eee;">
        <h2 style="color: #333;">환영합니다, {{name}}님!</h2>
        <p style="color: #666;">AssetGuard 기업 자산 관리 시스템에 등록되었습니다.</p>
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr><td style="padding: 8px; background: #f9f9f9; font-weight: bold;">이메일</td><td style="padding: 8px;">{{email}}</td></tr>
            <tr><td style="padding: 8px; background: #f9f9f9; font-weight: bold;">임시 비밀번호</td><td style="padding: 8px; font-family: monospace; color: #667eea;">{{password}}</td></tr>
        </table>
        <p style="color: #e53e3e; font-size: 14px;">⚠️ 보안을 위해 첫 로그인 후 반드시 비밀번호를 변경해 주세요.</p>
        <p><a href="{{login_url}}" style="background: #667eea; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none;">로그인 하기</a></p>
    </div>
</body>
</html>
        """
    }
}


async def send_email(to_email: str, subject: str, html_body: str, to_name: str = ""):
    """Send HTML email via SMTP"""
    if not settings.SMTP_USER:
        logger.warning(f"Email not configured. Would send to {to_email}: {subject}")
        return True
    
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        message["To"] = f"{to_name} <{to_email}>" if to_name else to_email
        
        html_part = MIMEText(html_body, "html", "utf-8")
        message.attach(html_part)
        
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            start_tls=True,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
        )
        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def render_template(template_name: str, **kwargs) -> tuple[str, str]:
    """Render email template and return (subject, body)"""
    template = EMAIL_TEMPLATES.get(template_name)
    if not template:
        return "Notification", str(kwargs)
    
    subject = Template(template["subject"]).render(**kwargs)
    body = Template(template["body"]).render(**kwargs)
    return subject, body


async def send_verification_email(email: str, name: str, code: str):
    subject, body = render_template("verification", name=name, code=code)
    return await send_email(email, subject, body, name)


async def send_certificate_expiry_email(
    email: str, cert_name: str, domain: str, 
    days_left: int, expiry_date: str, responsible: str, vendor: str
):
    subject, body = render_template(
        "certificate_expiry",
        cert_name=cert_name, domain=domain, days_left=days_left,
        expiry_date=expiry_date, responsible=responsible, vendor=vendor
    )
    return await send_email(email, subject, body)


async def send_security_alert_email(
    email: str, event_title: str, pc_name: str,
    severity: str, description: str, occurred_at: str, dashboard_url: str
):
    subject, body = render_template(
        "security_alert",
        event_title=event_title, pc_name=pc_name, severity=severity,
        description=description, occurred_at=occurred_at, dashboard_url=dashboard_url
    )
    return await send_email(email, subject, body)


async def send_welcome_email(email: str, name: str, password: str, login_url: str):
    subject, body = render_template(
        "welcome", name=name, email=email, password=password, login_url=login_url
    )
    return await send_email(email, subject, body, name)
