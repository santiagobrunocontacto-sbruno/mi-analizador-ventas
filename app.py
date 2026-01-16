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
        
        # 1. DETECTOR AUTOMÁTICO DE MODELO (Clave para que no de error 404)
        # Esto busca qué modelos tenés activos (v2.5, v1.5, etc) y elige el mejor
        modelos_visibles = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Si encuentra el 2.5 que vimos en tu foto, lo usa. Si no, el primero que haya.
        model_name = 'models/gemini-2.5-flash' if 'models/gemini-2.5-flash' in modelos_visibles else modelos_visibles[0]
        model = genai.GenerativeModel(model_name)
        
        # 2. LECTURA Y LIMPIEZA MATEMÁTICA
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        if 'Venta' in df.columns:
            # Limpiamos los números: sacamos puntos y cambiamos coma por punto
            df['Venta_Limpia'] = df['Venta'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Venta_Limpia'] = pd.to_numeric(df['Venta_Limpia'], errors='coerce').fillna(0)
            total_facturado = df['Venta_Limpia'].sum()
            st.success(f"✅ SISTEMA: Total Facturado Real = ${total_facturado:,.2f}")
        else:
            total_facturado = "No encontrado"
            st.warning("⚠️ No veo la columna 'Venta'. Revisá el nombre en el Excel.")

        st.write(f"### Datos (Modelo: {model_name})")
        st.dataframe(df.head())

        pregunta = st.text_input("¿Qué querés preguntarle a la IA?")
        
        if pregunta:
            # Le pasamos el total matemático a la IA para que no se equivoque
            prompt = f"Datos: {len(df)} filas. Total Venta: {total_facturado}. Columnas: {list(df.columns)}. Pregunta: {pregunta}"
            with st.spinner('Analizando...'):
                response = model.generate_content(prompt)
                st.success(response.text)
                    
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("💡 Pegá tu API Key y subí el archivo para empezar.")
