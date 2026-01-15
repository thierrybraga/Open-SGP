"""
Arquivo: app/modules/network/vendors/zabbix.py

Responsabilidade:
Integração com API do Zabbix para monitoramento de dispositivos.
"""
import requests
import json
import logging

logger = logging.getLogger(__name__)

class ZabbixClient:
    def __init__(self, url: str, user: str, password: str):
        self.url = url.rstrip('/') + '/api_jsonrpc.php'
        self.user = user
        self.password = password
        self.auth_token = None
        self.headers = {'Content-Type': 'application/json-rpc'}
        self.req_id = 1

    def _request(self, method: str, params: dict = None):
        if params is None:
            params = {}
            
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.req_id,
            "auth": self.auth_token
        }
        self.req_id += 1
        
        try:
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                raise Exception(f"Zabbix API Error: {result['error'].get('data')} ({result['error'].get('message')})")
                
            return result.get('result')
        except Exception as e:
            logger.error(f"Zabbix request failed: {str(e)}")
            raise

    def login(self):
        """Autentica no Zabbix e obtém token."""
        try:
            # Para Zabbix 6.x+, 'user.login' retorna o token diretamente
            # Payload específico para login (sem auth token)
            payload = {
                "jsonrpc": "2.0",
                "method": "user.login",
                "params": {
                    "user": self.user,
                    "password": self.password
                },
                "id": self.req_id
            }
            self.req_id += 1
            
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                raise Exception(f"Login failed: {result['error'].get('data')}")
                
            self.auth_token = result.get('result')
            return True
        except Exception as e:
            logger.error(f"Zabbix login failed: {str(e)}")
            raise

    def get_version(self) -> str:
        """Obtém versão da API do Zabbix (sem autenticação)."""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "apiinfo.version",
                "params": {},
                "id": self.req_id
            }
            self.req_id += 1
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=5)
            response.raise_for_status()
            result = response.json()
            if 'error' in result:
                raise Exception(f"Zabbix API Error: {result['error'].get('data')}")
            return result.get('result')
        except Exception as e:
            logger.error(f"Zabbix version check failed: {str(e)}")
            raise

    def get_host_group_id(self, name: str) -> str:
        """Busca ID de um grupo de hosts pelo nome."""
        result = self._request("hostgroup.get", {
            "filter": {"name": [name]},
            "output": ["groupid"]
        })
        if result:
            return result[0]['groupid']
        return None

    def create_host_group(self, name: str) -> str:
        """Cria um grupo de hosts."""
        group_id = self.get_host_group_id(name)
        if group_id:
            return group_id
            
        result = self._request("hostgroup.create", {"name": name})
        return result['groupids'][0]

    def create_host(self, host_name: str, ip: str, group_id: str, template_ids: list = None):
        """Cria um host no Zabbix."""
        if not template_ids:
            template_ids = [] # IDs de templates (ex: Template ICMP Ping)

        # Verifica se host já existe
        existing = self._request("host.get", {
            "filter": {"host": [host_name]},
            "output": ["hostid"]
        })
        
        if existing:
            # Atualiza IP se necessário (simplificado)
            return existing[0]['hostid']

        params = {
            "host": host_name,
            "interfaces": [
                {
                    "type": 1, # Agent
                    "main": 1,
                    "useip": 1,
                    "ip": ip,
                    "dns": "",
                    "port": "10050"
                },
                {
                    "type": 2, # SNMP
                    "main": 1,
                    "useip": 1,
                    "ip": ip,
                    "dns": "",
                    "port": "161"
                }
            ],
            "groups": [{"groupid": group_id}],
            "templates": [{"templateid": tid} for tid in template_ids]
        }
        
        result = self._request("host.create", params)
        return result['hostids'][0]
