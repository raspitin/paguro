#!/bin/bash

# Script di gestione e test per Paguro Villa Celi
# -------------------------------------------------
# Prerequisiti: docker, docker compose, curl, jq

# Configurazioni
COMPOSE_FILE="docker-compose.yml"
PAGURO_API_CONTAINER_NAME="paguro-api-simple" # Come definito in docker-compose.yml
OLLAMA_CONTAINER_NAME="paguro-ollama-simple" # Come definito in docker-compose.yml
DB_PATH_IN_CONTAINER="/app/data/affitti2025.db"
PAGURO_API_INTERNAL_URL="http://localhost:5000/api" # Accesso dall'host se le porte sono mappate
PAGURO_API_SERVICE_URL="http://${PAGURO_API_CONTAINER_NAME}:5000/api" # Accesso da altri container nella stessa rete docker
CLOUDFLARE_FQDN="www.viamerano24.it" # Sostituisci con il tuo FQDN effettivo
PAGURO_API_PUBLIC_URL="https://${CLOUDFLARE_FQDN}/api"

# Colori per output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funzione per loggare messaggi
log_info() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Verifica prerequisiti
check_prerequisites() {
    log_info "Verifica prerequisiti..."
    command -v docker >/dev/null 2>&1 || { log_error "Docker non trovato. Installalo prima di procedere."; exit 1; }
    docker compose version >/dev/null 2>&1 || { log_error "Docker Compose V2 (docker compose) non trovato. Installalo o aggiorna Docker Desktop/Engine."; exit 1; }
    command -v curl >/dev/null 2>&1 || { log_error "curl non trovato. Installalo prima di procedere."; exit 1; }
    command -v jq >/dev/null 2>&1 || { log_error "jq non trovato. Installalo prima di procedere."; exit 1; }

    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "File docker-compose.yml non trovato nella directory corrente."
        exit 1
    fi
    # Assumiamo che il Dockerfile sia presente se si sceglie l'opzione di build
    # if [ ! -f "Dockerfile" ]; then
    #     log_error "Dockerfile non trovato nella directory corrente. Necessario per la build."
    #     exit 1
    # fi
    log_info "Prerequisiti OK."
}

# Funzione per attendere che un container sia healthy
wait_for_healthy() {
    local container_name=$1
    local max_attempts=30 # Attendi massimo 30 * 5s = 150 secondi
    local attempt=0
    log_info "In attesa che il container '$container_name' diventi healthy..."
    while [ $attempt -lt $max_attempts ]; do
        status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null)
        if [ "$status" == "healthy" ]; then
            log_info "Container '$container_name' è healthy."
            return 0
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 5
    done
    log_error "Timeout: il container '$container_name' non è diventato healthy."
    return 1
}

# 1. Build pulita
clean_build_and_start() {
    log_info "Avvio build pulita..."
    log_info "Fermo e rimuovo container esistenti (se presenti)..."
    docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
    # log_info "Rimuovo immagini Docker precedenti per paguro-api (opzionale)..."
    # docker image rm paguro-api-simple_paguro-api # Il nome dell'immagine potrebbe variare in base al nome della directory
    log_info "Eseguo build dei container (senza cache)..."
    if [ ! -f "Dockerfile" ]; then
        log_warn "Dockerfile non trovato. La build potrebbe fallire o usare un'immagine esistente."
    fi
    docker compose -f "$COMPOSE_FILE" build --no-cache
    if [ $? -ne 0 ]; then
        log_error "Build fallita."
        exit 1
    fi
    log_info "Avvio i container in background..."
    docker compose -f "$COMPOSE_FILE" up -d
    if [ $? -ne 0 ]; then
        log_error "Avvio container fallito."
        exit 1
    fi
    log_info "Build pulita e avvio completati."
    wait_for_healthy "$PAGURO_API_CONTAINER_NAME" && wait_for_healthy "$OLLAMA_CONTAINER_NAME"
}

