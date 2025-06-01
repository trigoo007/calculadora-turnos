#!/usr/bin/env python3
"""
Script principal para ejecutar la aplicación Calculadora de Turnos.

Este script configura el entorno y ejecuta la aplicación Streamlit.
"""

import os
import sys
import subprocess
from pathlib import Path

# Agregar el directorio raíz al path de Python
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

def main():
    """Función principal para ejecutar la aplicación."""
    # Verificar que Streamlit esté instalado
    try:
        import streamlit
    except ImportError:
        print("Error: Streamlit no está instalado.")
        print("Por favor, instale las dependencias con: pip install -r requirements.txt")
        sys.exit(1)
    
    # Configurar variables de entorno si es necesario
    os.environ['PYTHONPATH'] = str(ROOT_DIR)
    
    # Ruta al archivo de la aplicación
    app_path = ROOT_DIR / "src" / "ui" / "streamlit_app.py"
    
    if not app_path.exists():
        print(f"Error: No se encuentra el archivo de la aplicación en {app_path}")
        sys.exit(1)
    
    # Ejecutar Streamlit
    print("🚀 Iniciando Calculadora de Turnos...")
    print(f"📁 Directorio de trabajo: {ROOT_DIR}")
    print("🌐 La aplicación se abrirá en tu navegador automáticamente")
    print("   Si no se abre, visita: http://localhost:8505")
    print("\n📌 Para detener la aplicación, presiona Ctrl+C\n")
    
    try:
        # Ejecutar Streamlit con la aplicación
        os.system(f"streamlit run {app_path} --server.port 8505")
    except KeyboardInterrupt:
        print("\n\n✅ Aplicación detenida correctamente")
    except Exception as e:
        print(f"\n❌ Error al ejecutar la aplicación: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 