import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Analizador de Ventas", layout="wide")
st.title("📊 Panel de Control de Ventas")

# 2. ENTRADA DE DATOS
with st.sidebar:
    api_key = st.text_input("Ingresá tu Google API Key:", type="password")
    uploaded_file = st.file_uploader("Subí tu archivo fac limpia.csv", type=["csv"])

if api_key and uploaded_file:
    try:
        genai.configure(api_key=api_key)
        
        # 3. LECTURA DEL ARCHIVO (Separador punto y coma según tu archivo)
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        # 4. LIMPIEZA DE COLUMNAS (Para que no falle por espacios)
        df.columns = df.columns.str.strip()
        
        if 'Venta' in df.columns:
            # Convertimos a números
            df['Venta_Num'] = pd.to_numeric(df['Venta'], errors='coerce').fillna(0)
            
            # Métricas rápidas
            total_facturado = df['Venta_Num'].sum()
            st.metric("TOTAL FACTURADO", f"${total_facturado:,.2f}")
            
            # --- PREPARACIÓN DE DATOS PARA LA IA ---
            # Creamos los resúmenes que pediste (Marcas y Categorías)
            resumen_marcas = df.groupby('Marca')['Venta_Num'].sum().nlargest(10).to_dict() if 'Marca' in df.columns else {}
            resumen_cats = df.groupby('Categoria')['Venta_Num'].sum().nlargest(10).to_dict() if 'Categoria' in df.columns else {}
            
            st.write("---")
            pregunta = st.text_input("¿Qué querés saber? (Ej: Ventas por marca)")
            
            if pregunta:
                # Inicializar IA
                modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(modelos[0])
                
                # Le damos los datos ya masticados a la IA
                prompt = f"""
                Sos un experto contable. Usá estos datos del archivo para responder:
                - Total General: {total_facturado}
                - Ranking de Marcas: {resumen_marcas}
                - Ranking de Categorías: {resumen_cats}
                
                Pregunta del usuario: {pregunta}
                
                Instrucción: Da la respuesta directa basada en los números. No inventes datos.
                """
                with st.spinner('Analizando...'):
                    response = model.generate_content(prompt)
                    st.success(response.text)

            # Gráfico visual para que no dependas solo de la IA
            if 'Marca' in df.columns:
                st.write("### Top 10 Marcas (Visual)")
                st.bar_chart(df.groupby('Marca')['Venta_Num'].sum().nlargest(10))
        
        else:
            st.error("No encontré la columna 'Venta'. Revisá el archivo.")

    except Exception as e:
        st.error(f"Ocurrió un error: {e}")
else:
    st.info("💡 Pegá tu API Key y subí el archivo CSV para activar el sistema.")
