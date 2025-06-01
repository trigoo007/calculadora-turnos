# Implementación de Calculadora de Turnos con Integración de Contexto en Docker y Cloudflare

Este documento proporciona una guía completa para implementar la aplicación "Calculadora de Turnos con Integración de Contexto" en un entorno Docker y exponerla a Internet a través de Cloudflare.

## Resumen Ejecutivo

La solución implementada permite:

1. Ejecutar la aplicación en contenedores Docker para facilitar el despliegue y mantenimiento
2. Persistir los datos importantes en volúmenes Docker para mantenerlos entre reinicicios
3. Exponer la aplicación a Internet de forma segura mediante túneles Cloudflare
4. Proporcionar una interfaz de administración para la base de datos SQLite

## Arquitectura de la Solución

La implementación consta de los siguientes componentes:

1. **Aplicación Calculadora**: Contenedor principal con la aplicación Streamlit y el sistema de contexto vectorial
2. **SQLite Browser**: Contenedor secundario para administración de la base de datos de conocimiento
3. **Cloudflare Tunnel**: Servicio que proporciona acceso seguro a Internet sin necesidad de abrir puertos
4. **Volúmenes Docker**: Para persistencia de datos entre reinicios

## Componentes Desarrollados

### 1. Dockerfile para Integración de Contexto

Se ha creado un Dockerfile específico (`Dockerfile.contexto`) que incluye:
- Dependencias para el sistema de contexto vectorial
- Configuración para la integración con Cloudflare
- Volúmenes para almacenamiento persistente

### 2. Docker Compose Optimizado

El archivo `docker-compose-contexto.yml` configura:
- Servicios necesarios para la aplicación
- Mapeo de puertos
- Volúmenes para persistencia de datos
- Variables de entorno para configuración
- Healthchecks para monitoreo

### 3. Script de Despliegue

El script `instalar_con_cloudflare.sh` automatiza:
- Instalación de Docker y Docker Compose
- Configuración del entorno
- Integración con Cloudflare Tunnel
- Inicialización de servicios

### 4. Interfaz Streamlit Integrada

Se ha desarrollado una interfaz Streamlit para la integración (`experimental/streamlit_contexto.py`) que incluye:
- Integración con el sistema de contexto vectorial
- Procesamiento de archivos CSV
- Consultas con contexto histórico
- Consultas SQL en lenguaje natural
- Historial de operaciones

## Requisitos del Sistema

### Hardware Recomendado
- CPU: 2+ núcleos
- RAM: 4+ GB
- Almacenamiento: 10+ GB

### Software Necesario
- Sistema operativo Linux (Ubuntu/Debian recomendado)
- Docker 20.10+
- Docker Compose 2.0+
- Cuenta en Cloudflare con un dominio registrado

## Guía de Implementación

### Preparación

1. Asegúrese de tener acceso SSH al servidor Linux
2. Copie todos los archivos del proyecto al servidor
3. Cree un túnel en Cloudflare y obtenga el token de conexión

### Instalación

1. Ejecute el script de instalación con privilegios de administrador:
   ```bash
   sudo ./instalar_con_cloudflare.sh
   ```

2. Durante la instalación, se le pedirá el token de Cloudflare cuando sea necesario

3. Verifique que los servicios estén en ejecución:
   ```bash
   docker-compose -f docker-compose-contexto.yml ps
   ```

### Configuración

La aplicación se configurará automáticamente con los parámetros predeterminados. Si necesita personalizar:

1. Edite las variables de entorno en `docker-compose-contexto.yml`
2. Reinicie los servicios:
   ```bash
   docker-compose -f docker-compose-contexto.yml down
   docker-compose -f docker-compose-contexto.yml up -d
   ```

## Seguridad

Se implementan las siguientes medidas de seguridad:

1. **Cloudflare Tunnel**: Evita exponer puertos directamente a Internet
2. **Contenedores aislados**: Separación de servicios en contenedores
3. **Volúmenes persistentes**: Protección de datos contra fallos del contenedor
4. **Variables de entorno**: Para configuración sensible

## Mantenimiento y Actualización

### Respaldos

Es recomendable programar respaldos periódicos de:
- Directorio `/conocimiento` (base de datos SQLite)
- Directorio `/root/vectorstore` (almacenamiento vectorial)

Ejemplo de script de respaldo:
```bash
#!/bin/bash
BACKUP_DIR="/backups/calculadora-$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR
docker-compose -f docker-compose-contexto.yml down
cp -r /opt/calculadora-turnos/conocimiento $BACKUP_DIR/
docker-compose -f docker-compose-contexto.yml up -d
```

### Actualización

Para actualizar la aplicación:

1. Detener los servicios:
   ```bash
   docker-compose -f docker-compose-contexto.yml down
   ```

2. Actualizar los archivos del proyecto

3. Reconstruir e iniciar los servicios:
   ```bash
   docker-compose -f docker-compose-contexto.yml up -d --build
   ```

## Solución de Problemas

### Verificar Logs

```bash
docker-compose -f docker-compose-contexto.yml logs -f
```

### Reiniciar Servicios

```bash
docker-compose -f docker-compose-contexto.yml restart
```

### Verificar Conexión Cloudflare

La conexión del túnel Cloudflare se puede verificar en el panel de Cloudflare Zero Trust.

## Conclusión

Esta implementación proporciona una solución robusta y segura para desplegar la Calculadora de Turnos con Integración de Contexto en un entorno productivo. El uso de Docker simplifica la gestión del entorno, mientras que Cloudflare proporciona acceso seguro desde Internet sin exponer el servidor directamente.

La arquitectura es escalable y puede adaptarse a futuras necesidades mediante la modificación de los archivos de configuración Docker y la adición de nuevos servicios según sea necesario.