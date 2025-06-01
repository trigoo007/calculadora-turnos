"""
Módulo de gestión de base de datos SQLite para la Calculadora de Turnos.

Este módulo maneja todas las operaciones de base de datos incluyendo
el almacenamiento de procedimientos, salas, patrones y estadísticas.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime
import json
from contextlib import contextmanager
import time

from config.settings import DATABASE_CONFIG, DATA_DIR

logger = logging.getLogger(__name__)


class SQLiteManager:
    """Gestor principal de la base de datos SQLite."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Inicializa el gestor de base de datos.
        
        Args:
            db_path: Ruta opcional a la base de datos
        """
        self.db_path = db_path or Path(DATABASE_CONFIG["path"])
        self.timeout = DATABASE_CONFIG["timeout"]
        self.check_same_thread = DATABASE_CONFIG["check_same_thread"]
        
        # Asegurar que el directorio existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar la base de datos
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager para obtener una conexión a la base de datos."""
        conn = None
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=self.timeout,
                check_same_thread=self.check_same_thread
            )
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error en la base de datos: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _init_database(self):
        """Inicializa las tablas de la base de datos."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de procedimientos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS procedimientos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    codigo TEXT UNIQUE NOT NULL,
                    tipo TEXT NOT NULL,
                    subtipo TEXT,
                    complejidad INTEGER DEFAULT 1,
                    tiempo_estimado INTEGER DEFAULT 20,
                    conteo INTEGER DEFAULT 0,
                    fecha_creacion TEXT NOT NULL,
                    fecha_actualizacion TEXT
                )
            ''')
            
            # Tabla de salas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS salas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    centro TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    subtipo TEXT,
                    capacidad INTEGER DEFAULT 1,
                    conteo INTEGER DEFAULT 0,
                    fecha_creacion TEXT NOT NULL,
                    fecha_actualizacion TEXT
                )
            ''')
            
            # Tabla de patrones de clasificación
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patrones_clasificacion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patron TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    subtipo TEXT,
                    descripcion TEXT,
                    fecha_creacion TEXT NOT NULL,
                    UNIQUE(patron, tipo)
                )
            ''')
            
            # Tabla de histórico de exámenes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historico_examenes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    hora TEXT,
                    paciente TEXT,
                    procedimiento_id INTEGER,
                    sala_id INTEGER,
                    tipo_examen TEXT,
                    es_tac_doble BOOLEAN DEFAULT 0,
                    es_tac_triple BOOLEAN DEFAULT 0,
                    turno_asignado TEXT,
                    fecha_procesamiento TEXT NOT NULL,
                    FOREIGN KEY (procedimiento_id) REFERENCES procedimientos(id),
                    FOREIGN KEY (sala_id) REFERENCES salas(id)
                )
            ''')
            
            # Tabla de configuración
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configuracion (
                    clave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL,
                    tipo TEXT DEFAULT 'string',
                    fecha_actualizacion TEXT NOT NULL
                )
            ''')
            
            # Crear índices para búsquedas rápidas
            indices = [
                'CREATE INDEX IF NOT EXISTS idx_procedimientos_tipo ON procedimientos(tipo)',
                'CREATE INDEX IF NOT EXISTS idx_procedimientos_subtipo ON procedimientos(subtipo)',
                'CREATE INDEX IF NOT EXISTS idx_salas_centro ON salas(centro)',
                'CREATE INDEX IF NOT EXISTS idx_salas_tipo ON salas(tipo)',
                'CREATE INDEX IF NOT EXISTS idx_patrones_tipo ON patrones_clasificacion(tipo)',
                'CREATE INDEX IF NOT EXISTS idx_historico_fecha ON historico_examenes(fecha)',
                'CREATE INDEX IF NOT EXISTS idx_historico_turno ON historico_examenes(turno_asignado)'
            ]
            
            for indice in indices:
                cursor.execute(indice)
            
            logger.info("Base de datos inicializada correctamente")
    
    def registrar_procedimiento(self, nombre: str, tipo: str, subtipo: str = None,
                              codigo: str = None, complejidad: int = 1,
                              tiempo_estimado: int = 20) -> int:
        """
        Registra un nuevo procedimiento o actualiza uno existente.
        
        Args:
            nombre: Nombre del procedimiento
            tipo: Tipo de procedimiento (TAC, RX, etc.)
            subtipo: Subtipo (DOBLE, TRIPLE, etc.)
            codigo: Código único del procedimiento
            complejidad: Nivel de complejidad (1-5)
            tiempo_estimado: Tiempo estimado en minutos
            
        Returns:
            ID del procedimiento
        """
        fecha_actual = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si ya existe
            cursor.execute(
                'SELECT id, conteo FROM procedimientos WHERE nombre = ?',
                (nombre,)
            )
            resultado = cursor.fetchone()
            
            if resultado:
                # Actualizar existente
                proc_id = resultado['id']
                nuevo_conteo = resultado['conteo'] + 1
                
                cursor.execute('''
                    UPDATE procedimientos 
                    SET conteo = ?, fecha_actualizacion = ?, subtipo = ?
                    WHERE id = ?
                ''', (nuevo_conteo, fecha_actual, subtipo, proc_id))
            else:
                # Insertar nuevo
                if not codigo:
                    codigo = self._generar_codigo_procedimiento(nombre)
                
                cursor.execute('''
                    INSERT INTO procedimientos 
                    (nombre, codigo, tipo, subtipo, complejidad, tiempo_estimado, 
                     conteo, fecha_creacion)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                ''', (nombre, codigo, tipo, subtipo, complejidad, 
                     tiempo_estimado, fecha_actual))
                
                proc_id = cursor.lastrowid
            
            return proc_id
    
    def registrar_sala(self, nombre: str, centro: str, tipo: str,
                      subtipo: str = None, capacidad: int = 1) -> int:
        """
        Registra una nueva sala o actualiza una existente.
        
        Args:
            nombre: Nombre de la sala
            centro: Centro al que pertenece (SCA, SJ, etc.)
            tipo: Tipo de sala
            subtipo: Subtipo de sala
            capacidad: Capacidad de la sala
            
        Returns:
            ID de la sala
        """
        fecha_actual = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si ya existe
            cursor.execute(
                'SELECT id, conteo FROM salas WHERE nombre = ?',
                (nombre,)
            )
            resultado = cursor.fetchone()
            
            if resultado:
                # Actualizar existente
                sala_id = resultado['id']
                nuevo_conteo = resultado['conteo'] + 1
                
                cursor.execute('''
                    UPDATE salas 
                    SET conteo = ?, fecha_actualizacion = ?
                    WHERE id = ?
                ''', (nuevo_conteo, fecha_actual, sala_id))
            else:
                # Insertar nueva
                cursor.execute('''
                    INSERT INTO salas 
                    (nombre, centro, tipo, subtipo, capacidad, conteo, fecha_creacion)
                    VALUES (?, ?, ?, ?, ?, 1, ?)
                ''', (nombre, centro, tipo, subtipo, capacidad, fecha_actual))
                
                sala_id = cursor.lastrowid
            
            return sala_id
    
    def registrar_patron(self, patron: str, tipo: str, 
                        subtipo: str = None, descripcion: str = None):
        """
        Registra un nuevo patrón de clasificación.
        
        Args:
            patron: Texto del patrón
            tipo: Tipo de patrón (tac_doble, tac_triple, etc.)
            subtipo: Subtipo opcional
            descripcion: Descripción del patrón
        """
        fecha_actual = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO patrones_clasificacion 
                (patron, tipo, subtipo, descripcion, fecha_creacion)
                VALUES (?, ?, ?, ?, ?)
            ''', (patron, tipo, subtipo, descripcion, fecha_actual))
    
    def obtener_patrones(self, tipo: str) -> List[str]:
        """
        Obtiene todos los patrones de un tipo específico.
        
        Args:
            tipo: Tipo de patrón a buscar
            
        Returns:
            Lista de patrones
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT patron FROM patrones_clasificacion WHERE tipo = ?',
                (tipo,)
            )
            
            return [row['patron'] for row in cursor.fetchall()]
    
    def buscar_procedimiento(self, nombre: str) -> Optional[Dict[str, Any]]:
        """
        Busca un procedimiento por nombre.
        
        Args:
            nombre: Nombre del procedimiento
            
        Returns:
            Diccionario con los datos del procedimiento o None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM procedimientos WHERE nombre = ?',
                (nombre,)
            )
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def buscar_sala(self, nombre: str) -> Optional[Dict[str, Any]]:
        """
        Busca una sala por nombre.
        
        Args:
            nombre: Nombre de la sala
            
        Returns:
            Diccionario con los datos de la sala o None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM salas WHERE nombre = ?',
                (nombre,)
            )
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de la base de datos.
        
        Returns:
            Diccionario con estadísticas
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total de procedimientos
            cursor.execute('SELECT COUNT(*) as total FROM procedimientos')
            total_procedimientos = cursor.fetchone()['total']
            
            # Procedimientos por tipo
            cursor.execute('''
                SELECT tipo, COUNT(*) as cantidad 
                FROM procedimientos 
                GROUP BY tipo
            ''')
            procedimientos_por_tipo = {
                row['tipo']: row['cantidad'] for row in cursor.fetchall()
            }
            
            # TAC por subtipo
            cursor.execute('''
                SELECT subtipo, COUNT(*) as cantidad 
                FROM procedimientos 
                WHERE tipo = 'TAC' 
                GROUP BY subtipo
            ''')
            tac_por_subtipo = {
                row['subtipo']: row['cantidad'] for row in cursor.fetchall()
            }
            
            # Total de salas
            cursor.execute('SELECT COUNT(*) as total FROM salas')
            total_salas = cursor.fetchone()['total']
            
            # Salas por centro
            cursor.execute('''
                SELECT centro, COUNT(*) as cantidad 
                FROM salas 
                GROUP BY centro
            ''')
            salas_por_centro = {
                row['centro']: row['cantidad'] for row in cursor.fetchall()
            }
            
            # Total de patrones
            cursor.execute('''
                SELECT tipo, COUNT(*) as cantidad 
                FROM patrones_clasificacion 
                GROUP BY tipo
            ''')
            patrones_por_tipo = {
                row['tipo']: row['cantidad'] for row in cursor.fetchall()
            }
            
            # Total de exámenes históricos
            cursor.execute('SELECT COUNT(*) as total FROM historico_examenes')
            total_historico = cursor.fetchone()['total']
            
            return {
                'procedimientos': {
                    'total': total_procedimientos,
                    'por_tipo': procedimientos_por_tipo,
                    'tac_por_subtipo': tac_por_subtipo
                },
                'salas': {
                    'total': total_salas,
                    'por_centro': salas_por_centro
                },
                'patrones': patrones_por_tipo,
                'historico_examenes': total_historico
            }
    
    def guardar_configuracion(self, clave: str, valor: Any, tipo: str = 'string'):
        """
        Guarda un valor de configuración.
        
        Args:
            clave: Clave de configuración
            valor: Valor a guardar
            tipo: Tipo de dato (string, int, float, json)
        """
        fecha_actual = datetime.now().isoformat()
        
        # Convertir valor según tipo
        if tipo == 'json':
            valor_str = json.dumps(valor)
        else:
            valor_str = str(valor)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO configuracion 
                (clave, valor, tipo, fecha_actualizacion)
                VALUES (?, ?, ?, ?)
            ''', (clave, valor_str, tipo, fecha_actual))
    
    def obtener_configuracion(self, clave: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.
        
        Args:
            clave: Clave de configuración
            default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT valor, tipo FROM configuracion WHERE clave = ?',
                (clave,)
            )
            
            row = cursor.fetchone()
            if not row:
                return default
            
            valor = row['valor']
            tipo = row['tipo']
            
            # Convertir según tipo
            if tipo == 'int':
                return int(valor)
            elif tipo == 'float':
                return float(valor)
            elif tipo == 'json':
                return json.loads(valor)
            else:
                return valor
    
    def _generar_codigo_procedimiento(self, nombre: str) -> str:
        """Genera un código único para un procedimiento."""
        import re
        import time
        
        # Limpiar nombre
        nombre_limpio = re.sub(r'[^\w\s]', '', nombre.upper())
        palabras = nombre_limpio.split()
        
        # Generar código base
        if len(palabras) >= 2:
            codigo_base = ''.join([p[:2] for p in palabras[:3]])
        else:
            codigo_base = palabras[0][:5] if palabras else 'PROC'
        
        # Agregar timestamp para garantizar unicidad
        timestamp = str(int(time.time() * 1000))[-6:]  # Últimos 6 dígitos del timestamp
        codigo = f"{codigo_base}_{timestamp}"
        
        return codigo
    
    def crear_backup(self, backup_path: Optional[Path] = None) -> Path:
        """
        Crea un backup de la base de datos.
        
        Args:
            backup_path: Ruta opcional para el backup
            
        Returns:
            Path al archivo de backup
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_path.parent / f"backup_{timestamp}.db"
        
        with self.get_connection() as conn:
            # Crear conexión al backup
            backup_conn = sqlite3.connect(str(backup_path))
            
            # Copiar base de datos
            conn.backup(backup_conn)
            
            backup_conn.close()
        
        logger.info(f"Backup creado: {backup_path}")
        return backup_path


# Instancia global del gestor
_db_manager = None


def get_db_manager() -> SQLiteManager:
    """Obtiene la instancia global del gestor de base de datos."""
    global _db_manager
    if _db_manager is None:
        _db_manager = SQLiteManager()
    return _db_manager


# Funciones de utilidad para compatibilidad
def registrar_procedimiento(nombre: str, tipo: str, subtipo: str = None) -> int:
    """Función de compatibilidad para registrar un procedimiento."""
    return get_db_manager().registrar_procedimiento(nombre, tipo, subtipo)


def buscar_procedimiento(nombre: str) -> Optional[Dict[str, Any]]:
    """Función de compatibilidad para buscar un procedimiento."""
    return get_db_manager().buscar_procedimiento(nombre) 