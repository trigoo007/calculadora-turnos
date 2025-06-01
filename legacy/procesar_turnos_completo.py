#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para procesar un archivo CSV con días de turno específicos
Maneja la lógica de días por turnos, con soporte para feriados
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

def obtener_dias_turno(fecha_turno, es_feriado=False):
    """
    Determina qué días completos deben incluirse para un turno.
    
    Reglas normales:
    - Lunes a jueves: incluye el propio día y el día siguiente
    - Viernes: incluye viernes, sábado y domingo
    - Sábado: incluye viernes, sábado y domingo
    - Domingo: incluye viernes, sábado, domingo y lunes
    
    Reglas para feriados:
    - Lunes a jueves: igual que domingo (viernes, sábado, domingo, lunes)
    - Viernes: igual que sábado (viernes, sábado, domingo)
    
    Retorna: lista de fechas (datetime) a incluir, horas del turno
    """
    dia_semana = fecha_turno.weekday()
    dias_incluir = []
    
    if es_feriado:
        if dia_semana == 4:  # Viernes feriado (como sábado)
            # Incluir viernes, sábado y domingo
            dias_incluir.append(fecha_turno)  # Viernes
            dias_incluir.append(fecha_turno + timedelta(days=1))  # Sábado
            dias_incluir.append(fecha_turno + timedelta(days=2))  # Domingo
            horas_turno = 24  # Como sábado: 09:00 a 09:00 (24 horas)
        else:  # Lunes a jueves feriado (como domingo)
            # Incluir viernes, sábado, domingo y lunes
            viernes_previo = fecha_turno - timedelta(days=((dia_semana + 3) % 7))
            dias_incluir.append(viernes_previo)  # Viernes
            dias_incluir.append(viernes_previo + timedelta(days=1))  # Sábado
            dias_incluir.append(viernes_previo + timedelta(days=2))  # Domingo
            dias_incluir.append(fecha_turno)  # Día actual (lunes a jueves)
            horas_turno = 23  # Como domingo: 09:00 a 08:00 (23 horas)
    else:
        if dia_semana < 4:  # Lunes a jueves
            # Incluir el día actual y el siguiente
            dias_incluir.append(fecha_turno)
            dias_incluir.append(fecha_turno + timedelta(days=1))
            horas_turno = 14  # 18:00 a 08:00 (14 horas)
        
        elif dia_semana == 4:  # Viernes
            # Incluir viernes, sábado y domingo
            dias_incluir.append(fecha_turno)  # Viernes
            dias_incluir.append(fecha_turno + timedelta(days=1))  # Sábado
            dias_incluir.append(fecha_turno + timedelta(days=2))  # Domingo
            horas_turno = 15  # 18:00 a 09:00 (15 horas)
        
        elif dia_semana == 5:  # Sábado
            # También incluir viernes, sábado y domingo
            dias_incluir.append(fecha_turno - timedelta(days=1))  # Viernes
            dias_incluir.append(fecha_turno)  # Sábado
            dias_incluir.append(fecha_turno + timedelta(days=1))  # Domingo
            horas_turno = 24  # 09:00 a 09:00 (24 horas)
        
        else:  # Domingo
            # Incluir viernes, sábado, domingo y lunes
            dias_incluir.append(fecha_turno - timedelta(days=2))  # Viernes
            dias_incluir.append(fecha_turno - timedelta(days=1))  # Sábado
            dias_incluir.append(fecha_turno)  # Domingo
            dias_incluir.append(fecha_turno + timedelta(days=1))  # Lunes
            horas_turno = 23  # 09:00 a 08:00 (23 horas)
    
    return dias_incluir, horas_turno

