#!/usr/bin/env python3
"""
Prueba manual simple del método estimar_dias_turno
"""

import pandas as pd
import sys
import os

# Datos de prueba que simulan duplas
datos_test = {
    'Fecha del procedimiento programado': [
        # DUPLA 1: Días consecutivos con alta concentración
        '08/05/2024', '08/05/2024', '08/05/2024', '08/05/2024', '08/05/2024',  # 5 exámenes día 1
        '09/05/2024', '09/05/2024', '09/05/2024', '09/05/2024', '09/05/2024', '09/05/2024',  # 6 exámenes día 2
        
        # DUPLA 2: Otra dupla
        '15/05/2024', '15/05/2024', '15/05/2024', '15/05/2024',  # 4 exámenes día 1
        '16/05/2024', '16/05/2024', '16/05/2024', '16/05/2024', '16/05/2024',  # 5 exámenes día 2
        
        # DUPLA 3: Tercera dupla
        '22/05/2024', '22/05/2024', '22/05/2024', '22/05/2024', '22/05/2024',  # 5 exámenes día 1
        '23/05/2024', '23/05/2024', '23/05/2024', '23/05/2024',  # 4 exámenes día 2
        
        # Días individuales (pocos exámenes - no deberían ser detectados)
        '10/05/2024', '10/05/2024',  # 2 exámenes
        '11/05/2024',  # 1 examen
        
        # Día individual con muchos exámenes (sin dupla)
        '25/05/2024', '25/05/2024', '25/05/2024', '25/05/2024', '25/05/2024', '25/05/2024',  # 6 exámenes
    ],
    'Nombre del procedimiento': [f'Procedimiento_{i}' for i in range(1, 32)]
}

df_test = pd.DataFrame(datos_test)

print("🔍 PRUEBA MANUAL: ESTIMADOR DE DUPLAS")
print("="*50)

print(f"📊 DATOS DE PRUEBA: {len(df_test)} exámenes")
print("\nDistribución esperada:")
conteo = df_test['Fecha del procedimiento programado'].value_counts().sort_index()
for fecha, cantidad in conteo.items():
    print(f"  {fecha}: {cantidad} exámenes")

print("\n🎯 DUPLAS ESPERADAS:")
print("  1. 08-may-2024 (primer día de dupla 08/05 + 09/05)")
print("  2. 15-may-2024 (primer día de dupla 15/05 + 16/05)")  
print("  3. 22-may-2024 (primer día de dupla 22/05 + 23/05)")
print("  4. 25-may-2024 (día individual con alta concentración)")

print("\n🤖 PROBANDO IMPORTACIÓN...")
try:
    from calculadora_turnos import CalculadoraTurnos
    print("✅ Módulo importado correctamente")
    
    calc = CalculadoraTurnos()
    print("✅ Instancia creada correctamente")
    
    if hasattr(calc, 'estimar_dias_turno'):
        print("✅ Método estimar_dias_turno encontrado")
        
        print("\n🚀 EJECUTANDO ESTIMACIÓN...")
        resultado = calc.estimar_dias_turno(df_test)
        
        print(f"\n📋 RESULTADO: {len(resultado)} turnos detectados")
        
        if resultado:
            print("\n🎯 TURNOS ESTIMADOS:")
            for i, (fecha, examenes) in enumerate(resultado, 1):
                print(f"  {i}. {fecha} - {examenes} exámenes")
            
            # Verificar límites (2-6 turnos)
            if 2 <= len(resultado) <= 6:
                print(f"\n✅ LÍMITES RESPETADOS: {len(resultado)} turnos (rango 2-6)")
            else:
                print(f"\n❌ LÍMITES VIOLADOS: {len(resultado)} turnos (debería ser 2-6)")
            
            # Verificar que detectó las duplas esperadas
            fechas_resultado = [fecha for fecha, _ in resultado]
            duplas_esperadas = ['08-may-2024', '15-may-2024', '22-may-2024']
            
            print(f"\n🔍 VERIFICACIÓN DE DUPLAS:")
            duplas_detectadas = 0
            for dupla in duplas_esperadas:
                if dupla in fechas_resultado:
                    print(f"  ✅ Dupla detectada: {dupla}")
                    duplas_detectadas += 1
                else:
                    print(f"  ❌ Dupla NO detectada: {dupla}")
            
            print(f"\n🏆 RESUMEN: {duplas_detectadas}/{len(duplas_esperadas)} duplas detectadas")
            
            if duplas_detectadas >= 2:
                print("🎉 PRUEBA EXITOSA: Funcionalidad de duplas operativa")
            else:
                print("⚠️  PRUEBA PARCIAL: Pocas duplas detectadas")
        else:
            print("❌ No se detectaron turnos")
            
    else:
        print("❌ Método estimar_dias_turno NO encontrado")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
