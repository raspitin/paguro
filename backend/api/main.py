#!/usr/bin/env python3
"""
🐚 Paguro - Backend Flask OTTIMIZZATO per Villa Celi
Receptionist Virtuale per appartamenti a Palinuro, Cilento
VERSIONE con Post-processing e CTA forzati
"""

import sqlite3
import requests
import re
import uuid
import os
import logging
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

# ====================================
# CONFIGURAZIONE E SETUP
# ====================================

app = Flask(__name__)
CORS(app)

# Configurazione centralizzata
class Config:
    DB_PATH = os.environ.get('DB_PATH', 'data/affitti2025.db')
    OLLAMA_URL = os.environ.get('OLLAMA_URL', "http://127.0.0.1:11434/api/generate")
    OLLAMA_MODEL = os.environ.get('MODEL', "llama3.2:1b")
    OLLAMA_TIMEOUT = 10
    OLLAMA_TEMPERATURE = 0.7
    OLLAMA_NUM_CTX = 2048
    RESPONSE_CACHE_SIZE = 100
    MAX_RESPONSE_LENGTH = 4  # Massimo 4 righe
    CTA_REQUIRED = True

# Assicura directory
if not os.path.exists(os.path.dirname(Config.DB_PATH)):
    os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)

# Cache migliorata
session_cache = {}
response_cache = {}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ====================================
# MAPPA MESI E RISPOSTE PREDEFINITE
# ====================================

MONTH_MAP = {
    'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4, 'maggio': 5, 'giugno': 6,
    'luglio': 7, 'agosto': 8, 'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
}

# Risposte predefinite ottimizzate per Villa Celi
PREDEFINED_RESPONSES = {
    "come si arriva": "🗺️ **Villa Celi si trova a Palinuro**, nel cuore del Cilento. Raggiungi facilmente:\n🚗 A3, uscita Battipaglia → SS18 (1h) o Sala Consilina → SS517 (45min)\n🚂 Stazione Pisciotta-Palinuro (5km)\n\n💡 **Prenota ora**: 'disponibilità luglio 2025'",
    
    "dove si trova": "📍 **Villa Celi è a Palinuro**, nel Parco Nazionale del Cilento.\nUna perla affacciata sul mare cristallino! 🌊🏞️\n\n💡 **Scopri le date libere**: 'disponibilità agosto 2025'",
    
    "cosa": "🌊 **A Palinuro**: spiagge dorate, Grotta Azzurra, Faro al tramonto, siti archeologici di Velia.\n🥾 Trekking nel Cilento, cucina tipica, sport acquatici.\n\n💡 **Prenota l'esperienza**: 'disponibilità settembre 2025'",
    "attività": "🌊 **A Palinuro**: spiagge dorate, Grotta Azzurra, Faro al tramonto, siti archeologici di Velia.\n🥾 Trekking nel Cilento, cucina tipica, sport acquatici.\n\n💡 **Prenota l'esperienza**: 'disponibilità settembre 2025'",
    "fare": "🌊 **A Palinuro**: spiagge dorate, Grotta Azzurra, Faro al tramonto, siti archeologici di Velia.\n🥾 Trekking nel Cilento, cucina tipica, sport acquatici.\n\n💡 **Prenota l'esperienza**: 'disponibilità settembre 2025'",
    
    "spiagge": "🏖️ **Spiagge di Palinuro**: Buon Dormire, Marinella, Ficocella, Arco Naturale.\n🚤 Grotta Azzurra raggiungibile in barca. Tutte a 300m da Villa Celi!\n\n💡 **Prenota il mare**: 'disponibilità luglio 2025'",
    
    "mare": "🌊 **Mare di Palinuro**: acque cristalline Bandiera Blu, fondali ricchi, sport acquatici.\n🏆 Tra i mari più belli d'Italia!\n\n💡 **Prenota il soggiorno**: 'disponibilità agosto 2025'",
    
    "servizi": "🏠 **Villa Celi**: appartamenti vista mare, WiFi, parcheggio, giardino, cucine attrezzate.\n🏖️ A 300m dalle spiagge, aria condizionata.\n\n💡 **Controlla disponibilità**: 'disponibilità luglio 2025'",
    
    "prezzo": "💰 **Prezzi Villa Celi**: tariffe competitive, offerte lunghi soggiorni.\n🏖️ Miglior rapporto qualità-prezzo nel Cilento!\n\n💡 **Verifica costi**: 'disponibilità agosto 2025'",
}

