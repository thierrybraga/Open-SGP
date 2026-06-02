"""
Arquivo: app/main.py

Responsabilidade:
Inicializa a aplicação FastAPI, registra rotas dos módulos e configura middlewares
essenciais como CORS e tratamento de erros.

Integrações:
- core.config
- core.database
- core.dependencies
- modules.auth
- modules.users
- modules.roles
- modules.permissions
- modules.administration.pops
- modules.administration.nas
- modules.administration.variables
- modules.administration.backups
"""

from time import perf_counter
from uuid import uuid4

import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.database import Base, engine, import_all_models
from .core.dependencies import get_current_user
from .core.logging import configure_logging, configure_sentry

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
logger = structlog.get_logger(__name__)

# Routers
from .modules.auth.routes import router as auth_router
from .modules.users.routes import router as users_router
from .modules.roles.routes import router as roles_router
from .modules.permissions.routes import router as permissions_router
from .modules.administration.pops.routes import router as pops_router
from .modules.administration.nas.routes import router as nas_router
from .modules.administration.variables.routes import router as variables_router
from .modules.administration.backups.routes import router as backups_router
from .modules.administration.setup.routes import router as setup_router
from .modules.administration.finance.routes import router as finance_admin_router
from .modules.administration.email_config.routes import router as email_config_router
from .modules.administration.email_servers.routes import router as email_servers_router
from .modules.administration.employees.routes import router as employees_router
from .modules.administration.operation_points.routes import router as operation_points_router
from .modules.administration.payment_gateways.routes import router as admin_payment_gateways_router
from .modules.anatel.routes import router as anatel_router
from .modules.clients.routes import router as clients_router
from .modules.plans.routes import router as plans_router
from .modules.support.routes import router as support_router
from .modules.contracts.routes import router as contracts_router
from .modules.contract_templates.routes import router as contract_templates_router
from .modules.billing.routes import router as billing_router
from .modules.billing.gateway.routes import router as billing_gateway_router
from .modules.billing.gateway.webhooks import router as billing_gateway_webhooks
from .modules.cashier.routes import router as cashier_router
from .modules.discounts.routes import router as discounts_router
from .modules.due_dates.routes import router as due_dates_router
from .modules.fiscal.routes import router as fiscal_router
from .modules.network.routes import router as network_router
from .modules.contract_tech.routes import router as contract_tech_router
from .modules.service_orders.routes import router as service_orders_router
from .modules.communication.routes import router as communication_router
from .modules.reports.routes import router as reports_router
from .modules.stock.routes import router as stock_router
from .modules.customer_app.routes import router as customer_app_router
from .modules.technician_app.routes import router as technician_app_router
from .modules.health.routes import router as health_router
from .modules.audit.routes import router as audit_router
from .modules.notifications.routes import router as notifications_router
from .modules.referrals.routes import router as referrals_router
from .modules.viability.routes import router as viability_router

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    configure_sentry()
    # Importar todos os modelos para garantir relacionamentos do SQLAlchemy
    import_all_models()
    if settings.should_auto_create_tables():
        Base.metadata.create_all(bind=engine)
    try:
        seed_reference_data()
    except Exception:
        pass
    yield


