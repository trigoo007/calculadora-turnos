#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesador simple de archivos Excel para Sistema de Códigos de Exámenes
---------------------------------------------------------------
Aplicación autónoma para importar datos desde archivos Excel.
"""

import streamlit as st
import pandas as pd
import os
import tempfile
from datetime import datetime
import sqlite3
import hashlib
import re

# Configuración de la página
st.set_page_config(
    page_title="Procesador de Excel",
    page_icon="📊",
    layout="wide"
)

# Título principal
st.title("Procesador de Archivos Excel de Exámenes")

# Definir rutas de archivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "examenes.db")

# Crear directorio de datos si no existe
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Funciones para manipular la base de datos
def conectar_db():
    """Establece conexión con la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()

def crear_tablas():
    """Crea las tablas necesarias si no existen."""
    conn, cursor = conectar_db()
    
    # Tabla de exámenes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS examenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        codigo TEXT UNIQUE NOT NULL,
        tipo TEXT NOT NULL,
        centro TEXT,
        sala TEXT,
        fecha_creacion TEXT,
        descripcion TEXT,
        conteo INTEGER DEFAULT 0
    )
    ''')
    
    # Tabla de uso
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS uso_examenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        examen_id INTEGER,
        centro TEXT,
        sala TEXT, 
        fecha TEXT,
        FOREIGN KEY(examen_id) REFERENCES examenes(id)
    )
    ''')
    
    # Índices
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_examenes_codigo ON examenes(codigo)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_examenes_tipo ON examenes(tipo)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_examenes_centro ON examenes(centro)')
    
    conn.commit()
    conn.close()

# Funciones de procesamiento
def detectar_tipo_examen(nombre):
    """Detecta el tipo de examen basado en su nombre."""
    nombre = str(nombre).lower()
    
    if 'tac' in nombre or 'tomogr' in nombre:
        return 'TAC'
    elif 'rx' in nombre or 'ray' in nombre or 'radio' in nombre:
        return 'RX'
    elif 'reson' in nombre or 'rm' in nombre:
        return 'RM'
    elif 'eco' in nombre or 'ultra' in nombre or 'us' in nombre:
        return 'US'
    elif 'pet' in nombre:
        return 'PET'
    else:
        return 'OTRO'

def normalizar_texto(texto):
    """Normaliza un texto para quitar acentos y caracteres especiales."""
    # Convertir a string y minúsculas
    texto = str(texto).lower()
    
    # Reemplazar caracteres especiales y acentos
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ü': 'u', 'ñ': 'n'
    }
    for origen, destino in reemplazos.items():
        texto = texto.replace(origen, destino)
    
    # Eliminar caracteres no alfanuméricos ni espacios
    texto = re.sub(r'[^\w\s]', '', texto)
    
    return texto

def obtener_prefijo(tipo):
    """Obtiene el prefijo del código según el tipo de examen."""
    prefijos = {
        'TAC': 'T',
        'RX': 'R',
        'RM': 'M',
        'US': 'U',
        'PET': 'P',
        'OTRO': 'O'
    }
    
    return prefijos.get(tipo.upper(), 'X')

def generar_codigo(nombre_examen, tipo):
    """Genera un código único para un examen basado en su nombre y tipo."""
    # Normalizar el nombre
    nombre_limpio = normalizar_texto(nombre_examen)
    
    # Obtener prefijo según tipo
    prefijo = obtener_prefijo(tipo)
    
    # Extraer palabras significativas para el código
    palabras = nombre_limpio.split()
    if len(palabras) >= 2:
        base_codigo = ''.join([p[0].upper() for p in palabras[:3]])
    else:
        base_codigo = palabras[0][:3].upper()
    
    # Generar sufijo de hash para garantizar unicidad
    hash_texto = hashlib.md5((str(nombre_examen) + tipo).encode()).hexdigest()[:3]
    
    # Combinar partes
    codigo = f"{prefijo}{base_codigo}{hash_texto}".upper()
    
    return codigo

