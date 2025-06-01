import streamlit as st

st.set_page_config(page_title="Test Simple", layout="wide")

st.title("Test Simple de Streamlit")
st.write("Si puedes ver esto, Streamlit está funcionando correctamente.")

# Test básico de widgets
nombre = st.text_input("Ingresa tu nombre:")
if nombre:
    st.write(f"Hola, {nombre}!")

# Test de columnas
col1, col2 = st.columns(2)
with col1:
    st.metric("Métrica 1", 100)
with col2:
    st.metric("Métrica 2", 200)

# Test de dataframe
import pandas as pd
df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6]
})
st.dataframe(df) 