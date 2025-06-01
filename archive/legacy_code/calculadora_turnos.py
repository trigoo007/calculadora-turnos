#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculadora de Turnos en Radiología
-----------------------------------
Aplicación para procesar datos de procedimientos médicos en radiología,
clasificar exámenes, calcular horas trabajadas y generar reportes.

Incluye sistema de aprendizaje para identificar y clasificar procedimientos
de manera automática, con soporte para TAC normal, doble y triple.
"""

import os
import sys
import csv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil import parser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import tempfile
import smtplib
import calendar

# Importar sistema de aprendizaje SQLite
try:
    from aprendizaje_datos_sqlite import SistemaAprendizajeSQLite
except ImportError:
    print("Error: No se pudo importar el sistema de aprendizaje SQLite.")
    print("Asegúrese de que el archivo aprendizaje_datos_sqlite.py esté en el mismo directorio.")
    SistemaAprendizajeSQLite = None

try:
    from tkcalendar import Calendar, DateEntry
except ImportError:
    # Mensaje de error amigable si la biblioteca no está instalada
    print("Error: La biblioteca 'tkcalendar' no está instalada.")
    print("Por favor, instálela usando: pip install tkcalendar")
    # Importamos un calendario básico para evitar errores fatales
    Calendar = None
    DateEntry = None

class CalculadoraTurnos:
    """Clase principal para la calculadora de turnos en radiología."""
    
    def __init__(self):
        self.data = None
        self.data_filtrada = None
        self.examenes_contabilizados = None
        self.resultado_economico = {
            'horas_trabajadas': 0,
            'rx_count': 0,
            'tac_count': 0,
            'tac_doble_count': 0,
            'tac_triple_count': 0,
            'rx_total': 0,
            'tac_total': 0,
            'tac_doble_total': 0,
            'tac_triple_total': 0,
            'honorarios_hora': 0,
            'total': 0
        }
        
        # Inicializar sistema de aprendizaje SQLite
        self.sistema_aprendizaje = None
        if SistemaAprendizajeSQLite is not None:
            try:
                self.sistema_aprendizaje = SistemaAprendizajeSQLite()
            except Exception as e:
                print(f"Error al inicializar el sistema de aprendizaje: {e}")
        
        # Tarifas
        self.TARIFA_HORA = 55000
        self.TARIFA_RX = 5300
        self.TARIFA_TAC = 42400
        self.TARIFA_TAC_DOBLE = 84800    # 2x TARIFA_TAC  
        self.TARIFA_TAC_TRIPLE = 127200  # 3x TARIFA_TAC
        
        # Columnas esperadas en el CSV
        self.columnas_esperadas = [
            'Número de cita',
            'Fecha del procedimiento programado',
            'Hora del procedimiento programado',
            'Apellidos del paciente',
            'Nombre del paciente',
            'ID del paciente',
            'Nombre del procedimiento',
            'Sala de adquisición'
        ]
    
    def cargar_archivo(self, ruta_archivo):
        """Carga y valida el archivo CSV."""
        try:
            # Verificar si el archivo existe
            if not os.path.exists(ruta_archivo):
                raise FileNotFoundError(f"El archivo {ruta_archivo} no existe.")
            
            # Leer el archivo CSV
            df = pd.read_csv(ruta_archivo)
            
            # Verificar columnas
            for col in self.columnas_esperadas:
                if col not in df.columns:
                    raise ValueError(f"El archivo no contiene la columna '{col}'")
            
            self.data = df
            return True, f"Archivo cargado exitosamente: {len(df)} registros"
        except Exception as e:
            print(f"Error al cargar el archivo: {e}")
            return False, f"Error al cargar el archivo: {str(e)}"
    
    def filtrar_datos(self):
        """Filtra los datos según los criterios especificados."""
        if self.data is None:
            return False, "No hay datos cargados para filtrar"
        
        try:
            # Filtrar salas que comienzan con SCA o SJ
            mask_incluir = (
                self.data['Sala de adquisición'].str.startswith('SCA') | 
                self.data['Sala de adquisición'].str.startswith('SJ')
            )
            
            # Excluir salas que comienzan con HOS
            mask_excluir = ~self.data['Sala de adquisición'].str.startswith('HOS')
            
            # Aplicar filtros
            self.data_filtrada = self.data[mask_incluir & mask_excluir].copy()
            
            n_registros = len(self.data_filtrada)
            return True, f"Datos filtrados correctamente: {n_registros} registros resultantes"
        except Exception as e:
            print(f"Error al filtrar datos: {e}")
            return False, f"Error al filtrar datos: {str(e)}"
    
    def clasificar_examenes(self):
        """Clasifica los exámenes según el criterio especificado, usando el sistema de aprendizaje."""
        if self.data_filtrada is None:
            return False, "No hay datos filtrados para clasificar"
        
        try:
            # Clasificar como RX o TAC
            self.data_filtrada['Tipo'] = 'RX'
            mask_tac = self.data_filtrada['Nombre del procedimiento'].str.contains('TAC', case=False, na=False)
            self.data_filtrada.loc[mask_tac, 'Tipo'] = 'TAC'
            
            # Inicializar columnas para TAC doble y triple
            self.data_filtrada['TAC doble'] = False
            self.data_filtrada['TAC triple'] = False
            
            # Si tenemos el sistema de aprendizaje disponible, usarlo para clasificación avanzada
            if self.sistema_aprendizaje is not None:
                # Para cada procedimiento, verificar su clasificación según el sistema de aprendizaje
                for idx, row in self.data_filtrada.iterrows():
                    nombre_proc = row['Nombre del procedimiento']
                    if row['Tipo'] == 'TAC':  # Solo analizar procedimientos TAC
                        # Clasificar procedimiento
                        clasificacion = self.sistema_aprendizaje.clasificar_procedimiento(nombre_proc)
                        
                        # Asignar subtipo según la clasificación
                        if clasificacion['subtipo'] == 'TRIPLE':
                            self.data_filtrada.at[idx, 'TAC triple'] = True
                        elif clasificacion['subtipo'] == 'DOBLE':
                            self.data_filtrada.at[idx, 'TAC doble'] = True
            else:
                # Fallback: Usar el método tradicional para TAC doble si no hay sistema de aprendizaje
                # Identificar TAC doble
                tac_dobles = [
                    "Tórax, abdomen y pelvis",
                    "AngioTAC de tórax, abdomen y pelvis"
                ]
                
                # Criterios adicionales para TAC doble
                tac_dobles_adicionales = [
                    "TX/ABD/PEL",
                    "Angio Tórax Abdomen y Pelvis"
                ]
                
                # Identificar TAC doble según criterios oficiales
                mask_tac_doble_oficiales = self.data_filtrada['Nombre del procedimiento'].isin(tac_dobles)
                
                # Identificar TAC doble según criterios adicionales
                mask_tac_doble_adicionales = False
                for criterio in tac_dobles_adicionales:
                    mask_tac_doble_adicionales |= self.data_filtrada['Nombre del procedimiento'].str.contains(criterio, case=False, na=False)
                
                # Combinar todas las condiciones para identificar TAC doble
                self.data_filtrada['TAC doble'] = mask_tac_doble_oficiales | mask_tac_doble_adicionales
            
            # Aprender de los nuevos datos
            if self.sistema_aprendizaje is not None:
                try:
                    # Analizar DataFrame para extraer información de procedimientos y salas
                    self.sistema_aprendizaje.analizar_dataframe(self.data_filtrada)
                except Exception as e:
                    print(f"Advertencia: No se pudo analizar datos para aprendizaje: {e}")
            
            # Contar tipos de exámenes
            rx_count = len(self.data_filtrada[self.data_filtrada['Tipo'] == 'RX'])
            tac_count = len(self.data_filtrada[self.data_filtrada['Tipo'] == 'TAC'])
            tac_doble_count = sum(self.data_filtrada['TAC doble']) if 'TAC doble' in self.data_filtrada.columns else 0
            tac_triple_count = sum(self.data_filtrada['TAC triple']) if 'TAC triple' in self.data_filtrada.columns else 0
            
            mensaje = f"Exámenes clasificados: {rx_count} RX, {tac_count} TAC"
            if tac_doble_count > 0:
                mensaje += f", {tac_doble_count} TAC doble"
            if tac_triple_count > 0:
                mensaje += f", {tac_triple_count} TAC triple"
            
            return True, mensaje
        except Exception as e:
            print(f"Error al clasificar exámenes: {e}")
            return False, f"Error al clasificar exámenes: {str(e)}"
    
    def asignar_a_turno(self, fecha):
        """
        Determina a qué turno pertenece un examen basado en su fecha.
        Los turnos contemplan las interfaces entre días y la lógica especial de fin de semana.
        
        Reglas:
        - Lunes a jueves: incluye exámenes del propio día y del día siguiente
        - Viernes: incluye exámenes del viernes, sábado y posiblemente domingo
        - Sábado: incluye exámenes del viernes, sábado, domingo y posiblemente lunes
        - Domingo: incluye exámenes del viernes, sábado, domingo y lunes
        """
        try:
            # Manejo especial para formato español (ej. "08-abr-2025")
            meses_esp = {
                'ene': 'jan', 'feb': 'feb', 'mar': 'mar', 'abr': 'apr',
                'may': 'may', 'jun': 'jun', 'jul': 'jul', 'ago': 'aug',
                'sep': 'sep', 'oct': 'oct', 'nov': 'nov', 'dic': 'dec'
            }
            
            # Convertir formato español a formato reconocible por dateutil
            for mes_esp, mes_eng in meses_esp.items():
                if mes_esp in fecha.lower():
                    fecha = fecha.lower().replace(mes_esp, mes_eng)
                    break
            
            # Convertir la fecha usando dateutil.parser
            dt = parser.parse(fecha)
            
            # Obtener el día de la semana (0=lunes, 6=domingo)
            dia_semana = dt.weekday()
            
            # La lógica de asignación de turnos
            if 0 <= dia_semana <= 3:  # Lunes a jueves
                # El examen puede ser del día actual o del día siguiente
                return True
            
            elif dia_semana == 4:  # Viernes
                # Exámenes del viernes se asignan al turno
                return True
            
            elif dia_semana == 5:  # Sábado
                # Exámenes del sábado se asignan al turno
                return True
            
            elif dia_semana == 6:  # Domingo
                # Exámenes del domingo se asignan al turno
                return True
            
            return True  # Por defecto, asignar todos los exámenes
                
        except Exception as e:
            print(f"Error al asignar a turno: {e}")
            return True  # Si hay algún error, incluir el examen por defecto
    
    def contabilizar_examenes(self):
        """
        Contabiliza todos los exámenes de salas SJ y SCA.
        Todos los exámenes filtrados serán contabilizados para el cálculo económico.
        """
        if self.data_filtrada is None:
            return False
        
        try:
            # Función para convertir fechas en formato español a formato reconocible
            def convertir_fecha(fecha_str):
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
                
                return parser.parse(fecha_lower).strftime('%Y-%m-%d')
            
            # Crear columna de fecha sin hora con conversión de formato español
            self.data_filtrada['Fecha sin hora'] = self.data_filtrada['Fecha del procedimiento programado'].apply(convertir_fecha)
            
            # Asignar todos los exámenes a turnos según la fecha
            self.data_filtrada['En_Turno'] = self.data_filtrada['Fecha sin hora'].apply(self.asignar_a_turno)
            
            # Contabilizar todos los exámenes filtrados
            self.examenes_contabilizados = self.data_filtrada[[
                'Número de cita',
                'Fecha sin hora',
                'Apellidos del paciente',
                'Nombre del paciente',
                'Nombre del procedimiento',
                'Sala de adquisición',
                'Tipo',
                'TAC doble',
                'TAC triple',
                'En_Turno'
            ]].copy()
            
            return True
        except Exception as e:
            print(f"Error al contabilizar exámenes: {e}")
            return False
    
    def calcular_horas_turno(self):
        """Calcula las horas trabajadas según los turnos."""
        if self.examenes_contabilizados is None:
            return False
        
        try:
            # Obtener las fechas únicas de los exámenes en turno
            fechas_unicas = self.examenes_contabilizados['Fecha sin hora'].unique()
            
            total_horas = 0
            
            for fecha_str in fechas_unicas:
                # Ya tenemos las fechas en formato 'YYYY-MM-DD' gracias a contabilizar_examenes
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
            
            self.resultado_economico['horas_trabajadas'] = total_horas
            
            return True
        except Exception as e:
            print(f"Error al calcular horas de turno: {e}")
            return False
    
    def calcular_honorarios(self):
        """Calcula los honorarios por exámenes y horas trabajadas."""
        if self.examenes_contabilizados is None:
            return False
        
        try:
            # Contar exámenes por tipo
            self.resultado_economico['rx_count'] = len(self.examenes_contabilizados[
                (self.examenes_contabilizados['Tipo'] == 'RX')
            ])
            
            self.resultado_economico['tac_count'] = len(self.examenes_contabilizados[
                (self.examenes_contabilizados['Tipo'] == 'TAC') & 
                (self.examenes_contabilizados['TAC doble'] == False) &
                (self.examenes_contabilizados['TAC triple'] == False)
            ])
            
            self.resultado_economico['tac_doble_count'] = len(self.examenes_contabilizados[
                (self.examenes_contabilizados['TAC doble'] == True) &
                (self.examenes_contabilizados['TAC triple'] == False)  # Priorizar triple si ambos están marcados
            ])
            
            self.resultado_economico['tac_triple_count'] = len(self.examenes_contabilizados[
                self.examenes_contabilizados['TAC triple'] == True
            ])
            
            # Calcular honorarios por tipo
            self.resultado_economico['rx_total'] = self.resultado_economico['rx_count'] * self.TARIFA_RX
            self.resultado_economico['tac_total'] = self.resultado_economico['tac_count'] * self.TARIFA_TAC
            self.resultado_economico['tac_doble_total'] = self.resultado_economico['tac_doble_count'] * self.TARIFA_TAC_DOBLE
            self.resultado_economico['tac_triple_total'] = self.resultado_economico['tac_triple_count'] * self.TARIFA_TAC_TRIPLE
            
            # Calcular honorarios por horas
            self.resultado_economico['honorarios_hora'] = self.resultado_economico['horas_trabajadas'] * self.TARIFA_HORA
            
            # Calcular total
            self.resultado_economico['total'] = (
                self.resultado_economico['rx_total'] +
                self.resultado_economico['tac_total'] +
                self.resultado_economico['tac_doble_total'] +
                self.resultado_economico['tac_triple_total'] +
                self.resultado_economico['honorarios_hora']
            )
            
            return True
        except Exception as e:
            print(f"Error al calcular honorarios: {e}")
            return False
    
    def generar_excel(self, directorio_salida):
        """Genera los archivos Excel con los resultados en formato específico."""
        if self.data_filtrada is None or self.examenes_contabilizados is None:
            return False
        
        try:
            # Función para seleccionar y reordenar columnas
            def preparar_tabla_minimalista(df):
                """Selecciona y reordena las columnas esenciales en un orden lógico."""
                # Seleccionar solo las columnas esenciales
                columnas = [
                    'Número de cita',
                    'Fecha del procedimiento programado',
                    'Apellidos del paciente',
                    'Nombre del paciente',
                    'Nombre del procedimiento',
                    'Sala de adquisición'
                ]
                
                # Asegurar que todas las columnas existen
                columnas_disponibles = [col for col in columnas if col in df.columns]
                
                # Crear una copia con las columnas seleccionadas
                df_min = df[columnas_disponibles].copy()
                
                # Renombrar columnas para que sean más cortas y elegantes
                nombres_nuevos = {
                    'Número de cita': 'Nº Cita',
                    'Fecha del procedimiento programado': 'Fecha',
                    'Apellidos del paciente': 'Apellidos',
                    'Nombre del paciente': 'Nombre',
                    'Nombre del procedimiento': 'Procedimiento',
                    'Sala de adquisición': 'Sala'
                }
                
                # Aplicar nuevos nombres
                df_min.rename(columns=nombres_nuevos, inplace=True)
                
                return df_min
            
            # Aplicar estilo al archivo Excel
            def aplicar_estilo_excel(writer, df, sheet_name):
                """Aplica un estilo elegante y minimalista a la hoja de Excel."""
                # Escribir DataFrame a la hoja de Excel
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Obtener la hoja de trabajo
                worksheet = writer.sheets[sheet_name]
                
                # Ajustar ancho de columnas (autofit)
                for i, col in enumerate(df.columns):
                    # Obtener longitud máxima del contenido de la columna
                    max_len = max(
                        df[col].astype(str).map(len).max(),
                        len(str(col))
                    ) + 2  # Agregar un poco de espacio
                    
                    # Establecer ancho columna (letra columna Excel, ancho)
                    col_letter = chr(65 + i)  # A, B, C, ...
                    worksheet.column_dimensions[col_letter].width = max_len
                
                # Otras mejoras de estilo se aplicarían aquí si openpyxl lo permitiera
                # Sin embargo, muchas características de estilo requieren funcionalidades avanzadas
            
            # 1. Generar archivo solo para TAC
            ruta_tac = os.path.join(directorio_salida, 'Tabla_TAC.xlsx')
            with pd.ExcelWriter(ruta_tac, engine='openpyxl') as writer:
                # TABLA TAC (SCA y SJ)
                df_tac = self.data_filtrada[
                    (self.data_filtrada['Tipo'] == 'TAC') & 
                    ((self.data_filtrada['Sala de adquisición'].str.startswith('SCA')) |
                     (self.data_filtrada['Sala de adquisición'].str.startswith('SJ')))
                ]
                # Aplicar formato minimalista
                df_tac_min = preparar_tabla_minimalista(df_tac)
                # Guardar con estilo
                aplicar_estilo_excel(writer, df_tac_min, 'TAC (SCA y SJ)')
                
                # Filtrar TAC SCA
                df_tac_sca = self.data_filtrada[
                    (self.data_filtrada['Tipo'] == 'TAC') & 
                    (self.data_filtrada['Sala de adquisición'].str.startswith('SCA'))
                ]
                # Aplicar formato minimalista
                df_tac_sca_min = preparar_tabla_minimalista(df_tac_sca)
                # Guardar con estilo
                aplicar_estilo_excel(writer, df_tac_sca_min, 'TAC SCA')
                
                # Filtrar TAC SJ
                df_tac_sj = self.data_filtrada[
                    (self.data_filtrada['Tipo'] == 'TAC') & 
                    (self.data_filtrada['Sala de adquisición'].str.startswith('SJ'))
                ]
                # Aplicar formato minimalista
                df_tac_sj_min = preparar_tabla_minimalista(df_tac_sj)
                # Guardar con estilo
                aplicar_estilo_excel(writer, df_tac_sj_min, 'TAC SJ')
            
            # 2. Generar archivo solo para RX
            ruta_rx = os.path.join(directorio_salida, 'Tabla_RX.xlsx')
            with pd.ExcelWriter(ruta_rx, engine='openpyxl') as writer:
                # TABLA RX (SCA y SJ)
                df_rx = self.data_filtrada[
                    (self.data_filtrada['Tipo'] == 'RX') & 
                    ((self.data_filtrada['Sala de adquisición'].str.startswith('SCA')) |
                     (self.data_filtrada['Sala de adquisición'].str.startswith('SJ')))
                ]
                # Aplicar formato minimalista
                df_rx_min = preparar_tabla_minimalista(df_rx)
                # Guardar con estilo
                aplicar_estilo_excel(writer, df_rx_min, 'RX (SCA y SJ)')
                
                # Filtrar RX SCA
                df_rx_sca = self.data_filtrada[
                    (self.data_filtrada['Tipo'] == 'RX') & 
                    (self.data_filtrada['Sala de adquisición'].str.startswith('SCA'))
                ]
                # Aplicar formato minimalista
                df_rx_sca_min = preparar_tabla_minimalista(df_rx_sca)
                # Guardar con estilo
                aplicar_estilo_excel(writer, df_rx_sca_min, 'RX SCA')
                
                # Filtrar RX SJ
                df_rx_sj = self.data_filtrada[
                    (self.data_filtrada['Tipo'] == 'RX') & 
                    (self.data_filtrada['Sala de adquisición'].str.startswith('SJ'))
                ]
                # Aplicar formato minimalista
                df_rx_sj_min = preparar_tabla_minimalista(df_rx_sj)
                # Guardar con estilo
                aplicar_estilo_excel(writer, df_rx_sj_min, 'RX SJ')
            
            # 3. Generar archivo para el contenido del correo (Excel y TXT)
            ruta_correo_excel = os.path.join(directorio_salida, 'Contenido_Correo.xlsx')
            ruta_correo_txt = os.path.join(directorio_salida, 'Contenido_Correo.txt')
            
            # Generar correo para obtener su contenido
            nombre_doctor = "Doctor"  # Valor por defecto
            correo_info = self.generar_correo(nombre_doctor)
            
            if correo_info:
                # Guardar en Excel para compatibilidad
                df_correo = pd.DataFrame({
                    'Tipo': ['Asunto', 'Cuerpo'],
                    'Contenido': [correo_info['asunto'], correo_info['cuerpo']]
                })
                df_correo.to_excel(ruta_correo_excel, index=False)
                
                # Guardar también como archivo de texto plano
                with open(ruta_correo_txt, 'w', encoding='utf-8') as f:
                    f.write(correo_info['cuerpo'])
            
            # 4. Generar archivo para el análisis monetario (Resumen_Economico)
            ruta_analisis = os.path.join(directorio_salida, 'Analisis_Monetario.xlsx')
            
            # Calcular total de TAC físicos (para informes oficiales, contar TAC doble y triple como múltiples TAC individuales)
            tac_fisicos_informes = self.resultado_economico['tac_count'] + self.resultado_economico['tac_doble_count'] + self.resultado_economico['tac_triple_count']
            # Para efectos de valor, consideramos el valor total
            tac_valor_total = self.resultado_economico['tac_total'] + self.resultado_economico['tac_doble_total'] + self.resultado_economico['tac_triple_total']
            
            # Para el informe, contar dobles como 2 TAC y triples como 3 TAC
            tac_conteo_total = self.resultado_economico['tac_count'] + (self.resultado_economico['tac_doble_count'] * 2) + (self.resultado_economico['tac_triple_count'] * 3)
            
            # Crear DataFrame con el resumen económico (sin mencionar TAC doble/triple en informe oficial)
            df_resumen = pd.DataFrame({
                'Concepto': [
                    'Horas trabajadas',
                    'Exámenes RX',
                    'Exámenes TAC',
                    'Honorarios por horas',
                    'Honorarios por RX',
                    'Honorarios por TAC',
                    'TOTAL'
                ],
                'Cantidad': [
                    self.resultado_economico['horas_trabajadas'],
                    self.resultado_economico['rx_count'],
                    tac_conteo_total,  # Suma contando TAC doble como 2 y triple como 3
                    '-',
                    '-',
                    '-',
                    '-'
                ],
                'Monto': [
                    self.resultado_economico['honorarios_hora'],
                    self.resultado_economico['rx_total'],
                    tac_valor_total,  # Suma de valores TAC normales + TAC doble + TAC triple
                    '-',
                    '-',
                    '-',
                    self.resultado_economico['total']
                ]
            })
            
            df_resumen.to_excel(ruta_analisis, index=False)
            
            # También creamos un archivo oculto con detalles técnicos para uso interno
            ruta_detalles = os.path.join(directorio_salida, 'Detalles_Tecnicos.xlsx')
            with pd.ExcelWriter(ruta_detalles, engine='openpyxl') as writer:
                # Detalles de exámenes contabilizados en formato minimalista
                examenes_min = preparar_tabla_minimalista(self.examenes_contabilizados)
                aplicar_estilo_excel(writer, examenes_min, 'Exámenes Contabilizados')
                
                # Detalles de TAC doble para revisar (también en formato minimalista)
                tac_dobles = self.data_filtrada[self.data_filtrada['TAC doble'] == True]
                tac_dobles_min = preparar_tabla_minimalista(tac_dobles)
                aplicar_estilo_excel(writer, tac_dobles_min, 'TAC Doble')
                
                # Detalles de TAC triple para revisar
                tac_triples = self.data_filtrada[self.data_filtrada['TAC triple'] == True]
                tac_triples_min = preparar_tabla_minimalista(tac_triples)
                aplicar_estilo_excel(writer, tac_triples_min, 'TAC Triple')
            
            return {
                'tabla_tac': ruta_tac,
                'tabla_rx': ruta_rx,
                'contenido_correo': ruta_correo_excel,
                'contenido_correo_txt': ruta_correo_txt,
                'analisis_monetario': ruta_analisis,
                'detalles_tecnicos': ruta_detalles
            }
        
        except Exception as e:
            print(f"Error al generar archivos Excel: {e}")
            return False
    
    def generar_correo(self, nombre_doctor):
        """Genera el contenido del correo formal según el formato especificado."""
        if self.examenes_contabilizados is None:
            return None
        
        try:
            # Determinar el período basado en las fechas de los turnos
            if hasattr(self, 'fechas_seleccionadas') and self.fechas_seleccionadas:
                # Si hay fechas seleccionadas explícitamente, usarlas para determinar el período
                meses_num = {
                    'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
                }
                
                meses_nombre = {
                    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril', 5: 'mayo', 6: 'junio',
                    7: 'julio', 8: 'agosto', 9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
                }
                
                meses = []
                for fecha in self.fechas_seleccionadas:
                    try:
                        # Extraer el mes (formato dd-mmm-yyyy)
                        partes = fecha.split('-')
                        if len(partes) >= 3 and partes[1] in meses_num:
                            mes_num = meses_num[partes[1]]
                            if mes_num not in meses:
                                meses.append(mes_num)
                    except:
                        continue
                
                if meses:
                    # Si tenemos meses identificados, usar el más común
                    mes_periodo = max(set(meses), key=meses.count)
                    periodo = meses_nombre[mes_periodo]
                else:
                    # Si no podemos determinar, usar el mes actual
                    periodo = datetime.now().strftime('%B').lower()
            else:
                # Si no hay fechas explícitas, usar las fechas de los exámenes
                fechas_unicas = self.examenes_contabilizados['Fecha sin hora'].unique()
                if len(fechas_unicas) > 0:
                    # Convertir a objetos datetime y obtener el mes más común
                    meses = [datetime.strptime(fecha, '%Y-%m-%d').month for fecha in fechas_unicas]
                    mes_periodo = max(set(meses), key=meses.count)
                    
                    # Mapear número de mes a nombre
                    meses_nombre = {
                        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril', 5: 'mayo', 6: 'junio',
                        7: 'julio', 8: 'agosto', 9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
                    }
                    periodo = meses_nombre[mes_periodo]
                else:
                    # Si no hay fechas, usar el mes actual
                    periodo = datetime.now().strftime('%B').lower()
            
            # Formatear las fechas de manera más simple
            if hasattr(self, 'fechas_seleccionadas') and self.fechas_seleccionadas:
                # Extraer solo los días de las fechas (formato dd-mmm-yyyy)
                dias = []
                for fecha in self.fechas_seleccionadas:
                    try:
                        # Extraer solo el día
                        dia = fecha.split('-')[0]
                        # Quitar ceros a la izquierda
                        dia = str(int(dia))
                        dias.append(dia)
                    except:
                        continue
                
                # Formatear elegantemente los días en lenguaje natural
                if len(dias) == 1:
                    fechas_str = dias[0]
                elif len(dias) == 2:
                    fechas_str = f"{dias[0]} y {dias[1]}"
                else:
                    # Ordenar los días numéricamente antes de formatear
                    dias_ordenados = sorted([int(d) for d in dias])
                    dias_str = [str(d) for d in dias_ordenados]
                    
                    # Identificar secuencias consecutivas para formato más natural
                    secuencias = []
                    secuencia_actual = [dias_ordenados[0]]
                    
                    for i in range(1, len(dias_ordenados)):
                        if dias_ordenados[i] == dias_ordenados[i-1] + 1:
                            secuencia_actual.append(dias_ordenados[i])
                        else:
                            if len(secuencia_actual) > 0:
                                secuencias.append(secuencia_actual)
                                secuencia_actual = [dias_ordenados[i]]
                    
                    if secuencia_actual:
                        secuencias.append(secuencia_actual)
                    
                    # Convertir secuencias a formato de texto
                    partes = []
                    for seq in secuencias:
                        if len(seq) == 1:
                            partes.append(str(seq[0]))
                        elif len(seq) == 2:
                            partes.append(f"{seq[0]} y {seq[1]}")
                        else:
                            partes.append(f"{seq[0]} al {seq[-1]}")
                    
                    # Unir las partes con comas y "y" antes del último elemento
                    if len(partes) == 1:
                        fechas_str = partes[0]
                    elif len(partes) == 2:
                        fechas_str = f"{partes[0]} y {partes[1]}"
                    else:
                        partes_excepto_ultima = partes[:-1]
                        ultima_parte = partes[-1]
                        fechas_str = ", ".join(partes_excepto_ultima) + " y " + ultima_parte
            else:
                # Si no hay fechas seleccionadas, usar las de los exámenes
                fechas_unicas = self.examenes_contabilizados['Fecha sin hora'].unique()
                dias = [datetime.strptime(fecha, '%Y-%m-%d').strftime('%d') for fecha in fechas_unicas]
                
                # Asegurar que los días no tengan ceros a la izquierda
                dias = [str(int(dia)) for dia in dias]
                
                # Formatear elegantemente los días en lenguaje natural
                if len(dias) == 1:
                    fechas_str = dias[0]
                elif len(dias) == 2:
                    fechas_str = f"{dias[0]} y {dias[1]}"
                else:
                    # Ordenar los días numéricamente antes de formatear
                    dias_ordenados = sorted([int(d) for d in dias])
                    dias_str = [str(d) for d in dias_ordenados]
                    
                    # Identificar secuencias consecutivas para formato más natural
                    secuencias = []
                    secuencia_actual = [dias_ordenados[0]]
                    
                    for i in range(1, len(dias_ordenados)):
                        if dias_ordenados[i] == dias_ordenados[i-1] + 1:
                            secuencia_actual.append(dias_ordenados[i])
                        else:
                            if len(secuencia_actual) > 0:
                                secuencias.append(secuencia_actual)
                                secuencia_actual = [dias_ordenados[i]]
                    
                    if secuencia_actual:
                        secuencias.append(secuencia_actual)
                    
                    # Convertir secuencias a formato de texto
                    partes = []
                    for seq in secuencias:
                        if len(seq) == 1:
                            partes.append(str(seq[0]))
                        elif len(seq) == 2:
                            partes.append(f"{seq[0]} y {seq[1]}")
                        else:
                            partes.append(f"{seq[0]} al {seq[-1]}")
                    
                    # Unir las partes con comas y "y" antes del último elemento
                    if len(partes) == 1:
                        fechas_str = partes[0]
                    elif len(partes) == 2:
                        fechas_str = f"{partes[0]} y {partes[1]}"
                    else:
                        partes_excepto_ultima = partes[:-1]
                        ultima_parte = partes[-1]
                        fechas_str = ", ".join(partes_excepto_ultima) + " y " + ultima_parte
            
            # Calcular total de TAC (contando dobles como 2 TAC y triples como 3 TAC)
            tac_conteo_total = self.resultado_economico['tac_count'] + (self.resultado_economico['tac_doble_count'] * 2) + (self.resultado_economico['tac_triple_count'] * 3)
            
            # Crear el contenido del correo con el formato solicitado
            asunto = f"Informe de turnos y exámenes realizados - {periodo.capitalize()} {datetime.now().year}"
            
            cuerpo = f"""Estimado Dr. {nombre_doctor}:

