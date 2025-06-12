# 🐚 Paguro - Chatbot Villa Celi

**Receptionist Virtuale AI per Villa Celi a Palinuro, Cilento**

## 🏖️ Panoramica

Paguro è il sistema di prenotazione automatizzato per Villa Celi, che combina:
- **Backend Python Flask** con AI Ollama
- **Plugin WordPress** per integrazione frontend
- **Database SQLite** per gestione disponibilità
- **Docker** per deployment scalabile

## 🚀 Quick Start

```bash
# Clone e setup
git clone [repo-url]
cd paguro-villa-celi

# Build e avvio (COMANDO AGGIORNATO)
./scripts/build.sh build

# Verifica stato
./deployment/scripts/deploy.sh status
```

## 📁 Struttura Progetto

```
paguro-villa-celi/
├── backend/          # API Python Flask
├── wordpress-plugin/ # Plugin WordPress
├── deployment/       # Script deploy e config
├── scripts/          # Utility scripts
└── docs/            # Documentazione
```

## 🔗 Links

- **Villa Celi**: https://www.villaceli.it
- **API**: https://api.viamerano24.it/api
- **Docs**: [docs/](docs/)

## 🛠️ Comandi Principali

```bash
# Build (AGGIORNATO con docker compose)
docker compose build

# Avvio
docker compose up -d

# Stop
docker compose down

# Test
./scripts/test.sh
```

## 📄 Licenza

MIT License - Villa Celi, Palinuro

---
🐚 **Paguro ti aspetta a Villa Celi nel Cilento!**
