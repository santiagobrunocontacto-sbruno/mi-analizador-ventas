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
        # Cargamos el archivo con el separador correcto
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        if 'Venta' in df.columns:
            # Limpieza numérica
            df['Venta_Numerica'] = pd.to_numeric(df['Venta'], errors='coerce').fillna(0)
            df['Fecha_DT'] = pd.to_datetime(df['Fecha de emisión'], dayfirst=True, errors='coerce')

            # --- PROCESAMIENTO DE RESÚMENES (Para que la IA sepa todo) ---
            # 1. Ventas por Marca
            resumen_marca = df.groupby('Marca')['Venta_Numerica'].sum().nlargest(10).to_string() if 'Marca' in df.columns else ""
            
            # 2. Ventas por Categoría
            resumen_cat = df.groupby('Categoria')['Venta_Numerica'].sum().nlargest(10).to_string() if 'Categoria' in df.columns else ""
            
            # 3. Ventas por Mes
            resumen_mes = df.groupby(df['Fecha_DT'].dt.strftime('%Y-%m'))['Venta_Numerica'].sum().to_string() if not df['Fecha_DT'].isnull().all() else ""

            # 4. Ventas por Vendedor
            resumen_vend = df.groupby('Nombre Vendedor')['Venta_Numerica'].sum().nlargest(10).to_string() if 'Nombre Vendedor' in df.columns else ""

            # MÉTRICAS VISUALES
            total_facturado = df['Venta_Numerica'].sum()
            c1, c2, c3 = st.columns(3)
            c1.metric("TOTAL FACTURADO", f"${total_facturado:,.2f}")
            c2.metric("OPERACIONES", f"{len(df):,}")
            c3.metric("TICKET PROMEDIO", f"${(total_facturado/len(df)):,.2f}")
            
            st.write("---")
            pregunta = st.text_input("¿Qué querés saber? (Marcas, Meses, Vendedores, Categorías...)")
            
            if pregunta:
                modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(modelos[0])
                
                # Le pasamos TODO el menú de datos ya calculados
                prompt = f"""
                Sos un experto en análisis comercial. Estos son los datos de la empresa:
                - TOTAL GENERAL: {total_facturado}
                - VENTAS POR MARCA: {resumen_marca}
                - VENTAS POR CATEGORÍA: {resumen_cat}
                - VENTAS POR MES: {resumen_mes}
                - VENTAS POR VENDEDOR: {resumen_vend}
                
                Pregunta del usuario: {pregunta}
                
                Instrucción: Usa los datos de arriba para responder. Si te preguntan por algo que no está arriba, aclará que no tenés ese resumen específico. Responde de forma ejecutiva.
                """
                with st.spinner('Consultando datos...'):
                    response = model.generate_content(prompt)
                    st.info(response.text)
            
            # Gráfico de apoyo visual para Marcas
            if 'Marca' in df.columns:
                st.
