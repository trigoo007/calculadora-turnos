#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify the new date formatting logic
"""

def format_dates(dias):
    """Test the date formatting logic"""
    # Formatear elegantemente los días en lenguaje natural
    if len(dias) == 1:
        fechas_str = dias[0]
    elif len(dias) == 2:
        fechas_str = f"{dias[0]} y {dias[1]}"
    else:
        # Ordenar los días numéricamente antes de formatear
        dias_ordenados = sorted([int(d) for d in dias])
        dias_str = [str(d) for d in dias_ordenados]
        
        # Identificar secuencias consecutivas para formato más natural
        secuencias = []
        secuencia_actual = [dias_ordenados[0]]
        
        for i in range(1, len(dias_ordenados)):
            if dias_ordenados[i] == dias_ordenados[i-1] + 1:
                secuencia_actual.append(dias_ordenados[i])
            else:
                if len(secuencia_actual) > 0:
                    secuencias.append(secuencia_actual)
                    secuencia_actual = [dias_ordenados[i]]
        
        if secuencia_actual:
            secuencias.append(secuencia_actual)
        
        # Convertir secuencias a formato de texto
        partes = []
        for seq in secuencias:
            if len(seq) == 1:
                partes.append(str(seq[0]))
            elif len(seq) == 2:
                partes.append(f"{seq[0]} y {seq[1]}")
            else:
                partes.append(f"{seq[0]} al {seq[-1]}")
        
        # Unir las partes con comas y "y" antes del último elemento
        if len(partes) == 1:
            fechas_str = partes[0]
        elif len(partes) == 2:
            fechas_str = f"{partes[0]} y {partes[1]}"
        else:
            partes_excepto_ultima = partes[:-1]
            ultima_parte = partes[-1]
            fechas_str = ", ".join(partes_excepto_ultima) + " y " + ultima_parte
    
    return fechas_str

# Test cases
test_cases = [
    ["5"],                        # Single day
    ["5", "10"],                  # Two days
    ["5", "6", "7"],              # Consecutive days
    ["5", "6", "7", "10"],        # Consecutive and non-consecutive
    ["5", "7", "9", "11"],        # Non-consecutive days
    ["5", "6", "7", "9", "10", "11", "15"],  # Mixed consecutive and non-consecutive
    ["1", "2", "3", "5", "10", "11", "12", "13"],  # Multiple sequences
    ["15", "6", "8", "7", "2", "3", "4", "1"]  # Unordered to verify sorting
]

if __name__ == "__main__":
    print("Testing date formatting:")
    print("-----------------------")
    
    for i, test in enumerate(test_cases):
        print(f"Test {i+1} - Input: {test}")
        result = format_dates(test)
        print(f"Output: {result}")
        print()