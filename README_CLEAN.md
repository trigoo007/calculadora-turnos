# Calculadora de Turnos en Radiología

## Descripción
Aplicación para procesar y calcular turnos en radiología con análisis de procedimientos médicos.

## Archivos Esenciales

### Aplicación Principal
- `ui/calculadora_streamlit.py` - Interfaz principal de Streamlit
- `experimental/streamlit_contexto.py` - Versión con contexto vectorial
- `aprendizaje_datos_sqlite.py` - Gestión de base de datos
- `asistente_phi2.py` - Asistente de IA
- `config.py` - Configuración

### Docker
- `Dockerfile` - Imagen básica
- `Dockerfile.contexto` - Imagen con contexto vectorial
- `docker-compose.yml` - Configuración básica
- `docker-compose-contexto.yml` - Configuración avanzada
- `docker-entrypoint.sh` - Script de entrada básico
- `docker-entrypoint-contexto.sh` - Script de entrada avanzado

### Instalación
- `instalar_y_ejecutar.sh` - Instalación básica
- `instalar_con_cloudflare.sh` - Instalación con Cloudflare
- `backup_automatico.sh` - Script de respaldo

### Dependencias
- `requirements.txt` - Dependencias básicas
- `requirements-contexto.txt` - Dependencias adicionales

## Ejecución Rápida

```bash
# Versión básica
./instalar_y_ejecutar.sh

# Con Docker
docker-compose up -d

# Versión con contexto vectorial
docker-compose -f docker-compose-contexto.yml up -d
```

## Carpetas
- `csv/` - Archivos de datos
- `conocimiento/` - Base de datos SQLite
- `ui/` - Interfaz de usuario
- `experimental/` - Funcionalidades experimentales
- `procesamiento/` - Módulos de procesamiento
- `utils/` - Utilidades
