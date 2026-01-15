"""
Arquivo: app/modules/administration/setup/service.py

Responsabilidade:
Lógica de negócio para wizard de setup inicial.
"""

from sqlalchemy.orm import Session
from datetime import datetime

from .models import SetupProgress
from .schemas import (
    CompanySetup, FinancialSetup, NetworkSetup, PlanSetup,
    ContractTemplateSetup, EmailSetup,MonitoringSetup, FirstUserSetup, CompleteSetupRequest
)
from ..finance.models import Company, Carrier, FinancialParameter
from ..pops.models import POP
from ..nas.models import NAS
from ...network.vendors.zabbix import ZabbixClient
from ...plans.models import Plan
from ...contract_templates.models import ContractTemplate
from ...users.models import User
from ...roles.models import Role


def get_or_create_setup_progress(db: Session) -> SetupProgress:
    """Obtém ou cria registro de progresso do setup."""
    progress = db.query(SetupProgress).first()
    if not progress:
        progress = SetupProgress()
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress


def setup_step1_company(db: Session, data: CompanySetup) -> Company:
    """Etapa 1: Configura empresa."""
    # Verificar se já existe empresa
    existing = db.query(Company).first()
    if existing:
        # Atualizar empresa existente
        for field, value in data.dict().items():
            setattr(existing, field, value)
        db.add(existing)
        company = existing
    else:
        # Criar nova empresa
        company = Company(**data.dict())
        db.add(company)

    # Atualizar progresso
    progress = get_or_create_setup_progress(db)
    progress.company_configured = True
    progress.current_step = max(progress.current_step, 2)
    db.add(progress)

    db.commit()
    db.refresh(company)
    return company


def setup_step2_financial(db: Session, data: FinancialSetup) -> Carrier:
    """Etapa 2: Configura portador e parâmetros financeiros."""
    # Criar portador
    carrier = Carrier(
        name=data.carrier_name,
        bank_code=data.bank_code,
        agency=data.agency,
        account=data.account,
        wallet=data.wallet,
        cnab_layout=data.cnab_layout,
        is_active=True
    )
    db.add(carrier)
    db.flush()

    # Criar parâmetros financeiros
    company = db.query(Company).first()
    if company:
        param = FinancialParameter(
            company_id=company.id,
            default_carrier_id=carrier.id,
            fine_percent=data.fine_percent,
            interest_percent=data.interest_percent,
            send_email_on_issue=False
        )
        db.add(param)

    # Atualizar progresso
    progress = get_or_create_setup_progress(db)
    progress.financial_configured = True
    progress.current_step = max(progress.current_step, 3)
    db.add(progress)

    db.commit()
    db.refresh(carrier)
    return carrier


def setup_step3_network(db: Session, data: NetworkSetup) -> tuple[POP, NAS]:
    """Etapa 3: Configura POP e NAS."""
    # Criar POP
    pop = POP(
        name=data.pop_name,
        city=data.pop_city,
        address=data.pop_address,
        latitude=data.pop_latitude,
        longitude=data.pop_longitude
    )
    db.add(pop)
    db.flush()

    # Criar NAS
    nas = NAS(
        name=data.nas_name,
        ip_address=data.nas_ip,
        secret=data.nas_secret,
        vendor=data.nas_vendor,
        pop_id=pop.id
    )
    db.add(nas)

    # Atualizar progresso
    progress = get_or_create_setup_progress(db)
    progress.network_configured = True
    progress.current_step = max(progress.current_step, 4)
    db.add(progress)

    db.commit()
    db.refresh(pop)
    db.refresh(nas)
    return pop, nas


def setup_step4_plan(db: Session, data: PlanSetup) -> Plan:
    """Etapa 4: Cria primeiro plano."""
    plan = Plan(
        name=data.name,
        category=data.category,
        description=data.description,
        download_speed_mbps=data.download_speed_mbps,
        upload_speed_mbps=data.upload_speed_mbps,
        price=data.price,
        is_active=True
    )
    db.add(plan)

    # Atualizar progresso
    progress = get_or_create_setup_progress(db)
    progress.plans_configured = True
    progress.current_step = max(progress.current_step, 5)
    db.add(progress)

    db.commit()
    db.refresh(plan)
    return plan


