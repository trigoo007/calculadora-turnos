#!/bin/bash
# =========================================================================
# Script para aplicar configuraciones Docker para Calculadora de Turnos
# =========================================================================
# Este script:
# 1. Actualiza docker-entrypoint-contexto.sh para usar streamlit_contexto.py
# 2. Crea enlaces simbólicos necesarios para backup_automatico.sh
# 3. Crea directorios necesarios para el funcionamiento correcto
#
# Autor: Script de mantenimiento Calculadora
# Fecha: Mayo 2025
# =========================================================================

# Colores para mensajes
VERDE='\033[0;32m'
ROJO='\033[0;31m'
AMARILLO='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Directorio base de la aplicación
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$APP_DIR" || { echo -e "${ROJO}Error: No se pudo acceder al directorio de la aplicación.${NC}"; exit 1; }

echo -e "${CYAN}==================================================${NC}"
echo -e "${CYAN}    Configuración Docker para Calculadora de Turnos${NC}"
echo -e "${CYAN}==================================================${NC}"

# Función para mostrar mensajes
function log() {
    echo -e "${2:-$VERDE}$1${NC}"
}

# Función para mostrar errores
function error_log() {
    echo -e "${ROJO}ERROR: $1${NC}"
}

# Función para mostrar advertencias
function warning_log() {
    echo -e "${AMARILLO}ADVERTENCIA: $1${NC}"
}

# Verificar que los archivos necesarios existen
if [ ! -f "$APP_DIR/docker-entrypoint-contexto.sh" ]; then
    error_log "No se encontró docker-entrypoint-contexto.sh en $APP_DIR"
    exit 1
fi

if [ ! -f "$APP_DIR/experimental/streamlit_contexto.py" ]; then
    error_log "No se encontró experimental/streamlit_contexto.py en $APP_DIR"
    exit 1
fi

if [ ! -f "$APP_DIR/backup/backup_automatico.sh" ]; then
    error_log "No se encontró backup/backup_automatico.sh en $APP_DIR"
    exit 1
fi

# 1. Actualizar docker-entrypoint-contexto.sh para usar streamlit_contexto.py
log "1. Actualizando docker-entrypoint-contexto.sh..."

# Crear respaldo antes de modificar
cp "$APP_DIR/docker-entrypoint-contexto.sh" "$APP_DIR/docker-entrypoint-contexto.sh.bak"
log "  Respaldo creado en docker-entrypoint-contexto.sh.bak" "$CYAN"

# Comprobar si ya está configurado correctamente
if grep -q "streamlit run experimental/streamlit_contexto.py" "$APP_DIR/docker-entrypoint-contexto.sh"; then
    log "  docker-entrypoint-contexto.sh ya está configurado correctamente" "$CYAN"
else
    # Actualizar la línea que ejecuta la aplicación
    sed -i.tmp 's/exec streamlit run.*/exec streamlit run experimental\/streamlit_contexto.py/' "$APP_DIR/docker-entrypoint-contexto.sh"
    
    # Verificar que la actualización fue exitosa
    if grep -q "exec streamlit run experimental/streamlit_contexto.py" "$APP_DIR/docker-entrypoint-contexto.sh"; then
        log "  ✅ docker-entrypoint-contexto.sh actualizado correctamente"
        rm -f "$APP_DIR/docker-entrypoint-contexto.sh.tmp"
    else
        error_log "No se pudo actualizar docker-entrypoint-contexto.sh"
        # Restaurar desde el respaldo
        cp "$APP_DIR/docker-entrypoint-contexto.sh.bak" "$APP_DIR/docker-entrypoint-contexto.sh"
        log "  Se restauró el archivo original desde el respaldo" "$AMARILLO"
    fi
fi

# 2. Crear enlace simbólico para backup_automatico.sh
log "\n2. Configurando script de respaldo..."

# Verificar si el enlace simbólico ya existe
if [ -L "$APP_DIR/backup_automatico.sh" ]; then
    log "  El enlace simbólico backup_automatico.sh ya existe" "$CYAN"
else
    # Crear enlace simbólico
    ln -s "$APP_DIR/backup/backup_automatico.sh" "$APP_DIR/backup_automatico.sh"
    
    if [ -L "$APP_DIR/backup_automatico.sh" ]; then
        log "  ✅ Enlace simbólico creado correctamente"
    else
        error_log "No se pudo crear el enlace simbólico"
    fi
fi

# Verificar permisos del script de respaldo
if [ ! -x "$APP_DIR/backup/backup_automatico.sh" ]; then
    chmod +x "$APP_DIR/backup/backup_automatico.sh"
    log "  ✅ Permisos de ejecución aplicados al script de respaldo"
fi

# 3. Crear directorios necesarios
log "\n3. Creando directorios necesarios..."

# Lista de directorios a crear en APP_DIR
DIRECTORIOS=(
    "conocimiento"
    "csv"
    "logs"
    "data"
    "temp"
    "vectorstore"
)

for DIR in "${DIRECTORIOS[@]}"; do
    if [ -d "$APP_DIR/$DIR" ]; then
        log "  Directorio $DIR ya existe" "$CYAN"
    else
        mkdir -p "$APP_DIR/$DIR"
        if [ -d "$APP_DIR/$DIR" ]; then
            log "  ✅ Directorio $DIR creado"
        else
            error_log "No se pudo crear el directorio $DIR"
        fi
    fi
done

# Crear directorio vectorstore en la ruta de usuario (necesario para Docker)
VECTOR_USER_DIR="$HOME/vectorstore"
if [ -d "$VECTOR_USER_DIR" ]; then
    log "  Directorio $VECTOR_USER_DIR ya existe" "$CYAN"
else
    mkdir -p "$VECTOR_USER_DIR"
    if [ -d "$VECTOR_USER_DIR" ]; then
        log "  ✅ Directorio $VECTOR_USER_DIR creado"
    else
        error_log "No se pudo crear el directorio $VECTOR_USER_DIR"
    fi
fi

# Verificar si docker-compose-contexto.yml existe
if [ ! -f "$APP_DIR/docker-compose-contexto.yml" ]; then
    warning_log "No se encontró docker-compose-contexto.yml. Se necesitará crear o configurar manualmente."
else
    log "  ✅ docker-compose-contexto.yml encontrado"
fi

# Mostrar mensaje de éxito
echo -e "\n${VERDE}==================================================${NC}"
echo -e "${VERDE}    Configuración completada exitosamente${NC}"
echo -e "${VERDE}==================================================${NC}"
echo
log "Para iniciar la aplicación con Docker:" "$CYAN"
echo -e "${VERDE}docker-compose -f docker-compose-contexto.yml up -d${NC}"
echo
log "Para verificar el estado de la aplicación:" "$CYAN"
echo -e "${VERDE}docker-compose -f docker-compose-contexto.yml ps${NC}"
echo
log "Para ver los logs de la aplicación:" "$CYAN"
echo -e "${VERDE}docker-compose -f docker-compose-contexto.yml logs -f${NC}"
echo

exit 0