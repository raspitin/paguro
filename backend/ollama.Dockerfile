FROM ollama/ollama:latest

# Installa curl per healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copia e rendi eseguibile lo script di entrypoint
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Esponi porta
EXPOSE 11434

# Entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
