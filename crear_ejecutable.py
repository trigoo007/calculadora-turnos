#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear un ejecutable de la aplicación
------------------------------------------------
Este script utiliza PyInstaller para crear un ejecutable independiente
de la Calculadora de Turnos en Radiología.
"""

import os
import sys
import platform
import shutil
import subprocess
from pathlib import Path

def instalar_dependencias():
    """Instala las dependencias necesarias para construir el ejecutable"""
    print("Instalando dependencias necesarias...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "streamlit", "pandas", "numpy", "plotly", "openpyxl", "python-dateutil"])
    print("Dependencias instaladas correctamente.")

def crear_icono():
    """Crea archivos de iconos en los formatos necesarios"""
    print("Preparando iconos...")
    # Crear directorio de recursos si no existe
    os.makedirs("recursos", exist_ok=True)
    
    # Aquí un icono dummy simple, en una aplicación real usarías un archivo .png/.ico real
    # Este es solo para la demostración
    with open("recursos/icono.ico", "w") as f:
        f.write("/* Archivo de icono dummy */")
    
    print("Iconos creados correctamente.")

def crear_ejecutable():
    """Crea el ejecutable con PyInstaller"""
    print("Creando ejecutable de la aplicación...")
    
    # Determinar el sistema operativo
    sistema = platform.system()
    
    # Directorio base del proyecto
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Archivos y directorios a incluir
    datas = [
        ("ui", "ui"),
        ("csv", "csv"),
        ("conocimiento", "conocimiento"),
        ("recursos", "recursos"),
        ("TIMELINE.md", "."),
        ("README.md", "."),
        ("README_INSTALACION.md", "."),
        ("CLAUDE.md", ".")
    ]
    
    # Preparar argumentos de datos para PyInstaller
    datas_args = []
    for src, dst in datas:
        src_path = os.path.join(base_dir, src)
        if os.path.exists(src_path):
            if platform.system() == "Windows":
                datas_args.append(f"--add-data={src_path};{dst}")
            else:
                datas_args.append(f"--add-data={src_path}:{dst}")
    
    # Argumentos PyInstaller
    pyinstaller_args = [
        "pyinstaller",
        "--onedir",  # Crear un directorio con archivos (más rápido que --onefile)
        "--windowed",  # No mostrar consola en Windows
        "--name=CalculadoraTurnos",
        "--icon=recursos/icono.ico",
    ]
    
    # Agregar argumentos de datos
    pyinstaller_args.extend(datas_args)
    
    # Agregar calculadora_app.py
    pyinstaller_args.append("calculadora_app.py")
    
    # Ejecutar PyInstaller
    subprocess.run(pyinstaller_args)
    
    print("Ejecutable creado correctamente.")

def crear_acceso_directo():
    """Crea un acceso directo para el escritorio"""
    print("Creando acceso directo para el escritorio...")
    
    sistema = platform.system()
    
    if sistema == "Windows":
        try:
            import win32com.client
            
            # Obtener la ruta al escritorio
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            
            # Crear acceso directo
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(os.path.join(desktop, "Calculadora de Turnos.lnk"))
            shortcut.TargetPath = os.path.join(os.getcwd(), "dist", "CalculadoraTurnos", "CalculadoraTurnos.exe")
            shortcut.WorkingDirectory = os.path.join(os.getcwd(), "dist", "CalculadoraTurnos")
            shortcut.IconLocation = os.path.join(os.getcwd(), "recursos", "icono.ico")
            shortcut.Description = "Calculadora de Turnos en Radiología"
            shortcut.save()
            
            print("Acceso directo creado en el escritorio.")
        except:
            print("No se pudo crear el acceso directo automáticamente.")
            print("Por favor, cree manualmente un acceso directo al ejecutable en dist/CalculadoraTurnos/CalculadoraTurnos.exe")
    
    elif sistema == "Darwin":  # macOS
        try:
            # Obtener la ruta al escritorio
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            
            # Crear un archivo .command
            command_path = os.path.join(desktop, "CalculadoraTurnos.command")
            with open(command_path, "w") as f:
                f.write(f"""#!/bin/bash
cd "{os.path.join(os.getcwd(), "dist", "CalculadoraTurnos")}"
./CalculadoraTurnos
""")
            
            # Hacer el archivo ejecutable
            os.chmod(command_path, 0o755)
            
            print("Acceso directo creado en el escritorio.")
        except:
            print("No se pudo crear el acceso directo automáticamente.")
            print("Por favor, cree manualmente un acceso directo a la aplicación en dist/CalculadoraTurnos/CalculadoraTurnos")
    
    elif sistema == "Linux":
        try:
            # Obtener la ruta al escritorio
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            
            # Crear un archivo .desktop
            desktop_path = os.path.join(desktop, "CalculadoraTurnos.desktop")
            with open(desktop_path, "w") as f:
                f.write(f"""[Desktop Entry]
Type=Application
Name=Calculadora de Turnos
Comment=Calculadora de Turnos en Radiología
Exec={os.path.join(os.getcwd(), "dist", "CalculadoraTurnos", "CalculadoraTurnos")}
Icon={os.path.join(os.getcwd(), "recursos", "icono.ico")}
Terminal=false
Categories=Utility;
""")
            
            # Hacer el archivo ejecutable
            os.chmod(desktop_path, 0o755)
            
            print("Acceso directo creado en el escritorio.")
        except:
            print("No se pudo crear el acceso directo automáticamente.")
            print("Por favor, cree manualmente un acceso directo a la aplicación en dist/CalculadoraTurnos/CalculadoraTurnos")
    
    else:
        print("Sistema operativo no reconocido. No se pudo crear acceso directo.")
        print("Por favor, cree manualmente un acceso directo a la aplicación en dist/CalculadoraTurnos/")

def main():
    """Función principal"""
    print("=" * 70)
    print("  Creando Ejecutable para Calculadora de Turnos en Radiología v0.8.1")
    print("=" * 70)
    
    try:
        # Instalar dependencias
        instalar_dependencias()
        
        # Crear iconos
        crear_icono()
        
        # Crear ejecutable
        crear_ejecutable()
        
        # Crear acceso directo
        crear_acceso_directo()
        
        print("\nProceso completado correctamente.")
        print("\nEl ejecutable se encuentra en:")
        print(f"  {os.path.join(os.getcwd(), 'dist', 'CalculadoraTurnos')}")
        print("\nPuede copiar esta carpeta completa a cualquier ubicación o equipo.")
        print("Para ejecutar la aplicación, haga doble clic en CalculadoraTurnos.")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("No se pudo completar el proceso.")
        sys.exit(1)

if __name__ == "__main__":
    main()