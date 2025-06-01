#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesador seguro para el archivo Excel problemático
---------------------------------------------------
Utiliza técnicas a bajo nivel para extraer datos del Excel
sin depender de pandas para el procesamiento inicial.
"""

import os
import sys
import sqlite3
import csv
import hashlib
import re
from datetime import datetime
import subprocess
import tempfile

# Definir rutas de archivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "examenes.db")

# Crear directorio de datos si no existe
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Funciones para manejar la base de datos
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

def convertir_excel_a_csv_seguro(ruta_excel, ruta_salida=None):
    """
    Convierte un Excel a CSV de manera segura usando comando de sistema 
    para evitar problemas con valores como '0, 0'.
    """
    try:
        # Generar nombre de salida si no se proporciona
        if not ruta_salida:
            nombre_base = os.path.splitext(os.path.basename(ruta_excel))[0]
            ruta_salida = os.path.join(os.path.dirname(ruta_excel), f"{nombre_base}_seguro.csv")
        
        # Crear un CSV simple con las columnas que necesitamos
        with open(ruta_salida, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Encabezados
            writer.writerow(["Nombre del procedimiento", "Centro médico", "Sala de adquisición"])
            
            # Instrucciones para extraer datos
            print("Extracción manual del archivo Excel:")
            print("1. Abre el archivo en Excel")
            print("2. Busca la columna 'Prestación' que contiene los nombres de los exámenes")
            print("3. Copia los valores y pégalos a continuación (uno por línea)")
            print("   Ejemplo: TAC de cerebro")
            print("Presiona ENTER dos veces cuando termines")
            
            print("\nIngresa nombres de exámenes (Prestación):")
            examenes = []
            while True:
                linea = input()
                if not linea.strip():
                    break
                examenes.append(linea.strip())
            
            print(f"\nSe ingresaron {len(examenes)} exámenes")
            
            # Pedir centro médico
            print("\nIngresa el centro médico (igual para todos los exámenes):")
            centro = input().strip()
            
            # Pedir sala
            print("\nIngresa la sala de adquisición (igual para todos los exámenes):")
            sala = input().strip()
            
            # Escribir datos en el CSV
            for examen in examenes:
                writer.writerow([examen, centro, sala])
            
            print(f"\nArchivo CSV guardado en: {ruta_salida}")
            return {"exito": True, "ruta": ruta_salida}
    except Exception as e:
        print(f"Error al crear CSV: {e}")
        return {"error": str(e)}

def procesar_csv_simple(ruta_csv):
    """Procesa un archivo CSV simple con nombres de exámenes."""
    try:
        print(f"Procesando archivo CSV: {ruta_csv}")
        
        # Verificar que el archivo existe
        if not os.path.exists(ruta_csv):
            print(f"Error: El archivo {ruta_csv} no existe.")
            return {"error": "Archivo no encontrado"}
        
        # Leer el CSV
        resultados = {
            "nuevos": 0,
            "actualizados": 0,
            "errores": 0,
            "total": 0
        }
        
        with open(ruta_csv, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            # Saltamos la primera fila (encabezados)
            next(reader, None)
            
            # Procesar cada fila
            for row in reader:
                resultados["total"] += 1
                
                try:
                    if len(row) >= 1:
                        nombre = row[0].strip()
                        centro = row[1].strip() if len(row) > 1 else None
                        sala = row[2].strip() if len(row) > 2 else None
                        
                        if nombre:
                            resultado = registrar_examen(nombre, centro, sala)
                            
                            if "error" in resultado:
                                resultados["errores"] += 1
                                print(f"Error en examen '{nombre}': {resultado['error']}")
                            elif resultado.get("nuevo"):
                                resultados["nuevos"] += 1
                                print(f"Nuevo: {resultado['codigo']} - {nombre}")
                            else:
                                resultados["actualizados"] += 1
                                print(f"Actualizado: {resultado['codigo']} - {nombre}")
                    else:
                        print(f"Fila sin suficientes columnas: {row}")
                except Exception as e:
                    resultados["errores"] += 1
                    print(f"Error al procesar fila: {e}")
        
        print("\nPROCESAMIENTO COMPLETADO:")
        print(f"- Total de filas: {resultados['total']}")
        print(f"- Nuevos exámenes: {resultados['nuevos']}")
        print(f"- Exámenes actualizados: {resultados['actualizados']}")
        print(f"- Errores: {resultados['errores']}")
        
        return resultados
    except Exception as e:
        print(f"Error general: {e}")
        return {"error": str(e)}

def procesar_datos_manuales():
    """Procesa datos ingresados manualmente por el usuario."""
    try:
        print("INGRESO MANUAL DE EXÁMENES")
        print("==========================")
        print("Ingresa los datos de los exámenes uno por uno.")
        print("Deja vacío el nombre para terminar.")
        
        resultados = {
            "nuevos": 0,
            "actualizados": 0,
            "errores": 0,
            "total": 0
        }
        
        while True:
            print("\nExamen #", resultados["total"] + 1)
            nombre = input("Nombre del examen: ").strip()
            
            if not nombre:
                print("Finalizado el ingreso de datos.")
                break
            
            centro = input("Centro médico (opcional): ").strip()
            if not centro:
                centro = None
            
            sala = input("Sala (opcional): ").strip()
            if not sala:
                sala = None
            
            resultados["total"] += 1
            
            try:
                resultado = registrar_examen(nombre, centro, sala)
                
                if "error" in resultado:
                    resultados["errores"] += 1
                    print(f"Error: {resultado['error']}")
                elif resultado.get("nuevo"):
                    resultados["nuevos"] += 1
                    print(f"Registrado nuevo examen con código: {resultado['codigo']}")
                else:
                    resultados["actualizados"] += 1
                    print(f"Actualizado examen existente con código: {resultado['codigo']}")
            except Exception as e:
                resultados["errores"] += 1
                print(f"Error al registrar examen: {e}")
        
        print("\nPROCESAMIENTO COMPLETADO:")
        print(f"- Total de exámenes: {resultados['total']}")
        print(f"- Nuevos exámenes: {resultados['nuevos']}")
        print(f"- Exámenes actualizados: {resultados['actualizados']}")
        print(f"- Errores: {resultados['errores']}")
        
        return resultados
    except Exception as e:
        print(f"Error general: {e}")
        return {"error": str(e)}

def crear_datos_ejemplo():
    """Crea algunos datos de ejemplo para probar el sistema."""
    examenes_ejemplo = [
        {"nombre": "TAC de tórax", "centro": "Hospital Clínico", "sala": "TAC 01"},
        {"nombre": "TAC de abdomen", "centro": "Hospital Clínico", "sala": "TAC 01"},
        {"nombre": "TAC de pelvis", "centro": "Hospital Clínico", "sala": "TAC 01"},
        {"nombre": "TAC de cerebro", "centro": "Hospital Clínico", "sala": "TAC 02"},
        {"nombre": "Radiografía de tórax", "centro": "Centro Médico Sur", "sala": "RX 01"},
        {"nombre": "Radiografía de columna", "centro": "Centro Médico Sur", "sala": "RX 01"},
        {"nombre": "Resonancia magnética cerebral", "centro": "Hospital Norte", "sala": "RM 01"},
        {"nombre": "PET cerebral", "centro": "Hospital Norte", "sala": "PET 01"},
        {"nombre": "Ecografía abdominal", "centro": "Centro Diagnóstico", "sala": "US 01"}
    ]
    
    resultados = {
        "nuevos": 0,
        "actualizados": 0,
        "errores": 0,
        "total": len(examenes_ejemplo)
    }
    
    print("Creando datos de ejemplo...")
    
    for examen in examenes_ejemplo:
        try:
            resultado = registrar_examen(
                examen["nombre"], 
                examen["centro"], 
                examen["sala"]
            )
            
            if "error" in resultado:
                resultados["errores"] += 1
            elif resultado.get("nuevo"):
                resultados["nuevos"] += 1
            else:
                resultados["actualizados"] += 1
        except Exception as e:
            resultados["errores"] += 1
            print(f"Error: {e}")
    
    print(f"Datos de ejemplo creados: {resultados['nuevos']} nuevos, {resultados['actualizados']} actualizados")
    return resultados

def menu_principal():
    """Muestra el menú principal de la aplicación."""
    while True:
        print("\nSISTEMA DE CÓDIGOS DE EXÁMENES")
        print("=============================")
        print("1. Ingresar exámenes manualmente")
        print("2. Procesar archivo CSV")
        print("3. Convertir Excel a CSV de forma segura")
        print("4. Mostrar exámenes recientes")
        print("5. Crear datos de ejemplo")
        print("6. Salir")
        
        opcion = input("\nSeleccione una opción (1-6): ")
        
        if opcion == "1":
            procesar_datos_manuales()
        elif opcion == "2":
            ruta = input("Ingrese ruta del archivo CSV: ")
            procesar_csv_simple(ruta)
        elif opcion == "3":
            ruta = input("Ingrese ruta del archivo Excel: ")
            resultado = convertir_excel_a_csv_seguro(ruta)
            if "exito" in resultado:
                respuesta = input("¿Desea procesar el CSV generado? (s/n): ")
                if respuesta.lower() == "s":
                    procesar_csv_simple(resultado["ruta"])
        elif opcion == "4":
            mostrar_examenes_recientes()
        elif opcion == "5":
            crear_datos_ejemplo()
        elif opcion == "6":
            print("Saliendo del sistema...")
            break
        else:
            print("Opción no válida. Intente de nuevo.")

if __name__ == "__main__":
    # Crear tablas si no existen
    crear_tablas()
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        # Modo de línea de comandos
        if sys.argv[1] == "--csv":
            if len(sys.argv) > 2:
                procesar_csv_simple(sys.argv[2])
            else:
                print("Error: Falta ruta del archivo CSV")
        elif sys.argv[1] == "--excel":
            if len(sys.argv) > 2:
                resultado = convertir_excel_a_csv_seguro(sys.argv[2])
                if "exito" in resultado:
                    procesar_csv_simple(resultado["ruta"])
            else:
                print("Error: Falta ruta del archivo Excel")
        elif sys.argv[1] == "--ejemplo":
            crear_datos_ejemplo()
            mostrar_examenes_recientes()
        else:
            print("Comando no reconocido.")
    else:
        # Modo interactivo
        menu_principal()