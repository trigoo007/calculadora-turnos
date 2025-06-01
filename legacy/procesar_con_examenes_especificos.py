#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para procesar turnos incluyendo explícitamente exámenes específicos
"""

import os
import sys
import pandas as pd
from dateutil import parser
from datetime import datetime
from calculadora_turnos import CalculadoraTurnos

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
    """Calcula las horas de un turno según el día de la semana."""
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
    """Procesa turnos asegurando que ciertos exámenes sean incluidos explícitamente."""
    # Archivo CSV
    ruta_csv = '/Users/rodrigomunoz/Calculadora/csv/Buscar-20250504200228.csv'
    
    # Fechas de turnos
    fechas_arg = ["08-abr-2025", "13-abr-2025", "18-abr-2025", "21-abr-2025"]
    
    # IDs de exámenes que deben incluirse
    examenes_especificos = ["9865805", "9883701", "9887600"]
    
    # Directorio salida
    directorio_salida = '/Users/rodrigomunoz/Calculadora/csv'
    
    # Nombre doctor
    nombre_doctor = "Cikutovic"
    
    print(f"Procesando archivo: {ruta_csv}")
    print(f"Días de turno: {fechas_arg}")
    print(f"Exámenes específicos a incluir: {examenes_especificos}")
    
    # Calcular horas de turno
    total_horas = 0
    for fecha_str in fechas_arg:
        fecha_turno = convertir_fecha_espanol(fecha_str)
        horas = calcular_horas_turno(fecha_turno)
        total_horas += horas
        
        dia_semana_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][fecha_turno.weekday()]
        print(f"Turno del {dia_semana_nombre} {fecha_turno.strftime('%d-%m-%Y')} ({horas} horas)")
    
    print(f"\nTotal de horas de turno: {total_horas}")
    
    try:
        # Cargar el CSV directamente con pandas
        df_original = pd.read_csv(ruta_csv)
        
        # Limpiar formato de número de cita
        df_original['Número de cita'] = df_original['Número de cita'].astype(str).str.replace('"', '').str.replace('=', '')
        
        # Crear la calculadora y procesar normalmente
        calculadora = CalculadoraTurnos()
        calculadora.cargar_archivo(ruta_csv)
        calculadora.filtrar_datos()
        calculadora.clasificar_examenes()
        calculadora.contabilizar_examenes()
        
        # Conservar el DataFrame filtrado original
        df_filtrado_original = calculadora.data_filtrada.copy()
        
        # Verificar si los exámenes específicos están en los datos filtrados
        examenes_encontrados = df_filtrado_original[df_filtrado_original['Número de cita'].isin(examenes_especificos)]
        
        if examenes_encontrados.empty:
            print("\nLos exámenes específicos no fueron detectados en el filtrado normal.")
            
            # Buscar los exámenes específicos en los datos originales
            examenes_a_agregar = df_original[df_original['Número de cita'].isin(examenes_especificos)]
            
            if not examenes_a_agregar.empty:
                print(f"Se encontraron {len(examenes_a_agregar)} exámenes específicos en los datos originales.")
                
                # Asegurarnos de que tengan las mismas columnas que los datos filtrados
                for col in df_filtrado_original.columns:
                    if col not in examenes_a_agregar.columns:
                        examenes_a_agregar[col] = None
                
                # Asignar tipo y TAC doble
                examenes_a_agregar['Tipo'] = 'TAC'
                examenes_a_agregar['TAC doble'] = True
                examenes_a_agregar['En_Turno'] = True
                
                # Agregar la columna 'Fecha sin hora' necesaria para contabilización
                examenes_a_agregar['Fecha sin hora'] = examenes_a_agregar['Fecha del procedimiento programado'].apply(
                    lambda fecha_str: convertir_fecha_espanol(fecha_str).strftime('%Y-%m-%d')
                )
                
                # Agregar los exámenes a los datos filtrados
                df_filtrado_combinado = pd.concat([df_filtrado_original, examenes_a_agregar[df_filtrado_original.columns]])
                
                # Actualizar los datos filtrados en la calculadora
                calculadora.data_filtrada = df_filtrado_combinado
                
                # Actualizar los exámenes contabilizados
                calculadora.examenes_contabilizados = df_filtrado_combinado[[
                    'Número de cita',
                    'Fecha sin hora',
                    'Apellidos del paciente',
                    'Nombre del paciente',
                    'Nombre del procedimiento',
                    'Sala de adquisición',
                    'Tipo',
                    'TAC doble',
                    'En_Turno'
                ]].copy()
                
                print(f"Se agregaron {len(examenes_a_agregar)} exámenes específicos manualmente.")
            else:
                print("No se encontraron los exámenes específicos en los datos originales.")
        else:
            print(f"\nLos exámenes específicos ya fueron detectados en el filtrado normal ({len(examenes_encontrados)} exámenes).")
        
        # Sobrescribir las horas calculadas con nuestro total específico
        calculadora.resultado_economico['horas_trabajadas'] = total_horas
        
        # Calcular honorarios
        calculadora.calcular_honorarios()
        
        # Generar archivos Excel
        rutas_excel = calculadora.generar_excel(directorio_salida)
        
        # Generar correo
        correo = calculadora.generar_correo(nombre_doctor)
        
        # Mostrar resultados
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
        
        # Verificar que los exámenes específicos estén en el Excel generado
        print("\nVerificando exámenes específicos en el archivo Excel generado:")
        try:
            df_contabilizados = pd.read_excel(os.path.join(directorio_salida, 'Examenes_Contabilizados.xlsx'))
            df_contabilizados['Número de cita'] = df_contabilizados['Número de cita'].astype(str).str.replace('"', '').str.replace('=', '')
            
            examenes_en_excel = df_contabilizados[df_contabilizados['Número de cita'].isin(examenes_especificos)]
            
            if examenes_en_excel.empty:
                print("Los exámenes específicos NO se encuentran en el archivo Excel generado.")
            else:
                print(f"Se encontraron {len(examenes_en_excel)} de {len(examenes_especificos)} exámenes específicos en el Excel.")
                for idx, exam in examenes_en_excel.iterrows():
                    print(f"- {exam['Número de cita']}: {exam['Nombre del procedimiento']}")
        except Exception as e:
            print(f"Error al verificar el archivo Excel: {e}")
        
    except Exception as e:
        print(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()