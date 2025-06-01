#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integración de Asistente phi-2 con Streamlit
--------------------------------------------
Interfaz de usuario para el asistente basado en phi-2
"""

import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import time
import tempfile

# Agregar el directorio raíz al path para importar módulos
RAIZ_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if RAIZ_DIR not in sys.path:
    sys.path.insert(0, RAIZ_DIR)

from asistente_phi2 import AsistentePhi2

# Configuración de la página
st.set_page_config(
    page_title="Asistente de Análisis con phi-2",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos personalizados
st.markdown("""
<style>
    .reportview-container {
        background-color: #f5f7f9;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
    }
    .stTextInput > div > div > input {
        border-radius: 8px;
    }
    .model-info {
        border-left: 3px solid #4CAF50;
        padding-left: 10px;
        margin: 15px 0;
    }
    .code-block {
        background-color: #f5f5f5;
        border-radius: 5px;
        padding: 10px;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar estado de la sesión
if 'asistente' not in st.session_state:
    st.session_state.asistente = AsistentePhi2()
    st.session_state.historial = []
    st.session_state.db_cargada = False
    st.session_state.db_ruta = None
    st.session_state.mostrar_sql = False
    
    # Intentar conectar automáticamente a la base de datos de conocimiento
    default_db_path = "/app/conocimiento/conocimiento.db" if os.path.exists("/app") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "conocimiento", "conocimiento.db")
    
    if os.path.exists(default_db_path):
        try:
            if st.session_state.asistente._conectar_db(default_db_path):
                st.session_state.db_cargada = True
                st.session_state.db_ruta = default_db_path
        except:
            pass  # Silenciosamente continuar si falla

