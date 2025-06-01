#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas de integración para asistente_phi2 con phi2_cache.
---------------------------------------------------------
Verifica la integración entre el asistente basado en phi-2 y el sistema de caché.
"""

import os
import sys
import unittest
import sqlite3
import tempfile
import pandas as pd
from unittest.mock import patch, MagicMock

# Asegurar que podemos importar desde el directorio padre
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar módulos a probar
import asistente_phi2
import phi2_cache
import config

class TestAsistentePhi2ConCache(unittest.TestCase):
    """Pruebas de integración para AsistentePhi2 con el sistema de caché."""

    def setUp(self):
        """Configuración de las pruebas."""
        # Crear archivos temporales para bases de datos
        self.temp_dir = tempfile.mkdtemp()
        self.temp_conocimiento_db = os.path.join(self.temp_dir, "conocimiento_test.db")
        self.temp_cache_db = os.path.join(self.temp_dir, "cache_test.db")
        
        # Crear una base de datos temporal para las pruebas
        self._crear_db_conocimiento()
        
        # Parchar la constante CACHE_DB para usar nuestra base de datos temporal
        self.original_cache_db = phi2_cache.CACHE_DB
        phi2_cache.CACHE_DB = self.temp_cache_db
        
        # Reiniciar la instancia global de caché
        phi2_cache._cache_instance = None
        
        # Crear una instancia de caché con tiempo de expiración corto para pruebas
        self.cache = phi2_cache.obtener_cache()
        self.cache.tiempo_expiracion = 1  # 1 segundo
        
        # Parchar la verificación de Ollama para que siempre retorne True
        self.patcher_verificar_ollama = patch.object(
            asistente_phi2.AsistentePhi2, 
            '_verificar_ollama', 
            return_value=True
        )
        self.mock_verificar_ollama = self.patcher_verificar_ollama.start()
        
        # Parchar las solicitudes a la API de Ollama
        self.patcher_requests_post = patch('asistente_phi2.requests.post')
        self.mock_requests_post = self.patcher_requests_post.start()
        
        # Configurar la respuesta simulada para la API de Ollama
        self.mock_response = MagicMock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {"response": "Respuesta simulada de phi-2"}
        self.mock_requests_post.return_value = self.mock_response
        
        # Crear instancia del asistente
        self.asistente = asistente_phi2.AsistentePhi2(ruta_db=self.temp_conocimiento_db)
        
        # Parchar generar_respuesta para monitorear las llamadas
        self.original_generar_respuesta = self.asistente.generar_respuesta
        self.asistente.generar_respuesta = self._generar_respuesta_con_cache
        
        # Contador de llamadas a la API
        self.llamadas_api = 0
    
    def tearDown(self):
        """Limpieza después de las pruebas."""
        # Cerrar la conexión del asistente si está abierta
        if self.asistente.conexion_db:
            self.asistente.conexion_db.close()
            self.asistente.conexion_db = None
        
        # Obtener el caché actual y cerrar sus conexiones
        cache = phi2_cache.obtener_cache()
        if hasattr(cache, 'conn') and cache.conn:
            cache.conn.close()
        
        # Restaurar la constante CACHE_DB
        phi2_cache.CACHE_DB = self.original_cache_db
        
        # Reiniciar la instancia de caché
        phi2_cache._cache_instance = None
        
        # Detener los patchers
        self.patcher_verificar_ollama.stop()
        self.patcher_requests_post.stop()
        
        # Eliminar archivos temporales
        if os.path.exists(self.temp_conocimiento_db):
            try:
                os.remove(self.temp_conocimiento_db)
            except:
                pass
                
        if os.path.exists(self.temp_cache_db):
            try:
                os.remove(self.temp_cache_db)
            except:
                pass
        
        # Eliminar el directorio temporal
        if os.path.exists(self.temp_dir):
            try:
                os.rmdir(self.temp_dir)
            except:
                pass
    
    def _crear_db_conocimiento(self):
        """Crea una base de datos temporal para pruebas."""
        conn = sqlite3.connect(self.temp_conocimiento_db)
        cursor = conn.cursor()
        
        # Crear tabla de exámenes
        cursor.execute('''
        CREATE TABLE examenes (
            id INTEGER PRIMARY KEY,
            tipo TEXT,
            nombre TEXT,
            "TAC doble" INTEGER,
            "TAC triple" INTEGER,
            fecha TEXT
        )
        ''')
        
        # Insertar datos de prueba
        datos_prueba = [
            (1, 'RX', 'RX Tórax', 0, 0, '01-may-2025'),
            (2, 'RX', 'RX Abdomen', 0, 0, '01-may-2025'),
            (3, 'TAC', 'TAC Cerebro', 0, 0, '02-may-2025'),
            (4, 'TAC', 'TAC Tórax-Abdomen', 1, 0, '02-may-2025'),
            (5, 'TAC', 'TAC Cerebro-Tórax-Abdomen', 0, 1, '03-may-2025'),
        ]
        
        cursor.executemany(
            'INSERT INTO examenes (id, tipo, nombre, "TAC doble", "TAC triple", fecha) VALUES (?, ?, ?, ?, ?, ?)',
            datos_prueba
        )
        
        conn.commit()
        conn.close()
    
    def _generar_respuesta_con_cache(self, pregunta: str) -> str:
        """
        Versión modificada de generar_respuesta que integra el caché y cuenta llamadas a la API.
        Esta función simula la integración que queremos probar.
        """
        # Parámetros para el modelo
        parametros = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "num_predict": 300,
            "stop": ["</RESPUESTA>", "<PREGUNTA>"]
        }
        
        # Primero, buscar en el caché
        cache = phi2_cache.obtener_cache()
        encontrado, respuesta_cache, tiempo = cache.buscar_en_cache(pregunta, parametros, 'respuesta')
        
        if encontrado:
            # Si se encuentra en caché, retornar sin llamar a la API
            return respuesta_cache
        
        # Si no se encuentra, llamar a la API (simulada)
        self.llamadas_api += 1
        respuesta = self.original_generar_respuesta(pregunta)
        
        # Guardar en caché para futuras consultas
        cache.guardar_en_cache(pregunta, respuesta, parametros, 0.5, 'respuesta')
        
        return respuesta
    
    def test_cache_primera_consulta(self):
        """Prueba que la primera consulta siempre va a la API y se guarda en caché."""
        pregunta = "¿Cuántos exámenes hay de cada tipo?"
        
        # Realizar la consulta
        respuesta = self.asistente.generar_respuesta(pregunta)
        
        # Verificar que se llamó a la API
        self.assertEqual(self.llamadas_api, 1)
        
        # Verificar que la respuesta es la simulada
        self.assertEqual(respuesta, "Respuesta simulada de phi-2")
        
        # Verificar que se guardó en caché
        cache = phi2_cache.obtener_cache()
        encontrado, respuesta_cache, _ = cache.buscar_en_cache(
            pregunta, 
            {
                "temperature": 0.1,
                "top_p": 0.95,
                "top_k": 40,
                "num_predict": 300,
                "stop": ["</RESPUESTA>", "<PREGUNTA>"]
            }, 
            'respuesta'
        )
        
        self.assertTrue(encontrado)
        self.assertEqual(respuesta_cache, "Respuesta simulada de phi-2")
    
    def test_cache_consulta_repetida(self):
        """Prueba que las consultas repetidas usan el caché y no llaman a la API."""
        pregunta = "¿Cuántos exámenes de TAC doble hay?"
        
        # Primera consulta (debe llamar a la API)
        respuesta1 = self.asistente.generar_respuesta(pregunta)
        self.assertEqual(self.llamadas_api, 1)
        
        # Segunda consulta con la misma pregunta (debe usar caché)
        respuesta2 = self.asistente.generar_respuesta(pregunta)
        
        # Verificar que no se llamó a la API nuevamente
        self.assertEqual(self.llamadas_api, 1)
        
        # Verificar que ambas respuestas son iguales
        self.assertEqual(respuesta1, respuesta2)
    
    def test_cache_consultas_diferentes(self):
        """Prueba que diferentes consultas generan diferentes entradas en caché."""
        pregunta1 = "¿Cuántos exámenes de RX hay?"
        pregunta2 = "¿Cuántos exámenes de TAC hay?"
        
        # Primera consulta
        respuesta1 = self.asistente.generar_respuesta(pregunta1)
        self.assertEqual(self.llamadas_api, 1)
        
        # Segunda consulta con pregunta diferente
        respuesta2 = self.asistente.generar_respuesta(pregunta2)
        self.assertEqual(self.llamadas_api, 2)
        
        # Verificar que ambas están en caché
        cache = phi2_cache.obtener_cache()
        parametros = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "num_predict": 300,
            "stop": ["</RESPUESTA>", "<PREGUNTA>"]
        }
        
        encontrado1, _, _ = cache.buscar_en_cache(pregunta1, parametros, 'respuesta')
        encontrado2, _, _ = cache.buscar_en_cache(pregunta2, parametros, 'respuesta')
        
        self.assertTrue(encontrado1)
        self.assertTrue(encontrado2)
    
    def test_cache_expiracion(self):
        """Prueba que las entradas de caché expiradas generan nuevas llamadas a la API."""
        import time
        
        pregunta = "¿Cuántos exámenes de TAC triple hay?"
        
        # Primera consulta
        respuesta1 = self.asistente.generar_respuesta(pregunta)
        self.assertEqual(self.llamadas_api, 1)
        
        # Esperar a que expire la entrada de caché (tiempo de expiración: 1 segundo)
        time.sleep(1.1)
        
        # Segunda consulta después de expiración
        respuesta2 = self.asistente.generar_respuesta(pregunta)
        
        # Verificar que se llamó a la API nuevamente
        self.assertEqual(self.llamadas_api, 2)
    
    def test_integracion_consulta_natural(self):
        """Prueba la integración de caché con la función consulta_natural."""
        # Parchar la función interna que llama a la API
        with patch.object(self.asistente, 'consulta_natural', wraps=self.asistente.consulta_natural) as mock_consulta:
            # Configurar una respuesta simulada para read_sql_query
            with patch('pandas.read_sql_query') as mock_read_sql:
                # DataFrame simulado para el resultado
                df_simulado = pd.DataFrame({
                    'tipo': ['RX', 'TAC'],
                    'cantidad': [2, 3]
                })
                mock_read_sql.return_value = df_simulado
                
                # Configurar la respuesta de la API para generar SQL
                self.mock_response.json.return_value = {
                    "response": "SELECT tipo, COUNT(*) as cantidad FROM examenes GROUP BY tipo"
                }
                
                # Primera consulta
                pregunta = "¿Cuántos exámenes hay por tipo?"
                exito1, resultado1 = self.asistente.consulta_natural(pregunta)
                
                # Verificar que se generó la consulta SQL
                self.assertTrue(exito1)
                self.assertTrue(isinstance(resultado1, pd.DataFrame))
                
                # Segunda consulta idéntica (debería usar caché)
                exito2, resultado2 = self.asistente.consulta_natural(pregunta)
                
                # Verificar que se usó el caché
                self.assertEqual(mock_consulta.call_count, 2)  # Llamada, pero debe usar caché internamente
                self.assertEqual(self.mock_requests_post.call_count, 1)  # Solo una llamada a la API
    
    def test_estadisticas_cache(self):
        """Prueba que las estadísticas del caché se actualizan correctamente."""
        # Crear un caché nuevo para este test específico
        temp_cache_db = os.path.join(self.temp_dir, "cache_stats_test.db")
        original_cache_db = phi2_cache.CACHE_DB
        phi2_cache.CACHE_DB = temp_cache_db
        phi2_cache._cache_instance = None
        
        # Obtener una nueva instancia limpia
        cache = phi2_cache.obtener_cache()
        
        # Simular consultas con el nuevo caché
        prompt1 = "Test prompt 1"
        prompt2 = "Test prompt 2"
        params = {"temperature": 0.1, "top_p": 0.9}
        
        # Guardar dos entradas
        cache.guardar_en_cache(prompt1, "Respuesta 1", params, 0.1, 'respuesta')
        cache.guardar_en_cache(prompt2, "Respuesta 2", params, 0.2, 'respuesta')
        
        # Buscar la primera entrada (hit)
        cache.buscar_en_cache(prompt1, params, 'respuesta')
        
        # Obtener estadísticas
        stats = cache.obtener_estadisticas()
        
        # Verificar estadísticas
        self.assertEqual(stats['total_entradas'], 2)  # Dos entradas
        self.assertEqual(stats['tipos']['respuesta']['hits'], 1)  # Un hit
        self.assertEqual(stats['tipos']['respuesta']['misses'], 2)  # Dos misses (al guardar)
        
        # Cerrar la conexión
        cache.cerrar_conexion()
        
        # Restaurar el valor original
        phi2_cache.CACHE_DB = original_cache_db
        phi2_cache._cache_instance = None

if __name__ == '__main__':
    unittest.main()