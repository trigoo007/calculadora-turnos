#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Simple de Codificación de Exámenes
------------------------------------------
Herramienta para generar códigos únicos para exámenes médicos y mantener
un registro estructurado por tipo de examen y centro de adquisición.
"""

import os
import sqlite3
import pandas as pd
import re
import json
from datetime import datetime
import hashlib

# Configuración de directorios y archivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "examenes.db")

# Crear directorio de datos si no existe
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

class SistemaCodigos:
    """Sistema simple para codificar exámenes médicos."""
    
    def __init__(self):
        """Inicializa el sistema de códigos."""
        self.conectar_db()
        self.crear_tablas()
    
    def conectar_db(self):
        """Conecta a la base de datos SQLite."""
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row  # Para obtener resultados como diccionarios
        self.cursor = self.conn.cursor()
    
    def cerrar_db(self):
        """Cierra la conexión a la base de datos."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def crear_tablas(self):
        """Crea las tablas necesarias si no existen."""
        # Tabla de exámenes
        self.cursor.execute('''
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
        
        # Tabla de uso (histórico)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS uso_examenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            examen_id INTEGER,
            centro TEXT,
            sala TEXT, 
            fecha TEXT,
            FOREIGN KEY(examen_id) REFERENCES examenes(id)
        )
        ''')
        
        # Crear índices para búsquedas rápidas
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_examenes_codigo ON examenes(codigo)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_examenes_tipo ON examenes(tipo)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_examenes_centro ON examenes(centro)')
        
        self.conn.commit()
    
    def generar_codigo(self, nombre_examen, tipo):
        """Genera un código único para un examen basado en su nombre y tipo."""
        # Normalizar el nombre
        nombre_limpio = self.normalizar_texto(nombre_examen)
        
        # Obtener prefijo según tipo
        prefijo = self.obtener_prefijo(tipo)
        
        # Extraer palabras significativas para el código
        palabras = nombre_limpio.split()
        if len(palabras) >= 2:
            base_codigo = ''.join([p[0].upper() for p in palabras[:3]])
        else:
            base_codigo = palabras[0][:3].upper()
        
        # Generar sufijo de hash para garantizar unicidad
        hash_texto = hashlib.md5((nombre_examen + tipo).encode()).hexdigest()[:3]
        
        # Combinar partes
        codigo = f"{prefijo}{base_codigo}{hash_texto}".upper()
        
        # Verificar si ya existe el código y añadir contador si es necesario
        self.cursor.execute("SELECT codigo FROM examenes WHERE codigo LIKE ?", (f"{codigo}%",))
        codigos_existentes = [row[0] for row in self.cursor.fetchall()]
        
        if codigo in codigos_existentes:
            contador = 1
            while f"{codigo}{contador}" in codigos_existentes:
                contador += 1
            codigo = f"{codigo}{contador}"
        
        return codigo
    
    def normalizar_texto(self, texto):
        """Normaliza un texto para quitar acentos y caracteres especiales."""
        # Convertir a minúsculas
        texto = texto.lower()
        
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
    
    def obtener_prefijo(self, tipo):
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
    
    def detectar_tipo_examen(self, nombre):
        """Detecta el tipo de examen basado en su nombre."""
        nombre = nombre.lower()
        
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
    
    def registrar_examen(self, nombre, centro=None, sala=None, descripcion=None):
        """Registra un nuevo examen o actualiza uno existente."""
        try:
            # Verificar si ya existe el examen por nombre
            self.cursor.execute("SELECT id, codigo, conteo FROM examenes WHERE nombre = ?", (nombre,))
            examen = self.cursor.fetchone()
            
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if examen:
                # Actualizar examen existente e incrementar contador
                examen_id = examen['id']
                nuevo_conteo = examen['conteo'] + 1
                
                self.cursor.execute("""
                    UPDATE examenes 
                    SET conteo = ?, centro = COALESCE(?, centro), sala = COALESCE(?, sala)
                    WHERE id = ?
                """, (nuevo_conteo, centro, sala, examen_id))
                
                # Registrar uso
                self.cursor.execute("""
                    INSERT INTO uso_examenes (examen_id, centro, sala, fecha)
                    VALUES (?, ?, ?, ?)
                """, (examen_id, centro, sala, fecha_actual))
                
                self.conn.commit()
                return {'id': examen_id, 'codigo': examen['codigo'], 'nuevo': False}
            else:
                # Detectar tipo
                tipo = self.detectar_tipo_examen(nombre)
                
                # Generar código único
                codigo = self.generar_codigo(nombre, tipo)
                
                # Insertar nuevo examen
                self.cursor.execute("""
                    INSERT INTO examenes 
                    (nombre, codigo, tipo, centro, sala, fecha_creacion, descripcion, conteo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (nombre, codigo, tipo, centro, sala, fecha_actual, descripcion))
                
                examen_id = self.cursor.lastrowid
                
                # Registrar primer uso
                self.cursor.execute("""
                    INSERT INTO uso_examenes (examen_id, centro, sala, fecha)
                    VALUES (?, ?, ?, ?)
                """, (examen_id, centro, sala, fecha_actual))
                
                self.conn.commit()
                return {'id': examen_id, 'codigo': codigo, 'nuevo': True}
        except Exception as e:
            print(f"Error al registrar examen: {e}")
            self.conn.rollback()
            return {'error': str(e)}
    
    def buscar_examenes(self, texto=None, tipo=None, centro=None, sala=None, limite=100):
        """Busca exámenes por texto, tipo, centro o sala."""
        query = "SELECT * FROM examenes WHERE 1=1"
        params = []
        
        if texto:
            query += " AND (nombre LIKE ? OR codigo LIKE ?)"
            params.extend([f"%{texto}%", f"%{texto}%"])
        
        if tipo:
            query += " AND tipo = ?"
            params.append(tipo)
        
        if centro:
            query += " AND centro LIKE ?"
            params.append(f"%{centro}%")
        
        if sala:
            query += " AND sala LIKE ?"
            params.append(f"%{sala}%")
        
        query += " ORDER BY conteo DESC LIMIT ?"
        params.append(limite)
        
        self.cursor.execute(query, params)
        resultados = [dict(row) for row in self.cursor.fetchall()]
        
        return resultados
    
    def obtener_examenes_por_tipo(self):
        """Obtiene estadísticas de exámenes agrupados por tipo."""
        self.cursor.execute("""
            SELECT tipo, COUNT(*) as total, SUM(conteo) as usos
            FROM examenes
            GROUP BY tipo
            ORDER BY total DESC
        """)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def obtener_centros(self):
        """Obtiene la lista de centros médicos únicos."""
        self.cursor.execute("""
            SELECT DISTINCT centro 
            FROM examenes 
            WHERE centro IS NOT NULL AND centro != ''
            ORDER BY centro
        """)
        return [row[0] for row in self.cursor.fetchall()]
    
    def obtener_salas(self, centro=None):
        """Obtiene la lista de salas únicas, opcionalmente filtradas por centro."""
        if centro:
            self.cursor.execute("""
                SELECT DISTINCT sala 
                FROM examenes 
                WHERE centro = ? AND sala IS NOT NULL AND sala != ''
                ORDER BY sala
            """, (centro,))
        else:
            self.cursor.execute("""
                SELECT DISTINCT sala 
                FROM examenes 
                WHERE sala IS NOT NULL AND sala != ''
                ORDER BY sala
            """)
        return [row[0] for row in self.cursor.fetchall()]
    
    def obtener_examen_por_codigo(self, codigo):
        """Obtiene información detallada de un examen por su código."""
        try:
            # Obtener datos del examen
            self.cursor.execute("SELECT * FROM examenes WHERE codigo = ?", (codigo,))
            examen = self.cursor.fetchone()
            
            if not examen:
                return None
            
            examen_dict = dict(examen)
            
            # Obtener historial de uso
            self.cursor.execute("""
                SELECT centro, sala, fecha
                FROM uso_examenes
                WHERE examen_id = ?
                ORDER BY fecha DESC
                LIMIT 10
            """, (examen['id'],))
            
            historial = [dict(row) for row in self.cursor.fetchall()]
            examen_dict['historial'] = historial
            
            return examen_dict
        except Exception as e:
            print(f"Error al obtener examen: {e}")
            return None
    
    def procesar_csv(self, ruta_archivo, mapeo_columnas=None):
        """Procesa un archivo CSV para importar exámenes.
        
        Args:
            ruta_archivo: Ruta al archivo CSV
            mapeo_columnas: Diccionario opcional para mapear columnas con nombres diferentes
                al formato estándar. Por ejemplo: {'nombre_procedimiento': 'Nombre examen'}
        """
        try:
            # Verificar si existe el archivo
            if not os.path.exists(ruta_archivo):
                return {"error": f"El archivo {ruta_archivo} no existe"}
            
            # Leer CSV
            df = pd.read_csv(ruta_archivo)
            
            # Definir mapeo de columnas estándar
            columnas_estandar = {
                'nombre_procedimiento': 'Nombre del procedimiento',
                'centro_medico': 'Centro médico',
                'sala_adquisicion': 'Sala de adquisición',
                'descripcion': 'Descripción'
            }
            
            # Aplicar mapeo personalizado si se proporciona
            if mapeo_columnas:
                for key, value in mapeo_columnas.items():
                    if key in columnas_estandar and value in df.columns:
                        columnas_estandar[key] = value
            
            # Verificar columna de nombre del procedimiento
            col_nombre = columnas_estandar['nombre_procedimiento']
            
            # Si no se encuentra la columna estándar, buscar columnas similares
            if col_nombre not in df.columns:
                # Buscar columnas que puedan contener nombres de procedimientos
                posibles_columnas = [
                    col for col in df.columns 
                    if ('nombre' in col.lower() and ('proced' in col.lower() or 'examen' in col.lower())) or
                       'procedimiento' in col.lower() or 'examen' in col.lower()
                ]
                
                if posibles_columnas:
                    # Usar la primera columna que parece contener nombres
                    col_nombre = posibles_columnas[0]
                    print(f"Usando columna alternativa para nombres: {col_nombre}")
                else:
                    return {"error": "No se encontró una columna válida para nombres de procedimientos"}
            
            # Determinar columnas para centro y sala
            col_centro = columnas_estandar['centro_medico'] if columnas_estandar['centro_medico'] in df.columns else None
            col_sala = columnas_estandar['sala_adquisicion'] if columnas_estandar['sala_adquisicion'] in df.columns else None
            col_descripcion = columnas_estandar['descripcion'] if columnas_estandar['descripcion'] in df.columns else None
            
            # Buscar columnas alternativas para centro y sala si no se encuentran las estándar
            if not col_centro:
                for col in df.columns:
                    if 'centro' in col.lower() or 'hospital' in col.lower() or 'clinica' in col.lower():
                        col_centro = col
                        break
            
            if not col_sala:
                for col in df.columns:
                    if 'sala' in col.lower() or 'equipo' in col.lower() or 'maquina' in col.lower():
                        col_sala = col
                        break
            
            # Inicializar resultados
            resultados = {
                "nuevos": 0,
                "actualizados": 0,
                "errores": 0,
                "columnas_usadas": {
                    "nombre": col_nombre,
                    "centro": col_centro,
                    "sala": col_sala,
                    "descripcion": col_descripcion
                }
            }
            
            # Procesar cada examen
            for _, row in df.iterrows():
                # Obtener nombre del procedimiento
                nombre = row[col_nombre]
                if pd.isna(nombre) or not str(nombre).strip():
                    continue  # Saltar filas vacías
                
                # Obtener centro y sala si existen
                centro = row[col_centro] if col_centro and not pd.isna(row[col_centro]) else None
                sala = row[col_sala] if col_sala and not pd.isna(row[col_sala]) else None
                descripcion = row[col_descripcion] if col_descripcion and not pd.isna(row[col_descripcion]) else None
                
                # Asegurarse de que los valores son strings válidos
                try:
                    nombre_limpio = str(nombre).strip() if not pd.isna(nombre) else None
                    centro_limpio = str(centro).strip() if not pd.isna(centro) and centro is not None else None
                    sala_limpia = str(sala).strip() if not pd.isna(sala) and sala is not None else None
                    descripcion_limpia = str(descripcion).strip() if not pd.isna(descripcion) and descripcion is not None else None
                    
                    # Verificar que el nombre no está vacío
                    if not nombre_limpio:
                        continue
                    
                    # Registrar examen
                    resultado = self.registrar_examen(
                        nombre=nombre_limpio,
                        centro=centro_limpio,
                        sala=sala_limpia,
                        descripcion=descripcion_limpia
                    )
                except Exception as e:
                    print(f"Error al procesar fila {_}: {e}")
                    resultados['errores'] += 1
                    continue
                
                if 'error' in resultado:
                    resultados['errores'] += 1
                elif resultado['nuevo']:
                    resultados['nuevos'] += 1
                else:
                    resultados['actualizados'] += 1
            
            return resultados
        except Exception as e:
            return {"error": f"Error al procesar CSV: {str(e)}"}
    
    def obtener_estadisticas(self):
        """Obtiene estadísticas generales del sistema."""
        stats = {}
        
        # Total de exámenes
        self.cursor.execute("SELECT COUNT(*) FROM examenes")
        stats["total_examenes"] = self.cursor.fetchone()[0]
        
        # Distribución por tipo
        stats["por_tipo"] = {}
        self.cursor.execute("SELECT tipo, COUNT(*) FROM examenes GROUP BY tipo")
        for row in self.cursor.fetchall():
            stats["por_tipo"][row[0]] = row[1]
        
        # Exámenes más usados
        self.cursor.execute("""
            SELECT nombre, codigo, tipo, conteo
            FROM examenes
            ORDER BY conteo DESC
            LIMIT 10
        """)
        stats["mas_usados"] = [dict(row) for row in self.cursor.fetchall()]
        
        # Total de usos registrados
        self.cursor.execute("SELECT COUNT(*) FROM uso_examenes")
        stats["total_usos"] = self.cursor.fetchone()[0]
        
        # Total de centros y salas
        self.cursor.execute("SELECT COUNT(DISTINCT centro) FROM examenes WHERE centro IS NOT NULL AND centro != ''")
        stats["total_centros"] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(DISTINCT sala) FROM examenes WHERE sala IS NOT NULL AND sala != ''")
        stats["total_salas"] = self.cursor.fetchone()[0]
        
        return stats
    
    def exportar_json(self, ruta_salida=None):
        """Exporta todos los datos a un archivo JSON."""
        try:
            # Obtener todos los exámenes
            self.cursor.execute("SELECT * FROM examenes")
            examenes = [dict(row) for row in self.cursor.fetchall()]
            
            # Generar nombre de archivo si no se proporciona
            if not ruta_salida:
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                ruta_salida = os.path.join(DATA_DIR, f"exportacion_{timestamp}.json")
            
            # Guardar en archivo JSON
            with open(ruta_salida, 'w', encoding='utf-8') as f:
                json.dump(examenes, f, ensure_ascii=False, indent=2)
            
            return {"exito": True, "archivo": ruta_salida, "total": len(examenes)}
        except Exception as e:
            return {"exito": False, "error": str(e)}
    
    def importar_json(self, ruta_archivo):
        """Importa exámenes desde un archivo JSON."""
        try:
            # Verificar si existe el archivo
            if not os.path.exists(ruta_archivo):
                return {"error": f"El archivo {ruta_archivo} no existe"}
            
            # Leer JSON
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                examenes = json.load(f)
            
            resultados = {
                "nuevos": 0,
                "actualizados": 0,
                "errores": 0
            }
            
            # Procesar cada examen
            for examen in examenes:
                nombre = examen.get('nombre')
                if not nombre:
                    resultados['errores'] += 1
                    continue
                
                # Verificar si ya existe
                self.cursor.execute("SELECT id FROM examenes WHERE codigo = ?", (examen.get('codigo'),))
                existente = self.cursor.fetchone()
                
                if existente:
                    # Actualizar
                    try:
                        self.cursor.execute("""
                            UPDATE examenes 
                            SET nombre = ?, tipo = ?, centro = ?, sala = ?, 
                                descripcion = ?, conteo = ?
                            WHERE id = ?
                        """, (
                            nombre, 
                            examen.get('tipo', 'OTRO'),
                            examen.get('centro'),
                            examen.get('sala'),
                            examen.get('descripcion'),
                            examen.get('conteo', 1),
                            existente['id']
                        ))
                        resultados['actualizados'] += 1
                    except:
                        resultados['errores'] += 1
                else:
                    # Insertar nuevo
                    try:
                        fecha = examen.get('fecha_creacion', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        
                        self.cursor.execute("""
                            INSERT INTO examenes 
                            (nombre, codigo, tipo, centro, sala, fecha_creacion, descripcion, conteo)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            nombre,
                            examen.get('codigo', self.generar_codigo(nombre, examen.get('tipo', 'OTRO'))),
                            examen.get('tipo', 'OTRO'),
                            examen.get('centro'),
                            examen.get('sala'),
                            fecha,
                            examen.get('descripcion'),
                            examen.get('conteo', 1)
                        ))
                        resultados['nuevos'] += 1
                    except:
                        resultados['errores'] += 1
            
            self.conn.commit()
            return resultados
        except Exception as e:
            self.conn.rollback()
            return {"error": f"Error al importar JSON: {str(e)}"}


