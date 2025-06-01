#!/bin/bash

# Script para ejecutar la Calculadora de Turnos
# =============================================

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Iniciando Calculadora de Turnos...${NC}"
echo ""

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo -e "${RED}✗ No se encontró el entorno virtual${NC}"
    echo "  Ejecute primero: ./scripts/install.sh"
    exit 1
fi

# Activar entorno virtual
echo "📌 Activando entorno virtual..."
source venv/bin/activate

# Verificar que Streamlit esté instalado
if ! python -c "import streamlit" 2>/dev/null; then
    echo -e "${RED}✗ Streamlit no está instalado${NC}"
    echo "  Ejecute: pip install -r requirements.txt"
    exit 1
fi

# Ejecutar la aplicación
echo -e "${GREEN}✓ Iniciando aplicación...${NC}"
echo ""
echo "🌐 La aplicación se abrirá en tu navegador"
echo "   URL: http://localhost:8501"
echo ""
echo "📌 Para detener: presiona Ctrl+C"
echo ""

# Ejecutar
python run_app.py 