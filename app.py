import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# CONFIGURACIÓN CORPORATIVA
st.set_page_config(page_title="Executive Sales Report", layout="wide")
sns.set_theme(style="whitegrid")

def limpieza_contable_simple(serie):
    """Limpia moneda de forma directa para evitar errores de interpretación"""
    # Pasamos a string y quitamos símbolos y puntos de miles
    s = serie.astype(str).str.replace('$', '', regex=False).str.replace('.', '', regex=False).str.strip()
    # Cambiamos la coma por punto para el decimal
    s = s.str.replace(',', '.', regex=False)
    # Convertimos a número (si falla algo pone 0)
    return pd.to_numeric(s, errors='coerce').fillna(0)

@st.cache_data
def cargar_datos(file):
    df = pd.read_csv(file, sep=';', encoding='latin-1')
    df.columns = df.columns.str.strip()
    
    # Procesamiento Numérico con la nueva función simple
    df['Venta_N'] = limpieza_contable_simple(df['Venta'])
    df['Costo_N'] = limpieza_contable_simple(df['Costo Total'])
    df['Cantidad_N'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0).astype(int)
    
    # Normalización
    df['Marca_Clean'] = df['Marca'].astype(str).str.upper().str.strip()
    df['Vendedor_Clean'] = df['Nombre Vendedor'].astype(str).str.upper().str.strip()
    df['Cat_Clean'] = df['Categoria'].astype(str).str.upper().str.strip()
    
    return df

# --- INTERFAZ ---
st.title("🏛️ Informe Anual de Gestión Comercial")
archivo = st.file_uploader("Cargar Base de Datos (CSV)", type=["csv"])

if archivo:
    df = cargar_datos(archivo)
    
    # ==========================================
    # 1. PERFORMANCE CORPORATIVA GLOBAL
    # ==========================================
    st.header("1. Performance Corporativa")
    
    v_tot = df['Venta_N'].sum()
    c_tot = df['Costo_N'].sum()
    
    # Cálculo de rentabilidad directa sobre el total visible
    renta_global = ((v_tot - c_tot) / v_tot * 100) if v_tot != 0 else 0
    cant_clientes_global = df['Razón social'].nunique()

    # KPI's Principales
    st.markdown(f"### VENTA TOTAL ANUAL: **$ {v_tot:,.0f}**")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("MARGEN RTA %", f"{renta_global:.1f}%")
        st.caption("Fórmula: (Venta - Costo) / Venta")
    with c2:
        st.metric("CANTIDAD DE CLIENTES", f"{cant_clientes_global:,}")
        st.caption("Recuento distintivo de Razón Social")
    with c3:
        # Mantenemos este espacio para un KPI futuro o podrías poner el total de marcas foco aquí
        vta_m_foco_total = df[df['Marca_Clean'].str.contains('SMART|X-VIEW|TABLET|CLOUD|LEVEL|MICROCASE|TERRA', na=False)]['Venta_N'].sum()
        st.metric("VTA. MARCAS FOCO", f"$ {vta_m_foco_total:,.0f}")

    # Gráfico de Marcas Foco (Siempre visible para calidad visual)
    st.subheader("📊 Facturación Marcas Foco")
    marcas_foco = ['SMART TEK', 'X-VIEW', 'TABLETS', 'CLOUDBOOK', 'LEVEL-UP', 'MICROCASE', 'TERRA']
    # Diccionario de búsqueda simplificado
    vta_m_foco = {m: df[df['Marca_Clean'].str.contains(m.split()[0], na=False)]['Venta_N'].sum() for m in marcas_foco}

    fig_f, ax_f = plt.subplots(figsize=(12, 4))
    sns.barplot(x=list(vta_m_foco.keys()), y=list(vta_m_foco.values()), palette="Blues_d", ax=ax_f)
    ax_f.ticklabel_format(style='plain', axis='y')
    # Etiquetas de datos sobre las barras
    for p in ax_f.patches:
        ax_f.annotate(f'${p.get_height():,.0f}', (p.get_x() + p.get_width() / 2., p.get_height()), 
                     ha='center', va='center', xytext=(0, 9), textcoords='offset points', fontsize=9)
    st.pyplot(fig_f)

    st.divider()

    # ==========================================
    # 2. DASHBOARD INDIVIDUAL: PABLO LOPEZ
    # ==========================================
    nombre_v = "PABLO LOPEZ"
    df_v = df[df['Vendedor_Clean'].str.contains(nombre_v, na=False)]
    
    if not df_v.empty:
        st.header(f"👤 Dashboard Gerencial: {nombre_v}")
        
        v_v = df_v['Venta_N'].sum()
        c_v = df_v['Costo_N'].sum()
        r_v = ((v_v - c_v) / v_v * 100) if v_v != 0 else 0
        cli_v = df_v['Razón social'].nunique()

        # ENCABEZADO ESTILO POWER BI (Fondo Azul)
        st.markdown(f"""
        <div style="background-color:#002147; padding:25px; border-radius:10px; color:white; border-left: 10px solid #0077B6">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div><span style="font-size:30px; font-weight:bold">{nombre_v}</span></div>
                <div><span style="font-size:35px; font-weight:bold">$ {v_v:,.0f}</span></div>
                <div style="text-align:right">
                    <span style="font-size:12px">CANT. CLIENTES</span><br><span style="font-size:22px; font-weight:bold">{cli_v}</span>
                </div>
                <div style="text-align:right">
                    <span style="font-size:12px">RENTA %</span><br><span style="font-size:22px; font-weight:bold">{r_v:.1f}%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_v1, col_v2 = st.columns([1, 1.2])

        with col_v1:
            st.subheader("Venta por Marca ($ y %)")
            m_data = df_v.groupby('Marca_Clean')['Venta_N'].sum().nlargest(6)
            fig_p, ax_p = plt.subplots(figsize=(6, 6))
            
            def make_autopct(values):
                def my_autopct(pct):
                    total = sum(values)
                    val = int(round(pct*total/100.0))
                    return '{:.1f}%\n($ {:,.0f})'.format(pct, val)
                return my_autopct

            ax_p.pie(m_data, labels=m_data.index, autopct=make_autopct(m_data), 
                     startangle=90, colors=sns.color_palette("viridis"), textprops={'fontsize': 9})
            st.pyplot(fig_p)

        with col_v2:
            st.subheader("Ranking de Categorías")
            cat_rank = df_v.groupby('Cat_Clean').agg({
                'Venta_N': 'sum',
                'Cantidad_N': 'sum'
            }).sort_values('Venta_N', ascending=False).head(10)
            
            st.table(cat_rank.style.format({'Venta_N': '$ {:,.0f}', 'Cantidad_N': '{:,}'}))

        st.subheader("Detalle de Cartera de Clientes")
        cli_df = df_v.groupby('Razón social').agg({
            'Venta_N': 'sum',
            'Costo_N': 'sum',
            'Cantidad_N': 'sum'
        }).reset_index()
        # Renta por cliente recalculada
        cli_df['Renta %'] = ((cli_df['Venta_N'] - cli_df['Costo_N']) / cli_df['Venta_N'] * 100)
        
        st.dataframe(
            cli_df[['Razón social', 'Venta_N', 'Renta %', 'Cantidad_N']]
            .sort_values('Venta_N', ascending=False)
            .style.format({'Venta_N': '$ {:,.0f}', 'Renta %': '{:.1f}%', 'Cantidad_N': '{:,}'}),
            use_container_width=True
        )

else:
    st.info("Subí el archivo CSV para generar el informe.")
