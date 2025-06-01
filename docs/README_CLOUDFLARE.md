# Desplegando la Calculadora de Turnos en Internet con Cloudflare

## COMUNICACIÓN RESTABLECIDA (12 de mayo de 2025)

✅ **La comunicación entre Gemini y Claude ha sido restablecida.**

Gemini ha respondido en el archivo `COLABORACION_GEMINI_CLAUDE.md`, que ahora funciona como canal principal de coordinación para este proyecto.

El resumen actual del estado del proyecto y el plan de trabajo se encuentran documentados en ese archivo. La próxima reunión de coordinación está programada para el 13 de mayo.

---

Este documento explica cómo desplegar la aplicación en un servidor Linux y exponerla a Internet de manera segura utilizando Cloudflare Tunnels.

## Requisitos

- Servidor Linux (Ubuntu/Debian recomendado)
- Docker y Docker Compose instalados
- Cuenta en Cloudflare
- Dominio registrado en Cloudflare (puede ser un subdominio)

## 1. Preparación del Servidor

### Instalar Docker y Docker Compose

```bash
# Actualizar paquetes
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y ca-certificates curl gnupg lsb-release

# Añadir clave GPG oficial de Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Configurar repositorio
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Añadir usuario al grupo docker (evita usar sudo)
sudo usermod -aG docker $USER
```

Después de estos comandos, es recomendable cerrar sesión y volver a iniciarla para que los cambios en los grupos tengan efecto.

### Clonar el Repositorio

```bash
# Crear directorio para la aplicación
mkdir -p ~/calculadora-turnos
cd ~/calculadora-turnos

# Copiar los archivos necesarios
# (Asumiendo que has copiado los archivos manualmente o con scp/rsync)
```

## 2. Configurar Cloudflare Tunnels

### Crear un Túnel en Cloudflare

