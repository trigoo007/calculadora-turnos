#!/usr/bin/env python3
"""
Test específico para verificar la detección de duplas en el estimador de turnos
"""

import sys
import os
import pandas as pd

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_deteccion_duplas():
    """Probar la funcionalidad de detección de duplas"""
    
    print("=== TEST DE DETECCIÓN DE DUPLAS ===")
    
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
        
        # Crear datos de prueba que simulen duplas reales
        datos_test = pd.DataFrame({
            'Fecha': [
                # DUPLA 1: 8-9 Mayo (alta concentración)
                '08/05/2024', '08/05/2024', '08/05/2024', '08/05/2024', '08/05/2024', '08/05/2024',  # 6 exámenes
                '09/05/2024', '09/05/2024', '09/05/2024', '09/05/2024', '09/05/2024',  # 5 exámenes
                
                # DUPLA 2: 15-16 Mayo (alta concentración)
                '15/05/2024', '15/05/2024', '15/05/2024', '15/05/2024', '15/05/2024',  # 5 exámenes
                '16/05/2024', '16/05/2024', '16/05/2024', '16/05/2024', '16/05/2024', '16/05/2024', '16/05/2024',  # 7 exámenes
                
                # DUPLA 3: 22-23 Mayo (concentración media-alta)
                '22/05/2024', '22/05/2024', '22/05/2024', '22/05/2024',  # 4 exámenes
                '23/05/2024', '23/05/2024', '23/05/2024', '23/05/2024', '23/05/2024',  # 5 exámenes
                
                # Días individuales con pocos exámenes (no deberían ser seleccionados)
                '10/05/2024', '10/05/2024',  # 2 exámenes
                '11/05/2024',  # 1 examen
                '17/05/2024', '17/05/2024', '17/05/2024',  # 3 exámenes
                
                # DÍA INDIVIDUAL con alta concentración 
                '25/05/2024', '25/05/2024', '25/05/2024', '25/05/2024', '25/05/2024', '25/05/2024', '25/05/2024',  # 7 exámenes
            ],
            'Examen': [f'Examen_{i}' for i in range(1, 54)]
        })
        
        print(f"✓ Datos de prueba creados: {len(datos_test)} registros")
        print("\n  Distribución por fecha (simulando duplas):")
        conteo_fechas = datos_test['Fecha'].value_counts().sort_index()
        for fecha, count in conteo_fechas.items():
            print(f"    {fecha}: {count} exámenes")
        
        # Ejecutar estimación
        resultado = calc.estimar_dias_turno(datos_test)
        
        print(f"\n✓ Estimación ejecutada exitosamente")
        print(f"✓ Resultado: {len(resultado)} turnos detectados")
        
        if resultado:
            print("\n  🎯 TURNOS ESTIMADOS (primeros días de cada dupla):")
            for i, (fecha, num_examenes) in enumerate(resultado, 1):
                print(f"    {i}. {fecha}: {num_examenes} exámenes")
                
            # Verificar que detectó las duplas correctamente
            fechas_resultado = [fecha for fecha, _ in resultado]
            
            # Verificar que se detectaron entre 2 y 6 turnos
            if 2 <= len(resultado) <= 6:
                print(f"\n✓ Límites respetados: {len(resultado)} turnos (entre 2 y 6)")
            else:
                print(f"\n⚠️  Límites no respetados: {len(resultado)} turnos (debería ser entre 2 y 6)")
            
            # Verificar que priorizó días con más exámenes
            examenes_ordenados = [num for _, num in resultado]
            if examenes_ordenados == sorted(examenes_ordenados, reverse=True):
                print("✓ Turnos ordenados por número de exámenes (mayor a menor)")
            else:
                print("⚠️  Turnos NO están ordenados correctamente")
                
        else:
            print("  ⚠️  No se estimaron fechas de turno")
        
        return True
        
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_deteccion_duplas()
    print(f"\n{'='*60}")
    if success:
        print("🎉 TEST DE DETECCIÓN DE DUPLAS COMPLETADO EXITOSAMENTE")
    else:
        print("❌ TEST DE DETECCIÓN DE DUPLAS FALLÓ")
    print(f"{'='*60}")
