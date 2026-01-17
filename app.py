import streamlit as st
import pandas as pd
import google.generativeai as genai
import re

st.set_page_config(page_title="Auditor de Ventas", layout="wide")
st.title("🚀 Panel de Control de Ventas")

with st.sidebar:
    api_key = st.text_input("Ingresá tu Google API Key:", type="password")
    uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv"])

def limpiar_monto_argentino(texto):
    if pd.isna(texto): return 0.0
    s = str(texto).strip()
    # 1. Borramos los puntos (que suelen ser separadores de miles)
    s = s.replace('.', '')
    # 2. Cambiamos la coma decimal por punto (para que Python lo entienda)
    s = s.replace(',', '.')
    # 3. Quitamos cualquier cosa que no sea número o el punto decimal nuevo
    s = re.sub(r'[^0-9.]', '', s)
    try:
        return float(s)
    except:
        return 0.0

if api_key and uploaded_file:
    try:
        genai.configure(api_key=api_key)
        # Leemos el archivo con codificación común en Argentina
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        # BUSCAR COLUMNA DE VENTA (Flexible a mayúsculas/minúsculas)
        col_v = next((c for c in df.columns if 'venta' in c.lower()), None)
        
        if col_v:
            df['Venta_Numerica'] = df[col_v].apply(limpiar_monto_argentino)
            total_facturado = df['Venta_Numerica'].sum()
            operaciones = len(df)
            ticket_promedio = total_facturado / operaciones if operaciones > 0 else 0
            
            # MOSTRAR MÉTRICAS (Uso de miles de millones si es necesario)
            c1, c2, c3 = st.columns(3)
            c1.metric("TOTAL FACTURADO", f"${total_facturado:,.2f}")
            c2.metric("OPERACIONES", f"{operaciones:,}")
            c3.metric("TICKET PROMEDIO", f"${ticket_promedio:,.2f}")
            
            st.write("---")
            pregunta = st.text_input("¿Qué querés consultar?")
            
            if pregunta:
                # Detector automático de modelo
                modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(modelos[0])
                
                # Resumen compacto para la IA
                resumen = f"Ventas totales: {total_facturado}. Cantidad de tickets: {operaciones}. Columnas: {list(df.columns)}"
                
                with st.spinner('Analizando...'):
                    response = model.generate_content(f"{resumen}\n\nPregunta: {pregunta}")
                    st.info(response.text)
        else:
            st.warning("⚠️ No se detectó la columna 'Venta'.")
            
        st.dataframe(df.head(10))
                
    except Exception as e:
        st.error(f"Error al procesar: {e}")
else:
    st.info("💡 Pegá tu API Key y subí el archivo CSV.")
