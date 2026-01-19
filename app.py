import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# CONFIGURACIÓN
st.set_page_config(page_title="Tablero Comercial IA", layout="wide")
sns.set_theme(style="whitegrid")

# --- LÓGICA DE LIMPIEZA (TU MOTOR ACTUAL) ---
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

# --- INTERFAZ PRINCIPAL ---
archivo = st.file_uploader("Cargar Base de Datos (CSV)", type=["csv"])

if archivo:
    df = cargar_limpio(archivo)
    
    # CREACIÓN DE PESTAÑAS PARA NO MEZCLAR
    tab_reporte, tab_ia = st.tabs(["📊 Reporte Mensual de Ventas", "🤖 Consultor IA Estratégico"])

    with tab_reporte:
        # --- AQUÍ VA TODO TU CÓDIGO ACTUAL SIN TOCAR UNA COMA ---
        v_total_global = df['Venta_N'].sum()
        c_total_global = df['Costo_N'].sum()
        renta_global = ((v_total_global - c_total_global) / v_total_global * 100) if v_total_global != 0 else 0
        
        st.header("1. Resumen Ejecutivo Global")
        st.markdown(f"### VENTA TOTAL COMPAÑÍA: **$ {v_total_global:,.0f}**")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("MARGEN RTA %", f"{renta_global:.2f} %")
        c2.metric("CLIENTES ÚNICOS", f"{df['Razón social'].nunique():,}")
        c3.metric("BULTOS TOTALES", f"{df['Cantidad_N'].sum():,}")

        # Marcas Foco
        foco = ['SMART', 'X-VIEW', 'TABLET', 'CLOUD', 'LEVEL', 'MICROCASE', 'TERRA']
        vtas_foco, labels_foco = [], []
        cols_f = st.columns(len(foco))
        for i, m in enumerate(foco):
            m_total = df[df['Marca_Clean'].str.contains(m, na=False)]['Venta_N'].sum()
            vtas_foco.append(m_total)
            labels_foco.append(m)
            cols_f[i].markdown(f"**{m}**\n\n$ {m_total:,.0f}")

        fig_b, ax_b = plt.subplots(figsize=(10, 2.5))
        sns.barplot(x=labels_foco, y=vtas_foco, palette="Blues_r", ax=ax_b)
        st.pyplot(fig_b)

        st.divider()
        st.header("👤 Análisis por Vendedor")
        vendedores = ["PABLO LOPEZ", "WALTER ABBAS", "FRANCISCO TEDIN", "OSMAR GRIGERA", "ALEJANDRO CHALIN", "FRANCO ABALLAY", "HORACIO GUSTAVO PÉREZ KOHUT", "LUIS RITUCCI", "NICOLAS PACCE", "NATALIA MONFORT"]

        for vend in vendedores:
            df_v = df[df['Vendedor_Clean'].str.contains(vend, na=False)].copy()
            if not df_v.empty:
                with st.expander(f"DASHBOARD: {vend}"):
                    v_v = df_v['Venta_N'].sum()
                    r_v = ((v_v - df_v['Costo_N'].sum()) / v_v * 100) if v_v != 0 else 0
                    st.markdown(f"<div style='background-color:#002147; padding:15px; border-radius:10px; color:white;'><b>{vend}</b> | Venta: $ {v_v:,.0f} | Renta: {r_v:.2f}%</div>", unsafe_allow_html=True)
                    
                    # Matriz de Clientes y Mix (Tu lógica de porcentajes que ya funciona)
                    matriz = df_v.groupby('Razón social').agg({'Venta_N': 'sum'}).reset_index()
                    matriz['% Participación'] = (matriz['Venta_N'] / v_v * 100)
                    for clave_m in ['SMART', 'X-VIEW', 'TABLET', 'LEVEL', 'CLOUD']:
                        vta_m_c = df_v[df_v['Marca_Clean'].str.contains(clave_m, na=False)].groupby('Razón social')['Venta_N'].sum()
                        matriz[f"{clave_m} %"] = (matriz['Razón social'].map(vta_m_c).fillna(0) / matriz['Venta_N']) * 100
                    st.dataframe(matriz.sort_values('Venta_N', ascending=False), use_container_width=True)

    with tab_ia:
        st.header("🤖 Consultor Estratégico IA")
        st.write("Haz preguntas sobre el rendimiento del mes, clientes críticos o mix de productos.")

        # --- LÓGICA DE "CEREBRO" DE IA ---
        # Preparamos un resumen de datos para que la IA sepa de qué habla
        resumen_datos = df.groupby('Vendedor_Clean')['Venta_N'].sum().to_dict()
        mejor_marca = df.groupby('Marca_Clean')['Venta_N'].sum().idxmax()
        
        pregunta = st.text_input("Escribe tu consulta aquí (ej: ¿Quién es el vendedor con mejor margen?)")
        
        if pregunta:
            # Simulamos la respuesta analítica basándonos en los datos reales del DF
            with st.spinner("Analizando base de datos..."):
                # Aquí es donde conectamos con el modelo. 
                # Por ahora, para que veas el funcionamiento, el sistema detecta palabras clave:
                if "vendedor" in pregunta.lower():
                    top_v = df.groupby('Vendedor_Clean')['Venta_N'].sum().idxmax()
                    resp = f"El vendedor con mayor volumen de facturación es **{top_v}**."
                elif "marca" in pregunta.lower():
                    resp = f"La marca líder este mes es **{mejor_marca}**."
                else:
                    resp = "Estoy listo para analizar profundamente. Para respuestas específicas de clientes, necesito que definamos los parámetros de búsqueda."
                
                st.info(f"**Análisis de IA:** {resp}")
                
                # Visualización sugerida por la IA
                st.subheader("Análisis Visual Sugerido")
                fig_ia, ax_ia = plt.subplots()
                df.groupby('Vendedor_Clean')['Venta_N'].sum().plot(kind='barh', ax=ax_ia)
                st.pyplot(fig_ia)

else:
    st.info("Sube el archivo para activar el consultor.")