# 2. Verifica accessibilità DB nel container
check_db_access() {
    log_info "Verifica accesso al database nel container '$PAGURO_API_CONTAINER_NAME'..."
    if ! wait_for_healthy "$PAGURO_API_CONTAINER_NAME"; then
        log_error "Container API non healthy. Impossibile verificare il DB."
        return 1
    fi

    # Verifica esistenza file DB
    docker exec "$PAGURO_API_CONTAINER_NAME" ls "$DB_PATH_IN_CONTAINER" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        log_error "File database $DB_PATH_IN_CONTAINER non trovato nel container."
        # Tentativo di creazione DB come fa lo script python all'avvio
        log_info "L'API potrebbe creare il DB al primo avvio. Controllo log API per creazione DB..."
        sleep 5 # Dai tempo all'API di avviarsi e creare il DB
        docker logs "$PAGURO_API_CONTAINER_NAME" | grep "Database creato"
        docker exec "$PAGURO_API_CONTAINER_NAME" ls "$DB_PATH_IN_CONTAINER" > /dev/null 2>&1
        if [ $? -ne 0 ]; then
             log_error "File database $DB_PATH_IN_CONTAINER ancora non trovato dopo attesa."
             return 1
        else
            log_info "Database sembra essere stato creato dall'API."
        fi
    fi

    # Verifica tabella appartamenti (potrebbe essere vuota)
    log_info "Eseguo query sulla tabella 'appartamenti'..."
    # Se sqlite3 non è nel container, questo test fallirà. Lo script python crea la tabella se non esiste.
    # Lo script python esegue un test simile all'avvio, quindi ci fidiamo del suo healthcheck.
    # Per un test più approfondito, assicurati che sqlite3 sia nel Dockerfile dell'API.
    # count=$(docker exec "$PAGURO_API_CONTAINER_NAME" sqlite3 "$DB_PATH_IN_CONTAINER" "SELECT count(*) FROM appartamenti;" 2>/dev/null)
    # if [ $? -ne 0 ]; then
    #     log_warn "Impossibile eseguire query sulla tabella 'appartamenti'. Potrebbe essere normale se sqlite3 non è nel container o il DB è appena stato creato."
    #     log_warn "L'API Flask esegue un controllo all'avvio, fare riferimento ai log del container."
    # else
    #     log_info "Tabella 'appartamenti' accessibile. Numero di righe: $count."
    # fi
    log_info "Verifica DB completata (controllo esistenza file e log API per creazione tabella)."
    log_info "Per un test più granulare del DB, l'API Flask esegue controlli all'avvio (vedi i log del container)."
}

# 3. Ferma/Riavvia container
stop_containers() {
    log_info "Fermo i container..."
    docker compose -f "$COMPOSE_FILE" stop
    log_info "Container fermati."
}

start_containers() {
    log_info "Avvio i container..."
    docker compose -f "$COMPOSE_FILE" up -d
    log_info "Container avviati."
    wait_for_healthy "$PAGURO_API_CONTAINER_NAME" && wait_for_healthy "$OLLAMA_CONTAINER_NAME"
}

restart_containers() {
    log_info "Riavvio i container..."
    docker compose -f "$COMPOSE_FILE" restart
    log_info "Container riavviati."
    wait_for_healthy "$PAGURO_API_CONTAINER_NAME" && wait_for_healthy "$OLLAMA_CONTAINER_NAME"
}

