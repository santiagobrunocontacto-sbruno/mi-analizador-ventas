import re
import unicodedata
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# NUEVO SDK (reemplaza google-generativeai)
from google import genai

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Tablero Comercial", layout="wide")
sns.set_theme(style="whitegrid")


# =========================
# UTILIDADES
# =========================
MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12
}

def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"\s+", " ", s)
    return s

def month_year_from_question(q: str):
    """
    Devuelve (month:int|None, year:int|None) si encuentra algo como:
    - 'enero', 'enero 2025', 'en enero', 'ene', 'enero/2025' (simple)
    - '2025' solo
    """
    qn = normalize_text(q)

    # año (20xx) si aparece
    year = None
    m_year = re.search(r"\b(20\d{2})\b", qn)
    if m_year:
        year = int(m_year.group(1))

    # mes por nombre
    month = None
    for nombre, num in MESES.items():
        if re.search(rf"\b{re.escape(nombre)}\b", qn):
            month = num
            break

    # abreviaturas comunes (ene, feb, mar, abr, may, jun, jul, ago, sep, oct, nov, dic)
    if month is None:
        abbr = {
            "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
            "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12
        }
        for a, num in abbr.items():
            if re.search(rf"\b{a}\b", qn):
                month = num
                break

    return month, year


# =========================
# LIMPIEZA / CARGA
# =========================
def auditoria_numerica(valor):
    """
    Limpia valores con $ / espacios / separadores AR/US y devuelve float.
    Soporta negativos y strings con % si llegaran.
    """
    if pd.isna(valor):
        return 0.0

    s = str(valor).strip()
    if not s:
        return 0.0

    # eliminar símbolos
    s = s.replace("$", "").replace(" ", "").replace("\u00a0", "")
    s = s.replace("%", "")

    # Manejo de separadores típicos:
    # 1.234,56  -> 1234.56
    # 1234,56   -> 1234.56
    # 1.234.567 -> 1234567
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    elif s.count(".") > 1:
        s = s.replace(".", "")

    try:
        return float(s)
    except Exception:
        return 0.0


@st.cache_data
def cargar_limpio(file):
    df = pd.read_csv(file, sep=";", encoding="latin-1")
    df.columns = df.columns.str.strip()

    # numéricos
    df["Venta_N"] = df["Venta"].apply(auditoria_numerica)
    df["Costo_N"] = df["Costo Total"].apply(auditoria_numerica)
    df["Cantidad_N"] = pd.to_numeric(df["Cantidad"], errors="coerce").fillna(0).astype(int)

    # si existen columnas de RTA, las limpiamos también (por si querés usarlas)
    if "RTA" in df.columns:
        df["RTA_N"] = df["RTA"].apply(auditoria_numerica)
    else:
        df["RTA_N"] = df["Venta_N"] - df["Costo_N"]

    if "RTA %" in df.columns:
        df["RTA_PCT_N"] = df["RTA %"].apply(auditoria_numerica)  # ya viene en porcentaje (ej 35.08)
    else:
        # margen % calculado
        df["RTA_PCT_N"] = df.apply(lambda r: ((r["Venta_N"] - r["Costo_N"]) / r["Venta_N"] * 100) if r["Venta_N"] else 0.0, axis=1)

    # limpieza de textos
    df["Vendedor_Clean"] = df["Nombre Vendedor"].astype(str).str.upper().str.strip()
    df["Marca_Clean"] = df["Marca"].astype(str).str.upper().str.strip()
    df["Cat_Clean"] = df["Categoria"].astype(str).str.upper().str.strip()

    # fecha (tu archivo trae "Fecha de emisión" como d/m/yyyy)
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
# MÉTRICAS DETERMINÍSTICAS (PYTHON)
# =========================
def vendor_metrics(df_base: pd.DataFrame, month: int | None = None, year: int | None = None) -> pd.DataFrame:
    df = df_base.copy()

    if month is not None and "Mes" in df.columns:
        df = df[df["Mes"] == month]
    if year is not None and "Año" in df.columns:
        df = df[df["Año"] == year]

    # agregados por vendedor
    g = df.groupby("Vendedor_Clean", dropna=False).agg(
        Venta=("Venta_N", "sum"),
        Costo=("Costo_N", "sum"),
        Unidades=("Cantidad_N", "sum"),
        Clientes=("Razón social", "nunique"),
    ).reset_index()

    g["Ganancia"] = g["Venta"] - g["Costo"]
    g["Margen_%"] = g.apply(lambda r: (r["Ganancia"] / r["Venta"] * 100) if r["Venta"] else 0.0, axis=1)

    # ordenar
    g = g.sort_values("Venta", ascending=False)
    return g


