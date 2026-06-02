from pathlib import Path


def test_health_readiness_uses_sqlalchemy_text_and_503_response():
    health_routes = Path(__file__).resolve().parents[1] / "app" / "modules" / "health" / "routes.py"
    content = health_routes.read_text(encoding="utf-8")

    assert 'db.execute(text("SELECT 1"))' in content
    assert "JSONResponse(status_code=200 if all_healthy else 503" in content


def test_metrics_use_prometheus_text_format():
    health_routes = Path(__file__).resolve().parents[1] / "app" / "modules" / "health" / "routes.py"
    content = health_routes.read_text(encoding="utf-8")

    assert "PlainTextResponse" in content
    assert "open_sgp_cpu_percent" in content
    assert "text/plain; version=0.0.4" in content


def test_ci_runs_alembic_upgrade_head():
    ci = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"
    content = ci.read_text(encoding="utf-8")

    assert "alembic upgrade head" in content
    assert "AUTO_CREATE_TABLES" in content
