#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para procesar un archivo CSV contando solo las horas de turnos específicos
pero considerando todos los exámenes
"""

import os
import sys
from datetime import datetime, timedelta
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

def calcular_horas_turno(fecha_turno, es_feriado=False):
    """
    Calcula las horas de un turno según el día de la semana.
    
    Reglas normales:
    - Lunes a jueves: 14 horas (18:00 a 08:00)
    - Viernes: 15 horas (18:00 a 09:00)
    - Sábado: 24 horas (09:00 a 09:00)
    - Domingo: 23 horas (09:00 a 08:00)
    
    Reglas para feriados:
    - Lunes a jueves: 23 horas (como domingo)
    - Viernes: 24 horas (como sábado)
    """
    dia_semana = fecha_turno.weekday()
    
    if es_feriado:
        if dia_semana == 4:  # Viernes feriado
            return 24  # Como sábado: 09:00 a 09:00 (24 horas)
        else:  # Lunes a jueves feriado
            return 23  # Como domingo: 09:00 a 08:00 (23 horas)
    else:
        if dia_semana < 4:  # Lunes a jueves
            return 14  # 18:00 a 08:00 (14 horas)
        elif dia_semana == 4:  # Viernes
            return 15  # 18:00 a 09:00 (15 horas)
        elif dia_semana == 5:  # Sábado
            return 24  # 09:00 a 09:00 (24 horas)
        else:  # Domingo
            return 23  # 09:00 a 08:00 (23 horas)

def main():
    """Función principal que procesa un archivo CSV con días de turno específicos."""
    if len(sys.argv) < 3:
        print("Uso: python3 procesar_turnos_horas.py <ruta_archivo_csv> <fecha1>[,F] [<fecha2>[,F] ...] [output_dir] [nombre_doctor]")
        print("Ejemplo: python3 procesar_turnos_horas.py data.csv 08-abr-2025 09-abr-2025,F")
        print("Las fechas deben estar en formato dd-mmm-yyyy")
        print("Para indicar que una fecha es feriado, agrega ',F' después (sin espacios)")
        sys.exit(1)
    
    # Obtener argumentos
    ruta_csv = sys.argv[1]
    
    # Buscar el directorio de salida y nombre del doctor (si existen)
    directorio_salida = None
    nombre_doctor = "Cikutovic"
    
    # Recorrer argumentos restantes para encontrar fechas y opciones
    fechas_arg = []
    for i in range(2, len(sys.argv)):
        arg = sys.argv[i]
        # Si el argumento no contiene guiones, asumimos que no es una fecha
        if '-' not in arg:
            # Si no se ha definido directorio, este es el directorio
            if directorio_salida is None:
                directorio_salida = arg
            else:
                # Si ya hay directorio, este es el nombre del doctor
                nombre_doctor = arg
        else:
            # Es una fecha
            fechas_arg.append(arg)
    
    # Si no se definió directorio, usar el del CSV
    if directorio_salida is None:
        directorio_salida = os.path.dirname(ruta_csv)
    
    print(f"Procesando archivo: {ruta_csv}")
    print(f"Directorio de salida: {directorio_salida}")
    print(f"Nombre del doctor: {nombre_doctor}")
    print(f"Días de turno a considerar para horas: {fechas_arg}")
    
    # Procesar las fechas y calcular horas
    fechas_turno = []
    total_horas = 0
    
    for fecha_arg in fechas_arg:
        try:
            # Verificar si la fecha está marcada como feriado
            if ',F' in fecha_arg:
                fecha_str = fecha_arg.split(',F')[0]
                es_feriado = True
            else:
                fecha_str = fecha_arg
                es_feriado = False
            
            fecha_turno = convertir_fecha_espanol(fecha_str)
            fechas_turno.append((fecha_turno, es_feriado))
            
            # Calcular horas para este turno
            horas = calcular_horas_turno(fecha_turno, es_feriado)
            total_horas += horas
            
            dia_semana_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][fecha_turno.weekday()]
            estado_feriado = "FERIADO" if es_feriado else "normal"
            print(f"Turno del {dia_semana_nombre} {fecha_turno.strftime('%d-%m-%Y')} ({estado_feriado}, {horas} horas)")
        except Exception as e:
            print(f"Error al procesar la fecha {fecha_arg}: {e}")
            print("Formato correcto: dd-mmm-yyyy (ej: 08-abr-2025)")
    
    if not fechas_turno:
        print("No se ingresaron fechas de turno válidas. Finalizando.")
        sys.exit(1)
    
    print(f"\nTotal de horas de turno: {total_horas}")
    
    # Procesamiento del archivo pero considerando TODOS los exámenes
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
        
        # Sobrescribir las horas calculadas con nuestro total específico
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
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()