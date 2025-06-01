#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lanzador directo de Streamlit para la Calculadora de Turnos
"""

import os
import sys
import webbrowser
import subprocess
import time
import platform
import threading

def run_streamlit():
    """Ejecuta Streamlit directamente"""
    # Asegurarnos de que estamos en el directorio correcto
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    # Agregar el directorio actual al path
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    
    print("Iniciando Streamlit...")
    print(f"Directorio de trabajo: {base_dir}")
    
    # Ejecutar Streamlit como un proceso externo
    cmd = [sys.executable, "-m", "streamlit", "run", "ui/calculadora_streamlit.py"]
    
    # En Windows, usamos un mecanismo diferente para no mostrar la consola
    if platform.system() == "Windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proceso = subprocess.Popen(
            cmd,
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    else:
        proceso = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    # Esperar un momento para que Streamlit inicie
    time.sleep(2)
    
    # No abrimos el navegador automáticamente para evitar duplicaciones
    # webbrowser.open("http://localhost:8501")
    print("Aplicación iniciada. Abra manualmente http://localhost:8501 en su navegador.")
    
    print("Aplicación iniciada. Para cerrarla, cierra esta ventana.")
    
    # Continuar ejecutando hasta que el proceso termine
    while proceso.poll() is None:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            proceso.terminate()
            break

if __name__ == "__main__":
    run_streamlit()