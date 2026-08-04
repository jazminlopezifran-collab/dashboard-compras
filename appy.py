import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Compras y Servicios",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Dashboard Dinámico de Gestión de Compras y Servicios")


# 1. CARGA Y LIMPIEZA DE DATOS
@st.cache_data
def cargar_datos():
    excel_file = "COMPRAS--.xlsx"

    # Hoja de Insumos
    try:
        df_insumos = pd.read_excel(
            excel_file, sheet_name="Historial de compras"
        )
        df_insumos["Origen"] = "Insumos / Materia Prima / Reventa"
    except Exception:
        df_insumos = pd.DataFrame()

    # Hoja de Servicios
    try:
        df_servicios = pd.read_excel(
            excel_file, sheet_name="Historial - Servicios"
        )
        df_servicios["Origen"] = "Servicios"
    except Exception:
        df_servicios = pd.DataFrame()

    # Unir compras y servicios
    df_total = pd.concat([df_insumos, df_servicios], ignore_index=True)

    if not df_total.empty:
        df_total.columns = df_total.columns.str.strip()

        # Convertir montos
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

        # Fechas
        df_total["Fecha"] = pd.to_datetime(df_total["Fecha"], errors="coerce")
        df_total["Periodo_Mes"] = df_total["Fecha"].dt.strftime("%Y-%m")

        # Eliminar filas totalmente vacías
        df_total = df_total.dropna(subset=["Proveedor", "Artículo"], how="all")

    # Cargar Cotizaciones si existen
    try:
        df_cotiz = pd.read_excel(excel_file, sheet_name="Cotizaciones")
        df_cotiz.columns = df_cotiz.columns.str.strip()
    except Exception:
        df_cotiz = pd.DataFrame()

    return df_total, df_cotiz


df_base, df_cotizaciones = cargar_datos()

# Estado de filtros
if "reset_filtros" not in st.session_state:
    st.session_state.reset_filtros = False


def resetear():
    st.session_state.reset_filtros = True


# 2. BARRA LATERAL - FILTROS DINÁMICOS
st.sidebar.header("🔍 Filtros Dinámicos")

# Botón para limpiar filtros
st.sidebar.button("🧹 Limpiar Filtros", on_click=resetear)

# Moneda
moneda = st.sidebar.radio("Moneda de visualización:", ["ARS ($)", "USD (US$)"])
col_monto = "TOTAL ARS" if moneda == "ARS ($)" else "TOTAL USD"
col_pu = "Precio Unitario ARS" if moneda == "ARS ($)" else "Precio Unitario USD"
simbolo = "$" if moneda == "ARS ($)" else "US$"

st.sidebar.markdown("---")

# Opciones para Filtros
origen_opts = sorted(df_base["Origen"].dropna().unique().tolist())
meses_opts = sorted(df_base["Periodo_Mes"].dropna().unique().tolist())
rubros_opts = (
    sorted(df_base["Rubro"].dropna().unique().tolist())
    if "Rubro" in df_base.columns
    else []
)
prov_opts = (
    sorted(df_base["Proveedor"].dropna().unique().tolist())
    if "Proveedor" in df_base.columns
    else []
)
art_opts = (
    sorted(df_base["Artículo"].dropna().unique().tolist())
    if "Artículo" in df_base.columns
    else []
)

if st.session_state.reset_filtros:
    sel_origen = []
    sel_meses = []
    sel_rubros = []
    sel_prov = []
    sel_art = []
    st.session_state.reset_filtros = False
else:
    sel_origen = st.sidebar.multiselect(
        "Tipo de Gastos:", origen_opts, placeholder="Todos"
    )
    sel_meses = st.sidebar.multiselect(
        "Filtrar por Mes:", meses_opts, placeholder="Todos"
    )
    sel_rubros = st.sidebar.multiselect(
        "Filtrar por Rubro:", rubros_opts, placeholder="Todos"
    )
    sel_prov = st.sidebar.multiselect(
        "Filtrar por Proveedor:", prov_opts, placeholder="Todos"
    )
    sel_art = st.sidebar.multiselect(
        "Filtrar por Artículo:", art_opts, placeholder="Todos"
    )

# Filtrado de DataFrame
df_filtrado = df_base.copy()
if sel_origen:
    df_filtrado = df_filtrado[df_filtrado["Origen"].isin(sel_origen)]
if sel_meses:
    df_filtrado = df_filtrado[df_filtrado["Periodo_Mes"].isin(sel_meses)]
if sel_rubros and "Rubro" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Rubro"].isin(sel_rubros)]
if sel_prov and "Proveedor" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Proveedor"].isin(sel_prov)]
if sel_art and "Artículo" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Artículo"].isin(sel_art)]


# 3. PESTAÑAS PRINCIPALES
tab_dash, tab_detalle, tab_cotiz = st.tabs(
    ["📊 Dashboard General", "📋 Detalle y Exportación", "💡 Cotizaciones"]
)

