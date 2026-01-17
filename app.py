import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# CONFIGURACIÓN
st.set_page_config(page_title="Executive Sales Report", layout="wide")

def auditoria_numerica(valor):
    """Convierte cualquier formato contable de Excel a número real de Python"""
    if pd.isna(valor): return 0.0
    s = str(valor).strip().replace('$', '').replace(' ', '')
    if not s: return 0.0
    
    # Si hay puntos y comas (formato 1.234,56), quitamos puntos y cambiamos coma por punto
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    # Si solo hay una coma, es el decimal
    elif ',' in s:
        s = s.replace(',', '.')
    # Si hay más de un punto (formato 1.234.567), quitamos todos
    elif s.count('.') > 1:
        s = s.replace('.', '')
    # Si hay un solo punto y 3 dígitos después, es de miles (ej: 7.860)
    elif '.' in s and len(s.split('.')[-1]) == 3:
        s = s.replace('.', '')
        
    try:
        return float(s)
    except:
        return 0.0

@st.cache_data
def cargar_limpio(file):
    df = pd.read_csv(file, sep=';', encoding='latin-1')
    df.columns = df.columns.str.strip()
    
    # Limpieza forzada
    df['Venta_N'] = df['Venta'].apply(auditoria_numerica)
    df['Costo_N'] = df['Costo Total'].apply(auditoria_numerica)
    df['Cantidad_N'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0).astype(int)
    
    # Normalización de nombres
    df['Vendedor_Clean'] = df['Nombre Vendedor'].astype(str).str.upper().str.strip()
    df['Marca_Clean'] = df['Marca'].astype(str).str.upper().str.strip()
    df['Cat_Clean'] = df['Categoria'].astype(str).str.upper().str.strip()
    
    return df

# --- INTERFAZ ---
st.title("🚀 Tablero de Comando Comercial")
archivo = st.file_uploader("Cargar fac limpia.csv", type=["csv"])

if archivo:
    df = cargar_limpio(archivo)
    
    # ==========================================
    # 1. KPIs GLOBALES
    # ==========================================
    v_total = df['Venta_N'].sum()
    c_total = df['Costo_N'].sum()
    # Renta calculada sobre los totales sumados (método contable puro)
    renta_total = ((v_total - c_total) / v_total * 100) if v_total != 0 else 0
    
    st.header("1. Resumen Ejecutivo")
    st.markdown(f"### VENTA TOTAL: **$ {v_total:,.0f}**")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("MARGEN RTA %", f"{renta_total:.2f} %")
    col2.metric("CLIENTES ÚNICOS", f"{df['Razón social'].nunique():,}")
    
    # MARCAS FOCO (Solución al $0 usando búsqueda por 'palabra clave')
    st.subheader("📊 Facturación por Marca Foco")
    foco = ['SMART', 'X-VIEW', 'TABLET', 'CLOUD', 'LEVEL', 'MICROCASE', 'TERRA']
    cols_f = st.columns(len(foco))
    for i, m in enumerate(foco):
        vta_m = df[df['Marca_Clean'].str.contains(m, na=False)]['Venta_N'].sum()
        cols_f[i].metric(m, f"${vta_m:,.0f}")

    st.divider()

    # ==========================================
    # 2. DASHBOARD VENDEDOR: PABLO LOPEZ
    # ==========================================
    df_pablo = df[df['Vendedor_Clean'].str.contains("PABLO LOPEZ", na=False)]
    
    if not df_pablo.empty:
        v_p = df_pablo['Venta_N'].sum()
        c_p = df_pablo['Costo_N'].sum()
        r_p = ((v_p - c_p) / v_p * 100) if v_p != 0 else 0
        
        # Diseño azul institucional
        st.markdown(f"""
        <div style="background-color:#002147; padding:25px; border-radius:10px; color:white; border-left: 10px solid #0077B6">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size:30px; font-weight:bold">PABLO LOPEZ</div>
                <div style="font-size:35px; font-weight:bold">$ {v_p:,.0f}</div>
                <div style="text-align:right">
                    <span style="font-size:12px">CLIENTES</span><br><span style="font-size:22px; font-weight:bold">{df_pablo['Razón social'].nunique()}</span>
                </div>
                <div style="text-align:right">
                    <span style="font-size:12px">RENTA %</span><br><span style="font-size:22px; font-weight:bold">{r_p:.2f}%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c_p1, c_p2 = st.columns([1, 1.2])
        
        with c_p1:
            st.subheader("Venta por Marca")
            m_v = df_pablo.groupby('Marca_Clean')['Venta_N'].sum().nlargest(6)
            fig, ax = plt.subplots()
            # Torta con monto en $ incluido
            ax.pie(m_v, labels=m_v.index, autopct=lambda p: f'{p:.1f}%\n(${p*v_p/100:,.0f})', 
                   startangle=90, colors=sns.color_palette("viridis"))
            st.pyplot(fig)

        with c_p2:
            st.subheader("Ranking Categorías")
            rank_cat = df_pablo.groupby('Cat_Clean').agg({'Venta_N': 'sum', 'Cantidad_N': 'sum'}).sort_values('Venta_N', ascending=False)
            st.table(rank_cat.head(10).style.format({'Venta_N': '$ {:,.0f}', 'Cantidad_N': '{:,}'}))

        st.subheader("Detalle por Cliente")
        cli_p = df_pablo.groupby('Razón social').agg({'Venta_N': 'sum', 'Costo_N': 'sum', 'Cantidad_N': 'sum'}).reset_index()
        cli_p['Renta %'] = ((cli_p['Venta_N'] - cli_p['Costo_N']) / cli_p['Venta_N'] * 100)
        st.dataframe(cli_p.sort_values('Venta_N', ascending=False).style.format({
            'Venta_N': '$ {:,.0f}', 'Renta %': '{:.2f}%', 'Cantidad_N': '{:,}'
        }), use_container_width=True)
