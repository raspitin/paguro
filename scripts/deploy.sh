c#!/bin/bash

# Deploy Script per Paguro Chatbot - Villa Celi AGGIORNATO
# CORRETTO: Usa 'docker compose' invece di 'docker-compose'

set -euo pipefail

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configurazione AGGIORNATA
PROJECT_NAME="paguro-villaceli"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# URLs Villa Celi
FRONTEND_URL="https://www.villaceli.it"
API_PROD_URL="https://api.viamerano24.it/api"
API_LOCAL_URL="http://localhost:5000/api"

# Funzioni utility
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] $1${NC}"
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

info() {
    echo -e "${CYAN}ℹ️ $1${NC}"
}

# Header Villa Celi
show_header() {
    echo -e "${PURPLE}🐚 Paguro Deploy Script - Villa Celi${NC}"
    echo -e "${CYAN}🏖️ Palinuro, Cilento - Receptionist Virtuale AI${NC}"
    echo -e "${CYAN}📱 Frontend: $FRONTEND_URL${NC}"
    echo -e "${CYAN}🔗 API Prod: $API_PROD_URL${NC}"
    echo -e "${BLUE}======================================================${NC}"
}

# Verifica prerequisiti AGGIORNATI
check_requirements() {
    log "Verificando prerequisiti..."
    
    # Docker
    if ! command -v docker &> /dev/null; then
        error "Docker non è installato"
    fi
    
    # Docker Compose V2 (CORRETTO)
    if ! docker compose version &> /dev/null; then
        error "Docker Compose V2 non è installato. Usa 'docker compose' (non docker-compose)"
    fi
    
    # Verifica versione
    local compose_version=$(docker compose version --short 2>/dev/null || echo "unknown")
    info "Docker Compose versione: $compose_version"
    
    # File compose
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "File $COMPOSE_FILE non trovato"
    fi
    
    # ENV file è opzionale
    if [ ! -f "$ENV_FILE" ]; then
        warning "File $ENV_FILE non trovato (opzionale per Villa Celi)"
    fi
    
    success "Prerequisiti verificati"
}

# Avvia servizi AGGIORNATO
start_services() {
    log "Avviando servizi $PROJECT_NAME per Villa Celi..."
    
    # CORRETTO: docker compose (non docker-compose)
    docker compose -f "$COMPOSE_FILE" up -d
    
    if [ $? -eq 0 ]; then
        success "Servizi Paguro avviati!"
        show_endpoints
    else
        error "Avvio servizi fallito!"
    fi
}

# Mostra endpoints
show_endpoints() {
    info "🔗 Endpoints Villa Celi disponibili:"
    echo "  • API Locale: $API_LOCAL_URL"
    echo "  • Health Check: $API_LOCAL_URL/health"
    echo "  • Ollama: http://localhost:11434"
    echo "  • Frontend Villa Celi: $FRONTEND_URL"
    echo "  • API Produzione: $API_PROD_URL"
}

# Ferma servizi AGGIORNATO
stop_services() {
    log "Fermando servizi $PROJECT_NAME..."
    docker compose -f "$COMPOSE_FILE" down
    success "Servizi fermati"
}

# Riavvia servizi AGGIORNATO
restart_services() {
    log "Riavviando servizi $PROJECT_NAME..."
    docker compose -f "$COMPOSE_FILE" restart
    success "Servizi riavviati"
    show_endpoints
}

# Stato migliorato per Villa Celi
show_status() {
    log "Stato servizi $PROJECT_NAME - Villa Celi:"
    echo ""
    
    # Stato containers
    docker compose -f "$COMPOSE_FILE" ps
    echo ""
    
    # Test API locale
    log "Test API locale Paguro..."
    if curl -s -f $API_LOCAL_URL/health > /dev/null; then
        local health_response=$(curl -s $API_LOCAL_URL/health)
        success "🐚 API Paguro locale raggiungibile"
        echo "    Response: $health_response"
    else
        warning "🐚 API Paguro locale non raggiungibile"
    fi
    
    # Test API produzione Villa Celi
    log "Test API produzione Villa Celi..."
    if curl -s -f $API_PROD_URL/health > /dev/null 2>&1; then
        success "🏖️ API produzione Villa Celi raggiungibile"
    else
        warning "🏖️ API produzione Villa Celi non raggiungibile"
    fi
    
    # Test Ollama
    log "Test Ollama AI..."
    if curl -s -f http://localhost:11434/api/version > /dev/null; then
        success "🤖 Ollama raggiungibile"
    else
        warning "🤖 Ollama non raggiungibile"
    fi
    
    # Risorse Docker
    echo ""
    log "Risorse Docker:"
    local containers=$(docker compose -f "$COMPOSE_FILE" ps -q)
    if [ -n "$containers" ]; then
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" $containers 2>/dev/null || warning "Impossibile ottenere statistiche"
    else
        warning "Nessun container in esecuzione"
    fi
    
    show_endpoints
}

