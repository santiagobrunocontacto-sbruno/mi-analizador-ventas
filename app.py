import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# CONFIGURACIÓN
st.set_page_config(page_title="Auditoría Comercial v5", layout="wide")

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
    df['Vendedor_Clean'] = df['Nombre Vendedor'].astype(str).str.upper().str.strip()
    df['Marca_Clean'] = df['Marca'].astype(str).str.upper().str.strip()
    df['Cat_Clean'] = df['Categoria'].astype(str).str.upper().str.strip()
    return df

if "archivo" in st.session_state or (archivo := st.file_uploader("Cargar Base", type=["csv"])):
    if 'archivo' not in st.session_state: st.session_state.archivo = archivo
    df = cargar_limpio(st.session_state.archivo)
    
    # --- PABLO LOPEZ ---
    vendedor = "PABLO LOPEZ"
    df_v = df[df['Vendedor_Clean'].str.contains(vendedor, na=False)].copy()
    v_total_vendedor = df_v['Venta_N'].sum()

    st.title(f"Dashboard: {vendedor}")
    
    # --- MATRIZ ESTRATÉGICA (CORREGIDA) ---
    st.subheader("🏛️ Matriz de Clientes: Venta y Mix de Marcas")
    
    # 1. Agrupamos primero por Cliente para tener el total de cada uno
    clientes = df_v.groupby('Razón social').agg({'Venta_N': 'sum'}).reset_index()
    clientes['% Participación'] = (clientes['Venta_N'] / v_total_vendedor * 100)

    # 2. Definimos las marcas foco para el mix
    marcas_foco_columnas = ['SMART', 'X-VIEW', 'TABLET', 'LEVEL', 'CLOUD', 'MICROCASE']
    
    # 3. Calculamos el mix REAL: ¿Cuánto de la venta de este cliente fue de cada marca?
    for m in marcas_foco_columnas:
        # Filtramos ventas de esa marca para CADA cliente
        ventas_marca_cliente = df_v[df_v['Marca_Clean'].str.contains(m, na=False)].groupby('Razón social')['Venta_N'].sum()
        # Unimos al dataframe de clientes (si no compró esa marca, ponemos 0)
        clientes[m] = clientes['Razón social'].map(ventas_marca_cliente).fillna(0)
        # Convertimos a porcentaje: (Venta Marca Cliente / Venta Total Cliente)
        clientes[m] = (clientes[m] / clientes['Venta_N']) * 100

    # Renombramos columnas para que queden prolijas
    clientes.rename(columns={'Venta_N': 'Venta', 'SMART': 'SMART TEK %', 'LEVEL': 'LEVEL UP %', 'CLOUD': 'CLOUDBOOK %'}, inplace=True)

    # 4. Formato y resaltado (Alertas > 10%)
    def style_performance(s):
        return ['background-color: #ffcccc' if (s.name == '% Participación' and v > 10) else '' for v in s]

    st.dataframe(
        clientes.sort_values('Venta', ascending=False).style.format({
            'Venta': '$ {:,.0f}',
            '% Participación': '{:.2f}%',
            'SMART TEK %': '{:.1f}%', 'X-VIEW': '{:.1f}%', 'TABLET': '{:.1f}%', 
            'LEVEL UP %': '{:.1f}%', 'CLOUDBOOK %': '{:.1f}%', 'MICROCASE': '{:.1f}%'
        }).apply(style_performance, axis=1),
        use_container_width=True
    )

    st.success(f"La tabla muestra qué % de la venta de cada cliente corresponde a cada marca foco.")
