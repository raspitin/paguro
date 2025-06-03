#!/bin/bash

# 🐚 Paguro - Script Build Automatico
# Villa Celi - Palinuro, Cilento

set -e  # Exit on any error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🐚 Paguro Build Script - Villa Celi${NC}"
echo -e "${BLUE}======================================${NC}"

# Funzioni utility
log_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verifica prerequisiti
check_prerequisites() {
    log_info "Verificando prerequisiti..."
    
    # Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker non trovato! Installa Docker prima di continuare."
        exit 1
    fi
    
    # Docker Compose (CORRETTO: usa il nuovo comando)
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose non trovato! Installa Docker Compose v2 prima di continuare."
        log_info "💡 Hint: usa 'docker compose' non 'docker-compose'"
        exit 1
    fi
    
    # Python (per test locali)
    if ! command -v python3 &> /dev/null; then
        log_warning "Python3 non trovato. I test locali non saranno disponibili."
    fi
    
    log_success "Prerequisiti verificati"
}

# Crea struttura directory
setup_directories() {
    log_info "Creando struttura directory..."
    
    mkdir -p data logs cache
    
    # Crea database di test se non esiste
    if [ ! -f "data/affitti2025.db" ]; then
        log_info "Creando database di test..."
        cat > create_test_db.py << 'EOF'
import sqlite3
from datetime import datetime

def create_test_database():
    conn = sqlite3.connect('data/affitti2025.db')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS appartamenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appartamento TEXT NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL
        )
    ''')
    
    # Dati di test Villa Celi
    test_data = [
        ('Corallo', '2025-07-01', '2025-07-08'),
        ('Corallo', '2025-07-15', '2025-07-22'),
        ('Corallo', '2025-08-01', '2025-08-08'),
        ('Perla', '2025-07-08', '2025-07-15'),
        ('Perla', '2025-08-08', '2025-08-15'),
        ('Stella Marina', '2025-07-22', '2025-07-29'),
        ('Stella Marina', '2025-08-15', '2025-08-22'),
        ('Riccio', '2025-07-29', '2025-08-05'),
    ]
    
    conn.executemany(
        'INSERT OR REPLACE INTO appartamenti (appartamento, check_in, check_out) VALUES (?, ?, ?)',
        test_data
    )
    
    conn.commit()
    conn.close()
    print("✅ Database di test creato!")

if __name__ == "__main__":
    create_test_database()
EOF

        if command -v python3 &> /dev/null; then
            python3 create_test_db.py
            rm create_test_db.py
        else
            log_warning "Impossibile creare database di test - Python3 non disponibile"
        fi
    fi
    
    log_success "Struttura directory creata"
}

# Pulisci build precedenti
clean_build() {
    log_info "Pulizia build precedenti..."
    
    # Stop containers se in esecuzione (CORRETTO: docker compose)
    docker compose -f docker-compose.yml down 2>/dev/null || true
    
    # Rimuovi immagini Paguro precedenti
    docker rmi paguro-chatbot-villa-celi-paguro-api 2>/dev/null || true
    docker rmi paguro-chatbot-villa-celi_paguro-api 2>/dev/null || true
    
    # Pulisci build cache se richiesto
    if [ "$1" = "--clean-cache" ]; then
        log_info "Pulizia cache Docker..."
        docker system prune -f
    fi
    
    log_success "Pulizia completata"
}

# Build Paguro
build_paguro() {
    log_info "Building Paguro..."
    
    # Build con docker compose (CORRETTO)
    docker compose -f docker-compose.yml build --no-cache
    
    if [ $? -eq 0 ]; then
        log_success "Build Paguro completato!"
    else
        log_error "Build Paguro fallito!"
        exit 1
    fi
}

# Avvia servizi
start_services() {
    log_info "Avviando servizi Paguro..."
    
    # CORRETTO: docker compose
    docker compose -f docker-compose.yml up -d
    
    if [ $? -eq 0 ]; then
        log_success "Servizi Paguro avviati!"
        log_info "Paguro API: http://localhost:5000"
        log_info "Ollama: http://localhost:11434"
    else
        log_error "Avvio servizi fallito!"
        exit 1
    fi
}

# Test connessione
test_connection() {
    log_info "Testing connessione Paguro..."
    
    # Aspetta che i servizi si avviino
    sleep 10
    
    # Test health check
    if curl -f -s http://localhost:5000/api/health > /dev/null; then
        log_success "Paguro API è online!"
        
        # Test chat veloce
        response=$(curl -s -X POST http://localhost:5000/api/chatbot \
            -H "Content-Type: application/json" \
            -d '{"message": "ciao"}' | grep -o '"message"' || echo "")
        
        if [ -n "$response" ]; then
            log_success "Chat Paguro funziona!"
        else
            log_warning "Chat Paguro potrebbe avere problemi"
        fi
    else
        log_error "Paguro API non risponde!"
        log_info "Controllando logs..."
        docker compose -f docker-compose.yml logs paguro-api
    fi
}

# Test database SQLite (CORRETTO)
test_database() {
    log_info "Testing database SQLite..."
    
    # Test usando Python nel container invece di sqlite3 client
    db_test_result=$(docker exec paguro-api-simple python3 -c "
import sqlite3
import os
try:
    conn = sqlite3.connect('/app/data/affitti2025.db')
    cursor = conn.execute('SELECT COUNT(*) FROM appartamenti;')
    count = cursor.fetchone()[0]
    conn.close()
    print(count)
except Exception as e:
    print('ERROR:', e)
    print('0')
" 2>/dev/null || echo "0")
    
    if [[ "$db_test_result" =~ ^[0-9]+$ ]] && [ "$db_test_result" -gt 0 ]; then
        log_success "Database OK - $db_test_result record trovati"
        
        # Mostra sample data
        log_info "Mostrando dati di esempio..."
        docker exec paguro-api-simple python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('/app/data/affitti2025.db')
    cursor = conn.execute('SELECT appartamento, check_in, check_out FROM appartamenti LIMIT 3;')
    for row in cursor.fetchall():
        print(f'  📋 {row[0]}: {row[1]} → {row[2]}')
    conn.close()
except Exception as e:
    print('  ❌ Errore nel leggere i dati:', e)
"
    elif [[ "$db_test_result" =~ ^[0-9]+$ ]] && [ "$db_test_result" -eq 0 ]; then
        log_warning "Database vuoto - creando dati di test..."
        
        # Crea dati nel container
        docker exec paguro-api-simple python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('/app/data/affitti2025.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS appartamenti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appartamento TEXT NOT NULL,
        check_in TEXT NOT NULL,
        check_out TEXT NOT NULL
    )''')
    
    test_data = [
        ('Corallo', '2025-07-01', '2025-07-08'),
        ('Perla', '2025-07-08', '2025-07-15'),
        ('Stella Marina', '2025-07-15', '2025-07-22'),
    ]
    
    conn.executemany(
        'INSERT INTO appartamenti (appartamento, check_in, check_out) VALUES (?, ?, ?)',
        test_data
    )
    conn.commit()
    conn.close()
    print('✅ Dati di test inseriti!')
