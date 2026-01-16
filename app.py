import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="Consultor de Ventas", layout="wide")
st.title("📊 Mi Analizador de Datos")

with st.sidebar:
    api_key = st.text_input("Ingresá tu Google API Key:", type="password")
    uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv"])

if api_key and uploaded_file:
    try:
        genai.configure(api_key=api_key)
        
        # Detector de modelo automático para evitar el 404
        modelos_visibles = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos_visibles else modelos_visibles[0]
        model = genai.GenerativeModel(model_name)
        
        # Leer el archivo completo
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        # --- LÓGICA DE CÁLCULO MATEMÁTICO ---
        total_calculado = 0
        if 'Venta' in df.columns:
            # Limpieza: Convertimos a texto, quitamos puntos de miles y cambiamos coma por punto decimal
            serie_limpia = df['Venta'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Venta_Numerica'] = pd.to_numeric(serie_limpia, errors='coerce').fillna(0)
            total_calculado = df['Venta_Numerica'].sum()
            st.success(f"📈 Total Facturado calculado por el sistema: ${total_calculado:,.2f}")
        
        st.write("### Vista previa de los datos")
        st.dataframe(df.head())

        pregunta = st.text_input("¿Qué querés saber sobre tus ventas?")
        
        if pregunta:
            # Le pasamos el resultado matemático a la IA para que no tenga que calcular ella
            prompt = f"""
            Actuá como un experto contable. 
            El usuario te pasa un archivo con {len(df)} registros.
            El TOTAL calculado matemáticamente de la columna 'Venta' es: {total_calculado}.
            Las columnas disponibles son: {list(df.columns)}.
            
            Pregunta del usuario: {pregunta}
            
            Instrucción: No digas cómo hacerlo, DA EL RESULTADO directamente usando el total que te acabo de dar. Si te pregunta por el total, usá el número {total_calculado}.
            """
            with st.spinner('Analizando...'):
                response = model.generate_content(prompt)
                st.info(response.text)
                    
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("💡 Pegá tu API Key y subí el archivo.")
