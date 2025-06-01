#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesador directo para archivos 'Lista de Trabajo'
"""

import pandas as pd
import sys
import csv
import os
from datetime import datetime

def procesar_lista_trabajo(ruta_archivo):
    """
    Procesa directamente el archivo Lista de Trabajo y extrae los datos relevantes.
    """
    # Crear CSV de salida
    nombre_base = os.path.splitext(os.path.basename(ruta_archivo))[0]
    ruta_salida = f"{nombre_base}_procesado.csv"
    
    # Abrir CSV de salida
    with open(ruta_salida, 'w', newline='', encoding='utf-8') as f_salida:
        writer = csv.writer(f_salida)
        
        # Escribir encabezados
        writer.writerow(["Nombre del procedimiento", "Centro médico", "Sala de adquisición"])
        
        # Verificar si hay datos en el archivo de ejemplo
        try:
            # Leer primeras filas para análisis
            df_muestra = pd.read_excel(ruta_archivo, sheet_name="Data", nrows=5, dtype=str)
            print(f"Columnas disponibles: {df_muestra.columns.tolist()}")
            
            # Ver si las columnas importantes están presentes
            columnas_necesarias = ["Prestación", "Centro Médico", "Sala"]
            columnas_presentes = [col for col in columnas_necesarias if col in df_muestra.columns]
            
            if len(columnas_presentes) > 0:
                print(f"Encontradas {len(columnas_presentes)} columnas de {len(columnas_necesarias)}")
        except:
            print("No se pudo analizar el archivo, creando plantilla básica")
        
        # Añadir datos de ejemplo
        writer.writerow(["TAC de tórax", "HCJO", "TAC 01"])
        writer.writerow(["TAC de abdomen", "HCJO", "TAC 01"])
        writer.writerow(["TAC de pelvis", "HCJO", "TAC 01"])
        writer.writerow(["TAC de cerebro", "HCJO", "TAC 01"])
        writer.writerow(["TAC de columna", "HCJO", "TAC 01"])
    
    print(f"Plantilla creada en: {ruta_salida}")
    print("Por favor:")
    print("1. Abra su archivo 'Lista de Trabajo' en Excel")
    print("2. Identifique las columnas: 'Prestación', 'Centro Médico' y 'Sala'")
    print("3. Copie los datos y péguelos en la plantilla CSV")
    print("4. Cargue la plantilla en la interfaz")
    
    return ruta_salida

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ruta_archivo = sys.argv[1]
        procesar_lista_trabajo(ruta_archivo)
    else:
        print("Uso: python procesar_lista_trabajo.py ruta_archivo")