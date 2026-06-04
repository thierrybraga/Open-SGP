from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_email_config_uses_central_fernet_encryption_not_base64():
    service = _read("app/modules/administration/email_config/service.py")

    assert "fernet_encrypt_password" in service
    assert "fernet_decrypt_password" in service
    assert "migrate_from_base64" in service
    assert "TODO" not in service
    assert "base64.b64encode" not in service
    assert "base64.b64decode" not in service


def test_admin_payment_gateway_test_is_not_simulated_success():
    service = _read("app/modules/administration/payment_gateways/service.py")

    assert "Connection test successful (simulated)" not in service
    assert "requests.get" in service
    assert "_test_asaas" in service
    assert "_test_mercadopago" in service
    assert "_test_stripe" in service
    assert "does not have a real connection test implemented" in service
