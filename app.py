import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="Consultor de Ventas", layout="wide")
st.title("📊 Mi Analizador de Datos")

# Barra lateral
with st.sidebar:
    api_key = st.text_input("Ingresá tu Google API Key:", type="password")
    uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv"])

if api_key and uploaded_file:
    genai.configure(api_key=api_key)
  model = genai.GenerativeModel('gemini-pro')
    
    df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
    st.write("### Vista previa de tus datos:")
    st.dataframe(df.head())

    pregunta = st.text_input("¿Qué querés saber?")
    
    if pregunta:
        # Aquí le damos instrucciones ultra claras a la IA
        prompt = f"Actuá como un experto contable. Analizá estos datos: {df.to_string(index=False)}. Pregunta: {pregunta}. Respondé de forma breve y clara."
        
        try:
            response = model.generate_content(prompt)
            st.success(response.text)
        except Exception as e:
            st.error(f"Error de la IA: {e}")
else:
    st.warning("Falta la API Key o el archivo CSV.")
