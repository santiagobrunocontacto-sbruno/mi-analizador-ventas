import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="Consultor de Ventas", layout="wide")
st.title("📊 Mi Analizador de Datos")

with st.sidebar:
    api_key = st.text_input("Ingresá tu Google API Key:", type="password")
    uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv"])

if api_key and uploaded_file:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Leemos TODO el archivo
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        # LIMPIEZA DE NÚMEROS: Intentamos convertir la columna 'Venta' a número real
        if 'Venta' in df.columns:
            # Quitamos puntos de miles y cambiamos comas por puntos decimales
            df['Venta_Limpia'] = df['Venta'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Venta_Limpia'] = pd.to_numeric(df['Venta_Limpia'], errors='coerce').fillna(0)
            total_real = df['Venta_Limpia'].sum()
        else:
            total_real = "Columna 'Venta' no encontrada"

        st.write(f"### Datos cargados con éxito")
        st.write(f"**Total calculado por sistema:** ${total_real:,.2f}" if isinstance(total_real, float) else total_real)
        st.dataframe(df.head())

        pregunta = st.text_input("¿Qué más querés saber?")
        
        if pregunta:
            # Aquí le pasamos un resumen estadístico, no todas las filas, para que no se maree
            resumen = df.describe().to_string()
            columnas = ", ".join(df.columns)
            prompt = f"Datos: Archivo con {len(df)} filas. Columnas: {columnas}. Suma total de Ventas: {total_real}. Resumen: {resumen}. Pregunta: {pregunta}"
            
            with st.spinner('Analizando...'):
                response = model.generate_content(prompt)
                st.success(response.text)
                    
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("💡 Ingresá tu API Key y subí el archivo.")
