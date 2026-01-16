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
        
        # Detector de modelo automático
        modelos_visibles = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos_visibles else modelos_visibles[0]
        model = genai.GenerativeModel(model_name)
        
        # Leer el archivo completo
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        # --- LIMPIEZA AGRESIVA DE NÚMEROS ---
        if 'Venta' in df.columns:
            # 1. Convertimos a string y sacamos espacios
            df['Venta_Aux'] = df['Venta'].astype(str).str.strip()
            # 2. Sacamos los puntos (que en Arg son miles)
            df['Venta_Aux'] = df['Venta_Aux'].str.replace('.', '', regex=False)
            # 3. Cambiamos la coma por punto (para que Python lo entienda como decimal)
            df['Venta_Aux'] = df['Venta_Aux'].str.replace(',', '.', regex=False)
            # 4. Convertimos a número real
            df['Venta_Numerica'] = pd.to_numeric(df['Venta_Aux'], errors='coerce').fillna(0)
            
            total_calculado = df['Venta_Numerica'].sum()
            
            # Buscamos la descripción más vendida (basado en cantidad de veces que aparece)
            desc_top = df['Descripción'].value_counts().idxmax() if 'Descripción' in df.columns else "N/A"
            
            st.success(f"✅ Total Facturado Real: ${total_calculado:,.2f}")
        else:
            total_calculado = 0
            st.warning("⚠️ No se encontró la columna 'Venta'")

        st.write("### Vista previa de tus datos")
        st.dataframe(df.head())

        pregunta = st.text_input("¿Qué querés saber sobre tus ventas?")
        
        if pregunta:
            # Le pasamos a la IA los datos masticados para que no invente ceros
            prompt = f"""
            Actuá como experto contable. 
            DATOS CLAVE:
            - Total de Ventas: {total_calculado}
            - Registros totales: {len(df)}
            - Columnas: {list(df.columns)}
            
            Pregunta: {pregunta}
            
            Responde con los números que te di arriba. Si preguntan por la descripción más vendida, 
            analizá los datos y respondé directamente.
            """
            with st.spinner('Procesando...'):
                response = model.generate_content(prompt)
                st.info(response.text)
                    
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("💡 Pegá tu API Key y subí el archivo para empezar.")
