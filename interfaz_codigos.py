#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz Streamlit para Sistema de Codificación de Exámenes
----------------------------------------------------------
Visualización y gestión interactiva del sistema de códigos de exámenes médicos.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
import io
import json
from sistema_codigos_examenes import SistemaCodigos

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Códigos de Exámenes",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Crear instancia del sistema de códigos
@st.cache_resource
def cargar_sistema():
    return SistemaCodigos()

sistema = cargar_sistema()

# Función para crear gráficos de barras
def crear_grafico_barras(data, x_col, y_col, titulo, color="viridis"):
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data
            
        if not df.empty:
            sns.barplot(x=x_col, y=y_col, data=df, palette=color, ax=ax)
            plt.title(titulo)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
        else:
            plt.title("No hay datos disponibles")
        
        return fig
    except Exception as e:
        st.error(f"Error al crear gráfico: {e}")
        fig, ax = plt.subplots(figsize=(10, 6))
        plt.title(f"Error al crear gráfico: {e}")
        return fig

# Barra lateral para navegación
st.sidebar.title("Sistema de Códigos")
pagina = st.sidebar.radio(
    "Ir a:",
    [
        "Cargar Archivos Excel",
        "Búsqueda",
        "Registrar Examen Individual",
        "Estadísticas",
        "Importar/Exportar"
    ]
)

