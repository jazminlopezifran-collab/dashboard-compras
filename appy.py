import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="Dashboard Ejecutivo de Compras", layout="wide")

st.title("📊 Panel de Control Ejecutivo - Gestión de Compras")
st.markdown("---")

@st.cache_data(ttl=3600)
def obtener_tc_bna():
    try:
        url = "https://dolarapi.com/v1/dolares/oficial"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json().get("venta", 1425.0)
    except Exception:
        pass
    return 1425.0

@st.cache_data
def cargar_datos():
    df = pd.read_excel('COMPRAS--.xlsx', sheet_name='Historial de compras')
    df.columns = df.columns.str.strip()
    return df

try:
    df_raw = cargar_datos()
    tc_bna = obtener_tc_bna()
    df = df_raw.copy()

    # --- FILTROS LATERALES ---
    st.sidebar.header("🔍 Filtros de Búsqueda")

    if 'Proveedor' in df.columns:
        prov_list = ["Todos"] + sorted([str(p) for p in df['Proveedor'].dropna().unique()])
        sel_prov = st.sidebar.selectbox("Filtrar por Proveedor", prov_list)
        if sel_prov != "Todos":
            df = df[df['Proveedor'].astype(str) == sel_prov]

    if 'Rubro' in df.columns:
        rubro_list = ["Todos"] + sorted([str(r) for r in df['Rubro'].dropna().unique()])
        sel_rubro = st.sidebar.selectbox("Filtrar por Rubro", rubro_list)
        if sel_rubro != "Todos":
            df = df[df['Rubro'].astype(str) == sel_rubro]

    # --- MÉTRICAS DE ENCABEZADO ---
    subtotal_ars = df['Subtotal ARS'].sum() if 'Subtotal ARS' in df.columns else 0.0
    total_ars = df['TOTAL ARS'].sum() if 'TOTAL ARS' in df.columns else 0.0
    total_usd = df['TOTAL USD'].sum() if 'TOTAL USD' in df.columns else 0.0
    cant_compras = len(df)

    st.subheader("💵 Resumen Financiero General")
    m1, m2, m3, m4 = st.columns(4)
    
    m1.metric("💰 Subtotal Acumulado (ARS)", f"${subtotal_ars:,.2f}")
    m2.metric("💳 Total con IVA (ARS)", f"${total_ars:,.2f}")
    m3.metric("🏛️ Total General (USD)", f"US$ {total_usd:,.2f}")
    m4.metric("📦 Cantidad de Registros", f"{cant_compras:,}")

    st.markdown("---")

    # --- GRÁFICOS VISUALES ---
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("🏆 Top Proveedores por Monto (ARS)")
        if 'Proveedor' in df.columns and 'Subtotal ARS' in df.columns:
            df_prov = (
                df.groupby('Proveedor')['Subtotal ARS']
                .sum()
                .reset_index()
                .sort_values(by='Subtotal ARS', ascending=False)
                .head(10)
            )
            fig_prov = px.bar(
                df_prov,
                x='Subtotal ARS',
                y='Proveedor',
                orientation='h',
                text_auto='.3s',
                color='Subtotal ARS',
                color_continuous_scale='Blues',
                labels={'Subtotal ARS': 'Monto ($ ARS)', 'Proveedor': 'Proveedor'}
            )
            fig_prov.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            st.plotly_chart(fig_prov, use_container_width=True)

    with g2:
        st.subheader("📦 Gastos por Rubro (ARS)")
        if 'Rubro' in df.columns and 'Subtotal ARS' in df.columns:
            df_rubro = (
                df.groupby('Rubro')['Subtotal ARS']
                .sum()
                .reset_index()
                .sort_values(by='Subtotal ARS', ascending=False)
            )
            fig_rubro = px.pie(
                df_rubro,
                values='Subtotal ARS',
                names='Rubro',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_rubro.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_rubro, use_container_width=True)

    st.markdown("---")
    
    st.subheader("🛍️ Top 10 Artículos / Insumos de Mayor Impacto")
    if 'Artículo' in df.columns and 'Subtotal ARS' in df.columns:
        df_art = (
            df.groupby('Artículo')['Subtotal ARS']
            .sum()
            .reset_index()
            .sort_values(by='Subtotal ARS', ascending=False)
            .head(10)
        )
        fig_art = px.bar(
            df_art,
            x='Artículo',
            y='Subtotal ARS',
            color='Subtotal ARS',
            color_continuous_scale='Teal',
            text_auto='.3s',
            labels={'Subtotal ARS': 'Monto ($ ARS)', 'Artículo': 'Artículo / Insumo'}
        )
        fig_art.update_layout(showlegend=False)
        st.plotly_chart(fig_art, use_container_width=True)

except Exception as e:
    st.error(f"Error al procesar el Historial de Compras: {e}")