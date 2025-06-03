#!/bin/bash

# Deploy Script per Paguro Chatbot - Villa Celi
# Gestisce deployment, avvio, stop e manutenzione del sistema Docker

set -euo pipefail

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurazione
PROJECT_NAME="paguro-chatbot"
COMPOSE_FILE="docker-compose.yml"
COMPOSE_FILE_SIMPLE="docker-compose.simple.yml"
ENV_FILE=".env"

# Auto-detect del file compose da usare
if [ -f "$COMPOSE_FILE_SIMPLE" ]; then
    COMPOSE_FILE="$COMPOSE_FILE_SIMPLE"
    echo -e "${BLUE}ℹ️ Usando $COMPOSE_FILE_SIMPLE per development${NC}"
elif [ -f "$COMPOSE_FILE" ]; then
    echo -e "${BLUE}ℹ️ Usando $COMPOSE_FILE per production${NC}"
else
    echo -e "${RED}❌ Nessun file docker-compose trovato!${NC}"
    exit 1
fi

# Funzioni utility
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Verifica prerequisiti
check_requirements() {
    log "Verificando prerequisiti..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker non è installato"
    fi
    
    if ! docker compose version &> /dev/null; then
        error "Docker Compose plugin non è installato"
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "File $COMPOSE_FILE non trovato"
    fi
    
    # ENV file è opzionale per Paguro
    if [ ! -f "$ENV_FILE" ]; then
        warning "File $ENV_FILE non trovato (opzionale)"
    fi
    
    success "Prerequisiti verificati"
}

# Funzione di help
show_help() {
    echo "🐚 Paguro Chatbot - Script di Deploy per Villa Celi"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandi disponibili:"
    echo "  start         - Avvia tutti i servizi Paguro"
    echo "  stop          - Ferma tutti i servizi"
    echo "  restart       - Riavvia tutti i servizi"
    echo "  status        - Mostra stato dei servizi"
    echo "  logs          - Mostra logs in tempo reale"
    echo "  logs-api      - Mostra logs solo dell'API Paguro"
    echo "  logs-ollama   - Mostra logs solo di Ollama"
    echo "  build         - Ricompila le immagini"
    echo "  update        - Aggiorna e riavvia"
    echo "  backup        - Esegui backup manuale database"
    echo "  clean         - Pulisci containers e volumi"
    echo "  health        - Verifica salute del sistema"
    echo "  config        - Mostra configurazione"
    echo "  db-shell      - Apri shell SQLite database"
    echo "  db-backup     - Backup database"
    echo "  db-restore    - Restore database"
    echo "  help          - Mostra questo help"
    echo ""
}

# Avvia servizi
start_services() {
    log "Avviando servizi $PROJECT_NAME..."
    docker compose -f "$COMPOSE_FILE" up -d
    
    log "Attendendo che i servizi siano pronti..."
    sleep 10
    
    # Verifica che i servizi siano up
    if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        success "Servizi avviati con successo"
        show_status
    else
        error "Errore nell'avvio dei servizi"
    fi
}

# Ferma servizi
stop_services() {
    log "Fermando servizi $PROJECT_NAME..."
    docker compose -f "$COMPOSE_FILE" down
    success "Servizi fermati"
}

# Riavvia servizi
restart_services() {
    log "Riavviando servizi $PROJECT_NAME..."
    docker compose -f "$COMPOSE_FILE" restart
    success "Servizi riavviati"
}

