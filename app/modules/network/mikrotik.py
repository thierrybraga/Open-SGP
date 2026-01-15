"""
Arquivo: app/modules/network/mikrotik.py

Responsabilidade:
Integração com dispositivos MikroTik via RouterOS API.

Requer: pip install routeros-api
"""

from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

try:
    import routeros_api
    ROUTEROS_AVAILABLE = True
except ImportError:
    ROUTEROS_AVAILABLE = False
    logger.warning("routeros-api not installed. MikroTik integration disabled.")


class MikroTikClient:
    """Cliente para comunicação com MikroTik RouterOS"""

    def __init__(self, host: str, username: str, password: str, port: int = 8728, use_ssl: bool = False):
        """
        Inicializa conexão com MikroTik.

        Args:
            host: IP ou hostname do MikroTik
            username: Usuário admin
            password: Senha
            port: Porta da API (padrão: 8728, SSL: 8729)
            use_ssl: Usar SSL/TLS
        """
        if not ROUTEROS_AVAILABLE:
            raise ImportError("routeros-api package not installed")

        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.use_ssl = use_ssl
        self.connection = None

    def connect(self):
        """Estabelece conexão com o MikroTik"""
        try:
            self.connection = routeros_api.RouterOsApiPool(
                self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                use_ssl=self.use_ssl,
                ssl_verify=False,
                plaintext_login=True
            )
            return self.connection.get_api()
        except Exception as e:
            logger.error(f"Failed to connect to MikroTik {self.host}: {e}")
            raise

    def disconnect(self):
        """Fecha conexão"""
        if self.connection:
            self.connection.disconnect()

    def create_pppoe_secret(self, username: str, password: str, service: str = "pppoe",
                           profile: str = "default", local_address: str = "",
                           remote_address: str = "") -> Dict[str, Any]:
        """
        Cria um secret PPPoE.

        Args:
            username: Nome de usuário
            password: Senha
            service: Serviço (pppoe, pptp, l2tp, etc.)
            profile: Profile a usar
            local_address: IP local (gateway)
            remote_address: IP do cliente

        Returns:
            Dict com informações do secret criado
        """
        api = self.connect()
        try:
            secrets = api.get_resource('/ppp/secret')
            secret = secrets.add(
                name=username,
                password=password,
                service=service,
                profile=profile,
                **({'local-address': local_address} if local_address else {}),
                **({'remote-address': remote_address} if remote_address else {})
            )
            return secret
        finally:
            self.disconnect()

    def remove_pppoe_secret(self, username: str) -> bool:
        """
        Remove secret PPPoE pelo username.

        Returns:
            True se removido com sucesso
        """
        api = self.connect()
        try:
            secrets = api.get_resource('/ppp/secret')
            secret_list = secrets.get(name=username)

            if secret_list:
                secrets.remove(id=secret_list[0]['id'])
                return True
            return False
        finally:
            self.disconnect()

    def enable_pppoe_secret(self, username: str) -> bool:
        """Habilita secret PPPoE"""
        return self._toggle_secret(username, disabled=False)

    def disable_pppoe_secret(self, username: str) -> bool:
        """Desabilita secret PPPoE"""
        return self._toggle_secret(username, disabled=True)

    def _toggle_secret(self, username: str, disabled: bool) -> bool:
        """Habilita/desabilita secret"""
        api = self.connect()
        try:
            secrets = api.get_resource('/ppp/secret')
            secret_list = secrets.get(name=username)

            if secret_list:
                secrets.set(id=secret_list[0]['id'], disabled='yes' if disabled else 'no')
                return True
            return False
        finally:
            self.disconnect()

    def get_active_connections(self) -> List[Dict[str, Any]]:
        """
        Retorna lista de conexões PPPoE ativas.

        Returns:
            Lista de dicts com informações de cada conexão
        """
        api = self.connect()
        try:
            active = api.get_resource('/ppp/active')
            return list(active.get())
        finally:
            self.disconnect()

    def add_queue_simple(self, name: str, target: str, max_limit: str,
                        burst_limit: Optional[str] = None,
                        burst_threshold: Optional[str] = None,
                        burst_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Adiciona uma fila simples (limitação de banda).

        Args:
            name: Nome da fila
            target: IP ou subnet alvo
            max_limit: Limite máximo (upload/download) ex: "10M/100M"
            burst_limit: Limite de burst ex: "15M/150M"
            burst_threshold: Threshold do burst ex: "8M/80M"
            burst_time: Tempo de burst ex: "20s/20s"

        Returns:
            Dict com informações da fila criada
        """
        api = self.connect()
        try:
            queues = api.get_resource('/queue/simple')
            queue = queues.add(
                name=name,
                target=target,
                max_limit=max_limit,
                **({'burst-limit': burst_limit} if burst_limit else {}),
                **({'burst-threshold': burst_threshold} if burst_threshold else {}),
                **({'burst-time': burst_time} if burst_time else {})
            )
            return queue
        finally:
            self.disconnect()

    def remove_queue_simple(self, name: str) -> bool:
        """Remove fila simples pelo nome"""
        api = self.connect()
        try:
            queues = api.get_resource('/queue/simple')
            queue_list = queues.get(name=name)

            if queue_list:
                queues.remove(id=queue_list[0]['id'])
                return True
            return False
        finally:
            self.disconnect()
