#!/bin/bash
# Script para crear una aplicación de escritorio sin apertura automática del navegador

# Asegurarse de que estamos en el directorio correcto
cd "$(dirname "$0")"

# Crear directorio temporal
TEMP_DIR=$(mktemp -d)
echo "Usando directorio temporal: $TEMP_DIR"

# Copiar archivos necesarios
echo "Copiando archivos..."
cp calculadora_app.py $TEMP_DIR/
cp -r ui $TEMP_DIR/
cp -r conocimiento $TEMP_DIR/
cp -r recursos $TEMP_DIR/
cp -r csv $TEMP_DIR/
cp README.md $TEMP_DIR/
cp CLAUDE.md $TEMP_DIR/
cp TIMELINE.md $TEMP_DIR/

# Modificar el archivo calculadora_app.py para no abrir automáticamente el navegador
echo "Modificando calculadora_app.py..."
sed -i '' 's/self.abrir_navegador()/#self.abrir_navegador()/g' $TEMP_DIR/calculadora_app.py

# Copiar el archivo iniciar_streamlit.py modificado
cp iniciar_streamlit.py $TEMP_DIR/

# Crear la estructura para la aplicación
echo "Creando estructura de la aplicación..."
APP_NAME="CalculadoraTurnos_SinNavegadorAutomatico"
APP_DIR="$HOME/Desktop/$APP_NAME.app"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Crear Info.plist
cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>CalculadoraTurnos</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.radiologia.calculadoraturnos</string>
    <key>CFBundleName</key>
    <string>CalculadoraTurnos</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Crear script ejecutable
cat > "$APP_DIR/Contents/MacOS/CalculadoraTurnos" << EOF
#!/bin/bash
cd "\$(dirname "\$0")/../Resources"
python3 calculadora_app.py
EOF
chmod +x "$APP_DIR/Contents/MacOS/CalculadoraTurnos"

# Copiar recursos
cp -r $TEMP_DIR/* "$APP_DIR/Contents/Resources/"

# Copiar icono si existe
if [ -f "recursos/icono.ico" ]; then
    cp "recursos/icono.ico" "$APP_DIR/Contents/Resources/AppIcon.icns"
fi

# Limpiar
echo "Limpiando..."
rm -rf $TEMP_DIR

echo "Aplicación creada en: $APP_DIR"
echo "IMPORTANTE: Esta aplicación no abrirá automáticamente el navegador."
echo "Para ver la interfaz, haga clic en el botón 'Abrir en Navegador' después de iniciar la aplicación."