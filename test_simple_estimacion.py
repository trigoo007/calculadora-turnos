#!/usr/bin/env python3
"""
Test simple para verificar la funcionalidad de estimación
"""

import pandas as pd
import sys
import os

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=== PRUEBA DE FUNCIONALIDAD DE ESTIMACIÓN ===")
    
    # Test 1: Importar módulo
    try:
        from calculadora_turnos import CalculadoraTurnos
        print("✓ CalculadoraTurnos importado correctamente")
    except Exception as e:
        print(f"✗ Error al importar CalculadoraTurnos: {e}")
        return False
    
    # Test 2: Crear instancia
    try:
        calc = CalculadoraTurnos()
        print("✓ Instancia de CalculadoraTurnos creada")
    except Exception as e:
        print(f"✗ Error al crear instancia: {e}")
        return False
    
    # Test 3: Verificar si existe método estimar_dias_turno
    if hasattr(calc, 'estimar_dias_turno'):
        print("✓ Método estimar_dias_turno encontrado")
        
        # Test 4: Crear datos de prueba
        datos_prueba = pd.DataFrame({
            'Fecha': ['2024-01-15', '2024-01-15', '2024-01-15', '2024-01-15',  # 4 exams
                     '2024-01-16', '2024-01-16',  # 2 exams  
                     '2024-01-17', '2024-01-17', '2024-01-17', '2024-01-17', '2024-01-17'],  # 5 exams
            'Examen': ['TC1', 'RM1', 'US1', 'RX1', 'TC2', 'RM2', 'TC3', 'US2', 'RX2', 'TC4', 'RM3']
        })
        
        print(f"✓ Datos de prueba creados: {len(datos_prueba)} registros")
        
        # Test 5: Ejecutar estimación
        try:
            resultado = calc.estimar_dias_turno(datos_prueba)
            print(f"✓ Estimación ejecutada exitosamente")
            print(f"  Resultado: {resultado}")
            return True
        except Exception as e:
            print(f"✗ Error al ejecutar estimación: {e}")
            return False
            
    else:
        print("✗ Método estimar_dias_turno NO encontrado")
        # Listar métodos disponibles
        metodos = [method for method in dir(calc) if not method.startswith('_')]
        print(f"  Métodos disponibles: {metodos}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
    else:
        print("\n❌ ALGUNAS PRUEBAS FALLARON")
