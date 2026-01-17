import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# CONFIGURACIÓN
st.set_page_config(page_title="Tablero Comercial Pro", layout="wide")
sns.set_theme(style="whitegrid")

def limpieza_contable_extrema(serie):
    """Limpia formatos contables complejos y asegura lectura correcta de millones"""
    s = serie.astype(str).str.strip()
    # Eliminamos el símbolo $ y espacios
    s = s.str.replace('$', '', regex=False).str.replace(' ', '', regex=False)
    # Caso crítico: Si hay puntos y comas, el punto es de miles. Lo borramos.
    # Luego la coma la pasamos a punto para que Python entienda el decimal.
    s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    return pd.to_numeric(s, errors='coerce').fillna(0)

@st.cache_data
def cargar_todo(file):
    df = pd.read_csv(file, sep=';', encoding='latin-1')
    df.columns = df.columns.str.strip()
    
    # PROCESAMIENTO NUMÉRICO AUDITADO
    df['Venta_N'] = limpieza_contable_extrema(df['Venta'])
    df['Costo_N'] = limpieza_contable_extrema(df['Costo Total'])
    df['Cantidad_N'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
    
    # NORMALIZACIÓN DE TEXTO
    df['Marca_Clean'] = df['Marca'].astype(str).str.upper().str.strip()
    df['Vendedor_Clean'] = df['Nombre Vendedor'].astype(str).str.upper().str.strip()
    
    return df

# --- INTERFAZ ---
st.title("🚀 Tablero de Comando Comercial")
archivo = st.file_uploader("Cargar fac limpia.csv", type=["csv"])

if archivo:
    df = cargar_todo(archivo)
    
    # ==========================================
    # 1. RESUMEN GENERAL (KPIs SUPERIORES)
    # ==========================================
    st.header("1. Resumen Ejecutivo Global")
    v_tot = df['Venta_N'].sum()
    c_tot = df['Costo_N'].sum()
    # Renta global exacta: (V-C)/V
    renta_global = ((v_tot - c_tot) / v_tot * 100) if v_tot != 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("VENTA TOTAL", f"$ {v_tot:,.0f}")
    c2.metric("MARGEN RTA %", f"{renta_global:.1f} %")
    c3.metric("TOTAL CLIENTES", f"{df['Razón social'].nunique():,}")
    
    # FACTURACIÓN POR MARCA FOCO (Corregido búsqueda por texto)
    st.subheader("📊 Facturación por Marca Foco")
    marcas_foco = ['SMART TEK', 'X-VIEW', 'TABLETS', 'CLOUDBOOK', 'LEVEL-UP', 'MICROCASE', 'TERRA']
    cols_f = st.columns(len(marcas_foco))
    
    for i, m in enumerate(marcas_foco):
        # Buscamos coincidencias parciales (ej: 'TABLET' encuentra 'TABLETS')
        base_m = m.split('-')[0].split(' ')[0] # Toma la primera palabra clave
        vta_m = df[df['Marca_Clean'].str.contains(base_m, na=False)]['Venta_N'].sum()
        cols_f[i].metric(m, f"${vta_m:,.0f}")

    st.divider()

    # ==========================================
    # 2. DASHBOARD INDIVIDUAL: PABLO LOPEZ
    # ==========================================
    st.header("👤 Dashboard de Desempeño: PABLO LOPEZ")
    
    # Filtramos datos específicos para Pablo
    df_pablo = df[df['Vendedor_Clean'].str.contains("PABLO LOPEZ", na=False)]
    
    if not df_pablo.empty:
        v_pablo = df_pablo['Venta_N'].sum()
        c_pablo = df_pablo['Costo_N'].sum()
        r_pablo = ((v_pablo - c_pablo) / v_pablo * 100) if v_pablo != 0 else 0
        cli_pablo = df_pablo['Razón social'].nunique()

        # Estética Power BI: Fondo azul para KPIs del vendedor
        st.markdown(f"""
        <div style="background-color:#1E3A8A; padding:20px; border-radius:10px; color:white; margin-bottom:20px">
            <div style="display:flex; justify-content:space-between; align-items:center">
                <h2 style="color:white; margin:0">PABLO LOPEZ</h2>
                <h1 style="color:white; margin:0">$ {v_pablo:,.0f}</h1>
                <div style="text-align:right">
                    <p style="margin:0">Cant. Clientes</p>
                    <h2 style="color:white; margin:0">{cli_pablo}</h2>
                </div>
                <div style="text-align:right">
                    <p style="margin:0">Renta %</p>
                    <h2 style="color:white; margin:0">{r_pablo:.2f}%</h2>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_p1, col_p2 = st.columns([1, 2])
        
        with col_p1:
            st.subheader("Venta x Marca")
            # Agrupamos marcas para el gráfico de torta de Pablo
            m_pablo = df_pablo.groupby('Marca_Clean')['Venta_N'].sum().nlargest(6)
            fig_pie, ax_pie = plt.subplots()
            ax_pie.pie(m_pablo, labels=m_pablo.index, autopct='%1.1f%%', startangle=90, colors=sns.color_palette("viridis"))
            st.pyplot(fig_pie)

        with col_p2:
            st.subheader("Detalle por Cliente (Razón Social)")
            # Tabla de performance por cliente
            tabla_cli = df_pablo.groupby('Razón social').agg({
                'Venta_N': 'sum',
                'Costo_N': 'sum',
                'Cantidad_N': 'sum'
            }).reset_index()
            
            tabla_cli['Renta %'] = ((tabla_cli['Venta_N'] - tabla_cli['Costo_N']) / tabla_cli['Venta_N'] * 100).round(1)
            
            st.dataframe(
                tabla_cli[['Razón social', 'Renta %', 'Venta_N', 'Cantidad_N']]
                .sort_values(by='Venta_N', ascending=False)
                .style.format({'Venta_N': '${:,.0f}', 'Renta %': '{:.1f}%'}),
                use_container_width=True,
                height=400
            )
    else:
        st.warning("No se encontraron datos para 'PABLO LOPEZ'. Verificá el nombre en el Excel.")

    st.divider()
    # (Aquí sigue el resto de tu informe vertical...)