# Logs AGGIORNATO
show_logs() {
    local service=${1:-""}
    if [ -n "$service" ]; then
        log "Logs di $service:"
        docker compose -f "$COMPOSE_FILE" logs -f "$service"
    else
        log "Logs di tutti i servizi Villa Celi:"
        docker compose -f "$COMPOSE_FILE" logs -f
    fi
}

# Build immagini AGGIORNATO
build_images() {
    log "Ricompilando immagini per Villa Celi..."
    docker compose -f "$COMPOSE_FILE" build --no-cache
    success "Immagini ricompilate"
}

# Update e restart AGGIORNATO
update_system() {
    log "Aggiornamento sistema Paguro Villa Celi..."
    
    # Pull nuove immagini base
    docker compose -f "$COMPOSE_FILE" pull
    
    # Rebuild custom images
    build_images
    
    # Restart services
    docker compose -f "$COMPOSE_FILE" up -d
    
    success "Sistema Paguro aggiornato per Villa Celi"
    show_endpoints
}

# Backup database Villa Celi
backup_database() {
    log "Eseguendo backup database Paguro Villa Celi..."
    
    local container_name=$(docker compose -f "$COMPOSE_FILE" ps -q paguro-api)
    if [ -z "$container_name" ]; then
        error "Container Paguro API non in esecuzione"
    fi
    
    local backup_dir="./backups/villaceli"
    local backup_file="villaceli_affitti_backup_$(date +%Y%m%d_%H%M%S).db"
    
    mkdir -p "$backup_dir"
    
    if docker exec "$container_name" test -f /app/data/affitti2025.db; then
        docker cp "$container_name:/app/data/affitti2025.db" "$backup_dir/$backup_file"
        success "Backup Villa Celi completato: $backup_dir/$backup_file"
    else
        error "Database Villa Celi non trovato nel container"
    fi
}

# Restore database Villa Celi
restore_database() {
    if [ -z "$1" ]; then
        error "Specificare il file di backup Villa Celi da ripristinare"
    fi
    
    local backup_file="$1"
    if [ ! -f "$backup_file" ]; then
        error "File di backup Villa Celi non trovato: $backup_file"
    fi
    
    log "Ripristinando database Villa Celi da $backup_file..."
    
    local container_name=$(docker compose -f "$COMPOSE_FILE" ps -q paguro-api)
    if [ -z "$container_name" ]; then
        error "Container Paguro API non in esecuzione"
    fi
    
    # Backup current database
    backup_database
    
    # Restore
    docker cp "$backup_file" "$container_name:/app/data/affitti2025.db"
    docker compose -f "$COMPOSE_FILE" restart paguro-api
    
    success "Database Villa Celi ripristinato"
}

# Database shell Villa Celi
database_shell() {
    log "Aprendo shell database SQLite Villa Celi..."
    
    local container_name=$(docker compose -f "$COMPOSE_FILE" ps -q paguro-api)
    if [ -z "$container_name" ]; then
        error "Container Paguro API non in esecuzione"
    fi
    
    echo -e "${YELLOW}Comandi SQLite utili per Villa Celi:${NC}"
    echo ".tables                     # Mostra tabelle"
    echo ".schema appartamenti        # Struttura tabella appartamenti"
    echo "SELECT * FROM appartamenti; # Mostra tutte le prenotazioni"
    echo "SELECT appartamento, COUNT(*) FROM appartamenti GROUP BY appartamento; # Prenotazioni per appartamento"
    echo "SELECT appartamento, check_in, check_out FROM appartamenti WHERE appartamento='Corallo'; # Prenotazioni Corallo"
    echo ".quit                       # Esci"
    echo ""
    
    docker exec -it "$container_name" sqlite3 /app/data/affitti2025.db
}

