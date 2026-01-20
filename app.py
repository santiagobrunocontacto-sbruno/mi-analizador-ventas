import re
import json
import unicodedata

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from google import genai

# =========================
# CONFIGURACIÓN DE PÁGINA
# =========================
st.set_page_config(page_title="Tablero Comercial", layout="wide")
sns.set_theme(style="whitegrid")

# =========================
# LIMPIEZA NUMÉRICA (TU LÓGICA)
# =========================
def auditoria_numerica(valor):
    if pd.isna(valor):
        return 0.0
    s = str(valor).strip().replace("$", "").replace(" ", "").replace("\u00a0", "")
    if not s:
        return 0.0

    # AR: 1.234,56 -> 1234.56
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    elif s.count(".") > 1:
        s = s.replace(".", "")

    try:
        return float(s)
    except:
        return 0.0


@st.cache_data
def cargar_limpio(file):
    df = pd.read_csv(file, sep=";", encoding="latin-1")
    df.columns = df.columns.str.strip()

    # Numéricos
    df["Venta_N"] = df["Venta"].apply(auditoria_numerica)
    df["Costo_N"] = df["Costo Total"].apply(auditoria_numerica)
    df["Cantidad_N"] = pd.to_numeric(df["Cantidad"], errors="coerce").fillna(0).astype(int)

    # Textos
    df["Vendedor_Clean"] = df["Nombre Vendedor"].astype(str).str.upper().str.strip()
    df["Marca_Clean"] = df["Marca"].astype(str).str.upper().str.strip()
    df["Cat_Clean"] = df["Categoria"].astype(str).str.upper().str.strip()

    # Fecha (si existe)
    if "Fecha de emisión" in df.columns:
        df["Fecha_dt"] = pd.to_datetime(df["Fecha de emisión"], dayfirst=True, errors="coerce")
        df["Año"] = df["Fecha_dt"].dt.year
        df["Mes"] = df["Fecha_dt"].dt.month
    else:
        df["Fecha_dt"] = pd.NaT
        df["Año"] = None
        df["Mes"] = None

    return df


# =========================
# CONSULTOR IA (IA→JSON / Python calcula)
# =========================
MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9,
    "octubre": 10, "noviembre": 11, "diciembre": 12
}

def normalize_text(s: str) -> str:
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"\s+", " ", s)
    return s

def extract_json(text: str) -> str:
    """Intenta rescatar el primer objeto JSON {...} del texto."""
    text = (text or "").strip().replace("```json", "").replace("```", "").strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    return m.group(0) if m else text

def build_query_from_llm(client, pregunta: str, df: pd.DataFrame) -> dict:
    cols = ", ".join(df.columns)

    prompt = f"""
Sos un analista que traduce preguntas comerciales a una consulta JSON.
Devolvé EXCLUSIVAMENTE un JSON válido (sin texto adicional).

Columnas disponibles: {cols}

Estructura esperada:
{{
  "metric": "sales" | "profit" | "margin_pct" | "units" | "clients",
  "group_by": "vendedor" | "marca" | "categoria" | "cliente" | "none",
  "filters": {{
      "month": 1-12 | null,
      "year": 2000-2100 | null,
      "vendedor_contains": string | null,
      "marca_contains": string | null,
      "categoria_contains": string | null,
      "cliente_contains": string | null
  }},
  "sort": {{"by": "sales" | "profit" | "margin_pct" | "units" | "clients", "order": "asc" | "desc"}},
  "limit": integer
}}

Reglas:
- sales = suma Venta_N
- profit = suma (Venta_N - Costo_N)
- margin_pct = profit / sales * 100
- units = suma Cantidad_N
- clients = clientes únicos (Razón social)
- Si preguntan "¿cuánto vendí en total?" => group_by = "none" y metric="sales"
- Si preguntan "¿quién?" o "top" => group_by distinto de none y sort desc.

Pregunta del usuario: {pregunta}
"""

    resp = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt
    )
    raw = extract_json(resp.text)
    return json.loads(raw)