# Mostra stato migliorato
show_status() {
    log "Stato servizi $PROJECT_NAME:"
    echo ""
    docker compose -f "$COMPOSE_FILE" ps
    echo ""
    
    # Test connessione API Paguro
    log "Test connessione API Paguro..."
    if curl -s -f http://localhost:5000/api/health > /dev/null; then
        local health_response=$(curl -s http://localhost:5000/api/health)
        success "🐚 Paguro API raggiungibile"
        echo "    Response: $health_response"
    else
        warning "🐚 Paguro API non raggiungibile"
    fi
    
    # Test Ollama
    log "Test Ollama AI engine..."
    if curl -s -f http://localhost:11434/api/version > /dev/null; then
        success "🤖 Ollama raggiungibile"
    else
        warning "🤖 Ollama non raggiungibile"
    fi
    
    # Stato containers
    echo ""
    log "Risorse Docker:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker compose -f "$COMPOSE_FILE" ps -q) 2>/dev/null || warning "Impossibile ottenere statistiche"
}

# Mostra logs
show_logs() {
    local service=${1:-""}
    if [ -n "$service" ]; then
        log "Logs di $service:"
        docker compose -f "$COMPOSE_FILE" logs -f "$service"
    else
        log "Logs di tutti i servizi:"
        docker compose -f "$COMPOSE_FILE" logs -f
    fi
}

# Build immagini
build_images() {
    log "Ricompilando immagini..."
    docker compose -f "$COMPOSE_FILE" build --no-cache
    success "Immagini ricompilate"
}

# Update e restart
update_system() {
    log "Aggiornamento sistema..."
    
    # Pull nuove immagini base
    docker compose -f "$COMPOSE_FILE" pull
    
    # Rebuild custom images
    build_images
    
    # Restart services
    docker compose -f "$COMPOSE_FILE" up -d
    
    success "Sistema aggiornato"
}

# Backup database
backup_database() {
    log "Eseguendo backup database Paguro..."
    
    local container_name=$(docker compose -f "$COMPOSE_FILE" ps -q paguro-api)
    if [ -z "$container_name" ]; then
        error "Container Paguro API non in esecuzione"
    fi
    
    local backup_dir="./backups"
    local backup_file="affitti_backup_$(date +%Y%m%d_%H%M%S).db"
    
    mkdir -p "$backup_dir"
    
    if docker exec "$container_name" test -f /app/data/affitti2025.db; then
        docker cp "$container_name:/app/data/affitti2025.db" "$backup_dir/$backup_file"
        success "Backup completato: $backup_dir/$backup_file"
    else
        error "Database non trovato nel container"
    fi
}

# Restore database
restore_database() {
    if [ -z "$1" ]; then
        error "Specificare il file di backup da ripristinare"
    fi
    
    local backup_file="$1"
    if [ ! -f "$backup_file" ]; then
        error "File di backup non trovato: $backup_file"
    fi
    
    log "Ripristinando database da $backup_file..."
    
    local container_name=$(docker compose -f "$COMPOSE_FILE" ps -q paguro-api)
    if [ -z "$container_name" ]; then
        error "Container Paguro API non in esecuzione"
    fi
    
    # Backup current database
    backup_database
    
    # Restore
    docker cp "$backup_file" "$container_name:/app/data/affitti2025.db"
    docker compose -f "$COMPOSE_FILE" restart paguro-api
    
    success "Database ripristinato"
}

# Database shell
database_shell() {
    log "Aprendo shell database SQLite Paguro..."
    
    local container_name=$(docker compose -f "$COMPOSE_FILE" ps -q paguro-api)
    if [ -z "$container_name" ]; then
        error "Container Paguro API non in esecuzione"
    fi
    
    echo -e "${YELLOW}Comandi SQLite utili:${NC}"
    echo ".tables                     # Mostra tabelle"
    echo ".schema appartamenti        # Struttura tabella"
    echo "SELECT * FROM appartamenti; # Mostra tutti i record"
    echo "SELECT appartamento, COUNT(*) FROM appartamenti GROUP BY appartamento; # Prenotazioni per appartamento"
    echo ".quit                       # Esci"
    echo ""
    
    docker exec -it "$container_name" sqlite3 /app/data/affitti2025.db
}

# Pulizia sistema
clean_system() {
    warning "Questa operazione rimuoverà tutti i containers e le immagini di $PROJECT_NAME"
    read -p "Continuare? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Pulizia sistema..."
        docker compose -f "$COMPOSE_FILE" down -v --rmi all
        docker system prune -f
        success "Sistema pulito"
    else
        log "Operazione annullata"
    fi
}

# Health check completo
health_check() {
    log "Verifica salute del sistema Paguro..."
    echo ""
    
    # Status containers
    echo "🐳 Container Status:"
    docker compose -f "$COMPOSE_FILE" ps
    echo ""
    
    # API Health
    echo "🐚 Paguro API Health Check:"
    if response=$(curl -s http://localhost:5000/api/health); then
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        success "🐚 Paguro API funzionante"
    else
        warning "🐚 Paguro API non risponde"
    fi
    echo ""
    
    # Ollama Status
    echo "🤖 Ollama AI Status:"
    if curl -s http://localhost:11434/api/version > /dev/null; then
        local ollama_version=$(curl -s http://localhost:11434/api/version)
        echo "$ollama_version"
        success "🤖 Ollama funzionante"
    else
        warning "🤖 Ollama non risponde"
    fi
    echo ""
    
    # Database check
    echo "🗄️ Database Check:"
    local container_name=$(docker compose -f "$COMPOSE_FILE" ps -q paguro-api)
    if [ -n "$container_name" ] && docker exec "$container_name" test -f /app/data/affitti2025.db; then
        local record_count=$(docker exec "$container_name" sqlite3 /app/data/affitti2025.db "SELECT COUNT(*) FROM appartamenti;" 2>/dev/null || echo "0")
        success "Database OK - $record_count prenotazioni"
    else
        warning "Database non accessibile"
    fi
    echo ""
    
    # Disk Usage
    echo "💾 Disk Usage Volumi:"
    docker system df
    echo ""
    
    # Logs recenti
    echo "📝 Ultimi errori nei logs:"
    docker compose -f "$COMPOSE_FILE" logs --tail=10 2>/dev/null | grep -i error || echo "Nessun errore recente"
}

# Mostra configurazione
show_config() {
    log "Configurazione attuale Paguro:"
    echo ""
    
    echo "📄 File Compose: $COMPOSE_FILE"
    echo ""
    
    if [ -f "$ENV_FILE" ]; then
        echo "📄 Variabili d'ambiente (.env):"
        grep -v '^#' "$ENV_FILE" | grep -v '^$' | head -20
        echo ""
    fi
    
    echo "🐳 Servizi Docker Compose:"
    docker compose -f "$COMPOSE_FILE" config --services
    echo ""
    
    echo "📁 Volumi Docker:"
    docker volume ls | grep "$PROJECT_NAME" || echo "Nessun volume specifico trovato"
    echo ""
    
    echo "🌐 Porte esposte:"
    echo "  - Paguro API: http://localhost:5000"
    echo "  - Ollama: http://localhost:11434"
    echo "  - Health Check: http://localhost:5000/api/health"
}

# Main
main() {
    case "${1:-help}" in
        "start")
            check_requirements
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            check_requirements
            restart_services
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "logs-api")
            show_logs "paguro-api"
            ;;
        "logs-ollama")
            show_logs "ollama"
            ;;
        "build")
            check_requirements
            build_images
            ;;
        "update")
            check_requirements
            update_system
            ;;
        "backup")
            backup_database
            ;;
        "clean")
            clean_system
            ;;
        "health")
            health_check
            ;;
        "config")
            show_config
            ;;
        "db-shell")
            database_shell
            ;;
        "db-backup")
            backup_database
            ;;
        "db-restore")
            shift
            restore_database "$@"
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Esegui main con tutti gli argomenti
main "$@"
