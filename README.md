# Open-SGP (Sistema de Gestão de Provedores)

O **Open-SGP** é um ERP (Enterprise Resource Planning) completo e open-source desenvolvido para Provedores de Internet (ISPs). Ele oferece uma solução robusta para gestão de clientes, financeira, técnica e operacional, construída com tecnologias modernas e escaláveis.

## 🚀 Visão Geral

O sistema é construído sobre uma arquitetura de microsserviços modulares (monólito modular) utilizando **FastAPI** e **Python**, garantindo alta performance e facilidade de manutenção.

### Principais Características
- **Gestão de Clientes**: CRM completo com múltiplos endereços, contatos e histórico.
- **Financeiro & Fiscal**: Emissão de boletos, remessa/retorno CNAB, Nota Fiscal (Modelos 21/22).
- **Rede & Técnico**: Integração com Mikrotik, OLTs, Radius, gestão de IPAM (IP Pools) e monitoramento.
- **Suporte**: Sistema de Tickets (Helpdesk) com SLA e gestão de ocorrências.
- **Estoque**: Controle multi-almoxarifado, movimentações, compras e comodato.
- **Comunicação**: Envio de SMS, E-mail e WhatsApp (Twilio, Gupshup, Zenvia).
- **Apps Móveis**: APIs prontas para aplicativos de Cliente e Técnico.

## 🛠️ Stack Tecnológica

- **Backend**: Python 3.10+, FastAPI
- **Banco de Dados**: PostgreSQL (Produção), SQLite (Dev/Test)
- **ORM**: SQLAlchemy 2.0 (Async)
- **Cache/Fila**: Redis
- **Autenticação**: OAuth2 com JWT
- **Migrações**: Alembic

---

## 📦 Módulos do Sistema

### 1. Autenticação & Usuários (`auth`, `users`, `roles`, `permissions`)
Gerenciamento de acesso baseado em funções (RBAC).
- **Auth**: Login via JWT, Refresh Token, 2FA, Rate Limiting (Proteção contra Brute-force).
- **Users**: Gestão de operadores do sistema.
- **Roles/Permissions**: Criação de perfis de acesso granulares (ex: "Técnico", "Financeiro").

### 2. Administrativo (`administration`)
Configurações globais do provedor.
- **POPs**: Pontos de Presença (locais físicos).
- **NAS**: Concentradores de acesso (Mikrotik, Huawei, etc.) autenticados via Radius.
- **Financeiro**: Configuração de Empresas, Contas Bancárias (Portadores) e Parâmetros de Juros/Multa.
- **Backups**: Rotinas de backup do sistema.

### 3. Core Business (`clients`, `plans`, `contracts`, `service_orders`)
O coração do negócio.
- **Clientes**: Cadastro PF/PJ, validação de CPF/CNPJ.
- **Planos**: Definição de velocidades, preços, fidelidade e configurações de Burst.
- **Contratos**: Vínculo Cliente-Plano. Gerencia ciclo de vida (Ativo, Suspenso, Cancelado).
- **Ordens de Serviço (OS)**: Instalação, Reparo, Retirada. Agendamento e checklist técnico.

### 4. Financeiro & Fiscal (`billing`, `fiscal`)
- **Faturamento**: Geração de faturas (Títulos) recorrentes.
- **Integração Bancária**: Geração de arquivos de Remessa e processamento de Retorno (CNAB 400/240).
- **Fiscal**: Emissão de Notas Fiscais de Telecomunicações (Modelo 21/22) e Integração SEFAZ.
- **Gateways**: Integração com gateways de pagamento para Cartão/Pix.

### 5. Técnico & Rede (`network`, `contract_tech`, `health`)
- **Radius**: Autenticação PPPoE/Hotspot (FreeRADIUS schema).
- **IPAM**: Gestão de Pools de IP (IPv4/IPv6), CGNAT e alocação dinâmica/estática.
- **Provisionamento**: Configuração automática de equipamentos (CPEs/ONUs).
- **Diagnóstico**: Histórico de sinal óptico, testes de velocidade e logs de conexão.
- **Monitoramento**: Integração com Zabbix para status de dispositivos.

### 6. Suporte & Atendimento (`support`, `communication`)
- **Helpdesk**: Abertura e acompanhamento de chamados.
- **SLA**: Controle de tempos de atendimento e solução.
- **Ocorrências**: Registro de falhas massivas ou manutenções programadas.
- **Mensageria**: Filas de envio para notificações automáticas (Fatura disponível, Agendamento de OS).

### 7. Estoque (`stock`)
- **Controle de Materiais**: Entrada e saída de equipamentos (Cabos, ONUs, Roteadores).
- **Comodato**: Rastreio de equipamentos emprestados aos clientes.
- **Compras & Fornecedores**: Gestão de aquisições.

---

## 🚀 Como Rodar

### Pré-requisitos
- Docker & Docker Compose
- Python 3.10+ (para execução local sem Docker)

### Via Docker (Recomendado)

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/open-sgp.git
cd open-sgp

# Crie o arquivo .env
cp .env.example .env

# Suba os containers
docker-compose up -d --build
```

A API estará disponível em: `http://localhost:8000/docs`

### Arquitetura de Produção

Para melhor performance e estabilidade operacional, o Docker do Open-SGP deve executar apenas os serviços do SGP: API, painel administrativo, worker, PostgreSQL e Redis.

- **Zabbix**: rode em uma VM dedicada. Configure a URL da API, usuário, senha, templates e grupos no setup de monitoramento do SGP.
- **FreeRADIUS**: rode em uma VM dedicada. A VM deve acessar as tabelas SQL do SGP (`radcheck`, `radreply`, `radusergroup`, `radacct`, `nas`) no PostgreSQL do SGP ou em uma réplica dedicada.
- **Docker Compose**: não sobe mais `zabbix-server`, `zabbix-web` nem container RADIUS.

### Execução Local

1.  **Crie um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate     # Windows
    ```

2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure o banco de dados:**
    ```bash
    # Edite o .env com suas credenciais do Postgres ou use SQLite (padrão dev)
    alembic upgrade head
    ```

4.  **Inicie o servidor:**
    ```bash
    uvicorn app.main:create_app --reload
    ```

## ⚙️ Variáveis de Ambiente (.env)

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `ENVIRONMENT` | Ambiente (development, production) | `development` |
| `DATABASE_URL` | String de conexão SQLAlchemy | `postgresql://...` |
| `SECRET_KEY` | Chave para assinatura de tokens JWT | `change-me` |
| `REDIS_URL` | URL do servidor Redis | `redis://localhost:6379/0` |
| `SMTP_HOST` | Servidor SMTP para e-mails | `localhost` |
| `SMS_GATEWAY_URL` | Endpoint para envio de SMS | - |

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, leia o guia de contribuição antes de submeter um Pull Request.

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.
