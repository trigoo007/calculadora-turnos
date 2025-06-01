#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de aprendizaje y análisis de datos para la Calculadora de Turnos (Versión SQLite)
----------------------------------------------------------------------------------------
Herramienta para indexar, clasificar y aprender de los datos procesados.
Utiliza SQLite para almacenar y gestionar eficientemente el conocimiento acumulado.

Características principales:
- Clasificación automática de procedimientos (RX, TAC normal, TAC doble, TAC triple)
- Generación de códigos únicos para procedimientos
- Clasificación y categorización de salas (SCA, SJ, HOS)
- Detección avanzada de patrones en TAC dobles y triples
- Búsquedas indexadas ultrarrápidas mediante SQLite
- Soporte para grandes volúmenes de datos
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime
import re
from collections import Counter, defaultdict

# Ruta a la base de datos SQLite
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONOCIMIENTO_DIR = os.path.join(BASE_DIR, "conocimiento")
DB_FILE = os.path.join(CONOCIMIENTO_DIR, "conocimiento.db")

# Asegurar que el directorio de conocimiento existe
if not os.path.exists(CONOCIMIENTO_DIR):
    os.makedirs(CONOCIMIENTO_DIR)


class SistemaAprendizajeSQLite:
    """Sistema para analizar, indexar y aprender de los datos procesados con SQLite."""
    
    def __init__(self):
        """Inicializa el sistema de aprendizaje y la base de datos SQLite."""
        # Contadores para uso temporal
        self.contador_procedimientos = Counter()
        self.contador_salas = Counter()
        
        # Inicializar la base de datos
        self.inicializar_db()
        
        # Cargar patrones para TAC doble y triple
        self.patrones_tac_doble = self.cargar_patrones('tac_doble')
        self.patrones_tac_triple = self.cargar_patrones('tac_triple')
    
    def inicializar_db(self):
        """Crea las tablas en la base de datos si no existen."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Tabla de procedimientos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS procedimientos (
            nombre TEXT PRIMARY KEY,
            codigo TEXT UNIQUE,
            tipo TEXT,
            subtipo TEXT,
            conteo INTEGER,
            primera_vez TEXT
        )
        ''')
        
        # Tabla de salas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS salas (
            nombre TEXT PRIMARY KEY,
            tipo TEXT,
            subtipo TEXT,
            conteo INTEGER,
            primera_vez TEXT
        )
        ''')
        
        # Tabla de patrones para TAC doble y triple
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS patrones (
            patron TEXT PRIMARY KEY,
            tipo TEXT
        )
        ''')
        
        # Crear índices para búsquedas rápidas
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_procedimientos_tipo ON procedimientos(tipo)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_procedimientos_subtipo ON procedimientos(subtipo)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_salas_tipo ON salas(tipo)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_patrones_tipo ON patrones(tipo)')
        
        conn.commit()
        conn.close()
    
    def cargar_patrones(self, tipo):
        """Carga los patrones de TAC doble o triple desde la base de datos."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT patron FROM patrones WHERE tipo = ?', (tipo,))
        patrones = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        # Si no hay patrones en la DB, cargar desde archivo JSON (para migración)
        if not patrones:
            try:
                if tipo == 'tac_doble':
                    json_file = os.path.join(CONOCIMIENTO_DIR, "patrones_tac_doble.json")
                else:
                    json_file = os.path.join(CONOCIMIENTO_DIR, "patrones_tac_triple.json")
                
                if os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        patrones = json.load(f)
                    
                    # Guardar patrones en la DB
                    self.guardar_patrones(patrones, tipo)
            except Exception as e:
                print(f"Error al cargar patrones desde JSON: {e}")
        
        return patrones
    
    def guardar_patrones(self, patrones, tipo):
        """Guarda los patrones en la base de datos."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        for patron in patrones:
            cursor.execute(
                'INSERT OR IGNORE INTO patrones (patron, tipo) VALUES (?, ?)',
                (patron, tipo)
            )
        
        conn.commit()
        conn.close()
    
    def generar_codigo_procedimiento(self, nombre_procedimiento):
        """Genera un código único para un procedimiento basado en su nombre."""
        # Eliminar caracteres especiales y convertir a minúsculas
        nombre_limpio = re.sub(r'[^\w\s]', '', nombre_procedimiento.lower())
        palabras = nombre_limpio.split()
        
        # Generar código basado en las primeras letras de cada palabra
        if len(palabras) >= 2:
            codigo = ''.join([p[0:2] for p in palabras[:3]])
        else:
            codigo = palabras[0][:5]
        
        # Comprobar si el código ya existe y generar uno único
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        base_codigo = codigo.upper()
        nuevo_codigo = base_codigo
        contador = 1
        
        while True:
            cursor.execute('SELECT COUNT(*) FROM procedimientos WHERE codigo = ?', (nuevo_codigo,))
            if cursor.fetchone()[0] == 0:
                break
            nuevo_codigo = f"{base_codigo}{contador}"
            contador += 1
        
        conn.close()
        return nuevo_codigo
    
    def clasificar_procedimiento(self, nombre_procedimiento):
        """Clasifica un procedimiento según su tipo y subtipo."""
        nombre = nombre_procedimiento.lower()
        
        # Clasificación básica
        if 'tac' in nombre or 'tomograf' in nombre:
            tipo = 'TAC'
            
            # Detectar si es TAC triple
            es_triple = False
            for patron in self.patrones_tac_triple:
                if patron.lower() in nombre:
                    es_triple = True
                    break
            
            # Detectar combinaciones específicas para TAC triple
            if any(all(region in nombre for region in combinacion) 
                  for combinacion in [
                      ['cuello', 'torax', 'abdomen'],
                      ['craneo', 'cuello', 'torax'],
                      ['cabeza', 'cuello', 'torax'],
                      ['cerebro', 'cuello', 'torax']
                  ]):
                es_triple = True
            
            # Si no es triple, verificar si es doble
            es_doble = False
            if not es_triple:
                for patron in self.patrones_tac_doble:
                    if patron.lower() in nombre:
                        es_doble = True
                        break
                
                # También detectar combinaciones específicas para TAC doble
                if any(all(region in nombre for region in combinacion) 
                      for combinacion in [
                          ['torax', 'abdomen'], 
                          ['tx', 'abd'], 
                          ['pecho', 'abdomen']
                      ]):
                    es_doble = True
            
            # Determinar subtipo
            if es_triple:
                subtipo = 'TRIPLE'
            elif es_doble:
                subtipo = 'DOBLE'
            else:
                subtipo = 'NORMAL'
        elif 'rx' in nombre or 'radio' in nombre or 'rayos' in nombre:
            tipo = 'RX'
            subtipo = 'NORMAL'
        else:
            tipo = 'OTRO'
            subtipo = 'DESCONOCIDO'
        
        return {
            'tipo': tipo,
            'subtipo': subtipo
        }
    
    def clasificar_sala(self, nombre_sala):
        """Clasifica una sala según su tipo y ubicación."""
        nombre = nombre_sala.upper()
        
        # Clasificación básica
        if 'SCA' in nombre or 'SCAD' in nombre:
            tipo = 'SCA'
        elif 'SJ' in nombre:
            tipo = 'SJ'
        elif 'HOS' in nombre:
            tipo = 'HOS'
        else:
            tipo = 'OTRO'
        
        # Subtipo (especialidad)
        if 'TAC' in nombre:
            subtipo = 'TAC'
        elif 'RX' in nombre or 'RAYOS' in nombre:
            subtipo = 'RX'
        elif 'PROC' in nombre:
            subtipo = 'PROCEDIMIENTOS'
        else:
            subtipo = 'GENERAL'
        
        return {
            'tipo': tipo,
            'subtipo': subtipo
        }
    
    def analizar_dataframe(self, df):
        """Analiza un DataFrame para extraer información sobre procedimientos y salas."""
        # Verificar columnas requeridas
        columnas_req = ['Nombre del procedimiento', 'Sala de adquisición']
        if not all(col in df.columns for col in columnas_req):
            return False, "El DataFrame no contiene las columnas requeridas"
        
        # Contadores para este análisis
        nuevos_procedimientos = 0
        nuevas_salas = 0
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Fecha actual para "primera_vez"
        fecha_actual = datetime.now().strftime('%Y-%m-%d')
        
        # Procesar procedimientos
        for proc in df['Nombre del procedimiento'].dropna().unique():
            self.contador_procedimientos[proc] += 1
            
            # Verificar si el procedimiento ya existe
            cursor.execute('SELECT * FROM procedimientos WHERE nombre = ?', (proc,))
            resultado = cursor.fetchone()
            
            if resultado is None:
                # Es un nuevo procedimiento
                codigo = self.generar_codigo_procedimiento(proc)
                clasificacion = self.clasificar_procedimiento(proc)
                
                try:
                    cursor.execute(
                        'INSERT INTO procedimientos (nombre, codigo, tipo, subtipo, conteo, primera_vez) VALUES (?, ?, ?, ?, ?, ?)',
                        (proc, codigo, clasificacion['tipo'], clasificacion['subtipo'], 1, fecha_actual)
                    )
                except sqlite3.IntegrityError:
                    # Si hay un conflicto con el código, generar uno nuevo con un sufijo aleatorio
                    import random
                    codigo = f"{codigo}_{random.randint(1000, 9999)}"
                    cursor.execute(
                        'INSERT INTO procedimientos (nombre, codigo, tipo, subtipo, conteo, primera_vez) VALUES (?, ?, ?, ?, ?, ?)',
                        (proc, codigo, clasificacion['tipo'], clasificacion['subtipo'], 1, fecha_actual)
                    )
                nuevos_procedimientos += 1
            else:
                # Actualizar conteo
                nuevo_conteo = resultado[4] + 1
                
                # Verificar si necesitamos actualizar la clasificación
                clasificacion_actual = self.clasificar_procedimiento(proc)
                if clasificacion_actual['subtipo'] != resultado[3]:  # resultado[3] es el subtipo
                    cursor.execute(
                        'UPDATE procedimientos SET conteo = ?, subtipo = ? WHERE nombre = ?',
                        (nuevo_conteo, clasificacion_actual['subtipo'], proc)
                    )
                else:
                    cursor.execute(
                        'UPDATE procedimientos SET conteo = ? WHERE nombre = ?',
                        (nuevo_conteo, proc)
                    )
        
        # Procesar salas
        for sala in df['Sala de adquisición'].dropna().unique():
            self.contador_salas[sala] += 1
            
            # Verificar si la sala ya existe
            cursor.execute('SELECT * FROM salas WHERE nombre = ?', (sala,))
            resultado = cursor.fetchone()
            
            if resultado is None:
                # Es una nueva sala
                clasificacion = self.clasificar_sala(sala)
                
                cursor.execute(
                    'INSERT INTO salas (nombre, tipo, subtipo, conteo, primera_vez) VALUES (?, ?, ?, ?, ?)',
                    (sala, clasificacion['tipo'], clasificacion['subtipo'], 1, fecha_actual)
                )
                nuevas_salas += 1
            else:
                # Actualizar conteo
                nuevo_conteo = resultado[3] + 1
                cursor.execute(
                    'UPDATE salas SET conteo = ? WHERE nombre = ?',
                    (nuevo_conteo, sala)
                )
        
        # Aprender patrones de TAC doble y triple
        if 'TAC doble' in df.columns:
            self.aprender_patrones_tac_doble(df)
        
        # Guardar cambios
        conn.commit()
        conn.close()
        
        # Aprender patrones de TAC triple
        self.aprender_patrones_tac_triple(df)
        
        return True, f"Análisis completado: {nuevos_procedimientos} nuevos procedimientos, {nuevas_salas} nuevas salas"
    
    def aprender_patrones_tac_doble(self, df):
        """Analiza exámenes marcados como TAC doble para identificar patrones comunes."""
        # Verificar columnas requeridas
        columnas_req = ['Nombre del procedimiento', 'TAC doble']
        if not all(col in df.columns for col in columnas_req):
            return False, "El DataFrame no contiene las columnas requeridas"
        
        # Extraer nombres de procedimientos marcados como TAC doble
        tac_dobles = df[df['TAC doble'] == True]['Nombre del procedimiento'].dropna().unique()
        
        # Extraer patrones comunes
        nuevos_patrones = 0
        nuevos_patrones_list = []
        
        for nombre in tac_dobles:
            # Verificar si ya tenemos este patrón
            if nombre not in self.patrones_tac_doble:
                self.patrones_tac_doble.append(nombre)
                nuevos_patrones_list.append(nombre)
                nuevos_patrones += 1
        
        # Guardar nuevos patrones en la DB
        if nuevos_patrones > 0:
            self.guardar_patrones(nuevos_patrones_list, 'tac_doble')
        
        return True, f"Aprendizaje completado: {nuevos_patrones} nuevos patrones de TAC doble identificados"
    
    def aprender_patrones_tac_triple(self, df):
        """Analiza exámenes para identificar patrones de TAC triple."""
        # Verificar si hay una columna para TAC triple
        if 'TAC triple' in df.columns:
            # Extraer nombres de procedimientos marcados como TAC triple
            tac_triples = df[df['TAC triple'] == True]['Nombre del procedimiento'].dropna().unique()
        else:
            # Si no hay columna específica, usar la clasificación para buscar
            tac_triples = []
            for nombre in df['Nombre del procedimiento'].dropna().unique():
                clasificacion = self.clasificar_procedimiento(nombre)
                if clasificacion['tipo'] == 'TAC' and clasificacion['subtipo'] == 'TRIPLE':
                    tac_triples.append(nombre)
        
        # Extraer patrones comunes
        nuevos_patrones = 0
        nuevos_patrones_list = []
        
        for nombre in tac_triples:
            # Verificar si ya tenemos este patrón
            if nombre not in self.patrones_tac_triple:
                self.patrones_tac_triple.append(nombre)
                nuevos_patrones_list.append(nombre)
                nuevos_patrones += 1
        
        # Guardar nuevos patrones en la DB
        if nuevos_patrones > 0:
            self.guardar_patrones(nuevos_patrones_list, 'tac_triple')
        
        return True, f"Aprendizaje completado: {nuevos_patrones} nuevos patrones de TAC triple identificados"
    
    def obtener_estadisticas(self):
        """Obtiene estadísticas sobre los datos aprendidos."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Contar procedimientos por tipo
        cursor.execute('SELECT COUNT(*) FROM procedimientos')
        total_procedimientos = cursor.fetchone()[0]
        
        tipos_procedimientos = {}
        cursor.execute('SELECT tipo, COUNT(*) FROM procedimientos GROUP BY tipo')
        for tipo, count in cursor.fetchall():
            tipos_procedimientos[tipo] = count
        
        # Contar por subtipo (especialmente para TAC)
        subtipos_procedimientos = {}
        cursor.execute('SELECT tipo, subtipo, COUNT(*) FROM procedimientos WHERE tipo = "TAC" GROUP BY subtipo')
        for tipo, subtipo, count in cursor.fetchall():
            subtipos_procedimientos[f"TAC_{subtipo}"] = count
        
        # Contar salas por tipo
        cursor.execute('SELECT COUNT(*) FROM salas')
        total_salas = cursor.fetchone()[0]
        
        tipos_salas = {}
        cursor.execute('SELECT tipo, COUNT(*) FROM salas GROUP BY tipo')
        for tipo, count in cursor.fetchall():
            tipos_salas[tipo] = count
        
        # Contar patrones
        cursor.execute('SELECT COUNT(*) FROM patrones WHERE tipo = "tac_doble"')
        total_patrones_doble = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM patrones WHERE tipo = "tac_triple"')
        total_patrones_triple = cursor.fetchone()[0]
        
        conn.close()
        
        # Construir diccionario de estadísticas
        stats = {
            'procedimientos': {
                'total': total_procedimientos,
                'por_tipo': tipos_procedimientos,
                'por_subtipo': subtipos_procedimientos
            },
            'salas': {
                'total': total_salas,
                'por_tipo': tipos_salas
            },
            'patrones_tac_doble': total_patrones_doble,
            'patrones_tac_triple': total_patrones_triple
        }
        
        return stats
    
    def verificar_clasificacion(self, nombre_procedimiento):
        """Verifica si un procedimiento debería ser clasificado como TAC doble."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT tipo, subtipo FROM procedimientos WHERE nombre = ?', (nombre_procedimiento,))
        resultado = cursor.fetchone()
        
        conn.close()
        
        if resultado:
            return resultado[0] == 'TAC' and resultado[1] == 'DOBLE'
        
        # Si no está en la base de datos, clasificar dinámicamente
        clasificacion = self.clasificar_procedimiento(nombre_procedimiento)
        return clasificacion['tipo'] == 'TAC' and clasificacion['subtipo'] == 'DOBLE'
    
    def obtener_procedimientos_tipo(self, tipo, subtipo=None):
        """Obtiene una lista de procedimientos de un tipo específico."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        if subtipo:
            cursor.execute(
                'SELECT nombre, codigo, subtipo, conteo FROM procedimientos WHERE tipo = ? AND subtipo = ? ORDER BY conteo DESC',
                (tipo, subtipo)
            )
        else:
            cursor.execute(
                'SELECT nombre, codigo, subtipo, conteo FROM procedimientos WHERE tipo = ? ORDER BY conteo DESC',
                (tipo,)
            )
        
        resultados = cursor.fetchall()
        conn.close()
        
        # Convertir a lista de diccionarios
        resultado = []
        for nombre, codigo, sub, conteo in resultados:
            resultado.append({
                'nombre': nombre,
                'codigo': codigo,
                'subtipo': sub,
                'conteo': conteo
            })
        
        return resultado
    
    def obtener_salas_tipo(self, tipo):
        """Obtiene una lista de salas de un tipo específico."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT nombre, subtipo, conteo FROM salas WHERE tipo = ? ORDER BY conteo DESC',
            (tipo,)
        )
        
        resultados = cursor.fetchall()
        conn.close()
        
        # Convertir a lista de diccionarios
        resultado = []
        for nombre, subtipo, conteo in resultados:
            resultado.append({
                'nombre': nombre,
                'subtipo': subtipo,
                'conteo': conteo
            })
        
        return resultado
    
    def migrar_desde_json(self):
        """Migra datos desde archivos JSON existentes a la base de datos SQLite."""
        # Migrar procedimientos
        json_file = os.path.join(CONOCIMIENTO_DIR, "procedimientos.json")
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    procedimientos = json.load(f)
                
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                for nombre, datos in procedimientos.items():
                    cursor.execute(
                        'INSERT OR IGNORE INTO procedimientos (nombre, codigo, tipo, subtipo, conteo, primera_vez) VALUES (?, ?, ?, ?, ?, ?)',
                        (nombre, datos.get('codigo', ''), datos.get('tipo', 'OTRO'), 
                         datos.get('subtipo', 'DESCONOCIDO'), datos.get('conteo', 1), 
                         datos.get('primera_vez', datetime.now().strftime('%Y-%m-%d')))
                    )
                
                conn.commit()
                conn.close()
                
                print(f"Migrados {len(procedimientos)} procedimientos desde JSON")
            except Exception as e:
                print(f"Error al migrar procedimientos: {e}")
        
        # Migrar salas
        json_file = os.path.join(CONOCIMIENTO_DIR, "salas.json")
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    salas = json.load(f)
                
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                for nombre, datos in salas.items():
                    cursor.execute(
                        'INSERT OR IGNORE INTO salas (nombre, tipo, subtipo, conteo, primera_vez) VALUES (?, ?, ?, ?, ?)',
                        (nombre, datos.get('tipo', 'OTRO'), datos.get('subtipo', 'GENERAL'), 
                         datos.get('conteo', 1), datos.get('primera_vez', datetime.now().strftime('%Y-%m-%d')))
                    )
                
                conn.commit()
                conn.close()
                
                print(f"Migradas {len(salas)} salas desde JSON")
            except Exception as e:
                print(f"Error al migrar salas: {e}")
        
        # Los patrones ya se migran automáticamente durante la inicialización


# Función principal para uso independiente
def main():
    """Función principal para uso del sistema de aprendizaje de forma independiente."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sistema de aprendizaje para la Calculadora de Turnos (SQLite)")
    parser.add_argument('--csv', help='Ruta al archivo CSV para analizar')
    parser.add_argument('--stats', action='store_true', help='Mostrar estadísticas del conocimiento actual')
    parser.add_argument('--tac', action='store_true', help='Listar procedimientos TAC')
    parser.add_argument('--tac-doble', action='store_true', help='Listar procedimientos TAC doble')
    parser.add_argument('--tac-triple', action='store_true', help='Listar procedimientos TAC triple')
    parser.add_argument('--salas', help='Listar salas por tipo (SCA, SJ, HOS, OTRO)')
    parser.add_argument('--migrar', action='store_true', help='Migrar datos desde JSON a SQLite')
    
    args = parser.parse_args()
    sistema = SistemaAprendizajeSQLite()
    
    # Migrar datos desde JSON si se solicita
    if args.migrar:
        print("Iniciando migración de datos desde JSON...")
        sistema.migrar_desde_json()
    
    # Analizar CSV si se proporciona
    if args.csv:
        if os.path.exists(args.csv):
            print(f"Analizando archivo CSV: {args.csv}")
            df = pd.read_csv(args.csv)
            exito, mensaje = sistema.analizar_dataframe(df)
            print(mensaje)
        else:
            print(f"Error: El archivo {args.csv} no existe")
    
    # Mostrar estadísticas
    if args.stats:
        stats = sistema.obtener_estadisticas()
        print("\nEstadísticas del sistema de aprendizaje:")
        print(f"- Procedimientos únicos: {stats['procedimientos']['total']}")
        for tipo, count in stats['procedimientos']['por_tipo'].items():
            print(f"  - {tipo}: {count}")
        
        # Mostrar subtipos de TAC
        print("  - Desglose de TAC por subtipo:")
        for subtipo, count in stats['procedimientos']['por_subtipo'].items():
            print(f"    * {subtipo}: {count}")
        
        print(f"- Salas únicas: {stats['salas']['total']}")
        for tipo, count in stats['salas']['por_tipo'].items():
            print(f"  - {tipo}: {count}")
        print(f"- Patrones de TAC doble: {stats['patrones_tac_doble']}")
        print(f"- Patrones de TAC triple: {stats['patrones_tac_triple']}")
    
    # Listar procedimientos TAC
    if args.tac:
        tac_procs = sistema.obtener_procedimientos_tipo('TAC')
        print("\nProcedimientos TAC:")
        for i, proc in enumerate(tac_procs[:20]):  # Mostrar solo los 20 más comunes
            print(f"- [{proc['codigo']}] {proc['nombre']} ({proc['conteo']})")
        if len(tac_procs) > 20:
            print(f"... y {len(tac_procs) - 20} más")
    
    # Listar procedimientos TAC doble
    if args.tac_doble:
        tac_doble_procs = sistema.obtener_procedimientos_tipo('TAC', 'DOBLE')
        print("\nProcedimientos TAC doble:")
        for proc in tac_doble_procs:
            print(f"- [{proc['codigo']}] {proc['nombre']} ({proc['conteo']})")
    
    # Listar procedimientos TAC triple
    if args.tac_triple:
        tac_triple_procs = sistema.obtener_procedimientos_tipo('TAC', 'TRIPLE')
        print("\nProcedimientos TAC triple:")
        for proc in tac_triple_procs:
            print(f"- [{proc['codigo']}] {proc['nombre']} ({proc['conteo']})")
    
    # Listar salas por tipo
    if args.salas:
        tipo_sala = args.salas.upper()
        salas = sistema.obtener_salas_tipo(tipo_sala)
        print(f"\nSalas de tipo {tipo_sala}:")
        for sala in salas:
            print(f"- {sala['nombre']} ({sala['subtipo']}, {sala['conteo']})")


if __name__ == "__main__":
    main()