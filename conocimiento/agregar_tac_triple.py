#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para agregar ejemplos de TAC triple al sistema de aprendizaje.
"""

import os
import json
import sys
import datetime

# Rutas a archivos de conocimiento
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCEDIMIENTOS_FILE = os.path.join(BASE_DIR, "procedimientos.json")

# Lista de procedimientos de TAC triple para agregar
PROCEDIMIENTOS_TRIPLE = [
    "TAC Cuello-Tórax-Abdomen",
    "TAC de Cuello, Tórax y Abdomen",
    "TAC Craneo-Cuello-Torax",
    "TAC Cerebro-Cuello-Torax",
    "TAC Cabeza-Cuello-Torax",
    "TAC Cerebro-Cuello-Abdomen",
    "TAC Craneo-Cuello-Torax-Abdomen"
]

def cargar_json(ruta):
    try:
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error al cargar {ruta}: {e}")
        return {}

def guardar_json(datos, ruta):
    try:
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error al guardar {ruta}: {e}")
        return False

def generar_codigo(nombre):
    """Genera un código único para un procedimiento basado en su nombre."""
    import re
    # Eliminar caracteres especiales y convertir a minúsculas
    nombre_limpio = re.sub(r'[^\w\s]', '', nombre.lower())
    palabras = nombre_limpio.split()
    
    # Generar código basado en las primeras letras de cada palabra
    if len(palabras) >= 2:
        codigo = ''.join([p[0:2] for p in palabras[:3]])
    else:
        codigo = palabras[0][:5]
    
    return codigo.upper()

def agregar_procedimientos_triple():
    # Cargar procedimientos
    procedimientos = cargar_json(PROCEDIMIENTOS_FILE)
    if procedimientos is None:
        procedimientos = {}
    
    # Contador de procedimientos agregados
    agregados = 0
    
    # Fecha actual para "primera_vez"
    fecha_actual = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Agregar procedimientos TAC triple
    for nombre in PROCEDIMIENTOS_TRIPLE:
        if nombre not in procedimientos:
            codigo = generar_codigo(nombre)
            
            # Verificar si el código ya existe y agregar sufijo si es necesario
            codigo_base = codigo
            contador = 1
            while any(datos.get('codigo') == codigo for datos in procedimientos.values()):
                codigo = f"{codigo_base}{contador}"
                contador += 1
            
            # Agregar el procedimiento
            procedimientos[nombre] = {
                'codigo': codigo,
                'tipo': 'TAC',
                'subtipo': 'TRIPLE',
                'conteo': 1,
                'primera_vez': fecha_actual
            }
            print(f"Agregado: {nombre} con código {codigo}")
            agregados += 1
        else:
            # Si ya existe, asegurarse de que sea de tipo TAC TRIPLE
            if procedimientos[nombre]['tipo'] == 'TAC' and procedimientos[nombre]['subtipo'] != 'TRIPLE':
                print(f"Reclasificando: {nombre} de {procedimientos[nombre]['subtipo']} a TRIPLE")
                procedimientos[nombre]['subtipo'] = 'TRIPLE'
                agregados += 1
    
    # Guardar procedimientos actualizados
    if agregados > 0:
        if guardar_json(procedimientos, PROCEDIMIENTOS_FILE):
            print(f"Se agregaron o actualizaron {agregados} procedimientos TAC triple")
            return True
        else:
            print("Error al guardar los procedimientos")
            return False
    else:
        print("No se agregaron nuevos procedimientos")
        return True

if __name__ == "__main__":
    print("Iniciando adición de procedimientos TAC triple...")
    if agregar_procedimientos_triple():
        print("Proceso completado exitosamente")
    else:
        print("El proceso falló")
        sys.exit(1)