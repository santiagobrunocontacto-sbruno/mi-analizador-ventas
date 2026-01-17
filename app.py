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
    """Convierte '722.107,50' o '1.200' en un número real 722107.50"""
    if pd.isna(texto): return 0.0
    s = str(texto).strip()
    # Si tiene coma y punto, el punto es de miles (lo borramos) y la coma es decimal
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    # Si solo tiene coma, es el decimal
    elif ',' in s:
        s = s.replace(',', '.')
    # Si solo tiene punto, pero parece de miles (ej: 1.200), lo sacamos
    # Un punto es de miles si tiene 3 dígitos después
    elif '.' in s:
        partes = s.split('.')
        if len(partes[-1]) == 3:
            s = s.replace('.', '')
    
    # Limpieza final de cualquier símbolo raro ($ o espacios)
    s = re.sub(r'[^0-9.]', '', s)
    try:
        return float(s)
    except:
        return 0.0

if api_key and uploaded_file:
    try:
        genai.configure(api_key=api_key)
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        # BUSCAR COLUMNA DE VENTA
        col_v = next((c for c in df.columns if 'venta' in c.lower()), None)
        
        if col_v:
            # Aplicamos la limpieza fila por fila
            df['Venta_Numerica'] = df[col_v].apply(limpiar_monto_argentino)
            
            total_facturado = df['Venta_Numerica'].sum()
            operaciones = len(df)
            ticket_promedio = total_facturado / operaciones if operaciones > 0 else 0
            
            # MOSTRAR MÉTRICAS
            c1, c2, c3 = st.columns(3)
            c1.metric("TOTAL FACTURADO", f"${total_facturado:,.2f}")
            c2.metric("OPERACIONES", f"{operaciones:,}")
            c3.metric("TICKET PROMEDIO", f"${ticket_promedio:,.2f}")
            
            # RESUMEN PARA LA IA
            # Agrupamos por Razón Social para darle datos masticados
            top_clientes = df.groupby('Razón social')['Venta_Numerica'].sum().nlargest(5) if 'Razón social' in df.columns else "No disponible"
            
            st.write("---")
            pregunta = st.text_input("¿Qué querés saber sobre estos datos?")
            
            if pregunta:
                modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(modelos[0])
                
                prompt = f"""
                Actuá como analista de ventas. 
                DATOS REALES: Total: {total_facturado}, Operaciones: {operaciones}, Clientes Top: {top_clientes}.
                Pregunta: {pregunta}
                Responde basándote en estos números. Si el total es {total_facturado}, usalo.
                """
                with st.spinner('Analizando...'):
                    response = model.generate_content(prompt)
                    st.info(response.text)
        else:
            st.error("No encontré la columna 'Venta'.")
            
        st.dataframe(df.head(10))
                
    except Exception as e:
        st.error(f"Error: {e}")
