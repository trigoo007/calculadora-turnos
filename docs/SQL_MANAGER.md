# SQLite Manager para la Base de Datos de Conocimiento

La Calculadora de Turnos ahora incluye un gestor de bases de datos SQLite accesible vía web, que facilita la visualización y edición de la base de datos de conocimiento.

## Acceso

Con la aplicación en Docker ejecutándose, accede al SQLite Manager en:

**URL**: http://localhost:8503

## Propósito

El SQLite Manager proporciona una interfaz gráfica para gestionar la base de datos `conocimiento.db` que contiene:

1. **Procedimientos médicos**: Nombres y clasificaciones estandarizados
2. **Salas**: Información sobre las salas de adquisición
3. **Patrones**: Patrones de clasificación para TAC doble y triple
4. **Otras tablas**: Tablas adicionales que contienen conocimiento aprendido

## Funcionalidades

- **Visualización de datos**: Ver el contenido de todas las tablas
- **Edición de registros**: Modificar nombres de procedimientos o salas
- **Ejecución de SQL**: Realizar consultas personalizadas
- **Exportación/Importación**: Hacer copias de seguridad o restaurar datos

## Recomendaciones de uso

1. **Visualización antes de editar**: Siempre revisa la estructura y los datos existentes antes de hacer cambios
2. **Consistencia en nombres**: Mantén consistencia en la nomenclatura
3. **Copias de seguridad**: Exporta la base de datos antes de hacer cambios importantes
4. **Validación**: Después de editar, verifica que los cambios sean reconocidos por el asistente phi-2

## Estructura de datos

La base de datos tiene la siguiente estructura principal:

- **procedimientos**: Información sobre procedimientos médicos
  - `nombre`: Nombre completo del procedimiento
  - `tipo`: Tipo de procedimiento (RX, TAC)
  - `tac_doble`: Flag para TAC doble
  - `tac_triple`: Flag para TAC triple

- **salas**: Información sobre salas de adquisición
  - `nombre`: Identificador de la sala
  - `descripcion`: Descripción de la sala
  - `tipo`: Tipo de sala (RX, TAC)

- **patrones_tac_doble**: Patrones para identificar TAC dobles
  - `patron`: Texto o patrón a buscar
  - `descripcion`: Descripción o justificación

- **patrones_tac_triple**: Patrones para identificar TAC triples
  - `patron`: Texto o patrón a buscar
  - `descripcion`: Descripción o justificación

## Beneficios para el asistente phi-2

Al mantener una base de datos de conocimiento bien estructurada:

1. El asistente phi-2 puede generar consultas SQL más precisas
2. Se mantiene consistencia en la nomenclatura de procedimientos y salas
3. La clasificación de TAC doble y triple es más fiable
4. El análisis de datos es más preciso y útil

## Importante

Los cambios realizados en la base de datos son permanentes y afectan inmediatamente al funcionamiento del asistente, sin necesidad de reiniciar la aplicación.