"""
Arquivo: app/modules/network/vendors/mikrotik.py

Responsabilidade:
Cliente Mikrotik (RouterOS) usando routeros_api para provisionamento,
controle de banda e bloqueio.

Integrações:
- modules.network.models.NetworkDevice
"""

import routeros_api

class MikrotikClient:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.api = None

    def _connect(self):
        try:
            self.connection = routeros_api.RouterOsApiPool(
                self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                plaintext_login=True
            )
            self.api = self.connection.get_api()
            return True
        except Exception:
            return False

    def _disconnect(self):
        if self.connection:
            self.connection.disconnect()

    def check_connection(self) -> bool:
        if self._connect():
            self._disconnect()
            return True
        return False

    def get_identity(self) -> str:
        if not self._connect():
            return "Unknown"
        try:
            identity = self.api.get_resource('/system/identity').get()
            return identity[0].get('name', 'MikroTik') if identity else "MikroTik"
        except Exception:
            return "Unknown"
        finally:
            self._disconnect()

    def provision_simple_queue(self, name: str, max_down_mbps: float, max_up_mbps: float, target_ip: str = None):
        """
        Cria ou atualiza uma Simple Queue.
        max-limit format: upload/download
        """
        if not self._connect():
            return False
        try:
            up_str = f"{int(max_up_mbps)}M"
            down_str = f"{int(max_down_mbps)}M"
            max_limit = f"{up_str}/{down_str}"
            
            queues = self.api.get_resource('/queue/simple')
            existing = queues.get(name=name)
            
            params = {
                "name": name,
                "max-limit": max_limit
            }
            if target_ip:
                params["target"] = target_ip
            
            if existing:
                queues.set(id=existing[0]['id'], **params)
            else:
                if target_ip:
                    queues.add(**params)
            return True
        except Exception:
            return False
        finally:
            self._disconnect()

    def block_client(self, name: str):
        """
        Bloqueia cliente adicionando IP à address-list 'blocked'.
        O IP é recuperado da Simple Queue com o nome (contract_id).
        """
        if not self._connect():
            return False
        try:
            queues = self.api.get_resource('/queue/simple')
            existing = queues.get(name=name)
            if existing:
                target = existing[0].get('target')
                if target:
                     # target pode ser "192.168.1.10/32" ou apenas IP
                     ip = target.split('/')[0]
                     addr_list = self.api.get_resource('/ip/firewall/address-list')
                     if not addr_list.get(list="blocked", address=ip):
                         addr_list.add(list="blocked", address=ip, comment=f"Blocked Contract {name}")
            return True
        except Exception:
            return False
        finally:
            self._disconnect()

    def unblock_client(self, name: str):
        """
        Desbloqueia cliente removendo IP da address-list 'blocked'.
        """
        if not self._connect():
            return False
        try:
            queues = self.api.get_resource('/queue/simple')
            existing = queues.get(name=name)
            if existing:
                target = existing[0].get('target')
                if target:
                     ip = target.split('/')[0]
                     addr_list = self.api.get_resource('/ip/firewall/address-list')
                     blocked = addr_list.get(list="blocked", address=ip)
                     for b in blocked:
                         addr_list.remove(id=b['id'])
            return True
        except Exception:
            return False
        finally:
            self._disconnect()

    def set_static_ip(self, name: str, ip: str):
        """
        Atualiza o target da Simple Queue.
        """
        if not self._connect():
            return False
        try:
            queues = self.api.get_resource('/queue/simple')
            existing = queues.get(name=name)
            if existing:
                queues.set(id=existing[0]['id'], target=ip)
            return True
        except Exception:
            return False
        finally:
            self._disconnect()

    def enable_cgnat(self, name: str):
        """
        Adiciona cliente à address-list 'cgnat_users'.
        """
        if not self._connect():
            return False
        try:
            queues = self.api.get_resource('/queue/simple')
            existing = queues.get(name=name)
            if existing:
                target = existing[0].get('target')
                if target:
                     ip = target.split('/')[0]
                     addr_list = self.api.get_resource('/ip/firewall/address-list')
                     if not addr_list.get(list="cgnat_users", address=ip):
                         addr_list.add(list="cgnat_users", address=ip, comment=f"CGNAT Contract {name}")
            return True
        except Exception:
            return False
        finally:
            self._disconnect()
