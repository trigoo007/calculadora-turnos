#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor de rendimiento para la Calculadora de Turnos
---------------------------------------------------
Proporciona funciones para monitorear el rendimiento de la aplicación
y diagnóstico de problemas.
"""

import os
import time
import json
import platform
import psutil
from datetime import datetime
from functools import wraps
from typing import Dict, List, Any, Callable, Optional

# Importar configuración
import config

# Obtener logger
logger = config.obtener_logger(__name__)

# Directorio para métricas de rendimiento
METRICAS_DIR = os.path.join(config.LOGS_DIR, "metricas")
os.makedirs(METRICAS_DIR, exist_ok=True)

# Diccionario para almacenar métricas temporales
_metricas_tiempo = {}
_operaciones_contabilizadas = {}

class Temporizador:
    """Clase para medir el tiempo de ejecución de funciones o bloques de código."""
    
    def __init__(self, nombre: str):
        """
        Inicializa un nuevo temporizador.
        
        Args:
            nombre: Nombre identificativo del temporizador
        """
        self.nombre = nombre
        self.inicio = None
        self.fin = None
    
    def __enter__(self):
        """Inicia el temporizador al entrar en un bloque with."""
        self.inicio = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Detiene el temporizador al salir de un bloque with."""
        self.fin = time.time()
        duracion = self.fin - self.inicio
        
        # Registrar métrica
        if self.nombre not in _metricas_tiempo:
            _metricas_tiempo[self.nombre] = []
        
        _metricas_tiempo[self.nombre].append(duracion)
        
        # Actualizar contadores
        if self.nombre not in _operaciones_contabilizadas:
            _operaciones_contabilizadas[self.nombre] = 0
        
        _operaciones_contabilizadas[self.nombre] += 1
        
        # Loguear tiempo de ejecución
        logger.debug(f"Tiempo de ejecución de {self.nombre}: {duracion:.4f} segundos")

