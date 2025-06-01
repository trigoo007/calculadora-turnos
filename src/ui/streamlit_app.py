"""
Aplicación principal de Streamlit para la Calculadora de Turnos.

Esta es la interfaz de usuario principal que integra todos los módulos
del sistema para proporcionar una experiencia completa de cálculo de turnos.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import base64
from io import BytesIO
import logging
from typing import Dict, List, Optional
import numpy as np

# Importar módulos del sistema
from src.core.data_processing import DataProcessor
from src.core.exam_classification import ExamClassifier
from src.core.turno_calculator import TurnoCalculator
from src.core.report_generator import ReportGenerator
from src.db.sqlite_manager import get_db_manager
from config.settings import UI_CONFIG, get_config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_session_state():
    """Inicializa las variables de estado de la sesión."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.data_processor = DataProcessor()
        st.session_state.exam_classifier = ExamClassifier()
        st.session_state.turno_calculator = TurnoCalculator()
        st.session_state.report_generator = ReportGenerator()
        st.session_state.db_manager = get_db_manager()
        
        # Estado del proceso
        st.session_state.file_loaded = False
        st.session_state.data_processed = False
        st.session_state.exams_classified = False
        st.session_state.turnos_calculated = False
        
        # Datos
        st.session_state.df_original = None
        st.session_state.df_processed = None
        st.session_state.df_classified = None
        st.session_state.resultado_economico = None
        st.session_state.fechas_turno = []


