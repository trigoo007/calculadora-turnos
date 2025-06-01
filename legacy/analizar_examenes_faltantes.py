#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar específicamente por qué ciertos exámenes no están siendo incluidos
"""

import pandas as pd
import os
import sys
from datetime import datetime
from dateutil import parser

def convertir_fecha_espanol(fecha_str):
    """Convierte una fecha en formato español a formato estándar."""
    meses_esp = {
        'ene': 'jan', 'feb': 'feb', 'mar': 'mar', 'abr': 'apr',
        'may': 'may', 'jun': 'jun', 'jul': 'jul', 'ago': 'aug',
        'sep': 'sep', 'oct': 'oct', 'nov': 'nov', 'dic': 'dec'
    }
    
    fecha_lower = fecha_str.lower()
    for mes_esp, mes_eng in meses_esp.items():
        if mes_esp in fecha_lower:
            fecha_lower = fecha_lower.replace(mes_esp, mes_eng)
            break
    
    return parser.parse(fecha_lower)

def main():
    """Analiza por qué ciertos exámenes no están siendo incluidos."""
    # Archivo CSV
    ruta_csv = '/Users/rodrigomunoz/Calculadora/csv/Buscar-20250504200228.csv'
    
    # IDs de exámenes a buscar
    examenes_a_buscar = ["9865805", "9883701", "9887600"]
    
    print(f"Analizando exámenes específicos en {ruta_csv}...")
    
    try:
        # Leer el CSV
        df = pd.read_csv(ruta_csv)
        
        # Limpiar formato de número de cita
        df['Número de cita'] = df['Número de cita'].astype(str).str.replace('"', '').str.replace('=', '')
        
        # Filtrar por los exámenes específicos
        examenes = df[df['Número de cita'].isin(examenes_a_buscar)]
        
        if examenes.empty:
            print("No se encontraron los exámenes especificados.")
            sys.exit(0)
        
        print(f"Se encontraron {len(examenes)} exámenes:")
        
        # Aplicar criterios de filtrado
        for idx, exam in examenes.iterrows():
            num_cita = exam['Número de cita']
            nom_proc = exam['Nombre del procedimiento']
            sala = exam['Sala de adquisición']
            fecha_str = exam['Fecha del procedimiento programado']
            
            # Convertir fecha
            try:
                fecha = convertir_fecha_espanol(fecha_str)
                fecha_str_std = fecha.strftime('%Y-%m-%d')
            except:
                fecha_str_std = "Error en fecha"
            
            print(f"\nExamen: {num_cita}")
            print(f"Procedimiento: {nom_proc}")
            print(f"Sala: {sala}")
            print(f"Fecha: {fecha_str} ({fecha_str_std})")
            
            # Verificar criterios de filtrado
            criterio_sala_sca_sj = sala.startswith('SCA') or sala.startswith('SJ')
            criterio_no_hospital = not sala.startswith('HOS')
            es_tac = "TAC" in str(nom_proc).upper()
            criterio_tac_doble = (
                "Tórax, abdomen y pelvis" in nom_proc or
                "AngioTAC de tórax, abdomen y pelvis" in nom_proc or
                "TX/ABD/PEL" in str(nom_proc).upper() or
                "Angio Tórax Abdomen y Pelvis" in str(nom_proc)
            )
            
            tipo = "TAC doble" if (es_tac and criterio_tac_doble) else ("TAC" if es_tac else "RX")
            
            print(f"Tipo detectado: {tipo}")
            print(f"Cumple criterio SCA/SJ: {criterio_sala_sca_sj}")
            print(f"Cumple criterio no Hospital: {criterio_no_hospital}")
            print(f"Cumple criterio TAC: {es_tac}")
            print(f"Cumple criterio TAC doble: {criterio_tac_doble}")
            
            pasa_filtro = criterio_sala_sca_sj and criterio_no_hospital
            print(f"PASA FILTRO INICIAL: {pasa_filtro}")
            
            if pasa_filtro:
                print("ESTE EXAMEN DEBERÍA ESTAR EN LOS RESULTADOS")
                print("Posibles razones por las que no aparece:")
                print("1. Problema con el formato de la fecha")
                print("2. Error en la fase de contabilización")
                print("3. Error al generar los archivos Excel")
            else:
                print("ESTE EXAMEN NO PASA LOS CRITERIOS DE FILTRADO")
                if not criterio_sala_sca_sj:
                    print("La sala no comienza con SCA o SJ")
                if not criterio_no_hospital:
                    print("La sala comienza con HOS (hospital)")
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()