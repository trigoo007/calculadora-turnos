# Ejecutando la Calculadora de Turnos en Docker

Este documento proporciona instrucciones para ejecutar la aplicación en Docker con la integración del asistente phi-2.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Inicio rápido

Para iniciar la aplicación completa (incluyendo Ollama y phi-2):

```bash
docker-compose up -d
```

La aplicación estará disponible en:
- **URL**: http://localhost:8501

## Estructura Docker

La configuración Docker incluye:

1. **Aplicación Streamlit**: La calculadora de turnos y el asistente phi-2
2. **Ollama**: Servicio para ejecutar el modelo phi-2 localmente
3. **Volúmenes**: Para persistir archivos CSV, conocimiento y datos de análisis

## Cómo funciona

El contenedor Docker:

1. Inicia el servicio Ollama en segundo plano
2. Descarga automáticamente el modelo phi-2 si no está disponible
3. Inicia la aplicación Streamlit en el puerto 8501

## Volúmenes persistentes

Los siguientes datos son persistentes entre reinicios:

- **/app/csv**: Archivos CSV de entrada y resultados
- **/app/conocimiento**: Base de datos SQLite con el conocimiento aprendido

## Puertos expuestos

- **8501**: Interfaz web de Streamlit
- **11434**: API de Ollama (útil para desarrollo)

## Integración con phi-2

El modelo phi-2 (1.7B parámetros) se utiliza para:

1. Consultas en lenguaje natural sobre los datos radiológicos
2. Generación de SQL a partir de preguntas en español
3. Análisis automático de los datos cargados

## Problemas comunes

- **Error "Ollama no disponible"**: El contenedor puede necesitar más tiempo para iniciar Ollama. Espera unos minutos y recarga la página.
- **Descargas lentas**: La primera ejecución descarga el modelo phi-2 (~1.6GB), lo que puede tardar según tu conexión.
- **Uso de memoria**: El contenedor requiere ~4GB de RAM para funcionar correctamente.

## Construir la imagen manualmente

Si necesitas personalizar la imagen:

```bash
docker build -t calculadora-turnos .
docker run -p 8501:8501 -p 11434:11434 -v ./csv:/app/csv calculadora-turnos
```

## Actualizar la imagen

Para actualizar a la última versión:

```bash
docker-compose down
docker-compose pull
docker-compose up -d
```