# ====================================
# POST-PROCESSING E CTA
# ====================================

def post_process_response(response_text, response_type="unknown"):
    """
    Post-processa ogni risposta per garantire:
    1. Max 4 righe di lunghezza
    2. Call-to-action sempre presente
    3. Focus su Villa Celi/Palinuro
    """
    if not response_text:
        return get_fallback_response("empty")
    
    # Dividi in righe e rimuovi righe vuote
    lines = [line.strip() for line in response_text.split('\n') if line.strip()]
    
    # Controlla se ha già un CTA valido
    has_cta = any(
        keyword in response_text.lower() 
        for keyword in ['disponibilità', 'prenota', 'villa celi', 'palinuro']
    )
    
    # Se troppo lungo, tronca e aggiungi CTA
    if len(lines) > Config.MAX_RESPONSE_LENGTH:
        lines = lines[:Config.MAX_RESPONSE_LENGTH-1]  # Lascia spazio per CTA
        has_cta = False  # Forza CTA se troncato
    
    # Aggiungi CTA se mancante
    if Config.CTA_REQUIRED and not has_cta:
        cta = get_cta_for_response_type(response_type)
        lines.append(cta)
    
    # Assicura focus su Villa Celi se generico
    if not any(keyword in response_text.lower() for keyword in ['villa celi', 'palinuro', 'cilento']):
        lines = adapt_response_to_villa_celi(lines, response_type)
    
    return '\n'.join(lines)

def get_cta_for_response_type(response_type):
    """Restituisce CTA specifico per tipo di risposta"""
    cta_map = {
        "weather": "💡 **Il tempo è perfetto per Villa Celi!** Scrivi: 'disponibilità luglio 2025'",
        "food": "💡 **Prenota Villa Celi per gustare il Cilento!** Scrivi: 'disponibilità agosto 2025'", 
        "activity": "💡 **Vivi Palinuro da Villa Celi!** Scrivi: 'disponibilità settembre 2025'",
        "generic": "💡 **Scopri Villa Celi a Palinuro!** Scrivi: 'disponibilità luglio 2025'",
        "unknown": "💡 **Ti aiuto con Villa Celi!** Scrivi: 'disponibilità agosto 2025'"
    }
    return cta_map.get(response_type, cta_map["generic"])

def adapt_response_to_villa_celi(lines, response_type):
    """Adatta risposte generiche a Villa Celi/Palinuro"""
    adaptations = {
        "weather": ["🌞 A Palinuro il clima è mediterraneo tutto l'anno!", "Villa Celi è la base perfetta per goderti il sole del Cilento."],
        "food": ["🍝 Il Cilento offre cucina autentica a km zero!", "Da Villa Celi raggiungi i migliori ristoranti di Palinuro."],
        "activity": ["🏖️ Palinuro offre mare, natura e cultura!", "Villa Celi è il punto di partenza ideale per esplorare."],
        "generic": ["🏖️ Villa Celi a Palinuro ti aspetta!", "Nel cuore del Cilento, a 300m dal mare."]
    }
    
    adaptation = adaptations.get(response_type, adaptations["generic"])
    return adaptation + lines[-1:]  # Mantieni ultima riga (spesso CTA)

