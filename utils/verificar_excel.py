#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar si ciertos exámenes están en los archivos Excel generados
"""

import pandas as pd
import os
import sys

def main():
    """Verifica si ciertos exámenes están en los archivos Excel generados."""
    # Directorio donde están los archivos Excel
    directorio = '/Users/rodrigomunoz/Calculadora/csv'
    
    # IDs de exámenes a buscar
    examenes_a_buscar = ["9865805", "9883701", "9887600"]
    
    # 1. Verificar Examenes_Contabilizados.xlsx
    ruta_contabilizados = os.path.join(directorio, 'Examenes_Contabilizados.xlsx')
    if os.path.exists(ruta_contabilizados):
        print(f"Buscando en {ruta_contabilizados}:")
        df = pd.read_excel(ruta_contabilizados)
        
        # Limpiar formato
        df['Número de cita'] = df['Número de cita'].astype(str).str.replace('"', '').str.replace('=', '')
        
        # Buscar exámenes
        encontrados = df[df['Número de cita'].isin(examenes_a_buscar)]
        
        if encontrados.empty:
            print("  No se encontraron los exámenes buscados")
        else:
            print(f"  Se encontraron {len(encontrados)} de 3 exámenes")
            for idx, exam in encontrados.iterrows():
                print(f"  - {exam['Número de cita']}: {exam['Nombre del procedimiento']} ({exam['Fecha sin hora']})")
    else:
        print(f"No se encontró el archivo {ruta_contabilizados}")
    
    # 2. Verificar Examenes_Filtrados.xlsx (hoja TAC SCA)
    ruta_filtrados = os.path.join(directorio, 'Examenes_Filtrados.xlsx')
    if os.path.exists(ruta_filtrados):
        print(f"\nBuscando en {ruta_filtrados} (hoja TAC SCA):")
        try:
            df_tac = pd.read_excel(ruta_filtrados, sheet_name='TAC SCA')
            
            # Limpiar formato
            df_tac['Número de cita'] = df_tac['Número de cita'].astype(str).str.replace('"', '').str.replace('=', '')
            
            # Buscar exámenes
            encontrados = df_tac[df_tac['Número de cita'].isin(examenes_a_buscar)]
            
            if encontrados.empty:
                print("  No se encontraron los exámenes buscados")
            else:
                print(f"  Se encontraron {len(encontrados)} de 3 exámenes")
                for idx, exam in encontrados.iterrows():
                    tac_doble = "TAC DOBLE" if exam['TAC doble'] else "TAC normal"
                    print(f"  - {exam['Número de cita']}: {exam['Nombre del procedimiento']} ({tac_doble})")
        except Exception as e:
            print(f"  Error al leer la hoja TAC SCA: {e}")
    else:
        print(f"No se encontró el archivo {ruta_filtrados}")
    
    # 3. Verificar Resumen_Economico.xlsx
    ruta_resumen = os.path.join(directorio, 'Resumen_Economico.xlsx')
    if os.path.exists(ruta_resumen):
        print(f"\nVerificando {ruta_resumen}:")
        df_resumen = pd.read_excel(ruta_resumen)
        print("  Resumen económico:")
        for idx, row in df_resumen.iterrows():
            print(f"  - {row['Concepto']}: {row['Cantidad']} ({row['Monto']})")
    else:
        print(f"No se encontró el archivo {ruta_resumen}")

if __name__ == "__main__":
    main()