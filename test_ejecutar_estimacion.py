#!/usr/bin/env python3
"""Test directo de la funcionalidad de estimación"""

import sys
import os
import pandas as pd

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_estimacion():
    """Probar la funcionalidad de estimación"""
    
    print("=== INICIANDO TEST DE ESTIMACIÓN ===")
    
    try:
        # Importar la clase
        from calculadora_turnos import CalculadoraTurnos
        print("✓ CalculadoraTurnos importado exitosamente")
        
        # Crear instancia
        calc = CalculadoraTurnos()
        print("✓ Instancia creada exitosamente")
        
        # Verificar que el método existe
        if not hasattr(calc, 'estimar_dias_turno'):
            print("✗ ERROR: método estimar_dias_turno no encontrado")
            return False
        
        print("✓ Método estimar_dias_turno encontrado")
        
        # Crear datos de prueba con diferentes concentraciones
        datos_test = pd.DataFrame({
            'Fecha': [
                '2024-01-15', '2024-01-15', '2024-01-15', '2024-01-15',  # 4 exámenes (alto)
                '2024-01-16', '2024-01-16',  # 2 exámenes (bajo)
                '2024-01-17', '2024-01-17', '2024-01-17', '2024-01-17', '2024-01-17', '2024-01-17',  # 6 exámenes (muy alto)
                '2024-01-18',  # 1 examen (muy bajo)
                '2024-01-19', '2024-01-19', '2024-01-19'  # 3 exámenes (medio)
            ],
            'Examen': [f'Examen_{i}' for i in range(16)]
        })
        
        print(f"✓ Datos de prueba creados: {len(datos_test)} registros")
        print("  Distribución por fecha:")
        for fecha in datos_test['Fecha'].unique():
            count = len(datos_test[datos_test['Fecha'] == fecha])
            print(f"    {fecha}: {count} exámenes")
        
        # Ejecutar estimación
        resultado = calc.estimar_dias_turno(datos_test)
        
        print(f"\n✓ Estimación ejecutada exitosamente")
        print(f"✓ Resultado: {len(resultado)} fechas estimadas")
        
        if resultado:
            print("  Fechas estimadas como días de turno:")
            for fecha, num_examenes in resultado:
                print(f"    {fecha}: {num_examenes} exámenes")
        else:
            print("  No se estimaron fechas de turno")
        
        return True
        
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_estimacion()
    print(f"\n{'='*50}")
    if success:
        print("🎉 TEST COMPLETADO EXITOSAMENTE")
    else:
        print("❌ TEST FALLÓ")
    print(f"{'='*50}")