# Interfaz simple de línea de comandos
def main():
    """Función principal para uso desde línea de comandos."""
    import argparse
    
    # Crear analizador de argumentos
    parser = argparse.ArgumentParser(description="Sistema de Codificación de Exámenes Médicos")
    parser.add_argument('--csv', help='Procesar archivo CSV')
    parser.add_argument('--buscar', help='Buscar exámenes por texto')
    parser.add_argument('--tipo', help='Filtrar por tipo de examen')
    parser.add_argument('--centro', help='Filtrar por centro médico')
    parser.add_argument('--sala', help='Filtrar por sala')
    parser.add_argument('--estadisticas', action='store_true', help='Mostrar estadísticas')
    parser.add_argument('--codigo', help='Buscar examen por código')
    parser.add_argument('--exportar', action='store_true', help='Exportar datos a JSON')
    parser.add_argument('--importar', help='Importar datos desde JSON')
    
    args = parser.parse_args()
    sistema = SistemaCodigos()
    
    try:
        # Procesar argumentos
        if args.csv:
            print(f"Procesando archivo CSV: {args.csv}")
            resultado = sistema.procesar_csv(args.csv)
            if "error" in resultado:
                print(f"Error: {resultado['error']}")
            else:
                print(f"Procesamiento completado:")
                print(f"  - Nuevos exámenes: {resultado['nuevos']}")
                print(f"  - Exámenes actualizados: {resultado['actualizados']}")
                print(f"  - Errores: {resultado['errores']}")
        
        elif args.buscar or args.tipo or args.centro or args.sala:
            print("Buscando exámenes...")
            examenes = sistema.buscar_examenes(args.buscar, args.tipo, args.centro, args.sala)
            
            if examenes:
                print(f"Se encontraron {len(examenes)} exámenes:")
                for i, examen in enumerate(examenes, 1):
                    print(f"{i}. [{examen['codigo']}] {examen['nombre']} - {examen['tipo']} ({examen['conteo']} usos)")
                    if examen['centro']:
                        print(f"   Centro: {examen['centro']}")
                    if examen['sala']:
                        print(f"   Sala: {examen['sala']}")
            else:
                print("No se encontraron exámenes con los criterios especificados.")
        
        elif args.codigo:
            examen = sistema.obtener_examen_por_codigo(args.codigo)
            if examen:
                print(f"Información del examen {args.codigo}:")
                print(f"Nombre: {examen['nombre']}")
                print(f"Tipo: {examen['tipo']}")
                print(f"Usos: {examen['conteo']}")
                print(f"Fecha de creación: {examen['fecha_creacion']}")
                
                if examen['centro']:
                    print(f"Centro: {examen['centro']}")
                if examen['sala']:
                    print(f"Sala: {examen['sala']}")
                if examen['descripcion']:
                    print(f"Descripción: {examen['descripcion']}")
                
                if examen['historial']:
                    print("\nHistorial de uso reciente:")
                    for uso in examen['historial']:
                        centro_sala = []
                        if uso['centro']:
                            centro_sala.append(uso['centro'])
                        if uso['sala']:
                            centro_sala.append(uso['sala'])
                        ubicacion = " - ".join(centro_sala) if centro_sala else "N/A"
                        print(f"  {uso['fecha']} en {ubicacion}")
            else:
                print(f"No se encontró ningún examen con código {args.codigo}")
        
        elif args.estadisticas:
            stats = sistema.obtener_estadisticas()
            print("\nEstadísticas del Sistema:")
            print(f"Total de exámenes: {stats['total_examenes']}")
            print(f"Total de usos registrados: {stats['total_usos']}")
            print(f"Centros médicos: {stats['total_centros']}")
            print(f"Salas de adquisición: {stats['total_salas']}")
            
            print("\nDistribución por tipo:")
            for tipo, cantidad in stats['por_tipo'].items():
                print(f"  - {tipo}: {cantidad}")
            
            if stats['mas_usados']:
                print("\nExámenes más utilizados:")
                for i, examen in enumerate(stats['mas_usados'], 1):
                    print(f"{i}. [{examen['codigo']}] {examen['nombre']} ({examen['conteo']} usos)")
        
        elif args.exportar:
            resultado = sistema.exportar_json()
            if resultado["exito"]:
                print(f"Datos exportados correctamente a: {resultado['archivo']}")
                print(f"Se exportaron {resultado['total']} exámenes.")
            else:
                print(f"Error al exportar: {resultado['error']}")
        
        elif args.importar:
            print(f"Importando datos desde: {args.importar}")
            resultado = sistema.importar_json(args.importar)
            if "error" in resultado:
                print(f"Error: {resultado['error']}")
            else:
                print(f"Importación completada:")
                print(f"  - Nuevos exámenes: {resultado['nuevos']}")
                print(f"  - Exámenes actualizados: {resultado['actualizados']}")
                print(f"  - Errores: {resultado['errores']}")
        
        else:
            # Si no se proporcionan argumentos, mostrar ayuda
            parser.print_help()
    
    finally:
        # Cerrar la conexión a la base de datos
        sistema.cerrar_db()


if __name__ == "__main__":
    main()