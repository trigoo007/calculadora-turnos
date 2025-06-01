# Sistema de Contexto para la Calculadora de Turnos

Este documento describe la implementación del sistema de almacenamiento y recuperación de contexto que proporciona "memoria histórica" a la Calculadora de Turnos en Radiología.

## Visión General

El Sistema de Contexto permite a la Calculadora y al Asistente phi-2 recordar información histórica sobre:

- Procesamientos anteriores de archivos CSV
- Consultas previas realizadas al sistema
- Decisiones de clasificación y cálculos económicos
- Conocimiento acumulado sobre procedimientos médicos

Esta memoria persistente mejora significativamente las capacidades del sistema, permitiendo consultas más precisas y contextualizadas.

## Componentes Principales

El sistema consta de cuatro módulos principales:

1. **contexto_vectorial.py** - Base del sistema que implementa el almacenamiento vectorial usando Chroma y Sentence Transformers
2. **recuperacion_contexto.py** - Sistema de recuperación de contexto relevante para consultas
3. **websocket_server.py** - Servidor WebSocket para exponer la funcionalidad a otras aplicaciones
4. **integracion_contexto_calculadora.py** - Integración con la Calculadora de Turnos

Adicionalmente, se proporciona un script demostrativo:

- **demo_sistema_integrado.py** - Muestra las capacidades completas del sistema

## Características Técnicas

### Embeddings y Búsqueda Semántica

El sistema utiliza el modelo `sentence-transformers/gte-base` para convertir textos en vectores, permitiendo búsquedas semánticas de alta calidad. Esto significa que puede:

- Encontrar información relacionada aunque no contenga exactamente las mismas palabras
- Recuperar contexto por similitud conceptual, no solo léxica
- Funcionar en cualquier idioma con resultados de alta calidad

### Almacenamiento Jerárquico (RAPTOR)

El sistema implementa la estrategia RAPTOR (Retrieval Augmented Prompt with Tree Organized Resumes) que:

1. Agrupa documentos antiguos por semana y tipo
2. Genera resúmenes jerárquicos para grupos de documentos
3. Marca documentos originales como archivados
4. Consulta primero resúmenes de alto nivel y solo desciende si es necesario

Esta estrategia garantiza la escalabilidad del sistema a medida que acumula más información.

### Mantenimiento Automático

Para evitar un crecimiento descontrolado del almacén:

- El sistema monitorea el tamaño del almacén vectorial
- Al superar 1 GB, comprime automáticamente los documentos menos consultados
- Mantiene estadísticas de uso para optimizar la compresión
- Limpia periódicamente documentos no accedidos en más de 30 días

## Integración con la Calculadora

La integración con la Calculadora de Turnos permite:

1. **Procesar y recordar CSV**: Cada archivo procesado se almacena en el contexto
2. **Consultas enriquecidas**: Las consultas al asistente phi-2 incluyen contexto relevante
3. **Generación SQL mejorada**: Consultas SQL más precisas gracias al contexto histórico
4. **Almacenamiento de datasets**: Los resultados de procesamientos se guardan para consultas futuras

## Integración con phi-2

El asistente phi-2 se beneficia del sistema de contexto para:

- Generar respuestas más precisas con información histórica relevante
- Crear consultas SQL que tienen en cuenta el esquema actual y procesamientos anteriores
- Mantener coherencia en conversaciones largas
- Recordar clasificaciones y decisiones tomadas previamente

## Uso del Sistema

### Mediante la API de Integración

```python
from integracion_contexto_calculadora import IntegracionContextoCalculadora

# Crear instancia
integracion = IntegracionContextoCalculadora()

# Procesar CSV con memoria
resultado = integracion.procesar_y_almacenar_csv("datos.csv", "output", "Dr. Apellido")

# Consulta con contexto histórico
respuesta = integracion.consulta_con_contexto("¿Cuántos TAC dobles hay?")

# Consulta SQL en lenguaje natural con contexto
exito, df = integracion.consulta_sql_con_contexto("Mostrar TAC dobles por fecha")
```

### Mediante el Script Demostrativo

El script de demostración proporciona una interfaz completa:

```bash
# Modo interactivo
python demo_sistema_integrado.py --interactivo

# Procesar archivo y consulta
python demo_sistema_integrado.py --proceso datos.csv --consulta "Resumen por día"

# Consulta SQL
python demo_sistema_integrado.py --sql "TAC dobles por paciente"
```

## Requisitos

- Python 3.6+
- Sentence Transformers (`sentence-transformers`)
- ChromaDB (`chromadb`)
- UUID (`uuid`)
- WebSockets (`websockets`)
- Resto de dependencias de la Calculadora

## Escenarios de Uso

1. **Análisis histórico**: "¿Cuántos TAC dobles se realizaron en abril comparado con mayo?"
2. **Consultas referenciales**: "¿Qué pacientes tuvieron el mismo tipo de procedimiento que González?"
3. **Tendencias temporales**: "¿Cuál es la distribución de exámenes por día de la semana?"
4. **Consultas complejas**: "¿Qué procedimientos tuvieron mayor crecimiento entre enero y marzo?"

## Próximas Mejoras

El sistema está preparado para las siguientes mejoras:

1. **Análisis predictivo**: Utilizar el historial para predecir cargas de trabajo
2. **Generación automática de informes**: Crear reportes con conocimiento de tendencias
3. **API REST**: Exponer toda la funcionalidad a través de una API REST
4. **Interfaz de usuario mejorada**: Panel de administración con visualizaciones avanzadas