def generate_download_link(df: pd.DataFrame, filename: str) -> str:
    """Genera un enlace de descarga para un DataFrame."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">📥 Descargar {filename}</a>'


def main():
    """Función principal de la aplicación."""
    # Configurar página
    try:
        st.set_page_config(
            page_title=UI_CONFIG["title"],
            page_icon=UI_CONFIG["page_icon"],
            layout=UI_CONFIG["layout"],
            initial_sidebar_state=UI_CONFIG["initial_sidebar_state"]
        )
    except Exception as e:
        logger.warning(f"Error configurando página: {e}")
        # Configuración básica si falla
        st.set_page_config(
            page_title="Calculadora de Turnos",
            layout="wide"
        )
    
    # Inicializar estado
    init_session_state()
    
    # CSS personalizado simplificado
    try:
        st.markdown("""
        <style>
        .main-header {
            text-align: center;
            padding: 2rem 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        
        .main-header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
        }
        
        .main-header p {
            font-size: 1.1rem;
            margin-top: 0.5rem;
            opacity: 0.9;
        }
        </style>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.warning(f"Error aplicando CSS: {e}")
    
    # Encabezado
    try:
        st.markdown("""
        <div class="main-header">
            <h1>📊 Calculadora de Turnos en Radiología</h1>
            <p>Sistema inteligente de procesamiento y análisis de procedimientos médicos</p>
        </div>
        """, unsafe_allow_html=True)
    except:
        # Encabezado simple si falla el HTML
        st.title("📊 Calculadora de Turnos en Radiología")
        st.subheader("Sistema inteligente de procesamiento y análisis de procedimientos médicos")
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Panel de Control")
        
        # Estado del proceso
        st.subheader("Estado del Proceso")
        
        if st.session_state.file_loaded:
            st.success("✅ Archivo cargado")
        else:
            st.info("⏳ Esperando archivo...")
        
        if st.session_state.data_processed:
            st.success("✅ Datos procesados")
        
        if st.session_state.exams_classified:
            st.success("✅ Exámenes clasificados")
        
        if st.session_state.turnos_calculated:
            st.success("✅ Turnos calculados")
        
        # Estadísticas de la base de datos
        if st.button("📊 Ver estadísticas del sistema"):
            try:
                stats = st.session_state.db_manager.obtener_estadisticas()
                # Mostrar estadísticas de forma más simple
                st.write("**Estadísticas del Sistema:**")
                st.write(f"- Total procedimientos: {stats.get('procedimientos', {}).get('total', 0)}")
                st.write(f"- Total salas: {stats.get('salas', {}).get('total', 0)}")
                st.write(f"- Exámenes históricos: {stats.get('historico_examenes', 0)}")
            except Exception as e:
                logger.warning(f"Error obteniendo estadísticas: {e}")
                st.warning("No se pudieron cargar las estadísticas")
        
        st.markdown("---")
        
        # Información
        st.markdown("""
        ### ℹ️ Información
        
        **Versión:** 1.0.0  
        **Última actualización:** Diciembre 2024
        
        Sistema desarrollado para automatizar el cálculo de turnos
        y honorarios en servicios de radiología.
        """)
    
    # Contenido principal
    if not st.session_state.file_loaded:
        # Sección de configuración de turnos ANTES de cargar archivo
        st.header("📅 Configuración de Turnos del Mes")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Ingrese los días de turno trabajados")
            
            # Selector de mes y año
            mes_col, año_col = st.columns(2)
            with mes_col:
                mes_actual = datetime.now().month
                mes_seleccionado = st.selectbox(
                    "Mes",
                    range(1, 13),
                    index=mes_actual - 1,
                    format_func=lambda x: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                                         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'][x-1]
                )
            
            with año_col:
                año_actual = datetime.now().year
                año_seleccionado = st.number_input("Año", min_value=2020, max_value=2030, value=año_actual)
            
            # Entrada de fechas de turno
            st.write("**Seleccione las fechas de turno:**")
            
            # Calendario simple para seleccionar fechas
            fecha_turno = st.date_input(
                "Agregar fecha de turno",
                value=datetime.now().date(),
                min_value=datetime(año_seleccionado, mes_seleccionado, 1).date(),
                max_value=datetime(año_seleccionado, mes_seleccionado, 28).date()
            )
            
            col_add, col_clear = st.columns([1, 1])
            with col_add:
                if st.button("➕ Agregar fecha", type="primary"):
                    if fecha_turno not in [f for f, _ in st.session_state.fechas_turno]:
                        st.session_state.fechas_turno.append((fecha_turno, False))
                        st.success(f"Fecha {fecha_turno} agregada")
            
            with col_clear:
                if st.button("🗑️ Limpiar todas"):
                    st.session_state.fechas_turno = []
                    st.rerun()
        
        with col2:
            st.subheader("📊 Resumen de Turnos")
            
            if st.session_state.fechas_turno:
                # Mostrar fechas seleccionadas
                st.write(f"**Total de días:** {len(st.session_state.fechas_turno)}")
                
                # Calcular horas estimadas (8 horas por turno)
                horas_totales = len(st.session_state.fechas_turno) * 8
                st.metric("Horas estimadas", f"{horas_totales} hrs")
                
                # Mostrar lista de fechas
                st.write("**Fechas seleccionadas:**")
                for fecha, _ in sorted(st.session_state.fechas_turno):
                    st.write(f"• {fecha.strftime('%d/%m/%Y')} - {fecha.strftime('%A')}")
            else:
                st.info("No hay fechas de turno seleccionadas")
        
        st.markdown("---")
        
        # Sección de carga de archivo
        st.header("📁 Cargar Archivo de Datos")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Seleccione un archivo CSV o Excel con los datos de procedimientos",
                type=['csv', 'xlsx', 'xls'],
                help="El archivo debe contener columnas como: Fecha, Procedimiento, Paciente, Sala"
            )
        
        with col2:
            st.markdown("### 📋 Formato esperado")
            st.markdown("""
            - Fecha del procedimiento
            - Nombre del procedimiento
            - Paciente
            - Sala de adquisición
            """)
        
        if uploaded_file is not None:
            with st.spinner("Procesando archivo..."):
                # Guardar archivo temporalmente
                temp_path = Path(tempfile.mkdtemp()) / uploaded_file.name
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                try:
                    # Procesar archivo
                    stats = st.session_state.data_processor.process_file(temp_path)
                    
                    # Cargar datos procesados
                    if temp_path.suffix.lower() == '.csv':
                        st.session_state.df_original = pd.read_csv(temp_path)
                    else:
                        st.session_state.df_original = pd.read_excel(temp_path)
                    
                    st.session_state.file_loaded = True
                    st.success(f"✅ Archivo cargado exitosamente: {stats['valid_rows']} registros válidos (solo SCA/SJ)")
                    
                    # Mostrar estadísticas
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total de registros", stats['total_rows'])
                    with col2:
                        st.metric("Registros SCA/SJ", stats['valid_rows'], delta=f"{stats['valid_rows']}", delta_color="normal")
                    with col3:
                        st.metric("Otros centros", stats['invalid_rows'], delta=f"-{stats['invalid_rows']}", delta_color="inverse")
                    with col4:
                        porcentaje_validos = (stats['valid_rows'] / stats['total_rows'] * 100) if stats['total_rows'] > 0 else 0
                        st.metric("% SCA/SJ", f"{porcentaje_validos:.1f}%")
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error al procesar el archivo: {str(e)}")
    
    else:
        # Crear pestañas para las diferentes funcionalidades
        tabs = st.tabs(["📊 Datos", "🔍 Análisis", "💰 Cálculo de Turnos", "📄 Reportes"])
        
        # Tab 1: Visualización de datos
        with tabs[0]:
            st.header("📊 Visualización de Datos")
            
            if st.session_state.df_original is not None:
                # Procesar y clasificar datos si no se ha hecho
                if not st.session_state.data_processed:
                    with st.spinner("Procesando datos..."):
                        # Detectar columnas
                        column_mapping = st.session_state.data_processor.detect_columns(
                            st.session_state.df_original
                        )
                        
                        # Limpiar datos
                        df_cleaned = st.session_state.data_processor.clean_data(
                            st.session_state.df_original, column_mapping
                        )
                        
                        # Validar datos - ESTO FILTRA SOLO SCA/SJ
                        df_valid, df_invalid = st.session_state.data_processor.validate_data(df_cleaned)
                        
                        # USAR SOLO LOS DATOS VÁLIDOS (SCA/SJ)
                        st.session_state.df_processed = df_valid
                        
                        # Guardar también los inválidos para referencia
                        st.session_state.df_invalid = df_invalid
                        
                        st.session_state.data_processed = True
                        
                        # Mostrar información del filtrado
                        if len(df_invalid) > 0:
                            st.info(f"ℹ️ Se filtraron {len(df_invalid)} registros que no son de SCA o SJ")
                
                # Mostrar datos procesados
                st.subheader("Datos Procesados")
                
                # Filtros
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    search_term = st.text_input("🔍 Buscar", placeholder="Nombre, procedimiento...")
                
                with col2:
                    if 'centro' in st.session_state.df_processed.columns:
                        try:
                            # Obtener centros únicos, excluyendo NaN
                            centros_unicos = st.session_state.df_processed['centro'].dropna().unique().tolist()
                            centros = ['Todos'] + sorted(centros_unicos)
                            centro_filter = st.selectbox("🏥 Centro", centros)
                        except Exception as e:
                            logger.warning(f"Error al crear filtro de centros: {e}")
                            centro_filter = 'Todos'
                
                with col3:
                    if 'fecha' in st.session_state.df_processed.columns:
                        try:
                            # Filtrar fechas válidas
                            fechas_validas = st.session_state.df_processed['fecha'].dropna()
                            if len(fechas_validas) > 0:
                                fecha_min = fechas_validas.min()
                                fecha_max = fechas_validas.max()
                                
                                # Verificar que las fechas sean válidas
                                if pd.notna(fecha_min) and pd.notna(fecha_max):
                                    fecha_filter = st.date_input(
                                        "📅 Rango de fechas",
                                        value=(fecha_min.date() if hasattr(fecha_min, 'date') else fecha_min, 
                                               fecha_max.date() if hasattr(fecha_max, 'date') else fecha_max),
                                        min_value=fecha_min.date() if hasattr(fecha_min, 'date') else fecha_min,
                                        max_value=fecha_max.date() if hasattr(fecha_max, 'date') else fecha_max
                                    )
                                else:
                                    st.warning("No se encontraron fechas válidas en los datos")
                            else:
                                st.warning("No hay fechas disponibles para filtrar")
                        except Exception as e:
                            logger.warning(f"Error al crear filtro de fechas: {e}")
                            st.warning("No se pudo crear el filtro de fechas")
                
                # Aplicar filtros
                df_filtered = st.session_state.df_processed.copy()
                
                if search_term:
                    mask = pd.Series(False, index=df_filtered.index)
                    for col in df_filtered.columns:
                        if df_filtered[col].dtype == 'object':
                            try:
                                mask |= df_filtered[col].astype(str).str.contains(search_term, case=False, na=False)
                            except:
                                pass
                    df_filtered = df_filtered[mask]
                
                if 'centro' in locals() and centro_filter != 'Todos':
                    df_filtered = df_filtered[df_filtered['centro'] == centro_filter]
                
                if 'fecha_filter' in locals() and len(fecha_filter) == 2:
                    try:
                        df_filtered = df_filtered[
                            (df_filtered['fecha'] >= pd.Timestamp(fecha_filter[0])) &
                            (df_filtered['fecha'] <= pd.Timestamp(fecha_filter[1]))
                        ]
                    except Exception as e:
                        logger.warning(f"Error al aplicar filtro de fechas: {e}")
                
                # Mostrar resultados
                st.info(f"Mostrando {len(df_filtered)} de {len(st.session_state.df_processed)} registros")
                st.dataframe(df_filtered, use_container_width=True)
                
                # Botón de descarga
                if st.button("📥 Descargar datos filtrados"):
                    st.markdown(
                        generate_download_link(df_filtered, "datos_filtrados.xlsx"),
                        unsafe_allow_html=True
                    )
        
        # Tab 2: Análisis de exámenes
        with tabs[1]:
            st.header("🔍 Análisis de Exámenes")
            
            if st.session_state.data_processed and st.session_state.df_processed is not None:
                if not st.session_state.exams_classified:
                    if st.button("🚀 Clasificar Exámenes", type="primary"):
                        with st.spinner("Clasificando exámenes..."):
                            # Clasificar cada examen
                            classifications = []
                            
                            for _, row in st.session_state.df_processed.iterrows():
                                if 'procedimiento' in row:
                                    classification = st.session_state.exam_classifier.classify_exam(
                                        row['procedimiento']
                                    )
                                    classifications.append(classification)
                                    
                                    # Registrar en base de datos - COMENTADO TEMPORALMENTE
                                    # try:
                                    #     st.session_state.db_manager.registrar_procedimiento(
                                    #         nombre=row['procedimiento'],
                                    #         tipo=classification['type'],
                                    #         subtipo=classification['subtype'],
                                    #         codigo=classification['code'],
                                    #         complejidad=classification['complexity'],
                                    #         tiempo_estimado=classification['estimated_time']
                                    #     )
                                    # except Exception as e:
                                    #     logger.warning(f"No se pudo registrar procedimiento: {e}")
                            
                            # Agregar clasificaciones al DataFrame
                            if classifications:
                                df_classifications = pd.DataFrame(classifications)
                                st.session_state.df_classified = pd.concat([
                                    st.session_state.df_processed,
                                    df_classifications
                                ], axis=1)
                            else:
                                st.session_state.df_classified = st.session_state.df_processed.copy()
                            
                            st.session_state.exams_classified = True
                            st.success("✅ Exámenes clasificados exitosamente")
                            st.rerun()
                
                else:
                    # Mostrar análisis
                    st.subheader("📊 Resumen de Clasificación")
                    
                    # Métricas principales
                    col1, col2, col3, col4 = st.columns(4)
                    
                    total_exams = len(st.session_state.df_classified)
                    
                    # Contar por tipo de examen de forma segura
                    if 'type' in st.session_state.df_classified.columns:
                        rx_count = len(st.session_state.df_classified[
                            st.session_state.df_classified['type'] == 'RX'
                        ])
                        tac_count = len(st.session_state.df_classified[
                            st.session_state.df_classified['type'] == 'TAC'
                        ])
                    else:
                        rx_count = 0
                        tac_count = 0
                    
                    otros_count = total_exams - rx_count - tac_count
                    
                    with col1:
                        st.metric("Total Exámenes", total_exams)
                    with col2:
                        st.metric("RX", rx_count)
                    with col3:
                        st.metric("TAC", tac_count)
                    with col4:
                        st.metric("Otros", otros_count)
                    
                    # Detalles de TAC
                    if 'is_tac_double' in st.session_state.df_classified.columns:
                        st.subheader("🔬 Análisis Detallado de TAC")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        # Calcular TAC simple, doble y triple de forma segura
                        if 'is_tac_triple' in st.session_state.df_classified.columns:
                            # Crear máscaras booleanas seguras
                            mask_tac = st.session_state.df_classified['type'] == 'TAC'
                            mask_not_double = ~st.session_state.df_classified['is_tac_double'].fillna(False)
                            mask_not_triple = ~st.session_state.df_classified['is_tac_triple'].fillna(False)
                            
                            tac_simple = len(st.session_state.df_classified[
                                mask_tac & mask_not_double & mask_not_triple
                            ])
                            
                            tac_triple = len(st.session_state.df_classified[
                                st.session_state.df_classified['is_tac_triple'].fillna(False) == True
                            ])
                        else:
                            # Solo TAC doble existe
                            mask_tac = st.session_state.df_classified['type'] == 'TAC'
                            mask_not_double = ~st.session_state.df_classified['is_tac_double'].fillna(False)
                            
                            tac_simple = len(st.session_state.df_classified[
                                mask_tac & mask_not_double
                            ])
                            tac_triple = 0
                        
                        tac_double = len(st.session_state.df_classified[
                            st.session_state.df_classified['is_tac_double'].fillna(False) == True
                        ])
                        
                        with col1:
                            st.metric("TAC Simple", tac_simple)
                        with col2:
                            st.metric("TAC Doble", tac_double)
                        with col3:
                            st.metric("TAC Triple", tac_triple)
                    
                    # NUEVA SECCIÓN: Estimación de días de turno
                    st.subheader("📅 Estimación de Días de Turno")
                    
                    if 'estimated_time' in st.session_state.df_classified.columns:
                        # Calcular tiempo total estimado
                        tiempo_total_minutos = st.session_state.df_classified['estimated_time'].sum()
                        tiempo_total_horas = tiempo_total_minutos / 60
                        
                        # Estimar días necesarios (8 horas por día)
                        dias_estimados = int(np.ceil(tiempo_total_horas / 8))
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Tiempo Total", f"{tiempo_total_horas:.1f} hrs")
                        with col2:
                            st.metric("Días Estimados (8h/día)", dias_estimados)
                        with col3:
                            promedio_por_examen = tiempo_total_minutos / total_exams if total_exams > 0 else 0
                            st.metric("Promedio por Examen", f"{promedio_por_examen:.1f} min")
                        
                        # Sugerencia de fechas
                        st.info(f"""
                        💡 **Sugerencia**: Basado en el análisis, necesitarás aproximadamente **{dias_estimados} días** 
                        de turno para completar todos los exámenes. Considera agregar estas fechas en la pestaña 
                        'Cálculo de Turnos'.
                        """)
                    
                    # Tabla de exámenes clasificados
                    st.subheader("📋 Detalle de Exámenes Clasificados")
                    
                    # Seleccionar columnas relevantes
                    columns_to_show = ['fecha', 'paciente', 'procedimiento', 'type', 
                                      'subtype', 'complexity', 'estimated_time']
                    available_columns = [col for col in columns_to_show 
                                       if col in st.session_state.df_classified.columns]
                    
                    df_show = st.session_state.df_classified[available_columns].copy()
                    
                    # Renombrar columnas para mejor visualización
                    rename_dict = {
                        'type': 'Tipo',
                        'subtype': 'Subtipo',
                        'complexity': 'Complejidad',
                        'estimated_time': 'Tiempo Est. (min)'
                    }
                    df_show.rename(columns=rename_dict, inplace=True)
                    
                    st.dataframe(df_show, use_container_width=True)
        
        # Tab 3: Cálculo de turnos
        with tabs[2]:
            st.header("💰 Cálculo de Turnos y Honorarios")
            
            if st.session_state.exams_classified and st.session_state.fechas_turno:
                # Mostrar fechas de turno ya seleccionadas
                st.subheader("📅 Fechas de Turno Seleccionadas")
                
                fechas_df = pd.DataFrame(
                    st.session_state.fechas_turno,
                    columns=['Fecha', 'Es Feriado']
                )
                fechas_df['Día'] = pd.to_datetime(fechas_df['Fecha']).dt.day_name()
                fechas_df['Día (ES)'] = pd.to_datetime(fechas_df['Fecha']).dt.day_name().map({
                    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
                })
                
                # Calcular horas por día según el día de la semana
                def calcular_horas_dia(row):
                    dia = row['Día']
                    if dia in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                        return 8  # Lunes a Viernes: 8 horas
                    elif dia == 'Saturday':
                        return 5  # Sábado: 5 horas
                    else:
                        return 0  # Domingo: sin turno regular
                
                fechas_df['Horas'] = fechas_df.apply(calcular_horas_dia, axis=1)
                
                # Mostrar tabla con horas
                st.dataframe(
                    fechas_df[['Fecha', 'Día (ES)', 'Horas']],
                    use_container_width=True,
                    hide_index=True
                )
                
                # Resumen de horas
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_dias = len(fechas_df)
                    st.metric("Total de días", total_dias)
                with col2:
                    total_horas = fechas_df['Horas'].sum()
                    st.metric("Total de horas", f"{total_horas} hrs")
                with col3:
                    honorarios_hora = total_horas * 55000
                    st.metric("Honorarios por hora", f"${honorarios_hora:,.0f}")
                
                # Calcular turnos
                if st.button("💵 Calcular Honorarios Totales", type="primary"):
                    with st.spinner("Calculando turnos y honorarios..."):
                        # Preparar fechas
                        fechas = [datetime.combine(f, datetime.min.time()) 
                                 for f, _ in st.session_state.fechas_turno]
                        
                        # Calcular
                        st.session_state.resultado_economico = st.session_state.turno_calculator.calcular_turnos(
                            st.session_state.df_classified,
                            fechas
                        )
                        
                        # Actualizar con las horas reales calculadas
                        st.session_state.resultado_economico['horas_trabajadas'] = total_horas
                        st.session_state.resultado_economico['honorarios_hora'] = honorarios_hora
                        
                        st.session_state.turnos_calculated = True
                        st.success("✅ Cálculo completado")
                
                # Mostrar resultados
                if st.session_state.turnos_calculated and st.session_state.resultado_economico:
                    st.subheader("💰 Resumen de Honorarios")
                    
                    resultado = st.session_state.resultado_economico
                    
                    # Métricas principales
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Horas Trabajadas",
                            f"{resultado['horas_trabajadas']} hrs",
                            f"${resultado['honorarios_hora']:,.0f}"
                        )
                    
                    with col2:
                        total_examenes = (
                            resultado['rx_count'] + 
                            resultado['tac_count'] + 
                            resultado['tac_doble_count'] + 
                            resultado['tac_triple_count']
                        )
                        st.metric("Total Exámenes", total_examenes)
                    
                    with col3:
                        st.metric(
                            "TOTAL A PAGAR",
                            f"${resultado['total']:,.0f}",
                            delta=None,
                            delta_color="normal"
                        )
                    
                    # Desglose detallado
                    st.subheader("📊 Desglose Detallado")
                    
                    desglose_data = {
                        'Concepto': [
                            'Horas trabajadas',
                            'Exámenes RX',
                            'Exámenes TAC simple',
                            'Exámenes TAC doble',
                            'Exámenes TAC triple'
                        ],
                        'Cantidad': [
                            resultado['horas_trabajadas'],
                            resultado['rx_count'],
                            resultado['tac_count'],
                            resultado['tac_doble_count'],
                            resultado['tac_triple_count']
                        ],
                        'Tarifa Unitaria': [
                            '$55,000',
                            '$5,300',
                            '$42,300',
                            '$84,600',
                            '$126,900'
                        ],
                        'Subtotal': [
                            f"${resultado['honorarios_hora']:,.0f}",
                            f"${resultado['rx_total']:,.0f}",
                            f"${resultado['tac_total']:,.0f}",
                            f"${resultado['tac_doble_total']:,.0f}",
                            f"${resultado['tac_triple_total']:,.0f}"
                        ]
                    }
                    
                    df_desglose = pd.DataFrame(desglose_data)
                    st.dataframe(df_desglose, use_container_width=True, hide_index=True)
                    
                    # Gráficos
                    st.subheader("📈 Visualización de Datos")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Gráfico de distribución de exámenes
                        import plotly.express as px
                        
                        exam_dist = pd.DataFrame({
                            'Tipo': ['RX', 'TAC Simple', 'TAC Doble', 'TAC Triple'],
                            'Cantidad': [
                                resultado['rx_count'],
                                resultado['tac_count'],
                                resultado['tac_doble_count'],
                                resultado['tac_triple_count']
                            ]
                        })
                        
                        fig_pie = px.pie(
                            exam_dist, 
                            values='Cantidad', 
                            names='Tipo',
                            title='Distribución de Exámenes',
                            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with col2:
                        # Gráfico de ingresos por tipo
                        income_dist = pd.DataFrame({
                            'Concepto': ['Horas', 'RX', 'TAC Simple', 'TAC Doble', 'TAC Triple'],
                            'Monto': [
                                resultado['honorarios_hora'],
                                resultado['rx_total'],
                                resultado['tac_total'],
                                resultado['tac_doble_total'],
                                resultado['tac_triple_total']
                            ]
                        })
                        
                        fig_bar = px.bar(
                            income_dist,
                            x='Concepto',
                            y='Monto',
                            title='Ingresos por Concepto',
                            color='Concepto',
                            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57']
                        )
                        fig_bar.update_layout(showlegend=False)
                        fig_bar.update_yaxis(tickformat='$,.0f')
                        st.plotly_chart(fig_bar, use_container_width=True)
            
            elif not st.session_state.fechas_turno:
                st.warning("⚠️ Por favor, primero ingrese las fechas de turno en la pantalla inicial")
            else:
                st.info("ℹ️ Primero debe clasificar los exámenes en la pestaña 'Análisis'")
        
        # Tab 4: Reportes
        with tabs[3]:
            st.header("📄 Generación de Reportes")
            
            if st.session_state.turnos_calculated:
                col1, col2 = st.columns(2)
                
                with col1:
                    nombre_doctor = st.text_input(
                        "Nombre del Doctor",
                        value="Dr. Juan Pérez",
                        help="Ingrese el nombre del doctor para el reporte"
                    )
                
                with col2:
                    formato_reporte = st.selectbox(
                        "Formato de reporte",
                        ["Excel completo", "Resumen PDF", "Correo electrónico"]
                    )
                
                if st.button("📄 Generar Reporte", type="primary"):
                    with st.spinner("Generando reporte..."):
                        if formato_reporte == "Excel completo":
                            # Generar reporte Excel
                            output_path = st.session_state.report_generator.generar_reporte_completo(
                                st.session_state.df_classified,
                                st.session_state.resultado_economico,
                                nombre_doctor
                            )
                            
                            # Leer el archivo generado
                            with open(output_path, 'rb') as f:
                                excel_data = f.read()
                            
                            # Crear enlace de descarga
                            b64 = base64.b64encode(excel_data).decode()
                            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="Reporte_Turnos.xlsx">📥 Descargar Reporte Excel</a>'
                            st.markdown(href, unsafe_allow_html=True)
                            
                            st.success("✅ Reporte generado exitosamente")
                        
                        elif formato_reporte == "Correo electrónico":
                            # Generar contenido del correo
                            correo = st.session_state.report_generator.generar_correo(
                                st.session_state.resultado_economico,
                                nombre_doctor
                            )
                            
                            st.subheader("📧 Contenido del Correo")
                            st.text_area("", correo, height=400)
                            
                            if st.button("📋 Copiar al portapapeles"):
                                st.write("Contenido copiado al portapapeles")


if __name__ == "__main__":
    main() 