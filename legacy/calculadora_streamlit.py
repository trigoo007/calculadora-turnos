#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculadora de Turnos en Radiología - Versión Streamlit
-------------------------------------------------------
Aplicación web para procesar datos de procedimientos médicos en radiología,
clasificar exámenes, calcular horas trabajadas y generar reportes.
"""

import os
import pandas as pd
import numpy as np
import tempfile
from datetime import datetime, timedelta
import streamlit as st
from dateutil import parser
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64
import re
import calendar
from collections import Counter
import importlib.util

# Asegurarse de que datetime está disponible en el ámbito global
import datetime as dt  # Importar el módulo completo por si acaso

# Importar el sistema de aprendizaje SQLite
try:
    from aprendizaje_datos_sqlite import SistemaAprendizajeSQLite
    SISTEMA_APRENDIZAJE_SQLITE_DISPONIBLE = True
except ImportError:
    SISTEMA_APRENDIZAJE_SQLITE_DISPONIBLE = False

# Importar el sistema de aprendizaje antiguo (JSON) como fallback
try:
    from aprendizaje_datos import SistemaAprendizaje
    SISTEMA_APRENDIZAJE_JSON_DISPONIBLE = True
except ImportError:
    SISTEMA_APRENDIZAJE_JSON_DISPONIBLE = False
    
# Determinar qué sistema usar (preferir SQLite)
SISTEMA_APRENDIZAJE_DISPONIBLE = SISTEMA_APRENDIZAJE_SQLITE_DISPONIBLE or SISTEMA_APRENDIZAJE_JSON_DISPONIBLE

# Configuración de la página
st.set_page_config(
    page_title="Calculadora de Turnos en Radiología",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Clase para la lógica de negocio
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
        
        # Inicializar sistema de aprendizaje
        self.sistema_aprendizaje = None
        
        # Preferir SQLite, fallback a JSON si no está disponible
        if SISTEMA_APRENDIZAJE_SQLITE_DISPONIBLE:
            try:
                self.sistema_aprendizaje = SistemaAprendizajeSQLite()
                self.sistema_tipo = "sqlite"
            except Exception as e:
                st.warning(f"Error al inicializar el sistema de aprendizaje SQLite: {e}")
                self.sistema_tipo = None
        elif SISTEMA_APRENDIZAJE_JSON_DISPONIBLE:
            try:
                self.sistema_aprendizaje = SistemaAprendizaje()
                self.sistema_tipo = "json"
            except Exception as e:
                st.warning(f"Error al inicializar el sistema de aprendizaje JSON: {e}")
                self.sistema_tipo = None
        
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
    
    def cargar_archivo(self, uploaded_file):
        """Carga y valida el archivo CSV desde Streamlit."""
        try:
            # Leer el archivo CSV cargado con pandas
            df = pd.read_csv(uploaded_file)
            
            # Verificar columnas
            for col in self.columnas_esperadas:
                if col not in df.columns:
                    return False, f"El archivo no contiene la columna '{col}'"
            
            self.data = df
            return True, "Archivo cargado correctamente"
        except Exception as e:
            return False, f"Error al cargar el archivo: {e}"
    
    def filtrar_datos(self):
        """Filtra los datos según los criterios especificados."""
        if self.data is None:
            return False, "No hay datos cargados"
        
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
            
            return True, f"Se filtraron {len(self.data_filtrada)} exámenes de {len(self.data)} totales"
        except Exception as e:
            return False, f"Error al filtrar datos: {e}"
    
    def clasificar_examenes(self):
        """Clasifica los exámenes según el criterio especificado, usando el sistema de aprendizaje."""
        if self.data_filtrada is None:
            return False, "No hay datos filtrados"
        
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
                        if self.sistema_tipo == "sqlite":
                            clasificacion = self.sistema_aprendizaje.clasificar_procedimiento(nombre_proc)
                            
                            # Asignar subtipo según la clasificación
                            if clasificacion['subtipo'] == 'TRIPLE':
                                self.data_filtrada.at[idx, 'TAC triple'] = True
                            elif clasificacion['subtipo'] == 'DOBLE':
                                self.data_filtrada.at[idx, 'TAC doble'] = True
                        else:
                            # Sistema JSON: solo verifica TAC doble
                            if self.sistema_aprendizaje.verificar_tac_doble(nombre_proc):
                                self.data_filtrada.at[idx, 'TAC doble'] = True
                
                # Aprender de los nuevos datos
                try:
                    if self.sistema_tipo == "sqlite":
                        # Analizar DataFrame para extraer información de procedimientos y salas
                        self.sistema_aprendizaje.analizar_dataframe(self.data_filtrada)
                    elif self.sistema_tipo == "json":
                        # Para el sistema JSON, solo podemos aprender patrones TAC doble
                        if 'TAC doble' in self.data_filtrada.columns:
                            tac_dobles = self.data_filtrada[self.data_filtrada['TAC doble'] == True]['Nombre del procedimiento'].unique()
                            for proc in tac_dobles:
                                self.sistema_aprendizaje.agregar_patron_tac_doble(proc)
                except Exception as e:
                    st.warning(f"Advertencia: No se pudo analizar datos para aprendizaje: {e}")
            else:
                # Fallback: Usar el método tradicional si no hay sistema de aprendizaje
                # Identificar TAC doble
                tac_dobles = [
                    "Tórax, abdomen y pelvis",
                    "AngioTAC de tórax, abdomen y pelvis"
                ]
                
                # Criterios adicionales para TAC doble
                tac_dobles_adicionales = [
                    "TX/ABD/PEL",
                    "Angio Tórax Abdomen y Pelvis",
                    "Torax-Abdomen-Pelvis",
                    "Tórax Abdomen Pelvis",
                    "Tórax abdomen y pelvis",
                    "Torax, Abdomen y Pelvis",
                    "TAC Torax-Abdomen-Pelvis Ped",
                    "Torax-Abdomen-Pelvis Ped",
                    "TAC TX/ABD/PEL"
                ]
                
                # Identificar TAC doble según criterios oficiales
                mask_tac_doble_oficiales = self.data_filtrada['Nombre del procedimiento'].isin(tac_dobles)
                
                # Identificar TAC doble según criterios adicionales
                mask_tac_doble_adicionales = False
                for criterio in tac_dobles_adicionales:
                    mask_tac_doble_adicionales |= self.data_filtrada['Nombre del procedimiento'].str.contains(criterio, case=False, na=False)
                
                # Identificar TAC dobles por ID específico (casos especiales)
                ids_tac_doble_especificos = ['9865805', '9883701', '9887600']
                mask_tac_doble_ids = self.data_filtrada['Número de cita'].isin(ids_tac_doble_especificos)
                
                # Combinar todas las condiciones para identificar TAC doble
                self.data_filtrada['TAC doble'] = mask_tac_doble_oficiales | mask_tac_doble_adicionales | mask_tac_doble_ids
            
            # Contar resultados de clasificación
            rx_count = sum(self.data_filtrada['Tipo'] == 'RX')
            tac_count = sum(self.data_filtrada['Tipo'] == 'TAC')
            tac_doble_count = sum(self.data_filtrada['TAC doble'])
            tac_triple_count = sum(self.data_filtrada['TAC triple']) if 'TAC triple' in self.data_filtrada.columns else 0
            
            return True, f"Clasificados: {rx_count} RX, {tac_count} TAC (de estos, {tac_doble_count} TAC dobles, {tac_triple_count} TAC triples)"
        except Exception as e:
            return False, f"Error al clasificar exámenes: {e}"

    def estimar_dias_turno(self):
        """
        Estima los posibles días de turno basados en la concentración de exámenes.
        Retorna una lista de fechas estimadas como días de turno.
        """
        if self.data_filtrada is None:
            return []
        
        try:
            # Convertir fechas a formato estandarizado
            self.data_filtrada['Fecha_dt'] = pd.to_datetime(
                self.data_filtrada['Fecha del procedimiento programado'], 
                dayfirst=True,  # Asumiendo formato día/mes/año
                errors='coerce'
            )
            
            # Agrupar por fecha y contar exámenes
            conteo_diario = self.data_filtrada.groupby(self.data_filtrada['Fecha_dt'].dt.date).size()
            
            # Calcular estadísticas
            promedio = conteo_diario.mean()
            umbral = max(promedio * 0.8, 3)  # Días con al menos 80% del promedio o mínimo 3 exámenes
            
            # Identificar días con alta concentración de exámenes
            dias_potenciales = conteo_diario[conteo_diario >= umbral].index.tolist()
            
            # Convertir a formato legible (dd-mmm-yyyy)
            meses_esp = {
                1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun',
                7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
            }
            
            fechas_estimadas = []
            for fecha in dias_potenciales:
                dia = fecha.day
                mes = meses_esp[fecha.month]
                anio = fecha.year
                fecha_esp = f"{dia:02d}-{mes}-{anio}"
                # Añadir el número de exámenes para referencia
                num_examenes = conteo_diario[fecha]
                fechas_estimadas.append((fecha_esp, num_examenes))
            
            return fechas_estimadas
            
        except Exception as e:
            st.error(f"Error al estimar días de turno: {e}")
            return []

    def calcular_horas_turno_especificas(self, dias_turnos):
        """
        Calcula las horas trabajadas según los días de turno específicos.
        
        Args:
            dias_turnos: Lista de tuplas (fecha, es_feriado) donde fecha está en formato dd-mmm-yyyy
                        y es_feriado es un booleano
        
        Returns:
            El total de horas trabajadas
        """
        if not dias_turnos:
            return 0
        
        try:
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
            total_horas = 0
            
            for fecha_str, es_feriado in dias_turnos:
                try:
                    fecha_turno = convertir_fecha_espanol(fecha_str)
                    
                    # Calcular horas para este turno
                    horas = calcular_horas_turno(fecha_turno, es_feriado)
                    total_horas += horas
                    
                except Exception as e:
                    st.error(f"Error al procesar la fecha {fecha_str}: {e}")
                    continue
            
            return total_horas
            
        except Exception as e:
            st.error(f"Error al calcular horas de turno: {e}")
            return 0
    
    def contabilizar_examenes(self):
        """
        Contabiliza todos los exámenes de salas SJ y SCA.
        """
        if self.data_filtrada is None:
            return False, "No hay datos filtrados"
        
        try:
            # Crear columna de fecha sin hora para agrupación
            self.data_filtrada['Fecha sin hora'] = pd.to_datetime(
                self.data_filtrada['Fecha del procedimiento programado'], 
                dayfirst=True
            ).dt.date.astype(str)
            
            # Los exámenes contabilizados son todos los que pasaron el filtro inicial
            # Verificar si existe la columna TAC triple
            if 'TAC triple' in self.data_filtrada.columns:
                self.examenes_contabilizados = self.data_filtrada[[
                    'Número de cita',
                    'Fecha sin hora',
                    'Apellidos del paciente',
                    'Nombre del paciente',
                    'Nombre del procedimiento',
                    'Sala de adquisición',
                    'Tipo',
                    'TAC doble',
                    'TAC triple'
                ]].copy()
            else:
                self.examenes_contabilizados = self.data_filtrada[[
                    'Número de cita',
                    'Fecha sin hora',
                    'Apellidos del paciente',
                    'Nombre del paciente',
                    'Nombre del procedimiento',
                    'Sala de adquisición',
                    'Tipo',
                    'TAC doble'
                ]].copy()
                # Agregar columna TAC triple por defecto
                self.examenes_contabilizados['TAC triple'] = False
            
            return True, f"Se contabilizaron {len(self.examenes_contabilizados)} exámenes"
        except Exception as e:
            return False, f"Error al contabilizar exámenes: {e}"
    
    def calcular_honorarios(self, total_horas):
        """
        Calcula los honorarios basados en las horas trabajadas y los exámenes realizados.
        
        Args:
            total_horas: Total de horas trabajadas
            
        Returns:
            Diccionario con el resultado económico
        """
        if self.data_filtrada is None:
            return None
        
        try:
            # Contar exámenes por tipo
            rx_count = sum(self.data_filtrada['Tipo'] == 'RX')
            tac_triple_count = sum(self.data_filtrada['TAC triple']) if 'TAC triple' in self.data_filtrada.columns else 0
            tac_doble_count = sum((self.data_filtrada['TAC doble']) & ~(self.data_filtrada['TAC triple']))
            tac_normal_count = sum((self.data_filtrada['Tipo'] == 'TAC') 
                                  & (self.data_filtrada['TAC doble'] == False) 
                                  & (self.data_filtrada['TAC triple'] == False if 'TAC triple' in self.data_filtrada.columns else True))
            
            # Calcular honorarios
            rx_total = rx_count * self.TARIFA_RX
            tac_total = tac_normal_count * self.TARIFA_TAC
            tac_doble_total = tac_doble_count * self.TARIFA_TAC_DOBLE
            tac_triple_total = tac_triple_count * self.TARIFA_TAC_TRIPLE
            honorarios_hora = total_horas * self.TARIFA_HORA
            
            # Total
            total = rx_total + tac_total + tac_doble_total + tac_triple_total + honorarios_hora
            
            # Actualizar el diccionario de resultados
            self.resultado_economico = {
                'horas_trabajadas': total_horas,
                'rx_count': rx_count,
                'tac_count': tac_normal_count,
                'tac_doble_count': tac_doble_count,
                'tac_triple_count': tac_triple_count,
                'rx_total': rx_total,
                'tac_total': tac_total,
                'tac_doble_total': tac_doble_total,
                'tac_triple_total': tac_triple_total,
                'honorarios_hora': honorarios_hora,
                'total': total
            }
            
            return self.resultado_economico
        
        except Exception as e:
            st.error(f"Error al calcular honorarios: {e}")
            return None


# Funciones de utilidad para la interfaz de Streamlit
def get_table_download_link(df, filename, text):
    """Genera un enlace para descargar el DataFrame como Excel."""
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}.xlsx">{text}</a>'
    return href

def mostrar_df_interactivo(df, key, height=400):
    """Muestra un DataFrame interactivo con opciones de filtro y ordenamiento."""
    if not isinstance(df, pd.DataFrame) or df.empty:
        st.warning("No hay datos para mostrar.")
        return
    
    # Mostrar la tabla con opciones de filtrado y ordenamiento
    st.dataframe(df, height=height, key=key)

def plot_distribucion_examenes(df):
    """Crea un gráfico de barras mostrando la distribución de exámenes por tipo y fecha."""
    if df is None or df.empty:
        return None
    
    # Asegurarse de que tenemos una columna de fecha como datetime
    if 'Fecha_dt' not in df.columns:
        df['Fecha_dt'] = pd.to_datetime(df['Fecha del procedimiento programado'], dayfirst=True, errors='coerce')
    
    # Agrupar por fecha y tipo
    df_grouped = df.groupby([df['Fecha_dt'].dt.date, 'Tipo']).size().reset_index(name='Cantidad')
    
    # Crear el gráfico con Plotly
    fig = px.bar(
        df_grouped, 
        x='Fecha_dt', 
        y='Cantidad', 
        color='Tipo',
        title='Distribución de Exámenes por Fecha y Tipo',
        labels={'Fecha_dt': 'Fecha', 'Cantidad': 'Número de Exámenes', 'Tipo': 'Tipo de Examen'},
        color_discrete_map={'RX': '#2ca02c', 'TAC': '#1f77b4'}
    )
    
    # Personalizar el diseño
    fig.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Número de Exámenes',
        legend_title='Tipo de Examen',
        barmode='group'
    )
    
    return fig

def plot_distribucion_salas(df):
    """Crea un gráfico de pie para mostrar la distribución de exámenes por sala."""
    if df is None or df.empty:
        return None
    
    # Agrupar por sala
    df_grouped = df.groupby('Sala de adquisición').size().reset_index(name='Cantidad')
    
    # Crear el gráfico con Plotly
    fig = px.pie(
        df_grouped, 
        values='Cantidad', 
        names='Sala de adquisición',
        title='Distribución de Exámenes por Sala',
        hole=0.4
    )
    
    # Personalizar el diseño
    fig.update_layout(
        legend_title='Sala',
    )
    
    return fig

def generar_contenido_correo(nombre_doctor, fechas_turnos, horas_trabajadas, rx_count, tac_count, periodo=''):
    """Genera el contenido del correo según el formato especificado."""
    # Si no se especificó un período, intentar determinarlo a partir de las fechas
    if not periodo and fechas_turnos:
        # Extraer el mes de la primera fecha (suponiendo formato dd-mmm-yyyy)
        try:
            meses_esp = {
                'ene': 'enero', 'feb': 'febrero', 'mar': 'marzo', 'abr': 'abril',
                'may': 'mayo', 'jun': 'junio', 'jul': 'julio', 'ago': 'agosto',
                'sep': 'septiembre', 'oct': 'octubre', 'nov': 'noviembre', 'dic': 'diciembre'
            }
            
            primera_fecha = fechas_turnos[0]
            mes_abrev = primera_fecha.split('-')[1]
            if mes_abrev in meses_esp:
                periodo = meses_esp[mes_abrev]
        except:
            # Si no se puede extraer, usar el mes actual
            periodo = dt.datetime.now().strftime('%B').lower()
    
    # Formatear las fechas (solo mostrar el día)
    dias = []
    for fecha in fechas_turnos:
        try:
            # Extraer solo el día y eliminar ceros a la izquierda
            dia = str(int(fecha.split('-')[0]))
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
    
    # Crear contenido del correo
    asunto = f"Informe de Turnos - {periodo.capitalize()} {dt.datetime.now().year}"
    
    cuerpo = f"""Estimado Dr. {nombre_doctor}

