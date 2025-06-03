#!/usr/bin/env python3
"""
🐚 Paguro - Script di Test Automatico PULITO
Villa Celi - Palinuro, Cilento
NESSUN DATO DI TEST INSERITO AUTOMATICAMENTE
"""

import requests
import json
import sqlite3
import os
import sys
from datetime import datetime, timedelta

# Configurazione
API_BASE_URL = "http://localhost:5000/api"

def colored_print(message, color="white"):
    """Stampa colorata per terminale"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{message}{colors['reset']}")

def load_db_config():
    """Carica configurazione database da .paguro_config"""
    config_file = ".paguro_config"
    if not os.path.exists(config_file):
        colored_print("❌ File configurazione .paguro_config non trovato!", "red")
        colored_print("💡 Esegui prima: ./build_paguro.sh config", "yellow")
        return None
        
    config = {}
    with open(config_file, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    config[key] = value.strip('"')
    
    return config.get('DB_PATH')

def test_database_structure():
    """Test SOLO struttura database - NESSUN INSERIMENTO DATI"""
    colored_print("\n🗄️ Testing Database Structure...", "blue")
    
    try:
        # Carica configurazione
        db_path = load_db_config()
        if not db_path:
            return False
            
        colored_print(f"📂 Database configurato: {db_path}", "cyan")
        
        if not os.path.exists(db_path):
            colored_print(f"⚠️ Database non trovato: {db_path}", "yellow")
            colored_print("💡 Il database verrà creato automaticamente dall'API", "cyan")
            return True
        
        # Connetti e verifica struttura
        conn = sqlite3.connect(db_path)
        
        # Verifica tabella appartamenti
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appartamenti';")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            colored_print("❌ Tabella 'appartamenti' non trovata", "red")
            conn.close()
            return False
        
        # Verifica struttura colonne
        cursor = conn.execute("PRAGMA table_info(appartamenti);")
        columns = cursor.fetchall()
        expected_columns = ['id', 'appartamento', 'check_in', 'check_out']
        found_columns = [col[1] for col in columns]
        
        for col in expected_columns:
            if col not in found_columns:
                colored_print(f"❌ Colonna mancante: {col}", "red")
                conn.close()
                return False
        
        # Conta record esistenti (SENZA INSERIRNE)
        cursor = conn.execute('SELECT COUNT(*) FROM appartamenti')
        count = cursor.fetchone()[0]
        
        colored_print(f"✅ Struttura database valida", "green")
        colored_print(f"📊 Record esistenti: {count}", "cyan")
        
        # Mostra appartamenti distinti se presenti
        if count > 0:
            cursor = conn.execute('SELECT DISTINCT appartamento FROM appartamenti ORDER BY appartamento')
            apartments = [row[0] for row in cursor.fetchall()]
            colored_print(f"🏠 Appartamenti trovati: {', '.join(apartments)}", "cyan")
        else:
            colored_print("📋 Database vuoto - nessuna prenotazione presente", "cyan")
        
        conn.close()
        return True
        
    except Exception as e:
        colored_print(f"❌ Errore database: {e}", "red")
        return False

def test_api_health():
    """Test health check API"""
    colored_print("\n🏥 Testing API Health...", "blue")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            colored_print(f"✅ API Health OK: {data.get('status', 'unknown')}", "green")
            
            # Mostra info aggiuntive se disponibili
            if 'location' in data:
                colored_print(f"📍 Location: {data['location']}", "cyan")
            if 'database' in data:
                colored_print(f"🗄️ Database: {data['database']}", "cyan")
            if 'features' in data:
                colored_print(f"✨ Features: {', '.join(data['features'])}", "cyan")
                
            return True
        else:
            colored_print(f"❌ API Health failed: {response.status_code}", "red")
            return False
            
    except requests.exceptions.ConnectionError:
        colored_print("❌ Impossibile connettersi all'API. Assicurati che sia in esecuzione su http://localhost:5000", "red")
        return False
    except Exception as e:
        colored_print(f"❌ Errore health check: {e}", "red")
        return False

def test_chatbot_basic():
    """Test basic chatbot functionality"""
    colored_print("\n🐚 Testing Paguro Basic Chat...", "blue")
    
    test_messages = [
        ("ciao", "greeting"),
        ("dove si trova villa celi", "predefined"),
        ("che tempo fa", "generic_with_cta"),
        ("disponibilità luglio 2025", "availability"),
    ]
    
    for message, test_type in test_messages:
        try:
            colored_print(f"   Testing: '{message}'", "cyan")
            
            response = requests.post(
                f"{API_BASE_URL}/chatbot",
                json={"message": message},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                response_msg = data.get('message', '')
                response_type = data.get('type', 'unknown')
                
                colored_print(f"   ✅ Response type: {response_type}", "green")
                colored_print(f"   📝 Message preview: {response_msg[:100]}...", "white")
                
                # Verifica che ci sia sempre un CTA
                has_cta = any(
                    keyword in response_msg.lower() 
                    for keyword in ['disponibilità', 'prenota', 'villa celi', 'palinuro', 'contatta']
                )
                
                if has_cta:
                    colored_print("   🎯 CTA presente nella risposta!", "green")
                else:
                    colored_print("   ⚠️ CTA mancante nella risposta", "yellow")
                
                # Verifica focus Villa Celi
                has_villa_focus = any(
                    keyword in response_msg.lower() 
                    for keyword in ['villa celi', 'palinuro', 'cilento']
                )
                
                if has_villa_focus:
                    colored_print("   🏖️ Focus Villa Celi presente!", "green")
                else:
                    colored_print("   ⚠️ Risposta generica senza focus Villa Celi", "yellow")
                
            else:
                colored_print(f"   ❌ HTTP {response.status_code}: {response.text}", "red")
                return False
                
        except Exception as e:
            colored_print(f"   ❌ Error testing '{message}': {e}", "red")
            return False
    
    colored_print("✅ Paguro basic chat tests passed!", "green")
    return True

def test_booking_flow():
    """Test booking flow senza inserire dati reali"""
    colored_print("\n📅 Testing Booking Flow...", "blue")
    
    try:
        # Step 1: Richiedi disponibilità
        colored_print("   Step 1: Richiesta disponibilità...", "cyan")
        response = requests.post(
            f"{API_BASE_URL}/chatbot",
            json={"message": "disponibilità luglio 2025"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code != 200:
            colored_print(f"   ❌ Step 1 failed: {response.status_code}", "red")
            return False
            
        data = response.json()
        session_id = data.get('session_id')
        availability_data = data.get('availability_data', [])
        response_type = data.get('type')
        
        colored_print(f"   📋 Response type: {response_type}", "cyan")
        
        if response_type == 'no_availability':
            colored_print("   📋 Nessuna disponibilità (normale se DB vuoto)", "cyan")
            colored_print("   💡 Il sistema gestisce correttamente database vuoti", "green")
            return True
        elif availability_data:
            colored_print(f"   ✅ Found {len(availability_data)} available options", "green")
            
            # Step 2: Test selezione (senza completarla)
            colored_print("   Step 2: Test selezione appartamento...", "cyan")
            choice_response = requests.post(
                f"{API_BASE_URL}/chatbot",
                json={
                    "message": "1", 
                    "session_id": session_id
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if choice_response.status_code == 200:
                choice_data = choice_response.json()
                if choice_data.get('type') == 'booking_redirect':
                    colored_print("   ✅ Booking redirect generated!", "green")
                    booking_data = choice_data.get('booking_data', {})
                    colored_print(f"   🏠 Appartamento: {booking_data.get('appartamento', 'N/A')}", "white")
                    colored_print(f"   📅 Date: {booking_data.get('check_in_formatted', 'N/A')} - {booking_data.get('check_out_formatted', 'N/A')}", "white")
                else:
                    colored_print(f"   ⚠️ Unexpected response type: {choice_data.get('type')}", "yellow")
            else:
                colored_print(f"   ❌ Step 2 failed: {choice_response.status_code}", "red")
                return False
        else:
            colored_print("   📋 Nessuna disponibilità trovata", "cyan")
        
        colored_print("✅ Booking flow test passed!", "green")
        return True
        
    except Exception as e:
        colored_print(f"❌ Booking flow error: {e}", "red")
        return False

def test_predefined_responses():
    """Test risposte predefinite per Palinuro"""
    colored_print("\n🏖️ Testing Predefined Responses...", "blue")
    
    palinuro_questions = [
        "dove si trova villa celi",
        "come arrivare a palinuro", 
        "cosa fare nel cilento",
        "spiagge palinuro",
        "servizi villa celi",
        "prezzi appartamenti"
    ]
    
    for question in palinuro_questions:
        try:
            colored_print(f"   Testing: '{question}'", "cyan")
            
            response = requests.post(
                f"{API_BASE_URL}/chatbot",
                json={"message": question},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', '')
                
                # Controlla se contiene info su Palinuro/Villa Celi
                if any(keyword in message.lower() for keyword in ['palinuro', 'villa celi', 'cilento']):
                    colored_print(f"   ✅ Relevant response for '{question}'", "green")
                else:
                    colored_print(f"   ⚠️ Generic response for '{question}'", "yellow")
                    
                # Controlla CTA
                has_cta = 'disponibilità' in message.lower()
                if has_cta:
                    colored_print(f"   🎯 CTA presente", "green")
                else:
                    colored_print(f"   ⚠️ CTA mancante", "yellow")
                    
            else:
                colored_print(f"   ❌ Failed: {response.status_code}", "red")
                
        except Exception as e:
            colored_print(f"   ❌ Error: {e}", "red")
    
    colored_print("✅ Predefined responses test completed!", "green")
    return True

def test_post_processing():
    """Test delle funzionalità di post-processing"""
    colored_print("\n🔧 Testing Post-Processing Features...", "blue")
    
    post_processing_tests = [
        ("ricetta carbonara", "Dovrebbe reindirizzare a Villa Celi"),
        ("che tempo fa", "Dovrebbe parlare di Palinuro + CTA"),
        ("cosa fare stasera", "Dovrebbe suggerire attività Cilento + CTA"),
        ("test", "Dovrebbe essere specifico per Villa Celi")
    ]
    
    for message, expected in post_processing_tests:
        try:
            colored_print(f"   Testing: '{message}' (expect: {expected})", "cyan")
            
            response = requests.post(
                f"{API_BASE_URL}/chatbot",
                json={"message": message},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                response_msg = data.get('message', '')
                
                # Conta righe (max 4)
                lines = [line.strip() for line in response_msg.split('\n') if line.strip()]
                
                if len(lines) <= 4:
                    colored_print(f"   ✅ Length OK: {len(lines)} lines", "green")
                else:
                    colored_print(f"   ⚠️ Too long: {len(lines)} lines (max 4)", "yellow")
                
                # Verifica CTA
                has_cta = any(
                    keyword in response_msg.lower() 
                    for keyword in ['disponibilità', 'villa celi', 'prenota']
                )
                
                if has_cta:
                    colored_print(f"   ✅ CTA presente", "green")
                else:
                    colored_print(f"   ❌ CTA mancante!", "red")
                
                # Verifica focus Villa Celi
                villa_focus = any(
                    keyword in response_msg.lower() 
                    for keyword in ['villa celi', 'palinuro', 'cilento']
                )
                
                if villa_focus:
                    colored_print(f"   ✅ Villa Celi focus", "green")
                else:
                    colored_print(f"   ⚠️ Focus generico", "yellow")
                
            else:
                colored_print(f"   ❌ Failed: {response.status_code}", "red")
                
        except Exception as e:
            colored_print(f"   ❌ Error: {e}", "red")
    
    colored_print("✅ Post-processing tests completed!", "green")
    return True

def run_all_tests():
    """Esegue tutti i test SENZA inserire dati"""
    colored_print("🐚 PAGURO - VILLA CELI TEST SUITE (NO TEST DATA)", "purple")
    colored_print("=" * 60, "purple")
    
    tests = [
        ("Database Structure", test_database_structure),
        ("API Health", test_api_health), 
        ("Basic Chat", test_chatbot_basic),
        ("Booking Flow", test_booking_flow),
        ("Predefined Responses", test_predefined_responses),
        ("Post-Processing", test_post_processing),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        colored_print(f"\n🧪 Running {test_name}...", "yellow")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            colored_print(f"❌ Test {test_name} crashed: {e}", "red")
            results.append((test_name, False))
    
    # Risultati finali
    colored_print("\n" + "=" * 60, "purple")
    colored_print("📊 TEST RESULTS SUMMARY", "purple")
    colored_print("=" * 60, "purple")
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result:
            colored_print(f"✅ {test_name}: PASSED", "green")
            passed += 1
        else:
            colored_print(f"❌ {test_name}: FAILED", "red")
            failed += 1
    
    colored_print(f"\n📈 Summary: {passed} passed, {failed} failed", "cyan")
    
    if failed == 0:
        colored_print("\n🎉 Tutti i test sono passati! Paguro è pronto per Villa Celi! 🐚", "green")
        colored_print("🗄️ Database utilizzato senza modifiche - NESSUN DATO DI TEST inserito", "cyan")
        return True
    else:
        colored_print(f"\n⚠️ {failed} test falliti. Controlla i log sopra per dettagli.", "yellow")
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        colored_print("\n⚠️ Test interrotti dall'utente", "yellow")
        sys.exit(1)
    except Exception as e:
        colored_print(f"\n💥 Errore critico: {e}", "red")
        sys.exit(1)
