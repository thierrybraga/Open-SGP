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
from collections.abc import Iterable
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
    RadIPPool,
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
    values = data.dict()
    values["cidr"] = _normalize_pool_cidr(values["cidr"])
    _validate_pool_settings(
        cidr=values["cidr"],
        pool_type=values["type"],
        gateway=values["gateway"],
        dns_primary=values["dns_primary"],
        dns_secondary=values["dns_secondary"],
    )
    pool = IPPool(**values)
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


def plan_profile_name(plan_id: int) -> str:
    return f"plan:{plan_id}"


def sync_service_profile_for_plan(db: Session, plan) -> ServiceProfile:
    """
    Keep the technical shaper profile aligned with the commercial plan.
    """
    profile = db.query(ServiceProfile).filter(ServiceProfile.name == plan_profile_name(plan.id)).first()
    if not profile:
        profile = ServiceProfile(name=plan_profile_name(plan.id))
        db.add(profile)

    profile.download_speed_mbps = plan.download_speed_mbps
    profile.upload_speed_mbps = plan.upload_speed_mbps
    profile.burst_enabled = plan.burst_enabled
    profile.burst_rate_percent = plan.burst_rate_percent
    profile.burst_threshold_seconds = plan.burst_threshold_seconds
    db.commit()
    db.refresh(profile)

    RadiusClient(db).create_plan_template(
        profile.name,
        download_mbps=profile.download_speed_mbps,
        upload_mbps=profile.upload_speed_mbps,
    )
    return profile


def create_assignment(db: Session, data: AssignmentCreate) -> ContractNetworkAssignment:
    values = data.dict()
    contract = db.query(Contract).filter(Contract.id == data.contract_id).first()
    if not contract:
        raise ValueError("Contract not found")

    if not values.get("profile_id") and contract.plan:
        profile = sync_service_profile_for_plan(db, contract.plan)
        values["profile_id"] = profile.id

    cna = ContractNetworkAssignment(**values)
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
        return OLTClient(device.host, device.username, device.password, vendor=device.vendor, port=device.port or 23)
    if device.vendor == "vsol":
        return VSOLClient(device.host, device.username, device.password, port=device.port or 23)
    return None


def _radius_credentials_for_assignment(cna: ContractNetworkAssignment) -> tuple[str, str]:
    username = cna.pppoe_user or str(cna.contract_id)
    password = cna.pppoe_password or str(cna.contract_id)
    return username, password


