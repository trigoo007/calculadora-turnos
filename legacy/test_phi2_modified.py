#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la integración con phi-2 en el puerto por defecto
"""

from asistente_phi2 import AsistentePhi2
import pandas as pd
import json
import os

def main():
    """Función principal para probar la integración con phi-2"""
    print("Iniciando prueba de integración con phi-2 (puerto por defecto)...")
    
    # Crear instancia del asistente con el puerto por defecto
    asistente = AsistentePhi2(puerto=11434)
    
    # Forzar el estado de Ollama a True para las pruebas
    asistente.ollama_disponible = True
    asistente.api_base = f"http://localhost:11434/api"
    
    # Verificar instalación
    estado = asistente.verificar_instalacion()
    print(f"Estado de la instalación: {json.dumps(estado, indent=2)}")
    
    if not estado["ollama_ejecutando"] or not estado["modelo_phi2_disponible"]:
        print("Error: Ollama no está ejecutándose o el modelo phi-2 no está disponible")
        return
    
    # Crear datos de ejemplo
    print("\nCreando datos de ejemplo para pruebas...")
    
    # Datos médicos de ejemplo
    data = {
        'Número de cita': list(range(1, 6)),
        'Fecha del procedimiento programado': ['01-may-2025', '02-may-2025', '03-may-2025', '05-may-2025', '06-may-2025'],
        'Sala de adquisición': ['SCA01', 'SCA02', 'SJ01', 'SCA01', 'SJ02'],
        'Tipo': ['RX', 'TAC', 'TAC', 'RX', 'TAC'],
        'Nombre del procedimiento': [
            'Radiografía de tórax', 
            'TAC de abdomen', 
            'TAC Tórax, abdomen y pelvis', 
            'Radiografía de columna',
            'AngioTAC de tórax, abdomen y pelvis'
        ],
        'TAC doble': [False, False, True, False, False],
        'TAC triple': [False, False, False, False, True]
    }
    
    df = pd.DataFrame(data)
    print(df)
    
    # Crear base de datos temporal para pruebas
    db_path = asistente.crear_base_datos_temporal(df, 'examenes')
    if not db_path:
        print("Error: No se pudo crear base de datos temporal")
        return
    
    print(f"\nBase de datos temporal creada en: {db_path}")
    
    # Probar consulta SQL directa
    print("\nProbando consulta SQL directa...")
    exito, resultado = asistente.ejecutar_consulta_sql("SELECT Tipo, COUNT(*) as cantidad FROM examenes GROUP BY Tipo")
    
    if exito:
        print("\nResultados SQL:")
        print(resultado)
    else:
        print(f"Error en consulta SQL: {resultado}")
    
    # Probar consulta en lenguaje natural
    print("\nProbando consulta en lenguaje natural...")
    
    consultas = [
        "¿Cuántos exámenes hay de cada tipo?",
        "¿Cuántos exámenes TAC dobles hay?",
        "Muestra los procedimientos ordenados por fecha"
    ]
    
    for consulta in consultas:
        print(f"\nConsulta: '{consulta}'")
        exito, resultado = asistente.consulta_natural(consulta)
        
        if exito:
            print("Resultado:")
            print(resultado)
        else:
            print(f"Error: {resultado}")
    
    # Probar generación de respuesta
    print("\nProbando generación de respuesta...")
    
    respuesta = asistente.generar_respuesta("Explica brevemente los beneficios de usar phi-2 para consultas radiológicas")
    print("\nRespuesta generada:")
    print(respuesta)
    
    print("\nPrueba completada.")

if __name__ == "__main__":
    main()