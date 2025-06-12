FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/app/data/affitti2025.db
ENV OLLAMA_URL=http://ollama:11434/api/generate
ENV MODEL=llama3.2:1b
ENV PORT=5000
ENV HOST=0.0.0.0

# User setup
RUN groupadd -g 1000 paguro && \
    useradd -u 1000 -g paguro -m -s /bin/bash paguro

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc sqlite3 curl dumb-init \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Create directories
RUN mkdir -p /app/data /app/logs /app/cache && \
    chown -R paguro:paguro /app

# Copy all files
COPY --chown=paguro:paguro . .

# Create fallback Python file
COPY --chown=paguro:paguro <<EOF /app/paguro_fallback.py
#!/usr/bin/env python3
from flask import Flask, jsonify
from flask_cors import CORS
import os, sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "service": "paguro_fallback_villaceli",
        "timestamp": datetime.now().isoformat(),
        "location": "Palinuro, Cilento",
        "message": "🐚 Paguro Fallback per Villa Celi"
    })

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        "message": "🏖️ Villa Celi - Paguro Fallback OK!",
        "appartamenti": ["Tartaruga", "Corallo"],
        "status": "fallback_ok"
    })

@app.route('/api/db/test', methods=['GET'])
def test_db():
    try:
        conn = sqlite3.connect(os.environ.get('DB_PATH', '/app/data/affitti2025.db'))
        cursor = conn.execute('SELECT COUNT(*) FROM appartamenti')
        count = cursor.fetchone()[0]
        conn.close()
        return jsonify({
            "database": "connected",
            "records": count,
            "message": f"🗄️ Database Villa Celi OK - {count} prenotazioni"
        })
    except Exception as e:
        return jsonify({
            "database": "error", 
            "error": str(e),
            "message": "❌ Errore database"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    print("🐚 Avvio Paguro Fallback per Villa Celi...")
    print(f"🌐 Porta: {port}")
    print(f"🗄️ Database: {os.environ.get('DB_PATH', '/app/data/affitti2025.db')}")
    app.run(host=host, port=port, debug=False)
EOF

# Create simple entrypoint
COPY --chown=paguro:paguro <<EOF /app/entrypoint.sh
#!/bin/bash
set -e

echo "🐚 Avvio Paguro per Villa Celi..."
echo "📍 Località: Palinuro, Cilento"
echo "🗄️ Database: \$DB_PATH"
echo "🤖 Ollama: \$OLLAMA_URL"
echo ""

echo "🔍 File Python disponibili:"
ls -la /app/*.py 2>/dev/null || echo "Nessun file .py trovato"
echo ""

# Find Python file to run
if [ -f "/app/wordpress_chatbot_api.py" ]; then
    MAIN_FILE="wordpress_chatbot_api.py"
    echo "✅ USANDO: wordpress_chatbot_api.py (ORIGINALE)"
elif [ -f "/app/main.py" ]; then
    MAIN_FILE="main.py"  
    echo "✅ USANDO: main.py"
else
    MAIN_FILE="paguro_fallback.py"
    echo "⚠️ USANDO: paguro_fallback.py (FALLBACK)"
fi

echo "🚀 Avvio: python \$MAIN_FILE"
echo ""

exec python "\$MAIN_FILE"
EOF

RUN chmod +x /app/entrypoint.sh && \
    chown paguro:paguro /app/entrypoint.sh /app/paguro_fallback.py

USER paguro
EXPOSE $PORT

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

VOLUME ["/app/data", "/app/logs"]

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/app/entrypoint.sh"]