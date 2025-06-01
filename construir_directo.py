#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simplificado para crear la aplicación directamente con PyInstaller
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

# Directorio base del proyecto
base_dir = os.path.dirname(os.path.abspath(__file__))

# Asegurarse de que dist/CalculadoraTurnos existe y está vacío
dist_dir = os.path.join(base_dir, "dist", "CalculadoraTurnos")
if os.path.exists(dist_dir):
    print(f"Limpiando directorio de destino: {dist_dir}")
    for item in os.listdir(dist_dir):
        item_path = os.path.join(dist_dir, item)
        if os.path.isfile(item_path):
            os.unlink(item_path)
        elif os.path.isdir(item_path):
            import shutil
            shutil.rmtree(item_path)

# Preparar argumentos para PyInstaller
args = [
    "pyinstaller",
    "--clean",
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--name=CalculadoraTurnos"
]

# Configurar datas
data_paths = [
    ("ui", "ui"),
    ("csv", "csv"),
    ("conocimiento", "conocimiento"),
    ("recursos", "recursos"),
    ("TIMELINE.md", "."),
    ("README.md", "."),
    ("README_INSTALACION.md", "."),
    ("CLAUDE.md", ".")
]

# Agregar datas
for src, dst in data_paths:
    src_path = os.path.join(base_dir, src)
    if os.path.exists(src_path):
        if platform.system() == "Windows":
            args.append(f"--add-data={src_path};{dst}")
        else:
            args.append(f"--add-data={src_path}:{dst}")

# Agregar calculadora_app.py
args.append("calculadora_app.py")

# Ejecutar PyInstaller
print("Ejecutando PyInstaller...")
print(" ".join(args))
result = subprocess.run(args)

# Crear acceso directo
if result.returncode == 0:
    print("Creando acceso directo...")
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    
    if platform.system() == "Darwin":  # macOS
        # Crear un archivo .command
        command_path = os.path.join(desktop, "CalculadoraTurnos.command")
        with open(command_path, "w") as f:
            f.write(f"""#!/bin/bash
cd "{os.path.join(os.getcwd(), "dist", "CalculadoraTurnos")}"
./CalculadoraTurnos
""")
        # Hacer el archivo ejecutable
        os.chmod(command_path, 0o755)
        print(f"Acceso directo creado en: {command_path}")
    else:
        print("En este sistema operativo, debes crear un acceso directo manualmente.")
    
    print("\n¡Aplicación creada exitosamente!")
    print(f"Ubicación: {os.path.join(base_dir, 'dist', 'CalculadoraTurnos')}")
else:
    print(f"Error al crear la aplicación: {result.returncode}")