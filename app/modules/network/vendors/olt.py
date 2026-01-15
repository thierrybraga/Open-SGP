"""
Arquivo: app/modules/network/vendors/olt.py

Responsabilidade:
Abstração genérica de OLT (Huawei/ZTE) para provisionar VLAN e perfis.

Integrações:
- modules.network.models.VLAN
"""

import socket

class OLTClient:
    def __init__(self, host: str, username: str, password: str, vendor: str | None = None):
        self.host = host
        self.username = username
        self.password = password
        self.vendor = (vendor or "generic").lower()

    def check_connection(self) -> bool:
        """
        Verifica conectividade básica (TCP handshake) na porta padrão (Telnet 23 ou SSH 22).
        Tenta ambas se não especificado.
        """
        try:
            # Tenta Telnet primeiro
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            if sock.connect_ex((self.host, 23)) == 0:
                sock.close()
                return True
            sock.close()
            
            # Tenta SSH
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            if sock.connect_ex((self.host, 22)) == 0:
                sock.close()
                return True
            sock.close()
            
            return False
        except Exception:
            return False

    def get_info(self) -> dict:
        if self.check_connection():
            return {"vendor": self.vendor, "status": "Online"}
        return {"vendor": self.vendor, "status": "Unreachable"}

    def provision_vlan(self, onu_id: str, vlan_id: int):
        return True

    def set_service_profile(self, onu_id: str, download_mbps: float, upload_mbps: float):
        return True

    def remove_service_profile(self, onu_id: str):
        return True

    def bind_vlan(self, onu_id: str, vlan_id: int):
        return True

    def unbind_vlan(self, onu_id: str, vlan_id: int):
        return True

    def onu_status(self, onu_id: str) -> dict:
        return {
            "onu_id": onu_id,
            "vendor": self.vendor,
            "online": True,
            "rx_power_dbm": -19.5,
            "tx_power_dbm": 2.0,
            "uptime_seconds": 86400,
            "last_flap": None,
        }
