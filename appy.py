import io
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


# 1. CARGA Y LIMPIEZA DE DATOS
@st.cache_data
def cargar_datos():
    excel_file = "COMPRAS--.xlsx"

    try:
        df_insumos = pd.read_excel(
            excel_file, sheet_name="Historial de compras"
        )
        df_insumos["Origen"] = "Insumos / Materia Prima / Reventa"
    except Exception:
        df_insumos = pd.DataFrame()

    try:
        df_servicios = pd.read_excel(
            excel_file, sheet_name="Historial - Servicios"
        )
        df_servicios["Origen"] = "Servicios"
    except Exception:
        df_servicios = pd.DataFrame()

    df_total = pd.concat([df_insumos, df_servicios], ignore_index=True)

    if not df_total.empty:
        df_total.columns = df_total.columns.str.strip()

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

        df_total["Fecha"] = pd.to_datetime(df_total["Fecha"], errors="coerce")
        df_total["Periodo_Mes"] = df_total["Fecha"].dt.strftime("%Y-%m")
        df_total = df_total.dropna(subset=["Proveedor", "Artículo"], how="all")

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


# 2. BARRA LATERAL
st.sidebar.header("🔍 Filtros Dinámicos")
st.sidebar.button("🧹 Limpiar Filtros", on_click=resetear)

moneda = st.sidebar.radio("Moneda de visualización:", ["ARS ($)", "USD (US$)"])
col_monto = "TOTAL ARS" if moneda == "ARS ($)" else "TOTAL USD"
col_pu = "Precio Unitario ARS" if moneda == "ARS ($)" else "Precio Unitario USD"
simbolo = "$" if moneda == "ARS ($)" else "US$"

st.sidebar.markdown("---")

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
    sel_origen, sel_meses, sel_rubros, sel_prov, sel_art = [], [], [], [], []
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

# 3. PESTAÑAS
tab_dash, tab_detalle, tab_cotiz = st.tabs(
    ["📊 Dashboard General", "📋 Detalle y Exportación", "💡 Cotizaciones"]
)

with tab_dash:
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

    tc_promedio = (
        df_filtrado[df_filtrado["TC BNA"] > 0]["TC BNA"].mean()
        if "TC BNA" in df_filtrado.columns
        else 0
    )

    st.subheader("📌 Resumen Ejecutivo e Indicadores Clave")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    kpi1.metric("Gasto Total", f"{simbolo} {total_gasto:,.2f}")
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
        st.markdown("### Top 8 Rubros por Monto")
        if "Rubro" in df_filtrado.columns:
            df_rubro = (
                df_filtrado.groupby("Rubro")[col_monto]
                .sum()
                .reset_index()
                .sort_values(by=col_monto, ascending=False)
                .head(8)
            )
            fig_rubro = px.bar(
                df_rubro,
                x=col_monto,
                y="Rubro",
                orientation="h",
                text_auto=".2s",
                color=col_monto,
                color_continuous_scale="Teal",
                labels={col_monto: f"Total ({simbolo})"},
            )
            fig_rubro.update_layout(
                yaxis={"categoryorder": "total ascending"},
                margin=dict(t=20, b=20),
            )
            st.plotly_chart(fig_rubro, use_container_width=True)

    # REEMPLAZO DE BARRAS APILADAS: Evolución Limpia de Gastos Mensuales
    st.markdown("### 📅 Evolución del Gasto Mensual")
    if "Periodo_Mes" in df_filtrado.columns:
        df_mes = (
            df_filtrado.groupby("Periodo_Mes")[col_monto].sum().reset_index()
        )
        fig_mes = px.line(
            df_mes,
            x="Periodo_Mes",
            y=col_monto,
            markers=True,
            text=col_monto,
            labels={
                "Periodo_Mes": "Mes",
                col_monto: f"Total Gastado ({simbolo})",
            },
            title="Gasto Total Mes a Mes",
        )
        fig_mes.update_traces(
            textposition="top center",
            texttemplate="%{y:,.0f}",
            line=dict(width=3, color="#0068c9"),
            marker=dict(size=8),
        )
        st.plotly_chart(fig_mes, use_container_width=True)

    st.markdown("---")

    # REEMPLAZO DE GRÁFICO RARO DE PRECIO: Análisis Inteligente por Artículo
    st.markdown("### 🔍 Ficha de Inspección de Artículo")
    if "Artículo" in df_filtrado.columns and col_pu in df_filtrado.columns:
        art_seleccionado = st.selectbox(
            "Seleccionar un artículo para inspeccionar su histórico de precio y proveedores:",
            options=sorted(df_filtrado["Artículo"].dropna().unique().tolist()),
        )
        if art_seleccionado:
            df_art = df_filtrado[
                df_filtrado["Artículo"] == art_seleccionado
            ].sort_values("Fecha")

            # Métricas rápidas del artículo
            m1, m2, m3, m4 = st.columns(4)
            u_precio = df_art[col_pu].iloc[-1]
            p_promedio = df_art[col_pu].mean()
            cant_compras = len(df_art)
            u_proveedor = df_art["Proveedor"].iloc[-1]

            m1.metric("Último Precio Pagado", f"{simbolo} {u_precio:,.2f}")
            m2.metric("Precio Promedio", f"{simbolo} {p_promedio:,.2f}")
            m3.metric("N° de Compras Realizadas", f"{cant_compras}")
            m4.metric("Último Proveedor", f"{u_proveedor}")

            # Visualización condicional según la cantidad de datos
            if cant_compras >= 2:
                fig_art = px.line(
                    df_art,
                    x="Fecha",
                    y=col_pu,
                    markers=True,
                    hover_data=["Proveedor", "Cantidad", "Unidad"],
                    title=f"Tendencia Histórica de Precio ({simbolo}) - {art_seleccionado}",
                )
                fig_art.update_traces(
                    line=dict(width=2, color="#ff4b4b"), marker=dict(size=7)
                )
                st.plotly_chart(fig_art, use_container_width=True)

            st.markdown("#### Historial Reciente de Compras de este Artículo")
            cols_art = [
                c
                for c in [
                    "Fecha",
                    "Proveedor",
                    "Cantidad",
                    "Unidad",
                    col_pu,
                    col_monto,
                ]
                if c in df_art.columns
            ]
            st.dataframe(df_art[cols_art], use_container_width=True)

with tab_detalle:
    st.subheader("📋 Detalle de Registros Filtrados")
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
        c1.metric("Cotizaciones Evaluadas", f"{len(df_cotizaciones)}")
        sob_total = (
            df_cotizaciones["Sobrecosto Total"].sum()
            if "Sobrecosto Total" in df_cotizaciones.columns
            else 0
        )
        c2.metric("Sobrecosto Estimado Total", f"$ {sob_total:,.2f}")

        st.markdown("---")
        st.dataframe(df_cotizaciones, use_container_width=True)
    else:
        st.info("No se encontró la pestaña 'Cotizaciones' en el Excel.")
