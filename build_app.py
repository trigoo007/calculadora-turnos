import os
import sys
import platform
import subprocess
from pathlib import Path

# Directorio base del proyecto
base_dir = os.path.dirname(os.path.abspath(__file__))

# Crear directorios necesarios
os.makedirs("dist/CalculadoraTurnos", exist_ok=True)

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

# Compilar la aplicación con PyInstaller
print("Compilando la aplicación...")

# Preparar argumentos para PyInstaller
args = ["pyinstaller", "--onedir", "--windowed", "--name=CalculadoraTurnos"]

# Agregar argumentos de datos
for src, dst in datas:
    src_path = os.path.join(base_dir, src)
    if os.path.exists(src_path):
        if platform.system() == "Windows":
            args.append(f"--add-data={src_path};{dst}")
        else:
            args.append(f"--add-data={src_path}:{dst}")

# Agregar el archivo principal
args.append("calculadora_app.py")

# Ejecutar PyInstaller
subprocess.run(args)

print("Compilación completada.")

# Crear acceso directo al escritorio
print("Creando acceso directo...")
try:
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
    elif platform.system() == "Linux":
        # Crear un archivo .desktop
        desktop_path = os.path.join(desktop, "CalculadoraTurnos.desktop")
        with open(desktop_path, "w") as f:
            f.write(f"""[Desktop Entry]
Type=Application
Name=Calculadora de Turnos
Comment=Calculadora de Turnos en Radiología
Exec={os.path.join(os.getcwd(), "dist", "CalculadoraTurnos", "CalculadoraTurnos")}
Terminal=false
Categories=Utility;
""")
        # Hacer el archivo ejecutable
        os.chmod(desktop_path, 0o755)
        print(f"Acceso directo creado en: {desktop_path}")
    elif platform.system() == "Windows":
        print("En Windows, crea manualmente un acceso directo al ejecutable en dist/CalculadoraTurnos/CalculadoraTurnos.exe")
except Exception as e:
    print(f"No se pudo crear el acceso directo: {e}")
    print("Puede crear manualmente un acceso directo al ejecutable en dist/CalculadoraTurnos/")

print("\nProceso completado.")
