import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Reporte Gerencial", layout="wide")

# Función para limpiar números (maneja puntos y comas)
def limpiar_numero(valor):
    if isinstance(valor, str):
        valor = valor.replace('.', '').replace(',', '.')
    return pd.to_numeric(valor, errors='coerce')

# --- PROCESAMIENTO ---
@st.cache_data
def procesar_archivo(file):
    try:
        # Cargamos con separador ; que es el de tu archivo
        df = pd.read_csv(file, sep=';', encoding='latin-1')
        df.columns = df.columns.str.strip()
        
        # Convertimos columnas clave
        df['Venta_N'] = limpiar_numero(df['Venta'])
        df['RTA_N'] = limpiar_numero(df['RTA'])
        df['Costo_N'] = limpiar_numero(df['Costo Total'])
        df['Cantidad_N'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
        
        # Fechas
        df['Fecha_DT'] = pd.to_datetime(df['Fecha de emisión'], dayfirst=True, errors='coerce')
        df['Mes_Año'] = df['Fecha_DT'].dt.strftime('%Y-%m')
        
        return df, None
    except Exception as e:
        return None, f"Error al procesar: {e}"

# --- FUNCIÓN PDF ---
def generar_pdf(stats):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="INFORME DE GESTIÓN COMERCIAL", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Resumen Ejecutivo:", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 10, txt=f"- Facturacion Total: {stats['total_v']}", ln=True)
    pdf.cell(200, 10, txt=f"- Rentabilidad Total (RTA): {stats['total_rta']}", ln=True)
    pdf.cell(200, 10, txt=f"- Margen Promedio: {stats['margen_p']}%", ln=True)
    pdf.cell(200, 10, txt=f"- Total Operaciones: {stats['ops']}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Top 5 Marcas:", ln=True)
    pdf.set_font("Arial", size=11)
    for marca, vta in stats['top_marcas'].items():
        pdf.cell(200, 8, txt=f"  * {marca}: ${vta:,.2f}", ln=True)

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
st.title("📈 Tablero de Comando Gerencial")
uploaded_file = st.file_uploader("Cargar archivo 'fac limpia.csv'", type=["csv"])

if uploaded_file:
    df, error = procesar_archivo(uploaded_file)
    
    if error:
        st.error(error)
    else:
        # CÁLCULOS (El 90% de tus dudas mensuales)
        total_v = df['Venta_N'].sum()
        total_rta = df['RTA_N'].sum()
        margen_avg = (total_rta / total_v * 100) if total_v != 0 else 0
        ops = len(df)
        
        # RANKINGS
        vendedores = df.groupby('Nombre Vendedor')['Venta_N'].sum().nlargest(10)
        marcas = df.groupby('Marca')['Venta_N'].sum().nlargest(10)
        clientes = df.groupby('Razón social')['Venta_N'].sum().nlargest(10)
        categorias = df.groupby('Categoria')['Venta_N'].sum().nlargest(10)

        # MÉTRICAS PRINCIPALES
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("VENTAS TOTALES", f"${total_v:,.0f}")
        c2.metric("RTA (Ganancia)", f"${total_rta:,.0f}")
        c3.metric("MARGEN %", f"{margen_avg:.1f}%")
        c4.metric("OPERACIONES", f"{ops:,}")

        st.divider()

        # GRÁFICOS
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("🏆 Top Vendedores")
            st.bar_chart(vendedores)
            
            st.subheader("🏬 Ventas por Marca")
            st.bar_chart(marcas)

        with col_b:
            st.subheader("📂 Ventas por Categoría")
            st.bar_chart(categorias)
            
            st.subheader("👥 Clientes VIP (Top 10)")
            st.dataframe(clientes, use_container_width=True)

        # BOTÓN PDF
        st.divider()
        stats_pdf = {
            'total_v': f"${total_v:,.2f}",
            'total_rta': f"${total_rta:,.2f}",
            'margen_p': f"{margen_avg:.1f}",
            'ops': f"{ops}",
            'top_marcas': marcas.head(5).to_dict()
        }
        
        if st.button("📥 Descargar Reporte PDF"):
            try:
                pdf_data = generar_pdf(stats_pdf)
                b64 = base64.b64encode(pdf_data).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="Reporte_Ventas_{datetime.now().strftime("%Y%m%d")}.pdf">Click aquí para descargar el PDF</a>'
                st.markdown(href, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error al generar PDF: {e}. Probablemente falte la librería 'fpdf'.")

else:
    st.info("👋 Santiago, subí el archivo para ver el análisis completo.")