with tab_dash:
    # KPI 1: Variación MoM (Mes a Mes)
    meses_disponibles = sorted(
        df_filtrado["Periodo_Mes"].dropna().unique().tolist()
    )
    mom_delta = None
    if len(meses_disponibles) >= 2:
        ultimo_mes = meses_disponibles[-1]
        penultimo_mes = meses_disponibles[-2]

        monto_ultimo = df_filtrado[df_filtrado["Periodo_Mes"] == ultimo_mes][
            col_monto
        ].sum()
        monto_penultimo = df_filtrado[
            df_filtrado["Periodo_Mes"] == penultimo_mes
        ][col_monto].sum()

        if monto_penultimo > 0:
            var_pct = ((monto_ultimo - monto_penultimo) / monto_penultimo) * 100
            mom_delta = (
                f"{var_pct:+.1f}% vs {penultimo_mes}"
            )

    # KPI 2: Concentración Top 3 Proveedores
    total_gasto = df_filtrado[col_monto].sum()
    pct_top3 = 0
    if "Proveedor" in df_filtrado.columns and total_gasto > 0:
        top3_sum = (
            df_filtrado.groupby("Proveedor")[col_monto]
            .sum()
            .nlargest(3)
            .sum()
        )
        pct_top3 = (top3_sum / total_gasto) * 100

    # KPI 3: TC BNA Promedio
    tc_promedio = (
        df_filtrado[df_filtrado["TC BNA"] > 0]["TC BNA"].mean()
        if "TC BNA" in df_filtrado.columns
        else 0
    )

    st.subheader("📌 Resumen Ejecutivo e Indicadores Clave")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    kpi1.metric(
        "Gasto Total", f"{simbolo} {total_gasto:,.2f}", delta=mom_delta
    )
    kpi2.metric("N° Operaciones", f"{len(df_filtrado)}")
    kpi3.metric(
        "Proveedores Activos",
        f"{df_filtrado['Proveedor'].nunique() if 'Proveedor' in df_filtrado.columns else 0}",
    )
    kpi4.metric("Concentración Top 3", f"{pct_top3:.1f}%")
    kpi5.metric(
        "TC BNA Promedio",
        f"${tc_promedio:,.2f}" if tc_promedio > 0 else "N/A",
    )

    st.markdown("---")

    # GRÁFICOS PRINCIPALES
    st.subheader("📈 Análisis Visual de Costos")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("### Top 10 Proveedores por Monto")
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
            fig_prov.update_layout(
                xaxis_tickangle=-45, margin=dict(t=20, b=20)
            )
            st.plotly_chart(fig_prov, use_container_width=True)

    with col_g2:
        st.markdown("### Distribución por Moneda de Pactación")
        if "Moneda" in df_filtrado.columns:
            df_moneda = (
                df_filtrado.groupby("Moneda")[col_monto].sum().reset_index()
            )
            fig_moneda = px.pie(
                df_moneda,
                names="Moneda",
                values=col_monto,
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_moneda.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig_moneda, use_container_width=True)

    # Gráficos Temporales
    st.markdown("### Evolución de Gastos Mensuales por Rubro")
    if "Periodo_Mes" in df_filtrado.columns and "Rubro" in df_filtrado.columns:
        df_rubro_tiempo = (
            df_filtrado.groupby(["Periodo_Mes", "Rubro"])[col_monto]
            .sum()
            .reset_index()
        )
        fig_rubro_tiempo = px.bar(
            df_rubro_tiempo,
            x="Periodo_Mes",
            y=col_monto,
            color="Rubro",
            labels={
                "Periodo_Mes": "Mes",
                col_monto: f"Monto ({simbolo})",
            },
        )
        st.plotly_chart(fig_rubro_tiempo, use_container_width=True)

    # Análisis de Evolución de Precio por Artículo
    st.markdown("### 🔍 Evolución del Precio Unitario por Artículo")
    if "Artículo" in df_filtrado.columns and col_pu in df_filtrado.columns:
        art_seleccionado = st.selectbox(
            "Seleccionar un artículo para ver la tendencia de su precio:",
            options=sorted(
                df_filtrado["Artículo"].dropna().unique().tolist()
            ),
        )
        if art_seleccionado:
            df_art = df_filtrado[
                df_filtrado["Artículo"] == art_seleccionado
            ].sort_values("Fecha")
            if not df_art.empty:
                fig_art = px.line(
                    df_art,
                    x="Fecha",
                    y=col_pu,
                    markers=True,
                    hover_data=["Proveedor", "Cantidad", "Unidad"],
                    title=f"Histórico de Precio Unitario ({simbolo}) - {art_seleccionado}",
                )
                st.plotly_chart(fig_art, use_container_width=True)

with tab_detalle:
    st.subheader("📋 Detalle de Registros Filtrados")
    st.markdown(
        "Explora y exporta la información según los filtros aplicados en la barra lateral."
    )

    cols_mostrar = [
        c
        for c in [
            "Fecha",
            "Origen",
            "Proveedor",
            "Rubro",
            "Artículo",
            "Cantidad",
            "Unidad",
            "Precio Unitario ARS",
            "Precio Unitario USD",
            "TOTAL ARS",
            "TOTAL USD",
            "TC BNA",
        ]
        if c in df_filtrado.columns
    ]

    st.dataframe(df_filtrado[cols_mostrar], use_container_width=True)

    # Exportación a Excel utilizando openpyxl
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_filtrado[cols_mostrar].to_excel(
            writer, index=False, sheet_name="Datos_Filtrados"
        )

    st.download_button(
        label="📥 Descargar Datos Filtrados a Excel",
        data=buffer.getvalue(),
        file_name="Reporte_Compras_Servicios.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with tab_cotiz:
    st.subheader("💡 Módulo de Análisis de Cotizaciones")
    if not df_cotizaciones.empty:
        c1, c2 = st.columns(2)
        total_cotiz = len(df_cotizaciones)
        sob_total = (
            df_cotizaciones["Sobrecosto Total"].sum()
            if "Sobrecosto Total" in df_cotizaciones.columns
            else 0
        )

        c1.metric("Cotizaciones Evaluadas", f"{total_cotiz}")
        c2.metric("Sobrecosto Estimado Total", f"$ {sob_total:,.2f}")

        st.markdown("---")
        st.markdown("### Tabla de Cotizaciones y Variaciones")
        st.dataframe(df_cotizaciones, use_container_width=True)
    else:
        st.info("No se encontró la pestaña 'Cotizaciones' en el Excel.")
