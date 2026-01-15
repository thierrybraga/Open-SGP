
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
        templates = []
        # TODO: Mapear templates IDs baseados no nome (ex: "Template Mikrotik")
        # Por enquanto, deixamos vazio ou fixo se soubermos os IDs
        
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
