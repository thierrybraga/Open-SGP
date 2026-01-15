"""
Arquivo: app/modules/administration/setup/routes.py

Responsabilidade:
Rotas REST para wizard de setup inicial.

Integrações:
- core.dependencies
- modules.administration.setup.service
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....core.dependencies import get_db
from .models import SetupProgress
from .schemas import (
    CompanySetup, FinancialSetup, NetworkSetup, PlanSetup,
    ContractTemplateSetup, EmailSetup, MonitoringSetup, FirstUserSetup,
    SetupProgressOut, CompleteSetupRequest
)
from .service import (
    get_or_create_setup_progress,
    setup_step1_company,
    setup_step2_financial,
    setup_step3_network,
    setup_step4_plan,
    setup_step5_contract_template,
    setup_step6_email,
    setup_step_monitoring,
    setup_step7_first_user,
    complete_setup_wizard
)


router = APIRouter()


@router.get("/progress", response_model=SetupProgressOut)
def get_setup_progress(db: Session = Depends(get_db)):
    """
    Retorna progresso atual do wizard de setup.
    """
    progress = get_or_create_setup_progress(db)
    return SetupProgressOut(
        **progress.__dict__,
        progress_percentage=progress.get_progress_percentage()
    )


@router.post("/step1/company")
def setup_company(data: CompanySetup, db: Session = Depends(get_db)):
    """
    Etapa 1: Configura empresa.
    """
    try:
        company = setup_step1_company(db, data)
        return {"success": True, "company_id": company.id, "message": "Company configured successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/step2/financial")
def setup_financial(data: FinancialSetup, db: Session = Depends(get_db)):
    """
    Etapa 2: Configura portador e parâmetros financeiros.
    """
    try:
        carrier = setup_step2_financial(db, data)
        return {"success": True, "carrier_id": carrier.id, "message": "Financial configuration completed"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/step3/network")
def setup_network(data: NetworkSetup, db: Session = Depends(get_db)):
    """
    Etapa 3: Configura POP e NAS.
    """
    try:
        pop, nas = setup_step3_network(db, data)
        return {
            "success": True,
            "pop_id": pop.id,
            "nas_id": nas.id,
            "message": "Network configuration completed"
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/step4/plan")
def setup_plan(data: PlanSetup, db: Session = Depends(get_db)):
    """
    Etapa 4: Cria primeiro plano.
    """
    try:
        plan = setup_step4_plan(db, data)
        return {"success": True, "plan_id": plan.id, "message": "Plan created successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/step5/contract-template")
def setup_contract_template(data: ContractTemplateSetup, db: Session = Depends(get_db)):
    """
    Etapa 5: Cria template de contrato.
    """
    try:
        template = setup_step5_contract_template(db, data)
        return {"success": True, "template_id": template.id, "message": "Contract template created"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/step6/email")
def setup_email(data: EmailSetup, db: Session = Depends(get_db)):
    """
    Etapa 6: Configura servidor de email.
    """
    try:
        result = setup_step6_email(db, data)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/step7/monitoring")
def setup_monitoring(data: MonitoringSetup, db: Session = Depends(get_db)):
    """
    Etapa 7: Configura monitoramento (Zabbix).
    """
    try:
        result = setup_step_monitoring(db, data)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/step7/first-user")
def setup_first_user(data: FirstUserSetup, db: Session = Depends(get_db)):
    """
    Etapa 7: Cria primeiro usuário administrador.
    """
    try:
        user = setup_step7_first_user(db, data)
        return {
            "success": True,
            "user_id": user.id,
            "username": user.username,
            "message": "First admin user created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/complete")
def complete_setup(data: CompleteSetupRequest, db: Session = Depends(get_db)):
    """
    Executa wizard completo de uma vez só.
    """
    try:
        result = complete_setup_wizard(db, data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/reset")
def reset_setup(db: Session = Depends(get_db)):
    """
    Reseta o progresso do setup (apenas para desenvolvimento/testes).
    """
    progress = db.query(SetupProgress).first()
    if progress:
        db.delete(progress)
        db.commit()
    return {"success": True, "message": "Setup progress reset"}
