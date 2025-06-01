#!/usr/bin/env python3
"""
Parche para corregir el error de st.column_config.Column con parámetro 'visible'

El error ocurre porque 'visible' no es un parámetro válido para st.column_config.Column.
Los parámetros válidos son: width, help, disabled, required
"""

# INCORRECTO - Esto causa el error:
# column_config = {
#     "ID": st.column_config.Column(
#         "ID",
#         disabled=True,
#         required=True,
#         visible=False  # ❌ Este parámetro NO existe
#     )
# }

# CORRECTO - Usar solo parámetros válidos:
# column_config = {
#     "ID": st.column_config.Column(
#         "ID",
#         disabled=True,
#         required=True
#     )
# }

# Si necesitas ocultar una columna, hay varias opciones:

# Opción 1: No incluir la columna en el DataFrame mostrado
# df_display = df.drop(columns=['ID'])  # Eliminar la columna antes de mostrar

# Opción 2: Usar st.dataframe con hide_index si es el índice
# st.dataframe(df, hide_index=True)

# Opción 3: Usar column_order para controlar qué columnas se muestran
# st.dataframe(df, column_order=['col1', 'col2'])  # Solo muestra estas columnas

print("""
SOLUCIÓN AL ERROR:

El error "TypeError: Column() got an unexpected keyword argument 'visible'" 
ocurre porque el parámetro 'visible' no existe en st.column_config.Column().

Para solucionarlo:

1. Busca en tu código donde uses st.column_config.Column con visible=True/False
2. Elimina el parámetro 'visible'
3. Si necesitas ocultar columnas, usa una de estas alternativas:
   - Elimina la columna del DataFrame antes de mostrarlo
   - Usa column_order para especificar qué columnas mostrar
   - Usa hide_index=True si es la columna índice

Ejemplo de código corregido:

# Antes (INCORRECTO):
column_config = {
    "ID": st.column_config.Column(
        "ID",
        disabled=True,
        required=True,
        visible=False  # ❌ Eliminar esta línea
    )
}

# Después (CORRECTO):
column_config = {
    "ID": st.column_config.Column(
        "ID",
        disabled=True,
        required=True
    )
}
""") 