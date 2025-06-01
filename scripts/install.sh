#!/bin/bash

# Script de instalación para Calculadora de Turnos
# =================================================

echo "🚀 Instalando Calculadora de Turnos..."
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar Python
echo "📌 Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python $PYTHON_VERSION encontrado${NC}"
else
    echo -e "${RED}✗ Python 3 no encontrado. Por favor instale Python 3.8 o superior${NC}"
    exit 1
fi

# Crear entorno virtual
echo ""
echo "📌 Creando entorno virtual..."
if [ -d "venv" ]; then
    echo "⚠️  El entorno virtual ya existe. ¿Desea recrearlo? (s/n)"
    read -r response
    if [[ "$response" =~ ^([sS])$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo -e "${GREEN}✓ Entorno virtual recreado${NC}"
    else
        echo "↪️  Usando entorno virtual existente"
    fi
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Entorno virtual creado${NC}"
fi

# Activar entorno virtual
echo ""
echo "📌 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo ""
echo "📌 Actualizando pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip actualizado${NC}"

# Instalar dependencias
echo ""
echo "📌 Instalando dependencias..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencias instaladas correctamente${NC}"
else
    echo -e "${RED}✗ Error al instalar dependencias${NC}"
    exit 1
fi

# Crear directorios necesarios
echo ""
echo "📌 Creando estructura de directorios..."
mkdir -p data/raw data/processed data/output logs
echo -e "${GREEN}✓ Directorios creados${NC}"

# Verificar archivos de conocimiento
echo ""
echo "📌 Verificando archivos de configuración..."
if [ -d "config/knowledge" ] && [ -f "config/knowledge/procedimientos.json" ]; then
    echo -e "${GREEN}✓ Archivos de conocimiento encontrados${NC}"
else
    echo -e "${RED}⚠️  Archivos de conocimiento no encontrados${NC}"
    echo "   Los archivos JSON de conocimiento deben estar en config/knowledge/"
fi

# Mensaje final
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Instalación completada exitosamente${NC}"
echo "=========================================="
echo ""
echo "Para ejecutar la aplicación:"
echo "  1. Active el entorno virtual: source venv/bin/activate"
echo "  2. Ejecute: python run_app.py"
echo ""
echo "O simplemente ejecute: ./scripts/run.sh"
echo "" 