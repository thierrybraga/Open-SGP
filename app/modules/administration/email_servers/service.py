"""
Arquivo: app/modules/administration/email_servers/service.py

Responsabilidade:
Lógica de negócio para Email Servers.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from datetime import datetime

from .models import EmailServer
from .schemas import EmailServerCreate, EmailServerUpdate, EmailTestRequest


def create_email_server(db: Session, data: EmailServerCreate) -> EmailServer:
    """
    Cria servidor de e-mail.
    """
    # Se for marcado como padrão, desmarcar outros
    if data.is_default:
        db.query(EmailServer).filter(
            EmailServer.is_default == True
        ).update({"is_default": False})

    server = EmailServer(**data.dict())
    db.add(server)
    db.commit()
    db.refresh(server)
    return server


def update_email_server(db: Session, server: EmailServer, data: EmailServerUpdate) -> EmailServer:
    """
    Atualiza servidor de e-mail.
    """
    update_data = data.dict(exclude_none=True)

    # Se está marcando como padrão, desmarcar outros
    if update_data.get('is_default') == True:
        db.query(EmailServer).filter(
            EmailServer.id != server.id,
            EmailServer.is_default == True
        ).update({"is_default": False})

    for field, value in update_data.items():
        setattr(server, field, value)

    db.add(server)
    db.commit()
    db.refresh(server)
    return server


def get_default_email_server(db: Session) -> EmailServer | None:
    """
    Retorna o servidor de e-mail padrão.
    """
    return db.query(EmailServer).filter(
        EmailServer.is_default == True,
        EmailServer.is_active == True
    ).first()


def test_email_server(db: Session, server_id: int, test_data: EmailTestRequest) -> dict:
    """
    Testa o servidor de e-mail enviando um e-mail de teste.
    """
    server = db.query(EmailServer).filter(EmailServer.id == server_id).first()
    if not server:
        return {"success": False, "error": "Email server not found"}

    try:
        # Criar mensagem
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{server.from_name or 'Open-SGP'} <{server.from_email}>"
        msg['To'] = test_data.to_email
        msg['Subject'] = test_data.subject

        # Corpo do e-mail
        html_body = f"""
        <html>
            <body>
                <h2>{test_data.subject}</h2>
                <p>{test_data.body}</p>
                <hr>
                <p><small>Sent from Open-SGP Email Server: {server.name}</small></p>
                <p><small>SMTP Host: {server.smtp_host}:{server.smtp_port}</small></p>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))

        # Conectar ao servidor SMTP
        if server.use_ssl:
            smtp = smtplib.SMTP_SSL(server.smtp_host, server.smtp_port)
        else:
            smtp = smtplib.SMTP(server.smtp_host, server.smtp_port)
            if server.use_tls:
                smtp.starttls()

        # Autenticar
        smtp.login(server.smtp_username, server.get_password())

        # Enviar
        smtp.sendmail(server.from_email, [test_data.to_email], msg.as_string())
        smtp.quit()

        # Atualizar estatísticas
        server.last_used_at = datetime.utcnow().isoformat()
        db.add(server)
        db.commit()

        return {
            "success": True,
            "message": f"Test email sent successfully to {test_data.to_email}",
            "server": server.name
        }

    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "error": "Authentication failed. Check username and password."
        }
    except smtplib.SMTPConnectError:
        return {
            "success": False,
            "error": f"Could not connect to SMTP server {server.smtp_host}:{server.smtp_port}"
        }
    except smtplib.SMTPException as e:
        return {
            "success": False,
            "error": f"SMTP error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def send_email(
    db: Session,
    to_email: str,
    subject: str,
    body: str,
    server_id: int = None
) -> dict:
    """
    Envia um e-mail usando o servidor especificado ou o padrão.
    """
    if server_id:
        server = db.query(EmailServer).filter(EmailServer.id == server_id).first()
    else:
        server = get_default_email_server(db)

    if not server:
        return {"success": False, "error": "No email server available"}

    if not server.is_active:
        return {"success": False, "error": "Email server is not active"}

    # Verificar limites
    if server.max_emails_per_hour and server.emails_sent_this_hour >= server.max_emails_per_hour:
        return {"success": False, "error": "Hourly email limit reached"}

    if server.max_emails_per_day and server.emails_sent_today >= server.max_emails_per_day:
        return {"success": False, "error": "Daily email limit reached"}

    try:
        # Criar e enviar mensagem (mesmo código do test_email_server)
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{server.from_name or 'Open-SGP'} <{server.from_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        if server.use_ssl:
            smtp = smtplib.SMTP_SSL(server.smtp_host, server.smtp_port)
        else:
            smtp = smtplib.SMTP(server.smtp_host, server.smtp_port)
            if server.use_tls:
                smtp.starttls()

        smtp.login(server.smtp_username, server.get_password())
        smtp.sendmail(server.from_email, [to_email], msg.as_string())
        smtp.quit()

        # Atualizar estatísticas
        server.emails_sent_today += 1
        server.emails_sent_this_hour += 1
        server.last_used_at = datetime.utcnow().isoformat()
        db.add(server)
        db.commit()

        return {"success": True, "message": "Email sent successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}
