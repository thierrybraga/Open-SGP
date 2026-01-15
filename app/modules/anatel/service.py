"""
Arquivo: app/modules/anatel/service.py

Responsabilidade:
Lógica de geração dos relatórios ANATEL (SICI e PPP SCM).

Integrações:
- modules.clients.models
- modules.contracts.models
- modules.support.models
- modules.service_orders.models
"""

from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func, case
import json

from .models import ANATELReport
from ..clients.models import Client
from ..contracts.models import Contract
from ..plans.models import Plan
from ..support.models import Ticket
from ..service_orders.models import ServiceOrder


def generate_sici_report(db: Session, data) -> dict:
    """
    Gera relatório SICI (Sistema de Coleta de Informações).

    Especificação ANATEL: Informações sobre assinantes de SCM.
    Periodicidade: Mensal
    """
    from ..administration.finance.models import Company

    # Buscar dados da empresa
    company = db.query(Company).first()
    if not company:
        raise ValueError("Company not configured")

    cnpj_prestadora = company.document.replace(".", "").replace("/", "").replace("-", "")

    # Período de referência
    reference_period = f"{data.reference_year}-{data.reference_month:02d}"

    # Query de contratos ativos no período
    q = db.query(Contract).join(Client).join(Plan)

    # Filtrar por status
    if not data.include_inactive:
        q = q.filter(Contract.status.in_(["active", "suspended"]))

    contracts = q.all()

    # Gerar registros SICI
    records = []
    stats = {
        "total_active": 0,
        "total_inactive": 0,
        "total_suspended": 0,
        "by_technology": {},
        "by_speed": {},
        "by_municipality": {}
    }

    for contract in contracts:
        if not contract.client:
            continue

        # Determinar tecnologia (baseado em configuração do plano ou padrão)
        technology = "Fibra Óptica"  # Padrão - pode ser configurado no plano
        if hasattr(contract.plan, 'technology'):
            technology = contract.plan.technology

        # Mapear tecnologia para código ANATEL
        tech_map = {
            "Fibra Óptica": "FIBRA",
            "Fibra": "FIBRA",
            "Rádio": "RADIO",
            "Wireless": "RADIO",
            "Cabo": "CABO",
            "xDSL": "xDSL",
            "Satelite": "SATELITE"
        }
        tech_code = tech_map.get(technology, "OUTROS")

        # Status do assinante
        status_map = {
            "active": "A",
            "suspended": "S",
            "inactive": "I",
            "canceled": "I"
        }
        status_code = status_map.get(contract.status, "I")

        # Atualizar estatísticas
        if status_code == "A":
            stats["total_active"] += 1
        elif status_code == "S":
            stats["total_suspended"] += 1
        else:
            stats["total_inactive"] += 1

        stats["by_technology"][tech_code] = stats["by_technology"].get(tech_code, 0) + 1

        # Velocidade
        download_kbps = int(contract.plan.download_speed * 1024) if contract.plan.download_speed else 0
        upload_kbps = int(contract.plan.upload_speed * 1024) if contract.plan.upload_speed else 0

        # Classificar velocidade
        if download_kbps <= 512:
            speed_class = "ate_512kbps"
        elif download_kbps <= 2048:
            speed_class = "512kbps_2mbps"
        elif download_kbps <= 12288:
            speed_class = "2mbps_12mbps"
        elif download_kbps <= 34816:
            speed_class = "12mbps_34mbps"
        else:
            speed_class = "acima_34mbps"

        stats["by_speed"][speed_class] = stats["by_speed"].get(speed_class, 0) + 1

        # Município (código IBGE)
        municipality_code = contract.client.city_ibge_code if hasattr(contract.client, 'city_ibge_code') else "0000000"
        if not municipality_code or municipality_code == "0000000":
            # Tentar buscar do endereço
            if contract.client.addresses and len(contract.client.addresses) > 0:
                # Usar código IBGE padrão ou configurado
                municipality_code = "3550308"  # São Paulo (padrão)

        stats["by_municipality"][municipality_code] = stats["by_municipality"].get(municipality_code, 0) + 1

        # Criar registro
        record = {
            "cnpj_prestadora": cnpj_prestadora,
            "codigo_ibge_municipio": municipality_code,
            "tipo_pessoa": contract.client.person_type,
            "cpf_cnpj_assinante": contract.client.document.replace(".", "").replace("/", "").replace("-", ""),
            "tipo_produto": "SCM",
            "tecnologia": tech_code,
            "velocidade_download_kbps": download_kbps,
            "velocidade_upload_kbps": upload_kbps,
            "status_assinante": status_code,
            "data_ativacao": contract.activation_date.isoformat() if contract.activation_date else contract.created_at[:10],
            "data_desativacao": contract.deactivation_date.isoformat() if hasattr(contract, 'deactivation_date') and contract.deactivation_date else None,
            "valor_mensalidade": float(contract.plan.price) if contract.plan.price else 0.0
        }

        records.append(record)

    # Gerar arquivo SICI (formato CSV)
    file_lines = []

    # Header
    file_lines.append("CNPJ_PRESTADORA;CODIGO_IBGE_MUNICIPIO;TIPO_PESSOA;CPF_CNPJ_ASSINANTE;TIPO_PRODUTO;TECNOLOGIA;VELOCIDADE_DOWNLOAD_KBPS;VELOCIDADE_UPLOAD_KBPS;STATUS_ASSINANTE;DATA_ATIVACAO;DATA_DESATIVACAO;VALOR_MENSALIDADE")

    # Data rows
    for record in records:
        line = ";".join([
            record["cnpj_prestadora"],
            record["codigo_ibge_municipio"],
            record["tipo_pessoa"],
            record["cpf_cnpj_assinante"],
            record["tipo_produto"],
            record["tecnologia"],
            str(record["velocidade_download_kbps"]),
            str(record["velocidade_upload_kbps"]),
            record["status_assinante"],
            record["data_ativacao"],
            record["data_desativacao"] or "",
            f"{record['valor_mensalidade']:.2f}"
        ])
        file_lines.append(line)

    file_content = "\n".join(file_lines)

    # Salvar histórico
    report = ANATELReport(
        report_type="sici",
        reference_period=reference_period,
        reference_year=data.reference_year,
        reference_month=data.reference_month,
        total_records=len(records),
        file_content=file_content,
        generation_status="completed",
        stats_json=json.dumps(stats)
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "reference_period": reference_period,
        "total_records": len(records),
        "total_active": stats["total_active"],
        "total_inactive": stats["total_inactive"],
        "total_suspended": stats["total_suspended"],
        "file_content": file_content,
        "statistics": stats
    }


