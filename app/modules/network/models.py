"""
Arquivo: app/modules/network/models.py

Responsabilidade:
Modelos de dispositivos de rede, pools de IP, VLANs, perfis de serviço,
atribuições de contrato e histórico técnico.

Integrações:
- modules.contracts.models
- core.database
- shared.models
"""

from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin


class NetworkDevice(Base, TimestampMixin):
    __tablename__ = "network_devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(20))  # router, olt, switch, bras
    vendor: Mapped[str] = mapped_column(String(20))  # mikrotik, huawei, zte, generic
    host: Mapped[str] = mapped_column(String(100))
    port: Mapped[int] = mapped_column(Integer, default=8728)
    username: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String(200))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Zabbix Integration
    zabbix_monitored: Mapped[bool] = mapped_column(Boolean, default=False)
    zabbix_host_id: Mapped[str | None] = mapped_column(String(20), nullable=True)


class VLAN(Base, TimestampMixin):
    __tablename__ = "vlans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("network_devices.id", ondelete="CASCADE"), index=True)
    vlan_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(100))
    purpose: Mapped[str] = mapped_column(String(50))  # clients, mgmt, backbone

    device = relationship("NetworkDevice")


class IPPool(Base, TimestampMixin):
    __tablename__ = "ip_pools"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    cidr: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(20))  # dynamic, static, cgnat
    gateway: Mapped[str] = mapped_column(String(50))
    dns_primary: Mapped[str] = mapped_column(String(50))
    dns_secondary: Mapped[str] = mapped_column(String(50))
    device_id: Mapped[int | None] = mapped_column(ForeignKey("network_devices.id", ondelete="SET NULL"), nullable=True)
    vlan_id: Mapped[int | None] = mapped_column(ForeignKey("vlans.id", ondelete="SET NULL"), nullable=True)

    device = relationship("NetworkDevice")
    vlan = relationship("VLAN")


class IPLease(Base, TimestampMixin):
    __tablename__ = "ip_leases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("ip_pools.id", ondelete="CASCADE"), index=True)
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True, index=True)
    ip_address: Mapped[str] = mapped_column(String(50), index=True)
    allocated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True, default="allocated")

    pool = relationship("IPPool")


class ServiceProfile(Base, TimestampMixin):
    __tablename__ = "service_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    download_speed_mbps: Mapped[float] = mapped_column(Float, default=0.0)
    upload_speed_mbps: Mapped[float] = mapped_column(Float, default=0.0)
    burst_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    burst_rate_percent: Mapped[float] = mapped_column(Float, default=0.0)
    burst_threshold_seconds: Mapped[int] = mapped_column(Integer, default=0)


class ContractNetworkAssignment(Base, TimestampMixin):
    __tablename__ = "contract_network_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("network_devices.id", ondelete="SET NULL"), nullable=True)
    ip_pool_id: Mapped[int | None] = mapped_column(ForeignKey("ip_pools.id", ondelete="SET NULL"), nullable=True)
    vlan_id: Mapped[int | None] = mapped_column(ForeignKey("vlans.id", ondelete="SET NULL"), nullable=True)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("service_profiles.id", ondelete="SET NULL"), nullable=True)
    pppoe_user: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    pppoe_password: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String(17), nullable=True)
    wifi_ssid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    wifi_password: Mapped[str | None] = mapped_column(String(64), nullable=True)
    static_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cgnat: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), index=True, default="active")  # active, blocked
    last_provisioned_at: Mapped[datetime | None] = mapped_column(nullable=True)

    device = relationship("NetworkDevice")
    ip_pool = relationship("IPPool")
    vlan = relationship("VLAN")
    profile = relationship("ServiceProfile")

    __table_args__ = ()


class ContractTechHistory(Base, TimestampMixin):
    __tablename__ = "contract_tech_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"), index=True)
    technician: Mapped[str] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(50))  # provision, block, unblock, change
    description: Mapped[str] = mapped_column(String(500))
    occurred_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# ===== RADIUS MODELS (FreeRADIUS Standard Schema) =====

class RadCheck(Base):
    __tablename__ = "radcheck"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    attribute: Mapped[str] = mapped_column(String(64), nullable=False)
    op: Mapped[str] = mapped_column(String(2), nullable=False, default=":=")
    value: Mapped[str] = mapped_column(String(253), nullable=False)


class RadReply(Base):
    __tablename__ = "radreply"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    attribute: Mapped[str] = mapped_column(String(64), nullable=False)
    op: Mapped[str] = mapped_column(String(2), nullable=False, default="=")
    value: Mapped[str] = mapped_column(String(253), nullable=False)


class RadUserGroup(Base):
    __tablename__ = "radusergroup"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    groupname: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1)


class RadGroupReply(Base):
    __tablename__ = "radgroupreply"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    groupname: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    attribute: Mapped[str] = mapped_column(String(64), nullable=False)
    op: Mapped[str] = mapped_column(String(2), nullable=False, default="=")
    value: Mapped[str] = mapped_column(String(253), nullable=False)


class RadGroupCheck(Base):
    __tablename__ = "radgroupcheck"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    groupname: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    attribute: Mapped[str] = mapped_column(String(64), nullable=False)
    op: Mapped[str] = mapped_column(String(2), nullable=False, default=":=")
    value: Mapped[str] = mapped_column(String(253), nullable=False)


class RadAcct(Base):
    __tablename__ = "radacct"

    radacctid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    acctsessionid: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    acctuniqueid: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    groupname: Mapped[str] = mapped_column(String(64), nullable=True)
    realm: Mapped[str] = mapped_column(String(64), nullable=True)
    nasipaddress: Mapped[str] = mapped_column(String(15), index=True, nullable=False)
    nasportid: Mapped[str] = mapped_column(String(15), nullable=True)
    nasporttype: Mapped[str] = mapped_column(String(32), nullable=True)
    acctstarttime: Mapped[datetime | None] = mapped_column(index=True)
    acctupdatetime: Mapped[datetime | None] = mapped_column()
    acctstoptime: Mapped[datetime | None] = mapped_column(index=True)
    acctinterval: Mapped[int | None] = mapped_column()
    acctsessiontime: Mapped[int | None] = mapped_column()
    acctauthentic: Mapped[str | None] = mapped_column(String(32))
    connectinfo_start: Mapped[str | None] = mapped_column(String(50))
    connectinfo_stop: Mapped[str | None] = mapped_column(String(50))
    acctinputoctets: Mapped[int | None] = mapped_column()
    acctoutputoctets: Mapped[int | None] = mapped_column()
    calledstationid: Mapped[str] = mapped_column(String(50), nullable=True)
    callingstationid: Mapped[str] = mapped_column(String(50), nullable=True)
    acctterminatecause: Mapped[str] = mapped_column(String(32), nullable=True)
    servicetype: Mapped[str] = mapped_column(String(32), nullable=True)
    framedprotocol: Mapped[str] = mapped_column(String(32), nullable=True)
    framedipaddress: Mapped[str] = mapped_column(String(15), nullable=True)


class RadIPPool(Base):
    __tablename__ = "radippool"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pool_name: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    framedipaddress: Mapped[str] = mapped_column(String(15), index=True, nullable=False)
    nasipaddress: Mapped[str] = mapped_column(String(15), index=True, nullable=False, default="")
    calledstationid: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    callingstationid: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    expiry_time: Mapped[datetime | None] = mapped_column(nullable=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    pool_key: Mapped[str] = mapped_column(String(30), nullable=False, default="")
