#!/usr/bin/env python3
"""
Script para corregir el uso incorrecto del parámetro 'visible' en st.column_config.Column
"""

import os
import re
from pathlib import Path

def fix_column_config_in_file(filepath):
    """Corrige el uso de visible en st.column_config.Column en un archivo."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar patrones de st.column_config.Column con visible
        pattern = r'st\.column_config\.Column\s*\([^)]*visible\s*=\s*[^,)]+[^)]*\)'
        
        if re.search(pattern, content):
            print(f"Encontrado uso de 'visible' en: {filepath}")
            
            # Reemplazar visible=True/False por nada (eliminar el parámetro)
            # Primero, encontrar todos los matches
            matches = list(re.finditer(pattern, content))
            
            # Procesar de atrás hacia adelante para no afectar los índices
            for match in reversed(matches):
                original = match.group(0)
                # Eliminar el parámetro visible
                fixed = re.sub(r',?\s*visible\s*=\s*[^,)]+', '', original)
                # Limpiar comas dobles o comas al final
                fixed = re.sub(r',\s*,', ',', fixed)
                fixed = re.sub(r',\s*\)', ')', fixed)
                fixed = re.sub(r'\(\s*,', '(', fixed)
                
                content = content[:match.start()] + fixed + content[match.end():]
            
            # Guardar el archivo corregido
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✓ Corregido: {filepath}")
            return True
    except Exception as e:
        print(f"Error procesando {filepath}: {e}")
    
    return False

def main():
    """Busca y corrige todos los archivos Python con el problema."""
    root_dir = Path('.')
    fixed_count = 0
    
    # Buscar en todos los archivos Python
    for py_file in root_dir.rglob('*.py'):
        if fix_column_config_in_file(py_file):
            fixed_count += 1
    
    print(f"\nTotal de archivos corregidos: {fixed_count}")
    
    # También buscar específicamente en archivos de Streamlit conocidos
    streamlit_files = [
        'calculadora_streamlit.py',
        'ui/calculadora_streamlit.py',
        'legacy/calculadora_streamlit.py',
        'calculadora_app.py'
    ]
    
    print("\nVerificando archivos específicos de Streamlit...")
    for file in streamlit_files:
        if Path(file).exists():
            print(f"Verificando: {file}")
            fix_column_config_in_file(file)

if __name__ == "__main__":
    main() 