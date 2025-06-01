#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar si exámenes específicos se clasifican como TAC doble
"""

from calculadora_turnos import CalculadoraTurnos
import pandas as pd
import sys

def main():
    """Verifica la clasificación de TAC doble para exámenes específicos."""
    if len(sys.argv) < 2:
        print("Uso: python3 verificar_tac_doble.py <ruta_archivo_csv> [ID1 ID2 ...]")
        sys.exit(1)
    
    ruta_csv = sys.argv[1]
    
    # Examenes específicos a buscar (por defecto o desde argumentos)
    examenes_a_buscar = ["9865805", "9883701", "9887600"]
    if len(sys.argv) > 2:
        examenes_a_buscar = sys.argv[2:]
    
    print(f"Verificando clasificación de: {', '.join(examenes_a_buscar)} en {ruta_csv}")
    
    try:
        # Cargar el CSV usando pandas directamente
        df = pd.read_csv(ruta_csv)
        
        # Limpiar el formato de número de cita (quitar comillas y el "=")
        df['Número de cita'] = df['Número de cita'].str.replace('"', '').str.replace('=', '')
        
        # Filtrar por los exámenes específicos
        examenes_encontrados = df[df['Número de cita'].isin(examenes_a_buscar)]
        
        if examenes_encontrados.empty:
            print("No se encontraron los exámenes especificados.")
            sys.exit(0)
        
        # Procesar cada examen
        for idx, exam in examenes_encontrados.iterrows():
            nombre_procedimiento = exam['Nombre del procedimiento']
            
            # Criterios para TAC doble según CalculadoraTurnos
            tac_dobles = [
                "Tórax, abdomen y pelvis",
                "AngioTAC de tórax, abdomen y pelvis"
            ]
            
            # Criterios adicionales que podrían considerarse como TAC doble
            criterios_adicionales = [
                "TX/ABD/PEL",
                "Angio Tórax Abdomen y Pelvis"
            ]
            
            es_tac_doble_oficial = nombre_procedimiento in tac_dobles
            es_tac_doble_adicional = any(criterio in nombre_procedimiento for criterio in criterios_adicionales)
            
            print(f"\nExamen: {exam['Número de cita']}")
            print(f"Procedimiento: {nombre_procedimiento}")
            print(f"Clasificado como TAC doble según criterios oficiales: {es_tac_doble_oficial}")
            print(f"Clasificado como TAC doble según criterios adicionales: {es_tac_doble_adicional}")
            print(f"Sugerencia: {'DEBERÍA SER TAC DOBLE' if es_tac_doble_adicional else 'TAC normal'}")
    
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()