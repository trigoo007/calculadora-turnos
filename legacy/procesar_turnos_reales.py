#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para procesar un archivo CSV con días de turno específicos
Maneja correctamente las interfases entre días y los horarios de turno
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

def obtener_rango_turno(fecha_inicio_turno):
    """
    Calcula el rango exacto (fecha_inicio, fecha_fin) de un turno basado en el día de la semana.
    
    Reglas:
    - Lunes a Jueves: 18:00 a 08:00 del día siguiente
    - Viernes: 18:00 a 09:00 del sábado
    - Sábado: 09:00 a 09:00 del domingo
    - Domingo: 09:00 a 08:00 del lunes
    """
    dia_semana = fecha_inicio_turno.weekday()
    
    # Crear fechas con horas específicas
    fecha_inicio = fecha_inicio_turno.replace(hour=0, minute=0, second=0, microsecond=0)
    fecha_fin = fecha_inicio + timedelta(days=1)
    
    if dia_semana < 4:  # Lunes a jueves
        # El turno va de 18:00 a 08:00 del día siguiente
        fecha_inicio = fecha_inicio.replace(hour=18)
        fecha_fin = fecha_fin.replace(hour=8)
        horas_turno = 14
    elif dia_semana == 4:  # Viernes
        # El turno va de 18:00 a 09:00 del sábado
        fecha_inicio = fecha_inicio.replace(hour=18)
        fecha_fin = fecha_fin.replace(hour=9)
        horas_turno = 15
    elif dia_semana == 5:  # Sábado
        # El turno va de 09:00 a 09:00 del domingo
        fecha_inicio = fecha_inicio.replace(hour=9)
        fecha_fin = fecha_fin.replace(hour=9)
        horas_turno = 24
    else:  # Domingo
        # El turno va de 09:00 a 08:00 del lunes
        fecha_inicio = fecha_inicio.replace(hour=9)
        fecha_fin = fecha_fin.replace(hour=8)
        horas_turno = 23
    
    return fecha_inicio, fecha_fin, horas_turno

def main():
    """Función principal que procesa un archivo CSV con días de turno específicos."""
    if len(sys.argv) < 2:
        print("Uso: python3 procesar_turnos_reales.py <ruta_archivo_csv> [directorio_salida] [nombre_doctor]")
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
    print("La fecha corresponde al día en que COMIENZA el turno.")
    print("Ingresa una fecha por línea. Escribe 'fin' cuando termines.")
    
    fechas_turno = []
    rangos_turno = []
    
    while True:
        entrada = input("Fecha de inicio del turno (o 'fin' para terminar): ").strip()
        if entrada.lower() == 'fin':
            break
        
        try:
            fecha_inicio_turno = convertir_fecha_espanol(entrada)
            fecha_inicio, fecha_fin, horas = obtener_rango_turno(fecha_inicio_turno)
            
            fechas_turno.append(fecha_inicio_turno.strftime('%Y-%m-%d'))
            rangos_turno.append((fecha_inicio, fecha_fin, horas))
            
            dia_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][fecha_inicio_turno.weekday()]
            print(f"Añadido turno del {dia_semana} {fecha_inicio_turno.strftime('%d-%m-%Y')}")
            print(f"  Horario: {fecha_inicio.strftime('%d-%m-%Y %H:%M')} a {fecha_fin.strftime('%d-%m-%Y %H:%M')} ({horas} horas)")
        except Exception as e:
            print(f"Error al procesar la fecha: {e}")
            print("Formato correcto: dd-mmm-yyyy (ej: 08-abr-2025)")
    
    if not fechas_turno:
        print("No se ingresaron fechas de turno. Finalizando.")
        sys.exit(1)
    
    print(f"\nTurnos seleccionados: {len(fechas_turno)}")
    total_horas = sum(horas for _, _, horas in rangos_turno)
    print(f"Total de horas de turno: {total_horas}")
    
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
        
        # Filtrar exámenes por turnos específicos
        try:
            # Crear columnas de fecha y hora
            calculadora.data_filtrada['Datetime'] = pd.to_datetime(
                calculadora.data_filtrada['Fecha del procedimiento programado'] + ' ' + 
                calculadora.data_filtrada['Hora del procedimiento programado'],
                format='%d-%b-%Y %H:%M'
            )
            
            # Marcar exámenes realizados en alguno de los turnos
            calculadora.data_filtrada['En_Turno_Real'] = False
            
            for fecha_inicio, fecha_fin, _ in rangos_turno:
                # Marcar exámenes que estén dentro del rango de tiempo del turno
                mask_turno = ((calculadora.data_filtrada['Datetime'] >= fecha_inicio) & 
                             (calculadora.data_filtrada['Datetime'] <= fecha_fin))
                
                calculadora.data_filtrada.loc[mask_turno, 'En_Turno_Real'] = True
            
            # Actualizar examenes_contabilizados con solo los exámenes dentro de turnos
            examenes_en_turno = calculadora.data_filtrada[calculadora.data_filtrada['En_Turno_Real']]
            
            # Si después del filtro no hay exámenes, informar y salir
            if examenes_en_turno.empty:
                print("No hay exámenes en los horarios de turno seleccionados")
                sys.exit(1)
            
            # Copiar las columnas necesarias a examenes_contabilizados
            calculadora.examenes_contabilizados = examenes_en_turno[[
                'Número de cita',
                'Fecha sin hora',
                'Apellidos del paciente',
                'Nombre del paciente',
                'Nombre del procedimiento',
                'Sala de adquisición',
                'Tipo',
                'TAC doble',
                'En_Turno_Real'
            ]].rename(columns={'En_Turno_Real': 'En_Turno'}).copy()
            
            print(f"Total de exámenes en turnos: {len(calculadora.examenes_contabilizados)}")
            
        except Exception as e:
            print(f"Error al filtrar por turnos: {e}")
            print(f"Detalle: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        # Asignar horas de turno totales
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