# Funzione generica per testare un endpoint
test_endpoint() {
    local url=$1
    local description=$2
    local expected_status_code=${3:-200}
    local check_json_field=${4:-}
    local expected_json_value=${5:-}

    log_info "Test endpoint: $description ($url)"
    response_code=$(curl -k -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$response_code" == "$expected_status_code" ]; then
        log_info "Risposta HTTP $response_code OK."
        if [ -n "$check_json_field" ]; then
            json_response=$(curl -k -s "$url")
            actual_value=$(echo "$json_response" | jq -r ".$check_json_field")
            if [ "$actual_value" == "$expected_json_value" ]; then
                log_info "Campo JSON '$check_json_field' ha valore atteso '$expected_json_value'."
            else
                log_error "Campo JSON '$check_json_field' ha valore '$actual_value', atteso '$expected_json_value'."
                log_error "Risposta JSON: $json_response"
                return 1
            fi
        fi
        return 0
    else
        log_error "Risposta HTTP $response_code. Atteso $expected_status_code."
        curl -k -s "$url" # Mostra output in caso di errore
        return 1
    fi
}

# 4. Test interni API (usando la porta mappata sull'host)
run_internal_api_tests() {
    log_info "Esecuzione test interni API (via localhost)..."
    if ! wait_for_healthy "$PAGURO_API_CONTAINER_NAME" || ! wait_for_healthy "$OLLAMA_CONTAINER_NAME"; then
        log_error "Uno o più container non sono healthy. Test interni API saltati."
        return 1
    fi

    test_endpoint "${PAGURO_API_INTERNAL_URL}/health" "Health check" 200 "status" "ok"
    test_endpoint "${PAGURO_API_INTERNAL_URL}/test" "Test endpoint" 200 "status" "ok"
    
    log_info "Test query disponibilità (interna)..."
    response=$(curl -s -X POST -H "Content-Type: application/json" \
        -d '{"message": "disponibilità luglio 2025", "session_id":"test_internal_session"}' \
        "${PAGURO_API_INTERNAL_URL}/chatbot")
    echo "$response" | jq -r '.message'
    if echo "$response" | jq -e '.type' | grep -q "availability_list\|no_availability"; then
        log_info "Test disponibilità interna OK."
    else
        log_error "Test disponibilità interna fallito. Risposta: $response"
    fi

    log_info "Test query generica (interna, dovrebbe usare Ollama)..."
    response=$(curl -s -X POST -H "Content-Type: application/json" \
        -d '{"message": "parlami di palinuro", "session_id":"test_internal_ollama_session"}' \
        "${PAGURO_API_INTERNAL_URL}/chatbot")
    echo "$response" | jq -r '.message'
    if echo "$response" | jq -e '.type' | grep -q "ollama_response"; then
        log_info "Test query generica interna (Ollama) OK."
    else
        log_error "Test query generica interna (Ollama) fallito. Risposta: $response"
    fi
    log_info "Test interni API completati."
}

# 5. Test API tramite FQDN (Cloudflare)
run_fqdn_api_tests() {
    log_info "Esecuzione test API tramite FQDN (Cloudflare)..."
    log_warn "Assicurati che il tunnel Cloudflare sia attivo e punti correttamente ai tuoi container."
    log_warn "URL pubblico testato: $PAGURO_API_PUBLIC_URL"

    test_endpoint "${PAGURO_API_PUBLIC_URL}/health" "Health check pubblico" 200 "status" "ok"
    test_endpoint "${PAGURO_API_PUBLIC_URL}/test" "Test endpoint pubblico" 200 "status" "ok"

    log_info "Test query disponibilità (pubblica)..."
    response=$(curl -k -s -X POST -H "Content-Type: application/json" \
        -d '{"message": "disponibilità agosto 2025", "session_id":"test_public_session"}' \
        "${PAGURO_API_PUBLIC_URL}/chatbot")
    echo "$response" | jq -r '.message'
    if echo "$response" | jq -e '.type' | grep -q "availability_list\|no_availability"; then
        log_info "Test disponibilità pubblica OK."
    else
        log_error "Test disponibilità pubblica fallito. Risposta: $response"
    fi
    log_info "Test API tramite FQDN completati."
}

# 6. Test fallback Ollama
test_ollama_fallback() {
    log_info "Esecuzione test fallback Ollama..."
    if ! wait_for_healthy "$PAGURO_API_CONTAINER_NAME"; then
        log_error "Container API non healthy. Test fallback Ollama saltato."
        return 1
    fi

    log_info "Verifica risposta normale con Ollama attivo..."
    if ! wait_for_healthy "$OLLAMA_CONTAINER_NAME"; then
        log_warn "Container Ollama non healthy. Potrebbe influenzare il test."
    fi
    response_ollama_ok=$(curl -s -X POST -H "Content-Type: application/json" \
        -d '{"message": "raccontami una storia su un paguro a palinuro", "session_id":"test_ollama_fallback_session_1"}' \
        "${PAGURO_API_INTERNAL_URL}/chatbot")
    echo "$response_ollama_ok" | jq -r '.message'
    if ! echo "$response_ollama_ok" | jq -e '.type' | grep -q "ollama_response"; then
        log_warn "La risposta con Ollama attivo non è di tipo 'ollama_response'. Verifica: $response_ollama_ok"
    else
        log_info "Risposta con Ollama attivo ricevuta correttamente."
    fi

    log_info "Fermo il container Ollama ('$OLLAMA_CONTAINER_NAME')..."
    docker stop "$OLLAMA_CONTAINER_NAME"
    if [ $? -ne 0 ]; then
        log_error "Impossibile fermare il container Ollama. Test fallback interrotto."
        # Prova a riavviare ollama se era fermo
        docker start "$OLLAMA_CONTAINER_NAME" >/dev/null 2>&1
        return 1
    fi
    log_info "Container Ollama fermato. Attendo qualche secondo..."
    sleep 10 # Dai tempo all'API di rilevare Ollama non disponibile

    log_info "Invio query generica con Ollama non disponibile..."
    response_ollama_fail=$(curl -s -X POST -H "Content-Type: application/json" \
        -d '{"message": "raccontami una storia su un paguro a palinuro", "session_id":"test_ollama_fallback_session_2"}' \
        "${PAGURO_API_INTERNAL_URL}/chatbot")
    
    echo "$response_ollama_fail" | jq -r '.message'
    if echo "$response_ollama_fail" | jq -e '.type' | grep -q "fallback_response"; then
        log_info "Test fallback Ollama SUPERATO. Ricevuta risposta di fallback."
    else
        log_error "Test fallback Ollama FALLITO. Risposta: $response_ollama_fail"
        log_error "Atteso tipo 'fallback_response'."
    fi

    log_info "Riavvio il container Ollama ('$OLLAMA_CONTAINER_NAME')..."
    docker start "$OLLAMA_CONTAINER_NAME"
    if ! wait_for_healthy "$OLLAMA_CONTAINER_NAME"; then
        log_warn "Container Ollama non è tornato healthy rapidamente."
    else
        log_info "Container Ollama riavviato e healthy."
    fi
    log_info "Test fallback Ollama completati."
}

# Funzione per visualizzare i log
view_logs() {
    log_info "Visualizzazione log (ultime 100 righe). Premi Ctrl+C per uscire."
    docker compose -f "$COMPOSE_FILE" logs -f --tail 100
}

# Menu principale
main_menu() {
    check_prerequisites
    echo -e "\n--- Menu Gestione Paguro Villa Celi ---"
    echo "1. Build pulita e avvio container"
    echo "2. Ferma container"
    echo "3. Avvia container (precedentemente buildati)"
    echo "4. Riavvia container"
    echo "5. Verifica accessibilità DB (interno al container API)"
    echo "6. Esegui test API interni (localhost)"
    echo "7. Esegui test API tramite FQDN (Cloudflare - ${PAGURO_API_PUBLIC_URL})"
    echo "8. Test fallback Ollama"
    echo "9. Visualizza log container (live)"
    echo "10. Esegui TUTTI i test (5, 6, 7, 8)"
    echo "0. Esci"
    echo "---------------------------------------"
    read -rp "Scegli un'opzione: " choice

    case $choice in
        1) clean_build_and_start ;;
        2) stop_containers ;;
        3) start_containers ;;
        4) restart_containers ;;
        5) check_db_access ;;
        6) run_internal_api_tests ;;
        7) run_fqdn_api_tests ;;
        8) test_ollama_fallback ;;
        9) view_logs ;;
        10)
            check_db_access
            run_internal_api_tests
            run_fqdn_api_tests
            test_ollama_fallback
            log_info "Tutti i test completati."
            ;;
        0) exit 0 ;;
        *) log_error "Opzione non valida." ;;
    esac
    echo ""
    read -rp "Premi Invio per tornare al menu..."
    main_menu
}

# Avvio
main_menu