def execute_query(df: pd.DataFrame, q: dict) -> pd.DataFrame:
    dff = df.copy()
    filters = q.get("filters") or {}

    # filtros fecha
    month = filters.get("month")
    year = filters.get("year")
    if month and "Mes" in dff.columns:
        dff = dff[dff["Mes"] == int(month)]
    if year and "Año" in dff.columns:
        dff = dff[dff["Año"] == int(year)]

    # filtros contains
    def apply_contains(col, key):
        val = filters.get(key)
        if val and col in dff.columns:
            mask = dff[col].astype(str).str.upper().str.contains(str(val).upper(), na=False)
            return dff[mask]
        return dff

    dff = apply_contains("Vendedor_Clean", "vendedor_contains")
    dff = apply_contains("Marca_Clean", "marca_contains")
    dff = apply_contains("Cat_Clean", "categoria_contains")
    dff = apply_contains("Razón social", "cliente_contains")

    if dff.empty:
        return pd.DataFrame()

    metric = q.get("metric", "sales")
    group_by = q.get("group_by", "none")

    # Totales
    if group_by == "none":
        sales = float(dff["Venta_N"].sum())
        cost = float(dff["Costo_N"].sum())
        units = int(dff["Cantidad_N"].sum())
        clients = int(dff["Razón social"].nunique())
        profit = sales - cost
        margin_pct = (profit / sales * 100) if sales else 0.0
        return pd.DataFrame([{
            "sales": sales,
            "profit": profit,
            "margin_pct": margin_pct,
            "units": units,
            "clients": clients
        }])

    gb_map = {
        "vendedor": "Vendedor_Clean",
        "marca": "Marca_Clean",
        "categoria": "Cat_Clean",
        "cliente": "Razón social"
    }
    gb_col = gb_map.get(group_by, "Vendedor_Clean")

    agg = dff.groupby(gb_col).agg(
        sales=("Venta_N", "sum"),
        cost=("Costo_N", "sum"),
        units=("Cantidad_N", "sum"),
        clients=("Razón social", "nunique"),
    ).reset_index()

    agg["profit"] = agg["sales"] - agg["cost"]
    agg["margin_pct"] = agg.apply(lambda r: (r["profit"] / r["sales"] * 100) if r["sales"] else 0.0, axis=1)

    sort = q.get("sort") or {}
    by = sort.get("by", metric if metric in agg.columns else "sales")
    order = sort.get("order", "desc")
    asc = (order == "asc")

    if by in agg.columns:
        agg = agg.sort_values(by, ascending=asc)

    limit = int(q.get("limit", 10))
    agg = agg.head(limit).rename(columns={gb_col: "grupo"})
    return agg

def format_answer(pregunta: str, q: dict, result: pd.DataFrame) -> str:
    if result.empty:
        return "No hay datos para esa consulta (revisá filtros o términos)."

    metric = q.get("metric", "sales")
    group_by = q.get("group_by", "none")

    metric_label = {
        "sales": "Venta",
        "profit": "Ganancia",
        "margin_pct": "Margen %",
        "units": "Unidades",
        "clients": "Clientes únicos"
    }.get(metric, metric)

    if group_by == "none":
        r = result.iloc[0]
        return (
            f"**Pregunta:** {pregunta}\n\n"
            f"- Venta: **$ {r['sales']:,.0f}**\n"
            f"- Ganancia: **$ {r['profit']:,.0f}**\n"
            f"- Margen: **{r['margin_pct']:.2f}%**\n"
            f"- Unidades: **{int(r['units']):,}**\n"
            f"- Clientes únicos: **{int(r['clients']):,}**\n"
        )

    top = result.iloc[0]
    val = top[metric] if metric in top.index else None
    if metric == "margin_pct":
        val_fmt = f"{float(val):.2f}%"
    elif metric in ["sales", "profit"]:
        val_fmt = f"$ {float(val):,.0f}"
    else:
        val_fmt = f"{int(val):,}"

    return f"📌 **Top 1 por {metric_label}:** **{top['grupo']}** → **{val_fmt}**"


# =========================
# APP
# =========================
archivo = st.file_uploader("Cargar Base de Datos (CSV)", type=["csv"])

