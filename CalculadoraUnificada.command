#!/bin/bash
# Script de control unificado para la Calculadora de Turnos
# Este script evita la duplicación de instancias y bloquea otras versiones

# ---- Funciones auxiliares ----

# Función para comprobar si un proceso ya está en ejecución
is_running() {
    local name=$1
    pgrep -f "$name" > /dev/null
    return $?
}

# Función para matar procesos relacionados con la calculadora
kill_calculadora_processes() {
    # Matar procesos de Streamlit
    pkill -f "streamlit run ui/calculadora_streamlit.py" 2>/dev/null
    # Matar procesos de Python que ejecutan calculadora_streamlit.py
    pkill -f "python.*calculadora_streamlit.py" 2>/dev/null
    # Matar procesos de iniciar_streamlit.py
    pkill -f "python.*iniciar_streamlit.py" 2>/dev/null
    # Esperar un segundo para que los procesos se cierren
    sleep 1
}

# Función para bloquear el inicio de otros scripts de la calculadora
block_other_launchers() {
    # Usamos un archivo de bloqueo para evitar que otros scripts se ejecuten
    touch /tmp/calculadora_turnos_running.lock
    
    # Programar la eliminación del archivo de bloqueo al terminar
    trap 'rm -f /tmp/calculadora_turnos_running.lock' EXIT
}

# Función para comprobar si otro lanzador está ejecutándose
other_launcher_running() {
    if [ -f /tmp/calculadora_turnos_running.lock ]; then
        # Verificar si el archivo de bloqueo no está obsoleto (más de 5 minutos)
        if [ $(find /tmp/calculadora_turnos_running.lock -mmin -5 | wc -l) -gt 0 ]; then
            return 0  # El archivo existe y es reciente
        else
            # El archivo es antiguo, lo eliminamos
            rm -f /tmp/calculadora_turnos_running.lock
            return 1
        fi
    else
        return 1  # No hay archivo de bloqueo
    fi
}

# ---- Programa principal ----

# Comprobar si otro lanzador ya está ejecutándose
if other_launcher_running; then
    echo "Otra instancia de la calculadora ya está en ejecución."
    echo "Abriendo solo el navegador..."
    # Esperar a que Streamlit esté disponible y abrir el navegador
    sleep 2
    open "http://localhost:8501"
    exit 0
fi

# No hay otra instancia, podemos continuar
echo "Iniciando Calculadora de Turnos..."

# Establecer el bloqueo para evitar otras instancias
block_other_launchers

# Matar cualquier instancia previa que pudiera estar ejecutándose
kill_calculadora_processes

# Ir al directorio de la aplicación
cd "/Users/rodrigomunoz/Calculadora"

# Iniciar la aplicación usando el método directo (más confiable)
python3 -m streamlit run ui/calculadora_streamlit.py

# La eliminación del archivo de bloqueo se maneja automáticamente al salir
# gracias a la instrucción trap configurada en block_other_launchers