import streamlit as st
import pandas as pd
import google.generativeai as genai

# Configuración de la página
st.set_page_config(page_title="Consultor de Ventas", layout="wide")
st.title("📊 Mi Analizador de Datos")

# Barra lateral para carga de datos
with st.sidebar:
    api_key = st.text_input("Ingresá tu Google API Key:", type="password")
    uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv"])

# Lógica principal
if api_key and uploaded_file:
    try:
        # Configurar la IA
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Leer el archivo con detección automática de separador (punto y coma o coma)
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        st.write("### Vista previa de tus datos:")
        st.dataframe(df.head())

        # Caja de preguntas
        pregunta = st.text_input("¿Qué querés saber sobre tus ventas?")
        
        if pregunta:
            # Creamos el contexto para la IA
            # Solo enviamos las primeras 100 filas si el archivo es muy grande para no trabar la IA
            datos_contexto = df.head(100).to_string(index=False)
            prompt = f"Actuá como un experto contable. Analizá estos datos de ventas:\n{datos_contexto}\n\nPregunta: {pregunta}\n\nRespondé de forma breve y profesional en español."
            
            with st.spinner('Pensando...'):
                try:
                    response = model.generate_content(prompt)
                    st.success(response.text)
                except Exception as e:
                    st.error(f"Error al generar respuesta: {e}")
                    
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
else:
    st.info("💡 Por favor, ingresá tu API Key y subí un archivo para comenzar.")
