import streamlit as st

st.title("Prueba")
archivo = st.file_uploader("Sube Excel")

if archivo:
    st.success("Funciona")