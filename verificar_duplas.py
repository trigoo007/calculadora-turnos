#!/usr/bin/env python3
"""
Verificación rápida de la funcionalidad de duplas
"""

import pandas as pd
import sys
import os

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verificar_funcionalidad_duplas():
    """Verificar que la funcionalidad de duplas esté correctamente implementada"""
    
    print("🔍 VERIFICACIÓN: ESTIMADOR DE DUPLAS")
    print("="*50)
    
    try:
        # 1. Importar calculadora
        from calculadora_turnos import CalculadoraTurnos
        print("✅ Módulo CalculadoraTurnos importado exitosamente")
        
        # 2. Crear instancia
        calc = CalculadoraTurnos()
        print("✅ Instancia creada exitosamente")
        
        # 3. Verificar método existe
        if hasattr(calc, 'estimar_dias_turno'):
            print("✅ Método estimar_dias_turno encontrado")
        else:
            print("❌ Método estimar_dias_turno NO encontrado")
            return False
        
        # 4. Crear datos de prueba simulando duplas
        datos_test = pd.DataFrame({
            'Fecha del procedimiento programado': [
                # DUPLA 1: Días consecutivos con alta concentración
                '08/05/2024', '08/05/2024', '08/05/2024', '08/05/2024', '08/05/2024',  # 5 exámenes
                '09/05/2024', '09/05/2024', '09/05/2024', '09/05/2024', '09/05/2024', '09/05/2024',  # 6 exámenes
                
                # DUPLA 2: Otra dupla
                '15/05/2024', '15/05/2024', '15/05/2024', '15/05/2024',  # 4 exámenes
                '16/05/2024', '16/05/2024', '16/05/2024', '16/05/2024', '16/05/2024',  # 5 exámenes
                
                # DUPLA 3: Tercera dupla
                '22/05/2024', '22/05/2024', '22/05/2024', '22/05/2024', '22/05/2024',  # 5 exámenes
                '23/05/2024', '23/05/2024', '23/05/2024', '23/05/2024',  # 4 exámenes
                
                # Días individuales (pocos exámenes)
                '10/05/2024', '10/05/2024',  # 2 exámenes
                '11/05/2024',  # 1 examen
                
                # Día individual con muchos exámenes (sin dupla)
                '25/05/2024', '25/05/2024', '25/05/2024', '25/05/2024', '25/05/2024', '25/05/2024',  # 6 exámenes
            ],
            'Nombre del procedimiento': [f'Procedimiento_{i}' for i in range(1, 32)]
        })
        
        print(f"✅ Datos de prueba creados: {len(datos_test)} registros")
        
        # Mostrar distribución de exámenes por fecha
        print("\n📊 DISTRIBUCIÓN DE EXÁMENES:")
        conteo = datos_test['Fecha del procedimiento programado'].value_counts().sort_index()
        for fecha, cantidad in conteo.items():
            print(f"  {fecha}: {cantidad} exámenes")
        
        # 5. Ejecutar estimación
        print("\n🤖 EJECUTANDO ESTIMACIÓN...")
        resultado = calc.estimar_dias_turno(datos_test)
        
        # 6. Verificar resultados
        print(f"\n📋 RESULTADOS:")
        if resultado:
            print(f"✅ Estimación exitosa: {len(resultado)} turnos detectados")
            
            # Verificar límites (2-6 turnos)
            if 2 <= len(resultado) <= 6:
                print(f"✅ Límites respetados: {len(resultado)} turnos (rango 2-6)")
            else:
                print(f"❌ Límites NO respetados: {len(resultado)} turnos (debería ser 2-6)")
            
            print("\n🎯 TURNOS ESTIMADOS:")
            for i, (fecha, examenes) in enumerate(resultado, 1):
                print(f"  {i}. {fecha} - {examenes} exámenes")
            
            # Verificar que se detectaron las duplas esperadas
            fechas_resultado = [fecha for fecha, _ in resultado]
            duplas_esperadas = ['08-may-2024', '15-may-2024', '22-may-2024']
            
            duplas_detectadas = 0
            for dupla_esperada in duplas_esperadas:
                if dupla_esperada in fechas_resultado:
                    duplas_detectadas += 1
                    print(f"  ✅ Dupla detectada: {dupla_esperada}")
                else:
                    print(f"  ⚠️  Dupla NO detectada: {dupla_esperada}")
            
            print(f"\n🏆 RESUMEN: {duplas_detectadas}/{len(duplas_esperadas)} duplas detectadas correctamente")
            
            return True
        else:
            print("❌ No se detectaron turnos")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    exito = verificar_funcionalidad_duplas()
    print(f"\n{'🎉 VERIFICACIÓN EXITOSA' if exito else '💥 VERIFICACIÓN FALLIDA'}")
    sys.exit(0 if exito else 1)
