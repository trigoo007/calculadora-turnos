# 📊 Calculadora de Turnos en Radiología

Sistema inteligente para el procesamiento y análisis de procedimientos médicos en servicios de radiología, diseñado específicamente para calcular turnos y honorarios de manera automatizada.

## 🎯 Características Principales

- **Carga automática de archivos** CSV/Excel con datos de procedimientos
- **Filtrado inteligente** de centros médicos (SCA y SJ)
- **Clasificación automática** de exámenes (RX, TAC simple, TAC doble, TAC triple)
- **Cálculo preciso** de horas trabajadas y honorarios
- **Generación de reportes** en Excel y formato de correo
- **Interfaz web moderna** con Streamlit

## 📋 Lógica de Negocio

### 1. Carga y Lectura del Archivo

El sistema lee archivos CSV/Excel que deben contener las siguientes columnas:
- Número de cita
- Fecha del procedimiento programado
- Hora del procedimiento programado
- Apellidos del paciente
- Nombre del paciente
- ID del paciente
- Nombre del procedimiento
- Sala de adquisición

### 2. Filtrado de Datos

- ✅ **Incluye** solo salas que comienzan con "SCA" o "SJ"
- ❌ **Excluye** salas que comienzan con "HOS" (Hospital)

### 3. Clasificación de Exámenes

Según el contenido de "Nombre del procedimiento":

- **RX**: Si NO contiene la palabra "TAC"
- **TAC simple**: Si contiene "TAC" y es de una sola región anatómica
- **TAC doble**: Si contiene "TAC" y abarca dos regiones anatómicas
- **TAC triple**: Si contiene "TAC" y abarca tres o más regiones anatómicas

**IMPORTANTE**: "Abdomen y pelvis" cuenta como UNA sola región anatómica.

### 4. Cálculo de Horas Trabajadas

Horarios de turno por día:

| Día | Horario de turno |
|-----|------------------|
| Lunes a jueves | 18:00 a 08:00 del día siguiente |
| Viernes | 18:00 a 09:00 del sábado |
| Sábado | 09:00 a 09:00 del domingo |
| Domingo | 09:00 a 08:00 del lunes |

### 5. Tarifas

💸 **Tarifa por horas trabajadas**
- $55,000 CLP por hora de turno

💸 **Tarifa por tipo de examen**
- RX: $5,300
- TAC simple: $42,300
- TAC doble: $84,600
- TAC triple: $126,900

## 🚀 Instalación

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/calculadora-turnos.git
cd calculadora-turnos
```

2. Crear un entorno virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## 💻 Uso

### Iniciar la aplicación

```bash
python run_app.py
```

O usando el script de shell:

```bash
./run_streamlit.sh
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

### Proceso de uso

1. **Configurar fechas de turno**: Ingresa las fechas en las que trabajaste
2. **Cargar archivo**: Sube tu archivo CSV o Excel con los datos
3. **Clasificar exámenes**: El sistema clasificará automáticamente los procedimientos
4. **Calcular honorarios**: Obtén el cálculo detallado de tus ingresos
5. **Generar reportes**: Descarga Excel o genera correo con el resumen

## 📁 Estructura del Proyecto

```
calculadora-turnos/
├── src/
│   ├── core/              # Lógica de negocio
│   │   ├── data_processing.py
│   │   ├── exam_classification.py
│   │   ├── turno_calculator.py
│   │   └── report_generator.py
│   ├── db/                # Gestión de base de datos
│   │   └── sqlite_manager.py
│   └── ui/                # Interfaz de usuario
│       └── streamlit_app.py
├── config/                # Configuración
│   ├── settings.py
│   └── knowledge/         # Archivos JSON de conocimiento
├── data/                  # Directorios de datos
│   ├── raw/
│   ├── processed/
│   └── output/
├── tests/                 # Pruebas
├── docs/                  # Documentación
└── requirements.txt       # Dependencias
```

## 🔧 Configuración

El archivo `config/settings.py` contiene todas las configuraciones del sistema:

- Rutas de directorios
- Tipos de exámenes
- Estimaciones de tiempo
- Configuración de la UI
- Parámetros de procesamiento

## 📊 Exportación de Datos

El sistema genera dos tipos de archivos:

### 📁 Examenes_Filtrados.xlsx
Contiene 4 hojas, una por combinación de tipo y sala:
- RX_SCA, RX_SJ, TAC_SCA, TAC_SJ

### 📁 Examenes_Contabilizados.xlsx
Tabla resumida con columnas esenciales:
- Número de cita
- Fecha sin hora
- Apellidos
- Nombre
- Nombre del procedimiento
- Sala de adquisición

## 🐛 Solución de Problemas

### Error: "No module named 'src'"
Asegúrate de ejecutar la aplicación desde el directorio raíz del proyecto o usa el script `run_streamlit.sh`

### Error: "UNIQUE constraint failed"
Este error ocurre cuando se intenta registrar un procedimiento duplicado en la base de datos. Es temporal y no afecta el funcionamiento.

### Puerto en uso
Si el puerto 8501 está en uso, puedes especificar otro:
```bash
streamlit run src/ui/streamlit_app.py --server.port 8505
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👥 Contacto

Para preguntas o soporte, por favor contacta al equipo de desarrollo.

---

**Versión**: 1.0.0  
**Última actualización**: Diciembre 2024 