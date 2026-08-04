import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Compras y Servicios",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Dashboard Dinámico de Gestión de Compras y Servicios")


# 1. Cargar las dos hojas de historial
@st.cache_data
def cargar_datos():
    excel_file = "COMPRAS--.xlsx"

    # Hoja de Insumos / Materia Prima / Reventa
    df_insumos = pd.read_excel(excel_file, sheet_name="Historial de compras")
    df_insumos["Origen"] = "Insumos / Materia Prima / Reventa"

    # Hoja de Servicios
    df_servicios = pd.read_excel(
        excel_file, sheet_name="Historial - Servicios"
    )
    df_servicios["Origen"] = "Servicios"

    # Unir ambas hojas
    df_total = pd.concat([df_insumos, df_servicios], ignore_index=True)

    # Limpiar columnas
    df_total.columns = df_total.columns.str.strip()

    # Convertir números limpiando errores
    df_total["TOTAL ARS"] = pd.to_numeric(
        df_total["TOTAL ARS"], errors="coerce"
    ).fillna(0)
    df_total["TOTAL USD"] = pd.to_numeric(
        df_total["TOTAL USD"], errors="coerce"
    ).fillna(0)

    # Formateo de fechas
    df_total["Fecha"] = pd.to_datetime(df_total["Fecha"], errors="coerce")
    df_total["Periodo_Mes"] = df_total["Fecha"].dt.strftime("%Y-%m")

    # Eliminar filas vacías
    df_total = df_total.dropna(subset=["Proveedor", "Artículo"], how="all")

    return df_total


df_base = cargar_datos()

# 2. BARRA LATERAL - FILTROS DINÁMICOS
st.sidebar.header("🔍 Filtros Dinámicos")

# Selección de Moneda
moneda = st.sidebar.radio("Moneda de visualización:", ["ARS ($)", "USD (US$)"])
col_monto = "TOTAL ARS" if moneda == "ARS ($)" else "TOTAL USD"
simbolo = "$" if moneda == "ARS ($)" else "US$"

st.sidebar.markdown("---")

# Filtro 1: Origen
origen_opciones = ["Todos"] + sorted(df_base["Origen"].unique().tolist())
origen_sel = st.sidebar.selectbox("Tipo de Gastos:", origen_opciones)

df_filtrado = df_base.copy()
if origen_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Origen"] == origen_sel]

# Filtro 2: Mes
meses = ["Todos"] + sorted(
    df_filtrado["Periodo_Mes"].dropna().unique().tolist()
)
mes_sel = st.sidebar.selectbox("Filtrar por Mes:", meses)
if mes_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Periodo_Mes"] == mes_sel]

# Filtro 3: Rubro
rubros = (
    ["Todos"] + sorted(df_filtrado["Rubro"].dropna().unique().tolist())
    if "Rubro" in df_filtrado.columns
    else ["Todos"]
)
rubro_sel = st.sidebar.selectbox("Filtrar por Rubro:", rubros)
if rubro_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Rubro"] == rubro_sel]

# Filtro 4: Proveedor
proveedores = (
    ["Todos"] + sorted(df_filtrado["Proveedor"].dropna().unique().tolist())
    if "Proveedor" in df_filtrado.columns
    else ["Todos"]
)
prov_sel = st.sidebar.selectbox("Filtrar por Proveedor:", proveedores)
if prov_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Proveedor"] == prov_sel]

# Filtro 5: Artículo / Insumo
articulos = (
    ["Todos"] + sorted(df_filtrado["Artículo"].dropna().unique().tolist())
    if "Artículo" in df_filtrado.columns
    else ["Todos"]
)
art_sel = st.sidebar.selectbox("Filtrar por Artículo/Insumo:", articulos)
if art_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Artículo"] == art_sel]


# 3. TARJETAS DE MÉTRICAS (KPIs)
st.subheader("📌 Resumen Ejecutivo")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_monto = df_filtrado[col_monto].sum()
cant_registros = len(df_filtrado)
cant_proveedores = (
    df_filtrado["Proveedor"].nunique()
    if "Proveedor" in df_filtrado.columns
    else 0
)
promedio_registro = (
    (total_monto / cant_registros) if cant_registros > 0 else 0
)

kpi1.metric("Gasto Total", f"{simbolo} {total_monto:,.2f}")
kpi2.metric("N° de Operaciones", f"{cant_registros}")
kpi3.metric("Proveedores Activos", f"{cant_proveedores}")
kpi4.metric("Costo Promedio", f"{simbolo} {promedio_registro:,.2f}")

st.markdown("---")

# 4. GRÁFICOS INTERACTIVOS
st.subheader("📈 Análisis Visual de Costos")

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("### Top Proveedores por Monto")
    if "Proveedor" in df_filtrado.columns:
        df_prov = (
            df_filtrado.groupby("Proveedor")[col_monto]
            .sum()
            .reset_index()
            .sort_values(by=col_monto, ascending=False)
            .head(10)
        )
        fig_prov = px.bar(
            df_prov,
            x="Proveedor",
            y=col_monto,
            text_auto=".2s",
            color=col_monto,
            color_continuous_scale="Blues",
            labels={col_monto: f"Total ({simbolo})"},
        )
        fig_prov.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_prov, use_container_width=True)

with col_g2:
    st.markdown("### Distribución por Rubro")
    if "Rubro" in df_filtrado.columns:
        df_rubro = (
            df_filtrado.groupby("Rubro")[col_monto].sum().reset_index()
        )
        fig_rubro = px.pie(
            df_rubro,
            names="Rubro",
            values=col_monto,
            hole=0.4,
        )
        st.plotly_chart(fig_rubro, use_container_width=True)

# Gráfico de Evolución Temporal
st.markdown("### Evolución de Gastos por Período")
if "Periodo_Mes" in df_filtrado.columns:
    df_tiempo = (
        df_filtrado.groupby(["Periodo_Mes", "Origen"])[col_monto]
        .sum()
        .reset_index()
    )
    fig_tiempo = px.bar(
        df_tiempo,
        x="Periodo_Mes",
        y=col_monto,
        color="Origen",
        barmode="group",
        labels={
            "Periodo_Mes": "Mes",
            col_monto: f"Monto ({simbolo})",
            "Origen": "Tipo",
        },
    )
    st.plotly_chart(fig_tiempo, use_container_width=True)
