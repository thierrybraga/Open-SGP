"""
Arquivo: app/modules/anatel/routes.py

Responsabilidade:
Rotas REST para relatórios ANATEL (SICI e PPP SCM).

Integrações:
- core.dependencies
- modules.anatel.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import ANATELReport
from .schemas import (
    SICIRequest, SICIOut,
    PPPSCMRequest, PPPSCMOut,
    ANATELReportOut, ANATELReportList
)
from .service import (
    generate_sici_report,
    generate_ppp_scm_report,
    list_anatel_reports,
    get_anatel_report
)


router = APIRouter()


# ===== SICI (Sistema de Coleta de Informações) =====

@router.post("/sici", response_model=SICIOut, dependencies=[Depends(require_permissions("anatel.sici.generate"))])
def generate_sici_endpoint(data: SICIRequest, db: Session = Depends(get_db)):
    """
    Gera relatório SICI (Sistema de Coleta de Informações).

    Especificação ANATEL: Dados de assinantes SCM.
    Periodicidade: Mensal
    Formato: CSV com separador ';'
    """
    try:
        result = generate_sici_report(db, data)
        return SICIOut(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/sici/{year}/{month}/download")
def download_sici_endpoint(
    year: int,
    month: int,
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db)
):
    """
    Gera e baixa relatório SICI em formato CSV.
    """
    try:
        data = SICIRequest(
            reference_year=year,
            reference_month=month,
            include_inactive=include_inactive
        )
        result = generate_sici_report(db, data)

        filename = f"SICI_{year}_{month:02d}.csv"

        return Response(
            content=result["file_content"],
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===== PPP SCM (Plano de Metas de Qualidade) =====

@router.post("/ppp-scm", response_model=PPPSCMOut, dependencies=[Depends(require_permissions("anatel.ppp_scm.generate"))])
def generate_ppp_scm_endpoint(data: PPPSCMRequest, db: Session = Depends(get_db)):
    """
    Gera relatório PPP SCM (Plano de Metas de Qualidade).

    Especificação ANATEL: Dados de infraestrutura e qualidade por município.
    Periodicidade: Mensal
    Formato: CSV com separador ';'
    """
    try:
        result = generate_ppp_scm_report(db, data)
        return PPPSCMOut(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/ppp-scm/{year}/{month}/download")
def download_ppp_scm_endpoint(
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    """
    Gera e baixa relatório PPP SCM em formato CSV.
    """
    try:
        data = PPPSCMRequest(
            reference_year=year,
            reference_month=month
        )
        result = generate_ppp_scm_report(db, data)

        filename = f"PPP_SCM_{year}_{month:02d}.csv"

        return Response(
            content=result["file_content"],
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===== HISTÓRICO DE RELATÓRIOS =====

@router.get("/reports", response_model=ANATELReportList)
def list_reports_endpoint(
    report_type: Optional[str] = Query(default=None),
    year: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista relatórios ANATEL gerados.
    """
    reports = list_anatel_reports(db, report_type=report_type, year=year)
    return ANATELReportList(
        reports=[ANATELReportOut(**r.__dict__) for r in reports],
        total=len(reports)
    )


@router.get("/reports/{report_id}", response_model=ANATELReportOut)
def get_report_endpoint(report_id: int, db: Session = Depends(get_db)):
    """
    Busca relatório ANATEL por ID.
    """
    try:
        report = get_anatel_report(db, report_id)
        return ANATELReportOut(**report.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/reports/{report_id}/download")
def download_report_endpoint(report_id: int, db: Session = Depends(get_db)):
    """
    Baixa arquivo de relatório ANATEL já gerado.
    """
    try:
        report = get_anatel_report(db, report_id)

        if not report.file_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File content not available"
            )

        # Nome do arquivo
        report_type_map = {
            "sici": "SICI",
            "ppp_scm": "PPP_SCM"
        }
        report_type_name = report_type_map.get(report.report_type, report.report_type.upper())
        filename = f"{report_type_name}_{report.reference_year}_{report.reference_month:02d}.csv"

        return Response(
            content=report.file_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/reports/{report_id}", dependencies=[Depends(require_permissions("anatel.reports.delete"))])
def delete_report_endpoint(report_id: int, db: Session = Depends(get_db)):
    """
    Remove relatório ANATEL do histórico.
    """
    try:
        report = get_anatel_report(db, report_id)
        db.delete(report)
        db.commit()
        return {"message": "Report deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===== DASHBOARD / ESTATÍSTICAS =====

@router.get("/dashboard/statistics")
def get_anatel_statistics(db: Session = Depends(get_db)):
    """
    Retorna estatísticas agregadas dos relatórios ANATEL.
    """
    import json
    from datetime import datetime

    # Buscar relatórios do ano corrente
    current_year = datetime.now().year

    sici_reports = db.query(ANATELReport).filter(
        ANATELReport.report_type == "sici",
        ANATELReport.reference_year == current_year
    ).all()

    ppp_reports = db.query(ANATELReport).filter(
        ANATELReport.report_type == "ppp_scm",
        ANATELReport.reference_year == current_year
    ).all()

    # Agregar estatísticas
    total_sici = len(sici_reports)
    total_ppp = len(ppp_reports)

    latest_sici_stats = {}
    if sici_reports:
        latest = sici_reports[0]
        if latest.stats_json:
            latest_sici_stats = json.loads(latest.stats_json)

    latest_ppp_stats = {}
    if ppp_reports:
        latest = ppp_reports[0]
        if latest.stats_json:
            latest_ppp_stats = json.loads(latest.stats_json)

    return {
        "current_year": current_year,
        "sici": {
            "total_reports_generated": total_sici,
            "latest_statistics": latest_sici_stats
        },
        "ppp_scm": {
            "total_reports_generated": total_ppp,
            "latest_statistics": latest_ppp_stats
        }
    }
