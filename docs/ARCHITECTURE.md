# Arquitectura del Sistema - Calculadora de Turnos

## Visión General

La Calculadora de Turnos es una aplicación modular diseñada siguiendo principios de arquitectura limpia y separación de responsabilidades. El sistema está organizado en capas bien definidas que facilitan el mantenimiento, testing y escalabilidad.

## Estructura de Capas

```
┌─────────────────────────────────────────────┐
│          Capa de Presentación (UI)          │
│         (Streamlit Web Interface)           │
└─────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────┐
│         Capa de Lógica de Negocio          │
│    (Core: Processing, Classification,       │
│     Calculation, Report Generation)         │
└─────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────┐
│          Capa de Persistencia               │
│         (SQLite Database Layer)             │
└─────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────┐
│            Capa de Datos                    │
│    (File System: Raw, Processed, Output)    │
└─────────────────────────────────────────────┘
```

## Componentes Principales

### 1. Módulo Core (`src/core/`)

#### 1.1 Data Processing (`data_processing.py`)
- **Responsabilidad**: Lectura, limpieza y transformación de datos
- **Clases principales**:
  - `DataProcessor`: Maneja todo el pipeline de procesamiento
- **Funciones clave**:
  - `read_excel()`: Lee archivos Excel con detección automática
  - `read_csv()`: Lee archivos CSV con encoding configurable
  - `detect_columns()`: Detecta automáticamente columnas relevantes
  - `clean_data()`: Normaliza y limpia los datos
  - `validate_data()`: Valida según reglas de negocio

#### 1.2 Exam Classification (`exam_classification.py`)
- **Responsabilidad**: Clasificación inteligente de exámenes médicos
- **Clases principales**:
  - `ExamClassifier`: Motor de clasificación con cache
- **Funciones clave**:
  - `classify_exam()`: Clasifica un examen completo
  - `_is_tac_double()`: Detecta TAC dobles
  - `_is_tac_triple()`: Detecta TAC triples
  - `_estimate_complexity()`: Calcula complejidad (1-5)
  - `_estimate_time()`: Estima tiempo del procedimiento

#### 1.3 Turno Calculator (`turno_calculator.py`)
- **Responsabilidad**: Cálculo de turnos y honorarios
- **Clases principales**:
  - `TurnoCalculator`: Calculadora con tarifas configurables
- **Funciones clave**:
  - `calcular_turnos()`: Calcula turnos y honorarios completos
  - `_asignar_a_turnos()`: Asigna exámenes a turnos específicos
  - `_calcular_horas_trabajadas()`: Calcula horas por turno
  - `_calcular_honorarios()`: Calcula honorarios totales

#### 1.4 Report Generator (`report_generator.py`)
- **Responsabilidad**: Generación de reportes en múltiples formatos
- **Clases principales**:
  - `ReportGenerator`: Generador con templates configurables
- **Funciones clave**:
  - `generar_reporte_completo()`: Excel con múltiples hojas
  - `generar_correo()`: Genera contenido de email
  - `exportar_csv()`: Exporta a CSV
  - `generar_resumen_texto()`: Resumen en texto plano

### 2. Módulo de Base de Datos (`src/db/`)

#### 2.1 SQLite Manager (`sqlite_manager.py`)
- **Responsabilidad**: Gestión de la persistencia de datos
- **Clases principales**:
  - `SQLiteManager`: Gestor con connection pooling
- **Tablas principales**:
  - `procedimientos`: Catálogo de procedimientos médicos
  - `salas`: Registro de salas y centros
  - `patrones_clasificacion`: Patrones para clasificación
  - `historico_examenes`: Histórico de exámenes procesados
  - `configuracion`: Configuración persistente

### 3. Módulo UI (`src/ui/`)

#### 3.1 Streamlit App (`streamlit_app.py`)
- **Responsabilidad**: Interfaz de usuario web
- **Componentes**:
  - Carga de archivos con drag & drop
  - Visualización interactiva de datos
  - Pestañas para workflow completo
  - Generación de reportes descargables
  - Asistente integrado con chat

