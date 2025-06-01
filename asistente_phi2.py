#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integración de Phi-2 para Asistente de Análisis de Turnos
---------------------------------------------------------
Módulo para integrar el modelo phi-2 como asistente de análisis
de datos médicos y consultas en lenguaje natural.
"""

import os
import sqlite3
import subprocess
import json
import requests
import tempfile
import pandas as pd
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any

# Importar sistema de caché y configuración
import phi2_cache
import config

# Obtener logger
logger = config.obtener_logger(__name__)

class AsistentePhi2:
    """Asistente basado en phi-2 para análisis de datos y consultas naturales."""
    
    def __init__(self, ruta_db: Optional[str] = None, host: str = "localhost", puerto: Optional[int] = None):
        """
        Inicializa el asistente con phi-2 y conexión a la base de datos.
        
        Args:
            ruta_db: Ruta a la base de datos SQLite (opcional)
            host: Host donde se ejecuta Ollama (por defecto: localhost)
            puerto: Puerto de Ollama (por defecto: se usará el puerto estándar 11434 o el configurado)
        """
        self.host = host
        
        # Si no se proporciona puerto, intentar usar el de la configuración
        if puerto is None:
            try:
                # Intentar cargar de la configuración
                from config import PHI2_CONFIG
                self.puerto = PHI2_CONFIG.get("PUERTO", 11434)
            except ImportError:
                # Si no se puede importar, usar el puerto estándar
                self.puerto = 11434
        else:
            self.puerto = puerto
            
        self.puertos_alternativos = []
        try:
            # Intentar cargar puerto alternativo de la configuración
            from config import PHI2_CONFIG
            puerto_alt = PHI2_CONFIG.get("PUERTO_ALTERNATIVO")
            if puerto_alt and puerto_alt != self.puerto:
                self.puertos_alternativos.append(puerto_alt)
        except ImportError:
            pass
            
        # Si el puerto configurado no es el estándar, añadir el puerto estándar como alternativa
        if self.puerto != 11434:
            self.puertos_alternativos.append(11434)
            
        self.api_base = f"http://{host}:{self.puerto}/api"
        self.modelo = "phi:latest"  # Nombre exacto del modelo en Ollama
        self.conexion_db = None
        self.ruta_db = ruta_db
        
        # Verificar si Ollama está disponible
        self.ollama_disponible = self._verificar_ollama()
        
        # Conectar a la base de datos si se proporcionó una ruta
        if ruta_db:
            self._conectar_db(ruta_db)
    
    def _verificar_ollama(self) -> bool:
        """
        Verifica si Ollama está disponible y si el modelo phi-2 está instalado.
        Intenta con el puerto principal y luego con los alternativos.
        
        Returns:
            bool: True si Ollama está disponible y el modelo instalado, False en caso contrario
        """
        # Intentar con el puerto principal primero
        if self._verificar_puerto(self.puerto):
            return True
            
        # Si falla, intentar con los puertos alternativos
        for puerto_alt in self.puertos_alternativos:
            print(f"Intentando conectar a Ollama en puerto alternativo: {puerto_alt}")
            if self._verificar_puerto(puerto_alt):
                # Actualizar el puerto y api_base a los que funcionaron
                self.puerto = puerto_alt
                self.api_base = f"http://{self.host}:{self.puerto}/api"
                print(f"Conexión exitosa a Ollama en puerto: {puerto_alt}")
                return True
                
        return False
        
    def _verificar_puerto(self, puerto: int) -> bool:
        """
        Verifica si Ollama está disponible en un puerto específico.
        
        Args:
            puerto: Puerto a verificar
            
        Returns:
            bool: True si Ollama está disponible en ese puerto, False en caso contrario
        """
        api_url = f"http://{self.host}:{puerto}/api"
        try:
            response = requests.get(f"{api_url}/tags", timeout=5)
            if response.status_code == 200:
                modelos = response.json().get("models", [])
                if any(m.get("name") == self.modelo for m in modelos):
                    return True
                
                # Si phi-2 no está disponible, intentar descargarlo
                print(f"Modelo {self.modelo} no encontrado. Intentando descargarlo...")
                pull_response = requests.post(
                    f"{api_url}/pull",
                    json={"name": self.modelo},
                    timeout=60
                )
                return pull_response.status_code == 200
            return False
        except requests.RequestException:
            return False
    
    def _conectar_db(self, ruta_db: str) -> bool:
        """
        Conecta a la base de datos SQLite.
        
        Args:
            ruta_db: Ruta a la base de datos SQLite
            
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario
        """
        try:
            # Cierra la conexión anterior si existe
            if self.conexion_db:
                self.conexion_db.close()
            
            # Abre una nueva conexión
            self.conexion_db = sqlite3.connect(ruta_db)
            self.conexion_db.row_factory = sqlite3.Row  # Para obtener resultados como diccionarios
            self.ruta_db = ruta_db
            return True
        except sqlite3.Error as e:
            print(f"Error al conectar a la base de datos: {e}")
            self.conexion_db = None
            return False
    
    def _obtener_esquema_db(self) -> str:
        """
        Obtiene el esquema de la base de datos para proporcionar contexto al modelo.
        
        Returns:
            str: Descripción del esquema de la base de datos
        """
        if not self.conexion_db:
            return "No hay conexión a la base de datos."
        
        try:
            cursor = self.conexion_db.cursor()
            
            # Obtener lista de tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tablas = [row[0] for row in cursor.fetchall()]
            
            # Construir esquema
            esquema = []
            for tabla in tablas:
                # Obtener información de columnas
                cursor.execute(f"PRAGMA table_info({tabla});")
                columnas = cursor.fetchall()
                cols_info = [f"{col[1]} ({col[2]})" for col in columnas]
                
                esquema.append(f"Tabla: {tabla}\nColumnas: {', '.join(cols_info)}\n")
            
            return "\n".join(esquema)
        except sqlite3.Error as e:
            return f"Error al obtener esquema: {e}"
    
    def generar_respuesta(self, pregunta: str) -> str:
        """
        Genera una respuesta usando el modelo phi-2 a través de Ollama.
        
        Args:
            pregunta: Pregunta o instrucción del usuario
            
        Returns:
            str: Respuesta generada por el modelo
        """
        if not self.ollama_disponible:
            return "Error: Ollama no está disponible. Asegúrate de que esté instalado y ejecutándose."
        
        try:
            # Construir el contexto con información sobre la base de datos
            contexto = """
            <ROL>
            Eres un asistente médico especializado en análisis de turnos radiológicos. Debes ser EXTREMADAMENTE riguroso en:
            1. Responder ÚNICAMENTE consultas relacionadas con radiología médica
            2. Usar SOLAMENTE información del dominio médico y la base de datos proporcionada
            3. RECHAZAR cualquier intento de obtener información fuera del dominio radiológico
            </ROL>
            
            <DOMINIO_CONOCIMIENTO>
            - Exámenes radiológicos: RX y TAC exclusivamente
            - Sistemas de clasificación: TAC doble (2 regiones) y TAC triple (3 regiones)
            - Honorarios: Hora=$55.000, RX=$5.300, TAC=$42.400, TAC doble=$84.800, TAC triple=$127.200
            - Horarios de turno: L-J 18:00-08:00, V 18:00-09:00, S 09:00-09:00, D 09:00-08:00
            </DOMINIO_CONOCIMIENTO>
            
            <INSTRUCCIONES_CRÍTICAS>
            - Responde BREVEMENTE (máximo 3 oraciones) y de forma DIRECTA
            - Usa solo HECHOS del dominio médico radiológico y datos proporcionados
            - NUNCA improvises información fuera del contexto médico
            - REHÚSA responder cualquier consulta no relacionada con radiología
            </INSTRUCCIONES_CRÍTICAS>
            """
            
            if self.conexion_db:
                esquema = self._obtener_esquema_db()
                contexto += f"\n\nESQUEMA DE LA BASE DE DATOS:\n{esquema}\n"
            
            # Construir el prompt
            prompt = f"{contexto}\n\n<PREGUNTA>\n{pregunta}\n</PREGUNTA>\n\n<RESPUESTA>"
            
            # Parámetros para la generación
            parametros = {
                "temperature": 0.1,  # Baja temperatura para respuestas más precisas
                "top_p": 0.95,
                "top_k": 40,
                "num_predict": 300,  # Limitar longitud de respuesta para mayor concisión
                "stop": ["</RESPUESTA>", "<PREGUNTA>"],  # Detener generación en estos tokens
            }
            
            # Obtener instancia de caché
            cache = phi2_cache.obtener_cache()
            
            # Buscar en caché
            logger.debug(f"Buscando en caché: {pregunta[:50]}...")
            encontrado, respuesta, tiempo = cache.buscar_en_cache(prompt, parametros, 'respuesta')
            
            if encontrado:
                logger.info(f"Respuesta encontrada en caché (generada en {tiempo:.3f}s): {pregunta[:50]}...")
                return respuesta
            
            # Si no está en caché, llamar a la API de Ollama
            logger.info(f"Caché miss, generando respuesta con Ollama: {pregunta[:50]}...")
            tiempo_inicio = time.time()
            
            # Llamar a la API de Ollama
            response = requests.post(
                f"{self.api_base}/generate",
                json={
                    "model": self.modelo,
                    "prompt": prompt,
                    "stream": False,
                    "options": parametros,
                },
                timeout=30
            )
            
            tiempo_generacion = time.time() - tiempo_inicio
            
            if response.status_code == 200:
                respuesta = response.json().get("response", "No se pudo generar una respuesta.")
                
                # Guardar en caché
                cache.guardar_en_cache(prompt, respuesta, parametros, tiempo_generacion, 'respuesta')
                logger.info(f"Respuesta generada en {tiempo_generacion:.3f}s y guardada en caché")
                
                return respuesta
            else:
                error_msg = f"Error al comunicarse con Ollama: {response.status_code}"
                logger.error(error_msg)
                return error_msg
        
        except Exception as e:
            error_msg = f"Error al generar respuesta: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def ejecutar_consulta_sql(self, consulta: str) -> Tuple[bool, Union[pd.DataFrame, str]]:
        """
        Ejecuta una consulta SQL directamente en la base de datos.
        
        Args:
            consulta: Consulta SQL a ejecutar
            
        Returns:
            Tuple[bool, Union[pd.DataFrame, str]]: 
                (éxito, resultado como DataFrame o mensaje de error)
        """
        if not self.conexion_db:
            return False, "No hay conexión a la base de datos."
        
        try:
            # Ejecutar la consulta y convertir el resultado a DataFrame
            df = pd.read_sql_query(consulta, self.conexion_db)
            return True, df
        except Exception as e:
            return False, f"Error al ejecutar consulta: {str(e)}"
    
    def consulta_natural(self, pregunta: str) -> Tuple[bool, Union[pd.DataFrame, str]]:
        """
        Convierte una pregunta en lenguaje natural a SQL y la ejecuta.
        
        Args:
            pregunta: Pregunta en lenguaje natural
            
        Returns:
            Tuple[bool, Union[pd.DataFrame, str]]: 
                (éxito, resultado como DataFrame o mensaje de error)
        """
        if not self.conexion_db:
            return False, "No hay conexión a la base de datos."
        
        if not self.ollama_disponible:
            return False, "Ollama no está disponible para procesar la consulta."
        
        try:
            # Obtener esquema para dar contexto
            esquema = self._obtener_esquema_db()
            
            # Prompt simplificado para generación de SQL
            prompt = f"""
            RESPONDE CON UNA CONSULTA SQL SOLAMENTE. No incluyas texto, comentarios ni explicaciones.

            ESQUEMA DE LA BASE DE DATOS:
            {esquema}
            
            INFORMACIÓN IMPORTANTE:
            - Solo genera una consulta SQL válida que comience con SELECT
            - Usa comillas dobles para las columnas con espacios: "TAC doble", "TAC triple", "Fecha del procedimiento programado"
            - Las columnas "TAC doble" y "TAC triple" son booleanas (0=falso, 1=verdadero)
            - La tabla principal es "examenes"
            - La columna "Tipo" tiene valores 'RX' o 'TAC'
            
            INSTRUCCIÓN: Convierte la siguiente pregunta en una consulta SQL válida.
            PREGUNTA: {pregunta}
            CONSULTA SQL: 
            """
            
            # Parámetros para la generación SQL
            parametros = {
                "temperature": 0.1,
                "top_p": 0.95,
                "top_k": 40,
                "num_predict": 100,  # SQL queries should be short
                "stop": ["</SQL>", "</PREGUNTA>"],  # Stop on these tokens
            }
            
            # Obtener instancia de caché
            cache = phi2_cache.obtener_cache()
            
            # Buscar en caché
            logger.debug(f"Buscando SQL en caché para: {pregunta[:50]}...")
            encontrado, sql_query, tiempo = cache.buscar_en_cache(prompt, parametros, 'sql')
            
            if not encontrado:
                # Si no está en caché, llamar a la API de Ollama
                logger.info(f"Caché miss para SQL, generando con Ollama: {pregunta[:50]}...")
                tiempo_inicio = time.time()
                
                # Llamar a la API de Ollama para generar la consulta SQL
                response = requests.post(
                    f"{self.api_base}/generate",
                    json={
                        "model": self.modelo,
                        "prompt": prompt,
                        "stream": False,
                        "options": parametros,
                    },
                    timeout=30
                )
                
                tiempo_generacion = time.time() - tiempo_inicio
                
                if response.status_code != 200:
                    return False, f"Error en la API de Ollama: {response.status_code}"
                
                # Extraer la consulta SQL generada
                sql_query = response.json().get("response", "").strip()
                
                # Guardar en caché
                cache.guardar_en_cache(prompt, sql_query, parametros, tiempo_generacion, 'sql')
                logger.info(f"SQL generado en {tiempo_generacion:.3f}s y guardado en caché")
            else:
                logger.info(f"SQL encontrado en caché (generado en {tiempo:.3f}s): {pregunta[:50]}...")
            
            # Extraer y limpiar la consulta SQL
            # Eliminar espacios en blanco al inicio y final
            sql_query = sql_query.strip()
            
            # Eliminar markdown y HTML
            sql_query = re.sub(r'```sql|```', '', sql_query)
            sql_query = re.sub(r'<[^>]+>.*?<\/[^>]+>', '', sql_query)
            sql_query = re.sub(r'<[^>]+>', '', sql_query)
            
            # Extraer la primera consulta SQL (desde SELECT hasta el punto y coma)
            match = re.search(r'\b(SELECT|select)\b[^;]*;?', sql_query)
            if match:
                clean_sql = match.group(0).strip()
                # Asegurar que termina con punto y coma
                if not clean_sql.endswith(';'):
                    clean_sql += ';'
            else:
                logger.error(f"No se generó una consulta SQL válida: {sql_query}")
                return False, f"No se generó una consulta SQL válida: {sql_query}"
            
            # Corregir columnas con espacios
            columnas_con_espacios = [
                "TAC doble", "TAC triple", "Fecha del procedimiento programado", 
                "Número de cita", "Sala de adquisición", "Nombre del procedimiento",
                "Apellidos del paciente", "Nombre del paciente", "ID del paciente",
                "Hora del procedimiento programado"
            ]
            
            for columna in columnas_con_espacios:
                # Reemplazar solo si la columna no está entre comillas
                clean_sql = re.sub(f'\b{columna}\b(?!["\\]\\)])', f'"{columna}"', clean_sql)
            
            # Usar la consulta limpia
            sql_query = clean_sql
            logger.debug(f"Consulta SQL limpia: {sql_query}")
            
            # Ejecutar la consulta SQL generada
            try:
                tiempo_inicio = time.time()
                df = pd.read_sql_query(sql_query, self.conexion_db)
                tiempo_ejecucion = time.time() - tiempo_inicio
                logger.info(f"Consulta SQL ejecutada en {tiempo_ejecucion:.3f}s con {len(df)} resultados")
                return True, df
            except Exception as e:
                error_msg = f"Error al ejecutar la consulta SQL generada: {str(e)}\n\nConsulta generada: {sql_query}"
                logger.error(error_msg)
                return False, error_msg
            
        except Exception as e:
            error_msg = f"Error en consulta natural: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def crear_base_datos_temporal(self, df: pd.DataFrame, nombre_tabla: str = "analisis") -> Optional[str]:
        """
        Crea una base de datos SQLite temporal con los datos del DataFrame.
        
        Args:
            df: DataFrame con los datos a guardar
            nombre_tabla: Nombre de la tabla a crear
            
        Returns:
            Optional[str]: Ruta a la base de datos temporal o None si hay error
        """
        try:
            # Crear directorio temporal si no existe
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Crear archivo de base de datos temporal
            fd, temp_db_path = tempfile.mkstemp(suffix='.db', prefix='analisis_', dir=temp_dir)
            os.close(fd)  # Cerrar el descriptor de archivo
            
            # Crear conexión a la base de datos temporal
            conn = sqlite3.connect(temp_db_path)
            
            # Guardar DataFrame en la base de datos
            df.to_sql(nombre_tabla, conn, index=False, if_exists='replace')
            
            # Cerrar conexión
            conn.close()
            
            # Conectar a esta nueva base de datos
            self._conectar_db(temp_db_path)
            
            return temp_db_path
        
        except Exception as e:
            print(f"Error al crear base de datos temporal: {e}")
            return None
    
    def instalar_ollama(self) -> bool:
        """
        Intenta instalar Ollama automáticamente si no está disponible.
        
        Returns:
            bool: True si la instalación fue exitosa, False en caso contrario
        """
        try:
            sistema = os.uname().sysname.lower()
            
            if "darwin" in sistema:  # macOS
                try:
                    # Intentar instalar con brew
                    subprocess.run(["brew", "install", "ollama"], check=True)
                    subprocess.run(["brew", "services", "start", "ollama"], check=True)
                    return True
                except subprocess.CalledProcessError:
                    print("No se pudo instalar Ollama con Homebrew.")
                    return False
                
            elif "linux" in sistema:
                # Script de instalación oficial para Linux
                try:
                    subprocess.run(["curl", "-fsSL", "https://ollama.com/install.sh", "|", "sh"], check=True, shell=True)
                    subprocess.run(["systemctl", "start", "ollama"], check=True)
                    return True
                except subprocess.CalledProcessError:
                    print("No se pudo instalar Ollama en Linux.")
                    return False
            
            else:
                print(f"Sistema operativo no compatible para instalación automática: {sistema}")
                return False
                
        except Exception as e:
            print(f"Error al intentar instalar Ollama: {e}")
            return False
    
    def verificar_instalacion(self) -> Dict[str, Any]:
        """
        Verifica el estado de la instalación de Ollama y el modelo phi-2.
        
        Returns:
            Dict: Estado de instalación y disponibilidad
        """
        estado = {
            "ollama_instalado": False,
            "ollama_ejecutando": False,
            "modelo_phi2_disponible": False,
            "db_conectada": self.conexion_db is not None,
            "mensaje": ""
        }
        
        # Verificar si Ollama está instalado
        try:
            resultado = subprocess.run(["which", "ollama"], capture_output=True, text=True)
            estado["ollama_instalado"] = resultado.returncode == 0
        except:
            estado["ollama_instalado"] = False
        
        # Verificar si Ollama está ejecutándose
        try:
            response = requests.get(f"{self.api_base}/tags", timeout=2)
            estado["ollama_ejecutando"] = response.status_code == 200
            
            # Verificar si el modelo phi-2 está disponible
            if estado["ollama_ejecutando"]:
                modelos = response.json().get("models", [])
                estado["modelo_phi2_disponible"] = any(m.get("name") == self.modelo for m in modelos)
        except:
            estado["ollama_ejecutando"] = False
        
        # Construir mensaje
        if not estado["ollama_instalado"]:
            estado["mensaje"] = "Ollama no está instalado. Intenta instalarlo manualmente."
        elif not estado["ollama_ejecutando"]:
            estado["mensaje"] = "Ollama está instalado pero no se está ejecutando."
        elif not estado["modelo_phi2_disponible"]:
            estado["mensaje"] = f"El modelo {self.modelo} no está disponible. Puedes instalarlo con: ollama pull {self.modelo}"
        elif not estado["db_conectada"]:
            estado["mensaje"] = "No hay conexión a la base de datos."
        else:
            estado["mensaje"] = "Todo está correctamente configurado y listo para usar."
        
        return estado

# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia
    asistente = AsistentePhi2()
    
    # Verificar instalación
    estado = asistente.verificar_instalacion()
    print(f"Estado: {json.dumps(estado, indent=2)}")
    
    # Si todo está bien, probar una consulta
    if estado["ollama_ejecutando"] and estado["modelo_phi2_disponible"]:
        respuesta = asistente.generar_respuesta("¿Cuáles son los beneficios de usar phi-2 para análisis médico?")
        print(f"\nRespuesta: {respuesta}")