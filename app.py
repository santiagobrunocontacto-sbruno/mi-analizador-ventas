import streamlit as st
import pandas as pd
import google.generativeai as genai

# Configuración de la página
st.set_page_config(page_title="Consultor de Ventas", layout="wide")
st.title("📊 Mi Analizador de Datos")

# Barra lateral
with st.sidebar:
    api_key = st.text_input("Ingresá tu Google API Key:", type="password")
    uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv"])

if api_key and uploaded_file:
    try:
        # CONFIGURACIÓN REFORZADA
        genai.configure(api_key=api_key)
        
        # Probamos con el nombre de modelo más estándar de todos
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Leer el archivo
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        st.write("### Vista previa de tus datos:")
        st.dataframe(df.head())

        pregunta = st.text_input("¿Qué querés saber sobre tus ventas?")
        
        if pregunta:
            # Simplificamos el contexto para que no pese tanto
            columnas = ", ".join(df.columns.tolist())
            datos_muestra = df.head(30).to_string(index=False)
            
            prompt = f"""
            Actuá como un analista de datos. 
            Columnas disponibles: {columnas}
            Datos:
            {datos_muestra}
            
            Pregunta: {pregunta}
            Responde en español de forma concisa.
            """
            
            with st.spinner('Analizando...'):
                try:
                    # USAMOS EL MÉTODO MÁS COMPATIBLE
                    response = model.generate_content(prompt)
                    st.success(response.text)
                except Exception as e:
                    # SEGUNDO INTENTO CON NOMBRE ALTERNATIVO SI FALLA EL PRIMERO
                    try:
                        model_alt = genai.GenerativeModel('models/gemini-pro')
                        response = model_alt.generate_content(prompt)
                        st.success(response.text)
                    except:
                        st.error("Google no reconoce el modelo. Revisá que tu API Key sea correcta y esté activa.")
                    
    except Exception as e:
        st.error(f"Error al procesar: {e}")
else:
    st.info("💡 Ingresá tu API Key y subí el archivo para empezar.")
