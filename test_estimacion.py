#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de estimación de días de turno
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_estimation_functionality():
    """Probar la funcionalidad de estimación"""
    print("=== INICIANDO PRUEBA DE FUNCIONALIDAD DE ESTIMACIÓN ===\n")
    
    # Importar la función de estimación
    try:
        from calculadora_turnos import CalculadoraTurnos
        print("✓ Módulo calculadora_turnos importado correctamente")
    except ImportError as e:
        print(f"✗ Error al importar calculadora_turnos: {e}")
        return False
    
    # Crear datos de prueba
    print("\n--- Creando datos de prueba ---")
    test_data = {
        'Fecha': [
            '2024-01-15', '2024-01-15', '2024-01-15', '2024-01-15',  # 4 exámenes
            '2024-01-16', '2024-01-16',  # 2 exámenes
            '2024-01-17', '2024-01-17', '2024-01-17', '2024-01-17', '2024-01-17',  # 5 exámenes
            '2024-01-18',  # 1 examen
            '2024-01-19', '2024-01-19', '2024-01-19',  # 3 exámenes
            '2024-01-20', '2024-01-20', '2024-01-20', '2024-01-20', '2024-01-20', '2024-01-20'  # 6 exámenes
        ],
        'Examen': [
            'TC Torax', 'RM Cerebro', 'US Abdomen', 'RX Torax',
            'TC Abdomen', 'RM Columna',
            'TC Cerebro', 'US Pelvis', 'RX Columna', 'TC Torax', 'RM Torax',
            'US Abdomen',
            'TC Pelvis', 'RM Abdomen', 'RX Pelvis',
            'TC Cerebro', 'RM Cerebro', 'US Torax', 'RX Abdomen', 'TC Columna', 'RM Pelvis'
        ],
        'Modalidad': [
            'TC', 'RM', 'US', 'RX',
            'TC', 'RM',
            'TC', 'US', 'RX', 'TC', 'RM',
            'US',
            'TC', 'RM', 'RX',
            'TC', 'RM', 'US', 'RX', 'TC', 'RM'
        ]
    }
    
    df_test = pd.DataFrame(test_data)
    print(f"✓ Datos de prueba creados: {len(df_test)} registros")
    print(f"Fechas únicas: {df_test['Fecha'].nunique()}")
    print("Distribución por fecha:")
    for fecha, grupo in df_test.groupby('Fecha'):
        print(f"  {fecha}: {len(grupo)} exámenes")
    
    # Probar la función de estimación
    print("\n--- Probando función estimar_dias_turno ---")
    try:
        calc = CalculadoraTurnos()
        
        # Verificar si existe el método
        if hasattr(calc, 'estimar_dias_turno'):
            print("✓ Método estimar_dias_turno encontrado")
            
            # Ejecutar la estimación
            fechas_estimadas = calc.estimar_dias_turno(df_test)
            
            print(f"\n--- Resultados de la estimación ---")
            print(f"Fechas estimadas: {len(fechas_estimadas)}")
            
            if fechas_estimadas:
                for i, fecha_info in enumerate(fechas_estimadas, 1):
                    print(f"  {i}. {fecha_info}")
                
                # Análisis de los resultados
                print(f"\n--- Análisis de resultados ---")
                # Contar exámenes por fecha en los datos originales
                conteo_por_fecha = df_test.groupby('Fecha').size()
                promedio = conteo_por_fecha.mean()
                umbral = max(promedio * 0.8, 3)
                
                print(f"Promedio de exámenes por día: {promedio:.2f}")
                print(f"Umbral calculado (80% del promedio, mín 3): {umbral:.2f}")
                print("Fechas que superan el umbral:")
                for fecha, cantidad in conteo_por_fecha.items():
                    if cantidad >= umbral:
                        print(f"  {fecha}: {cantidad} exámenes ✓")
                    else:
                        print(f"  {fecha}: {cantidad} exámenes")
                
                return True
            else:
                print("⚠ No se estimaron fechas (lista vacía)")
                return False
                
        else:
            print("✗ Método estimar_dias_turno NO encontrado")
            print("Métodos disponibles:", [m for m in dir(calc) if not m.startswith('_')])
            return False
            
    except Exception as e:
        print(f"✗ Error al ejecutar estimación: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streamlit_imports():
    """Verificar que todos los imports de Streamlit funcionen"""
    print("\n=== VERIFICANDO IMPORTS DE STREAMLIT ===\n")
    
    try:
        import streamlit as st
        print("✓ Streamlit importado correctamente")
        print(f"Versión de Streamlit: {st.__version__}")
        
        # Verificar imports específicos del proyecto
        from ui.calculadora_streamlit import main
        print("✓ Función main de calculadora_streamlit importada")
        
        return True
    except ImportError as e:
        print(f"✗ Error en imports: {e}")
        return False

def main():
    """Función principal de prueba"""
    print("CALCULADORA DE TURNOS EN RADIOLOGÍA - PRUEBA DE ESTIMACIÓN")
    print("=" * 60)
    
    # Verificar imports
    imports_ok = test_streamlit_imports()
    
    # Probar funcionalidad de estimación
    estimation_ok = test_estimation_functionality()
    
    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS:")
    print(f"• Imports de Streamlit: {'✓ OK' if imports_ok else '✗ FALLÓ'}")
    print(f"• Funcionalidad de estimación: {'✓ OK' if estimation_ok else '✗ FALLÓ'}")
    
    if imports_ok and estimation_ok:
        print("\n🎉 TODAS LAS PRUEBAS PASARON - La funcionalidad de estimación está operativa")
        return True
    else:
        print("\n⚠ ALGUNAS PRUEBAS FALLARON - Revisar los errores anteriores")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
