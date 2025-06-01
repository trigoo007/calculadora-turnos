#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de caché para consultas phi-2
------------------------------------
Implementa un sistema de caché para evitar consultas repetidas al modelo phi-2,
mejorando el rendimiento y reduciendo la carga del modelo.
"""

import os
import json
import time
import sqlite3
import hashlib
from typing import Dict, Any, Optional, Tuple

# Importar configuración
import config

# Obtener logger
logger = config.obtener_logger(__name__)

# Ruta a la base de datos de caché
CACHE_DB = os.path.join(config.TEMP_DIR, "phi2_cache.db")

class CachePhi2:
    """Clase para gestionar el caché de consultas phi-2."""
    
    def __init__(self, tiempo_expiracion: int = 86400, tamano_maximo: int = 1000):
        """
        Inicializa el sistema de caché.
        
        Args:
            tiempo_expiracion: Tiempo en segundos para que expire una entrada (por defecto: 24 horas)
            tamano_maximo: Número máximo de entradas en el caché antes de eliminar las menos usadas
        """
        self.tiempo_expiracion = tiempo_expiracion
        self.tamano_maximo = tamano_maximo
        self.inicializar_db()
    
    def inicializar_db(self):
        """Inicializa la base de datos de caché."""
        try:
            # Mantener una única conexión para el objeto
            self.conn = sqlite3.connect(CACHE_DB)
            cursor = self.conn.cursor()
            
            # Tabla de caché de consultas
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultas_cache (
                clave TEXT PRIMARY KEY,
                prompt TEXT,
                respuesta TEXT,
                parametros TEXT,
                timestamp REAL,
                tiempo_generacion REAL
            )
            ''')
            
            # Tabla de estadísticas
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_stats (
                tipo TEXT PRIMARY KEY,
                hits INTEGER,
                misses INTEGER,
                ultima_actualizacion REAL
            )
            ''')
            
            # Inicializar estadísticas si no existen
            cursor.execute('''
            INSERT OR IGNORE INTO cache_stats (tipo, hits, misses, ultima_actualizacion)
            VALUES (?, ?, ?, ?)
            ''', ('sql', 0, 0, time.time()))
            
            cursor.execute('''
            INSERT OR IGNORE INTO cache_stats (tipo, hits, misses, ultima_actualizacion)
            VALUES (?, ?, ?, ?)
            ''', ('respuesta', 0, 0, time.time()))
            
            self.conn.commit()
            
            logger.debug("Base de datos de caché inicializada")
        except Exception as e:
            logger.error(f"Error al inicializar la base de datos de caché: {e}")
            if hasattr(self, 'conn'):
                self.conn.close()
                self.conn = None
    
    def generar_clave(self, prompt: str, parametros: Dict[str, Any]) -> str:
        """
        Genera una clave única para una consulta.
        
        Args:
            prompt: Texto del prompt
            parametros: Parámetros de generación
            
        Returns:
            str: Clave única (hash)
        """
        # Combinar prompt y parámetros relevantes
        key_string = prompt
        
        # Añadir parámetros que afectan a la generación
        relevantes = ['temperature', 'top_p', 'top_k', 'num_predict', 'stop']
        for param in relevantes:
            if param in parametros:
                key_string += f"|{param}:{parametros[param]}"
        
        # Generar hash
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def guardar_en_cache(self, prompt: str, respuesta: str, parametros: Dict[str, Any], 
                        tiempo_generacion: float, tipo: str = 'respuesta'):
        """
        Guarda una respuesta en el caché.
        
        Args:
            prompt: Texto del prompt
            respuesta: Respuesta generada
            parametros: Parámetros de generación
            tiempo_generacion: Tiempo que tomó generar la respuesta
            tipo: Tipo de entrada (sql o respuesta)
        """
        try:
            # Generar clave
            clave = self.generar_clave(prompt, parametros)
            
            # Serializar parámetros
            params_json = json.dumps(parametros)
            
            # Verificar que existe una conexión a la BD
            if not hasattr(self, 'conn') or self.conn is None:
                self.inicializar_db()
                
            cursor = self.conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO consultas_cache 
            (clave, prompt, respuesta, parametros, timestamp, tiempo_generacion)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (clave, prompt, respuesta, params_json, time.time(), tiempo_generacion))
            
            # Actualizar estadísticas (miss)
            cursor.execute('''
            UPDATE cache_stats
            SET misses = misses + 1, ultima_actualizacion = ?
            WHERE tipo = ?
            ''', (time.time(), tipo))
            
            self.conn.commit()
            
            logger.debug(f"Entrada guardada en caché: {clave[:8]}... (tipo: {tipo})")
            
            # Verificar y limitar el tamaño del caché después de añadir una entrada
            self.limitar_tamano_cache()
            
        except Exception as e:
            logger.error(f"Error al guardar en caché: {e}")
    
    def buscar_en_cache(self, prompt: str, parametros: Dict[str, Any], 
                      tipo: str = 'respuesta') -> Tuple[bool, Optional[str], float]:
        """
        Busca una respuesta en el caché.
        
        Args:
            prompt: Texto del prompt
            parametros: Parámetros de generación
            tipo: Tipo de entrada (sql o respuesta)
            
        Returns:
            Tuple[bool, Optional[str], float]: 
                (encontrado, respuesta, tiempo_generacion)
        """
        try:
            # Generar clave
            clave = self.generar_clave(prompt, parametros)
            
            # Verificar que existe una conexión a la BD
            if not hasattr(self, 'conn') or self.conn is None:
                self.inicializar_db()
                
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT respuesta, timestamp, tiempo_generacion
            FROM consultas_cache
            WHERE clave = ?
            ''', (clave,))
            
            resultado = cursor.fetchone()
            
            if resultado:
                respuesta, timestamp, tiempo_generacion = resultado
                ahora = time.time()
                
                # Verificar si la entrada ha expirado
                if ahora - timestamp > self.tiempo_expiracion:
                    # Entrada expirada, eliminarla
                    cursor.execute('DELETE FROM consultas_cache WHERE clave = ?', (clave,))
                    
                    # Actualizar estadísticas (miss)
                    cursor.execute('''
                    UPDATE cache_stats
                    SET misses = misses + 1, ultima_actualizacion = ?
                    WHERE tipo = ?
                    ''', (ahora, tipo))
                    
                    self.conn.commit()
                    
                    logger.debug(f"Entrada de caché expirada: {clave[:8]}...")
                    return False, None, 0
                
                # Actualizar estadísticas (hit)
                cursor.execute('''
                UPDATE cache_stats
                SET hits = hits + 1, ultima_actualizacion = ?
                WHERE tipo = ?
                ''', (ahora, tipo))
                
                # Actualizar el timestamp para mantener la entrada fresca (LRU)
                cursor.execute('''
                UPDATE consultas_cache
                SET timestamp = ?
                WHERE clave = ?
                ''', (ahora, clave))
                
                self.conn.commit()
                
                logger.debug(f"Caché hit: {clave[:8]}... (tipo: {tipo})")
                return True, respuesta, tiempo_generacion
            
            logger.debug(f"Caché miss: {clave[:8]}... (tipo: {tipo})")
            return False, None, 0
            
        except Exception as e:
            logger.error(f"Error al buscar en caché: {e}")
            return False, None, 0
    
    def limpiar_cache_expirado(self):
        """Elimina entradas de caché expiradas."""
        try:
            # Verificar que existe una conexión a la BD
            if not hasattr(self, 'conn') or self.conn is None:
                self.inicializar_db()
                
            cursor = self.conn.cursor()
            
            # Tiempo límite
            limite = time.time() - self.tiempo_expiracion
            
            # Eliminar entradas expiradas
            cursor.execute('DELETE FROM consultas_cache WHERE timestamp < ?', (limite,))
            
            eliminadas = cursor.rowcount
            self.conn.commit()
            
            logger.info(f"Se eliminaron {eliminadas} entradas de caché expiradas")
            return eliminadas
        except Exception as e:
            logger.error(f"Error al limpiar caché expirado: {e}")
            return 0
    
    def vaciar_cache(self):
        """Elimina todas las entradas de caché."""
        try:
            # Verificar que existe una conexión a la BD
            if not hasattr(self, 'conn') or self.conn is None:
                self.inicializar_db()
                
            cursor = self.conn.cursor()
            
            # Eliminar todas las entradas
            cursor.execute('DELETE FROM consultas_cache')
            
            eliminadas = cursor.rowcount
            
            # Reiniciar estadísticas
            cursor.execute('''
            UPDATE cache_stats
            SET hits = 0, misses = 0, ultima_actualizacion = ?
            ''', (time.time(),))
            
            self.conn.commit()
            
            logger.info(f"Se vaciaron todas las entradas de caché ({eliminadas} eliminadas)")
            return eliminadas
        except Exception as e:
            logger.error(f"Error al vaciar caché: {e}")
            return 0
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de uso del caché.
        
        Returns:
            Dict[str, Any]: Estadísticas de uso
        """
        try:
            # Verificar que existe una conexión a la BD
            if not hasattr(self, 'conn') or self.conn is None:
                self.inicializar_db()
                
            cursor = self.conn.cursor()
            
            # Obtener estadísticas
            cursor.execute('SELECT tipo, hits, misses, ultima_actualizacion FROM cache_stats')
            resultados = cursor.fetchall()
            
            # Contar entradas actuales
            cursor.execute('SELECT COUNT(*) FROM consultas_cache')
            total_entradas = cursor.fetchone()[0]
            
            # Construir diccionario de estadísticas
            stats = {
                "total_entradas": total_entradas,
                "tipos": {}
            }
            
            for tipo, hits, misses, ultima_actualizacion in resultados:
                total = hits + misses
                hit_rate = hits / total if total > 0 else 0
                
                stats["tipos"][tipo] = {
                    "hits": hits,
                    "misses": misses,
                    "total": total,
                    "hit_rate": hit_rate,
                    "ultima_actualizacion": ultima_actualizacion
                }
            
            return stats
        except Exception as e:
            logger.error(f"Error al obtener estadísticas de caché: {e}")
            return {"error": str(e)}

    def limitar_tamano_cache(self):
        """
        Limita el tamaño del caché eliminando las entradas menos recientemente usadas (LRU).
        Se ejecuta después de añadir nuevas entradas si el tamaño del caché excede el tamaño máximo.
        """
        try:
            # Verificar que existe una conexión a la BD
            if not hasattr(self, 'conn') or self.conn is None:
                self.inicializar_db()
                
            cursor = self.conn.cursor()
            
            # Contar entradas
            cursor.execute('SELECT COUNT(*) FROM consultas_cache')
            total_entradas = cursor.fetchone()[0]
            
            # Si excede el tamaño máximo, eliminar las menos recientemente usadas
            if total_entradas > self.tamano_maximo:
                entradas_a_eliminar = total_entradas - self.tamano_maximo
                
                # Obtener las entradas más antiguas por timestamp (LRU)
                cursor.execute('''
                DELETE FROM consultas_cache
                WHERE clave IN (
                    SELECT clave FROM consultas_cache
                    ORDER BY timestamp ASC
                    LIMIT ?
                )
                ''', (entradas_a_eliminar,))
                
                eliminadas = cursor.rowcount
                self.conn.commit()
                
                logger.info(f"Se eliminaron {eliminadas} entradas LRU del caché para mantener el límite de tamaño")
                return eliminadas
            
            return 0
        except Exception as e:
            logger.error(f"Error al limitar tamaño del caché: {e}")
            return 0
    
    # Agregar un método para cerrar la conexión
    def cerrar_conexion(self):
        """
        Cierra la conexión a la base de datos.
        """
        if hasattr(self, 'conn') and self.conn is not None:
            try:
                self.conn.close()
                self.conn = None
                logger.debug("Conexión a la base de datos de caché cerrada")
            except Exception as e:
                logger.error(f"Error al cerrar la conexión a la base de datos: {e}")
    
    # Método para limpieza al finalizar el programa
    def __del__(self):
        """Destructor para asegurar que se cierra la conexión."""
        self.cerrar_conexion()

