#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Guardián de Arquitectura
------------------------
Este script verifica y mantiene la estructura del proyecto,
evitando la creación desorganizada de archivos y asegurando
que todos los cambios sigan las convenciones establecidas.

IMPORTANTE: Este archivo requiere permisos de administrador para ser modificado.
"""

import os
import sys
import json
import hashlib
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='guardian_arquitectura.log'
)
logger = logging.getLogger('GuardianArquitectura')

# Obtener la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directorios aprobados en la estructura
DIRECTORIOS_APROBADOS = {
    'ui',
    'tests',
    'utils',
    'procesamiento',
    'legacy',
    'experimental',
    'conocimiento',
    'recursos',
    'logs',
    'temp',
    'csv'
}

# Archivos fundamentales que no deben ser modificados sin autorización
ARCHIVOS_PROTEGIDOS = {
    'config.py',
    'calculadora_turnos.py',
    'asistente_phi2.py',
    'phi2_cache.py',
    'aprendizaje_datos_sqlite.py',
    'validacion.py',
    'monitor.py',
    'ESTRUCTURA_PROYECTO.md',
    'GUARDIAN.md',
    'INSTRUCCIONES_GUARDIAN.md',
    'guardian_arquitectura.py',
    'guardian_arquitectura.service',
    'guardian_arquitectura.timer',
    'instalar_guardian.sh',
    'pre-commit'
}

# Extensiones de archivo permitidas
EXTENSIONES_PERMITIDAS = {
    '.py',    # Python scripts
    '.md',    # Markdown documentation
    '.txt',   # Text files
    '.json',  # JSON data
    '.csv',   # CSV data
    '.xlsx',  # Excel files
    '.db',    # SQLite databases
    '.log',   # Log files
    '.sh',    # Shell scripts
    '.yml',   # YAML config
    '.yaml',  # YAML config
    '.toml',  # TOML config
    '.ini',   # INI config
    '.cfg',   # Config files
    '.html',  # HTML files
    '.css',   # CSS files
    '.js',    # JavaScript
    '.png',   # Images
    '.jpg',   # Images
    '.jpeg',  # Images
    '.gif',   # Images
    '.svg',   # Vector images
    '',       # Sin extensión (como Dockerfile)
    '.service' # Archivos de servicio systemd
}

# Patrones de nombre de archivo permitidos para la raíz
PATRONES_RAIZ_PERMITIDOS = [
    # Documentación
    r'^README.*\.md$',
    r'^TIMELINE\.md$',
    r'^.*_PROYECTO\.md$',
    r'^ESTRUCTURA.*\.md$',
    r'^INFORME.*\.md$',
    r'^CLAUDE\.md$',
    r'^.*\.md$',
    r'^HISTORIAL.*\.txt$',
    r'^.*_PHI2\.md$',
    r'^DOCKER\.md$',
    r'^DOCUMENTACION.*\.md$',
    
    # Código y configuración
    r'^.*\.py$',
    r'^config\.py$',
    r'^setup\.py$',
    r'^requirements\.txt$',
    
    # Docker y servicios
    r'^Dockerfile$',
    r'^docker-compose\.yml$',
    r'^docker-entrypoint\.sh$',
    r'^.*\.service$',
    
    # Scripts utilitarios
    r'^instalar.*\.sh$',
    r'^pre-commit$',
    
    # Archivos de log
    r'^.*\.log$'
]

# Estado de la última verificación
ultimo_estado = {
    'timestamp': '',
    'hash_estructura': '',
    'archivos_no_autorizados': [],
    'directorios_no_autorizados': [],
    'modificaciones_protegidas': []
}

class GuardianArquitectura:
    """Clase para verificar y mantener la estructura del proyecto."""
    
    def __init__(self, directorio_base: str = BASE_DIR):
        """Inicializa el guardián con el directorio base del proyecto."""
        self.directorio_base = directorio_base
        self.estado_anterior = self._cargar_estado()
        self.estado_actual = {
            'timestamp': datetime.datetime.now().isoformat(),
            'hash_estructura': '',
            'archivos_no_autorizados': [],
            'directorios_no_autorizados': [],
            'modificaciones_protegidas': []
        }
        
        # Crear archivo de estado si no existe
        if not os.path.exists(os.path.join(BASE_DIR, '.estructura_estado.json')):
            self._guardar_estado()
    
    def _cargar_estado(self) -> Dict:
        """Carga el estado anterior desde el archivo de estado."""
        try:
            estado_path = os.path.join(self.directorio_base, '.estructura_estado.json')
            if os.path.exists(estado_path):
                with open(estado_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error al cargar estado: {e}")
        
        return {
            'timestamp': '',
            'hash_estructura': '',
            'archivos_no_autorizados': [],
            'directorios_no_autorizados': [],
            'modificaciones_protegidas': []
        }
    
    def _guardar_estado(self) -> None:
        """Guarda el estado actual en el archivo de estado."""
        try:
            with open(os.path.join(self.directorio_base, '.estructura_estado.json'), 'w') as f:
                json.dump(self.estado_actual, f, indent=2)
        except Exception as e:
            logger.error(f"Error al guardar estado: {e}")
    
    def _obtener_hash_estructura(self) -> str:
        """Genera un hash único para la estructura actual del proyecto."""
        estructura = []
        
        for dirpath, dirnames, filenames in os.walk(self.directorio_base):
            # Skip hidden directories and __pycache__
            dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != '__pycache__']
            
            ruta_relativa = os.path.relpath(dirpath, self.directorio_base)
            if ruta_relativa == '.':
                ruta_relativa = ''
            
            # Agregar directorio
            estructura.append(f"D:{ruta_relativa}")
            
            # Agregar archivos no ocultos
            for filename in sorted(filenames):
                if not filename.startswith('.') and not filename.endswith('.pyc'):
                    ruta_completa = os.path.join(ruta_relativa, filename)
                    try:
                        m_time = os.path.getmtime(os.path.join(dirpath, filename))
                        estructura.append(f"F:{ruta_completa}:{m_time}")
                    except:
                        estructura.append(f"F:{ruta_completa}:0")
        
        # Generar hash
        estructura_str = "\n".join(estructura)
        return hashlib.sha256(estructura_str.encode()).hexdigest()
    
    def verificar_estructura(self) -> Tuple[bool, Dict]:
        """
        Verifica que la estructura del proyecto siga las convenciones.
        
        Returns:
            Tuple[bool, Dict]: (estructura_correcta, problemas_detectados)
        """
        problemas = {
            'directorios_no_autorizados': [],
            'archivos_no_autorizados': [],
            'archivos_raiz_incorrectos': [],
            'modificaciones_protegidas': []
        }
        
        # Verificar directorios no autorizados
        directorios = [d for d in os.listdir(self.directorio_base) 
                      if os.path.isdir(os.path.join(self.directorio_base, d))
                      and not d.startswith('.')
                      and not d == '__pycache__']
        
        for dir_name in directorios:
            if dir_name not in DIRECTORIOS_APROBADOS:
                problemas['directorios_no_autorizados'].append(dir_name)
        
        # Verificar archivos en la raíz
        import re
        archivos_raiz = [f for f in os.listdir(self.directorio_base) 
                        if os.path.isfile(os.path.join(self.directorio_base, f))
                        and not f.startswith('.')]
        
        for archivo in archivos_raiz:
            # Verificar extensión
            _, extension = os.path.splitext(archivo)
            if extension not in EXTENSIONES_PERMITIDAS:
                problemas['archivos_raiz_incorrectos'].append(f"{archivo} (extensión no permitida)")
                continue
            
            # Verificar patrón de nombre
            if not any(re.match(patron, archivo) for patron in PATRONES_RAIZ_PERMITIDOS):
                problemas['archivos_raiz_incorrectos'].append(f"{archivo} (nombre no conforme)")
        
        # Verificar modificaciones en archivos protegidos
        for archivo_protegido in ARCHIVOS_PROTEGIDOS:
            ruta_completa = os.path.join(self.directorio_base, archivo_protegido)
            if os.path.exists(ruta_completa):
                # Verificar si ha sido modificado desde la última verificación
                try:
                    m_time = os.path.getmtime(ruta_completa)
                    if self.estado_anterior.get('timestamp'):
                        timestamp_anterior = datetime.datetime.fromisoformat(self.estado_anterior['timestamp'])
                        tiempo_modificacion = datetime.datetime.fromtimestamp(m_time)
                        
                        if tiempo_modificacion > timestamp_anterior:
                            problemas['modificaciones_protegidas'].append(archivo_protegido)
                except Exception as e:
                    logger.error(f"Error al verificar modificación de {archivo_protegido}: {e}")
        
        # Actualizar estado
        self.estado_actual['hash_estructura'] = self._obtener_hash_estructura()
        self.estado_actual['directorios_no_autorizados'] = problemas['directorios_no_autorizados']
        self.estado_actual['archivos_no_autorizados'] = problemas['archivos_raiz_incorrectos']
        self.estado_actual['modificaciones_protegidas'] = problemas['modificaciones_protegidas']
        
        # Guardar estado
        self._guardar_estado()
        
        # Determinar si la estructura es correcta
        estructura_correcta = (
            len(problemas['directorios_no_autorizados']) == 0 and
            len(problemas['archivos_raiz_incorrectos']) == 0
        )
        
        return estructura_correcta, problemas
    
    def generar_informe(self) -> str:
        """Genera un informe detallado sobre el estado de la estructura del proyecto."""
        # Verificar estructura
        estructura_correcta, problemas = self.verificar_estructura()
        
        # Construir informe
        ahora = datetime.datetime.now()
        informe = []
        informe.append("# Informe de Estructura del Proyecto")
        informe.append(f"Fecha: {ahora.strftime('%Y-%m-%d %H:%M:%S')}")
        informe.append(f"Timestamp: {ahora.timestamp()}")
        informe.append(f"Hash de estructura: {self.estado_actual['hash_estructura'][:10]}...")
        informe.append("")
        
        if estructura_correcta:
            informe.append("## ✅ Estructura Correcta")
            informe.append("La estructura del proyecto cumple con las convenciones establecidas.")
        else:
            informe.append("## ❌ Problemas Detectados")
            
            if problemas['directorios_no_autorizados']:
                informe.append("\n### Directorios No Autorizados")
                for dir_name in problemas['directorios_no_autorizados']:
                    informe.append(f"- {dir_name}")
            
            if problemas['archivos_raiz_incorrectos']:
                informe.append("\n### Archivos Raíz Incorrectos")
                for archivo in problemas['archivos_raiz_incorrectos']:
                    informe.append(f"- {archivo}")
        
        if problemas['modificaciones_protegidas']:
            informe.append("\n## ⚠️ Modificaciones en Archivos Protegidos")
            informe.append("Los siguientes archivos protegidos han sido modificados:")
            for archivo in problemas['modificaciones_protegidas']:
                informe.append(f"- {archivo}")
        
        informe.append("\n## Directorios Aprobados")
        for directorio in sorted(DIRECTORIOS_APROBADOS):
            informe.append(f"- {directorio}/")
        
        informe.append("\n## Archivos Protegidos")
        for archivo in sorted(ARCHIVOS_PROTEGIDOS):
            informe.append(f"- {archivo}")
            
        # Agregar resumen de estadísticas del proyecto
        informe.append("\n## Estadísticas del Proyecto")
        estadisticas = self.generar_estadisticas()
        for categoria, valor in estadisticas.items():
            informe.append(f"- {categoria}: {valor}")
        
        return "\n".join(informe)
    
    def generar_estadisticas(self) -> Dict[str, int]:
        """Genera estadísticas sobre el proyecto."""
        estadisticas = {
            "Total de archivos": 0,
            "Archivos Python": 0,
            "Archivos de documentación": 0,
            "Directorios": 0
        }
        
        # Contar archivos y directorios
        for dirpath, dirnames, filenames in os.walk(self.directorio_base):
            # Skip hidden directories and __pycache__
            dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != '__pycache__']
            
            # Contar directorios
            estadisticas["Directorios"] += len(dirnames)
            
            # Contar archivos por tipo
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                
                estadisticas["Total de archivos"] += 1
                
                # Contar por extensión
                ext = os.path.splitext(filename)[1].lower()
                if ext == '.py':
                    estadisticas["Archivos Python"] += 1
                elif ext in ['.md', '.txt']:
                    estadisticas["Archivos de documentación"] += 1
        
        # Añadir estadísticas adicionales
        try:
            # Contar líneas de código en archivos Python
            lineas_codigo = 0
            for dirpath, _, filenames in os.walk(self.directorio_base):
                for filename in filenames:
                    if filename.endswith('.py') and not filename.startswith('.'):
                        try:
                            with open(os.path.join(dirpath, filename), 'r', encoding='utf-8') as f:
                                lineas_codigo += sum(1 for _ in f)
                        except:
                            pass
            
            estadisticas["Líneas de código Python"] = lineas_codigo
        except:
            pass
        
        return estadisticas
    
    def crear_gitignore(self) -> None:
        """Crea o actualiza el archivo .gitignore para excluir archivos temporales y logs."""
        gitignore_path = os.path.join(self.directorio_base, '.gitignore')
        
        # Entradas que deben estar en .gitignore
        entradas = [
            "# Archivos generados",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "*.so",
            ".Python",
            "env/",
            "build/",
            "develop-eggs/",
            "dist/",
            "downloads/",
            "eggs/",
            ".eggs/",
            "lib/",
            "lib64/",
            "parts/",
            "sdist/",
            "var/",
            "*.egg-info/",
            ".installed.cfg",
            "*.egg",
            "",
            "# Directorios temporales",
            "temp/",
            "tmp/",
            "",
            "# Logs",
            "logs/",
            "*.log",
            "",
            "# Archivos del sistema",
            ".DS_Store",
            "Thumbs.db",
            "",
            "# Archivos de entorno",
            ".env",
            ".venv",
            "venv/",
            "ENV/",
            "",
            "# Archivos de configuración local",
            "config.local.py",
            "",
            "# Archivos de estado del guardián",
            ".estructura_estado.json",
            "guardian_arquitectura.log"
        ]
        
        # Si el archivo ya existe, leer su contenido y agregar líneas faltantes
        lineas_actuales = []
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                lineas_actuales = [line.strip() for line in f.readlines()]
        
        # Agregar entradas faltantes
        nuevas_entradas = [entrada for entrada in entradas if entrada not in lineas_actuales]
        
        if nuevas_entradas:
            with open(gitignore_path, 'a') as f:
                f.write("\n")
                f.write("\n".join(nuevas_entradas))
                f.write("\n")
                
    def restaurar_estructura(self) -> bool:
        """
        Intenta restaurar la estructura correcta del proyecto.
        
        Returns:
            bool: True si se realizaron cambios, False en caso contrario
        """
        cambios_realizados = False
        
        # Verificar estructura actual
        estructura_correcta, problemas = self.verificar_estructura()
        
        if estructura_correcta:
            return False
        
        # 1. Mover archivos incorrectos a directorios apropiados
        for archivo in problemas.get('archivos_raiz_incorrectos', []):
            # Obtener nombre del archivo (sin la descripción del problema)
            nombre_archivo = archivo.split(' ')[0]
            ruta_completa = os.path.join(self.directorio_base, nombre_archivo)
            
            if os.path.exists(ruta_completa):
                # Determinar el directorio destino según la extensión
                ext = os.path.splitext(nombre_archivo)[1].lower()
                
                if ext == '.py' and not nombre_archivo.startswith('test_'):
                    # Scripts Python no test -> utils
                    destino = os.path.join(self.directorio_base, 'utils', nombre_archivo)
                elif nombre_archivo.startswith('test_'):
                    # Scripts de test -> tests
                    destino = os.path.join(self.directorio_base, 'tests', nombre_archivo)
                elif ext in ['.md', '.txt']:
                    # Documentación -> legacy
                    destino = os.path.join(self.directorio_base, 'legacy', nombre_archivo)
                elif ext == '.log':
                    # Logs -> logs
                    destino = os.path.join(self.directorio_base, 'logs', nombre_archivo)
                else:
                    # Otros -> legacy
                    destino = os.path.join(self.directorio_base, 'legacy', nombre_archivo)
                
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                
                try:
                    # Mover archivo
                    import shutil
                    shutil.move(ruta_completa, destino)
                    logger.info(f"Archivo movido: {nombre_archivo} -> {os.path.relpath(destino, self.directorio_base)}")
                    cambios_realizados = True
                except Exception as e:
                    logger.error(f"Error al mover archivo {nombre_archivo}: {e}")
        
        # 2. Crear directorios aprobados faltantes
        for directorio in DIRECTORIOS_APROBADOS:
            ruta_directorio = os.path.join(self.directorio_base, directorio)
            if not os.path.exists(ruta_directorio):
                try:
                    os.makedirs(ruta_directorio)
                    logger.info(f"Directorio creado: {directorio}/")
                    cambios_realizados = True
                except Exception as e:
                    logger.error(f"Error al crear directorio {directorio}: {e}")
        
        # 3. Mover directorios no autorizados a legacy/
        for directorio in problemas.get('directorios_no_autorizados', []):
            ruta_directorio = os.path.join(self.directorio_base, directorio)
            if os.path.exists(ruta_directorio) and os.path.isdir(ruta_directorio):
                try:
                    # Crear directorio legacy si no existe
                    os.makedirs(os.path.join(self.directorio_base, 'legacy'), exist_ok=True)
                    
                    # Mover directorio a legacy/
                    import shutil
                    destino = os.path.join(self.directorio_base, 'legacy', directorio)
                    shutil.move(ruta_directorio, destino)
                    logger.info(f"Directorio movido: {directorio}/ -> legacy/{directorio}/")
                    cambios_realizados = True
                except Exception as e:
                    logger.error(f"Error al mover directorio {directorio}: {e}")
        
        return cambios_realizados
    
    def verificar_automaticamente(self) -> None:
        """Ejecuta verificación automática y genera reporte."""
        estructura_correcta, problemas = self.verificar_estructura()
        informe = self.generar_informe()
        
        # Guardar informe
        ruta_informe = os.path.join(self.directorio_base, 'INFORME_ESTRUCTURA.md')
        with open(ruta_informe, 'w') as f:
            f.write(informe)
        
        # Crear o actualizar .gitignore
        self.crear_gitignore()
        
        # Informar resultado
        if estructura_correcta:
            logger.info("✅ Estructura correcta. Informe generado en INFORME_ESTRUCTURA.md")
        else:
            logger.warning("❌ Problemas detectados. Informe generado en INFORME_ESTRUCTURA.md")
            for tipo, items in problemas.items():
                if items:
                    logger.warning(f"{tipo}: {', '.join(items)}")

# Ejecutar verificación si es el script principal
if __name__ == "__main__":
    import argparse
    
    # Crear parser de argumentos
    parser = argparse.ArgumentParser(description="Guardián de Arquitectura del Proyecto")
    parser.add_argument('--auto-fix', action='store_true', help='Corregir automáticamente problemas detectados')
    args = parser.parse_args()
    
    print("Guardián de Arquitectura - Verificador de estructura del proyecto")
    print("-" * 60)
    
    guardian = GuardianArquitectura()
    estructura_correcta, problemas = guardian.verificar_estructura()
    
    if estructura_correcta:
        print("✅ La estructura del proyecto es correcta")
    else:
        print("❌ Se han detectado problemas en la estructura:")
        
        if problemas['directorios_no_autorizados']:
            print("\nDirectorios no autorizados:")
            for dir_name in problemas['directorios_no_autorizados']:
                print(f"  - {dir_name}")
        
        if problemas['archivos_raiz_incorrectos']:
            print("\nArchivos incorrectos en la raíz:")
            for archivo in problemas['archivos_raiz_incorrectos']:
                print(f"  - {archivo}")
        
        # Si se especificó --auto-fix, corregir automáticamente
        if args.auto_fix:
            print("\nIntentando corregir problemas automáticamente...")
            cambios = guardian.restaurar_estructura()
            if cambios:
                print("✅ Se realizaron correcciones automáticas.")
                print("Ejecutando nueva verificación...")
                estructura_correcta, problemas = guardian.verificar_estructura()
                if estructura_correcta:
                    print("✅ La estructura ahora es correcta.")
                else:
                    print("⚠️ Algunos problemas no pudieron ser corregidos automáticamente.")
            else:
                print("⚠️ No se pudieron realizar correcciones automáticas.")
        else:
            print("\nPara corregir automáticamente los problemas, ejecute:")
            print("python guardian_arquitectura.py --auto-fix")
    
    if problemas['modificaciones_protegidas']:
        print("\n⚠️  Archivos protegidos modificados:")
        for archivo in problemas['modificaciones_protegidas']:
            print(f"  - {archivo}")
    
    # Generar informe
    informe = guardian.generar_informe()
    ruta_informe = os.path.join(BASE_DIR, 'INFORME_ESTRUCTURA.md')
    
    with open(ruta_informe, 'w') as f:
        f.write(informe)
    
    print(f"\nSe ha guardado un informe detallado en {ruta_informe}")
    
    # Crear o actualizar .gitignore
    guardian.crear_gitignore()
    print("\n.gitignore actualizado")