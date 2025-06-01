# Calculadora de Turnos en Radiología

Aplicación para procesar datos de procedimientos médicos en radiología, clasificar exámenes, calcular horas trabajadas y generar reportes económicos.

> [!TIP]
> Consulta el archivo [TIMELINE.md](TIMELINE.md) para ver la historia completa de desarrollo y las últimas actualizaciones del proyecto.
>
> Para colaboradores técnicos: Revisa [CLAUDE.md](CLAUDE.md) para instrucciones específicas de trabajo con este proyecto.
>
> Se ha reorganizado la estructura del proyecto - consulta [ESTRUCTURA_PROYECTO.md](ESTRUCTURA_PROYECTO.md) para comprender la nueva organización.
>
> Guardian de Arquitectura: Revisa [GUARDIAN.md](GUARDIAN.md) e [INSTRUCCIONES_GUARDIAN.md](INSTRUCCIONES_GUARDIAN.md) para la protección de la estructura.

## Características

- Procesamiento de archivos CSV con datos de procedimientos radiológicos
- Filtrado y clasificación automática de exámenes (RX, TAC, TAC doble, TAC triple)
- Detección de procedimientos realizados en horario de turno
- Cálculo de horas trabajadas según horarios oficiales
- Cálculo de honorarios médicos
- Generación de reportes en Excel
- Generación automática de correo formal para envío de reportes
- Sistema de aprendizaje basado en SQLite para clasificación avanzada
- **¡NUEVO!** Asistente con phi-2 para consultas en lenguaje natural
- **¡NUEVO!** Guardian de Arquitectura para mantener la estructura del proyecto

## Requisitos

- Python 3.6 o superior
- Bibliotecas principales:
  - pandas
  - numpy
  - openpyxl
  - python-dateutil
  - tkinter (incluido en la mayoría de instalaciones de Python)
- Para la versión web:
  - streamlit
  - plotly
- Para el asistente phi-2 (opcional):
  - [Ollama](https://ollama.ai/) (para ejecutar phi-2 localmente)
  - requests

## Instalación

1. Asegúrese de tener Python instalado en su sistema
2. Instale las dependencias básicas:

```bash
pip install pandas numpy openpyxl python-dateutil
```

3. Para la versión web y visualizaciones:

```bash
pip install streamlit plotly
```

4. Para el asistente con phi-2 (opcional):
   - Instale Ollama desde [ollama.ai](https://ollama.ai/)
   - Descargue el modelo phi-2: `ollama pull phi`
   - Instale bibliotecas adicionales: `pip install requests`

## Uso

### Versión de escritorio

1. Ejecute el script principal:

```bash
python calculadora_turnos.py
```

2. Use la interfaz gráfica para:
   - Seleccionar el archivo CSV con datos de procedimientos
   - Elegir el directorio donde guardar los reportes
   - Ingresar el nombre del médico para el reporte
   - Procesar los datos y generar reportes

### Versión web (Streamlit)

1. Ejecute la aplicación web:

```bash
streamlit run ui/calculadora_streamlit.py
```

2. Utilice la interfaz web interactiva para:
   - Cargar el archivo CSV
   - Estimar días de turno automáticamente
   - Visualizar datos con gráficos interactivos
   - Generar reportes completos
   - Utilizar el asistente con phi-2 para consultas en lenguaje natural

### Asistente con phi-2 (standalone)

Para usar solo el asistente con phi-2:

```bash
streamlit run ui/asistente_streamlit.py
```

Para más detalles sobre el asistente, consulte [README_ASISTENTE.md](README_ASISTENTE.md)

## Estructura de datos esperada

El archivo CSV debe contener las siguientes columnas:

- `Número de cita`
- `Fecha del procedimiento programado`
- `Hora del procedimiento programado`
- `Apellidos del paciente`
- `Nombre del paciente`
- `ID del paciente`
- `Nombre del procedimiento`
- `Sala de adquisición`

## Horarios de turno

La aplicación detecta automáticamente si un procedimiento ocurrió dentro del horario oficial de turno:

- **Lunes a jueves**: 18:00 a 08:00 del día siguiente
- **Viernes**: 18:00 a 09:00 del sábado
- **Sábado**: 09:00 a 09:00 del domingo
- **Domingo**: 09:00 a 08:00 del lunes siguiente

## Tarifas configuradas

- Tarifa por hora: $55.000
- RX: $5.300 por examen
- TAC: $42.400 por examen
- TAC doble: $84.800 por examen
- TAC triple: $127.200 por examen

## Archivos generados

### Versión de escritorio

1. **Examenes_Filtrados.xlsx**: Contiene 4 hojas con exámenes clasificados:
   - RX SCA
   - RX SJ
   - TAC SCA
   - TAC SJ

2. **Examenes_Contabilizados.xlsx**: Solo procedimientos realizados en horario de turno

3. **Resumen_Economico.xlsx**: Desglose económico con horas trabajadas, número de exámenes y montos totales

### Versión web (actualizada)

1. **Tabla_RX.xlsx**: Datos simplificados de exámenes RX para el médico
   
2. **Tabla_TAC.xlsx**: Datos simplificados de exámenes TAC para el médico
   
3. **Contenido_Correo.txt/.xlsx**: Texto listo para enviar al médico con formato natural
   
4. **Analisis_Monetario.xlsx**: Resumen económico con cálculos de honorarios
   
5. **Detalles_Tecnicos.xlsx**: Archivo multi-hoja con información técnica detallada:
   - Resumen económico completo (incluye TAC triples)
   - Detalles de TAC dobles y triples
   - Distribución de exámenes por sala

## Funciones avanzadas

### Sistema de aprendizaje SQLite

La aplicación incluye un sistema de aprendizaje que:
- Almacena patrones de procedimientos en una base de datos SQLite
- Mejora la detección automática de TAC dobles y triples
- Se actualiza automáticamente con cada análisis

### Asistente con phi-2

La integración con phi-2 permite:
- Realizar consultas en lenguaje natural sobre los datos
- Obtener análisis automáticos sin conocimientos de SQL
- Acceder a insights complejos de forma conversacional

Consulte [README_ASISTENTE.md](README_ASISTENTE.md) para más detalles.