def responder_deterministico(pregunta: str, df: pd.DataFrame) -> str | None:
    """
    Respuestas exactas para preguntas típicas.
    Si matchea, devuelve texto listo para mostrar.
    Si no, devuelve None y dejamos que Gemini responda.
    """
    qn = normalize_text(pregunta)
    month, year = month_year_from_question(pregunta)

    # helpers de texto para período
    periodo_txt = ""
    if month or year:
        parts = []
        if month:
            nombre_mes = [k for k, v in MESES.items() if v == month and len(k) > 3][0]
            parts.append(nombre_mes.capitalize())
        if year:
            parts.append(str(year))
        periodo_txt = " (" + " ".join(parts) + ")"

    # 1) "vendedor con mas margen" / "mejor margen" / "mas rentable"
    if ("vendedor" in qn and ("margen" in qn or "renta" in qn or "rentable" in qn)) or ("mejor margen" in qn) or ("mas rentable" in qn):
        met = vendor_metrics(df, month=month, year=year)
        if met.empty:
            return f"No encontré datos para calcular margen por vendedor{periodo_txt}."
        top = met.sort_values("Margen_%", ascending=False).head(5)

        ganador = top.iloc[0]
        txt = (
            f"📌 **Vendedor con mayor margen %{periodo_txt}:** **{ganador['Vendedor_Clean']}**\n\n"
            f"- Margen: **{ganador['Margen_%']:.2f}%**\n"
            f"- Venta: **$ {ganador['Venta']:,.0f}**\n"
            f"- Ganancia: **$ {ganador['Ganancia']:,.0f}**\n"
            f"- Clientes: **{int(ganador['Clientes']):,}**\n\n"
            f"**Top 5 por margen %{periodo_txt}:**\n"
        )
        for _, r in top.iterrows():
            txt += f"- {r['Vendedor_Clean']}: {r['Margen_%']:.2f}% (Venta $ {r['Venta']:,.0f})\n"
        return txt

    # 2) "quien facturo mas" / "vendedor que mas facturo" / "mayor venta"
    if ("factur" in qn and "vendedor" in qn) or ("vendedor" in qn and ("mas vendio" in qn or "mayor venta" in qn or "mas venta" in qn)):
        met = vendor_metrics(df, month=month, year=year)
        if met.empty:
            return f"No encontré datos para calcular ventas por vendedor{periodo_txt}."
        top = met.sort_values("Venta", ascending=False).head(5)
        ganador = top.iloc[0]
        txt = (
            f"📌 **Vendedor con mayor facturación{periodo_txt}:** **{ganador['Vendedor_Clean']}**\n\n"
            f"- Venta: **$ {ganador['Venta']:,.0f}**\n"
            f"- Margen: **{ganador['Margen_%']:.2f}%**\n"
            f"- Ganancia: **$ {ganador['Ganancia']:,.0f}**\n\n"
            f"**Top 5 por facturación{periodo_txt}:**\n"
        )
        for _, r in top.iterrows():
            txt += f"- {r['Vendedor_Clean']}: $ {r['Venta']:,.0f} (Margen {r['Margen_%']:.2f}%)\n"
        return txt

    # 3) "clientes unicos" (global o por periodo)
    if "clientes unicos" in qn or ("cuantos clientes" in qn and "unicos" in qn):
        dff = df.copy()
        if month is not None and "Mes" in dff.columns:
            dff = dff[dff["Mes"] == month]
        if year is not None and "Año" in dff.columns:
            dff = dff[dff["Año"] == year]
        return f"👥 **Clientes únicos{periodo_txt}:** **{dff['Razón social'].nunique():,}**"

    return None