if archivo:
    df = cargar_limpio(archivo)

    # PESTAÑAS
    tab_reporte, tab_ia = st.tabs(["📊 Reporte Comercial", "🤖 Consultor IA"])

    # -------------------------
    # REPORTE (TU REPORTE ORIGINAL, SIN ROMPER)
    # -------------------------
    with tab_reporte:
        v_total = df["Venta_N"].sum()
        renta_g = ((v_total - df["Costo_N"].sum()) / v_total * 100) if v_total != 0 else 0

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

        vendedores = [
            "PABLO LOPEZ", "WALTER ABBAS", "FRANCISCO TEDIN", "OSMAR GRIGERA",
            "ALEJANDRO CHALIN", "FRANCO ABALLAY", "HORACIO GUSTAVO PÉREZ KOHUT",
            "LUIS RITUCCI", "NICOLAS PACCE", "NATALIA MONFORT"
        ]

        for vend in vendedores:
            df_v = df[df['Vendedor_Clean'].str.contains(vend, na=False)].copy()
            if not df_v.empty:
                v_v = df_v['Venta_N'].sum()
                r_v = ((v_v - df_v['Costo_N'].sum()) / v_v * 100) if v_v != 0 else 0
                cant_clientes = df_v['Razón social'].nunique()

                with st.expander(f"DASHBOARD: {vend}", expanded=(vend == "PABLO LOPEZ")):
                    st.markdown(f"""
                    <div style="background-color:#002147; padding:20px; border-radius:10px; color:white; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px">
                        <span style="font-size:24px; font-weight:bold">{vend}</span>
                        <span style="font-size:28px; font-weight:bold">$ {v_v:,.0f}</span>
                        <div style="text-align:right"><span style="font-size:14px">CLIENTES</span><br><span style="font-size:20px; font-weight:bold">{cant_clientes}</span></div>
                        <div style="text-align:right"><span style="font-size:14px">RENTA</span><br><span style="font-size:20px; font-weight:bold">{r_v:.2f}%</span></div>
                    </div>""", unsafe_allow_html=True)

                    col_l, col_r = st.columns([1, 1.2])

                    with col_l:
                        st.subheader("Venta por Marca")
                        m_v = df_v.groupby('Marca_Clean')['Venta_N'].sum().nlargest(6)
                        fig_p, ax_p = plt.subplots()
                        ax_p.pie(m_v, labels=m_v.index, autopct='%1.1f%%', startangle=90,
                                colors=sns.color_palette("viridis"))
                        st.pyplot(fig_p)

                    with col_r:
                        st.subheader("Ranking Categorías")
                        rank_cat = df_v.groupby('Cat_Clean').agg({'Venta_N': 'sum', 'Cantidad_N': 'sum'}) \
                            .sort_values('Venta_N', ascending=False).head(10)
                        st.dataframe(rank_cat.style.format({'Venta_N': '$ {:,.0f}', 'Cantidad_N': '{:,}'}), use_container_width=True)

                    st.subheader("Matriz de Clientes y Mix de Marcas")
                    matriz = df_v.groupby('Razón social').agg({'Venta_N': 'sum'}).reset_index()
                    matriz['% Part.'] = (matriz['Venta_N'] / v_v * 100) if v_v else 0

                    for clave_m in ['SMART', 'X-VIEW', 'TABLET', 'LEVEL', 'CLOUD', 'MICROCASE']:
                        vta_m_c = df_v[df_v['Marca_Clean'].str.contains(clave_m, na=False)] \
                            .groupby('Razón social')['Venta_N'].sum()
                        matriz[f"{clave_m} %"] = (matriz['Razón social'].map(vta_m_c).fillna(0) / matriz['Venta_N']) * 100

                    def highlight_10(s):
                        if s.name != '% Part.':
                            return [''] * len(s)
                        return ['background-color: #ffcccc' if v > 10 else '' for v in s]

                    st.dataframe(
                        matriz.sort_values('Venta_N', ascending=False).style.format({
                            'Venta_N': '$ {:,.0f}', '% Part.': '{:.2f}%',
                            'SMART %': '{:.1f}%', 'X-VIEW %': '{:.1f}%', 'TABLET %': '{:.1f}%',
                            'LEVEL %': '{:.1f}%', 'CLOUD %': '{:.1f}%', 'MICROCASE %': '{:.1f}%'
                        }).apply(highlight_10, axis=0),
                        use_container_width=True
                    )

                    st.divider()

    # -------------------------
    # CONSULTOR IA (SIN MANUAL)
    # -------------------------
    with tab_ia:
        st.header("🤖 Consultor Comercial Inteligente (sin manual)")

        key = st.text_input("Gemini API Key:", type="password", key="gemini_api_key")
        pregunta = st.text_input("Escribí cualquier pregunta comercial:")

        if pregunta:
            if not key:
                st.info("Ingresá tu API Key para usar el consultor.")
            else:
                try:
                    client = genai.Client(api_key=key)

                    with st.spinner("Interpretando la pregunta..."):
                        q = build_query_from_llm(client, pregunta, df)

                    with st.spinner("Calculando resultados..."):
                        result = execute_query(df, q)

                    st.success("Resultado (exacto):")
                    st.markdown(format_answer(pregunta, q, result))
                    st.dataframe(result, use_container_width=True)

                    with st.expander("Consulta interpretada (debug)"):
                        st.json(q)

                except Exception as e:
                    st.error("Error interpretando o ejecutando la consulta.")
                    st.warning(f"Detalle técnico: {e}")
else:
    st.info("Por favor, carga el archivo CSV para comenzar el análisis.")
