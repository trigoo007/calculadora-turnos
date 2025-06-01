#!/bin/bash
# Script para crear aplicación de escritorio sin icono
# Calculadora de Turnos en Radiología v0.8.1

echo "===================================================="
echo "  Crear Aplicación de Escritorio (Sin Icono)"
echo "  Calculadora de Turnos en Radiología v0.8.1"
echo "===================================================="

# Determinar el sistema operativo
OS=$(uname -s)

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 no está instalado."
    echo "Por favor, instale Python 3 antes de continuar."
    exit 1
fi

# Crear entorno virtual para no afectar el sistema
echo "Creando entorno virtual..."
python3 -m venv env
if [ $? -ne 0 ]; then
    echo "Error al crear el entorno virtual."
    exit 1
fi

# Activar entorno virtual
if [ "$OS" = "Darwin" ] || [ "$OS" = "Linux" ]; then
    source env/bin/activate
else
    source env/Scripts/activate
fi

# Instalar dependencias necesarias
echo "Instalando dependencias..."
pip install pyinstaller streamlit pandas numpy plotly openpyxl python-dateutil
if [ $? -ne 0 ]; then
    echo "Error al instalar dependencias."
    exit 1
fi

# Crear un script PyInstaller simplificado
cat > build_app.py << 'EOF'
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
EOF

# Ejecutar el script Python
echo "Generando la aplicación de escritorio..."
python build_app.py

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "===================================================="
    echo "  ¡Aplicación de escritorio creada con éxito!"
    echo "===================================================="
    echo ""
    echo "La aplicación se encuentra en el directorio:"
    echo "  $(pwd)/dist/CalculadoraTurnos"
    echo ""
    echo "Puede copiar esta carpeta completa a cualquier ubicación."
    echo "Para ejecutar la aplicación, simplemente haga doble clic"
    echo "en el archivo 'CalculadoraTurnos'."
    echo ""
    echo "También se intentó crear un acceso directo en su escritorio."
    echo "===================================================="
else
    echo ""
    echo "===================================================="
    echo "  Ocurrió un error durante la creación."
    echo "  Por favor, revise los mensajes de error anteriores."
    echo "===================================================="
fi

# Desactivar entorno virtual
deactivate