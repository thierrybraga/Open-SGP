"""
Arquivo: app/modules/network/service.py

Responsabilidade:
Regras de negócio de rede: criar entidades, provisionar contratos, bloquear e
desbloquear conforme status financeiro, registrar histórico técnico.

Integrações:
- modules.network.models
- modules.contracts.models
- modules.billing.models
"""

from datetime import datetime
from sqlalchemy.orm import Session
import ipaddress

from .models import (
    NetworkDevice,
    VLAN,
    IPPool,
    ServiceProfile,
    ContractNetworkAssignment,
    ContractTechHistory,
    IPLease,
    RadAcct,
)
from ..contracts.models import Contract
from ..billing.models import Title
from .schemas import (
    DeviceCreate,
    VLANCreate,
    IPPoolCreate,
    ServiceProfileCreate,
    AssignmentCreate,
    RadiusSessionOut,
    RadiusUsageHistory,
)
from .vendors.mikrotik import MikrotikClient
from .vendors.radius import RadiusClient
from .vendors.olt import OLTClient
from .vendors.vsol import VSOLClient
from .zabbix_sync import sync_device_to_zabbix


def create_device(db: Session, data: DeviceCreate) -> NetworkDevice:
    dev = NetworkDevice(**data.dict())
    db.add(dev)
    db.commit()
    db.refresh(dev)
    
    # Sync with Zabbix if requested
    if dev.zabbix_monitored:
        sync_device_to_zabbix(db, dev.id)
        
    return dev


def create_vlan(db: Session, data: VLANCreate) -> VLAN:
    vlan = VLAN(**data.dict())
    db.add(vlan)
    db.commit()
    db.refresh(vlan)
    return vlan


def create_pool(db: Session, data: IPPoolCreate) -> IPPool:
    pool = IPPool(**data.dict())
    db.add(pool)
    db.commit()
    db.refresh(pool)
    return pool


def create_profile(db: Session, data: ServiceProfileCreate) -> ServiceProfile:
    prof = ServiceProfile(**data.dict())
    db.add(prof)
    db.commit()
    db.refresh(prof)
    return prof


def create_assignment(db: Session, data: AssignmentCreate) -> ContractNetworkAssignment:
    cna = ContractNetworkAssignment(**data.dict())
    db.add(cna)
    db.commit()
    db.refresh(cna)
    return cna


def _write_history(db: Session, contract_id: int, action: str, description: str):
    h = ContractTechHistory(contract_id=contract_id, action=action, description=description)
    db.add(h)
    db.commit()


def _vendor_clients(device: NetworkDevice):
    if device.vendor == "mikrotik":
        return MikrotikClient(device.host, device.port, device.username, device.password)
    if device.vendor in ("huawei", "zte"):
        return OLTClient(device.host, device.username, device.password, vendor=device.vendor)
    if device.vendor == "vsol":
        return VSOLClient(device.host, device.username, device.password)
    return None


def test_device_connection(db: Session, device_id: int) -> bool:
    dev = db.query(NetworkDevice).filter(NetworkDevice.id == device_id).first()
    if not dev:
        raise ValueError("Device not found")
    
    client = _vendor_clients(dev)
    if not client:
        # Generic devices or unknown vendors are considered "connected" if enabled
        return True
        
    # Real connection check
    try:
        if hasattr(client, "check_connection"):
            return client.check_connection()
        return True
    except Exception:
        return False



def provision_contract(db: Session, contract_id: int) -> ContractNetworkAssignment:
    cna = db.query(ContractNetworkAssignment).filter(ContractNetworkAssignment.contract_id == contract_id).first()
    if not cna:
        raise ValueError("Assignment not found")
    dev = cna.device
    client = None
    if dev:
        client = _vendor_clients(dev)
    prof = cna.profile
    # Dynamic IP allocation
    if cna.ip_pool and cna.ip_pool.type == "dynamic" and not cna.static_ip:
        lease = db.query(IPLease).filter(IPLease.contract_id == contract_id, IPLease.status == "allocated").first()
        if not lease:
            lease = allocate_dynamic_ip(db, cna.ip_pool.id, contract_id)
        if lease:
            cna.static_ip = lease.ip_address
    if dev and prof:
        if dev.vendor == "mikrotik":
            mk = MikrotikClient(dev.host, dev.port, dev.username, dev.password)
            mk.provision_simple_queue(
                name=str(contract_id), max_down_mbps=prof.download_speed_mbps, max_up_mbps=prof.upload_speed_mbps
            )
            if cna.static_ip:
                mk.set_static_ip(name=str(contract_id), ip=cna.static_ip)
            if cna.cgnat:
                mk.enable_cgnat(name=str(contract_id))
        elif dev.vendor in ("huawei", "zte", "vsol"):
            if dev.vendor == "vsol":
                olt = VSOLClient(dev.host, dev.username, dev.password)
            else:
                olt = OLTClient(dev.host, dev.username, dev.password, vendor=dev.vendor)
            olt.set_service_profile(
                onu_id=str(contract_id), download_mbps=prof.download_speed_mbps, upload_mbps=prof.upload_speed_mbps
            )
            if cna.vlan:
                try:
                    olt.provision_vlan(onu_id=str(contract_id), vlan_id=cna.vlan.vlan_id)
                except Exception:
                    pass
        elif dev.type == "bras":
            # Use specific credentials if available, otherwise fallback to contract_id
            u_user = cna.pppoe_user if cna.pppoe_user else str(contract_id)
            u_pass = cna.pppoe_password if cna.pppoe_password else str(contract_id)
            
            RadiusClient(db).create_or_update_user(
                username=u_user,
                password=u_pass,
                download_mbps=prof.download_speed_mbps,
                upload_mbps=prof.upload_speed_mbps,
                burst_enabled=prof.burst_enabled,
                burst_rate_percent=prof.burst_rate_percent,
                burst_threshold_seconds=prof.burst_threshold_seconds,
                ip_address=cna.static_ip,
            )
    cna.last_provisioned_at = datetime.utcnow()
    db.add(cna)
    db.commit()
    db.refresh(cna)
    _write_history(db, contract_id, "provision", "Provisionamento realizado")
    return cna


