#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de validación centralizada para la Calculadora de Turnos
--------------------------------------------------------------
Proporciona funciones de validación para garantizar integridad de datos.
"""

import os
import re
import pandas as pd
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional, Union

# Importar configuración
import config

# Obtener logger
logger = config.obtener_logger(__name__)

def validar_csv(ruta_archivo: str) -> Tuple[bool, str]:
    """
    Valida que un archivo CSV tenga el formato correcto y contenga las columnas requeridas.
    
    Args:
        ruta_archivo: Ruta al archivo CSV a validar
        
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    # Verificar que el archivo existe
    if not os.path.exists(ruta_archivo):
        mensaje = f"El archivo {ruta_archivo} no existe"
        logger.error(mensaje)
        return False, mensaje
    
    # Verificar extensión
    if not ruta_archivo.lower().endswith('.csv'):
        mensaje = f"El archivo {ruta_archivo} no es un archivo CSV válido"
        logger.error(mensaje)
        return False, mensaje
    
    try:
        # Intentar leer el archivo
        df = pd.read_csv(ruta_archivo)
        
        # Verificar que no esté vacío
        if df.empty:
            mensaje = f"El archivo {ruta_archivo} está vacío"
            logger.error(mensaje)
            return False, mensaje
        
        # Verificar columnas requeridas
        columnas_requeridas = config.cargar_configuracion()["COLUMNAS_REQUERIDAS"]
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        
        if columnas_faltantes:
            mensaje = f"Faltan las siguientes columnas requeridas: {', '.join(columnas_faltantes)}"
            logger.error(mensaje)
            return False, mensaje
        
        # Verificación básica de datos
        # - Comprobar que las fechas tengan formato válido
        if 'Fecha del procedimiento programado' in df.columns:
            fechas_invalidas = []
            for idx, fecha in enumerate(df['Fecha del procedimiento programado']):
                if not isinstance(fecha, str):
                    continue
                    
                # Patrones comunes de fecha
                patrones = [
                    r'\d{2}-\w{3}-\d{4}',  # 01-ene-2025
                    r'\d{2}/\d{2}/\d{4}',   # 01/01/2025
                    r'\d{4}-\d{2}-\d{2}'    # 2025-01-01
                ]
                
                if not any(re.match(patron, fecha) for patron in patrones):
                    fechas_invalidas.append((idx + 2, fecha))  # +2 por encabezado y 1-indexed
            
            if fechas_invalidas:
                logger.warning(f"Se encontraron {len(fechas_invalidas)} fechas con formato posiblemente inválido")
                for idx, fecha in fechas_invalidas[:5]:  # Mostrar solo las primeras 5
                    logger.warning(f"  - Fila {idx}: '{fecha}'")
                if len(fechas_invalidas) > 5:
                    logger.warning(f"  - Y {len(fechas_invalidas) - 5} más...")
        
        # La validación de contenido se realiza, pero no es bloqueante
        return True, f"El archivo {ruta_archivo} es válido"
        
    except Exception as e:
        mensaje = f"Error al validar el archivo {ruta_archivo}: {str(e)}"
        logger.error(mensaje)
        return False, mensaje

def validar_procedimiento(nombre: str) -> Dict[str, Any]:
    """
    Valida y clasifica un procedimiento médico.
    
    Args:
        nombre: Nombre del procedimiento a validar
        
    Returns:
        Dict[str, Any]: Información validada del procedimiento
    """
    if not nombre or not isinstance(nombre, str):
        return {
            "valido": False,
            "tipo": "DESCONOCIDO",
            "subtipo": "DESCONOCIDO",
            "mensaje": "Nombre de procedimiento vacío o inválido"
        }
    
    # Clasificación básica
    nombre_lower = nombre.lower()
    
    if 'tac' in nombre_lower or 'tomograf' in nombre_lower:
        tipo = 'TAC'
        
        # Detectar TAC triple
        patrones_triple = [
            ['cerebro', 'cuello', 'torax'],
            ['cabeza', 'cuello', 'torax'],
            ['craneo', 'cuello', 'torax'],
            ['torax', 'abdomen', 'pelvis'],
            ['tx', 'abd', 'pelv'],
            ['cérebro', 'senos paranasales', 'macizo facial'],
        ]
        
        es_triple = False
        for combinacion in patrones_triple:
            if all(region in nombre_lower for region in combinacion):
                es_triple = True
                break
        
        # Detectar TAC doble si no es triple
        es_doble = False
        if not es_triple:
            patrones_doble = [
                ['torax', 'abdomen'],
                ['tx', 'abd'],
                ['craneo', 'cuello'],
                ['cerebro', 'cuello'],
                ['craneo', 'senos paranasales'],
                ['cerebro', 'senos paranasales']
            ]
            
            for combinacion in patrones_doble:
                if all(region in nombre_lower for region in combinacion):
                    es_doble = True
                    break
        
        # Asignar subtipo
        if es_triple:
            subtipo = 'TRIPLE'
        elif es_doble:
            subtipo = 'DOBLE'
        else:
            subtipo = 'NORMAL'
            
    elif 'rx' in nombre_lower or 'radio' in nombre_lower or 'rayos' in nombre_lower:
        tipo = 'RX'
        subtipo = 'NORMAL'
    else:
        tipo = 'OTRO'
        subtipo = 'DESCONOCIDO'
        
    return {
        "valido": True,
        "tipo": tipo,
        "subtipo": subtipo,
        "mensaje": "Procedimiento validado correctamente"
    }

