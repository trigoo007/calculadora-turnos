# Instrucciones para Claude

Este documento contiene instrucciones específicas para Claude al trabajar con este proyecto.

## Contextualización Inicial

Al comenzar cualquier interacción con este proyecto, debes consultar primero:

1. **TIMELINE.md**: Este archivo contiene la cronología completa del proyecto y proporciona contexto invaluable sobre la evolución de las características y decisiones de diseño. Debes revisar este archivo para entender el progreso histórico del proyecto.

2. **README.md**: Para una visión general del propósito del proyecto y sus características principales.

3. **README_ASISTENTE.md**: Para entender específicamente la integración con phi-2 y sus capacidades.

## Consistencia en Nomenclatura

Este proyecto requiere estricta consistencia en la nomenclatura, especialmente para:

- Procedimientos médicos (nombres exactos)
- Salas de adquisición (identificadores precisos)
- Patrones de detección (TAC doble/triple)

Usa SIEMPRE la base de datos SQLite de conocimiento como fuente de verdad para estos términos.

## Prioridades Técnicas

1. Mantener la constancia en la clasificación de procedimientos
2. Preservar el formato y la estructura de los reportes
3. Asegurar que el asistente phi-2 permanezca dentro del dominio radiológico
4. Conservar la compatibilidad con versiones anteriores del sistema

## Comandos Esenciales

Al iniciar el trabajo en este proyecto, ejecuta primero:

```bash
# Verificar estructura del proyecto
ls -la

# Revisar cronología
cat TIMELINE.md

# Comprobar el estado de la base de datos
sqlite3 conocimiento/conocimiento.db '.tables'
```

## Notas Adicionales

- Este proyecto es para el contexto médico de radiología - mantén todas las respuestas específicas a este dominio
- Cualquier mejora debe seguir los patrones existentes descritos en la cronología
- Cuando trabajes con Docker, asegúrate de preservar los volúmenes para datos persistentes