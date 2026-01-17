import streamlit as st
import pandas as pd
import google.generativeai as genai
import traceback

st.set_page_config(page_title="Auditor Pro", layout="wide")
st.title("📊 Auditoría Comercial Inteligente")

with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input("Ingresá tu API Key:", type="password")
    uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv"])

if api_key and uploaded_file:
    try:
        genai.configure(api_key=api_key)
        
        # --- NUEVO: DETECTOR AUTOMÁTICO DE MODELO ---
        # Listamos los modelos que tu API Key tiene permitidos
        modelos_disponibles = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Elegimos el mejor disponible: preferimos flash, si no pro, si no el primero que haya
        modelo_a_usar = ""
        for m in modelos_disponibles:
            if "gemini-1.5-flash" in m:
                modelo_a_usar = m
                break
        if not modelo_a_usar:
            for m in modelos_disponibles:
                if "gemini-pro" in m:
                    modelo_a_usar = m
                    break
        if not modelo_a_usar:
            modelo_a_usar = modelos_disponibles[0]
            
        st.sidebar.success(f"Usando modelo: {modelo_a_usar}")

        # --- PROCESAMIENTO DE DATOS ---
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        df.columns = df.columns.str.strip()
        
        def encontrar_columna(lista, objetivo):
            for c in lista:
                if objetivo.lower() in str(c).lower(): return c
            return None

        col_venta = encontrar_columna(df.columns, 'Venta')
        col_marca = encontrar_columna(df.columns, 'Marca')
        col_vendedor = encontrar_columna(df.columns, 'Vendedor')
        col_cliente = encontrar_columna(df.columns, 'Razón social')

        if col_venta:
            df['Venta_Num'] = pd.to_numeric(df[col_venta], errors='coerce').fillna(0)
            total_facturado = df['Venta_Num'].sum()
            
            # Resúmenes para la IA
            res_marcas = df.groupby(col_marca)['Venta_Num'].sum().nlargest(15).to_dict() if col_marca else {}
            res_vend = df.groupby(col_vendedor)['Venta_Num'].sum().nlargest(15).to_dict() if col_vendedor else {}
            res_cli = df.groupby(col_cliente)['Venta_Num'].sum().nlargest(15).to_dict() if col_cliente else {}

            t1, t2 = st.tabs(["📉 Tablero de Control", "🤖 Consultor IA"])
            
            with t1:
                c1, c2, c3 = st.columns(3)
                c1.metric("FACTURACIÓN TOTAL", f"${total_facturado:,.2f}")
                c2.metric("OPERACIONES", f"{len(df):,}")
                c3.metric("TICKET PROMEDIO", f"${(total_facturado/len(df)) if len(df)>0 else 0:,.2f}")
                
                if col_marca:
                    st.write("### Ventas por Marca")
                    st.bar_chart(pd.Series(res_marcas))

            with t2:
                st.write("### 💬 Consultas Gerenciales")
                pregunta = st.text_input("Hacé tu pregunta:")
                
                if pregunta:
                    # Usamos el modelo que detectamos automáticamente arriba
                    model = genai.GenerativeModel(modelo_a_usar)
                    
                    contexto = f"""
                    Datos resumidos:
                    - Total Facturado: {total_facturado}
                    - Top Marcas: {res_marcas}
                    - Top Vendedores: {res_vend}
                    - Top Clientes: {res_cli}
                    
                    Pregunta: {pregunta}
                    Responde de forma ejecutiva y precisa.
                    """
                    
                    with st.spinner("Analizando con la IA..."):
                        response = model.generate_content(contexto)
                        st.info(response.text)
        else:
            st.error("No se encontró la columna 'Venta'.")

    except Exception as e:
        st.error("🚨 Error detectado:")
        st.code(traceback.format_exc())
else:
    st.info("👋 Esperando API Key y archivo...")
