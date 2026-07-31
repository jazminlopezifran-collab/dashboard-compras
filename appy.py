import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Dashboard de Compras", layout="wide")

st.title("📊 Dashboard de Gestión de Compras")

# 1. Cargar datos
df = pd.read_excel("COMPRAS--.xlsx")

# Convertir la columna de fecha a tipo datetime si aún no lo está
# (Asegúrate de que 'Fecha' sea el nombre exacto de la columna en tu Excel)
df["Fecha"] = pd.to_datetime(df["Fecha"])

# Crear una columna con el nombre del Mes / Año para filtrar fácilmente
df["Mes"] = df["Fecha"].dt.strftime("%Y-%m")

# 2. Barra lateral con Filtros
st.sidebar.header("🔍 Filtros")

# Filtro de Mes
meses_disponibles = ["Todos"] + sorted(df["Mes"].unique().tolist())
mes_seleccionado = st.sidebar.selectbox("Seleccionar Mes:", meses_disponibles)

# Aplicar el filtro de mes al DataFrame
df_filtrado = df.copy()
if mes_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Mes"] == mes_seleccionado]

# 3. Métricas y KPIs
st.subheader("Resumen General")
monto_total = df_filtrado["Monto"].sum()  # Cambia 'Monto' si tu columna se llama distinto
st.metric("Monto Total Gastado", f"${monto_total:,.2f}")

# 4. Gráficos interactivos (usan 'df_filtrado')
col1, col2 = st.columns(2)

with col1:
    st.subheader("Gastos por Proveedor")
    fig_proveedor = px.bar(
        df_filtrado,
        x="Proveedor",
        y="Monto",
        title="Total por Proveedor",
        color="Proveedor",
    )
    st.plotly_chart(fig_proveedor, use_container_width=True)

with col2:
    st.subheader("Gastos por Insumo / Categoría")
    fig_insumo = px.pie(
        df_filtrado,
        names="Insumo",
        values="Monto",
        title="Distribución por Insumo",
    )
    st.plotly_chart(fig_insumo, use_container_width=True)
