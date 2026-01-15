"""
Arquivo: app/modules/communication/providers/email.py

Responsabilidade:
Envio de e-mails via SMTP com suporte a TLS e autenticação.

Integrações:
- core.config.Settings
"""

import smtplib
from email.mime.text import MIMEText

from ....core.config import settings


def send_email(destination: str, subject: str, content: str) -> bool:
    if settings.environment == "testing":
        return True
    msg = MIMEText(content)
    msg["Subject"] = subject or "Mensagem"
    msg["From"] = settings.smtp_user or "noreply@example.com"
    msg["To"] = destination

    if settings.smtp_use_tls:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        server.starttls()
    else:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
    try:
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(msg["From"], [destination], msg.as_string())
        server.quit()
        return True
    except Exception:
        try:
            server.quit()
        except Exception:
            pass
        return False

