#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz simple para procesar archivos Excel de exámenes médicos
----------------------------------------------------------------
Versión simplificada que procesa directamente archivos Excel
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
import sys
import tempfile
from sistema_codigos_examenes import SistemaCodigos

# Configuración básica de la página
st.set_page_config(
    page_title="Sistema de Códigos de Exámenes", 
    page_icon="🏥",
    layout="wide"
)

# Cargar el sistema de códigos
@st.cache_resource
def cargar_sistema():
    return SistemaCodigos()

sistema = cargar_sistema()

# Función para procesar Excel directamente
def procesar_excel_directo(ruta_excel, hoja_nombre):
    """Procesa un archivo Excel directamente sin conversiones intermedias."""
    try:
        # Leer excel con todos los valores como strings para evitar errores de conversión
        df = pd.read_excel(ruta_excel, sheet_name=hoja_nombre, dtype=str)
        
        # Mapear columnas conocidas
        columnas_mapeo = {
            "Prestación": "Nombre del procedimiento",
            "Centro Médico": "Centro médico", 
            "Sala": "Sala de adquisición"
        }
        
        # Verificar qué columnas están disponibles
        columnas_presentes = {}
        for col_original, col_sistema in columnas_mapeo.items():
            if col_original in df.columns:
                columnas_presentes[col_original] = col_sistema
            
        # Si no encontramos columnas exactas, buscar similares
        if len(columnas_presentes) == 0:
            for col in df.columns:
                col_lower = col.lower()
                if "prestacion" in col_lower or "procedimiento" in col_lower or "examen" in col_lower:
                    columnas_presentes[col] = "Nombre del procedimiento"
                elif "centro" in col_lower or "hospital" in col_lower or "clinica" in col_lower:
                    columnas_presentes[col] = "Centro médico"
                elif "sala" in col_lower or "equipo" in col_lower:
                    columnas_presentes[col] = "Sala de adquisición"
        
        # Crear DataFrame procesado
        df_procesado = pd.DataFrame()
        
        # Copiar datos de las columnas encontradas
        for col_original, col_sistema in columnas_presentes.items():
            serie = df[col_original].fillna("").astype(str).str.strip()
            df_procesado[col_sistema] = serie
            
        # Asegurarnos de que tenemos todas las columnas necesarias
        for col_sistema in ["Nombre del procedimiento", "Centro médico", "Sala de adquisición"]:
            if col_sistema not in df_procesado.columns:
                df_procesado[col_sistema] = ""
        
        # Filtrar filas vacías
        df_procesado = df_procesado[df_procesado["Nombre del procedimiento"].str.strip() != ""]
        
        return df_procesado
    except Exception as e:
        st.error(f"Error al procesar Excel: {e}")
        return None

# Función para listar hojas Excel
def listar_hojas_excel(ruta_excel):
    """Lista las hojas disponibles en un Excel."""
    try:
        return pd.ExcelFile(ruta_excel).sheet_names
    except Exception as e:
        st.error(f"Error al leer hojas del Excel: {e}")
        return []

# Título principal
st.title("Procesador de Exámenes Médicos 🏥")

# Sección de carga de archivos
st.header("1. Cargar Archivo Excel")
uploaded_file = st.file_uploader(
    "Seleccione su archivo de exámenes (Excel)",
    type=["xlsx", "xls"]
)

