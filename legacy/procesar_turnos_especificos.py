#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para procesar un archivo CSV con días de turno específicos
Permite al usuario indicar exactamente qué días considerar como turnos
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
    """Función principal que procesa un archivo CSV con días de turno específicos."""
    if len(sys.argv) < 2:
        print("Uso: python3 procesar_turnos_especificos.py <ruta_archivo_csv> [directorio_salida] [nombre_doctor]")
        print("Luego se te pedirá ingresar los días específicos de turno")
        sys.exit(1)
    
    # Obtener argumentos
    ruta_csv = sys.argv[1]
    directorio_salida = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(ruta_csv)
    nombre_doctor = sys.argv[3] if len(sys.argv) > 3 else "Cikutovic"
    
    print(f"Procesando archivo: {ruta_csv}")
    print(f"Directorio de salida: {directorio_salida}")
    print(f"Nombre del doctor: {nombre_doctor}")
    
    # Obtener fechas específicas de turno
    print("\nIngresa las fechas específicas de turno (formato: dd-mmm-yyyy, ej: 08-abr-2025)")
    print("Ingresa una fecha por línea. Escribe 'fin' cuando termines.")
    
    dias_turno = []
    while True:
        entrada = input("Fecha de turno (o 'fin' para terminar): ").strip()
        if entrada.lower() == 'fin':
            break
        
        try:
            fecha = convertir_fecha_espanol(entrada)
            dias_turno.append(fecha.strftime('%Y-%m-%d'))
            print(f"Añadido: {fecha.strftime('%d-%m-%Y')}")
        except Exception as e:
            print(f"Error al procesar la fecha: {e}")
            print("Formato correcto: dd-mmm-yyyy (ej: 08-abr-2025)")
    
    if not dias_turno:
        print("No se ingresaron fechas de turno. Finalizando.")
        sys.exit(1)
    
    print(f"\nFechas de turno seleccionadas: {', '.join([datetime.strptime(f, '%Y-%m-%d').strftime('%d/%m/%Y') for f in dias_turno])}")
    
    # Procesamiento personalizado con días de turno específicos
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
        
        # Filtrar por días de turno específicos
        try:
            # Convertir la columna de fecha a datetime para poder filtrar
            calculadora.examenes_contabilizados['Fecha_dt'] = pd.to_datetime(
                calculadora.examenes_contabilizados['Fecha sin hora']
            )
            
            # Filtrar solo por los días de turno especificados
            calculadora.examenes_contabilizados = calculadora.examenes_contabilizados[
                calculadora.examenes_contabilizados['Fecha sin hora'].isin(dias_turno)
            ]
            
            # Si después del filtro no hay exámenes, informar y salir
            if calculadora.examenes_contabilizados.empty:
                print("No hay exámenes en los días de turno seleccionados")
                sys.exit(1)
            
            print(f"Total de exámenes en los días de turno seleccionados: {len(calculadora.examenes_contabilizados)}")
            
            # Eliminar la columna auxiliar que ya no necesitamos
            calculadora.examenes_contabilizados = calculadora.examenes_contabilizados.drop(columns=['Fecha_dt'])
            
        except Exception as e:
            print(f"Error al filtrar por días de turno: {e}")
            sys.exit(1)
        
        # Calcular horas de turno con los datos filtrados
        # Para cada día específico, calcular las horas según el día de la semana
        total_horas = 0
        for fecha_str in dias_turno:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
            dia_semana = fecha.weekday()
            
            # Determinar la duración del turno según el día
            if dia_semana < 4:  # Lunes a jueves
                horas_turno = 14  # 18:00 a 08:00 (14 horas)
            elif dia_semana == 4:  # Viernes
                horas_turno = 15  # 18:00 a 09:00 (15 horas)
            elif dia_semana == 5:  # Sábado
                horas_turno = 24  # 09:00 a 09:00 (24 horas)
            else:  # Domingo
                horas_turno = 23  # 09:00 a 08:00 (23 horas)
            
            total_horas += horas_turno
            print(f"Día {fecha.strftime('%d/%m/%Y')} ({['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][dia_semana]}): {horas_turno} horas")
        
        calculadora.resultado_economico['horas_trabajadas'] = total_horas
        
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