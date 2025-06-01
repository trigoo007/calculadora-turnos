#!/bin/bash
# Script para realizar respaldos automáticos de las bases de datos y almacenamiento vectorial
# Puede ser configurado como una tarea programada (cron)

# Configuración
BACKUP_DIR="/backups/calculadora-turnos"
BACKUP_RETAIN_DAYS=30  # Días a retener respaldos
APP_DIR="/opt/calculadora-turnos"  # Directorio de la aplicación
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}"

# Crear directorio de respaldo con fecha
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

echo "==================================================="
echo "  Respaldo Automático de Calculadora de Turnos"
echo "  $(date)"
echo "==================================================="

# Verificar si Docker está en ejecución
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker no está en ejecución. Abortando respaldo."
    exit 1
fi

# Respaldo de datos importantes mientras el contenedor sigue en ejecución
echo "Iniciando respaldo de datos..."

# 1. Respaldo de la base de datos de conocimiento
echo "Respaldando base de datos SQLite..."
if [ -d "${APP_DIR}/conocimiento" ]; then
    cp -r "${APP_DIR}/conocimiento" "${BACKUP_DIR}/${BACKUP_NAME}/"
    echo "✓ Base de datos SQLite respaldada"
else
    echo "⚠ Directorio de conocimiento no encontrado"
fi

# 2. Respaldo del almacenamiento vectorial
echo "Respaldando almacenamiento vectorial..."
if docker exec calculadora-turnos-contexto tar -cf - /root/vectorstore | tar -xf - -C "${BACKUP_DIR}/${BACKUP_NAME}/"; then
    echo "✓ Almacenamiento vectorial respaldado"
else
    echo "⚠ No se pudo respaldar el almacenamiento vectorial"
fi

# 3. Respaldo de configuración Docker
echo "Respaldando configuración Docker..."
if [ -f "${APP_DIR}/docker-compose-contexto.yml" ]; then
    cp "${APP_DIR}/docker-compose-contexto.yml" "${BACKUP_DIR}/${BACKUP_NAME}/"
    echo "✓ Configuración Docker respaldada"
else
    echo "⚠ Archivo docker-compose-contexto.yml no encontrado"
fi

# 4. Respaldo de datos CSV
echo "Respaldando archivos CSV..."
if [ -d "${APP_DIR}/csv" ]; then
    cp -r "${APP_DIR}/csv" "${BACKUP_DIR}/${BACKUP_NAME}/"
    echo "✓ Archivos CSV respaldados"
else
    echo "⚠ Directorio CSV no encontrado"
fi

# Comprimir el respaldo
echo "Comprimiendo respaldo..."
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" -C "${BACKUP_DIR}" "${BACKUP_NAME}"
rm -rf "${BACKUP_DIR}/${BACKUP_NAME}"  # Eliminar directorio sin comprimir
echo "✓ Respaldo comprimido: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

# Eliminar respaldos antiguos
echo "Eliminando respaldos antiguos (> ${BACKUP_RETAIN_DAYS} días)..."
find "${BACKUP_DIR}" -name "backup_*.tar.gz" -type f -mtime +${BACKUP_RETAIN_DAYS} -delete
echo "✓ Limpieza de respaldos antiguos completada"

echo "==================================================="
echo "  Respaldo completado exitosamente"
echo "  Ubicación: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo "  Tamaño: $(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)"
echo "==================================================="

# Instrucciones para programar este script como una tarea cron
echo ""
echo "Para programar este script como una tarea diaria, ejecute:"
echo "crontab -e"
echo ""
echo "Y añada la siguiente línea para ejecutar a las 2 AM todos los días:"
echo "0 2 * * * /opt/calculadora-turnos/backup_automatico.sh >> /var/log/calculadora-backup.log 2>&1"
echo ""