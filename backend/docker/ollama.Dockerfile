# ollama.Dockerfile
FROM ollama/ollama:latest

# Installa curl per il healthcheck e per lo script
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copia l'entrypoint script e rendilo eseguibile
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Imposta l'entrypoint per il container
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
