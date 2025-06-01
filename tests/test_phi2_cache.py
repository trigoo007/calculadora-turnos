#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas unitarias para el módulo de caché phi-2.
"""

import os
import sys
import unittest
import time
import tempfile
from unittest.mock import patch, MagicMock

# Asegurar que podemos importar desde el directorio padre
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar módulos a probar
import phi2_cache

class TestPhi2Cache(unittest.TestCase):
    """Pruebas para el sistema de caché de phi-2."""
    
    def setUp(self):
        """Configuración de las pruebas."""
        # Crear un archivo temporal para la base de datos de caché
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, "test_cache.db")
        
        # Parchar la constante CACHE_DB para usar nuestra base de datos temporal
        self.original_cache_db = phi2_cache.CACHE_DB
        phi2_cache.CACHE_DB = self.temp_db
        
        # Crear una instancia de caché con un tiempo de expiración corto para pruebas
        self.cache = phi2_cache.CachePhi2(tiempo_expiracion=1)  # 1 segundo
        
        # Algunos prompts y parámetros de prueba
        self.prompt1 = "¿Cuántos exámenes hay de cada tipo?"
        self.prompt2 = "¿Cuántos TAC dobles hay?"
        
        self.parametros1 = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40
        }
        
        self.parametros2 = {
            "temperature": 0.2,
            "top_p": 0.9,
            "top_k": 30
        }
        
        self.respuesta1 = "SELECT tipo, COUNT(*) as cantidad FROM examenes GROUP BY tipo"
        self.respuesta2 = "SELECT COUNT(*) as cantidad FROM examenes WHERE \"TAC doble\" = TRUE"
    
    def tearDown(self):
        """Limpieza después de las pruebas."""
        # Restaurar la constante CACHE_DB
        phi2_cache.CACHE_DB = self.original_cache_db
        
        # Eliminar el archivo temporal de la base de datos
        if os.path.exists(self.temp_db):
            os.remove(self.temp_db)
        
        # Eliminar el directorio temporal
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_generar_clave(self):
        """Prueba la generación de claves únicas."""
        # Generar clave para prompt1 con parametros1
        clave1 = self.cache.generar_clave(self.prompt1, self.parametros1)
        self.assertIsNotNone(clave1)
        self.assertEqual(len(clave1), 32)  # MD5 tiene 32 caracteres en hexadecimal
        
        # Generar clave para prompt2 con parametros2
        clave2 = self.cache.generar_clave(self.prompt2, self.parametros2)
        self.assertIsNotNone(clave2)
        self.assertEqual(len(clave2), 32)
        
        # Verificar que las claves son diferentes
        self.assertNotEqual(clave1, clave2)
        
        # Verificar que la misma combinación produce la misma clave
        clave1_repetida = self.cache.generar_clave(self.prompt1, self.parametros1)
        self.assertEqual(clave1, clave1_repetida)
    
    def test_guardar_y_buscar_en_cache(self):
        """Prueba guardar y buscar en caché."""
        # Guardar en caché
        self.cache.guardar_en_cache(self.prompt1, self.respuesta1, self.parametros1, 0.5, 'sql')
        
        # Buscar en caché (debería encontrarlo)
        encontrado, respuesta, tiempo = self.cache.buscar_en_cache(self.prompt1, self.parametros1, 'sql')
        self.assertTrue(encontrado)
        self.assertEqual(respuesta, self.respuesta1)
        self.assertEqual(tiempo, 0.5)
        
        # Buscar un prompt que no está en caché
        encontrado, respuesta, tiempo = self.cache.buscar_en_cache(self.prompt2, self.parametros2, 'sql')
        self.assertFalse(encontrado)
        self.assertIsNone(respuesta)
        self.assertEqual(tiempo, 0)
        
        # Guardar el segundo prompt y buscarlo
        self.cache.guardar_en_cache(self.prompt2, self.respuesta2, self.parametros2, 0.7, 'sql')
        
        encontrado, respuesta, tiempo = self.cache.buscar_en_cache(self.prompt2, self.parametros2, 'sql')
        self.assertTrue(encontrado)
        self.assertEqual(respuesta, self.respuesta2)
        self.assertEqual(tiempo, 0.7)
    
    def test_expiracion_cache(self):
        """Prueba la expiración de entradas de caché."""
        # Guardar en caché
        self.cache.guardar_en_cache(self.prompt1, self.respuesta1, self.parametros1, 0.5, 'sql')
        
        # Buscar inmediatamente (debería encontrarlo)
        encontrado, respuesta, tiempo = self.cache.buscar_en_cache(self.prompt1, self.parametros1, 'sql')
        self.assertTrue(encontrado)
        
        # Esperar a que expire la entrada (tiempo de expiración es 1 segundo)
        time.sleep(1.1)
        
        # Buscar después de expirar (no debería encontrarlo)
        encontrado, respuesta, tiempo = self.cache.buscar_en_cache(self.prompt1, self.parametros1, 'sql')
        self.assertFalse(encontrado)
    
    def test_limpiar_cache_expirado(self):
        """Prueba la limpieza de entradas expiradas."""
        # Guardar varias entradas en caché
        self.cache.guardar_en_cache(self.prompt1, self.respuesta1, self.parametros1, 0.5, 'sql')
        self.cache.guardar_en_cache(self.prompt2, self.respuesta2, self.parametros2, 0.7, 'sql')
        
        # Esperar a que expiren
        time.sleep(1.1)
        
        # Limpiar caché expirado
        eliminadas = self.cache.limpiar_cache_expirado()
        self.assertEqual(eliminadas, 2)  # Deberían haberse eliminado ambas entradas
        
        # Verificar que no se encuentran
        encontrado1, _, _ = self.cache.buscar_en_cache(self.prompt1, self.parametros1, 'sql')
        encontrado2, _, _ = self.cache.buscar_en_cache(self.prompt2, self.parametros2, 'sql')
        
        self.assertFalse(encontrado1)
        self.assertFalse(encontrado2)
    
    def test_vaciar_cache(self):
        """Prueba vaciar completamente el caché."""
        # Guardar varias entradas en caché
        self.cache.guardar_en_cache(self.prompt1, self.respuesta1, self.parametros1, 0.5, 'sql')
        self.cache.guardar_en_cache(self.prompt2, self.respuesta2, self.parametros2, 0.7, 'sql')
        
        # Vaciar caché
        eliminadas = self.cache.vaciar_cache()
        self.assertEqual(eliminadas, 2)  # Deberían haberse eliminado ambas entradas
        
        # Verificar que no se encuentran
        encontrado1, _, _ = self.cache.buscar_en_cache(self.prompt1, self.parametros1, 'sql')
        encontrado2, _, _ = self.cache.buscar_en_cache(self.prompt2, self.parametros2, 'sql')
        
        self.assertFalse(encontrado1)
        self.assertFalse(encontrado2)
    
    def test_estadisticas(self):
        """Prueba las estadísticas de uso del caché."""
        # Guardar entradas en caché
        self.cache.guardar_en_cache(self.prompt1, self.respuesta1, self.parametros1, 0.5, 'sql')
        self.cache.guardar_en_cache(self.prompt2, self.respuesta2, self.parametros2, 0.7, 'respuesta')
        
        # Buscar varias veces (algunas hits, algunas misses)
        self.cache.buscar_en_cache(self.prompt1, self.parametros1, 'sql')  # Hit
        self.cache.buscar_en_cache("prompt inexistente", self.parametros1, 'sql')  # Miss
        self.cache.buscar_en_cache(self.prompt2, self.parametros2, 'respuesta')  # Hit
        
        # Obtener estadísticas
        stats = self.cache.obtener_estadisticas()
        
        # Verificar que hay 2 entradas en total
        self.assertEqual(stats['total_entradas'], 2)
        
        # Verificar estadísticas de 'sql'
        self.assertIn('sql', stats['tipos'])
        self.assertEqual(stats['tipos']['sql']['hits'], 1)
        self.assertEqual(stats['tipos']['sql']['misses'], 2)  # 1 al guardar, 1 al buscar inexistente
        
        # Verificar estadísticas de 'respuesta'
        self.assertIn('respuesta', stats['tipos'])
        self.assertEqual(stats['tipos']['respuesta']['hits'], 1)
        self.assertEqual(stats['tipos']['respuesta']['misses'], 1)  # 1 al guardar
    
    def test_obtener_cache(self):
        """Prueba obtener la instancia global de caché."""
        # Obtener la instancia
        cache1 = phi2_cache.obtener_cache()
        self.assertIsInstance(cache1, phi2_cache.CachePhi2)
        
        # Obtener nuevamente (debería ser la misma instancia)
        cache2 = phi2_cache.obtener_cache()
        self.assertIs(cache1, cache2)

if __name__ == '__main__':
    unittest.main()