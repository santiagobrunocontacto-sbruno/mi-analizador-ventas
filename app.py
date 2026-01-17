import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF

# CONFIGURACIÓN
st.set_page_config(page_title="Tablero Gerencial", layout="wide")
sns.set_theme(style="whitegrid")

def limpiar_moneda(serie):
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)

@st.cache_data
def cargar_datos(file):
    df = pd.read_csv(file, sep=';', encoding='latin-1')
    df.columns = df.columns.str.strip()
    df['Venta_N'] = limpiar_moneda(df['Venta'])
    df['Costo_N'] = limpiar_moneda(df['Costo Total'])
    df['Cantidad_N'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
    df['Fecha_DT'] = pd.to_datetime(df['Fecha de emisión'], dayfirst=True, errors='coerce')
    df['Mes'] = df['Fecha_DT'].dt.to_period('M').astype(str)
    return df

# --- INTERFAZ ---
st.title("🏛️ Informe de Gestión Comercial")
archivo = st.file_uploader("Cargar fac limpia.csv", type=["csv"])

if archivo:
    df = cargar_datos(archivo)
    
    # ==========================================
    # 1. BLOQUE DE KPIs SUPERIORES
    # ==========================================
    st.header("1. Resumen Ejecutivo")
    
    # Cálculos
    total_vta = df['Venta_N'].sum()
    costo_vta = df['Costo_N'].sum()
    margen_valor = ((total_vta - costo_vta) / total_vta * 100) if total_vta != 0 else 0
    cant_clientes = df['Razón social'].nunique()

    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL FACTURADO", f"${total_vta:,.0f}")
    c2.metric("MARGEN RTA %", f"{margen_valor:.1f}%")
    c3.metric("CLIENTES ÚNICOS", f"{cant_clientes:,}")

    st.divider()

    # ==========================================
    # 2. TOTALES POR MARCA (Tus 7 marcas foco)
    # ==========================================
    st.subheader("📊 Facturación por Marca Foco")
    marcas_foco = ['SMART TEK', 'X-VIEW', 'TABLETS', 'CLOUDBOOK', 'LEVEL-UP', 'MICROCASE', 'TERRA']
    
    # Filtramos y sumamos
    df_foco = df[df['Marca'].str.upper().isin(marcas_foco)]
    vta_marcas = df_foco.groupby('Marca')['Venta_N'].sum().reindex(marcas_foco).fillna(0)
    
    # Mostrar como etiquetas bonitas o tabla
    cols_m = st.columns(len(marcas_foco))
    for i, marca in enumerate(marcas_foco):
        cols_m[i].write(f"**{marca}**")
        cols_m[i].write(f"${vta_marcas[marca]:,.0f}")

    # Gráfico de marcas sin notación científica
    fig_m, ax_m = plt.subplots(figsize=(10, 3))
    vta_marcas.plot(kind='bar', color='#1f77b4', ax=ax_m)
    ax_m.ticklabel_format(style='plain', axis='y') # Quita el 1e9
    plt.xticks(rotation=45)
    st.pyplot(fig_m)

    st.divider()

    # ==========================================
    # 3. PERFORMANCE VENDEDORES (Recuperado)
    # ==========================================
    st.header("2. Performance por Vendedor")
    meses_ord = sorted(df['Mes'].unique())
    
    vendedores = df['Nombre Vendedor'].unique()
    for v in vendedores:
        with st.expander(f"Análisis Detallado: {v}"):
            df_v = df[df['Nombre Vendedor'] == v]
            v_por_mes = df_v.groupby('Mes')['Venta_N'].sum().reindex(meses_ord, fill_value=0)
            
            col_v1, col_v2 = st.columns([2, 1])
            with col_v1:
                fig_v, ax_v = plt.subplots(figsize=(8, 2))
                sns.line_chart = sns.barplot(x=v_por_mes.index, y=v_por_mes.values, ax=ax_v, palette="Blues_d")
                ax_v.ticklabel_format(style='plain', axis='y')
                st.pyplot(fig_v)
            with col_v2:
                v_total_v = df_v['Venta_N'].sum()
                st.write(f"**Acumulado:** ${v_total_v:,.0f}")
                if len(v_por_mes) > 1:
                    crec = (v_por_mes.iloc[-1] / v_por_mes.iloc[-2] - 1) * 100 if v_por_mes.iloc[-2] != 0 else 0
                    st.write(f"**Crec. Mes Ant:** {crec:.1f}%")

    # ==========================================
    # 4. CATEGORÍAS (Recuperado)
    # ==========================================
    st.header("3. Inteligencia de Categorías")
    cat_vta = df.groupby('Categoria')['Venta_N'].sum().nlargest(10)
    st