if uploaded_file is not None:
    # Crear archivo temporal para el Excel
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        temp_excel_path = tmp_file.name
    
    # Obtener hojas disponibles
    hojas = listar_hojas_excel(temp_excel_path)
    
    if hojas:
        # Seleccionar hoja si hay más de una
        if len(hojas) > 1:
            hoja_seleccionada = st.selectbox(
                "Seleccionar hoja:",
                hojas,
                index=0 if "Data" not in hojas else hojas.index("Data")
            )
        else:
            hoja_seleccionada = hojas[0]
        
        # Procesar datos para vista previa
        try:
            df_preview = pd.read_excel(temp_excel_path, sheet_name=hoja_seleccionada, nrows=5, dtype=str)
            st.subheader(f"Vista previa (primeras 5 filas):")
            st.dataframe(df_preview, use_container_width=True)
            
            # Mostrar columnas detectadas
            columnas_detectadas = []
            for col in df_preview.columns:
                col_lower = col.lower()
                if any(term in col_lower for term in ["prestacion", "procedimiento", "examen"]):
                    columnas_detectadas.append(f"✅ '{col}' -> Procedimiento")
                elif any(term in col_lower for term in ["centro", "hospital", "clinica"]):
                    columnas_detectadas.append(f"✅ '{col}' -> Centro médico")
                elif any(term in col_lower for term in ["sala", "equipo"]):
                    columnas_detectadas.append(f"✅ '{col}' -> Sala")
            
            if columnas_detectadas:
                st.success("Columnas detectadas automáticamente:")
                for col in columnas_detectadas:
                    st.write(col)
            else:
                st.warning("No se detectaron columnas automáticamente. Procesaremos manualmente.")
        except Exception as e:
            st.warning(f"No se pudo mostrar vista previa: {str(e)}")
        
        # Botón para procesar
        if st.button("Procesar Archivo", type="primary"):
            with st.spinner(f"Procesando archivo Excel..."):
                # Procesar Excel directamente
                df_procesado = procesar_excel_directo(temp_excel_path, hoja_seleccionada)
                
                if df_procesado is not None and not df_procesado.empty:
                    st.success(f"Archivo procesado correctamente. Se encontraron {len(df_procesado)} exámenes.")
                    
                    # Guardar en CSV temporal
                    csv_temp = f"/tmp/datos_procesados_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
                    df_procesado.to_csv(csv_temp, index=False)
                    
                    # Procesar con el sistema de códigos
                    resultado = sistema.procesar_csv(csv_temp)
                    
                    if 'error' in resultado:
                        st.error(f"Error al procesar datos: {resultado['error']}")
                    else:
                        # Mostrar resultados
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Nuevos códigos", resultado["nuevos"])
                        with col2:
                            st.metric("Códigos actualizados", resultado["actualizados"])
                        with col3:
                            st.metric("Errores", resultado["errores"])
                        
                        # Mostrar tabla de exámenes procesados
                        st.subheader("Exámenes procesados:")
                        examenes = sistema.buscar_examenes(limite=100)
                        
                        if examenes:
                            df_examenes = pd.DataFrame(examenes)
                            df_examenes = df_examenes[['codigo', 'nombre', 'tipo', 'centro', 'sala', 'conteo']]
                            df_examenes.columns = ['Código', 'Nombre', 'Tipo', 'Centro', 'Sala', 'Usos']
                            df_examenes = df_examenes.fillna("N/A")
                            
                            st.dataframe(df_examenes, use_container_width=True)
                        
                        # Limpiar archivos temporales
                        try:
                            os.remove(csv_temp)
                        except:
                            pass
                else:
                    st.error("No se pudieron extraer datos del archivo Excel.")
            
            # Limpiar archivo temporal
            try:
                os.remove(temp_excel_path)
            except:
                pass

# Sección de búsqueda
st.markdown("---")
st.header("2. Buscar Exámenes")

# Opciones de búsqueda simples
busqueda_texto = st.text_input("Buscar por nombre o código:")

if st.button("Buscar"):
    if busqueda_texto:
        examenes = sistema.buscar_examenes(texto=busqueda_texto)
        
        if examenes:
            st.success(f"Se encontraron {len(examenes)} exámenes")
            
            # Mostrar resultados
            df_resultados = pd.DataFrame(examenes)
            df_resultados = df_resultados[['codigo', 'nombre', 'tipo', 'centro', 'sala', 'conteo']]
            df_resultados.columns = ['Código', 'Nombre', 'Tipo', 'Centro', 'Sala', 'Usos']
            df_resultados = df_resultados.fillna("N/A")
            
            st.dataframe(df_resultados, use_container_width=True)
        else:
            st.info("No se encontraron exámenes con ese criterio")
    else:
        st.info("Ingrese algún texto para buscar")

# Cerrar conexiones
try:
    sistema.cerrar_db()
except:
    pass