# CLAUDE.md

Guia para agentes de IA (e novos devs) trabalharem no **Open-SGP**. Leia antes de
editar código. Mantenha este arquivo atualizado quando a arquitetura mudar.

---

## 1. O que é

**Open-SGP (Sistema de Gestão de Provedores)** — ERP open-source (MIT) para
Provedores de Internet (ISPs): clientes, contratos, financeiro/fiscal, rede,
suporte, estoque e apps móveis.

Arquitetura: **monólito modular** em FastAPI. Dois processos web sobre o mesmo
banco/código:

- **API REST** (FastAPI) — `app/main.py`, porta `8000`, docs em `/docs`.
- **Painel administrativo** (Flask) — `admin_panel/app.py`, porta `5000`.
- **Worker** de comunicação (fila Redis) — `app/workers/communication_worker.py`.

## 2. Stack

| Camada | Tecnologia |
|--------|-----------|
| Linguagem | Python 3.10+ (tooling/CI mira **3.11**) |
| API | FastAPI 0.115, Uvicorn/Gunicorn |
| Painel | Flask 3 |
| ORM | SQLAlchemy 2.0 (engine **síncrono** — ver §9) |
| Banco | PostgreSQL 16 (prod) · SQLite (dev/test) |
| Migrações | Alembic |
| Cache/Fila | Redis |
| Auth | OAuth2 + JWT (PyJWT), RBAC, 2FA TOTP (pyotp) opt-in |
| Rede | routeros-api (Mikrotik), paramiko (SSH/OLT), pyzabbix |
| Fiscal | lxml, signxml, zeep, cryptography (NF-e/NFS-e, SEFAZ) |
| Observabilidade | structlog, sentry-sdk, métricas Prometheus |
| Testes | pytest, pytest-cov, httpx, Faker |
| Lint/format | black, isort, ruff — **line-length 120** |

## 3. Comandos essenciais

```bash
# Setup local
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                               # editar SECRET_KEY etc.

# Banco (Alembic é a única fonte de verdade do schema)
alembic upgrade head
alembic revision -m "descricao" --autogenerate     # nova migração
alembic history                                    # ver grafo de revisões

# Rodar a API (factory)
uvicorn app.main:create_app --reload --factory
# ou app pré-criado:
uvicorn app.main:app --reload

# Painel admin (Flask)
flask --app admin_panel.app run --port 5000

# Worker de comunicação
python -m app.workers.communication_worker

# Testes
pytest                          # tudo (config em pytest.ini / pyproject.toml)
pytest tests/test_rbac_permissions.py -v
pytest -m "not slow"            # markers: slow, integration, unit, requires_redis, requires_db

# Lint / format
ruff check app && black app && isort app

# Docker (sobe api, admin, worker, postgres, redis)
docker-compose up -d --build
```

> Em testes, `ENVIRONMENT=testing` usa SQLite (`isp_erp_test.db`) e cria tabelas
> automaticamente. Fora de testes, a criação automática só ocorre com
> `AUTO_CREATE_TABLES=true`.

## 4. Layout do repositório

```
app/
  main.py                 # cria FastAPI, registra ~41 routers, seed RBAC
  core/                   # infra transversal
    config.py             # Settings (env vars) + validações de produção
    database.py           # Base, engine, SessionLocal, import_all_models()
    dependencies.py       # get_db, get_current_user, require_permissions (cache Redis)
    security.py           # hash de senha, JWT encode/decode, blacklist de token
    encryption.py         # criptografia de segredos (gateways, certificados)
    logging.py            # structlog + Sentry
  shared/                 # utilitários de domínio reutilizáveis
    money.py              # helpers de Decimal/centavos (NUNCA usar float p/ dinheiro)
    boleto.py, cnab.py    # boleto e CNAB 240/400
    validators.py         # CPF/CNPJ (validate-docbr), etc.
    models.py, schemas.py, utils.py
  modules/<modulo>/       # um pacote por domínio (ver §5)
  workers/                # communication_worker, backup_worker
admin_panel/              # painel Flask (app.py monolítico + templates/ + static/)
alembic/versions/         # 36 migrações (0001 … 0035)
scripts/                  # seed_database, seed_demo_data, setup_zabbix, setup_radius_automation, kill_locks…
tests/                    # pytest (conftest.py + test_*.py)
radius/                   # assets do FreeRADIUS
docs/SPRINTS.md           # histórico de sprints de hardening
docker-compose.yml        # dev (api+admin+worker+db+redis)
docker-compose.prod.yml   # produção
deploy.py, manage-docker.sh
```

~286 arquivos `.py`, ~33k linhas. Há `.db` SQLite versionados no repo
(`isp_erp.db`, `isp_erp_test.db`, `test.db`) — são dados de dev/teste, não toque
sem motivo.

## 5. Anatomia de um módulo

Cada módulo em `app/modules/<nome>/` segue o mesmo padrão de 4 arquivos:

```
models.py    # modelos SQLAlchemy (tabelas)
schemas.py   # schemas Pydantic (entrada/saída da API)
service.py   # regra de negócio (chamada pelas rotas)
routes.py    # APIRouter; cada rota declara a permissão exigida
```

Arquivos opcionais conforme o módulo: `dashboard.py`, `pdf_generator.py`
(billing), `vendors/` (network: mikrotik, olt, radius, vsol, zabbix), subpacotes
(`billing/gateway/` com `webhooks.py`).

**Convenção de cabeçalho** — todo arquivo começa com docstring:

```python
"""
Arquivo: app/modules/clients/routes.py
Responsabilidade: <o que faz>
Integrações: <core.*, modules.* de que depende>
"""
```

Mantenha esse cabeçalho ao criar/editar arquivos.