def seed_reference_data() -> None:
    """
    Seed baseline RBAC data.

    This must not create default credentials. The initial admin user is opt-in via
    BOOTSTRAP_ADMIN_ENABLED=true and BOOTSTRAP_ADMIN_PASSWORD.
    """
    from sqlalchemy.orm import Session

    from .core.security import hash_password
    from .modules.permissions.models import Permission
    from .modules.roles.models import Role
    from .modules.users.models import User

    db = Session(bind=engine)
    try:
        base_perms = [
            ("users.create", "Criar usuários"),
            ("users.read", "Listar usuários"),
            ("users.update", "Atualizar usuários"),
            ("users.roles.assign", "Atribuir roles ao usuário"),
            ("roles.create", "Criar roles"),
            ("roles.read", "Listar roles"),
            ("permissions.create", "Criar permissões"),
            ("permissions.read", "Listar permissões"),
            ("admin.pops.create", "Criar POPs"),
            ("admin.nas.create", "Criar NAS"),
            ("admin.variables.create", "Criar variáveis"),
            ("admin.backups.create", "Criar configs de backup"),
            ("admin.backups.trigger", "Acionar backup"),
            ("admin.finance.companies.create", "Criar empresas"),
            ("admin.finance.carriers.create", "Criar portadores"),
            ("admin.finance.receipts.create", "Criar pontos de recebimento"),
            ("admin.finance.parameters.create", "Criar parâmetros financeiros"),
            ("clients.create", "Criar clientes"),
            ("clients.update", "Atualizar clientes"),
            ("clients.read", "Listar clientes"),
            ("clients.approve", "Aprovar pré-cadastros de clientes"),
            ("plans.create", "Criar planos"),
            ("plans.update", "Atualizar planos"),
            ("plans.read", "Listar planos"),
            ("contracts.create", "Criar contratos"),
            ("contracts.update", "Atualizar contratos"),
            ("contracts.read", "Listar contratos"),
            ("billing.titles.create", "Criar títulos"),
            ("billing.titles.update", "Atualizar títulos"),
            ("billing.titles.read", "Listar títulos"),
            ("billing.boletos.generate", "Gerar boletos"),
            ("billing.cnab.remit", "Gerar remessas CNAB"),
            ("billing.cnab.return", "Processar retornos CNAB"),
            ("billing.promises.create", "Criar promessas de pagamento"),
            ("billing.promises.read", "Listar promessas"),
            ("billing.gateway.config.create", "Criar configuração de gateway"),
            ("billing.gateway.charge.create", "Criar cobrança no gateway"),
            ("billing.gateway.charge.update", "Atualizar status de cobrança"),
            ("billing.gateway.read", "Listar configs/cobranças do gateway"),
            ("fiscal.invoices.create", "Criar invoices"),
            ("fiscal.invoices.issue", "Emitir invoices"),
            ("fiscal.invoices.cancel", "Cancelar invoices"),
            ("fiscal.invoices.read", "Listar invoices"),
            ("fiscal.debit_notes.create", "Criar notas de débito"),
            ("fiscal.plan_details.create", "Criar detalhes fiscais de plano"),
            ("fiscal.plan_details.update", "Atualizar detalhes fiscais de plano"),
            ("fiscal.plan_details.delete", "Excluir detalhes fiscais de plano"),
            ("fiscal.tv_telephony_gateways.create", "Criar gateway TV/telefonia"),
            ("fiscal.tv_telephony_gateways.update", "Atualizar gateway TV/telefonia"),
            ("fiscal.tv_telephony_gateways.delete", "Excluir gateway TV/telefonia"),
            ("fiscal.tv_telephony_gateways.test", "Testar gateway TV/telefonia"),
            ("network.devices.create", "Criar dispositivos de rede"),
            ("network.read", "Ler dados de rede"),
            ("network.vlans.create", "Criar VLANs"),
            ("network.pools.create", "Criar pools de IP"),
            ("network.profiles.create", "Criar perfis de serviço"),
            ("network.assignments.create", "Criar atribuições de rede"),
            ("network.assignments.update", "Atualizar atribuições de rede"),
            ("network.provision", "Provisionar contrato"),
            ("network.block", "Bloquear contrato"),
            ("network.unblock", "Desbloquear contrato"),
            ("network.sync_billing", "Sincronizar bloqueio via financeiro"),
            ("contract_tech.equipment.create", "Registrar equipamentos"),
            ("contract_tech.signal.create", "Registrar medições de sinal"),
            ("contract_tech.speedtest.create", "Registrar speedtests"),
            ("contract_tech.logs.create", "Registrar logs técnicos"),
            ("support.tickets.create", "Criar tickets"),
            ("support.tickets.read", "Listar tickets"),
            ("support.tickets.update", "Atualizar tickets"),
            ("support.messages.create", "Adicionar mensagens em ticket"),
            ("support.tags.create", "Criar tags de ticket"),
            ("support.occurrences.create", "Criar ocorrências"),
            ("support.occurrences.read", "Listar ocorrências"),
            ("support.occurrences.update", "Atualizar ocorrências"),
            ("service_orders.create", "Criar ordens de serviço"),
            ("service_orders.update", "Atualizar ordens de serviço"),
            ("service_orders.assign", "Atribuir técnico/Agendar OS"),
            ("service_orders.close", "Concluir OS"),
            ("service_orders.read", "Listar ordens de serviço"),
            ("communication.templates.create", "Criar templates de comunicação"),
            ("communication.templates.update", "Atualizar templates de comunicação"),
            ("communication.templates.read", "Listar templates de comunicação"),
            ("communication.messages.enqueue", "Enfileirar mensagens"),
            ("communication.messages.dispatch", "Despachar mensagens"),
            ("communication.messages.requeue", "Reprocessar mensagens"),
            ("communication.messages.read", "Listar fila de mensagens"),
            ("reports.definitions.create", "Criar definições de relatórios"),
            ("reports.definitions.update", "Atualizar definições de relatórios"),
            ("reports.definitions.delete", "Excluir definições de relatórios"),
            ("reports.definitions.read", "Listar definições de relatórios"),
            ("reports.run", "Executar relatórios"),
            ("dashboard.widgets.create", "Criar widgets de dashboard"),
            ("dashboard.widgets.update", "Atualizar widgets de dashboard"),
            ("dashboard.widgets.read", "Listar widgets de dashboard"),
            ("dashboard.overview.read", "Ler visão geral do dashboard"),
            ("stock.warehouses.create", "Criar almoxarifados"),
            ("stock.warehouses.update", "Atualizar almoxarifados"),
            ("stock.warehouses.read", "Listar almoxarifados"),
            ("stock.items.create", "Criar itens de estoque"),
            ("stock.items.update", "Atualizar itens de estoque"),
            ("stock.items.read", "Listar itens de estoque"),
            ("stock.movements.create", "Registrar movimentos de estoque"),
            ("stock.movements.read", "Listar movimentos de estoque"),
            ("stock.balance.read", "Consultar saldo de estoque"),
            ("stock.categories.create", "Criar categorias de estoque"),
            ("stock.manufacturers.create", "Criar fabricantes"),
            ("stock.suppliers.create", "Criar fornecedores"),
            ("stock.suppliers.update", "Atualizar fornecedores"),
            ("stock.vehicles.create", "Criar veículos"),
            ("stock.kits.create", "Criar kits"),
            ("stock.purchases.create", "Criar compras"),
            ("stock.transfers.create", "Criar transferências de estoque"),
            ("stock.comodatos.create", "Criar comodatos"),
            ("stock.comodatos.update", "Atualizar comodatos"),
            ("customer.profile.read", "Ler perfil do cliente"),
            ("customer.contracts.read", "Listar contratos do cliente"),
            ("customer.billing.read", "Listar títulos do cliente"),
            ("customer.preferences.update", "Atualizar preferências do cliente"),
            ("customer.notifications.register", "Registrar token de notificação"),
            ("customer.support.create", "Abrir ticket de suporte pelo cliente"),
            ("technician.profile.read", "Ler perfil de técnico"),
            ("technician.orders.read", "Listar OS atribuídas ao técnico"),
            ("technician.orders.start", "Iniciar OS"),
            ("technician.orders.complete", "Concluir OS"),
            ("technician.worklogs.create", "Adicionar log de trabalho"),
            ("technician.materials.register", "Registrar materiais utilizados"),
            ("administration.email.create", "Criar configuração de e-mail"),
            ("administration.email.update", "Atualizar configuração de e-mail"),
            ("administration.email.delete", "Excluir configuração de e-mail"),
            ("administration.email.test", "Testar configuração de e-mail"),
            ("administration.email_servers.create", "Criar servidor de e-mail"),
            ("administration.email_servers.update", "Atualizar servidor de e-mail"),
            ("administration.email_servers.delete", "Excluir servidor de e-mail"),
            ("administration.email_servers.test", "Testar servidor de e-mail"),
            ("administration.employees.create", "Criar colaborador"),
            ("administration.employees.update", "Atualizar colaborador"),
            ("administration.employees.delete", "Excluir colaborador"),
            ("administration.employees.terminate", "Desligar colaborador"),
            ("administration.operation_points.create", "Criar ponto de operação"),
            ("administration.operation_points.update", "Atualizar ponto de operação"),
            ("administration.operation_points.delete", "Excluir ponto de operação"),
            ("administration.payment_gateways.create", "Criar gateway de pagamento"),
            ("administration.payment_gateways.update", "Atualizar gateway de pagamento"),
            ("administration.payment_gateways.delete", "Excluir gateway de pagamento"),
            ("administration.payment_gateways.test", "Testar gateway de pagamento"),
            ("anatel.sici.generate", "Gerar relatório SICI"),
            ("anatel.ppp_scm.generate", "Gerar relatório PPP-SCM"),
            ("anatel.reports.delete", "Excluir relatórios ANATEL"),
            ("cashier.open", "Abrir caixa"),
            ("cashier.close", "Fechar caixa"),
            ("cashier.movements.create", "Criar movimento de caixa"),
            ("discounts.create", "Criar descontos"),
            ("discounts.update", "Atualizar descontos"),
            ("discounts.delete", "Excluir descontos"),
            ("due_dates.create", "Criar datas de vencimento"),
            ("due_dates.update", "Atualizar datas de vencimento"),
            ("due_dates.delete", "Excluir datas de vencimento"),
            ("referrals.create", "Criar indicação"),
            ("referrals.update", "Atualizar indicação"),
            ("referrals.delete", "Excluir indicação"),
            ("referrals.rewards.create", "Criar recompensa de indicação"),
            ("referrals.rewards.pay", "Pagar recompensa de indicação"),
            ("referrals.programs.create", "Criar programa de indicação"),
            ("referrals.programs.update", "Atualizar programa de indicação"),
            ("viability.create", "Criar viabilidade"),
            ("viability.update", "Atualizar viabilidade"),
            ("viability.analyze", "Analisar viabilidade"),
            ("viability.admin", "Administrar viabilidades"),
            ("contracts.templates.create", "Criar template de contrato"),
            ("contracts.templates.update", "Atualizar template de contrato"),
            ("contracts.templates.delete", "Excluir template de contrato"),
            ("contracts.generate", "Gerar contrato"),
            ("contracts.addendums.create", "Criar aditivo"),
            ("contracts.addendums.update", "Atualizar aditivo"),
        ]

        for code, desc in base_perms:
            if not db.query(Permission).filter(Permission.code == code).first():
                db.add(Permission(code=code, description=desc))
        db.commit()

        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(name="admin")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)

        admin_role.permissions = db.query(Permission).all()
        db.add(admin_role)
        db.commit()

        if settings.should_bootstrap_admin():
            admin_user = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
            if not admin_user:
                admin_user = User(
                    username=settings.bootstrap_admin_username,
                    email=settings.bootstrap_admin_email,
                    hashed_password=hash_password(settings.bootstrap_admin_password),
                    is_active=True,
                )
                admin_user.roles = [admin_role]
                db.add(admin_user)
                db.commit()
    finally:
        db.close()


