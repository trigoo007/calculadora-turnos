#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Codificación de Exámenes Médicos
------------------------------------------
Módulo para la generación, gestión y validación de códigos de exámenes médicos.
Permite asignar códigos únicos a procedimientos y mantener un registro histórico.

Características principales:
- Generación automática de códigos para procedimientos médicos
- Clasificación inteligente por tipo y subtipo de procedimiento
- Registro de frecuencia y estadísticas de uso
- Exportación/importación de códigos en formatos estándar
- Verificación de integridad y validación de códigos
"""

import os
import sqlite3
import re
import json
import pandas as pd
from datetime import datetime
import hashlib
from collections import Counter, defaultdict

# Configuración de rutas de archivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTROS_DIR = os.path.join(BASE_DIR, "registros")
DB_FILE = os.path.join(REGISTROS_DIR, "codigos_examenes.db")

# Asegurar que el directorio de registros existe
if not os.path.exists(REGISTROS_DIR):
    os.makedirs(REGISTROS_DIR)

class CodigosExamenes:
    """Sistema para generar, validar y gestionar códigos de exámenes médicos."""
    
    def __init__(self):
        """Inicializa el sistema de códigos y la base de datos SQLite."""
        # Contadores para uso temporal
        self.contador_examenes = Counter()
        self.centros_adquisicion = {}
        self.salas_adquisicion = {}
        
        # Configurar ruta de la base de datos
        self.__db_file = DB_FILE
        
        # Inicializar la base de datos
        self.inicializar_db()
        
        # Cargar patrones de clasificación
        self.patrones_rx_especial = self.cargar_patrones('rx_especial')
        self.patrones_proc_complejo = self.cargar_patrones('proc_complejo')
    
    def inicializar_db(self):
        """Crea las tablas en la base de datos si no existen."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Tabla de códigos de exámenes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS codigos_examenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            codigo TEXT UNIQUE,
            tipo TEXT,
            subtipo TEXT,
            complejidad INTEGER,
            tiempo_estimado INTEGER,
            conteo INTEGER DEFAULT 0,
            fecha_creacion TEXT,
            ultima_actualizacion TEXT
        )
        ''')
        
        # Tabla de centros médicos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS centros_medicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            codigo TEXT,
            direccion TEXT,
            region TEXT,
            conteo INTEGER DEFAULT 0
        )
        ''')
        
        # Tabla de salas de adquisición
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS salas_adquisicion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            centro_id INTEGER,
            tipo_equipo TEXT,
            conteo INTEGER DEFAULT 0,
            FOREIGN KEY (centro_id) REFERENCES centros_medicos(id)
        )
        ''')
        
        # Tabla de patrones para clasificación
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS patrones_clasificacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patron TEXT,
            tipo TEXT,
            subtipo TEXT,
            descripcion TEXT
        )
        ''')
        
        # Tabla de histórico de usos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_examenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_id INTEGER,
            fecha TEXT,
            centro_medico_id INTEGER,
            sala_id INTEGER,
            tiempo_real INTEGER,
            observaciones TEXT,
            FOREIGN KEY (codigo_id) REFERENCES codigos_examenes(id),
            FOREIGN KEY (centro_medico_id) REFERENCES centros_medicos(id),
            FOREIGN KEY (sala_id) REFERENCES salas_adquisicion(id)
        )
        ''')
        
        # Tabla de mapeo con sistemas externos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mapeo_codigos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_interno_id INTEGER,
            sistema_externo TEXT,
            codigo_externo TEXT,
            FOREIGN KEY (codigo_interno_id) REFERENCES codigos_examenes(id)
        )
        ''')
        
        # Índices para búsquedas rápidas
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_codigos_tipo ON codigos_examenes(tipo)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_codigos_subtipo ON codigos_examenes(subtipo)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_centros_nombre ON centros_medicos(nombre)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_salas_centro ON salas_adquisicion(centro_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_historico_centro ON historico_examenes(centro_medico_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_historico_sala ON historico_examenes(sala_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_historico_fecha ON historico_examenes(fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_patrones_tipo ON patrones_clasificacion(tipo)')
        
        conn.commit()
        conn.close()
    
    def cargar_patrones(self, tipo):
        """Carga los patrones de clasificación desde la base de datos."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT patron FROM patrones_clasificacion WHERE tipo = ?', (tipo,))
        patrones = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        # Si no hay patrones en la DB, cargar patrones predeterminados
        if not patrones:
            patrones = self.cargar_patrones_predeterminados(tipo)
            if patrones:
                self.guardar_patrones(patrones, tipo)
        
        return patrones
    
    def cargar_patrones_predeterminados(self, tipo):
        """Carga patrones predeterminados según el tipo."""
        patrones = []
        
        if tipo == 'rx_especial':
            patrones = [
                'columna completa', 'pelvis cadera femur', 
                'torax ap lateral', 'columna dorsolumbar'
            ]
        elif tipo == 'proc_complejo':
            patrones = [
                'biopsia', 'puncion', 'infiltracion', 
                'drenaje', 'ablacion', 'nefrostomia'
            ]
        
        return patrones
    
    def guardar_patrones(self, patrones, tipo):
        """Guarda los patrones en la base de datos."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        for patron in patrones:
            cursor.execute(
                'INSERT OR IGNORE INTO patrones_clasificacion (patron, tipo) VALUES (?, ?)',
                (patron, tipo)
            )
        
        conn.commit()
        conn.close()
    
    def generar_codigo(self, nombre_examen):
        """Genera un código único para un examen basado en su nombre."""
        # Limpiar y normalizar el nombre
        nombre_limpio = self.normalizar_texto(nombre_examen)
        palabras = nombre_limpio.split()
        
        # Generar prefijo según el tipo de examen
        tipo_info = self.clasificar_examen(nombre_examen)
        prefijo = self.generar_prefijo(tipo_info['tipo'], tipo_info['subtipo'])
        
        # Generar código base con iniciales o partes significativas
        if len(palabras) >= 2:
            # Usar las primeras letras de las palabras principales 
            codigo_base = ''.join([p[0] for p in palabras[:3] if len(p) > 0])
            
            # Si tenemos menos de 3 caracteres, agregar más letras
            if len(codigo_base) < 3:
                codigo_base = ''.join([p[:2] for p in palabras[:2] if len(p) > 1])
        else:
            # Si solo hay una palabra, usar primeras letras
            codigo_base = palabras[0][:3] if palabras and len(palabras[0]) >= 3 else "EXM"
        
        # Generar hash único (últimos 3 caracteres) para diferenciación
        hash_corto = hashlib.md5(nombre_examen.encode()).hexdigest()[:3]
        
        # Combinar elementos y convertir a mayúsculas
        codigo_base = (prefijo + codigo_base + hash_corto).upper()
        
        # Verificar unicidad en la base de datos
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT codigo FROM codigos_examenes WHERE codigo = ?', (codigo_base,))
        if cursor.fetchone():
            # Si ya existe, agregar un contador incremental
            contador = 1
            while True:
                nuevo_codigo = f"{codigo_base}{contador}"
                cursor.execute('SELECT codigo FROM codigos_examenes WHERE codigo = ?', (nuevo_codigo,))
                if not cursor.fetchone():
                    codigo_base = nuevo_codigo
                    break
                contador += 1
        
        conn.close()
        return codigo_base
    
    def normalizar_texto(self, texto):
        """Normaliza un texto para procesamiento (quita acentos y caracteres especiales)."""
        # Convertir a minúsculas
        texto = texto.lower()
        
        # Reemplazar caracteres especiales y acentos
        reemplazos = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ü': 'u', 'ñ': 'n', '@': 'a', '&': 'y'
        }
        for origen, destino in reemplazos.items():
            texto = texto.replace(origen, destino)
        
        # Eliminar caracteres no alfanuméricos
        texto = re.sub(r'[^\w\s]', '', texto)
        
        return texto
    
    def generar_prefijo(self, tipo, subtipo):
        """Genera el prefijo del código según tipo y subtipo."""
        prefijos = {
            'TAC': {
                'NORMAL': 'T',
                'CONTRASTADO': 'TC'
            },
            'RX': {
                'NORMAL': 'R',
                'ESPECIAL': 'RE',
                'CONTRASTADO': 'RC'
            },
            'RM': {
                'NORMAL': 'M',
                'CONTRASTADO': 'MC',
                'ESPECIAL': 'ME'
            },
            'US': {
                'NORMAL': 'U',
                'DOPPLER': 'UD',
                'ESPECIAL': 'UE'
            },
            'PET': {
                'NORMAL': 'P',
                'CT': 'PC'
            },
            'PROC': {
                'SIMPLE': 'PS',
                'COMPLEJO': 'PC',
                'AVANZADO': 'PA'
            }
        }
        
        # Obtener el prefijo según tipo/subtipo
        if tipo in prefijos and subtipo in prefijos[tipo]:
            return prefijos[tipo][subtipo]
        
        # Prefijo predeterminado para tipos desconocidos
        return 'X'
    
    def clasificar_examen(self, nombre_examen):
        """Clasifica un examen según su tipo y subtipo."""
        nombre = nombre_examen.lower()
        
        # Detectar tipo principal
        if 'tac' in nombre or 'tomograf' in nombre or 'tomo' in nombre:
            tipo = 'TAC'
            # Para TAC, usar el nombre completo como subtipo
            subtipo = nombre_examen.upper()
        
        elif 'rx' in nombre or 'radio' in nombre or 'rayos' in nombre:
            tipo = 'RX'
            
            # Verificar RX especial
            es_especial = False
            for patron in self.patrones_rx_especial:
                if patron.lower() in nombre:
                    es_especial = True
                    break
            
            # Verificar si es contrastado
            if 'contraste' in nombre or 'contrast' in nombre:
                subtipo = 'CONTRASTADO'
            elif es_especial:
                subtipo = 'ESPECIAL'
            else:
                subtipo = 'NORMAL'
        
        elif 'resonancia' in nombre or 'rm' in nombre or 'rmn' in nombre:
            tipo = 'RM'
            
            if 'contraste' in nombre or 'contrast' in nombre:
                subtipo = 'CONTRASTADO'
            elif 'angio' in nombre or 'espec' in nombre:
                subtipo = 'ESPECIAL'
            else:
                subtipo = 'NORMAL'
        
        elif 'ultrasonido' in nombre or 'ecograf' in nombre or 'eco' in nombre or 'us' in nombre:
            tipo = 'US'
            
            if 'doppler' in nombre:
                subtipo = 'DOPPLER'
            elif 'especial' in nombre or '4d' in nombre or 'avanz' in nombre:
                subtipo = 'ESPECIAL'
            else:
                subtipo = 'NORMAL'
        
        elif 'pet' in nombre or 'positron' in nombre:
            tipo = 'PET'
            
            if 'ct' in nombre or 'tac' in nombre or 'tomo' in nombre:
                subtipo = 'CT'
            else:
                subtipo = 'NORMAL'
        
        elif 'proc' in nombre or 'biopsia' in nombre or 'puncion' in nombre or 'drenaje' in nombre:
            tipo = 'PROC'
            
            # Verificar procedimiento complejo
            es_complejo = False
            for patron in self.patrones_proc_complejo:
                if patron.lower() in nombre:
                    es_complejo = True
                    break
            
            if es_complejo:
                subtipo = 'COMPLEJO'
            elif 'avanz' in nombre or 'espec' in nombre:
                subtipo = 'AVANZADO'
            else:
                subtipo = 'SIMPLE'
        
        else:
            # Tipo desconocido
            tipo = 'OTRO'
            subtipo = 'GENERAL'
        
        # Estimar complejidad (1-5)
        complejidad = self.estimar_complejidad(nombre, tipo, subtipo)
        
        # Estimar tiempo en minutos
        tiempo_estimado = self.estimar_tiempo(nombre, tipo, subtipo)
        
        return {
            'tipo': tipo,
            'subtipo': subtipo,
            'complejidad': complejidad,
            'tiempo_estimado': tiempo_estimado
        }
    
    def estimar_complejidad(self, nombre, tipo, subtipo):
        """Estima la complejidad del examen en escala 1-5."""
        # Valores base por tipo
        complejidad_base = {
            'RX': 1,
            'US': 2,
            'TAC': 3,
            'RM': 4,
            'PET': 5,
            'PROC': 3,
            'OTRO': 2
        }
        
        # Ajustes por subtipo
        ajustes_subtipo = {
            'NORMAL': 0,
            'CONTRASTADO': 1,
            'ESPECIAL': 1,
            'DOPPLER': 1,
            'COMPLEJO': 1,
            'AVANZADO': 2,
            'CT': 1
        }
        
        # Palabras clave que indican mayor complejidad
        palabras_complejas = [
            'especial', 'completo', 'compleja', 'multiple', 
            'detallado', 'avanzado', 'dinamico', 'multiplanar'
        ]
        
        # Calcular base + ajustes
        complejidad = complejidad_base.get(tipo, 2)
        complejidad += ajustes_subtipo.get(subtipo, 0)
        
        # Ajuste por palabras clave en el nombre
        for palabra in palabras_complejas:
            if palabra in nombre.lower():
                complejidad += 1
                break
        
        # Limitar a escala 1-5
        return max(1, min(5, complejidad))
    
    def estimar_tiempo(self, nombre, tipo, subtipo):
        """Estima el tiempo en minutos que toma el examen."""
        # Tiempos base por tipo
        tiempo_base = {
            'RX': 10,
            'US': 20,
            'TAC': 15,
            'RM': 30,
            'PET': 60,
            'PROC': 30,
            'OTRO': 20
        }
        
        # Ajustes por subtipo
        ajustes_subtipo = {
            'NORMAL': 0,
            'CONTRASTADO': 15,
            'ESPECIAL': 10,
            'DOPPLER': 10,
            'COMPLEJO': 30,
            'AVANZADO': 45,
            'CT': 15
        }
        
        # Calcular tiempo estimado
        tiempo = tiempo_base.get(tipo, 20)
        tiempo += ajustes_subtipo.get(subtipo, 0)
        
        # Ajustes adicionales basados en palabras clave
        if 'contraste' in nombre.lower():
            tiempo += 10
        if 'urgencia' in nombre.lower() or 'urgente' in nombre.lower():
            tiempo = int(tiempo * 0.8)  # 20% más rápido en urgencias
        
        return tiempo
    
    def registrar_examen(self, nombre_examen):
        """Registra un nuevo examen o actualiza un examen existente."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si ya existe
        cursor.execute('SELECT id, codigo, conteo FROM codigos_examenes WHERE nombre = ?', (nombre_examen,))
        resultado = cursor.fetchone()
        
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if resultado:
            # Actualizar examen existente
            examen_id, codigo, conteo = resultado
            
            # Incrementar contador
            nuevo_conteo = conteo + 1
            
            cursor.execute(
                'UPDATE codigos_examenes SET conteo = ?, ultima_actualizacion = ? WHERE id = ?',
                (nuevo_conteo, fecha_actual, examen_id)
            )
            
            conn.commit()
            conn.close()
            
            return {
                'codigo': codigo,
                'nuevo': False,
                'conteo': nuevo_conteo
            }
        else:
            # Clasificar examen
            clasificacion = self.clasificar_examen(nombre_examen)
            
            # Generar código único
            codigo = self.generar_codigo(nombre_examen)
            
            # Insertar nuevo examen
            cursor.execute(
                '''INSERT INTO codigos_examenes 
                   (nombre, codigo, tipo, subtipo, complejidad, tiempo_estimado, 
                    conteo, fecha_creacion, ultima_actualizacion)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (nombre_examen, codigo, clasificacion['tipo'], clasificacion['subtipo'],
                 clasificacion['complejidad'], clasificacion['tiempo_estimado'],
                 1, fecha_actual, fecha_actual)
            )
            
            # Obtener el ID del nuevo examen
            examen_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return {
                'codigo': codigo,
                'nuevo': True,
                'conteo': 1,
                'id': examen_id
            }
    
    def registrar_centro_medico(self, nombre, codigo=None, direccion=None, region=None):
        """Registra un nuevo centro médico o actualiza uno existente."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si ya existe
        cursor.execute('SELECT id FROM centros_medicos WHERE nombre = ?', (nombre,))
        resultado = cursor.fetchone()
        
        if resultado:
            # Actualizar existente
            centro_id = resultado[0]
            cursor.execute(
                '''UPDATE centros_medicos 
                   SET codigo = ?, direccion = ?, region = ? 
                   WHERE id = ?''',
                (codigo, direccion, region, centro_id)
            )
            conn.commit()
            conn.close()
            return centro_id, False  # ID, no es nuevo
        else:
            # Insertar nuevo
            cursor.execute(
                '''INSERT INTO centros_medicos 
                   (nombre, codigo, direccion, region, conteo) 
                   VALUES (?, ?, ?, ?, 0)''',
                (nombre, codigo, direccion, region)
            )
            centro_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Actualizar caché
            self.centros_adquisicion[nombre] = centro_id
            
            return centro_id, True  # ID, es nuevo
    
    def registrar_sala(self, nombre, centro_id=None, centro_nombre=None, tipo_equipo=None):
        """Registra una nueva sala de adquisición o actualiza una existente."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Obtener ID del centro si se proporcionó el nombre
        if not centro_id and centro_nombre:
            # Verificar si está en caché
            if centro_nombre in self.centros_adquisicion:
                centro_id = self.centros_adquisicion[centro_nombre]
            else:
                # Buscar en la base de datos
                cursor.execute('SELECT id FROM centros_medicos WHERE nombre = ?', (centro_nombre,))
                resultado = cursor.fetchone()
                if resultado:
                    centro_id = resultado[0]
                    # Actualizar caché
                    self.centros_adquisicion[centro_nombre] = centro_id
                else:
                    # Registrar nuevo centro
                    centro_id, _ = self.registrar_centro_medico(centro_nombre)
        
        # Verificar si la sala ya existe
        cursor.execute('SELECT id FROM salas_adquisicion WHERE nombre = ?', (nombre,))
        resultado = cursor.fetchone()
        
        if resultado:
            # Actualizar sala existente
            sala_id = resultado[0]
            cursor.execute(
                '''UPDATE salas_adquisicion 
                   SET centro_id = ?, tipo_equipo = ? 
                   WHERE id = ?''',
                (centro_id, tipo_equipo, sala_id)
            )
            conn.commit()
            conn.close()
            return sala_id, False  # ID, no es nueva
        else:
            # Insertar nueva sala
            cursor.execute(
                '''INSERT INTO salas_adquisicion 
                   (nombre, centro_id, tipo_equipo, conteo) 
                   VALUES (?, ?, ?, 0)''',
                (nombre, centro_id, tipo_equipo)
            )
            sala_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Actualizar caché
            self.salas_adquisicion[nombre] = {
                'id': sala_id,
                'centro_id': centro_id
            }
            
            return sala_id, True  # ID, es nueva
    
    def registrar_uso_examen(self, codigo_examen, centro_medico=None, sala=None, tiempo_real=None, observaciones=None):
        """Registra el uso de un examen en el histórico con centro y sala."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si el código existe
        cursor.execute('SELECT id FROM codigos_examenes WHERE codigo = ?', (codigo_examen,))
        resultado = cursor.fetchone()
        
        if not resultado:
            conn.close()
            return False, "Código de examen no encontrado"
        
        examen_id = resultado[0]
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Obtener o registrar el centro médico y la sala
        centro_id = None
        sala_id = None
        
        if centro_medico:
            # Buscar o registrar centro
            centro_id, _ = self.registrar_centro_medico(centro_medico)
            
            # Actualizar contador de centro
            cursor.execute('UPDATE centros_medicos SET conteo = conteo + 1 WHERE id = ?', (centro_id,))
        
        if sala:
            # Buscar o registrar sala
            sala_id, _ = self.registrar_sala(sala, centro_id, centro_medico)
            
            # Actualizar contador de sala
            cursor.execute('UPDATE salas_adquisicion SET conteo = conteo + 1 WHERE id = ?', (sala_id,))
        
        # Registrar en histórico
        cursor.execute(
            '''INSERT INTO historico_examenes 
               (codigo_id, fecha, centro_medico_id, sala_id, tiempo_real, observaciones)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (examen_id, fecha_actual, centro_id, sala_id, tiempo_real, observaciones)
        )
        
        # Actualizar contador en la tabla principal
        cursor.execute(
            'UPDATE codigos_examenes SET conteo = conteo + 1, ultima_actualizacion = ? WHERE id = ?',
            (fecha_actual, examen_id)
        )
        
        conn.commit()
        conn.close()
        
        return True, "Uso de examen registrado correctamente"
    
    def buscar_examenes(self, texto_busqueda, tipo=None, subtipo=None, limit=100):
        """Busca exámenes por texto, tipo o subtipo."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Construir consulta base
        query = '''SELECT id, nombre, codigo, tipo, subtipo, complejidad, 
                         tiempo_estimado, conteo, fecha_creacion
                  FROM codigos_examenes WHERE '''
        
        params = []
        condiciones = []
        
        # Condición por texto
        if texto_busqueda:
            condiciones.append("(nombre LIKE ? OR codigo LIKE ?)")
            params.extend([f"%{texto_busqueda}%", f"%{texto_busqueda}%"])
        
        # Condición por tipo
        if tipo:
            condiciones.append("tipo = ?")
            params.append(tipo)
        
        # Condición por subtipo
        if subtipo:
            condiciones.append("subtipo = ?")
            params.append(subtipo)
        
        # Si no hay condiciones, mostrar todos
        if not condiciones:
            condiciones = ["1=1"]
        
        # Combinar condiciones con AND
        query += " AND ".join(condiciones)
        
        # Ordenar por frecuencia de uso (conteo) descendente
        query += " ORDER BY conteo DESC LIMIT ?"
        params.append(limit)
        
        # Ejecutar consulta
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        
        conn.close()
        
        # Convertir a lista de diccionarios
        examenes = []
        for r in resultados:
            examenes.append({
                'id': r[0],
                'nombre': r[1],
                'codigo': r[2],
                'tipo': r[3],
                'subtipo': r[4],
                'complejidad': r[5],
                'tiempo_estimado': r[6],
                'conteo': r[7],
                'fecha_creacion': r[8]
            })
        
        return examenes
    
    def obtener_examen_por_codigo(self, codigo):
        """Obtiene los detalles de un examen por su código."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT id, nombre, codigo, tipo, subtipo, complejidad, 
                     tiempo_estimado, conteo, fecha_creacion, ultima_actualizacion
              FROM codigos_examenes WHERE codigo = ?''',
            (codigo,)
        )
        
        resultado = cursor.fetchone()
        
        if not resultado:
            conn.close()
            return None
        
        # Convertir a diccionario
        examen = {
            'id': resultado[0],
            'nombre': resultado[1],
            'codigo': resultado[2],
            'tipo': resultado[3],
            'subtipo': resultado[4],
            'complejidad': resultado[5],
            'tiempo_estimado': resultado[6],
            'conteo': resultado[7],
            'fecha_creacion': resultado[8],
            'ultima_actualizacion': resultado[9]
        }
        
        # Obtener historial de uso
        cursor.execute(
            '''SELECT fecha, centro_medico, sala, tiempo_real 
               FROM historico_examenes 
               WHERE codigo_id = ? 
               ORDER BY fecha DESC LIMIT 10''',
            (examen['id'],)
        )
        
        historial = []
        for h in cursor.fetchall():
            historial.append({
                'fecha': h[0],
                'centro_medico': h[1],
                'sala': h[2],
                'tiempo_real': h[3]
            })
        
        examen['historial'] = historial
        
        conn.close()
        return examen
    
    def validar_codigo(self, codigo):
        """Valida si un código es válido y corresponde a un examen registrado."""
        if not codigo or len(codigo) < 3:
            return False, "Código demasiado corto"
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM codigos_examenes WHERE codigo = ?', (codigo,))
        
        if cursor.fetchone():
            conn.close()
            return True, "Código válido"
        
        conn.close()
        return False, "Código no encontrado en el sistema"
    
    def estadisticas_codigos(self):
        """Obtiene estadísticas generales sobre los códigos de exámenes."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Total de códigos
        cursor.execute('SELECT COUNT(*) FROM codigos_examenes')
        total_codigos = cursor.fetchone()[0]
        
        # Total por tipo
        cursor.execute('SELECT tipo, COUNT(*) FROM codigos_examenes GROUP BY tipo')
        total_por_tipo = {tipo: count for tipo, count in cursor.fetchall()}
        
        # Total por subtipo
        cursor.execute('SELECT subtipo, COUNT(*) FROM codigos_examenes GROUP BY subtipo')
        total_por_subtipo = {subtipo: count for subtipo, count in cursor.fetchall()}
        
        # Los 5 exámenes más comunes
        cursor.execute(
            '''SELECT nombre, codigo, tipo, conteo 
               FROM codigos_examenes 
               ORDER BY conteo DESC LIMIT 5'''
        )
        
        examenes_comunes = []
        for r in cursor.fetchall():
            examenes_comunes.append({
                'nombre': r[0],
                'codigo': r[1],
                'tipo': r[2],
                'conteo': r[3]
            })
        
        # Total de registros en histórico
        cursor.execute('SELECT COUNT(*) FROM historico_examenes')
        total_historico = cursor.fetchone()[0]
        
        # Estadísticas de tiempo
        cursor.execute(
            '''SELECT AVG(tiempo_real) as promedio, 
                      MIN(tiempo_real) as minimo,
                      MAX(tiempo_real) as maximo
               FROM historico_examenes 
               WHERE tiempo_real IS NOT NULL'''
        )
        
        tiempo_stats = cursor.fetchone()
        if tiempo_stats and tiempo_stats[0]:
            tiempo_promedio = round(tiempo_stats[0], 2)
            tiempo_minimo = tiempo_stats[1]
            tiempo_maximo = tiempo_stats[2]
        else:
            tiempo_promedio = tiempo_minimo = tiempo_maximo = None
        
        conn.close()
        
        return {
            'total_codigos': total_codigos,
            'por_tipo': total_por_tipo,
            'por_subtipo': total_por_subtipo,
            'examenes_comunes': examenes_comunes,
            'total_historico': total_historico,
            'tiempo': {
                'promedio': tiempo_promedio,
                'minimo': tiempo_minimo,
                'maximo': tiempo_maximo
            }
        }
    
    def agregar_mapeo_externo(self, codigo_interno, sistema_externo, codigo_externo):
        """Agrega un mapeo entre código interno y sistema externo."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si el código interno existe
        cursor.execute('SELECT id FROM codigos_examenes WHERE codigo = ?', (codigo_interno,))
        resultado = cursor.fetchone()
        
        if not resultado:
            conn.close()
            return False, "Código interno no encontrado"
        
        codigo_id = resultado[0]
        
        # Verificar si ya existe el mapeo
        cursor.execute(
            '''SELECT id FROM mapeo_codigos 
               WHERE codigo_interno_id = ? AND sistema_externo = ?''',
            (codigo_id, sistema_externo)
        )
        
        if cursor.fetchone():
            # Actualizar mapeo existente
            cursor.execute(
                '''UPDATE mapeo_codigos SET codigo_externo = ?
                   WHERE codigo_interno_id = ? AND sistema_externo = ?''',
                (codigo_externo, codigo_id, sistema_externo)
            )
        else:
            # Insertar nuevo mapeo
            cursor.execute(
                '''INSERT INTO mapeo_codigos 
                   (codigo_interno_id, sistema_externo, codigo_externo)
                   VALUES (?, ?, ?)''',
                (codigo_id, sistema_externo, codigo_externo)
            )
        
        conn.commit()
        conn.close()
        
        return True, "Mapeo agregado correctamente"
    
    def obtener_mapeos_externos(self, codigo_interno):
        """Obtiene todos los mapeos externos para un código interno."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Obtener ID del código interno
        cursor.execute('SELECT id FROM codigos_examenes WHERE codigo = ?', (codigo_interno,))
        resultado = cursor.fetchone()
        
        if not resultado:
            conn.close()
            return []
        
        codigo_id = resultado[0]
        
        # Obtener todos los mapeos
        cursor.execute(
            '''SELECT sistema_externo, codigo_externo 
               FROM mapeo_codigos 
               WHERE codigo_interno_id = ?''',
            (codigo_id,)
        )
        
        mapeos = []
        for r in cursor.fetchall():
            mapeos.append({
                'sistema': r[0],
                'codigo': r[1]
            })
        
        conn.close()
        return mapeos
    
    def exportar_codigos_json(self, ruta_archivo=None):
        """Exporta todos los códigos a un archivo JSON."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Obtener todos los códigos
        cursor.execute(
            '''SELECT id, nombre, codigo, tipo, subtipo, complejidad, 
                     tiempo_estimado, conteo, fecha_creacion, ultima_actualizacion
               FROM codigos_examenes'''
        )
        
        codigos = []
        for r in cursor.fetchall():
            codigo_id = r[0]
            
            # Obtener mapeos para este código
            cursor.execute(
                '''SELECT sistema_externo, codigo_externo 
                   FROM mapeo_codigos 
                   WHERE codigo_interno_id = ?''',
                (codigo_id,)
            )
            
            mapeos = {}
            for m in cursor.fetchall():
                mapeos[m[0]] = m[1]
            
            codigos.append({
                'nombre': r[1],
                'codigo': r[2],
                'tipo': r[3],
                'subtipo': r[4],
                'complejidad': r[5],
                'tiempo_estimado': r[6],
                'conteo': r[7],
                'fecha_creacion': r[8],
                'ultima_actualizacion': r[9],
                'mapeos': mapeos
            })
        
        conn.close()
        
        # Si no se especifica ruta, usar predeterminada
        if not ruta_archivo:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            ruta_archivo = os.path.join(REGISTROS_DIR, f"exportacion_codigos_{timestamp}.json")
        
        # Guardar a archivo JSON
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(codigos, f, indent=2, ensure_ascii=False)
        
        return ruta_archivo
    
    def importar_codigos_json(self, ruta_archivo):
        """Importa códigos desde un archivo JSON."""
        if not os.path.exists(ruta_archivo):
            return False, f"El archivo {ruta_archivo} no existe"
        
        try:
            # Cargar datos del JSON
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                codigos = json.load(f)
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            nuevos = 0
            actualizados = 0
            
            # Procesar cada código
            for codigo_data in codigos:
                # Verificar si ya existe
                cursor.execute('SELECT id FROM codigos_examenes WHERE codigo = ?', (codigo_data['codigo'],))
                resultado = cursor.fetchone()
                
                if resultado:
                    # Actualizar código existente
                    codigo_id = resultado[0]
                    
                    cursor.execute(
                        '''UPDATE codigos_examenes SET 
                           tipo = ?, subtipo = ?, complejidad = ?, 
                           tiempo_estimado = ?, conteo = ?
                           WHERE id = ?''',
                        (codigo_data['tipo'], codigo_data['subtipo'], 
                         codigo_data['complejidad'], codigo_data['tiempo_estimado'],
                         codigo_data['conteo'], codigo_id)
                    )
                    
                    actualizados += 1
                else:
                    # Insertar nuevo código
                    cursor.execute(
                        '''INSERT INTO codigos_examenes 
                           (nombre, codigo, tipo, subtipo, complejidad, 
                            tiempo_estimado, conteo, fecha_creacion, ultima_actualizacion)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (codigo_data['nombre'], codigo_data['codigo'], 
                         codigo_data['tipo'], codigo_data['subtipo'],
                         codigo_data['complejidad'], codigo_data['tiempo_estimado'],
                         codigo_data['conteo'], 
                         codigo_data.get('fecha_creacion', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                         codigo_data.get('ultima_actualizacion', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    )
                    
                    codigo_id = cursor.lastrowid
                    nuevos += 1
                
                # Procesar mapeos si existen
                if 'mapeos' in codigo_data and codigo_data['mapeos']:
                    for sistema, codigo_externo in codigo_data['mapeos'].items():
                        cursor.execute(
                            '''INSERT OR REPLACE INTO mapeo_codigos 
                               (codigo_interno_id, sistema_externo, codigo_externo)
                               VALUES (?, ?, ?)''',
                            (codigo_id, sistema, codigo_externo)
                        )
            
            conn.commit()
            conn.close()
            
            return True, f"Importación completada: {nuevos} nuevos, {actualizados} actualizados"
        
        except Exception as e:
            return False, f"Error al importar: {str(e)}"
    
    def buscar_examenes_por_centro(self, centro_medico=None, sala=None, fecha_inicio=None, fecha_fin=None, limit=100):
        """Busca exámenes por centro médico y/o sala de adquisición con filtro por fechas."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Construir consulta base
        query = '''
        SELECT e.id, e.nombre, e.codigo, e.tipo, e.subtipo, 
               c.nombre as centro, s.nombre as sala, h.fecha, h.tiempo_real
        FROM historico_examenes h
        JOIN codigos_examenes e ON h.codigo_id = e.id
        LEFT JOIN centros_medicos c ON h.centro_medico_id = c.id
        LEFT JOIN salas_adquisicion s ON h.sala_id = s.id
        WHERE 1=1
        '''
        
        params = []
        
        # Aplicar filtros
        if centro_medico:
            query += " AND c.nombre LIKE ?"
            params.append(f"%{centro_medico}%")
            
        if sala:
            query += " AND s.nombre LIKE ?"
            params.append(f"%{sala}%")
            
        if fecha_inicio:
            query += " AND h.fecha >= ?"
            params.append(fecha_inicio)
            
        if fecha_fin:
            query += " AND h.fecha <= ?"
            params.append(fecha_fin)
            
        # Ordenar por fecha descendente
        query += " ORDER BY h.fecha DESC LIMIT ?"
        params.append(limit)
        
        # Ejecutar consulta
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        examenes = []
        for r in resultados:
            examenes.append({
                'id': r[0],
                'nombre': r[1],
                'codigo': r[2],
                'tipo': r[3],
                'subtipo': r[4],
                'centro': r[5],
                'sala': r[6],
                'fecha': r[7],
                'tiempo_real': r[8]
            })
        
        conn.close()
        return examenes
    
    def obtener_estadisticas_centro(self, centro_medico=None):
        """Obtiene estadísticas de exámenes por centro médico."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        stats = {}
        
        # Si se especifica un centro, buscar su ID
        centro_id = None
        if centro_medico:
            cursor.execute('SELECT id FROM centros_medicos WHERE nombre = ?', (centro_medico,))
            resultado = cursor.fetchone()
            if resultado:
                centro_id = resultado[0]
            else:
                conn.close()
                return {'error': f"Centro médico '{centro_medico}' no encontrado"}
        
        # Estadísticas por centro médico
        if centro_id:
            # Estadísticas para un centro específico
            cursor.execute('''
                SELECT c.nombre, COUNT(h.id) as total_examenes,
                       SUM(CASE WHEN e.tipo = 'TAC' THEN 1 ELSE 0 END) as total_tac,
                       SUM(CASE WHEN e.tipo = 'RX' THEN 1 ELSE 0 END) as total_rx,
                       COUNT(DISTINCT s.id) as total_salas
                FROM centros_medicos c
                LEFT JOIN historico_examenes h ON h.centro_medico_id = c.id
                LEFT JOIN codigos_examenes e ON h.codigo_id = e.id
                LEFT JOIN salas_adquisicion s ON h.sala_id = s.id
                WHERE c.id = ?
                GROUP BY c.id
            ''', (centro_id,))
            
            row = cursor.fetchone()
            if row:
                stats['centro'] = {
                    'nombre': row[0],
                    'total_examenes': row[1],
                    'total_tac': row[2],
                    'total_rx': row[3],
                    'total_salas': row[4]
                }
                
                # Examenes por sala para este centro
                cursor.execute('''
                    SELECT s.nombre, COUNT(h.id) as total,
                           SUM(CASE WHEN e.tipo = 'TAC' THEN 1 ELSE 0 END) as tac,
                           SUM(CASE WHEN e.tipo = 'RX' THEN 1 ELSE 0 END) as rx
                    FROM salas_adquisicion s
                    LEFT JOIN historico_examenes h ON h.sala_id = s.id
                    LEFT JOIN codigos_examenes e ON h.codigo_id = e.id
                    WHERE s.centro_id = ?
                    GROUP BY s.id
                    ORDER BY total DESC
                ''', (centro_id,))
                
                stats['salas'] = []
                for r in cursor.fetchall():
                    stats['salas'].append({
                        'nombre': r[0],
                        'total': r[1],
                        'tac': r[2],
                        'rx': r[3]
                    })
                
                # Examenes más comunes en este centro
                cursor.execute('''
                    SELECT e.nombre, e.codigo, e.tipo, COUNT(h.id) as total
                    FROM historico_examenes h
                    JOIN codigos_examenes e ON h.codigo_id = e.id
                    WHERE h.centro_medico_id = ?
                    GROUP BY e.id
                    ORDER BY total DESC
                    LIMIT 10
                ''', (centro_id,))
                
                stats['examenes_comunes'] = []
                for r in cursor.fetchall():
                    stats['examenes_comunes'].append({
                        'nombre': r[0],
                        'codigo': r[1],
                        'tipo': r[2],
                        'total': r[3]
                    })
            else:
                stats['centro'] = {
                    'nombre': centro_medico,
                    'total_examenes': 0,
                    'total_salas': 0
                }
        else:
            # Estadísticas para todos los centros
            cursor.execute('''
                SELECT c.id, c.nombre, COUNT(h.id) as total_examenes
                FROM centros_medicos c
                LEFT JOIN historico_examenes h ON h.centro_medico_id = c.id
                GROUP BY c.id
                ORDER BY total_examenes DESC
            ''')
            
            stats['centros'] = []
            for r in cursor.fetchall():
                stats['centros'].append({
                    'id': r[0],
                    'nombre': r[1],
                    'total_examenes': r[2]
                })
            
            # Total global
            cursor.execute('SELECT COUNT(*) FROM historico_examenes')
            stats['total_global'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def procesar_dataframe(self, df):
        """Procesa un DataFrame para extraer y registrar códigos de exámenes."""
        if 'Nombre del procedimiento' not in df.columns:
            return False, "El DataFrame debe contener la columna 'Nombre del procedimiento'"
        
        nuevos_examenes = 0
        actualizados = 0
        nuevos_centros = 0
        nuevas_salas = 0
        usos_registrados = 0
        errores = 0
        
        # Procesar centros médicos si existe la columna
        if 'Centro médico' in df.columns:
            for centro in df['Centro médico'].dropna().unique():
                try:
                    _, es_nuevo = self.registrar_centro_medico(centro)
                    if es_nuevo:
                        nuevos_centros += 1
                except Exception as e:
                    print(f"Error al registrar centro '{centro}': {e}")
        
        # Procesar salas si existe la columna
        if 'Sala de adquisición' in df.columns:
            for sala in df['Sala de adquisición'].dropna().unique():
                try:
                    # Obtener centro asociado si existe
                    centro_medico = None
                    if 'Centro médico' in df.columns:
                        # Buscar el primer registro que utiliza esta sala para obtener su centro
                        filtro = df[df['Sala de adquisición'] == sala]
                        if not filtro.empty and 'Centro médico' in filtro.columns:
                            centro_medico = filtro.iloc[0]['Centro médico']
                    
                    # Detectar tipo de equipo por nombre de sala
                    tipo_equipo = None
                    sala_lower = sala.lower()
                    if 'tac' in sala_lower or 'tc' in sala_lower:
                        tipo_equipo = 'TAC'
                    elif 'rx' in sala_lower or 'rayos' in sala_lower:
                        tipo_equipo = 'RX'
                    elif 'rm' in sala_lower or 'resonancia' in sala_lower:
                        tipo_equipo = 'RM'
                    elif 'us' in sala_lower or 'eco' in sala_lower:
                        tipo_equipo = 'US'
                    
                    _, es_nueva = self.registrar_sala(sala, centro_nombre=centro_medico, tipo_equipo=tipo_equipo)
                    if es_nueva:
                        nuevas_salas += 1
                except Exception as e:
                    print(f"Error al registrar sala '{sala}': {e}")
        
        # Procesar exámenes
        for nombre_examen in df['Nombre del procedimiento'].dropna().unique():
            try:
                resultado = self.registrar_examen(nombre_examen)
                if resultado['nuevo']:
                    nuevos_examenes += 1
                else:
                    actualizados += 1
            except Exception as e:
                errores += 1
                print(f"Error al procesar examen '{nombre_examen}': {e}")
        
        # Registrar usos si existen las columnas necesarias
        if 'Nombre del procedimiento' in df.columns and 'Sala de adquisición' in df.columns:
            for _, row in df.iterrows():
                try:
                    nombre_examen = row['Nombre del procedimiento']
                    if pd.isna(nombre_examen):
                        continue
                        
                    sala = row['Sala de adquisición'] if 'Sala de adquisición' in row and not pd.isna(row['Sala de adquisición']) else None
                    centro_medico = row['Centro médico'] if 'Centro médico' in row and not pd.isna(row['Centro médico']) else None
                    
                    # Obtener fecha si existe
                    fecha = None
                    tiempo_real = None
                    observaciones = None
                    
                    if 'Fecha del procedimiento' in row:
                        fecha = row['Fecha del procedimiento']
                    
                    if 'Duración' in row and not pd.isna(row['Duración']):
                        tiempo_real = row['Duración']
                    
                    # Obtener código
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute('SELECT codigo FROM codigos_examenes WHERE nombre = ?', (nombre_examen,))
                    resultado = cursor.fetchone()
                    conn.close()
                    
                    if resultado:
                        codigo = resultado[0]
                        # Registrar uso
                        self.registrar_uso_examen(
                            codigo, 
                            centro_medico=centro_medico, 
                            sala=sala, 
                            tiempo_real=tiempo_real,
                            observaciones=observaciones
                        )
                        usos_registrados += 1
                except Exception as e:
                    print(f"Error al registrar uso: {e}")
        
        return True, f"Procesamiento completado: {nuevos_examenes} exámenes nuevos, {actualizados} actualizados, {nuevos_centros} centros nuevos, {nuevas_salas} salas nuevas, {usos_registrados} usos registrados, {errores} errores"


# Función main para uso en línea de comandos
def main():
    """Función principal para uso del sistema desde línea de comandos."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sistema de Codificación de Exámenes Médicos")
    parser.add_argument('--csv', help='Ruta al archivo CSV para procesar')
    parser.add_argument('--buscar', help='Buscar exámenes por texto')
    parser.add_argument('--tipo', help='Filtrar por tipo de examen')
    parser.add_argument('--codigo', help='Buscar un código específico')
    parser.add_argument('--centro', help='Buscar exámenes por centro médico')
    parser.add_argument('--sala', help='Buscar exámenes por sala de adquisición')
    parser.add_argument('--estadisticas', action='store_true', help='Mostrar estadísticas generales del sistema')
    parser.add_argument('--estadisticas-centro', help='Mostrar estadísticas de un centro médico específico')
    parser.add_argument('--exportar', help='Exportar códigos a JSON (ruta del archivo)')
    parser.add_argument('--importar', help='Importar códigos desde JSON (ruta del archivo)')
    
    args = parser.parse_args()
    sistema = CodigosExamenes()
    
    # Procesar CSV
    if args.csv:
        if os.path.exists(args.csv):
            try:
                df = pd.read_csv(args.csv)
                exito, mensaje = sistema.procesar_dataframe(df)
                print(mensaje)
            except Exception as e:
                print(f"Error al procesar CSV: {e}")
        else:
            print(f"Error: El archivo {args.csv} no existe")
    
    # Buscar exámenes por texto
    if args.buscar:
        examenes = sistema.buscar_examenes(args.buscar, tipo=args.tipo)
        print(f"\nResultados de búsqueda para '{args.buscar}':")
        for i, e in enumerate(examenes, 1):
            print(f"{i}. [{e['codigo']}] {e['nombre']} ({e['tipo']}/{e['subtipo']}) - {e['conteo']} usos")
    
    # Buscar exámenes por centro/sala
    if args.centro or args.sala:
        examenes = sistema.buscar_examenes_por_centro(centro_medico=args.centro, sala=args.sala)
        filtro = ""
        if args.centro:
            filtro += f"centro '{args.centro}'"
        if args.centro and args.sala:
            filtro += " y "
        if args.sala:
            filtro += f"sala '{args.sala}'"
            
        print(f"\nExámenes realizados en {filtro}:")
        for i, e in enumerate(examenes, 1):
            print(f"{i}. [{e['codigo']}] {e['nombre']} - {e['fecha']} ({e['centro'] or 'N/A'}/{e['sala'] or 'N/A'})")
    
    # Buscar código específico
    if args.codigo:
        examen = sistema.obtener_examen_por_codigo(args.codigo)
        if examen:
            print(f"\nInformación del examen {args.codigo}:")
            print(f"Nombre: {examen['nombre']}")
            print(f"Tipo: {examen['tipo']}/{examen['subtipo']}")
            print(f"Complejidad: {examen['complejidad']}/5")
            print(f"Tiempo estimado: {examen['tiempo_estimado']} minutos")
            print(f"Usos registrados: {examen['conteo']}")
            print(f"Creado el: {examen['fecha_creacion']}")
            
            if examen['historial']:
                print("\nHistorial de uso reciente:")
                for h in examen['historial']:
                    sala = h['sala'] if h['sala'] else 'N/A'
                    centro = h['centro_medico'] if h['centro_medico'] else 'N/A'
                    print(f"- {h['fecha']} en {centro} ({sala})")
        else:
            print(f"Código {args.codigo} no encontrado")
    
    # Mostrar estadísticas generales
    if args.estadisticas:
        stats = sistema.estadisticas_codigos()
        print("\nEstadísticas del sistema:")
        print(f"Total de códigos: {stats['total_codigos']}")
        
        print("\nPor tipo:")
        for tipo, count in stats['por_tipo'].items():
            print(f"- {tipo}: {count}")
        
        print("\nExámenes más comunes:")
        for e in stats['examenes_comunes']:
            print(f"- {e['nombre']} ({e['codigo']}): {e['conteo']} usos")
        
        if stats['tiempo']['promedio']:
            print(f"\nTiempo promedio de examen: {stats['tiempo']['promedio']} minutos")
            print(f"Tiempo mínimo: {stats['tiempo']['minimo']} minutos")
            print(f"Tiempo máximo: {stats['tiempo']['maximo']} minutos")
    
    # Mostrar estadísticas por centro
    if args.estadisticas_centro:
        stats = sistema.obtener_estadisticas_centro(args.estadisticas_centro)
        
        if 'error' in stats:
            print(f"Error: {stats['error']}")
        elif 'centro' in stats:
            centro = stats['centro']
            print(f"\nEstadísticas del centro: {centro['nombre']}")
            print(f"Total de exámenes: {centro['total_examenes']}")
            print(f"Exámenes TAC: {centro['total_tac']}")
            print(f"Exámenes RX: {centro['total_rx']}")
            print(f"Número de salas: {centro['total_salas']}")
            
            if 'salas' in stats and stats['salas']:
                print("\nExámenes por sala:")
                for s in stats['salas']:
                    print(f"- {s['nombre']}: {s['total']} exámenes (TAC: {s['tac']}, RX: {s['rx']})")
            
            if 'examenes_comunes' in stats and stats['examenes_comunes']:
                print("\nExámenes más comunes en este centro:")
                for e in stats['examenes_comunes']:
                    print(f"- {e['nombre']} ({e['codigo']}): {e['total']} usos")
        else:
            print("\nEstadísticas por centro:")
            total = stats.get('total_global', 0)
            print(f"Total de exámenes en el sistema: {total}")
            
            if 'centros' in stats:
                for c in stats['centros']:
                    print(f"- {c['nombre']}: {c['total_examenes']} exámenes")
    
    # Exportar códigos
    if args.exportar:
        ruta = sistema.exportar_codigos_json(args.exportar)
        print(f"Códigos exportados a: {ruta}")
    
    # Importar códigos
    if args.importar:
        exito, mensaje = sistema.importar_codigos_json(args.importar)
        print(mensaje)


if __name__ == "__main__":
    main()