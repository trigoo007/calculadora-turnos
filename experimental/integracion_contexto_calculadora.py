#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integración del Sistema de Contexto con la Calculadora de Turnos
----------------------------------------------------------------
Este módulo integra el sistema de almacenamiento y recuperación de contexto
con la calculadora de turnos para proporcionar memoria histórica.
"""

import os
import json
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from recuperacion_contexto import RecuperacionContexto
from contexto_vectorial import ContextoVectorial

# Importar componentes de la calculadora
try:
    import config
    from calculadora_turnos import CalculadoraTurnos
    from asistente_phi2 import AsistentePhi2
except ImportError:
    print("Advertencia: No se pudieron importar todos los componentes de la calculadora.")

# Obtener logger
try:
    logger = config.obtener_logger(__name__)
except:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class IntegracionContextoCalculadora:
    """
    Clase que integra el sistema de contexto con la calculadora de turnos.
    """
    
    def __init__(self):
        """
        Inicializa la integración entre el sistema de contexto y la calculadora.
        """
        # Inicializar sistema de contexto
        self.recuperacion_contexto = None
        try:
            self.recuperacion_contexto = RecuperacionContexto()
            logger.info("Sistema de recuperación de contexto inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar sistema de recuperación de contexto: {e}")
        
        # Inicializar calculadora
        self.calculadora = None
        try:
            self.calculadora = CalculadoraTurnos()
            logger.info("Calculadora de turnos inicializada correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar calculadora: {e}")
        
        # Inicializar asistente phi-2
        self.asistente = None
        try:
            ruta_db = os.path.join(config.CONOCIMIENTO_DIR, "conocimiento.db")
            if os.path.exists(ruta_db):
                self.asistente = AsistentePhi2(ruta_db=ruta_db)
                logger.info("Asistente phi-2 inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar asistente phi-2: {e}")
    
    def procesar_y_almacenar_csv(self, ruta_csv: str, directorio_salida: str, nombre_doctor: str) -> Dict[str, Any]:
        """
        Procesa un archivo CSV con la calculadora y almacena los resultados en el contexto.
        
        Args:
            ruta_csv: Ruta al archivo CSV a procesar
            directorio_salida: Directorio donde guardar los resultados
            nombre_doctor: Nombre del doctor para el reporte
            
        Returns:
            Diccionario con los resultados del procesamiento
        """
        if not self.calculadora:
            error_msg = "No se pudo procesar el archivo: Calculadora no inicializada"
            logger.error(error_msg)
            return {"error": error_msg}
        
        try:
            # Procesar archivo con la calculadora
            exito, resultado = self.calculadora.procesar_archivo(ruta_csv, directorio_salida, nombre_doctor)
            
            if not exito:
                return {"error": f"Error al procesar archivo: {resultado}"}
            
            # Almacenar resultados en el contexto
            self._almacenar_en_contexto(ruta_csv, resultado)
            
            return resultado
            
        except Exception as e:
            error_msg = f"Error al procesar y almacenar CSV: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def consulta_con_contexto(self, consulta: str) -> str:
        """
        Realiza una consulta al asistente phi-2 con contexto añadido.
        
        Args:
            consulta: Pregunta o consulta del usuario
            
        Returns:
            Respuesta del asistente phi-2 con contexto
        """
        if not self.asistente:
            return "No se pudo realizar la consulta: Asistente phi-2 no inicializado"
        
        try:
            # Verificar si el sistema de contexto está disponible
            if self.recuperacion_contexto is None:
                logger.warning("Sistema de contexto no disponible, se realizará la consulta sin contexto")
                # Realizar la consulta directamente al asistente
                return self.asistente.generar_respuesta(consulta)
            
            # Recuperar contexto relevante
            contexto = self.recuperacion_contexto.recuperar_para_consulta(consulta)
            
            # Añadir el contexto a la consulta
            consulta_con_contexto = f"Contexto previo:\n{contexto}\n\nConsulta actual:\n{consulta}"
            
            # Realizar la consulta al asistente
            respuesta = self.asistente.generar_respuesta(consulta_con_contexto)
            
            # Almacenar la consulta y respuesta en el contexto
            self.recuperacion_contexto.guardar_mensaje(consulta, "usuario")
            self.recuperacion_contexto.guardar_mensaje(respuesta, "asistente")
            
            return respuesta
            
        except Exception as e:
            error_msg = f"Error al realizar consulta con contexto: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    def consulta_sql_con_contexto(self, consulta: str) -> Tuple[bool, Any]:
        """
        Realiza una consulta SQL en lenguaje natural con contexto añadido.
        
        Args:
            consulta: Consulta en lenguaje natural
            
        Returns:
            Tupla (éxito, resultado) donde resultado es un DataFrame o mensaje de error
        """
        if not self.asistente:
            return False, "No se pudo realizar la consulta: Asistente phi-2 no inicializado"
        
        try:
            # Verificar si el sistema de contexto está disponible
            prompt_sql = ""
            if self.recuperacion_contexto is None:
                logger.warning("Sistema de contexto no disponible, se realizará la consulta SQL sin contexto")
                # Construir un prompt básico sin contexto
                prompt_sql = f"""
                Eres un experto en SQL que genera consultas precisas.
                
                IMPORTANTE - REGLAS PARA TU RESPUESTA:
                1. DEBES generar SOLAMENTE una consulta SQL sin ningún otro texto
                2. NO incluyas explicaciones, comentarios o texto adicional
                3. NO uses comillas alrededor de los nombres de columna con espacios - usa ["TAC doble"] en su lugar
                4. SIEMPRE empieza tu respuesta con SELECT o WITH
                5. NO uses columnas que no existen en el esquema
                
                PREGUNTA DEL USUARIO: {consulta}
                
                CONSULTA SQL (SOLO SQL, SIN EXPLICACIONES):
                """
            else:
                # Recuperar contexto relevante
                contexto = self.recuperacion_contexto.recuperar_para_consulta(consulta)
                
                # Construir un prompt especial para generación SQL con contexto
                prompt_sql = f"""
                Eres un experto en SQL que genera consultas precisas.
                
                CONTEXTO HISTÓRICO:
                {contexto}
                
                IMPORTANTE - REGLAS PARA TU RESPUESTA:
                1. DEBES generar SOLAMENTE una consulta SQL sin ningún otro texto
                2. NO incluyas explicaciones, comentarios o texto adicional
                3. NO uses comillas alrededor de los nombres de columna con espacios - usa ["TAC doble"] en su lugar
                4. SIEMPRE empieza tu respuesta con SELECT o WITH
                5. NO uses columnas que no existen en el esquema
                
                PREGUNTA DEL USUARIO: {consulta}
                
                CONSULTA SQL (SOLO SQL, SIN EXPLICACIONES):
                """
                
                # Guardar el prompt en el contexto
                doc_id = self.recuperacion_contexto.guardar_mensaje(prompt_sql, "sistema")
            
            # Realizar la consulta SQL con el prompt generado
            exito, resultado = self.asistente.consulta_natural(consulta)
            
            # Guardar la consulta y el resultado en el contexto si está disponible
            if self.recuperacion_contexto is not None:
                if exito:
                    resultado_str = f"Consulta SQL exitosa con {len(resultado)} resultados"
                    if len(resultado) > 0:
                        muestra = resultado.head(3).to_json(orient="records")
                        resultado_str += f"\nMuestra de resultados: {muestra}"
                else:
                    resultado_str = f"Error en consulta SQL: {resultado}"
                
                self.recuperacion_contexto.guardar_mensaje(consulta, "usuario")
                self.recuperacion_contexto.guardar_mensaje(resultado_str, "sistema")
            
            return exito, resultado
            
        except Exception as e:
            error_msg = f"Error al realizar consulta SQL con contexto: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def almacenar_dataset(self, df: pd.DataFrame, nombre: str) -> str:
        """
        Almacena un DataFrame en el sistema de contexto.
        
        Args:
            df: DataFrame a almacenar
            nombre: Nombre del dataset
            
        Returns:
            ID del documento guardado
        """
        # Verificar si el sistema de contexto está disponible
        if self.recuperacion_contexto is None:
            logger.warning("Sistema de contexto no disponible, no se almacenará el dataset")
            return ""
            
        try:
            # Procesar y almacenar el dataset
            return self.recuperacion_contexto.guardar_dataset(df, nombre)
            
        except Exception as e:
            error_msg = f"Error al almacenar dataset: {str(e)}"
            logger.error(error_msg)
            return ""
    
    def _almacenar_en_contexto(self, ruta_csv: str, resultado: Dict[str, Any]) -> None:
        """
        Almacena los resultados del procesamiento en el sistema de contexto.
        
        Args:
            ruta_csv: Ruta al archivo CSV procesado
            resultado: Resultado del procesamiento
        """
        # Verificar si el sistema de contexto está disponible
        if self.recuperacion_contexto is None:
            logger.warning("Sistema de contexto no disponible, no se almacenarán los resultados")
            return
            
        try:
            # Crear un resumen del procesamiento
            nombre_archivo = os.path.basename(ruta_csv)
            fecha_actual = pd.Timestamp.now().strftime("%d-%m-%Y %H:%M")
            eco = resultado['resultado_economico']
            
            resumen = f"""
            Procesamiento de {nombre_archivo} realizado el {fecha_actual}
            
            RESUMEN ECONÓMICO:
            - Horas trabajadas: {eco['horas_trabajadas']}
            - RX: {eco['rx_count']} (${eco['rx_total']:,})
            - TAC: {eco['tac_count']} (${eco['tac_total']:,})
            - TAC doble: {eco['tac_doble_count']} (${eco['tac_doble_total']:,})
            - TAC triple: {eco['tac_triple_count']} (${eco['tac_triple_total']:,})
            - Honorarios por horas: ${eco['honorarios_hora']:,}
            - TOTAL: ${eco['total']:,}
            
            ARCHIVOS GENERADOS:
            """
            
            for nombre, ruta in resultado['rutas_excel'].items():
                resumen += f"- {nombre}: {os.path.basename(ruta)}\n"
            
            # Guardar en el contexto
            self.recuperacion_contexto.guardar_mensaje(
                resumen,
                "sistema", 
            )
            
            # Si el resultado contiene un DataFrame, almacenarlo también
            if 'examenes_filtrados' in resultado and isinstance(resultado['examenes_filtrados'], pd.DataFrame):
                self.almacenar_dataset(resultado['examenes_filtrados'], f"examenes_{nombre_archivo}")
            
            logger.info(f"Resultados del procesamiento de {nombre_archivo} almacenados en el contexto")
            
        except Exception as e:
            logger.error(f"Error al almacenar resultados en contexto: {e}")


def ejemplo_uso():
    """Función de ejemplo para demostrar el uso de la integración."""
    print("Integración del Sistema de Contexto con la Calculadora de Turnos")
    print("---------------------------------------------------------------")
    
    # Crear instancia de integración
    integracion = IntegracionContextoCalculadora()
    
    # Ejemplo de procesamiento de CSV
    ruta_csv = input("Ingrese la ruta al archivo CSV a procesar (o presione Enter para omitir): ")
    if ruta_csv:
        directorio_salida = os.path.dirname(ruta_csv)
        nombre_doctor = input("Ingrese el nombre del doctor (o presione Enter para usar 'Cikutovic'): ") or "Cikutovic"
        
        print(f"Procesando {ruta_csv}...")
        resultado = integracion.procesar_y_almacenar_csv(ruta_csv, directorio_salida, nombre_doctor)
        
        if "error" in resultado:
            print(f"Error: {resultado['error']}")
        else:
            print("Procesamiento exitoso!")
            eco = resultado['resultado_economico']
            print(f"Total: ${eco['total']:,}")
    
    # Ejemplo de consulta con contexto
    consulta = input("\nIngrese una consulta para el asistente (o presione Enter para omitir): ")
    if consulta:
        print("Consultando con contexto...")
        respuesta = integracion.consulta_con_contexto(consulta)
        print(f"Respuesta: {respuesta}")
    
    # Ejemplo de consulta SQL con contexto
    consulta_sql = input("\nIngrese una consulta SQL en lenguaje natural (o presione Enter para omitir): ")
    if consulta_sql:
        print("Consultando SQL con contexto...")
        exito, resultado = integracion.consulta_sql_con_contexto(consulta_sql)
        
        if exito and isinstance(resultado, pd.DataFrame):
            print("Consulta exitosa!")
            print(resultado.head())
        else:
            print(f"Error: {resultado}")


if __name__ == "__main__":
    ejemplo_uso()