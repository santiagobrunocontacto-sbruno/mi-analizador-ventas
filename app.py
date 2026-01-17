import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Dashboard de Decisión Comercial", layout="wide")

def limpiar_dinero(serie):
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)

@st.cache_data
def cargar_datos(file):
    df = pd.read_csv(file, sep=';', encoding='latin-1')
    df.columns = df.columns.str.strip()
    df['Venta_N'] = limpiar_dinero(df['Venta'])
    df['RTA_N'] = limpiar_dinero(df['RTA'])
    df['Cantidad_N'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
    df['Fecha_DT'] = pd.to_datetime(df['Fecha de emisión'], dayfirst=True, errors='coerce')
    df['Mes_Periodo'] = df['Fecha_DT'].dt.to_period('M')
    return df

# --- INTERFAZ ---
st.title("📈 Business Intelligence: Gestión de Equipos y Productos")

archivo = st.file_uploader("Cargar fac limpia.csv", type=["csv"])

if archivo:
    df_base = cargar_datos(archivo)
    
    # --- FILTROS LATERALES (La magia del filtrado) ---
    with st.sidebar:
        st.header("🎯 Filtros de Decisión")
        marcas_sel = st.multiselect("Filtrar por Marca", options=df_base['Marca'].unique())
        cat_sel = st.multiselect("Filtrar por Categoría", options=df_base['Categoria'].unique())
        vend_sel = st.multiselect("Filtrar por Vendedor", options=df_base['Nombre Vendedor'].unique())

    # Aplicar filtros
    df = df_base.copy()
    if marcas_sel: df = df[df['Marca'].isin(marcas_sel)]
    if cat_sel: df = df[df['Categoria'].isin(cat_sel)]
    if vend_sel: df = df[df['Nombre Vendedor'].isin(vend_sel)]

    # --- SECCIÓN 1: PERFORMANCE DEL EQUIPO ---
    st.header("👥 Performance del Equipo Comercial")
    
    # Pivot de Ventas por Vendedor y Mes
    perf_vend = df.pivot_table(index='Nombre Vendedor', columns='Mes_Periodo', values='Venta_N', aggfunc='sum').fillna(0)
    
    # Cálculo de Crecimiento MoM
    if len(perf_vend.columns) > 1:
        ultimo_mes = perf_vend.columns[-1]
        mes_anterior = perf_vend.columns[-2]
        perf_vend['Crecimiento %'] = ((perf_vend[ultimo_mes] - perf_vend[mes_anterior]) / perf_vend[mes_anterior] * 100).fillna(0)
    
    st.subheader("Crecimiento vs Mes Anterior")
    st.dataframe(perf_vend.style.highlight_max(axis=0, color='#90EE90').highlight_min(axis=0, color='#FFCCCB'))

    # --- SECCIÓN 2: CATEGORÍAS Y RENTABILIDAD ---
    st.divider()
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.subheader("📦 Categoría más vendida (Unidades)")
        cat_unidades = df.groupby(['Mes_Periodo', 'Categoria'])['Cantidad_N'].sum().reset_index()
        idx = cat_unidades.groupby(['Mes_Periodo'])['Cantidad_N'].transform(max) == cat_unidades['Cantidad_N']
        st.table(cat_unidades[idx].tail(6))

    with col_c2:
        st.subheader("💰 Ticket Promedio por Categoría")
        ticket_cat = df.groupby('Categoria').apply(lambda x: x['Venta_N'].sum() / len(x)).sort_values(ascending=False)
        st.bar_chart(ticket_cat)

    # --- SECCIÓN 3: PRODUCTOS CRÍTICOS (Márgenes) ---
    st.divider()
    st.subheader("⚠️ Auditoría de Productos (Rentabilidad)")
    col_p1, col_p2 = st.columns(2)
    
    # Agrupar por descripción para ver rentabilidad real
    prod_rta = df.groupby('Descripción').agg({'Venta_N':'sum', 'RTA_N':'sum'})
    prod_rta['Margen_%'] = (prod_rta['RTA_N'] / prod_rta['Venta_N'] * 100).fillna(0)
    
    with col_p1:
        st.write("Top 5 Mayor Margen")
        st.table(prod_rta[prod_rta['Venta_N'] > 1000].nlargest(5, 'Margen_%'))
    
    with col_p2:
        st.write("Top 5 Menor Margen (Ojo acá)")
        st.table(prod_rta[prod_rta['Venta_N'] > 1000].nsmallest(5, 'Margen_%'))

    # --- SECCIÓN 4: ALERTA DE CLIENTES (CHURN) ---
    st.divider()
    st.header("🚨 Alerta de Clientes Perdidos")
    st.info("Clientes que compraron en el pasado pero no registran actividad en los últimos 60 días.")
    
    fecha_max = df_base['Fecha_DT'].max()
    clientes_last = df_base.groupby('Razón social')['Fecha_DT'].max().reset_index()
    clientes_last['Dias_Sin_Comprar'] = (fecha_max - clientes_last['Fecha_DT']).dt.days
    perdidos = clientes_last[clientes_last['Dias_Sin_Comprar'] > 60].sort_values('Dias_Sin_Comprar', ascending=False)
    
    st.dataframe(perdidos, use_container_width=True)

else:
    st.info("Cargá el archivo para activar la inteligencia comercial.")
