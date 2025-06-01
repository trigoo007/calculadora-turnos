#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar el funcionamiento de la Calculadora de Turnos
con el sistema de aprendizaje SQLite integrado.
"""

import os
import sys
from calculadora_turnos import CalculadoraTurnos

def main():
    # Archivo CSV de ejemplo para procesar
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CSV_DIR = os.path.join(BASE_DIR, "csv")
    ARCHIVO_EJEMPLO = os.path.join(CSV_DIR, "Buscar-20250504200228.csv")
    
    # Verificar que el archivo existe
    if not os.path.exists(ARCHIVO_EJEMPLO):
        print(f"Error: No se encontró el archivo de ejemplo {ARCHIVO_EJEMPLO}")
        sys.exit(1)
    
    print("=" * 50)
    print("PRUEBA DE CALCULADORA DE TURNOS CON SQLITE")
    print("=" * 50)
    print(f"Procesando archivo: {ARCHIVO_EJEMPLO}")
    
    # Crear instancia de la calculadora
    calculadora = CalculadoraTurnos()
    
    # Cargar y procesar el archivo
    print("\nCargando archivo...")
    if not calculadora.cargar_archivo(ARCHIVO_EJEMPLO):
        print("Error al cargar el archivo.")
        sys.exit(1)
    print("✓ Archivo cargado correctamente.")
    
    # Filtrar datos
    print("\nFiltrando datos...")
    if not calculadora.filtrar_datos():
        print("Error al filtrar datos.")
        sys.exit(1)
    print("✓ Datos filtrados correctamente.")
    
    # Clasificar exámenes
    print("\nClasificando exámenes...")
    if not calculadora.clasificar_examenes():
        print("Error al clasificar exámenes.")
        sys.exit(1)
    print("✓ Exámenes clasificados correctamente.")
    
    # Mostrar estadísticas de clasificación
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
    
    # Contabilizar exámenes
    print("\nContabilizando exámenes...")
    if not calculadora.contabilizar_examenes():
        print("Error al contabilizar exámenes.")
        sys.exit(1)
    print("✓ Exámenes contabilizados correctamente.")
    
    # Calcular horas y honorarios
    print("\nCalculando horas y honorarios...")
    
    # Ejemplo de fechas de turno (opcional)
    fechas_turno = "14-abr-2025,24-abr-2025,20-abr-2025"
    
    if fechas_turno and fechas_turno.strip():
        fechas_lista = [fecha.strip() for fecha in fechas_turno.split(',')]
        print("Calculando horas para fechas específicas de turno:")
        for fecha in fechas_lista:
            print(f"  - {fecha}")
        total_horas = calculadora.calcular_horas_turno_especificas(fechas_lista)
        # Sobrescribir las horas calculadas
        calculadora.resultado_economico['horas_trabajadas'] = total_horas
    else:
        # Calcular horas de turno automáticamente
        if not calculadora.calcular_horas_turno():
            print("Error al calcular horas de turno.")
            sys.exit(1)
    
    # Calcular honorarios
    if not calculadora.calcular_honorarios():
        print("Error al calcular honorarios.")
        sys.exit(1)
    
    print("✓ Cálculos completados.")
    
    # Mostrar resumen económico
    eco = calculadora.resultado_economico
    
    print("\n" + "=" * 50)
    print("RESUMEN ECONÓMICO")
    print("=" * 50)
    print(f"Horas trabajadas: {eco['horas_trabajadas']} (${eco['honorarios_hora']:,})")
    print(f"RX: {eco['rx_count']} (${eco['rx_total']:,})")
    print(f"TAC normal: {eco['tac_count']} (${eco['tac_total']:,})")
    print(f"TAC doble: {eco['tac_doble_count']} (${eco['tac_doble_total']:,})")
    print(f"TAC triple: {eco['tac_triple_count']} (${eco['tac_triple_total']:,})")
    
    # Calcular total de TAC (contando dobles como 2 y triples como 3)
    tac_conteo_total = eco['tac_count'] + (eco['tac_doble_count'] * 2) + (eco['tac_triple_count'] * 3)
    print(f"TAC total para informes: {tac_conteo_total}")
    
    print(f"TOTAL: ${eco['total']:,}")
    
    # Generar texto de correo
    print("\n" + "=" * 50)
    print("EJEMPLO DE CORREO GENERADO")
    print("=" * 50)
    
    correo = calculadora.generar_correo("Cikutovic")
    if correo:
        print(f"Asunto: {correo['asunto']}")
        print("-" * 50)
        print(correo['cuerpo'])
    else:
        print("Error al generar correo.")
    
    print("\n" + "=" * 50)
    print("PRUEBA COMPLETADA EXITOSAMENTE")
    print("=" * 50)

if __name__ == "__main__":
    main()