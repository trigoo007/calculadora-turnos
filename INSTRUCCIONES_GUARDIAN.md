# Instrucciones para Instalar y Usar el Guardian de Arquitectura

Este documento proporciona instrucciones paso a paso para instalar y configurar el Guardian de Arquitectura en un nuevo sistema.

## Instalación Básica (Usuarios Desarrolladores)

### 1. Verificar la estructura sin instalar

Puede verificar la estructura del proyecto simplemente ejecutando:

```bash
python guardian_arquitectura.py
```

Esto generará un informe en `INFORME_ESTRUCTURA.md` sin realizar cambios.

### 2. Corregir problemas manualmente

Si encuentra problemas en la estructura, puede corregirlos automáticamente con:

```bash
python guardian_arquitectura.py --auto-fix
```

### 3. Configurar el hook de Git

Para validar la estructura antes de cada commit, configure el hook pre-commit:

```bash
cp pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```

## Instalación Protegida (Administradores)

Para una instalación protegida donde los archivos críticos requieren permisos de administrador:

### 1. Ejecutar el script de instalación

```bash
sudo ./instalar_guardian.sh --dir /ruta/completa/al/proyecto
```

Esto instalará el Guardian en `/opt/calculadora/` con permisos de root.

### 2. Verificar la instalación

```bash
sudo /opt/calculadora/guardian_arquitectura.py
```

### 3. Verificar que el servicio systemd está activo

```bash
sudo systemctl status guardian_arquitectura.timer
```

## Solución de Problemas Comunes

### El hook pre-commit no funciona

Asegúrese de que:
- El archivo `.git/hooks/pre-commit` existe y tiene permisos de ejecución
- La ruta a `guardian_arquitectura.py` en el hook es correcta

### El servicio systemd no se inicia

Verifique:
- Los logs del sistema: `journalctl -u guardian_arquitectura.service`
- Que el archivo service está instalado correctamente: `systemctl status guardian_arquitectura.service`

### Errores de permiso

Si recibe errores como "Permission denied":

```bash
sudo chmod +x /opt/calculadora/guardian_arquitectura.py
sudo chown root:root /opt/calculadora/guardian_arquitectura.py
sudo chmod 700 /opt/calculadora/guardian_arquitectura.py
```

## Para Nuevos Proyectos

Si desea utilizar el Guardian en un nuevo proyecto:

1. Copie `guardian_arquitectura.py` a la raíz del nuevo proyecto
2. Modifique las constantes al inicio del archivo para ajustar:
   - DIRECTORIOS_APROBADOS
   - ARCHIVOS_PROTEGIDOS
   - EXTENSIONES_PERMITIDAS
   - PATRONES_RAIZ_PERMITIDOS
3. Siga los pasos de instalación mencionados anteriormente

## Uso en Entornos CI/CD

Para integrar el Guardian en pipelines CI/CD:

```yml
# Ejemplo para GitHub Actions
name: "Verificar Estructura"
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  verificar-estructura:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Instalar Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Verificar estructura
        run: python guardian_arquitectura.py
```

## Recursos Adicionales

- Consulte [GUARDIAN.md](GUARDIAN.md) para documentación detallada
- Revise el código de `guardian_arquitectura.py` para entender su funcionamiento interno
EOF < /dev/null