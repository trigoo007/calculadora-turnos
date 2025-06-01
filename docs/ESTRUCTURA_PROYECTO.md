# Estructura del Proyecto Calculadora de Turnos en Radiología

Este documento describe la estructura organizada del proyecto después de la refactorización realizada en Mayo 2025.

## Directorio Raíz

Contiene los componentes esenciales del sistema:

- `calculadora_turnos.py`: Clase principal para procesar datos radiológicos.
- `asistente_phi2.py`: Integración con el modelo phi-2 para consultas en lenguaje natural.
- `aprendizaje_datos_sqlite.py`: Sistema de aprendizaje basado en SQLite.
- `config.py`: Configuración centralizada del proyecto.
- `phi2_cache.py`: Sistema de caché para consultas phi-2.
- `validacion.py`: Funciones de validación de datos.
- `monitor.py`: Monitoreo de operaciones.
- `setup.py`: Script de instalación del paquete.

## Directorios Organizados

### /ui
Interfaces de usuario:
- `calculadora_streamlit.py`: Interfaz web principal (versión corregida).
- `asistente_streamlit.py`: Interfaz independiente para el asistente phi-2.

### /tests
Pruebas unitarias y de integración:
- `test_calculadora.py`: Pruebas para calculadora_turnos.py.
- `test_phi2.py`: Pruebas para asistente_phi2.py.
- `test_phi2_cache.py`: Pruebas para el sistema de caché.
- `test_validacion.py`: Pruebas para validación.
- `test_fecha_formato.py`: Pruebas para formato de fechas.
- `test_integracion_sqlite.py`: Pruebas de integración SQLite.
- `test_calculo.py`: Pruebas de cálculo específicas.

### /utils
Utilidades y herramientas:
- `reclasificar_procedimientos.py`: Reclasificación de procedimientos.
- `agregar_tac_triple.py`: Agregar patrones TAC triple.
- `verificar_tac_doble.py`: Verificación de TAC doble.
- `verificar_excel.py`: Verificación de Excel.

### /procesamiento
Scripts de procesamiento consolidados:
- `procesar_turnos.py`: Versión unificada de procesamiento.

### /legacy
Scripts antiguos o reemplazados:
- `calculadora_streamlit.py`: Versión original con problemas.
- `aprendizaje_datos.py`: Versión JSON antigua.
- `procesar_turnos_*.py`: Versiones antiguas de procesamiento.
- `test_phi2_*.py`: Versiones antiguas de pruebas phi-2.
- Varios scripts auxiliares obsoletos.

### /experimental
Scripts en desarrollo:
- `contexto_vectorial.py`: Implementación vectorial.
- `recuperacion_contexto.py`: Sistema de recuperación de contexto.
- `websocket_server.py`: Servidor websocket.
- `streamlit_integration.py`: Integración experimental.
- `demo_sistema_integrado.py`: Demo del sistema integrado.

### /conocimiento
Base de datos y herramientas específicas:
- Base de datos SQLite para el sistema de aprendizaje.
- Archivos JSON con patrones.

### /recursos
Recursos adicionales:
- Documentación.
- Demos.

## Notas sobre la organización

1. Los archivos en el directorio raíz son los componentes fundamentales del sistema.
2. Cada directorio agrupa archivos con propósito similar para facilitar el mantenimiento.
3. La carpeta `legacy` contiene versiones antiguas que se mantienen como referencia.
4. La carpeta `experimental` contiene desarrollos en progreso que aún no están listos para producción.

Para iniciar la aplicación, ejecute:
```bash
# Versión web
streamlit run ui/calculadora_streamlit.py

# Asistente phi-2 independiente
streamlit run ui/asistente_streamlit.py
```