### Módulos registrados (prefixo da rota)

`auth` (`/api/auth`, **público**) · `users` · `roles` · `permissions` ·
`administration/*` (`/api/admin/...`: pops, nas, variables, backups, setup,
finance, email-config, email-servers, employees, operation-points,
payment-gateways) · `anatel` · `clients` · `plans` · `support` · `contracts` ·
`contract-templates` · `billing` (+ `billing/gateway` + webhooks) · `cashier` ·
`discounts` · `due-dates` · `fiscal` · `network` · `notifications` ·
`contract-tech` · `service-orders` · `communication` · `reports` · `stock` ·
`customer` (customer_app) · `technician` (technician_app) · `referrals` ·
`viability` · `health` (**público**) · `audit`.

> ⚠️ Existe `app/modules/tech_app/` (só `service.py`/`schemas.py`, sem
> `__init__`/`routes`) que **não é registrado** — o módulo de técnico ativo é
> `technician_app`. Não confunda os dois.

## 6. Padrões ao adicionar funcionalidade

**Nova rota num módulo existente:** adicione no `routes.py`, protegida por
permissão explícita:

```python
@router.post("/", dependencies=[Depends(require_permissions("clients.create"))])
def create(payload: ClientCreate, db: Session = Depends(get_db)):
    ...
```

**Nova permissão:** o código (ex.: `"clients.create"`) precisa estar no seed em
`app/main.py` → `seed_reference_data()` (lista `base_perms`). Há teste estático
(`tests/test_rbac_permissions.py`) que falha se uma rota usa permissão fora do
seed — rode-o.

**Novo módulo:** crie `models/schemas/service/routes`, registre o router em
`app/main.py` (`include_router(..., prefix="/api/...", dependencies=protected)`)
e adicione o `import` dos modelos em `app/core/database.py → import_all_models()`
(senão o Alembic autogenerate e os relacionamentos não enxergam as tabelas).

**Mudança de schema:** sempre via migração Alembic. Não há `ALTER TABLE` em
runtime (`ensure_required_columns` foi neutralizado de propósito).

**Dinheiro:** use `Decimal` e os helpers de `app/shared/money.py`; colunas
monetárias são `Numeric(12,2)`. Há teste que proíbe retornar `Float` monetário.

## 7. Segurança / RBAC

- Todas as rotas sob `/api/*` exigem JWT (`get_current_user`), **exceto** `auth`,
  `health` e os webhooks de gateway.
- Autorização por permissão: `Depends(require_permissions("modulo.acao"))`.
  Permissões do usuário são cacheadas no Redis por 5 min (`user:{id}:permissions`).
- Logout usa blacklist de token no Redis (`TOKEN_BLACKLIST_TTL`).
- `seed_reference_data()` cria as permissões e a role `admin` (com todas). **Não**
  cria credenciais padrão. O admin inicial é opt-in:
  `BOOTSTRAP_ADMIN_ENABLED=true` + `BOOTSTRAP_ADMIN_PASSWORD`.
- Registro público fechado por padrão (`PUBLIC_REGISTRATION_ENABLED=false`).
- Produção valida: `SECRET_KEY` ≠ `change-me` e ≥32 chars; `CORS_ALLOW_ORIGINS`
  não pode ser `*` (validadores em `config.py`).

## 8. Configuração (.env)

Tudo via env vars lidas em `app/core/config.py` (`settings` singleton). Use
`.env.example` como base. Principais grupos: ambiente/segurança
(`ENVIRONMENT`, `SECRET_KEY`, `JWT_EXPIRATION_MINUTES`), banco (`DATABASE_URL`,
`TEST_DATABASE_URL`), `REDIS_URL`, `CORS_ALLOW_ORIGINS`, SMTP, SMS/WhatsApp
(gateway, Twilio, Gupshup, Zenvia), fiscal/SEFAZ (`A1_CERT_*`,
`SEFAZ_ENVIRONMENT`, `SEFAZ_UF`), Sentry, logging, feature flags
(`FEATURE_2FA_*`), e bootstrap (`AUTO_CREATE_TABLES`, `BOOTSTRAP_ADMIN_*`).

`environment` válido: `development | production | testing | staging`.

## 9. Pegadinhas conhecidas

- **ORM síncrono, não async.** O README diz "SQLAlchemy 2.0 Async", mas
  `database.py` usa `create_engine`/`Session` **síncronos** e as rotas são `def`
  comuns. Escreva código síncrono; não introduza `AsyncSession` sem alinhar.
- **Alembic é a fonte de verdade do schema.** `Base.metadata.create_all` só roda
  em testes ou com `AUTO_CREATE_TABLES=true`. Toda mudança de tabela = migração.
- **Registre modelos** novos em `import_all_models()` — senão autogenerate perde
  tabelas e relacionamentos quebram.
- **Permissões fora do seed quebram o teste estático** de RBAC.
- **Produção separa serviços:** Zabbix e FreeRADIUS rodam em VMs dedicadas (não no
  docker-compose). O FreeRADIUS lê as tabelas SQL do SGP (`radcheck`, `radreply`,
  `radusergroup`, `radacct`, `nas`).
- **`admin_panel/app.py` é monolítico** (refatoração em blueprints é pendência
  conhecida — ver `docs/SPRINTS.md`).

## 10. Estado do projeto

`docs/SPRINTS.md` registra 6 sprints de hardening já aplicadas (segurança/RBAC,
schema/migrações, painel admin/CSRF, financeiro em `Decimal`, observabilidade).
Pendências em aberto: quebrar o painel Flask em blueprints, validar CNAB/boleto
com fixtures reais por banco, e tornar o Redis fail-closed para logout em
produção. Versão atual: `0.1.0`, branch `main`.
