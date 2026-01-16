import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="Auditor de Ventas", layout="wide")
st.title("🚀 Mi Auditor de Datos")

with st.sidebar:
    api_key = st.text_input("Ingresá tu Google API Key:", type="password")
    uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv"])

if api_key and uploaded_file:
    try:
        genai.configure(api_key=api_key)
        
        # Leemos el archivo
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        # --- PROCESAMIENTO MATEMÁTICO REAL ---
        # Buscamos cualquier columna que se parezca a "Venta"
        col_v = [c for c in df.columns if 'venta' in c.lower()]
        
        if col_v:
            nombre_col = col_v[0]
            # Limpieza profunda: sacamos espacios, sacamos puntos de miles, cambiamos coma por punto decimal
            valores = df[nombre_col].astype(str).str.strip()
            valores = valores.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Venta_Limpia'] = pd.to_numeric(valores, errors='coerce').fillna(0)
            
            total_real = df['Venta_Limpia'].sum()
            
            # MOSTRAR EL RESULTADO EN UN CARTEL GIGANTE
            st.metric(label=f"TOTAL FACTURADO (Columna: {nombre_col})", value=f"${total_real:,.2f}")
            st.success(f"Se analizaron {len(df)} filas exitosamente.")
        else:
            st.error("No encontré ninguna columna que diga 'Venta'. Revisá los nombres en tu Excel.")

        st.write("### Vista previa de los registros:")
        st.dataframe(df.head(10))

        # --- SECCIÓN DE PREGUNTAS ---
        pregunta = st.text_input("Hacé una pregunta específica (ej: ¿Quién es el cliente que más compró?)")
        
        if pregunta:
            # Seleccionamos el modelo dinámicamente
            modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model = genai.GenerativeModel(modelos[0])
            
            # Mandamos un resumen compacto para no saturar a la IA
            contexto = f"Total Ventas: {total_real}. Filas: {len(df)}. Columnas: {list(df.columns)}"
            with st.spinner('Pensando...'):
                response = model.generate_content(f"{contexto}\n\nPregunta: {pregunta}")
                st.info(response.text)
                
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Esperando API Key y archivo CSV...")
