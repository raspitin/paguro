#!/bin/bash
set -e

# Avvia il server Ollama in background
/bin/ollama serve &

# Cattura il PID del processo ollama serve
OLLAMA_PID=$!

echo "Ollama server avviato in background con PID: $OLLAMA_PID"

# Attendi che il server Ollama sia pronto sulla porta 11434
echo "Attendendo che Ollama sia pronto..."
ATTEMPTS=0
MAX_ATTEMPTS=60 # 60 * 1 secondo = 60 secondi di attesa
while ! curl -s http://localhost:11434/api/version > /dev/null; do
  ATTEMPTS=$((ATTEMPTS+1))
  if [ $ATTEMPTS -ge $MAX_ATTEMPTS ]; then
    echo "Errore: Ollama non è partito in tempo. Controlla i log."
    exit 1
  fi
  sleep 1
done
echo "Ollama è pronto!"

# Esegui il pull del modello
echo "Effettuando il pull del modello: llama3.2:1b"
/bin/ollama pull llama3.2:1b

echo "Download del modello completato."

# Mantiene il processo serve in foreground (assicura che il container non si fermi)
wait $OLLAMA_PID
