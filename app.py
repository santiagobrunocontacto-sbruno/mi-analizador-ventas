import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Executive Report v4", layout="wide")

def auditoria_numerica(valor):
    if pd.isna(valor): return 0.0
    s = str(valor).strip().replace('$', '').replace(' ', '')
    if not s: return 0.0
    if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.')
    elif ',' in s: s = s.replace(',', '.')
    elif s.count('.') > 1: s = s.replace('.', '')
    elif '.' in s and len(s.split('.')[-1]) == 3: s = s.replace('.', '')
    try: return float(s)
    except: return 0.0

@st.cache_data
def cargar_limpio(file):
    df = pd.read_csv(file, sep=';', encoding='latin-1')
    df.columns = df.columns.str.strip()
    df['Venta_N'] = df['Venta'].apply(auditoria_numerica)
    df['Costo_N'] = df['Costo Total'].apply(auditoria_numerica)
    df['Cantidad_N'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0).astype(int)
    df['Vendedor_Clean'] = df['Nombre Vendedor'].astype(str).str.upper().str.strip()
    df['Marca_Clean'] = df['Marca'].astype(str).str.upper().str.strip()
    df['Cat_Clean'] = df['Categoria'].astype(str).str.upper().str.strip()
    return df

if "archivo" not in st.session_state:
    archivo = st.file_uploader("Cargar Base de Datos", type=["csv"])
    if archivo: st.session_state.archivo = archivo

if "archivo" in st.session_state:
    df = cargar_limpio(st.session_state.archivo)
    
    # --- 1. RESUMEN EJECUTIVO GLOBAL ---
    v_total = df['Venta_N'].sum()
    c_total = df['Costo_N'].sum()
    renta_total = ((v_total - c_total) / v_total * 100) if v_total != 0 else 0
    
    st.header("1. Resumen Ejecutivo Global")
    st.markdown(f"### VENTA TOTAL: **$ {v_total:,.0f}**")
    
    c1, c2 = st.columns(2)
    c1.metric("MARGEN RTA %", f"{renta_total:.2f} %")
    c2.metric("CLIENTES ÚNICOS", f"{df['Razón social'].nunique():,}")

    # --- INDICADORES POR MARCA ---
    st.subheader("📊 Facturación por Marca Foco")
    foco = ['SMART', 'X-VIEW', 'TABLET', 'CLOUD', 'LEVEL', 'MICROCASE', 'TERRA']
    
    vtas_foco = []
    labels_foco = []
    cols_f = st.columns(len(foco))
    for i, m in enumerate(foco):
        # Búsqueda parcial para asegurar que sume todo lo que contenga la palabra
        m_total = df[df['Marca_Clean'].str.contains(m, na=False)]['Venta_N'].sum()
        vtas_foco.append(m_total)
        labels_foco.append(m)
        with cols_f[i]:
            st.markdown(f"**{m}**")
            st.markdown(f"<h4 style='color: #0077B6;'>$ {m_total:,.0f}</h4>", unsafe_allow_html=True)

    fig_b, ax_b = plt.subplots(figsize=(10, 3.5))
    sns.barplot(x=labels_foco, y=vtas_foco, palette="Blues_r", ax=ax_b)
    ax_b.set_ylabel("Facturación ($)")
    ax_b.ticklabel_format(style='plain', axis='y')
    # Etiquetas de valores sobre las barras
    for p in ax_b.patches:
        ax_b.annotate(f'${p.get_height():,.0f}', (p.get_x() + p.get_width() / 2., p.get_height()), 
                     ha='center', va='center', xytext=(0, 10), textcoords='offset points', fontsize=8)
    st.pyplot(fig_b)

    st.divider()

    # --- 2. DASHBOARD VENDEDOR: PABLO LOPEZ ---
    vendedor_fijo = "PABLO LOPEZ"
    df_v = df[df['Vendedor_Clean'].str.contains(vendedor_fijo, na=False)]
    
    if not df_v.empty:
        v_v = df_v['Venta_N'].sum()
        r_v = ((v_v - df_v['Costo_N'].sum()) / v_v * 100) if v_v != 0 else 0
        
        st.markdown(f"""
        <div style="background-color:#002147; padding:20px; border-radius:10px; color:white; display:flex; justify-content:space-between; align-items:center">
            <span style="font-size:24px; font-weight:bold">{vendedor_fijo}</span>
            <span style="font-size:28px">$ {v_v:,.0f}</span>
            <span style="font-size:20px">RENTA: {r_v:.2f}%</span>
        </div>""", unsafe_allow_html=True)

        col_l, col_r = st.columns([1, 1.2])
        
        with col_l:
            st.subheader("Venta por Marca")
            m_v = df_v.groupby('Marca_Clean')['Venta_N'].sum().nlargest(6)
            fig_p, ax_p = plt.subplots()
            ax_p.pie(m_v, labels=m_v.index, autopct=lambda p: f'{p:.1f}%\n(${p*v_v/100:,.0f})', 
                   startangle=90, colors=sns.color_palette("viridis"))
            st.pyplot(fig_p)

        with col_r:
            st.subheader("Ranking Categorías")
            rank_cat = df_v.groupby('Cat_Clean').agg({'Venta_N': 'sum', 'Cantidad_N': 'sum'}).sort_values('Venta_N', ascending=False).head(10)
            rank_cat.index.name = "Categorías"
            rank_cat.columns = ['Venta', 'Cantidad']
            st.table(rank_cat.style.format({'Venta': '$ {:,.0f}', 'Cantidad': '{:,}'}))

        # --- MATRIZ DE CLIENTES CON ALERTAS ---
        st.subheader("🏛️ Matriz Estratégica de Cartera")
        st.info("Nota: Los clientes que representan más del 10% de la venta total se resaltan en color de alerta.")
        
        # 1. Base de clientes y participación
        matriz = df_v.groupby('Razón social').agg({'Venta_N': 'sum'}).reset_index()
        matriz['% Participación'] = (matriz['Venta_N'] / v_v * 100)
        
        # 2. Mix de marcas principales
        # Buscamos marcas que contengan los nombres clave
        columnas_mix = ['SMART TEK', 'X-VIEW', 'TABLET', 'LEVEL UP', 'CLOUDBOOK', 'MICROCASE']
        for c in columnas_mix:
            key = c.split()[0] # Toma la primera palabra para buscar
            matriz[c] = df_v[df_v['Marca_Clean'].str.contains(key, na=False)].groupby('Razón social')['Venta_N'].sum()
            matriz[c] = (matriz[c].fillna(0) / matriz['Venta_N'] * 100)
        
        # 3. Función de resaltado
        def highlight_top_clients(s):
            return ['background-color: #ffcccc' if (isinstance(val, float) and val > 10 and s.name == '% Participación') else '' for val in s]

        # 4. Mostrar DataFrame final
        st.dataframe(
            matriz.sort_values('Venta_N', ascending=False).style
            .format({
                'Venta_N': '$ {:,.0f}', 
                '% Participación': '{:.2f}%',
                'SMART TEK': '{:.1f}%', 'X-VIEW': '{:.1f}%', 'TABLET': '{:.1f}%', 
                'LEVEL UP': '{:.1f}%', 'CLOUDBOOK': '{:.1f}%', 'MICROCASE': '{:.1f}%'
            })
            .apply(highlight_top_clients),
            use_container_width=True
        )

else:
    st.info("Subí el archivo CSV para procesar los datos.")