Junto con saludarle, le envío el informe detallado de los turnos realizados durante el período de {periodo} {datetime.now().year}.

**Detalle de turnos:**
- Días de turnos realizados: {fechas_str}.
- Total de horas: {self.resultado_economico['horas_trabajadas']} hrs.

**Exámenes informados (SCA y SJ):**
- Radiografías (RX): {self.resultado_economico['rx_count']}
- Tomografías (TAC): {tac_conteo_total}

Adjunto encontrará el archivo con el detalle completo de los exámenes realizados en SCA y SJ.

Quedo atento a sus comentarios.

Saludos cordiales,"""
            
            return {
                'asunto': asunto,
                'cuerpo': cuerpo
            }
        
        except Exception as e:
            print(f"Error al generar correo: {e}")
            return None
    
    def calcular_horas_turno_especificas(self, fechas_arg):
        """Calcula las horas de turno para las fechas específicas proporcionadas."""
        from dateutil import parser
        
        # Función para convertir fecha española a objeto datetime
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
        
        # Función para calcular horas según día de la semana
        def calcular_horas_turno(fecha_turno, es_feriado=False):
            """
            Calcula las horas de un turno según el día de la semana.
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
        
        return total_horas

    def procesar_archivo(self, ruta_archivo, directorio_salida, nombre_doctor, fechas_turno=None):
        """Procesa el archivo completo y genera todos los resultados."""
        # Cargar el archivo CSV
        if not self.cargar_archivo(ruta_archivo):
            return False, "Error al cargar el archivo CSV"
        
        # Filtrar datos
        if not self.filtrar_datos():
            return False, "Error al filtrar los datos"
        
        # Clasificar exámenes
        if not self.clasificar_examenes():
            return False, "Error al clasificar los exámenes"
        
        # Contabilizar exámenes en turno
        if not self.contabilizar_examenes():
            return False, "Error al contabilizar exámenes en turno"
        
        # Si se proporcionaron fechas de turno específicas, calcular horas manualmente
        if fechas_turno and fechas_turno.strip():
            fechas_lista = [fecha.strip() for fecha in fechas_turno.split(',')]
            total_horas = self.calcular_horas_turno_especificas(fechas_lista)
            # Sobrescribir las horas calculadas
            self.resultado_economico['horas_trabajadas'] = total_horas
        else:
            # Calcular horas de turno automáticamente
            if not self.calcular_horas_turno():
                return False, "Error al calcular horas de turno"
        
        # Calcular honorarios
        if not self.calcular_honorarios():
            return False, "Error al calcular honorarios"
        
        # Generar archivos Excel
        rutas_excel = self.generar_excel(directorio_salida)
        if not rutas_excel:
            return False, "Error al generar archivos Excel"
        
        # Generar correo
        correo = self.generar_correo(nombre_doctor)
        if not correo:
            return False, "Error al generar correo"
        
        return True, {
            'rutas_excel': rutas_excel,
            'correo': correo,
            'resultado_economico': self.resultado_economico
        }
    
    def estimar_dias_turno(self, dataframe=None):
        """
        Estima los posibles días de turno basados en la detección de duplas.
        
        Busca días consecutivos con alta concentración de exámenes (duplas) y 
        selecciona el primer día de cada dupla como día de turno.
        
        Límites: Mínimo 2 turnos, máximo 6 turnos.
        
        Args:
            dataframe: DataFrame opcional con datos de exámenes. Si no se proporciona,
                      usa self.data_filtrada
        
        Returns:
            Lista de tuplas (fecha_formateada, num_examenes) donde fecha_formateada
            está en formato dd-mmm-yyyy
        """
        # Usar dataframe proporcionado o self.data_filtrada
        datos = dataframe if dataframe is not None else self.data_filtrada
        
        if datos is None or datos.empty:
            return []
        
        try:
            # Determinar la columna de fecha
            columna_fecha = None
            if 'Fecha del procedimiento programado' in datos.columns:
                columna_fecha = 'Fecha del procedimiento programado'
            elif 'Fecha' in datos.columns:
                columna_fecha = 'Fecha'
            else:
                # Buscar primera columna que contenga 'fecha' o 'Fecha'
                for col in datos.columns:
                    if 'fecha' in col.lower():
                        columna_fecha = col
                        break
                
                if columna_fecha is None:
                    print("No se encontró columna de fecha válida")
                    return []
            
            # Convertir fechas a formato estandarizado
            datos['Fecha_dt'] = pd.to_datetime(
                datos[columna_fecha], 
                dayfirst=True,  # Asumiendo formato día/mes/año
                errors='coerce'
            )
            
            # Filtrar filas con fechas válidas
            datos_validos = datos.dropna(subset=['Fecha_dt'])
            
            if datos_validos.empty:
                print("No hay fechas válidas para procesar")
                return []
            
            # Agrupar por fecha y contar exámenes
            conteo_diario = datos_validos.groupby(datos_validos['Fecha_dt'].dt.date).size().sort_index()
            
            # Calcular umbral dinámico para detectar días con alta concentración
            promedio = conteo_diario.mean()
            umbral_alto = max(promedio * 1.2, 4)  # Días con alta concentración
            
            # Identificar días con alta concentración
            dias_alta_concentracion = conteo_diario[conteo_diario >= umbral_alto]
            
            if dias_alta_concentracion.empty:
                print("No se encontraron días con alta concentración de exámenes")
                return []
            
            # Detectar duplas (días consecutivos con alta concentración)
            fechas_duplas = []
            fechas_ordenadas = sorted(dias_alta_concentracion.index)
            
            i = 0
            while i < len(fechas_ordenadas):
                fecha_actual = fechas_ordenadas[i]
                examenes_actual = conteo_diario[fecha_actual]
                
                # Verificar si el siguiente día también tiene alta concentración (dupla)
                if i + 1 < len(fechas_ordenadas):
                    fecha_siguiente = fechas_ordenadas[i + 1]
                    diferencia_dias = (fecha_siguiente - fecha_actual).days
                    
                    if diferencia_dias == 1:  # Días consecutivos = DUPLA
                        examenes_siguiente = conteo_diario[fecha_siguiente]
                        total_examenes = examenes_actual + examenes_siguiente
                        
                        # Agregar el PRIMER día de la dupla
                        fechas_duplas.append((fecha_actual, total_examenes, "DUPLA"))
                        i += 2  # Saltar ambos días de la dupla
                        continue
                
                # Si no hay dupla pero tiene alta concentración, considerarlo como turno individual
                fechas_duplas.append((fecha_actual, examenes_actual, "INDIVIDUAL"))
                i += 1
            
            # Ordenar por total de exámenes (mayor a menor) y aplicar límites
            fechas_duplas.sort(key=lambda x: x[1], reverse=True)
            
            # Aplicar límites: mínimo 2, máximo 6 turnos
            max_turnos = min(6, len(fechas_duplas))
            min_turnos = min(2, len(fechas_duplas))
            
            turnos_seleccionados = fechas_duplas[:max_turnos] if len(fechas_duplas) >= min_turnos else []
            
            # Convertir a formato legible (dd-mmm-yyyy)
            meses_esp = {
                1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun',
                7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
            }
            
            fechas_estimadas = []
            for fecha, total_examenes, tipo in turnos_seleccionados:
                dia = fecha.day
                mes = meses_esp[fecha.month]
                anio = fecha.year
                fecha_esp = f"{dia:02d}-{mes}-{anio}"
                fechas_estimadas.append((fecha_esp, total_examenes))
            
            print(f"Estimación completada: {len(fechas_estimadas)} turnos detectados")
            return fechas_estimadas
            
        except Exception as e:
            print(f"Error al estimar días de turno: {e}")
            return []


