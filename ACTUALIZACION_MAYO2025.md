# Actualización de Mayo 2025 - Calculadora de Turnos

## Resumen de Cambios

En esta actualización de mayo 2025, hemos implementado mejoras significativas que incrementan las capacidades de memoria y análisis contextual de la Calculadora de Turnos en Radiología, incorporando un sistema de almacenamiento vectorial y recuperación de contexto histórico.

## Nuevas Características

### 1. Sistema de Contexto Histórico

Hemos implementado un sistema completo de memoria persistente que permite a la calculadora y al asistente phi-2 recordar:

- Procesamientos anteriores realizados
- Patrones de clasificación aprendidos
- Consultas previas y sus resultados
- Conocimiento acumulado sobre procedimientos médicos

La implementación se basa en la estrategia RAPTOR (Retrieval Augmented Prompt with Tree Organized Resumes) que proporciona escalabilidad a largo plazo.

### 2. Asistente phi-2 Mejorado

El asistente phi-2 ahora es capaz de:

- Recuperar información histórica relevante para cada consulta
- Generar respuestas más precisas y contextualizadas
- Realizar comparaciones con datos históricos
- Mantener coherencia a lo largo de conversaciones extensas

### 3. Consultas SQL Enriquecidas

Las consultas SQL en lenguaje natural ahora:

- Incluyen contexto histórico relevante
- Tienen conocimiento de la estructura actual de la base de datos
- Pueden hacer referencia a entidades mencionadas en consultas anteriores
- Producen resultados más precisos y relevantes

### 4. Script de Demostración Integrado

Se ha creado un script demostrativo completo (`demo_sistema_integrado.py`) que permite:

- Procesar archivos CSV con memoria histórica
- Realizar consultas en lenguaje natural al asistente
- Ejecutar consultas SQL con contexto
- Interactuar con el sistema mediante un modo interactivo completo

## Componentes Nuevos

Esta actualización incluye los siguientes nuevos archivos:

1. **contexto_vectorial.py** - Sistema base de embeddings con Sentence Transformers
2. **recuperacion_contexto.py** - Sistema de recuperación de contexto relevante
3. **websocket_server.py** - Servidor WebSocket para exposición de servicios
4. **integracion_contexto_calculadora.py** - Integración con la calculadora
5. **demo_sistema_integrado.py** - Script demostrativo del sistema completo
6. **SISTEMA_CONTEXTO.md** - Documentación del sistema de contexto

## Beneficios Principales

### Mayor Precisión

El sistema de contexto mejora significativamente la precisión en:
- Clasificación de procedimientos
- Respuestas del asistente
- Consultas SQL generadas
- Análisis de tendencias temporales

### Eficiencia Mejorada

La implementación permite:
- Generación más rápida de respuestas complejas
- Menor necesidad de reprocesar datos históricos
- Más precisión en la primera respuesta, reduciendo iteraciones
- Consultas que combinan datos de múltiples procesamientos

### Escalabilidad

El sistema ha sido diseñado para escalar eficientemente:
- Manejo transparente del crecimiento de datos históricos
- Compresión automática de información antigua
- Estructura jerárquica que prioriza información relevante
- Mantenimiento automático del tamaño del almacén

## Requisitos Adicionales

Esta actualización añade las siguientes dependencias:

- **sentence-transformers**: Para generación de embeddings de alta calidad
- **chromadb**: Para almacenamiento vectorial persistente
- **websockets**: Para exposición de servicios
- **uuid**: Para identificación única de documentos

Estos pueden instalarse con:

```bash
pip install sentence-transformers chromadb websockets uuid
```

## Uso Recomendado

Para aprovechar al máximo las nuevas capacidades:

1. Utilice el script de demostración para explorar las funcionalidades:
   ```bash
   python demo_sistema_integrado.py --interactivo
   ```

2. Para procesar nuevos datos con memoria contextual:
   ```bash
   python demo_sistema_integrado.py --proceso datos.csv
   ```

3. Para realizar consultas específicas con contexto:
   ```bash
   python demo_sistema_integrado.py --consulta "Análisis por fecha" --sql "TAC dobles por sala"
   ```

## Próximos Pasos

En futuras actualizaciones, planeamos expandir estas capacidades con:

1. **Análisis predictivo**: Utilizar el histórico para predecir tendencias
2. **Automatización de reportes**: Generar informes periódicos con insights clave
3. **API REST completa**: Exponer todas las funcionalidades a través de endpoints REST
4. **Panel administrativo avanzado**: Interfaz visual para gestión del sistema