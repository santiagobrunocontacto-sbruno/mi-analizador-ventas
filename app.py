import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gerencia Comercial AI", layout="wide", initial_sidebar_state="expanded")

# --- ESTILOS CSS PARA QUE SE VEA PROFESIONAL ---
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #4CAF50;}
    .big-font {font-size:20px !important;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Tablero de Comando Comercial")
st.markdown("Sistema de Inteligencia de Negocios y Auditoría de Ventas")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("🔐 Acceso y Datos")
    api_key = st.text_input("Google API Key:", type="password")
    uploaded_file = st.file_uploader("Cargar Reporte (CSV)", type=["csv"])
    st.info("Formato soportado: CSV separado por punto y coma (;)")

# --- FUNCIONES DE LÓGICA DE NEGOCIO (EL CEREBRO) ---
@st.cache_data # Esto hace que no recalcule todo si solo cambias de pestaña
def cargar_y_procesar_datos(file):
    try:
        # 1. Detectar separador automáticamente (probamos ; primero que es el tuyo)
        df = pd.read_csv(file, sep=None, engine='python', encoding='latin-1')
        
        # 2. Normalizar nombres de columnas (quitar espacios extra)
        df.columns = df.columns.str.strip()
        
        # 3. Validar columnas críticas
        if 'Venta' not in df.columns:
            return None, "Error: No se encontró la columna 'Venta'."
        
        # 4. Limpieza de Números (Manejo de tu formato específico)
        # Tu archivo tiene enteros o floats estándar. Forzamos conversión.
        df['Venta_Real'] = pd.to_numeric(df['Venta'], errors='coerce').fillna(0)
        
        # 5. Limpieza de Fechas
        col_fecha = next((c for c in df.columns if 'fecha' in c.lower()), None)
        if col_fecha:
            df['Fecha_DT'] = pd.to_datetime(df[col_fecha], dayfirst=True, errors='coerce')
            df['Mes_Año'] = df['Fecha_DT'].dt.strftime('%Y-%m')
        else:
            df['Mes_Año'] = "Sin Fecha"

        return df, None
    except Exception as e:
        return None, f"Error crítico al leer archivo: {str(e)}"

def generar_resumen_gerencial(df):
    """Calcula todos los KPIs posibles para alimentar a la IA"""
    stats = {}
    
    # KPIs Generales
    stats['total_venta'] = df['Venta_Real'].sum()
    stats['total_ops'] = len(df)
    stats['ticket_promedio'] = stats['total_venta'] / stats['total_ops'] if stats['total_ops'] > 0 else 0
    
    # Rankings (Top 10 de cada dimensión disponible)
    if 'Marca' in df.columns:
        stats['top_marcas'] = df.groupby('Marca')['Venta_Real'].sum().nlargest(10).to_dict()
    
    if 'Categoria' in df.columns:
        stats['top_categorias'] = df.groupby('Categoria')['Venta_Real'].sum().nlargest(10).to_dict()
        
    if 'Nombre Vendedor' in df.columns:
        stats['top_vendedores'] = df.groupby('Nombre Vendedor')['Venta_Real'].sum().nlargest(10).to_dict()
        
    if 'Razón social' in df.columns:
        stats['top_clientes'] = df.groupby('Razón social')['Venta_Real'].sum().nlargest(10).to_dict()
    
    # Serie de Tiempo
    if 'Mes_Año' in df.columns:
        stats['venta_mensual'] = df.groupby('Mes_Año')['Venta_Real'].sum().to_dict()

    return stats

# --- INTERFAZ PRINCIPAL ---
if api_key and uploaded_file:
    genai.configure(api_key=api_key)
    
    # Procesar archivo
    df, error = cargar_y_procesar_datos(uploaded_file)
    
    if error:
        st.error(error)
    else:
        # Generar "La Verdad" (Todos los números calculados)
        kpis = generar_resumen_gerencial(df)
        
        # TABS PARA ORGANIZAR LA VISTA
        tab1, tab2, tab3 = st.tabs(["📈 Tablero Visual", "🤖 Consultor IA", "📋 Datos Crudos"])
        
        with tab1:
            # Métricas grandes
            c1, c2, c3 = st.columns(3)
            c1.metric("Facturación Total", f"${kpis['total_venta']:,.2f}")
            c2.metric("Operaciones", f"{kpis['total_ops']:,}")
            c3.metric("Ticket Promedio", f"${kpis['ticket_promedio']:,.2f}")
            
            st.markdown("---")
            
            # Gráficos Automáticos
            col_graph1, col_graph2 = st.columns(2)
            
            with col_graph1:
                if 'top_marcas' in kpis:
                    st.subheader("Top Marcas")
                    # Convertimos el dict a DataFrame para graficar fácil
                    df_marcas = pd.DataFrame(list(kpis['top_marcas'].items()), columns=['Marca', 'Venta'])
                    fig = px.bar(df_marcas, x='Marca', y='Venta', color='Venta')
                    st.plotly_chart(fig, use_container_width=True)
            
            with col_graph2:
                if 'venta_mensual' in kpis:
                    st.subheader("Evolución Mensual")
                    df_mes = pd.DataFrame(list(kpis['venta_mensual'].items()), columns=['Mes', 'Venta'])
                    # Ordenar cronológicamente si es posible
                    df_mes = df_mes.sort_values('Mes')
                    fig2 = px.line(df_mes, x='Mes', y='Venta', markers=True)
                    st.plotly_chart(fig2, use_container_width=True)

        with tab2:
            st.subheader("💬 Preguntale al Gerente Virtual")
            st.info("Este asistente tiene acceso a todos los KPIs calculados. Preguntá con confianza.")
            
            pregunta = st.chat_input("Ej: ¿Quién es el mejor vendedor? ¿Qué marca cayó este mes?")
            
            if pregunta:
                # Mostramos la pregunta
                with st.chat_message("user"):
                    st.write(pregunta)
                
                # Preparamos el Prompt con LOS DATOS YA CALCULADOS (Infalible)
                prompt_sistema = f"""
                Actúas como un Gerente General analítico y preciso.
                Tienes acceso a los siguientes DATOS REALES Y VERIFICADOS de la empresa:
                
                - Total Facturado: ${kpis['total_venta']:,.2f}
                - Cantidad Tickets: {kpis['total_ops']}
                - Ticket Promedio: ${kpis['ticket_promedio']:,.2f}
                
                - Ranking Marcas (Top 10): {kpis.get('top_marcas', 'No disponible')}
                - Ranking Categorías: {kpis.get('top_categorias', 'No disponible')}
                - Ranking Vendedores: {kpis.get('top_vendedores', 'No disponible')}
                - Ranking Clientes: {kpis.get('top_clientes', 'No disponible')}
                - Ventas por Mes: {kpis.get('venta_mensual', 'No disponible')}
                
                PREGUNTA DEL USUARIO: "{pregunta}"
                
                INSTRUCCIONES:
                1. Usa SOLO los datos de arriba. No inventes.
                2. Si la respuesta está en los datos, dala directamente.
                3. Sé breve y ejecutivo. Usa negritas para los números importantes.
                4. Si preguntan algo que no está en los datos (ej: margen de ganancia si no hay columna de costo), aclara que no tenés esa info.
                """
                
                with st.chat_message("assistant"):
                    with st.spinner("Analizando tablero de comando..."):
                        try:
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            response = model.generate_content(prompt_sistema)
                            st.write(response.text)
                        except Exception as e:
                            st.error(f"Error de conexión con IA: {e}")

        with tab3:
            st.dataframe(df)

else:
    # Pantalla de bienvenida
    st.markdown("""
    ### 👋 Bienvenido al Sistema de Gestión Comercial
    Para comenzar:
    1. Ingresá tu **API Key** en el menú izquierdo.
    2. Subí tu archivo **CSV** (probado con `fac limpia.csv`).
    
    El sistema calculará automáticamente todos los indicadores clave.
    """)
