import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="Auditor de Ventas", layout="wide")
st.title("🚀 Panel de Control de Ventas")

with st.sidebar:
    api_key = st.text_input("Ingresá tu Google API Key:", type="password")
    uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv"])

if api_key and uploaded_file:
    try:
        genai.configure(api_key=api_key)
        
        # 1. LEER CON EL SEPARADOR CORRECTO (punto y coma)
        # Usamos sep=None para que Python detecte si es ; o , automáticamente
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        # 2. PROCESAR COLUMNA VENTA
        if 'Venta' in df.columns:
            # Convertimos a número asegurando que no haya errores de texto
            df['Venta_Numerica'] = pd.to_numeric(df['Venta'], errors='coerce').fillna(0)
            
            total_facturado = df['Venta_Numerica'].sum()
            operaciones = len(df)
            ticket_promedio = total_facturado / operaciones if operaciones > 0 else 0
            
            # MOSTRAR MÉTRICAS
            c1, c2, c3 = st.columns(3)
            c1.metric("TOTAL FACTURADO", f"${total_facturado:,.2f}")
            c2.metric("OPERACIONES", f"{operaciones:,}")
            c3.metric("TICKET PROMEDIO", f"${ticket_promedio:,.2f}")
            
            st.write("---")
            pregunta = st.text_input("¿Qué querés consultar sobre estas ventas?")
            
            if pregunta:
                modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(modelos[0])
                
                # Le pasamos los datos clave para que no invente
                prompt = f"Total ventas: {total_facturado}. Operaciones: {operaciones}. Pregunta: {pregunta}"
                
                with st.spinner('Analizando...'):
                    response = model.generate_content(prompt)
                    st.info(response.text)
        else:
            st.error("No se encontró la columna 'Venta'. Revisá el encabezado del archivo.")

        st.write("### Vista previa de los datos cargados")
        st.dataframe(df.head(10))
                
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("💡 Pegá tu API Key y subí el archivo para empezar.")
