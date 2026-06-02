# Plano de Sprints Prioritarias

## Sprint 1 - Hardening inicial

Status: aplicada.

- Remover credenciais padrao e login demonstrativo.
- Proteger endpoints sensiveis por autenticacao.
- Tornar criacao automatica de tabelas opt-in.
- Criar bootstrap de administrador apenas quando configurado explicitamente.
- Endurecer configuracao Docker contra `SECRET_KEY` padrao e CORS aberto.
- Adicionar regressao minima para endpoint sensivel sem token.

## Sprint 2 - Schema e migracoes

Status: aplicada parcialmente; validacao completa depende das dependencias do projeto instaladas.

- Resolver branch duplicada das migracoes `0022`.
- Remover alteracoes de schema em runtime de `ensure_required_columns`.
- Garantir que Alembic importe todos os modelos no `env.py`.
- Adicionar teste de integridade do grafo de revisoes.
- Validar `alembic upgrade head` em banco limpo quando o ambiente tiver dependencias instaladas.

## Sprint 3 - RBAC e superficie de API

Status: aplicada nos modulos criticos.

- Fechar registro publico por padrao com `PUBLIC_REGISTRATION_ENABLED=false`.
- Inventariar endpoints sensiveis de clientes, contratos, planos, usuarios, permissoes, financeiro, rede, suporte e ordens de servico.
- Trocar protecao generica de leitura por permissoes explicitas nos modulos criticos.
- Corrigir lacunas de permissoes usadas nas rotas.
- Adicionar teste estatico para garantir que permissoes usadas em rotas estejam no seed.
- Adicionar regressao para registro publico bloqueado por padrao.

## Sprint 4 - Painel administrativo

Status: aplicada parcialmente; refatoracao em blueprints fica para sprint dedicada.

- Adicionar protecao CSRF central para formularios e chamadas `fetch`.
- Expor helper `window.postAction` para acoes administrativas mutaveis.
- Expandir protecao de sessao para `/admin`, `/communication`, `/network` e `/api` do painel Flask.
- Remover GET implicito de rotas mutaveis de backup, rede, ocorrencias e criacao de OS.
- Atualizar templates que navegavam para acoes mutaveis para enviar POST.
- Adicionar testes estaticos para CSRF e para impedir rotas mutaveis com GET implicito.
- Quebrar `admin_panel/app.py` em blueprints permanece como proxima etapa de manutencao.

## Sprint 5 - Financeiro e fiscal

Status: aplicada parcialmente nos fluxos monetarios centrais de billing.

- Adicionar helper central de dinheiro com `Decimal` e arredondamento em centavos.
- Migrar colunas monetarias de billing e gateway para `Numeric(12, 2)`.
- Ajustar schemas financeiros centrais para `Decimal`.
- Remover URL placeholder de boleto e apontar para endpoint interno de PDF.
- Corrigir calculos de pagamento, retorno, ajustes, carnê e CNAB para usar `Decimal` internamente.
- Adicionar migração `0028_billing_decimal_money`.
- Adicionar testes estaticos para impedir retorno de `Float` monetario e URL placeholder.
- Revisar transacoes de lote com rollback atomico permanece como proxima etapa.
- Validar CNAB/boleto com fixtures reais por banco/layout permanece como proxima etapa.

## Sprint 6 - Observabilidade e operacao

Status: aplicada parcialmente; validacao completa depende das dependencias do projeto instaladas.

- Adicionar configuracao central de logging estruturado com `structlog`.
- Inicializar Sentry quando `SENTRY_DSN` estiver configurado.
- Adicionar middleware de request log com `X-Request-ID`.
- Corrigir readiness para usar SQLAlchemy `text("SELECT 1")` e responder HTTP 503 quando dependencias falham.
- Expor metricas basicas em formato Prometheus text exposition.
- Registrar excecoes do worker de comunicacao em vez de silenciar falhas.
- Atualizar CI para Python 3.11, actions atuais, cache pip, `alembic upgrade head` e testes.
- Adicionar testes estaticos de observabilidade/CI.
- Tornar Redis fail-closed para logout em producao permanece como proxima etapa de seguranca operacional.
