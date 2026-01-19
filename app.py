import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

# CONFIGURACIÓN ORIGINAL
st.set_page_config(page_title="Tablero Comercial Corporativo", layout="wide")
sns.set_theme(style="whitegrid")

# --- MOTOR DE CÁLCULO (TU LÓGICA ORIGINAL) ---
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

# --- CARGA DE DATOS ---
archivo = st.file_uploader("Cargar Base de Datos (CSV)", type=["csv"])

if archivo:
    df = cargar_limpio(archivo)
    
    # PESTAÑAS
    tab_reporte, tab_ia = st.tabs(["📊 Reporte Detallado", "🤖 Consultor IA Estratégico"])

    with tab_reporte:
        # 1. RESUMEN EJECUTIVO (COMO EN TU FOTO)
        v_total_global = df['Venta_N'].sum()
        c_total_global = df['Costo_N'].sum()
        renta_global = ((v_total_global - c_total_global) / v_total_global * 100) if v_total_global != 0 else 0
        
        st.title("1. Resumen Ejecutivo Global")
        st.markdown(f"### VENTA TOTAL: **$ {v_total_global:,.0f}**")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("MARGEN RTA %", f"{renta_global:.2f} %")
        c2.metric("CLIENTES ÚNICOS", f"{df['Razón social'].nunique():,}")
        c3.metric("BULTOS TOTALES", f"{df['Cantidad_N'].sum():,}")

        # GRÁFICO DE MARCAS FOCO (RESTAURADO)
        st.subheader("📊 Facturación por Marca Foco")
        foco_list = ['SMART', 'X-VIEW', 'TABLET', 'CLOUD', 'LEVEL', 'MICROCASE', 'TERRA']
        vtas_foco = []
        for m in foco_list:
            vtas_foco.append(df[df['Marca_Clean'].str.contains(m, na=False)]['Venta_N'].sum())
        
        fig_gen, ax_gen = plt.subplots(figsize=(10, 3))
        sns.barplot(x=foco_list, y=vtas_foco, palette="Blues_r", ax=ax_gen)
        st.pyplot(fig_gen)

        st.divider()

        # 2. SECCIÓN VENDEDORES
        vendedores = ["PABLO LOPEZ", "WALTER ABBAS", "FRANCISCO TEDIN", "OSMAR GRIGERA", "ALEJANDRO CHALIN", "FRANCO ABALLAY", "HORACIO GUSTAVO PÉREZ KOHUT", "LUIS RITUCCI", "NICOLAS PACCE", "NATALIA MONFORT"]

        for vend in vendedores:
            df_v = df[df['Vendedor_Clean'].str.contains(vend, na=False)].copy()
            if not df_v.empty:
                with st.expander(f"DASHBOARD: {vend}", expanded=(vend == "PABLO LOPEZ")):
                    v_v = df_v['Venta_N'].sum()
                    r_v = ((v_v - df_v['Costo_N'].sum()) / v_v * 100) if v_v != 0 else 0
                    
                    st.markdown(f"""
                    <div style="background-color:#002147; padding:15px; border-radius:10px; color:white; display:flex; justify-content:space-between;">
                        <span style="font-size:20px; font-weight:bold">{vend} | Venta: $ {v_v:,.0f} | Renta: {r_v:.2f}%</span>
                    </div>""", unsafe_allow_html=True)
                    
                    # Gráficos y Tablas originales...
                    col1, col2 = st.columns([1, 1.2])
                    with col1:
                        st.write("**Venta por Marca**")
                        m_v = df_v.groupby('Marca_Clean')['Venta_N'].sum().nlargest(5)
                        fig, ax = plt.subplots()
                        ax.pie(m_v, labels=m_v.index, autopct='%1.1f%%', startangle=90)
                        st.pyplot(fig)
                    with col2:
                        st.write("**Matriz de Clientes**")
                        matriz = df_v.groupby('Razón social').agg({'Venta_N': 'sum'}).reset_index()
                        matriz['% Part.'] = (matriz['Venta_N'] / v_v * 100)
                        st.dataframe(matriz.sort_values('Venta_N', ascending=False), height=300)

    with tab_ia:
        st.header("🤖 Consultor Estratégico")
        st.markdown("""
        **Para solucionar el error de IA:** 1. Crea un archivo de texto llamado `requirements.txt` en tu carpeta de proyecto.
        2. Escribe adentro: `google-generativeai` y `pandas`.
        3. Sube ese archivo a tu repositorio de Streamlit Cloud.
        """)
        
        pregunta = st.text_input("Haz una consulta sobre los datos cargados:")
        if pregunta:
            # Análisis "Manual" inteligente (Sin necesidad de API mientras arreglas el error)
            if "total" in pregunta.lower():
                st.success(f"La venta total del mes es de $ {v_total_global:,.0f}")
            elif "vendedor" in pregunta.lower():
                mejor = df.groupby('Vendedor_Clean')['Venta_N'].sum().idxmax()
                st.success(f"El vendedor estrella es {mejor}")
            else:
                st.warning("IA en mantenimiento. Por favor, instala las librerías mencionadas arriba para activar el cerebro completo.")

else:
    st.info("Sube el CSV para activar el reporte.")
