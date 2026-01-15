#!/bin/bash
#
# manage-docker.sh - Script de gerenciamento do Docker para ISP ERP
# Uso: ./manage-docker.sh [comando]
#

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Comandos
case "${1:-help}" in
    start)
        echo_info "Iniciando containers..."
        docker-compose up -d
        echo_info "Containers iniciados!"
        echo_info "API: http://localhost:8000"
        echo_info "Admin Panel: http://localhost:5000"
        echo_info "Docs: http://localhost:8000/docs"
        ;;

    stop)
        echo_info "Parando containers..."
        docker-compose down
        echo_info "Containers parados!"
        ;;

    restart)
        echo_info "Reiniciando containers..."
        docker-compose restart
        echo_info "Containers reiniciados!"
        ;;

    rebuild)
        echo_warn "Rebuilding containers (pode demorar)..."
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        echo_info "Rebuild completo!"
        ;;

    rebuild-fast)
        echo_info "Rebuilding containers (usando cache)..."
        docker-compose down
        docker-compose build
        docker-compose up -d
        echo_info "Rebuild completo!"
        ;;

    logs)
        echo_info "Mostrando logs (Ctrl+C para sair)..."
        docker-compose logs -f
        ;;

    logs-api)
        echo_info "Logs da API (Ctrl+C para sair)..."
        docker-compose logs -f api
        ;;

    logs-admin)
        echo_info "Logs do Admin Panel (Ctrl+C para sair)..."
        docker-compose logs -f admin
        ;;

    status)
        echo_info "Status dos containers:"
        docker-compose ps
        ;;

    clean)
        echo_warn "Limpando containers, volumes e images..."
        read -p "Tem certeza? Isso vai apagar TODOS os dados do banco! (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]
        then
            docker-compose down -v
            docker system prune -f
            echo_info "Limpeza completa!"
        else
            echo_info "Cancelado."
        fi
        ;;

    shell-api)
        echo_info "Abrindo shell no container da API..."
        docker exec -it isp_erp_api /bin/bash
        ;;

    shell-admin)
        echo_info "Abrindo shell no container do Admin..."
        docker exec -it isp_erp_admin /bin/bash
        ;;

    shell-db)
        echo_info "Abrindo psql no banco de dados..."
        docker exec -it isp_erp_db psql -U postgres -d isp_erp
        ;;

    migrate)
        echo_info "Executando migrations..."
        docker exec -it isp_erp_api alembic upgrade head
        echo_info "Migrations executadas!"
        ;;

    migrate-create)
        if [ -z "$2" ]; then
            echo_error "Uso: $0 migrate-create <nome_da_migration>"
            exit 1
        fi
        echo_info "Criando migration: $2"
        docker exec -it isp_erp_api alembic revision --autogenerate -m "$2"
        ;;

    test)
        echo_info "Executando testes..."
        docker exec -it isp_erp_api pytest
        ;;

    test-cov)
        echo_info "Executando testes com coverage..."
        docker exec -it isp_erp_api pytest --cov=isp_erp --cov-report=html
        echo_info "Relatório gerado em htmlcov/index.html"
        ;;

    backup-db)
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        echo_info "Criando backup do banco: $BACKUP_FILE"
        docker exec isp_erp_db pg_dump -U postgres isp_erp > "$BACKUP_FILE"
        echo_info "Backup criado: $BACKUP_FILE"
        ;;

    restore-db)
        if [ -z "$2" ]; then
            echo_error "Uso: $0 restore-db <arquivo.sql>"
            exit 1
        fi
        echo_warn "Restaurando banco de dados de: $2"
        read -p "Tem certeza? Isso vai sobrescrever os dados atuais! (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]
        then
            docker exec -i isp_erp_db psql -U postgres -d isp_erp < "$2"
            echo_info "Banco restaurado!"
        else
            echo_info "Cancelado."
        fi
        ;;

    health)
        echo_info "Verificando saúde dos serviços..."
        echo ""
        echo "API Health:"
        curl -s http://localhost:8000/health | python -m json.tool || echo_error "API não está respondendo"
        echo ""
        echo "API Readiness:"
        curl -s http://localhost:8000/health/readiness | python -m json.tool || echo_error "API não está pronta"
        echo ""
        echo "Admin Panel:"
        curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:5000/ || echo_error "Admin Panel não está respondendo"
        ;;

    update)
        echo_info "Atualizando sistema..."
        git pull
        docker-compose down
        docker-compose build
        docker exec -it isp_erp_api alembic upgrade head
        docker-compose up -d
        echo_info "Sistema atualizado!"
        ;;

    help|*)
        echo "ISP ERP - Docker Management Script"
        echo ""
        echo "Uso: $0 [comando]"
        echo ""
        echo "Comandos disponíveis:"
        echo "  start          - Inicia os containers"
        echo "  stop           - Para os containers"
        echo "  restart        - Reinicia os containers"
        echo "  rebuild        - Rebuild completo (sem cache)"
        echo "  rebuild-fast   - Rebuild rápido (com cache)"
        echo "  logs           - Mostra logs de todos containers"
        echo "  logs-api       - Mostra logs da API"
        echo "  logs-admin     - Mostra logs do Admin Panel"
        echo "  status         - Mostra status dos containers"
        echo "  clean          - Limpa containers, volumes e images"
        echo ""
        echo "  shell-api      - Abre shell no container da API"
        echo "  shell-admin    - Abre shell no container do Admin"
        echo "  shell-db       - Abre psql no banco de dados"
        echo ""
        echo "  migrate        - Executa migrations"
        echo "  migrate-create - Cria nova migration"
        echo "  test           - Executa testes"
        echo "  test-cov       - Executa testes com coverage"
        echo ""
        echo "  backup-db      - Faz backup do banco de dados"
        echo "  restore-db     - Restaura banco de dados"
        echo "  health         - Verifica saúde dos serviços"
        echo "  update         - Atualiza sistema (git pull + rebuild + migrate)"
        echo ""
        echo "  help           - Mostra esta ajuda"
        ;;
esac
