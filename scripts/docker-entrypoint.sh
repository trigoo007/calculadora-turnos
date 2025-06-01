#!/bin/bash
set -e

echo "==================================================="
echo "  Calculadora de Turnos en Radiología v0.8.1"
echo "==================================================="

# Actualizar los archivos de requisitos
echo "Instalando dependencias..."
echo "streamlit==1.45.0" > requirements.txt
echo "pandas==2.0.3" >> requirements.txt
echo "numpy==1.24.3" >> requirements.txt
echo "plotly==5.18.0" >> requirements.txt
echo "openpyxl==3.1.2" >> requirements.txt
echo "python-dateutil==2.8.2" >> requirements.txt
echo "requests==2.31.0" >> requirements.txt

# Instalar las dependencias actualizadas
pip install --no-cache-dir -r requirements.txt

# Verificar los directorios necesarios
echo "Verificando directorios..."
mkdir -p /app/logs
mkdir -p /app/temp
mkdir -p /app/conocimiento
mkdir -p /app/csv

# Ejecutar la aplicación Streamlit
echo "Iniciando la aplicación Streamlit..."
echo "La aplicación estará disponible en http://localhost:8501"
echo "==================================================="
exec streamlit run ui/calculadora_streamlit.py