# Página para cargar archivos Excel
if pagina == "Cargar Archivos Excel":
    st.title("Carga de Archivos Excel de Exámenes")
    
    st.markdown("""
    ### 📊 Cargar Archivo Excel de Exámenes Médicos
    
    Suba su archivo Excel con los datos de exámenes para generar códigos y mantener un registro estructurado.
    """)
    
    # Destacar la carga de archivos con caja informativa
    st.info("👉 **Cargue su archivo Excel (.xlsx, .xls)** con la lista de exámenes para procesarlos automáticamente")
    
    # Sección de carga de archivos con tamaño destacado
    uploaded_file = st.file_uploader("Seleccionar archivo Excel", type=["xlsx", "xls", "csv"])
    
    if uploaded_file is not None:
        try:
            # Detectar tipo de archivo
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            # Leer según el tipo de archivo
            if file_extension in ['xlsx', 'xls']:
                # Importar el convertidor de Excel
                from convertir_excel import convertir_excel_a_csv, obtener_hojas_excel
                
                # Guardar temporalmente el archivo Excel
                temp_excel_path = os.path.join("data", f"temp_excel_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_extension}")
                with open(temp_excel_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Obtener la lista de hojas del archivo Excel
                hojas_info = obtener_hojas_excel(temp_excel_path)
                
                if "error" in hojas_info:
                    st.error(f"Error al leer hojas del Excel: {hojas_info['error']}")
                    if os.path.exists(temp_excel_path):
                        os.remove(temp_excel_path)
                    st.stop()
                
                # Seleccionar la hoja que se quiere usar
                hoja_seleccionada = 0  # Por defecto, la primera hoja
                
                if len(hojas_info["hojas"]) > 1:
                    opciones_hojas = [f"{i}: {nombre}" for i, nombre in enumerate(hojas_info["hojas"])]
                    hoja_combo = st.selectbox(
                        "Seleccionar hoja del archivo Excel:", 
                        opciones_hojas,
                        help="El archivo Excel tiene múltiples hojas. Seleccione la que contiene los datos de exámenes."
                    )
                    # Extraer el índice de la hoja seleccionada
                    try:
                        hoja_seleccionada = int(hoja_combo.split(':')[0])
                    except ValueError:
                        # Si hay algún problema con la extracción, usar la primera hoja
                        hoja_seleccionada = 0
                        st.warning("No se pudo extraer el índice de la hoja correctamente. Usando la primera hoja.")
                
                # Leer con pandas para vista previa
                df = pd.read_excel(temp_excel_path, sheet_name=hoja_seleccionada)
                st.write(f"Vista previa (Excel - Hoja: {hojas_info['hojas'][hoja_seleccionada]}):")
                st.dataframe(df.head(5), use_container_width=True)
                
                # Preparar nombre para archivo CSV
                temp_csv_path = os.path.join("data", f"temp_csv_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
                
                # Guardar información de la hoja seleccionada para usarla después
                hoja_info = {
                    "indice": hoja_seleccionada,
                    "nombre": hojas_info["hojas"][hoja_seleccionada]
                }
            else:
                # Para archivos CSV, leer directamente
                df = pd.read_csv(uploaded_file)
                st.write("Vista previa (CSV):")
                st.dataframe(df.head(5), use_container_width=True)
                
                # Guardar temporalmente el archivo CSV
                temp_csv_path = os.path.join("data", f"temp_csv_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
                with open(temp_csv_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # No necesitamos convertir, ya es CSV
                temp_excel_path = None
                hoja_info = None
            
            # Verificar columnas necesarias
            if "Nombre del procedimiento" not in df.columns:
                columnas_similares = [col for col in df.columns 
                                     if ('nombre' in col.lower() and ('proced' in col.lower() or 'examen' in col.lower())) or
                                        'procedimiento' in col.lower() or 'examen' in col.lower()]
                
                if columnas_similares:
                    st.warning(f"""⚠️ No se encontró la columna exacta 'Nombre del procedimiento' pero se detectaron columnas similares: 
                                {', '.join(columnas_similares)}. 
                                El sistema intentará usar estas columnas automáticamente.""")
                else:
                    st.error("❌ El archivo debe contener una columna con nombres de exámenes (buscando 'Nombre del procedimiento' o similar)")
                    st.stop()
            
            # Destacar el botón de procesamiento
            if st.button("🔍 PROCESAR ARCHIVO", type="primary", use_container_width=True):
                with st.spinner("Procesando datos..."):
                    # Si es Excel, convertir primero
                    if file_extension in ['xlsx', 'xls']:
                        st.info(f"Convirtiendo archivo Excel a formato procesable (Hoja: {hoja_info['nombre']})...")
                        
                        try:
                            # Primero intentar con el convertidor habitual
                            conversion = convertir_excel_a_csv(
                                temp_excel_path, 
                                temp_csv_path,
                                hoja=hoja_info['indice'],
                                detectar_cabeceras=True
                            )
                            
                            # Si hay error, intentar con el transformador especializado
                            if "error" in conversion:
                                st.warning(f"El conversor estándar encontró un error: {conversion['error']}")
                                st.info("Intentando con método alternativo para archivos Excel problemáticos...")
                                
                                # Importar el transformador especializado
                                from transformar_excel import transformar_excel_a_csv
                                
                                # Intentar transformación especializada
                                resultado_transform = transformar_excel_a_csv(
                                    temp_excel_path,
                                    temp_csv_path,
                                    hoja_info['indice']
                                )
                                
                                if resultado_transform['exito']:
                                    st.success(f"Conversión exitosa con método alternativo ({resultado_transform['metodo']}).")
                                    # Actualizar la ruta del CSV si fue cambiada
                                    if resultado_transform['ruta_csv'] != temp_csv_path:
                                        temp_csv_path = resultado_transform['ruta_csv']
                                else:
                                    st.error(f"No se pudo convertir el archivo Excel automáticamente: {resultado_transform.get('error', 'Error desconocido')}")
                                    
                                    # Activar solución de emergencia
                                    try:
                                        from solucion_emergencia import extraer_columnas_necesarias, crear_plantilla_csv, generar_instrucciones_usuario
                                        
                                        st.warning("⚠️ Se ha detectado un formato Excel problemático que no podemos procesar directamente.")
                                        
                                        # Generar archivos de ayuda
                                        directorio_downloads = os.path.dirname(temp_excel_path)
                                        base_name = os.path.splitext(os.path.basename(uploaded_file.name))[0]
                                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                                        
                                        # Crear rutas
                                        ruta_csv_emergencia = os.path.join(directorio_downloads, f"{base_name}_simplificado_{timestamp}.csv")
                                        ruta_plantilla = os.path.join(directorio_downloads, f"plantilla_examenes_{timestamp}.csv")
                                        ruta_instrucciones = os.path.join(directorio_downloads, f"INSTRUCCIONES_EXCEL_PROBLEMATICO_{timestamp}.txt")
                                        
                                        # Generar archivos
                                        resultado_csv = extraer_columnas_necesarias(temp_excel_path, ruta_csv_emergencia)
                                        resultado_plantilla = crear_plantilla_csv(ruta_plantilla)
                                        resultado_instr = generar_instrucciones_usuario(ruta_instrucciones)
                                        
                                        # Mostrar mensaje e instrucciones
                                        st.info("🛠️ Hemos generado archivos de ayuda para procesar su Excel:")
                                        
                                        # Crear expander con instrucciones
                                        with st.expander("➡️ Cómo procesar su archivo Excel (haga clic para ver)"):
                                            st.markdown("""
                                            ### Instrucciones para procesar su archivo Excel
                                            
                                            Hemos detectado que su archivo Excel tiene un formato que causa problemas al procesarlo automáticamente.
                                            Por favor, siga estos pasos:
                                            
                                            1. **Opción 1: Usar la plantilla CSV**
                                               - Descargue la plantilla CSV generada
                                               - Ábrala en Excel y copie los datos de su archivo original
                                               - Guárdela y cárguela en esta interfaz
                                            
                                            2. **Opción 2: Convertir manualmente el Excel original**
                                               - Abra su archivo Excel en Microsoft Excel o LibreOffice
                                               - Guárdelo como CSV (*.csv) desde el menú "Guardar como..."
                                               - Cargue el nuevo CSV en esta interfaz
                                            
                                            Los datos mínimos necesarios son:
                                            - Nombre del procedimiento (columna "Prestación" en su Excel)
                                            - Centro médico (columna "Centro Médico" en su Excel)
                                            - Sala de adquisición (columna "Sala" en su Excel)
                                            """)
                                        
                                        # Proporcionar enlaces para descargar los archivos de ayuda
                                        if resultado_plantilla["exito"]:
                                            # Leer el contenido de la plantilla para permitir la descarga
                                            with open(ruta_plantilla, "r", encoding="utf-8") as f:
                                                contenido_plantilla = f.read()
                                            
                                            # Botón de descarga para la plantilla
                                            st.download_button(
                                                label="📝 Descargar Plantilla CSV",
                                                data=contenido_plantilla,
                                                file_name=f"plantilla_examenes.csv",
                                                mime="text/csv",
                                                help="Descargue esta plantilla, llénela con los datos de su Excel y cárguela aquí"
                                            )
                                        
                                        if resultado_instr["exito"]:
                                            # Leer el contenido de las instrucciones para permitir la descarga
                                            with open(ruta_instrucciones, "r", encoding="utf-8") as f:
                                                contenido_instr = f.read()
                                            
                                            # Botón de descarga para las instrucciones
                                            st.download_button(
                                                label="📋 Descargar Instrucciones Detalladas",
                                                data=contenido_instr,
                                                file_name=f"INSTRUCCIONES_EXCEL_PROBLEMATICO.txt",
                                                mime="text/plain",
                                                help="Descargue las instrucciones completas para procesar su archivo Excel"
                                            )
                                            
                                    except Exception as e:
                                        st.error(f"Error al generar solución de emergencia: {str(e)}")
                                    
                                    # Limpiar archivos temporales y detener proceso
                                    if os.path.exists(temp_excel_path):
                                        os.remove(temp_excel_path)
                                    st.stop()
                        except Exception as e:
                            st.error(f"Error al convertir Excel: {str(e)}")
                            # Limpiar archivos temporales
                            if os.path.exists(temp_excel_path):
                                os.remove(temp_excel_path)
                            st.stop()
                        
                        # Mostrar información adicional
                        if not conversion["info_columnas"]["tiene_columna_nombre"]:
                            st.warning("No se encontró la columna 'Nombre del procedimiento' exacta.")
                            if conversion["info_columnas"]["columnas_similares"]:
                                columnas_similares = ", ".join(conversion["info_columnas"]["columnas_similares"])
                                st.info(f"Se encontraron columnas similares: {columnas_similares}")
                                st.write("El sistema intentará usar estas columnas como alternativa.")
                    
                    # Procesar el CSV con detección automática de columnas
                    resultado = sistema.procesar_csv(temp_csv_path)
                
                if "error" in resultado:
                    st.error(f"Error: {resultado['error']}")
                else:
                    st.success(f"✅ Procesamiento completado con éxito")
                    
                    # Mostrar resultados
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Nuevos exámenes", resultado["nuevos"])
                    with col2:
                        st.metric("Actualizados", resultado["actualizados"])
                    with col3:
                        st.metric("Errores", resultado["errores"])
                    
                    # Mostrar información de columnas usadas si está disponible
                    if "columnas_usadas" in resultado:
                        with st.expander("Detalles de columnas utilizadas"):
                            st.markdown("#### Mapeo de columnas")
                            
                            columnas_info = pd.DataFrame({
                                "Campo del sistema": ["Nombre del procedimiento", "Centro médico", "Sala de adquisición", "Descripción"],
                                "Columna utilizada": [
                                    resultado["columnas_usadas"]["nombre"] or "No disponible",
                                    resultado["columnas_usadas"]["centro"] or "No disponible",
                                    resultado["columnas_usadas"]["sala"] or "No disponible",
                                    resultado["columnas_usadas"]["descripcion"] or "No disponible"
                                ]
                            })
                            
                            st.dataframe(columnas_info)
                
                # Limpiar archivos temporales
                if temp_excel_path and os.path.exists(temp_excel_path):
                    os.remove(temp_excel_path)
                if os.path.exists(temp_csv_path):
                    os.remove(temp_csv_path)
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
            # Asegurarse de limpiar cualquier archivo temporal en caso de error
            try:
                if 'temp_excel_path' in locals() and temp_excel_path and os.path.exists(temp_excel_path):
                    os.remove(temp_excel_path)
                if 'temp_csv_path' in locals() and temp_csv_path and os.path.exists(temp_csv_path):
                    os.remove(temp_csv_path)
            except:
                pass
    
    # Mostrar estadísticas básicas en tarjetas después de la carga
    try:
        stats = sistema.obtener_estadisticas()
        
        st.subheader("Estadísticas del Sistema")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Exámenes", f"{stats['total_examenes']:,}")
        
        with col2:
            st.metric("Usos Registrados", f"{stats['total_usos']:,}")
        
        with col3:
            st.metric("Centros", f"{stats['total_centros']:,}")
        
        # Mostrar distribución por tipo si hay datos
        if stats['total_examenes'] > 0 and len(stats['por_tipo']) > 0:
            # Crear DataFrame para gráfico
            tipo_df = pd.DataFrame([
                {"tipo": tipo, "cantidad": cantidad} 
                for tipo, cantidad in stats['por_tipo'].items()
            ])
            
            fig = crear_grafico_barras(tipo_df, "tipo", "cantidad", "Exámenes por Tipo")
            st.pyplot(fig)
    
    except Exception as e:
        pass  # Silenciar errores de estadísticas para no distraer del flujo principal

# Página para registrar exámenes individuales
elif pagina == "Registrar Examen Individual":
    st.title("Registrar Examen Individual")
    
    st.subheader("Registrar Nuevo Examen")
    
    with st.form("form_nuevo_examen"):
        nombre = st.text_input("Nombre del examen o procedimiento*", 
                              placeholder="TAC de tórax")
        
        # Selector de tipo con detección automática
        tipos = ["Detectar automáticamente", "TAC", "RX", "RM", "US", "PET", "OTRO"]
        tipo_seleccionado = st.selectbox("Tipo de examen", tipos)
        
        col1, col2 = st.columns(2)
        
        with col1:
            centro = st.text_input("Centro médico", placeholder="Hospital Central")
        
        with col2:
            sala = st.text_input("Sala", placeholder="SCA TAC 01")
        
        descripcion = st.text_area("Descripción (opcional)", 
                                 placeholder="Detalles adicionales del examen...")
        
        submitted = st.form_submit_button("Registrar Examen")
        
        if submitted:
            if nombre:
                tipo_final = None
                if tipo_seleccionado != "Detectar automáticamente":
                    tipo_final = tipo_seleccionado
                    
                resultado = sistema.registrar_examen(
                    nombre=nombre,
                    centro=centro if centro else None,
                    sala=sala if sala else None,
                    descripcion=descripcion if descripcion else None
                )
                
                if "error" in resultado:
                    st.error(f"Error al registrar examen: {resultado['error']}")
                else:
                    if resultado["nuevo"]:
                        st.success(f"Examen registrado con código: {resultado['codigo']}")
                    else:
                        st.info(f"El examen ya existía. Se actualizó su contador. Código: {resultado['codigo']}")
                    
                    # Mostrar detalles del examen registrado
                    examen = sistema.obtener_examen_por_codigo(resultado['codigo'])
                    if examen:
                        st.write(f"**Tipo detectado:** {examen['tipo']}")
                        st.write(f"**Usos totales:** {examen['conteo']}")
            else:
                st.warning("El nombre del examen es obligatorio")

# Página de búsqueda
elif pagina == "Búsqueda":
    st.title("Búsqueda de Exámenes")
    
    # Opciones de búsqueda
    col1, col2, col3 = st.columns(3)
    
    with col1:
        busqueda_texto = st.text_input("Texto a buscar", 
                                     placeholder="Nombre o código",
                                     help="Busca en nombres y códigos")
    
    with col2:
        # Opciones de tipo
        tipos = ["Todos", "TAC", "RX", "RM", "US", "PET", "OTRO"]
        tipo_busqueda = st.selectbox("Tipo de examen", tipos)
        tipo_filtro = None if tipo_busqueda == "Todos" else tipo_busqueda
    
    with col3:
        # Obtener lista de centros
        try:
            centros = ["Todos"] + sistema.obtener_centros()
            centro_busqueda = st.selectbox("Centro médico", centros)
            centro_filtro = None if centro_busqueda == "Todos" else centro_busqueda
        except:
            centro_busqueda = "Todos"
            centro_filtro = None
            st.error("Error al cargar centros médicos")
    
    # Filtro adicional por sala
    if centro_filtro:
        try:
            # Obtener salas del centro seleccionado
            salas = ["Todas"] + sistema.obtener_salas(centro_filtro)
            sala_busqueda = st.selectbox("Sala", salas)
            sala_filtro = None if sala_busqueda == "Todas" else sala_busqueda
        except:
            sala_busqueda = "Todas"
            sala_filtro = None
    else:
        try:
            # Obtener todas las salas
            salas = ["Todas"] + sistema.obtener_salas()
            sala_busqueda = st.selectbox("Sala", salas)
            sala_filtro = None if sala_busqueda == "Todas" else sala_busqueda
        except:
            sala_busqueda = "Todas"
            sala_filtro = None
    
    # Botón de búsqueda
    if st.button("Buscar"):
        try:
            examenes = sistema.buscar_examenes(
                texto=busqueda_texto if busqueda_texto else None,
                tipo=tipo_filtro,
                centro=centro_filtro,
                sala=sala_filtro
            )
            
            if examenes:
                st.success(f"Se encontraron {len(examenes)} exámenes")
                
                # Convertir a DataFrame para mostrar
                df = pd.DataFrame(examenes)
                df = df[['codigo', 'nombre', 'tipo', 'centro', 'sala', 'conteo']]
                df.columns = ['Código', 'Nombre', 'Tipo', 'Centro', 'Sala', 'Usos']
                
                # Reemplazar valores nulos
                df = df.fillna("N/A")
                
                st.dataframe(df, use_container_width=True)
                
                # Opción para ver detalles
                with st.expander("Ver detalles de un examen"):
                    codigo_detalle = st.selectbox(
                        "Seleccione un código para ver detalles",
                        [""] + list(df['Código'])
                    )
                    
                    if codigo_detalle:
                        examen = sistema.obtener_examen_por_codigo(codigo_detalle)
                        if examen:
                            st.subheader(f"Detalles de {examen['nombre']}")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Código:** {examen['codigo']}")
                                st.write(f"**Tipo:** {examen['tipo']}")
                                st.write(f"**Usos totales:** {examen['conteo']}")
                                st.write(f"**Fecha de creación:** {examen['fecha_creacion']}")
                            
                            with col2:
                                if examen['centro']:
                                    st.write(f"**Centro:** {examen['centro']}")
                                if examen['sala']:
                                    st.write(f"**Sala:** {examen['sala']}")
                                if examen['descripcion']:
                                    st.write(f"**Descripción:** {examen['descripcion']}")
                            
                            if examen['historial']:
                                st.subheader("Historial de usos recientes")
                                
                                # Crear DataFrame de historial
                                hist_df = pd.DataFrame(examen['historial'])
                                hist_df.columns = ['Centro', 'Sala', 'Fecha']
                                hist_df = hist_df.fillna("N/A")
                                
                                st.dataframe(hist_df, use_container_width=True)
            else:
                st.warning("No se encontraron exámenes con los criterios especificados")
        
        except Exception as e:
            st.error(f"Error en la búsqueda: {e}")
    
    # Búsqueda directa por código
    st.subheader("Búsqueda por código")
    
    codigo_busqueda = st.text_input("Ingrese un código de examen", placeholder="T123ABC")
    
    if codigo_busqueda:
        if st.button("Buscar por código"):
            examen = sistema.obtener_examen_por_codigo(codigo_busqueda)
            
            if examen:
                st.subheader(f"Detalles de {examen['nombre']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Código:** {examen['codigo']}")
                    st.write(f"**Tipo:** {examen['tipo']}")
                    st.write(f"**Usos totales:** {examen['conteo']}")
                    st.write(f"**Fecha de creación:** {examen['fecha_creacion']}")
                
                with col2:
                    if examen['centro']:
                        st.write(f"**Centro:** {examen['centro']}")
                    if examen['sala']:
                        st.write(f"**Sala:** {examen['sala']}")
                    if examen['descripcion']:
                        st.write(f"**Descripción:** {examen['descripcion']}")
                
                if examen['historial']:
                    st.subheader("Historial de usos recientes")
                    
                    # Crear DataFrame de historial
                    hist_df = pd.DataFrame(examen['historial'])
                    hist_df.columns = ['Centro', 'Sala', 'Fecha']
                    hist_df = hist_df.fillna("N/A")
                    
                    st.dataframe(hist_df, use_container_width=True)
            else:
                st.warning(f"No se encontró ningún examen con el código {codigo_busqueda}")

# Página de estadísticas
elif pagina == "Estadísticas":
    st.title("Estadísticas del Sistema")
    
    try:
        stats = sistema.obtener_estadisticas()
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Exámenes", f"{stats['total_examenes']:,}")
        
        with col2:
            st.metric("Usos Registrados", f"{stats['total_usos']:,}")
        
        with col3:
            st.metric("Centros Médicos", f"{stats['total_centros']:,}")
        
        with col4:
            st.metric("Salas", f"{stats['total_salas']:,}")
        
        # Distribución por tipo
        if stats['total_examenes'] > 0:
            st.subheader("Distribución por Tipo de Examen")
            
            # Crear DataFrame para gráfico
            tipo_df = pd.DataFrame([
                {"tipo": tipo, "cantidad": cantidad} 
                for tipo, cantidad in stats['por_tipo'].items()
            ])
            
            fig = crear_grafico_barras(tipo_df, "tipo", "cantidad", "Exámenes por Tipo", "viridis")
            st.pyplot(fig)
            
            # Tabla de distribución
            st.dataframe(tipo_df, use_container_width=True)
            
            # Exámenes más usados
            if stats['mas_usados']:
                st.subheader("Exámenes más utilizados")
                
                # Crear DataFrame para gráfico
                most_used_df = pd.DataFrame(stats['mas_usados'])
                most_used_df = most_used_df.sort_values('conteo', ascending=False)
                
                # Truncar nombres largos para el gráfico
                most_used_df['nombre_corto'] = most_used_df['nombre'].apply(
                    lambda x: x[:25] + '...' if len(str(x)) > 25 else x
                )
                
                fig = crear_grafico_barras(most_used_df, "nombre_corto", "conteo", 
                                         "Exámenes más utilizados", "plasma")
                st.pyplot(fig)
                
                # Tabla detallada
                detailed_df = pd.DataFrame(stats['mas_usados'])
                detailed_df = detailed_df[['codigo', 'nombre', 'tipo', 'conteo']]
                detailed_df.columns = ['Código', 'Nombre', 'Tipo', 'Usos']
                
                st.dataframe(detailed_df, use_container_width=True)
            
            # Análisis por centro y sala
            if stats['total_centros'] > 0:
                st.subheader("Exámenes por Centro y Sala")
                
                # Obtener datos agrupados por centro y tipo
                by_center_df = pd.DataFrame(
                    sistema.buscar_examenes(limite=1000)
                )
                
                if not by_center_df.empty and 'centro' in by_center_df.columns:
                    # Filtrar registros sin centro
                    by_center_df = by_center_df[by_center_df['centro'].notna()]
                    
                    if not by_center_df.empty:
                        # Agrupar por centro y tipo
                        center_type_counts = by_center_df.groupby(['centro', 'tipo']).size().reset_index(name='count')
                        
                        # Pivot para mejor visualización
                        pivot_df = center_type_counts.pivot(index='centro', columns='tipo', values='count').fillna(0)
                        
                        # Ordenar por total
                        pivot_df['Total'] = pivot_df.sum(axis=1)
                        pivot_df = pivot_df.sort_values('Total', ascending=False)
                        
                        st.dataframe(pivot_df, use_container_width=True)
                        
                        # Gráfico
                        fig, ax = plt.subplots(figsize=(10, 6))
                        pivot_df.drop('Total', axis=1).plot(kind='bar', stacked=True, ax=ax)
                        plt.title("Distribución de exámenes por centro")
                        plt.ylabel("Cantidad de exámenes")
                        plt.xticks(rotation=45, ha="right")
                        plt.tight_layout()
                        st.pyplot(fig)
        else:
            st.info("No hay datos suficientes para mostrar estadísticas")
    
    except Exception as e:
        st.error(f"Error al generar estadísticas: {e}")

# Página de importación/exportación
elif pagina == "Importar/Exportar":
    st.title("Importar / Exportar Datos")
    
    tab1, tab2 = st.tabs(["Exportar", "Importar"])
    
    with tab1:
        st.subheader("Exportar datos")
        
        st.write("Exporte todos los datos del sistema a un archivo JSON")
        
        if st.button("Generar archivo de exportación"):
            try:
                with st.spinner("Generando archivo..."):
                    resultado = sistema.exportar_json()
                
                if resultado["exito"]:
                    st.success(f"Exportación completada. Se exportaron {resultado['total']} exámenes.")
                    
                    # Leer el archivo para descarga
                    with open(resultado["archivo"], "r", encoding="utf-8") as f:
                        contenido = f.read()
                    
                    # Botón de descarga
                    st.download_button(
                        label="Descargar archivo JSON",
                        data=contenido,
                        file_name=os.path.basename(resultado["archivo"]),
                        mime="application/json"
                    )
                else:
                    st.error(f"Error al exportar: {resultado['error']}")
            except Exception as e:
                st.error(f"Error al exportar datos: {e}")
    
    with tab2:
        st.subheader("Importar datos")
        
        st.write("Importe datos desde un archivo JSON exportado previamente")
        
        uploaded_file = st.file_uploader("Seleccionar archivo JSON", type=["json"])
        
        if uploaded_file is not None:
            try:
                # Validar que sea un JSON válido
                try:
                    data = json.loads(uploaded_file.getvalue().decode('utf-8'))
                except:
                    st.error("El archivo no contiene JSON válido")
                    st.stop()
                
                # Guardar temporalmente
                temp_path = os.path.join("data", f"temp_import_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
                
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                if st.button("Importar datos"):
                    with st.spinner("Importando datos..."):
                        resultado = sistema.importar_json(temp_path)
                    
                    if "error" in resultado:
                        st.error(f"Error: {resultado['error']}")
                    else:
                        st.success("Importación completada con éxito")
                        
                        # Mostrar resultados
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Nuevos exámenes", resultado["nuevos"])
                        with col2:
                            st.metric("Actualizados", resultado["actualizados"])
                        with col3:
                            st.metric("Errores", resultado["errores"])
                        
                        # Eliminar archivo temporal
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")

# Cierre de conexión
try:
    sistema.cerrar_db()
except:
    pass