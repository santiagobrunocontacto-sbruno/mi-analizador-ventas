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
        # Configurar la IA con el nombre de modelo más compatible
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Leer el archivo con detección automática
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        st.write("### Vista previa de tus datos:")
        st.dataframe(df.head())

        # Caja de preguntas
        pregunta = st.text_input("¿Qué querés saber sobre tus ventas?")
        
        if pregunta:
            # Le pasamos los nombres de las columnas para que no se pierda
            columnas = ", ".join(df.columns.tolist())
            datos_contexto = df.head(50).to_string(index=False)
            
            prompt = f"""
            Actuá como un experto contable. 
            Las columnas de este archivo son: {columnas}.
            Aquí tenés una muestra de los datos:
            {datos_contexto}
            
            Pregunta del usuario: {pregunta}
            
            Instrucción: Si el usuario pregunta por ventas o totales y no ves una columna llamada 'Venta', buscá la columna que parezca tener los montos (como 'Importe', 'Total' o 'Precio'). Respondé de forma clara en español.
            """
            
            with st.spinner('La IA está analizando tus datos...'):
                try:
                    response = model.generate_content(prompt)
                    st.success(response.text)
                except Exception as e:
                    # Si falla gemini-pro, intentamos con la versión flash pero con el nombre alternativo
                    try:
                        model_alt = genai.GenerativeModel('models/gemini-1.5-flash-latest')
                        response = model_alt.generate_content(prompt)
                        st.success(response.text)
                    except:
                        st.error(f"Error de conexión con Google: {e}")
                    
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
else:
    st.info("💡 Por favor, ingresá tu API Key y subí un archivo para comenzar.")
