import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="Auditor Comercial", layout="wide")
st.title("📊 Sistema de Auditoría de Ventas")

with st.sidebar:
    api_key = st.text_input("Ingresá tu API Key:", type="password")
    uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv"])

if api_key and uploaded_file:
    try:
        genai.configure(api_key=api_key)
        
        # 1. LEER ARCHIVO (Separador automático para fac limpia.csv)
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        df.columns = df.columns.str.strip()
        
        # 2. PROCESAR COLUMNA VENTA
        col_v = next((c for c in df.columns if 'venta' in c.lower()), None)
        
        if col_v:
            df['Venta_N'] = pd.to_numeric(df[col_v], errors='coerce').fillna(0)
            total = df['Venta_N'].sum()
            
            # Mostramos métricas básicas de inmediato
            st.metric("TOTAL FACTURADO", f"${total:,.2f}")
            
            # 3. PREPARAR RESUMEN CORTO (Para no gastar cuota)
            # Solo enviamos el Top 5 de cada cosa para que la IA gaste menos 'combustible'
            res_marca = df.groupby('Marca')['Venta_N'].sum().nlargest(5).to_dict() if 'Marca' in df.columns else {}
            res_vend = df.groupby('Nombre Vendedor')['Venta_N'].sum().nlargest(5).to_dict() if 'Nombre Vendedor' in df.columns else {}
            
            st.write("---")
            pregunta = st.text_input("¿Qué necesitás saber?")
            
            if pregunta:
                # MODELO FLASH: Es el que más cupo tiene en la versión gratis
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                contexto = f"Datos: Total {total}. Top Marcas: {res_marca}. Top Vendedores: {res_vend}. Pregunta: {pregunta}"
                
                try:
                    with st.spinner('Analizando...'):
                        response = model.generate_content(contexto)
                        st.success(response.text)
                except Exception as ai_err:
                    if "429" in str(ai_err):
                        st.error("⚠️ Cuota agotada. Por favor, esperá 60 segundos antes de preguntar de nuevo.")
                    else:
                        st.error(f"Error de la IA: {ai_err}")
                        
            # Gráfico simple para que siempre tengas info visual
            if 'Marca' in df.columns:
                st.subheader("Top Marcas")
                st.bar_chart(df.groupby('Marca')['Venta_N'].sum().nlargest(10))

        else:
            st.error("No se encontró la columna 'Venta'.")

    except Exception as e:
        st.error(f"Error técnico: {e}")
else:
    st.info("💡 Pegá tu API Key y subí el archivo para empezar.")
