"""
Arquivo: app/modules/communication/providers/whatsapp.py

Responsabilidade:
Envio de mensagens WhatsApp via gateway HTTP configurável.

Integrações:
- core.config.Settings
"""

import json
from urllib import request
from urllib.error import URLError, HTTPError

from ....core.config import settings
from base64 import b64encode
from urllib.parse import urlencode


def _send_gateway(destination: str, content: str) -> bool:
    url = settings.whatsapp_gateway_url
    token = settings.whatsapp_api_token
    if not url or not token:
        return False
    payload = json.dumps({"to": destination, "message": content}).encode("utf-8")
    req = request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except (HTTPError, URLError, TimeoutError):
        return False


def _send_twilio(destination: str, content: str) -> bool:
    sid = settings.twilio_account_sid
    token = settings.twilio_auth_token
    from_number = settings.twilio_whatsapp_number
    if not sid or not token or not from_number:
        return False
    api_url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    body = urlencode(
        {
            "To": f"whatsapp:{destination}",
            "From": f"whatsapp:{from_number}",
            "Body": content,
        }
    ).encode("utf-8")
    auth = b64encode(f"{sid}:{token}".encode("utf-8")).decode("ascii")
    req = request.Request(api_url, data=body, method="POST")
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except (HTTPError, URLError, TimeoutError):
        return False


def _send_gupshup(destination: str, content: str) -> bool:
    api_url = settings.gupshup_api_url or "https://api.gupshup.io/sm/api/v1/msg"
    api_key = settings.gupshup_api_key
    if not api_key:
        return False
    payload = json.dumps(
        {
            "channel": "whatsapp",
            "source": settings.twilio_whatsapp_number or "",
            "destination": destination,
            "message": {"type": "text", "text": content},
        }
    ).encode("utf-8")
    req = request.Request(api_url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("apikey", api_key)
    try:
        with request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except (HTTPError, URLError, TimeoutError):
        return False


def _send_zenvia(destination: str, content: str) -> bool:
    api_url = settings.zenvia_api_url or "https://api.zenvia.com/v2/channels/whatsapp/messages"
    token = settings.zenvia_api_token
    if not token:
        return False
    payload = json.dumps(
        {
            "from": settings.twilio_whatsapp_number or "",
            "to": destination,
            "contents": [{"type": "text", "text": content}],
        }
    ).encode("utf-8")
    req = request.Request(api_url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-API-TOKEN", token)
    try:
        with request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except (HTTPError, URLError, TimeoutError):
        return False


def send_whatsapp(destination: str, content: str) -> bool:
    if settings.environment == "testing":
        return True
    provider = (settings.whatsapp_provider or "gateway").lower()
    if provider == "twilio":
        return _send_twilio(destination, content)
    if provider == "gupshup":
        return _send_gupshup(destination, content)
    if provider == "zenvia":
        return _send_zenvia(destination, content)
    return _send_gateway(destination, content)
