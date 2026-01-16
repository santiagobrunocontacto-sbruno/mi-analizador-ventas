import streamlit as st
import pandas as pd
import google.generativeai as genai

# Configuración visual de la App
st.set_page_config(page_title="Mi Analizador de Ventas", layout="wide")
st.title("📊 Consultor de Datos Inteligente")

# 1. Configuración de la API Key en la barra lateral
with st.sidebar:
    api_key = st.text_input("Ingresá tu Google API Key:", type="password")
    archivo_subido = st.file_uploader("Subí tu archivo CSV", type=["csv"])

if api_key and archivo_subido:
    genai.configure(api_key=api_key)
    
    # 2. Carga de datos
    df = pd.read_csv(archivo_subido, sep=';', encoding='latin1')
    df.columns = df.columns.str.strip()
    
    st.write("### Vista previa de tus datos:")
    st.dataframe(df.head())

    # 3. Chat con los datos
    pregunta = st.text_input("¿Qué querés saber de tus ventas?")
    
    if pregunta:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Tenés este DataFrame 'df' con columnas: {df.columns.tolist()}. Pregunta: {pregunta}. Responde SOLO con el código Python/Pandas para obtener el resultado."
        
        try:
            response = model.generate_content(prompt)
            codigo = response.text.replace('```python', '').replace('```', '').strip()
            
            # Ejecutamos el código y mostramos el resultado
            resultado = eval(codigo)
            st.success(f"**Resultado:** {resultado}")
            
        except Exception as e:
            st.error(f"Hubo un error al procesar la pregunta. Probá ser más específico.")