def block_contract(db: Session, contract_id: int) -> ContractNetworkAssignment:
    cna = db.query(ContractNetworkAssignment).filter(ContractNetworkAssignment.contract_id == contract_id).first()
    if not cna:
        raise ValueError("Assignment not found")
    dev = cna.device
    if dev:
        client = _vendor_clients(dev)
        if dev.vendor == "mikrotik":
            MikrotikClient(dev.host, dev.port, dev.username, dev.password).block_client(str(contract_id))
            _write_history(db, contract_id, "block", "Mikrotik: cliente bloqueado")
        elif dev.vendor in ("huawei", "zte", "vsol"):
            try:
                if dev.vendor == "vsol":
                    olt = VSOLClient(dev.host, dev.username, dev.password)
                else:
                    olt = OLTClient(dev.host, dev.username, dev.password, vendor=dev.vendor)
                olt.remove_service_profile(onu_id=str(contract_id))
                if cna.vlan:
                    try:
                        olt.unbind_vlan(onu_id=str(contract_id), vlan_id=cna.vlan.vlan_id)
                    except Exception:
                        pass
                _write_history(db, contract_id, "block", f"OLT {dev.vendor}: perfil removido")
            except Exception:
                pass
        elif dev.type == "bras":
            RadiusClient(db).block_user(str(contract_id))
    cna.status = "blocked"
    db.add(cna)
    db.commit()
    db.refresh(cna)
    _write_history(db, contract_id, "block", "Contrato bloqueado")
    return cna


def get_onu_status(db: Session, device_id: int, onu_id: str) -> dict:
    dev = db.query(NetworkDevice).filter(NetworkDevice.id == device_id).first()
    if not dev:
        raise ValueError("Device not found")
    if dev.vendor not in ("huawei", "zte", "vsol"):
        raise ValueError("Device is not an OLT")
    
    if dev.vendor == "vsol":
        olt = VSOLClient(dev.host, dev.username, dev.password)
    else:
        olt = OLTClient(dev.host, dev.username, dev.password, vendor=dev.vendor)
        
    status = olt.onu_status(onu_id=str(onu_id))
    _write_history(db, int(onu_id), "onu_status", f"OLT {dev.vendor}: status consultado")
    return status


def unbind_vlan_for_contract(db: Session, contract_id: int) -> ContractNetworkAssignment:
    cna = db.query(ContractNetworkAssignment).filter(ContractNetworkAssignment.contract_id == contract_id).first()
    if not cna:
        raise ValueError("Assignment not found")
    dev = cna.device
    if dev and cna.vlan and dev.vendor in ("huawei", "zte", "vsol"):
        try:
            if dev.vendor == "vsol":
                olt = VSOLClient(dev.host, dev.username, dev.password)
            else:
                olt = OLTClient(dev.host, dev.username, dev.password, vendor=dev.vendor)
            olt.unbind_vlan(onu_id=str(contract_id), vlan_id=cna.vlan.vlan_id)
            _write_history(db, contract_id, "unbind_vlan", f"OLT {dev.vendor}: VLAN {cna.vlan.vlan_id} desassociada")
        except Exception:
            pass
    db.refresh(cna)
    return cna