def classify_response_type(message):
    """Classifica il tipo di domanda per CTA specifico"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['tempo', 'meteo', 'clima', 'pioggia', 'sole']):
        return "weather"
    elif any(word in message_lower for word in ['mangiare', 'ristorante', 'cibo', 'ricetta', 'cucina']):
        return "food"
    elif any(word in message_lower for word in ['fare', 'attività', 'visitare', 'vedere', 'divertimento']):
        return "activity"
    else:
        return "generic"

def get_fallback_response(reason="unknown"):
    """Fallback specifici per tipo di problema"""
    fallbacks = {
        "empty": "🤔 **Non ho ricevuto la domanda**.\n💡 **Prova**: 'disponibilità luglio 2025' o 'dove si trova Villa Celi'",
        "weather": "🌞 **Il tempo a Palinuro è ottimo tutto l'anno!**\n🏖️ Perfetto per le vacanze al mare.\n💡 **Pianifica il soggiorno**: 'disponibilità luglio 2025'",
        "food": "🍝 **Ti aiuto con le prenotazioni, non le ricette!**\n🏖️ Ma a Palinuro trovi cucina cilentana autentica.\n💡 **Prenota Villa Celi**: 'disponibilità agosto 2025'",
        "activity": "🏖️ **A Palinuro ci sono mille attività!**\n🌊 Mare, grotte, trekking, cultura del Cilento.\n💡 **Prenota l'avventura**: 'disponibilità settembre 2025'",
        "unknown": "🤔 **Non ho capito la richiesta**.\n🔍 **Prova**: 'disponibilità luglio 2025' o 'dove si trova'\n💡 **Oppure scrivi 'ciao' per ricominciare!**"
    }
    return fallbacks.get(reason, fallbacks["unknown"])

# ====================================
# FUNZIONI DATABASE
# ====================================

def get_db_connection():
    """Connessione database SQLite con gestione errori"""
    try:
        if not os.path.exists(Config.DB_PATH):
            conn = sqlite3.connect(Config.DB_PATH)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS appartamenti (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appartamento TEXT NOT NULL,
                    check_in TEXT NOT NULL,
                    check_out TEXT NOT NULL
                )
            ''')
            conn.commit()
            conn.close()
            logger.info(f"Database creato: {Config.DB_PATH}")
        
        conn = sqlite3.connect(Config.DB_PATH, isolation_level=None)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn
    except Exception as e:
        logger.error(f"Errore connessione database: {e}")
        raise

# ====================================
# FUNZIONI CORE BUSINESS LOGIC
# ====================================

def query_appartamenti(month, year, apartment_name=None):
    """Trova settimane libere sabato-sabato"""
    try:
        conn = get_db_connection()
        
        # Recupera appartamenti dal DB
        all_apartments_query = "SELECT DISTINCT appartamento FROM appartamenti ORDER BY appartamento;"
        cursor = conn.execute(all_apartments_query)
        all_apartments_in_db = [row[0] for row in cursor.fetchall()]
        
        apartments_to_check = [apartment_name.capitalize()] if apartment_name else all_apartments_in_db

        if not apartments_to_check:
            logger.warning("Nessun appartamento trovato")
            return []

        # Range del mese
        start_month_date = datetime(year, month, 1)
        if month == 12:
            end_month_date = datetime(year, 12, 31)
        else:
            end_month_date = datetime(year, month + 1, 1) - timedelta(days=1)

        logger.info(f"Cercando disponibilità per {month}/{year} dal {start_month_date.date()} al {end_month_date.date()}")

        final_availabilities = []

        for apt_name_to_check in apartments_to_check:
            try:
                # Periodi occupati
                occupied_query = """
                SELECT check_in, check_out
                FROM appartamenti
                WHERE appartamento = ?
                  AND check_in <= ?
                  AND check_out >= ?
                ORDER BY check_in;
                """
                
                cursor = conn.execute(occupied_query, (
                    apt_name_to_check,
                    end_month_date.strftime('%Y-%m-%d'),
                    start_month_date.strftime('%Y-%m-%d')
                ))
                
                occupied_periods_raw = cursor.fetchall()
                
                occupied_periods_for_apt = []
                for occ in occupied_periods_raw:
                    try:
                        ci_str, co_str = occ
                        occupied_periods_for_apt.append({
                            'check_in': datetime.strptime(ci_str, '%Y-%m-%d'),
                            'check_out': datetime.strptime(co_str, '%Y-%m-%d')
                        })
                    except ValueError as ve:
                        logger.warning(f"Formato data non valido: {occ} in {apt_name_to_check}: {ve}")
                        continue

                logger.info(f"Appartamento {apt_name_to_check}: {len(occupied_periods_for_apt)} periodi occupati")

                # Genera settimane sabato-sabato
                current_saturday = start_month_date
                while current_saturday.weekday() != 5:
                    current_saturday -= timedelta(days=1)

                while current_saturday <= end_month_date:
                    week_start = current_saturday
                    week_end = week_start + timedelta(days=7)

                    if not (week_end < start_month_date or week_start > end_month_date):
                        is_week_free_for_apt = True
                        
                        for occupied in occupied_periods_for_apt:
                            if (week_start < occupied['check_out'] and week_end > occupied['check_in']):
                                is_week_free_for_apt = False
                                break
                        
                        if is_week_free_for_apt:
                            final_availabilities.append((
                                len(final_availabilities) + 1,
                                apt_name_to_check,
                                week_start.strftime('%Y-%m-%d'),
                                week_end.strftime('%Y-%m-%d')
                            ))
                            logger.info(f"Settimana libera: {apt_name_to_check} {week_start.date()}-{week_end.date()}")
                    
                    current_saturday += timedelta(days=7)
                    
            except Exception as e:
                logger.error(f"Errore elaborazione appartamento {apt_name_to_check}: {e}")
                continue
        
        conn.close()
        logger.info(f"Totale disponibilità trovate: {len(final_availabilities)}")
        return final_availabilities
        
    except Exception as e:
        logger.error(f"Errore calcolo disponibilità: {e}")
        return []

def format_date_italian(date_str):
    """Formatta data in italiano"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        months = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                  'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
        return f"{date_obj.day} {months[date_obj.month]}"
    except:
        return date_str