Junto con saludar, le envío el informe detallado de los turnos realizados durante el período de {periodo}.

Días de turnos realizados: {fechas_str}.
Total de horas trabajadas: {horas_trabajadas} hrs.
Cantidad de exámenes informados:
- RX: {rx_count}
- TAC: {tac_count}

Adjunto en el archivo va el detalle de los exámenes de SCA y SJ.

Saludos cordiales."""
    
    return {
        'asunto': asunto,
        'cuerpo': cuerpo
    }

def enviar_correo(destinatario, asunto, cuerpo, archivos_adjuntos):
    """
    Envía un correo electrónico con los archivos adjuntos.
    
    Args:
        destinatario: Dirección de correo electrónico del destinatario
        asunto: Asunto del correo
        cuerpo: Cuerpo del correo (texto plano)
        archivos_adjuntos: Lista de rutas a los archivos adjuntos
        
    Returns:
        (éxito, mensaje) donde éxito es un booleano y mensaje es un mensaje descriptivo
    """
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication
        import tempfile
        import os
        
        # Crear objeto mensaje
        msg = MIMEMultipart()
        msg['From'] = st.session_state.get('correo_remitente', "ejemplo@gmail.com")
        msg['To'] = destinatario
        msg['Subject'] = asunto
        
        # Agregar cuerpo del mensaje
        msg.attach(MIMEText(cuerpo, 'plain'))
        
        # Agregar archivos adjuntos
        for archivo in archivos_adjuntos:
            try:
                with open(archivo, 'rb') as f:
                    adjunto = MIMEApplication(f.read(), _subtype='xlsx')
                    # Usar solo el nombre del archivo, no la ruta completa
                    nombre_archivo = os.path.basename(archivo)
                    adjunto.add_header('Content-Disposition', 'attachment', filename=nombre_archivo)
                    msg.attach(adjunto)
            except Exception as e:
                st.error(f"Error al adjuntar el archivo {archivo}: {str(e)}")
                continue
        
        # Esta función en una aplicación real enviaría el correo
        # Aquí simulamos el envío para demostración
        # En la implementación final, se usaría un servidor SMTP real
        
        # Guardamos el correo en un archivo temporal para demostración
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, 'correo_enviado.txt')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(f"Para: {destinatario}\n")
            f.write(f"Asunto: {asunto}\n\n")
            f.write(cuerpo)
            f.write("\n\nArchivos adjuntos:\n")
            for archivo in archivos_adjuntos:
                f.write(f"- {os.path.basename(archivo)}\n")
        
        return True, f"Correo preparado correctamente. En una implementación real, se enviaría a {destinatario}."
    
    except Exception as e:
        return False, f"Error al enviar el correo: {str(e)}"

def main():
    """Función principal de la aplicación Streamlit."""
    st.title("Calculadora de Turnos en Radiología")
    
    # Inicializar el estado de la sesión
    if 'calculadora' not in st.session_state:
        st.session_state.calculadora = CalculadoraTurnos()
        st.session_state.archivo_cargado = False
        st.session_state.examenes_clasificados = False
        st.session_state.examenes_revisados = set()  # Para seguimiento de exámenes revisados
        st.session_state.dias_turno = []  # Para almacenar los días de turno seleccionados
        
        # Inicializar sistema de aprendizaje si está disponible
        if SISTEMA_APRENDIZAJE_DISPONIBLE:
            # Preferir SQLite, fallback a JSON
            if SISTEMA_APRENDIZAJE_SQLITE_DISPONIBLE:
                try:
                    st.session_state.sistema_aprendizaje = SistemaAprendizajeSQLite()
                    st.session_state.sistema_tipo = "sqlite"
                    st.sidebar.success("✅ Sistema de aprendizaje SQLite inicializado correctamente")
                except Exception as e:
                    st.sidebar.warning(f"⚠️ Error al inicializar SQLite: {e}")
                    if SISTEMA_APRENDIZAJE_JSON_DISPONIBLE:
                        st.session_state.sistema_aprendizaje = SistemaAprendizaje()
                        st.session_state.sistema_tipo = "json"
                        st.sidebar.info("ℹ️ Usando sistema de aprendizaje JSON (fallback)")
            elif SISTEMA_APRENDIZAJE_JSON_DISPONIBLE:
                st.session_state.sistema_aprendizaje = SistemaAprendizaje()
                st.session_state.sistema_tipo = "json"
                st.sidebar.info("ℹ️ Usando sistema de aprendizaje JSON")
    
    # Crear un expander para la información de introducción
    with st.expander("Acerca de la Calculadora de Turnos", expanded=not st.session_state.archivo_cargado):
        st.markdown("""
        ## Calculadora de Turnos en Radiología
        
        Esta aplicación le permite procesar datos de procedimientos médicos en radiología para:
        
        - **Analizar exámenes** de RX y TAC realizados en salas SCA y SJ
        - **Estimar y calcular** días de turno y horas trabajadas
        - **Clasificar automáticamente** exámenes incluyendo detección de TAC dobles
        - **Generar reportes** detallados para facturación y gestión
        - **Enviar informes** por correo con archivos adjuntos
        
        ### Para comenzar:
        1. Cargue un archivo CSV usando el selector en la barra lateral izquierda
        2. Utilice las herramientas de análisis para estimar sus días de turno
        3. Verifique los exámenes clasificados y genere sus reportes
        
        Esta herramienta fue diseñada para facilitar la gestión y cálculo de honorarios médicos,
        automatizando tareas repetitivas y ahorrando tiempo en la gestión administrativa.
        """)
        
        # Imagen opcional
        st.image("https://img.freepik.com/free-photo/doctor-with-stethoscope-hands-hospital-background_1423-1.jpg", 
                width=600, 
                caption="Gestión eficiente de turnos médicos")
    
    # Mostrar mensaje de inicio si no hay archivo cargado
    if not st.session_state.archivo_cargado:
        st.info("👈 Comience seleccionando un archivo CSV en el panel lateral izquierdo")
    
    # Sidebar para cargar archivo y configuraciones
    with st.sidebar:
        st.header("Configuración")
        
        # Sección para cargar el archivo CSV
        st.subheader("Cargar Archivo")
        uploaded_file = st.file_uploader("Seleccione el archivo CSV", type=['csv'])
        
        if uploaded_file is not None and (not st.session_state.archivo_cargado or 
                                          uploaded_file.name != st.session_state.get('archivo_nombre', '')):
            with st.spinner("Cargando archivo..."):
                # Cargar directamente desde Streamlit FileUploader
                exito, mensaje = st.session_state.calculadora.cargar_archivo(uploaded_file)
                if exito:
                    st.success(mensaje)
                    st.session_state.archivo_cargado = True
                    st.session_state.archivo_nombre = uploaded_file.name
                    
                    # Guardar una referencia al archivo para procesamiento posterior
                    if 'uploaded_csv' not in st.session_state:
                        st.session_state.uploaded_csv = uploaded_file
                    
                    # Continuar con el procesamiento
                    exito, mensaje = st.session_state.calculadora.filtrar_datos()
                    if exito:
                        st.info(mensaje)
                        exito, mensaje = st.session_state.calculadora.clasificar_examenes()
                        if exito:
                            st.info(mensaje)
                            st.session_state.examenes_clasificados = True
                            
                            # Aprender de los datos clasificados si el sistema está disponible
                            if SISTEMA_APRENDIZAJE_DISPONIBLE and hasattr(st.session_state, 'sistema_aprendizaje'):
                                with st.spinner("Analizando y aprendiendo patrones de datos..."):
                                    exito_aprend, msg_aprend = st.session_state.sistema_aprendizaje.analizar_dataframe(
                                        st.session_state.calculadora.data_filtrada
                                    )
                                    if exito_aprend and 'TAC doble' in st.session_state.calculadora.data_filtrada.columns:
                                        st.session_state.sistema_aprendizaje.aprender_patrones_tac_doble(
                                            st.session_state.calculadora.data_filtrada
                                        )
                                    st.success("Sistema de aprendizaje actualizado con nuevos patrones")
                            
                            # Establecer el tab activo como visualización de datos
                            if 'active_tab' not in st.session_state:
                                st.session_state.active_tab = 0
                            
                            # Recargar la página para mostrar los resultados inmediatamente
                            st.rerun()
                        else:
                            st.error(mensaje)
                    else:
                        st.error(mensaje)
                else:
                    st.error(mensaje)
        
        if st.session_state.archivo_cargado:
            # Configuración para el cálculo de turnos
            st.subheader("Configuración de Turnos")
            
            # Estimar días de turno basados en patrones
            if st.button("Estimar días de turno"):
                with st.spinner("Analizando patrones de exámenes..."):
                    fechas_estimadas = st.session_state.calculadora.estimar_dias_turno()
                    if fechas_estimadas:
                        st.session_state.fechas_estimadas = fechas_estimadas
                        st.success(f"Se estimaron {len(fechas_estimadas)} posibles días de turno")
                    else:
                        st.warning("No se pudieron estimar días de turno")
            
            # Mostrar fechas estimadas si existen
            if 'fechas_estimadas' in st.session_state and st.session_state.fechas_estimadas:
                st.markdown("### Días con alta probabilidad de turnos")
                
                # Crear dos columnas para fechas estimadas y botones de acción
                col_est, col_actions = st.columns([3, 1])
                
                with col_est:
                    # Tabla de fechas estimadas con checkbox
                    estimadas_data = []
                    for fecha, num_examenes in st.session_state.fechas_estimadas:
                        # Verificar si ya está seleccionada
                        ya_seleccionada = fecha in [d for d, _ in st.session_state.dias_turno]
                        
                        # Agregar a datos de la tabla
                        estimadas_data.append({
                            "✓": ya_seleccionada,
                            "Fecha": fecha,
                            "Exámenes": num_examenes,
                            "ID": f"est_{fecha}"
                        })
                    
                    # Convertir a dataframe para mostrar como tabla
                    df_estimadas = pd.DataFrame(estimadas_data)
                    
                    # Mostrar tabla con checkboxes editables
                    edited_df = st.data_editor(
                        df_estimadas,
                        column_config={
                            "✓": st.column_config.CheckboxColumn(
                                "Seleccionar",
                                help="Marque para confirmar como día de turno"
                            ),
                            "ID": st.column_config.Column(
                                "ID",
                                disabled=True,
                                required=True
                            )
                        },
                        hide_index=True,
                        key="editor_fechas_est"
                    )
                
                with col_actions:
                    # Botón para confirmar todas las fechas seleccionadas
                    if st.button("Confirmar seleccionadas", key="conf_todas"):
                        # Actualizar días de turno según selecciones
                        fechas_seleccionadas = []
                        for i, row in edited_df.iterrows():
                            if row["✓"]:
                                fecha = row["Fecha"]
                                if fecha not in [d for d, _ in st.session_state.dias_turno]:
                                    st.session_state.dias_turno.append((fecha, False))
                                fechas_seleccionadas.append(fecha)
                        
                        # Eliminar las que ya no están seleccionadas
                        for d, f in list(st.session_state.dias_turno):
                            if d in [fecha for fecha, _ in st.session_state.fechas_estimadas] and d not in fechas_seleccionadas:
                                st.session_state.dias_turno.remove((d, f))
                        
                        # Mostrar mensaje de confirmación
                        num_seleccionadas = sum(edited_df["✓"])
                        st.success(f"Confirmadas {num_seleccionadas} fechas de turno")
                        
                    # Botón para marcar todos como feriados
                    if st.button("Seleccionar todas", key="sel_todas"):
                        # Seleccionar todas y actualizar interfaz
                        for i, row in edited_df.iterrows():
                            edited_df.at[i, "✓"] = True
                
                # Nota informativa
                st.info("Seleccione las fechas que desea confirmar como días de turno y haga clic en 'Confirmar seleccionadas'")
                
                # Expander para mostrar instrucciones adicionales
                with st.expander("Ayuda: Cómo confirmar fechas de turno"):
                    st.markdown("""
                    1. Marque las casillas en la columna **Seleccionar** para los días que fueron efectivamente turnos.
                    2. Haga clic en **Confirmar seleccionadas** para guardarlas como días de turno.
                    3. Si necesita marcar alguna fecha como feriado, utilice la opción "Añadir día de turno" más abajo.
                    4. También puede usar **Seleccionar todas** si todos los días estimados fueron turnos.
                    """)
                
                # Separador visual
                st.divider()
            
            # Opción para agregar días de turno manualmente
            st.markdown("### Añadir día de turno")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                # Selección de fecha manual
                fecha_manual = st.date_input(
                    "Seleccione fecha",
                    dt.datetime.now(),
                    format="DD/MM/YYYY"
                )
            with col2:
                # Opción para marcar como feriado
                es_feriado = st.checkbox("Es feriado", key="manual_feriado")
            
            # Botón para agregar la fecha manual
            if st.button("Agregar fecha"):
                # Convertir a formato dd-mmm-yyyy
                meses_esp = {
                    1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun',
                    7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
                }
                
                fecha_esp = f"{fecha_manual.day:02d}-{meses_esp[fecha_manual.month]}-{fecha_manual.year}"
                
                # Verificar si ya existe
                if fecha_esp in [d for d, _ in st.session_state.dias_turno]:
                    st.warning(f"La fecha {fecha_esp} ya está en la lista")
                else:
                    st.session_state.dias_turno.append((fecha_esp, es_feriado))
                    st.success(f"Fecha {fecha_esp} agregada")
            
            # Mostrar lista actual de días de turno
            if st.session_state.dias_turno:
                st.markdown("### Días de turno confirmados")
                
                # Crear tabla con los días confirmados
                turnos_data = []
                for i, (fecha, es_feriado) in enumerate(st.session_state.dias_turno):
                    turnos_data.append({
                        "Fecha": fecha,
                        "Tipo": "🔴 FERIADO" if es_feriado else "📆 Normal",
                        "Acción": f"del_{i}"  # ID para botones de eliminar
                    })
                
                # Convertir a dataframe
                df_turnos = pd.DataFrame(turnos_data)
                
                # Mostrar tabla con opción de eliminar
                st.dataframe(df_turnos[["Fecha", "Tipo"]], hide_index=True)
                
                # Opciones para gestionar días confirmados
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    if st.button("Eliminar seleccionados", key="del_sel"):
                        # Como no tenemos selección múltiple directa, esta opción abre un selector
                        st.session_state.mostrar_selector_eliminar = True
                
                with col2:
                    if st.button("Marcar como feriado", key="mark_holiday"):
                        st.session_state.mostrar_selector_feriado = True
                
                with col3:
                    if st.button("Limpiar todos", key="clear_all"):
                        # Pedir confirmación
                        if st.session_state.get('confirmar_limpiar', False):
                            st.session_state.dias_turno = []
                            st.session_state.confirmar_limpiar = False
                            st.success("Se han eliminado todos los días de turno")
                            st.rerun()
                        else:
                            st.session_state.confirmar_limpiar = True
                            st.warning("¿Está seguro? Presione de nuevo para confirmar")
                
                # Selector para eliminar días específicos
                if st.session_state.get('mostrar_selector_eliminar', False):
                    # Crear lista de opciones
                    opciones = [f"{fecha} {'(FERIADO)' if es_feriado else ''}" for fecha, es_feriado in st.session_state.dias_turno]
                    indices = list(range(len(opciones)))
                    
                    # Mostrar selector múltiple
                    st.markdown("#### Seleccione días a eliminar")
                    dias_a_eliminar = st.multiselect("Días a eliminar", 
                                                     options=indices, 
                                                     format_func=lambda x: opciones[x])
                    
                    # Botón para confirmar eliminación
                    if st.button("Eliminar seleccionados", key="confirm_del"):
                        # Eliminar en orden inverso para evitar problemas de índices
                        for idx in sorted(dias_a_eliminar, reverse=True):
                            if 0 <= idx < len(st.session_state.dias_turno):
                                st.session_state.dias_turno.pop(idx)
                        
                        # Limpiar estado y refrescar
                        st.session_state.mostrar_selector_eliminar = False
                        st.success(f"Se eliminaron {len(dias_a_eliminar)} días de turno")
                        st.rerun()
                
                # Selector para marcar días como feriado
                if st.session_state.get('mostrar_selector_feriado', False):
                    # Crear lista de opciones (solo mostrar días normales)
                    dias_normales = [(i, fecha) for i, (fecha, es_feriado) in enumerate(st.session_state.dias_turno) if not es_feriado]
                    
                    if dias_normales:
                        opciones = [fecha for _, fecha in dias_normales]
                        indices = [i for i, _ in dias_normales]
                        
                        # Mostrar selector múltiple
                        st.markdown("#### Seleccione días a marcar como feriado")
                        dias_a_marcar = st.multiselect("Días a marcar como feriado", 
                                                      options=indices, 
                                                      format_func=lambda x: opciones[indices.index(x)])
                        
                        # Botón para confirmar
                        if st.button("Marcar como feriado", key="confirm_holiday"):
                            # Marcar días seleccionados como feriado
                            for idx in dias_a_marcar:
                                # Buscar la fecha en la lista original
                                for i, (fecha, es_feriado) in enumerate(st.session_state.dias_turno):
                                    if i == idx:
                                        # Actualizar marcando como feriado
                                        st.session_state.dias_turno[i] = (fecha, True)
                            
                            # Limpiar estado y refrescar
                            st.session_state.mostrar_selector_feriado = False
                            st.success(f"Se marcaron {len(dias_a_marcar)} días como feriado")
                            st.rerun()
                    else:
                        st.info("No hay días normales disponibles para marcar como feriado")
                        if st.button("Cerrar", key="close_feriado"):
                            st.session_state.mostrar_selector_feriado = False
                            st.rerun()
            
    # Verificar si el módulo de asistente phi-2 está disponible
    has_phi2 = importlib.util.find_spec("asistente_phi2") is not None

    # Contenido principal
    if st.session_state.archivo_cargado:
        tab_names = ["Visualización de Datos", "Análisis de Exámenes", "Generar Reportes"]
        
        # Agregar tab de configuración avanzada si el sistema de aprendizaje está disponible
        if SISTEMA_APRENDIZAJE_DISPONIBLE and hasattr(st.session_state, 'sistema_aprendizaje'):
            tab_names.append("Configuración Avanzada")
        
        # Agregar tab para asistente con phi-2 si está disponible
        if has_phi2:
            tab_names.append("Asistente phi-2")
        
        # Usar active_tab para seleccionar la pestaña activa por defecto
        active_tab_index = st.session_state.get('active_tab', 0)
        
        # Asegurar que el índice es válido
        if active_tab_index >= len(tab_names):
            active_tab_index = 0
            st.session_state.active_tab = 0
            
        tabs = st.tabs(tab_names)
        
        # Tab 1: Visualización de Datos
        with tabs[0]:
            st.header("Visualización de Datos")
            
            # Mostrar los datos cargados
            if st.session_state.calculadora.data_filtrada is not None:
                st.subheader("Vista previa de datos")
                df = st.session_state.calculadora.data_filtrada
                
                # Seleccionar las columnas en el orden deseado
                columnas = [
                    'Número de cita',
                    'Fecha del procedimiento programado',
                    'Apellidos del paciente',
                    'Nombre del paciente',
                    'Nombre del procedimiento',
                    'Sala de adquisición',
                    'Tipo'
                ]
                
                # Verificar que todas las columnas existen
                columnas_disponibles = [col for col in columnas if col in df.columns]
                
                # Renombrar columnas para que sean más cortas y elegantes
                df_display = df[columnas_disponibles].copy()
                nombres_nuevos = {
                    'Número de cita': 'Nº Cita',
                    'Fecha del procedimiento programado': 'Fecha',
                    'Apellidos del paciente': 'Apellidos',
                    'Nombre del paciente': 'Nombre',
                    'Nombre del procedimiento': 'Procedimiento',
                    'Sala de adquisición': 'Sala'
                }
                
                df_display.rename(columns={k: v for k, v in nombres_nuevos.items() if k in df_display.columns}, 
                               inplace=True)
                
                # Barra de búsqueda para filtrar datos en tiempo real
                st.subheader("Búsqueda de exámenes")
                col1, col2 = st.columns([3, 1])
                with col1:
                    busqueda = st.text_input("Búsqueda (nombre, apellido, ID, procedimiento...)", 
                                           key="busqueda_examen")
                with col2:
                    tipo_filtro = st.selectbox("Tipo", ["Todos", "RX", "TAC", "TAC doble", "TAC triple"], key="tipo_filtro")
                
                # Filtrar por texto de búsqueda
                df_filtrado = df_display
                if busqueda:
                    # Buscar en todas las columnas
                    mask = pd.Series(False, index=df_filtrado.index)
                    for col in df_filtrado.columns:
                        mask |= df_filtrado[col].astype(str).str.contains(busqueda, case=False, na=False)
                    df_filtrado = df_filtrado[mask]
                
                # Filtrar por tipo
                original_index = df_filtrado.index.tolist()
                if tipo_filtro == "RX":
                    indices = [i for i in original_index if df['Tipo'].iloc[i] == 'RX']
                    df_filtrado = df_filtrado.loc[indices]
                elif tipo_filtro == "TAC":
                    indices = [i for i in original_index if df['Tipo'].iloc[i] == 'TAC']
                    df_filtrado = df_filtrado.loc[indices]
                elif tipo_filtro == "TAC doble":
                    if 'TAC doble' in df.columns:
                        indices = [i for i in original_index if df['TAC doble'].iloc[i] == True]
                        df_filtrado = df_filtrado.loc[indices]
                    else:
                        st.warning("No hay datos con clasificación de TAC doble")
                        df_filtrado = pd.DataFrame(columns=df.columns)
                elif tipo_filtro == "TAC triple":
                    if 'TAC triple' in df.columns:
                        indices = [i for i in original_index if df['TAC triple'].iloc[i] == True]
                        df_filtrado = df_filtrado.loc[indices]
                    else:
                        st.warning("No hay datos con clasificación de TAC triple")
                        df_filtrado = pd.DataFrame(columns=df.columns)
                
                # Mostrar métricas de resultados
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de exámenes filtrados", len(df_filtrado))
                with col2:
                    rx_count = sum(df.loc[df_filtrado.index, 'Tipo'] == 'RX') if not df_filtrado.empty else 0
                    st.metric("RX", rx_count)
                with col3:
                    tac_count = sum(df.loc[df_filtrado.index, 'Tipo'] == 'TAC') if not df_filtrado.empty else 0
                    tac_doble_count = sum(df.loc[df_filtrado.index, 'TAC doble'] == True) if not df_filtrado.empty else 0
                    tac_triple_count = sum(df.loc[df_filtrado.index, 'TAC triple'] == True) if 'TAC triple' in df.columns and not df_filtrado.empty else 0
                    st.metric("TAC (dobles/triples)", f"{tac_count} ({tac_doble_count}/{tac_triple_count})")
                
                # Mostrar la tabla con los resultados de la búsqueda
                if df_filtrado.empty:
                    st.info("No se encontraron exámenes que coincidan con los criterios de búsqueda.")
                else:
                    st.dataframe(df_filtrado, height=400)
                
                # Opción para descargar los datos
                st.markdown(get_table_download_link(df_filtrado, 
                                                  "datos_filtrados", 
                                                  "Descargar datos filtrados"), 
                          unsafe_allow_html=True)
                
                # Visualizaciones
                st.subheader("Visualizaciones")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de distribución por fecha y tipo
                    fig1 = plot_distribucion_examenes(df)
                    if fig1:
                        st.plotly_chart(fig1, use_container_width=True)
                
                with col2:
                    # Gráfico de distribución por sala
                    fig2 = plot_distribucion_salas(df)
                    if fig2:
                        st.plotly_chart(fig2, use_container_width=True)
                
        # Tab 2: Análisis de Exámenes
        with tabs[1]:
            st.header("Análisis de Exámenes")
            
            if st.session_state.examenes_clasificados:
                # Mostrar detalles de exámenes por tipo
                st.subheader("Exámenes de Radiografía (RX)")
                df_rx = st.session_state.calculadora.data_filtrada[
                    st.session_state.calculadora.data_filtrada['Tipo'] == 'RX'
                ]
                
                # Mismo formato que en la visualización
                columnas = [
                    'Número de cita',
                    'Fecha del procedimiento programado',
                    'Apellidos del paciente',
                    'Nombre del paciente',
                    'Nombre del procedimiento',
                    'Sala de adquisición'
                ]
                columnas_disponibles = [col for col in columnas if col in df_rx.columns]
                df_rx_display = df_rx[columnas_disponibles].copy()
                df_rx_display.rename(columns={k: v for k, v in nombres_nuevos.items() if k in df_rx_display.columns}, 
                                  inplace=True)
                
                # Añadir columna de checklist para verificación
                if not df_rx_display.empty:
                    mostrar_df_interactivo(df_rx_display, "rx_table")
                    st.text(f"Total de exámenes RX: {len(df_rx_display)}")
                else:
                    st.info("No hay exámenes de tipo RX")
                
                st.subheader("Exámenes de Tomografía (TAC)")
                df_tac = st.session_state.calculadora.data_filtrada[
                    st.session_state.calculadora.data_filtrada['Tipo'] == 'TAC'
                ]
                
                columnas_disponibles = [col for col in columnas if col in df_tac.columns]
                df_tac_display = df_tac[columnas_disponibles].copy()
                df_tac_display.rename(columns={k: v for k, v in nombres_nuevos.items() if k in df_tac_display.columns}, 
                                   inplace=True)
                
                if not df_tac_display.empty:
                    # Identificar TAC dobles
                    tac_dobles = st.session_state.calculadora.data_filtrada[
                        st.session_state.calculadora.data_filtrada['TAC doble'] == True
                    ]
                    tac_dobles_ids = set(tac_dobles['Número de cita'])
                    
                    # Resaltar TAC dobles (esto funcionaría mejor con aggrid o similar)
                    st.text("Los exámenes TAC doble están marcados con asterisco (*)")
                    df_tac_display['Nº Cita'] = df_tac_display['Nº Cita'].apply(
                        lambda x: f"{x} *" if x in tac_dobles_ids else x
                    )
                    
                    mostrar_df_interactivo(df_tac_display, "tac_table")
                    
                    # Conteos
                    tac_simples = len(df_tac) - len(tac_dobles)
                    st.text(f"Total de exámenes TAC: {len(df_tac)} (simples: {tac_simples}, dobles: {len(tac_dobles)})")
                    
                    # Sección para verificar TAC dobles
                    with st.expander("Verificar detección de TAC dobles", expanded=False):
                        st.write("Esta sección muestra ejemplos de TAC dobles detectados según diferentes patrones")
                        
                        # Patrones específicos a verificar
                        patrones_verificar = [
                            "TX/ABD/PEL",
                            "Torax-Abdomen-Pelvis",
                            "Tórax Abdomen Pelvis",
                            "tórax, abdomen y pelvis",
                            "torax, abdomen"
                        ]
                        
                        # Buscar TAC dobles por patrón
                        for patron in patrones_verificar:
                            examenes_patron = st.session_state.calculadora.data_filtrada[
                                st.session_state.calculadora.data_filtrada['Nombre del procedimiento'].str.contains(
                                    patron, case=False, na=False
                                )
                            ]
                            
                            if not examenes_patron.empty:
                                # Crear tabla para mostrar
                                df_patron = examenes_patron[['Número de cita', 'Nombre del procedimiento', 'TAC doble']].copy()
                                
                                # Contar cuántos fueron detectados como dobles
                                total_patron = len(df_patron)
                                clasificados_doble = sum(df_patron['TAC doble'])
                                
                                st.write(f"**Patrón '{patron}'**: {clasificados_doble} de {total_patron} detectados como TAC doble")
                                
                                if clasificados_doble < total_patron:
                                    st.warning(f"⚠️ ¡Atención! {total_patron - clasificados_doble} exámenes con patrón '{patron}' NO fueron clasificados como TAC doble")
                                
                                # Mostrar los primeros ejemplos
                                st.dataframe(df_patron.head(5))
                else:
                    st.info("No hay exámenes de tipo TAC")
                
        # Tab 3: Generar Reportes
        with tabs[2]:
            st.header("Generar Reportes")
            
            st.subheader("Generación de Archivos Excel y Correo")
            
            # Crear columnas para organizar la interfaz
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Configuración del doctor
                nombre_doctor = st.text_input("Nombre del Doctor", 
                                          value=st.session_state.get('nombre_doctor', 'Cikutovic'),
                                          key="nombre_doc_reportes")
                
                # Guardar el nombre del doctor en la sesión
                if nombre_doctor != st.session_state.get('nombre_doctor', ''):
                    st.session_state.nombre_doctor = nombre_doctor
                
                # Selección de directorio de salida
                directorio_base = os.path.dirname(os.path.abspath(__file__))
                fecha_actual = datetime.now()
                mes = fecha_actual.strftime("%B").upper()
                año = fecha_actual.strftime("%Y")
                
                # Traducir mes a español si es necesario
                meses_es = {
                    "JANUARY": "ENERO", "FEBRUARY": "FEBRERO", "MARCH": "MARZO", "APRIL": "ABRIL",
                    "MAY": "MAYO", "JUNE": "JUNIO", "JULY": "JULIO", "AUGUST": "AGOSTO",
                    "SEPTEMBER": "SEPTIEMBRE", "OCTOBER": "OCTUBRE", "NOVEMBER": "NOVIEMBRE", "DECEMBER": "DICIEMBRE"
                }
                
                if mes in meses_es:
                    mes = meses_es[mes]
                
                # Crear directorio de salida por defecto
                directorio_defecto = os.path.join(directorio_base, "csv", f"TURNOS {mes} {año}")
                
                # Mostrar ruta y botón para cambiar
                st.text(f"Directorio de salida: {directorio_defecto}")
                if st.button("Cambiar directorio"):
                    # Aquí se podría añadir un selector, pero Streamlit no tiene uno nativo
                    # por lo que usamos el predeterminado
                    pass
            
            with col2:
                # Mostrar configuración de fechas de turno
                st.text("Fechas de turno seleccionadas:")
                
                if hasattr(st.session_state, 'dias_turno') and st.session_state.dias_turno:
                    for fecha, es_feriado in st.session_state.dias_turno:
                        st.text(f"✓ {fecha} {'(FERIADO)' if es_feriado else ''}")
                else:
                    st.warning("No hay fechas de turno seleccionadas. Seleccione fechas en la pestaña Visualización.")
            
            # Separador visual
            st.divider()
            
            # Botón para generar reportes
            if st.button("Generar Reportes Excel", type="primary"):
                if not hasattr(st.session_state, 'dias_turno') or not st.session_state.dias_turno:
                    st.error("Debe seleccionar al menos una fecha de turno")
                else:
                    # Crear directorio si no existe
                    os.makedirs(directorio_defecto, exist_ok=True)
                    
                    # Preparar fechas en formato correcto para la calculadora
                    fechas_turno = ','.join([fecha for fecha, _ in st.session_state.dias_turno])
                    
                    # Calcular horas de turno por fechas
                    with st.spinner("Procesando datos y generando reportes..."):
                        # Ejecutar procesamiento
                        # Si tenemos el CSV cargado en la sesión, lo usamos directamente
                        if 'uploaded_csv' in st.session_state:
                            # Guardar temporalmente el archivo
                            import tempfile
                            temp_dir = tempfile.mkdtemp()
                            temp_file = os.path.join(temp_dir, st.session_state.archivo_nombre)
                            
                            with open(temp_file, 'wb') as f:
                                f.write(st.session_state.uploaded_csv.getbuffer())
                            
                            # Ejecutar procesamiento con la ruta temporal
                            exito, resultado = st.session_state.calculadora.procesar_archivo(
                                temp_file,
                                directorio_defecto,
                                nombre_doctor,
                                fechas_turno
                            )
                        else:
                            st.error("No se encontró el archivo cargado en la sesión")
                            exito = False
                            resultado = "Error: archivo no disponible"
                        
                        if exito:
                            st.success("¡Reportes generados correctamente!")
                            
                            # Guardar rutas para acceso posterior
                            st.session_state.archivos_generados = resultado['rutas_excel']
                            st.session_state.correo_generado = resultado['correo']
                            st.session_state.resultado_economico = resultado['resultado_economico']
                            
                            # Mostrar resumen
                            st.subheader("Resumen Económico")
                            eco = resultado['resultado_economico']
                            
                            # Crear tabla resumen
                            resumen_data = [
                                ["Horas trabajadas", eco['horas_trabajadas'], f"${eco['honorarios_hora']:,}"],
                                ["Exámenes RX", eco['rx_count'], f"${eco['rx_total']:,}"],
                                ["Exámenes TAC", eco['tac_count'], f"${eco['tac_total']:,}"],
                                ["TAC doble", eco['tac_doble_count'], f"${eco['tac_doble_total']:,}"],
                                ["TAC triple", eco['tac_triple_count'], f"${eco['tac_triple_total']:,}"],
                                ["**TOTAL**", "", f"**${eco['total']:,}**"]
                            ]
                            
                            # Mostrar como dataframe para mejor formato
                            df_resumen = pd.DataFrame(resumen_data, columns=["Concepto", "Cantidad", "Monto"])
                            st.dataframe(df_resumen, hide_index=True)
                            
                            # Mostrar botones para abrir archivos
                            st.subheader("Archivos Generados")
                            
                            for nombre, ruta in resultado['rutas_excel'].items():
                                if st.button(f"Abrir {os.path.basename(ruta)}"):
                                    # Abrir archivo (esto no funciona directamente en Streamlit, pero sí en local)
                                    import webbrowser
                                    webbrowser.open(ruta)
                            
                            # Mostrar contenido del correo
                            st.subheader("Contenido del Correo")
                            st.text_area("Asunto", resultado['correo']['asunto'], height=50)
                            st.text_area("Cuerpo", resultado['correo']['cuerpo'], height=300)
                        else:
                            st.error(f"Error al generar reportes: {resultado}")
            
            # Verificar si hay archivos generados previamente
            if 'archivos_generados' in st.session_state and 'correo_generado' in st.session_state:
                # Mostrar contenido del correo generado previamente
                with st.expander("Ver correo generado anteriormente"):
                    st.text("Asunto:")
                    st.code(st.session_state.correo_generado['asunto'])
                    st.text("Cuerpo:")
                    st.code(st.session_state.correo_generado['cuerpo'])
                
                # Mostrar resumen económico anterior
                if 'resultado_economico' in st.session_state:
                    with st.expander("Ver resumen económico anterior"):
                        eco = st.session_state.resultado_economico
                        
                        # Crear tabla resumen
                        resumen_data = [
                            ["Horas trabajadas", eco['horas_trabajadas'], f"${eco['honorarios_hora']:,}"],
                            ["Exámenes RX", eco['rx_count'], f"${eco['rx_total']:,}"],
                            ["Exámenes TAC", eco['tac_count'], f"${eco['tac_total']:,}"],
                            ["TAC doble", eco['tac_doble_count'], f"${eco['tac_doble_total']:,}"],
                            ["TAC triple", eco['tac_triple_count'], f"${eco['tac_triple_total']:,}"],
                            ["**TOTAL**", "", f"**${eco['total']:,}**"]
                        ]
                        
                        # Mostrar como dataframe para mejor formato
                        df_resumen = pd.DataFrame(resumen_data, columns=["Concepto", "Cantidad", "Monto"])
                        st.dataframe(df_resumen, hide_index=True)
        
        # Tab 4: Configuración Avanzada (solo si el sistema de aprendizaje está disponible)
        # Tab de Configuración Avanzada
        tab_idx = 3
        if SISTEMA_APRENDIZAJE_DISPONIBLE and hasattr(st.session_state, 'sistema_aprendizaje') and len(tabs) > tab_idx:
            with tabs[tab_idx]:
                st.header("Configuración Avanzada")
                tab_idx += 1
        
        # Tab de Asistente phi-2
        if has_phi2 and len(tabs) > tab_idx:
            with tabs[tab_idx]:
                st.header("Asistente con phi-2")
                
                # Solo cargar e inicializar el asistente cuando se accede a esta pestaña
                # para evitar cargar dependencias innecesarias
                try:
                    from asistente_phi2 import AsistentePhi2
                    
                    # Inicializar el asistente si no existe
                    if 'phi2_asistente' not in st.session_state:
                        st.session_state.phi2_asistente = AsistentePhi2()
                        st.session_state.phi2_historial = []
                        
                        # Conectar automáticamente a la base de datos de conocimiento si existe
                        conocimiento_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conocimiento", "conocimiento.db")
                        if os.path.exists(conocimiento_db):
                            try:
                                st.session_state.phi2_asistente._conectar_db(conocimiento_db)
                                st.session_state.phi2_db_conectada = True
                            except:
                                st.session_state.phi2_db_conectada = False
                    
                    # Verificar estado de la instalación
                    estado = st.session_state.phi2_asistente.verificar_instalacion()
                    
                    if not estado["ollama_ejecutando"]:
                        st.warning("⚠️ Ollama no está en ejecución. El asistente necesita Ollama para funcionar.")
                        if st.button("Iniciar Ollama"):
                            import subprocess
                            try:
                                subprocess.Popen(["ollama", "serve"], 
                                               stdout=subprocess.PIPE, 
                                               stderr=subprocess.PIPE)
                                st.success("Ollama iniciado. Espere unos segundos...")
                                st.balloons()
                            except Exception as e:
                                st.error(f"Error al iniciar Ollama: {e}")
                    
                    # Mostrar estado de la conexión a la base de datos
                    if st.session_state.get('phi2_db_conectada', False):
                        st.success("✅ Base de datos de conocimiento conectada")
                    else:
                        st.warning("⚠️ Base de datos de conocimiento no disponible")
                        conocimiento_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conocimiento", "conocimiento.db")
                        if st.button("Conectar a base de conocimiento"):
                            try:
                                if st.session_state.phi2_asistente._conectar_db(conocimiento_db):
                                    st.session_state.phi2_db_conectada = True
                                    st.success("Conectado exitosamente")
                                    st.rerun()
                                else:
                                    st.error("No se pudo conectar a la base de datos")
                            except Exception as e:
                                st.error(f"Error al conectar: {e}")
                    
                    # Información sobre phi-2
                    with st.expander("ℹ️ Acerca de phi-2", expanded=not estado["ollama_ejecutando"]):
                        st.markdown("""
                        ## phi-2: Modelo Ultraliviano de Microsoft
                        
                        * **Tamaño**: Solo 1.7B parámetros
                        * **Velocidad**: Extremadamente rápido, incluso en CPU
                        * **Especialidad**: Excelente en tareas estructuradas y consultas SQL
                        * **Recursos**: Mínimo consumo de memoria y CPU
                        
                        ### Ventajas para análisis radiológico
                        
                        * Puede analizar patrones en los datos estructurados de exámenes
                        * Formular consultas complejas a partir de preguntas en lenguaje natural
                        * Funcionar localmente sin enviar datos sensibles a la nube
                        * Generar resúmenes concisos de los resultados
                        
                        ### Instalación
                        
                        El asistente requiere [Ollama](https://ollama.ai) para funcionar.
                        Una vez instalado, el modelo se descarga automáticamente con:
                        
                        ```bash
                        ollama pull phi
                        ```
                        """)
                    
                    # Interfaz de consulta
                    if estado["ollama_ejecutando"]:
                        # Crear base de datos temporal si se ha cargado un archivo
                        if st.session_state.calculadora.data_filtrada is not None and 'db_creada' not in st.session_state:
                            # Crear copia del DataFrame
                            df = st.session_state.calculadora.data_filtrada.copy()
                            with st.spinner("Preparando datos para consultas..."):
                                # Crear base de datos temporal
                                db_path = st.session_state.phi2_asistente.crear_base_datos_temporal(df, "examenes")
                                if db_path:
                                    st.session_state.db_creada = True
                                    st.success("✅ Datos preparados para consultas")
                        
                        # Campo para consultas
                        st.markdown("### Consulta en lenguaje natural")
                        consulta = st.text_input("Haz una pregunta sobre los exámenes:",
                                              placeholder="Ej: ¿Cuántos exámenes TAC hay en total?",
                                              key="phi2_consulta")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Realizar consulta SQL", key="btn_consulta_sql"):
                                if not consulta:
                                    st.warning("Por favor escribe una consulta primero")
                                else:
                                    with st.spinner("Procesando consulta..."):
                                        exito, resultado = st.session_state.phi2_asistente.consulta_natural(consulta)
                                        
                                        # Guardar en historial
                                        st.session_state.phi2_historial.append({
                                            "consulta": consulta,
                                            "tipo": "sql",
                                            "exito": exito,
                                            "resultado": resultado
                                        })
                                        
                                        if exito and isinstance(resultado, pd.DataFrame):
                                            st.dataframe(resultado)
                                        else:
                                            st.error(f"Error: {resultado}")
                        
                        with col2:
                            if st.button("Generar respuesta", key="btn_respuesta"):
                                if not consulta:
                                    st.warning("Por favor escribe una consulta primero")
                                else:
                                    with st.spinner("Generando respuesta con phi-2..."):
                                        respuesta = st.session_state.phi2_asistente.generar_respuesta(consulta)
                                        
                                        # Guardar en historial
                                        st.session_state.phi2_historial.append({
                                            "consulta": consulta,
                                            "tipo": "respuesta",
                                            "resultado": respuesta
                                        })
                                        
                                        st.info(respuesta)
                        
                        # Mostrar historial de consultas
                        if st.session_state.phi2_historial:
                            with st.expander("Historial de consultas", expanded=False):
                                for i, item in enumerate(reversed(st.session_state.phi2_historial)):
                                    st.markdown(f"**Consulta {len(st.session_state.phi2_historial)-i}:** {item['consulta']}")
                                    
                                    if item["tipo"] == "sql":
                                        if item.get("exito", False) and isinstance(item["resultado"], pd.DataFrame):
                                            st.dataframe(item["resultado"], height=150)
                                        else:
                                            st.error(str(item["resultado"]))
                                    else:
                                        st.info(item["resultado"])
                                    
                                    st.divider()
                    
                except ImportError:
                    st.error("El módulo asistente_phi2 no está disponible. Por favor, instale las dependencias necesarias.")
                    
                    with st.expander("Instrucciones de instalación"):
                        st.markdown("""
                        ## Instalación de dependencias para el asistente phi-2
                        
                        1. Instalar Ollama desde [ollama.ai](https://ollama.ai)
                        2. Instalar las dependencias Python:
                           ```bash
                           pip install requests sqlite3
                           ```
                        3. Descargar el modelo phi-2:
                           ```bash
                           ollama pull phi
                           ```
                        
                        Una vez completados estos pasos, reinicie la aplicación.
                        """)
                
                except Exception as e:
                    st.error(f"Error al inicializar el asistente phi-2: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
                
                # Mostrar estadísticas del sistema de aprendizaje
                stats = st.session_state.sistema_aprendizaje.obtener_estadisticas()
                
                # Sección de estadísticas generales
                with st.expander("Estadísticas del sistema de aprendizaje", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Procedimientos únicos", stats['procedimientos']['total'])
                        st.write("Distribución por tipo:")
                        for tipo, count in stats['procedimientos']['por_tipo'].items():
                            st.text(f"- {tipo}: {count}")
                    
                    with col2:
                        st.metric("Salas únicas", stats['salas']['total'])
                        st.write("Distribución por tipo:")
                        for tipo, count in stats['salas']['por_tipo'].items():
                            st.text(f"- {tipo}: {count}")
                        
                        st.metric("Patrones de TAC doble", stats['patrones_tac_doble'])
                        if 'patrones_tac_triple' in stats:
                            st.metric("Patrones de TAC triple", stats['patrones_tac_triple'])
                
                # Sección para ver procedimientos TAC doble
                with st.expander("Procedimientos TAC doble conocidos", expanded=False):
                    tac_doble_procs = st.session_state.sistema_aprendizaje.obtener_procedimientos_tipo('TAC', 'DOBLE')
                    
                    if tac_doble_procs:
                        # Crear DataFrame para mostrar
                        df_tac_doble = pd.DataFrame(tac_doble_procs)
                        st.dataframe(df_tac_doble)
                        
                        st.download_button(
                            "Descargar lista de TAC dobles",
                            df_tac_doble.to_csv(index=False).encode('utf-8'),
                            "tac_dobles.csv",
                            "text/csv",
                            key='download-tac-doble'
                        )
                
                # Sección para ver procedimientos TAC triple (solo si es sistema SQLite)
                if hasattr(st.session_state, 'sistema_tipo') and st.session_state.sistema_tipo == 'sqlite':
                    with st.expander("Procedimientos TAC triple conocidos", expanded=False):
                        try:
                            tac_triple_procs = st.session_state.sistema_aprendizaje.obtener_procedimientos_tipo('TAC', 'TRIPLE')
                            
                            if tac_triple_procs:
                                # Crear DataFrame para mostrar
                                df_tac_triple = pd.DataFrame(tac_triple_procs)
                                st.dataframe(df_tac_triple)
                                
                                st.download_button(
                                    "Descargar lista de TAC triples",
                                    df_tac_triple.to_csv(index=False).encode('utf-8'),
                                    "tac_triples.csv",
                                    "text/csv",
                                    key='download-tac-triple'
                                )
                            else:
                                st.info("No hay procedimientos TAC triple registrados.")
                        except Exception as e:
                            st.warning(f"No se pudieron obtener los procedimientos TAC triple: {e}")
                else:
                    if not tac_doble_procs:
                        st.info("Aún no se han aprendido procedimientos TAC doble")
                
                # Sección para ver salas conocidas
                with st.expander("Salas conocidas", expanded=False):
                    # Selector para el tipo de sala
                    tipo_sala = st.selectbox(
                        "Tipo de sala",
                        ["SCA", "SJ", "HOS", "OTRO"]
                    )
                    
                    salas = st.session_state.sistema_aprendizaje.obtener_salas_tipo(tipo_sala)
                    
                    if salas:
                        # Crear DataFrame para mostrar
                        df_salas = pd.DataFrame(salas)
                        st.dataframe(df_salas)
                    else:
                        st.info(f"No se encontraron salas de tipo {tipo_sala}")
                
                # Sección para buscar procedimientos
                with st.expander("Buscar procedimientos por nombre", expanded=False):
                    busqueda_proc = st.text_input("Ingrese término de búsqueda")
                    
                    if busqueda_proc:
                        # Buscar procedimientos que contengan el término
                        procs_encontrados = []
                        for nombre, datos in st.session_state.sistema_aprendizaje.procedimientos.items():
                            if busqueda_proc.lower() in nombre.lower():
                                procs_encontrados.append({
                                    "nombre": nombre,
                                    "codigo": datos["codigo"],
                                    "tipo": datos["tipo"],
                                    "subtipo": datos["subtipo"],
                                    "conteo": datos["conteo"]
                                })
                        
                        if procs_encontrados:
                            # Ordenar por conteo (mayor a menor)
                            procs_encontrados = sorted(procs_encontrados, key=lambda x: x["conteo"], reverse=True)
                            df_encontrados = pd.DataFrame(procs_encontrados)
                            st.dataframe(df_encontrados, height=300)
                            
                            # Mostrar cuántos TAC dobles
                            tac_dobles_encontrados = sum(1 for p in procs_encontrados if p["tipo"] == "TAC" and p["subtipo"] == "DOBLE")
                            if tac_dobles_encontrados > 0:
                                st.info(f"{tac_dobles_encontrados} de los resultados son TAC doble")
                        else:
                            st.info(f"No se encontraron procedimientos con '{busqueda_proc}'")
                
                # Mensaje informativo
                st.markdown("""
                **Información**: El sistema de aprendizaje recopila y analiza datos de los archivos procesados para mejorar
                la precisión en la detección de patrones como TAC dobles y tipos de salas. Cuantos más archivos
                procese, más precisa será la clasificación automática.
                """)
                st.info("Todos los datos aprendidos se guardan para futuras sesiones y se actualizan automáticamente.")
            
            # Formulario para generar reportes
            if st.session_state.examenes_clasificados and st.session_state.dias_turno:
                # Configuración del médico
                st.subheader("Información del Médico")
                nombre_doctor = st.text_input("Nombre del Doctor", "Cikutovic", help="Este nombre se utilizará en el correo y los reportes")
                
                # Almacenar en session_state para mantener consistencia
                if nombre_doctor != st.session_state.get('nombre_doctor', ''):
                    st.session_state.nombre_doctor = nombre_doctor
                    st.info(f"Nombre del doctor actualizado a: {nombre_doctor}")
                
                # Calcular horas de turno basadas en días seleccionados
                with st.spinner("Calculando horas de turno..."):
                    # Contabilizar los exámenes primero
                    if not hasattr(st.session_state.calculadora, 'examenes_contabilizados') or st.session_state.calculadora.examenes_contabilizados is None:
                        exito, mensaje = st.session_state.calculadora.contabilizar_examenes()
                        if not exito:
                            st.warning(mensaje)
                            
                    # Calcular las horas según los días de turno
                    total_horas = st.session_state.calculadora.calcular_horas_turno_especificas(st.session_state.dias_turno)
                
                # Calcular honorarios con las horas calculadas
                resultado_eco = st.session_state.calculadora.calcular_honorarios(total_horas)
                
                # Mostrar resumen económico en forma de métricas
                st.subheader("Resumen Económico")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Horas trabajadas", f"{resultado_eco['horas_trabajadas']} hrs.", 
                             help="Total de horas según días de turno")
                    st.metric("Honorarios por horas", f"${resultado_eco['honorarios_hora']:,}", 
                             help=f"Tarifa: ${st.session_state.calculadora.TARIFA_HORA:,} por hora")
                
                with col2:
                    st.metric("Exámenes RX", resultado_eco['rx_count'], 
                             help=f"Tarifa: ${st.session_state.calculadora.TARIFA_RX:,} por examen")
                    st.metric("Honorarios por RX", f"${resultado_eco['rx_total']:,}")
                
                with col3:
                    # Verificar si hay TAC triple en los resultados
                    has_tac_triple = 'tac_triple_count' in resultado_eco and resultado_eco['tac_triple_count'] > 0
                    
                    # Calcular totales
                    tac_fisicos = resultado_eco['tac_count'] + resultado_eco['tac_doble_count'] + (resultado_eco['tac_triple_count'] if has_tac_triple else 0)
                    tac_valor = resultado_eco['tac_total'] + resultado_eco['tac_doble_total'] + (resultado_eco['tac_triple_total'] if has_tac_triple else 0)
                    
                    # Calcular total para informe (dobles como 2, triples como 3)
                    tac_conteo_total = resultado_eco['tac_count'] + (resultado_eco['tac_doble_count'] * 2) + (resultado_eco['tac_triple_count'] * 3 if has_tac_triple else 0)
                    
                    # Texto para mostrar TAC doble/triple
                    tac_doble_text = f"{resultado_eco['tac_doble_count']} dobles"
                    tac_triple_text = f", {resultado_eco['tac_triple_count']} triples" if has_tac_triple else ""
                    
                    # Tarifas para mostrar en el tooltip
                    help_text = f"Tarifa: ${st.session_state.calculadora.TARIFA_TAC:,} normal, ${st.session_state.calculadora.TARIFA_TAC_DOBLE:,} doble"
                    if has_tac_triple:
                        help_text += f", ${st.session_state.calculadora.TARIFA_TAC_TRIPLE:,} triple"
                    
                    # Para informes, mostrar conteo total
                    st.metric(f"Exámenes TAC ({tac_doble_text}{tac_triple_text})", 
                             f"{tac_fisicos} físicos / {tac_conteo_total} para informes", 
                             help=help_text)
                    
                    st.metric("Honorarios por TAC", f"${tac_valor:,}")
                
                # Mostrar el total con mayor prominencia
                st.markdown(f"### Total: ${resultado_eco['total']:,}")
                
                # Conteos de exámenes (mantener para compatibilidad con el resto del código)
                rx_count = resultado_eco['rx_count']
                tac_count = resultado_eco['tac_count']
                tac_doble_count = resultado_eco['tac_doble_count']
                
                # Determinar el período basado en los días de turno
                periodo = ""
                if st.session_state.dias_turno:
                    meses_esp = {
                        'ene': 'enero', 'feb': 'febrero', 'mar': 'marzo', 'abr': 'abril',
                        'may': 'mayo', 'jun': 'junio', 'jul': 'julio', 'ago': 'agosto',
                        'sep': 'septiembre', 'oct': 'octubre', 'nov': 'noviembre', 'dic': 'diciembre'
                    }
                    
                    # Extraer meses de las fechas
                    meses = []
                    for fecha, _ in st.session_state.dias_turno:
                        try:
                            # Extraer abreviatura del mes
                            mes_abrev = fecha.split('-')[1]
                            if mes_abrev in meses_esp:
                                meses.append(meses_esp[mes_abrev])
                        except:
                            continue
                    
                    # Usar el mes más frecuente
                    if meses:
                        periodo = Counter(meses).most_common(1)[0][0]
                
                # Generar correo con el nombre del doctor actualizado
                correo = generar_contenido_correo(
                    st.session_state.get('nombre_doctor', nombre_doctor),  # Usar el nombre almacenado
                    [d for d, _ in st.session_state.dias_turno],
                    total_horas,
                    rx_count,
                    tac_count + tac_doble_count,  # Total de TAC (simples + dobles)
                    periodo
                )
                
                # Contenido del correo
                with st.expander("Vista Previa del Correo", expanded=True):
                    # Asunto
                    st.markdown(f"**Asunto:** {correo['asunto']}")
                    
                    # Cuerpo
                    st.text_area("Cuerpo del correo", correo['cuerpo'], height=200)
                    
                    # Botones para acciones
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Copiar al portapapeles"):
                            # En Streamlit no podemos acceder directamente al portapapeles
                            # pero podemos mostrar un cuadro de texto seleccionable
                            st.code(correo['cuerpo'], language=None)
                            st.info("👆 Selecciona el texto de arriba y cópialo con Ctrl+C o Cmd+C")
                    
                    with col2:
                        # Generar archivo de texto para descargar
                        txt_bytes = correo['cuerpo'].encode()
                        b64 = base64.b64encode(txt_bytes).decode()
                        href = f'<a href="data:file/txt;base64,{b64}" download="Contenido_Correo.txt">Descargar como TXT</a>'
                        st.markdown(href, unsafe_allow_html=True)
                
                # Generar archivos Excel
                with st.expander("Generar Archivos Excel", expanded=True):
                    # Variables para almacenar rutas locales de archivos generados
                    if 'archivos_generados' not in st.session_state:
                        st.session_state.archivos_generados = {}
                    
                    if st.button("Generar Tablas Excel"):
                        # Crear un directorio temporal para los archivos
                        import tempfile
                        import os
                        from datetime import datetime
                        
                        temp_dir = tempfile.mkdtemp()
                        st.session_state.temp_dir = temp_dir
                        st.session_state.archivos_generados = {}
                        
                        # Generar nombre de carpeta
                        fecha_actual = dt.datetime.now()
                        folder_name = f"TURNOS_{periodo.upper()}_{fecha_actual.year}"
                        
                        # Generar tablas Excel
                        try:
                            # 1. Tabla RX - Solo con la información esencial para el doctor
                            df_rx = st.session_state.calculadora.data_filtrada[
                                st.session_state.calculadora.data_filtrada['Tipo'] == 'RX'
                            ]
                            # Columnas simplificadas para el doctor
                            columnas_doctor = [
                                'Número de cita', 
                                'Fecha del procedimiento programado', 
                                'Apellidos del paciente', 
                                'Nombre del paciente', 
                                'Nombre del procedimiento', 
                                'Sala de adquisición'
                            ]
                            columnas_disponibles = [col for col in columnas_doctor if col in df_rx.columns]
                            df_rx_download = df_rx[columnas_disponibles].copy()
                            
                            # Renombrar columnas para hacerlas más legibles
                            renombrar = {
                                'Número de cita': 'Nº Cita',
                                'Fecha del procedimiento programado': 'Fecha',
                                'Apellidos del paciente': 'Apellidos',
                                'Nombre del paciente': 'Nombre',
                                'Nombre del procedimiento': 'Procedimiento',
                                'Sala de adquisición': 'Sala'
                            }
                            df_rx_download = df_rx_download.rename(columns={k: renombrar[k] for k in columnas_disponibles if k in renombrar})
                            
                            ruta_rx = os.path.join(temp_dir, 'Tabla_RX.xlsx')
                            df_rx_download.to_excel(ruta_rx, index=False)
                            st.session_state.archivos_generados['rx'] = ruta_rx
                            
                            # 2. Tabla TAC - Solo con la información esencial para el doctor
                            df_tac = st.session_state.calculadora.data_filtrada[
                                st.session_state.calculadora.data_filtrada['Tipo'] == 'TAC'
                            ]
                            # Usar las mismas columnas simplificadas
                            columnas_disponibles = [col for col in columnas_doctor if col in df_tac.columns]
                            df_tac_download = df_tac[columnas_disponibles].copy()
                            
                            # Renombrar columnas para hacerlas más legibles
                            df_tac_download = df_tac_download.rename(columns={k: renombrar[k] for k in columnas_disponibles if k in renombrar})
                            
                            ruta_tac = os.path.join(temp_dir, 'Tabla_TAC.xlsx')
                            df_tac_download.to_excel(ruta_tac, index=False)
                            st.session_state.archivos_generados['tac'] = ruta_tac
                            
                            # Calcular honorarios
                            resultado_eco = st.session_state.calculadora.calcular_honorarios(total_horas)
                            
                            # 3. Archivo de detalles técnicos (para ti)
                            # Este archivo contiene toda la información técnica detallada
                            
                            # Verificar si hay TAC triple en los resultados
                            has_tac_triple = 'tac_triple_count' in resultado_eco and resultado_eco['tac_triple_count'] > 0
                            
                            # Para el informe, contar dobles como 2 y triples como 3
                            tac_conteo_total = resultado_eco['tac_count'] + (resultado_eco['tac_doble_count'] * 2) + (resultado_eco['tac_triple_count'] * 3 if has_tac_triple else 0)
                            
                            # Crear un Excel con múltiples hojas
                            ruta_detalles = os.path.join(temp_dir, 'Detalles_Tecnicos.xlsx')
                            writer = pd.ExcelWriter(ruta_detalles, engine='openpyxl')
                            
                            # 3.1. Hoja de resumen económico
                            df_resumen = pd.DataFrame({
                                'Concepto': [
                                    'Horas trabajadas',
                                    'Exámenes RX',
                                    'Exámenes TAC normales',
                                    'Exámenes TAC dobles',
                                    'Exámenes TAC triples',
                                    'Total TAC físicos',
                                    'Total TAC para informes',
                                    'Honorarios por horas',
                                    'Honorarios por RX',
                                    'Honorarios por TAC normales',
                                    'Honorarios por TAC dobles',
                                    'Honorarios por TAC triples',
                                    'TOTAL'
                                ],
                                'Cantidad': [
                                    resultado_eco['horas_trabajadas'],
                                    resultado_eco['rx_count'],
                                    resultado_eco['tac_count'],
                                    resultado_eco['tac_doble_count'],
                                    resultado_eco['tac_triple_count'] if has_tac_triple else 0,
                                    resultado_eco['tac_count'] + resultado_eco['tac_doble_count'] + (resultado_eco['tac_triple_count'] if has_tac_triple else 0),
                                    tac_conteo_total,
                                    '-',
                                    '-',
                                    '-',
                                    '-',
                                    '-',
                                    '-'
                                ],
                                'Monto': [
                                    resultado_eco['honorarios_hora'],
                                    resultado_eco['rx_total'],
                                    resultado_eco['tac_total'],
                                    resultado_eco['tac_doble_total'],
                                    resultado_eco['tac_triple_total'] if has_tac_triple else 0,
                                    '-',
                                    '-',
                                    resultado_eco['honorarios_hora'],
                                    resultado_eco['rx_total'],
                                    resultado_eco['tac_total'],
                                    resultado_eco['tac_doble_total'],
                                    resultado_eco['tac_triple_total'] if has_tac_triple else 0,
                                    resultado_eco['total']
                                ]
                            })
                            
                            df_resumen.to_excel(writer, sheet_name="Resumen_Económico", index=False)
                            
                            # 3.2. Hoja de TAC dobles
                            tac_dobles = st.session_state.calculadora.data_filtrada[
                                st.session_state.calculadora.data_filtrada['TAC doble'] == True
                            ]
                            
                            if not tac_dobles.empty:
                                # Todas las columnas disponibles para máximo detalle
                                tac_dobles.to_excel(writer, sheet_name="TAC_Dobles", index=False)
                            
                            # 3.3. Hoja de TAC triples
                            if 'TAC triple' in st.session_state.calculadora.data_filtrada.columns:
                                tac_triples = st.session_state.calculadora.data_filtrada[
                                    st.session_state.calculadora.data_filtrada['TAC triple'] == True
                                ]
                                
                                if not tac_triples.empty:
                                    tac_triples.to_excel(writer, sheet_name="TAC_Triples", index=False)
                            
                            # 3.4. Hoja de exámenes por sala
                            salas_pivot = pd.pivot_table(
                                st.session_state.calculadora.data_filtrada,
                                index='Sala de adquisición',
                                columns='Tipo',
                                values='Número de cita',
                                aggfunc='count',
                                fill_value=0
                            ).reset_index()
                            
                            salas_pivot.to_excel(writer, sheet_name="Exámenes_Por_Sala", index=False)
                            
                            # 3.5. Guardar y cerrar el Excel
                            writer.close()
                            st.session_state.archivos_generados['detalles'] = ruta_detalles
                            
                            # 4. Correo como archivo de texto
                            ruta_correo = os.path.join(temp_dir, 'Contenido_Correo.txt')
                            with open(ruta_correo, 'w', encoding='utf-8') as f:
                                f.write(correo['cuerpo'])
                            st.session_state.archivos_generados['correo'] = ruta_correo
                            
                            st.success(f"Archivos generados correctamente en directorio temporal")
                        except Exception as e:
                            st.error(f"Error al generar archivos: {str(e)}")
                    
                    # Mostrar enlaces de descarga si hay archivos generados
                    if 'archivos_generados' in st.session_state and st.session_state.archivos_generados:
                        st.markdown("### Archivos generados")
                        
                        # Mostrar los archivos como enlaces descargables
                        for nombre, ruta in st.session_state.archivos_generados.items():
                            archivo_nombre = os.path.basename(ruta)
                            if nombre == 'rx':
                                etiqueta = "Tabla de RX (para el doctor)"
                            elif nombre == 'tac':
                                etiqueta = "Tabla de TAC (para el doctor)"
                            elif nombre == 'detalles':
                                etiqueta = "Detalles Técnicos (para ti)"
                            elif nombre == 'correo':
                                etiqueta = "Contenido del Correo"
                            else:
                                etiqueta = archivo_nombre
                            
                            # Si es Excel, crear enlace de descarga
                            if ruta.endswith('.xlsx'):
                                with open(ruta, 'rb') as f:
                                    bytes_data = f.read()
                                    b64 = base64.b64encode(bytes_data).decode()
                                    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{archivo_nombre}">{etiqueta}</a>'
                                    st.markdown(href, unsafe_allow_html=True)
                
                # Envío de correo electrónico
                with st.expander("Enviar por Correo Electrónico", expanded=True):
                    if 'archivos_generados' not in st.session_state or not st.session_state.archivos_generados:
                        st.warning("Primero debe generar los archivos Excel para poder enviarlos por correo")
                    else:
                        st.subheader("Configuración del Correo")
                        
                        # Configuración del remitente
                        col1, col2 = st.columns(2)
                        with col1:
                            correo_remitente = st.text_input("Correo del remitente", 
                                                         value=st.session_state.get('correo_remitente', "ejemplo@gmail.com"),
                                                         help="Su dirección de correo para enviar el informe")
                            if correo_remitente != st.session_state.get('correo_remitente', ''):
                                st.session_state.correo_remitente = correo_remitente
                        
                        with col2:
                            correo_destinatario = st.text_input("Correo del destinatario", 
                                                            value=st.session_state.get('correo_destinatario', ""),
                                                            help="Dirección de correo del médico")
                            if correo_destinatario != st.session_state.get('correo_destinatario', ''):
                                st.session_state.correo_destinatario = correo_destinatario
                        
                        # Selección de archivos a adjuntar
                        st.write("Seleccione los archivos a adjuntar:")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            adjuntar_rx = st.checkbox("Tabla de RX", value=True, key="adj_rx")
                            adjuntar_tac = st.checkbox("Tabla de TAC", value=True, key="adj_tac")
                        
                        with col2:
                            adjuntar_resumen = st.checkbox("Detalles Técnicos (para ti)", value=True, key="adj_resumen")
                        
                        # Botón para enviar correo
                        if st.button("Enviar Correo"):
                            if not correo_destinatario or not '@' in correo_destinatario:
                                st.error("Debe ingresar una dirección de correo válida para el destinatario")
                            else:
                                # Crear lista de archivos adjuntos
                                archivos_adjuntos = []
                                if adjuntar_rx and 'rx' in st.session_state.archivos_generados:
                                    archivos_adjuntos.append(st.session_state.archivos_generados['rx'])
                                if adjuntar_tac and 'tac' in st.session_state.archivos_generados:
                                    archivos_adjuntos.append(st.session_state.archivos_generados['tac'])
                                if adjuntar_resumen and 'detalles' in st.session_state.archivos_generados:
                                    archivos_adjuntos.append(st.session_state.archivos_generados['detalles'])
                                
                                # Enviar correo
                                with st.spinner("Enviando correo..."):
                                    exito, mensaje = enviar_correo(
                                        correo_destinatario,
                                        correo['asunto'],
                                        correo['cuerpo'],
                                        archivos_adjuntos
                                    )
                                
                                if exito:
                                    st.success(mensaje)
                                    # Mostrar mensaje adicional para sistemas de prueba
                                    st.info("Nota: En esta versión de prueba, el correo se guarda en un archivo temporal pero no se envía realmente.")
                                else:
                                    st.error(mensaje)
            else:
                if not st.session_state.dias_turno:
                    st.warning("Debe seleccionar al menos un día de turno para generar reportes")
                else:
                    st.warning("Debe cargar y clasificar los exámenes primero")


if __name__ == "__main__":
    main()