#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para procesar un archivo CSV con la Calculadora de Turnos sin interfaz gráfica
Permite especificar fechas para filtrar los turnos
"""

import os
import sys
from datetime import datetime
from calculadora_turnos import CalculadoraTurnos
import pandas as pd
from dateutil import parser

def convertir_fecha_espanol(fecha_str):
    """Convierte una fecha en formato español a un objeto datetime."""
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
    """Función principal que procesa un archivo CSV directamente."""
    if len(sys.argv) < 2:
        print("Uso: python3 procesar_csv_con_fechas.py <ruta_archivo_csv> [directorio_salida] [nombre_doctor] [fecha_inicio] [fecha_fin]")
        print("Ejemplo de fechas: 01-abr-2025 30-abr-2025")
        sys.exit(1)
    
    # Obtener argumentos
    ruta_csv = sys.argv[1]
    directorio_salida = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(ruta_csv)
    nombre_doctor = sys.argv[3] if len(sys.argv) > 3 else "Cikutovic"
    
    # Obtener fechas si se proporcionan
    fecha_inicio = None
    fecha_fin = None
    if len(sys.argv) > 4:
        try:
            fecha_inicio_str = sys.argv[4]
            fecha_inicio = convertir_fecha_espanol(fecha_inicio_str)
            print(f"Fecha de inicio: {fecha_inicio.strftime('%d-%m-%Y')}")
        except Exception as e:
            print(f"Error al procesar la fecha de inicio: {e}")
            print("Usando todo el rango de fechas disponible")
    
    if len(sys.argv) > 5:
        try:
            fecha_fin_str = sys.argv[5]
            fecha_fin = convertir_fecha_espanol(fecha_fin_str)
            print(f"Fecha de fin: {fecha_fin.strftime('%d-%m-%Y')}")
        except Exception as e:
            print(f"Error al procesar la fecha de fin: {e}")
            print("Usando todo el rango de fechas disponible")
    
    print(f"Procesando archivo: {ruta_csv}")
    print(f"Directorio de salida: {directorio_salida}")
    print(f"Nombre del doctor: {nombre_doctor}")
    
    # Procesamiento personalizado con filtro de fechas
    try:
        # Crear instancia de la calculadora
        calculadora = CalculadoraTurnos()
        
        # Cargar el archivo CSV
        if not calculadora.cargar_archivo(ruta_csv):
            print("Error al cargar el archivo CSV")
            sys.exit(1)
        
        # Filtrar datos
        if not calculadora.filtrar_datos():
            print("Error al filtrar los datos")
            sys.exit(1)
        
        # Clasificar exámenes
        if not calculadora.clasificar_examenes():
            print("Error al clasificar los exámenes")
            sys.exit(1)
        
        # Contabilizar exámenes
        if not calculadora.contabilizar_examenes():
            print("Error al contabilizar los exámenes")
            sys.exit(1)
        
        # Si se proporcionaron fechas, filtrar los exámenes por rango de fechas
        if fecha_inicio or fecha_fin:
            try:
                # Convertir la columna de fecha a datetime para poder filtrar
                calculadora.examenes_contabilizados['Fecha_dt'] = pd.to_datetime(
                    calculadora.examenes_contabilizados['Fecha sin hora']
                )
                
                # Aplicar filtros según las fechas proporcionadas
                if fecha_inicio:
                    calculadora.examenes_contabilizados = calculadora.examenes_contabilizados[
                        calculadora.examenes_contabilizados['Fecha_dt'] >= fecha_inicio
                    ]
                
                if fecha_fin:
                    calculadora.examenes_contabilizados = calculadora.examenes_contabilizados[
                        calculadora.examenes_contabilizados['Fecha_dt'] <= fecha_fin
                    ]
                
                # Si después del filtro no hay exámenes, informar y salir
                if calculadora.examenes_contabilizados.empty:
                    print("No hay exámenes en el rango de fechas seleccionado")
                    sys.exit(1)
                
                print(f"Total de exámenes en el rango de fechas: {len(calculadora.examenes_contabilizados)}")
                
                # Eliminar la columna auxiliar que ya no necesitamos
                calculadora.examenes_contabilizados = calculadora.examenes_contabilizados.drop(columns=['Fecha_dt'])
                
            except Exception as e:
                print(f"Error al filtrar por fechas: {e}")
                sys.exit(1)
        
        # Calcular horas de turno con los datos filtrados
        if not calculadora.calcular_horas_turno():
            print("Error al calcular horas de turno")
            sys.exit(1)
        
        # Calcular honorarios
        if not calculadora.calcular_honorarios():
            print("Error al calcular honorarios")
            sys.exit(1)
        
        # Generar archivos Excel
        rutas_excel = calculadora.generar_excel(directorio_salida)
        if not rutas_excel:
            print("Error al generar archivos Excel")
            sys.exit(1)
        
        # Generar correo
        correo = calculadora.generar_correo(nombre_doctor)
        if not correo:
            print("Error al generar correo")
            sys.exit(1)
        
        # Imprimir resultados
        print("\nProcesamiento exitoso!")
        print("\nRESUMEN ECONÓMICO:")
        
        # Mostrar información de archivos generados
        print("\nARCHIVOS GENERADOS:")
        for nombre, ruta in rutas_excel.items():
            print(f"- {nombre}: {os.path.basename(ruta)}")
        
        # Formatear resultados económicos
        eco = calculadora.resultado_economico
        
        print(f"\nHoras trabajadas: {eco['horas_trabajadas']}")
        print(f"Honorarios por horas: ${eco['honorarios_hora']:,}")
        
        print(f"\nExámenes RX: {eco['rx_count']} (${eco['rx_total']:,})")
        print(f"Exámenes TAC: {eco['tac_count']} (${eco['tac_total']:,})")
        print(f"Exámenes TAC doble: {eco['tac_doble_count']} (${eco['tac_doble_total']:,})")
        
        print(f"\nTOTAL: ${eco['total']:,}")
        
        # Mostrar contenido del correo
        print("\nCORREO GENERADO:")
        print(f"Asunto: {correo['asunto']}")
        print(f"Cuerpo:\n{correo['cuerpo']}")
        
    except Exception as e:
        print(f"Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()