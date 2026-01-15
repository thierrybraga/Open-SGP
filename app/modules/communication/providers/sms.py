"""
Arquivo: app/modules/communication/providers/sms.py

Responsabilidade:
Envio de SMS via gateway HTTP configurável, com autenticação por API key.

Integrações:
- core.config.Settings
"""

import json
from urllib import request
from urllib.error import URLError, HTTPError

from ....core.config import settings


def send_sms(destination: str, content: str) -> bool:
    if settings.environment == "testing":
        return True

    url = settings.sms_gateway_url
    api_key = settings.sms_api_key
    if not url or not api_key:
        return False

    payload = json.dumps({"to": destination, "message": content}).encode("utf-8")
    req = request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")

    try:
        with request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except (HTTPError, URLError, TimeoutError):
        return False
