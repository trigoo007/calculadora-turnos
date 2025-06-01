#!/bin/bash

# Script para ejecutar la aplicación Streamlit

# Cambiar al directorio del proyecto
cd "$(dirname "$0")"

# Configurar PYTHONPATH
export PYTHONPATH="$PWD:$PYTHONPATH"

# Puerto a usar
PORT=8505

echo "🚀 Iniciando Calculadora de Turnos..."
echo "📁 Directorio de trabajo: $PWD"
echo "🌐 La aplicación se abrirá en: http://localhost:$PORT"
echo "📌 Para detener la aplicación, presiona Ctrl+C"
echo ""

# Ejecutar Streamlit
streamlit run src/ui/streamlit_app.py --server.port $PORT 