def create_app() -> FastAPI:
    app = FastAPI(title="ISP ERP API", version="0.1.0", lifespan=lifespan)
    protected = [Depends(get_current_user)]

    # Add rate limiter to app state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = perf_counter()
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            elapsed_ms = round((perf_counter() - start) * 1000, 2)
            status_code = response.status_code if response is not None else 500
            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                elapsed_ms=elapsed_ms,
            )
            if response is not None:
                response.headers["X-Request-ID"] = request_id

    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(users_router, prefix="/api/users", tags=["Users"], dependencies=protected)
    app.include_router(roles_router, prefix="/api/roles", tags=["Roles"], dependencies=protected)
    app.include_router(permissions_router, prefix="/api/permissions", tags=["Permissions"], dependencies=protected)
    app.include_router(pops_router, prefix="/api/admin/pops", tags=["Administration/POPs"], dependencies=protected)
    app.include_router(nas_router, prefix="/api/admin/nas", tags=["Administration/NAS"], dependencies=protected)
    app.include_router(variables_router, prefix="/api/admin/variables", tags=["Administration/Variables"], dependencies=protected)
    app.include_router(backups_router, prefix="/api/admin/backups", tags=["Administration/Backups"], dependencies=protected)
    app.include_router(setup_router, prefix="/api/setup", tags=["Setup"], dependencies=protected)
    app.include_router(finance_admin_router, prefix="/api/admin/finance", tags=["Administration/Finance"], dependencies=protected)
    app.include_router(email_config_router, prefix="/api/admin/email-config", tags=["Administration/EmailConfig"], dependencies=protected)
    app.include_router(email_servers_router, prefix="/api/admin/email-servers", tags=["Administration/EmailServers"], dependencies=protected)
    app.include_router(employees_router, prefix="/api/admin/employees", tags=["Administration/Employees"], dependencies=protected)
    app.include_router(operation_points_router, prefix="/api/admin/operation-points", tags=["Administration/OperationPoints"], dependencies=protected)
    app.include_router(
        admin_payment_gateways_router,
        prefix="/api/admin/payment-gateways",
        tags=["Administration/PaymentGateways"],
        dependencies=protected,
    )
    app.include_router(anatel_router, prefix="/api/anatel", tags=["ANATEL"], dependencies=protected)
    app.include_router(clients_router, prefix="/api/clients", tags=["Clients"], dependencies=protected)
    app.include_router(plans_router, prefix="/api/plans", tags=["Plans"], dependencies=protected)
    app.include_router(support_router, prefix="/api/support", tags=["Support"], dependencies=protected)
    app.include_router(contracts_router, prefix="/api/contracts", tags=["Contracts"], dependencies=protected)
    app.include_router(contract_templates_router, prefix="/api/contracts/templates", tags=["ContractTemplates"], dependencies=protected)
    app.include_router(billing_router, prefix="/api/billing", tags=["Billing"], dependencies=protected)
    app.include_router(billing_gateway_router, prefix="/api/billing/gateway", tags=["Billing/Gateway"], dependencies=protected)
    app.include_router(billing_gateway_webhooks, prefix="/api/billing/gateway", tags=["Billing/Gateway"])
    app.include_router(cashier_router, prefix="/api/cashier", tags=["Cashier"], dependencies=protected)
    app.include_router(discounts_router, prefix="/api/discounts", tags=["Discounts"], dependencies=protected)
    app.include_router(due_dates_router, prefix="/api/due-dates", tags=["DueDates"], dependencies=protected)
    app.include_router(fiscal_router, prefix="/api/fiscal", tags=["Fiscal"], dependencies=protected)
    app.include_router(network_router, prefix="/api/network", tags=["Network"], dependencies=protected)
    app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"], dependencies=protected)
    app.include_router(contract_tech_router, prefix="/api/contract-tech", tags=["ContractTech"], dependencies=protected)
    app.include_router(service_orders_router, prefix="/api/service-orders", tags=["ServiceOrders"], dependencies=protected)
    app.include_router(communication_router, prefix="/api/communication", tags=["Communication"], dependencies=protected)
    app.include_router(reports_router, prefix="/api/reports", tags=["Reports"], dependencies=protected)
    app.include_router(stock_router, prefix="/api/stock", tags=["Stock"], dependencies=protected)
    app.include_router(customer_app_router, prefix="/api/customer", tags=["CustomerApp"], dependencies=protected)
    app.include_router(technician_app_router, prefix="/api/technician", tags=["TechnicianApp"], dependencies=protected)
    app.include_router(referrals_router, prefix="/api/referrals", tags=["Referrals"], dependencies=protected)
    app.include_router(viability_router, prefix="/api/viability", tags=["Viability"], dependencies=protected)
    app.include_router(health_router, tags=["Health"])
    app.include_router(audit_router, tags=["Audit"], dependencies=protected)

    return app


app = create_app()
