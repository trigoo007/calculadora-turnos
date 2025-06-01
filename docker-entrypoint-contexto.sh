#!/bin/bash
set -e

echo "==================================================="
echo "  Calculadora de Turnos en Radiología v0.9.0"
echo "  Con Integración de Contexto Vectorial"
echo "==================================================="

# Actualizar los archivos de requisitos
echo "Instalando dependencias..."
pip install --no-cache-dir chromadb==0.4.18 sentence-transformers==2.2.2

# Verificar los directorios necesarios
echo "Verificando directorios..."
mkdir -p /app/logs
mkdir -p /app/temp
mkdir -p /app/conocimiento
mkdir -p /app/csv
mkdir -p /root/vectorstore

# Verificar variables de entorno para el túnel de Cloudflare
if [ -z "$CLOUDFLARE_TUNNEL_TOKEN" ]; then
  echo "No se ha proporcionado CLOUDFLARE_TUNNEL_TOKEN, no se configurará el túnel Cloudflare."
  USE_CLOUDFLARE=false
else
  echo "Se ha detectado CLOUDFLARE_TUNNEL_TOKEN, configurando túnel Cloudflare..."
  USE_CLOUDFLARE=true
fi

# Iniciar cloudflared en segundo plano si está configurado
if [ "$USE_CLOUDFLARE" = true ]; then
  echo "Iniciando túnel Cloudflare en segundo plano..."
  cloudflared tunnel run --token $CLOUDFLARE_TUNNEL_TOKEN &
  CLOUDFLARE_PID=$!
  echo "Cloudflared iniciado con PID: $CLOUDFLARE_PID"
  echo "La aplicación estará disponible a través del túnel Cloudflare."
fi

# Verificar autenticación
if [ "$ENABLE_AUTHENTICATION" = "true" ]; then
  echo "Autenticación de Streamlit activada"
  # Verificar si existe el archivo de usuarios
  if [ ! -f "/app/experimental/usuarios.json" ]; then
    echo "Creando archivo de usuarios predeterminado..."
    # Crear archivo de usuarios con admin/calculadora2025
    # El hash corresponde a "calculadora2025"
    echo '{"admin": "4bb8105e6638c0d7bbdec3e3f8940f781f5df03daf5b007f03442b352e4a5f77"}' > /app/experimental/usuarios.json
  fi
fi

# Iniciar la aplicación
echo "Iniciando la aplicación Streamlit..."
echo "La aplicación estará disponible en http://localhost:8501"
echo "==================================================="

# Función para manejar la señal SIGTERM
handle_sigterm() {
  echo "Recibida señal de terminación, cerrando servicios..."
  if [ "$USE_CLOUDFLARE" = true ]; then
    echo "Deteniendo túnel Cloudflare (PID: $CLOUDFLARE_PID)..."
    kill -TERM $CLOUDFLARE_PID
  fi
  exit 0
}

# Registrar la función para la señal SIGTERM
trap handle_sigterm SIGTERM

# Ejecutar la aplicación Streamlit con la interfaz integrada
# Actualizado para usar streamlit_contexto.py como punto de entrada
exec streamlit run experimental/streamlit_contexto.py