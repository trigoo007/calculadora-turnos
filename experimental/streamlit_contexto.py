#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz Streamlit para la Integración del Sistema de Contexto con la Calculadora de Turnos
------------------------------------------------------------------------------------------
Este módulo proporciona una interfaz web para interactuar con el sistema de contexto y
la calculadora de turnos radiológicos.
"""

import os
import sys
import json
import pandas as pd
import streamlit as st
from datetime import datetime
from pathlib import Path

# Asegurar que podemos importar desde el directorio raíz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar la integración
from integracion_contexto_calculadora import IntegracionContextoCalculadora

# Configurar la página
st.set_page_config(
    page_title="Calculadora de Turnos con Contexto",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #424242;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #FFF8E1;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .error-box {
        background-color: #FFEBEE;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar estado de sesión
if 'integracion' not in st.session_state:
    # Mostrar mensaje de inicialización
    with st.spinner("Inicializando el sistema de contexto y la calculadora..."):
        try:
            st.session_state.integracion = IntegracionContextoCalculadora()
            st.session_state.mensajes = []
            st.session_state.archivos_procesados = []
        except Exception as e:
            st.error(f"Error al inicializar el sistema: {str(e)}")

# Función para procesar archivo CSV
def procesar_archivo_csv(archivo, nombre_doctor):
    if archivo is None:
        return False, "No se seleccionó ningún archivo"
    
    try:
        # Guardar el archivo temporalmente
        archivo_temp = Path(f"temp/upload_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
        archivo_temp.parent.mkdir(exist_ok=True)
        
        # Escribir el contenido del archivo
        with open(archivo_temp, "wb") as f:
            f.write(archivo.getbuffer())
        
        # Procesar el archivo
        directorio_salida = os.path.dirname(archivo_temp)
        resultado = st.session_state.integracion.procesar_y_almacenar_csv(
            str(archivo_temp),
            directorio_salida,
            nombre_doctor
        )
        
        if "error" in resultado:
            return False, resultado["error"]
        
        # Añadir a la lista de archivos procesados
        st.session_state.archivos_procesados.append({
            "nombre": archivo.name,
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "doctor": nombre_doctor,
            "resultado": resultado
        })
        
        return True, resultado
    
    except Exception as e:
        return False, f"Error al procesar archivo: {str(e)}"

# Función para realizar consulta
def realizar_consulta(consulta):
    if not consulta:
        return
    
    # Añadir consulta a la lista de mensajes
    st.session_state.mensajes.append({
        "autor": "usuario",
        "texto": consulta,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")
    })
    
    try:
        # Realizar consulta con contexto
        respuesta = st.session_state.integracion.consulta_con_contexto(consulta)
        
        # Añadir respuesta a la lista de mensajes
        st.session_state.mensajes.append({
            "autor": "asistente",
            "texto": respuesta,
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")
        })
    
    except Exception as e:
        # Añadir mensaje de error
        st.session_state.mensajes.append({
            "autor": "sistema",
            "texto": f"Error al procesar consulta: {str(e)}",
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")
        })

# Función para realizar consulta SQL
def realizar_consulta_sql(consulta):
    if not consulta:
        return None, "No se especificó ninguna consulta"
    
    try:
        # Realizar consulta SQL con contexto
        exito, resultado = st.session_state.integracion.consulta_sql_con_contexto(consulta)
        
        if not exito:
            return None, f"Error: {resultado}"
        
        return resultado, None
    
    except Exception as e:
        return None, f"Error al procesar consulta SQL: {str(e)}"

# Interfaz principal
st.markdown('<div class="main-header">Calculadora de Turnos en Radiología</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Sistema Integrado con Recuperación de Contexto</div>', unsafe_allow_html=True)

# Pestañas principales
tab_procesar, tab_consultar, tab_sql, tab_historial = st.tabs([
    "Procesar CSV", "Consultar Asistente", "Consultas SQL", "Historial"
])

# ------ Pestaña de Procesamiento ------
with tab_procesar:
    st.markdown('<div class="sub-header">Procesar Archivo CSV</div>', unsafe_allow_html=True)
    
    # Formulario de procesamiento
    with st.form("formulario_procesar"):
        archivo_csv = st.file_uploader("Seleccione archivo CSV a procesar", type=["csv"])
        nombre_doctor = st.text_input("Nombre del Doctor", value="Cikutovic")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submit_button = st.form_submit_button("Procesar Archivo")
    
    # Procesar el archivo si se ha enviado el formulario
    if submit_button:
        with st.spinner("Procesando archivo..."):
            exito, resultado = procesar_archivo_csv(archivo_csv, nombre_doctor)
            
            if exito:
                st.markdown('<div class="success-box">¡Archivo procesado correctamente!</div>', unsafe_allow_html=True)
                
                # Mostrar resumen económico
                eco = resultado["resultado_economico"]
                
                st.markdown("#### Resumen Económico")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Horas Trabajadas", f"{eco['horas_trabajadas']:.1f}")
                    st.metric("RX", f"{eco['rx_count']} (${eco['rx_total']:,.2f})")
                
                with col2:
                    st.metric("TAC", f"{eco['tac_count']} (${eco['tac_total']:,.2f})")
                    st.metric("TAC doble", f"{eco['tac_doble_count']} (${eco['tac_doble_total']:,.2f})")
                
                with col3:
                    st.metric("TAC triple", f"{eco['tac_triple_count']} (${eco['tac_triple_total']:,.2f})")
                    st.metric("TOTAL", f"${eco['total']:,.2f}", delta=f"${eco['total']-eco['honorarios_hora']:,.2f}")
                
                # Mostrar archivos generados
                st.markdown("#### Archivos Generados")
                for nombre, ruta in resultado["rutas_excel"].items():
                    archivo_base = os.path.basename(ruta)
                    st.markdown(f"- **{nombre}**: {archivo_base}")
            else:
                st.markdown(f'<div class="error-box">Error: {resultado}</div>', unsafe_allow_html=True)

# ------ Pestaña de Consultas ------
with tab_consultar:
    st.markdown('<div class="sub-header">Consultas al Asistente con Contexto</div>', unsafe_allow_html=True)
    
    # Mostrar mensajes anteriores
    for mensaje in st.session_state.mensajes:
        if mensaje["autor"] == "usuario":
            st.markdown(f"**👤 Usuario** ({mensaje['timestamp']}):")
            st.markdown(f"> {mensaje['texto']}")
        elif mensaje["autor"] == "asistente":
            st.markdown(f"**🤖 Asistente** ({mensaje['timestamp']}):")
            st.markdown(mensaje['texto'])
        else:
            st.markdown(f"**⚠️ Sistema** ({mensaje['timestamp']}):")
            st.error(mensaje['texto'])
    
    # Formulario de consulta
    with st.form("formulario_consulta"):
        consulta = st.text_area("Escriba su consulta", height=100)
        enviar_consulta = st.form_submit_button("Enviar Consulta")
    
    if enviar_consulta:
        with st.spinner("Procesando consulta..."):
            realizar_consulta(consulta)
            st.experimental_rerun()

# ------ Pestaña de SQL ------
with tab_sql:
    st.markdown('<div class="sub-header">Consultas SQL en Lenguaje Natural</div>', unsafe_allow_html=True)
    
    # Formulario de consulta SQL
    with st.form("formulario_sql"):
        consulta_sql = st.text_area("Escriba su consulta en lenguaje natural", 
                                    placeholder="Ejemplo: Muestra los procedimientos TAC doble realizados en la última semana",
                                    height=100)
        enviar_sql = st.form_submit_button("Ejecutar Consulta")
    
    if enviar_sql:
        with st.spinner("Procesando consulta SQL..."):
            df_resultado, error = realizar_consulta_sql(consulta_sql)
            
            if error:
                st.markdown(f'<div class="error-box">Error: {error}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="success-box">Consulta ejecutada correctamente</div>', unsafe_allow_html=True)
                st.dataframe(df_resultado)
                
                # Opción para descargar resultados
                if not df_resultado.empty:
                    csv = df_resultado.to_csv(index=False)
                    st.download_button(
                        label="Descargar resultados como CSV",
                        data=csv,
                        file_name=f"consulta_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv",
                        mime="text/csv"
                    )

# ------ Pestaña de Historial ------
with tab_historial:
    st.markdown('<div class="sub-header">Historial de Archivos Procesados</div>', unsafe_allow_html=True)
    
    if not st.session_state.archivos_procesados:
        st.info("Aún no se han procesado archivos en esta sesión.")
    else:
        for i, archivo in enumerate(reversed(st.session_state.archivos_procesados)):
            with st.expander(f"{archivo['nombre']} - {archivo['fecha']} - Dr. {archivo['doctor']}"):
                # Mostrar información del procesamiento
                resultado = archivo["resultado"]
                eco = resultado["resultado_economico"]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Resumen Económico")
                    st.write(f"**Horas trabajadas:** {eco['horas_trabajadas']:.1f}")
                    st.write(f"**RX:** {eco['rx_count']} (${eco['rx_total']:,.2f})")
                    st.write(f"**TAC:** {eco['tac_count']} (${eco['tac_total']:,.2f})")
                    st.write(f"**TAC doble:** {eco['tac_doble_count']} (${eco['tac_doble_total']:,.2f})")
                    st.write(f"**TAC triple:** {eco['tac_triple_count']} (${eco['tac_triple_total']:,.2f})")
                    st.write(f"**TOTAL:** ${eco['total']:,.2f}")
                
                with col2:
                    st.markdown("#### Archivos Generados")
                    for nombre, ruta in resultado["rutas_excel"].items():
                        archivo_base = os.path.basename(ruta)
                        st.write(f"**{nombre}:** {archivo_base}")

# Información del sistema en el sidebar
with st.sidebar:
    st.markdown("### Sistema de Contexto")
    
    # Verificar estado del sistema
    sistema_ok = st.session_state.integracion is not None
    
    if sistema_ok:
        st.markdown('<div class="success-box">Sistema inicializado correctamente</div>', unsafe_allow_html=True)
        
        # Mostrar información de componentes
        st.write("**Componentes activos:**")
        
        # Verificar calculadora
        if st.session_state.integracion.calculadora:
            st.write("✅ Calculadora de Turnos")
        else:
            st.write("❌ Calculadora de Turnos")
        
        # Verificar asistente
        if st.session_state.integracion.asistente:
            st.write("✅ Asistente phi-2")
        else:
            st.write("❌ Asistente phi-2")
        
        # Verificar sistema de contexto
        if st.session_state.integracion.recuperacion_contexto:
            st.write("✅ Sistema de Contexto")
        else:
            st.write("❌ Sistema de Contexto")
    else:
        st.markdown('<div class="error-box">Error al inicializar sistema</div>', unsafe_allow_html=True)
    
    # Información de la versión
    st.markdown("---")
    st.markdown("### Información del Sistema")
    st.write("**Versión:** 0.9.0")
    st.write(f"**Fecha:** {datetime.now().strftime('%d/%m/%Y')}")
    st.write("**Modo:** Docker + Contexto")

# Iniciar la aplicación
if __name__ == "__main__":
    st.write("Aplicación inicializada correctamente.")