import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Dashboard de Compras", layout="wide")
st.title("📊 Dashboard de Gestión de Compras")

# Cargar datos
df = pd.read_excel("COMPRAS--.xlsx")

# Limpiar nombres de columnas (quita espacios extra)
df.columns = df.columns.str.strip()

# Buscar automáticamente cuál es la columna de Fecha
columna_fecha = None
for col in df.columns:
    if "fecha" in col.lower() or "date" in col.lower() or "mes" in col.lower():
        columna_fecha = col
        break

st.sidebar.header("🔍 Filtros")

# Si encuentra la columna de fecha, arma el filtro por mes
if columna_fecha:
    df[columna_fecha] = pd.to_datetime(df[columna_fecha], errors="coerce")
    df["Mes"] = df[columna_fecha].dt.strftime("%Y-%m")

    meses_disponibles = ["Todos"] + sorted(
        df["Mes"].dropna().unique().tolist()
    )
    mes_seleccionado = st.sidebar.selectbox(
        "Seleccionar Mes:", meses_disponibles
    )

    if mes_seleccionado != "Todos":
        df = df[df["Mes"] == mes_seleccionado]

# Mostrar los datos y gráficos
st.subheader("Datos de Compras")
st.dataframe(df, use_container_width=True)
