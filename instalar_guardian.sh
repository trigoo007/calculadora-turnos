#\!/bin/bash
# Script de instalación del Guardian de Arquitectura
# Este script debe ejecutarse con sudo

# Colores para mensajes
ROJO='\033[0;31m'
VERDE='\033[0;32m'
AMARILLO='\033[0;33m'
NORMAL='\033[0m'

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    echo -e "${ROJO}Este script debe ejecutarse como root (sudo).${NORMAL}"
    exit 1
fi

# Directorio de instalación
INSTALL_DIR="/opt/calculadora"

# Verificar argumento de instalación
if [ "$1" \!= "--dir" ]; then
    echo "Uso: sudo ./instalar_guardian.sh --dir /ruta/al/proyecto/calculadora"
    exit 1
fi

if [ -z "$2" ]; then
    echo "Debe especificar el directorio del proyecto:"
    echo "Uso: sudo ./instalar_guardian.sh --dir /ruta/al/proyecto/calculadora"
    exit 1
fi

SOURCE_DIR="$2"

# Verificar que el directorio fuente existe
if [ \! -d "$SOURCE_DIR" ]; then
    echo -e "${ROJO}El directorio $SOURCE_DIR no existe.${NORMAL}"
    exit 1
fi

# Verificar que guardian_arquitectura.py existe en el directorio fuente
if [ \! -f "$SOURCE_DIR/guardian_arquitectura.py" ]; then
    echo -e "${ROJO}No se encontró guardian_arquitectura.py en $SOURCE_DIR.${NORMAL}"
    exit 1
fi

echo -e "${AMARILLO}Instalando Guardian de Arquitectura desde $SOURCE_DIR a $INSTALL_DIR...${NORMAL}"

# Crear directorio de instalación si no existe
mkdir -p $INSTALL_DIR

# Copiar el proyecto
echo "Copiando archivos del proyecto..."
cp -r $SOURCE_DIR/* $INSTALL_DIR/

# Hacer ejecutable el guardian
chmod +x $INSTALL_DIR/guardian_arquitectura.py

# Cambiar propietario a root y permisos para proteger archivos críticos
echo "Configurando permisos..."
chown root:root $INSTALL_DIR/guardian_arquitectura.py
chmod 700 $INSTALL_DIR/guardian_arquitectura.py

# Instalar el servicio systemd si existe el archivo .service
if [ -f "$INSTALL_DIR/guardian_arquitectura.service" ]; then
    echo "Instalando servicio systemd..."
    cp $INSTALL_DIR/guardian_arquitectura.service /etc/systemd/system/
    cp $INSTALL_DIR/guardian_arquitectura.timer /etc/systemd/system/
    
    # Recargar systemd
    systemctl daemon-reload
    
    # Habilitar y iniciar el servicio
    systemctl enable guardian_arquitectura.timer
    systemctl start guardian_arquitectura.timer
    
    echo -e "${VERDE}Servicio systemd instalado y activado.${NORMAL}"
else
    echo -e "${AMARILLO}No se encontró archivo .service. No se instaló como servicio.${NORMAL}"
fi

# Instalar el hook pre-commit en el directorio .git si existe
if [ -d "$SOURCE_DIR/.git" ]; then
    echo "Instalando hook pre-commit de Git..."
    
    # Crear archivo pre-commit
    cat > "$SOURCE_DIR/.git/hooks/pre-commit" << 'PRECOMMIT'
#\!/bin/bash

echo "Verificando estructura del proyecto antes de commit..."
/opt/calculadora/guardian_arquitectura.py

# Si el guardian retorna error, abortar el commit
if [ $? -ne 0 ]; then
    echo "Error en la estructura del proyecto. Commit abortado."
    echo "Ejecute 'python guardian_arquitectura.py --auto-fix' para corregir problemas."
    exit 1
fi

echo "Estructura del proyecto correcta. Continuando con el commit."
exit 0
PRECOMMIT
    
    # Hacer ejecutable el hook
    chmod +x "$SOURCE_DIR/.git/hooks/pre-commit"
    
    echo -e "${VERDE}Hook pre-commit de Git instalado.${NORMAL}"
else
    echo -e "${AMARILLO}No se encontró directorio .git. No se instaló hook de Git.${NORMAL}"
fi

echo -e "${VERDE}Guardian de Arquitectura instalado correctamente.${NORMAL}"
echo ""
echo "Para verificar manualmente la estructura del proyecto:"
echo "  sudo $INSTALL_DIR/guardian_arquitectura.py"
echo ""
echo "Para corregir automáticamente problemas de estructura:"
echo "  sudo $INSTALL_DIR/guardian_arquitectura.py --auto-fix"
echo ""
echo "El servicio verificará la estructura automáticamente cada hora."

exit 0
EOF < /dev/null