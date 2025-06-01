#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz Streamlit para Sistema de Codificación de Exámenes
----------------------------------------------------------
Visualización y gestión interactiva del sistema de códigos de exámenes médicos.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
import io
import json
from codigo_examenes import CodigosExamenes

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
    return CodigosExamenes()

sistema = cargar_sistema()

# Función para crear gráficos
def crear_grafico_barras(datos, x, y, titulo, color='viridis'):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    if isinstance(datos, list):
        # Convertir lista de diccionarios a DataFrame
        df = pd.DataFrame(datos)
    else:
        df = datos
    
    if len(df) > 0:
        try:
            bar_plot = sns.barplot(x=x, y=y, data=df, palette=color, ax=ax)
            plt.title(titulo)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Añadir valores en las barras
            for p in bar_plot.patches:
                bar_plot.annotate(format(p.get_height(), '.0f'),
                                  (p.get_x() + p.get_width() / 2., p.get_height()),
                                  ha = 'center', va = 'center',
                                  xytext = (0, 9),
                                  textcoords = 'offset points')
        except Exception as e:
            plt.text(0.5, 0.5, f"Error al crear gráfico: {str(e)}", 
                     horizontalalignment='center', verticalalignment='center',
                     transform=ax.transAxes, fontsize=12)
    else:
        plt.text(0.5, 0.5, "No hay datos disponibles", 
                 horizontalalignment='center', verticalalignment='center',
                 transform=ax.transAxes, fontsize=14)
    
    return fig

# Barra lateral para navegación
st.sidebar.title("Navegación")
pagina = st.sidebar.radio(
    "Ir a:",
    [
        "Inicio", 
        "Búsqueda de Códigos", 
        "Estadísticas", 
        "Cargar Datos",
        "Gestión de Centros y Salas"
    ]
)

# Página de inicio
if pagina == "Inicio":
    st.title("Sistema de Codificación de Exámenes Médicos")
    
    st.markdown("""
    ### Bienvenido al sistema de gestión y análisis de códigos de exámenes
    
    Esta aplicación permite:
    - Buscar y visualizar códigos de exámenes médicos
    - Generar estadísticas por tipos de exámenes, centros médicos y salas
    - Cargar datos desde archivos CSV
    - Gestionar centros médicos y salas de adquisición
    
    Utilice la barra lateral para navegar entre las diferentes secciones.
    """)
    
    # Mostrar algunos datos generales
    try:
        stats = sistema.estadisticas_codigos()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de códigos", f"{stats.get('total_codigos', 0):,}")
        
        with col2:
            # Contar centros médicos
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM centros_medicos")
            total_centros = cursor.fetchone()[0]
            conn.close()
            st.metric("Centros médicos", f"{total_centros:,}")
        
        with col3:
            # Contar usos registrados
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM historico_examenes")
            total_usos = cursor.fetchone()[0]
            conn.close()
            st.metric("Usos registrados", f"{total_usos:,}")
        
        # Mostrar distribución por tipo si hay datos
        if stats.get('total_codigos', 0) > 0 and 'por_tipo' in stats:
            st.subheader("Distribución por tipo de examen")
            
            # Crear DataFrame para el gráfico
            tipos_df = pd.DataFrame({
                'Tipo': list(stats['por_tipo'].keys()),
                'Cantidad': list(stats['por_tipo'].values())
            })
            
            if not tipos_df.empty:
                fig = crear_grafico_barras(tipos_df, 'Tipo', 'Cantidad', 
                                        'Cantidad de exámenes por tipo')
                st.pyplot(fig)
        
        # Mostrar exámenes más comunes si hay datos
        if 'examenes_comunes' in stats and stats['examenes_comunes']:
            st.subheader("Exámenes más frecuentes")
            
            examenes_df = pd.DataFrame(stats['examenes_comunes'])
            examenes_df = examenes_df.sort_values('conteo', ascending=False).head(10)
            
            # Truncar nombres largos
            examenes_df['nombre_corto'] = examenes_df['nombre'].apply(
                lambda x: x[:30] + '...' if len(x) > 30 else x)
            
            if not examenes_df.empty:
                fig = crear_grafico_barras(examenes_df, 'nombre_corto', 'conteo', 
                                        'Exámenes más frecuentes')
                st.pyplot(fig)
    except Exception as e:
        st.error(f"Error al cargar estadísticas: {e}")
        
