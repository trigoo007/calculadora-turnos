# Guía de Instalación - Calculadora de Turnos en Radiología

Esta guía le ayudará a instalar y ejecutar la Calculadora de Turnos en Radiología versión 0.8.1.

## Requisitos Previos

- Docker (versión 19.03.0 o superior)
- Docker Compose (versión 1.25.0 o superior)

## Instalación Rápida

Para instalar y ejecutar la aplicación, simplemente ejecute el script de instalación:

```bash
bash instalar_y_ejecutar.sh
```

Este script:
1. Verificará que Docker y Docker Compose estén instalados
2. Creará los directorios necesarios
3. Construirá la imagen Docker
4. Detendrá cualquier instancia previa
5. Le preguntará si desea ejecutar la aplicación inmediatamente

## Acceso a la Aplicación

Una vez que la aplicación esté en ejecución, puede acceder a ella en:

- **Calculadora de Turnos**: http://localhost:8501
- **Gestor SQLite** (para ver la base de datos): http://localhost:8503

## Características Principales

- Interfaz simplificada y más estable
- Asistente básico integrado para consultas sobre los datos
- Visualización mejorada de TAC dobles y triples
- Estimación automática de fechas de turno
- Generación de reportes económicos

## Detener la Aplicación

Para detener la aplicación, ejecute:

```bash
docker-compose down
```

## Solución de Problemas

Si encuentra algún problema:

1. Verifique que los puertos 8501 y 8503 no estén en uso por otras aplicaciones
2. Intente reiniciar Docker
3. Ejecute el script de instalación nuevamente

## Estructura de Directorios

- `csv/`: Archivos CSV de entrada y salida
- `conocimiento/`: Base de datos SQLite con patrones aprendidos
- `logs/`: Registros de la aplicación
- `ui/`: Interfaces de usuario