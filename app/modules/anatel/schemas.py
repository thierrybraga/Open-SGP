"""
Arquivo: app/modules/anatel/schemas.py

Responsabilidade:
Schemas Pydantic para relatórios ANATEL.

Integrações:
- modules.anatel.models
"""

from typing import Optional
from pydantic import BaseModel


# ===== SICI (Sistema de Coleta de Informações) =====

class SICIRequest(BaseModel):
    """
    Parâmetros para geração do relatório SICI.
    """
    reference_year: int  # Ano de referência
    reference_month: int  # Mês de referência (1-12)
    include_inactive: bool = False  # Incluir clientes inativos


class SICIRecord(BaseModel):
    """
    Registro individual do SICI.
    """
    # Identificação
    cnpj_prestadora: str  # CNPJ da prestadora
    codigo_ibge_municipio: str  # Código IBGE do município

    # Dados do assinante
    tipo_pessoa: str  # PF ou PJ
    cpf_cnpj_assinante: str  # Documento do assinante

    # Dados do serviço
    tipo_produto: str  # Tipo de produto (SCM)
    tecnologia: str  # Tecnologia (Fibra, Rádio, Cabo, etc)
    velocidade_download_kbps: int  # Velocidade contratada em Kbps
    velocidade_upload_kbps: int  # Velocidade upload em Kbps

    # Status
    status_assinante: str  # A (ativo), I (inativo), S (suspenso)
    data_ativacao: str  # Data de ativação (YYYY-MM-DD)
    data_desativacao: Optional[str] = None  # Data de desativação

    # Valor
    valor_mensalidade: float  # Valor da mensalidade


class SICIOut(BaseModel):
    """
    Saída do relatório SICI.
    """
    reference_period: str  # YYYY-MM
    total_records: int
    total_active: int
    total_inactive: int
    total_suspended: int
    file_content: str  # Conteúdo do arquivo SICI
    statistics: dict  # Estatísticas agregadas


# ===== PPP SCM (Plano de Metas de Qualidade) =====

class PPPSCMRequest(BaseModel):
    """
    Parâmetros para geração do relatório PPP SCM.
    """
    reference_year: int
    reference_month: int


class PPPSCMRecord(BaseModel):
    """
    Registro individual do PPP SCM.
    """
    # Identificação
    cnpj_prestadora: str
    codigo_ibge_municipio: str

    # Infraestrutura
    total_acessos_scm: int  # Total de acessos SCM
    acessos_scm_fibra: int  # Acessos em fibra óptica
    acessos_scm_radio: int  # Acessos em rádio
    acessos_scm_cabo: int  # Acessos em cabo
    acessos_scm_outros: int  # Outros tipos

    # Velocidades
    acessos_ate_512kbps: int
    acessos_512kbps_2mbps: int
    acessos_2mbps_12mbps: int
    acessos_12mbps_34mbps: int
    acessos_acima_34mbps: int

    # Qualidade
    solicitacoes_reparo: int  # Solicitações de reparo no período
    reparos_ate_24h: int  # Reparos concluídos em até 24h

    # Reclamações
    reclamacoes_mes: int  # Reclamações no mês
    reclamacoes_procedentes: int  # Reclamações procedentes


class PPPSCMOut(BaseModel):
    """
    Saída do relatório PPP SCM.
    """
    reference_period: str  # YYYY-MM
    total_municipalities: int
    total_accesses: int
    file_content: str  # Conteúdo do arquivo PPP SCM
    statistics: dict


# ===== HISTÓRICO =====

class ANATELReportOut(BaseModel):
    """
    Saída de relatório ANATEL armazenado.
    """
    id: int
    report_type: str
    reference_period: str
    reference_year: int
    reference_month: int
    total_records: int
    file_path: Optional[str]
    generation_status: str
    error_message: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class ANATELReportList(BaseModel):
    """
    Lista de relatórios ANATEL.
    """
    reports: list[ANATELReportOut]
    total: int
