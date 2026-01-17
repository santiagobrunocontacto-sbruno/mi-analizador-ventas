import streamlit as st
import pandas as pd
import google.generativeai as genai

# Configuración inicial
st.set_page_config(page_title="Consultor de Ventas", layout="wide")
st.title("📊 Mi Analizador de Negocios")

with st.sidebar:
    api_key = st.text_input("Google API Key:", type="password")
    uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv"])

if api_key and uploaded_file:
    try:
        genai.configure(api_key=api_key)
        # Lectura automática del separador ';'
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        if 'Venta' in df.columns:
            # Procesamiento de datos
            df['Venta_Num'] = pd.to_numeric(df['Venta'], errors='coerce').fillna(0)
            df['Fecha_DT'] = pd.to_datetime(df['Fecha de emisión'], dayfirst=True, errors='coerce')

            # --- RESÚMENES PARA QUE LA IA NO FALLE ---
            # Ventas por Marca
            res_marca = df.groupby('Marca')['Venta_Num'].sum().nlargest(10).to_dict() if 'Marca' in df.columns else {}
            # Ventas por Categoría
            res_cat = df.groupby('Categoria')['Venta_Num'].sum().nlargest(10).to_dict() if 'Categoria' in df.columns else {}
            # Ventas por Mes
            res_mes = df.groupby(df['Fecha_DT'].dt.strftime('%Y-%m'))['Venta_Num'].sum().to_dict() if not df['Fecha_DT'].isnull().all() else {}

            # MÉTRICAS PRINCIPALES
            total = df['Venta_Num'].sum()
            c1, c2, c3 = st.columns(3)
            c1.metric("TOTAL FACTURADO", f"${total:,.2f}")
            c2.metric("OPERACIONES", f"{len(df):,}")
            c3.metric("TICKET PROMEDIO", f"${(total/len(df)):,.2f}")
            
            st.write("---")
            pregunta = st.text_input("¿Qué querés saber? (Ej: Ventas por marca, por mes...)")
            
            if pregunta:
                modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(modelos[0])
                
                # Contexto enriquecido para la IA
                prompt = f"""
                Datos de la empresa:
                - Total: {total}
                - Marcas Top: {res_marca}
                - Categorías Top: {res_cat}
                - Meses: {res_mes}
                
                Pregunta: {pregunta}
                Responde de forma ejecutiva basándote en estos números.
                """
                with st.spinner('Analizando...'):
                    response = model.generate_content(prompt)
                    st.info(response.text)
            
            # Gráfico visual de apoyo
            if 'Marca' in df.columns:
                st.write("### Participación por Marca")
                st.bar_chart(df.groupby('Marca')['Venta_Num'].sum().nlargest(10))
        
    except Exception as e:
        st.error(f"Hubo un problema: {e}")
else:
    st.info("💡 Por favor, ingresá tu API Key y cargá el archivo para activar el panel.")