def validar_sala(nombre: str) -> Dict[str, Any]:
    """
    Valida y clasifica una sala de adquisición.
    
    Args:
        nombre: Nombre de la sala a validar
        
    Returns:
        Dict[str, Any]: Información validada de la sala
    """
    if not nombre or not isinstance(nombre, str):
        return {
            "valido": False,
            "tipo": "DESCONOCIDO",
            "subtipo": "DESCONOCIDO",
            "mensaje": "Nombre de sala vacío o inválido"
        }
    
    # Clasificación básica
    nombre_upper = nombre.upper()
    
    # Determinar tipo de sala
    if 'SCA' in nombre_upper:
        tipo = 'SCA'
    elif 'SJ' in nombre_upper:
        tipo = 'SJ'
    elif 'HOS' in nombre_upper:
        tipo = 'HOS'
    else:
        tipo = 'OTRO'
    
    # Determinar subtipo/modalidad
    if 'TAC' in nombre_upper:
        subtipo = 'TAC'
    elif 'RX' in nombre_upper or 'RAYOS' in nombre_upper:
        subtipo = 'RX'
    elif 'PROC' in nombre_upper:
        subtipo = 'PROCEDIMIENTOS'
    else:
        subtipo = 'GENERAL'
    
    return {
        "valido": True,
        "tipo": tipo,
        "subtipo": subtipo,
        "mensaje": "Sala validada correctamente"
    }

def validar_fecha(fecha: str) -> Dict[str, Any]:
    """
    Valida y normaliza una fecha.
    
    Args:
        fecha: Fecha a validar (en formato dd-mmm-yyyy, dd/mm/yyyy, etc.)
        
    Returns:
        Dict[str, Any]: Información validada de la fecha
    """
    if not fecha or not isinstance(fecha, str):
        return {
            "valido": False,
            "fecha_normalizada": None,
            "mensaje": "Fecha vacía o inválida"
        }
    
    # Patrones de fecha comunes
    patrones = [
        ('%d-%b-%Y', r'\d{2}-\w{3}-\d{4}'),  # 01-ene-2025
        ('%d/%m/%Y', r'\d{2}/\d{2}/\d{4}'),   # 01/01/2025
        ('%Y-%m-%d', r'\d{4}-\d{2}-\d{2}')    # 2025-01-01
    ]
    
    fecha_normalizada = None
    
    # Intentar parsear la fecha con cada patrón
    for formato, patron in patrones:
        if re.match(patron, fecha):
            try:
                fecha_dt = datetime.strptime(fecha, formato)
                fecha_normalizada = fecha_dt.strftime('%d-%b-%Y')  # Formato estándar
                return {
                    "valido": True,
                    "fecha_normalizada": fecha_normalizada,
                    "fecha_dt": fecha_dt,
                    "mensaje": "Fecha validada correctamente"
                }
            except ValueError:
                pass
    
    # Si llegamos aquí, ningún patrón ha funcionado
    return {
        "valido": False,
        "fecha_normalizada": None,
        "mensaje": f"Formato de fecha no reconocido: {fecha}"
    }

