import re
import json
import logging
from datetime import datetime, timedelta
from cachetools import TTLCache
from collections import defaultdict
import sqlite3
import os

# --- Configurazione ---
# Puoi definire le variabili di configurazione qui o in un file config.py separato
class Config:
    BOOKING_PAGE_URL = os.environ.get('BOOKING_PAGE_URL', 'https://www.villaceli.it/prenotazione/')
    DATABASE_PATH = os.environ.get('DB_PATH', 'data/affitti2025.db') # Percorso del database SQLite
    OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')
    MODEL = os.environ.get('MODEL', 'llama3.2:1b')

config = Config()

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Mappe per la conversione mesi ---
MONTH_MAP = {
    'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4, 'maggio': 5, 'giugno': 6,
    'luglio': 7, 'agosto': 8, 'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
}

# --- Cache per la sessione (TTL: 30 minuti) ---
session_cache = TTLCache(maxsize=1000, ttl=1800) # 1000 sessioni, 30 minuti di TTL

# --- Funzioni di utilità del database ---
def get_db_connection():
    """Stabilisce una connessione al database SQLite."""
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row # Permette di accedere alle colonne per nome
        return conn
    except sqlite3.Error as e:
        logger.error(f"Errore connessione al database: {e}")
        return None

def initialize_db():
    """Inizializza il database se non esiste (per testing o primo avvio)."""
    if not os.path.exists(os.path.dirname(config.DATABASE_PATH)):
        os.makedirs(os.path.dirname(config.DATABASE_PATH))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS appartamenti (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    descrizione TEXT
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS disponibilita (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appartamento_id INTEGER,
                    data_checkin TEXT NOT NULL,
                    data_checkout TEXT NOT NULL,
                    prezzo REAL,
                    FOREIGN KEY (appartamento_id) REFERENCES appartamenti(id)
                );
            """)
            # Esempio di dati iniziali (se il DB è vuoto)
            cursor.execute("INSERT OR IGNORE INTO appartamenti (nome, descrizione) VALUES ('Appartamento A', 'Monolocale accogliente');")
            cursor.execute("INSERT OR IGNORE INTO appartamenti (nome, descrizione) VALUES ('Appartamento B', 'Bilocale con vista mare');")
            conn.commit()
            logger.info("Database inizializzato o aggiornato.")
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'inizializzazione del database: {e}")
        finally:
            conn.close()

# Inizializza il database all'avvio
initialize_db()

# --- Funzioni di analisi e logica ---

def analyze_message(message):
    """Analizza il messaggio per identificare il tipo di richiesta."""
    message_lower = message.lower().strip()

    detected_month = None
    detected_year = None
    detected_apartment = None

    # Estrazione mese
    for month_name, month_num in MONTH_MAP.items():
        if month_name in message_lower:
            detected_month = month_num
            break
    
    # Estrazione anno
    year_match = re.search(r'202[4-9]|20[3-9]\d', message_lower)
    if year_match:
        detected_year = int(year_match.group(0))
    elif detected_month:
        current_year = datetime.now().year
        # Se il mese rilevato è precedente al mese attuale, assumiamo l'anno prossimo
        if detected_month < datetime.now().month:
            detected_year = current_year + 1
        else:
            detected_year = current_year
    else:
        detected_year = datetime.now().year

    # Estrazione appartamento
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT DISTINCT nome FROM appartamenti;")
        apartment_names_in_db = [row[0].lower() for row in cursor.fetchall()]
        conn.close()
        
        for apt_name in apartment_names_in_db:
            if re.search(r'\b' + re.escape(apt_name) + r'\b', message_lower):
                detected_apartment = apt_name
                break
    except Exception as e:
        logger.error(f"Errore recupero nomi appartamenti: {e}")
        # Continua anche in caso di errore, trattando come general_query

    # Determinazione del tipo di query
    if any(keyword in message_lower for keyword in ['prezzi', 'costo', 'quanto costa', 'tariffe', 'preventivo']):
        return "price_request"
    elif any(keyword in message_lower for keyword in ['dove si trova', 'indicazioni', 'come arrivare', 'mappa', 'strada']):
        return "directions_request"
    elif "disponibilità" in message_lower or "libero" in message_lower:
        return "availability_query"
    elif detected_month and detected_apartment:
        return "availability_query"
    elif detected_month:
        return "availability_query"
    elif re.match(r'^\s*\d+\s*$', message_lower): # Se è solo un numero, è una scelta di prenotazione
        return "booking_choice"
    else:
        return "general_query"

def get_availability(month=None, year=None, apartment_name=None):
    """
    Recupera le disponibilità degli appartamenti dal database per un dato mese/anno/appartamento.
    Simula la disponibilità se non ci sono dati reali.
    """
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year

    conn = get_db_connection()
    if not conn:
        logger.error("Impossibile connettersi al database per la disponibilità.")
        return []

    available_slots = []
    try:
        query = """
            SELECT a.nome as appartamento, d.data_checkin, d.data_checkout
            FROM disponibilita d
            JOIN appartamenti a ON d.appartamento_id = a.id
            WHERE STRFTIME('%Y', d.data_checkin) = ? AND STRFTIME('%m', d.data_checkin) = ?
        """
        params = [str(year), f'{month:02d}']

        if apartment_name:
            query += " AND LOWER(a.nome) = LOWER(?)"
            params.append(apartment_name.lower())
        
        query += " ORDER BY d.data_checkin, a.nome;"

        cursor = conn.execute(query, params)
        for row in cursor.fetchall():
            checkin_date = datetime.strptime(row['data_checkin'], '%Y-%m-%d')
            checkout_date = datetime.strptime(row['data_checkout'], '%Y-%m-%d')
            
            # Filtra le date passate
            if checkout_date >= datetime.now():
                available_slots.append({
                    "appartamento": row['appartamento'],
                    "check_in": row['data_checkin'],
                    "check_out": row['data_checkout'],
                    "check_in_formatted": checkin_date.strftime('%d/%m/%Y'),
                    "check_out_formatted": checkout_date.strftime('%d/%m/%Y')
                })
    except sqlite3.Error as e:
        logger.error(f"Errore durante il recupero delle disponibilità dal DB: {e}")
    finally:
        conn.close()

    if not available_slots:
        logger.info(f"Nessuna disponibilità trovata per mese={month}, anno={year}, appartamento={apartment_name}. Genero dati di esempio.")
        # Genera dati di esempio se non ci sono disponibilità reali
        today = datetime.now().date()
        current_year = today.year
        current_month = today.month

        # Assicurati che il mese e l'anno siano nel futuro o nell'attuale
        if year < current_year or (year == current_year and month < current_month):
            # Se la richiesta è per un mese/anno passato, sposta all'anno prossimo
            if month < current_month:
                year = current_year + 1
            else:
                year = current_year # Mese uguale o futuro
        
        # Simula disponibilità ogni sabato del mese per 7 giorni
        simulated_slots = []
        first_day_of_month = datetime(year, month, 1)
        for i in range(32): # Controlla i giorni del mese
            current_date = first_day_of_month + timedelta(days=i)
            if current_date.month != month: # Esce se si passa al mese successivo
                break
            
            # Solo sabati
            if current_date.weekday() == 5: # Sabato è il giorno 5 (Lunedì è 0)
                if current_date >= today: # Solo date future o odierne
                    sim_checkin = current_date
                    sim_checkout = current_date + timedelta(days=7)
                    if not apartment_name or apartment_name.lower() == 'appartamento a':
                        simulated_slots.append({
                            "appartamento": "Appartamento A",
                            "check_in": sim_checkin.strftime('%Y-%m-%d'),
                            "check_out": sim_checkout.strftime('%Y-%m-%d'),
                            "check_in_formatted": sim_checkin.strftime('%d/%m/%Y'),
                            "check_out_formatted": sim_checkout.strftime('%d/%m/%Y')
                        })
                    if not apartment_name or apartment_name.lower() == 'appartamento b':
                        simulated_slots.append({
                            "appartamento": "Appartamento B",
                            "check_in": sim_checkin.strftime('%Y-%m-%d'),
                            "check_out": sim_checkout.strftime('%Y-%m-%d'),
                            "check_in_formatted": sim_checkin.strftime('%d/%m/%Y'),
                            "check_out_formatted": sim_checkout.strftime('%d/%m/%Y')
                        })
        return simulated_slots

    return available_slots

def format_availability(availability_list):
    """Formatta la lista delle disponibilità per la visualizzazione."""
    if not availability_list:
        return "Non ho trovato disponibilità per il periodo o l'appartamento richiesto."

    grouped_availability = defaultdict(lambda: defaultdict(list))
    for item in availability_list:
        month_year = datetime.strptime(item['check_in'], '%Y-%m-%d').strftime('%B %Y')
        grouped_availability[month_year][item['appartamento']].append(item)

    response_parts = ["Ecco le disponibilità che ho trovato:"]
    idx = 1
    for month_year, apartments in grouped_availability.items():
        response_parts.append(f"\n🗓️ **{month_year.capitalize()}**:")
        for apt_name, slots in apartments.items():
            response_parts.append(f"🏠 **{apt_name}**:")
            for slot in slots:
                response_parts.append(
                    f"{idx}. Dal sabato {slot['check_in_formatted']} al sabato {slot['check_out_formatted']}"
                )
                slot['index'] = idx # Aggiunge l'indice per la selezione successiva
                idx += 1
    
    response_parts.append("\nPer prenotare, rispondi con il **numero** della disponibilità scelta.")
    return "\n".join(response_parts)

def handle_booking_choice(booking_choice, session_id):
    """Genera risposta di prenotazione con booking_data."""
    session_data = session_cache.get(session_id, {})
    availability_data = session_data.get('availability_data', [])
    
    if not availability_data:
        return {
            "message": "❌ **Errore**: Prima cerca le disponibilità, poi scegli il numero da prenotare.",
            "type": "error"
        }
    
    booking_item = None
    for item in availability_data:
        if item.get('index') == booking_choice: # Usa .get per sicurezza
            booking_item = item
            break
    
    if not booking_item:
        return {
            "message": f"❌ **Numero non valido**. Scegli un numero tra 1 e {len(availability_data)}.",
            "type": "error"
        }
    
    booking_data = {
        "appartamento": booking_item['appartamento'],
        "check_in": booking_item['check_in'],
        "check_out": booking_item['check_out'],
        "check_in_formatted": booking_item['check_in_formatted'],
        "check_out_formatted": booking_item['check_out_formatted']
    }
    
    message = f"""🎉 **Perfetto!** Hai scelto:

🏠 **{booking_data['appartamento']}**
📅 **Dal** sabato {booking_data['check_in_formatted']} **al** sabato {booking_data['check_out_formatted']}

⏳ **Ti sto reindirizzando al form di prenotazione...**"""

    logger.info(f"Booking generato per sessione {session_id}: {booking_data}")
    return {
        "message": message,
        "type": "booking",
        "booking_data": booking_data
    }

def get_ollama_response(prompt):
    """Invia una richiesta al modello Ollama per una risposta generica."""
    try:
        import requests
        headers = {'Content-Type': 'application/json'}
        data = {
            "model": config.MODEL,
            "prompt": prompt,
            "stream": False # Non vogliamo lo streaming per questa API
        }
        logger.info(f"Invio prompt a Ollama: {prompt[:100]}...")
        response = requests.post(config.OLLAMA_URL, headers=headers, data=json.dumps(data), timeout=60)
        response.raise_for_status() # Lancia un errore per status codes non 2xx
        
        result = response.json()
        if 'response' in result:
            logger.info("Risposta da Ollama ricevuta.")
            return result['response'].strip()
        else:
            logger.warning("Risposta Ollama non contiene 'response' key.")
            return "Mi dispiace, c'è stato un problema nel recuperare la risposta. Riprova più tardi."
    except requests.exceptions.RequestException as e:
        logger.error(f"Errore di richiesta a Ollama: {e}")
        return "Mi dispiace, il servizio di intelligenza artificiale non è al momento disponibile. Riprova più tardi."
    except json.JSONDecodeError as e:
        logger.error(f"Errore nel parsing della risposta JSON da Ollama: {e}")
        return "Mi dispiace, ho ricevuto una risposta non valida dal servizio di intelligenza artificiale."
    except Exception as e:
        logger.error(f"Errore generico in get_ollama_response: {e}")
        return "Si è verificato un errore inatteso. Per favore, riprova."


# --- Funzione principale di gestione della query ---

def handle_query_complete(query, session_id):
    """
    Gestisce una query completa, analizzando il messaggio e generando una risposta appropriata.
    """
    logger.info(f"Gestione query per sessione {session_id}: '{query}'")
    
    session_data = session_cache.get(session_id, {})
    query_type = analyze_message(query)
    logger.info(f"Tipo di query rilevato: {query_type}")

    response_data = {"message": "Non ho capito la tua richiesta. Puoi riformulare?", "type": "info"}

    if query_type == "price_request":
        message = (
            "Per ricevere un preventivo accurato, ti prego di **compilare il form di prenotazione** "
            "specificando le date di tuo interesse. In questo modo potremo fornirti tutti i dettagli sui prezzi e la disponibilità. "
            "Ti reindirizzo subito alla pagina di prenotazione!"
        )
        response_data = {
            "message": message,
            "type": "booking_redirect", # Questo tipo indica al frontend di reindirizzare
            "booking_data": {
                "redirect_url": config.BOOKING_PAGE_URL 
            }
        }
    elif query_type == "directions_request":
        message = (
            "Villa Celi si trova a Palinuro, nel cuore del Cilento. "
            "Ecco le indicazioni generali: dall'autostrada A3 Salerno-Reggio Calabria, prendi l'uscita Padula-Buonabitacolo e segui le indicazioni per Palinuro. "
            "Una volta arrivato a Palinuro, troverai facilmente le indicazioni per Villa Celi."
            "<br><br>👉 **<a href='https://www.villaceli.it/dove-siamo/' target='_blank'>Clicca qui per calcolare il percorso su Google Maps!</a>**"
        )
        response_data = {
            "message": message,
            "type": "info"
        }
    elif query_type == "availability_query":
        # Estrarre mese, anno, appartamento dal messaggio se presenti
        detected_month = None
        detected_year = None
        detected_apartment = None
        
        message_lower = query.lower().strip()
        for month_name, month_num in MONTH_MAP.items():
            if month_name in message_lower:
                detected_month = month_num
                break
        
        year_match = re.search(r'202[4-9]|20[3-9]\d', message_lower)
        if year_match:
            detected_year = int(year_match.group(0))

        try:
            conn = get_db_connection()
            cursor = conn.execute("SELECT DISTINCT nome FROM appartamenti;")
            apartment_names_in_db = [row[0].lower() for row in cursor.fetchall()]
            conn.close()
            for apt_name in apartment_names_in_db:
                if re.search(r'\b' + re.escape(apt_name) + r'\b', message_lower):
                    detected_apartment = apt_name
                    break
        except Exception as e:
            logger.error(f"Errore durante l'estrazione appartamento per availability_query: {e}")

        availability_list = get_availability(detected_month, detected_year, detected_apartment)
        formatted_message = format_availability(availability_list)
        
        session_data['availability_data'] = availability_list # Salva in sessione per la scelta successiva
        session_cache[session_id] = session_data

        response_data = {
            "message": formatted_message,
            "type": "availability" if availability_list else "info"
        }
    elif query_type == "booking_choice":
        try:
            booking_number = int(query.strip())
            response_data = handle_booking_choice(booking_number, session_id)
        except ValueError:
            response_data = {
                "message": "Per favore, inserisci un numero valido per la prenotazione.",
                "type": "error"
            }
    else: # general_query
        # Se non è una query specifica, passa a Ollama
        ollama_prompt = f"Rispondi alla seguente domanda su Villa Celi (Palinuro, Cilento, Italia). Sii conciso e usa un tono amichevole e ospitale. Villa Celi è un complesso di appartamenti e non un hotel. Se non sai la risposta, chiedi di riformulare o di consultare il sito. Domanda: {query}"
        ollama_response_text = get_ollama_response(ollama_prompt)
        response_data = {
            "message": ollama_response_text,
            "type": "info"
        }

    logger.info(f"Risposta generata per sessione {session_id}: {response_data['type']} - {response_data['message'][:50]}...")
    return response_data

# Esempio di utilizzo (solo per test locali)
if __name__ == '__main__':
    # Questo blocco viene eseguito solo quando lo script è avviato direttamente
    # NON VERRÀ ESEGUITO QUANDO IL FILE È IMPORTATO DALL'API FLASK
    print("--- Test del modulo handle_query_complete.py ---")
    
    # Inizializza il DB per assicurarsi che esista e contenga dati di esempio
    initialize_db()

    test_session_id = "test_session_123"

    print("\nTest 1: Richiesta di prezzi")
    response = handle_query_complete("quanto costa?", test_session_id)
    print(json.dumps(response, indent=2, ensure_ascii=False))

    print("\nTest 2: Richiesta di indicazioni stradali")
    response = handle_query_complete("come arrivo a villa celi?", test_session_id)
    print(json.dumps(response, indent=2, ensure_ascii=False))

    print("\nTest 3: Richiesta disponibilità agosto")
    response = handle_query_complete("disponibilità agosto", test_session_id)
    print(json.dumps(response, indent=2, ensure_ascii=False))
    
    print("\nTest 4: Richiesta disponibilità appartamento B per luglio")
    response = handle_query_complete("disponibilità appartamento b luglio", test_session_id)
    print(json.dumps(response, indent=2, ensure_ascii=False))

    # Assicurati che ci siano dati di disponibilità in sessione per il test successivo
    # Per semplicità, forziamo l'aggiunta di un elemento simulato nella cache per il test di booking
    session_data_for_booking = session_cache.get(test_session_id, {})
    if not session_data_for_booking.get('availability_data'):
        # Aggiungiamo dati di esempio se non ci sono dopo i test precedenti
        session_data_for_booking['availability_data'] = [{
            "appartamento": "Appartamento A",
            "check_in": "2025-07-05",
            "check_out": "2025-07-12",
            "check_in_formatted": "05/07/2025",
            "check_out_formatted": "12/07/2025",
            "index": 1
        }]
        session_cache[test_session_id] = session_data_for_booking
        print("\n(Aggiunti dati di esempio per il test di prenotazione)")

    print("\nTest 5: Scelta di prenotazione (numero 1)")
    response = handle_query_complete("1", test_session_id)
    print(json.dumps(response, indent=2, ensure_ascii=False))

    print("\nTest 6: Query generica (passa a Ollama)")
    response = handle_query_complete("parlami del cilento", test_session_id)
    print(json.dumps(response, indent=2, ensure_ascii=False))