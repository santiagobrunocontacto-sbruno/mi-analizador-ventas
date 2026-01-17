import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import tempfile
import os

# CONFIGURACIÓN VISUAL
st.set_page_config(page_title="Informe Gerencial de Ventas", layout="centered")
sns.set_theme(style="whitegrid")

def limpiar_moneda(serie):
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)

@st.cache_data
def cargar_y_procesar(file):
    df = pd.read_csv(file, sep=';', encoding='latin-1')
    df.columns = df.columns.str.strip()
    df['Venta_N'] = limpiar_moneda(df['Venta'])
    df['RTA_N'] = limpiar_moneda(df['RTA'])
    df['Cantidad_N'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
    df['Fecha_DT'] = pd.to_datetime(df['Fecha de emisión'], dayfirst=True, errors='coerce')
    df['Mes'] = df['Fecha_DT'].dt.to_period('M').astype(str)
    return df

# --- INTERFAZ ---
st.title("🏛️ Informe Anual de Gestión Comercial")
st.markdown("---")

archivo = st.file_uploader("Cargar archivo de ventas", type=["csv"])

if archivo:
    df = cargar_y_procesar(archivo)
    meses_ordenados = sorted(df['Mes'].unique())

    # ==========================================
    # SECCIÓN 1: RESUMEN EJECUTIVO (KPIs)
    # ==========================================
    st.header("1. Resumen Ejecutivo")
    c1, c2, c3 = st.columns(3)
    total_vta = df['Venta_N'].sum()
    total_rta = df['RTA_N'].sum()
    c1.metric("Venta Total", f"${total_vta:,.0f}")
    c2.metric("Rentabilidad Total", f"${total_rta:,.0f}")
    c3.metric("Margen Promedio", f"{(total_rta/total_vta*100):.1f}%")

    # Gráfico de Evolución Mensual
    st.subheader("Evolución de Ventas y Rentabilidad")
    evol = df.groupby('Mes').agg({'Venta_N':'sum', 'RTA_N':'sum'})
    fig, ax = plt.subplots(figsize=(10, 4))
    evol.plot(kind='line', marker='o', ax=ax, color=['#1f77b4', '#ff7f0e'])
    plt.title("Venta vs RTA por Mes")
    st.pyplot(fig)

    st.markdown("---")

    # ==========================================
    # SECCIÓN 2: PERFORMANCE POR VENDEDOR
    # ==========================================
    st.header("2. Análisis por Equipo de Ventas")
    
    vendedores = df['Nombre Vendedor'].unique()
    for vend in vendedores:
        with st.container():
            st.subheader(f"👤 Vendedor: {vend}")
            df_v = df[df['Nombre Vendedor'] == vend]
            v_mes = df_v.groupby('Mes')['Venta_N'].sum().reindex(meses_ordenados, fill_value=0)
            
            # Cálculo de crecimiento
            v_crecimiento = v_mes.pct_change() * 100
            
            col_v1, col_v2 = st.columns([2, 1])
            with col_v1:
                fig_v, ax_v = plt.subplots(figsize=(8, 3))
                sns.barplot(x=v_mes.index, y=v_mes.values, palette="viridis", ax=ax_v)
                plt.xticks(rotation=45)
                st.pyplot(fig_v)
            
            with col_v2:
                ultimo_mes_v = v_mes.iloc[-1]
                crecimiento_v = v_crecimiento.iloc[-1]
                st.write(f"**Venta Último Mes:** ${ultimo_mes_v:,.0f}")
                color_c = "green" if crecimiento_v >= 0 else "red"
                st.markdown(f"**Crecimiento MoM:** :{color_c}[{crecimiento_v:.1f}%]")
            st.divider()

    # ==========================================
    # SECCIÓN 3: CATEGORÍAS Y PRODUCTOS
    # ==========================================
    st.header("3. Inteligencia de Producto")
    
    # Categoría más vendida por mes (unidades)
    st.subheader("📦 Líder de Ventas por Mes (En Unidades)")
    cat_mes = df.groupby(['Mes', 'Categoria'])['Cantidad_N'].sum().reset_index()
    lideres = cat_mes.loc[cat_mes.groupby('Mes')['Cantidad_N'].idxmax()]
    st.table(lideres)

    # Ticket promedio por categoría
    st.subheader("🎫 Ticket Promedio por Categoría")
    ticket_cat = df.groupby('Categoria').apply(lambda x: x['Venta_N'].sum() / len(x)).sort_values()
    fig_t, ax_t = plt.subplots(figsize=(10, 5))
    ticket_cat.plot(kind='barh', color='skyblue', ax=ax_t)
    st.pyplot(fig_t)

    # Productos con Mayor y Menor Rentabilidad
    st.subheader("💎 Auditoría de Rentabilidad (Margen %)")
    prod_perf = df.groupby('Descripción').agg({'Venta_N':'sum', 'RTA_N':'sum'})
    prod_perf['Margen_%'] = (prod_perf['RTA_N'] / prod_perf['Venta_N'] * 100)
    # Filtrar solo productos con ventas significativas
    prod_perf = prod_perf[prod_perf['Venta_N'] > (total_vta * 0.001)] 

    c_p1, c_p2 = st.columns(2)
    with c_p1:
        st.write("**Top 5 Mayor Margen**")
        st.dataframe(prod_perf.nlargest(5, 'Margen_%')[['Margen_%']])
    with c_p2:
        st.write("**Top 5 Menor Margen**")
        st.dataframe(prod_perf.nsmallest(5, 'Margen_%')[['Margen_%']])

    # ==========================================
    # SECCIÓN 4: EXPORTACIÓN PDF
    # ==========================================
    st.markdown("---")
    if st.button("🎨 Generar Informe PDF Profesional"):
        # Creamos el PDF con fpdf2
        pdf = FPDF()
        pdf.add_page()
        
        # Encabezado
        pdf.set_fill_color(31, 119, 180)
        pdf.rect(0, 0, 210, 40, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 24)
        pdf.cell(0, 20, "REPORTE COMERCIAL", ln=True, align='C')
        
        # Contenido
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 14)
        pdf.ln(25)
        pdf.cell(0, 10, f"Resumen General de Facturacion: ${total_vta:,.2f}", ln=True)
        pdf.cell(0, 10, f"Rentabilidad Total (RTA): ${total_rta:,.2f}", ln=True)
        
        # Guardar gráfico de evolución para el PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            fig.savefig(tmpfile.name, format='png')
            pdf.image(tmpfile.name, x=10, y=80, w=180)
        
        # Nota: Aquí se pueden agregar más páginas y gráficos siguiendo la misma lógica
        
        pdf_output = pdf.output()
        st.download_button(label="Descargar PDF", data=bytes(pdf_output), file_name="Reporte_Gerencial.pdf", mime="application/pdf")

else:
    st.info("Sube el archivo para generar el gran informe comercial.")