def validar_configuracion(config_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valida que una configuración tenga el formato correcto y contenga las secciones requeridas.
    
    Args:
        config_data: Diccionario con la configuración a validar
        
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    # Secciones requeridas
    secciones_requeridas = ["TARIFAS", "HORARIOS_TURNO", "PHI2", "OUTPUT"]
    
    # Verificar secciones requeridas
    secciones_faltantes = [sec for sec in secciones_requeridas if sec not in config_data]
    if secciones_faltantes:
        mensaje = f"Faltan las siguientes secciones requeridas: {', '.join(secciones_faltantes)}"
        logger.error(mensaje)
        return False, mensaje
    
    # Verificar tarifas
    if "TARIFAS" in config_data:
        tarifas_requeridas = ["TARIFA_HORA", "TARIFA_RX", "TARIFA_TAC", "TARIFA_TAC_DOBLE", "TARIFA_TAC_TRIPLE"]
        tarifas_faltantes = [tar for tar in tarifas_requeridas if tar not in config_data["TARIFAS"]]
        
        if tarifas_faltantes:
            mensaje = f"Faltan las siguientes tarifas requeridas: {', '.join(tarifas_faltantes)}"
            logger.error(mensaje)
            return False, mensaje
    
    # Verificación de horarios de turno
    if "HORARIOS_TURNO" in config_data:
        dias_requeridos = ["LUNES_JUEVES", "VIERNES", "SABADO", "DOMINGO"]
        dias_faltantes = [dia for dia in dias_requeridos if dia not in config_data["HORARIOS_TURNO"]]
        
        if dias_faltantes:
            mensaje = f"Faltan los siguientes días en horarios de turno: {', '.join(dias_faltantes)}"
            logger.error(mensaje)
            return False, mensaje
            
        # Verificar que cada día tenga inicio, fin y duración
        for dia, horario in config_data["HORARIOS_TURNO"].items():
            campos_requeridos = ["inicio", "fin", "duracion"]
            campos_faltantes = [campo for campo in campos_requeridos if campo not in horario]
            
            if campos_faltantes:
                mensaje = f"Faltan los siguientes campos en horario de {dia}: {', '.join(campos_faltantes)}"
                logger.error(mensaje)
                return False, mensaje
    
    # Verificar configuración de phi-2
    if "PHI2" in config_data:
        campos_phi2 = ["HOST", "PUERTO", "MODELO", "TEMPERATURE", "TOP_P"]
        campos_faltantes = [campo for campo in campos_phi2 if campo not in config_data["PHI2"]]
        
        if campos_faltantes:
            mensaje = f"Faltan los siguientes campos en configuración de phi-2: {', '.join(campos_faltantes)}"
            logger.warning(mensaje)  # Solo advertencia, no es crítico
    
    # La configuración parece válida
    return True, "Configuración validada correctamente"
        
# Función para probar el módulo
def main():
    """Función principal para probar el módulo de validación."""
    print("Prueba de funciones de validación:")
    
    # Probar validación de procedimientos
    procedimientos_prueba = [
        "RX de Tórax",
        "TAC de Cerebro",
        "TAC Tórax-Abdomen-Pelvis",
        "TAC Abdomen-Pelvis",
        "Ecografía Abdominal"
    ]
    
    print("\nValidación de procedimientos:")
    for proc in procedimientos_prueba:
        resultado = validar_procedimiento(proc)
        print(f"- {proc}: {resultado['tipo']}/{resultado['subtipo']} ({resultado['mensaje']})")
    
    # Probar validación de salas
    salas_prueba = [
        "SCA01",
        "SJ02",
        "HOS-TAC",
        "PROC01"
    ]
    
    print("\nValidación de salas:")
    for sala in salas_prueba:
        resultado = validar_sala(sala)
        print(f"- {sala}: {resultado['tipo']}/{resultado['subtipo']} ({resultado['mensaje']})")
    
    # Probar validación de fechas
    fechas_prueba = [
        "01-ene-2025",
        "01/01/2025",
        "2025-01-01",
        "01/13/2025"  # Inválida
    ]
    
    print("\nValidación de fechas:")
    for fecha in fechas_prueba:
        resultado = validar_fecha(fecha)
        if resultado["valido"]:
            print(f"- {fecha} -> {resultado['fecha_normalizada']} (válida)")
        else:
            print(f"- {fecha} -> Inválida: {resultado['mensaje']}")

if __name__ == "__main__":
    main()