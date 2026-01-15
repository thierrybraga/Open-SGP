"""
Arquivo: app/modules/fiscal/models.py

Responsabilidade:
Definição dos modelos de banco de dados para o módulo fiscal (Notas Fiscais, Configurações Fiscais).

Integrações:
- app.modules.contracts.models
- app.modules.billing.models
- app.modules.plans.models
"""

from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from ...core.database import Base
from ...shared.models import TimestampMixin

class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    title_id = Column(Integer, ForeignKey("titles.id", ondelete="SET NULL"), nullable=True)
    number = Column(String(20), nullable=False, index=True)
    series = Column(String(5), nullable=False, server_default="1")
    status = Column(String(20), nullable=False, index=True) # draft, emitted, canceled
    issue_date = Column(Date, nullable=True)
    cancel_date = Column(Date, nullable=True)
    total_amount = Column(Float, nullable=False)
    service_description = Column(String(500), nullable=False)
    municipality_code = Column(String(10), nullable=False)
    taxation_code = Column(String(10), nullable=False, server_default="0000")
    xml_path = Column(String(500), nullable=True)
    pdf_url = Column(String(500), nullable=True)
    
    invoice_type = Column(String(20), server_default="service", nullable=False) # service, debit_note, telecom_21, telecom_22
    reference_invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    debit_reason = Column(String(500), nullable=True)

    # Relacionamentos
    contract = relationship("Contract", backref="invoices")
    title = relationship("Title", backref="invoices")
    reference_invoice = relationship("Invoice", remote_side=[id])

class ServicePlanDetail(Base, TimestampMixin):
    __tablename__ = "service_plan_details"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    service_code = Column(String(20), nullable=False)
    cnae_code = Column(String(10), nullable=True)
    taxation_code = Column(String(10), nullable=False, server_default="0000")
    fiscal_description = Column(String(500), nullable=False)
    iss_rate = Column(Float, server_default="0.0", nullable=False)
    cofins_rate = Column(Float, server_default="0.0", nullable=False)
    pis_rate = Column(Float, server_default="0.0", nullable=False)
    csll_rate = Column(Float, server_default="0.0", nullable=False)
    irpj_rate = Column(Float, server_default="0.0", nullable=False)
    iss_retention = Column(Boolean, server_default="false", nullable=False)
    municipality_code = Column(String(10), nullable=False)
    notes = Column(String(1000), nullable=True)

    # Relacionamentos
    plan = relationship("Plan", backref="fiscal_details")

class TVTelephonyGateway(Base, TimestampMixin):
    __tablename__ = "tv_telephony_gateways"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    gateway_type = Column(String(20), nullable=False, index=True) # tv, telephony
    provider = Column(String(50), nullable=False) # e.g. "voip_provider_x", "iptv_provider_y"
    api_url = Column(String(500), nullable=False)
    api_key = Column(String(255), nullable=True)
    api_secret = Column(String(255), nullable=True)
    config_json = Column(String(2000), nullable=True)
    is_active = Column(Boolean, server_default="true", nullable=False, index=True)
    is_default = Column(Boolean, server_default="false", nullable=False)
    last_test_at = Column(String(30), nullable=True)
    last_test_success = Column(Boolean, nullable=True)
    last_test_message = Column(String(500), nullable=True)
