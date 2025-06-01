#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculadora de Turnos en Radiología - Versión Streamlit
-------------------------------------------------------
Aplicación web para procesar datos de procedimientos médicos en radiología,
clasificar exámenes, calcular horas trabajadas y generar reportes.
"""

# Importaciones globales
import os
import sys
import pandas as pd
import numpy as np
import tempfile
import json
from datetime import datetime, timedelta
import streamlit as st
from dateutil import parser
# Importaciones adicionales para procesamiento de fechas mejorado
import re
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64
import re
import importlib.util

# Agregar el directorio raíz al path para importar módulos
RAIZ_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if RAIZ_DIR not in sys.path:
    sys.path.insert(0, RAIZ_DIR)

# Importar módulo de la calculadora
from calculadora_turnos import CalculadoraTurnos

# Intentar importar el sistema de aprendizaje
try:
    from aprendizaje_datos_sqlite import SistemaAprendizajeSQLite
    SISTEMA_APRENDIZAJE_DISPONIBLE = True
except ImportError:
    SISTEMA_APRENDIZAJE_DISPONIBLE = False

# Función para generar enlaces de descarga de Excel
def generate_excel_download_link(df, filename):
    """Genera un enlace para descargar un DataFrame como Excel."""
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    processed_data = output.getvalue()
    b64 = base64.b64encode(processed_data).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{filename}</a>'

# Función para mostrar DataFrames interactivos
def mostrar_df_interactivo(df, key_prefix):
    """Muestra un DataFrame con opciones interactivas."""
    # Mostrar como tabla con ordenamiento y filtros
    st.dataframe(df, use_container_width=True)

# Función principal de la aplicación
def main():
    """Función principal para configurar la interfaz Streamlit."""
    # Configuración de la página
    st.set_page_config(
        page_title="Calculadora de Turnos en Radiología",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # CSS personalizado - diseño elegante y legible
    st.markdown("""
    <style>
    /* Estilo general y fuentes */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }
    
    /* Encabezado principal */
    .main-header {
        margin: 3rem 0 2rem 0;
        text-align: center;
    }
    .main-header h1 {
        color: #1E3A8A;
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .main-header p {
        font-size: 1.3rem;
        color: #475569;
    }
    
    /* Control del espacio para evitar solapamientos */
    .block-container {
        padding-top: 3rem !important;
        margin-top: 1rem;
    }
    
    /* Estilos para encabezados */
    h2 {
        color: #1E3A8A;
        border-bottom: 2px solid #3B82F6;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        font-weight: 600;
    }
    h3 {
        color: #1E40AF;
        margin-top: 1.5rem;
        font-weight: 500;
    }
    
    /* Estilo para pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 54px;
        white-space: pre-wrap;
        background-color: #EFF6FF;
        border-radius: 8px;
        border: 1px solid #DBEAFE;
        padding: 12px 18px;
        font-size: 16px;
        font-weight: 500;
        color: #2563EB;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563EB;
        color: white;
        border: 1px solid #1E40AF;
    }
    
    /* Estilo para botones */
    .stButton>button {
        font-weight: 600;
        border-radius: 8px;
        padding: 4px 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Estilo para dataframes */
    .dataframe {
        border-collapse: separate !important;
        border-spacing: 0 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
    }
    .dataframe th {
        background-color: #EFF6FF !important;
        color: #1E40AF !important;
        font-weight: 600 !important;
        border-top: none !important;
    }
    .dataframe td {
        border-top: 1px solid #E5E7EB !important;
    }
    
    /* Estilo para métricas */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #1E3A8A !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Título y descripción en un contenedor personalizado - más contrastado
    st.markdown('<div class="main-header"><h1>📊 Calculadora de Turnos en Radiología</h1><p>Procesamiento y análisis inteligente de procedimientos médicos</p></div>', unsafe_allow_html=True)

    # Inicializar la sesión
    if 'calculadora' not in st.session_state:
        st.session_state.calculadora = CalculadoraTurnos()
        st.session_state.archivo_cargado = False
        st.session_state.datos_filtrados = False
        st.session_state.examenes_clasificados = False
        st.session_state.dias_turno = []  # Lista para almacenar fechas de turno (fecha, es_feriado)

    # Inicializar sistema de aprendizaje si está disponible
    if SISTEMA_APRENDIZAJE_DISPONIBLE and 'sistema_aprendizaje' not in st.session_state:
        try:
            st.session_state.sistema_aprendizaje = SistemaAprendizajeSQLite()
        except Exception as e:
            st.error(f"Error al inicializar sistema de aprendizaje: {e}")

    # Sidebar con opciones principales
    with st.sidebar:
        st.header("Navegación")
        
        if not st.session_state.archivo_cargado:
            st.info("👉 Cargue un archivo CSV para comenzar")
        else:
            st.success("✅ Archivo cargado")
            
            # Botones de navegación en el sidebar
            if st.button("Volver al inicio"):
                st.session_state.pop('archivo_cargado')
                st.rerun()
        
        # Mostrar información sobre el sistema de aprendizaje
        st.header("Información del Sistema")
        
        if SISTEMA_APRENDIZAJE_DISPONIBLE:
            st.success("✅ Sistema de aprendizaje SQLite disponible")
        else:
            st.warning("⚠️ Sistema de aprendizaje no disponible")
        
        # Asistente básico siempre disponible
        st.success("✅ Asistente básico disponible")
            
        st.markdown("---")
        st.markdown("### Acerca de")
        st.markdown("""
        **Calculadora de Turnos en Radiología**
        
        Versión 0.8.1
        
        Desarrollada para automatizar el proceso de cálculo de turnos,
        informes radiológicos y honorarios profesionales.
        
        Con diseño optimizado, asistente simplificado integrado
        y análisis inteligente de exámenes médicos.
        """)

    # Sección para cargar el archivo CSV
    st.subheader("Cargar Archivo")
    uploaded_file = st.file_uploader("Seleccione el archivo CSV", type=['csv'])
    
    if uploaded_file is not None and (not st.session_state.archivo_cargado or 
                                      uploaded_file.name != st.session_state.get('archivo_nombre', '')):
        with st.spinner("Cargando archivo..."):
            # Guardar temporalmente el archivo
            temp_file = os.path.join(tempfile.mkdtemp(), uploaded_file.name)
            with open(temp_file, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            # Cargar el archivo con la calculadora
            exito, mensaje = st.session_state.calculadora.cargar_archivo(temp_file)
            if exito:
                st.success(mensaje)
                st.session_state.archivo_cargado = True
                st.session_state.archivo_nombre = uploaded_file.name
                st.session_state.archivo_ruta = temp_file
                st.session_state.uploaded_csv = uploaded_file
                
                # Continuar con el procesamiento
                exito, mensaje = st.session_state.calculadora.filtrar_datos()
                if exito:
                    st.info(mensaje)
                    st.session_state.datos_filtrados = True
                    
                    # Clasificar exámenes
                    exito, mensaje = st.session_state.calculadora.clasificar_examenes()
                    if exito:
                        st.success(mensaje)
                        st.session_state.examenes_clasificados = True
                        
                        # Aprender de los datos clasificados si el sistema está disponible
                        # Desactivado temporalmente para evitar el error "database is locked"
                        if False and SISTEMA_APRENDIZAJE_DISPONIBLE and hasattr(st.session_state, 'sistema_aprendizaje'):
                            with st.spinner("Analizando y aprendiendo patrones de datos..."):
                                try:
                                    exito_aprend, msg_aprend = st.session_state.sistema_aprendizaje.analizar_dataframe(
                                        st.session_state.calculadora.data_filtrada
                                    )
                                    if exito_aprend and 'TAC doble' in st.session_state.calculadora.data_filtrada.columns:
                                        st.session_state.sistema_aprendizaje.aprender_patrones_tac_doble(
                                            st.session_state.calculadora.data_filtrada
                                        )
                                    st.success("Sistema de aprendizaje actualizado con nuevos patrones")
                                except Exception as e:
                                    st.warning(f"No se pudo actualizar el sistema de aprendizaje: {e}")

    # Contenido principal cuando un archivo está cargado
    if st.session_state.archivo_cargado:
        # Crear pestañas para organizar la interfaz con nombres mejorados
        tab_names = ["📊 Visualización", "🔬 Análisis de Exámenes", "📝 Reportes"]
        
        # Agregar pestaña para asistente simplificado (sin depender de phi-2)
        tab_names.append("🤖 Asistente Básico")
        
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
                
                # Calcular métricas avanzadas
                total_examenes = len(df)
                total_rx = len(df[df['Tipo'] == 'RX'])
                total_tac_base = len(df[df['Tipo'] == 'TAC'])
                
                # Contar TAC dobles y triples
                tac_dobles = sum(df['TAC doble']) if 'TAC doble' in df.columns else 0
                tac_triples = sum(df['TAC triple']) if 'TAC triple' in df.columns else 0
                
                # Calcular TAC total corregido (cada doble cuenta como 2, cada triple como 3)
                tac_total_corregido = total_tac_base + tac_dobles + (tac_triples * 2)
                
                # Mostrar métricas de resultados en dos filas
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📊 Total de exámenes", total_examenes)
                with col2:
                    st.metric("💉 Total RX", total_rx)
                
                # Segunda fila para métricas de TAC
                st.markdown("### 📋 Detalles de TAC")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🖥️ TAC base", total_tac_base)
                with col2:
                    st.metric("🔄 TAC total corregido", tac_total_corregido, 
                             delta=tac_dobles + (tac_triples * 2) if (tac_dobles + tac_triples) > 0 else None,
                             delta_color="normal")
                with col3:
                    if tac_dobles > 0 or tac_triples > 0:
                        st.metric("⚠️ TAC especiales", 
                                 f"{tac_dobles} dobles, {tac_triples} triples")
                    else:
                        st.metric("⚠️ TAC especiales", "Ninguno")
                
                # Viñeta para mostrar detalles de TAC dobles/triples
                if tac_dobles > 0 or tac_triples > 0:
                    with st.expander("Ver detalles de TAC dobles y triples"):
                        # Preparar datos para mostrar
                        if tac_dobles > 0:
                            st.subheader("📑 TAC dobles")
                            tac_dobles_df = df[df['TAC doble'] == True].copy() if 'TAC doble' in df.columns else pd.DataFrame()
                            
                            if not tac_dobles_df.empty:
                                # Seleccionar columnas relevantes
                                cols_mostrar = ['Fecha del procedimiento programado', 'Nombre del procedimiento', 'Sala de adquisición']
                                cols_disponibles = [c for c in cols_mostrar if c in tac_dobles_df.columns]
                                
                                # Renombrar columnas para mejor visualización
                                nombres_cols = {
                                    'Fecha del procedimiento programado': 'Fecha',
                                    'Nombre del procedimiento': 'Procedimiento',
                                    'Sala de adquisición': 'Sala'
                                }
                                
                                df_mostrar = tac_dobles_df[cols_disponibles].copy()
                                df_mostrar.rename(columns={k: v for k, v in nombres_cols.items() if k in df_mostrar.columns}, inplace=True)
                                
                                # Mostrar tabla interactiva
                                st.dataframe(df_mostrar, use_container_width=True)
                        
                        if tac_triples > 0:
                            st.subheader("📑 TAC triples")
                            tac_triples_df = df[df['TAC triple'] == True].copy() if 'TAC triple' in df.columns else pd.DataFrame()
                            
                            if not tac_triples_df.empty:
                                # Seleccionar columnas relevantes
                                cols_mostrar = ['Fecha del procedimiento programado', 'Nombre del procedimiento', 'Sala de adquisición']
                                cols_disponibles = [c for c in cols_mostrar if c in tac_triples_df.columns]
                                
                                # Renombrar columnas para mejor visualización
                                df_mostrar = tac_triples_df[cols_disponibles].copy()
                                df_mostrar.rename(columns={k: v for k, v in nombres_cols.items() if k in df_mostrar.columns}, inplace=True)
                                
                                # Mostrar tabla interactiva
                                st.dataframe(df_mostrar, use_container_width=True)
                
                # Mostrar tabla de resultados filtrados
                if not df_filtrado.empty:
                    st.dataframe(df_filtrado, use_container_width=True)
                    st.info(f"Mostrando {len(df_filtrado)} de {len(df)} exámenes")
                else:
                    st.warning("No hay exámenes que coincidan con los criterios de búsqueda")
                
                # Sección para fechas de turno
                st.subheader("Selección de días de turno")
                
                # Mostrar fechas de turno seleccionadas
                if st.session_state.dias_turno:
                    st.write("Días de turno seleccionados:")
                    
                    # Mostrar tabla de fechas
                    dias_data = []
                    for fecha, es_feriado in st.session_state.dias_turno:
                        # Convertir fecha a objeto datetime para obtener día de semana
                        try:
                            # Convertir formato español a inglés si es necesario
                            fecha_procesada = fecha
                            for mes_esp, mes_eng in [('ene', 'jan'), ('abr', 'apr'), ('ago', 'aug'), ('dic', 'dec')]:
                                if mes_esp in fecha_procesada.lower():
                                    fecha_procesada = fecha_procesada.lower().replace(mes_esp, mes_eng)
                            
                            fecha_dt = parser.parse(fecha_procesada)
                            dia_semana = fecha_dt.strftime('%A')
                            
                            # Traducir día de semana si está en inglés
                            dias_es = {
                                'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                                'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
                            }
                            if dia_semana in dias_es:
                                dia_semana = dias_es[dia_semana]
                        
                        except:
                            dia_semana = "Desconocido"
                        
                        # Calcular horas basadas en día de semana o feriado
                        if es_feriado:
                            horas = 24 if dia_semana in ['Viernes', 'Friday'] else 23
                            tipo = "Feriado"
                        else:
                            if dia_semana in ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']:
                                horas = 14  # L-J: 18:00 a 08:00 (14 horas)
                            elif dia_semana in ['Viernes', 'Friday']:
                                horas = 15  # V: 18:00 a 09:00 (15 horas)
                            elif dia_semana in ['Sábado', 'Saturday']:
                                horas = 24  # S: 09:00 a 09:00 (24 horas)
                            else:  # Domingo
                                horas = 23  # D: 09:00 a 08:00 (23 horas)
                            tipo = "Normal"
                        
                        dias_data.append({
                            "Fecha": fecha,
                            "Día": dia_semana,
                            "Tipo": tipo,
                            "Horas": horas,
                            "Eliminar": False
                        })
                    
                    # Crear DataFrame y mostrar como tabla editable
                    df_dias = pd.DataFrame(dias_data)
                    
                    # Mostrar dataframe
                    edited_df = st.data_editor(
                        df_dias,
                        column_config={
                            "Eliminar": st.column_config.CheckboxColumn(
                                "Eliminar",
                                help="Marque para eliminar este día"
                            )
                        },
                        hide_index=True
                    )
                    
                    # Calcular total de horas
                    total_horas = sum(df_dias["Horas"])
                    st.info(f"Total de horas: {total_horas}")
                    
                    # Botón para eliminar días seleccionados
                    if st.button("Eliminar días marcados"):
                        # Identificar fechas a eliminar
                        fechas_eliminar = []
                        for i, row in edited_df.iterrows():
                            if row["Eliminar"]:
                                fechas_eliminar.append(row["Fecha"])
                        
                        # Eliminar de la lista de días de turno
                        if fechas_eliminar:
                            st.session_state.dias_turno = [
                                (fecha, feriado) for fecha, feriado in st.session_state.dias_turno
                                if fecha not in fechas_eliminar
                            ]
                            st.success(f"Se eliminaron {len(fechas_eliminar)} días de turno")
                            st.rerun()
                
                # Sección de selección de fechas mejorada
                st.write("## 📅 Selección de Fechas de Turno")
                
                # Crear tabs para diferentes métodos de selección
                fecha_tabs = st.tabs(["🧙‍♂️ Asistente de Fechas", "📋 Selector Calendario"])
                
                # Tab 1: Asistente de fechas (estimador automático)
                with fecha_tabs[0]:
                    st.markdown("### 🔍 Sugerencia automática de días de turno")
                    st.markdown("El sistema detectará los días con mayor actividad y los sugerirá como días de turno.")
                    
                    # Botón para estimación automática usando el método unificado
                    if st.button("✨ ESTIMAR FECHAS AUTOMÁTICAMENTE ✨", type="primary", use_container_width=True):
                        try:
                            with st.spinner("🔍 Analizando patrones de duplas en los datos..."):
                                # Verificar que hay datos
                                if len(df) == 0:
                                    st.error("No hay datos cargados para analizar.")
                                    return
                                
                                # Usar el método estimar_dias_turno del archivo principal
                                st.info("🤖 Usando algoritmo avanzado de detección de duplas...")
                                resultado_estimacion = st.session_state.calculadora.estimar_dias_turno(df)
                                
                                if resultado_estimacion:
                                    st.success(f"✅ Se detectaron {len(resultado_estimacion)} posibles días de turno")
                                    
                                    # Mostrar información sobre límites aplicados
                                    st.info(f"🎯 **Algoritmo de duplas aplicado**: Se detectaron días consecutivos con alta concentración de exámenes. Límites: mínimo 2, máximo 6 turnos.")
                                    
                                    # Preparar datos para mostrar
                                    fechas_sugeridas = []
                                    for fecha_esp, total_examenes in resultado_estimacion:
                                        fechas_sugeridas.append({
                                            'Fecha': fecha_esp,
                                            'Exámenes': total_examenes,
                                            'Seleccionar': True,
                                            'Es Feriado': False
                                        })
                                    
                                    # Convertir a DataFrame para mostrar
                                    sugerencias_df = pd.DataFrame(fechas_sugeridas)
                                    
                                    # Mostrar tabla de sugerencias
                                    st.markdown("### 📋 Días de turno sugeridos (basados en duplas)")
                                    edited_sugerencias = st.data_editor(
                                        sugerencias_df,
                                        column_config={
                                            "Seleccionar": st.column_config.CheckboxColumn(
                                                "Añadir",
                                                help="Marque para añadir esta fecha"
                                            ),
                                            "Es Feriado": st.column_config.CheckboxColumn(
                                                "Feriado",
                                                help="Marque si el día fue feriado"
                                            ),
                                            "Exámenes": st.column_config.NumberColumn(
                                                "Cantidad",
                                                help="Total de exámenes en esta dupla o día individual"
                                            ),
                                            "Fecha": st.column_config.TextColumn(
                                                "Fecha",
                                                help="Fecha en formato dd-mmm-yyyy"
                                            )
                                        },
                                        hide_index=True,
                                        use_container_width=True
                                    )
                                    
                                    # Botón para agregar fechas seleccionadas
                                    col1, col2 = st.columns([1, 2])
                                    with col1:
                                        if st.button("Agregar seleccionadas", type="primary"):
                                            # Identificar fechas seleccionadas
                                            dias_agregar = []
                                            for _, row in edited_sugerencias.iterrows():
                                                if row["Seleccionar"]:
                                                    dias_agregar.append((row["Fecha"], row["Es Feriado"]))
                                            
                                            # Agregar a la lista de días de turno
                                            if dias_agregar:
                                                # Filtrar fechas que ya existen
                                                fechas_existentes = [fecha for fecha, _ in st.session_state.dias_turno]
                                                nuevas_fechas = [(fecha, es_feriado) for fecha, es_feriado in dias_agregar if fecha not in fechas_existentes]
                                                
                                                if nuevas_fechas:
                                                    st.session_state.dias_turno.extend(nuevas_fechas)
                                                    st.success(f"✅ Se agregaron {len(nuevas_fechas)} días de turno")
                                                    st.rerun()
                                                else:
                                                    st.warning("Todas las fechas ya están en la lista")
                                    
                                    # Texto de ayuda
                                    with col2:
                                        st.info("💡 **Duplas**: Días consecutivos con alta concentración de exámenes. Se selecciona el primer día de cada dupla.")
                                
                                else:
                                    st.warning("⚠️ No se detectaron duplas o días con suficiente actividad para sugerir como turnos.")
                                    st.info("Intente con el selector manual de fechas en la pestaña siguiente.")
                                
                        except Exception as e:
                            st.error(f"Error en la estimación de fechas: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
                
                # Tab 2: Selector de calendario
                with fecha_tabs[1]:
                    st.markdown("### 📆 Seleccionar fecha manualmente")
                    
                    # Usar un date input de Streamlit
                    col1, col2 = st.columns(2)
                    with col1:
                        # Usar date_input de streamlit
                        fecha_seleccionada = st.date_input(
                            "Seleccione una fecha:",
                            value=None,
                            format="DD/MM/YYYY"
                        )
                    
                    with col2:
                        # Checkbox para feriado
                        es_feriado_manual = st.checkbox("Es día feriado", key="feriado_checkbox_manual")
                    
                    # Botón para agregar la fecha
                    if st.button("Agregar esta fecha", use_container_width=True):
                        if fecha_seleccionada:
                            # Convertir a formato esperado (dd-mmm-yyyy)
                            meses_abbr = {
                                1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun',
                                7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
                            }
                            
                            fecha_formateada = f"{fecha_seleccionada.day:02d}-{meses_abbr[fecha_seleccionada.month]}-{fecha_seleccionada.year}"
                            
                            # Verificar si ya existe
                            if any(fecha == fecha_formateada for fecha, _ in st.session_state.dias_turno):
                                st.warning(f"⚠️ La fecha {fecha_formateada} ya está en la lista")
                            else:
                                # Agregar a la lista
                                st.session_state.dias_turno.append((fecha_formateada, es_feriado_manual))
                                st.success(f"✅ Fecha {fecha_formateada} agregada correctamente")
                                st.rerun()
                        else:
                            st.error("⛔ Por favor seleccione una fecha válida")
                
                # Análisis visual de los datos
                st.subheader("Análisis Visual")
                
                # Añadir gráfico de distribución por tipo
                if 'Tipo' in df.columns:
                    # Contar por tipo
                    tipo_counts = df['Tipo'].value_counts().reset_index()
                    tipo_counts.columns = ['Tipo', 'Cantidad']
                    
                    # Gráfico de barras
                    fig = px.bar(
                        tipo_counts, 
                        x='Tipo', 
                        y='Cantidad', 
                        color='Tipo',
                        title='Distribución de Exámenes por Tipo',
                        labels={'Tipo': 'Tipo de Examen', 'Cantidad': 'Número de Exámenes'},
                        color_discrete_map={'RX': '#2196F3', 'TAC': '#FF5722'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Distribución por sala
                if 'Sala de adquisición' in df.columns:
                    # Contar por sala
                    sala_counts = df['Sala de adquisición'].value_counts().reset_index()
                    sala_counts.columns = ['Sala', 'Cantidad']
                    
                    # Limitar a las 10 salas más frecuentes
                    if len(sala_counts) > 10:
                        sala_counts = sala_counts.head(10)
                    
                    # Gráfico de barras horizontal
                    fig = px.bar(
                        sala_counts, 
                        y='Sala', 
                        x='Cantidad', 
                        orientation='h',
                        title='Distribución de Exámenes por Sala (Top 10)',
                        labels={'Sala': 'Sala de Adquisición', 'Cantidad': 'Número de Exámenes'},
                        color='Cantidad',
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig, use_container_width=True)

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
                # Crear directorio de salida por defecto
                ruta_actual = os.path.dirname(os.path.abspath(__file__))
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
                
                directorio_defecto = os.path.join(ruta_actual, "csv", f"TURNOS {mes} {año}")
                
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
                    
                    # Ejecutar procesamiento
                    with st.spinner("Procesando datos y generando reportes..."):
                        # Si tenemos el CSV cargado en la sesión, lo usamos directamente
                        if 'uploaded_csv' in st.session_state:
                            # Guardar temporalmente el archivo
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
                                nombre_archivo = os.path.basename(ruta)
                                # Generar enlace de descarga
                                with open(ruta, 'rb') as f:
                                    bytes_data = f.read()
                                    b64 = base64.b64encode(bytes_data).decode()
                                    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{nombre_archivo}">{nombre_archivo}</a>'
                                    st.markdown(href, unsafe_allow_html=True)
                            
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
        # Rediseño de pestañas principales - eliminar configuración avanzada innecesaria y mejorar phi-2
        tab_idx = 3
        
        # Tab de Asistente simplificado (sin depender de phi-2)
        with tabs[tab_idx]:
            st.markdown("## 🤖 Asistente Básico")
            st.markdown("### 💬 Consultas simples sobre los datos cargados")
            
            # Inicializar historial
            if 'asistente_historial' not in st.session_state:
                st.session_state.asistente_historial = []
            
            # Ejemplos de preguntas
            with st.expander("🔍 Preguntas que puede hacer", expanded=True):
                st.markdown("""
                - **Recuentos básicos**: "¿Cuántos TAC dobles hay en total?"
                - **Estadísticas**: "¿Cuántos RX hay?"
                - **Información**: "¿Cuántos días de turno tengo?"
                """)
            
            # Entrada de usuario
            pregunta = st.text_input("Escriba su consulta:", 
                                  placeholder="Ej: ¿Cuántos TAC dobles hay en total?",
                                  key="asistente_input")
            
            # Inicializar variables de estado para el asistente
            if 'asistente_respuesta' not in st.session_state:
                st.session_state.asistente_respuesta = ""
                st.session_state.mostrar_respuesta = False
            
            # Contenedor para la respuesta (permanece visible entre recargas)
            respuesta_container = st.container()
            
            # Procesar la pregunta sin recargar la página
            if st.button("Enviar consulta", type="primary", use_container_width=True, key="btn_consulta"):
                # Asegurar que nos mantenemos en la pestaña de asistente después de la consulta
                st.session_state.active_tab = tab_idx
                
                if not pregunta:
                    with respuesta_container:
                        st.warning("⚠️ Por favor ingrese una consulta")
                else:
                    # Activar el flag para mostrar respuesta
                    st.session_state.mostrar_respuesta = True
                    
                    # Guardar la pregunta para mantenerla entre recargas
                    st.session_state.ultima_pregunta = pregunta
                    
                    with st.spinner("Analizando datos..."):
                        # Verificar si hay datos cargados
                        if (hasattr(st.session_state, 'calculadora') and 
                            hasattr(st.session_state.calculadora, 'data_filtrada') and 
                            st.session_state.calculadora.data_filtrada is not None):
                            
                            # Acceder a los datos
                            df = st.session_state.calculadora.data_filtrada
                            
                            # Calcular estadísticas básicas
                            total_examenes = len(df)
                            total_rx = len(df[df['Tipo'] == 'RX']) if 'Tipo' in df.columns else 0
                            total_tac = len(df[df['Tipo'] == 'TAC']) if 'Tipo' in df.columns else 0
                            tac_dobles = sum(df['TAC doble']) if 'TAC doble' in df.columns else 0
                            tac_triples = sum(df['TAC triple']) if 'TAC triple' in df.columns else 0
                            dias_turno = len(st.session_state.dias_turno) if hasattr(st.session_state, 'dias_turno') else 0
                            
                            # Generar respuesta simple
                            respuesta = "No entendí tu consulta. Intenta preguntar por TAC dobles, RX o días de turno."
                            pregunta_lower = pregunta.lower()
                            
                            # Respuestas predefinidas (más variantes para mejor detección)
                            if any(palabra in pregunta_lower for palabra in ["cuant", "total", "hay", "cuánt", "cantidad"]):
                                if "tac doble" in pregunta_lower:
                                    respuesta = f"Hay un total de {tac_dobles} TAC dobles en los datos."
                                elif "tac triple" in pregunta_lower:
                                    respuesta = f"Hay un total de {tac_triples} TAC triples en los datos."
                                elif "rx" in pregunta_lower:
                                    respuesta = f"Hay un total de {total_rx} exámenes RX en los datos."
                                elif "tac" in pregunta_lower:
                                    respuesta = f"Hay un total de {total_tac} exámenes TAC en los datos."
                                elif "examen" in pregunta_lower:
                                    respuesta = f"Hay un total de {total_examenes} exámenes en los datos."
                                elif any(palabra in pregunta_lower for palabra in ["turno", "día", "dias", "fecha"]):
                                    respuesta = f"Hay {dias_turno} días de turno seleccionados actualmente."
                            
                            # Guardar respuesta en la sesión
                            st.session_state.asistente_respuesta = respuesta
                            
                            # Guardar en historial
                            st.session_state.asistente_historial.append({
                                "pregunta": pregunta,
                                "respuesta": respuesta
                            })
                            
                            # Mostrar la respuesta en el contenedor
                            with respuesta_container:
                                st.success("✅ Consulta procesada")
                                st.info(respuesta)
                            
                        else:
                            # Mostrar error en el contenedor
                            with respuesta_container:
                                st.error("No hay datos cargados para analizar")
                                st.info("Primero debe cargar un archivo CSV con datos de exámenes")
            
            # Mostrar la respuesta anterior si existe (para mantenerla entre recargas)
            if st.session_state.get('mostrar_respuesta', False) and st.session_state.get('asistente_respuesta', ''):
                with respuesta_container:
                    st.success("✅ Consulta procesada")
                    st.info(st.session_state.asistente_respuesta)
                    
            # Mostrar historial de consultas si existe
            if st.session_state.asistente_historial:
                with st.expander("📜 Historial de consultas", expanded=False):
                    for i, item in enumerate(reversed(st.session_state.asistente_historial[-5:])):
                        st.markdown(f"**Pregunta:** {item['pregunta']}")
                        st.markdown(f"**Respuesta:** {item['respuesta']}")
                        st.markdown("---")
            
            # Información sobre el asistente
            with st.expander("ℹ️ Acerca del Asistente", expanded=False):
                st.markdown("""
                ### Asistente Básico de Radiología
                
                Este asistente simple permite consultas rápidas sobre los datos cargados:
                
                - **Recuentos rápidos**: Exámenes por tipo, TAC dobles/triples
                - **Información general**: Días de turno seleccionados
                - **Estadísticas básicas**: Totales de diferentes tipos de examen
                
                Usa palabras como "cuántos", "hay" o "total" seguidas de lo que buscas.
                """)

# Ejecutar la aplicación
if __name__ == "__main__":
    main()
