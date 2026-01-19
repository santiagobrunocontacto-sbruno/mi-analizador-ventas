import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# CONFIGURACIÓN ORIGINAL
st.set_page_config(page_title="Tablero Comercial Corporativo", layout="wide")
sns.set_theme(style="whitegrid")

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
    
    # PESTAÑAS (MANTENIENDO EL DISEÑO EN LA TAB1)
    tab_reporte, tab_ia = st.tabs(["📊 Reporte Detallado", "🤖 Consultor IA Estratégico"])

    with tab_reporte:
        # --- RESUMEN GLOBAL ---
        v_total_global = df['Venta_N'].sum()
        c_total_global = df['Costo_N'].sum()
        renta_global = ((v_total_global - c_total_global) / v_total_global * 100) if v_total_global != 0 else 0
        
        st.title("🏛️ Informe de Gestión Comercial")
        st.markdown(f"### VENTA TOTAL COMPAÑÍA: **$ {v_total_global:,.0f}**")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("MARGEN RTA %", f"{renta_global:.2f} %")
        c2.metric("CLIENTES ÚNICOS", f"{df['Razón social'].nunique():,}")
        c3.metric("BULTOS TOTALES", f"{df['Cantidad_N'].sum():,}")

        st.divider()

        # --- SECCIÓN VENDEDORES (DISEÑO ORIGINAL RESTAURADO) ---
        vendedores_objetivo = [
            "PABLO LOPEZ", "WALTER ABBAS", "FRANCISCO TEDIN", 
            "OSMAR GRIGERA", "ALEJANDRO CHALIN", "FRANCO ABALLAY", 
            "HORACIO GUSTAVO PÉREZ KOHUT", "LUIS RITUCCI", 
            "NICOLAS PACCE", "NATALIA MONFORT"
        ]

        for vend in vendedores_objetivo:
            df_v = df[df['Vendedor_Clean'].str.contains(vend, na=False)].copy()
            if not df_v.empty:
                v_v = df_v['Venta_N'].sum()
                c_v = df_v['Costo_N'].sum()
                r_v = ((v_v - c_v) / v_v * 100) if v_v != 0 else 0
                
                # Volvemos al diseño de Pablo Lopez que tenías antes
                st.markdown(f"### 👤 Dashboard de Desempeño: {vend}")
                st.markdown(f"""
                <div style="background-color:#002147; padding:20px; border-radius:10px; color:white; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px">
                    <span style="font-size:24px; font-weight:bold">{vend}</span>
                    <span style="font-size:28px; font-weight:bold">$ {v_v:,.0f}</span>
                    <div style="text-align:right">
                        <span style="font-size:14px">CLIENTES</span><br><span style="font-size:22px; font-weight:bold">{df_v['Razón social'].nunique()}</span>
                    </div>
                    <div style="text-align:right">
                        <span style="font-size:14px">RENTA %</span><br><span style="font-size:22px; font-weight:bold">{r_v:.2f}%</span>
                    </div>
                </div>""", unsafe_allow_html=True)

                col_l, col_r = st.columns([1, 1.2])
                with col_l:
                    st.subheader("Venta x Marca")
                    m_v = df_v.groupby('Marca_Clean')['Venta_N'].sum().nlargest(6)
                    fig_p, ax_p = plt.subplots()
                    ax_p.pie(m_v, labels=m_v.index, autopct=lambda p: f'{p:.1f}%', startangle=90, colors=sns.color_palette("viridis"))
                    st.pyplot(fig_p)

                with col_r:
                    st.subheader("Ranking Categorías")
                    rank_cat = df_v.groupby('Cat_Clean').agg({'Venta_N': 'sum', 'Cantidad_N': 'sum'}).sort_values('Venta_N', ascending=False).head(10)
                    st.table(rank_cat.style.format({'Venta_N': '$ {:,.0f}', 'Cantidad_N': '{:,}'}))

                st.subheader("🏛️ Matriz de Clientes: Venta y Mix de Marcas")
                matriz = df_v.groupby('Razón social').agg({'Venta_N': 'sum'}).reset_index()
                matriz['% Participación'] = (matriz['Venta_N'] / v_v * 100)
                
                for clave_m in ['SMART', 'X-VIEW', 'TABLET', 'LEVEL', 'CLOUD', 'MICROCASE']:
                    vta_m_c = df_v[df_v['Marca_Clean'].str.contains(clave_m, na=False)].groupby('Razón social')['Venta_N'].sum()
                    matriz[f"{clave_m} %"] = (matriz['Razón social'].map(vta_m_c).fillna(0) / matriz['Venta_N']) * 100

                st.dataframe(matriz.sort_values('Venta_N', ascending=False).style.format({
                    'Venta_N': '$ {:,.0f}', '% Participación': '{:.2f}%',
                    'SMART %': '{:.1f}%', 'X-VIEW %': '{:.1f}%', 'TABLET %': '{:.1f}%', 
                    'LEVEL %': '{:.1f}%', 'CLOUD %': '{:.1f}%', 'MICROCASE %': '{:.1f}%'
                }), use_container_width=True)
                st.divider()

    with tab_ia:
        st.header("🤖 Consultor Estratégico Inteligente")
        st.info("Para que la IA responda basándose en tus datos reales, introduce tu API KEY abajo.")
        
        api_key = st.text_input("Introduce tu Gemini API Key:", type="password")
        
        pregunta = st.text_input("Hazle una pregunta a tus datos:")
        
        if pregunta and api_key:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # RESUMEN DE DATOS PARA LA IA
            resumen_vendedores = df.groupby('Vendedor_Clean')['Venta_N'].sum().sort_values(ascending=False).to_string()
            
            prompt = f"Eres un analista experto. Basado en estos datos de ventas: {resumen_vendedores}. Responde a la pregunta del usuario: {pregunta}"
            
            response = model.generate_content(prompt)
            st.markdown(f"### 💡 Respuesta de la IA:")
            st.write(response.text)
        elif pregunta:
            st.warning("Por favor, introduce una API Key válida para procesar la pregunta.")

else:
    st.info("Sube el archivo CSV para comenzar.")
