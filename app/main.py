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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.database import Base, engine, import_all_models, ensure_required_columns

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

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
from .modules.clients.routes import router as clients_router
from .modules.plans.routes import router as plans_router
from .modules.support.routes import router as support_router
from .modules.contracts.routes import router as contracts_router
from .modules.billing.routes import router as billing_router
from .modules.billing.gateway.routes import router as billing_gateway_router
from .modules.billing.gateway.webhooks import router as billing_gateway_webhooks
from .modules.fiscal.routes import router as fiscal_router
from .modules.network.routes import router as network_router
from .modules.contract_tech.routes import router as contract_tech_router
from .modules.support.routes import router as support_router
from .modules.service_orders.routes import router as service_orders_router
from .modules.communication.routes import router as communication_router
from .modules.reports.routes import router as reports_router
from .modules.stock.routes import router as stock_router
from .modules.customer_app.routes import router as customer_app_router
from .modules.technician_app.routes import router as technician_app_router
from .modules.health.routes import router as health_router
from .modules.audit.routes import router as audit_router
from .modules.notifications.routes import router as notifications_router

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Importar todos os modelos para garantir relacionamentos do SQLAlchemy
    import_all_models()
    # Criar tabelas no banco de dados
    Base.metadata.create_all(bind=engine)
    # Garantir colunas críticas
    ensure_required_columns()
    yield

def create_app() -> FastAPI:
    app = FastAPI(title="ISP ERP API", version="0.1.0", lifespan=lifespan)

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

    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(users_router, prefix="/api/users", tags=["Users"])
    app.include_router(roles_router, prefix="/api/roles", tags=["Roles"])
    app.include_router(permissions_router, prefix="/api/permissions", tags=["Permissions"])
    app.include_router(pops_router, prefix="/api/admin/pops", tags=["Administration/POPs"])
    app.include_router(nas_router, prefix="/api/admin/nas", tags=["Administration/NAS"])
    app.include_router(variables_router, prefix="/api/admin/variables", tags=["Administration/Variables"])
    app.include_router(backups_router, prefix="/api/admin/backups", tags=["Administration/Backups"])
    app.include_router(setup_router, prefix="/api/setup", tags=["Setup"])
    app.include_router(finance_admin_router, prefix="/api/admin/finance", tags=["Administration/Finance"])
    app.include_router(clients_router, prefix="/api/clients", tags=["Clients"])
    app.include_router(plans_router, prefix="/api/plans", tags=["Plans"])
    app.include_router(support_router, prefix="/api/support", tags=["Support"])
    app.include_router(contracts_router, prefix="/api/contracts", tags=["Contracts"])
    app.include_router(billing_router, prefix="/api/billing", tags=["Billing"])
    app.include_router(billing_gateway_router, prefix="/api/billing/gateway", tags=["Billing/Gateway"])
    app.include_router(billing_gateway_webhooks, prefix="/api/billing/gateway", tags=["Billing/Gateway"])
    app.include_router(fiscal_router, prefix="/api/fiscal", tags=["Fiscal"])
    app.include_router(network_router, prefix="/api/network", tags=["Network"])
    app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])
    app.include_router(contract_tech_router, prefix="/api/contract-tech", tags=["ContractTech"])
    app.include_router(support_router, prefix="/api/support", tags=["Support"])
    app.include_router(service_orders_router, prefix="/api/service-orders", tags=["ServiceOrders"])
    app.include_router(communication_router, prefix="/api/communication", tags=["Communication"])
    app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
    app.include_router(stock_router, prefix="/api/stock", tags=["Stock"])
    app.include_router(customer_app_router, prefix="/api/customer", tags=["CustomerApp"])
    app.include_router(technician_app_router, prefix="/api/technician", tags=["TechnicianApp"])
    app.include_router(health_router, tags=["Health"])
    app.include_router(audit_router, tags=["Audit"])

    @app.on_event("startup")
    def on_startup():
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            # Tables may already exist, log and continue
            print(f"Note: Database tables already exist or error creating: {e}")
        # Garantir colunas críticas
        ensure_required_columns()

        try:
            from .modules.permissions.models import Permission
            from .modules.roles.models import Role
            from .modules.users.models import User
            from .core.security import hash_password
            from sqlalchemy.orm import Session

            db = Session(bind=engine)
            base_perms = [
                ("users.create", "Criar usuários"),
                ("users.update", "Atualizar usuários"),
                ("users.roles.assign", "Atribuir roles ao usuário"),
                ("roles.create", "Criar roles"),
                ("permissions.create", "Criar permissões"),
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
                ("network.devices.create", "Criar dispositivos de rede"),
                ("network.vlans.create", "Criar VLANs"),
                ("network.pools.create", "Criar pools de IP"),
                ("network.profiles.create", "Criar perfis de serviço"),
                ("network.assignments.create", "Criar atribuições de rede"),
                ("network.provision", "Provisionar contrato"),
                ("network.block", "Bloquear contrato"),
                ("network.unblock", "Desbloquear contrato"),
                ("network.sync_billing", "Sincronizar bloqueio via financeiro"),
                ("contract_tech.equipment.create", "Registrar equipamentos"),
                ("contract_tech.signal.create", "Registrar medições de sinal"),
                ("contract_tech.speedtest.create", "Registrar speedtests"),
                ("contract_tech.logs.create", "Registrar logs técnicos"),
                ("support.tickets.create", "Criar tickets"),
                ("support.tickets.update", "Atualizar tickets"),
                ("support.messages.create", "Adicionar mensagens em ticket"),
                ("support.tags.create", "Criar tags de ticket"),
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
                ("stock.vehicles.create", "Criar veículos"),
                ("stock.kits.create", "Criar kits"),
                ("stock.purchases.create", "Criar compras"),
                ("stock.transfers.create", "Criar transferências de estoque"),
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
            ]
            for code, desc in base_perms:
                if not db.query(Permission).filter(Permission.code == code).first():
                    db.add(Permission(code=code, description=desc))
            db.commit()

            admin_role = db.query(Role).filter(Role.name == "admin").first()
            if not admin_role:
                admin_role = Role(name="admin")
                admin_role.permissions = db.query(Permission).all()
                db.add(admin_role)
                db.commit()
                db.refresh(admin_role)

            if not db.query(User).filter(User.username == "admin").first():
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    hashed_password=hash_password("admin"),
                    is_active=True,
                )
                admin_user.roles = [admin_role]
                db.add(admin_user)
                db.commit()
        except Exception:
            pass

    return app


app = create_app()
