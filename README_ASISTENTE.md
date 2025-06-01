# Asistente de Análisis con phi-2

Esta aplicación integra el modelo phi-2 de Microsoft para proporcionar capacidades de procesamiento de lenguaje natural y consultas SQL en la calculadora de turnos de radiología.

**Actualizado (Mayo 2025)**: Se han realizado mejoras significativas en los prompts y la integración con Docker. Ver [RESUMEN_PHI2.md](RESUMEN_PHI2.md) para más detalles.

## Características

- **Consultas en lenguaje natural**: Realiza preguntas sobre tus datos en español conversacional
- **Análisis automático**: Obtén insights sobre tus datos sin necesidad de conocer SQL
- **Liviano y rápido**: Funciona en CPU estándar sin requerir GPU
- **Privacidad total**: Todos los datos y análisis se procesan localmente en tu máquina

## Requisitos

- **Ollama**: Motor para ejecutar modelos de lenguaje de forma local
- **phi-2**: Modelo de lenguaje pequeño (1.7B parámetros) desarrollado por Microsoft

## Instalación

1. Instalar Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

2. Descargar el modelo phi-2

```bash
ollama pull phi
```

3. Iniciar Ollama

```bash
ollama serve
```

## Uso

### Opción 1: Ejecución Local

1. Inicia la aplicación Streamlit:

```bash
streamlit run calculadora_streamlit.py
```

2. Carga tus archivos CSV con datos de exámenes radiológicos

3. Navega a la pestaña "Asistente phi-2"

4. Realiza consultas en lenguaje natural, por ejemplo:
   - "¿Cuántos exámenes de cada tipo hay en total?"
   - "¿Cuáles son los procedimientos más comunes?"
   - "Muestra la distribución de exámenes por sala y tipo"

### Opción 2: Usando Docker (Recomendado)

1. Inicia la aplicación con Docker Compose:

```bash
docker-compose up -d
```

2. Accede a los servicios en tu navegador:
   - **Calculadora**: http://localhost:8502
   - **SQLite Manager**: http://localhost:8503 (para gestionar la base de datos de conocimiento)

3. Las dependencias (Ollama y phi-2) se instalarán automáticamente

4. Los archivos CSV en la carpeta `csv/` y la base de conocimiento en `conocimiento/` se montarán automáticamente en el contenedor

5. La base de datos de conocimiento se carga automáticamente para garantizar la consistencia en nombres de procedimientos y salas

Consulta [DOCKER.md](DOCKER.md) para más detalles sobre la configuración Docker y [SQL_MANAGER.md](SQL_MANAGER.md) para información sobre cómo gestionar la base de datos.

## ¿Por qué phi-2?

phi-2 es ideal para esta aplicación porque:

- **Ultraliviano**: Solo 1.7B parámetros, lo que permite ejecutarlo en cualquier computadora
- **Rápido en CPU**: No requiere GPU para ofrecer buena velocidad de respuesta
- **Especializado en tareas estructuradas**: Excelente en generación de SQL y razonamiento lógico
- **Consumo mínimo de recursos**: Funciona eficientemente incluso en sistemas con recursos limitados

## Ejemplos de Consultas

- "¿Cuántos exámenes TAC dobles hay en total?"
- "Muestra los 5 procedimientos más comunes"
- "¿Cuál es la distribución de exámenes por día de la semana?"
- "Compara el número de exámenes por sala"
- "¿Cuántos exámenes hay por tipo y sala?"

## Modo independiente

También puedes usar el asistente de forma independiente:

```bash
streamlit run asistente_streamlit.py
```

Esta interfaz proporciona acceso a todas las funcionalidades del asistente phi-2 sin necesidad de cargar la calculadora completa.

## Desarrollo

El asistente está implementado en tres módulos principales:

1. `asistente_phi2.py`: Clase principal que gestiona la interacción con Ollama y phi-2
2. `asistente_streamlit.py`: Interfaz Streamlit independiente para el asistente
3. Integración en `calculadora_streamlit.py`: Pestaña adicional en la aplicación principal

Para probar el sistema completo, se recomienda usar el script de prueba:

```bash
python test_phi2.py
```

Este script crea una base de datos temporal con datos de ejemplo y prueba las funciones principales del asistente.

## Limitaciones y Consideraciones

- phi-2 está optimizado para precisión en consultas específicas, no para generación de texto largo
- Para análisis médicos muy complejos o interpretación de textos extensos, puede ser necesario un modelo más grande como Mixtral o LLaMA 3
- El sistema utiliza prompts especializados para restringir las respuestas al dominio radiológico
- La generación de SQL puede fallar en consultas muy complejas o ambiguas
- La primera ejecución puede tardar varios minutos mientras se descarga el modelo phi-2 (~1.6GB)

## Próximas Mejoras

1. Expansión del dominio de conocimiento médico
2. Refinamiento de la generación SQL para consultas complejas
3. Optimización de rendimiento para bases de datos grandes
4. Integración de visualizaciones automáticas basadas en el tipo de consulta
5. Soporte para modelos alternativos (Gemma 2B, LLaMA 3, etc.)