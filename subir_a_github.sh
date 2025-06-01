#!/bin/bash
# Script para subir el proyecto a GitHub

echo "🚀 SUBIENDO CALCULADORA DE TURNOS A GITHUB"
echo "==========================================="

# Navegar al directorio del proyecto
cd /Users/rodrigomunoz/Calculadora

# Verificar si existe .git, si no, inicializar
if [ ! -d ".git" ]; then
    echo "📁 Inicializando repositorio Git..."
    git init
    git remote add origin https://github.com/trigoo007/calculadora-turnos.git
fi

# Configurar usuario Git (ajustar según necesidades)
git config user.name "Rodrigo Muñoz"
git config user.email "trigoo007@gmail.com"

# Verificar archivos a subir
echo "📋 Verificando archivos..."
git status

# Agregar todos los archivos
echo "➕ Agregando archivos..."
git add .

# Crear commit con mensaje descriptivo
echo "💾 Creando commit..."
git commit -m "🎉 Subida inicial del proyecto Calculadora de Turnos de Radiología

Incluye:
✅ Sistema completo de procesamiento de exámenes radiológicos
✅ Calculadora de honorarios y turnos médicos
✅ Interfaz web Streamlit
✅ Sistema de códigos de exámenes
✅ Funcionalidad de estimación de duplas
✅ Aplicación de escritorio
✅ Configuración Docker
✅ Sistema de aprendizaje SQLite
✅ Tests y validaciones
✅ Documentación completa

Características principales:
- Procesamiento automático de archivos Excel
- Cálculo de honorarios por procedimientos
- Detección inteligente de duplas de turnos
- Interfaz web moderna con Streamlit
- Soporte para múltiples formatos de entrada
- Sistema de códigos de exámenes configurable
- Generación de reportes detallados
- Aplicación standalone para escritorio"

# Verificar si hay conflictos con el repositorio remoto
echo "🔍 Verificando repositorio remoto..."
git fetch origin main 2>/dev/null || git fetch origin master 2>/dev/null || echo "Repositorio remoto vacío o inaccesible"

# Intentar hacer push
echo "🚀 Subiendo a GitHub..."
git push -u origin main 2>/dev/null || git push -u origin master 2>/dev/null || {
    echo "⚠️  Intentando forzar push inicial..."
    git push --set-upstream origin main --force
}

echo "✅ ¡Subida completada exitosamente!"
echo ""
echo "🔗 Repositorio disponible en: https://github.com/trigoo007/calculadora-turnos"
echo ""
echo "📚 Próximos pasos recomendados:"
echo "   1. Configurar README.md con instrucciones de instalación"
echo "   2. Agregar badges de estado al repositorio"
echo "   3. Configurar GitHub Actions para CI/CD"
echo "   4. Crear releases para versiones estables"
echo ""
