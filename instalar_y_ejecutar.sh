#!/bin/bash
# Script de instalación y ejecución para la Calculadora de Turnos en Radiología
# Versión 0.8.1

echo "===================================================="
echo "  Instalación de Calculadora de Turnos en Radiología"
echo "  Versión 0.8.1"
echo "===================================================="

# Verificar que tenemos Docker instalado
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker no está instalado. Por favor, instala Docker primero."
    echo "Visita https://docs.docker.com/get-docker/ para instrucciones."
    exit 1
fi

# Verificar que tenemos Docker Compose instalado
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose no está instalado. Por favor, instala Docker Compose primero."
    echo "Visita https://docs.docker.com/compose/install/ para instrucciones."
    exit 1
fi

# Determinar el directorio base
BASE_DIR=$(pwd)
echo "Directorio base: $BASE_DIR"

# Comprobar que estamos en el directorio correcto
if [ ! -f "$BASE_DIR/ui/calculadora_streamlit.py" ]; then
    echo "ERROR: No se encuentra el archivo ui/calculadora_streamlit.py"
    echo "Asegúrate de ejecutar este script desde el directorio raíz del proyecto."
    exit 1
fi

# Crear directorios necesarios
echo "Creando directorios necesarios..."
mkdir -p logs
mkdir -p temp
mkdir -p csv

# Construir la imagen Docker
echo "Construyendo la imagen Docker..."
docker-compose build

# Verificar si ya hay una instancia en ejecución
if docker ps | grep -q calculadora; then
    echo "Hay una instancia de la calculadora en ejecución. Deteniéndola..."
    docker-compose down
fi

# Preguntar al usuario si quiere ejecutar la aplicación ahora
echo ""
read -p "¿Deseas ejecutar la aplicación ahora? (s/n): " ejecutar
if [[ $ejecutar == "s" || $ejecutar == "S" ]]; then
    echo "Iniciando la aplicación..."
    docker-compose up -d
    
    # Esperar a que la aplicación esté lista
    echo "Esperando a que la aplicación esté lista..."
    sleep 5
    
    # Obtener la URL de la aplicación
    IP_DOCKER=$(docker-compose logs | grep "Network URL" | tail -n 1 | sed -E 's/.*http:\/\/([^:]+):.*/\1/')
    PUERTO=$(docker-compose port calculadora 8501 | cut -d':' -f2)
    
    if [ -n "$IP_DOCKER" ] && [ -n "$PUERTO" ]; then
        URL_APP="http://$IP_DOCKER:$PUERTO"
    else
        URL_APP="http://localhost:8501"
    fi
    
    echo ""
    echo "===================================================="
    echo "  Calculadora de Turnos en Radiología"
    echo "  Versión 0.8.1"
    echo ""
    echo "  La aplicación está ejecutándose en:"
    echo "  $URL_APP"
    echo ""
    echo "  Para detener la aplicación, ejecuta:"
    echo "  docker-compose down"
    echo "===================================================="
    
    # Abrir el navegador automáticamente si es posible
    if command -v open &> /dev/null; then
        open "$URL_APP"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "$URL_APP"
    elif command -v start &> /dev/null; then
        start "$URL_APP"
    else
        echo "Por favor, abre la URL manualmente en tu navegador."
    fi
else
    echo ""
    echo "Instalación completada. Para ejecutar la aplicación, usa:"
    echo "docker-compose up -d"
    echo ""
    echo "Para acceder a la aplicación, abre en tu navegador:"
    echo "http://localhost:8501"
fi

echo ""
echo "¡Gracias por usar la Calculadora de Turnos en Radiología!"