def unblock_contract(db: Session, contract_id: int) -> ContractNetworkAssignment:
    cna = db.query(ContractNetworkAssignment).filter(ContractNetworkAssignment.contract_id == contract_id).first()
    if not cna:
        raise ValueError("Assignment not found")
    dev = cna.device
    if dev:
        client = _vendor_clients(dev)
        if dev.vendor == "mikrotik":
            MikrotikClient(dev.host, dev.port, dev.username, dev.password).unblock_client(str(contract_id))
            _write_history(db, contract_id, "unblock", "Mikrotik: cliente desbloqueado")
        elif dev.vendor in ("huawei", "zte", "vsol"):
            try:
                if dev.vendor == "vsol":
                    olt = VSOLClient(dev.host, dev.username, dev.password)
                else:
                    olt = OLTClient(dev.host, dev.username, dev.password, vendor=dev.vendor)
                prof = cna.profile
                if prof:
                    olt.set_service_profile(onu_id=str(contract_id), download_mbps=prof.download_speed_mbps, upload_mbps=prof.upload_speed_mbps)
                if cna.vlan:
                    olt.bind_vlan(onu_id=str(contract_id), vlan_id=cna.vlan.vlan_id)
                _write_history(db, contract_id, "unblock", f"OLT {dev.vendor}: perfil/vlan aplicados")
            except Exception:
                pass
        elif dev.type == "bras":
            RadiusClient(db).unblock_user(str(contract_id))
    cna.status = "active"
    db.add(cna)
    db.commit()
    db.refresh(cna)
    _write_history(db, contract_id, "unblock", "Contrato desbloqueado")
    return cna


def sync_billing_blocking(db: Session, contract_id: int) -> ContractNetworkAssignment:
    from datetime import date as _date
    from sqlalchemy import or_, and_
    today = _date.today()
    overdue_count = (
        db.query(Title)
        .filter(Title.contract_id == contract_id)
        .filter(
            or_(
                Title.status == "overdue",
                and_(Title.status == "open", Title.due_date < today),
            )
        )
        .count()
    )
    if overdue_count > 0:
        return block_contract(db, contract_id)
    else:
        return unblock_contract(db, contract_id)


def _pool_ips(cidr: str) -> list[str]:
    net = ipaddress.ip_network(cidr, strict=False)
    ips = [str(ip) for ip in net.hosts()]
    return ips


def allocate_dynamic_ip(db: Session, pool_id: int, contract_id: int) -> IPLease:
    pool = db.query(IPPool).filter(IPPool.id == pool_id).first()
    if not pool:
        raise ValueError("Pool not found")
    used = {l.ip_address for l in db.query(IPLease).filter(IPLease.pool_id == pool_id, IPLease.status == "allocated").all()}
    for ip in _pool_ips(pool.cidr):
        if ip in used:
            continue
        lease = IPLease(pool_id=pool_id, contract_id=contract_id, ip_address=ip, allocated_at=datetime.utcnow(), status="allocated")
        db.add(lease)
        db.commit()
        db.refresh(lease)
        _write_history(db, contract_id, "ip_allocate", f"IP {ip} alocado do pool {pool.name}")
        return lease
    raise ValueError("No available IPs in pool")


def release_ip_for_contract(db: Session, contract_id: int) -> IPLease | None:
    lease = db.query(IPLease).filter(IPLease.contract_id == contract_id, IPLease.status == "allocated").first()
    if not lease:
        return None
    lease.status = "released"
    lease.released_at = datetime.utcnow()
    db.add(lease)
    db.commit()
    _write_history(db, contract_id, "ip_release", f"IP {lease.ip_address} liberado")
    return lease


def get_radius_active_session(db: Session, username: str) -> RadiusSessionOut | None:
    session = (
        db.query(RadAcct)
        .filter(RadAcct.username == username, RadAcct.acctstoptime.is_(None))
        .order_by(RadAcct.acctstarttime.desc())
        .first()
    )
    if not session:
        return None
    
    return RadiusSessionOut(
        username=session.username,
        ip_address=session.framedipaddress or "0.0.0.0",
        start_time=session.acctstarttime or datetime.utcnow(),
        input_mb=round((session.acctinputoctets or 0) / 1024 / 1024, 2),
        output_mb=round((session.acctoutputoctets or 0) / 1024 / 1024, 2),
        status="online"
    )


def get_radius_usage_history(db: Session, username: str, limit: int = 20) -> list[RadiusUsageHistory]:
    sessions = (
        db.query(RadAcct)
        .filter(RadAcct.username == username)
        .order_by(RadAcct.acctstarttime.desc())
        .limit(limit)
        .all()
    )
    
    result = []
    for s in sessions:
        duration = s.acctsessiontime
        if not duration and s.acctstoptime and s.acctstarttime:
            duration = int((s.acctstoptime - s.acctstarttime).total_seconds())
            
        result.append(RadiusUsageHistory(
            session_id=s.acctsessionid,
            start_time=s.acctstarttime or datetime.utcnow(),
            stop_time=s.acctstoptime,
            duration_seconds=duration,
            input_mb=round((s.acctinputoctets or 0) / 1024 / 1024, 2),
            output_mb=round((s.acctoutputoctets or 0) / 1024 / 1024, 2),
            termination_cause=s.acctterminatecause
        ))
    return result
