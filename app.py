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
        # Detectamos el separador ; que usa tu archivo
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        if 'Venta' in df.columns:
            # Procesamiento de números
            df['Venta_Numerica'] = pd.to_numeric(df['Venta'], errors='coerce').fillna(0)
            
            # --- NUEVO: PROCESAMIENTO DE FECHAS ---
            # Convertimos la columna 'Fecha de emisión' a formato fecha real
            df['Fecha_DT'] = pd.to_datetime(df['Fecha de emisión'], dayfirst=True, errors='coerce')
            
            # Resumen por mes para la IA
            ventas_por_mes = ""
            if not df['Fecha_DT'].isnull().all():
                resumen_mensual = df.groupby(df['Fecha_DT'].dt.strftime('%Y-%m'))['Venta_Numerica'].sum()
                ventas_por_mes = resumen_mensual.to_string()

            # Resumen por Vendedor
            ventas_vendedor = df.groupby('Nombre Vendedor')['Venta_Numerica'].sum().nlargest(5).to_string() if 'Nombre Vendedor' in df.columns else ""

            # MÉTRICAS PRINCIPALES
            total_facturado = df['Venta_Numerica'].sum()
            c1, c2, c3 = st.columns(3)
            c1.metric("TOTAL FACTURADO", f"${total_facturado:,.2f}")
            c2.metric("OPERACIONES", f"{len(df):,}")
            c3.metric("TICKET PROMEDIO", f"${(total_facturado/len(df)):,.2f}")
            
            st.write("---")
            pregunta = st.text_input("¿Qué querés saber? (Ej: Ventas por mes, mejor vendedor...)")
            
            if pregunta:
                modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(modelos[0])
                
                # Le pasamos a la IA los datos ya agrupados
                prompt = f"""
                Actuá como analista senior. Datos analizados por el sistema:
                - TOTAL GENERAL: {total_facturado}
                - VENTAS POR MES:
                {ventas_por_mes}
                - TOP 5 VENDEDORES:
                {ventas_vendedor}
                
                Pregunta del usuario: {pregunta}
                
                Respuesta: (Si te piden ventas por mes, usá los datos de arriba. Respondé de forma clara y directa).
                """
                with st.spinner('Analizando...'):
                    response = model.generate_content(prompt)
                    st.info(response.text)
            
            st.write("### Datos Mensuales (Vista rápida)")
            if not df['Fecha_DT'].isnull().all():
                st.bar_chart(df.groupby(df['Fecha_DT'].dt.strftime('%m-%Y'))['Venta_Numerica'].sum())
        
    except Exception as e:
        st.error(f"Error: {e}")
