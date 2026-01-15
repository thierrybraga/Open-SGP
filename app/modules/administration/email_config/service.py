"""
Arquivo: app/modules/administration/email_config/service.py

Responsabilidade:
Lógica de negócio para Configuração de E-mail.
"""

from sqlalchemy.orm import Session
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .models import EmailConfiguration
from .schemas import EmailConfigurationCreate, EmailConfigurationUpdate, EmailTestRequest


def encrypt_password(password: str) -> str:
    """
    Criptografa senha do SMTP.
    Implementação simples - em produção usar Fernet ou similar.
    """
    # TODO: Implementar criptografia real (Fernet, AES, etc.)
    import base64
    return base64.b64encode(password.encode()).decode()


def decrypt_password(encrypted: str) -> str:
    """
    Descriptografa senha do SMTP.
    """
    # TODO: Implementar descriptografia real
    import base64
    return base64.b64decode(encrypted.encode()).decode()


def create_email_configuration(db: Session, data: EmailConfigurationCreate) -> EmailConfiguration:
    """Cria nova configuração de email."""
    # Se é default, remover default das outras
    if data.is_default:
        db.query(EmailConfiguration).update({"is_default": False})

    # Criptografar senha
    encrypted_password = encrypt_password(data.smtp_password)

    config_data = data.dict()
    config_data['smtp_password'] = encrypted_password

    config = EmailConfiguration(**config_data)
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def update_email_configuration(db: Session, config: EmailConfiguration, data: EmailConfigurationUpdate) -> EmailConfiguration:
    """Atualiza configuração de email."""
    update_data = data.dict(exclude_none=True)

    # Se está setando como default, remover default das outras
    if update_data.get('is_default') == True:
        db.query(EmailConfiguration).filter(EmailConfiguration.id != config.id).update({"is_default": False})

    # Criptografar nova senha se fornecida
    if 'smtp_password' in update_data:
        update_data['smtp_password'] = encrypt_password(update_data['smtp_password'])

    for field, value in update_data.items():
        setattr(config, field, value)

    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def get_default_email_configuration(db: Session) -> EmailConfiguration | None:
    """Retorna configuração padrão de email."""
    return db.query(EmailConfiguration).filter(
        EmailConfiguration.is_default == True,
        EmailConfiguration.is_active == True
    ).first()


def test_email_configuration(db: Session, config: EmailConfiguration, test_request: EmailTestRequest) -> dict:
    """
    Testa configuração de email enviando um e-mail de teste.
    """
    try:
        # Descriptografar senha
        password = decrypt_password(config.smtp_password)

        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = f"{config.from_name} <{config.from_email}>"
        msg['To'] = test_request.to_email
        msg['Subject'] = test_request.subject

        if config.reply_to_email:
            msg['Reply-To'] = config.reply_to_email

        msg.attach(MIMEText(test_request.body, 'plain'))

        # Conectar e enviar
        if config.use_ssl:
            server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=config.timeout)
        else:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=config.timeout)
            if config.use_tls:
                server.starttls()

        server.login(config.smtp_user, password)
        server.send_message(msg)
        server.quit()

        # Atualizar último teste
        config.last_test_at = datetime.utcnow().isoformat()
        config.last_test_success = True
        config.last_test_error = None
        db.add(config)
        db.commit()

        return {
            "success": True,
            "message": f"Email sent successfully to {test_request.to_email}",
            "error_detail": None
        }

    except smtplib.SMTPAuthenticationError as e:
        error_msg = "SMTP authentication failed. Check username and password."
        config.last_test_at = datetime.utcnow().isoformat()
        config.last_test_success = False
        config.last_test_error = error_msg
        db.add(config)
        db.commit()

        return {
            "success": False,
            "message": "Email test failed",
            "error_detail": error_msg
        }

    except smtplib.SMTPException as e:
        error_msg = f"SMTP error: {str(e)}"
        config.last_test_at = datetime.utcnow().isoformat()
        config.last_test_success = False
        config.last_test_error = error_msg
        db.add(config)
        db.commit()

        return {
            "success": False,
            "message": "Email test failed",
            "error_detail": error_msg
        }

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        config.last_test_at = datetime.utcnow().isoformat()
        config.last_test_success = False
        config.last_test_error = error_msg
        db.add(config)
        db.commit()

        return {
            "success": False,
            "message": "Email test failed",
            "error_detail": error_msg
        }


def send_email(db: Session, to_email: str, subject: str, body: str, config_id: int = None) -> bool:
    """
    Envia email usando configuração especificada ou padrão.
    """
    if config_id:
        config = db.query(EmailConfiguration).filter(EmailConfiguration.id == config_id).first()
    else:
        config = get_default_email_configuration(db)

    if not config:
        raise ValueError("No email configuration available")

    try:
        password = decrypt_password(config.smtp_password)

        msg = MIMEMultipart()
        msg['From'] = f"{config.from_name} <{config.from_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        if config.reply_to_email:
            msg['Reply-To'] = config.reply_to_email

        msg.attach(MIMEText(body, 'plain'))

        if config.use_ssl:
            server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=config.timeout)
        else:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=config.timeout)
            if config.use_tls:
                server.starttls()

        server.login(config.smtp_user, password)
        server.send_message(msg)
        server.quit()

        return True

    except Exception as e:
        print(f"Email send error: {str(e)}")
        return False
