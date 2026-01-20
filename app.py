import re
import json
import unicodedata
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from google import genai

# =========================
# CONFIGURACIÓN GENERAL
# =========================
st.set_page_config(page_title="Tablero Comercial", layout="wide")
sns.set_theme(style="whitegrid")

# =========================
# UTILIDADES TEXTO
# =========================
MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9,
    "octubre": 10, "noviembre": 11, "diciembre": 12
}

def normalize_text(s):
    s = str(s).lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s)

def detect_month_year(text):
    t = normalize_text(text)
    month = None
    year = None

    for k, v in MESES.items():
        if k in t:
            month = v
            break

    m = re.search(r"\b(20\d{2})\b", t)
    if m:
        year = int(m.group(1))

    return month, year

# =========================
# LIMPIEZA NUMÉRICA
# =========================
def auditoria_numerica(valor):
    if pd.isna(valor):
        return 0.0
    s = str(valor).replace("$", "").replace(" ", "").replace("%", "")
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

# =========================
# CARGA Y PREPARACIÓN DATA
# =========================
@st.cache_data
def cargar_limpio(file):
    df = pd.read_csv(file, sep=";", encoding="latin-1")
    df.columns = df.columns.str.strip()

    df["Venta_N"] = df["Venta"].apply(auditoria_numerica)
    df["Costo_N"] = df["Costo Total"].apply(auditoria_numerica)
    df["Cantidad_N"] = pd.to_numeric(df["Cantidad"], errors="coerce").fillna(0).astype(int)

    df["Vendedor_Clean"] = df["Nombre Vendedor"].astype(str).str.upper().str.strip()
    df["Marca_Clean"] = df["Marca"].astype(str).str.upper().str.strip()
    df["Cat_Clean"] = df["Categoria"].astype(str).str.upper().str.strip()

    if "Fecha de emisión" in df.columns:
        df["Fecha_dt"] = pd.to_datetime(df["Fecha de emisión"], dayfirst=True, errors="coerce")
        df["Mes"] = df["Fecha_dt"].dt.month
        df["Año"] = df["Fecha_dt"].dt.year
    else:
        df["Mes"] = None
        df["Año"] = None

    return df

# =========================
# MOTOR DE CÁLCULO
# =========================
def ejecutar_consulta(df, query):
    dff = df.copy()

    f = query.get("filters", {})
    if f.get("month"):
        dff = dff[dff["Mes"] == f["month"]]
    if f.get("year"):
        dff = dff[dff["Año"] == f["year"]]

    for col, key in [
        ("Vendedor_Clean", "vendedor"),
        ("Marca_Clean", "marca"),
        ("Cat_Clean", "categoria"),
        ("Razón social", "cliente")
    ]:
        if f.get(key):
            dff = dff[dff[col].str.contains(f[key], na=False)]

    if dff.empty:
        return pd.DataFrame()

    group_map = {
        "vendedor": "Vendedor_Clean",
        "marca": "Marca_Clean",
        "categoria": "Cat_Clean",
        "cliente": "Razón social"
    }

    gb = group_map.get(query["group_by"])
    agg = dff.groupby(gb).agg(
        ventas=("Venta_N", "sum"),
        costo=("Costo_N", "sum"),
        unidades=("Cantidad_N", "sum"),
        clientes=("Razón social", "nunique")
    ).reset_index()

    agg["ganancia"] = agg["ventas"] - agg["costo"]
    agg["margen"] = agg.apply(lambda r: (r["ganancia"] / r["ventas"] * 100) if r["ventas"] else 0, axis=1)

    sort_by = query["sort"]["by"]
    asc = query["sort"]["order"] == "asc"
    agg = agg.sort_values(sort_by, ascending=asc)

    return agg.head(query["limit"])

# =========================
# IA → CONSULTA ESTRUCTURADA
# =========================
def interpretar_pregunta(client, pregunta):
    prompt = f"""
Convertí esta pregunta comercial en un JSON ESTRICTO.

Pregunta: {pregunta}

Formato:
{{
 "metric": "ventas | ganancia | margen | unidades | clientes",
 "group_by": "vendedor | marca | categoria | cliente",
 "filters": {{
    "month": null | 1-12,
    "year": null | 2024,
    "vendedor": null | string,
    "marca": null | string,
    "categoria": null | string,
    "cliente": null | string
 }},
 "sort": {{ "by": "ventas | ganancia | margen | unidades | clientes", "order": "desc" }},
 "limit": 5
}}

NO escribas texto fuera del JSON.
"""
    r = client.models.generate_content("gemini-flash-latest", prompt).text
    r = r.replace("```json", "").replace("```", "").strip()
    return json.loads(r)

# =========================
# APP
# =========================
archivo = st.file_uploader("Cargar Base de Datos (CSV)", type=["csv"])

if archivo:
    df = cargar_limpio(archivo)
    tab_rep, tab_ia = st.tabs(["📊 Reporte Comercial", "🤖 Consultor IA"])

    # =========================
    # REPORTE (NO SE TOCA)
    # =========================
    with tab_rep:
        v_total = df["Venta_N"].sum()
        margen = ((v_total - df["Costo_N"].sum()) / v_total * 100) if v_total else 0

        st.header("Resumen Ejecutivo")
        st.metric("Venta Total", f"$ {v_total:,.0f}")
        st.metric("Margen %", f"{margen:.2f}%")
        st.metric("Clientes", df["Razón social"].nunique())

    # =========================
    # CONSULTOR SIN MANUAL
    # =========================
    with tab_ia:
        st.header("🤖 Consultor Comercial Inteligente")

        key = st.text_input("Gemini API Key", type="password")
        pregunta = st.text_input("Escribí cualquier pregunta comercial:")

        if pregunta and key:
            try:
                client = genai.Client(api_key=key)
                query = interpretar_pregunta(client, pregunta)
                resultado = ejecutar_consulta(df, query)

                if resultado.empty:
                    st.warning("No hay datos para esa consulta.")
                else:
                    st.success("Resultado exacto")
                    st.dataframe(resultado, use_container_width=True)
                    with st.expander("Consulta interpretada (debug)"):
                        st.json(query)

            except Exception as e:
                st.error("Error interpretando la consulta")
                st.text(e)
else:
    st.info("Subí un archivo CSV para comenzar.")

