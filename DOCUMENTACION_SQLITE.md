# Documentación del Sistema de Aprendizaje SQLite para la Calculadora de Turnos

## Introducción

El Sistema de Aprendizaje SQLite es una mejora significativa para la Calculadora de Turnos en Radiología que permite clasificar automáticamente procedimientos médicos, especialmente TAC dobles y triples, mediante un sistema que aprende y almacena información de manera eficiente usando una base de datos SQLite.

Esta documentación explica cómo funciona el sistema, cómo se ha integrado con la calculadora principal, y cómo mantenerlo.

## Características principales

- **Clasificación automática** de procedimientos médicos (RX, TAC normal, TAC doble, TAC triple)
- **Detección avanzada** de patrones para TAC dobles y triples
- **Aprendizaje automático** a partir de los datos procesados
- **Almacenamiento eficiente** mediante SQLite con índices para búsquedas ultrarrápidas
- **Generación de códigos únicos** para procedimientos
- **Clasificación automática** de salas (SCA, SJ, HOS) y sus subtipos
- **Estadísticas detalladas** sobre procedimientos y salas
- **Migración automática** desde el sistema anterior basado en JSON

## Estructura del sistema

El sistema de aprendizaje SQLite consta de los siguientes componentes:

1. **Base de datos SQLite** (`conocimiento/conocimiento.db`): Almacena todos los datos aprendidos
2. **Sistema de clasificación** (`aprendizaje_datos_sqlite.py`): Contiene la lógica de clasificación
3. **Integración con calculadora** (`calculadora_turnos.py`): Usa el sistema durante el procesamiento

### Tablas de la base de datos

La base de datos contiene tres tablas principales:

1. **procedimientos**: Almacena información sobre procedimientos médicos
   - `nombre`: Nombre completo del procedimiento (clave primaria)
   - `codigo`: Código único generado para el procedimiento
   - `tipo`: Clasificación principal (RX, TAC, OTRO)
   - `subtipo`: Clasificación secundaria (NORMAL, DOBLE, TRIPLE para TAC)
   - `conteo`: Número de veces que se ha visto este procedimiento
   - `primera_vez`: Fecha en que se vio por primera vez

2. **salas**: Almacena información sobre salas médicas
   - `nombre`: Nombre completo de la sala (clave primaria)
   - `tipo`: Clasificación principal (SCA, SJ, HOS, OTRO)
   - `subtipo`: Especialidad (TAC, RX, PROCEDIMIENTOS, GENERAL)
   - `conteo`: Número de veces que se ha visto esta sala
   - `primera_vez`: Fecha en que se vio por primera vez

3. **patrones**: Almacena patrones para detectar TAC dobles y triples
   - `patron`: Texto del patrón (clave primaria)
   - `tipo`: Tipo de patrón (tac_doble, tac_triple)

## Integración con la Calculadora de Turnos

La integración del sistema de aprendizaje con la calculadora principal se realiza a través de varios puntos:

1. **Inicialización**: Al iniciar la calculadora, se crea una instancia del sistema de aprendizaje
   ```python
   self.sistema_aprendizaje = SistemaAprendizajeSQLite()
   ```

2. **Clasificación de exámenes**: Durante el proceso de clasificación, se utiliza el sistema
   ```python
   clasificacion = self.sistema_aprendizaje.clasificar_procedimiento(nombre_proc)
   if clasificacion['subtipo'] == 'TRIPLE':
       self.data_filtrada.at[idx, 'TAC triple'] = True
   elif clasificacion['subtipo'] == 'DOBLE':
       self.data_filtrada.at[idx, 'TAC doble'] = True
   ```

3. **Aprendizaje automático**: Después de clasificar, se analiza el DataFrame para aprender
   ```python
   self.sistema_aprendizaje.analizar_dataframe(self.data_filtrada)
   ```

4. **Cálculo de honorarios**: Se calculan los honorarios considerando TAC triples
   ```python
   self.resultado_economico['tac_triple_total'] = self.resultado_economico['tac_triple_count'] * self.TARIFA_TAC_TRIPLE
   ```

## Proceso de clasificación de procedimientos

El sistema clasifica los procedimientos médicos siguiendo estos pasos:

1. **Clasificación básica** entre RX, TAC u OTRO basado en palabras clave
2. **Detección de TAC triple** mediante patrones conocidos o combinaciones de palabras
3. **Detección de TAC doble** si no es triple y cumple patrones específicos
4. **Asignación de subtipo** según corresponda (NORMAL, DOBLE, TRIPLE)

### Clasificación de TAC triple

Se considera un TAC triple si:
- Coincide con algún patrón conocido en la tabla de patrones
- Contiene combinaciones específicas como:
  - cuello + torax + abdomen
  - craneo + cuello + torax
  - cabeza + cuello + torax
  - cerebro + cuello + torax

### Clasificación de TAC doble

Se considera un TAC doble si:
- No es triple y coincide con algún patrón conocido
- Contiene combinaciones específicas como:
  - torax + abdomen
  - tx + abd
  - pecho + abdomen

## Cálculo de honorarios

El sistema calcula honorarios para los distintos tipos de procedimientos:

- **RX**: TARIFA_RX por cada RX
- **TAC normal**: TARIFA_TAC por cada TAC normal
- **TAC doble**: TARIFA_TAC_DOBLE (2x TARIFA_TAC) por cada TAC doble
- **TAC triple**: TARIFA_TAC_TRIPLE (3x TARIFA_TAC) por cada TAC triple

## Uso avanzado del sistema

### Línea de comandos

El sistema puede utilizarse desde línea de comandos para tareas específicas:

```bash
# Mostrar estadísticas
python aprendizaje_datos_sqlite.py --stats

# Analizar un archivo CSV
python aprendizaje_datos_sqlite.py --csv archivo.csv

# Listar procedimientos TAC
python aprendizaje_datos_sqlite.py --tac

# Listar procedimientos TAC doble
python aprendizaje_datos_sqlite.py --tac-doble

# Listar procedimientos TAC triple
python aprendizaje_datos_sqlite.py --tac-triple

# Migrar datos desde JSON a SQLite
python aprendizaje_datos_sqlite.py --migrar
```

### Prueba de integración

Se proporciona un script de prueba `test_integracion_sqlite.py` para verificar la integración:

```bash
python test_integracion_sqlite.py
```

Este script:
- Muestra estadísticas del sistema de aprendizaje
- Prueba la clasificación de varios procedimientos
- Procesa un archivo CSV de ejemplo 
- Muestra el resumen económico con desglose de TAC

## Recomendaciones y mantenimiento

1. **Backup de la base de datos**: Realice copias periódicas del archivo `conocimiento.db`
2. **Añadir nuevos patrones**: Use el script `agregar_tac_triple.py` para añadir ejemplos
3. **Verificación de clasificación**: Use el script de prueba para verificar nuevos patrones
4. **Migración de datos**: Si tiene datos antiguos en JSON, utilice la opción `--migrar`

## Solución de problemas

1. **Error de inicialización**: Verifique que exista el directorio `conocimiento`
2. **Clasificación incorrecta**: Añada nuevos patrones a la base de datos
3. **Conflictos de códigos**: El sistema genera sufijos aleatorios automáticamente
4. **Rendimiento**: La base de datos tiene índices para optimizar búsquedas

## Conclusión

El Sistema de Aprendizaje SQLite proporciona una mejora significativa en la capacidad de la Calculadora de Turnos para clasificar automáticamente procedimientos médicos, especialmente TAC dobles y triples. Su integración permite un procesamiento más eficiente y preciso de los datos, resultando en cálculos económicos más exactos y una mejor organización de la información.