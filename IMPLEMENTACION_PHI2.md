# Implementación del Asistente con phi-2

Este documento describe la implementación y configuración del asistente basado en phi-2 para la Calculadora de Turnos en Radiología.

## Estructura de la Integración

La integración de phi-2 se realizó en varios componentes:

1. **Módulo Principal** (`asistente_phi2.py`): Clase AsistentePhi2 que gestiona la comunicación con Ollama, la generación de consultas SQL y respuestas en lenguaje natural.

2. **Interfaz Independiente** (`asistente_streamlit.py`): Aplicación Streamlit independiente que permite usar el asistente sin necesidad de cargar la calculadora completa.

3. **Integración en Calculadora** (`calculadora_streamlit.py`): Tab adicional en la calculadora principal que integra el asistente.

4. **Script de Prueba** (`test_phi2.py`): Verifica la funcionalidad básica del asistente con datos de ejemplo.

5. **Configuración Docker** (`Dockerfile`, `docker-compose.yml`, `docker-entrypoint.sh`): Permite desplegar la aplicación con todas sus dependencias en un contenedor.

## Características Implementadas

- **Consultas en lenguaje natural**: Convierte preguntas en español a consultas SQL
- **Generación de respuestas**: Responde consultas sobre radiología usando el contexto de la base de datos
- **Análisis automático**: Genera insights sobre los datos cargados
- **Restricción de dominio**: Limita respuestas exclusivamente al ámbito radiológico
- **Infraestructura local**: Todo el procesamiento se realiza en la máquina local (privacidad)

## Configuración de Prompts

Se optimizaron cuidadosamente los prompts para mejorar la interacción con phi-2:

1. **Generación SQL**:
   - Instrucciones estructuradas para generar solo SQL válido
   - Manejo adecuado de nombres de columnas con espacios
   - Restricciones para evitar comentarios o explicaciones

2. **Respuestas Generales**:
   - Contexto de dominio médico radiológico
   - Límites claros para enfocarse exclusivamente en datos radiológicos
   - Instrucciones para generar respuestas concisas y directas

3. **Procesamiento de Respuestas**:
   - Limpieza de texto no deseado
   - Extracción de consultas SQL válidas
   - Corrección automática de errores comunes

## Implementación Docker

El contenedor Docker proporciona un entorno completo con todas las dependencias:

1. **Base**: Python 3.9 slim
2. **Ollama**: Motor para ejecutar modelos de lenguaje local
3. **phi-2**: Modelo de lenguaje liviano (1.7B parámetros)
4. **Streamlit**: Interfaz web interactiva
5. **Dependencias adicionales**: pandas, numpy, plotly, etc.

El `docker-entrypoint.sh` automatiza:
- Inicialización de Ollama
- Descarga de phi-2 si no está disponible
- Instalación de dependencias
- Inicio de la aplicación Streamlit

## Cómo Usar el Asistente

### Opción 1: Ejecución Local

```bash
# Instalar Ollama
brew install ollama  # macOS
curl -fsSL https://ollama.com/install.sh | sh  # Linux

# Descargar phi-2
ollama pull phi

# Iniciar la aplicación
streamlit run calculadora_streamlit.py
```

### Opción 2: Docker (Recomendado)

```bash
# Construir y ejecutar con Docker Compose
docker-compose up -d

# Acceder a la aplicación
# http://localhost:8502
```

## Limitaciones Actuales

1. **Generación SQL**: En ocasiones produce SQL con errores para consultas complejas
2. **Restricción de Dominio**: Puede ser demasiado restrictivo en algunos casos
3. **Velocidad**: El primer uso puede ser lento debido a la carga del modelo
4. **Hardware**: Funciona mejor con al menos 8GB de RAM disponible

## Próximos Pasos

1. Refinar los prompts para mejorar la generación de SQL
2. Implementar caché de consultas para mejorar rendimiento
3. Agregar análisis visual automático según tipo de consulta
4. Expandir el dominio de conocimiento médico
5. Evaluar modelos alternativos como Gemma 2B o LLaMA 3 7B

## Comandos Útiles

```bash
# Probar integracion
python test_phi2.py

# Iniciar solo el asistente
streamlit run asistente_streamlit.py

# Verificar estado de Ollama
ollama list

# Reiniciar contenedor Docker
docker-compose restart
```