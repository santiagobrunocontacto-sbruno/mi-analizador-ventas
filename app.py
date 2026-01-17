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
        # Cargamos el archivo detectando el separador ; automáticamente
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        if 'Venta' in df.columns:
            # Procesamiento numérico y de fechas
            df['Venta_Numerica'] = pd.to_numeric(df['Venta'], errors='coerce').fillna(0)
            df['Fecha_DT'] = pd.to_datetime(df['Fecha de emisión'], dayfirst=True, errors='coerce')

            # --- PRE-CÁLCULOS PARA LA IA (Evita errores de respuesta) ---
            # Ventas por Marca
            res_marca = df.groupby('Marca')['Venta_Numerica'].sum().nlargest(10).to_string() if 'Marca' in df.columns else "N/A"
            # Ventas por Categoría
            res_cat = df.groupby('Categoria')['Venta_Numerica'].sum().nlargest(10).to_string() if 'Categoria' in df.columns else "N/A"
            # Ventas por Mes
            res_mes = df.groupby(df['Fecha_DT'].dt.strftime('%Y-%m'))['Venta_Numerica'].sum().to_string() if not df['Fecha_DT'].isnull().all() else "N/A"
            # Ventas por Vendedor
            res_vend = df.groupby('Nombre Vendedor')['Venta_Numerica'].sum().nlargest(10).to_string() if 'Nombre Vendedor' in df.columns else "N/A"

            # MÉTRICAS VISUALES
            total_facturado = df['Venta_Numerica'].sum()
            c1, c2, c3 = st.columns(3)
            c1.metric("TOTAL FACTURADO", f"${total_facturado:,.2f}")
            c2.metric("OPERACIONES", f"{len(df):,}")
            c3.metric("TICKET PROMEDIO", f"${(total_facturado/len(df)):,.2f}")
            
            st.write("---")
            pregunta = st.text_input("Consultá sobre Marcas, Meses, Vendedores o Categorías:")
            
            if pregunta:
                modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(modelos[0])
                
                # Le pasamos a la IA los resúmenes ya masticados
                prompt = f"""
                Sos un experto comercial. Usá estos datos reales para responder:
                - TOTAL: {total_facturado}
                - RANKING MARCAS: {res_marca}
                - RANKING CATEGORÍAS: {res_cat}
                - VENTAS POR MES: {res_mes}
                - TOP VENDEDORES: {res_vend}
                
                Pregunta: {pregunta}
                Responde de forma clara y directa. Si el dato no está en el ranking, menciónalo.
                """
                with st.spinner('Analizando...'):
                    response = model.generate_content(prompt)
                    st.info(response.text)
            
            # Gráfico visual de apoyo
            if 'Marca' in df.columns:
                st.write("### Gráfico: Top Marcas por Ventas")
                st.bar_chart(df.groupby('Marca')['Venta_Numerica'].sum().nlargest(10))
        
    except Exception as e:
        st.error(f"Error técnico: {e}")
else:
    st.info("💡 Pegá tu API Key y subí el archivo para empezar.")
