"""
Arquivo: app/modules/network/vendors/olt.py

Responsabilidade:
Adapters Huawei/ZTE via sessão CLI Telnet para provisionamento básico de VLAN,
perfil de serviço e consulta de ONU.

Integrações:
- modules.network.service
"""

import re
import socket
import time
from dataclasses import dataclass
from typing import Iterable


class OLTCommandError(RuntimeError):
    """Raised when the OLT rejects or does not complete a command."""


@dataclass(frozen=True)
class ONURef:
    raw: str
    frame: str | None
    slot: str | None
    pon: str | None
    onu: str


class OLTClient:
    PROMPT_RE = re.compile(rb"(?m)(?:[\r\n]|^)[\w()./: -]*(?:>|#|])\s*$")
    ERROR_RE = re.compile(r"(?i)(invalid|unknown|incomplete|ambiguous|error|failed|denied|not\s+found|failure)")
    FLOAT_RE = re.compile(r"(-?\d+(?:\.\d+)?)")

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        vendor: str | None = None,
        port: int = 23,
        timeout: float = 8.0,
        enable_password: str | None = None,
    ):
        self.host = host
        self.port = port or 23
        self.username = username
        self.password = password
        self.enable_password = enable_password
        self.timeout = timeout
        self.vendor = (vendor or "generic").lower()

    def check_connection(self) -> bool:
        try:
            with socket.create_connection((self.host, self.port), timeout=3):
                return True
        except OSError:
            return False

    def get_info(self) -> dict:
        if self.vendor not in ("huawei", "zte"):
            if self.check_connection():
                return {"vendor": self.vendor, "status": "online"}
            return {"vendor": self.vendor, "status": "unreachable"}
        try:
            output = self._run_first_supported([["display version"], ["show version"]])
            return {"vendor": self.vendor, "status": "online", "raw": output}
        except (OLTCommandError, OSError) as exc:
            return {"vendor": self.vendor, "status": "error", "error": str(exc)}

    def provision_vlan(self, onu_id: str, vlan_id: int) -> bool:
        self._ensure_supported()
        ref = self._parse_onu_ref(onu_id)
        self._run_first_supported(self._vlan_commands(ref, vlan_id, remove=False))
        return True

    def set_service_profile(self, onu_id: str, download_mbps: float, upload_mbps: float) -> bool:
        self._ensure_supported()
        ref = self._parse_onu_ref(onu_id)
        down_kbps = int(download_mbps * 1024)
        up_kbps = int(upload_mbps * 1024)
        self._run_first_supported(self._profile_commands(ref, down_kbps, up_kbps, remove=False))
        return True

    def remove_service_profile(self, onu_id: str) -> bool:
        self._ensure_supported()
        ref = self._parse_onu_ref(onu_id)
        self._run_first_supported(self._profile_commands(ref, 0, 0, remove=True))
        return True

    def bind_vlan(self, onu_id: str, vlan_id: int) -> bool:
        return self.provision_vlan(onu_id, vlan_id)

    def unbind_vlan(self, onu_id: str, vlan_id: int) -> bool:
        self._ensure_supported()
        ref = self._parse_onu_ref(onu_id)
        self._run_first_supported(self._vlan_commands(ref, vlan_id, remove=True))
        return True

    def onu_status(self, onu_id: str) -> dict:
        self._ensure_supported()
        ref = self._parse_onu_ref(onu_id)
        info = self._run_first_supported(self._status_commands(ref))
        optical = self._run_first_supported(self._optical_commands(ref))
        combined = f"{info}\n{optical}"
        return {
            "onu_id": onu_id,
            "vendor": self.vendor,
            "source": "device",
            "online": self._parse_online(combined),
            "rx_power_dbm": self._parse_metric(combined, ("rx", "receive")),
            "tx_power_dbm": self._parse_metric(combined, ("tx", "transmit")),
            "uptime_seconds": self._parse_uptime_seconds(combined),
            "raw": combined,
        }

    def _ensure_supported(self) -> None:
        if self.vendor not in ("huawei", "zte"):
            raise NotImplementedError(f"OLT vendor {self.vendor} requer adapter específico do fabricante")

    def _run_first_supported(self, command_sets: Iterable[list[str]]) -> str:
        errors = []
        for commands in command_sets:
            try:
                return self._run_commands(commands)
            except OLTCommandError as exc:
                errors.append(str(exc))
        raise OLTCommandError("; ".join(errors) or f"No supported {self.vendor} command completed successfully")

    def _run_commands(self, commands: Iterable[str]) -> str:
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.settimeout(self.timeout)
            self._login(sock)
            outputs = []
            for command in commands:
                output = self._send_and_read(sock, command)
                outputs.append(output)
                self._raise_if_error(command, output)
            return "\n".join(outputs)

    def _login(self, sock: socket.socket) -> None:
        initial = self._read_until(sock, (b"login", b"Login", b"username", b"Username", b"password", b"Password", b">", b"#", b"]"))
        lower = initial.decode("utf-8", errors="replace").lower()
        if "login" in lower or "username" in lower or "user name" in lower:
            self._send(sock, self.username)
            prompt = self._read_until(sock, (b"password", b"Password", b">", b"#", b"]"))
            if b"assword" in prompt:
                self._send(sock, self.password)
        elif "password" in lower:
            self._send(sock, self.password)

        prompt = self._read_until_prompt(sock)
        if prompt.rstrip().endswith(b">"):
            self._send(sock, "enable")
            enable_prompt = self._read_until(sock, (b"password", b"Password", b"#", b"]", b">"))
            if b"assword" in enable_prompt:
                self._send(sock, self.enable_password or self.password)
            self._read_until_prompt(sock)

    def _send_and_read(self, sock: socket.socket, command: str) -> str:
        self._send(sock, command)
        return self._strip_command_echo(command, self._read_until_prompt(sock).decode("utf-8", errors="replace"))

    def _send(self, sock: socket.socket, value: str) -> None:
        sock.sendall(value.encode("utf-8") + b"\r\n")

    def _read_until_prompt(self, sock: socket.socket) -> bytes:
        return self._read_until(sock, (b">", b"#", b"]"))

    def _read_until(self, sock: socket.socket, markers: tuple[bytes, ...]) -> bytes:
        deadline = time.monotonic() + self.timeout
        data = b""
        while time.monotonic() < deadline:
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
                break
            if not chunk:
                break
            data += self._remove_telnet_negotiation(chunk)
            if self.PROMPT_RE.search(data) or any(marker in data for marker in markers):
                break
        return data

    def _remove_telnet_negotiation(self, data: bytes) -> bytes:
        result = bytearray()
        i = 0
        while i < len(data):
            if data[i] == 255 and i + 2 < len(data):
                i += 3
                continue
            result.append(data[i])
            i += 1
        return bytes(result)

    def _strip_command_echo(self, command: str, output: str) -> str:
        lines = output.replace("\r", "").split("\n")
        return "\n".join(line for line in lines if line.strip() and line.strip() != command).strip()

    def _raise_if_error(self, command: str, output: str) -> None:
        if self.ERROR_RE.search(output):
            raise OLTCommandError(f"{self.vendor} OLT command failed: {command}: {output.strip()}")

    def _parse_onu_ref(self, onu_id: str) -> ONURef:
        raw = str(onu_id).strip()
        if not raw:
            raise ValueError("ONU identifier is required")
        path, onu = raw.rsplit(":", 1) if ":" in raw else ("", raw)
        parts = [part for part in re.split(r"[/\s-]+", path) if part]
        frame = parts[0] if len(parts) >= 3 else None
        slot = parts[-2] if len(parts) >= 2 else None
        pon = parts[-1] if parts else None
        return ONURef(raw=raw, frame=frame, slot=slot, pon=pon, onu=onu)

    def _huawei_interface(self, ref: ONURef) -> str:
        if ref.frame and ref.slot:
            return f"interface gpon {ref.frame}/{ref.slot}"
        if ref.slot:
            return f"interface gpon 0/{ref.slot}"
        return "interface gpon 0/0"

    def _huawei_port(self, ref: ONURef) -> str:
        return ref.pon or "0"

    def _zte_pon(self, ref: ONURef) -> str:
        if ref.frame and ref.slot and ref.pon:
            return f"{ref.frame}/{ref.slot}/{ref.pon}"
        if ref.slot and ref.pon:
            return f"1/{ref.slot}/{ref.pon}"
        return ref.pon or "1/1/1"

    def _vlan_commands(self, ref: ONURef, vlan_id: int, remove: bool) -> list[list[str]]:
        if self.vendor == "huawei":
            command = (
                f"undo service-port port {self._huawei_port(ref)} ont {ref.onu} vlan {vlan_id}"
                if remove
                else f"service-port vlan {vlan_id} gpon {self._huawei_port(ref)} ont {ref.onu} gemport 1 multi-service user-vlan {vlan_id} tag-transform translate"
            )
            return [["config", self._huawei_interface(ref), command, "quit", "quit"]]

        command = (
            f"no switchport vlan {vlan_id} tag vport {ref.onu}"
            if remove
            else f"switchport vlan {vlan_id} tag vport {ref.onu}"
        )
        return [["configure terminal", f"interface gpon-olt_{self._zte_pon(ref)}", command, "exit", "exit"]]

    def _profile_commands(self, ref: ONURef, down_kbps: int, up_kbps: int, remove: bool) -> list[list[str]]:
        if self.vendor == "huawei":
            command = (
                f"ont bandwidth-profile {self._huawei_port(ref)} {ref.onu} traffic-table index 0"
                if remove
                else f"ont bandwidth-profile {self._huawei_port(ref)} {ref.onu} car inbound {up_kbps} outbound {down_kbps}"
            )
            return [["config", self._huawei_interface(ref), command, "quit", "quit"]]

        command = (
            f"no onu rate-limit {ref.onu}"
            if remove
            else f"onu rate-limit {ref.onu} upstream {up_kbps} downstream {down_kbps}"
        )
        return [["configure terminal", f"interface gpon-onu_{self._zte_pon(ref)}:{ref.onu}", command, "exit", "exit"]]

    def _status_commands(self, ref: ONURef) -> list[list[str]]:
        if self.vendor == "huawei":
            return [
                ["display ont info summary"],
                [self._huawei_interface(ref), f"display ont info {self._huawei_port(ref)} {ref.onu}", "quit"],
            ]
        return [
            [f"show gpon onu state gpon-olt_{self._zte_pon(ref)}"],
            [f"show onu running config gpon-onu_{self._zte_pon(ref)}:{ref.onu}"],
        ]

    def _optical_commands(self, ref: ONURef) -> list[list[str]]:
        if self.vendor == "huawei":
            return [[self._huawei_interface(ref), f"display ont optical-info {self._huawei_port(ref)} {ref.onu}", "quit"]]
        return [[f"show pon power attenuation gpon-onu_{self._zte_pon(ref)}:{ref.onu}"]]

    def _parse_online(self, output: str) -> bool:
        if re.search(r"(?i)\b(offline|down|los|dying gasp|deactive)\b", output):
            return False
        if re.search(r"(?i)\b(online|up|active|working|normal)\b", output):
            return True
        return False

    def _parse_metric(self, output: str, labels: tuple[str, ...]) -> float | None:
        for line in output.splitlines():
            lower = line.lower()
            if not any(label in lower for label in labels):
                continue
            match = re.search(rf"(?i)(?:{'|'.join(re.escape(label) for label in labels)})[^\d-]*(-?\d+(?:\.\d+)?)", line)
            if not match:
                match = self.FLOAT_RE.search(line)
            if match:
                return float(match.group(1))
        return None

    def _parse_uptime_seconds(self, output: str) -> int | None:
        line = next((line for line in output.splitlines() if "uptime" in line.lower() or "up time" in line.lower()), "")
        if not line:
            return None
        total = 0
        for label, multiplier in {"day": 86400, "hour": 3600, "min": 60, "sec": 1}.items():
            match = re.search(rf"(\d+)\s*{label}", line, re.I)
            if match:
                total += int(match.group(1)) * multiplier
        if total:
            return total
        match = re.search(r"(\d+):(\d+):(\d+)", line)
        if match:
            hours, minutes, seconds = [int(part) for part in match.groups()]
            return hours * 3600 + minutes * 60 + seconds
        return None