# =========================
# APP
# =========================
archivo = st.file_uploader("Cargar Base de Datos (CSV)", type=["csv"])

if archivo:
    df = cargar_limpio(archivo)

    # PESTAÑAS
    tab_reporte, tab_ia = st.tabs(["📊 Reporte Comercial", "🤖 Consultor IA"])

    with tab_reporte:
        # 1. RESUMEN GLOBAL
        v_total = df["Venta_N"].sum()
        costo_total = df["Costo_N"].sum()
        renta_g = ((v_total - costo_total) / v_total * 100) if v_total != 0 else 0

        st.header("1. Resumen Ejecutivo Global")
        st.markdown(f"### VENTA TOTAL: **$ {v_total:,.0f}**")

        c1, c2, c3 = st.columns(3)
        c1.metric("MARGEN RTA %", f"{renta_g:.2f} %")
        c2.metric("CLIENTES ÚNICOS", f"{df['Razón social'].nunique():,}")
        c3.metric("BULTOS TOTALES", f"{df['Cantidad_N'].sum():,}")

        st.subheader("📊 Facturación por Marca Foco")
        foco = ["SMART", "X-VIEW", "TABLET", "CLOUD", "LEVEL", "MICROCASE", "TERRA"]
        vtas_foco = [df[df["Marca_Clean"].str.contains(m, na=False)]["Venta_N"].sum() for m in foco]

        fig_m, ax_m = plt.subplots(figsize=(10, 3))
        sns.barplot(x=foco, y=vtas_foco, palette="Blues_r", ax=ax_m)
        ax_m.ticklabel_format(style="plain", axis="y")
        st.pyplot(fig_m)

        st.divider()

        # 2. SECCIÓN VENDEDORES (MANTENEMOS TU LÓGICA)
        vendedores = [
            "PABLO LOPEZ", "WALTER ABBAS", "FRANCISCO TEDIN", "OSMAR GRIGERA",
            "ALEJANDRO CHALIN", "FRANCO ABALLAY", "HORACIO GUSTAVO PÉREZ KOHUT",
            "LUIS RITUCCI", "NICOLAS PACCE", "NATALIA MONFORT"
        ]

        for vend in vendedores:
            df_v = df[df["Vendedor_Clean"].str.contains(vend, na=False)].copy()

            if not df_v.empty:
                v_v = df_v["Venta_N"].sum()
                c_v = df_v["Costo_N"].sum()
                r_v = ((v_v - c_v) / v_v * 100) if v_v != 0 else 0
                cant_clientes = df_v["Razón social"].nunique()

                with st.expander(f"DASHBOARD: {vend}", expanded=(vend == "PABLO LOPEZ")):
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
                        m_v = df_v.groupby("Marca_Clean")["Venta_N"].sum().nlargest(6)
                        fig_p, ax_p = plt.subplots()
                        ax_p.pie(
                            m_v,
                            labels=m_v.index,
                            autopct="%1.1f%%",
                            startangle=90,
                            colors=sns.color_palette("viridis")
                        )
                        st.pyplot(fig_p)

                    with col_r:
                        st.subheader("Ranking Categorías")
                        rank_cat = (
                            df_v.groupby("Cat_Clean")
                            .agg({"Venta_N": "sum", "Cantidad_N": "sum"})
                            .sort_values("Venta_N", ascending=False)
                            .head(10)
                        )
                        st.dataframe(
                            rank_cat.style.format({"Venta_N": "$ {:,.0f}", "Cantidad_N": "{:,}"}),
                            use_container_width=True
                        )

                    st.subheader("Matriz de Clientes y Mix de Marcas")
                    matriz = df_v.groupby("Razón social").agg({"Venta_N": "sum"}).reset_index()
                    matriz["% Part."] = (matriz["Venta_N"] / v_v * 100) if v_v != 0 else 0

                    for clave_m in ["SMART", "X-VIEW", "TABLET", "LEVEL", "CLOUD", "MICROCASE"]:
                        vta_m_c = (
                            df_v[df_v["Marca_Clean"].str.contains(clave_m, na=False)]
                            .groupby("Razón social")["Venta_N"]
                            .sum()
                        )
                        matriz[f"{clave_m} %"] = (matriz["Razón social"].map(vta_m_c).fillna(0) / matriz["Venta_N"]) * 100

                    def highlight_10(s):
                        if s.name != "% Part.":
                            return [""] * len(s)
                        return ["background-color: #ffcccc" if v > 10 else "" for v in s]

                    st.dataframe(
                        matriz.sort_values("Venta_N", ascending=False).style.format({
                            "Venta_N": "$ {:,.0f}",
                            "% Part.": "{:.2f}%",
                            "SMART %": "{:.1f}%",
                            "X-VIEW %": "{:.1f}%",
                            "TABLET %": "{:.1f}%",
                            "LEVEL %": "{:.1f}%",
                            "CLOUD %": "{:.1f}%",
                            "MICROCASE %": "{:.1f}%"
                        }).apply(highlight_10, axis=0),
                        use_container_width=True
                    )

                    st.divider()

    with tab_ia:
        st.header("🤖 Consultor Estratégico (Python + IA)")

        # Para producción: guardalo en Secrets y usá:
        # key = st.secrets.get("GEMINI_API_KEY", "")
        key = st.text_input("Gemini API Key:", type="password", key="gemini_api_key")

        pregunta = st.text_input("Haz una pregunta a tus datos:")

        if pregunta:
            # 1) Intento determinístico (exacto) con Python
            respuesta_exacta = responder_deterministico(pregunta, df)
            if respuesta_exacta:
                st.success("Respuesta (cálculo exacto):")
                st.markdown(respuesta_exacta)
            else:
                # 2) Si no matchea a consulta típica, usamos IA como consultor/redactor
                if not key:
                    st.info("Ingresá tu Gemini API Key para habilitar el consultor IA en consultas abiertas.")
                else:
                    try:
                        client = genai.Client(api_key=key)

                        v_total = df["Venta_N"].sum()
                        costo_total = df["Costo_N"].sum()
                        renta_g = ((v_total - costo_total) / v_total * 100) if v_total != 0 else 0

                        # Contexto mejorado (incluye margen por vendedor top 5)
                        met = vendor_metrics(df)
                        top5_venta = met.sort_values("Venta", ascending=False).head(5)[["Vendedor_Clean", "Venta", "Margen_%"]]
                        top5_margen = met.sort_values("Margen_%", ascending=False).head(5)[["Vendedor_Clean", "Margen_%", "Venta"]]

                        contexto = f"""
Resumen:
- Venta Total: $ {v_total:,.0f}
- Margen General: {renta_g:.2f}%
- Clientes Únicos: {df['Razón social'].nunique():,}
- Filas: {len(df):,}

Top 5 vendedores por Venta (Venta, Margen%):
{top5_venta.to_string(index=False)}

Top 5 vendedores por Margen% (Margen%, Venta):
{top5_margen.to_string(index=False)}

Columnas disponibles:
{', '.join(df.columns)}
"""

                        prompt = (
                            f"{contexto}\n\n"
                            f"Pregunta del usuario: {pregunta}\n\n"
                            "Instrucciones:\n"
                            "- Responde en español argentino.\n"
                            "- Si la pregunta requiere un cálculo específico que no se incluye en el contexto, explicá qué dato faltó.\n"
                            "- Si podés responder con lo disponible, hacelo de forma ejecutiva.\n"
                        )

                        with st.spinner("Analizando información comercial..."):
                            resp = client.models.generate_content(
                                model="gemini-flash-latest",
                                contents=prompt
                            )

                        st.success("Análisis de la IA:")
                        st.write(resp.text)

                    except Exception as e:
                        st.error("Ocurrió un error al consultar la IA.")
                        st.warning(f"Detalle técnico: {e}")
                        st.info("Tip: asegurate de usar `google-genai` en requirements.txt y redeployar en Streamlit.")

else:
    st.info("Por favor, carga el archivo CSV para comenzar el análisis.")
