# Aplicación de Escritorio - Calculadora de Turnos en Radiología

Este documento le guiará en el proceso de creación y uso de la versión de escritorio de la Calculadora de Turnos en Radiología.

## Creación de la Aplicación de Escritorio

Existen dos formas de crear la aplicación de escritorio:

### 1. Usar el Script Automatizado (Recomendado)

El método más sencillo es ejecutar el script automatizado:

```bash
bash crear_aplicacion_escritorio.sh
```

Este script:
1. Crea un entorno virtual de Python
2. Instala todas las dependencias necesarias
3. Genera la aplicación ejecutable
4. Crea un acceso directo en su escritorio

### 2. Ejecución Manual

Si prefiere realizar el proceso manualmente:

```bash
# Crear y activar entorno virtual
python -m venv env
source env/bin/activate  # En Windows: env\Scripts\activate

# Instalar dependencias
pip install pyinstaller streamlit pandas numpy plotly openpyxl python-dateutil

# Crear ejecutable
python crear_ejecutable.py

# Desactivar entorno virtual
deactivate
```

## Uso de la Aplicación

Una vez creada, la aplicación se encuentra en el directorio:

```
dist/CalculadoraTurnos/
```

Para utilizarla:

1. Puede ejecutar directamente la aplicación desde este directorio
2. Puede copiar todo el directorio `CalculadoraTurnos` a otra ubicación o equipo
3. Puede usar el acceso directo creado en su escritorio

Al iniciar la aplicación:

1. Se abrirá una ventana con la interfaz principal
2. Haga clic en "Iniciar Aplicación" para iniciar el servidor Streamlit
3. Se abrirá automáticamente su navegador web con la aplicación
4. Puede usar el botón "Abrir en Navegador" para abrir la aplicación nuevamente si cerró la pestaña

## Características

- **Completamente Portable**: Funciona sin instalación en cualquier equipo compatible
- **Interfaz Nativa**: Ventana de aplicación con iconos y controles nativos
- **Auto-contenida**: Incluye todas las dependencias necesarias
- **Fácil Distribución**: Solo copie la carpeta generada para compartir

## Requisitos

- Windows, macOS o Linux
- 500 MB de espacio en disco
- 4 GB de RAM recomendados

## Solución de Problemas

Si la aplicación no inicia correctamente:

1. Verifique que no haya otra instancia de la aplicación en ejecución
2. Compruebe que el puerto 8501 no esté en uso por otra aplicación
3. Asegúrese de que su sistema tenga una versión moderna de navegador web

## Notas Importantes

- La aplicación sigue utilizando un navegador web para mostrar la interfaz principal
- Todos los archivos de datos se almacenan en el mismo directorio de la aplicación
- Para preservar sus datos al actualizar, copie las carpetas `csv` y `conocimiento`