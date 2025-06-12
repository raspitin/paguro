# 🐚 Paguro - Dockerfile Backend per Villa Celi
# Receptionist Virtuale AI per Palinuro, Cilento
# VERSIONE CORRETTA: Adattato alla nuova struttura

FROM python:3.11-slim

# Metadata Paguro
LABEL maintainer="Villa Celi <info@villaceli.it>"
LABEL description="🐚 Paguro - Backend API per Villa Celi a Palinuro"
LABEL version="2.0.0"
LABEL location="Palinuro, Cilento, Italia"

# Variabili d'ambiente per Paguro
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV DB_PATH=/app/data/affitti2025.db
ENV OLLAMA_URL=http://ollama:11434/api/generate
ENV MODEL=llama3.2:1b
ENV PORT=5000
ENV HOST=0.0.0.0
ENV VILLA_CELI_FRONTEND=https://www.villaceli.it
ENV API_BASE_URL=https://api.viamerano24.it/api

# Crea utente non-root per sicurezza
RUN groupadd -g 1000 paguro && \
    useradd -u 1000 -g paguro -m -s /bin/bash paguro

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    curl \
    dumb-init \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean

# Crea directory di lavoro
WORKDIR /app

# Copia requirements e installa dipendenze Python
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Crea directory per dati Villa Celi
RUN mkdir -p /app/data /app/logs /app/cache && \
    chown -R paguro:paguro /app

# Copia codice sorgente (ADATTATO ALLA NUOVA STRUTTURA)
# Solo se il file esiste, altrimenti usa quello che c'è
COPY --chown=paguro:paguro . .

# Se non esiste main.py, cerca wordpress_chatbot_api.py e rinominalo
RUN if [ ! -f "main.py" ] && [ -f "wordpress_chatbot_api.py" ]; then \
        mv wordpress_chatbot_api.py main.py; \
        echo "✅ Rinominato wordpress_chatbot_api.py → main.py"; \
    fi

# Crea script di avvio semplificato
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🐚 Avvio Paguro per Villa Celi..."\n\
echo "📍 Località: Palinuro, Cilento"\n\
echo "🌐 Frontend: $VILLA_CELI_FRONTEND"\n\
echo "📡 API: $API_BASE_URL"\n\
echo "🗄️ Database: $DB_PATH"\n\
echo "🤖 Ollama: $OLLAMA_URL"\n\
\n\
# Verifica file principale\n\
if [ -f "main.py" ]; then\n\
    MAIN_FILE="main.py"\n\
elif [ -f "wordpress_chatbot_api.py" ]; then\n\
    MAIN_FILE="wordpress_chatbot_api.py"\n\
else\n\
    echo "❌ Nessun file Python principale trovato!"\n\
    exit 1\n\
fi\n\
\n\
echo "🚀 Avvio Paguro con $MAIN_FILE..."\n\
exec python "$MAIN_FILE"' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh && \
    chown paguro:paguro /app/entrypoint.sh

# Cambia a utente non-root
USER paguro

# Esponi porta per Paguro API
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

# Volume per persistenza dati Villa Celi
VOLUME ["/app/data", "/app/logs"]

# Usa dumb-init per signal handling corretto
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Comando di avvio Paguro
CMD ["/app/entrypoint.sh"]