# Página de búsqueda de códigos
elif pagina == "Búsqueda de Códigos":
    st.title("Búsqueda de Códigos de Exámenes")
    
    # Tabs para diferentes tipos de búsqueda
    tab1, tab2, tab3 = st.tabs(["Por Texto/Tipo", "Por Centro/Sala", "Por Código"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            texto_busqueda = st.text_input("Texto a buscar", placeholder="TAC abdomen")
        
        with col2:
            tipos = ["Todos", "TAC", "RX", "RM", "US", "PET", "PROC", "OTRO"]
            tipo_seleccionado = st.selectbox("Tipo de examen", tipos)
            
            if tipo_seleccionado == "Todos":
                tipo_seleccionado = None
        
        if st.button("Buscar", key="buscar_texto"):
            if texto_busqueda or tipo_seleccionado:
                examenes = sistema.buscar_examenes(texto_busqueda, tipo=tipo_seleccionado)
                
                if examenes:
                    st.success(f"Se encontraron {len(examenes)} resultados")
                    # Crear DataFrame para mostrar
                    df = pd.DataFrame(examenes)
                    # Reordenar columnas y formatear
                    if 'conteo' in df.columns:
                        df = df[['codigo', 'nombre', 'tipo', 'subtipo', 'complejidad', 'conteo']]
                        df.columns = ['Código', 'Nombre', 'Tipo', 'Subtipo', 'Complejidad', 'Usos']
                    else:
                        df = df[['codigo', 'nombre', 'tipo', 'subtipo', 'complejidad']]
                        df.columns = ['Código', 'Nombre', 'Tipo', 'Subtipo', 'Complejidad']
                    
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("No se encontraron resultados")
            else:
                st.warning("Ingrese un texto para buscar o seleccione un tipo")
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # Obtener lista de centros
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("SELECT nombre FROM centros_medicos ORDER BY nombre")
            centros = [c[0] for c in cursor.fetchall()]
            centros.insert(0, "Todos")
            
            centro_seleccionado = st.selectbox("Centro médico", centros)
            if centro_seleccionado == "Todos":
                centro_seleccionado = None
        
        with col2:
            # Obtener salas (filtradas por centro si se seleccionó uno)
            salas = ["Todas"]
            conn = conectar_db()
            cursor = conn.cursor()
            
            if centro_seleccionado:
                cursor.execute(
                    """SELECT s.nombre FROM salas_adquisicion s 
                       JOIN centros_medicos c ON s.centro_id = c.id 
                       WHERE c.nombre = ? ORDER BY s.nombre""", 
                    (centro_seleccionado,)
                )
                salas.extend([s[0] for s in cursor.fetchall()])
            else:
                cursor.execute("SELECT nombre FROM salas_adquisicion ORDER BY nombre")
                salas.extend([s[0] for s in cursor.fetchall()])
            
            conn.close()
            
            sala_seleccionada = st.selectbox("Sala de adquisición", salas)
            if sala_seleccionada == "Todas":
                sala_seleccionada = None
        
        # Fechas
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Desde fecha", 
                                        value=datetime.now() - timedelta(days=30))
        with col2:
            fecha_fin = st.date_input("Hasta fecha", 
                                    value=datetime.now())
        
        if st.button("Buscar", key="buscar_centro"):
            # Convertir fechas a formato string
            fecha_inicio_str = fecha_inicio.strftime('%Y-%m-%d')
            fecha_fin_str = fecha_fin.strftime('%Y-%m-%d')
            
            examenes = sistema.buscar_examenes_por_centro(
                centro_medico=centro_seleccionado, 
                sala=sala_seleccionada,
                fecha_inicio=fecha_inicio_str,
                fecha_fin=fecha_fin_str
            )
            
            if examenes:
                st.success(f"Se encontraron {len(examenes)} resultados")
                # Crear DataFrame para mostrar
                df = pd.DataFrame(examenes)
                # Reordenar columnas y formatear
                df = df[['codigo', 'nombre', 'tipo', 'centro', 'sala', 'fecha', 'tiempo_real']]
                df.columns = ['Código', 'Nombre', 'Tipo', 'Centro', 'Sala', 'Fecha', 'Duración (min)']
                
                # Reemplazar valores None con "N/A"
                df = df.fillna("N/A")
                
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No se encontraron resultados")
    
    with tab3:
        codigo = st.text_input("Ingrese el código del examen", placeholder="TACC123")
        
        if st.button("Buscar código"):
            if codigo:
                examen = sistema.obtener_examen_por_codigo(codigo)
                
                if examen:
                    # Mostrar información del examen
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Información del Examen")
                        st.markdown(f"**Código:** {examen['codigo']}")
                        st.markdown(f"**Nombre:** {examen['nombre']}")
                        st.markdown(f"**Tipo:** {examen['tipo']}")
                        st.markdown(f"**Subtipo:** {examen['subtipo']}")
                        st.markdown(f"**Complejidad:** {examen['complejidad']}/5")
                        st.markdown(f"**Tiempo estimado:** {examen['tiempo_estimado']} minutos")
                        st.markdown(f"**Usos registrados:** {examen['conteo']}")
                        st.markdown(f"**Fecha de creación:** {examen['fecha_creacion']}")
                    
                    with col2:
                        if 'historial' in examen and examen['historial']:
                            st.subheader("Historial de Uso")
                            historial_df = pd.DataFrame(examen['historial'])
                            historial_df.columns = ['Fecha', 'Centro', 'Sala', 'Duración (min)']
                            historial_df = historial_df.fillna("N/A")
                            st.dataframe(historial_df, use_container_width=True)
                        else:
                            st.info("No hay historial de uso disponible")
                else:
                    st.warning(f"No se encontró ningún examen con el código {codigo}")
            else:
                st.warning("Ingrese un código para buscar")

# Página de estadísticas
elif pagina == "Estadísticas":
    st.title("Estadísticas del Sistema")
    
    tab1, tab2 = st.tabs(["Estadísticas Generales", "Por Centro Médico"])
    
    with tab1:
        try:
            stats = sistema.estadisticas_codigos()
            
            if stats.get('total_codigos', 0) > 0:
                # Mostrar totales
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de códigos", f"{stats['total_codigos']:,}")
                with col2:
                    # Calcular total de procedimientos
                    total_proc = sum(stats['por_tipo'].values())
                    st.metric("Total de procedimientos", f"{total_proc:,}")
                with col3:
                    # Total de exámenes en histórico
                    st.metric("Usos registrados", f"{stats.get('total_historico', 0):,}")
                
                # Distribución por tipo
                st.subheader("Distribución por tipo de examen")
                tipos_df = pd.DataFrame({
                    'Tipo': list(stats['por_tipo'].keys()),
                    'Cantidad': list(stats['por_tipo'].values())
                })
                
                fig = crear_grafico_barras(tipos_df, 'Tipo', 'Cantidad', 
                                        'Cantidad de exámenes por tipo')
                st.pyplot(fig)
                
                # Si hay datos de tiempo, mostrar estadísticas
                if 'tiempo' in stats and stats['tiempo']['promedio']:
                    st.subheader("Estadísticas de tiempo")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Tiempo promedio", f"{stats['tiempo']['promedio']:.1f} min")
                    with col2:
                        st.metric("Tiempo mínimo", f"{stats['tiempo']['minimo']} min")
                    with col3:
                        st.metric("Tiempo máximo", f"{stats['tiempo']['maximo']} min")
                
                # Exámenes más comunes
                if 'examenes_comunes' in stats and stats['examenes_comunes']:
                    st.subheader("Exámenes más frecuentes")
                    examenes_df = pd.DataFrame(stats['examenes_comunes'])
                    examenes_df = examenes_df.sort_values('conteo', ascending=False)
                    
                    # Truncar nombres largos
                    examenes_df['nombre_corto'] = examenes_df['nombre'].apply(
                        lambda x: x[:30] + '...' if len(x) > 30 else x)
                    
                    fig = crear_grafico_barras(examenes_df, 'nombre_corto', 'conteo', 
                                            'Exámenes más frecuentes')
                    st.pyplot(fig)
                    
                    # Mostrar tabla detallada
                    st.dataframe(
                        examenes_df[['codigo', 'nombre', 'tipo', 'conteo']].rename(
                            columns={'codigo': 'Código', 'nombre': 'Nombre', 
                                    'tipo': 'Tipo', 'conteo': 'Usos'}
                        ),
                        use_container_width=True
                    )
            else:
                st.info("No hay datos suficientes para mostrar estadísticas.")
                st.info("Cargue algunos datos desde la sección 'Cargar Datos'.")
        except Exception as e:
            st.error(f"Error al cargar estadísticas generales: {e}")
    
    with tab2:
        try:
            # Obtener lista de centros
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("SELECT nombre FROM centros_medicos ORDER BY nombre")
            centros = [c[0] for c in cursor.fetchall()]
            conn.close()
            
            if centros:
                centro_seleccionado = st.selectbox(
                    "Seleccione un centro médico", 
                    ["Todos"] + centros
                )
                
                if st.button("Generar estadísticas"):
                    if centro_seleccionado == "Todos":
                        # Estadísticas de todos los centros
                        stats = sistema.obtener_estadisticas_centro()
                        
                        if 'total_global' in stats:
                            st.metric("Total de exámenes en todos los centros", 
                                    f"{stats['total_global']:,}")
                            
                            if 'centros' in stats and stats['centros']:
                                st.subheader("Exámenes por centro médico")
                                
                                centros_df = pd.DataFrame(stats['centros'])
                                centros_df = centros_df.sort_values('total_examenes', ascending=False)
                                centros_df.columns = ['ID', 'Centro', 'Total Exámenes']
                                
                                # Crear gráfico
                                fig = crear_grafico_barras(
                                    centros_df, 'Centro', 'Total Exámenes',
                                    'Exámenes por centro médico'
                                )
                                st.pyplot(fig)
                                
                                # Mostrar tabla
                                st.dataframe(
                                    centros_df[['Centro', 'Total Exámenes']],
                                    use_container_width=True
                                )
                            else:
                                st.info("No hay datos de centros médicos para mostrar.")
                        else:
                            st.info("No hay datos de exámenes registrados.")
                    else:
                        # Estadísticas de un centro específico
                        stats = sistema.obtener_estadisticas_centro(centro_seleccionado)
                        
                        if 'error' in stats:
                            st.error(stats['error'])
                        elif 'centro' in stats:
                            centro = stats['centro']
                            
                            # Métricas principales
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total exámenes", f"{centro['total_examenes']:,}")
                            with col2:
                                st.metric("Exámenes TAC", f"{centro['total_tac']:,}")
                            with col3:
                                st.metric("Exámenes RX", f"{centro['total_rx']:,}")
                            
                            # Exámenes por sala
                            if 'salas' in stats and stats['salas']:
                                st.subheader("Exámenes por sala")
                                
                                salas_df = pd.DataFrame(stats['salas'])
                                salas_df = salas_df.sort_values('total', ascending=False)
                                
                                # Crear gráfico
                                fig = crear_grafico_barras(
                                    salas_df, 'nombre', 'total',
                                    f'Exámenes por sala en {centro_seleccionado}'
                                )
                                st.pyplot(fig)
                                
                                # Mostrar desglose por tipo en tabla
                                salas_df.columns = ['Sala', 'Total', 'TAC', 'RX']
                                st.dataframe(salas_df, use_container_width=True)
                            
                            # Exámenes más comunes
                            if 'examenes_comunes' in stats and stats['examenes_comunes']:
                                st.subheader("Exámenes más frecuentes en este centro")
                                
                                examenes_df = pd.DataFrame(stats['examenes_comunes'])
                                examenes_df = examenes_df.sort_values('total', ascending=False)
                                
                                # Truncar nombres largos
                                examenes_df['nombre_corto'] = examenes_df['nombre'].apply(
                                    lambda x: x[:30] + '...' if len(x) > 30 else x)
                                
                                # Crear gráfico
                                fig = crear_grafico_barras(
                                    examenes_df, 'nombre_corto', 'total',
                                    f'Exámenes más frecuentes en {centro_seleccionado}'
                                )
                                st.pyplot(fig)
                                
                                # Mostrar tabla detallada
                                examenes_df.columns = ['Nombre', 'Código', 'Tipo', 'Total', 'Nombre Corto']
                                st.dataframe(
                                    examenes_df[['Código', 'Nombre', 'Tipo', 'Total']],
                                    use_container_width=True
                                )
                        else:
                            st.warning("No se encontraron datos para este centro médico.")
            else:
                st.info("No hay centros médicos registrados en el sistema.")
                st.info("Agregue centros desde la sección 'Gestión de Centros y Salas'.")
        except Exception as e:
            st.error(f"Error al cargar estadísticas por centro: {e}")

# Página para cargar datos
elif pagina == "Cargar Datos":
    st.title("Cargar Datos al Sistema")
    
    st.markdown("""
    En esta sección puede cargar archivos CSV para registrar nuevos exámenes, centros y salas en el sistema.
    
    Los archivos CSV deben contener al menos la columna 'Nombre del procedimiento'.
    Para registrar centros y salas, incluya también las columnas 'Centro médico' y 'Sala de adquisición'.
    """)
    
    # Opción para cargar archivo
    archivo_csv = st.file_uploader("Seleccione un archivo CSV", type=['csv'])
    
    if archivo_csv is not None:
        try:
            # Leer el archivo CSV
            df = pd.read_csv(archivo_csv)
            
            # Mostrar primeras filas para verificación
            st.subheader("Vista previa")
            st.dataframe(df.head(5), use_container_width=True)
            
            # Verificar columnas necesarias
            if 'Nombre del procedimiento' not in df.columns:
                st.error("El archivo debe contener la columna 'Nombre del procedimiento'")
            else:
                # Opciones adicionales
                with st.expander("Opciones avanzadas"):
                    st.write("Mapeo de columnas")
                    col_centro = st.selectbox(
                        "Columna para Centro médico", 
                        ['Centro médico'] + list(df.columns),
                        index=0 if 'Centro médico' in df.columns else -1
                    )
                    
                    col_sala = st.selectbox(
                        "Columna para Sala de adquisición", 
                        ['Sala de adquisición'] + list(df.columns),
                        index=0 if 'Sala de adquisición' in df.columns else -1
                    )
                    
                    col_fecha = st.selectbox(
                        "Columna para Fecha", 
                        ['Fecha del procedimiento'] + list(df.columns),
                        index=0 if 'Fecha del procedimiento' in df.columns else -1
                    )
                    
                    col_duracion = st.selectbox(
                        "Columna para Duración", 
                        ['Duración'] + list(df.columns),
                        index=0 if 'Duración' in df.columns else -1
                    )
                
                # Botón para procesar
                if st.button("Procesar archivo"):
                    # Renombrar columnas según mapeo
                    df_procesado = df.copy()
                    
                    if col_centro != 'Centro médico' and col_centro in df_procesado.columns:
                        df_procesado['Centro médico'] = df_procesado[col_centro]
                    
                    if col_sala != 'Sala de adquisición' and col_sala in df_procesado.columns:
                        df_procesado['Sala de adquisición'] = df_procesado[col_sala]
                    
                    if col_fecha != 'Fecha del procedimiento' and col_fecha in df_procesado.columns:
                        df_procesado['Fecha del procedimiento'] = df_procesado[col_fecha]
                    
                    if col_duracion != 'Duración' and col_duracion in df_procesado.columns:
                        df_procesado['Duración'] = df_procesado[col_duracion]
                    
                    # Procesar datos
                    with st.spinner("Procesando datos..."):
                        exito, mensaje = sistema.procesar_dataframe(df_procesado)
                    
                    if exito:
                        st.success(mensaje)
                    else:
                        st.error(mensaje)
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
    
    # Opciones para exportar/importar datos
    st.subheader("Exportar / Importar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Exportar todos los códigos a JSON"):
            try:
                # Crear un archivo temporal
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                ruta_archivo = sistema.exportar_codigos_json()
                
                # Leer el archivo JSON para descargarlo
                with open(ruta_archivo, 'r') as f:
                    datos_json = f.read()
                
                # Botón de descarga
                st.download_button(
                    label="Descargar archivo JSON",
                    data=datos_json,
                    file_name=f"codigos_examenes_{timestamp}.json",
                    mime="application/json"
                )
                
                st.success(f"Datos exportados correctamente: {os.path.basename(ruta_archivo)}")
            except Exception as e:
                st.error(f"Error al exportar datos: {e}")
    
    with col2:
        # Importar desde JSON
        archivo_json = st.file_uploader("Importar desde JSON", type=['json'])
        
        if archivo_json is not None:
            try:
                # Guardar archivo temporal
                bytes_data = archivo_json.getvalue()
                json_data = bytes_data.decode('utf-8')
                
                # Validar que es un JSON válido
                try:
                    json.loads(json_data)
                except:
                    st.error("El archivo no contiene JSON válido")
                    st.stop()
                
                # Guardar a archivo temporal
                temp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        f"temp_import_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
                
                with open(temp_file, 'w') as f:
                    f.write(json_data)
                
                if st.button("Importar datos"):
                    with st.spinner("Importando datos..."):
                        exito, mensaje = sistema.importar_codigos_json(temp_file)
                    
                    if exito:
                        st.success(mensaje)
                    else:
                        st.error(mensaje)
                    
                    # Eliminar archivo temporal
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
            except Exception as e:
                st.error(f"Error al importar datos: {e}")

# Página de gestión de centros y salas
elif pagina == "Gestión de Centros y Salas":
    st.title("Gestión de Centros Médicos y Salas")
    
    tab1, tab2 = st.tabs(["Centros Médicos", "Salas de Adquisición"])
    
    with tab1:
        st.subheader("Centros Médicos Registrados")
        
        # Obtener y mostrar centros existentes
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, codigo, direccion, region, conteo FROM centros_medicos ORDER BY nombre")
        centros = cursor.fetchall()
        conn.close()
        
        if centros:
            # Crear DataFrame
            centros_df = pd.DataFrame(centros, columns=['ID', 'Nombre', 'Código', 'Dirección', 'Región', 'Usos'])
            st.dataframe(centros_df, use_container_width=True)
        else:
            st.info("No hay centros médicos registrados")
        
        # Formulario para agregar nuevo centro
        st.subheader("Agregar Nuevo Centro Médico")
        
        with st.form("form_nuevo_centro"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre_centro = st.text_input("Nombre del centro", key="nombre_centro")
                codigo_centro = st.text_input("Código (opcional)", key="codigo_centro")
            
            with col2:
                direccion_centro = st.text_input("Dirección (opcional)", key="direccion_centro")
                region_centro = st.text_input("Región (opcional)", key="region_centro")
            
            submitted = st.form_submit_button("Registrar Centro")
            
            if submitted:
                if nombre_centro:
                    try:
                        centro_id, es_nuevo = sistema.registrar_centro_medico(
                            nombre_centro, codigo_centro, direccion_centro, region_centro
                        )
                        
                        if es_nuevo:
                            st.success(f"Centro médico '{nombre_centro}' registrado con éxito!")
                        else:
                            st.info(f"El centro '{nombre_centro}' ya existía. Se actualizaron sus datos.")
                        
                        # Recargar la página para mostrar cambios
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error al registrar centro: {e}")
                else:
                    st.warning("El nombre del centro es obligatorio")
    
    with tab2:
        st.subheader("Salas de Adquisición Registradas")
        
        # Obtener y mostrar salas existentes
        conn = sistema._CodigosExamenes__db_connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.nombre, c.nombre, s.tipo_equipo, s.conteo 
            FROM salas_adquisicion s
            LEFT JOIN centros_medicos c ON s.centro_id = c.id
            ORDER BY c.nombre, s.nombre
        """)
        salas = cursor.fetchall()
        conn.close()
        
        if salas:
            # Crear DataFrame
            salas_df = pd.DataFrame(salas, columns=['ID', 'Nombre', 'Centro', 'Tipo Equipo', 'Usos'])
            st.dataframe(salas_df, use_container_width=True)
        else:
            st.info("No hay salas de adquisición registradas")
        
        # Formulario para agregar nueva sala
        st.subheader("Agregar Nueva Sala de Adquisición")
        
        with st.form("form_nueva_sala"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre_sala = st.text_input("Nombre de la sala", key="nombre_sala")
                
                # Obtener lista de centros para seleccionar
                conn = conectar_db()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nombre FROM centros_medicos ORDER BY nombre")
                centros_lista = cursor.fetchall()
                conn.close()
                
                if centros_lista:
                    centro_opciones = ["[Seleccione un centro]"] + [c[1] for c in centros_lista]
                    centro_sala = st.selectbox("Centro médico", centro_opciones, key="centro_sala")
                    
                    if centro_sala == "[Seleccione un centro]":
                        centro_id = None
                    else:
                        centro_id = next((c[0] for c in centros_lista if c[1] == centro_sala), None)
                else:
                    st.warning("No hay centros médicos registrados. Debe crear un centro primero.")
                    centro_id = None
                    centro_sala = None
            
            with col2:
                tipo_equipo_opciones = ["", "TAC", "RX", "RM", "US", "PET", "OTRO"]
                tipo_equipo = st.selectbox("Tipo de equipo", tipo_equipo_opciones, key="tipo_equipo")
                
                # Campo adicional para notas o descripción
                notas_sala = st.text_area("Notas (opcional)", key="notas_sala")
            
            submitted = st.form_submit_button("Registrar Sala")
            
            if submitted:
                if nombre_sala and centro_sala and centro_sala != "[Seleccione un centro]":
                    try:
                        sala_id, es_nueva = sistema.registrar_sala(
                            nombre_sala, centro_id, None, tipo_equipo
                        )
                        
                        if es_nueva:
                            st.success(f"Sala '{nombre_sala}' registrada con éxito en {centro_sala}!")
                        else:
                            st.info(f"La sala '{nombre_sala}' ya existía. Se actualizaron sus datos.")
                        
                        # Recargar la página para mostrar cambios
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error al registrar sala: {e}")
                else:
                    if not nombre_sala:
                        st.warning("El nombre de la sala es obligatorio")
                    if not centro_sala or centro_sala == "[Seleccione un centro]":
                        st.warning("Debe seleccionar un centro médico")

# Iniciar la clase CodigosExamenes con método para conectar a la DB
# Asegurar que existe el directorio y la base de datos
import os
from codigo_examenes import REGISTROS_DIR, DB_FILE

# Asegurar que el directorio existe
if not os.path.exists(REGISTROS_DIR):
    os.makedirs(REGISTROS_DIR)

# Verificar si la base de datos existe, si no, inicializarla
if not os.path.exists(DB_FILE):
    sistema.inicializar_db()

# Método de conexión para Streamlit
def conectar_db():
    return sqlite3.connect(DB_FILE)


# Función principal
if __name__ == "__main__":
    # Se ejecuta al iniciar la aplicación
    pass