import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64

# CONFIGURACIÓN
st.set_page_config(page_title="Reporte Gerencial Pro", layout="wide")

# --- FUNCIONES DE CÁLCULO ---
def procesar_datos(df):
    df.columns = df.columns.str.strip()
    # Limpieza de números
    df['Venta_Real'] = pd.to_numeric(df['Venta'], errors='coerce').fillna(0)
    df['RTA_Real'] = pd.to_numeric(df['RTA'], errors='coerce').fillna(0)
    
    # Procesar fechas
    if 'Fecha de emisión' in df.columns:
        df['Fecha_DT'] = pd.to_datetime(df['Fecha de emisión'], dayfirst=True, errors='coerce')
        df['Mes'] = df['Fecha_DT'].dt.strftime('%Y-%m')
    return df

def crear_pdf(resumen):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="REPORTE GERENCIAL DE VENTAS", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for k, v in resumen.items():
        pdf.cell(200, 10, txt=f"{k}: {v}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
st.title("📊 Tablero de Comando Mensual")
uploaded_file = st.file_uploader("Subí tu archivo 'fac limpia.csv'", type=["csv"])

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')
    df = procesar_datos(df_raw)
    
    # --- CÁLCULOS AUTOMÁTICOS ---
    total_v = df['Venta_Real'].sum()
    total_rta = df['RTA_Real'].sum()
    ops = len(df)
    vendedores = df.groupby('Nombre Vendedor')['Venta_N'].sum().nlargest(10) if 'Nombre Vendedor' in df.columns else None
    marcas = df.groupby('Marca')['Venta_Real'].sum().nlargest(10) if 'Marca' in df.columns else None
    clientes = df.groupby('Razón social')['Venta_Real'].sum().nlargest(10) if 'Razón social' in df.columns else None

    # --- VISTA EN PANTALLA ---
    c1, c2, c3 = st.columns(3)
    c1.metric("FACTURACIÓN TOTAL", f"${total_v:,.2f}")
    c2.metric("RENTABILIDAD (RTA)", f"${total_rta:,.2f}")
    c3.metric("TICKET PROMEDIO", f"${(total_v/ops):,.2f}")

    st.write("---")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🏆 Top 10 Vendedores")
        st.bar_chart(vendedores)
        st.subheader("🏬 Top 10 Marcas")
        st.bar_chart(marcas)

    with col_b:
        st.subheader("👤 Top 10 Clientes")
        st.table(clientes)
        if 'Mes' in df.columns:
            st.subheader("📅 Evolución Mensual")
            st.line_chart(df.groupby('Mes')['Venta_Real'].sum())

    # --- BOTÓN DE PDF ---
    resumen_dict = {
        "Total Facturado": f"${total_v:,.2f}",
        "Rentabilidad": f"${total_rta:,.2f}",
        "Total Operaciones": f"{ops}",
        "Mejor Vendedor": f"{vendedores.index[0] if vendedores is not None else 'N/A'}"
    }
    
    if st.button("Generar Reporte PDF"):
        pdf_bytes = crear_pdf(resumen_dict)
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="reporte_ventas.pdf">Descargar PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

else:
    st.info("Subí el archivo para generar el reporte automático.")
