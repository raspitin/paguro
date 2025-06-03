# 🐚 Paguro - Dockerfile per Villa Celi
# Receptionist Virtuale AI per Palinuro, Cilento

FROM python:3.11-slim

# Metadata Paguro
LABEL maintainer="Villa Celi <info@villaceli.it>"
LABEL description="🐚 Paguro - Receptionist Virtuale AI per Villa Celi a Palinuro"
LABEL version="1.0.0"
LABEL location="Palinuro, Cilento, Italia"

# Variabili d'ambiente per Paguro
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=wordpress_chatbot_api.py
ENV FLASK_ENV=production
ENV DB_PATH=/app/data/affitti2025.db
ENV OLLAMA_URL=http://ollama:11434/api/generate
ENV MODEL=llama3.2:1b
ENV PORT=5000

# Crea utente non-root per sicurezza con UID/GID 1000
# Crea un gruppo 'paguro' con GID 1000
RUN groupadd -g 1000 paguro && \
    # Crea l'utente 'paguro' con UID 1000 e lo aggiunge al gruppo 'paguro'
    useradd -u 1000 -g paguro -m -s /bin/bash paguro

# Installa dipendenze di sistema (AGGIUNTO SQLITE3 CLIENT + CURL)
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crea directory di lavoro
WORKDIR /app

# Copia requirements per cache layer Docker
COPY requirements-minimal.txt* ./

# Installa dipendenze Python per Paguro
RUN pip install --no-cache-dir -r requirements-minimal.txt || \
    pip install --no-cache-dir \
        flask==2.3.3 \
        flask-cors==4.0.0 \
        requests==2.31.0 \
        python-dotenv==1.0.0 \
        colorlog==6.8.0 \
        gunicorn==21.2.0
# Note: sqlite3 è già incluso in Python standard library

# Crea directory per dati Villa Celi
RUN mkdir -p /app/data /app/logs /app/cache && \
    # **IMPORTANTE: Cambia la proprietà delle directory a 'paguro' (UID 1000, GID 1000)**
    chown -R paguro:paguro /app

# Copia codice sorgente Paguro
COPY wordpress_chatbot_api.py ./
COPY assets/ ./assets/
COPY README.md LICENSE ./

# **IMPORTANTE: Assicurati che tutti i file copiati siano di proprietà di 'paguro'**
RUN chown -R paguro:paguro /app

# Cambia utente
USER paguro

# Esponi porta per Paguro API
EXPOSE $PORT

# Health check per Paguro (CORRETTO CON CURL)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

# Comando di avvio Paguro
CMD ["python", "wordpress_chatbot_api.py"]

# Volume per persistenza dati Villa Celi
VOLUME ["/app/data", "/app/logs"]
