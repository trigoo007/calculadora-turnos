#!/bin/bash
# Script mejorado para ejecutar CalculadoraTurnos sin problema de duplicación

# Ir al directorio de la aplicación
cd "/Users/rodrigomunoz/Calculadora/dist/CalculadoraTurnos"

# Verificar si hay un proceso de la calculadora ya en ejecución
if pgrep -f "CalculadoraTurnos" > /dev/null; then
    echo "La aplicación ya está en ejecución. Abriendo solo el navegador..."
    # Esperar a que Streamlit esté disponible
    sleep 3
    open "http://localhost:8501"
else
    # Ejecutar la aplicación
    ./CalculadoraTurnos
fi