def setup_step5_contract_template(db: Session, data: ContractTemplateSetup) -> ContractTemplate:
    """Etapa 5: Cria template de contrato."""
    template = ContractTemplate(
        name=data.name,
        content=data.content,
        content_type="html",
        version="1.0",
        is_active=True
    )
    db.add(template)

    # Atualizar progresso
    progress = get_or_create_setup_progress(db)
    progress.contract_template_configured = True
    progress.current_step = max(progress.current_step, 6)
    db.add(progress)

    db.commit()
    db.refresh(template)
    return template


def setup_step6_email(db: Session, data: EmailSetup) -> dict:
    """Etapa 6: Configura servidor de email."""
    # Salvar configurações no progresso
    progress = get_or_create_setup_progress(db)
    config_data = progress.get_config_data()
    config_data['email'] = data.dict()
    progress.set_config_data(config_data)
    progress.email_configured = True
    progress.current_step = max(progress.current_step, 7)

    db.add(progress)
    db.commit()

    return {"message": "Email configuration saved", "config": data.dict(exclude={'smtp_password'})}


def setup_step_monitoring(db: Session, data: MonitoringSetup) -> dict:
    """Etapa: Configura monitoramento (Zabbix)."""
    # Salvar configurações no progresso
    progress = get_or_create_setup_progress(db)
    config_data = progress.get_config_data()
    config_data['monitoring'] = data.dict()
    progress.set_config_data(config_data)
    
    # Tentar conectar e configurar se habilitado
    status_msg = "Saved"
    if data.enable_monitoring:
        try:
            zabbix = ZabbixClient(data.url, data.user, data.password)
            zabbix.login()
            # Criar grupo padrão
            zabbix.create_host_group("ISP Clientes")
            status_msg = "Connected and configured"
        except Exception as e:
            status_msg = f"Saved but connection failed: {str(e)}"

    progress.monitoring_configured = True
    progress.current_step = max(progress.current_step, 8) # Monitoring is usually late step

    db.add(progress)
    db.commit()

    return {"message": status_msg, "config": data.dict(exclude={'password'})}


def setup_step7_first_user(db: Session, data: FirstUserSetup) -> User:
    """Etapa 7: Cria primeiro usuário administrador."""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Buscar ou criar role de admin
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        admin_role = Role(
            name="admin",
            description="Administrador do sistema",
            is_active=True
        )
        db.add(admin_role)
        db.flush()

    # Criar usuário
    user = User(
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        hashed_password=pwd_context.hash(data.password),
        role_id=admin_role.id,
        is_active=True
    )
    db.add(user)

    # Atualizar progresso
    progress = get_or_create_setup_progress(db)
    progress.first_user_created = True
    progress.is_completed = True
    progress.current_step = 8
    db.add(progress)

    db.commit()
    db.refresh(user)
    return user


def complete_setup_wizard(db: Session, data: CompleteSetupRequest) -> dict:
    """Executa wizard completo de uma vez."""
    results = {}

    try:
        # Etapa 1: Empresa
        company = setup_step1_company(db, data.company)
        results['company'] = company.id

        # Etapa 2: Financeiro
        carrier = setup_step2_financial(db, data.financial)
        results['carrier'] = carrier.id

        # Etapa 3: Rede
        pop, nas = setup_step3_network(db, data.network)
        results['pop'] = pop.id
        results['nas'] = nas.id

        # Etapa 4: Plano
        plan = setup_step4_plan(db, data.plan)
        results['plan'] = plan.id

        # Etapa 5: Template de contrato
        template = setup_step5_contract_template(db, data.contract_template)
        results['contract_template'] = template.id

        # Etapa 6: Email
        email_result = setup_step6_email(db, data.email)
        results['email'] = "configured"

        # Etapa: Monitoramento
        mon_result = setup_step_monitoring(db, data.monitoring)
        results['monitoring'] = mon_result['message']

        # Etapa 7: Primeiro usuário
        user = setup_step7_first_user(db, data.first_user)
        results['user'] = user.id

        results['success'] = True
        results['message'] = "Setup completed successfully"

        return results

    except Exception as e:
        db.rollback()
        raise ValueError(f"Setup failed: {str(e)}")
