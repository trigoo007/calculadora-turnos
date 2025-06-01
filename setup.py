#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de configuración para la Calculadora de Turnos en Radiología
Facilita la instalación de dependencias y preparación del entorno
"""

import os
import sys
import subprocess
import platform

def print_header(message):
    """Imprime un mensaje de encabezado formateado."""
    print("\n" + "=" * 60)
    print(f"  {message}")
    print("=" * 60)

def run_command(command, description, optional=False):
    """Ejecuta un comando y maneja errores."""
    print(f"\n> {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True)
        print(f"✓ Completado: {description}")
        return True
    except subprocess.CalledProcessError as e:
        if optional:
            print(f"! Advertencia: No se pudo completar {description}")
            print(f"  {e.stderr.strip() if e.stderr else 'Error desconocido'}")
            return False
        else:
            print(f"✗ Error: No se pudo completar {description}")
            print(f"  {e.stderr.strip() if e.stderr else 'Error desconocido'}")
            return False

def check_python_version():
    """Verifica que la versión de Python sea compatible."""
    print_header("Verificando versión de Python")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print(f"✗ Error: Se requiere Python 3.6 o superior. Versión actual: {sys.version.split()[0]}")
        return False
    
    print(f"✓ Versión de Python compatible: {sys.version.split()[0]}")
    return True

def install_basic_dependencies():
    """Instala las dependencias básicas para la aplicación."""
    print_header("Instalando dependencias básicas")
    
    dependencies = "pandas numpy openpyxl python-dateutil"
    return run_command(f"pip install {dependencies}", "Instalación de dependencias básicas")

def install_streamlit_dependencies():
    """Instala las dependencias para la versión web de la aplicación."""
    print_header("Instalando dependencias para la interfaz web")
    
    dependencies = "streamlit plotly"
    return run_command(f"pip install {dependencies}", "Instalación de dependencias de Streamlit")

def check_ollama():
    """Verifica si Ollama está instalado y el modelo phi-2 está disponible."""
    print_header("Verificando la instalación de Ollama (opcional)")
    
    # Verificar si Ollama está instalado
    ollama_exists = run_command("which ollama", 
                             "Verificando si Ollama está instalado", 
                             optional=True)
    
    if not ollama_exists:
        print("\nOllama no está instalado. Es necesario para el asistente con phi-2.")
        print("Puede instalarlo manualmente desde: https://ollama.ai/")
        print("O ejecutar el siguiente comando:")
        
        if platform.system() == "Darwin":  # macOS
            print("  brew install ollama")
        elif platform.system() == "Linux":
            print("  curl -fsSL https://ollama.com/install.sh | sh")
        else:
            print("  Visite https://ollama.ai/ para obtener instrucciones de instalación")
            
        return False
    
    # Verificar si Ollama está en ejecución
    ollama_running = run_command("curl -s http://localhost:11434/api/tags", 
                              "Verificando si Ollama está en ejecución", 
                              optional=True)
    
    if not ollama_running:
        print("\nOllama no está en ejecución. Inicie Ollama con:")
        print("  ollama serve")
        return False
    
    # Verificar si el modelo phi-2 está disponible
    phi2_available = run_command("ollama list | grep -q phi", 
                              "Verificando si el modelo phi-2 está disponible", 
                              optional=True)
    
    if not phi2_available:
        print("\nEl modelo phi-2 no está disponible. Puede descargarlo con:")
        print("  ollama pull phi")
        return False
    
    print("\n✓ Ollama y phi-2 están configurados correctamente")
    return True

def create_directories():
    """Crea los directorios necesarios si no existen."""
    print_header("Creando directorios necesarios")
    
    directories = ["csv", "temp", "recursos"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Creado directorio: {directory}")
        else:
            print(f"• El directorio {directory} ya existe")
    
    return True

def print_next_steps():
    """Muestra los siguientes pasos para el usuario."""
    print_header("Configuración completada")
    
    print("Puedes ejecutar la aplicación con uno de los siguientes comandos:\n")
    print("1. Versión de escritorio:")
    print("   python calculadora_turnos.py\n")
    print("2. Versión web (Streamlit):")
    print("   streamlit run calculadora_streamlit.py\n")
    print("3. Asistente independiente con phi-2:")
    print("   streamlit run asistente_streamlit.py\n")
    print("Para más información, consulta README.md y TIMELINE.md")

def main():
    """Función principal que ejecuta el proceso de configuración."""
    print_header("Configuración de la Calculadora de Turnos en Radiología")
    
    # Verificar versión de Python
    if not check_python_version():
        return
    
    # Instalar dependencias básicas
    if not install_basic_dependencies():
        return
    
    # Instalar dependencias de Streamlit
    install_streamlit_dependencies()
    
    # Crear directorios
    create_directories()
    
    # Verificar Ollama (opcional)
    check_ollama()
    
    # Mostrar siguientes pasos
    print_next_steps()

if __name__ == "__main__":
    main()