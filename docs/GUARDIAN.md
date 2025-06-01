# Guardian de Arquitectura

Este componente asegura que la estructura del proyecto se mantenga consistente según las convenciones definidas, protegiendo contra modificaciones no autorizadas de archivos críticos y automatizando la corrección de la estructura.

## Características

- Verificación automática de la estructura del proyecto
- Detección de archivos y directorios no autorizados
- Notificación de modificaciones a archivos protegidos
- Capacidad de auto-corrección con el parámetro `--auto-fix`
- Generación de informes detallados
- Estadísticas de proyecto (archivos, líneas de código)
- Integración con systemd para ejecución periódica
- Hook pre-commit para Git

## Uso Básico

### Verificar la estructura

```bash
python guardian_arquitectura.py
```

El comando anterior verificará la estructura del proyecto y generará un informe detallado en `INFORME_ESTRUCTURA.md`.

### Corregir automáticamente la estructura

```bash
python guardian_arquitectura.py --auto-fix
```

Esto detectará problemas y realizará las siguientes correcciones:
- Mover archivos incorrectos al directorio apropiado
- Crear directorios aprobados faltantes
- Mover directorios no autorizados a legacy/

## Instalación con Protección a Nivel Sistema

Para instalar el Guardian con protección a nivel sistema (requiere permisos de administrador):

```bash
sudo ./instalar_guardian.sh --dir /ruta/al/proyecto/calculadora
```

Esta instalación:
1. Copia los archivos del proyecto a `/opt/calculadora/`
2. Cambia la propiedad de archivos críticos a root
3. Establece permisos restrictivos (700) en archivos protegidos
4. Instala servicios systemd para ejecución periódica
5. Configura un hook pre-commit de Git

## Integración con Git

El Guardian puede integrarse con Git para verificar la estructura antes de cada commit:

```bash
cp pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```

## Servicios Systemd

Se proporcionan dos archivos para la integración con systemd:

1. `guardian_arquitectura.service` - Define el servicio
2. `guardian_arquitectura.timer` - Programa la ejecución periódica (cada hora)

Para instalar y activar manualmente:

```bash
sudo cp guardian_arquitectura.service /etc/systemd/system/
sudo cp guardian_arquitectura.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable guardian_arquitectura.timer
sudo systemctl start guardian_arquitectura.timer
```

## Configuración

El Guardian define las siguientes convenciones:

- **Directorios aprobados**: ui, tests, utils, procesamiento, legacy, experimental, conocimiento, recursos, logs, temp, csv
- **Archivos protegidos**: Componentes críticos que requieren autorización para modificar
- **Extensiones permitidas**: Tipos de archivo permitidos en el proyecto
- **Patrones de nombre**: Convenciones de nomenclatura para archivos en la raíz

Estas configuraciones se definen en constantes al inicio del archivo `guardian_arquitectura.py`.

## Informes

Cada verificación genera un informe detallado en `INFORME_ESTRUCTURA.md` que incluye:

- Estado general de la estructura
- Problemas detectados
- Modificaciones en archivos protegidos
- Lista de directorios aprobados y archivos protegidos
- Estadísticas del proyecto
EOF < /dev/null