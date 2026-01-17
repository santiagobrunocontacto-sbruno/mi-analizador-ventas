import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# CONFIGURACIÓN DE PÁGINA ESTILO CORPORATIVO
st.set_page_config(page_title="Executive Sales Report", layout="wide")
sns.set_theme(style="whitegrid")

def limpieza_contable_total(serie):
    """Función definitiva para limpiar moneda argentina (puntos de miles y coma decimal)"""
    s = serie.astype(str).str.strip()
    s = s.str.replace('$', '', regex=False).str.replace(' ', '', regex=False)
    # Si el número tiene coma y punto, el punto es de miles (se borra) y la coma es decimal (se pasa a punto)
    if s.str.contains(',').any() and s.str.contains('\.').any():
        s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    # Si solo tiene coma, es el separador decimal
    elif s.str.contains(',').any():
        s = s.str.replace(',', '.', regex=False)
    # Si solo tiene punto y parece ser de miles (ej: 7.860.717)
    elif s.str.count('\.') > 1:
        s = s.str.replace('.', '', regex=False)
    return pd.to_numeric(s, errors='coerce').fillna(0)

@st.cache_data
def cargar_datos(file):
    df = pd.read_csv(file, sep=';', encoding='latin-1')
    df.columns = df.columns.str.strip()
    
    # Procesamiento Matemático
    df['Venta_N'] = limpieza_contable_total(df['Venta'])
    df['Costo_N'] = limpieza_contable_total(df['Costo Total'])
    df['Cantidad_N'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0).astype(int)
    
    # Normalización de Texto
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
    # 1. RESUMEN EJECUTIVO GLOBAL
    # ==========================================
    st.header("1. Performance Corporativa")
    v_tot = df['Venta_N'].sum()
    c_tot = df['Costo_N'].sum()
    renta_global = ((v_tot - c_tot) / v_tot * 100) if v_tot != 0 else 0
    
    # Formato de moneda para visualización clara
    st.markdown(f"### VENTA TOTAL ANUAL: **$ {v_tot:,.0f}**")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("MARGEN RTA %", f"{renta_global:.2f} %")
    c2.metric("CLIENTES ACTIVOS", f"{df['Razón social'].nunique():,}")
    c3.metric("BULTOS TOTALES", f"{df['Cantidad_N'].sum():,}")

    # GRÁFICO DE MARCAS FOCO (Con valores enteros)
    st.subheader("📊 Facturación Marcas Foco")
    marcas_foco = ['SMART TEK', 'X-VIEW', 'TABLETS', 'CLOUDBOOK', 'LEVEL-UP', 'MICROCASE', 'TERRA']
    vta_m_foco = {}
    for m in marcas_foco:
        # Búsqueda inteligente para evitar el $0 (ej: busca 'LEVEL' para encontrar 'LEVEL-UP')
        busqueda = m.split('-')[0].split(' ')[0]
        vta_m_foco[m] = df[df['Marca_Clean'].str.contains(busqueda, na=False)]['Venta_N'].sum()

    fig_f, ax_f = plt.subplots(figsize=(12, 4))
    sns.barplot(x=list(vta_m_foco.keys()), y=list(vta_m_foco.values()), palette="Blues_d", ax=ax_f)
    ax_f.ticklabel_format(style='plain', axis='y')
    for p in ax_f.patches:
        ax_f.annotate(f'${p.get_height():,.0f}', (p.get_x() + p.get_width() / 2., p.get_height()), 
                     ha='center', va='center', xytext=(0, 9), textcoords='offset points', fontsize=8)
    st.pyplot(fig_f)

    st.divider()

    # ==========================================
    # 2. DASHBOARD INDIVIDUAL: PABLO LOPEZ
    # ==========================================
    nombre_vendedor = "PABLO LOPEZ" # Esto se puede convertir en un selector luego
    df_v = df[df['Vendedor_Clean'].str.contains(nombre_vendedor, na=False)]
    
    if not df_v.empty:
        st.header(f"👤 Dashboard Gerencial: {nombre_vendedor}")
        
        v_v = df_v['Venta_N'].sum()
        c_v = df_v['Costo_N'].sum()
        r_v = ((v_v - c_v) / v_v * 100) if v_v != 0 else 0
        
        # Simulación Año Anterior (Para cuando sumes el dato)
        v_año_ant = 0 # Aquí iría la lógica de filtrado del año pasado
        crecimiento = ((v_v - v_año_ant) / v_año_ant * 100) if v_año_ant > 0 else 0

        # ENCABEZADO AZUL CORPORATIVO
        st.markdown(f"""
        <div style="background-color:#002147; padding:25px; border-radius:10px; color:white; border-left: 10px solid #0077B6">
            <table style="width:100%; border:none">
                <tr>
                    <td style="font-size:30px; font-weight:bold">{nombre_vendedor}</td>
                    <td style="text-align:center; font-size:35px; font-weight:bold">$ {v_v:,.0f}</td>
                    <td style="text-align:right">
                        <span style="font-size:14px">RENTA %</span><br>
                        <span style="font-size:24px; font-weight:bold">{r_v:.2f}%</span>
                    </td>
                    <td style="text-align:right">
                        <span style="font-size:14px">CRECIMIENTO vs AA</span><br>
                        <span style="font-size:24px; font-weight:bold">{crecimiento:.1f}%</span>
                    </td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        col_v1, col_v2 = st.columns([1, 1.5])

        with col_v1:
            st.subheader("Venta por Marca ($ y %)")
            m_v_data = df_v.groupby('Marca_Clean')['Venta_N'].sum().nlargest(6)
            
            fig_p, ax_p = plt.subplots(figsize=(6, 6))
            # Función para mostrar Monto + Porcentaje en la torta
            def fmt(x):
                return '{:.1f}%\n(${:,.0f})'.format(x, v_v * x / 100)
            
            ax_p.pie(m_v_data, labels=m_v_data.index, autopct=fmt, startangle=90, 
                     colors=sns.color_palette("mako"), textprops={'fontsize': 8})
            st.pyplot(fig_p)

        with col_v2:
            st.subheader("Ranking de Categorías Vendidas")
            cat_rank = df_v.groupby('Cat_Clean').agg({
                'Venta_N': 'sum',
                'Cantidad_N': 'sum'
            }).sort_values('Venta_N', ascending=False)
            
            st.dataframe(cat_rank.style.format({'Venta_N': '${:,.0f}', 'Cantidad_N': '{:,}'}), use_container_width=True)

        st.subheader("Detalle de Cartera de Clientes")
        cli_df = df_v.groupby('Razón social').agg({
            'Venta_N': 'sum',
            'Costo_N': 'sum',
            'Cantidad_N': 'sum'
        }).reset_index()
        cli_df['Renta %'] = ((cli_df['Venta_N'] - cli_df['Costo_N']) / cli_df['Venta_N'] * 100).round(2)
        
        st.dataframe(
            cli_df[['Razón social', 'Venta_N', 'Renta %', 'Cantidad_N']]
            .sort_values('Venta_N', ascending=False)
            .style.format({'Venta_N': '${:,.0f}', 'Renta %': '{:.2f}%', 'Cantidad_N': '{:,}'}),
            use_container_width=True
        )

else:
    st.info("Esperando archivo CSV para generar el Reporte Multinacional...")
