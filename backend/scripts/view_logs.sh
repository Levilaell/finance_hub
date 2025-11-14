#!/bin/bash
# Script para visualizar logs no Railway
# Uso: ./scripts/view_logs.sh [opção]

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
}

case "$1" in
    "errors")
        print_header "Últimos 50 Erros"
        railway run "tail -50 backend/logs/errors.log"
        ;;
    "webhook-errors")
        print_header "Erros de Webhooks"
        railway run "tail -50 backend/logs/webhook_errors.log"
        ;;
    "celery-errors")
        print_header "Erros do Celery"
        railway run "tail -50 backend/logs/celery_errors.log"
        ;;
    "live")
        print_header "Logs em Tempo Real (Ctrl+C para sair)"
        railway logs --follow
        ;;
    "web")
        print_header "Logs do Serviço Web"
        railway logs --service web
        ;;
    "worker")
        print_header "Logs do Worker Celery"
        railway logs --service celery-1
        ;;
    "export")
        FILENAME="logs_$(date +%Y%m%d_%H%M%S).txt"
        print_header "Exportando logs para $FILENAME"
        railway logs > "$FILENAME"
        echo -e "${GREEN}Logs salvos em: $FILENAME${NC}"
        ;;
    "ssh")
        print_header "Conectando ao Container"
        echo -e "${YELLOW}Comandos úteis:${NC}"
        echo "  cd backend/logs"
        echo "  ls -lh"
        echo "  tail -f webhook_errors.log"
        echo ""
        railway run bash
        ;;
    "count")
        print_header "Contagem de Erros"
        railway run "grep -c 'ERROR' backend/logs/errors.log 2>/dev/null || echo '0 (arquivo não existe ou vazio)'"
        ;;
    *)
        echo -e "${YELLOW}Uso: ./scripts/view_logs.sh [opção]${NC}"
        echo ""
        echo "Opções disponíveis:"
        echo "  errors          - Ver últimos 50 erros gerais"
        echo "  webhook-errors  - Ver erros de webhooks"
        echo "  celery-errors   - Ver erros do Celery"
        echo "  live            - Seguir logs em tempo real"
        echo "  web             - Logs do serviço web"
        echo "  worker          - Logs do worker Celery"
        echo "  export          - Exportar logs para arquivo"
        echo "  ssh             - Conectar ao container (requer volume)"
        echo "  count           - Contar total de erros"
        echo ""
        echo -e "${YELLOW}Exemplos:${NC}"
        echo "  ./scripts/view_logs.sh errors"
        echo "  ./scripts/view_logs.sh live"
        echo "  ./scripts/view_logs.sh ssh"
        ;;
esac
