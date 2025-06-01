# Plantilla para Changelog con Timestamps

Utiliza esta plantilla al documentar nuevas actualizaciones en el proyecto. Incluye siempre la hora exacta (HH:MM) para cada cambio, lo que facilita el seguimiento preciso del desarrollo.

## Ejemplo para Actualización Menor (PATCH)

```markdown
#### vX.X.Y - HH:MM - Breve descripción
- HH:MM - Detalle del cambio específico realizado
- HH:MM - Segundo cambio o corrección
- HH:MM - Tercer cambio o mejora
```

## Ejemplo para Actualización de Característica (MINOR)

```markdown
#### vX.Y.0 - HH:MM - Nombre de la nueva característica
- HH:MM - Implementación de la característica principal
- HH:MM - Componente específico desarrollado
- HH:MM - Tests implementados
- HH:MM - Documentación actualizada
```

## Ejemplo para Actualización Mayor (MAJOR)

```markdown
### DD/MM/AAAA - Título del Lanzamiento Mayor

#### vY.0.0 - HH:MM - Nombre de la versión mayor
- HH:MM - Cambio arquitectónico principal
- HH:MM - Migración de sistema X a sistema Y
- HH:MM - Implementación de nuevo paradigma
- HH:MM - Actualización de dependencias críticas
```

## Convenciones Importantes

1. **Formato de hora**: Utilizar siempre formato 24 horas (HH:MM)
2. **Orden cronológico**: Ordenar los cambios por hora de implementación
3. **Fecha completa**: Incluir la fecha completa (DD/MM/AAAA) para secciones principales
4. **Versionado semántico**: Seguir MAJOR.MINOR.PATCH

## Proceso Recomendado

1. Obtener la hora actual antes de cada entrada: `date "+%H:%M"`
2. Registrar inmediatamente el cambio después de implementarlo
3. Para sesiones de trabajo prolongadas, seguir actualizando el registro con entradas incrementales
4. Al finalizar, revisar el registro para garantizar la coherencia de los timestamps