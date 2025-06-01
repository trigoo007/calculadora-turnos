#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lector directo de archivos Excel para el sistema de códigos de exámenes.
Esta versión simplificada maneja directamente archivos Excel sin convertirlos.
"""

import pandas as pd
import os
import sys
import json
from datetime import datetime

def leer_excel_directo(ruta_excel, hoja="Data"):
    """Lee un archivo Excel y extrae los datos relevantes directamente."""
    try:
        # Cargar el Excel completo, forzando todos los datos como strings
        df = pd.read_excel(ruta_excel, sheet_name=hoja, engine='openpyxl', convert_float=False, 
                         dtype=str, keep_default_na=False)
        
        print(f"Excel cargado exitosamente: {ruta_excel}, hoja: {hoja}")
        print(f"Dimensiones: {df.shape}")
        print(f"Columnas: {df.columns.tolist()}")
        
        # Mapear columnas a los nombres esperados por el sistema
        columnas_mapeo = {
            "Prestación": "Nombre del procedimiento",
            "Centro Médico": "Centro médico", 
            "Sala": "Sala de adquisición"
        }
        
        # Verificar qué columnas están disponibles
        columnas_presentes = {}
        for col_original, col_sistema in columnas_mapeo.items():
            if col_original in df.columns:
                columnas_presentes[col_original] = col_sistema
                print(f"Columna encontrada: {col_original} -> {col_sistema}")
            else:
                print(f"Columna no encontrada: {col_original}")
                
        # Si no encontramos las columnas exactas, buscar similares
        if len(columnas_presentes) == 0:
            print("Buscando columnas similares...")
            for col in df.columns:
                col_lower = col.lower()
                if "prestacion" in col_lower or "procedimiento" in col_lower or "examen" in col_lower:
                    columnas_presentes[col] = "Nombre del procedimiento"
                    print(f"Columna similar encontrada: {col} -> Nombre del procedimiento")
                elif "centro" in col_lower or "hospital" in col_lower or "clinica" in col_lower:
                    columnas_presentes[col] = "Centro médico"
                    print(f"Columna similar encontrada: {col} -> Centro médico")
                elif "sala" in col_lower or "equipo" in col_lower:
                    columnas_presentes[col] = "Sala de adquisición"
                    print(f"Columna similar encontrada: {col} -> Sala de adquisición")
        
        # Verificar si tenemos al menos la columna de procedimientos
        if "Nombre del procedimiento" not in columnas_presentes.values():
            print("ADVERTENCIA: No se encontró la columna de procedimientos")
            return None
            
        # Crear un nuevo DataFrame con las columnas mapeadas
        df_procesado = pd.DataFrame()
        
        # Copiar datos de las columnas encontradas
        for col_original, col_sistema in columnas_presentes.items():
            if col_original in df.columns:
                # Usar la serie original, limpiando valores problemáticos
                serie = df[col_original].astype(str)
                # Reemplazar 'nan' y valores vacíos
                serie = serie.str.replace('nan', '').str.strip()
                df_procesado[col_sistema] = serie
            
        # Asegurarse de que tengamos todas las columnas necesarias
        for col_sistema in set(columnas_mapeo.values()):
            if col_sistema not in df_procesado.columns:
                df_procesado[col_sistema] = ""
        
        # Filtrar para mantener solo registros con nombre de procedimiento
        df_procesado = df_procesado[df_procesado["Nombre del procedimiento"].str.strip() != ""]
        
        print(f"DataFrame procesado: {df_procesado.shape} filas")
        if len(df_procesado) > 0:
            print("Primeras 3 filas:")
            print(df_procesado.head(3))
            
        # Guardar en un archivo temporal
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        nombre_base = os.path.splitext(os.path.basename(ruta_excel))[0]
        ruta_procesado = f"/tmp/{nombre_base}_procesado_{timestamp}.csv"
        
        df_procesado.to_csv(ruta_procesado, index=False)
        print(f"Archivo procesado guardado en: {ruta_procesado}")
        
        return {
            "exito": True,
            "ruta_procesada": ruta_procesado,
            "filas": len(df_procesado),
            "columnas": df_procesado.columns.tolist()
        }
    
    except Exception as e:
        print(f"Error al procesar Excel: {e}")
        return {"error": str(e)}

def listar_hojas_excel(ruta_excel):
    """Lista las hojas disponibles en un archivo Excel."""
    try:
        xls = pd.ExcelFile(ruta_excel)
        print(f"Hojas disponibles en {ruta_excel}:")
        for i, hoja in enumerate(xls.sheet_names):
            print(f"  {i}: {hoja}")
        return xls.sheet_names
    except Exception as e:
        print(f"Error al listar hojas: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python leer_excel_directo.py ruta_excel [hoja]")
        sys.exit(1)
    
    ruta_excel = sys.argv[1]
    
    # Primero listar las hojas
    hojas = listar_hojas_excel(ruta_excel)
    
    # Procesar la hoja especificada o la primera
    hoja = sys.argv[2] if len(sys.argv) > 2 else hojas[0] if hojas else "Data"
    
    resultado = leer_excel_directo(ruta_excel, hoja)
    if resultado:
        print(json.dumps(resultado, indent=2))