def main():
    """Función principal que procesa un archivo CSV con días de turno específicos."""
    if len(sys.argv) < 2:
        print("Uso: python3 procesar_turnos_completo.py <ruta_archivo_csv> [directorio_salida] [nombre_doctor]")
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
    print("\nIngresa las fechas de tus turnos (formato: dd-mmm-yyyy, ej: 08-abr-2025)")
    print("Ingresa una fecha por línea. Se te preguntará si el día es feriado.")
    print("Escribe 'fin' cuando termines.")
    
    fechas_turno = []
    dias_incluidos = set()
    total_horas = 0
    
    while True:
        entrada = input("\nFecha de turno (o 'fin' para terminar): ").strip()
        if entrada.lower() == 'fin':
            break
        
        try:
            fecha_turno = convertir_fecha_espanol(entrada)
            
            # Mostrar el día de la semana
            dia_semana_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][fecha_turno.weekday()]
            print(f"La fecha {fecha_turno.strftime('%d-%m-%Y')} es {dia_semana_nombre}")
            
            # Preguntar si es feriado
            es_feriado = input("¿Es día feriado? (s/n): ").strip().lower() == 's'
            
            fechas_turno.append((fecha_turno, es_feriado))
            
            # Obtener los días a incluir para este turno
            dias, horas = obtener_dias_turno(fecha_turno, es_feriado)
            total_horas += horas
            
            # Agregar días al conjunto
            for dia in dias:
                dias_incluidos.add(dia.strftime('%Y-%m-%d'))
            
            estado_feriado = "FERIADO" if es_feriado else "normal"
            print(f"Añadido turno del {dia_semana_nombre} {fecha_turno.strftime('%d-%m-%Y')} ({estado_feriado}, {horas} horas)")
            print(f"  Días incluidos: {', '.join([d.strftime('%d-%m-%Y (%A)') for d in dias])}")
        except Exception as e:
            print(f"Error al procesar la fecha: {e}")
            print("Formato correcto: dd-mmm-yyyy (ej: 08-abr-2025)")
    
    if not fechas_turno:
        print("No se ingresaron fechas de turno. Finalizando.")
        sys.exit(1)
    
    print(f"\nTurnos seleccionados: {len(fechas_turno)}")
    print(f"Días totales a incluir: {len(dias_incluidos)}")
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
        
        # Filtrar exámenes por días incluidos
        try:
            # Crear fechas en formato 'YYYY-MM-DD' para filtrar
            calculadora.data_filtrada['Fecha_YYYY_MM_DD'] = calculadora.data_filtrada['Fecha del procedimiento programado'].apply(
                lambda x: convertir_fecha_espanol(x).strftime('%Y-%m-%d')
            )
            
            # Filtrar solo por los días incluidos
            mask_dias_incluidos = calculadora.data_filtrada['Fecha_YYYY_MM_DD'].isin(dias_incluidos)
            examenes_incluidos = calculadora.data_filtrada[mask_dias_incluidos]
            
            # Si después del filtro no hay exámenes, informar y salir
            if examenes_incluidos.empty:
                print("No hay exámenes en los días seleccionados")
                sys.exit(1)
            
            # Copiar las columnas necesarias a examenes_contabilizados
            calculadora.examenes_contabilizados = examenes_incluidos[[
                'Número de cita',
                'Fecha sin hora',
                'Apellidos del paciente',
                'Nombre del paciente',
                'Nombre del procedimiento',
                'Sala de adquisición',
                'Tipo',
                'TAC doble'
            ]].copy()
            
            # Todos están en turno
            calculadora.examenes_contabilizados['En_Turno'] = True
            
            print(f"Total de exámenes en los días de turno: {len(calculadora.examenes_contabilizados)}")
            
            # Mostrar exámenes por día
            fechas_examen = calculadora.examenes_contabilizados['Fecha sin hora'].value_counts().sort_index()
            print("\nExámenes por día:")
            for fecha, count in fechas_examen.items():
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
                print(f"  {fecha_obj.strftime('%d-%m-%Y (%A)')}: {count} exámenes")
            
        except Exception as e:
            print(f"Error al filtrar por días: {e}")
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