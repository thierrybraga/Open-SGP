import re
from pathlib import Path


def test_billing_money_columns_use_numeric():
    models = (Path(__file__).resolve().parents[1] / "app" / "modules" / "billing" / "models.py").read_text(
        encoding="utf-8"
    )
    gateway_models = (
        Path(__file__).resolve().parents[1] / "app" / "modules" / "billing" / "gateway" / "models.py"
    ).read_text(encoding="utf-8")

    combined = models + "\n" + gateway_models
    assert "Numeric(12, 2)" in combined
    assert not re.search(r"amount:\s*Mapped\[float\]\s*=\s*mapped_column\(Float", combined)
    assert not re.search(r"value:\s*Mapped\[float\]\s*=\s*mapped_column\(Float", combined)


def test_billing_has_no_placeholder_boleto_url():
    root = Path(__file__).resolve().parents[1] / "app"
    placeholders = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "boleto.example.com" in text or "pay.example.com" in text:
            placeholders.append(str(path))

    assert not placeholders, f"Placeholder payment URLs remain: {placeholders}"


def test_boleto_due_factor_uses_2025_febraban_restart():
    boleto = (Path(__file__).resolve().parents[1] / "app" / "shared" / "boleto.py").read_text(encoding="utf-8")

    assert "DATA_REINICIO_FATOR" in boleto
    assert "FATOR_REINICIO = 1000" in boleto
    assert "fator % 9999" not in boleto


def test_boleto_pdf_draws_real_barcode():
    pdf_generator = (
        Path(__file__).resolve().parents[1] / "app" / "modules" / "billing" / "pdf_generator.py"
    ).read_text(encoding="utf-8")

    assert "_draw_interleaved_2_of_5" in pdf_generator
    assert "ITF_PATTERNS" in pdf_generator
    assert "simulado" not in pdf_generator.lower()
