#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para procesar un archivo CSV con la Calculadora de Turnos sin interfaz gráfica
"""

import os
import sys
from calculadora_turnos import CalculadoraTurnos

def main():
    """Función principal que procesa un archivo CSV directamente."""
    if len(sys.argv) < 2:
        print("Uso: python3 procesar_csv.py <ruta_archivo_csv> [directorio_salida] [nombre_doctor]")
        sys.exit(1)
    
    # Obtener argumentos
    ruta_csv = sys.argv[1]
    directorio_salida = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(ruta_csv)
    nombre_doctor = sys.argv[3] if len(sys.argv) > 3 else "Cikutovic"
    
    print(f"Procesando archivo: {ruta_csv}")
    print(f"Directorio de salida: {directorio_salida}")
    print(f"Nombre del doctor: {nombre_doctor}")
    
    # Crear instancia de la calculadora
    calculadora = CalculadoraTurnos()
    
    # Procesar archivo
    exito, resultado = calculadora.procesar_archivo(ruta_csv, directorio_salida, nombre_doctor)
    
    if exito:
        print("\nProcesamiento exitoso!")
        print("\nRESUMEN ECONÓMICO:")
        
        # Mostrar información de archivos generados
        print("\nARCHIVOS GENERADOS:")
        for nombre, ruta in resultado['rutas_excel'].items():
            print(f"- {nombre}: {os.path.basename(ruta)}")
        
        # Formatear resultados económicos
        eco = resultado['resultado_economico']
        
        print(f"\nHoras trabajadas: {eco['horas_trabajadas']}")
        print(f"Honorarios por horas: ${eco['honorarios_hora']:,}")
        
        print(f"\nExámenes RX: {eco['rx_count']} (${eco['rx_total']:,})")
        print(f"Exámenes TAC: {eco['tac_count']} (${eco['tac_total']:,})")
        print(f"Exámenes TAC doble: {eco['tac_doble_count']} (${eco['tac_doble_total']:,})")
        
        print(f"\nTOTAL: ${eco['total']:,}")
        
        # Mostrar contenido del correo
        print("\nCORREO GENERADO:")
        print(f"Asunto: {resultado['correo']['asunto']}")
        print(f"Cuerpo:\n{resultado['correo']['cuerpo']}")
    else:
        print(f"Error al procesar el archivo: {resultado}")

if __name__ == "__main__":
    main()