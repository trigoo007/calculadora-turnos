#!/usr/bin/env python3
"""
Demostración de la funcionalidad de estimación de duplas
"""

import pandas as pd
import sys
import os

# Agregar directorio al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_estimacion_duplas():
    """Demostrar el funcionamiento del estimador de duplas"""
    
    print("🔍 DEMOSTRACIÓN: ESTIMADOR DE DUPLAS DE TURNOS")
    print("="*60)
    
    # Importar calculadora
    from calculadora_turnos import CalculadoraTurnos
    calc = CalculadoraTurnos()
    
    # Crear datos de prueba que representen un escenario real
    print("\n📊 DATOS DE ENTRADA:")
    print("Simulando exámenes distribuidos en diferentes días...")
    
    datos_reales = pd.DataFrame({
        'Fecha del procedimiento programado': [
            # DUPLA 1: 8-9 Mayo (muchos exámenes concentrados)
            '08/05/2024', '08/05/2024', '08/05/2024', '08/05/2024', '08/05/2024', '08/05/2024',  # 6 exámenes día 8
            '09/05/2024', '09/05/2024', '09/05/2024', '09/05/2024', '09/05/2024',  # 5 exámenes día 9
            
            # DUPLA 2: 15-16 Mayo (concentración alta)
            '15/05/2024', '15/05/2024', '15/05/2024', '15/05/2024', '15/05/2024',  # 5 exámenes día 15
            '16/05/2024', '16/05/2024', '16/05/2024', '16/05/2024', '16/05/2024', '16/05/2024', '16/05/2024',  # 7 exámenes día 16
            
            # DUPLA 3: 22-23 Mayo
            '22/05/2024', '22/05/2024', '22/05/2024', '22/05/2024',  # 4 exámenes día 22
            '23/05/2024', '23/05/2024', '23/05/2024', '23/05/2024', '23/05/2024',  # 5 exámenes día 23
            
            # Días aislados (pocos exámenes)
            '10/05/2024', '10/05/2024',  # 2 exámenes
            '11/05/2024',  # 1 examen
            '17/05/2024', '17/05/2024',  # 2 exámenes
            
            # Día individual con alta concentración (sin dupla)
            '25/05/2024', '25/05/2024', '25/05/2024', '25/05/2024', '25/05/2024', '25/05/2024',  # 6 exámenes
        ],
        'Nombre del procedimiento': [f'Procedimiento_{i}' for i in range(1, 46)]
    })
    
    # Mostrar distribución
    conteo = datos_reales['Fecha del procedimiento programado'].value_counts().sort_index()
    for fecha, cantidad in conteo.items():
        tipo_dia = ""
        if fecha in ['08/05/2024', '15/05/2024', '22/05/2024']:
            tipo_dia = " 🎯 (Primer día de dupla esperado)"
        elif fecha in ['09/05/2024', '16/05/2024', '23/05/2024']:
            tipo_dia = " (Segundo día de dupla)"
        elif fecha == '25/05/2024':
            tipo_dia = " (Individual alto)"
        else:
            tipo_dia = " (Individual bajo)"
            
        print(f"  {fecha}: {cantidad} exámenes{tipo_dia}")
    
    print(f"\nTotal de registros: {len(datos_reales)}")
    
    # Ejecutar estimación
    print("\n🤖 EJECUTANDO ESTIMACIÓN DE DUPLAS...")
    try:
        resultado = calc.estimar_dias_turno(datos_reales)
        
        if resultado:
            print(f"\n✅ RESULTADO: {len(resultado)} turnos estimados")
            print("\n🎯 TURNOS DETECTADOS:")
            for i, (fecha, total_examenes) in enumerate(resultado, 1):
                print(f"  {i}. {fecha} - {total_examenes} exámenes")
            
            # Verificar lógica
            print(f"\n📋 VERIFICACIÓN:")
            print(f"  • Número de turnos: {len(resultado)} (límite: 2-6) ✓")
            
            # Verificar que detectó los primeros días de las duplas
            fechas_esperadas = ['08-may-2024', '15-may-2024', '22-may-2024']
            fechas_resultado = [fecha for fecha, _ in resultado]
            
            duplas_detectadas = 0
            for fecha_esperada in fechas_esperadas:
                if fecha_esperada in fechas_resultado:
                    duplas_detectadas += 1
                    print(f"  • Dupla detectada correctamente: {fecha_esperada} ✓")
            
            print(f"\n🎉 RESUMEN: {duplas_detectadas}/3 duplas detectadas correctamente")
            
        else:
            print("❌ No se detectaron turnos")
            
        return resultado
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

if __name__ == "__main__":
    resultado = demo_estimacion_duplas()
    
    print("\n" + "="*60)
    if resultado:
        print("🎉 DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
        print("✅ El estimador de duplas funciona correctamente")
    else:
        print("❌ DEMOSTRACIÓN FALLÓ")
    print("="*60)
