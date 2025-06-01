#!/usr/bin/env python3
"""
Versión simplificada de la aplicación Calculadora de Turnos
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.data_processing import DataProcessor
from src.core.exam_classification import ExamClassifier
from src.core.turno_calculator import TurnoCalculator

# Configuración básica
st.set_page_config(
    page_title="Calculadora de Turnos",
    layout="wide"
)

# Título simple
st.title("📊 Calculadora de Turnos - Versión Simple")

# Inicializar procesadores
if 'data_processor' not in st.session_state:
    st.session_state.data_processor = DataProcessor()
    st.session_state.exam_classifier = ExamClassifier()
    st.session_state.turno_calculator = TurnoCalculator()

# Cargar archivo
uploaded_file = st.file_uploader("Seleccione un archivo CSV o Excel", type=['csv', 'xlsx', 'xls'])

if uploaded_file is not None:
    # Leer archivo
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"Archivo cargado: {len(df)} filas")
        
        # Mostrar columnas disponibles
        st.write("**Columnas en el archivo:**")
        st.write(list(df.columns))
        
        # Detectar columnas
        column_mapping = st.session_state.data_processor.detect_columns(df)
        
        st.write("**Columnas detectadas:**")
        for key, value in column_mapping.items():
            st.write(f"- {key}: {value}")
        
        # Procesar datos
        if st.button("Procesar Datos"):
            # Limpiar datos
            df_clean = st.session_state.data_processor.clean_data(df, column_mapping)
            
            # Clasificar exámenes si hay columna de procedimiento
            if 'procedimiento' in df_clean.columns:
                st.write("Clasificando exámenes...")
                
                # Clasificar cada procedimiento
                tipos = []
                tac_dobles = []
                tac_triples = []
                
                for proc in df_clean['procedimiento']:
                    if pd.notna(proc):
                        classification = st.session_state.exam_classifier.classify_exam(str(proc))
                        tipos.append(classification['type'])
                        tac_dobles.append(classification['is_tac_double'])
                        tac_triples.append(classification['is_tac_triple'])
                    else:
                        tipos.append('OTRO')
                        tac_dobles.append(False)
                        tac_triples.append(False)
                
                df_clean['tipo'] = tipos
                df_clean['is_tac_double'] = tac_dobles
                df_clean['is_tac_triple'] = tac_triples
                
                # Mostrar estadísticas
                st.write("**Resumen de clasificación:**")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total", len(df_clean))
                with col2:
                    st.metric("RX", len(df_clean[df_clean['tipo'] == 'RX']))
                with col3:
                    st.metric("TAC", len(df_clean[df_clean['tipo'] == 'TAC']))
                with col4:
                    st.metric("Otros", len(df_clean[df_clean['tipo'] == 'OTRO']))
                
                # TAC dobles y triples
                st.write("**Detalles TAC:**")
                col1, col2, col3 = st.columns(3)
                
                tac_simple = len(df_clean[(df_clean['tipo'] == 'TAC') & 
                                         (~df_clean['is_tac_double']) & 
                                         (~df_clean['is_tac_triple'])])
                tac_doble = len(df_clean[df_clean['is_tac_double'] == True])
                tac_triple = len(df_clean[df_clean['is_tac_triple'] == True])
                
                with col1:
                    st.metric("TAC Simple", tac_simple)
                with col2:
                    st.metric("TAC Doble", tac_doble)
                with col3:
                    st.metric("TAC Triple", tac_triple)
                
                # Mostrar algunos ejemplos
                st.write("**Ejemplos de procedimientos clasificados:**")
                ejemplos = df_clean[['procedimiento', 'tipo', 'is_tac_double', 'is_tac_triple']].head(20)
                st.dataframe(ejemplos)
                
                # Guardar para cálculos
                st.session_state.df_classified = df_clean
                st.success("✅ Datos procesados y clasificados correctamente")
            else:
                st.error("No se encontró la columna de procedimientos")
                
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.write("Detalles del error:")
        st.write(e) 