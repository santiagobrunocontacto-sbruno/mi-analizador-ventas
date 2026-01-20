import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# NUEVO SDK (reemplaza google-generativeai)
from google import genai

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Tablero Comercial", layout="wide")
sns.set_theme(style="whitegrid")

# --- FUNCIONES DE LIMPIEZA (MANTENEMOS TU LÓGICA DE AUDITORÍA) ---
def auditoria_numerica(valor):
    if pd.isna(valor):
        return 0.0
    s = str(valor).strip().replace('$', '').replace(' ', '')
    if not s:
        return 0.0

    # Manejo de separadores típicos AR:
    # 1.234,56  -> 1234.56
    # 1234,56   -> 1234.56
    # 1.234.567 -> 1234567
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    elif s.count('.') > 1:
        s = s.replace('.', '')

    try:
        return float(s)
    except Exception:
        return 0.0


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
        # 1. RESUMEN GLOBAL
        v_total = df['Venta_N'].sum()
        costo_total = df['Costo_N'].sum()
        renta_g = ((v_total - costo_total) / v_total * 100) if v_total != 0 else 0

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

        # 2. SECCIÓN VENDEDORES (DISEÑO BLINDADO)
        vendedores = [
            "PABLO LOPEZ", "WALTER ABBAS", "FRANCISCO TEDIN", "OSMAR GRIGERA",
            "ALEJANDRO CHALIN", "FRANCO ABALLAY", "HORACIO GUSTAVO PÉREZ KOHUT",
            "LUIS RITUCCI", "NICOLAS PACCE", "NATALIA MONFORT"
        ]

        for vend in vendedores:
            df_v = df[df['Vendedor_Clean'].str.contains(vend, na=False)].copy()

            if not df_v.empty:
                v_v = df_v['Venta_N'].sum()
                c_v = df_v['Costo_N'].sum()
                r_v = ((v_v - c_v) / v_v * 100) if v_v != 0 else 0
                cant_clientes = df_v['Razón social'].nunique()

                with st.expander(f"DASHBOARD: {vend}", expanded=(vend == "PABLO LOPEZ")):
                    # BARRA AZUL DE TOTALES
                    st.markdown(
                        f"""
                        <div style="background-color:#002147; padding:20px; border-radius:10px; color:white;
                                    display:flex; justify-content:space-between; align-items:center; margin-bottom:20px">
                            <span style="font-size:24px; font-weight:bold">{vend}</span>
                            <span style="font-size:28px; font-weight:bold">$ {v_v:,.0f}</span>
                            <div style="text-align:right">
                                <span style="font-size:14px">CLIENTES</span><br>
                                <span style="font-size:20px; font-weight:bold">{cant_clientes}</span>
                            </div>
                            <div style="text-align:right">
                                <span style="font-size:14px">RENTA</span><br>
                                <span style="font-size:20px; font-weight:bold">{r_v:.2f}%</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    col_l, col_r = st.columns([1, 1.2])

                    with col_l:
                        st.subheader("Venta por Marca")
                        m_v = df_v.groupby('Marca_Clean')['Venta_N'].sum().nlargest(6)
                        fig_p, ax_p = plt.subplots()
                        ax_p.pie(
                            m_v,
                            labels=m_v.index,
                            autopct='%1.1f%%',
                            startangle=90,
                            colors=sns.color_palette("viridis")
                        )
                        st.pyplot(fig_p)

                    with col_r:
                        st.subheader("Ranking Categorías")
                        rank_cat = (
                            df_v.groupby('Cat_Clean')
                            .agg({'Venta_N': 'sum', 'Cantidad_N': 'sum'})
                            .sort_values('Venta_N', ascending=False)
                            .head(10)
                        )
                        st.dataframe(
                            rank_cat.style.format({'Venta_N': '$ {:,.0f}', 'Cantidad_N': '{:,}'}),
                            use_container_width=True
                        )

                    st.subheader("Matriz de Clientes y Mix de Marcas")
                    matriz = df_v.groupby('Razón social').agg({'Venta_N': 'sum'}).reset_index()
                    matriz['% Part.'] = (matriz['Venta_N'] / v_v * 100) if v_v != 0 else 0

                    for clave_m in ['SMART', 'X-VIEW', 'TABLET', 'LEVEL', 'CLOUD', 'MICROCASE']:
                        vta_m_c = (
                            df_v[df_v['Marca_Clean'].str.contains(clave_m, na=False)]
                            .groupby('Razón social')['Venta_N']
                            .sum()
                        )
                        matriz[f"{clave_m} %"] = (matriz['Razón social'].map(vta_m_c).fillna(0) / matriz['Venta_N']) * 100

                    def highlight_10(s):
                        # pinta en rojo si % Part. > 10
                        if s.name != '% Part.':
                            return [''] * len(s)
                        return ['background-color: #ffcccc' if v > 10 else '' for v in s]

                    st.dataframe(
                        matriz.sort_values('Venta_N', ascending=False).style.format({
                            'Venta_N': '$ {:,.0f}',
                            '% Part.': '{:.2f}%',
                            'SMART %': '{:.1f}%',
                            'X-VIEW %': '{:.1f}%',
                            'TABLET %': '{:.1f}%',
                            'LEVEL %': '{:.1f}%',
                            'CLOUD %': '{:.1f}%',
                            'MICROCASE %': '{:.1f}%'
                        }).apply(highlight_10, axis=0),
                        use_container_width=True
                    )

                    st.divider()

    with tab_ia:
        st.header("🤖 Consultor Estratégico")

        # (Recomendado) En producción, guardá esto en Secrets y usá:
        # key = st.secrets.get("GEMINI_API_KEY", "")
        # Acá lo dejamos como input para que pruebes rápido.
        key = st.text_input("Gemini API Key:", type="password", key="gemini_api_key")
        pregunta = st.text_input("Haz una pregunta a tus datos:")

        if pregunta and key:
            try:
                # Cliente nuevo del SDK Google GenAI
                client = genai.Client(api_key=key)

                # Resumen compacto para la IA
                v_total = df['Venta_N'].sum()
                costo_total = df['Costo_N'].sum()
                renta_g = ((v_total - costo_total) / v_total * 100) if v_total != 0 else 0
                top_vendedores = df.groupby('Vendedor_Clean')['Venta_N'].sum().nlargest(5).to_dict()

                contexto = f"""
Resumen de ventas:
- Venta Total: $ {v_total:,.0f}
- Margen General: {renta_g:.2f}%
- Top 5 Vendedores (Venta): {top_vendedores}
- Total Clientes Únicos: {df['Razón social'].nunique()}
"""

                prompt = (
                    f"{contexto}\n"
                    f"Pregunta: {pregunta}\n\n"
                    "Responde de forma ejecutiva y profesional. "
                    "Si faltan datos para responder (por ejemplo, no hay fecha/mes en el dataset), "
                    "pedí exactamente qué columna o filtro necesitás."
                )

                with st.spinner("Analizando información comercial..."):
                    # Alias recomendado para evitar quilombos de naming/versionado
                    resp = client.models.generate_content(
                        model="gemini-flash-latest",
                        contents=prompt
                    )

                st.success("Análisis de la IA:")
                st.write(resp.text)

            except Exception as e:
                st.error("Ocurrió un error al consultar la IA.")
                st.warning(f"Detalle técnico: {e}")
                st.info(
                    "Tip: asegurate de haber cambiado requirements.txt a usar `google-genai` "
                    "y de haber redeployado la app en Streamlit."
                )

else:
    st.info("Por favor, carga el archivo CSV para comenzar el análisis.")