# Test completo Villa Celi
test_villa_celi_system() {
    log "Test completo sistema Villa Celi..."
    echo ""
    
    # Test containers
    echo "🐳 Container Status:"
    docker compose -f "$COMPOSE_FILE" ps
    echo ""
    
    # Test API locale
    echo "🐚 Paguro API Test (Locale):"
    if response=$(curl -s $API_LOCAL_URL/health); then
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        success "API locale Villa Celi OK"
        
        # Test chat
        log "Test chat Paguro..."
        chat_response=$(curl -s -X POST -H "Content-Type: application/json" \
            -d '{"message": "disponibilità luglio 2025", "session_id":"test_villa_celi"}' \
            $API_LOCAL_URL/chatbot)
        
        if echo "$chat_response" | grep -q '"message"'; then
            success "Chat Paguro funziona"
        else
            warning "Possibili problemi con chat Paguro"
        fi
    else
        warning "API locale Villa Celi non risponde"
    fi
    echo ""
    
    # Test API produzione
    echo "🌐 API Produzione Villa Celi:"
    if curl -s -f $API_PROD_URL/health > /dev/null 2>&1; then
        success "API produzione raggiungibile"
    else
        warning "API produzione non raggiungibile (normale se non deployata)"
    fi
    echo ""
    
    # Test Ollama
    echo "🤖 Ollama AI Status:"
    if curl -s http://localhost:11434/api/version > /dev/null; then
        local ollama_version=$(curl -s http://localhost:11434/api/version)
        echo "$ollama_version"
        success "Ollama funzionante"
    else
        warning "Ollama non risponde"
    fi
    echo ""
    
    # Test database Villa Celi
    echo "🗄️ Database Villa Celi:"
    local container_name=$(docker compose -f "$COMPOSE_FILE" ps -q paguro-api)
    if [ -n "$container_name" ] && docker exec "$container_name" test -f /app/data/affitti2025.db; then
        local record_count=$(docker exec "$container_name" sqlite3 /app/data/affitti2025.db "SELECT COUNT(*) FROM appartamenti;" 2>/dev/null || echo "0")
        success "Database Villa Celi OK - $record_count prenotazioni"
        
        # Mostra appartamenti disponibili
        if [ "$record_count" -gt 0 ]; then
            echo "🏠 Appartamenti Villa Celi:"
            docker exec "$container_name" sqlite3 /app/data/affitti2025.db "SELECT DISTINCT appartamento FROM appartamenti ORDER BY appartamento;" 2>/dev/null || echo "Errore lettura appartamenti"
        fi
    else
        warning "Database Villa Celi non accessibile"
    fi
    echo ""
    
    # Test frontend Villa Celi
    echo "🌐 Frontend Villa Celi Test:"
    if curl -s -f $FRONTEND_URL > /dev/null 2>&1; then
        success "Sito Villa Celi raggiungibile"
    else
        warning "Sito Villa Celi non raggiungibile"
    fi
    echo ""
    
    # Disk usage
    echo "💾 Utilizzo Spazio:"
    docker system df
    echo ""
    
    show_endpoints
}

# Pulizia sistema AGGIORNATA
clean_system() {
    warning "Questa operazione rimuoverà tutti i container e le immagini di $PROJECT_NAME Villa Celi"
    read -p "Continuare? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Pulizia sistema Villa Celi..."
        docker compose -f "$COMPOSE_FILE" down -v --rmi all
        docker system prune -f
        success "Sistema Villa Celi pulito"
    else
        log "Operazione annullata"
    fi
}

# Configurazione sistema Villa Celi
show_config() {
    log "Configurazione Paguro Villa Celi:"
    echo ""
    
    echo "📄 File Compose: $COMPOSE_FILE"
    echo "🏖️ Progetto: $PROJECT_NAME"
    echo ""
    
    if [ -f "$ENV_FILE" ]; then
        echo "📄 Variabili d'ambiente (.env):"
        grep -v '^#' "$ENV_FILE" | grep -v '^ | head -20
        echo ""
    fi
    
    echo "🐳 Servizi Docker:"
    docker compose -f "$COMPOSE_FILE" config --services
    echo ""
    
    echo "📁 Volumi Docker Villa Celi:"
    docker volume ls | grep "$PROJECT_NAME" || echo "Nessun volume specifico trovato"
    echo ""
    
    echo "🌐 URLs Villa Celi:"
    echo "  • Frontend: $FRONTEND_URL"
    echo "  • API Produzione: $API_PROD_URL"
    echo "  • API Locale: $API_LOCAL_URL"
    echo "  • Health Check: $API_LOCAL_URL/health"
    echo "  • Ollama: http://localhost:11434"
}

# Menu principale
show_help() {
    echo "🐚 Paguro Villa Celi - Script di Deploy"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandi disponibili:"
    echo "  start         - Avvia tutti i servizi Villa Celi"
    echo "  stop          - Ferma tutti i servizi"
    echo "  restart       - Riavvia tutti i servizi"
    echo "  status        - Mostra stato dei servizi"
    echo "  logs          - Mostra logs in tempo reale"
    echo "  logs-api      - Logs solo dell'API Paguro"
    echo "  logs-ollama   - Logs solo di Ollama"
    echo "  build         - Ricompila le immagini"
    echo "  update        - Aggiorna e riavvia"
    echo "  backup        - Backup database Villa Celi"
    echo "  restore       - Restore database"
    echo "  clean         - Pulisci container e volumi"
    echo "  test          - Test completo sistema Villa Celi"
    echo "  config        - Mostra configurazione"
    echo "  db-shell      - Shell database SQLite"
    echo "  help          - Mostra questo help"
    echo ""
    echo "🏖️ Villa Celi - Palinuro, Cilento"
}

# Main function
main() {
    show_header
    
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
        "restore")
            shift
            restore_database "$@"
            ;;
        "clean")
            clean_system
            ;;
        "test")
            test_villa_celi_system
            ;;
        "config")
            show_config
            ;;
        "db-shell")
            database_shell
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Esegui main con tutti gli argomenti
main "$@"