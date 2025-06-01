#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integración de Streamlit con el Sistema de Recuperación de Contexto
-------------------------------------------------------------------
Este módulo proporciona funciones para integrar el sistema de recuperación
de contexto con aplicaciones Streamlit.
"""

import json
import logging
import asyncio
import websockets
from typing import Dict, Any, Optional, Tuple
import streamlit as st

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("streamlit_integration.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("streamlit_integration")

class StreamlitIntegration:
    """
    Clase para integrar el sistema de recuperación de contexto con aplicaciones Streamlit.
    """
    
    def __init__(self, ws_url: str = "ws://localhost:9574/retriever"):
        """
        Inicializa la integración con Streamlit.
        
        Args:
            ws_url: URL del servidor WebSocket de recuperación de contexto
        """
        self.ws_url = ws_url
        
        # Inicializar variables de sesión de Streamlit si no existen
        if "conversacion" not in st.session_state:
            st.session_state.conversacion = []
        
        logger.info("Integración con Streamlit inicializada")
    
    async def _connect_websocket(self) -> websockets.WebSocketClientProtocol:
        """
        Conecta al servidor WebSocket.
        
        Returns:
            Conexión WebSocket
        """
        try:
            return await websockets.connect(self.ws_url)
        except Exception as e:
            logger.error(f"Error al conectar al servidor WebSocket: {e}")
            raise
    
    async def _send_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía una solicitud al servidor WebSocket.
        
        Args:
            data: Datos a enviar
            
        Returns:
            Respuesta del servidor
        """
        try:
            # Conectar al servidor WebSocket
            websocket = await self._connect_websocket()
            
            # Enviar datos
            await websocket.send(json.dumps(data))
            
            # Recibir respuesta
            response = await websocket.recv()
            
            # Cerrar conexión
            await websocket.close()
            
            # Parsear respuesta JSON
            return json.loads(response)
        
        except Exception as e:
            logger.error(f"Error al enviar solicitud WebSocket: {e}")
            return {"error": str(e), "status": "error"}
    
    def recuperar_contexto(self, query: str, k: int = 5) -> str:
        """
        Recupera contexto relevante para una consulta.
        
        Args:
            query: Consulta del usuario
            k: Número de documentos a recuperar
            
        Returns:
            Bloque de contexto recuperado
        """
        try:
            # Preparar datos de la solicitud
            data = {
                "action": "retrieve",
                "query": query,
                "k": k
            }
            
            # Ejecutar solicitud de forma asíncrona
            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(self._send_request(data))
            loop.close()
            
            # Verificar respuesta
            if response.get("status") == "success":
                return response.get("context", "")
            else:
                logger.error(f"Error al recuperar contexto: {response.get('error')}")
                return f"Error al recuperar contexto: {response.get('error')}"
        
        except Exception as e:
            logger.error(f"Error al recuperar contexto: {e}")
            return f"Error al recuperar contexto: {str(e)}"
    
    def guardar_mensaje(self, mensaje: str, autor: str) -> str:
        """
        Guarda un mensaje en el almacén vectorial.
        
        Args:
            mensaje: Texto del mensaje
            autor: Autor del mensaje (usuario o asistente)
            
        Returns:
            ID del documento guardado o mensaje de error
        """
        try:
            # Preparar datos de la solicitud
            data = {
                "action": "store",
                "message": mensaje,
                "author": autor
            }
            
            # Ejecutar solicitud de forma asíncrona
            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(self._send_request(data))
            loop.close()
            
            # Verificar respuesta
            if response.get("status") == "success":
                return response.get("doc_id", "")
            else:
                logger.error(f"Error al guardar mensaje: {response.get('error')}")
                return f"Error: {response.get('error')}"
        
        except Exception as e:
            logger.error(f"Error al guardar mensaje: {e}")
            return f"Error: {str(e)}"
    
    def construir_prompt(self, query: str) -> str:
        """
        Construye un prompt completo para la consulta.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Prompt completo
        """
        try:
            # Preparar datos de la solicitud
            data = {
                "action": "build_prompt",
                "query": query
            }
            
            # Ejecutar solicitud de forma asíncrona
            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(self._send_request(data))
            loop.close()
            
            # Verificar respuesta
            if response.get("status") == "success":
                return response.get("prompt", "")
            else:
                logger.error(f"Error al construir prompt: {response.get('error')}")
                return f"Error al construir prompt: {response.get('error')}"
        
        except Exception as e:
            logger.error(f"Error al construir prompt: {e}")
            return f"Error al construir prompt: {str(e)}"
    
    def realizar_mantenimiento(self) -> Dict[str, Any]:
        """
        Realiza mantenimiento del almacén vectorial.
        
        Returns:
            Estadísticas del mantenimiento
        """
        try:
            # Preparar datos de la solicitud
            data = {
                "action": "maintenance",
                "query": "mantenimiento"  # Campo requerido aunque no se use
            }
            
            # Ejecutar solicitud de forma asíncrona
            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(self._send_request(data))
            loop.close()
            
            # Verificar respuesta
            if response.get("status") == "success":
                return response.get("results", {})
            else:
                logger.error(f"Error al realizar mantenimiento: {response.get('error')}")
                return {"error": response.get('error')}
        
        except Exception as e:
            logger.error(f"Error al realizar mantenimiento: {e}")
            return {"error": str(e)}
    
    def mostrar_chat_ui(self, placeholder=None):
        """
        Muestra una interfaz de chat para interactuar con el asistente.
        
        Args:
            placeholder: Placeholder de Streamlit para mostrar el chat
        """
        # Contenedor para el historial de chat
        chat_container = placeholder if placeholder else st.container()
        
        with chat_container:
            # Mostrar historial de mensajes
            for mensaje in st.session_state.conversacion:
                if mensaje["autor"] == "usuario":
                    st.chat_message("user").write(mensaje["texto"])
                else:
                    st.chat_message("assistant").write(mensaje["texto"])
        
        # Campo de entrada para el usuario
        prompt = st.chat_input("Escribe tu mensaje aquí...")
        
        if prompt:
            # Mostrar mensaje del usuario
            st.chat_message("user").write(prompt)
            
            # Añadir mensaje del usuario al historial
            st.session_state.conversacion.append({
                "autor": "usuario",
                "texto": prompt
            })
            
            # Guardar mensaje del usuario
            self.guardar_mensaje(prompt, "usuario")
            
            # Construir prompt completo para Claude
            prompt_completo = self.construir_prompt(prompt)
            
            # Aquí se conectaría con Claude (implementar según tu integración específica)
            respuesta = "Por implementar: Aquí va la respuesta de Claude basada en el prompt completo."
            
            # Mostrar respuesta del asistente
            st.chat_message("assistant").write(respuesta)
            
            # Añadir respuesta al historial
            st.session_state.conversacion.append({
                "autor": "asistente",
                "texto": respuesta
            })
            
            # Guardar respuesta del asistente
            self.guardar_mensaje(respuesta, "asistente")
    
    def mostrar_panel_admin(self):
        """
        Muestra un panel de administración para el sistema de recuperación de contexto.
        """
        st.header("Panel de Administración - Sistema de Recuperación")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Mantenimiento")
            
            if st.button("Realizar mantenimiento"):
                with st.spinner("Realizando mantenimiento..."):
                    resultados = self.realizar_mantenimiento()
                    
                    if "error" in resultados:
                        st.error(f"Error al realizar mantenimiento: {resultados['error']}")
                    else:
                        st.success("Mantenimiento completado correctamente")
                        st.json(resultados)
        
        with col2:
            st.subheader("Prueba de recuperación")
            
            query = st.text_input("Consulta para recuperar contexto:")
            k = st.slider("Número de documentos a recuperar:", 1, 10, 5)
            
            if st.button("Recuperar"):
                with st.spinner("Recuperando contexto..."):
                    contexto = self.recuperar_contexto(query, k)
                    st.markdown(contexto)

# Ejemplo de uso en una aplicación Streamlit
def crear_pagina_demo():
    """
    Crea una página de demostración de la integración con Streamlit.
    """
    st.title("Demostración de Recuperación de Contexto")
    
    # Crear instancia de integración
    integracion = StreamlitIntegration()
    
    # Crear tabs
    tab_chat, tab_admin = st.tabs(["Chat", "Administración"])
    
    with tab_chat:
        integracion.mostrar_chat_ui()
    
    with tab_admin:
        integracion.mostrar_panel_admin()

# Si se ejecuta como script principal
if __name__ == "__main__":
    # Mostrar la página de demostración
    crear_pagina_demo()