class App:
    """Interfaz gráfica para la calculadora de turnos."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Turnos en Radiología")
        self.root.geometry("800x700")  # Aumentamos el tamaño para acomodar el calendario
        self.root.resizable(True, True)
        
        self.calculadora = CalculadoraTurnos()
        self.ruta_csv = None
        self.directorio_salida = None
        self.fechas_seleccionadas = []  # Lista para almacenar las fechas seleccionadas
        
        # Configurar manejo de excepciones para toda la aplicación
        self.configurar_manejo_excepciones()
        
        self.setup_ui()
    
    def configurar_manejo_excepciones(self):
        """Configura un manejador de excepciones para capturar errores no controlados."""
        def reportar_error(exc_type, exc_value, exc_traceback):
            # Formatear el error para mostrarlo
            import traceback
            error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            
            # Registrar en consola
            print("ERROR NO CONTROLADO:")
            print(error_msg)
            
            # Intentar mostrar un mensaje al usuario
            try:
                messagebox.showerror("Error en la aplicación", 
                                    "Ha ocurrido un error inesperado. Por favor, reinicie la aplicación.\n\n" + 
                                    str(exc_value))
            except:
                pass
            
            # Prevenir cierre inmediato si es posible
            return True  # True indica que hemos manejado la excepción
        
        # Establecer el manejador de excepciones para la interfaz
        self.root.report_callback_exception = reportar_error
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Estilo para ttk
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#ccc")
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = ttk.Label(
            main_frame, 
            text="Calculadora de Turnos en Radiología",
            font=("Helvetica", 16, "bold")
        )
        titulo.pack(pady=10)
        
        # Frame para selección de archivo
        file_frame = ttk.LabelFrame(main_frame, text="Selección de Archivo", padding="10")
        file_frame.pack(fill=tk.X, pady=10)
        
        self.lbl_archivo = ttk.Label(file_frame, text="Ningún archivo seleccionado")
        self.lbl_archivo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        btn_seleccionar = ttk.Button(
            file_frame, 
            text="Seleccionar CSV", 
            command=self.seleccionar_archivo
        )
        btn_seleccionar.pack(side=tk.RIGHT, padx=5)
        
        # Mensaje informativo sobre archivo CSV
        ttk.Label(file_frame, 
                text="Por favor seleccione un archivo CSV con los datos de los exámenes", 
                foreground="blue").pack(anchor=tk.W, padx=5, pady=2)
        
        # Nota: Ya no mostramos el frame para seleccionar directorio de salida
        # Los resultados se guardarán automáticamente en la carpeta csv/TURNOS MES AÑO
        
        # Frame para nombre del doctor y fechas
        doctor_frame = ttk.LabelFrame(main_frame, text="Información del Doctor", padding="10")
        doctor_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(doctor_frame, text="Nombre del Doctor:").pack(side=tk.LEFT, padx=5)
        
        self.entry_doctor = ttk.Entry(doctor_frame, width=30)
        self.entry_doctor.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry_doctor.insert(0, "Cikutovic")  # Valor por defecto
        
        # Frame para días de turno
        turnos_frame = ttk.LabelFrame(main_frame, text="Días de Turno", padding="10")
        turnos_frame.pack(fill=tk.X, pady=10)
        
        # Verificar si tkcalendar está disponible
        if Calendar is not None:
            # Versión con calendario visual
            self.setup_calendario_completo(turnos_frame)
        else:
            # Versión alternativa con entrada de texto básica
            self.setup_entrada_texto_basica(turnos_frame)
        
        # Frame para botones de acción
        btn_frame = ttk.Frame(main_frame, padding="10")
        btn_frame.pack(fill=tk.X, pady=20)
        
        btn_procesar = ttk.Button(
            btn_frame, 
            text="Procesar Archivo", 
            command=self.procesar_archivo,
            style="TButton"
        )
        btn_procesar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        btn_ver_correo = ttk.Button(
            btn_frame, 
            text="Ver Correo", 
            command=self.ver_correo,
            style="TButton"
        )
        btn_ver_correo.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
        
        # Frame para resultados
        self.result_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
        self.result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Text widget para mostrar resultados
        self.txt_resultados = tk.Text(self.result_frame, height=10, wrap=tk.WORD)
        self.txt_resultados.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar para el text widget
        scrollbar = ttk.Scrollbar(self.txt_resultados)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_resultados.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.txt_resultados.yview)
        
        # Frame para botones de acceso rápido a Excel
        self.excel_frame = ttk.Frame(self.result_frame)
        self.excel_frame.pack(fill=tk.X, pady=5)
        
        # Botones para abrir Excel
        self.btn_rx_excel = ttk.Button(
            self.excel_frame,
            text="Ver RX",
            command=lambda: self.abrir_excel_tabla("RX (SCA y SJ)"),
            state=tk.DISABLED
        )
        self.btn_rx_excel.pack(side=tk.LEFT, padx=5)
        
        self.btn_tac_excel = ttk.Button(
            self.excel_frame,
            text="Ver TAC",
            command=lambda: self.abrir_excel_tabla("TAC (SCA y SJ)"),
            state=tk.DISABLED
        )
        self.btn_tac_excel.pack(side=tk.LEFT, padx=5)
        
        self.btn_resumen_excel = ttk.Button(
            self.excel_frame,
            text="Ver Resumen Económico",
            command=lambda: self.abrir_excel_resumen(),
            state=tk.DISABLED
        )
        self.btn_resumen_excel.pack(side=tk.LEFT, padx=5)
        
        # Frame para informar estado
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.lbl_status = ttk.Label(
            status_frame, 
            text="Listo para procesar", 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.lbl_status.pack(fill=tk.X)
    
    def seleccionar_archivo(self):
        """Abre diálogo para seleccionar archivo CSV."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo CSV",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        
        if file_path:
            self.ruta_csv = file_path
            self.lbl_archivo.config(text=os.path.basename(file_path))
            self.lbl_status.config(text=f"Archivo seleccionado: {os.path.basename(file_path)}")
    
    def seleccionar_directorio(self):
        """Abre diálogo para seleccionar directorio de salida."""
        directory = filedialog.askdirectory(
            title="Seleccionar directorio para archivos de salida"
        )
        
        if directory:
            self.directorio_salida = directory
            self.lbl_directorio.config(text=directory)
            self.lbl_status.config(text=f"Directorio de salida: {directory}")
    
    def agregar_fecha(self):
        """Agrega la fecha seleccionada en el calendario a la lista."""
        try:
            # Obtener la fecha seleccionada directamente del calendario
            fecha_str = self.cal.get_date()  # En formato dd/mm/yyyy
            
            # Convertir a objeto datetime
            day, month, year = fecha_str.split('/')
            fecha_dt = datetime(int(year), int(month), int(day))
            
            # Formatear en español: dd-mmm-yyyy
            meses_esp = {
                1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun',
                7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
            }
            
            fecha_esp = f"{fecha_dt.day:02d}-{meses_esp[fecha_dt.month]}-{fecha_dt.year}"
            
            # Mostrar información de depuración en la barra de estado
            self.lbl_status.config(text=f"Fecha seleccionada: {fecha_str} → {fecha_esp}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar la fecha: {e}")
            return
        
        # Verificar si es feriado
        es_feriado = self.es_feriado_var.get()
        
        # Crear texto a mostrar y agregar a la lista
        if es_feriado:
            texto_fecha = f"{fecha_esp},F (FERIADO)"
            fecha_almacenada = f"{fecha_esp},F"
        else:
            texto_fecha = fecha_esp
            fecha_almacenada = fecha_esp
        
        # Verificar si la fecha ya existe
        if fecha_almacenada in [f.split(' ')[0] for f in self.fechas_seleccionadas]:
            messagebox.showwarning("Fecha duplicada", f"La fecha {fecha_esp} ya ha sido agregada.")
            return
        
        # Agregar a la lista de fechas seleccionadas
        self.fechas_seleccionadas.append(fecha_almacenada)
        
        # Mostrar en la listbox
        self.listbox_fechas.insert(tk.END, texto_fecha)
        
        # Actualizar el campo oculto para compatibilidad
        self.entry_turnos.delete(0, tk.END)
        self.entry_turnos.insert(0, ','.join(self.fechas_seleccionadas))
        
        # Desactivar la opción de feriado después de agregar
        self.es_feriado_var.set(False)
        
        # Actualizar estado
        self.lbl_status.config(text=f"Fecha agregada: {texto_fecha}")
    
    def eliminar_ultima_fecha(self):
        """Elimina la última fecha agregada a la lista."""
        if self.fechas_seleccionadas:
            # Eliminar la última fecha
            ultima_fecha = self.fechas_seleccionadas.pop()
            
            # Eliminar de la listbox (el último elemento)
            self.listbox_fechas.delete(tk.END)
            
            # Actualizar el campo oculto
            self.entry_turnos.delete(0, tk.END)
            self.entry_turnos.insert(0, ','.join(self.fechas_seleccionadas))
            
            # Actualizar estado
            self.lbl_status.config(text=f"Última fecha eliminada: {ultima_fecha}")
        else:
            messagebox.showinfo("Información", "No hay fechas para eliminar.")
    
    def limpiar_fechas(self):
        """Elimina todas las fechas de la lista."""
        if self.fechas_seleccionadas:
            # Preguntar confirmación
            respuesta = messagebox.askyesno(
                "Confirmar", 
                "¿Está seguro de eliminar todas las fechas seleccionadas?"
            )
            
            if respuesta:
                # Limpiar la lista de fechas
                self.fechas_seleccionadas = []
                
                # Limpiar la listbox
                self.listbox_fechas.delete(0, tk.END)
                
                # Limpiar el campo oculto
                self.entry_turnos.delete(0, tk.END)
                
                # Actualizar estado
                self.lbl_status.config(text="Se han eliminado todas las fechas")
        else:
            messagebox.showinfo("Información", "No hay fechas para eliminar.")
    
    def setup_calendario_completo(self, parent_frame):
        """Configura la interfaz con calendario visual para selección de fechas."""
        # Panel superior para selección de fechas
        select_frame = ttk.Frame(parent_frame)
        select_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        # Panel izquierdo para el calendario
        calendar_frame = ttk.Frame(select_frame)
        calendar_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Crear un calendario para seleccionar fechas
        ttk.Label(calendar_frame, text="Seleccione las fechas de turno:").pack(anchor=tk.W, pady=2)
        
        current_date = datetime.now()
        
        # Frame para el calendario y la etiqueta de fecha
        cal_container = ttk.Frame(calendar_frame)
        cal_container.pack(pady=5)
        
        self.cal = Calendar(cal_container, 
                          selectmode='day',
                          year=current_date.year,
                          month=current_date.month,
                          day=current_date.day,
                          firstweekday='monday',
                          showweeknumbers=False,
                          date_pattern='dd/mm/yyyy')  # Formato de fecha más estándar
        self.cal.pack(padx=5, pady=5)
        
        # Etiqueta para mostrar la fecha actual seleccionada
        self.lbl_fecha_actual = ttk.Label(cal_container, 
                                        text=f"Fecha: {current_date.day} de {current_date.strftime('%B')} de {current_date.year}", 
                                        font=("Helvetica", 10, "bold"))
        self.lbl_fecha_actual.pack(pady=5)
        
        # Configurar evento cuando se cambia la fecha
        self.cal.bind("<<CalendarSelected>>", self.actualizar_etiqueta_fecha)
        
        # Panel derecho para botones y días seleccionados
        control_frame = ttk.Frame(select_frame)
        control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Botones para agregar fechas y marcar como feriado
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.es_feriado_var = tk.BooleanVar(value=False)
        chk_feriado = ttk.Checkbutton(btn_frame, text="Es feriado", variable=self.es_feriado_var)
        chk_feriado.pack(side=tk.LEFT, padx=5)
        
        btn_agregar = ttk.Button(btn_frame, text="Agregar fecha", command=self.agregar_fecha)
        btn_agregar.pack(side=tk.LEFT, padx=5)
        
        btn_eliminar = ttk.Button(btn_frame, text="Eliminar última fecha", command=self.eliminar_ultima_fecha)
        btn_eliminar.pack(side=tk.LEFT, padx=5)
        
        btn_limpiar = ttk.Button(btn_frame, text="Limpiar todas", command=self.limpiar_fechas)
        btn_limpiar.pack(side=tk.LEFT, padx=5)
        
        # Lista de fechas seleccionadas
        ttk.Label(control_frame, text="Fechas seleccionadas:").pack(anchor=tk.W, pady=2)
        
        # Frame para la lista de fechas
        dates_frame = ttk.Frame(control_frame)
        dates_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Listbox para mostrar fechas seleccionadas
        self.listbox_fechas = tk.Listbox(dates_frame, height=6)
        self.listbox_fechas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar para la lista
        scrollbar = ttk.Scrollbar(dates_frame, orient=tk.VERTICAL, command=self.listbox_fechas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox_fechas.config(yscrollcommand=scrollbar.set)
        
        # Mantener el campo de texto original para compatibilidad
        self.entry_turnos = ttk.Entry(parent_frame)
        self.entry_turnos.pack(fill=tk.X, padx=5, pady=5, expand=True)
        self.entry_turnos.pack_forget()  # Ocultamos el campo pero lo mantenemos funcional
    
    def setup_entrada_texto_basica(self, parent_frame):
        """Configura la interfaz básica con entrada de texto para fechas."""
        # Crear un marco para las instrucciones y la entrada
        input_frame = ttk.Frame(parent_frame)
        input_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        # Instrucciones para el formato de fecha
        ttk.Label(input_frame, 
                text="Introduzca los días de turno separados por comas (formato dd-mmm-yyyy):",
                font=("Helvetica", 10, "bold")).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(input_frame, 
                text="Ejemplo: 08-abr-2025,13-abr-2025,18-abr-2025",
                foreground="blue").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(input_frame, 
                text="Para marcar un día como feriado, agregue ',F' después de la fecha (ej: 08-abr-2025,F)",
                foreground="dark green").pack(anchor=tk.W, padx=5, pady=2)
        
        # Campo de entrada para las fechas
        self.entry_turnos = ttk.Entry(input_frame, width=60)
        self.entry_turnos.pack(fill=tk.X, padx=5, pady=10, expand=True)
        
        # Botones para gestionar fechas
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        # Botón para analizar fechas y mostrarlas
        ttk.Button(btn_frame, 
                 text="Analizar fechas ingresadas", 
                 command=self.analizar_fechas_texto).pack(side=tk.LEFT, padx=5)
        
        # Frame para la lista de fechas
        list_frame = ttk.LabelFrame(parent_frame, text="Fechas analizadas")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Listbox para mostrar fechas analizadas
        self.listbox_fechas = tk.Listbox(list_frame, height=8)
        self.listbox_fechas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar para la lista
        scrollbar = ttk.Scrollbar(self.listbox_fechas, orient=tk.VERTICAL, command=self.listbox_fechas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox_fechas.config(yscrollcommand=scrollbar.set)
        
        # Inicializar la lista de fechas seleccionadas
        self.fechas_seleccionadas = []
    
    def analizar_fechas_texto(self):
        """Analiza las fechas ingresadas en el campo de texto."""
        # Obtener texto de la entrada
        texto_fechas = self.entry_turnos.get().strip()
        
        if not texto_fechas:
            messagebox.showinfo("Información", "No ha ingresado ninguna fecha.")
            return
        
        # Limpiar listbox
        self.listbox_fechas.delete(0, tk.END)
        
        # Limpiar lista de fechas seleccionadas
        self.fechas_seleccionadas = []
        
        # Dividir por comas
        fechas_lista = [f.strip() for f in texto_fechas.split(',')]
        
        # Procesar cada fecha
        for fecha in fechas_lista:
            if not fecha:  # Saltar entradas vacías
                continue
                
            # Identificar si es feriado
            es_feriado = fecha.endswith(",F") or fecha.endswith(",f")
            
            if es_feriado:
                fecha = fecha[:-2]  # Quitar el indicador de feriado
                
            # Agregar a la lista y mostrar
            self.fechas_seleccionadas.append(fecha + (",F" if es_feriado else ""))
            
            # Mostrar en la listbox
            texto_mostrar = f"{fecha} {'(FERIADO)' if es_feriado else ''}"
            self.listbox_fechas.insert(tk.END, texto_mostrar)
        
        # Actualizar estado
        self.lbl_status.config(text=f"Se analizaron {len(self.fechas_seleccionadas)} fechas")
    
    def actualizar_etiqueta_fecha(self, event=None):
        """Actualiza la etiqueta con la fecha seleccionada actualmente."""
        fecha_str = self.cal.get_date()
        
        # Mostrar la fecha en formato español
        try:
            day, month, year = fecha_str.split('/')
            meses_esp = {
                1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril', 5: 'mayo', 6: 'junio',
                7: 'julio', 8: 'agosto', 9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
            }
            fecha_esp = f"{int(day)} de {meses_esp[int(month)]} de {year}"
            self.lbl_fecha_actual.config(text=f"Fecha: {fecha_esp}")
        except Exception:
            # Si hay un error, mostrar la fecha en formato original
            self.lbl_fecha_actual.config(text=f"Fecha: {fecha_str}")
    
    def procesar_archivo(self):
        """Procesa el archivo CSV y genera los resultados en la estructura de carpetas apropiada."""
        if not self.ruta_csv:
            messagebox.showerror("Error", "Debe seleccionar un archivo CSV")
            return
        
        nombre_doctor = self.entry_doctor.get().strip()
        if not nombre_doctor:
            messagebox.showerror("Error", "Debe ingresar el nombre del doctor")
            return
        
        # Obtener fechas de turno (opcional)
        fechas_turno = self.entry_turnos.get().strip()
        
        # Crear directorio de salida estructurado
        # Formato: csv/TURNOS MES AÑO
        fecha_actual = datetime.now()
        mes = fecha_actual.strftime("%B").upper()  # Nombre de mes en mayúsculas
        año = fecha_actual.strftime("%Y")
        
        # Convertir nombre de mes en inglés a español si es necesario
        meses_es = {
            "JANUARY": "ENERO", "FEBRUARY": "FEBRERO", "MARCH": "MARZO", "APRIL": "ABRIL",
            "MAY": "MAYO", "JUNE": "JUNIO", "JULY": "JULIO", "AUGUST": "AGOSTO",
            "SEPTEMBER": "SEPTIEMBRE", "OCTOBER": "OCTUBRE", "NOVEMBER": "NOVIEMBRE", "DECEMBER": "DICIEMBRE"
        }
        
        if mes in meses_es:
            mes = meses_es[mes]
        
        # Crear la ruta de directorio
        nombre_directorio = f"TURNOS {mes} {año}"
        base_dir = os.path.dirname(os.path.abspath(__file__))
        directorio_salida = os.path.join(base_dir, "csv", nombre_directorio)
        
        # Crear directorio si no existe
        os.makedirs(directorio_salida, exist_ok=True)
        
        # Guardar directorio para uso futuro
        self.directorio_salida = directorio_salida
        
        # Actualizar estado
        self.lbl_status.config(text=f"Procesando archivo en {directorio_salida}...")
        self.root.update()
        
        # Procesar archivo
        exito, resultado = self.calculadora.procesar_archivo(
            self.ruta_csv, 
            self.directorio_salida, 
            nombre_doctor,
            fechas_turno
        )
        
        if exito:
            # Mostrar resultados
            self.mostrar_resultados(resultado)
            messagebox.showinfo(
                "Éxito", 
                f"Archivos generados correctamente en la carpeta:\n{nombre_directorio}"
            )
        else:
            messagebox.showerror("Error", f"Error al procesar el archivo: {resultado}")
        
        # Actualizar estado
        self.lbl_status.config(text="Procesamiento completado")
    
    def mostrar_resultados(self, resultado):
        """Muestra los resultados en la interfaz de manera detallada y ordenada."""
        self.txt_resultados.delete(1.0, tk.END)
        
        # Guardar el resultado actual para poder acceder a las rutas posteriormente
        self.resultado_actual = resultado
        
        # Habilitar los botones de Excel
        self.btn_rx_excel.config(state=tk.NORMAL)
        self.btn_tac_excel.config(state=tk.NORMAL)
        self.btn_resumen_excel.config(state=tk.NORMAL)
        
        # Mostrar información de archivos generados
        self.txt_resultados.insert(tk.END, "ARCHIVOS GENERADOS:\n", "title")
        
        # Obtener el nombre del directorio de salida para mostrarlo
        dir_salida = os.path.basename(self.directorio_salida)
        self.txt_resultados.insert(tk.END, f"Carpeta: csv/{dir_salida}\n\n")
        
        # Mostrar archivos generados con descripción
        self.txt_resultados.insert(tk.END, "Archivos:\n")
        self.txt_resultados.insert(tk.END, f"- Tabla_TAC.xlsx: Contiene todos los exámenes TAC (SCA y SJ)\n")
        self.txt_resultados.insert(tk.END, f"- Tabla_RX.xlsx: Contiene todos los exámenes RX (SCA y SJ)\n")
        self.txt_resultados.insert(tk.END, f"- Contenido_Correo.xlsx: Texto del correo para enviar al médico\n")
        self.txt_resultados.insert(tk.END, f"- Analisis_Monetario.xlsx: Resumen económico detallado\n")
        self.txt_resultados.insert(tk.END, f"- Detalles_Tecnicos.xlsx: Información técnica adicional\n\n")
        
        self.txt_resultados.insert(tk.END, "\nRESUMEN ECONÓMICO:\n", "title")
        
        # Formatear resultados económicos
        eco = resultado['resultado_economico']
        
        self.txt_resultados.insert(tk.END, f"Horas trabajadas: {eco['horas_trabajadas']}\n")
        self.txt_resultados.insert(tk.END, f"Honorarios por horas: ${eco['honorarios_hora']:,}\n\n")
        
        self.txt_resultados.insert(tk.END, f"Exámenes RX: {eco['rx_count']} (${eco['rx_total']:,})\n")
        
        # Calcular para interfaz (mostrar detalles de TAC doble/triple)
        tac_fisicos = eco['tac_count'] + eco['tac_doble_count'] + eco['tac_triple_count']
        tac_doble_count = eco['tac_doble_count']
        tac_triple_count = eco['tac_triple_count']
        tac_valor_total = eco['tac_total'] + eco['tac_doble_total'] + eco['tac_triple_total']
        
        # Contar para informes (dobles como 2, triples como 3)
        tac_conteo_total = eco['tac_count'] + (eco['tac_doble_count'] * 2) + (eco['tac_triple_count'] * 3)
        
        # Mostrar en interfaz (mostrar tanto físicos como conteo para informes)
        self.txt_resultados.insert(tk.END, f"Exámenes TAC: {eco['tac_count']} simples + {tac_doble_count} dobles + {tac_triple_count} triples\n")
        self.txt_resultados.insert(tk.END, f"  - {tac_fisicos} estudios físicos / {tac_conteo_total} para informes (${tac_valor_total:,})\n\n")
        
        self.txt_resultados.insert(tk.END, f"TOTAL: ${eco['total']:,}\n\n", "total")
        
        # Mostrar tablas de exámenes
        self.txt_resultados.insert(tk.END, "RESUMEN DE EXÁMENES:\n", "title")
        
        # Tabla RX (SCA y SJ)
        self.txt_resultados.insert(tk.END, "1. TABLA RX (SCA y SJ):\n", "subtitle")
        rx_count = eco['rx_count']
        rx_sca_count = len(self.calculadora.data_filtrada[(self.calculadora.data_filtrada['Tipo'] == 'RX') & 
                                          (self.calculadora.data_filtrada['Sala de adquisición'].str.startswith('SCA'))])
        rx_sj_count = len(self.calculadora.data_filtrada[(self.calculadora.data_filtrada['Tipo'] == 'RX') & 
                                         (self.calculadora.data_filtrada['Sala de adquisición'].str.startswith('SJ'))])
        
        self.txt_resultados.insert(tk.END, f"   - Total exámenes RX: {rx_count}\n")
        self.txt_resultados.insert(tk.END, f"   - Exámenes RX SCA: {rx_sca_count}\n")
        self.txt_resultados.insert(tk.END, f"   - Exámenes RX SJ: {rx_sj_count}\n")
        self.txt_resultados.insert(tk.END, f"   - Valor total: ${eco['rx_total']:,}\n\n")
        
        # Tabla TAC (SCA y SJ)
        self.txt_resultados.insert(tk.END, "2. TABLA TAC (SCA y SJ):\n", "subtitle")
        tac_sca_count = len(self.calculadora.data_filtrada[(self.calculadora.data_filtrada['Tipo'] == 'TAC') & 
                                          (self.calculadora.data_filtrada['Sala de adquisición'].str.startswith('SCA'))])
        tac_sj_count = len(self.calculadora.data_filtrada[(self.calculadora.data_filtrada['Tipo'] == 'TAC') & 
                                         (self.calculadora.data_filtrada['Sala de adquisición'].str.startswith('SJ'))])
        
        # Aquí también mostramos TAC doble y triple para información del usuario
        self.txt_resultados.insert(tk.END, f"   - Total exámenes TAC: {tac_fisicos} físicos / {tac_conteo_total} para informes\n")
        self.txt_resultados.insert(tk.END, f"   - Exámenes TAC SCA: {tac_sca_count}\n")
        self.txt_resultados.insert(tk.END, f"   - Exámenes TAC SJ: {tac_sj_count}\n")
        self.txt_resultados.insert(tk.END, f"   - De estos, TAC doble (x2): {tac_doble_count}\n")
        self.txt_resultados.insert(tk.END, f"   - De estos, TAC triple (x3): {eco['tac_triple_count']}\n")
        self.txt_resultados.insert(tk.END, f"   - Valor total: ${tac_valor_total:,}\n\n")
        
        # Info sobre TAC doble y triple para usuario
        self.txt_resultados.insert(tk.END, "Nota: En los informes oficiales, cada TAC doble cuenta como 2 TAC y cada triple como 3.\n")
        self.txt_resultados.insert(tk.END, "      Esto explica la diferencia entre exámenes físicos y conteo para informes.\n\n")
        
        # Para abrir los archivos
        self.txt_resultados.insert(tk.END, "Para ver los detalles completos, use los botones debajo o abra los archivos Excel generados.\n")
        
        # Configurar etiquetas de texto
        self.txt_resultados.tag_configure("title", font=("Helvetica", 12, "bold"))
        self.txt_resultados.tag_configure("subtitle", font=("Helvetica", 10, "bold"))
        self.txt_resultados.tag_configure("total", font=("Helvetica", 12, "bold"), foreground="blue")
    
    def ver_correo(self):
        """Muestra una ventana con el correo generado."""
        if not hasattr(self.calculadora, 'examenes_contabilizados') or self.calculadora.examenes_contabilizados is None:
            messagebox.showerror("Error", "Primero debe procesar un archivo")
            return
        
        nombre_doctor = self.entry_doctor.get().strip()
        if not nombre_doctor:
            messagebox.showerror("Error", "Debe ingresar el nombre del doctor")
            return
        
        # Generar correo
        correo = self.calculadora.generar_correo(nombre_doctor)
        
        if not correo:
            messagebox.showerror("Error", "No se pudo generar el correo")
            return
        
        # Crear ventana para mostrar el correo
        correo_window = tk.Toplevel(self.root)
        correo_window.title("Vista Previa del Correo")
        correo_window.geometry("600x500")
        
        frame = ttk.Frame(correo_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Asunto
        ttk.Label(frame, text="Asunto:", font=("Helvetica", 11, "bold")).pack(anchor=tk.W)
        ttk.Label(frame, text=correo['asunto']).pack(anchor=tk.W, pady=(0, 10))
        
        # Cuerpo
        ttk.Label(frame, text="Cuerpo:", font=("Helvetica", 11, "bold")).pack(anchor=tk.W)
        
        txt_cuerpo = tk.Text(frame, wrap=tk.WORD)
        txt_cuerpo.pack(fill=tk.BOTH, expand=True, pady=5)
        txt_cuerpo.insert(tk.END, correo['cuerpo'])
        txt_cuerpo.config(state=tk.DISABLED)
        
        # Scrollbar para el texto del cuerpo
        scrollbar = ttk.Scrollbar(txt_cuerpo)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        txt_cuerpo.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=txt_cuerpo.yview)
        
        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # Botón para copiar al portapapeles
        btn_copiar = ttk.Button(
            btn_frame, 
            text="Copiar al Portapapeles",
            command=lambda: self.copiar_correo(correo)
        )
        btn_copiar.pack(side=tk.LEFT, padx=5)
        
        # Botón para guardar como archivo de texto
        btn_guardar_txt = ttk.Button(
            btn_frame, 
            text="Guardar como TXT",
            command=lambda: self.guardar_correo_txt(correo)
        )
        btn_guardar_txt.pack(side=tk.LEFT, padx=5)
        
        # Botón para cerrar la ventana
        btn_cerrar = ttk.Button(
            btn_frame, 
            text="Cerrar",
            command=correo_window.destroy
        )
        btn_cerrar.pack(side=tk.RIGHT, padx=5)
    
    def copiar_correo(self, correo):
        """Copia el contenido del correo al portapapeles."""
        texto_completo = f"Asunto: {correo['asunto']}\n\n{correo['cuerpo']}"
        self.root.clipboard_clear()
        self.root.clipboard_append(texto_completo)
        messagebox.showinfo("Copiado", "Contenido del correo copiado al portapapeles")
    
    def guardar_correo_txt(self, correo):
        """Guarda el contenido del correo como archivo de texto en la carpeta de resultados."""
        if not hasattr(self, 'directorio_salida') or not self.directorio_salida:
            messagebox.showerror("Error", "No se ha generado la carpeta de resultados.")
            return
        
        try:
            # Ruta del archivo de texto
            ruta_txt = os.path.join(self.directorio_salida, 'Contenido_Correo.txt');
            
            # Contenido del correo
            texto_correo = correo['cuerpo']
            
            # Guardar en archivo de texto
            with open(ruta_txt, 'w', encoding='utf-8') as f:
                f.write(texto_correo)
            
            messagebox.showinfo("Archivo guardado", 
                               f"El contenido del correo ha sido guardado como archivo de texto en:\n{ruta_txt}")
            
            # Abrir el archivo automáticamente
            try:
                if os.name == 'nt':  # Windows
                    os.system(f'start notepad "{ruta_txt}"')
                elif os.name == 'posix':  # macOS/Linux
                    os.system(f'open "{ruta_txt}"')
                else:
                    # Fallback: intentar usar webbrowser
                    webbrowser.open(ruta_txt)
            except:
                pass
                
            return ruta_txt
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo de texto: {e}")
            return None
    
    def abrir_excel_tabla(self, nombre_hoja):
        """Abre el archivo Excel de exámenes filtrados en la hoja especificada."""
        if not hasattr(self.calculadora, 'data_filtrada') or self.calculadora.data_filtrada is None:
            messagebox.showerror("Error", "No hay datos filtrados disponibles.")
            return
        
        # Usamos la ruta de los resultados almacenada
        if not hasattr(self, 'resultado_actual') or not self.resultado_actual:
            messagebox.showerror("Error", "No hay resultados disponibles.")
            return
        
        # Determinar qué archivo abrir según la hoja seleccionada
        if 'RX' in nombre_hoja:
            ruta_excel = self.resultado_actual['tabla_rx']
        else:  # TAC
            ruta_excel = self.resultado_actual['tabla_tac']
        
        try:
            # En sistemas Windows
            if os.name == 'nt':
                os.system(f'start excel "{ruta_excel}"')
            # En sistemas macOS
            elif os.name == 'posix':
                os.system(f'open "{ruta_excel}"')
            else:
                # Fallback para otros sistemas
                webbrowser.open(ruta_excel)
            
            messagebox.showinfo("Excel Abierto", f"Tabla de exámenes abierta")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo Excel: {e}")
    
    def abrir_excel_resumen(self):
        """Abre el archivo Excel del resumen económico."""
        if not hasattr(self, 'resultado_actual') or not self.resultado_actual:
            messagebox.showerror("Error", "No hay resultados disponibles.")
            return
        
        ruta_excel = self.resultado_actual['analisis_monetario']
        
        try:
            # En sistemas Windows
            if os.name == 'nt':
                os.system(f'start excel "{ruta_excel}"')
            # En sistemas macOS
            elif os.name == 'posix':
                os.system(f'open "{ruta_excel}"')
            else:
                # Fallback para otros sistemas
                webbrowser.open(ruta_excel)
            
            messagebox.showinfo("Excel Abierto", "Análisis Monetario abierto")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo Excel: {e}")


def main():
    """Función principal que inicia la aplicación."""
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()