def generate_availability_response(results):
    """Genera risposta con lista disponibilità"""
    if not results:
        return {
            "message": "❌ **Nessuna settimana libera** per il periodo richiesto.\n💡 Prova altri mesi o contattaci per soluzioni personalizzate!",
            "type": "no_availability",
            "availability_count": 0
        }
    
    results.sort(key=lambda x: (x[1], x[2])) 
    message_parts = ["✅ **Disponibilità trovate** (settimane sabato-sabato):\n"]
    
    grouped_results = {}
    for result in results:
        apt_name = result[1]
        if apt_name not in grouped_results:
            grouped_results[apt_name] = []
        grouped_results[apt_name].append(result)

    global_index = 1
    availability_data_list = []

    for apt_name, apt_results in grouped_results.items():
        message_parts.append(f"\n🏠 **Appartamento: {apt_name}**")
        for result in apt_results:
            id_apt, appartamento, check_in, check_out = result
            check_in_formatted = format_date_italian(check_in)
            check_out_formatted = format_date_italian(check_out)
            
            message_parts.append(f"**{global_index}.** 📅 Da sabato {check_in_formatted} a sabato {check_out_formatted}")
            
            availability_data_list.append({
                "index": global_index,
                "id": id_apt,
                "appartamento": appartamento,
                "check_in": check_in,
                "check_out": check_out,
                "check_in_formatted": check_in_formatted,
                "check_out_formatted": check_out_formatted
            })
            global_index += 1
    
    message_parts.append("\n💡 **Per prenotare**, scrivi il numero che preferisci. Esempio: *\"voglio prenotare la 1\"*")
    
    return {
        "message": "\n".join(message_parts),
        "type": "availability_list",
        "availability_count": len(results),
        "availability_data": availability_data_list
    }

def generate_booking_response(booking_choice, session_id):
    """Genera risposta di prenotazione con booking_data"""
    session_data = session_cache.get(session_id, {})
    availability_data = session_data.get('availability_data', [])
    
    if not availability_data:
        return {
            "message": "❌ **Errore**: Prima cerca le disponibilità, poi scegli il numero da prenotare.",
            "type": "error"
        }
    
    booking_item = None
    for item in availability_data:
        if item['index'] == booking_choice:
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

    return {
        "message": message,
        "type": "booking_redirect",
        "booking_data": booking_data
    }

def find_predefined_response(message):
    """Cerca risposta predefinita per il messaggio"""
    message_lower = message.lower().strip()
    
    logger.info(f"🔍 Cercando risposta predefinita per: '{message_lower}'")
    
    priority_matches = {
        "dove": "dove si trova",
        "trova": "dove si trova", 
        "palinuro": "dove si trova",
        "arriva": "come si arriva",
        "raggiungere": "come si arriva",
        "attività": "attività",
        "cosa fare": "cosa",
        "fare": "fare",
        "spiagge": "spiagge",
        "mare": "mare",
        "servizi": "servizi",
        "prezzo": "prezzo",
        "costo": "prezzo",
    }
    
    for keyword, response_key in priority_matches.items():
        if keyword in message_lower:
            if response_key in PREDEFINED_RESPONSES:
                logger.info(f"✅ Risposta predefinita trovata: {response_key}")
                return PREDEFINED_RESPONSES[response_key]
    
    for key, response in PREDEFINED_RESPONSES.items():
        if key in message_lower:
            logger.info(f"✅ Corrispondenza diretta trovata: {key}")
            return response
    
    logger.info("❌ Nessuna risposta predefinita trovata")
    return None

