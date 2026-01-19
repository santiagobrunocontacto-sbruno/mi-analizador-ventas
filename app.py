import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import google.generativeai as genai

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Tablero Comercial", layout="wide")
sns.set_theme(style="whitegrid")

def auditoria_numerica(valor):
    if pd.isna(valor): return 0.0
    s = str(valor).strip().replace('$', '').replace(' ', '')
    if not s: return 0.0
    if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.')
    elif ',' in s: s = s.replace(',', '.')
    elif s.count('.') > 1: s = s.replace('.', '')
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
    return df

# --- CARGA DE DATOS ---
archivo = st.file_uploader("Cargar Base de Datos (CSV)", type=["csv"])

if archivo:
    df = cargar_limpio(archivo)
    tab_reporte, tab_ia = st.tabs(["📊 Reporte Detallado", "🤖 Consultor IA Estratégico"])

    with tab_reporte:
        v_total = df['Venta_N'].sum()
        renta_g = ((v_total - df['Costo_N'].sum()) / v_total * 100) if v_total != 0 else 0
        
        st.title("1. Resumen Ejecutivo Global")
        st.markdown(f"### VENTA TOTAL: **$ {v_total:,.0f}**")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("MARGEN RTA %", f"{renta_g:.2f} %")
        c2.metric("CLIENTES ÚNICOS", f"{df['Razón social'].nunique():,}")
        c3.metric("BULTOS TOTALES", f"{len(df):,}")

        # --- GRÁFICO DE MARCAS FOCO (RESTAURADO) ---
        st.subheader("📊 Facturación por Marca Foco")
        foco = ['SMART', 'X-VIEW', 'TABLET', 'CLOUD', 'LEVEL', 'MICROCASE', 'TERRA']
        vtas_foco = [df[df['Marca_Clean'].str.contains(m, na=False)]['Venta_N'].sum() for m in foco]
        
        fig_m, ax_m = plt.subplots(figsize=(10, 3))
        sns.barplot(x=foco, y=vtas_foco, palette="Blues_r", ax=ax_m)
        st.pyplot(fig_m)

        st.divider()

        # --- SECCIÓN VENDEDORES (DISEÑO ORIGINAL) ---
        vendedores = ["PABLO LOPEZ", "WALTER ABBAS", "FRANCISCO TEDIN", "OSMAR GRIGERA", "ALEJANDRO CHALIN", "FRANCO ABALLAY", "HORACIO GUSTAVO PÉREZ KOHUT", "LUIS RITUCCI", "NICOLAS PACCE", "NATALIA MONFORT"]

        for vend in vendedores:
            df_v = df[df['Vendedor_Clean'].str.contains(vend, na=False)].copy()
            if not df_v.empty:
                v_v = df_v['Venta_N'].sum()
                r_v = ((v_v - df_v['Costo_N'].sum()) / v_v * 100) if v_v != 0 else 0
                
                with st.expander(f"DASHBOARD: {vend}"):
                    st.markdown(f"""
                    <div style="background-color:#002147; padding:20px; border-radius:10px; color:white; display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:22px; font-weight:bold">{vend}</span>
                        <span style="font-size:26px; font-weight:bold">$ {v_v:,.0f}</span>
                        <span style="font-size:18px">Renta: {r_v:.2f}%</span>
                    </div><br>""", unsafe_allow_html=True)
                    
                    col_l, col_r = st.columns([1, 1.2])
                    with col_l:
                        m_v = df_v.groupby('Marca_Clean')['Venta_N'].sum().nlargest(5)
                        fig_p, ax_p = plt.subplots()
                        ax_p.pie(m_v, labels=m_v.index, autopct='%1.1f%%', startangle=90)
                        st.pyplot(fig_p)
                    with col_r:
                        matriz = df_v.groupby('Razón social').agg({'Venta_N': 'sum'}).reset_index()
                        st.dataframe(matriz.sort_values('Venta_N', ascending=False), use_container_width=True)

    with tab_ia:
        st.header("🤖 Consultor Estratégico")
        key = st.text_input("Gemini API Key:", type="password")
        pregunta = st.text_input("¿Qué quieres saber de tus ventas?")
        
        if pregunta and key:
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Le damos contexto a la IA para que no responda genérico
                resumen = f"Venta total: {v_total}. Vendedor top: {df.groupby('Vendedor_Clean')['Venta_N'].sum().idxmax()}. Marcas foco: {foco}"
                prompt = f"Basado en estos datos: {resumen}, responde: {pregunta}. Se breve y profesional."
                
                response = model.generate_content(prompt)
                st.write(response.text)
            except Exception as e:
                st.error(f"Error: {e}")
