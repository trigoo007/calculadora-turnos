#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demostración del Sistema Integrado de Calculadora de Turnos con Contexto
------------------------------------------------------------------------
Script de demostración que muestra las capacidades del sistema integrado.
"""

import os
import sys
import pandas as pd
import time
import argparse
import threading
import queue
from typing import Dict, List, Any, Optional

try:
    # Importar componentes principales
    from integracion_contexto_calculadora import IntegracionContextoCalculadora
    import config
    
    # Configurar logger
    logger = config.obtener_logger(__name__)
except Exception as e:
    print(f"Error al importar componentes necesarios: {e}")
    print("Asegúrese de ejecutar este script desde el directorio raíz del proyecto")
    sys.exit(1)

# Cola para gestionar outputs en threads separados
output_queue = queue.Queue()

def iniciar_servicios():
    """
    Inicia los servicios necesarios para la demostración.
    
    Returns:
        bool: True si todos los servicios se iniciaron correctamente
    """
    servicios_ok = True
    
    print("Iniciando servicios...")
    
    # Asegurar que los directorios necesarios existen
    os.makedirs(os.path.expanduser("~/vectorstore"), exist_ok=True)
    os.makedirs(os.path.join(config.BASE_DIR, "conocimiento"), exist_ok=True)
    
    # Verificar si el servidor WebSocket está en ejecución
    try:
        import websockets
        import asyncio
        import json
        
        async def verificar_websocket():
            try:
                uri = "ws://localhost:9574/retriever"
                async with websockets.connect(uri, timeout=2) as websocket:
                    await websocket.send(json.dumps({"query": "test", "action": "retrieve"}))
                    await asyncio.wait_for(websocket.recv(), timeout=2)
                return True
            except:
                return False
        
        if not asyncio.run(verificar_websocket()):
            print("El servidor WebSocket de contexto no está en ejecución.")
            print("Iniciando servidor WebSocket en segundo plano...")
            
            # Iniciar primero el recuperador de contexto para probar que funcione
            try:
                from recuperacion_contexto import RecuperacionContexto
                from contexto_vectorial import ContextoVectorial
                
                # Inicializar para probar que funcionan
                contexto = ContextoVectorial()
                recuperador = RecuperacionContexto()
                
                # Guardar un documento inicial de prueba
                doc_id = contexto.guardar_documento(
                    contenido="Este es un documento de prueba para verificar el sistema.",
                    autor="sistema",
                    tipo_doc="prueba"
                )
                print(f"✅ Sistema de contexto vectorial preparado (documento {doc_id[:8]}...)")
            except Exception as e:
                print(f"⚠️  Error al inicializar el sistema de contexto: {e}")
                print("La recuperación de contexto puede no funcionar correctamente.")
                servicios_ok = False
                # Continuar de todos modos...
            
            # Iniciar servidor WebSocket en segundo plano
            try:
                from websocket_server import main as ws_main
                
                ws_thread = threading.Thread(target=lambda: asyncio.run(ws_main()))
                ws_thread.daemon = True
                ws_thread.start()
                
                # Esperar a que el servidor se inicie
                time.sleep(2)
                
                # Verificar de nuevo
                if not asyncio.run(verificar_websocket()):
                    print("⚠️  No se pudo iniciar el servidor WebSocket. La recuperación de contexto puede no funcionar correctamente.")
                    servicios_ok = False
                else:
                    print("✅ Servidor WebSocket iniciado correctamente.")
            except Exception as e:
                print(f"⚠️  Error al iniciar el servidor WebSocket: {e}")
                servicios_ok = False
    except ImportError as e:
        print(f"⚠️  No se pudo verificar el servidor WebSocket: {e}")
        print("La recuperación de contexto puede no funcionar correctamente.")
        servicios_ok = False
    
    # Verificar si Ollama está disponible
    try:
        import requests
        response = requests.get("http://localhost:15763/api/tags", timeout=2)
        if response.status_code == 200:
            # Verificar si phi está disponible
            modelos = response.json().get("models", [])
            phi_disponible = any(m.get("name", "").startswith("phi") for m in modelos)
            
            if phi_disponible:
                print("✅ Ollama está en ejecución y el modelo phi está disponible.")
            else:
                print("⚠️  Ollama está en ejecución pero el modelo phi no está disponible.")
                print("   Puede descargar el modelo con: ollama pull phi")
                servicios_ok = False
        else:
            print("⚠️  No se pudo comunicar con Ollama. El asistente phi-2 no funcionará correctamente.")
            servicios_ok = False
    except:
        print("⚠️  Ollama no está en ejecución o no está accesible. El asistente phi-2 no funcionará correctamente.")
        servicios_ok = False
    
    return servicios_ok

def procesar_archivo(integracion, ruta_archivo, directorio_salida, nombre_doctor):
    """
    Procesa un archivo CSV y almacena los resultados en el contexto.
    
    Args:
        integracion: Instancia de IntegracionContextoCalculadora
        ruta_archivo: Ruta al archivo CSV a procesar
        directorio_salida: Directorio donde guardar los resultados
        nombre_doctor: Nombre del doctor para el reporte
    """
    if not os.path.exists(ruta_archivo):
        print(f"Error: El archivo {ruta_archivo} no existe.")
        return
    
    print(f"Procesando archivo {os.path.basename(ruta_archivo)}...")
    resultado = integracion.procesar_y_almacenar_csv(ruta_archivo, directorio_salida, nombre_doctor)
    
    if "error" in resultado:
        print(f"❌ Error al procesar archivo: {resultado['error']}")
        return
    
    print(f"✅ Archivo procesado correctamente.")
    
    # Mostrar resultados
    eco = resultado['resultado_economico']
    print("\n📊 RESUMEN DE RESULTADOS:")
    print(f"Horas trabajadas: {eco['horas_trabajadas']}")
    print(f"RX: {eco['rx_count']} (${eco['rx_total']:,})")
    print(f"TAC: {eco['tac_count']} (${eco['tac_total']:,})")
    print(f"TAC doble: {eco['tac_doble_count']} (${eco['tac_doble_total']:,})")
    print(f"TAC triple: {eco['tac_triple_count']} (${eco['tac_triple_total']:,})")
    print(f"Honorarios por horas: ${eco['honorarios_hora']:,}")
    print(f"TOTAL: ${eco['total']:,}")
    
    print("\n📝 ARCHIVOS GENERADOS:")
    for nombre, ruta in resultado['rutas_excel'].items():
        print(f"- {nombre}: {os.path.basename(ruta)}")
    
    print("\n📧 CONTENIDO DEL CORREO:")
    print(f"Asunto: {resultado['correo']['asunto']}")
    print(f"Cuerpo:\n{resultado['correo']['cuerpo']}")

def consultar_con_contexto(integracion, consulta):
    """
    Realiza una consulta en lenguaje natural al asistente con contexto.
    
    Args:
        integracion: Instancia de IntegracionContextoCalculadora
        consulta: Consulta en lenguaje natural
    """
    print(f"💬 Consultando: {consulta}")
    print("Recuperando contexto y generando respuesta...")
    
    respuesta = integracion.consulta_con_contexto(consulta)
    
    print(f"🤖 Respuesta: {respuesta}")

def consultar_sql_con_contexto(integracion, consulta):
    """
    Realiza una consulta SQL en lenguaje natural al asistente con contexto.
    
    Args:
        integracion: Instancia de IntegracionContextoCalculadora
        consulta: Consulta en lenguaje natural
    """
    print(f"🔍 Consultando SQL: {consulta}")
    print("Recuperando contexto y generando consulta SQL...")
    
    exito, resultado = integracion.consulta_sql_con_contexto(consulta)
    
    if exito and isinstance(resultado, pd.DataFrame):
        print(f"✅ Consulta SQL exitosa ({len(resultado)} resultados):")
        print("\nResultados:")
        if len(resultado) > 10:
            print(resultado.head(10).to_string())
            print(f"... y {len(resultado) - 10} filas más")
        else:
            print(resultado.to_string())
    else:
        print(f"❌ Error en consulta SQL: {resultado}")

def modo_interactivo(integracion):
    """
    Ejecuta un modo interactivo para consultas al asistente con contexto.
    
    Args:
        integracion: Instancia de IntegracionContextoCalculadora
    """
    print("\n🤖 MODO INTERACTIVO - Asistente con Contexto Histórico")
    print("Escriba su consulta o comando:")
    print("- Para salir, escriba 'exit' o 'quit'")
    print("- Para consulta SQL, escriba 'sql:' seguido de su consulta")
    print("- Para procesar un archivo, escriba 'procesar:' seguido de la ruta")
    
    while True:
        try:
            # Solicitar entrada
            entrada = input("\n> ")
            
            # Verificar comandos de salida
            if entrada.lower() in ["exit", "quit", "salir"]:
                print("Saliendo del modo interactivo...")
                break
            
            # Procesar comandos especiales
            if entrada.lower().startswith("sql:"):
                consulta = entrada[4:].strip()
                consultar_sql_con_contexto(integracion, consulta)
                
            elif entrada.lower().startswith("procesar:"):
                ruta = entrada[9:].strip()
                directorio_salida = os.path.dirname(ruta) if os.path.dirname(ruta) else "."
                nombre_doctor = input("Nombre del doctor (o Enter para 'Cikutovic'): ") or "Cikutovic"
                procesar_archivo(integracion, ruta, directorio_salida, nombre_doctor)
                
            else:
                # Consulta normal
                consultar_con_contexto(integracion, entrada)
                
        except KeyboardInterrupt:
            print("\nOperación cancelada.")
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Función principal para la demostración."""
    parser = argparse.ArgumentParser(description='Demostración del Sistema Integrado de Calculadora de Turnos con Contexto')
    
    # Argumentos generales
    parser.add_argument('--proceso', help='Archivo CSV a procesar', default='')
    parser.add_argument('--salida', help='Directorio de salida para resultados', default='')
    parser.add_argument('--doctor', help='Nombre del doctor para el reporte', default='Cikutovic')
    
    # Argumentos para consultas
    parser.add_argument('--consulta', help='Consulta en lenguaje natural', default='')
    parser.add_argument('--sql', help='Consulta SQL en lenguaje natural', default='')
    
    # Modo interactivo
    parser.add_argument('--interactivo', action='store_true', help='Iniciar modo interactivo para consultas')
    
    args = parser.parse_args()
    
    # Iniciar servicios necesarios
    servicios_ok = iniciar_servicios()
    if not servicios_ok:
        print("\n⚠️  Algunos servicios no están disponibles. La funcionalidad puede estar limitada.")
        try:
            respuesta = input("¿Desea continuar de todos modos? (s/n): ")
            if respuesta.lower() != 's':
                print("Saliendo...")
                return
        except EOFError:
            print("Entrada interrumpida. Continuando en modo limitado...")
            # Continuar de todos modos sin preguntar
    
    # Crear instancia de integración
    integracion = IntegracionContextoCalculadora()
    
    # Verificar si la integración se creó correctamente
    if not integracion.calculadora:
        print("⚠️  No se pudo inicializar la calculadora. La funcionalidad estará limitada.")
    if not integracion.asistente:
        print("⚠️  No se pudo inicializar el asistente phi-2. La funcionalidad estará limitada.")
    
    # Procesar archivo si se especificó
    if args.proceso:
        directorio_salida = args.salida if args.salida else os.path.dirname(args.proceso)
        procesar_archivo(integracion, args.proceso, directorio_salida, args.doctor)
    
    # Realizar consulta si se especificó
    if args.consulta:
        consultar_con_contexto(integracion, args.consulta)
    
    # Realizar consulta SQL si se especificó
    if args.sql:
        consultar_sql_con_contexto(integracion, args.sql)
    
    # Modo simple sin servicios
    if not servicios_ok:
        print("\n🔧 MODO SIMPLE - Funcionalidad limitada")
        print("Algunas características no estarán disponibles debido a servicios faltantes.")
        print("Puede procesar archivos CSV pero el sistema de contexto y asistente no funcionarán.")
        
        # Preguntar al usuario qué desea hacer
        print("\nOpciones disponibles:")
        print("1. Procesar un archivo CSV")
        print("2. Mostrar información sobre el sistema")
        print("3. Salir")
        
        try:
            opcion = input("\nSeleccione una opción (1-3): ")
            
            if opcion == "1":
                try:
                    ruta = input("\nRuta del archivo CSV a procesar: ")
                    directorio_salida = input("Directorio de salida (o Enter para usar el mismo directorio): ") or os.path.dirname(ruta)
                    nombre_doctor = input("Nombre del doctor (o Enter para 'Cikutovic'): ") or "Cikutovic"
                    if os.path.exists(ruta):
                        procesar_archivo(integracion, ruta, directorio_salida, nombre_doctor)
                    else:
                        print(f"El archivo {ruta} no existe.")
                except EOFError:
                    print("Entrada interrumpida.")
            elif opcion == "2":
                print("\nInformación del sistema:")
                print(f"- Versión del sistema: {config.VERSION}")
                print(f"- Directorio base: {config.BASE_DIR}")
                print(f"- Calculadora disponible: {'Sí' if integracion.calculadora else 'No'}")
                print(f"- Asistente phi-2 disponible: {'Sí' if integracion.asistente else 'No'}")
                print(f"- Sistema de contexto disponible: {'Sí' if integracion.recuperacion_contexto else 'No'}")
            else:
                print("Saliendo...")
        except EOFError:
            # Opción por defecto si no se puede leer la entrada
            print("\nMostrando información del sistema por defecto:")
            print(f"- Versión del sistema: {config.VERSION}")
            print(f"- Directorio base: {config.BASE_DIR}")
            print(f"- Calculadora disponible: {'Sí' if integracion.calculadora else 'No'}")
            print(f"- Asistente phi-2 disponible: {'Sí' if integracion.asistente else 'No'}")
            print(f"- Sistema de contexto disponible: {'Sí' if integracion.recuperacion_contexto else 'No'}")
    # Iniciar modo interactivo si se solicitó o si no se especificó ninguna acción
    elif args.interactivo or not (args.proceso or args.consulta or args.sql):
        modo_interactivo(integracion)
    
    print("\n✅ Demostración completada.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        # Mostrar información de depuración en modo debug
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()