# 🐚 Paguro - Chatbot WordPress per Villa Celi

**Paguro** è il receptionist virtuale di Villa Celi a Palinuro, nel cuore del Cilento.

chatbot disponibilità appartamenti

## 🌊 Chi è Paguro?

Paguro è il nostro chatbot AI che rappresenta lo spirito accogliente di Villa Celi. Come un vero paguro che trova la sua casa perfetta, Paguro aiuta i nostri ospiti a trovare l'appartamento ideale per le loro vacanze nel Cilento.

## 📋 Caratteristiche

- **🐚 Paguro AI**: Assistente virtuale personalizzato per Villa Celi
- **📅 Gestione Prenotazioni**: Sistema automatico di booking sabato-sabato
- **🔗 Integrazione WordPress**: Plugin completo ottimizzato per Villa Celi
- **🗄️ Database SQLite**: Gestione intelligente disponibilità appartamenti
- **📱 Responsive**: Interfaccia ottimizzata per tutti i dispositivi
- **⚡ API Python Flask**: Backend robusto con risposte predefinite per Palinuro
- **🏖️ Floating Widget**: Paguro sempre disponibile in ogni pagina
- **🎨 Design Coordinato**: Colori e stile armonizzati con il sito Villa Celi

## 🚀 Installazione

### Prerequisiti
- WordPress 5.0+
- PHP 7.4+
- Python 3.8+
- Ninja Forms Plugin

### 1. Plugin WordPress
```bash
# Copia i file nella directory del plugin
wp-content/plugins/paguro-chatbot/
```

### 2. Backend Python (Paguro Brain)
```bash
# Installa dipendenze per Paguro
pip install flask flask-cors requests

# Avvia il cervello di Paguro
python wordpress_chatbot_api.py
```

### 3. Database
- Il database SQLite viene creato automaticamente
- Popola con i dati degli appartamenti di Villa Celi

## 📖 Utilizzo

### Shortcode Paguro Standard
```
[appartamenti_chatbot title="🐚 Paguro - Receptionist Virtuale"]
```

### Widget Floating Paguro
```
[chatbot_floating trigger_text="🐚 Paguro" position="bottom-right"]
```

## 🔧 Configurazione

### WordPress Admin
- **Impostazioni → Paguro Chatbot**
- Configura URL API: `http://127.0.0.1:5000/api` (locale)
- Imposta ID form Ninja Forms per le prenotazioni

### API Python (Cervello di Paguro)
- Modifica `DB_PATH` per il percorso database Villa Celi
- Configura `OLLAMA_URL` se usi Ollama
- Porta predefinita: 5000

## 📁 Struttura Progetto

```
📦 paguro-chatbot/
├── 🐚 chatbot-appartamenti.php     # Plugin principale con Paguro
├── 📁 assets/
│   ├── 🎨 chatbot.css              # Stili coordinati Villa Celi
│   ├── ⚡ chatbot.js               # Frontend Paguro
│   └── 🔧 booking-populate.js      # Auto-popolazione form
├── 🧠 wordpress_chatbot_api.py     # Cervello di Paguro (API Python)
├── 📋 README.md
└── 🚫 .gitignore
```

## 🔄 Flusso Funzionamento Paguro

1. **👋 Benvenuto**: Paguro accoglie l'ospite con personalità unica
2. **🗣️ Conversazione**: L'utente chiede disponibilità ("luglio 2025")
3. **🧠 Elaborazione**: Paguro analizza con AI e database
4. **📋 Risultati**: Mostra disponibilità appartamenti con pulsanti
5. **🎯 Selezione**: Utente sceglie numero appartamento preferito
6. **🔄 Redirect**: Automatico alla pagina prenotazione Villa Celi
7. **📝 Form**: Auto-popolazione campi Ninja Forms
8. **✅ Booking**: Gestione prenotazione completa

## 🛠️ Sviluppo

### Debug Paguro
- Console browser per frontend Paguro
- Log Python per backend (cervello Paguro)
- WordPress debug per plugin

### Personalizzazione
- Modifica risposte in `PREDEFINED_RESPONSES`
- Personalizza stili in `assets/chatbot.css`
- Estendi API in `wordpress_chatbot_api.py`

## 📝 API Endpoints Paguro

- `GET /api/health` - Health check Paguro
- `POST /api/chatbot` - Chat principale con Paguro
- `GET /api/db/appartamenti` - Debug database Villa Celi
- `GET /api/test` - Test connessione

## 🤝 Contribuire a Paguro

1. Fork del progetto Villa Celi
2. Crea feature branch (`git checkout -b feature/PaguroEnhancement`)
3. Commit modifiche (`git commit -m 'Add: nuova funzionalità Paguro'`)
4. Push branch (`git push origin feature/PaguroEnhancement`)
5. Apri Pull Request

## 📄 Licenza

Questo progetto è sotto licenza MIT - vedi file [LICENSE](LICENSE) per dettagli.

## 👨‍💻 Team Villa Celi

**Andrea**
- Email: andrea@villaceli.it
- Località: Villa Celi, Palinuro - Cilento

## 🔗 Links Utili

- 🏖️ [Villa Celi Official](https://www.villaceli.it)
- 📝 [WordPress Plugin Directory](https://wordpress.org/plugins/)
- 🥷 [Ninja Forms](https://ninjaforms.com/)
- ⚡ [Flask Documentation](https://flask.palletsprojects.com/)
- 🤖 [Ollama Models](https://ollama.ai/library)

---
🐚 **Paguro ti aspetta a Villa Celi, nel cuore del Cilento!**

⭐ Se questo progetto ti è utile, lascia una stella e aiuta Paguro a crescere!
