import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Gestión de Compras",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Dashboard de Gestión de Compras")

# 1. Cargar la hoja correcta del Excel
excel_file = "COMPRAS--.xlsx"
df = pd.read_excel(excel_file, sheet_name="Historial de compras")

# Limpiar nombres de columnas de espacios
df.columns = df.columns.str.strip()

# Asegurar formato de fecha
df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

# Formatear el mes como Año-Mes (o Nombre de Mes) para el filtro
df["Periodo_Mes"] = df["Fecha"].dt.strftime("%Y-%m")

# 2. Barra lateral con Filtros
st.sidebar.header("🔍 Filtros")

# Filtro por Mes
meses_disponibles = ["Todos"] + sorted(
    df["Periodo_Mes"].dropna().unique().tolist()
)
mes_seleccionado = st.sidebar.selectbox("Filtrar por Mes:", meses_disponibles)

# Filtro por Moneda (ARS / USD)
moneda = st.sidebar.radio("Ver montos en:", ["ARS ($)", "USD (US$)"])
col_monto = "TOTAL ARS" if moneda == "ARS ($)" else "TOTAL USD"
simbolo_moneda = "$" if moneda == "ARS ($)" else "US$"

# Aplicar filtros
df_filtrado = df.copy()
if mes_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Periodo_Mes"] == mes_seleccionado]

# 3. Métricas Principales (KPIs)
st.subheader("Resumen General")
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

total_gastado = df_filtrado[col_monto].sum()
total_compras = len(df_filtrado)
cant_proveedores = df_filtrado["Proveedor"].nunique()

col_kpi1.metric(
    "Monto Total Gastado", f"{simbolo_moneda} {total_gastado:,.2f}"
)
col_kpi2.metric("Cantidad de Registros", f"{total_compras}")
col_kpi3.metric("Proveedores Distintos", f"{cant_proveedores}")

st.markdown("---")

# 4. Gráficos Interactivos
st.subheader("Análisis Visual")
c1, c2 = st.columns(2)

with c1:
    st.markdown("### Gastos por Proveedor")
    prov_df = (
        df_filtrado.groupby("Proveedor")[col_monto]
        .sum()
        .reset_index()
        .sort_values(by=col_monto, ascending=False)
    )
    fig_prov = px.bar(
        prov_df,
        x="Proveedor",
        y=col_monto,
        labels={col_monto: f"Total ({simbolo_moneda})"},
        text_auto=".2s",
        color=col_monto,
        color_continuous_scale="Viridis",
    )
    fig_prov.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_prov, use_container_width=True)

with c2:
    st.markdown("### Distribución por Rubro / Categoría")
    rubro_df = (
        df_filtrado.groupby("Rubro")[col_monto].sum().reset_index()
    )
    fig_rubro = px.pie(
        rubro_df,
        names="Rubro",
        values=col_monto,
        hole=0.4,
    )
    st.plotly_chart(fig_rubro, use_container_width=True)

# 5. Tabla de datos detallada abajo
st.markdown("---")
st.subheader("📋 Detalle del Historial de Compras")
st.dataframe(
    df_filtrado[
        [
            "Fecha",
            "Proveedor",
            "Rubro",
            "Artículo",
            "Cantidad",
            "Unidad",
            "TOTAL ARS",
            "TOTAL USD",
        ]
    ],
    use_container_width=True,
)
