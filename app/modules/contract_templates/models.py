"""
Arquivo: app/modules/contract_templates/models.py

Responsabilidade:
Modelos de Templates de Contrato e Aditivos.

Integrações:
- core.database
- shared.models
"""

from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin


class ContractTemplate(Base, TimestampMixin):
    __tablename__ = "contract_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    version: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Conteúdo do template (HTML ou Markdown)
    content: Mapped[str] = mapped_column(Text)

    # Variáveis disponíveis (JSON com lista de variáveis)
    available_variables: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Auditoria
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relacionamentos
    creator = relationship("User", foreign_keys=[created_by])


class ContractAddendum(Base, TimestampMixin):
    __tablename__ = "contract_addendums"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"), index=True)
    addendum_number: Mapped[int] = mapped_column(Integer)  # 1, 2, 3...

    # Tipo de aditivo
    type: Mapped[str] = mapped_column(String(50))  # plan_change, price_change, term_change, other

    # Descrição
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)

    # Vigência
    effective_date: Mapped[datetime] = mapped_column()

    # Valores antigos e novos (JSON)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Documento
    document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Auditoria
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)

    # Relacionamentos
    contract = relationship("Contract", back_populates="addendums")
    creator = relationship("User", foreign_keys=[created_by])
