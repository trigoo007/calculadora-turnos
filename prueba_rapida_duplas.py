#!/usr/bin/env python3
"""
Prueba rápida de funcionalidad de duplas
"""

import pandas as pd
import sys
import os

def main():
    print("🔍 PRUEBA RÁPIDA: ESTIMADOR DE DUPLAS")
    print("="*40)
    
    try:
        # Importar el módulo
        from calculadora_turnos import CalculadoraTurnos
        print("✅ Módulo importado")
        
        # Crear instancia
        calc = CalculadoraTurnos()
        print("✅ Instancia creada")
        
        # Verificar método
        if hasattr(calc, 'estimar_dias_turno'):
            print("✅ Método estimar_dias_turno encontrado")
        else:
            print("❌ Método NO encontrado")
            return
        
        # Datos de prueba simples
        datos = pd.DataFrame({
            'Fecha del procedimiento programado': [
                '08/05/2024', '08/05/2024', '08/05/2024', '08/05/2024', '08/05/2024',  # 5 exámenes - DUPLA día 1
                '09/05/2024', '09/05/2024', '09/05/2024', '09/05/2024', '09/05/2024', '09/05/2024',  # 6 exámenes - DUPLA día 2
                '15/05/2024', '15/05/2024', '15/05/2024', '15/05/2024',  # 4 exámenes - DUPLA día 1
                '16/05/2024', '16/05/2024', '16/05/2024', '16/05/2024', '16/05/2024',  # 5 exámenes - DUPLA día 2
                '22/05/2024', '22/05/2024',  # 2 exámenes - día individual
            ],
            'Nombre del procedimiento': [f'Proc_{i}' for i in range(1, 18)]
        })
        
        print(f"✅ Datos creados: {len(datos)} registros")
        
        # Ejecutar estimación
        print("\n🤖 Ejecutando estimación...")
        resultado = calc.estimar_dias_turno(datos)
        
        print(f"\n📋 RESULTADO: {len(resultado)} turnos detectados")
        
        if resultado:
            for i, (fecha, examenes) in enumerate(resultado, 1):
                print(f"  {i}. {fecha} - {examenes} exámenes")
                
            # Verificar límites
            if 2 <= len(resultado) <= 6:
                print(f"✅ Límites OK: {len(resultado)} turnos (2-6)")
            else:
                print(f"❌ Límites violados: {len(resultado)} turnos")
        else:
            print("❌ Sin resultados")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
