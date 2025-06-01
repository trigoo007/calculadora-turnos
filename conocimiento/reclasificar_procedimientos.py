#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para reclasificar procedimientos específicos en el sistema de aprendizaje.
Este script busca procedimientos específicos y los reclasifica como TAC triple.
"""

import os
import json
import sys

# Rutas a archivos de conocimiento
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCEDIMIENTOS_FILE = os.path.join(BASE_DIR, "procedimientos.json")

# Lista de procedimientos que deben ser reclasificados como TAC triple
PROCEDIMIENTOS_TRIPLE = [
    "TAC Cuello-Tórax-Abdomen",
    "TAC de Cuello, Tórax y Abdomen",
    "TAC Craneo-Cuello-Torax",
    "TAC Cerebro-Cuello-Torax",
    "TAC Cerebro-Cuello-Abdomen",
    "TAC Cerebro-Cuello-Torax-Abdomen",
    "TAC de Cabeza, Cuello y Tórax",
    "TAC de Cerebro, Cuello y Tórax"
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

def reclasificar_procedimientos():
    # Cargar procedimientos
    procedimientos = cargar_json(PROCEDIMIENTOS_FILE)
    if not procedimientos:
        print("No se pudieron cargar los procedimientos")
        return False
    
    # Contador de procedimientos reclasificados
    reclasificados = 0
    
    # Buscar coincidencias exactas
    for nombre, datos in procedimientos.items():
        if nombre in PROCEDIMIENTOS_TRIPLE:
            if datos['tipo'] == 'TAC' and datos['subtipo'] != 'TRIPLE':
                print(f"Reclasificando: {nombre} de {datos['subtipo']} a TRIPLE")
                datos['subtipo'] = 'TRIPLE'
                reclasificados += 1
    
    # Buscar coincidencias parciales
    for nombre, datos in procedimientos.items():
        if datos['tipo'] == 'TAC' and datos['subtipo'] != 'TRIPLE':
            # Verificar si contiene patrones de TAC triple
            for patron in PROCEDIMIENTOS_TRIPLE:
                if patron.lower() in nombre.lower():
                    print(f"Reclasificando por coincidencia parcial: {nombre} de {datos['subtipo']} a TRIPLE")
                    datos['subtipo'] = 'TRIPLE'
                    reclasificados += 1
                    break
            
            # Verificar otras combinaciones específicas
            partes = nombre.lower().split()
            if ('cerebro' in partes or 'craneo' in partes or 'cabeza' in partes) and \
               ('cuello' in partes) and \
               ('torax' in partes or 'tx' in partes):
                print(f"Reclasificando por análisis de partes: {nombre} de {datos['subtipo']} a TRIPLE")
                datos['subtipo'] = 'TRIPLE'
                reclasificados += 1
    
    # Guardar procedimientos actualizados
    if reclasificados > 0:
        if guardar_json(procedimientos, PROCEDIMIENTOS_FILE):
            print(f"Se reclasificaron {reclasificados} procedimientos como TAC triple")
            return True
        else:
            print("Error al guardar los procedimientos reclasificados")
            return False
    else:
        print("No se encontraron procedimientos para reclasificar")
        return True

if __name__ == "__main__":
    print("Iniciando reclasificación de procedimientos...")
    if reclasificar_procedimientos():
        print("Reclasificación completada exitosamente")
    else:
        print("La reclasificación falló")
        sys.exit(1)