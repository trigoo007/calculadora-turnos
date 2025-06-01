#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesador directo de archivos Excel para exámenes médicos
----------------------------------------------------------
Este script procesa un archivo Excel directamente desde línea de comandos,
sin necesidad de interfaz web.
"""

import pandas as pd
import sqlite3
import os
import sys
import re
import hashlib
from datetime import datetime

# Definir rutas de archivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "examenes.db")

# Crear directorio de datos si no existe
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Funciones para la base de datos
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
            
            resultado = {'id': examen_id, 'codigo': codigo, 'nuevo': True, 'tipo': tipo}
        
        return resultado
    except Exception as e:
        conn.rollback()
        print(f"Error al registrar examen '{nombre}': {str(e)}")
        return {'error': str(e)}
    finally:
        conn.close()

def mostrar_examenes_recientes(limite=20):
    """Muestra los exámenes más recientes de la base de datos."""
    conn, cursor = conectar_db()
    
    try:
        cursor.execute("""
            SELECT id, codigo, nombre, tipo, centro, sala, conteo 
            FROM examenes 
            ORDER BY id DESC 
            LIMIT ?
        """, (limite,))
        
        examenes = [dict(row) for row in cursor.fetchall()]
        
        print("\nEXÁMENES RECIENTES:")
        print("-" * 80)
        print(f"{'CÓDIGO':<10} {'TIPO':<6} {'CENTRO':<15} {'SALA':<10} {'USOS':<5} {'NOMBRE':<30}")
        print("-" * 80)
        
        for e in examenes:
            centro = str(e['centro'])[:15] if e['centro'] else "N/A"
            sala = str(e['sala'])[:10] if e['sala'] else "N/A"
            nombre = str(e['nombre'])[:30]
            
            print(f"{e['codigo']:<10} {e['tipo']:<6} {centro:<15} {sala:<10} {e['conteo']:<5} {nombre:<30}")
        
        return examenes
    except Exception as e:
        print(f"Error al mostrar exámenes: {str(e)}")
        return []
    finally:
        conn.close()

def mostrar_estadisticas():
    """Muestra estadísticas básicas sobre los datos."""
    conn, cursor = conectar_db()
    
    try:
        # Total de exámenes
        cursor.execute("SELECT COUNT(*) FROM examenes")
        total = cursor.fetchone()[0]
        
        # Distribución por tipo
        cursor.execute("SELECT tipo, COUNT(*) FROM examenes GROUP BY tipo")
        distribucion = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Exámenes por centro
        cursor.execute("""
            SELECT centro, COUNT(*) 
            FROM examenes 
            WHERE centro IS NOT NULL AND centro != '' 
            GROUP BY centro
        """)
        centros = {row[0]: row[1] for row in cursor.fetchall()}
        
        print("\nESTADÍSTICAS DEL SISTEMA:")
        print("-" * 40)
        print(f"Total de exámenes registrados: {total}")
        
        print("\nDistribución por tipo:")
        for tipo, cantidad in distribucion.items():
            print(f"  - {tipo}: {cantidad}")
        
        if centros:
            print("\nExámenes por centro:")
            for centro, cantidad in centros.items():
                print(f"  - {centro}: {cantidad}")
        
        return {
            "total": total,
            "por_tipo": distribucion,
            "por_centro": centros
        }
    except Exception as e:
        print(f"Error al generar estadísticas: {str(e)}")
        return {}
    finally:
        conn.close()

def procesar_excel(ruta_excel, hoja="Data"):
    """Procesa un archivo Excel y registra los exámenes en la base de datos."""
    try:
        print(f"Procesando archivo: {ruta_excel}, hoja: {hoja}")
        
        # Intentar leer el Excel
        try:
            # Ver las hojas disponibles
            xls = pd.ExcelFile(ruta_excel)
            print(f"Hojas disponibles: {xls.sheet_names}")
            
            # Verificar si la hoja existe
            if hoja not in xls.sheet_names:
                print(f"La hoja '{hoja}' no existe. Usando la primera hoja: {xls.sheet_names[0]}")
                hoja = xls.sheet_names[0]
            
            # Leer datos con todos los valores como strings para evitar errores
            df = pd.read_excel(ruta_excel, sheet_name=hoja, dtype=str)
            
            print(f"Archivo leído correctamente. Dimensiones: {df.shape}")
            print(f"Columnas: {df.columns.tolist()}")
        except Exception as e:
            print(f"Error al leer Excel: {str(e)}")
            return {"error": f"No se pudo leer el archivo Excel: {str(e)}"}
        
        # Detectar columnas relevantes
        col_nombre = None
        col_centro = None
        col_sala = None
        
        # Buscar columnas estándar
        for col in df.columns:
            col_lower = str(col).lower()
            if ("nombre" in col_lower and "procedimiento" in col_lower) or "prestacion" in col_lower:
                col_nombre = col
                print(f"Columna de procedimientos: {col}")
            elif "centro" in col_lower and "medico" in col_lower:
                col_centro = col
                print(f"Columna de centro médico: {col}")
            elif "sala" in col_lower:
                col_sala = col
                print(f"Columna de sala: {col}")
        
        # Si no encontramos la columna de nombre, buscar alternativas
        if not col_nombre:
            for col in df.columns:
                col_lower = str(col).lower()
                if "examen" in col_lower or "procedimiento" in col_lower or "estudio" in col_lower:
                    col_nombre = col
                    print(f"Columna de procedimientos (alternativa): {col}")
                    break
        
        # Verificar que tenemos al menos la columna de nombre
        if not col_nombre:
            print("ERROR: No se encontró una columna con nombres de procedimientos.")
            print("Columnas disponibles:")
            for col in df.columns:
                print(f"  - {col}")
            return {"error": "No se encontró una columna con nombres de procedimientos"}
        
        # Procesar cada fila
        resultados = {
            "nuevos": 0,
            "actualizados": 0,
            "errores": 0,
            "total": len(df)
        }
        
        for idx, row in df.iterrows():
            try:
                # Obtener valores limpiando nulos
                nombre = str(row[col_nombre]) if not pd.isna(row[col_nombre]) else None
                centro = str(row[col_centro]) if col_centro and not pd.isna(row[col_centro]) else None
                sala = str(row[col_sala]) if col_sala and not pd.isna(row[col_sala]) else None
                
                # Limpiar espacios
                nombre = nombre.strip() if nombre else None
                centro = centro.strip() if centro else None
                sala = sala.strip() if sala else None
                
                if not nombre:
                    continue
                
                # Registrar el examen
                resultado = registrar_examen(nombre, centro, sala)
                
                if 'error' in resultado:
                    resultados['errores'] += 1
                elif resultado.get('nuevo'):
                    resultados['nuevos'] += 1
                    print(f"Nuevo: {resultado.get('codigo')} - {nombre} ({resultado.get('tipo')})")
                else:
                    resultados['actualizados'] += 1
            except Exception as e:
                resultados['errores'] += 1
                print(f"Error en fila {idx}: {str(e)}")
        
        print("\nPROCESAMIENTO COMPLETADO:")
        print(f"- Total de filas: {resultados['total']}")
        print(f"- Nuevos exámenes: {resultados['nuevos']}")
        print(f"- Exámenes actualizados: {resultados['actualizados']}")
        print(f"- Errores: {resultados['errores']}")
        
        return resultados
    except Exception as e:
        print(f"Error general: {str(e)}")
        return {"error": str(e)}

def crear_csv_resultados(examenes, ruta_salida=None):
    """Crea un archivo CSV con los resultados de los exámenes procesados."""
    if not examenes:
        print("No hay exámenes para exportar")
        return
    
    # Crear un DataFrame con los exámenes
    df = pd.DataFrame(examenes)
    
    # Determinar ruta de salida
    if not ruta_salida:
        ruta_salida = os.path.join(BASE_DIR, f"examenes_procesados_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
    
    # Guardar como CSV
    df.to_csv(ruta_salida, index=False)
    print(f"Archivo CSV guardado en: {ruta_salida}")
    return ruta_salida

if __name__ == "__main__":
    # Crear tablas si no existen
    crear_tablas()
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        ruta_excel = sys.argv[1]
        hoja = sys.argv[2] if len(sys.argv) > 2 else "Data"
        
        # Procesar el archivo
        resultado = procesar_excel(ruta_excel, hoja)
        
        if 'error' not in resultado:
            # Mostrar exámenes recientes
            examenes = mostrar_examenes_recientes()
            
            # Crear CSV con resultados
            crear_csv_resultados(examenes)
            
            # Mostrar estadísticas
            mostrar_estadisticas()
        
    else:
        print("Uso: python procesar_directo.py ruta_archivo.xlsx [hoja]")
        print("Ejemplo: python procesar_directo.py '/Users/rodrigomunoz/Downloads/Lista de Trabajo.xlsx' Data")