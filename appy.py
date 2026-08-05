import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Compras", page_icon="📊", layout="wide"
)

st.title("📊 Dashboard de Seguimiento de Compras")


# 1. Carga de datos
@st.cache_data
def cargar_datos():
    excel_file = "COMPRAS--.xlsx"

    # Lectura de la hoja Insumos
    try:
        df_insumos = pd.read_excel(
            excel_file, sheet_name="Historial de compras"
        )
        df_insumos["Origen"] = "Insumos / Materia Prima / Reventa"
    except Exception as e:
        st.error(f"❌ Error al cargar 'Historial de compras': {e}")
        df_insumos = pd.DataFrame()

    # Lectura de la hoja Servicios
    try:
        df_servicios = pd.read_excel(
            excel_file, sheet_name="Historial - Servicios"
        )
        df_servicios["Origen"] = "Servicios"
    except Exception as e:
        st.error(f"❌ Error al cargar 'Historial - Servicios': {e}")
        df_servicios = pd.DataFrame()

    # Unificación de datos
    df_total = pd.concat([df_insumos, df_servicios], ignore_index=True)

    if not df_total.empty:
        df_total.columns = df_total.columns.str.strip()

        # Asignación segura de Subtotales (Sin IVA)
        if len(df_total.columns) >= 14:
            df_total["Subtotal ARS"] = pd.to_numeric(
                df_total.iloc[:, 12], errors="coerce"
            ).fillna(0)
            df_total["Subtotal USD"] = pd.to_numeric(
                df_total.iloc[:, 13], errors="coerce"
            ).fillna(0)
        else:
            df_total["Subtotal ARS"] = pd.to_numeric(
                df_total.get("Subtotal ARS", 0), errors="coerce"
            ).fillna(0)
            df_total["Subtotal USD"] = pd.to_numeric(
                df_total.get("Subtotal USD", 0), errors="coerce"
            ).fillna(0)

        # Conversión de columnas numéricas adicionales
        for col in [
            "TOTAL ARS",
            "TOTAL USD",
            "Precio Unitario ARS",
            "Precio Unitario USD",
            "TC BNA",
        ]:
            if col in df_total.columns:
                df_total[col] = pd.to_numeric(
                    df_total[col], errors="coerce"
                ).fillna(0)

        # Formato de fechas y meses
        df_total["Fecha"] = pd.to_datetime(df_total["Fecha"], errors="coerce")
        df_total["Periodo_Mes"] = df_total["Fecha"].dt.strftime("%Y-%m")
        df_total = df_total.dropna(subset=["Proveedor", "Artículo"], how="all")

    # Lectura opcional de cotizaciones
    try:
        df_cotiz = pd.read_excel(excel_file, sheet_name="Cotizaciones")
        df_cotiz.columns = df_cotiz.columns.str.strip()
    except Exception:
        df_cotiz = pd.DataFrame()

    return df_total, df_cotiz


df_total, df_cotiz = cargar_datos()

if df_total.empty:
    st.warning(
        "⚠️ No se pudieron cargar datos del archivo Excel. Verificá que 'COMPRAS--.xlsx' esté en la raíz del repositorio."
    )
    st.stop()

# 2. Filtros Laterales (Sidebar)
st.sidebar.header("🔍 Filtros de Búsqueda")

moneda_sel = st.sidebar.radio("Seleccionar Moneda de Análisis:", ["USD", "ARS"])
col_monto = "Subtotal USD" if moneda_sel == "USD" else "Subtotal ARS"
col_total = "TOTAL USD" if moneda_sel == "USD" else "TOTAL ARS"
simbolo = "US$" if moneda_sel == "USD" else "$"

# Filtro de Origen
origenes = ["Todos"] + sorted(df_total["Origen"].dropna().unique().tolist())
origen_sel = st.sidebar.selectbox("Tipo de Compra / Origen:", origenes)

