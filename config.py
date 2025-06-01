#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de configuración centralizada para la Calculadora de Turnos
-----------------------------------------------------------------
Proporciona acceso a toda la configuración de la aplicación en un único punto.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Versión actual de la aplicación
VERSION = "0.7.1"

# Directorio base y rutas principales
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONOCIMIENTO_DIR = os.path.join(BASE_DIR, "conocimiento")
CSV_DIR = os.path.join(BASE_DIR, "csv")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
RECURSOS_DIR = os.path.join(BASE_DIR, "recursos")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Asegurar que los directorios existan
for directory in [CONOCIMIENTO_DIR, CSV_DIR, TEMP_DIR, RECURSOS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Archivo de base de datos principal
DB_FILE = os.path.join(CONOCIMIENTO_DIR, "conocimiento.db")

# Archivo de configuración JSON (cargado si existe)
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# Tarifas por defecto
DEFAULT_TARIFAS = {
    "TARIFA_HORA": 55000,
    "TARIFA_RX": 5300,
    "TARIFA_TAC": 42400,
    "TARIFA_TAC_DOBLE": 84800,
    "TARIFA_TAC_TRIPLE": 127200
}

# Configuración de horarios de turno por defecto
DEFAULT_HORARIOS_TURNO = {
    "LUNES_JUEVES": {"inicio": "18:00", "fin": "08:00", "duracion": 14},
    "VIERNES": {"inicio": "18:00", "fin": "09:00", "duracion": 15},
    "SABADO": {"inicio": "09:00", "fin": "09:00", "duracion": 24},
    "DOMINGO": {"inicio": "09:00", "fin": "08:00", "duracion": 23}
}

# Configuración de phi-2
PHI2_CONFIG = {
    "HOST": "localhost",
    "PUERTO": 11434,  # Puerto estándar de Ollama
    "PUERTO_ALTERNATIVO": 15763,  # Puerto alternativo para instalaciones personalizadas
    "MODELO": "phi:latest",
    "TEMPERATURE": 0.1,
    "TOP_P": 0.95,
    "TOP_K": 40,
    "MAX_TOKENS": 300
}

# Configuración de salida
OUTPUT_CONFIG = {
    "PREFIJO_ARCHIVO": "Turnos_",
    "FORMATO_FECHA": "%d-%m-%Y",
    "FORMATOS_PERMITIDOS": ["xlsx", "csv", "json", "txt"]
}

# Columnas requeridas en el CSV de entrada
COLUMNAS_REQUERIDAS = [
    "Número de cita",
    "Fecha del procedimiento programado",
    "Hora del procedimiento programado",
    "Nombre del procedimiento",
    "Sala de adquisición"
]

# Cache de configuración cargada
_config_cache = None

def cargar_configuracion() -> Dict[str, Any]:
    """
    Carga la configuración desde el archivo JSON si existe,
    combinándola con los valores por defecto.
    
    Returns:
        Dict[str, Any]: Diccionario con la configuración completa
    """
    global _config_cache
    
    # Si ya tenemos la configuración en caché, devolverla
    if _config_cache is not None:
        return _config_cache
    
    # Configuración por defecto
    config = {
        "VERSION": VERSION,
        "TARIFAS": DEFAULT_TARIFAS.copy(),
        "HORARIOS_TURNO": DEFAULT_HORARIOS_TURNO.copy(),
        "PHI2": PHI2_CONFIG.copy(),
        "OUTPUT": OUTPUT_CONFIG.copy(),
        "COLUMNAS_REQUERIDAS": COLUMNAS_REQUERIDAS.copy(),
        "DEBUG": False
    }
    
    # Cargar desde archivo si existe
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config_archivo = json.load(f)
            
            # Actualizar configuración por secciones para preservar valores default
            # si alguna sección está incompleta en el archivo
            if "TARIFAS" in config_archivo:
                config["TARIFAS"].update(config_archivo["TARIFAS"])
            if "HORARIOS_TURNO" in config_archivo:
                config["HORARIOS_TURNO"].update(config_archivo["HORARIOS_TURNO"])
            if "PHI2" in config_archivo:
                config["PHI2"].update(config_archivo["PHI2"])
            if "OUTPUT" in config_archivo:
                config["OUTPUT"].update(config_archivo["OUTPUT"])
            if "COLUMNAS_REQUERIDAS" in config_archivo:
                # Asegurar que tenemos al menos las columnas mínimas
                config["COLUMNAS_REQUERIDAS"] = list(set(COLUMNAS_REQUERIDAS + 
                                                      config_archivo["COLUMNAS_REQUERIDAS"]))
            if "DEBUG" in config_archivo:
                config["DEBUG"] = config_archivo["DEBUG"]
        except Exception as e:
            print(f"Error al cargar configuración: {e}")
            # Si hay error, usar configuración por defecto
    
    # Guardar en caché
    _config_cache = config
    return config

def guardar_configuracion(config: Dict[str, Any]) -> bool:
    """
    Guarda la configuración en el archivo JSON.
    
    Args:
        config: Diccionario con la configuración a guardar
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    global _config_cache
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        
        # Actualizar caché
        _config_cache = config
        return True
    except Exception as e:
        print(f"Error al guardar configuración: {e}")
        return False

def obtener_valor(seccion: str, clave: str, default: Any = None) -> Any:
    """
    Obtiene un valor específico de la configuración.
    
    Args:
        seccion: Sección de la configuración (TARIFAS, HORARIOS_TURNO, etc.)
        clave: Clave específica dentro de la sección
        default: Valor por defecto si no se encuentra
        
    Returns:
        Any: Valor de configuración o default si no existe
    """
    config = cargar_configuracion()
    
    if seccion in config and clave in config[seccion]:
        return config[seccion][clave]
    return default

def configurar_logging():
    """Configura el sistema de logging centralizado."""
    # Determinar nivel de logging
    debug_mode = cargar_configuracion().get("DEBUG", False)
    nivel = logging.DEBUG if debug_mode else logging.INFO
    
    # Configurar formato
    formato = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Ruta al archivo de log
    log_file = os.path.join(LOGS_DIR, f"calculadora_{VERSION}.log")
    
    # Configurar logger raíz
    logging.basicConfig(
        level=nivel,
        format=formato,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # También mostrar logs en consola
        ]
    )

def obtener_logger(nombre_modulo: str) -> logging.Logger:
    """
    Obtiene un logger configurado para un módulo específico.
    
    Args:
        nombre_modulo: Nombre del módulo que solicita el logger
        
    Returns:
        logging.Logger: Logger configurado
    """
    return logging.getLogger(nombre_modulo)

def obtener_version() -> str:
    """Retorna la versión actual de la aplicación."""
    return VERSION

# Configurar logging al importar este módulo
configurar_logging()