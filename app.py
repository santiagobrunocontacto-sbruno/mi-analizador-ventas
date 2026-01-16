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
        
        # Detector de modelo automático para evitar el error 404
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
        model = genai.GenerativeModel(model_name)
        
        # Leer el archivo completo
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        # --- LIMPIEZA DE DATOS ---
        # 1. Buscamos la columna de guita (puede llamarse 'Venta' o 'Ventas')
        col_venta = next((c for c in df.columns if 'venta' in c.lower()), None)
        
        total_final = 0
        if col_venta:
            # Limpieza: quitamos puntos (miles), cambiamos comas por puntos (decimales)
            df['Venta_Calculo'] = df[col_venta].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Venta_Calculo'] = pd.to_numeric(df['Venta_Calculo'], errors='coerce').fillna(0)
            total_final = df['Venta_Calculo'].sum()
            st.success(f"📈 Total detectado matemáticamente: ${total_final:,.2f}")
        else:
            st.warning("No encontré una columna llamada 'Venta'.")

        st.write("### Vista previa de tus datos:")
        st.dataframe(df.head())

        pregunta = st.text_input("¿Qué querés saber?")
        
        if pregunta:
            # En lugar de mandarle todas las filas, le mandamos un RESUMEN
            # Esto evita que la IA se sature y tire cualquier número
            top_clientes = df['Razón social'].value_counts().head(5).to_string() if 'Razón social' in df.columns else ""
            
            prompt = f"""
            Actuá como un experto contable. 
            DATOS REALES DEL ARCHIVO:
            - Cantidad de operaciones: {len(df)}
            - TOTAL FACTURADO (Suma real): {total_final}
            - Principales Clientes: {top_clientes}
            
            Pregunta: {pregunta}
            
            Responde basado ÚNICAMENTE en los números de arriba. No digas que el total es 0, porque ya sabemos que es {total_final}.
            """
            
            with st.spinner('Analizando...'):
                response = model.generate_content(prompt)
                st.info(response.text)
                    
    except Exception as e:
        st.error(f"Error técnico: {e}")
else:
    st.info("💡 Pegá tu API Key y cargá el archivo.")
