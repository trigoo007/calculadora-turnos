#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de aprendizaje y análisis de datos para la Calculadora de Turnos
-----------------------------------------------------------------------
Herramienta para indexar, clasificar y aprender de los datos procesados.
Permite identificar patrones en procedimientos y salas para mejorar la precisión.

Características principales:
- Clasificación automática de procedimientos (RX, TAC normal, TAC doble, TAC triple)
- Generación de códigos únicos para procedimientos
- Clasificación y categorización de salas (SCA, SJ, HOS)
- Detección avanzada de patrones en TAC dobles y triples
- Aprendizaje y mejora continua con nuevos datos
"""

import os
import pandas as pd
import numpy as np
import json
from datetime import datetime
import re
from collections import Counter, defaultdict

# Rutas a archivos de conocimiento
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONOCIMIENTO_DIR = os.path.join(BASE_DIR, "conocimiento")
PROCEDIMIENTOS_FILE = os.path.join(CONOCIMIENTO_DIR, "procedimientos.json")
SALAS_FILE = os.path.join(CONOCIMIENTO_DIR, "salas.json")
PATRONES_FILE = os.path.join(CONOCIMIENTO_DIR, "patrones_tac_doble.json")
PATRONES_TRIPLE_FILE = os.path.join(CONOCIMIENTO_DIR, "patrones_tac_triple.json")

# Asegurar que el directorio de conocimiento existe
if not os.path.exists(CONOCIMIENTO_DIR):
    os.makedirs(CONOCIMIENTO_DIR)


class SistemaAprendizaje:
    """Sistema para analizar, indexar y aprender de los datos procesados."""
    
    def __init__(self):
        """Inicializa el sistema de aprendizaje y carga datos existentes."""
        self.procedimientos = self._cargar_json(PROCEDIMIENTOS_FILE, {})
        self.salas = self._cargar_json(SALAS_FILE, {})
        self.patrones_tac_doble = self._cargar_json(PATRONES_FILE, [])
        self.patrones_tac_triple = self._cargar_json(PATRONES_TRIPLE_FILE, [])
        self.contador_procedimientos = Counter()
        self.contador_salas = Counter()
        
    def _cargar_json(self, ruta, valor_default):
        """Carga datos de un archivo JSON o devuelve un valor predeterminado."""
        try:
            if os.path.exists(ruta):
                with open(ruta, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return valor_default
        except Exception as e:
            print(f"Error al cargar {ruta}: {e}")
            return valor_default
    
    def _guardar_json(self, datos, ruta):
        """Guarda datos en un archivo JSON."""
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error al guardar {ruta}: {e}")
            return False
    
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
        
        # Añadir sufijo numérico para evitar colisiones
        base_codigo = codigo
        contador = 1
        while codigo in self.procedimientos:
            codigo = f"{base_codigo}{contador}"
            contador += 1
        
        return codigo.upper()
    
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
        
        # Procesar procedimientos
        for proc in df['Nombre del procedimiento'].dropna().unique():
            self.contador_procedimientos[proc] += 1
            
            # Si es nuevo, agregar al diccionario de procedimientos
            if proc not in self.procedimientos:
                codigo = self.generar_codigo_procedimiento(proc)
                clasificacion = self.clasificar_procedimiento(proc)
                
                self.procedimientos[proc] = {
                    'codigo': codigo,
                    'tipo': clasificacion['tipo'],
                    'subtipo': clasificacion['subtipo'],
                    'conteo': 1,
                    'primera_vez': datetime.now().strftime('%Y-%m-%d')
                }
                nuevos_procedimientos += 1
            else:
                # Actualizar conteo
                self.procedimientos[proc]['conteo'] += 1
                
                # Verificar si necesitamos actualizar la clasificación
                # (por ejemplo, si ahora tenemos información para clasificarlo como triple)
                clasificacion_actual = self.clasificar_procedimiento(proc)
                if clasificacion_actual['subtipo'] != self.procedimientos[proc]['subtipo']:
                    self.procedimientos[proc]['subtipo'] = clasificacion_actual['subtipo']
        
        # Procesar salas
        for sala in df['Sala de adquisición'].dropna().unique():
            self.contador_salas[sala] += 1
            
            # Si es nueva, agregar al diccionario de salas
            if sala not in self.salas:
                clasificacion = self.clasificar_sala(sala)
                
                self.salas[sala] = {
                    'tipo': clasificacion['tipo'],
                    'subtipo': clasificacion['subtipo'],
                    'conteo': 1,
                    'primera_vez': datetime.now().strftime('%Y-%m-%d')
                }
                nuevas_salas += 1
            else:
                # Actualizar conteo
                self.salas[sala]['conteo'] += 1
        
        # Aprender patrones de TAC triple
        self.aprender_patrones_tac_triple(df)
        
        # Guardar datos actualizados
        self._guardar_json(self.procedimientos, PROCEDIMIENTOS_FILE)
        self._guardar_json(self.salas, SALAS_FILE)
        
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
        for nombre in tac_dobles:
            # Verificar si ya tenemos este patrón
            if nombre not in self.patrones_tac_doble:
                self.patrones_tac_doble.append(nombre)
                nuevos_patrones += 1
        
        # Guardar patrones actualizados
        self._guardar_json(self.patrones_tac_doble, PATRONES_FILE)
        
        return True, f"Aprendizaje completado: {nuevos_patrones} nuevos patrones de TAC doble identificados"
    
    def aprender_patrones_tac_triple(self, df):
        """Analiza exámenes marcados como TAC triple para identificar patrones comunes."""
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
        for nombre in tac_triples:
            # Verificar si ya tenemos este patrón
            if nombre not in self.patrones_tac_triple:
                self.patrones_tac_triple.append(nombre)
                nuevos_patrones += 1
        
        # También añadir patrones específicos conocidos para TAC triple
        patrones_conocidos = [
            "TAC Cuello-Tórax-Abdomen",
            "TAC de Cuello, Tórax y Abdomen",
            "TAC Craneo-Cuello-Torax",
            "TAC Cerebro-Cuello-Torax",
            "TAC Craneo-Cuello-Torax-Abdomen",
            "TAC Cerebro-Cuello-Torax-Abdomen",
            "TAC de Cabeza, Cuello y Tórax",
            "TAC de Cerebro, Cuello y Tórax"
        ]
        
        for patron in patrones_conocidos:
            if patron not in self.patrones_tac_triple:
                self.patrones_tac_triple.append(patron)
                nuevos_patrones += 1
        
        # Guardar patrones actualizados
        self._guardar_json(self.patrones_tac_triple, PATRONES_TRIPLE_FILE)
        
        return True, f"Aprendizaje completado: {nuevos_patrones} nuevos patrones de TAC triple identificados"
    
    def obtener_estadisticas(self):
        """Obtiene estadísticas sobre los datos aprendidos."""
        stats = {
            'procedimientos': {
                'total': len(self.procedimientos),
                'por_tipo': defaultdict(int),
                'por_subtipo': defaultdict(int)
            },
            'salas': {
                'total': len(self.salas),
                'por_tipo': defaultdict(int)
            },
            'patrones_tac_doble': len(self.patrones_tac_doble),
            'patrones_tac_triple': len(self.patrones_tac_triple)
        }
        
        # Contar por tipo y subtipo de procedimiento
        for proc, datos in self.procedimientos.items():
            stats['procedimientos']['por_tipo'][datos['tipo']] += 1
            
            # Contar por subtipo (especialmente para TAC)
            if datos['tipo'] == 'TAC':
                subtipo_key = f"TAC_{datos['subtipo']}"
                stats['procedimientos']['por_subtipo'][subtipo_key] += 1
        
        # Contar por tipo de sala
        for sala, datos in self.salas.items():
            stats['salas']['por_tipo'][datos['tipo']] += 1
        
        return stats
    
    def verificar_clasificacion(self, nombre_procedimiento):
        """Verifica si un procedimiento debería ser clasificado como TAC doble."""
        if nombre_procedimiento in self.procedimientos:
            return (
                self.procedimientos[nombre_procedimiento]['tipo'] == 'TAC' and
                self.procedimientos[nombre_procedimiento]['subtipo'] == 'DOBLE'
            )
        
        # Si no está en el catálogo, clasificar dinámicamente
        clasificacion = self.clasificar_procedimiento(nombre_procedimiento)
        return clasificacion['tipo'] == 'TAC' and clasificacion['subtipo'] == 'DOBLE'
    
    def obtener_procedimientos_tipo(self, tipo, subtipo=None):
        """Obtiene una lista de procedimientos de un tipo específico."""
        resultado = []
        for proc, datos in self.procedimientos.items():
            if datos['tipo'] == tipo:
                if subtipo is None or datos['subtipo'] == subtipo:
                    resultado.append({
                        'nombre': proc,
                        'codigo': datos['codigo'],
                        'subtipo': datos['subtipo'],
                        'conteo': datos['conteo']
                    })
        
        # Ordenar por conteo (mayor a menor)
        return sorted(resultado, key=lambda x: x['conteo'], reverse=True)
    
    def obtener_salas_tipo(self, tipo):
        """Obtiene una lista de salas de un tipo específico."""
        resultado = []
        for sala, datos in self.salas.items():
            if datos['tipo'] == tipo:
                resultado.append({
                    'nombre': sala,
                    'subtipo': datos['subtipo'],
                    'conteo': datos['conteo']
                })
        
        # Ordenar por conteo (mayor a menor)
        return sorted(resultado, key=lambda x: x['conteo'], reverse=True)


# Integración con la Calculadora de Turnos
def integrar_con_calculadora(calculadora, df):
    """Integra el sistema de aprendizaje con la calculadora de turnos."""
    sistema = SistemaAprendizaje()
    
    # Analizar DataFrame
    sistema.analizar_dataframe(df)
    
    # Si existe la clasificación de TAC doble, aprender de ella
    if 'TAC doble' in df.columns:
        sistema.aprender_patrones_tac_doble(df)
    
    # Devolver el sistema para uso posterior
    return sistema


# Función principal para uso independiente
def main():
    """Función principal para uso del sistema de aprendizaje de forma independiente."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sistema de aprendizaje para la Calculadora de Turnos")
    parser.add_argument('--csv', help='Ruta al archivo CSV para analizar')
    parser.add_argument('--stats', action='store_true', help='Mostrar estadísticas del conocimiento actual')
    parser.add_argument('--tac', action='store_true', help='Listar procedimientos TAC')
    parser.add_argument('--tac-doble', action='store_true', help='Listar procedimientos TAC doble')
    parser.add_argument('--tac-triple', action='store_true', help='Listar procedimientos TAC triple')
    parser.add_argument('--salas', help='Listar salas por tipo (SCA, SJ, HOS, OTRO)')
    
    args = parser.parse_args()
    sistema = SistemaAprendizaje()
    
    # Analizar CSV si se proporciona
    if args.csv:
        if os.path.exists(args.csv):
            df = pd.read_csv(args.csv)
            exito, mensaje = sistema.analizar_dataframe(df)
            print(mensaje)
            
            if 'TAC doble' in df.columns:
                exito, mensaje = sistema.aprender_patrones_tac_doble(df)
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
        for proc in tac_procs[:20]:  # Mostrar solo los 20 más comunes
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