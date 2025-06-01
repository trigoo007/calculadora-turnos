#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la integración del sistema de aprendizaje SQLite
con la Calculadora de Turnos en Radiología.

Este script procesa un archivo CSV de ejemplo y muestra estadísticas 
sobre los procedimientos y salas clasificados, especialmente los TAC
dobles y triples.
"""

import os
import sys
import pandas as pd
from calculadora_turnos import CalculadoraTurnos
from aprendizaje_datos_sqlite import SistemaAprendizajeSQLite

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, "csv")
TEST_CSV = os.path.join(CSV_DIR, "Buscar-20250504200228.csv")

def imprimir_separador(texto=""):
    """Imprime un separador visual con texto opcional."""
    ancho = 80
    if texto:
        espacios = (ancho - len(texto) - 2) // 2
        print("=" * espacios + f" {texto} " + "=" * espacios)
    else:
        print("=" * ancho)

def mostrar_estadisticas_aprendizaje():
    """Muestra estadísticas del sistema de aprendizaje."""
    imprimir_separador("ESTADÍSTICAS DEL SISTEMA DE APRENDIZAJE")
    
    sistema = SistemaAprendizajeSQLite()
    stats = sistema.obtener_estadisticas()
    
    print(f"Procedimientos únicos: {stats['procedimientos']['total']}")
    for tipo, count in stats['procedimientos']['por_tipo'].items():
        print(f"  - {tipo}: {count}")
    
    # Mostrar subtipos de TAC
    print("\nDesglose de TAC por subtipo:")
    for subtipo, count in stats['procedimientos']['por_subtipo'].items():
        print(f"  - {subtipo}: {count}")
    
    print(f"\nSalas únicas: {stats['salas']['total']}")
    for tipo, count in stats['salas']['por_tipo'].items():
        print(f"  - {tipo}: {count}")
    
    print(f"\nPatrones TAC doble: {stats['patrones_tac_doble']}")
    print(f"Patrones TAC triple: {stats['patrones_tac_triple']}")
    
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

def probar_clasificacion_examen():
    """Prueba la clasificación de exámenes con el sistema de aprendizaje."""
    imprimir_separador("PRUEBA DE CLASIFICACIÓN DE EXÁMENES")
    
    sistema = SistemaAprendizajeSQLite()
    
    # Lista de procedimientos para probar
    procedimientos_prueba = [
        "RX de Tórax AP",
        "TAC de Cerebro",
        "TAC Tórax-Abdomen-Pelvis",
        "TAC de Cuello, Tórax y Abdomen",
        "TAC TX/ABD/PEL",
        "TAC Craneo-Cuello-Torax",
        "TAC Cerebro-Cuello-Torax",
        "Ecografía Abdominal",
        "TAC de Tórax",
        "RX de Columna Lumbar"
    ]
    
    # Probar clasificación de cada procedimiento
    for proc in procedimientos_prueba:
        clasificacion = sistema.clasificar_procedimiento(proc)
        tipo = clasificacion['tipo']
        subtipo = clasificacion['subtipo']
        
        # Indicador visual para facilitar lectura
        if subtipo == 'TRIPLE':
            indic = "*** TRIPLE ***"
        elif subtipo == 'DOBLE':
            indic = "** DOBLE **"
        else:
            indic = ""
        
        print(f"{proc:<30} -> {tipo:<5} {subtipo:<8} {indic}")

def procesar_archivo_test():
    """Procesa un archivo CSV de ejemplo con la calculadora de turnos."""
    imprimir_separador("PROCESAMIENTO DE ARCHIVO DE PRUEBA")
    
    if not os.path.exists(TEST_CSV):
        print(f"Error: No se encontró el archivo de prueba: {TEST_CSV}")
        return False
    
    print(f"Procesando archivo: {os.path.basename(TEST_CSV)}")
    
    # Crear instancia de la calculadora
    calculadora = CalculadoraTurnos()
    
    # Cargar y procesar el archivo
    if not calculadora.cargar_archivo(TEST_CSV):
        print("Error al cargar el archivo.")
        return False
    
    print("Archivo cargado correctamente.")
    
    # Filtrar datos
    if not calculadora.filtrar_datos():
        print("Error al filtrar datos.")
        return False
    
    print("Datos filtrados correctamente.")
    
    # Clasificar exámenes usando sistema de aprendizaje
    if not calculadora.clasificar_examenes():
        print("Error al clasificar exámenes.")
        return False
    
    print("Exámenes clasificados correctamente.")
    
    # Mostrar resultados de la clasificación
    data = calculadora.data_filtrada
    
    # Contar por tipo básico
    count_rx = len(data[data['Tipo'] == 'RX'])
    count_tac = len(data[data['Tipo'] == 'TAC'])
    
    print(f"\nTotal de exámenes: {len(data)}")
    print(f"  - RX: {count_rx}")
    print(f"  - TAC: {count_tac}")
    
    # Contar TAC por subtipo
    count_tac_normal = len(data[(data['Tipo'] == 'TAC') & (~data['TAC doble']) & (~data['TAC triple'])])
    count_tac_doble = len(data[data['TAC doble'] == True])
    count_tac_triple = len(data[data['TAC triple'] == True])
    
    print("\nDesglose de TAC:")
    print(f"  - TAC normal: {count_tac_normal}")
    print(f"  - TAC doble: {count_tac_doble}")
    print(f"  - TAC triple: {count_tac_triple}")
    
    if count_tac_doble > 0:
        print("\nEjemplos de TAC doble encontrados:")
        tac_dobles = data[data['TAC doble'] == True]
        for i, (_, row) in enumerate(tac_dobles.iterrows()[:3]):  # Mostrar hasta 3 ejemplos
            print(f"  - {row['Nombre del procedimiento']}")
    
    if count_tac_triple > 0:
        print("\nEjemplos de TAC triple encontrados:")
        tac_triples = data[data['TAC triple'] == True]
        for i, (_, row) in enumerate(tac_triples.iterrows()[:3]):  # Mostrar hasta 3 ejemplos
            print(f"  - {row['Nombre del procedimiento']}")
    
    # Contabilizar y calcular honorarios
    if not calculadora.contabilizar_examenes():
        print("Error al contabilizar exámenes.")
        return False
    
    calculadora.calcular_horas_turno()
    calculadora.calcular_honorarios()
    
    # Mostrar resumen económico
    eco = calculadora.resultado_economico
    
    imprimir_separador("RESUMEN ECONÓMICO")
    print(f"Horas trabajadas: {eco['horas_trabajadas']} ({eco['honorarios_hora']:,})")
    print(f"RX: {eco['rx_count']} (${eco['rx_total']:,})")
    print(f"TAC normal: {eco['tac_count']} (${eco['tac_total']:,})")
    print(f"TAC doble: {eco['tac_doble_count']} (${eco['tac_doble_total']:,})")
    print(f"TAC triple: {eco['tac_triple_count']} (${eco['tac_triple_total']:,})")
    print(f"TOTAL: ${eco['total']:,}")
    
    return True

def main():
    imprimir_separador("TEST DE INTEGRACIÓN SQLITE")
    print("Este script prueba la integración del sistema de aprendizaje SQLite")
    print("con la calculadora de turnos en radiología.\n")
    
    # Mostrar estadísticas del sistema de aprendizaje
    mostrar_estadisticas_aprendizaje()
    
    # Probar clasificación de procedimientos
    probar_clasificacion_examen()
    
    # Procesar archivo de prueba
    procesar_archivo_test()
    
    imprimir_separador("FIN DE LA PRUEBA")

if __name__ == "__main__":
    main()