def analyze_message(message):
    """Analizza messaggio per identificare tipo richiesta - VERSIONE OTTIMIZZATA"""
    message_lower = message.lower().strip()
    
    logger.info(f"🔍 Analizzando messaggio: '{message}'")

    # 0. CONTROLLO PRIORITARIO: Risposte predefinite
    predefined_response = find_predefined_response(message)
    if predefined_response:
        return 'predefined_response', predefined_response

    detected_month = None
    detected_year = None
    detected_apartment = None

    # 1. PATTERN PRENOTAZIONE (alta priorità)
    if re.match(r'^\d+$', message_lower):
        try:
            choice_number = int(message_lower)
            logger.info(f"✅ Riconosciuto numero puro: {choice_number}")
            return 'booking_request', choice_number
        except ValueError:
            pass
    
    booking_patterns = [
        r'voglio prenotare.*(\d+)', r'prenota.*(\d+)', r'scelgo.*(\d+)',
        r'prendo.*(\d+)', r'numero.*(\d+)', r'la\s*(\d+)', r'il\s*(\d+)'
    ]
    for pattern in booking_patterns:
        match = re.search(pattern, message_lower)
        if match:
            try:
                choice_number = int(match.group(1))
                logger.info(f"✅ Riconosciuta richiesta prenotazione: {choice_number}")
                return 'booking_request', choice_number
            except ValueError:
                continue

    # 2. PATTERN DISPONIBILITÀ
    availability_keywords = ['disponibilit', 'liber', 'case', 'libero', 'appartament', 'disponibil']
    has_availability_keyword = any(word in message_lower for word in availability_keywords)
    
    if has_availability_keyword:
        logger.info("🏠 Riconosciuta richiesta di disponibilità")
        
        # Estrai mese
        for month_name, month_num in MONTH_MAP.items():
            if month_name in message_lower:
                detected_month = month_num
                logger.info(f"📅 Mese trovato: {month_name} ({month_num})")
                break
        
        # Estrai anno
        year_match = re.search(r'202[4-9]|20[3-9]\d', message_lower)
        if year_match:
            detected_year = int(year_match.group(0))
            logger.info(f"📅 Anno trovato: {detected_year}")
        elif detected_month:
            current_year = datetime.now().year
            if detected_month < datetime.now().month:
                detected_year = current_year + 1
            else:
                detected_year = current_year
            logger.info(f"📅 Anno inferito: {detected_year}")

        # Estrai appartamento
        try:
            conn = get_db_connection()
            cursor = conn.execute("SELECT DISTINCT appartamento FROM appartamenti;")
            apartment_names_in_db = [row[0].lower() for row in cursor.fetchall()]
            conn.close()
            
            for apt_name in apartment_names_in_db:
                if re.search(r'\b' + re.escape(apt_name) + r'\b', message_lower):
                    detected_apartment = apt_name
                    logger.info(f"🏠 Appartamento trovato: {apt_name}")
                    break
        except Exception as e:
            logger.error(f"Errore recupero nomi appartamenti: {e}")

        if detected_month and detected_year:
            return 'availability_request', {
                'month': detected_month, 
                'year': detected_year, 
                'apartment': detected_apartment
            }
        elif detected_apartment and not detected_month:
            return 'missing_info_availability', {'apartment': detected_apartment}

    # 3. SALUTI
    greeting_patterns = [
        r'^ciao\s*$', r'^salve\s*$', r'^buongiorno\s*$', r'^buonasera\s*$', 
        r'^help\s*$', r'^aiuto\s*$', r'^inizia\s*$'
    ]
    
    for pattern in greeting_patterns:
        if re.match(pattern, message_lower):
            logger.info(f"👋 Riconosciuto saluto: {message_lower}")
            return 'greeting', None
    
    # 4. TEST (da handle_query_complete.py)
    if 'test' in message_lower:
        return 'test_request', None
    
    # 5. TUTTO IL RESTO
    logger.info(f"❓ Messaggio non riconosciuto: '{message}'")
    return 'unknown', None

