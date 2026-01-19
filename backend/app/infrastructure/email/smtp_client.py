import aiosmtplib
from email.message import EmailMessage

from app.core.config import settings


class SMTPClient:
    """SMTP送信クライアント（MailHog用）"""

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str = "noreply@example.com",
    ) -> None:
        """メール送信"""
        message = EmailMessage()
        message["From"] = from_email
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
        )
