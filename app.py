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
        
        # Detector automático de modelo
        modelos_visibles = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos_visibles else modelos_visibles[0]
        model = genai.GenerativeModel(model_name)
        
        # Leer el archivo completo
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        # --- LIMPIEZA Y CÁLCULOS AUTOMÁTICOS ---
        # Buscamos la columna de guita
        col_v = next((c for c in df.columns if 'venta' in c.lower()), None)
        
        if col_v:
            # Limpiamos el formato argentino (punto de mil, coma decimal)
            valores = df[col_v].astype(str).str.strip().str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Venta_Numerica'] = pd.to_numeric(valores, errors='coerce').fillna(0)
            
            total_facturado = df['Venta_Numerica'].sum()
            operaciones = len(df)
            ticket_promedio = total_facturado / operaciones if operaciones > 0 else 0
            
            # MOSTRAR MÉTRICAS ARRIBA (Para que sea simple para cualquiera)
            col1, col2, col3 = st.columns(3)
            col1.metric("TOTAL FACTURADO", f"${total_facturado:,.2f}")
            col2.metric("OPERACIONES", f"{operaciones:,}")
            col3.metric("TICKET PROMEDIO", f"${ticket_promedio:,.2f}")
        
        st.write("---")
        st.write("### 🔍 Consultor Inteligente")
        pregunta = st.text_input("Preguntale a la IA sobre estos datos (ej: ¿Cuál fue el mejor cliente?)")
        
        if pregunta:
            # Resumen para la IA (para que no se sature con 10k filas)
            top_clientes = df.groupby('Razón social')['Venta_Numerica'].sum().nlargest(5).to_string() if 'Razón social' in df.columns else "N/A"
            top_productos = df.groupby('Descripción')['Venta_Numerica'].sum().nlargest(5).to_string() if 'Descripción' in df.columns else "N/A"
            
            prompt = f"""
            Sos un Consultor de Negocios experto. El usuario tiene un archivo con {operaciones} filas.
            Total Ventas: {total_facturado}
            Top 5 Clientes: {top_clientes}
            Top 5 Productos: {top_productos}
            Columnas: {list(df.columns)}

            Instrucción: Responde la pregunta del usuario de forma directa y profesional. 
            Si te preguntan por totales, usa el valor {total_facturado}. No expliques cómo calcularlo.
            Pregunta: {pregunta}
            """
            with st.spinner('Analizando...'):
                response = model.generate_content(prompt)
                st.info(response.text)

        st.write("---")
        st.write("### Vista previa de los datos")
        st.dataframe(df.head(20))
                
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("💡 Esperando API Key y archivo CSV...")