def sync_radius_auth_for_assignment(
    db: Session,
    cna: ContractNetworkAssignment,
    profile: ServiceProfile | None = None,
    plan_group_name: str | None = None,
) -> None:
    """
    Keep PPPoE/RADIUS authentication aligned with the contract assignment.

    The access device can be an OLT, Mikrotik or BRAS, but authentication is
    centralized in FreeRADIUS. This makes provisioning deterministic instead of
    only creating RADIUS users when the selected network device is typed as BRAS.
    """
    prof = profile or cna.profile
    if not prof:
        return
    username, password = _radius_credentials_for_assignment(cna)
    RadiusClient(db).create_or_update_user(
        username=username,
        password=password,
        plan_group_name=plan_group_name or prof.name,
        download_mbps=prof.download_speed_mbps,
        upload_mbps=prof.upload_speed_mbps,
        burst_enabled=prof.burst_enabled,
        burst_rate_percent=prof.burst_rate_percent,
        burst_threshold_seconds=prof.burst_threshold_seconds,
        ip_address=cna.static_ip,
    )


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
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not prof and contract and contract.plan:
        prof = sync_service_profile_for_plan(db, contract.plan)
        cna.profile_id = prof.id
        cna.profile = prof
    # Dynamic IP allocation
    if cna.ip_pool and cna.ip_pool.type == "dynamic" and not cna.static_ip:
        lease = db.query(IPLease).filter(IPLease.contract_id == contract_id, IPLease.status == "allocated").first()
        if not lease:
            lease = allocate_dynamic_ip(db, cna.ip_pool.id, contract_id)
        if lease:
            cna.static_ip = lease.ip_address
    if prof:
        sync_radius_auth_for_assignment(db, cna, prof, plan_group_name=prof.name)

    if dev and prof:
        if dev.vendor == "mikrotik":
            mk = MikrotikClient(dev.host, dev.port, dev.username, dev.password)
            mk.provision_simple_queue(
                name=str(contract_id),
                max_down_mbps=prof.download_speed_mbps,
                max_up_mbps=prof.upload_speed_mbps,
                target_ip=cna.static_ip,
            )
            if cna.static_ip:
                mk.set_static_ip(name=str(contract_id), ip=cna.static_ip)
            if cna.cgnat:
                mk.enable_cgnat(name=str(contract_id))
        elif dev.vendor in ("huawei", "zte", "vsol"):
            if dev.vendor == "vsol":
                olt = VSOLClient(dev.host, dev.username, dev.password, port=dev.port or 23)
            else:
                olt = OLTClient(dev.host, dev.username, dev.password, vendor=dev.vendor, port=dev.port or 23)
            olt.set_service_profile(
                onu_id=str(contract_id), download_mbps=prof.download_speed_mbps, upload_mbps=prof.upload_speed_mbps
            )
            if cna.vlan:
                olt.provision_vlan(onu_id=str(contract_id), vlan_id=cna.vlan.vlan_id)
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
    username, _password = _radius_credentials_for_assignment(cna)
    RadiusClient(db).block_user(username)
    if dev:
        client = _vendor_clients(dev)
        if dev.vendor == "mikrotik":
            MikrotikClient(dev.host, dev.port, dev.username, dev.password).block_client(str(contract_id))
            _write_history(db, contract_id, "block", "Mikrotik: cliente bloqueado")
        elif dev.vendor in ("huawei", "zte", "vsol"):
            if dev.vendor == "vsol":
                olt = VSOLClient(dev.host, dev.username, dev.password, port=dev.port or 23)
            else:
                olt = OLTClient(dev.host, dev.username, dev.password, vendor=dev.vendor, port=dev.port or 23)
            olt.remove_service_profile(onu_id=str(contract_id))
            if cna.vlan:
                olt.unbind_vlan(onu_id=str(contract_id), vlan_id=cna.vlan.vlan_id)
            _write_history(db, contract_id, "block", f"OLT {dev.vendor}: perfil removido")
    cna.status = "blocked"
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract and contract.status != "canceled":
        contract.status = "suspended"
        db.add(contract)
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
        olt = VSOLClient(dev.host, dev.username, dev.password, port=dev.port or 23)
    else:
        olt = OLTClient(dev.host, dev.username, dev.password, vendor=dev.vendor, port=dev.port or 23)
        
    onu = olt.onu_status(onu_id=str(onu_id))
    if str(onu_id).isdigit():
        _write_history(db, int(onu_id), "onu_status", f"OLT {dev.vendor}: status consultado")
    return onu


def unbind_vlan_for_contract(db: Session, contract_id: int) -> ContractNetworkAssignment:
    cna = db.query(ContractNetworkAssignment).filter(ContractNetworkAssignment.contract_id == contract_id).first()
    if not cna:
        raise ValueError("Assignment not found")
    dev = cna.device
    if dev and cna.vlan and dev.vendor in ("huawei", "zte", "vsol"):
        if dev.vendor == "vsol":
            olt = VSOLClient(dev.host, dev.username, dev.password, port=dev.port or 23)
        else:
            olt = OLTClient(dev.host, dev.username, dev.password, vendor=dev.vendor, port=dev.port or 23)
        olt.unbind_vlan(onu_id=str(contract_id), vlan_id=cna.vlan.vlan_id)
        _write_history(db, contract_id, "unbind_vlan", f"OLT {dev.vendor}: VLAN {cna.vlan.vlan_id} desassociada")
    db.refresh(cna)
    return cna


def unblock_contract(db: Session, contract_id: int) -> ContractNetworkAssignment:
    cna = db.query(ContractNetworkAssignment).filter(ContractNetworkAssignment.contract_id == contract_id).first()
    if not cna:
        raise ValueError("Assignment not found")
    dev = cna.device
    username, _password = _radius_credentials_for_assignment(cna)
    RadiusClient(db).unblock_user(username)
    if cna.profile:
        sync_radius_auth_for_assignment(db, cna, cna.profile)
    if dev:
        client = _vendor_clients(dev)
        if dev.vendor == "mikrotik":
            MikrotikClient(dev.host, dev.port, dev.username, dev.password).unblock_client(str(contract_id))
            _write_history(db, contract_id, "unblock", "Mikrotik: cliente desbloqueado")
        elif dev.vendor in ("huawei", "zte", "vsol"):
            if dev.vendor == "vsol":
                olt = VSOLClient(dev.host, dev.username, dev.password, port=dev.port or 23)
            else:
                olt = OLTClient(dev.host, dev.username, dev.password, vendor=dev.vendor, port=dev.port or 23)
            prof = cna.profile
            if prof:
                olt.set_service_profile(onu_id=str(contract_id), download_mbps=prof.download_speed_mbps, upload_mbps=prof.upload_speed_mbps)
            if cna.vlan:
                olt.bind_vlan(onu_id=str(contract_id), vlan_id=cna.vlan.vlan_id)
            _write_history(db, contract_id, "unblock", f"OLT {dev.vendor}: perfil/vlan aplicados")
    cna.status = "active"
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract and contract.status == "suspended":
        contract.status = "active"
        db.add(contract)
    db.add(cna)
    db.commit()
    db.refresh(cna)
    _write_history(db, contract_id, "unblock", "Contrato desbloqueado")
    return cna


