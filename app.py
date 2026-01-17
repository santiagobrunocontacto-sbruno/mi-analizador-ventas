import streamlit as st
import pandas as pd
import google.generativeai as genai

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gerencia Comercial AI", layout="wide")
st.title("📊 Tablero de Comando & Consultor")

# BARRA LATERAL
with st.sidebar:
    api_key = st.text_input("API Key de Google:", type="password")
    uploaded_file = st.file_uploader("Subí tu archivo CSV", type=["csv"])

# LÓGICA PRINCIPAL
if api_key and uploaded_file:
    try:
        genai.configure(api_key=api_key)
        
        # 1. CARGA DE DATOS (Detectando separador y limpiando)
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        df.columns = df.columns.str.strip() # Limpiar espacios en nombres de columnas
        
        if 'Venta' in df.columns:
            # 2. PROCESAMIENTO MATEMÁTICO (La base sólida)
            df['Venta_Real'] = pd.to_numeric(df['Venta'], errors='coerce').fillna(0)
            
            # Procesar Fechas
            if 'Fecha de emisión' in df.columns:
                df['Fecha_DT'] = pd.to_datetime(df['Fecha de emisión'], dayfirst=True, errors='coerce')
                df['Mes'] = df['Fecha_DT'].dt.strftime('%Y-%m')
            
            # 3. CÁLCULO DE TODOS LOS RANKINGS (El "Cerebro Comercial")
            # Aquí preparamos los datos para que la IA sepa DE TODO
            
            total_facturado = df['Venta_Real'].sum()
            
            # Ranking VENDEDORES (Top 20 para tener buen contexto)
            ranking_vendedores = {}
            if 'Nombre Vendedor' in df.columns:
                ranking_vendedores = df.groupby('Nombre Vendedor')['Venta_Real'].sum().nlargest(20).to_dict()
            
            # Ranking CLIENTES (Top 20)
            ranking_clientes = {}
            if 'Razón social' in df.columns:
                ranking_clientes = df.groupby('Razón social')['Venta_Real'].sum().nlargest(20).to_dict()

            # Ranking MARCAS
            ranking_marcas = {}
            if 'Marca' in df.columns:
                ranking_marcas = df.groupby('Marca')['Venta_Real'].sum().nlargest(20).to_dict()

            # Evolución MENSUAL
            ventas_mensuales = {}
            if 'Mes' in df.columns:
                ventas_mensuales = df.groupby('Mes')['Venta_Real'].sum().to_dict()

            # --- INTERFAZ VISUAL ---
            
            # Pestañas para organizar
            tab1, tab2 = st.tabs(["📈 Tablero", "💬 Chat con Gerente IA"])
            
            with tab1:
                # Métricas Clave
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Facturado", f"${total_facturado:,.2f}")
                col2.metric("Operaciones", f"{len(df):,}")
                col3.metric("Ticket Promedio", f"${total_facturado/len(df):,.2f}")
                
                st.markdown("---")
                
                # Gráficos de apoyo
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("Top Vendedores")
                    if ranking_vendedores:
                        st.bar_chart(pd.Series(ranking_vendedores))
                with c2:
                    st.subheader("Evolución Mensual")
                    if ventas_mensuales:
                        st.line_chart(pd.Series(ventas_mensuales))

            with tab2:
                st.header("Consultor de Negocios Inteligente")
                st.info("Ahora la IA conoce a tus vendedores, clientes y marcas principales.")
                
                pregunta = st.text_input("Hacé tu pregunta (Ej: ¿Quién es el mejor vendedor? ¿Qué cliente compró más?)")
                
                if pregunta:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # EL SECRETO: Le pasamos TODO el contexto calculado
                    prompt_contexto = f"""
                    Actuá como un Gerente Comercial experto. Responde basándote EXCLUSIVAMENTE en estos datos procesados:

                    1. FACTURACIÓN TOTAL: ${total_facturado:,.2f}
                    
                    2. EVOLUCIÓN MENSUAL (Mes: Venta):
                    {ventas_mensuales}

                    3. TOP VENDEDORES (Nombre: Venta):
                    {ranking_vendedores}

                    4. TOP CLIENTES (Razón Social: Venta):
                    {ranking_clientes}

                    5. TOP MARCAS (Marca: Venta):
                    {ranking_marcas}

                    PREGUNTA DEL USUARIO: {pregunta}

                    INSTRUCCIONES:
                    - Si la respuesta está en los datos de arriba, sé preciso y da el número.
                    - Si te preguntan por un vendedor o cliente que NO está en el Top 20, aclará: "No figura en el Top 20 de mayores ventas".
                    - Responde de forma profesional y ejecutiva.
                    """
                    
                    with st.spinner("Analizando la base de datos..."):
                        response = model.generate_content(prompt_contexto)
                        st.markdown(response.text)

        else:
            st.error("Error: No se encontró la columna 'Venta'. Verificá el archivo.")

    except Exception as e:
        st.error(f"Error técnico: {e}")
else:
    st.info("Por favor, ingresá la API Key y cargá el archivo.")