1. Inicia sesión en tu panel de [Cloudflare](https://dash.cloudflare.com/)
2. Ve a la sección "Zero Trust" o "Tunnels" (según la interfaz actual)
3. Crea un nuevo túnel con un nombre descriptivo (ej. "calculadora-turnos")
4. Durante la configuración, se te proporcionará un token único. **¡GUÁRDALO!** Lo necesitarás para el archivo docker-compose.

### Configurar el Dominio para el Túnel

1. En la configuración del túnel, añade una "Public Hostname"
2. Selecciona tu dominio (debe estar configurado en Cloudflare)
3. Configura un subdominio (ej. "calculadora.tudominio.com")
4. Como servicio, selecciona "HTTP" y apunta a "localhost:8501"
5. Guarda la configuración

## 3. Desplegar la Aplicación

### Usar el Script de Instalación Automatizada

La forma más sencilla de desplegar la aplicación es utilizando el script de instalación automatizada:

```bash
# Hacer el script ejecutable
chmod +x instalar_con_cloudflare.sh

# Ejecutar el script con privilegios de superusuario
sudo ./instalar_con_cloudflare.sh
```

El script realizará los siguientes pasos:
1. Instalar dependencias necesarias
2. Configurar Docker y Docker Compose si no están instalados
3. Solicitar el token del túnel Cloudflare
4. Configurar respaldos automáticos (opcional)
5. Iniciar los servicios

### Instalación Manual (Alternativa)

Si prefieres hacer la instalación manualmente:

1. Edita el archivo `docker-compose-contexto.yml` y añade el token del túnel Cloudflare:

```bash
nano docker-compose-contexto.yml
```

Busca la sección `environment` del servicio `calculadora` y reemplaza:

```yaml
environment:
  - STREAMLIT_SERVER_PORT=8501
  - STREAMLIT_SERVER_ADDRESS=0.0.0.0
  - CLOUDFLARE_TUNNEL_TOKEN=your_tunnel_token_here  # Reemplaza con tu token
  - ENABLE_AUTHENTICATION=true                      # Habilitar autenticación
  - ADMIN_EMAIL=admin@ejemplo.com                   # Correo para el admin
```

2. Iniciar la aplicación:

```bash
# Construir e iniciar los contenedores
docker-compose -f docker-compose-contexto.yml up -d

# Ver logs para verificar que todo funciona correctamente
docker-compose -f docker-compose-contexto.yml logs -f
```

## 4. Configurar Cloudflare Access (Autenticación)

Para proteger el acceso a la aplicación, especialmente importante dado que maneja datos médicos, es altamente recomendable configurar Cloudflare Access.

### Requisitos para Cloudflare Access

- Plan Cloudflare Zero Trust (tiene una capa gratuita)
- Túnel Cloudflare configurado (pasos anteriores)
- Proveedores de identidad configurados (opcional, pero recomendado)

### Paso 1: Activar Cloudflare Zero Trust

1. En tu panel de Cloudflare, ve a "Zero Trust" > "Overview"
2. Si es la primera vez, sigue los pasos para configurar tu cuenta de Zero Trust
3. Selecciona o configura tu organización y dominio de equipo (ej. "miempresa.cloudflareaccess.com")

### Paso 2: Configurar Proveedores de Identidad (Opcional)

Para una autenticación más robusta, configura al menos un proveedor de identidad:

1. Ve a "Zero Trust" > "Settings" > "Authentication"
2. Haz clic en "Add new" y selecciona el proveedor que desees:
   - One-time PIN (más simple, solo requiere acceso al correo electrónico)
   - Google Workspace
   - Microsoft Azure AD
   - Okta
   - GitHub
   - Y muchos otros

Sigue las instrucciones específicas para cada proveedor.

### Paso 3: Crear una Aplicación en Access

1. Ve a "Zero Trust" > "Access" > "Applications"
2. Haz clic en "Add an application"
3. Selecciona "Self-hosted" como tipo de aplicación
4. Completa la información:
   - Nombre: "Calculadora de Turnos"
   - Dominio: El subdominio que configuraste (ej. "calculadora.tudominio.com")
   - Asegúrate de que "Session duration" sea adecuado (ej. 24 horas)

### Paso 4: Configurar Políticas de Acceso

1. En la misma configuración de aplicación, añade al menos una política:
   - Nombre: "Acceso a Calculadora de Turnos"
   - Action: Allow
   - Configura los criterios de acceso. Opciones recomendadas:
     - Emails: Especifica correos electrónicos autorizados (ej. "usuario@tuempresa.com")
     - Domains: Permite acceso a todos con un dominio de correo específico (ej. "tuempresa.com")
     - Groups: Si tienes grupos configurados en tu proveedor de identidad
     - IP Ranges: Para restringir acceso a rangos IP específicos

2. Puedes añadir múltiples políticas con diferentes criterios

3. Guarda la configuración

### Paso 5: Personalización Adicional (Opcional)

1. Personaliza la página de inicio de sesión:
   - Ve a "Zero Trust" > "Settings" > "Custom Pages"
   - Puedes personalizar el logo, los colores y textos

2. Configura la duración de las sesiones:
   - Ve a "Zero Trust" > "Settings" > "Session Controls"
   - Ajusta según tus necesidades de seguridad

### Probando el Acceso

1. Accede a tu aplicación a través del subdominio configurado
2. Deberías ser redirigido a la página de inicio de sesión de Cloudflare Access
3. Autentica con el método configurado
4. Una vez autenticado, tendrás acceso a la aplicación

## 5. Respaldos Automáticos

### Configuración de Respaldos

Para mayor seguridad, el sistema incluye un mecanismo de respaldo automatizado:

1. El script `backup_automatico.sh` está configurado para:
   - Respaldar la base de datos SQLite
   - Respaldar el almacenamiento vectorial
   - Comprimir y rotar automáticamente los respaldos
   - Mantener un historial de 30 días

2. Puedes ejecutarlo manualmente:
   ```bash
   sudo /opt/calculadora-turnos/backup_automatico.sh
   ```

3. Para configurarlo como tarea programada (si no lo has hecho durante la instalación):
   ```bash
   # Abrir el editor de crontab
   crontab -e
   
   # Añadir la siguiente línea para ejecutarlo diariamente a las 2AM
   0 2 * * * /opt/calculadora-turnos/backup_automatico.sh >> /var/log/calculadora-backup.log 2>&1
   ```

## 6. Mantenimiento y Administración

### Actualizar la Aplicación

```bash
# Detener los contenedores
docker-compose -f docker-compose-contexto.yml down

# Reconstruir e iniciar (si hay cambios en el Dockerfile)
docker-compose -f docker-compose-contexto.yml up -d --build
```

### Monitoreo

```bash
# Ver el estado de los contenedores
docker-compose -f docker-compose-contexto.yml ps

# Ver los logs en tiempo real
docker-compose -f docker-compose-contexto.yml logs -f

# Ver uso de recursos
docker stats
```

## 7. Solución de Problemas

### El túnel no se conecta

1. Verifica que el token de Cloudflare es correcto
2. Comprueba los logs del contenedor: `docker-compose logs -f calculadora`
3. Asegúrate de que el puerto 8501 está expuesto correctamente
4. Verifica el estado del túnel en el panel de Cloudflare

### La aplicación no carga

1. Verifica que el contenedor está en ejecución: `docker-compose ps`
2. Comprueba si hay errores en los logs: `docker-compose logs calculadora`
3. Reinicia el contenedor: `docker-compose restart calculadora`

### Problemas con la autenticación

1. **Para Cloudflare Access:**
   - Verifica en el panel de Cloudflare si hay logs de intentos fallidos de autenticación
   - Asegúrate de que las políticas de acceso están correctamente configuradas
   - Comprueba que el proveedor de identidad funciona correctamente

2. **Para autenticación integrada en Streamlit:**
   - Verifica que `ENABLE_AUTHENTICATION=true` está configurado en el docker-compose
   - Comprueba los logs por errores relacionados con autenticación
   - Si olvidaste la contraseña de admin, puedes reiniciar el archivo usuarios.json

## 8. Consideraciones de Seguridad Adicionales

1. **Actualizaciones regulares:**
   - Mantén actualizados el sistema operativo, Docker y las dependencias
   - Verifica regularmente si hay actualizaciones de seguridad

2. **Firewall:**
   - Configura un firewall (ej. ufw en Ubuntu) y limita los puertos expuestos
   - Solo expón los puertos necesarios (8501 para Streamlit, 22 para SSH)

3. **Cifrado de datos:**
   - Considera cifrar los volúmenes de datos en reposo para mayor seguridad
   - Utiliza LUKS o soluciones similares para cifrado a nivel de disco

4. **Monitoreo de seguridad:**
   - Implementa herramientas de monitoreo de logs (ej. Fail2ban)
   - Considera un sistema de detección de intrusiones (IDS)

5. **Respaldos externos:**
   - Configura respaldos externos fuera del servidor (ej. almacenamiento en la nube)
   - Prueba regularmente la restauración de respaldos