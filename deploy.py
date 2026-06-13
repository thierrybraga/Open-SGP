"""
Deploy local do Open-SGP usando Docker Compose.

Fluxo:
1. valida Docker/Compose e arquivo .env
2. executa build das imagens
3. sobe banco/Redis e executa Alembic
4. sobe API, painel admin e worker
5. valida endpoints de saúde e status dos containers
"""

from __future__ import annotations

import argparse
import base64
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
COMPOSE_FILE = ROOT / "docker-compose.prod.yml"

REQUIRED_ENV = {
    "ENVIRONMENT": "production",
    "SECRET_KEY": None,
    "ENCRYPTION_KEY": None,
    "POSTGRES_PASSWORD": None,
    "DATABASE_URL": None,
    "REDIS_URL": None,
    "CORS_ALLOW_ORIGINS": None,
}


class DeployError(RuntimeError):
    pass


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        check=check,
    )


def compose_cmd(*args: str) -> list[str]:
    return ["docker", "compose", "--env-file", str(ENV_FILE), "-f", str(COMPOSE_FILE), *args]


def check_prerequisites() -> None:
    if not COMPOSE_FILE.exists():
        raise DeployError(f"Arquivo ausente: {COMPOSE_FILE.name}")
    run(["docker", "--version"])
    run(["docker", "compose", "version"])
    run(["docker", "info"])


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def generate_env() -> None:
    if ENV_FILE.exists():
        raise DeployError(".env já existe; remova-o manualmente se quiser regenerar")
    if not ENV_EXAMPLE.exists():
        raise DeployError(".env.example não encontrado")

    secret = secrets.token_urlsafe(48)
    postgres_password = secrets.token_urlsafe(32)
    encryption_key = run_python_fernet_key()

    content = ENV_EXAMPLE.read_text(encoding="utf-8")
    replacements = {
        "ENVIRONMENT=development": "ENVIRONMENT=production",
        "SECRET_KEY=CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET_KEY": f"SECRET_KEY={secret}",
        "ENCRYPTION_KEY=": f"ENCRYPTION_KEY={encryption_key}",
        "POSTGRES_PASSWORD=change-me-postgres-password": f"POSTGRES_PASSWORD={postgres_password}",
        "DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/isp_erp": (
            f"DATABASE_URL=postgresql+psycopg2://postgres:{postgres_password}@db:5432/isp_erp"
        ),
        "REDIS_URL=redis://localhost:6379/0": "REDIS_URL=redis://redis:6379/0",
        "CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:8080": (
            "CORS_ALLOW_ORIGINS=http://localhost:5000,http://127.0.0.1:5000"
        ),
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    ENV_FILE.write_text(content, encoding="utf-8")
    print(".env gerado com chaves locais. Revise integrações reais antes de produção externa.")


def run_python_fernet_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


def validate_env() -> None:
    values = parse_env(ENV_FILE)
    if not values:
        raise DeployError("Arquivo .env ausente. Execute: python deploy.py init-env")

    missing = [key for key in REQUIRED_ENV if not values.get(key)]
    if missing:
        raise DeployError(f"Variáveis obrigatórias ausentes no .env: {', '.join(missing)}")

    if values.get("ENVIRONMENT") != "production":
        raise DeployError("ENVIRONMENT deve ser production para este deploy")
    if values.get("SECRET_KEY", "").startswith("CHANGE_ME") or len(values.get("SECRET_KEY", "")) < 32:
        raise DeployError("SECRET_KEY precisa ser forte e ter pelo menos 32 caracteres")
    if values.get("CORS_ALLOW_ORIGINS") == "*":
        raise DeployError("CORS_ALLOW_ORIGINS não pode ser '*' em produção")
    if "localhost" in values.get("DATABASE_URL", ""):
        raise DeployError("DATABASE_URL do deploy deve apontar para db:5432, não localhost")


def wait_for_url(url: str, *, attempts: int = 30, delay: float = 2.0) -> None:
    last_error = ""
    for _ in range(attempts):
        try:
            req = Request(url, headers={"User-Agent": "open-sgp-deploy"})
            with urlopen(req, timeout=5) as response:
                if 200 <= response.status < 500:
                    return
        except HTTPError as exc:
            if 200 <= exc.code < 500:
                return
            last_error = str(exc)
        except (OSError, URLError) as exc:
            last_error = str(exc)
        except TimeoutError as exc:
            last_error = str(exc)
        time.sleep(delay)
    raise DeployError(f"Endpoint não respondeu: {url}. Último erro: {last_error}")


def deploy(skip_build: bool = False) -> None:
    check_prerequisites()
    validate_env()

    if not skip_build:
        run(compose_cmd("build"))

    run(compose_cmd("up", "-d", "db", "redis"))
    run(compose_cmd("run", "--rm", "migrate"))
    run(compose_cmd("up", "-d", "--remove-orphans"))

    wait_for_url("http://127.0.0.1:8000/health/", attempts=45)
    wait_for_url("http://127.0.0.1:5000/login", attempts=45)
    run(compose_cmd("ps"))

    print("\nDeploy concluído.")
    print("API: http://127.0.0.1:8000/docs")
    print("Painel admin: http://127.0.0.1:5000/login")
    print("Zabbix: externo (configure a URL/API no setup do SGP)")
    print("RADIUS: externo (configure a VM FreeRADIUS para usar as tabelas SQL do SGP)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy local do Open-SGP")
    parser.add_argument("action", nargs="?", default="deploy", choices=["deploy", "init-env", "config", "logs"])
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()

    try:
        if args.action == "init-env":
            generate_env()
        elif args.action == "config":
            validate_env()
            run(compose_cmd("config"))
        elif args.action == "logs":
            run(compose_cmd("logs", "-f", "--tail=200"), check=False)
        else:
            deploy(skip_build=args.skip_build)
        return 0
    except (DeployError, subprocess.CalledProcessError) as exc:
        print(f"\nFalha no deploy: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
