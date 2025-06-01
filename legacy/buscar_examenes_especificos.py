#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para buscar exámenes específicos en el archivo CSV
"""

import pandas as pd
from dateutil import parser
import sys

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
    
    return parser.parse(fecha_lower).strftime('%Y-%m-%d')

def main():
    """Función principal para buscar exámenes específicos."""
    if len(sys.argv) < 2:
        print("Uso: python3 buscar_examenes_especificos.py <ruta_archivo_csv> [ID1 ID2 ...]")
        sys.exit(1)
    
    ruta_csv = sys.argv[1]
    
    # Examenes específicos a buscar (por defecto o desde argumentos)
    examenes_a_buscar = ["9865805", "9883701", "9887600"]
    if len(sys.argv) > 2:
        examenes_a_buscar = sys.argv[2:]
    
    print(f"Buscando exámenes: {', '.join(examenes_a_buscar)} en {ruta_csv}")
    
    try:
        # Cargar el CSV
        df = pd.read_csv(ruta_csv)
        
        # Limpiar el formato de número de cita (quitar comillas y el "=")
        df['Número de cita'] = df['Número de cita'].str.replace('"', '').str.replace('=', '')
        
        # Filtrar por los exámenes específicos
        examenes_encontrados = df[df['Número de cita'].isin(examenes_a_buscar)]
        
        if examenes_encontrados.empty:
            print("No se encontraron los exámenes especificados.")
            sys.exit(0)
        
        # Agregar columna de fecha convertida
        examenes_encontrados['Fecha convertida'] = examenes_encontrados['Fecha del procedimiento programado'].apply(convertir_fecha_espanol)
        
        # Verificar si cumplen con los criterios de filtrado normales
        for idx, exam in examenes_encontrados.iterrows():
            sala = exam['Sala de adquisición']
            es_tac = "TAC" in str(exam['Nombre del procedimiento']).upper()
            
            print(f"\nExamen: {exam['Número de cita']}")
            print(f"Fecha: {exam['Fecha del procedimiento programado']} ({exam['Fecha convertida']})")
            print(f"Procedimiento: {exam['Nombre del procedimiento']}")
            print(f"Sala: {sala}")
            print(f"Paciente: {exam['Apellidos del paciente']}, {exam['Nombre del paciente']}")
            
            # Verificar criterios de filtrado
            cumple_sala = sala.startswith('SCA') or sala.startswith('SJ')
            no_es_hospital = not sala.startswith('HOS')
            tipo = "TAC" if es_tac else "RX"
            
            print(f"Tipo: {tipo}")
            print(f"Cumple criterio de sala (SCA o SJ): {cumple_sala}")
            print(f"No es Hospital (no empieza con HOS): {no_es_hospital}")
            print(f"Debería ser incluido en filtrado: {cumple_sala and no_es_hospital}")
    
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()