# Instancia global de caché
_cache_instance = None

def obtener_cache() -> CachePhi2:
    """
    Obtiene la instancia global de caché.
    
    Returns:
        CachePhi2: Instancia de caché
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CachePhi2()
    return _cache_instance

# Función principal para pruebas
def main():
    """Función principal para pruebas."""
    print("Sistema de caché para consultas phi-2")
    print("---------------------------------")
    
    # Crear instancia
    cache = obtener_cache()
    
    # Simular algunas consultas
    prompt1 = "¿Cuántos exámenes hay de cada tipo?"
    parametros1 = {
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 40
    }
    
    prompt2 = "¿Cuántos TAC dobles hay?"
    parametros2 = {
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 40
    }
    
    # Buscar en caché (probablemente miss en la primera ejecución)
    encontrado1, respuesta1, tiempo1 = cache.buscar_en_cache(prompt1, parametros1, 'sql')
    print(f"Consulta 1 - Encontrado: {encontrado1}")
    
    if not encontrado1:
        # Simular generación
        tiempo_generacion = 0.5
        respuesta_generada = "SELECT tipo, COUNT(*) as cantidad FROM examenes GROUP BY tipo"
        
        # Guardar en caché
        cache.guardar_en_cache(prompt1, respuesta_generada, parametros1, tiempo_generacion, 'sql')
        print(f"Consulta 1 - Guardada en caché: {respuesta_generada}")
    
    # Segunda búsqueda (debería ser hit)
    encontrado1_2, respuesta1_2, tiempo1_2 = cache.buscar_en_cache(prompt1, parametros1, 'sql')
    print(f"Consulta 1 (repetida) - Encontrado: {encontrado1_2}")
    if encontrado1_2:
        print(f"Consulta 1 (repetida) - Respuesta: {respuesta1_2}")
        print(f"Consulta 1 (repetida) - Tiempo original de generación: {tiempo1_2:.4f}s")
    
    # Segunda consulta
    encontrado2, respuesta2, tiempo2 = cache.buscar_en_cache(prompt2, parametros2, 'sql')
    print(f"Consulta 2 - Encontrado: {encontrado2}")
    
    if not encontrado2:
        # Simular generación
        tiempo_generacion = 0.7
        respuesta_generada = "SELECT COUNT(*) as cantidad FROM examenes WHERE \"TAC doble\" = TRUE"
        
        # Guardar en caché
        cache.guardar_en_cache(prompt2, respuesta_generada, parametros2, tiempo_generacion, 'sql')
        print(f"Consulta 2 - Guardada en caché: {respuesta_generada}")
    
    # Estadísticas
    print("\nEstadísticas de caché:")
    stats = cache.obtener_estadisticas()
    
    print(f"Total de entradas: {stats['total_entradas']}")
    for tipo, datos in stats["tipos"].items():
        hit_rate_pct = datos["hit_rate"] * 100
        print(f"Tipo {tipo}: {datos['hits']} hits, {datos['misses']} misses, {hit_rate_pct:.2f}% hit rate")
    
    # Limpiar caché expirado
    print("\nLimpiando caché expirado...")
    eliminadas = cache.limpiar_cache_expirado()
    print(f"Entradas eliminadas: {eliminadas}")

if __name__ == "__main__":
    main()