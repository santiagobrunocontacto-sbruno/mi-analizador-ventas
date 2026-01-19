import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import google.generativeai as genai

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Tablero Comercial", layout="wide")
sns.set_theme(style="whitegrid")

# --- FUNCIONES DE LIMPIEZA ---
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
    tab_reporte, tab_ia = st.tabs(["📊 Reporte Comercial", "🤖 Consultor IA"])

    with tab_reporte:
        # 1. RESUMEN GLOBAL (INTOCABLE)
        v_total = df['Venta_N'].sum()
        renta_g = ((v_total - df['Costo_N'].sum()) / v_total * 100) if v_total != 0 else 0
        
        st.header("1. Resumen Ejecutivo Global")
        st.markdown(f"### VENTA TOTAL: **$ {v_total:,.0f}**")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("MARGEN RTA %", f"{renta_g:.2f} %")
        c2.metric("CLIENTES ÚNICOS", f"{df['Razón social'].nunique():,}")
        c3.metric("BULTOS TOTALES", f"{df['Cantidad_N'].sum():,}")

        st.subheader("📊 Facturación por Marca Foco")
        foco = ['SMART', 'X-VIEW', 'TABLET', 'CLOUD', 'LEVEL', 'MICROCASE', 'TERRA']
        vtas_foco = [df[df['Marca_Clean'].str.contains(m, na=False)]['Venta_N'].sum() for m in foco]
        
        fig_m, ax_m = plt.subplots(figsize=(10, 3))
        sns.barplot(x=foco, y=vtas_foco, palette="Blues_r", ax=ax_m)
        ax_m.ticklabel_format(style='plain', axis='y')
        st.pyplot(fig_m)

        st.divider()

        # 2. SECCIÓN VENDEDORES (DISEÑO BLINDADO: BARRA + TORTA + TABLA CATEGORIAS + MATRIZ)
        vendedores = ["PABLO LOPEZ", "WALTER ABBAS", "FRANCISCO TEDIN", "OSMAR GRIGERA", "ALEJANDRO CHALIN", "FRANCO ABALLAY", "HORACIO GUSTAVO PÉREZ KOHUT", "LUIS RITUCCI", "NICOLAS PACCE", "NATALIA MONFORT"]

        for vend in vendedores:
            df_v = df[df['Vendedor_Clean'].str.contains(vend, na=False)].copy()
            if not df_v.empty:
                v_v = df_v['Venta_N'].sum()
                r_v = ((v_v - df_v['Costo_N'].sum()) / v_v * 100) if v_v != 0 else 0
                cant_clientes = df_v['Razón social'].nunique()
                
                with st.expander(f"DASHBOARD: {vend}", expanded=(vend == "PABLO LOPEZ")):
                    # BARRA AZUL DE TOTALES
                    st.markdown(f"""
                    <div style="background-color:#002147; padding:20px; border-radius:10px; color:white; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px">
                        <span style="font-size:24px; font-weight:bold">{vend}</span>
                        <span style="font-size:28px; font-weight:bold">$ {v_v:,.0f}</span>
                        <div style="text-align:right"><span style="font-size:14px">CLIENTES</span><br><span style="font-size:20px; font-weight:bold">{cant_clientes}</span></div>
                        <div style="text-align:right"><span style="font-size:14px">RENTA</span><br><span style="font-size:20px; font-weight:bold">{r_v:.2f}%</span></div>
                    </div>""", unsafe_allow_html=True)
                    
                    # COLUMNAS: IZQ (GRAFICO TORTA) | DER (TABLA CATEGORIAS)
                    col_l, col_r = st.columns([1, 1.2])
                    
                    with col_l:
                        st.subheader("Venta por Marca")
                        m_v = df_v.groupby('Marca_Clean')['Venta_N'].sum().nlargest(6)
                        fig_p, ax_p = plt.subplots()
                        ax_p.pie(m_v, labels=m_v.index, autopct='%1.1f%%', startangle=90, colors=sns.color_palette("viridis"))
                        st.pyplot(fig_p)
                    
                    with col_r:
                        st.subheader("Ranking Categorías")
                        # Tabla de categorías recuperada
                        rank_cat = df_v.groupby('Cat_Clean').agg({'Venta_N': 'sum', 'Cantidad_N': 'sum'}).sort_values('Venta_N', ascending=False).head(10)
                        st.dataframe(rank_cat.style.format({'Venta_N': '$ {:,.0f}', 'Cantidad_N': '{:,}'}), use_container_width=True)

                    # MATRIZ INFERIOR (CLIENTES)
                    st.subheader("Matriz de Clientes y Mix de Marcas")
                    matriz = df_v.groupby('Razón social').agg({'Venta_N': 'sum'}).reset_index()
                    matriz['% Part.'] = (matriz['Venta_N'] / v_v * 100)
                    
                    for clave_m in ['SMART', 'X-VIEW', 'TABLET', 'LEVEL', 'CLOUD', 'MICROCASE']:
                        vta_m_c = df_v[df_v['Marca_Clean'].str.contains(clave_m, na=False)].groupby('Razón social')['Venta_N'].sum()
                        matriz[f"{clave_m} %"] = (matriz['Razón social'].map(vta_m_c).fillna(0) / matriz['Venta_N']) * 100

                    # Estilo Alerta Roja (>10%)
                    def highlight_10(s):
                        return ['background-color: #ffcccc' if (s.name == '% Part.' and v > 10) else '' for v in s]

                    st.dataframe(matriz.sort_values('Venta_N', ascending=False).style.format({
                        'Venta_N': '$ {:,.0f}', '% Part.': '{:.2f}%',
                        'SMART %': '{:.1f}%', 'X-VIEW %': '{:.1f}%', 'TABLET %': '{:.1f}%', 
                        'LEVEL %': '{:.1f}%', 'CLOUD %': '{:.1f}%', 'MICROCASE %': '{:.1f}%'
                    }).apply(highlight_10, axis=1), use_container_width=True)
                    
                    st.divider()

    with tab_ia:
        st.header("🤖 Consultor Estratégico")
        st.info("Escribe tu API Key. El sistema buscará automáticamente el mejor modelo disponible.")
        
        key = st.text_input("Gemini API Key:", type="password")
        pregunta = st.text_input("Pregunta (ej: ¿Qué vendedor tiene el mejor margen?):")
        
        if pregunta and key:
            genai.configure(api_key=key)
            
            # --- CONTEXTO PARA LA IA ---
            resumen = f"""
            Total Venta Compañía: ${v_total:,.0f}.
            Ranking Vendedores (Venta): {df.groupby('Vendedor_Clean')['Venta_N'].sum().sort_values(ascending=False).to_dict()}.
            Ranking Vendedores (Rentabilidad %): {(df.groupby('Vendedor_Clean').apply(lambda x: (x['Venta_N'].sum() - x['Costo_N'].sum())/x['Venta_N'].sum()*100)).sort_values(ascending=False).to_dict()}.
            """
            prompt = f"Actúa como un analista de ventas experto. Basado en estos datos: {resumen}. Responde a la pregunta del usuario: {pregunta}. Sé breve y directo."
            
            # --- LÓGICA MULTI-MODELO (SOLUCIÓN AL ERROR 404) ---
            modelos_a_probar = ['gemini-1.5-flash', 'gemini-1.0-pro', 'gemini-pro']
            respuesta_exitosa = False
            
            with st.spinner("Analizando con IA..."):
                for nombre_modelo in modelos_a_probar:
                    try:
                        model = genai.GenerativeModel(nombre_modelo)
                        response = model.generate_content(prompt)
                        st.success(f"Respuesta generada (Modelo usado: {nombre_modelo}):")
                        st.write(response.text)
                        respuesta_exitosa = True
                        break # Si funciona, salimos del bucle
                    except Exception as e:
                        continue # Si falla, probamos el siguiente
                
                if not respuesta_exitosa:
                    st.error("Error: No se pudo conectar con ningún modelo de IA. Verifica tu API Key.")
                    st.caption("Detalle técnico: Todos los modelos (Flash, Pro, 1.0) devolvieron error.")

else:
    st.info("Por favor, carga el archivo CSV.")