### 4. Configuración (`config/`)

#### 4.1 Settings (`settings.py`)
- **Configuraciones centralizadas**:
  - Rutas de directorios
  - Configuración de base de datos
  - Parámetros de procesamiento
  - Tarifas y horarios
  - Configuración de UI
  - Logging y caché

#### 4.2 Knowledge Base (`knowledge/`)
- **Archivos JSON con conocimiento del dominio**:
  - `procedimientos.json`: Catálogo de procedimientos
  - `salas.json`: Información de salas
  - `patrones_tac_doble.json`: Patrones para TAC doble
  - `patrones_tac_triple.json`: Patrones para TAC triple

## Flujo de Datos

```
1. Usuario carga archivo (CSV/Excel)
         ↓
2. DataProcessor lee y limpia datos
         ↓
3. ExamClassifier clasifica cada examen
         ↓
4. SQLiteManager persiste información
         ↓
5. TurnoCalculator calcula turnos/honorarios
         ↓
6. ReportGenerator genera reportes
         ↓
7. UI muestra resultados y permite descargas
```

## Patrones de Diseño Utilizados

### 1. **Singleton Pattern**
- Usado en `SQLiteManager` para mantener una única instancia de conexión a BD

### 2. **Factory Pattern**
- En generación de reportes para diferentes formatos

### 3. **Strategy Pattern**
- En clasificación de exámenes según tipo

### 4. **Repository Pattern**
- `SQLiteManager` actúa como repositorio para entidades del dominio

### 5. **Dependency Injection**
- Los módulos reciben sus dependencias a través del constructor

## Consideraciones de Seguridad

1. **Validación de Entrada**
   - Todos los datos de entrada son validados
   - Sanitización de nombres de archivo

2. **Gestión de Base de Datos**
   - Uso de prepared statements
   - Transacciones para operaciones críticas

3. **Manejo de Errores**
   - Try-catch comprehensivos
   - Logging de errores sin exponer información sensible

4. **Configuración**
   - Separación de configuración sensible
   - Uso de variables de entorno

## Escalabilidad

### Horizontal
- La aplicación puede ejecutarse en múltiples instancias
- Base de datos SQLite puede migrarse a PostgreSQL/MySQL

### Vertical
- Procesamiento por lotes configurable
- Caché para operaciones costosas

## Testing

### Estructura de Tests
```
tests/
├── unit/           # Tests unitarios por módulo
├── integration/    # Tests de integración
└── e2e/           # Tests end-to-end
```

### Cobertura Objetivo
- Unit tests: >80% cobertura
- Integration tests: Flujos críticos
- E2E tests: Happy path principal

## Deployment

### Docker
- Dockerfile optimizado con multi-stage build
- docker-compose para desarrollo local

### Producción
- Recomendado: Docker + reverse proxy (nginx)
- Alternativa: Heroku, AWS ECS, Google Cloud Run

## Monitoreo y Logging

### Logging
- Configuración centralizada en `settings.py`
- Niveles: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Rotación automática de logs

### Métricas
- Tiempo de procesamiento por archivo
- Cantidad de exámenes procesados
- Errores de clasificación
- Uso de memoria y CPU

## Mantenimiento

### Actualización de Conocimiento
1. Modificar archivos JSON en `config/knowledge/`
2. Ejecutar scripts de migración si es necesario
3. Reiniciar aplicación

### Backup
- Script automático en `scripts/backup_db.sh`
- Backup de base de datos y archivos de configuración

## Roadmap Futuro

1. **API REST**
   - Exponer funcionalidad como API
   - Integración con sistemas externos

2. **Machine Learning**
   - Mejorar clasificación con ML
   - Predicción de tiempos

3. **Multi-tenancy**
   - Soporte para múltiples organizaciones
   - Aislamiento de datos

4. **Reportes Avanzados**
   - Dashboards interactivos
   - Análisis predictivo 