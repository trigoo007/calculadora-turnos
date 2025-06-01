#!/bin/bash
# =========================================================================
# Script de Respaldo Automático para Calculadora de Turnos en Radiología
# =========================================================================
# Este script realiza respaldos periódicos de los datos críticos del sistema:
# - Base de datos SQLite de conocimiento
# - Almacenamiento vectorial
# - Archivos CSV de datos y resultados
# - Configuración Docker
# 
# Uso: 
# - Ejecutar manualmente: bash backup_automatico.sh
# - Configurar como tarea cron: 0 2 * * * /ruta/backup_automatico.sh
#
# Autor: Sistema de Integración Calculadora
# Fecha: Mayo 2025
# =========================================================================

# Configuración
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
APP_DIR="/Users/rodrigomunoz/Calculadora"  # Directorio de la aplicación
BACKUP_DIR="${APP_DIR}/backup"             # Directorio de respaldos
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz"
RETENTION_DAYS=30                          # Días a mantener respaldos
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

# Directorios a respaldar
KNOWLEDGE_DIR="${APP_DIR}/conocimiento"
CSV_DIR="${APP_DIR}/csv"
VECTOR_DIR="${HOME}/vectorstore"
CONFIG_FILES="${APP_DIR}/docker-compose*.yml ${APP_DIR}/Dockerfile* ${APP_DIR}/*.md"

# Crear directorio de respaldo si no existe
mkdir -p "${BACKUP_DIR}"

# Iniciar log
echo "=======================================" > "${LOG_FILE}"
echo "INICIO DE RESPALDO: $(date)" >> "${LOG_FILE}"
echo "=======================================" >> "${LOG_FILE}"

# Función para registrar mensajes
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "${LOG_FILE}"
}

# Verificar si los directorios existen
log "Verificando directorios de origen..."

if [ ! -d "${KNOWLEDGE_DIR}" ]; then
    log "ADVERTENCIA: Directorio de conocimiento no encontrado: ${KNOWLEDGE_DIR}"
fi

if [ ! -d "${CSV_DIR}" ]; then
    log "ADVERTENCIA: Directorio de CSV no encontrado: ${CSV_DIR}"
fi

if [ ! -d "${VECTOR_DIR}" ]; then
    log "ADVERTENCIA: Directorio de almacenamiento vectorial no encontrado: ${VECTOR_DIR}"
    # Crear directorio vacío para vectorstore si no existe
    mkdir -p "${VECTOR_DIR}"
fi

# Crear directorio temporal para el respaldo
TEMP_BACKUP_DIR=$(mktemp -d)
log "Directorio temporal creado: ${TEMP_BACKUP_DIR}"

# Función para manejar errores
handle_error() {
    log "ERROR: $1"
    log "Limpiando directorio temporal..."
    rm -rf "${TEMP_BACKUP_DIR}"
    exit 1
}

# Copiar archivos al directorio temporal
log "Copiando archivos al directorio temporal..."

# Estructura del respaldo
mkdir -p "${TEMP_BACKUP_DIR}/conocimiento"
mkdir -p "${TEMP_BACKUP_DIR}/csv"
mkdir -p "${TEMP_BACKUP_DIR}/vectorstore"
mkdir -p "${TEMP_BACKUP_DIR}/config"

# Copiar base de datos de conocimiento
if [ -d "${KNOWLEDGE_DIR}" ]; then
    log "Copiando base de datos de conocimiento..."
    cp -R "${KNOWLEDGE_DIR}"/* "${TEMP_BACKUP_DIR}/conocimiento/" || handle_error "Error al copiar la base de datos de conocimiento"
    log "Base de datos de conocimiento copiada correctamente"
fi

# Copiar archivos CSV
if [ -d "${CSV_DIR}" ]; then
    log "Copiando archivos CSV..."
    cp -R "${CSV_DIR}"/* "${TEMP_BACKUP_DIR}/csv/" || handle_error "Error al copiar archivos CSV"
    log "Archivos CSV copiados correctamente"
fi

# Copiar almacenamiento vectorial
if [ -d "${VECTOR_DIR}" ]; then
    log "Copiando almacenamiento vectorial..."
    cp -R "${VECTOR_DIR}"/* "${TEMP_BACKUP_DIR}/vectorstore/" || handle_error "Error al copiar almacenamiento vectorial"
    log "Almacenamiento vectorial copiado correctamente"
fi

# Copiar archivos de configuración
log "Copiando archivos de configuración..."
mkdir -p "${TEMP_BACKUP_DIR}/config"
cp ${CONFIG_FILES} "${TEMP_BACKUP_DIR}/config/" 2>/dev/null || log "Advertencia: Algunos archivos de configuración no existen"
log "Archivos de configuración copiados correctamente"

# Crear archivo de metadatos
log "Creando archivo de metadatos..."
cat > "${TEMP_BACKUP_DIR}/metadata.json" << EOF
{
    "timestamp": "$(date +"%Y-%m-%d %H:%M:%S")",
    "hostname": "$(hostname)",
    "backup_type": "completo",
    "version": "0.9.0",
    "app_path": "${APP_DIR}"
}
EOF

# Comprimir el respaldo
log "Comprimiendo respaldo..."
tar -czf "${BACKUP_FILE}" -C "${TEMP_BACKUP_DIR}" . || handle_error "Error al comprimir el respaldo"
log "Respaldo comprimido: ${BACKUP_FILE}"

# Limpiar directorio temporal
log "Limpiando directorio temporal..."
rm -rf "${TEMP_BACKUP_DIR}"

# Eliminar respaldos antiguos
log "Eliminando respaldos antiguos (> ${RETENTION_DAYS} días)..."
find "${BACKUP_DIR}" -name "backup_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -name "backup_*.log" -type f -mtime +${RETENTION_DAYS} -delete

# Contar respaldos restantes
REMAINING_BACKUPS=$(find "${BACKUP_DIR}" -name "backup_*.tar.gz" -type f | wc -l)
log "Respaldos restantes: ${REMAINING_BACKUPS}"

# Registrar el tamaño del respaldo
BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
log "Tamaño del respaldo: ${BACKUP_SIZE}"

# Finalizar log
echo "=======================================" >> "${LOG_FILE}"
echo "FIN DE RESPALDO: $(date)" >> "${LOG_FILE}"
echo "=======================================" >> "${LOG_FILE}"

log "Respaldo completado exitosamente"
exit 0