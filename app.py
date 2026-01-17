import streamlit as st
import pandas as pd
import google.generativeai as genai

# CONFIGURACIÓN SIMPLE
st.set_page_config(page_title="Tablero Comercial", layout="wide")
st.title("📊 Tablero de Comando Comercial")

# BARRA LATERAL
with st.sidebar:
    api_key = st.text_input("Tu Google API Key:", type="password")
    uploaded_file = st.file_uploader("Subí el archivo 'fac limpia.csv'", type=["csv"])

# LÓGICA PRINCIPAL
if api_key and uploaded_file:
    try:
        genai.configure(api_key=api_key)
        
        # 1. LEER ARCHIVO (Detectando punto y coma)
        df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
        
        # 2. LIMPIAR COLUMNAS (Quitar espacios invisibles)
        df.columns = df.columns.str.strip()
        
        if 'Venta' in df.columns:
            # 3. LIMPIEZA DE DATOS
            # Forzamos conversión a número, los errores se vuelven 0
            df['Venta_Real'] = pd.to_numeric(df['Venta'], errors='coerce').fillna(0)
            
            # Convertimos fechas si existen
            if 'Fecha de emisión' in df.columns:
                df['Fecha_DT'] = pd.to_datetime(df['Fecha de emisión'], dayfirst=True, errors='coerce')
                df['Mes'] = df['Fecha_DT'].dt.strftime('%Y-%m')

            # 4. CÁLCULO DE KPIS (La "Verdad" matemática)
            total_facturado = df['Venta_Real'].sum()
            cant_operaciones = len(df)
            ticket_promedio = total_facturado / cant_operaciones if cant_operaciones > 0 else 0
            
            # Rankings (Diccionarios para la IA)
            top_marcas = df.groupby('Marca')['Venta_Real'].sum().nlargest(10).to_dict() if 'Marca' in df.columns else {}
            top_categorias = df.groupby('Categoria')['Venta_Real'].sum().nlargest(10).to_dict() if 'Categoria' in df.columns else {}
            ventas_por_mes = df.groupby('Mes')['Venta_Real'].sum().to_dict() if 'Mes' in df.columns else {}

            # 5. MOSTRAR RESULTADOS EN PESTAÑAS
            tab1, tab2 = st.tabs(["📈 Panel Visual", "🤖 Consultor IA"])
            
            with tab1:
                # Métricas Grandes
                col1, col2, col3 = st.columns(3)
                col1.metric("Facturación Total", f"${total_facturado:,.2f}")
                col2.metric("Tickets", f"{cant_operaciones:,}")
                col3.metric("Ticket Promedio", f"${ticket_promedio:,.2f}")
                
                st.write("---")
                
                # Gráficos Nativos (Simples pero no fallan)
                c_graph1, c_graph2 = st.columns(2)
                with c_graph1:
                    if top_marcas:
                        st.subheader("Top 10 Marcas ($)")
                        st.bar_chart(pd.Series(top_marcas))
                
                with c_graph2:
                    if ventas_por_mes:
                        st.subheader("Evolución Mensual ($)")
                        st.line_chart(pd.Series(ventas_por_mes))

            with tab2:
                st.info("Preguntá sobre Marcas, Categorías, Meses o Vendedores.")
                pregunta = st.text_input("Escribí tu consulta aquí:")
                
                if pregunta:
                    # Preparamos al modelo
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Le pasamos los DATOS YA CALCULADOS
                    prompt = f"""
                    Actuá como Gerente Comercial. Usá estos datos VERIFICADOS:
                    
                    - Facturación Total: ${total_facturado:,.2f}
                    - Ranking Marcas: {top_marcas}
                    - Ranking Categorías: {top_categorias}
                    - Evolución Mensual: {ventas_por_mes}
                    
                    Pregunta del usuario: {pregunta}
                    
                    Respondé de forma directa basándote solo en estos números.
                    """
                    
                    with st.spinner("Analizando datos..."):
                        res = model.generate_content(prompt)
                        st.success(res.text)

        else:
            st.error("No encontré la columna 'Venta'. Revisá el archivo.")

    except Exception as e:
        st.error(f"Error técnico: {e}")
else:
    st.info("Esperando API Key y Archivo CSV...")
