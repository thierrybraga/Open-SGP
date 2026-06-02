from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_fiscal_service_does_not_fake_signature_or_sefaz_success():
    service = _read("app/modules/fiscal/service.py")

    assert "return True" not in service
    assert "Simula" not in service
    assert "Dummy implementation" not in service
    assert "A1_CERT_PFX_PATH" in service
    assert "A1_CERT_PASSWORD" in service
    assert "SefazClient" in service
    assert 'invoice.status = "emitted"' in service
    assert 'status_code in ("100", "104")' in service


def test_fiscal_routes_persist_issue_sign_and_sefaz_state_changes():
    routes = _read("app/modules/fiscal/routes.py")

    assert "inv = issue_invoice(db, inv, payload)" in routes
    assert "inv = sign_invoice_a1(inv)" in routes
    assert "inv = send_to_sefaz(inv, force=force)" in routes
    assert routes.count("db.commit()") >= 3


def test_gateway_charges_do_not_generate_placeholder_payment_urls():
    service = _read("app/modules/billing/gateway/service.py")

    assert "pay.example.com" not in service
    assert "requests.post" in service
    assert "Unsupported payment gateway provider" in service
    assert "do not create local placeholder payment URLs" in service