# Filtro de Rubro
rubros = ["Todos"] + sorted(df_total["Rubro"].dropna().unique().tolist())
rubro_sel = st.sidebar.selectbox("Rubro:", rubros)

# Filtro de Proveedor
proveedores = ["Todos"] + sorted(
    df_total["Proveedor"].dropna().unique().tolist()
)
prov_sel = st.sidebar.selectbox("Proveedor:", proveedores)

# Aplicar Filtros
df_filtrado = df_total.copy()
if origen_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Origen"] == origen_sel]
if rubro_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Rubro"] == rubro_sel]
if prov_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Proveedor"] == prov_sel]

# 3. Métricas Principales (KPIs)
total_subtotal = df_filtrado[col_monto].sum()
total_con_iva = df_filtrado[col_total].sum()
cant_compras = len(df_filtrado)

col1, col2, col3 = st.columns(3)
col1.metric(
    f"Subtotal Total (Sin IVA)", f"{simbolo} {total_subtotal:,.2f}"
)
col2.metric(f"Total General (Con IVA)", f"{simbolo} {total_con_iva:,.2f}")
col3.metric("Cantidad de Registros", f"{cant_compras}")

st.markdown("---")

# 4. Gráficos Interactivos

# Gráfico 1: Evolución Mensual Corregido (Eje X Categórico)
st.markdown("### 📅 Evolución del Subtotal Mensual (Sin IVA)")
if "Periodo_Mes" in df_filtrado.columns and not df_filtrado.empty:
    df_mes = (
        df_filtrado.groupby("Periodo_Mes")[col_monto]
        .sum()
        .reset_index()
        .sort_values(by="Periodo_Mes")
    )
    df_mes["Periodo_Mes"] = df_mes["Periodo_Mes"].astype(str)

    fig_mes = px.line(
        df_mes,
        x="Periodo_Mes",
        y=col_monto,
        markers=True,
        text=col_monto,
        labels={
            "Periodo_Mes": "Mes",
            col_monto: f"Subtotal Gastado ({simbolo})",
        },
    )
    fig_mes.update_xaxes(
        type="category"
    )  # Evita que interprete horas/días al hacer zoom
    fig_mes.update_traces(
        textposition="top center",
        texttemplate="%{y:,.0f}",
        line=dict(width=3, color="#0068c9"),
        marker=dict(size=8),
    )
    st.plotly_chart(fig_mes, use_container_width=True)

col_g1, col_g2 = st.columns(2)

# Gráfico 2: Gastos por Rubro
with col_g1:
    st.markdown("### 🏷️ Subtotal por Rubro")
    if "Rubro" in df_filtrado.columns and not df_filtrado.empty:
        df_rubro = (
            df_filtrado.groupby("Rubro")[col_monto]
            .sum()
            .reset_index()
            .sort_values(by=col_monto, ascending=True)
        )
        fig_rubro = px.bar(
            df_rubro,
            x=col_monto,
            y="Rubro",
            orientation="h",
            text_auto=",.0f",
            labels={col_monto: f"Monto ({simbolo})", "Rubro": ""},
        )
        st.plotly_chart(fig_rubro, use_container_width=True)

# Gráfico 3: Top Proveedores
with col_g2:
    st.markdown("### 🏢 Top 10 Proveedores")
    if "Proveedor" in df_filtrado.columns and not df_filtrado.empty:
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
            text_auto=",.0f",
            labels={col_monto: f"Monto ({simbolo})", "Proveedor": ""},
        )
        st.plotly_chart(fig_prov, use_container_width=True)

st.markdown("---")

# 5. Tabla de Datos Detallada
st.markdown("### 📋 Detalle de Registro de Compras")
st.dataframe(
    df_filtrado[
        [
            "Fecha",
            "Origen",
            "Rubro",
            "Proveedor",
            "Artículo",
            "Cantidad",
            "Unidad",
            col_monto,
            col_total,
        ]
    ],
    use_container_width=True,
)
