"""
Arquivo: app/modules/network/routes.py

Responsabilidade:
Rotas REST para rede: dispositivos, VLANs, pools, perfis, atribuições, provisionamento,
bloqueio/desbloqueio e histórico técnico.

Integrações:
- core.dependencies
- modules.network.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import NetworkDevice, VLAN, IPPool, ServiceProfile, ContractNetworkAssignment, ContractTechHistory
from .schemas import (
    DeviceCreate,
    DeviceOut,
    VLANCreate,
    VLANOut,
    IPPoolCreate,
    IPPoolOut,
    ServiceProfileCreate,
    ServiceProfileOut,
    AssignmentCreate,
    AssignmentOut,
    RadiusSessionOut,
    RadiusUsageHistory,
)
from .service import (
    create_device,
    create_vlan,
    create_pool,
    create_profile,
    create_assignment,
    provision_contract,
    block_contract,
    unblock_contract,
    sync_billing_blocking,
    allocate_dynamic_ip,
    release_ip_for_contract,
    get_onu_status,
    unbind_vlan_for_contract,
    get_radius_active_session,
    get_radius_usage_history,
)


router = APIRouter()


@router.get("/devices", response_model=List[DeviceOut])
def list_devices(db: Session = Depends(get_db)):
    items = db.query(NetworkDevice).all()
    return [DeviceOut(**d.__dict__) for d in items]


@router.post("/devices", response_model=DeviceOut, dependencies=[Depends(require_permissions("network.devices.create"))])
def create_device_endpoint(data: DeviceCreate, db: Session = Depends(get_db)):
    d = create_device(db, data)
    return DeviceOut(**d.__dict__)


@router.get("/vlans", response_model=List[VLANOut])
def list_vlans(db: Session = Depends(get_db)):
    items = db.query(VLAN).all()
    return [VLANOut(**v.__dict__) for v in items]


@router.post("/vlans", response_model=VLANOut, dependencies=[Depends(require_permissions("network.vlans.create"))])
def create_vlan_endpoint(data: VLANCreate, db: Session = Depends(get_db)):
    v = create_vlan(db, data)
    return VLANOut(**v.__dict__)


@router.get("/pools", response_model=List[IPPoolOut])
def list_pools(db: Session = Depends(get_db)):
    items = db.query(IPPool).all()
    return [IPPoolOut(**p.__dict__) for p in items]


@router.post("/pools", response_model=IPPoolOut, dependencies=[Depends(require_permissions("network.pools.create"))])
def create_pool_endpoint(data: IPPoolCreate, db: Session = Depends(get_db)):
    p = create_pool(db, data)
    return IPPoolOut(**p.__dict__)


@router.get("/profiles", response_model=List[ServiceProfileOut])
def list_profiles(db: Session = Depends(get_db)):
    items = db.query(ServiceProfile).all()
    return [ServiceProfileOut(**s.__dict__) for s in items]


@router.post("/profiles", response_model=ServiceProfileOut, dependencies=[Depends(require_permissions("network.profiles.create"))])
def create_profile_endpoint(data: ServiceProfileCreate, db: Session = Depends(get_db)):
    s = create_profile(db, data)
    return ServiceProfileOut(**s.__dict__)


@router.get("/assignments", response_model=List[AssignmentOut])
def list_assignments(contract_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(ContractNetworkAssignment)
    if contract_id:
        q = q.filter(ContractNetworkAssignment.contract_id == contract_id)
    items = q.all()
    return [AssignmentOut(**a.__dict__) for a in items]


@router.post("/assignments", response_model=AssignmentOut, dependencies=[Depends(require_permissions("network.assignments.create"))])
def create_assignment_endpoint(data: AssignmentCreate, db: Session = Depends(get_db)):
    a = create_assignment(db, data)
    return AssignmentOut(**a.__dict__)


@router.post("/provision/{contract_id}", response_model=AssignmentOut, dependencies=[Depends(require_permissions("network.provision"))])
def provision_contract_endpoint(contract_id: int, db: Session = Depends(get_db)):
    try:
        a = provision_contract(db, contract_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return AssignmentOut(**a.__dict__)


@router.post("/block/{contract_id}", response_model=AssignmentOut, dependencies=[Depends(require_permissions("network.block"))])
def block_contract_endpoint(contract_id: int, db: Session = Depends(get_db)):
    try:
        a = block_contract(db, contract_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return AssignmentOut(**a.__dict__)


@router.post("/unblock/{contract_id}", response_model=AssignmentOut, dependencies=[Depends(require_permissions("network.unblock"))])
def unblock_contract_endpoint(contract_id: int, db: Session = Depends(get_db)):
    try:
        a = unblock_contract(db, contract_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return AssignmentOut(**a.__dict__)


@router.get("/tech-history/{contract_id}")
def tech_history(contract_id: int, db: Session = Depends(get_db)):
    items = db.query(ContractTechHistory).filter(ContractTechHistory.contract_id == contract_id).all()
    return [
        {
            "id": h.id,
            "contract_id": h.contract_id,
            "action": h.action,
            "description": h.description,
            "occurred_at": h.occurred_at.isoformat(),
        }
        for h in items
    ]


@router.post("/sync-billing/{contract_id}", response_model=AssignmentOut, dependencies=[Depends(require_permissions("network.sync_billing"))])
def sync_billing(contract_id: int, db: Session = Depends(get_db)):
    a = sync_billing_blocking(db, contract_id)
    return AssignmentOut(**a.__dict__)


@router.post("/assignments/{contract_id}/allocate-ip", dependencies=[Depends(require_permissions("network.assignments.create"))])
def allocate_ip(contract_id: int, db: Session = Depends(get_db)):
    a = db.query(ContractNetworkAssignment).filter(ContractNetworkAssignment.contract_id == contract_id).first()
    if not a or not a.ip_pool:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignment or pool missing")
    lease = allocate_dynamic_ip(db, a.ip_pool.id, contract_id)
    a.static_ip = lease.ip_address
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"contract_id": contract_id, "ip": lease.ip_address}


@router.post("/assignments/{contract_id}/release-ip", dependencies=[Depends(require_permissions("network.assignments.create"))])
def release_ip(contract_id: int, db: Session = Depends(get_db)):
    lease = release_ip_for_contract(db, contract_id)
    a = db.query(ContractNetworkAssignment).filter(ContractNetworkAssignment.contract_id == contract_id).first()
    if a and lease:
        if a.static_ip == lease.ip_address:
            a.static_ip = None
            db.add(a)
            db.commit()
            db.refresh(a)
    return {"contract_id": contract_id, "released": bool(lease), "ip": lease.ip_address if lease else None}


@router.get("/olt/{device_id}/onu/{onu_id}/status")
def onu_status(device_id: int, onu_id: str, db: Session = Depends(get_db)):
    try:
        status = get_onu_status(db, device_id, onu_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/assignments/{contract_id}/unbind-vlan", dependencies=[Depends(require_permissions("network.assignments.update"))])
def unbind_vlan(contract_id: int, db: Session = Depends(get_db)):
    try:
        a = unbind_vlan_for_contract(db, contract_id)
        return AssignmentOut(**a.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/radius/session/{username}", response_model=Optional[RadiusSessionOut])
def radius_session(username: str, db: Session = Depends(get_db)):
    return get_radius_active_session(db, username)


@router.get("/radius/history/{username}", response_model=List[RadiusUsageHistory])
def radius_history(username: str, db: Session = Depends(get_db)):
    return get_radius_usage_history(db, username)
