#!/bin/bash
# Script para crear aplicación de escritorio
# Calculadora de Turnos en Radiología v0.8.1

echo "===================================================="
echo "  Crear Aplicación de Escritorio"
echo "  Calculadora de Turnos en Radiología v0.8.1"
echo "===================================================="

# Determinar el sistema operativo
OS=$(uname -s)

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 no está instalado."
    echo "Por favor, instale Python 3 antes de continuar."
    exit 1
fi

# Crear entorno virtual para no afectar el sistema
echo "Creando entorno virtual..."
python3 -m venv env
if [ $? -ne 0 ]; then
    echo "Error al crear el entorno virtual."
    exit 1
fi

# Activar entorno virtual
if [ "$OS" = "Darwin" ] || [ "$OS" = "Linux" ]; then
    source env/bin/activate
else
    source env/Scripts/activate
fi

# Ejecutar el script de creación de ejecutable
echo "Iniciando creación del ejecutable..."
python crear_ejecutable.py

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "===================================================="
    echo "  ¡Aplicación de escritorio creada con éxito!"
    echo "===================================================="
    echo ""
    echo "La aplicación se encuentra en el directorio:"
    echo "  $(pwd)/dist/CalculadoraTurnos"
    echo ""
    echo "Puede copiar esta carpeta completa a cualquier ubicación."
    echo "Para ejecutar la aplicación, simplemente haga doble clic"
    echo "en el archivo 'CalculadoraTurnos'."
    echo ""
    echo "También se intentó crear un acceso directo en su escritorio."
    echo "===================================================="
else
    echo ""
    echo "===================================================="
    echo "  Ocurrió un error durante la creación."
    echo "  Por favor, revise los mensajes de error anteriores."
    echo "===================================================="
fi

# Desactivar entorno virtual
deactivate