def registrar_examen(nombre, centro=None, sala=None, descripcion=None):
    """Registra un nuevo examen o actualiza uno existente."""
    conn, cursor = conectar_db()
    
    try:
        # Verificar si ya existe el examen por nombre
        cursor.execute("SELECT id, codigo, conteo FROM examenes WHERE nombre = ?", (nombre,))
        examen = cursor.fetchone()
        
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if examen:
            # Actualizar examen existente e incrementar contador
            examen_id = examen['id']
            nuevo_conteo = examen['conteo'] + 1
            
            cursor.execute("""
                UPDATE examenes 
                SET conteo = ?, centro = COALESCE(?, centro), sala = COALESCE(?, sala)
                WHERE id = ?
            """, (nuevo_conteo, centro, sala, examen_id))
            
            # Registrar uso
            cursor.execute("""
                INSERT INTO uso_examenes (examen_id, centro, sala, fecha)
                VALUES (?, ?, ?, ?)
            """, (examen_id, centro, sala, fecha_actual))
            
            conn.commit()
            
            resultado = {'id': examen_id, 'codigo': examen['codigo'], 'nuevo': False}
        else:
            # Detectar tipo
            tipo = detectar_tipo_examen(nombre)
            
            # Generar código único
            codigo = generar_codigo(nombre, tipo)
            
            # Comprobar si el código ya existe y modificarlo si es necesario
            cursor.execute("SELECT codigo FROM examenes WHERE codigo LIKE ?", (f"{codigo}%",))
            codigos_existentes = [row[0] for row in cursor.fetchall()]
            
            if codigo in codigos_existentes:
                contador = 1
                while f"{codigo}{contador}" in codigos_existentes:
                    contador += 1
                codigo = f"{codigo}{contador}"
            
            # Insertar nuevo examen
            cursor.execute("""
                INSERT INTO examenes 
                (nombre, codigo, tipo, centro, sala, fecha_creacion, descripcion, conteo)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (nombre, codigo, tipo, centro, sala, fecha_actual, descripcion))
            
            examen_id = cursor.lastrowid
            
            # Registrar primer uso
            cursor.execute("""
                INSERT INTO uso_examenes (examen_id, centro, sala, fecha)
                VALUES (?, ?, ?, ?)
            """, (examen_id, centro, sala, fecha_actual))
            
            conn.commit()
            
            resultado = {'id': examen_id, 'codigo': codigo, 'nuevo': True}
    except Exception as e:
        conn.rollback()
        resultado = {'error': str(e)}
    finally:
        conn.close()
    
    return resultado

def procesar_dataframe(df):
    """Procesa un DataFrame con datos de exámenes."""
    resultados = {
        "nuevos": 0,
        "actualizados": 0,
        "errores": 0,
        "total": len(df)
    }
    
    # Columnas estándar que buscamos
    col_nombre = None
    col_centro = None
    col_sala = None
    
    # Buscar columnas que coincidan con lo que necesitamos
    for col in df.columns:
        col_lower = str(col).lower()
        # Columna de nombre/procedimiento
        if ("nombre" in col_lower and "procedimiento" in col_lower) or "prestacion" in col_lower:
            col_nombre = col
        # Columna de centro médico
        elif "centro" in col_lower and "medico" in col_lower:
            col_centro = col
        # Columna de sala
        elif "sala" in col_lower:
            col_sala = col
    
    # Si no encontramos columna de nombre, buscar alternativas
    if not col_nombre:
        for col in df.columns:
            col_lower = str(col).lower()
            if "examen" in col_lower or "procedimiento" in col_lower or "estudio" in col_lower:
                col_nombre = col
                break
    
    # Verificar que tenemos la columna principal
    if not col_nombre:
        return {"error": "No se encontró una columna con nombres de procedimientos/exámenes"}
    
    # Procesar cada fila
    for _, row in df.iterrows():
        try:
            # Intentar obtener los valores con manejo de errores
            nombre = str(row[col_nombre]) if col_nombre and not pd.isna(row[col_nombre]) else None
            centro = str(row[col_centro]) if col_centro and not pd.isna(row[col_centro]) else None
            sala = str(row[col_sala]) if col_sala and not pd.isna(row[col_sala]) else None
            
            # Limpiar valores
            nombre = nombre.strip() if nombre else None
            centro = centro.strip() if centro else None
            sala = sala.strip() if sala else None
            
            # Saltar filas sin nombre
            if not nombre:
                continue
            
            # Registrar el examen
            resultado = registrar_examen(nombre, centro, sala)
            
            if 'error' in resultado:
                resultados['errores'] += 1
            elif resultado['nuevo']:
                resultados['nuevos'] += 1
            else:
                resultados['actualizados'] += 1
        except Exception as e:
            resultados['errores'] += 1
            print(f"Error al procesar fila: {e}")
    
    return resultados

def buscar_examenes(texto=None, tipo=None, limite=50):
    """Busca exámenes en la base de datos."""
    conn, cursor = conectar_db()
    
    query = "SELECT * FROM examenes WHERE 1=1"
    params = []
    
    if texto:
        query += " AND (nombre LIKE ? OR codigo LIKE ?)"
        params.extend([f"%{texto}%", f"%{texto}%"])
    
    if tipo and tipo != "Todos":
        query += " AND tipo = ?"
        params.append(tipo)
    
    query += " ORDER BY conteo DESC LIMIT ?"
    params.append(limite)
    
    cursor.execute(query, params)
    resultados = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return resultados

# Crear tablas si no existen
crear_tablas()

# Interfaz principal
st.markdown("### Cargue un archivo Excel con información de exámenes para procesarlo.")

# Widget para cargar archivo Excel
archivo_excel = st.file_uploader("Seleccionar archivo Excel:", type=["xlsx", "xls"])

if archivo_excel is not None:
    # Guardar archivo temporalmente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
        temp_file.write(archivo_excel.getbuffer())
        ruta_temp = temp_file.name
    
    # Obtener las hojas disponibles
    try:
        xls = pd.ExcelFile(ruta_temp)
        hojas = xls.sheet_names
        
        # Selector de hojas
        hoja_seleccionada = st.selectbox(
            "Seleccionar hoja:",
            hojas,
            index=0
        )
        
        # Cargar datos de la hoja seleccionada
        try:
            df = pd.read_excel(ruta_temp, sheet_name=hoja_seleccionada, dtype=str)
            
            # Mostrar vista previa
            st.subheader("Vista previa de datos")
            st.dataframe(df.head(5), use_container_width=True)
            
            # Información de columnas detectadas
            st.subheader("Columnas detectadas")
            columnas_info = []
            
            for col in df.columns:
                col_lower = str(col).lower()
                if ("nombre" in col_lower and "procedimiento" in col_lower) or "prestacion" in col_lower:
                    columnas_info.append(f"✅ {col} → Nombre del procedimiento")
                elif "centro" in col_lower and "medico" in col_lower:
                    columnas_info.append(f"✅ {col} → Centro médico")
                elif "sala" in col_lower:
                    columnas_info.append(f"✅ {col} → Sala")
            
            if columnas_info:
                for info in columnas_info:
                    st.write(info)
            else:
                st.warning("No se detectaron columnas estándar. Se intentará procesar con heurísticas.")
            
            # Botón para procesar
            if st.button("Procesar Archivo", type="primary"):
                with st.spinner("Procesando datos..."):
                    # Procesar datos
                    resultados = procesar_dataframe(df)
                    
                    if "error" in resultados:
                        st.error(f"Error: {resultados['error']}")
                    else:
                        # Mostrar resultados
                        st.success("Archivo procesado correctamente")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Nuevos exámenes", resultados["nuevos"])
                        
                        with col2:
                            st.metric("Actualizados", resultados["actualizados"])
                        
                        with col3:
                            st.metric("Errores", resultados["errores"])
                        
                        # Mostrar algunos de los exámenes procesados
                        st.subheader("Exámenes procesados recientemente")
                        examenes = buscar_examenes(limite=20)
                        
                        if examenes:
                            # Convertir a DataFrame para mostrar
                            df_examenes = pd.DataFrame(examenes)
                            df_examenes = df_examenes[['codigo', 'nombre', 'tipo', 'centro', 'sala', 'conteo']]
                            df_examenes.columns = ['Código', 'Nombre', 'Tipo', 'Centro', 'Sala', 'Usos']
                            
                            # Reemplazar valores nulos
                            df_examenes = df_examenes.fillna("N/A")
                            
                            # Mostrar DataFrame
                            st.dataframe(df_examenes, use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar datos de la hoja: {e}")
    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")

# Sección de búsqueda
st.markdown("---")
st.header("Búsqueda de Exámenes")

# Opciones de búsqueda
col1, col2 = st.columns(2)

with col1:
    texto_busqueda = st.text_input("Buscar por nombre o código:")

with col2:
    tipo_busqueda = st.selectbox(
        "Filtrar por tipo:",
        ["Todos", "TAC", "RX", "RM", "US", "PET", "OTRO"]
    )

# Botón de búsqueda
if st.button("Buscar"):
    examenes = buscar_examenes(texto_busqueda, tipo_busqueda)
    
    if examenes:
        st.success(f"Se encontraron {len(examenes)} exámenes")
        
        # Convertir a DataFrame
        df_resultados = pd.DataFrame(examenes)
        df_resultados = df_resultados[['codigo', 'nombre', 'tipo', 'centro', 'sala', 'conteo']]
        df_resultados.columns = ['Código', 'Nombre', 'Tipo', 'Centro', 'Sala', 'Usos']
        
        # Reemplazar valores nulos
        df_resultados = df_resultados.fillna("N/A")
        
        # Mostrar resultados
        st.dataframe(df_resultados, use_container_width=True)
    else:
        st.info("No se encontraron exámenes")