def main():
    """Función principal de la aplicación Streamlit"""
    st.title("Asistente de Análisis con phi-2")
    
    # Verificar el estado de instalación de Ollama y phi-2
    estado = st.session_state.asistente.verificar_instalacion()
    
    # Mostrar información sobre phi-2
    with st.sidebar:
        st.header("Acerca de phi-2")
        
        st.markdown("""
        <div class="model-info">
        <h4>phi-2</h4>
        <p>Modelo liviano (1.7B parámetros) desarrollado por Microsoft.</p>
        <ul>
            <li>Ultra rápido en CPU</li>
            <li>Excelente para tareas estructuradas</li>
            <li>Ideal para consultas SQL</li>
            <li>Optimizado para bajo consumo de recursos</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Estado de instalación
        st.subheader("Estado del sistema")
        if estado["ollama_instalado"]:
            st.success("✅ Ollama instalado")
        else:
            st.error("❌ Ollama no instalado")
            if st.button("Instalar Ollama"):
                with st.spinner("Instalando Ollama..."):
                    exito = st.session_state.asistente.instalar_ollama()
                    if exito:
                        st.success("Ollama instalado correctamente")
                        st.rerun()
                    else:
                        st.error("No se pudo instalar Ollama automáticamente")
                        st.markdown("""
                        Para instalar manualmente:
                        ```bash
                        # macOS
                        brew install ollama
                        
                        # Linux
                        curl -fsSL https://ollama.com/install.sh | sh
                        ```
                        """)
        
        if estado["ollama_ejecutando"]:
            st.success("✅ Ollama en ejecución")
        else:
            st.error("❌ Ollama no está ejecutándose")
            if st.button("Iniciar Ollama"):
                with st.spinner("Iniciando Ollama..."):
                    try:
                        import subprocess
                        subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        time.sleep(5)  # Esperar a que inicie
                        st.success("Ollama iniciado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al iniciar Ollama: {e}")
        
        if estado["modelo_phi2_disponible"]:
            st.success("✅ Modelo phi-2 disponible")
        else:
            st.error("❌ Modelo phi-2 no disponible")
            if st.button("Descargar phi-2"):
                with st.spinner("Descargando modelo phi-2..."):
                    try:
                        import subprocess
                        subprocess.run(["ollama", "pull", "phi"], check=True)
                        st.success("Modelo phi-2 descargado correctamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al descargar phi-2: {e}")
        
        st.divider()
        
        # Opciones para cargar datos
        st.subheader("Cargar datos")
        opcion_carga = st.radio("Seleccione una fuente de datos:", 
                              ["Base de datos SQLite existente", "CSV de Radiología", "Sin datos"])
        
        if opcion_carga == "CSV de Radiología":
            uploaded_file = st.file_uploader("Seleccione archivo CSV", type=['csv'])
            if uploaded_file is not None:
                with st.spinner("Cargando y procesando datos..."):
                    # Guardar el archivo en un directorio temporal
                    temp_dir = tempfile.mkdtemp()
                    temp_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(temp_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Cargar el CSV en un DataFrame
                    df = pd.read_csv(temp_path)
                    
                    # Crear base de datos SQLite temporal
                    db_path = st.session_state.asistente.crear_base_datos_temporal(df, "examenes")
                    
                    if db_path:
                        st.session_state.db_cargada = True
                        st.session_state.db_ruta = db_path
                        st.success(f"Datos cargados exitosamente. Se encontraron {len(df)} registros.")
        
        elif opcion_carga == "Base de datos SQLite existente":
            # Ruta predeterminada a la base de datos de conocimiento
            default_db_path = "/app/conocimiento/conocimiento.db" if os.path.exists("/app") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "conocimiento", "conocimiento.db")
            
            db_path = st.text_input("Ruta a la base de datos SQLite:", 
                                  value=st.session_state.get('db_ruta', default_db_path))
            
            # Mensaje de ayuda
            st.info("La base de datos contiene el conocimiento de procedimientos, salas y patrones aprendidos.")
            
            if db_path and os.path.exists(db_path):
                if st.button("Conectar"):
                    with st.spinner("Conectando a la base de datos..."):
                        exito = st.session_state.asistente._conectar_db(db_path)
                        if exito:
                            st.session_state.db_cargada = True
                            st.session_state.db_ruta = db_path
                            st.success("Conexión exitosa a la base de datos")
                            
                            # Obtener estadísticas básicas
                            try:
                                cursor = st.session_state.asistente.conexion_db.cursor()
                                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                                tablas = [row[0] for row in cursor.fetchall()]
                                st.write(f"Tablas disponibles: {', '.join(tablas)}")
                            except:
                                pass
                        else:
                            st.error("Error al conectar a la base de datos")
            elif db_path:
                st.error("La ruta especificada no existe")
        
        # Opción para mostrar SQL generado
        st.subheader("Opciones avanzadas")
        st.session_state.mostrar_sql = st.checkbox("Mostrar SQL generado", 
                                                value=st.session_state.get('mostrar_sql', False))
    
    # Contenido principal
    tab_consulta, tab_analisis, tab_ayuda = st.tabs(["Consultas", "Análisis", "Ayuda"])
    
    # Pestaña de consultas
    with tab_consulta:
        st.header("Consultas en lenguaje natural")
        
        # Campo de entrada para la consulta
        pregunta = st.text_input("Haz una pregunta sobre los datos:",
                              placeholder="Ej: ¿Cuántos exámenes TAC hay en total?")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Consultar", disabled=not estado["ollama_ejecutando"] or not st.session_state.db_cargada):
                if not pregunta:
                    st.warning("Por favor, ingresa una pregunta")
                else:
                    with st.spinner("Procesando consulta..."):
                        # Realizar consulta en lenguaje natural
                        exito, resultado = st.session_state.asistente.consulta_natural(pregunta)
                        
                        # Guardar en historial
                        st.session_state.historial.append({
                            "pregunta": pregunta,
                            "exito": exito,
                            "resultado": resultado,
                            "tipo": "consulta"
                        })
                        
                        # Mostrar resultados
                        if exito and isinstance(resultado, pd.DataFrame):
                            st.success("Consulta ejecutada correctamente")
                            st.dataframe(resultado)
                            
                            # Crear gráfico automático si es apropiado
                            if len(resultado) > 0 and len(resultado) <= 100:
                                if "count" in resultado.columns or any("count" in col.lower() for col in resultado.columns):
                                    col_count = next((col for col in resultado.columns if "count" in col.lower()), None)
                                    col_categoria = next((col for col in resultado.columns if col != col_count), None)
                                    
                                    if col_count and col_categoria and len(resultado) <= 10:
                                        st.bar_chart(resultado.set_index(col_categoria))
                        else:
                            st.error(f"Error: {resultado}")
        
        with col2:
            if st.button("Generar respuesta", disabled=not estado["ollama_ejecutando"]):
                if not pregunta:
                    st.warning("Por favor, ingresa una pregunta")
                else:
                    with st.spinner("Generando respuesta..."):
                        # Generar respuesta con phi-2
                        respuesta = st.session_state.asistente.generar_respuesta(pregunta)
                        
                        # Guardar en historial
                        st.session_state.historial.append({
                            "pregunta": pregunta,
                            "resultado": respuesta,
                            "tipo": "respuesta"
                        })
                        
                        # Mostrar respuesta
                        st.info(respuesta)
        
        # Mostrar SQL generado si está activada la opción
        if st.session_state.mostrar_sql and st.session_state.historial:
            ultimo_item = st.session_state.historial[-1]
            if ultimo_item["tipo"] == "consulta" and not ultimo_item["exito"] and isinstance(ultimo_item["resultado"], str):
                consulta_sql = ultimo_item["resultado"].split("Consulta generada: ")[-1] if "Consulta generada: " in ultimo_item["resultado"] else ""
                if consulta_sql:
                    st.markdown("### SQL Generado")
                    st.code(consulta_sql, language="sql")
        
        # Historial de consultas
        if st.session_state.historial:
            with st.expander("Historial de consultas", expanded=False):
                for i, item in enumerate(reversed(st.session_state.historial[-10:])):  # Mostrar solo las últimas 10
                    st.markdown(f"**Pregunta {len(st.session_state.historial)-i}:** {item['pregunta']}")
                    
                    if item["tipo"] == "consulta":
                        if item["exito"] and isinstance(item["resultado"], pd.DataFrame):
                            st.dataframe(item["resultado"], height=150)
                        else:
                            st.error(item["resultado"])
                    else:
                        st.info(item["resultado"])
                    
                    st.divider()
    
    # Pestaña de análisis
    with tab_analisis:
        st.header("Análisis de datos")
        
        if not st.session_state.db_cargada:
            st.info("Carga datos primero para ver análisis")
        else:
            # Mostrar estadísticas básicas si hay datos cargados
            try:
                exito, df_stats = st.session_state.asistente.ejecutar_consulta_sql(
                    "SELECT COUNT(*) as total_examenes FROM examenes"
                )
                
                if exito and isinstance(df_stats, pd.DataFrame) and not df_stats.empty:
                    total_examenes = df_stats.iloc[0]['total_examenes']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total de exámenes", f"{total_examenes:,}")
                    
                    # Intentar obtener tipos de exámenes
                    try:
                        exito, df_tipos = st.session_state.asistente.ejecutar_consulta_sql(
                            "SELECT Tipo, COUNT(*) as cantidad FROM examenes GROUP BY Tipo"
                        )
                        
                        if exito and isinstance(df_tipos, pd.DataFrame) and not df_tipos.empty:
                            for i, row in df_tipos.iterrows():
                                with col2 if i % 2 == 0 else col3:
                                    st.metric(f"Exámenes {row['Tipo']}", f"{row['cantidad']:,}")
                    except:
                        pass
            except:
                st.error("No se pudieron cargar estadísticas básicas")
            
            # Análisis automático con phi-2
            if st.button("Generar análisis automático", disabled=not estado["ollama_ejecutando"]):
                with st.spinner("Analizando datos con phi-2..."):
                    prompt = """
                    Analiza estos datos de exámenes radiológicos y proporciona un breve resumen con:
                    1. Distribución de exámenes por tipo
                    2. Patrones temporales si existen
                    3. Cualquier observación relevante
                    Sé conciso y enfócate en los datos más importantes.
                    """
                    
                    analisis = st.session_state.asistente.generar_respuesta(prompt)
                    st.info(analisis)
    
    # Pestaña de ayuda
    with tab_ayuda:
        st.header("Ayuda y ejemplos")
        
        st.markdown("""
        ### ¿Qué es este asistente?
        
        Este asistente utiliza el modelo de lenguaje **phi-2** de Microsoft para permitirte consultar 
        y analizar datos radiológicos usando lenguaje natural.
        
        ### Preguntas de ejemplo:
        
        - ¿Cuántos exámenes de cada tipo hay en total?
        - ¿Cuáles son los procedimientos más comunes?
        - Muestra la distribución de exámenes por día
        - ¿Cuántos TAC dobles hay?
        - Resume la distribución de exámenes por sala
        
        ### Cómo funciona:
        
        1. El asistente convierte tu pregunta en una consulta SQL
        2. Ejecuta la consulta en la base de datos
        3. Te muestra los resultados y, cuando es apropiado, gráficos visuales
        
        ### Requisitos:
        
        - **Ollama**: Motor para ejecutar modelos de IA localmente
        - **phi-2**: Modelo de lenguaje pequeño y eficiente
        
        ### Tips:
        
        - Sé específico en tus preguntas
        - Para preguntas complejas, divídelas en partes más pequeñas
        - Activa "Mostrar SQL generado" para ver cómo el sistema interpreta tus preguntas
        """)
        
        st.info("El modelo phi-2 es rápido y eficiente, pero tiene limitaciones. Para análisis muy complejos, considera modelos más grandes como Mixtral o LLaMA 3 8B.")

if __name__ == "__main__":
    main()