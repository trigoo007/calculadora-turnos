#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la funcionalidad básica de la calculadora
"""

import os
from calculadora_turnos import CalculadoraTurnos

def main():
    print("Test de funcionalidad básica de la calculadora")
    
    # Crear una instancia de la calculadora
    calculadora = CalculadoraTurnos()
    
    # Definir rutas
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_csv = os.path.join(ruta_actual, "csv", "Buscar-20250504200228.csv")
    
    # Crear directorio de salida
    directorio_salida = os.path.join(ruta_actual, "csv", "test_output")
    os.makedirs(directorio_salida, exist_ok=True)
    
    # Datos de turno
    nombre_doctor = "Doctor Test"
    fechas_turno = "05-may-2025"
    
    # Procesar archivo
    print(f"Procesando archivo: {ruta_csv}")
    print(f"Directorio de salida: {directorio_salida}")
    
    exito, resultado = calculadora.procesar_archivo(
        ruta_csv, 
        directorio_salida, 
        nombre_doctor, 
        fechas_turno
    )
    
    # Mostrar resultado
    if exito:
        print("¡Procesamiento exitoso!")
        print("\nResumen de resultados:")
        print(f"1. Total de horas: {resultado['resultado_economico']['horas_trabajadas']}")
        print(f"2. Exámenes RX: {resultado['resultado_economico']['rx_count']}")
        print(f"3. Exámenes TAC: {resultado['resultado_economico']['tac_count']}")
        print(f"4. TAC doble: {resultado['resultado_economico']['tac_doble_count']}")
        print(f"5. TAC triple: {resultado['resultado_economico']['tac_triple_count']}")
        print(f"6. Total: ${resultado['resultado_economico']['total']:,}")
        
        print("\nArchivos generados:")
        for nombre, ruta in resultado['rutas_excel'].items():
            print(f"- {nombre}: {os.path.basename(ruta)}")
        
        print("\nContenido del correo:")
        print(f"Asunto: {resultado['correo']['asunto']}")
        print(f"Cuerpo:\n{resultado['correo']['cuerpo']}")
    else:
        print(f"Error: {resultado}")

if __name__ == "__main__":
    main()