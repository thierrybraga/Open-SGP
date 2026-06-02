"""
Arquivo: app/modules/network/vendors/vsol.py

Responsabilidade:
Adapter VSOL via sessão Telnet para provisionamento básico de VLAN, perfil de
serviço e consulta operacional/óptica de ONU.

Integrações:
- modules.network.service
"""

import re
import socket
import time
from dataclasses import dataclass
from typing import Iterable


class VSOLCommandError(RuntimeError):
    """Raised when the OLT rejects or does not complete a command."""


@dataclass(frozen=True)
class VSOLONURef:
    """
    Parsed ONU identifier.

    Supported input examples:
    - "1"
    - "1/3"
    - "1/1:3"
    - "0/1/1:3"
    """

    raw: str
    pon: str | None
    onu: str


class VSOLClient:
    PROMPT_RE = re.compile(rb"(?m)(?:[\r\n]|^)[\w()./: -]*(?:>|#)\s*$")
    ERROR_RE = re.compile(r"(?i)(invalid|unknown|incomplete|ambiguous|error|failed|denied|not\s+found)")
    FLOAT_RE = re.compile(r"(-?\d+(?:\.\d+)?)")

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
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
        self.vendor = "vsol"

    def check_connection(self) -> bool:
        try:
            with socket.create_connection((self.host, self.port), timeout=3):
                return True
        except OSError:
            return False

    def get_info(self) -> dict:
        try:
            output = self._run_commands(["show version"])
        except VSOLCommandError as exc:
            return {"vendor": "VSOL", "status": "error", "error": str(exc)}
        except OSError:
            return {"vendor": "VSOL", "status": "unreachable"}

        model = self._extract_first(output, (r"(?i)\bmodel\s*[:=]\s*(\S+)", r"(?i)\bproduct\s*[:=]\s*(\S+)"))
        version = self._extract_first(output, (r"(?i)\bversion\s*[:=]\s*([^\r\n]+)", r"(?i)\bsoftware\s*[:=]\s*([^\r\n]+)"))
        return {
            "vendor": "VSOL",
            "status": "online",
            "model": model,
            "version": version,
            "raw": output,
        }

    def provision_vlan(self, onu_id: str, vlan_id: int) -> bool:
        ref = self._parse_onu_ref(onu_id)
        commands = self._config_commands(
            ref,
            [
                f"ont port native-vlan {ref.onu} 1 {vlan_id}",
                f"onu port vlan {ref.onu} eth 1 mode tag vlan {vlan_id}",
            ],
        )
        self._run_first_supported(commands)
        return True

    def set_service_profile(self, onu_id: str, download_mbps: float, upload_mbps: float) -> bool:
        ref = self._parse_onu_ref(onu_id)
        upload_kbps = int(upload_mbps * 1024)
        download_kbps = int(download_mbps * 1024)
        commands = self._config_commands(
            ref,
            [
                f"traffic-profile {ref.onu} up {upload_kbps} down {download_kbps}",
                f"onu bandwidth-profile {ref.onu} upstream {upload_kbps} downstream {download_kbps}",
                f"rate-limit onu {ref.onu} upstream {upload_kbps} downstream {download_kbps}",
            ],
        )
        self._run_first_supported(commands)
        return True

    def remove_service_profile(self, onu_id: str) -> bool:
        ref = self._parse_onu_ref(onu_id)
        commands = self._config_commands(
            ref,
            [
                f"no traffic-profile {ref.onu}",
                f"no onu bandwidth-profile {ref.onu}",
                f"no rate-limit onu {ref.onu}",
            ],
        )
        self._run_first_supported(commands)
        return True

    def bind_vlan(self, onu_id: str, vlan_id: int) -> bool:
        return self.provision_vlan(onu_id, vlan_id)

    def unbind_vlan(self, onu_id: str, vlan_id: int) -> bool:
        ref = self._parse_onu_ref(onu_id)
        commands = self._config_commands(
            ref,
            [
                f"no ont port native-vlan {ref.onu} 1",
                f"no onu port vlan {ref.onu} eth 1",
                f"onu port vlan {ref.onu} eth 1 mode transparent",
            ],
        )
        self._run_first_supported(commands)
        return True

    def onu_status(self, onu_id: str) -> dict:
        ref = self._parse_onu_ref(onu_id)
        info_output = self._run_first_supported(self._show_commands(ref, "info"))
        optical_output = self._run_first_supported(self._show_commands(ref, "optical"))

        combined = f"{info_output}\n{optical_output}"
        return {
            "onu_id": onu_id,
            "vendor": "vsol",
            "source": "device",
            "online": self._parse_online(combined),
            "rx_power_dbm": self._parse_metric(combined, ("rx", "receive")),
            "tx_power_dbm": self._parse_metric(combined, ("tx", "transmit")),
            "uptime_seconds": self._parse_uptime_seconds(combined),
            "distance_m": self._parse_int_metric(combined, ("distance",)),
            "temperature_c": self._parse_metric(combined, ("temperature", "temp")),
            "voltage_v": self._parse_metric(combined, ("voltage",)),
            "bias_current_ma": self._parse_metric(combined, ("bias", "current")),
            "raw": combined,
        }

    def _run_first_supported(self, command_sets: Iterable[list[str]]) -> str:
        errors = []
        for commands in command_sets:
            try:
                return self._run_commands(commands)
            except VSOLCommandError as exc:
                errors.append(str(exc))
        raise VSOLCommandError("; ".join(errors) or "No supported VSOL command completed successfully")

    def _run_commands(self, commands: Iterable[str]) -> str:
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.settimeout(self.timeout)
            self._login(sock)
            output_parts = []
            for command in commands:
                output = self._send_and_read(sock, command)
                output_parts.append(output)
                self._raise_if_error(command, output)
            return "\n".join(output_parts)

    def _login(self, sock: socket.socket) -> None:
        initial = self._read_until_prompt_or_login(sock)
        lower = initial.lower()
        if "login" in lower or "username" in lower or "user name" in lower:
            self._send(sock, self.username)
            password_prompt = self._read_until(sock, (b"password", b"Password", b"#", b">"))
            if b"assword" in password_prompt:
                self._send(sock, self.password)
        elif "password" in lower:
            self._send(sock, self.password)

        prompt = self._read_until_prompt(sock)
        if prompt.rstrip().endswith(b">"):
            self._send(sock, "enable")
            enable_output = self._read_until(sock, (b"password", b"Password", b"#", b">"))
            if b"assword" in enable_output:
                self._send(sock, self.enable_password or self.password)
            self._read_until_prompt(sock)

    def _send_and_read(self, sock: socket.socket, command: str) -> str:
        self._send(sock, command)
        return self._strip_command_echo(command, self._read_until_prompt(sock).decode("utf-8", errors="replace"))

    def _send(self, sock: socket.socket, value: str) -> None:
        sock.sendall(value.encode("utf-8") + b"\r\n")

    def _read_until_prompt_or_login(self, sock: socket.socket) -> str:
        return self._read_until(sock, (b"login", b"Login", b"username", b"Username", b"password", b"Password", b">", b"#")).decode(
            "utf-8", errors="replace"
        )

    def _read_until_prompt(self, sock: socket.socket) -> bytes:
        return self._read_until(sock, (b">", b"#"))

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
        stripped = [line for line in lines if line.strip() and line.strip() != command]
        return "\n".join(stripped).strip()

    def _raise_if_error(self, command: str, output: str) -> None:
        if self.ERROR_RE.search(output):
            raise VSOLCommandError(f"VSOL command failed: {command}: {output.strip()}")

    def _config_commands(self, ref: VSOLONURef, candidates: list[str]) -> list[list[str]]:
        command_sets = []
        for candidate in candidates:
            for config_command in ("configure terminal", "config"):
                if ref.pon:
                    for interface_prefix in ("interface gpon", "interface epon", "interface pon"):
                        command_sets.append([config_command, f"{interface_prefix} {ref.pon}", candidate, "exit", "exit"])
                else:
                    command_sets.append([config_command, candidate, "exit"])
        return command_sets

    def _show_commands(self, ref: VSOLONURef, kind: str) -> list[list[str]]:
        if kind == "info":
            candidates = [
                f"show onu info {ref.raw}",
                f"show onu information {ref.raw}",
                f"show onu {ref.raw}",
            ]
        else:
            candidates = [
                f"show onu optical-power {ref.raw}",
                f"show onu optical power {ref.raw}",
                f"show onu power {ref.raw}",
            ]
        if ref.pon:
            for interface_name in ("gpon", "epon", "pon"):
                candidates.append(f"show onu {kind} interface {interface_name} {ref.pon} onu {ref.onu}")
        return [[candidate] for candidate in candidates]

    def _parse_onu_ref(self, onu_id: str) -> VSOLONURef:
        raw = str(onu_id).strip()
        if not raw:
            raise ValueError("ONU identifier is required")
        if ":" in raw:
            pon, onu = raw.rsplit(":", 1)
            return VSOLONURef(raw=raw, pon=pon.strip() or None, onu=onu.strip())
        if "/" in raw:
            pon, onu = raw.rsplit("/", 1)
            return VSOLONURef(raw=raw, pon=pon.strip() or None, onu=onu.strip())
        return VSOLONURef(raw=raw, pon=None, onu=raw)

    def _parse_online(self, output: str) -> bool:
        if re.search(r"(?i)\b(offline|down|los|dying gasp)\b", output):
            return False
        if re.search(r"(?i)\b(online|up|working|active)\b", output):
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

    def _parse_int_metric(self, output: str, labels: tuple[str, ...]) -> int | None:
        value = self._parse_metric(output, labels)
        return int(value) if value is not None else None

    def _parse_uptime_seconds(self, output: str) -> int | None:
        line = next((line for line in output.splitlines() if "uptime" in line.lower()), "")
        if not line:
            return None
        total = 0
        patterns = {
            "day": 86400,
            "hour": 3600,
            "min": 60,
            "sec": 1,
        }
        for label, multiplier in patterns.items():
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

    def _extract_first(self, output: str, patterns: tuple[str, ...]) -> str | None:
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1).strip()
        return None
