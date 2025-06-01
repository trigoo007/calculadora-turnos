#!/bin/bash
# Script para instalar y configurar la Calculadora de Turnos con integración Cloudflare
set -e

echo "======================================================================"
echo "  Instalación de Calculadora de Turnos con Cloudflare Tunnel"
echo "======================================================================"

# Verificar si se está ejecutando como root o con sudo
if [ "$EUID" -ne 0 ]; then
  echo "Este script debe ejecutarse con privilegios de superusuario (sudo)."
  echo "Por favor, ejecute: sudo $0"
  exit 1
fi

# Verificar sistema operativo
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "No se pudo determinar el sistema operativo."
    exit 1
fi

echo "Sistema operativo detectado: $OS"

# Instalar dependencias según el sistema operativo
echo "Instalando dependencias del sistema..."
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt update
    apt install -y curl wget git ca-certificates gnupg lsb-release
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
    yum update -y
    yum install -y curl wget git ca-certificates gnupg
else
    echo "Sistema operativo no soportado directamente. Se intentará continuar, pero pueden ocurrir errores."
fi

# Instalar Docker si no está instalado
if ! command -v docker &> /dev/null; then
    echo "Docker no está instalado. Instalando Docker..."
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        # Configurar el repositorio
        mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/$OS/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
        apt update
        apt install -y docker-ce docker-ce-cli containerd.io
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
        yum install -y yum-utils
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        yum install -y docker-ce docker-ce-cli containerd.io
    fi
    
    # Iniciar y habilitar Docker
    systemctl start docker
    systemctl enable docker
    
    echo "Docker instalado correctamente."
else
    echo "Docker ya está instalado."
fi

# Instalar Docker Compose si no está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose no está instalado. Instalando Docker Compose..."
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose instalado correctamente."
else
    echo "Docker Compose ya está instalado."
fi

# Verificar si el directorio de instalación ya existe
INSTALL_DIR="/opt/calculadora-turnos"
if [ -d "$INSTALL_DIR" ]; then
    echo "El directorio de instalación ya existe. ¿Desea sobrescribirlo? (S/N)"
    read -r OVERWRITE
    if [[ "$OVERWRITE" =~ ^[Ss]$ ]]; then
        echo "Respaldando configuración anterior..."
        BACKUP_DIR="/opt/calculadora-turnos.backup-$(date +%Y%m%d%H%M%S)"
        mv "$INSTALL_DIR" "$BACKUP_DIR"
        echo "Configuración anterior respaldada en $BACKUP_DIR"
    else
        echo "Instalación cancelada por el usuario."
        exit 0
    fi
fi

# Crear directorio de instalación
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Copiar archivos del directorio actual si están disponibles
if [ -f "./Dockerfile.contexto" ]; then
    echo "Copiando archivos desde el directorio actual..."
    cp -r ./* "$INSTALL_DIR/"
else
    echo "ERROR: No se encontraron los archivos necesarios en el directorio actual."
    echo "Asegúrate de ejecutar este script desde el directorio que contiene los archivos de la aplicación."
    exit 1
fi

# Configurar túnel de Cloudflare
echo "======================================================================"
echo "  Configuración del túnel Cloudflare"
echo "======================================================================"
echo "¿Desea configurar un túnel Cloudflare para acceso público? (S/N)"
read -r SETUP_CLOUDFLARE

if [[ "$SETUP_CLOUDFLARE" =~ ^[Ss]$ ]]; then
    echo "Por favor, ingrese su token de túnel Cloudflare:"
    read -r CLOUDFLARE_TOKEN
    
    # Actualizar el archivo docker-compose-contexto.yml con el token
    sed -i "s/# - CLOUDFLARE_TUNNEL_TOKEN=your_tunnel_token_here/- CLOUDFLARE_TUNNEL_TOKEN=$CLOUDFLARE_TOKEN/" docker-compose-contexto.yml
    
    echo "Túnel Cloudflare configurado correctamente."
else
    echo "No se configurará el túnel Cloudflare. La aplicación solo estará disponible localmente."
fi

# Configurar respaldos automáticos
echo "======================================================================"
echo "  Configuración de respaldos automáticos"
echo "======================================================================"
echo "¿Desea configurar respaldos automáticos? (S/N)"
read -r SETUP_BACKUPS

if [[ "$SETUP_BACKUPS" =~ ^[Ss]$ ]]; then
    # Crear directorio para respaldos
    mkdir -p /backups/calculadora-turnos
    
    # Asegurar que el script sea ejecutable
    chmod +x "$INSTALL_DIR/backup_automatico.sh"
    
    # Configurar cron para ejecutar respaldos diarios (a las 2 AM)
    echo "Configurando respaldo automático diario a las 2 AM..."
    (crontab -l 2>/dev/null || echo "") | grep -v "$INSTALL_DIR/backup_automatico.sh" | \
    { cat; echo "0 2 * * * $INSTALL_DIR/backup_automatico.sh >> /var/log/calculadora-backup.log 2>&1"; } | crontab -
    
    echo "Respaldos automáticos configurados correctamente."
    echo "Los respaldos se guardarán en /backups/calculadora-turnos/"
    echo "Se ejecutará un respaldo automático todos los días a las 2 AM."
else
    echo "No se configurarán respaldos automáticos."
    echo "Puede ejecutar respaldos manualmente con: sudo $INSTALL_DIR/backup_automatico.sh"
fi

# Iniciar los servicios
echo "======================================================================"
echo "  Iniciando los servicios"
echo "======================================================================"
cd "$INSTALL_DIR"
docker-compose -f docker-compose-contexto.yml up -d

# Verificar que los servicios estén en ejecución
echo "Verificando servicios..."
docker-compose -f docker-compose-contexto.yml ps

# Mostrar información de acceso
echo "======================================================================"
echo "  Instalación completada"
echo "======================================================================"
echo "La aplicación está ahora instalada y en ejecución."
echo ""
echo "Acceso local: http://localhost:8501"

if [[ "$SETUP_CLOUDFLARE" =~ ^[Ss]$ ]]; then
    echo ""
    echo "La aplicación debería estar accesible a través de su túnel Cloudflare."
    echo "Verifique la URL configurada en su panel de Cloudflare."
fi

echo ""
echo "Para administrar la aplicación:"
echo "- Ver logs: docker-compose -f $INSTALL_DIR/docker-compose-contexto.yml logs -f"
echo "- Detener: docker-compose -f $INSTALL_DIR/docker-compose-contexto.yml down"
echo "- Reiniciar: docker-compose -f $INSTALL_DIR/docker-compose-contexto.yml restart"
echo ""
echo "Documentación adicional disponible en README_CLOUDFLARE.md"
echo "======================================================================"