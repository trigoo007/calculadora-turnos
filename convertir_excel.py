#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convertidor de Excel a CSV
-------------------------
Herramienta para convertir archivos Excel (.xlsx) a formato CSV
para usarlos en el Sistema de Codificación de Exámenes.
"""

import pandas as pd
import os
import sys
import argparse
from datetime import datetime

def obtener_hojas_excel(ruta_excel):
    """Obtiene la lista de hojas disponibles en un archivo Excel."""
    try:
        if not os.path.exists(ruta_excel):
            return {"error": f"El archivo {ruta_excel} no existe"}
        
        # Verificar que es un archivo Excel
        if not ruta_excel.endswith(('.xls', '.xlsx')):
            return {"error": f"El archivo {ruta_excel} no es un archivo Excel válido"}
        
        # Leer hojas
        xls = pd.ExcelFile(ruta_excel)
        
        return {
            "exito": True,
            "hojas": xls.sheet_names
        }
    except Exception as e:
        return {"error": f"Error al leer hojas del Excel: {str(e)}"}

def convertir_excel_a_csv(ruta_excel, ruta_salida=None, hoja=0, detectar_cabeceras=True):
    """Convierte un archivo Excel a CSV.
    
    Args:
        ruta_excel: Ruta al archivo Excel de origen
        ruta_salida: Ruta al archivo CSV de salida
        hoja: Nombre o índice de la hoja a convertir (por defecto la primera hoja)
        detectar_cabeceras: Intentar detectar si la primera fila son cabeceras
    """
    try:
        # Verificar que el archivo existe
        if not os.path.exists(ruta_excel):
            return {"error": f"El archivo {ruta_excel} no existe"}
        
        # Verificar que es un archivo Excel
        if not ruta_excel.endswith(('.xls', '.xlsx')):
            return {"error": f"El archivo {ruta_excel} no es un archivo Excel válido"}
        
        # Leer Excel
        try:
            df = pd.read_excel(ruta_excel, sheet_name=hoja)
        except ValueError as e:
            # Si el usuario pasó un nombre de hoja inválido, mostrar las hojas disponibles
            hojas_info = obtener_hojas_excel(ruta_excel)
            if "error" in hojas_info:
                return {"error": f"Error al leer archivo Excel: {str(e)}"}
            else:
                hojas_disponibles = ", ".join(hojas_info["hojas"])
                return {"error": f"Hoja '{hoja}' no encontrada. Hojas disponibles: {hojas_disponibles}"}
        
        # Detectar si la primera fila son cabeceras
        if detectar_cabeceras:
            # Si todos los valores de la primera fila son strings y no hay valores nulos,
            # es probable que sean cabeceras
            primera_fila = df.iloc[0]
            es_cabecera = all(isinstance(x, str) for x in primera_fila) and not primera_fila.isnull().any()
            
            if not es_cabecera and len(df) > 1:
                # Usar la primera fila como datos y agregar cabeceras genéricas
                columnas = [f"Columna{i+1}" for i in range(len(df.columns))]
                df.columns = columnas
        
        # Generar nombre de archivo de salida si no se proporciona
        if not ruta_salida:
            nombre_base = os.path.splitext(os.path.basename(ruta_excel))[0]
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Incluir nombre de hoja si no es la primera hoja
            if isinstance(hoja, str):
                nombre_hoja = hoja.replace(' ', '_')
                ruta_salida = f"{nombre_base}_{nombre_hoja}_{timestamp}.csv"
            else:
                ruta_salida = f"{nombre_base}_{timestamp}.csv"
        
        # Limpiar datos problemáticos antes de guardar
        # Limpieza de valores con comas que podrían causar problemas en conversión a enteros
        for columna in df.columns:
            if df[columna].dtype == 'object':  # Solo para columnas de texto
                # Reemplazar valores como '0, 0' por '0'
                df[columna] = df[columna].astype(str).str.replace(r'(\d+)\s*,\s*(\d+)', r'\1\2', regex=True)
                
                # Eliminar espacios en blanco al principio y final
                df[columna] = df[columna].str.strip()
                
                # Reemplazar valores vacíos por NaN
                df[columna] = df[columna].replace('', pd.NA)
        
        # Guardar como CSV
        df.to_csv(ruta_salida, index=False)
        
        # Intentar renombrar columnas si 'Nombre del procedimiento' no está presente
        # pero hay algo similar
        columnas_df = df.columns.tolist()
        tiene_columna_nombre = 'Nombre del procedimiento' in columnas_df
        columnas_similares = [
            col for col in columnas_df 
            if 'nombre' in col.lower() and ('proced' in col.lower() or 'examen' in col.lower())
        ]
        
        info_columnas = {
            "tiene_columna_nombre": tiene_columna_nombre,
            "columnas_similares": columnas_similares if columnas_similares else None
        }
        
        return {
            "exito": True,
            "archivo_salida": ruta_salida,
            "filas": len(df),
            "columnas": df.columns.tolist(),
            "info_columnas": info_columnas,
            "hoja_procesada": hoja
        }
    
    except Exception as e:
        return {"error": f"Error al convertir archivo: {str(e)}"}

def main():
    """Función principal para uso desde línea de comandos."""
    parser = argparse.ArgumentParser(description="Convertidor de Excel a CSV")
    parser.add_argument('excel', help='Ruta al archivo Excel a convertir')
    parser.add_argument('--salida', help='Ruta del archivo CSV de salida')
    parser.add_argument('--hoja', default=0, help='Índice o nombre de la hoja a convertir (por defecto: primera hoja)')
    parser.add_argument('--listar-hojas', action='store_true', help='Listar las hojas disponibles en el archivo')
    parser.add_argument('--no-detectar-cabeceras', action='store_true', help='No intentar detectar si la primera fila son cabeceras')
    
    args = parser.parse_args()
    
    # Si se solicita listar hojas
    if args.listar_hojas:
        hojas_info = obtener_hojas_excel(args.excel)
        if "error" in hojas_info:
            print(f"ERROR: {hojas_info['error']}")
            sys.exit(1)
        else:
            print(f"Hojas disponibles en {args.excel}:")
            for i, hoja in enumerate(hojas_info["hojas"]):
                print(f"  {i}: {hoja}")
            sys.exit(0)
    
    # Convertir hoja a entero si es posible
    try:
        hoja = int(args.hoja)
    except ValueError:
        hoja = args.hoja  # Si no es un número, usar como nombre de hoja
    
    # Realizar la conversión
    resultado = convertir_excel_a_csv(
        args.excel, 
        args.salida, 
        hoja=hoja,
        detectar_cabeceras=not args.no_detectar_cabeceras
    )
    
    if "error" in resultado:
        print(f"ERROR: {resultado['error']}")
        sys.exit(1)
    else:
        print(f"Conversión exitosa:")
        print(f"- Archivo generado: {resultado['archivo_salida']}")
        print(f"- Filas: {resultado['filas']}")
        print(f"- Hoja procesada: {resultado['hoja_procesada']}")
        print(f"- Columnas: {', '.join(resultado['columnas'])}")
        
        # Mostrar información sobre columnas relevantes
        if not resultado["info_columnas"]["tiene_columna_nombre"]:
            print("\nADVERTENCIA: No se encontró la columna 'Nombre del procedimiento'")
            if resultado["info_columnas"]["columnas_similares"]:
                print("Columnas similares encontradas que podrían contener nombres de procedimientos:")
                for col in resultado["info_columnas"]["columnas_similares"]:
                    print(f"  - {col}")
        
        sys.exit(0)

if __name__ == "__main__":
    main()