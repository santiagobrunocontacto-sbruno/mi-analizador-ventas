import streamlit as st
import pandas as pd
import google.generativeai as genai
import traceback

# 1. Configuración de arranque
st.set_page_config(page_title="Auditor Pro", layout="wide")
st.title("📊 Auditoría Comercial Inteligente")

with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input("Ingresá tu API Key:", type="password")
    uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv"])

if api_key and uploaded_file:
    try:
        genai.configure(api_key=api_key)
        
        # 2. Lectura ultra-robusta
        # Intentamos detectar el formato automáticamente
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        # Limpiamos nombres de columnas (quitamos espacios y pasamos a minúsculas para el código)
        df.columns = df.columns.str.strip()
        columnas_originales = list(df.columns)
        
        # Buscamos las columnas sin importar mayúsculas o acentos
        def encontrar_columna(lista, objetivo):
            for c in lista:
                if objetivo.lower() in c.lower(): return c
            return None

        col_venta = encontrar_columna(columnas_originales, 'Venta')
        col_marca = encontrar_columna(columnas_originales, 'Marca')
        col_vendedor = encontrar_columna(columnas_originales, 'Vendedor')
        col_cat = encontrar_columna(columnas_originales, 'Categoria')
        col_fecha = encontrar_columna(columnas_originales, 'Fecha')
        col_cliente = encontrar_columna(columnas_originales, 'Razón social')

        if col_venta:
            # 3. Procesamiento de datos
            df['Venta_Num'] = pd.to_numeric(df[col_venta], errors='coerce').fillna(0)
            total_facturado = df['Venta_Num'].sum()
            
            # Pre-cálculos para la IA
            res_marcas = df.groupby(col_marca)['Venta_Num'].sum().nlargest(15).to_dict() if col_marca else {}
            res_vend = df.groupby(col_vendedor)['Venta_Num'].sum().nlargest(15).to_dict() if col_vendedor else {}
            res_cat = df.groupby(col_cat)['Venta_Num'].sum().nlargest(15).to_dict() if col_cat else {}
            res_cli = df.groupby(col_cliente)['Venta_Num'].sum().nlargest(15).to_dict() if col_cliente else {}

            # 4. Interfaz de Usuario
            t1, t2 = st.tabs(["📉 Tablero de Control", "🤖 Consultor IA"])
            
            with t1:
                st.subheader("Métricas Principales")
                c1, c2, c3 = st.columns(3)
                c1.metric("FACTURACIÓN TOTAL", f"${total_facturado:,.2f}")
                c2.metric("OPERACIONES", f"{len(df):,}")
                c3.metric("TICKET PROMEDIO", f"${(total_facturado/len(df)) if len(df)>0 else 0:,.2f}")
                
                if col_marca:
                    st.write("### Ventas por Marca")
                    st.bar_chart(pd.Series(res_marcas))

            with t2:
                st.write("### 💬 Consultas Gerenciales")
                pregunta = st.text_input("Ejemplo: ¿Cuál es el podio de marcas y quién es el mejor vendedor?")
                
                if pregunta:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    contexto = f"""
                    Datos resumidos de la empresa:
                    - Total Facturado: {total_facturado}
                    - Top Marcas: {res_marcas}
                    - Top Vendedores: {res_vend}
                    - Top Categorías: {res_cat}
                    - Top Clientes: {res_cli}
                    
                    Pregunta: {pregunta}
                    Responde como un analista de negocios, de forma breve y con datos precisos.
                    """
                    
                    with st.spinner("Analizando..."):
                        response = model.generate_content(contexto)
                        st.info(response.text)
        else:
            st.error(f"No encontré la columna 'Venta'. Las columnas detectadas son: {columnas_originales}")

    except Exception as e:
        # SISTEMA DE DIAGNÓSTICO: Si falla, nos dice por qué
        st.error("🚨 Se detectó un error en el procesamiento:")
        st.code(traceback.format_exc())
        st.warning("Enviame una captura de este código de error para que lo solucione.")

else:
    st.info("👋 Hola Santiago. Cargá tu API Key y el archivo para empezar.")
