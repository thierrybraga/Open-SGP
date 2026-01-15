"""
Arquivo: app/modules/network/schemas.py

Responsabilidade:
Esquemas Pydantic para dispositivos, pools, VLANs, perfis e atribuições.

Integrações:
- modules.network.models
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DeviceCreate(BaseModel):
    name: str
    type: str
    vendor: str
    host: str
    port: int = 8728
    username: str
    password: str
    enabled: bool = True
    zabbix_monitored: bool = False

class DeviceOut(BaseModel):
    id: int
    name: str
    type: str
    vendor: str
    host: str
    port: int
    enabled: bool
    zabbix_monitored: bool
    zabbix_host_id: Optional[str] = None

    class Config:
        from_attributes = True


class VLANCreate(BaseModel):
    device_id: int
    vlan_id: int
    name: str
    purpose: str


class VLANOut(BaseModel):
    id: int
    device_id: int
    vlan_id: int
    name: str
    purpose: str

    class Config:
        from_attributes = True


class IPPoolCreate(BaseModel):
    name: str
    cidr: str
    type: str
    gateway: str
    dns_primary: str
    dns_secondary: str
    device_id: Optional[int] = None
    vlan_id: Optional[int] = None


class IPPoolOut(BaseModel):
    id: int
    name: str
    cidr: str
    type: str
    gateway: str
    dns_primary: str
    dns_secondary: str
    device_id: Optional[int]
    vlan_id: Optional[int]

    class Config:
        from_attributes = True


class ServiceProfileCreate(BaseModel):
    name: str
    download_speed_mbps: float
    upload_speed_mbps: float
    burst_enabled: bool = False
    burst_rate_percent: float = 0.0
    burst_threshold_seconds: int = 0


class ServiceProfileOut(BaseModel):
    id: int
    name: str
    download_speed_mbps: float
    upload_speed_mbps: float
    burst_enabled: bool
    burst_rate_percent: float
    burst_threshold_seconds: int

    class Config:
        from_attributes = True


class AssignmentCreate(BaseModel):
    contract_id: int
    device_id: Optional[int] = None
    ip_pool_id: Optional[int] = None
    vlan_id: Optional[int] = None
    profile_id: Optional[int] = None
    static_ip: Optional[str] = None
    cgnat: bool = False


class AssignmentOut(BaseModel):
    id: int
    contract_id: int
    device_id: Optional[int]
    ip_pool_id: Optional[int]
    vlan_id: Optional[int]
    profile_id: Optional[int]
    static_ip: Optional[str]
    cgnat: bool
    status: str
    last_provisioned_at: Optional[datetime]

    class Config:
        from_attributes = True


class RadiusSessionOut(BaseModel):
    username: str
    ip_address: str
    start_time: datetime
    input_mb: float
    output_mb: float
    status: str


class RadiusUsageHistory(BaseModel):
    session_id: str
    start_time: datetime
    stop_time: Optional[datetime]
    duration_seconds: Optional[int]
    input_mb: float
    output_mb: float
    termination_cause: Optional[str]

