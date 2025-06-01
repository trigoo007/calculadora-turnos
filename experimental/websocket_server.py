#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor WebSocket para Recuperación de Contexto
------------------------------------------------
Este módulo implementa un servidor WebSocket que expone el sistema de recuperación
de contexto para su uso desde aplicaciones Streamlit.
"""

import json
import asyncio
import logging
import argparse
import websockets
from typing import Dict, Any
from recuperacion_contexto import RecuperacionContexto

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("websocket_server.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("websocket_server")

# Crear instancia global del recuperador de contexto
recuperador = None  # Se inicializará en main() para manejar errores

async def handler(websocket):
    """
    Manejador de conexiones WebSocket.
    
    Args:
        websocket: Objeto de conexión WebSocket
    """
    try:
        async for message in websocket:
            logger.info(f"Mensaje recibido: {message[:100]}...")
            
            try:
                # Parsear mensaje JSON
                data = json.loads(message)
                
                # Verificar campos requeridos
                if "query" not in data:
                    await websocket.send(json.dumps({
                        "error": "El campo 'query' es requerido"
                    }))
                    continue
                
                # Procesar según la acción solicitada
                action = data.get("action", "retrieve")
                
                if action == "retrieve":
                    # Recuperar contexto
                    query = data["query"]
                    k = data.get("k", 5)
                    
                    # Obtener contexto
                    contexto = recuperador.recuperar_para_consulta(query, k=k)
                    
                    # Enviar respuesta
                    await websocket.send(json.dumps({
                        "context": contexto,
                        "status": "success"
                    }))
                
                elif action == "store":
                    # Guardar mensaje
                    mensaje = data.get("message", data["query"])
                    autor = data.get("author", "usuario")
                    
                    # Guardar mensaje
                    doc_id = recuperador.guardar_mensaje(mensaje, autor)
                    
                    # Enviar respuesta
                    await websocket.send(json.dumps({
                        "doc_id": doc_id,
                        "status": "success"
                    }))
                    
                elif action == "build_prompt":
                    # Construir prompt completo
                    query = data["query"]
                    
                    # Construir prompt
                    prompt = recuperador.construir_prompt_completo(query)
                    
                    # Enviar respuesta
                    await websocket.send(json.dumps({
                        "prompt": prompt,
                        "status": "success"
                    }))
                
                elif action == "maintenance":
                    # Realizar mantenimiento
                    resultados = recuperador.realizar_mantenimiento()
                    
                    # Enviar respuesta
                    await websocket.send(json.dumps({
                        "results": resultados,
                        "status": "success"
                    }))
                
                else:
                    await websocket.send(json.dumps({
                        "error": f"Acción no reconocida: {action}",
                        "status": "error"
                    }))
            
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "error": "Formato JSON inválido",
                    "status": "error"
                }))
            
            except Exception as e:
                logger.error(f"Error al procesar mensaje: {str(e)}")
                await websocket.send(json.dumps({
                    "error": str(e),
                    "status": "error"
                }))
    
    except websockets.exceptions.ConnectionClosedError:
        logger.info("Conexión cerrada por el cliente")
    
    except Exception as e:
        logger.error(f"Error en handler: {str(e)}")

async def main(host: str = "localhost", port: int = 9574):
    """
    Función principal que inicia el servidor WebSocket.
    
    Args:
        host: Host donde escuchar conexiones
        port: Puerto donde escuchar conexiones
    """
    # Inicializar servidor WebSocket
    logger.info(f"Iniciando servidor WebSocket en {host}:{port}")
    
    try:
        # Inicializar recuperador de contexto para verificar su funcionamiento
        global recuperador
        if recuperador is None:
            recuperador = RecuperacionContexto()
        
        # Iniciar servidor
        async with websockets.serve(handler, host, port):
            logger.info(f"Servidor WebSocket iniciado en ws://{host}:{port}/retriever")
            await asyncio.Future()  # Ejecutar indefinidamente
    except Exception as e:
        logger.error(f"Error al iniciar servidor WebSocket: {e}")
        print(f"Error al iniciar servidor WebSocket: {e}")
        print("El servidor WebSocket no está disponible. Las funciones de recuperación de contexto no funcionarán correctamente.")

if __name__ == "__main__":
    # Parsear argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Servidor WebSocket para Recuperación de Contexto")
    parser.add_argument("--host", default="localhost", help="Host donde escuchar conexiones")
    parser.add_argument("--port", type=int, default=8009, help="Puerto donde escuchar conexiones")
    args = parser.parse_args()
    
    # Iniciar servidor
    asyncio.run(main(host=args.host, port=args.port))