def sync_billing_blocking(db: Session, contract_id: int) -> ContractNetworkAssignment:
    from datetime import date as _date
    from sqlalchemy import or_, and_
    today = _date.today()
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract and not contract.suspend_on_arrears:
        return unblock_contract(db, contract_id)
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


def _normalize_pool_cidr(cidr: str) -> str:
    try:
        net = ipaddress.ip_network((cidr or "").strip(), strict=False)
    except ValueError as exc:
        raise ValueError("Invalid pool CIDR") from exc
    if net.version != 4:
        raise ValueError("Only IPv4 pools are supported")
    if next(net.hosts(), None) is None:
        raise ValueError("Pool CIDR has no usable host addresses")
    return str(net)


def _validate_ip(value: str, field_name: str) -> ipaddress.IPv4Address:
    try:
        ip = ipaddress.ip_address((value or "").strip())
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name}") from exc
    if ip.version != 4:
        raise ValueError(f"{field_name} must be IPv4")
    return ip


def _validate_pool_settings(
    cidr: str,
    pool_type: str,
    gateway: str,
    dns_primary: str,
    dns_secondary: str,
) -> None:
    if pool_type not in {"dynamic", "static", "cgnat"}:
        raise ValueError("Invalid pool type")
    net = ipaddress.ip_network(cidr, strict=False)
    gateway_ip = _validate_ip(gateway, "gateway")
    if gateway_ip not in net:
        raise ValueError("Gateway must belong to the pool CIDR")
    _validate_ip(dns_primary, "primary DNS")
    _validate_ip(dns_secondary, "secondary DNS")


def _pool_ips(cidr: str) -> Iterable[str]:
    net = ipaddress.ip_network(cidr, strict=False)
    return (str(ip) for ip in net.hosts())


def _radius_pool_name(pool: IPPool) -> str:
    return f"sgp_pool_{pool.id}"


def _reserve_radius_pool_ip(db: Session, pool: IPPool, lease: IPLease) -> None:
    item = db.query(RadIPPool).filter(RadIPPool.framedipaddress == lease.ip_address).first()
    if not item:
        item = RadIPPool(framedipaddress=lease.ip_address)
        db.add(item)
    item.pool_name = _radius_pool_name(pool)
    item.nasipaddress = pool.device.host if pool.device else ""
    item.calledstationid = ""
    item.callingstationid = ""
    item.expiry_time = None
    item.username = str(lease.contract_id or "")
    item.pool_key = f"lease:{lease.id}"


def _release_radius_pool_ip(db: Session, lease: IPLease) -> None:
    item = db.query(RadIPPool).filter(RadIPPool.framedipaddress == lease.ip_address).first()
    if item:
        item.username = ""
        item.pool_key = ""
        item.expiry_time = datetime.utcnow()
        db.add(item)


def allocate_dynamic_ip(db: Session, pool_id: int, contract_id: int) -> IPLease:
    pool = db.query(IPPool).filter(IPPool.id == pool_id).first()
    if not pool:
        raise ValueError("Pool not found")
    if pool.type != "dynamic":
        raise ValueError("IP allocation requires a dynamic pool")
    active_lease = db.query(IPLease).filter(IPLease.contract_id == contract_id, IPLease.status == "allocated").first()
    if active_lease:
        return active_lease
    used = {l.ip_address for l in db.query(IPLease).filter(IPLease.pool_id == pool_id, IPLease.status == "allocated").all()}
    for ip in _pool_ips(pool.cidr):
        if ip in used:
            continue
        lease = IPLease(pool_id=pool_id, contract_id=contract_id, ip_address=ip, allocated_at=datetime.utcnow(), status="allocated")
        db.add(lease)
        db.flush()
        _reserve_radius_pool_ip(db, pool, lease)
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
    _release_radius_pool_ip(db, lease)
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
