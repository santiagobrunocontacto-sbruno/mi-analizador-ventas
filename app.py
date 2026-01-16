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
        
        # BUSCADOR AUTOMÁTICO DE MODELOS
        # Esto evita el error 404 porque elige uno que SÍ exista en tu cuenta
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = available_models[0] if available_models else 'gemini-pro'
        model = genai.GenerativeModel(model_name)
        
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        st.write(f"### Datos cargados (Usando modelo: {model_name})")
        st.dataframe(df.head())

        pregunta = st.text_input("¿Qué querés saber?")
        
        if pregunta:
            prompt = f"Datos: {df.head(20).to_string()}\n\nPregunta: {pregunta}"
            with st.spinner('Analizando...'):
                try:
                    response = model.generate_content(prompt)
                    st.success(response.text)
                except Exception as e:
                    st.error(f"Error al responder: {e}")
                    
    except Exception as e:
        st.error(f"Error de configuración: {e}. Verificá que tu API Key sea válida.")
else:
    st.info("💡 Ingresá tu API Key y subí el archivo.")
