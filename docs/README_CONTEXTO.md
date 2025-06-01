# Sistema de Recuperación y Almacenamiento de Contexto

Este módulo implementa un sistema vectorial para mantener la "memoria" del proyecto Calculadora de Turnos en Radiología, permitiendo recuperar información relevante del historial de desarrollo y conversaciones previas.

## Características Principales

- **Embeddings con Sentence Transformers**: Utiliza el modelo `sentence-transformers/gte-base` para generar vectores de alta calidad.
- **Almacén Vectorial Chroma**: Base de datos vectorial persistente con búsqueda semántica eficiente.
- **Recuperación por Relevancia**: Obtiene fragmentos históricos relevantes para cada consulta.
- **Resúmenes Jerárquicos (RAPTOR)**: Sistema de compresión jerárquica que agrupa y resume información antigua.
- **Control de Versiones**: Gestión de versiones de documentos para evitar duplicados.
- **Mantenimiento Automático**: Gestión inteligente del espacio de almacenamiento.
- **Integración Streamlit**: Componentes listos para usar en aplicaciones Streamlit.

## Componentes

El sistema consta de los siguientes módulos:

1. **contexto_vectorial.py**: Implementa el almacenamiento y recuperación vectorial básico.
2. **recuperacion_contexto.py**: Gestiona la recuperación y mantenimiento de contexto.
3. **websocket_server.py**: Servidor WebSocket para integración con aplicaciones.
4. **streamlit_integration.py**: Componentes para integrar con Streamlit.

## Arquitectura

La arquitectura implementa la estrategia RAPTOR (Retrieval Augmented Prompt with Tree Organized Resumes):

```
Usuario → Consulta → Embedding → Búsqueda Vectorial → Recuperación Jerárquica → Contexto Recuperado
```

### Flujo de Datos

1. Las consultas del usuario se convierten a embeddings.
2. Se buscan primero en resúmenes de alto nivel (más eficiente).
3. Si es necesario, se desciende a documentos más específicos.
4. Se construye un prompt con los fragmentos más relevantes.
5. Los nuevos mensajes se almacenan en el repositorio vectorial.

## Estructura del Prompt

El sistema estructura cada prompt en bloques fijos:

```
### Sistema
(rol y reglas)

### Contexto recuperado
(fragmentos top-k)

### Historial reciente
(últimos mensajes)

### Pregunta
(input del usuario)
```

## Uso

### Iniciar el Servidor WebSocket

```bash
python websocket_server.py --host localhost --port 8009
```

### Integración en Aplicaciones Streamlit

```python
import streamlit as st
from streamlit_integration import StreamlitIntegration

# Crear instancia de integración
integracion = StreamlitIntegration()

# Recuperar contexto
contexto = integracion.recuperar_contexto("cómo funciona el TAC doble")

# Mostrar chat UI
integracion.mostrar_chat_ui()

# Guardar mensajes
integracion.guardar_mensaje("Este es un mensaje de prueba", "usuario")
```

## Mantenimiento

El sistema realiza mantenimiento automático cuando:

- El número de documentos supera el umbral configurado (1000 por defecto)
- El tamaño del almacén supera el límite establecido (5 MB por defecto)
- Se solicita mantenimiento manual desde el panel de administración

Durante el mantenimiento:

1. Los documentos se agrupan por semana y tipo.
2. Se generan resúmenes para cada grupo.
3. Los documentos originales se marcan como archivados.
4. Los documentos no accedidos en 30 días se resumen y comprimen.

## Requisitos

- Python 3.6+
- sentence-transformers
- chromadb
- websockets
- streamlit (para integración con aplicaciones Streamlit)

## Configuración

Las principales configuraciones están en constantes al inicio de cada archivo:

- **VECTORSTORE_DIR**: Directorio para persistir el almacén vectorial
- **COLLECTION_NAME**: Nombre de la colección en Chroma
- **MODEL_NAME**: Modelo de embeddings a utilizar
- **MAX_DOCUMENTS**: Límite para activar resúmenes jerárquicos
- **MAX_SIZE_MB**: Tamaño máximo del almacén vectorial