except Exception as e:
    print('❌ Errore nel creare dati:', e)
"
        log_success "Dati di test creati"
    else
        log_warning "Database inaccessibile o errore di connessione"
    fi
}

# Test completo (se disponibile)
run_full_tests() {
    if [ -f "test_paguro.py" ] && command -v python3 &> /dev/null; then
        log_info "Eseguendo test completi..."
        python3 test_paguro.py
    else
        log_warning "Test completi non disponibili (manca test_paguro.py o Python3)"
    fi
}

# Menu principale
show_menu() {
    echo -e "\n${PURPLE}🐚 Paguro Build Menu${NC}"
    echo "1. Build completo (clean + build + start + test)"
    echo "2. Build veloce (solo build + start)"
    echo "3. Solo build"
    echo "4. Solo start"
    echo "5. Test connessione"
    echo "6. Test database"
    echo "7. Test completi"
    echo "8. Stop servizi"
    echo "9. Logs"
    echo "10. Clean build"
    echo "0. Exit"
    echo -n "Scegli opzione: "
}

# Funzioni menu
option_full_build() {
    check_prerequisites
    setup_directories
    clean_build
    build_paguro
    start_services
    test_connection
    test_database
    run_full_tests
    
    echo -e "\n${GREEN}🎉 Paguro è pronto per Villa Celi!${NC}"
    echo -e "${CYAN}🔗 API: http://localhost:5000${NC}"
    echo -e "${CYAN}📊 Health: http://localhost:5000/api/health${NC}"
}

option_quick_build() {
    check_prerequisites
    setup_directories
    build_paguro
    start_services
    test_connection
    test_database
}

option_only_build() {
    check_prerequisites
    build_paguro
}

option_only_start() {
    start_services
    test_connection
    test_database
}

option_test_connection() {
    test_connection
}

option_test_database() {
    test_database
}

option_full_tests() {
    run_full_tests
}

option_stop() {
    log_info "Fermando servizi Paguro..."
    docker compose -f docker-compose.yml down
    log_success "Servizi fermati"
}

option_logs() {
    echo -e "${CYAN}📋 Logs Paguro (Ctrl+C per uscire):${NC}"
    docker compose -f docker-compose.yml logs -f
}

option_clean() {
    clean_build --clean-cache
}

# Main script
main() {
    # Se eseguito con parametri
    case "$1" in
        "build")
            option_full_build
            ;;
        "quick")
            option_quick_build
            ;;
        "start")
            option_only_start
            ;;
        "stop")
            option_stop
            ;;
        "test")
            option_test_connection
            ;;
        "testdb")
            option_test_database
            ;;
        "clean")
            option_clean
            ;;
        *)
            # Menu interattivo
            while true; do
                show_menu
                read -r choice
                case $choice in
                    1) option_full_build ;;
                    2) option_quick_build ;;
                    3) option_only_build ;;
                    4) option_only_start ;;
                    5) option_test_connection ;;
                    6) option_test_database ;;
                    7) option_full_tests ;;
                    8) option_stop ;;
                    9) option_logs ;;
                    10) option_clean ;;
                    0) 
                        echo -e "${CYAN}🐚 Arrivederci da Paguro!${NC}"
                        exit 0
                        ;;
                    *)
                        log_error "Opzione non valida"
                        ;;
                esac
                echo -e "\n${YELLOW}Premi ENTER per continuare...${NC}"
                read -r
            done
            ;;
    esac
}

# Esegui script
main "$@"