def generate_ppp_scm_report(db: Session, data) -> dict:
    """
    Gera relatório PPP SCM (Plano de Metas de Qualidade).

    Especificação ANATEL: Dados de infraestrutura e qualidade por município.
    Periodicidade: Mensal
    """
    from ..administration.finance.models import Company

    # Buscar dados da empresa
    company = db.query(Company).first()
    if not company:
        raise ValueError("Company not configured")

    cnpj_prestadora = company.document.replace(".", "").replace("/", "").replace("-", "")

    # Período de referência
    reference_period = f"{data.reference_year}-{data.reference_month:02d}"

    # Data de início e fim do período
    year = data.reference_year
    month = data.reference_month
    if month == 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1

    period_start = f"{year}-{month:02d}-01"
    period_end = f"{next_year}-{next_month:02d}-01"

    # Buscar contratos ativos agrupados por município
    contracts_query = db.query(
        Client.city_ibge_code,
        func.count(Contract.id).label('total_acessos')
    ).join(
        Contract, Client.id == Contract.client_id
    ).join(
        Plan, Contract.plan_id == Plan.id
    ).filter(
        Contract.status == "active"
    ).group_by(Client.city_ibge_code)

    # Dados agregados por município
    municipalities_data = {}

    for row in contracts_query.all():
        city_code = row.city_ibge_code if row.city_ibge_code else "3550308"
        municipalities_data[city_code] = {
            "total_acessos": row.total_acessos,
            "acessos_fibra": 0,
            "acessos_radio": 0,
            "acessos_cabo": 0,
            "acessos_outros": 0,
            "ate_512kbps": 0,
            "512kbps_2mbps": 0,
            "2mbps_12mbps": 0,
            "12mbps_34mbps": 0,
            "acima_34mbps": 0
        }

    # Buscar detalhes de tecnologia e velocidade por município
    contracts = db.query(Contract).join(Client).join(Plan).filter(
        Contract.status == "active"
    ).all()

    for contract in contracts:
        if not contract.client:
            continue

        city_code = contract.client.city_ibge_code if hasattr(contract.client, 'city_ibge_code') and contract.client.city_ibge_code else "3550308"

        if city_code not in municipalities_data:
            continue

        # Tecnologia
        technology = "Fibra Óptica"
        if hasattr(contract.plan, 'technology'):
            technology = contract.plan.technology

        if "Fibra" in technology:
            municipalities_data[city_code]["acessos_fibra"] += 1
        elif "Rádio" in technology or "Wireless" in technology:
            municipalities_data[city_code]["acessos_radio"] += 1
        elif "Cabo" in technology:
            municipalities_data[city_code]["acessos_cabo"] += 1
        else:
            municipalities_data[city_code]["acessos_outros"] += 1

        # Velocidade
        download_mbps = contract.plan.download_speed if contract.plan.download_speed else 0

        if download_mbps <= 0.5:
            municipalities_data[city_code]["ate_512kbps"] += 1
        elif download_mbps <= 2:
            municipalities_data[city_code]["512kbps_2mbps"] += 1
        elif download_mbps <= 12:
            municipalities_data[city_code]["2mbps_12mbps"] += 1
        elif download_mbps <= 34:
            municipalities_data[city_code]["12mbps_34mbps"] += 1
        else:
            municipalities_data[city_code]["acima_34mbps"] += 1

    # Buscar dados de qualidade (tickets de suporte e OSs)
    quality_data = {}

    for city_code in municipalities_data.keys():
        # Solicitações de reparo (tickets técnicos no período)
        repair_tickets = db.query(func.count(Ticket.id)).join(
            Contract, Ticket.contract_id == Contract.id
        ).join(
            Client, Contract.client_id == Client.id
        ).filter(
            Client.city_ibge_code == city_code,
            Ticket.category == "technical",
            Ticket.created_at >= period_start,
            Ticket.created_at < period_end
        ).scalar()

        # Reparos concluídos em até 24h (service orders)
        repairs_24h = db.query(func.count(ServiceOrder.id)).join(
            Contract, ServiceOrder.contract_id == Contract.id
        ).join(
            Client, Contract.client_id == Client.id
        ).filter(
            Client.city_ibge_code == city_code,
            ServiceOrder.service_type == "repair",
            ServiceOrder.status == "completed",
            ServiceOrder.created_at >= period_start,
            ServiceOrder.created_at < period_end
        ).scalar()

        # Reclamações
        complaints = db.query(func.count(Ticket.id)).join(
            Contract, Ticket.contract_id == Contract.id
        ).join(
            Client, Contract.client_id == Client.id
        ).filter(
            Client.city_ibge_code == city_code,
            Ticket.category == "complaint",
            Ticket.created_at >= period_start,
            Ticket.created_at < period_end
        ).scalar()

        complaints_valid = db.query(func.count(Ticket.id)).join(
            Contract, Ticket.contract_id == Contract.id
        ).join(
            Client, Contract.client_id == Client.id
        ).filter(
            Client.city_ibge_code == city_code,
            Ticket.category == "complaint",
            Ticket.status.in_(["resolved", "closed"]),
            Ticket.created_at >= period_start,
            Ticket.created_at < period_end
        ).scalar()

        quality_data[city_code] = {
            "solicitacoes_reparo": repair_tickets or 0,
            "reparos_ate_24h": repairs_24h or 0,
            "reclamacoes_mes": complaints or 0,
            "reclamacoes_procedentes": complaints_valid or 0
        }

    # Gerar arquivo PPP SCM (formato CSV)
    file_lines = []

    # Header
    file_lines.append("CNPJ_PRESTADORA;CODIGO_IBGE_MUNICIPIO;TOTAL_ACESSOS_SCM;ACESSOS_SCM_FIBRA;ACESSOS_SCM_RADIO;ACESSOS_SCM_CABO;ACESSOS_SCM_OUTROS;ACESSOS_ATE_512KBPS;ACESSOS_512KBPS_2MBPS;ACESSOS_2MBPS_12MBPS;ACESSOS_12MBPS_34MBPS;ACESSOS_ACIMA_34MBPS;SOLICITACOES_REPARO;REPAROS_ATE_24H;RECLAMACOES_MES;RECLAMACOES_PROCEDENTES")

    # Data rows
    total_accesses = 0
    for city_code, data_mun in municipalities_data.items():
        quality = quality_data.get(city_code, {
            "solicitacoes_reparo": 0,
            "reparos_ate_24h": 0,
            "reclamacoes_mes": 0,
            "reclamacoes_procedentes": 0
        })

        line = ";".join([
            cnpj_prestadora,
            city_code,
            str(data_mun["total_acessos"]),
            str(data_mun["acessos_fibra"]),
            str(data_mun["acessos_radio"]),
            str(data_mun["acessos_cabo"]),
            str(data_mun["acessos_outros"]),
            str(data_mun["ate_512kbps"]),
            str(data_mun["512kbps_2mbps"]),
            str(data_mun["2mbps_12mbps"]),
            str(data_mun["12mbps_34mbps"]),
            str(data_mun["acima_34mbps"]),
            str(quality["solicitacoes_reparo"]),
            str(quality["reparos_ate_24h"]),
            str(quality["reclamacoes_mes"]),
            str(quality["reclamacoes_procedentes"])
        ])
        file_lines.append(line)
        total_accesses += data_mun["total_acessos"]

    file_content = "\n".join(file_lines)

    # Estatísticas
    stats = {
        "total_municipalities": len(municipalities_data),
        "total_accesses": total_accesses,
        "by_technology": {
            "fibra": sum(d["acessos_fibra"] for d in municipalities_data.values()),
            "radio": sum(d["acessos_radio"] for d in municipalities_data.values()),
            "cabo": sum(d["acessos_cabo"] for d in municipalities_data.values()),
            "outros": sum(d["acessos_outros"] for d in municipalities_data.values())
        },
        "by_speed": {
            "ate_512kbps": sum(d["ate_512kbps"] for d in municipalities_data.values()),
            "512kbps_2mbps": sum(d["512kbps_2mbps"] for d in municipalities_data.values()),
            "2mbps_12mbps": sum(d["2mbps_12mbps"] for d in municipalities_data.values()),
            "12mbps_34mbps": sum(d["12mbps_34mbps"] for d in municipalities_data.values()),
            "acima_34mbps": sum(d["acima_34mbps"] for d in municipalities_data.values())
        },
        "quality": {
            "total_repairs": sum(q["solicitacoes_reparo"] for q in quality_data.values()),
            "repairs_24h": sum(q["reparos_ate_24h"] for q in quality_data.values()),
            "total_complaints": sum(q["reclamacoes_mes"] for q in quality_data.values()),
            "valid_complaints": sum(q["reclamacoes_procedentes"] for q in quality_data.values())
        }
    }

    # Salvar histórico
    report = ANATELReport(
        report_type="ppp_scm",
        reference_period=reference_period,
        reference_year=data.reference_year,
        reference_month=data.reference_month,
        total_records=len(municipalities_data),
        file_content=file_content,
        generation_status="completed",
        stats_json=json.dumps(stats)
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "reference_period": reference_period,
        "total_municipalities": len(municipalities_data),
        "total_accesses": total_accesses,
        "file_content": file_content,
        "statistics": stats
    }


def list_anatel_reports(db: Session, report_type: str = None, year: int = None) -> list:
    """
    Lista relatórios ANATEL gerados.
    """
    q = db.query(ANATELReport)

    if report_type:
        q = q.filter(ANATELReport.report_type == report_type)
    if year:
        q = q.filter(ANATELReport.reference_year == year)

    reports = q.order_by(ANATELReport.created_at.desc()).all()
    return reports


def get_anatel_report(db: Session, report_id: int) -> ANATELReport:
    """
    Busca relatório ANATEL por ID.
    """
    report = db.query(ANATELReport).filter(ANATELReport.id == report_id).first()
    if not report:
        raise ValueError("Report not found")
    return report
