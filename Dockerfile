FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos necesarios
COPY requirements.txt .
COPY *.py .
COPY ui ./ui
COPY guardián_arquitectura.py .
COPY csv ./csv
COPY setup.py .
COPY TIMELINE.md .
COPY README*.md .
COPY CLAUDE.md .

# Crear directorios necesarios
RUN mkdir -p temp
RUN mkdir -p conocimiento
RUN mkdir -p recursos
RUN mkdir -p logs

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Script para preparar el entorno y ejecutar la aplicación
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Puerto para Streamlit
EXPOSE 8501

# Comando para iniciar la aplicación
ENTRYPOINT ["./docker-entrypoint.sh"]