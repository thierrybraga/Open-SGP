"""
Arquivo: app/modules/network/vendors/radius.py

Responsabilidade:
Gerenciamento de usuários FreeRADIUS via banco de dados (SQL).
Manipula tabelas radcheck, radreply e radusergroup.

Integrações:
- modules.network.models (RadCheck, RadReply, RadUserGroup)
"""

from sqlalchemy.orm import Session
from ..models import RadCheck, RadReply, RadUserGroup, RadGroupReply, RadAcct
from ...administration.nas.models import NAS
import socket
import struct
import hashlib
import random

class RadiusClient:
    def __init__(self, db: Session):
        self.db = db

    def _set_check_attribute(self, username: str, attribute: str, value: str, op: str = ":="):
        """Define um atributo na tabela radcheck"""
        item = self.db.query(RadCheck).filter(
            RadCheck.username == username,
            RadCheck.attribute == attribute
        ).first()
        
        if item:
            item.value = value
            item.op = op
        else:
            item = RadCheck(username=username, attribute=attribute, value=value, op=op)
            self.db.add(item)

    def _set_reply_attribute(self, username: str, attribute: str, value: str, op: str = "="):
        """Define um atributo na tabela radreply"""
        item = self.db.query(RadReply).filter(
            RadReply.username == username,
            RadReply.attribute == attribute
        ).first()
        
        if item:
            item.value = value
            item.op = op
        else:
            item = RadReply(username=username, attribute=attribute, value=value, op=op)
            self.db.add(item)

    def _remove_reply_attribute(self, username: str, attribute: str):
        """Remove um atributo da tabela radreply"""
        self.db.query(RadReply).filter(
            RadReply.username == username,
            RadReply.attribute == attribute
        ).delete()

    def _set_group_reply_attribute(self, groupname: str, attribute: str, value: str, op: str = "="):
        """Define um atributo na tabela radgroupreply (Template)"""
        item = self.db.query(RadGroupReply).filter(
            RadGroupReply.groupname == groupname,
            RadGroupReply.attribute == attribute
        ).first()
        
        if item:
            item.value = value
            item.op = op
        else:
            item = RadGroupReply(groupname=groupname, attribute=attribute, value=value, op=op)
            self.db.add(item)

    def _assign_user_group(self, username: str, groupname: str, priority: int = 1):
        """Associa usuário a um grupo (Template)"""
        # Remove grupos anteriores (assumindo 1 plano por vez para simplificar)
        self.db.query(RadUserGroup).filter(
            RadUserGroup.username == username
        ).delete()
        
        item = RadUserGroup(username=username, groupname=groupname, priority=priority)
        self.db.add(item)

    def create_plan_template(self, name: str, download_mbps: float, upload_mbps: float):
        """
        Cria um template (Grupo) no Radius para um plano de internet.
        Ex: 'plan_100m' -> Mikrotik-Rate-Limit = 100M/50M
        """
        down_str = f"{int(download_mbps)}M" if download_mbps >= 1 else f"{int(download_mbps*1024)}k"
        up_str = f"{int(upload_mbps)}M" if upload_mbps >= 1 else f"{int(upload_mbps*1024)}k"
        rate_limit = f"{down_str}/{up_str}"
        
        # Define atributos do grupo
        self._set_group_reply_attribute(name, "Mikrotik-Rate-Limit", rate_limit)
        self._set_group_reply_attribute(name, "Framed-Protocol", "PPP")
        self._set_group_reply_attribute(name, "Service-Type", "Framed-User")
        
        self.db.commit()
        return True

    def create_or_update_user(
        self,
        username: str,
        password: str,
        plan_group_name: str | None = None,
        ip_address: str | None = None,
        # Legacy params (kept for compatibility but optional if group used)
        download_mbps: float | None = None,
        upload_mbps: float | None = None,
        burst_enabled: bool = False,
        burst_rate_percent: float = 0.0,
        burst_threshold_seconds: int = 0
    ):
        """
        Cria ou atualiza usuário no Radius.
        Suporta Templates (Grupos) ou Atributos Individuais.
        """
        # 1. Senha (Sempre individual)
        self._set_check_attribute(username, "Cleartext-Password", password)

        # 2. Estratégia de Plano: Grupo (Template) ou Individual
        if plan_group_name:
            # Usa Template (Recomendado)
            self._assign_user_group(username, plan_group_name)
            # Remove atributos individuais que conflitem
            self._remove_reply_attribute(username, "Mikrotik-Rate-Limit")
        elif download_mbps and upload_mbps:
            # Usa Atributos Individuais (Legado)
            down_str = f"{int(download_mbps)}M" if download_mbps >= 1 else f"{int(download_mbps*1024)}k"
            up_str = f"{int(upload_mbps)}M" if upload_mbps >= 1 else f"{int(upload_mbps*1024)}k"
            rate_limit = f"{down_str}/{up_str}"
            self._set_reply_attribute(username, "Mikrotik-Rate-Limit", rate_limit)
        
        # 3. IP Address (Framed-IP-Address) - Sempre Individual se fixo
        if ip_address:
            self._set_reply_attribute(username, "Framed-IP-Address", ip_address)
        else:
            self._remove_reply_attribute(username, "Framed-IP-Address")
            
        self.db.commit()
        return True

    def _send_disconnect_packet(self, nas_ip: str, secret: str, username: str, session_id: str):
        """
        Envia um pacote Disconnect-Request (RFC 3576) para o NAS.
        """
        # Constantes
        CODE_DISCONNECT_REQUEST = 40
        IDENTIFIER = random.randint(0, 255)
        
        # Atributos
        # User-Name (Type 1)
        attr_username = b'\x01' + bytes([len(username) + 2]) + username.encode('utf-8')
        # Acct-Session-Id (Type 44)
        attr_session = b'\x2c' + bytes([len(session_id) + 2]) + session_id.encode('utf-8')
        
        attributes = attr_username + attr_session
        
        # Length (Code + ID + Length + Auth + Attrs)
        length = 1 + 1 + 2 + 16 + len(attributes)
        
        # Authenticator Calculation
        # MD5(Code + ID + Length + 16*0x00 + Attributes + Secret)
        header_no_auth = struct.pack('!BBH', CODE_DISCONNECT_REQUEST, IDENTIFIER, length)
        zero_auth = b'\x00' * 16
        
        payload = header_no_auth + zero_auth + attributes + secret.encode('utf-8')
        authenticator = hashlib.md5(payload).digest()
        
        # Packet construction
        packet = header_no_auth + authenticator + attributes
        
        # Send
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            sock.sendto(packet, (nas_ip, 3799)) # Port 3799 is standard for CoA
            sock.close()
            return True
        except Exception as e:
            print(f"Error sending CoA to {nas_ip}: {e}")
            return False

    def disconnect_user(self, username: str):
        """
        Desconecta o usuário do NAS imediatamente.
        """
        # 1. Encontrar sessão ativa
        session = self.db.query(RadAcct).filter(
            RadAcct.username == username,
            RadAcct.acctstoptime.is_(None)
        ).order_by(RadAcct.acctstarttime.desc()).first()
        
        if not session:
            return False # Usuário offline
            
        # 2. Encontrar NAS e Secret
        # Tenta pelo IP do NAS registrado na sessão
        nas = self.db.query(NAS).filter(NAS.ip_address == session.nasipaddress).first()
        
        if not nas:
            return False
            
        # 3. Enviar pacote
        return self._send_disconnect_packet(nas.ip_address, nas.secret, username, session.acctsessionid)

    def block_user(self, username: str):
        """Bloqueia usuário (Auth-Type := Reject) e desconecta"""
        self._set_check_attribute(username, "Auth-Type", "Reject")
        self.db.commit()
        
        # Tenta desconectar se estiver online
        self.disconnect_user(username)
        
        return True

    def unblock_user(self, username: str):
        """Desbloqueia usuário (Remove Auth-Type := Reject)"""
        self.db.query(RadCheck).filter(
            RadCheck.username == username,
            RadCheck.attribute == "Auth-Type",
            RadCheck.value == "Reject"
        ).delete()
        self.db.commit()
        return True
