"""
Arquivo: app/core/database.py

Responsabilidade:
Configura o SQLAlchemy 2.0, cria engine e SessionLocal, e expõe Base declarativa.

Integrações:
- core.config
- modules.* modelos
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.effective_database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """
    Dependency que fornece uma sessão de banco de dados.
    Garante que a sessão seja fechada após o uso.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def import_all_models() -> None:
    """
    Importa todos os modelos para garantir que o SQLAlchemy
    conheça todos os relacionamentos antes de criar as tabelas.
    """
    try:
        from ..modules.users import models as _users
        from ..modules.roles import models as _roles
        from ..modules.permissions import models as _perms
    except Exception:
        pass
    try:
        from ..modules.clients import models as _clients
    except Exception:
        pass
    try:
        from ..modules.viability import models as _viability
    except Exception:
        pass
    try:
        from ..modules.plans import models as _plans
    except Exception:
        pass
    try:
        from ..modules.contracts import models as _contracts
    except Exception:
        pass
    try:
        from ..modules.contract_tech import models as _contract_tech
    except Exception:
        pass
    try:
        from ..modules.contract_templates import models as _contract_templates
    except Exception:
        pass
    try:
        from ..modules.billing import models as _billing
        from ..modules.billing.gateway import models as _billing_gw
    except Exception:
        pass
    try:
        from ..modules.cashier import models as _cashier
    except Exception:
        pass
    try:
        from ..modules.discounts import models as _discounts
    except Exception:
        pass
    try:
        from ..modules.due_dates import models as _due_dates
    except Exception:
        pass
    try:
        from ..modules.referrals import models as _referrals
    except Exception:
        pass
    try:
        from ..modules.network import models as _network
    except Exception:
        pass
    try:
        from ..modules.support import models as _support
    except Exception:
        pass
    try:
        from ..modules.communication import models as _comm
    except Exception:
        pass
    try:
        from ..modules.service_orders import models as _so
    except Exception:
        pass
    try:
        from ..modules.fiscal import models as _fiscal
    except Exception:
        pass
    try:
        from ..modules.anatel import models as _anatel
    except Exception:
        pass
    try:
        from ..modules.reports import models as _reports
    except Exception:
        pass
    try:
        from ..modules.stock import models as _stock
    except Exception:
        pass
    try:
        from ..modules.customer_app import models as _customer_app
    except Exception:
        pass
    try:
        from ..modules.technician_app import models as _technician_app
    except Exception:
        pass
    try:
        from ..modules.audit import models as _audit
    except Exception:
        pass
    try:
        from ..modules.administration.pops import models as _pops
        from ..modules.administration.nas import models as _nas
        from ..modules.administration.variables import models as _vars
        from ..modules.administration.backups import models as _backups
        from ..modules.administration.finance import models as _finance
        from ..modules.administration.setup import models as _setup
    except Exception:
        pass
    try:
        from ..modules.notifications import models as _notifications
    except Exception:
        pass


def ensure_required_columns() -> None:
    """
    Executa verificações rápidas de esquema e aplica correções mínimas
    para campos críticos ausentes que impedem a inicialização do painel.
    """
    try:
        with engine.connect() as conn:
            # support_tickets.sla_due_at
            cols_res = conn.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name='support_tickets'")
            )
            cols = [row[0] for row in cols_res.fetchall()]
            if "sla_due_at" not in cols:
                conn.execute(text("ALTER TABLE support_tickets ADD COLUMN sla_due_at TIMESTAMP NULL"))
                conn.commit()

            # network_devices.zabbix_monitored / zabbix_host_id
            nd_cols_res = conn.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name='network_devices'")
            )
            nd_cols = [row[0] for row in nd_cols_res.fetchall()]
            if "zabbix_monitored" not in nd_cols:
                conn.execute(text("ALTER TABLE network_devices ADD COLUMN zabbix_monitored BOOLEAN DEFAULT FALSE"))
                conn.commit()
            if "zabbix_host_id" not in nd_cols:
                conn.execute(text("ALTER TABLE network_devices ADD COLUMN zabbix_host_id VARCHAR(20) NULL"))
                conn.commit()

    except Exception as e:
        # Log não fatal: se falhar, o painel pode continuar, mas a dashboard pode quebrar
        print(f"Schema check warning: {e}")
