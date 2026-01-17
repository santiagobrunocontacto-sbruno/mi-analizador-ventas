import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# CONFIGURACIÓN
st.set_page_config(page_title="Informe Gerencial de Ventas", layout="wide")
sns.set_theme(style="whitegrid")

def limpieza_contable(serie):
    """Convierte strings con formato '1.234.567,89' a float puro"""
    s = serie.astype(str).str.strip()
    # Si el número tiene puntos de miles y coma decimal, limpiamos:
    s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    return pd.to_numeric(s, errors='coerce').fillna(0)

@st.cache_data
def cargar_y_limpiar(file):
    df = pd.read_csv(file, sep=';', encoding='latin-1')
    df.columns = df.columns.str.strip()
    
    # Limpieza de valores según formato Argentina
    df['Venta_N'] = limpieza_contable(df['Venta'])
    df['Costo_N'] = limpieza_contable(df['Costo Total'])
    
    # Limpieza de nombres de marcas para evitar el error de $0
    df['Marca_Clean'] = df['Marca'].astype(str).str.upper().str.strip()
    
    # Fechas
    df['Fecha_DT'] = pd.to_datetime(df['Fecha de emisión'], dayfirst=True, errors='coerce')
    df['Mes'] = df['Fecha_DT'].dt.to_period('M').astype(str)
    return df

# --- INTERFAZ ---
st.title("🏛️ Auditoría Comercial de Precisión")
archivo = st.file_uploader("Cargar fac limpia.csv", type=["csv"])

if archivo:
    df = cargar_y_limpiar(archivo)
    
    # ==========================================
    # 1. KPIs SUPERIORES (Cálculo Manual Auditado)
    # ==========================================
    st.header("1. Resumen Ejecutivo")
    
    vta_total = df['Venta_N'].sum()
    cst_total = df['Costo_N'].sum()
    
    # La fórmula que me pediste: (V-C)/V
    if vta_total > 0:
        margen_final = ((vta_total - cst_total) / vta_total) * 100
    else:
        margen_final = 0

    cant_clientes = df['Razón social'].nunique()

    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL FACTURADO", f"${vta_total:,.0f}")
    c2.metric("MARGEN RTA % (Auditado)", f"{margen_final:.1f}%")
    c3.metric("CLIENTES ÚNICOS", f"{cant_clientes:,}")

    st.divider()

    # ==========================================
    # 2. TOTALES POR MARCA (Búsqueda Flexible)
    # ==========================================
    st.subheader("📊 Facturación por Marca Foco")
    
    # Usamos nombres normalizados para que no den $0
    marcas_busqueda = {
        'SMART TEK': 'SMART TEK', 
        'X-VIEW': 'X-VIEW', 
        'TABLETS': 'TABLET', # Agregamos variantes por si acaso
        'CLOUDBOOK': 'CLOUDBOOK', 
        'LEVEL-UP': 'LEVEL', 
        'MICROCASE': 'MICROCASE', 
        'TERRA': 'TERRA'
    }
    
    # Filtro inteligente: busca si la palabra está contenida en la marca
    vta_marcas = {}
    for nombre_lindo, busqueda in marcas_busqueda.items():
        suma = df[df['Marca_Clean'].str.contains(busqueda, na=False)]['Venta_N'].sum()
        vta_marcas[nombre_lindo] = suma

    # Mostrar en columnas
    cols_m = st.columns(len(vta_marcas))
    for i, (m, v) in enumerate(vta_marcas.items()):
        cols_m[i].markdown(f"**{m}**")
        cols_m[i].markdown(f"${v:,.0f}")

    # Gráfico corregido (Sin notación científica)
    fig_m, ax_m = plt.subplots(figsize=(10, 4))
    nombres = list(vta_marcas.keys())
    valores = list(vta_marcas.values())
    ax_m.bar(nombres, valores, color='#004c6d')
    ax_m.ticklabel_format(style='plain', axis='y') # Fuera el 1e9
    plt.xticks(rotation=45)
    st.pyplot(fig_m)

    st.divider()

    # ==========================================
    # 3. PERFORMANCE VENDEDORES (Recuperado)
    # ==========================================
    st.header("2. Performance por Vendedor")
    vendedores = df['Nombre Vendedor'].unique()
    meses_ord = sorted(df['Mes'].unique())

    for vend in vendedores:
        with st.expander(f"Ver evolución de {vend}"):
            df_v = df[df['Nombre Vendedor'] == vend]
            v_mes = df_v.groupby('Mes')['Venta_N'].sum().reindex(meses_ord, fill_value=0)
            
            fig_v, ax_v = plt.subplots(figsize=(10, 2))
            ax_v.plot(v_mes.index, v_mes.values, marker='o', color='green')
            ax_v.ticklabel_format(style='plain', axis='y')
            st.pyplot(fig_v)
            st.write(f"Venta Total del Vendedor: ${df_v['Venta_N'].sum():,.0f}")

else:
    st.info("Subí el archivo para recalcular con la nueva lógica.")
