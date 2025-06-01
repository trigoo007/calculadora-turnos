#!/usr/bin/env python3
"""
Script de prueba para verificar que Streamlit funciona correctamente
"""

import streamlit as st
import pandas as pd

st.title("🧪 Test de Streamlit - Calculadora de Turnos")

st.write("Si ves este mensaje, Streamlit está funcionando correctamente.")

# Test básico de data_editor con column_config
st.subheader("Test de configuración de columnas")

# Crear datos de prueba
df_test = pd.DataFrame({
    'Nombre': ['Test 1', 'Test 2', 'Test 3'],
    'Activo': [True, False, True],
    'Número': [1, 2, 3]
})

# Test de data_editor con column_config
edited_df = st.data_editor(
    df_test,
    column_config={
        "Activo": st.column_config.CheckboxColumn(
            "Estado",
            help="Marque si está activo"
        ),
        "Número": st.column_config.NumberColumn(
            "Cantidad",
            help="Número de elementos"
        )
    },
    hide_index=True,
    use_container_width=True
)

st.write("Datos editados:", edited_df)

st.success("✅ Test completado exitosamente!")
