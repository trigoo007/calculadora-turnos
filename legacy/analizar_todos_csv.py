#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar todos los archivos CSV disponibles
y actualizar la base de conocimiento SQLite de la Calculadora de Turnos.

Este script busca CSV en las carpetas predefinidas, los procesa
para extraer información sobre procedimientos y salas, y actualiza
la base de datos de conocimiento SQLite.
"""

import os
import sys
import pandas as pd
import glob
from datetime import datetime
from aprendizaje_datos_sqlite import SistemaAprendizajeSQLite

# Directorios donde buscar archivos CSV
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, "csv")
CONOCIMIENTO_DIR = os.path.join(BASE_DIR, "conocimiento")

def imprimir_separador(texto=""):
    """Imprime un separador visual con texto opcional."""
    ancho = 80
    if texto:
        espacios = (ancho - len(texto) - 2) // 2
        print("=" * espacios + f" {texto} " + "=" * espacios)
    else:
        print("=" * ancho)

def obtener_lista_archivos_csv():
    """Obtiene una lista de todos los archivos CSV disponibles para analizar."""
    # Buscar archivos CSV en la carpeta principal
    archivos_csv = glob.glob(os.path.join(CSV_DIR, "*.csv"))
    
    # Buscar en todas las subcarpetas de CSV
    for root, dirs, files in os.walk(CSV_DIR):
        for file in files:
            if file.endswith(".csv"):
                ruta_completa = os.path.join(root, file)
                if ruta_completa not in archivos_csv:
                    archivos_csv.append(ruta_completa)
    
    # Buscar en la carpeta de conocimiento
    archivos_conocimiento = glob.glob(os.path.join(CONOCIMIENTO_DIR, "*.csv"))
    
    # Combinar todas las rutas
    return archivos_csv + archivos_conocimiento

def analizar_csv(ruta_archivo, sistema):
    """Analiza un archivo CSV y actualiza el sistema de aprendizaje."""
    try:
        print(f"Analizando {os.path.basename(ruta_archivo)}...", end="")
        
        # Cargar el CSV
        df = pd.read_csv(ruta_archivo)
        
        # Verificar si contiene las columnas necesarias
        columnas_req = ['Nombre del procedimiento', 'Sala de adquisición']
        if not all(col in df.columns for col in columnas_req):
            print(" ❌ No contiene las columnas requeridas")
            return False
        
        # Analizar con el sistema de aprendizaje
        exito, mensaje = sistema.analizar_dataframe(df)
        
        if exito:
            # Obtener estadísticas de este CSV
            n_proc = len(df['Nombre del procedimiento'].dropna().unique())
            n_salas = len(df['Sala de adquisición'].dropna().unique())
            print(f" ✅ {n_proc} procedimientos, {n_salas} salas")
            return True
        else:
            print(f" ❌ Error: {mensaje}")
            return False
    
    except Exception as e:
        print(f" ❌ Error: {str(e)}")
        return False

def mostrar_estadisticas(sistema):
    """Muestra estadísticas del sistema de aprendizaje después del análisis."""
    imprimir_separador("ESTADÍSTICAS FINALES")
    
    stats = sistema.obtener_estadisticas()
    
    print(f"🏥 Procedimientos únicos: {stats['procedimientos']['total']}")
    for tipo, count in stats['procedimientos']['por_tipo'].items():
        print(f"  - {tipo}: {count}")
    
    # Mostrar subtipos de TAC
    print("\n🔍 Desglose de TAC por subtipo:")
    for subtipo, count in stats['procedimientos']['por_subtipo'].items():
        print(f"  - {subtipo}: {count}")
    
    print(f"\n🏢 Salas únicas: {stats['salas']['total']}")
    for tipo, count in stats['salas']['por_tipo'].items():
        print(f"  - {tipo}: {count}")
    
    print(f"\n📋 Patrones TAC doble: {stats['patrones_tac_doble']}")
    print(f"📋 Patrones TAC triple: {stats['patrones_tac_triple']}")
    
    # Listar algunos procedimientos TAC doble y triple
    imprimir_separador("EJEMPLOS DE TAC DOBLE")
    tac_dobles = sistema.obtener_procedimientos_tipo('TAC', 'DOBLE')
    for i, proc in enumerate(tac_dobles[:5]):  # Mostrar solo los 5 primeros como ejemplo
        print(f"- [{proc['codigo']}] {proc['nombre']} (visto {proc['conteo']} veces)")
    if len(tac_dobles) > 5:
        print(f"... y {len(tac_dobles) - 5} más")
    
    imprimir_separador("EJEMPLOS DE TAC TRIPLE")
    tac_triples = sistema.obtener_procedimientos_tipo('TAC', 'TRIPLE')
    for i, proc in enumerate(tac_triples[:5]):  # Mostrar solo los 5 primeros como ejemplo
        print(f"- [{proc['codigo']}] {proc['nombre']} (visto {proc['conteo']} veces)")
    if len(tac_triples) > 5:
        print(f"... y {len(tac_triples) - 5} más")

def main():
    imprimir_separador("ANÁLISIS DE TODOS LOS ARCHIVOS CSV")
    print(f"Fecha y hora: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    print("Este script analizará todos los archivos CSV disponibles para")
    print("actualizar la base de conocimiento SQLite del sistema.\n")
    
    # Inicializar sistema de aprendizaje
    sistema = SistemaAprendizajeSQLite()
    
    # Obtener estadísticas iniciales
    stats_iniciales = sistema.obtener_estadisticas()
    print(f"Estadísticas iniciales:")
    print(f"- Procedimientos: {stats_iniciales['procedimientos']['total']}")
    print(f"- Salas: {stats_iniciales['salas']['total']}")
    print(f"- Patrones TAC doble: {stats_iniciales['patrones_tac_doble']}")
    print(f"- Patrones TAC triple: {stats_iniciales['patrones_tac_triple']}\n")
    
    # Obtener lista de archivos CSV
    archivos_csv = obtener_lista_archivos_csv()
    print(f"Se encontraron {len(archivos_csv)} archivos CSV para analizar.\n")
    
    # Analizar cada archivo
    analizados = 0
    correctos = 0
    
    imprimir_separador("PROCESANDO ARCHIVOS")
    
    for ruta in archivos_csv:
        analizados += 1
        if analizar_csv(ruta, sistema):
            correctos += 1
    
    # Mostrar resumen
    imprimir_separador("RESUMEN DE ANÁLISIS")
    print(f"Archivos analizados: {analizados}")
    print(f"Archivos procesados correctamente: {correctos}")
    print(f"Archivos con error: {analizados - correctos}")
    
    # Obtener estadísticas finales
    stats_finales = sistema.obtener_estadisticas()
    nuevos_proc = stats_finales['procedimientos']['total'] - stats_iniciales['procedimientos']['total']
    nuevas_salas = stats_finales['salas']['total'] - stats_iniciales['salas']['total']
    nuevos_patrones_doble = stats_finales['patrones_tac_doble'] - stats_iniciales['patrones_tac_doble']
    nuevos_patrones_triple = stats_finales['patrones_tac_triple'] - stats_iniciales['patrones_tac_triple']
    
    print(f"\nNuevos elementos aprendidos:")
    print(f"- Procedimientos: {nuevos_proc}")
    print(f"- Salas: {nuevas_salas}")
    print(f"- Patrones TAC doble: {nuevos_patrones_doble}")
    print(f"- Patrones TAC triple: {nuevos_patrones_triple}")
    
    # Mostrar estadísticas detalladas
    mostrar_estadisticas(sistema)
    
    imprimir_separador("FIN DEL ANÁLISIS")

if __name__ == "__main__":
    main()