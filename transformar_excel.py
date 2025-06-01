#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transformador de Excel a CSV para archivos problemáticos
-------------------------------------------------------
Utiliza una estrategia más robusta para manejar archivos Excel con formatos problemáticos.
"""

import pandas as pd
import os
import sys
import subprocess
import tempfile
import shutil
import json
from datetime import datetime

def verificar_dependencias():
    """Verifica si las dependencias necesarias están instaladas."""
    try:
        # Intentar verificar si ssconvert está instalado (Gnumeric)
        result = subprocess.run(['which', 'ssconvert'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, 
                              text=True)
        
        if result.returncode == 0:
            return {'ssconvert': True}
        else:
            return {'ssconvert': False}
    except Exception:
        return {'ssconvert': False}

def convertir_con_python(ruta_excel, ruta_salida=None, hoja=0):
    """Intenta convertir el Excel a CSV usando Python (pandas)."""
    try:
        # Crear ruta de salida si no se proporciona
        if not ruta_salida:
            base_name = os.path.splitext(os.path.basename(ruta_excel))[0]
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            ruta_salida = os.path.join(os.path.dirname(ruta_excel), 
                                     f"{base_name}_{timestamp}.csv")
        
        # Intentar obtener nombres de hojas
        xls = pd.ExcelFile(ruta_excel)
        sheet_names = xls.sheet_names
        
        # Seleccionar hoja
        sheet_name = sheet_names[hoja] if isinstance(hoja, int) and 0 <= hoja < len(sheet_names) else hoja
        
        # Leer Excel forzando todo como texto
        df = pd.read_excel(ruta_excel, sheet_name=sheet_name, dtype=str)
        
        # Limpiar datos
        for col in df.columns:
            # Reemplazar NaN con cadenas vacías
            df[col] = df[col].fillna('')
            
            # Limpiar valores con coma (ej: '0, 0')
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(r'(\d+)\s*,\s*(\d+)', r'\1\2', regex=True)
        
        # Guardar como CSV
        df.to_csv(ruta_salida, index=False)
        
        return {
            'exito': True,
            'metodo': 'pandas',
            'ruta_csv': ruta_salida,
            'filas': len(df),
            'columnas': list(df.columns)
        }
    except Exception as e:
        print(f"Error al convertir con pandas: {str(e)}")
        return {'exito': False, 'metodo': 'pandas', 'error': str(e)}

def convertir_con_ssconvert(ruta_excel, ruta_salida=None, hoja=0):
    """Convierte un Excel a CSV usando ssconvert (Gnumeric)."""
    try:
        # Crear ruta de salida temporal si no se proporciona
        if not ruta_salida:
            base_name = os.path.splitext(os.path.basename(ruta_excel))[0]
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            ruta_salida = os.path.join(os.path.dirname(ruta_excel), 
                                     f"{base_name}_{timestamp}.csv")
        
        # Preparar el comando
        comando = ['ssconvert', ruta_excel, ruta_salida]
        
        # Ejecutar el comando
        result = subprocess.run(comando, 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, 
                              text=True)
        
        if result.returncode != 0:
            return {'exito': False, 'metodo': 'ssconvert', 'error': result.stderr}
        
        # Leer el CSV resultante para obtener información
        if os.path.exists(ruta_salida):
            df = pd.read_csv(ruta_salida)
            
            return {
                'exito': True,
                'metodo': 'ssconvert',
                'ruta_csv': ruta_salida,
                'filas': len(df),
                'columnas': list(df.columns)
            }
        else:
            return {'exito': False, 'metodo': 'ssconvert', 'error': 'No se generó el archivo CSV'}
    except Exception as e:
        return {'exito': False, 'metodo': 'ssconvert', 'error': str(e)}

def transformar_excel_a_csv(ruta_excel, ruta_salida=None, hoja=0):
    """
    Transforma un archivo Excel a CSV usando diversos métodos.
    
    Args:
        ruta_excel: Ruta al archivo Excel de origen
        ruta_salida: Ruta al archivo CSV de salida
        hoja: Índice o nombre de la hoja a convertir
        
    Returns:
        Dictionary con información del resultado
    """
    print(f"Transformando Excel a CSV: {ruta_excel}")
    
    # Crear CSV temporal si no se proporciona una ruta específica
    if not ruta_salida:
        base_name = os.path.splitext(os.path.basename(ruta_excel))[0]
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Si es un índice, usar nombres genéricos; si es un string, usar el nombre de la hoja
        hoja_str = f"hoja{hoja}" if isinstance(hoja, int) else hoja.replace(' ', '_')
        ruta_salida = os.path.join(os.path.dirname(ruta_excel), 
                                 f"{base_name}_{hoja_str}_{timestamp}.csv")
    
    # 1. Intentar con pandas directamente (el método más simple)
    resultado = convertir_con_python(ruta_excel, ruta_salida, hoja)
    if resultado['exito']:
        print(f"Conversión exitosa con pandas: {ruta_salida}")
        return resultado
    
    # 2. Verificar dependencias para métodos alternativos
    dependencias = verificar_dependencias()
    
    # 3. Intentar con ssconvert si está disponible
    if dependencias['ssconvert']:
        resultado = convertir_con_ssconvert(ruta_excel, ruta_salida, hoja)
        if resultado['exito']:
            print(f"Conversión exitosa con ssconvert: {ruta_salida}")
            return resultado
    
    # 4. Solución de último recurso: exportar a un formato intermedio y luego convertir
    try:
        # Crear directorio temporal
        temp_dir = tempfile.mkdtemp()
        temp_csv = os.path.join(temp_dir, "temp_output.csv")
        
        # Guardar un mensaje indicando que no se pudo convertir
        with open(temp_csv, 'w') as f:
            f.write("Error: No se pudo convertir el archivo Excel. El formato puede estar dañado o contener caracteres especiales incompatibles.\n")
            f.write(f"Archivo original: {ruta_excel}\n")
            f.write(f"Fecha de intento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Copiar el archivo temporal a la ruta de salida
        shutil.copy(temp_csv, ruta_salida)
        
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir)
        
        return {
            'exito': False,
            'metodo': 'fallback',
            'ruta_csv': ruta_salida,
            'error': 'No se pudo convertir el archivo Excel con ningún método disponible.'
        }
    except Exception as e:
        return {'exito': False, 'metodo': 'fallback', 'error': str(e)}

if __name__ == "__main__":
    # Procesar argumentos de línea de comandos
    if len(sys.argv) < 2:
        print("Uso: python transformar_excel.py ruta_excel [ruta_csv] [hoja]")
        sys.exit(1)
    
    ruta_excel = sys.argv[1]
    ruta_csv = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Procesar argumento de hoja
    hoja = 0  # Por defecto, primera hoja
    if len(sys.argv) > 3:
        try:
            # Intentar convertir a entero
            hoja = int(sys.argv[3])
        except ValueError:
            # Si no es un entero, usar como nombre de hoja
            hoja = sys.argv[3]
    
    # Ejecutar la transformación
    resultado = transformar_excel_a_csv(ruta_excel, ruta_csv, hoja)
    
    # Mostrar el resultado
    print(json.dumps(resultado, indent=2))