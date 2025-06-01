#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Recuperación de Contexto para Proyecto Calculadora de Turnos en Radiología
-------------------------------------------------------------------------------------
Este módulo implementa la funcionalidad de recuperación de contexto para el asistente Claude,
permitiendo mantener una memoria persistente del proyecto y recuperar información relevante.
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple
from contexto_vectorial import ContextoVectorial

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("contexto_recuperacion.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("recuperacion_contexto")

class RecuperacionContexto:
    """
    Sistema para recuperar contexto relevante y mantener la ventana de contexto
    controlada en conversaciones con Claude.
    """
    
    def __init__(self, max_tokens_ventana: int = 6000):
        """
        Inicializa el sistema de recuperación de contexto.
        
        Args:
            max_tokens_ventana: Número máximo de tokens en la ventana inmediata
        """
        self.max_tokens_ventana = max_tokens_ventana
        self.contexto_vectorial = ContextoVectorial()
        self.historial_reciente = []
        logger.info("Sistema de Recuperación de Contexto inicializado")
    
    def extraer_informacion_util(self, mensaje: str) -> Dict[str, Any]:
        """
        Extrae información útil de un mensaje del usuario.
        
        Args:
            mensaje: Mensaje del usuario
            
        Returns:
            Diccionario con la información extraída
        """
        # Por ahora, una implementación simple
        return {
            "texto": mensaje,
            "timestamp": datetime.datetime.now().isoformat(),
            "tipo": self._detectar_tipo_mensaje(mensaje)
        }
    
    def guardar_mensaje(self, mensaje: str, autor: str) -> str:
        """
        Guarda un mensaje en el almacén vectorial.
        
        Args:
            mensaje: Texto del mensaje
            autor: Autor del mensaje (usuario o asistente)
            
        Returns:
            ID del documento guardado
        """
        tipo_doc = self._detectar_tipo_mensaje(mensaje)
        
        try:
            doc_id = self.contexto_vectorial.guardar_documento(
                contenido=mensaje,
                autor=autor,
                tipo_doc=tipo_doc
            )
            
            # Mantener historial reciente actualizado
            self.historial_reciente.append({
                "autor": autor,
                "mensaje": mensaje,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # Mantener historial reciente limitado
            if len(self.historial_reciente) > 10:
                self.historial_reciente = self.historial_reciente[-10:]
            
            logger.info(f"Mensaje guardado con ID: {doc_id}, Tipo: {tipo_doc}")
            return doc_id
        
        except Exception as e:
            logger.error(f"Error al guardar mensaje: {e}")
            return ""
    
    def recuperar_para_consulta(self, consulta: str, k: int = 5) -> str:
        """
        Recupera contexto relevante para una consulta.
        
        Args:
            consulta: Consulta del usuario
            k: Número de documentos a recuperar
            
        Returns:
            Bloque de contexto recuperado formateado
        """
        try:
            # Recuperar documentos relevantes
            documentos = self.contexto_vectorial.recuperar_contexto(consulta, k=k)
            
            # Formatear contexto recuperado
            contexto = self.contexto_vectorial.formatear_contexto_recuperado(documentos)
            
            logger.info(f"Recuperados {len(documentos)} documentos para consulta")
            return contexto
        
        except Exception as e:
            logger.error(f"Error al recuperar contexto: {e}")
            return "### Contexto recuperado\n\nNo se pudo recuperar contexto para esta consulta."
    
    def construir_prompt_completo(self, consulta: str) -> str:
        """
        Construye un prompt completo con la estructura fija especificada.
        
        Args:
            consulta: Consulta o input del usuario
            
        Returns:
            Prompt completo estructurado
        """
        # Estructura fija del prompt
        prompt = []
        
        # Sistema (rol y reglas)
        prompt.append("### Sistema\n")
        prompt.append("Eres Claude Code, trabajando como copiloto técnico del proyecto Calculadora de Turnos en Radiología.")
        prompt.append("Tu misión es asistir en el desarrollo y mantenimiento de esta aplicación médica.")
        prompt.append("Debes ser preciso, técnico y mantener la coherencia con el historial del proyecto.\n")
        
        # Contexto recuperado
        contexto = self.recuperar_para_consulta(consulta)
        prompt.append(contexto)
        
        # Historial reciente (últimos mensajes)
        prompt.append("### Historial reciente\n")
        for item in self.historial_reciente[-5:]:  # Últimos 5 mensajes
            autor = "Usuario" if item["autor"] == "usuario" else "Asistente"
            prompt.append(f"**{autor}**: {item['mensaje'][:300]}{'...' if len(item['mensaje']) > 300 else ''}\n")
        
        # Pregunta (input del usuario)
        prompt.append(f"### Pregunta\n{consulta}")
        
        return "\n".join(prompt)
    
    def guardar_dataset(self, df, nombre: str) -> str:
        """
        Guarda un perfil de dataset en el almacén vectorial.
        
        Args:
            df: DataFrame a procesar
            nombre: Nombre del dataset
            
        Returns:
            ID del documento guardado
        """
        try:
            doc_id = self.contexto_vectorial.procesar_dataset(df, nombre)
            logger.info(f"Dataset '{nombre}' procesado y guardado con ID: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Error al procesar dataset '{nombre}': {e}")
            return ""
    
    def realizar_mantenimiento(self) -> Dict[str, Any]:
        """
        Realiza mantenimiento del almacén vectorial.
        
        Returns:
            Estadísticas del mantenimiento
        """
        try:
            resultados = self.contexto_vectorial.mantenimiento_automatico()
            logger.info(f"Mantenimiento completado: {json.dumps(resultados)}")
            return resultados
        except Exception as e:
            logger.error(f"Error al realizar mantenimiento: {e}")
            return {"error": str(e)}
    
    def _detectar_tipo_mensaje(self, mensaje: str) -> str:
        """
        Detecta el tipo de mensaje basado en su contenido.
        
        Args:
            mensaje: Texto del mensaje
            
        Returns:
            Tipo de mensaje detectado
        """
        mensaje_lower = mensaje.lower()
        
        # Detección simple basada en palabras clave
        if "```" in mensaje and ("def " in mensaje or "class " in mensaje or "function" in mensaje):
            return "codigo"
        elif any(palabra in mensaje_lower for palabra in ["version", "changelog", "actualiz", "nuevo", "v0.", "v1."]):
            return "changelog"
        elif any(palabra in mensaje_lower for palabra in ["requisito", "feature", "funcionalidad", "implement"]):
            return "requisito"
        elif any(palabra in mensaje_lower for palabra in ["error", "bug", "falla", "crash", "exception"]):
            return "error"
        elif any(palabra in mensaje_lower for palabra in ["pregunta", "duda", "como", "qué", "cuál", "?"]):
            return "pregunta"
        else:
            return "conversacion"

# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia
    recuperador = RecuperacionContexto()
    
    # Probar guardar mensaje
    doc_id = recuperador.guardar_mensaje(
        mensaje="¿Cómo funciona la clasificación de TAC doble en el sistema?",
        autor="usuario"
    )
    
    print(f"Mensaje guardado con ID: {doc_id}")
    
    # Probar recuperación
    contexto = recuperador.recuperar_para_consulta("TAC doble clasificación")
    print(contexto)
    
    # Probar construcción de prompt completo
    prompt = recuperador.construir_prompt_completo("¿Cómo añadir soporte para TAC triple?")
    print("\nPROMPT COMPLETO:")
    print("-" * 50)
    print(prompt)