def generate_ollama_response(prompt):
    """Fallback Ollama OTTIMIZZATO con cache hash"""
    logger.info(f"🤖 Chiamando Ollama per: '{prompt[:50]}...'")
    
    # Cache con hash (più efficiente)
    cache_key = f"ollama_{hashlib.md5(prompt.encode()).hexdigest()[:8]}"
    if cache_key in response_cache:
        logger.info("📋 Risposta trovata in cache")
        return response_cache[cache_key]
    
    try:
        # Prompt OTTIMIZZATO per Villa Celi
        enhanced_prompt = f"""Sei Paguro, l'assistente virtuale di Villa Celi, appartamenti vacanze a PALINURO nel Cilento (Salerno).

REGOLE FERREE:
- Rispondi SOLO su Palinuro/Cilento/Villa Celi
- Massimo 3 righe
- Sempre orientato alle prenotazioni
- NON menzionare altre località

Domanda dell'ospite: {prompt}

Risposta breve e focalizzata:"""

        logger.info("📡 Inviando richiesta a Ollama...")
        response = requests.post(
            Config.OLLAMA_URL,
            json={
                "model": Config.OLLAMA_MODEL,
                "prompt": enhanced_prompt,
                "stream": False,
                "options": {
                    "temperature": Config.OLLAMA_TEMPERATURE,
                    "num_ctx": Config.OLLAMA_NUM_CTX,
                    "num_predict": 150
                }
            },
            timeout=Config.OLLAMA_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json().get("response", "").strip()
            logger.info(f"✅ Ollama risposta ricevuta: '{result[:50]}...'")
            
            if result:
                # Cache con limite dimensioni
                if len(response_cache) < Config.RESPONSE_CACHE_SIZE:
                    response_cache[cache_key] = result
                return result
            else:
                logger.warning("⚠️ Ollama risposta vuota")
                return None
        else:
            logger.error(f"❌ Ollama errore HTTP: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("⏰ Timeout Ollama")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"🔗 Errore connessione Ollama: {e}")
        return None
    except Exception as e:
        logger.error(f"💥 Errore generico Ollama: {e}")
        return None

def handle_query(message, session_id):
    """Gestisce query con POST-PROCESSING COMPLETO"""
    try:
        request_type, param = analyze_message(message)
        
        logger.info(f"📋 [{session_id}] Messaggio: '{message}' -> Tipo: {request_type}")
        
        # GESTIONE PRIORITARIA: Risposte predefinite (già ottimizzate)
        if request_type == 'predefined_response':
            logger.info("✅ Usando risposta predefinita")
            return {
                "message": param,  # Già ottimizzate
                "type": "predefined_response"
            }
        
        elif request_type == 'availability_request':
            month_num = param.get('month')
            year_num = param.get('year')
            apt_name = param.get('apartment')

            if not month_num or not year_num:
                return {
                    "message": "Mi dispiace, per la disponibilità ho bisogno di un mese e un anno.\nEsempio: 'disponibilità luglio 2025' o 'appartamenti liberi agosto'.",
                    "type": "error"
                }

            logger.info(f"🔍 Cercando disponibilità per {month_num}/{year_num}, appartamento: {apt_name}")
            results = query_appartamenti(month_num, year_num, apt_name)
            response = generate_availability_response(results)
            
            if response['type'] == 'availability_list':
                session_cache[session_id] = {
                    'last_query': 'availability',
                    'availability_data': response.get('availability_data', []),
                    'timestamp': datetime.now()
                }
            
            return response
            
        elif request_type == 'missing_info_availability':
            apt_name = param.get('apartment')
            return {
                "message": f"Per l'appartamento **{apt_name.capitalize()}**, in che mese e anno?\nEsempio: 'disponibilità {apt_name} luglio 2025'.",
                "type": "prompt_for_info"
            }
            
        elif request_type == 'booking_request':
            return generate_booking_response(param, session_id)
            
        elif request_type == 'greeting':
            return {
                "message": "👋 **Ciao!** Sono Paguro, l'assistente per le prenotazioni di Villa Celi a Palinuro.\n💡 **Scrivi** \"disponibilità luglio 2025\" o \"dove si trova\" per iniziare!",
                "type": "greeting"
            }
        
        elif request_type == 'test_request':
            return {
                "message": "✅ **Test Paguro OK!** Sistema operativo per Villa Celi.\n💡 **Prova**: 'disponibilità luglio 2025'",
                "type": "test"
            }
        
        elif request_type == 'unknown':
            # OLLAMA con POST-PROCESSING COMPLETO
            logger.info("🤖 Processando richiesta generica con Ollama...")
            
            # Classifica tipo per CTA specifico
            response_type = classify_response_type(message)
            
            # Crea prompt contestualizzato
            context_prompt = f"""Sei l'assistente virtuale di Villa Celi, appartamenti vacanze a Palinuro nel Cilento. 
            Rispondi in modo cordiale e professionale a questa domanda dell'ospite: {message}
            
            Mantieni la risposta breve e utile. Se non conosci informazioni specifiche, invita gentilmente a contattare Villa Celi."""
            
            ollama_response = generate_ollama_response(context_prompt)
            
            if ollama_response:
                # POST-PROCESSING COMPLETO
                processed_response = post_process_response(ollama_response, response_type)
                logger.info("✅ Risposta Ollama post-processata")
                return {
                    "message": processed_response,
                    "type": "ollama_response"
                }
            else:
                # FALLBACK SPECIFICO PER TIPO
                fallback_response = get_fallback_response(response_type)
                logger.warning("⚠️ Ollama non disponibile, usando fallback specifico")
                return {
                    "message": fallback_response,
                    "type": "fallback_response"
                }
        
        else:
            logger.error(f"❌ Tipo di richiesta non gestito: {request_type}")
            return {
                "message": get_fallback_response("unknown"),
                "type": "error"
            }
            
    except Exception as e:
        logger.error(f"💥 Errore in handle_query: {e}", exc_info=True)
        return {
            "message": get_fallback_response("unknown"),
            "type": "error"
        }

def generate_session_id():
    """Genera ID sessione unico"""
    return f"session_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}"

# ====================================
# FLASK ENDPOINTS
# ====================================

logger.info("🚀 [DEBUG] Registrando endpoint Flask...")

@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint di health check"""
    logger.info("🏥 [DEBUG] Health endpoint chiamato")
    return jsonify({
        "status": "ok",
        "service": "paguro_receptionist_villa_celi_optimized",
        "timestamp": datetime.now().isoformat(),
        "location": "Palinuro, Cilento",
        "database": "connected" if os.path.exists(Config.DB_PATH) else "missing",
        "features": ["post_processing", "forced_cta", "villa_celi_focus"]
    })

@app.route('/api/chat', methods=['POST'])
@app.route('/api/chatbot', methods=['POST'])
def chat():
    """Endpoint principale chat con POST-PROCESSING"""
    logger.info("🐚 [DEBUG] Chat endpoint chiamato")
    try:
        data = request.get_json()
        
        if not data:
            logger.error("❌ [DEBUG] Nessun JSON ricevuto")
            return jsonify({"error": "No JSON data provided"}), 400
        
        message = data.get('message', '').strip()
        session_id = data.get('session_id', generate_session_id())
        
        if not message:
            logger.error("❌ [DEBUG] Messaggio vuoto")
            return jsonify({"error": "Message is required"}), 400
        
        logger.info(f"📨 [DEBUG] Nuova richiesta: '{message}' [Session: {session_id}]")
        
        # Gestisci la query con post-processing
        response = handle_query(message, session_id)
        response['session_id'] = session_id
        response['timestamp'] = datetime.now().isoformat()
        
        logger.info(f"📤 [DEBUG] Risposta: tipo={response.get('type')}, lunghezza={len(response.get('message', ''))}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"💥 [DEBUG] Errore chat endpoint: {e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": get_fallback_response("unknown"),
            "type": "error"
        }), 500

@app.route('/api/db/appartamenti', methods=['GET'])
def get_appartamenti():
    """Endpoint per debug database"""
    logger.info("🗄️ [DEBUG] Database debug endpoint chiamato")
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT id, appartamento, check_in, check_out FROM appartamenti ORDER BY appartamento, check_in LIMIT 50;")
        results = cursor.fetchall()
        conn.close()
        
        return jsonify({
            "status": "ok",
            "description": "Elenco delle date in cui gli appartamenti sono OCCUPATI.",
            "count": len(results),
            "data": [
                {
                    "id": r[0],
                    "appartamento": r[1],
                    "check_in": r[2],
                    "check_out": r[3]
                }
                for r in results
            ]
        })
    except Exception as e:
        logger.error(f"💥 [DEBUG] Errore debug database: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test_api():
    """Endpoint di test API"""
    logger.info("🧪 [DEBUG] Test API chiamato")
    return jsonify({
        "message": "API Paguro OTTIMIZZATA per Villa Celi Palinuro funzionante!",
        "location": "Palinuro, Cilento",
        "timestamp": datetime.now().isoformat(),
        "status": "ok",
        "optimizations": ["post_processing", "forced_cta", "villa_celi_focus", "response_length_control"]
    }), 200   

# ====================================
# UTILITY FUNCTIONS
# ====================================

def cleanup_sessions():
    """Rimuove sessioni più vecchie di 2 ore"""
    cutoff = datetime.now() - timedelta(hours=2)
    to_remove = []
    
    for session_id, data in session_cache.items():
        if data.get('timestamp', datetime.min) < cutoff:
            to_remove.append(session_id)
    
    for session_id in to_remove:
        del session_cache[session_id]
    
    logger.info(f"🧹 Cleanup: rimosse {len(to_remove)} sessioni scadute")

# ====================================
# MAIN EXECUTION
# ====================================

if __name__ == "__main__":
    logger.info("🚀 [DEBUG] === AVVIO PAGURO OTTIMIZZATO - VILLA CELI PALINURO ===")
    logger.info(f"📂 Database: {Config.DB_PATH}")
    logger.info(f"🤖 Ollama: {Config.OLLAMA_URL}")
    logger.info(f"🎯 Model: {Config.OLLAMA_MODEL}")
    logger.info(f"🏖️ Località: Palinuro, Cilento")
    logger.info(f"✨ Features: Post-processing, CTA forzati, Focus Villa Celi")
    
    # Lista endpoint registrati
    logger.info("📋 [DEBUG] Endpoint registrati:")
    for rule in app.url_map.iter_rules():
        logger.info(f"   {rule.endpoint}: {rule.rule} {list(rule.methods)}")
    
    # Test database
    try:
        conn_test = get_db_connection()
        cursor_test = conn_test.execute("SELECT COUNT(*) FROM appartamenti;")
        count = cursor_test.fetchone()[0]
        conn_test.close()
        logger.info(f"✅ Database OK - {count} record trovati nella tabella 'appartamenti'.")
    except Exception as e:
        logger.error(f"❌ Errore database: {e}")
        logger.info("🔧 Creando database vuoto...")
        try:
            conn = get_db_connection()
            conn.close()
            logger.info("✅ Database creato")
        except Exception as e2:
            logger.error(f"❌ Impossibile creare database: {e2}")
    
    # Test Ollama
    try:
        test_response = generate_ollama_response("Test connessione Villa Celi")
        if test_response:
            logger.info("✅ Ollama OK - Connessione riuscita")
        else:
            logger.warning("⚠️ Ollama Warning - Connessione fallita ma continuo")
    except Exception as e:
        logger.warning(f"⚠️ Ollama non disponibile: {e}")
    
    # Avvia server Flask
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    logger.info(f"🚀 [DEBUG] Paguro OTTIMIZZATO è pronto su http://{host}:{port}")
    logger.info("🚀 [DEBUG] Endpoints disponibili:")
    logger.info("   - GET  /api/health")
    logger.info("   - POST /api/chat")
    logger.info("   - POST /api/chatbot")
    logger.info("   - GET  /api/db/appartamenti")
    logger.info("   - GET  /api/test")
    
    try:
        app.run(host=host, port=port, debug=False)
    except Exception as e:
        logger.error(f"💥 [DEBUG] Errore avvio server: {e}", exc_info=True)
        raise
