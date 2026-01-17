import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import tempfile

# CONFIGURACIÓN
st.set_page_config(page_title="Informe Gerencial de Ventas", layout="wide")
sns.set_theme(style="whitegrid")

def limpiar_moneda(serie):
    # Limpieza robusta para formatos argentinos (puntos de miles y coma decimal)
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)

@st.cache_data
def cargar_y_procesar(file):
    df = pd.read_csv(file, sep=';', encoding='latin-1')
    df.columns = df.columns.str.strip()
    
    # Procesamiento de columnas numéricas
    df['Venta_N'] = limpiar_moneda(df['Venta'])
    df['Costo_N'] = limpiar_moneda(df['Costo Total'])
    df['RTA_N'] = limpiar_moneda(df['RTA'])
    
    # Procesamiento de fechas
    df['Fecha_DT'] = pd.to_datetime(df['Fecha de emisión'], dayfirst=True, errors='coerce')
    df['Mes'] = df['Fecha_DT'].dt.to_period('M').astype(str)
    
    return df

# --- INTERFAZ ---
st.title("🏛️ Auditoría Comercial de Precisión")
archivo = st.file_uploader("Cargar fac limpia.csv", type=["csv"])

if archivo:
    df = cargar_y_procesar(archivo)
    
    # ==========================================
    # 1. CÁLCULOS DEL RESUMEN EJECUTIVO
    # ==========================================
    
    # A. Total Facturado General
    total_facturado = df['Venta_N'].sum()
    
    # B. Facturado por Marcas Específicas
    marcas_objetivo = ['SMART TEK', 'X-VIEW', 'TABLETS', 'CLOUDBOOK', 'LEVEL-UP', 'MICROCASE', 'TERRA']
    df_marcas_filt = df[df['Marca'].str.upper().isin(marcas_objetivo)]
    total_marcas_especificas = df_marcas_filt['Venta_N'].sum()
    
    # C. Rentabilidad Promedio (Fórmula Gerencial)
    # (Venta Total - Costo Total) / Venta Total
    venta_neta = df['Venta_N'].sum()
    costo_neto = df['Costo_N'].sum()
    
    if venta_neta > 0:
        margen_real = ((venta_neta - costo_neto) / venta_neta) * 100
    else:
        margen_real = 0
        
    # D. Cantidad de Clientes (Recuento distintivo)
    cant_clientes = df['Razón social'].nunique()

    # ==========================================
    # VISUALIZACIÓN DE KPIs
    # ==========================================
    st.header("1. Resumen Ejecutivo")
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric("TOTAL FACTURADO", f"${total_facturado:,.0f}")
        st.caption("Total general del archivo")

    with c2:
        st.metric("VTA. MARCAS FOCO", f"${total_marcas_especificas:,.0f}")
        st.caption("Solo marcas seleccionadas")

    with c3:
        # Formato: 2 dígitos y 1 decimal (ej: 25.4%)
        st.metric("MARGEN RTA %", f"{margen_real:.1} %")
        st.caption("Fórmula: (Vta-Costo)/Vta")

    with c4:
        st.metric("CLIENTES ÚNICOS", f"{cant_clientes:,}")
        st.caption("Recuento de Razones Sociales")

    st.divider()
    
    # Gráfico simple de apoyo para el Top de Marcas Foco
    st.subheader("Distribución de Venta: Marcas Seleccionadas")
    vta_por_marca = df_marcas_filt.groupby('Marca')['Venta_N'].sum().sort_values(ascending=False)
    
    fig, ax = plt.subplots(figsize=(10, 4))
    vta_por_marca.plot(kind='bar', color='#004c6d', ax=ax)
    plt.ylabel("Venta ($)")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.info("📌 Estos son los KPIs base. Quedo a la espera de los siguientes cambios que mencionaste para seguir expandiendo el reporte.")

else:
    st.info("Subí el archivo para validar los nuevos KPIs.")