def medir_tiempo(func: Callable) -> Callable:
    """
    Decorador para medir el tiempo de ejecución de una función.
    
    Args:
        func: Función a medir
        
    Returns:
        Callable: Función decorada
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        nombre_funcion = func.__name__
        with Temporizador(nombre_funcion):
            return func(*args, **kwargs)
    return wrapper

def obtener_metricas_rendimiento() -> Dict[str, Any]:
    """
    Obtiene métricas de rendimiento del sistema.
    
    Returns:
        Dict[str, Any]: Métricas de rendimiento
    """
    # Información del sistema
    info_sistema = {
        "sistema_operativo": platform.system(),
        "version_os": platform.version(),
        "arquitectura": platform.machine(),
        "python_version": platform.python_version(),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Información de CPU
    info_cpu = {
        "nucleos_fisicos": psutil.cpu_count(logical=False),
        "nucleos_logicos": psutil.cpu_count(logical=True),
        "uso_cpu": psutil.cpu_percent(interval=1)
    }
    
    # Información de memoria
    mem = psutil.virtual_memory()
    info_memoria = {
        "total": mem.total / (1024 ** 3),  # GB
        "disponible": mem.available / (1024 ** 3),  # GB
        "usado": mem.used / (1024 ** 3),  # GB
        "porcentaje_uso": mem.percent
    }
    
    # Información de disco
    disco = psutil.disk_usage('/')
    info_disco = {
        "total": disco.total / (1024 ** 3),  # GB
        "usado": disco.used / (1024 ** 3),  # GB
        "libre": disco.free / (1024 ** 3),  # GB
        "porcentaje_uso": disco.percent
    }
    
    # Proceso actual
    proceso = psutil.Process(os.getpid())
    info_proceso = {
        "memoria_uso": proceso.memory_info().rss / (1024 ** 2),  # MB
        "tiempo_cpu": proceso.cpu_times().user,
        "hilos": proceso.num_threads()
    }
    
    # Métricas de tiempo
    metricas_tiempo = {}
    for nombre, tiempos in _metricas_tiempo.items():
        if tiempos:
            metricas_tiempo[nombre] = {
                "promedio": sum(tiempos) / len(tiempos),
                "min": min(tiempos),
                "max": max(tiempos),
                "total": sum(tiempos),
                "conteo": len(tiempos)
            }
    
    return {
        "sistema": info_sistema,
        "cpu": info_cpu,
        "memoria": info_memoria,
        "disco": info_disco,
        "proceso": info_proceso,
        "tiempos": metricas_tiempo,
        "operaciones": _operaciones_contabilizadas
    }

def guardar_metricas_rendimiento(etiqueta: Optional[str] = None) -> str:
    """
    Guarda las métricas de rendimiento en un archivo JSON.
    
    Args:
        etiqueta: Etiqueta opcional para identificar el archivo
        
    Returns:
        str: Ruta al archivo de métricas
    """
    metricas = obtener_metricas_rendimiento()
    
    # Nombre de archivo con timestamp y etiqueta opcional
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"metricas_{timestamp}"
    
    if etiqueta:
        nombre_archivo += f"_{etiqueta}"
    
    nombre_archivo += ".json"
    ruta_archivo = os.path.join(METRICAS_DIR, nombre_archivo)
    
    # Guardar métricas
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        json.dump(metricas, f, indent=4)
    
    logger.info(f"Métricas de rendimiento guardadas en {ruta_archivo}")
    return ruta_archivo

def diagnostico_sistema() -> Dict[str, Any]:
    """
    Realiza un diagnóstico completo del sistema y devuelve recomendaciones.
    
    Returns:
        Dict[str, Any]: Diagnóstico del sistema y recomendaciones
    """
    metricas = obtener_metricas_rendimiento()
    recomendaciones = []
    advertencias = []
    
    # Comprobar CPU
    uso_cpu = metricas["cpu"]["uso_cpu"]
    if uso_cpu > 90:
        advertencias.append(f"Uso de CPU muy alto ({uso_cpu}%). El rendimiento puede verse afectado.")
    elif uso_cpu > 70:
        recomendaciones.append(f"Uso de CPU elevado ({uso_cpu}%). Considere cerrar aplicaciones innecesarias.")
    
    # Comprobar memoria
    memoria_disponible = metricas["memoria"]["disponible"]
    porcentaje_uso_memoria = metricas["memoria"]["porcentaje_uso"]
    
    if porcentaje_uso_memoria > 90:
        advertencias.append(f"Uso de memoria muy alto ({porcentaje_uso_memoria}%). Posible riesgo de swapping.")
    elif porcentaje_uso_memoria > 80:
        recomendaciones.append(f"Uso de memoria elevado ({porcentaje_uso_memoria}%). Considere liberar memoria.")
    
    if memoria_disponible < 1:  # Menos de 1 GB
        advertencias.append(f"Memoria disponible baja ({memoria_disponible:.2f} GB). El rendimiento puede verse afectado.")
    
    # Comprobar disco
    espacio_libre = metricas["disco"]["libre"]
    porcentaje_uso_disco = metricas["disco"]["porcentaje_uso"]
    
    if porcentaje_uso_disco > 90:
        advertencias.append(f"Espacio en disco casi agotado ({porcentaje_uso_disco}%). Libere espacio.")
    elif porcentaje_uso_disco > 80:
        recomendaciones.append(f"Espacio en disco alto ({porcentaje_uso_disco}%). Considere liberar espacio.")
    
    if espacio_libre < 5:  # Menos de 5 GB
        advertencias.append(f"Espacio libre en disco bajo ({espacio_libre:.2f} GB). Puede afectar al almacenamiento de resultados.")
    
    # Proceso actual
    memoria_proceso = metricas["proceso"]["memoria_uso"]
    
    if memoria_proceso > 500:  # Más de 500 MB
        recomendaciones.append(f"La aplicación está utilizando mucha memoria ({memoria_proceso:.2f} MB). Considere reiniciarla periódicamente.")
    
    # Verificar rendimiento de operaciones críticas
    operaciones_lentas = []
    if "tiempos" in metricas:
        for operacion, datos in metricas["tiempos"].items():
            if "promedio" in datos and datos["promedio"] > 1.0:  # Más de 1 segundo
                operaciones_lentas.append(f"{operacion}: {datos['promedio']:.2f}s")
    
    if operaciones_lentas:
        recomendaciones.append(f"Operaciones con rendimiento bajo: {', '.join(operaciones_lentas)}")
    
    return {
        "metricas": metricas,
        "estado": "crítico" if advertencias else "alerta" if recomendaciones else "normal",
        "advertencias": advertencias,
        "recomendaciones": recomendaciones
    }

# Funciones para acceder al monitor desde otros módulos
def iniciar_temporizador(nombre: str) -> Temporizador:
    """
    Inicia un temporizador para medir el tiempo de ejecución.
    
    Args:
        nombre: Nombre identificativo del temporizador
        
    Returns:
        Temporizador: Objeto temporizador iniciado
    """
    return Temporizador(nombre)

def reiniciar_metricas():
    """Reinicia todas las métricas acumuladas."""
    global _metricas_tiempo, _operaciones_contabilizadas
    _metricas_tiempo = {}
    _operaciones_contabilizadas = {}
    logger.info("Métricas de rendimiento reiniciadas")

# Función principal
def main():
    """Función principal para pruebas del módulo de monitoreo."""
    print("Módulo de monitoreo de rendimiento")
    print("----------------------------------")
    
    # Simular algunas operaciones
    print("Simulando operaciones...")
    
    for i in range(5):
        with Temporizador(f"operacion_test_{i}"):
            # Simular alguna operación
            time.sleep(0.1 * (i + 1))
    
    # Función decorada con el temporizador
    @medir_tiempo
    def operacion_lenta():
        time.sleep(0.5)
        return "Operación completada"
    
    for i in range(3):
        operacion_lenta()
    
    # Obtener y mostrar métricas
    print("\nMétricas de rendimiento:")
    metricas = obtener_metricas_rendimiento()
    
    # Mostrar información del sistema
    print(f"\nSistema: {metricas['sistema']['sistema_operativo']} {metricas['sistema']['version_os']}")
    print(f"CPU: {metricas['cpu']['uso_cpu']}% (Núcleos: {metricas['cpu']['nucleos_fisicos']} físicos, {metricas['cpu']['nucleos_logicos']} lógicos)")
    print(f"Memoria: {metricas['memoria']['usado']:.2f} GB / {metricas['memoria']['total']:.2f} GB ({metricas['memoria']['porcentaje_uso']}%)")
    
    # Mostrar métricas de tiempo
    print("\nTiempos de ejecución:")
    for nombre, datos in metricas["tiempos"].items():
        print(f"- {nombre}: {datos['promedio']:.4f}s promedio, {datos['min']:.4f}s mínimo, {datos['max']:.4f}s máximo")
    
    # Guardar métricas
    ruta_archivo = guardar_metricas_rendimiento("test")
    print(f"\nMétricas guardadas en {ruta_archivo}")
    
    # Diagnóstico
    print("\nDiagnóstico del sistema:")
    diagnostico = diagnostico_sistema()
    
    print(f"Estado: {diagnostico['estado']}")
    
    if diagnostico["advertencias"]:
        print("\nAdvertencias:")
        for adv in diagnostico["advertencias"]:
            print(f"- {adv}")
    
    if diagnostico["recomendaciones"]:
        print("\nRecomendaciones:")
        for rec in diagnostico["recomendaciones"]:
            print(f"- {rec}")

if __name__ == "__main__":
    main()