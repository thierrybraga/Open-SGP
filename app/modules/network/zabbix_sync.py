
"""
Arquivo: app/modules/network/zabbix_sync.py

Responsabilidade:
Lógica de negócio para sincronização de dispositivos com Zabbix.
"""
import logging
from sqlalchemy.orm import Session
from .models import NetworkDevice
from .vendors.zabbix import ZabbixClient
from ..administration.setup.models import SetupProgress

logger = logging.getLogger(__name__)


DEFAULT_TEMPLATE_MAP = {
    "mikrotik": ["Template Net Mikrotik SNMP"],
    "huawei": ["Template Net Huawei GPON SNMP"],
    "zte": ["Template Net ZTE GPON SNMP"],
    "vsol": ["Template Net VSOL GPON SNMP"],
    "router": ["Template Module ICMP Ping"],
    "switch": ["Template Module ICMP Ping"],
    "olt": ["Template Module ICMP Ping"],
    "bras": ["Template Module ICMP Ping"],
}


def get_zabbix_client(db: Session) -> ZabbixClient | None:
    """
    Obtém cliente Zabbix configurado no setup.
    """
    progress = db.query(SetupProgress).first()
    if not progress or not progress.monitoring_configured:
        return None
        
    config = progress.get_config_data().get('monitoring', {})
    if not config or not config.get('enable_monitoring'):
        return None
        
    try:
        return ZabbixClient(
            url=config.get('url'),
            user=config.get('user'),
            password=config.get('password')
        )
    except Exception as e:
        logger.error(f"Failed to initialize Zabbix Client: {e}")
        return None

def sync_device_to_zabbix(db: Session, device_id: int):
    """
    Sincroniza um dispositivo de rede com o Zabbix.
    Se zabbix_monitored=True, cria ou atualiza o host no Zabbix.
    """
    device = db.query(NetworkDevice).filter(NetworkDevice.id == device_id).first()
    if not device:
        return
        
    if not device.zabbix_monitored:
        return

    client = get_zabbix_client(db)
    if not client:
        logger.warning("Zabbix sync skipped: Not configured")
        return

    try:
        # Checagem rápida de disponibilidade
        client.get_version()
        client.login()
        
        # 1. Garantir grupo
        group_name = "ISP Devices"
        group_id = client.create_host_group(group_name)
        
        # 2. Definir templates baseados no vendor
        template_names = _template_names_for_device(config, device)
        templates = client.get_template_ids_by_names(template_names)
        
        # 3. Criar/Atualizar Host
        host_id = client.create_host(
            host_name=device.name,
            ip=device.host,
            group_id=group_id,
            template_ids=templates
        )
        
        # 4. Salvar ID no banco
        device.zabbix_host_id = host_id
        db.add(device)
        db.commit()
        
        logger.info(f"Device {device.name} synced to Zabbix (ID: {host_id})")
        
    except Exception as e:
        logger.error(f"Failed to sync device {device.name} to Zabbix: {e}")


def _template_names_for_device(config: dict, device: NetworkDevice) -> list[str]:
    configured_map = config.get("template_map") or {}
    vendor = (device.vendor or "").lower()
    device_type = (device.type or "").lower()
    names = configured_map.get(vendor) or configured_map.get(device_type)
    if isinstance(names, str):
        return [names]
    if isinstance(names, list):
        return [str(name) for name in names if name]
    return DEFAULT_TEMPLATE_MAP.get(vendor) or DEFAULT_TEMPLATE_MAP.get(device_type) or []
