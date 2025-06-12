#!/bin/bash
set -e

# Avvia Ollama in background
/bin/ollama serve &
OLLAMA_PID=$!

echo "🤖 Ollama server avviato con PID: $OLLAMA_PID"

# Attendi che Ollama sia pronto
echo "⏳ Attendendo Ollama..."
for i in {1..60}; do
    if curl -s http://localhost:11434/api/version > /dev/null; then
        echo "✅ Ollama pronto!"
        break
    fi
    sleep 1
done

# Download modello
echo "📥 Download modello llama3.2:1b..."
/bin/ollama pull llama3.2:1b

echo "🚀 Ollama configurato e pronto!"

# Mantieni in foreground
wait $OLLAMA_PID
