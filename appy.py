# Evolución de Gastos Mensuales
st.markdown("### 📅 Evolución del Subtotal Mensual (Sin IVA)")
if "Periodo_Mes" in df_filtrado.columns:
    # Aseguramos ordenar cronológicamente y convertir a texto para un eje X limpio
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
    fig_mes.update_xaxes(type="category")  # Trata los meses como etiquetas fijas
    fig_mes.update_traces(
        textposition="top center",
        texttemplate="%{y:,.0f}",
        line=dict(width=3, color="#0068c9"),
        marker=dict(size=8),
    )
    st.plotly_chart(fig_mes, use_container_width=True)
    
