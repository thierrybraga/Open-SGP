"""
Arquivo: app/modules/network/vendors/zabbix.py

Responsabilidade:
Integração com API do Zabbix para monitoramento de dispositivos.
"""
import requests
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

    def get_template_ids_by_names(self, names: list[str]) -> list[str]:
        """Resolve template names to Zabbix template IDs."""
        if not names:
            return []
        result = self._request("template.get", {
            "filter": {"host": names},
            "output": ["templateid", "host", "name"],
        })
        found = {item.get("host"): item["templateid"] for item in result}
        found.update({item.get("name"): item["templateid"] for item in result})
        missing = [name for name in names if name not in found]
        if missing:
            logger.warning("Zabbix templates not found: %s", ", ".join(missing))
        return [found[name] for name in names if name in found]

    def _agent_interface(self, ip: str) -> dict:
        return {
            "type": 1,
            "main": 1,
            "useip": 1,
            "ip": ip,
            "dns": "",
            "port": "10050",
        }

    def _snmp_interface(self, ip: str, community: str | None = None) -> dict:
        return {
            "type": 2,
            "main": 1,
            "useip": 1,
            "ip": ip,
            "dns": "",
            "port": "161",
            "details": {
                "version": 2,
                "bulk": 1,
                "community": community or "{$SNMP_COMMUNITY}",
            },
        }

    def _host_macros(self, snmp_community: str | None = None) -> list[dict]:
        macros = []
        if snmp_community:
            macros.append({"macro": "{$SNMP_COMMUNITY}", "value": snmp_community})
        return macros

    def _get_host(self, host_name: str) -> dict | None:
        result = self._request("host.get", {
            "filter": {"host": [host_name]},
            "output": ["hostid", "host", "name", "status", "available", "snmp_available"],
            "selectInterfaces": ["interfaceid", "type", "main", "ip", "dns", "port", "details", "available", "error"],
            "selectParentTemplates": ["templateid", "host", "name"],
            "selectGroups": ["groupid", "name"],
            "selectMacros": ["hostmacroid", "macro", "value"],
        })
        return result[0] if result else None

    def _get_host_by_id(self, host_id: str) -> dict | None:
        result = self._request("host.get", {
            "hostids": [host_id],
            "output": ["hostid", "host", "name", "status", "available", "snmp_available"],
            "selectInterfaces": ["interfaceid", "type", "main", "ip", "dns", "port", "details", "available", "error"],
            "selectParentTemplates": ["templateid", "host", "name"],
            "selectGroups": ["groupid", "name"],
            "selectMacros": ["hostmacroid", "macro", "value"],
        })
        return result[0] if result else None

    def _update_or_create_interface(self, host_id: str, existing: list[dict], desired: dict) -> None:
        same_type = [iface for iface in existing if str(iface.get("type")) == str(desired["type"])]
        main = next((iface for iface in same_type if str(iface.get("main")) == "1"), None)
        iface = main or (same_type[0] if same_type else None)
        if iface:
            payload = {"interfaceid": iface["interfaceid"], **desired}
            self._request("hostinterface.update", payload)
            return
        self._request("hostinterface.create", {"hostid": host_id, **desired})

    def _update_host_interfaces(self, host_id: str, existing: list[dict], ip: str, snmp_community: str | None) -> None:
        self._update_or_create_interface(host_id, existing, self._agent_interface(ip))
        self._update_or_create_interface(host_id, existing, self._snmp_interface(ip, snmp_community))

    def sync_host(
        self,
        host_name: str,
        ip: str,
        group_id: str,
        host_id: str | None = None,
        template_ids: list | None = None,
        snmp_community: str | None = None,
        enabled: bool = True,
    ) -> str:
        """Cria ou atualiza um host no Zabbix."""
        if not template_ids:
            template_ids = []
        macros = self._host_macros(snmp_community)
        existing = self._get_host_by_id(host_id) if host_id else None
        if not existing:
            existing = self._get_host(host_name)
        
        if existing:
            host_id = existing["hostid"]
            self._update_host_interfaces(host_id, existing.get("interfaces", []), ip, snmp_community)
            params = {
                "hostid": host_id,
                "host": host_name,
                "groups": [{"groupid": group_id}],
                "status": 0 if enabled else 1,
            }
            if template_ids:
                params["templates"] = [{"templateid": tid} for tid in template_ids]
            if macros:
                params["macros"] = macros
            self._request("host.update", params)
            return host_id

        params = {
            "host": host_name,
            "interfaces": [
                self._agent_interface(ip),
                self._snmp_interface(ip, snmp_community),
            ],
            "groups": [{"groupid": group_id}],
            "templates": [{"templateid": tid} for tid in template_ids],
            "status": 0 if enabled else 1,
        }
        if macros:
            params["macros"] = macros
        
        result = self._request("host.create", params)
        return result['hostids'][0]

    def create_host(self, host_name: str, ip: str, group_id: str, template_ids: list = None):
        """Compatibilidade: cria ou atualiza host habilitado."""
        return self.sync_host(host_name, ip, group_id, template_ids=template_ids, enabled=True)

    def disable_host(self, host_id: str | None = None, host_name: str | None = None) -> bool:
        """Desativa um host monitorado no Zabbix."""
        resolved_host_id = host_id
        if not resolved_host_id and host_name:
            host = self._get_host(host_name)
            resolved_host_id = host["hostid"] if host else None
        if not resolved_host_id:
            return False
        self._request("host.update", {"hostid": resolved_host_id, "status": 1})
        return True

    def get_host_status(self, host_id: str | None = None, host_name: str | None = None) -> dict | None:
        """Obtém status operacional básico do host no Zabbix."""
        params = {
            "output": ["hostid", "host", "name", "status", "available", "snmp_available"],
            "selectInterfaces": ["interfaceid", "type", "main", "ip", "port", "available", "error"],
        }
        if host_id:
            params["hostids"] = [host_id]
        elif host_name:
            params["filter"] = {"host": [host_name]}
        else:
            return None

        result = self._request("host.get", params)
        if not result:
            return None
        host = result[0]
        return {
            "host_id": host.get("hostid"),
            "host": host.get("host"),
            "enabled": str(host.get("status")) == "0",
            "agent_available": str(host.get("available")) == "1",
            "snmp_available": str(host.get("snmp_available")) == "1",
            "interfaces": host.get("interfaces") or [],
        }
