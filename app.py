import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(layout="wide", page_title="ERP Watertec - Dashboard Executivo")

st.markdown("""
    <style>
    .kpi-row { display: flex; gap: 15px; margin-bottom: 20px; }
    .kpi-card { background-color: #ffffff; border-left: 5px solid #0056b3; padding: 15px; border-radius: 8px; flex: 1; box-shadow: 2px 2px 8px rgba(0,0,0,0.08); }
    .kpi-card h4 { margin: 0; font-size: 11px; color: #6c757d; text-transform: uppercase; font-weight: 700; }
    .kpi-card h2 { margin: 6px 0 0 0; font-size: 20px; color: #212529; font-weight: bold; }
    .kpi-red { border-left-color: #dc3545; }
    .kpi-green { border-left-color: #198754; }
    .kpi-yellow { border-left-color: #ffc107; }
    
    .dash-box { background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; border-radius: 8px; margin-bottom: 20px; color: #212529; }
    .client-section { background-color: #1e2227; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #333a42; color: #fff; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def carregar_dados():
    df = pd.read_excel('CARTEIRA_FINANCEIRA.xlsx', sheet_name='CARTEIRA-06-10', header=7)
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['STATUS', 'VALOR TOTAL DO PEDIDO'], how='all')
    
    cols_fin = ['VALOR TOTAL DO PEDIDO', 'VALOR A PAGAR', 'SINAL 30%', 'Venda watertec']
    for col in cols_fin:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    if 'OV' in df.columns:
        df['OV'] = df['OV'].fillna(0).astype(str).str.replace('.0', '', regex=False)
        df['OV'] = df['OV'].replace('0', 'SEM OV')
        
    return df

try:
    df = carregar_dados()

    st.title("📊 ERP Watertec - Dashboard Comercial e Financeiro")
    st.markdown("Visão executiva com indicadores de desempenho e gráficos coloridos de alta legibilidade.")

    total_carteira = df['VALOR TOTAL DO PEDIDO'].sum()
    total_pendente = df[df['PENDENTE X PAGO'].astype(str).str.contains('PENDENTE', na=False)]['VALOR A PAGAR'].sum()
    total_pago = total_carteira - total_pendente
    if total_pago < 0: total_pago = 0
    notas_emitidas = df[df['STATUS'].astype(str).str.contains('NOTA EMITIDA', na=False)]['VALOR TOTAL DO PEDIDO'].sum()

    st.markdown(f"""
        <div class="kpi-row">
            <div class="kpi-card">
                <h4>Total da Carteira</h4>
                <h2>R$ {total_carteira:,.2f}</h2>
            </div>
            <div class="kpi-card kpi-red">
                <h4>Total Pendente a Pagar</h4>
                <h2 style="color: #dc3545;">R$ {total_pendente:,.2f}</h2>
            </div>
            <div class="kpi-card kpi-green">
                <h4>Total Já Pago (Parciais)</h4>
                <h2 style="color: #198754;">R$ {total_pago:,.2f}</h2>
            </div>
            <div class="kpi-card kpi-yellow">
                <h4>Notas Emitidas / Faturado</h4>
                <h2>R$ {notas_emitidas:,.2f}</h2>
            </div>
        </div>
    """, unsafe_allow_html=True)

    venda_watertec_val = df['Venda watertec'].sum()
    custo_a_pagar = total_pendente
    disponivel_pago = total_pago
    
    margem_pct = 0.0
    if venda_watertec_val > 0:
        margem_pct = ((venda_watertec_val - custo_a_pagar) / venda_watertec_val) * 100

    st.markdown("""
        <div class="dash-box">
            <h4 style="margin-top:0; color:#0d6efd; font-size:14px;">📈 Desempenho de Vendas, Custos e Margem (Gráficos Coloridos)</h4>
    """, unsafe_allow_html=True)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Vendas Watertec", f"R$ {venda_watertec_val:,.2f}")
    col_m2.metric("Custo / A Pagar", f"R$ {custo_a_pagar:,.2f}")
    col_m3.metric("Disponível Já Pago", f"R$ {disponivel_pago:,.2f}")
    col_m4.metric("Margem de Venda (%)", f"{margem_pct:.2f}%")

    if not df.empty:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("<font size='2' color='#333'>**Volume por Status Operacional (Barras Coloridas)**</font>", unsafe_allow_html=True)
            df_status = df.groupby('STATUS')['VALOR TOTAL DO PEDIDO'].sum().reset_index()
            chart_status = alt.Chart(df_status).mark_bar().encode(
                x=alt.X('STATUS:N', title='Status Operacional', axis=alt.Axis(labelAngle=0)),
                y=alt.Y('VALOR TOTAL DO PEDIDO:Q', title='Valor Total (R$)'),
                color=alt.Color('STATUS:N', legend=None, scale=alt.Scale(scheme='tableau10'))
            ).properties(height=200)
            st.altair_chart(chart_status, use_container_width=True)

        with col_g2:
            st.markdown("<font size='2' color='#333'>**Evolução Financeira Consolidada (Gráfico de Linha)**</font>", unsafe_allow_html=True)
            df_fin_chart = pd.DataFrame({
                "Métrica": ["Vendas Watertec", "Total Pedido", "A Pagar", "Pago"],
                "Valor": [venda_watertec_val, total_carteira, custo_a_pagar, total_pago]
            })
            chart_line = alt.Chart(df_fin_chart).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X('Métrica:N', title='Indicador'),
                y=alt.Y('Valor:Q', title='Valor (R$)'),
                color=alt.value('#0d6efd')
            ).properties(height=200)
            st.altair_chart(chart_line, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.divider()

    st.markdown("### 🔍 Filtros de Consulta")
    f1, f2, f3, f4 = st.columns(4)
    
    with f1:
        lista_clientes = ["Todos"] + sorted([str(x) for x in df['Cliente / Destino'].dropna().unique()])
        cliente_filtro = st.selectbox("Cliente / Destino:", lista_clientes)
    with f2:
        lista_ov = ["Todas"] + sorted([str(x) for x in df['OV'].unique() if x != 'SEM OV'])
        ov_filtro = st.selectbox("Ordem de Venda (OV):", lista_ov)
    with f3:
        lista_pag = ["Todos"] + sorted([str(x) for x in df['PENDENTE X PAGO'].dropna().unique()]) if 'PENDENTE X PAGO' in df.columns else ["Todos"]
        pag_filtro = st.selectbox("Status Financeiro:", lista_pag)
    with f4:
        lista_status = ["Todos"] + sorted([str(x) for x in df['STATUS'].dropna().unique()]) if 'STATUS' in df.columns else ["Todos"]
        status_filtro = st.selectbox("Status Operacional:", lista_status)

    df_filtrado = df.copy()
    if cliente_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Cliente / Destino'].astype(str) == cliente_filtro]
    if ov_filtro != "Todas":
        df_filtrado = df_filtrado[df_filtrado['OV'] == ov_filtro]
    if pag_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['PENDENTE X_PAGO' if 'PENDENTE X_PAGO' in df.columns else 'PENDENTE X PAGO'].astype(str) == pag_filtro]
    if status_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['STATUS'].astype(str) == status_filtro]

    st.divider()

    st.markdown("### 🏢 Visão Detalhada por Cliente e Itens")
    st.info("Desdobramento consolidado por cliente com base nos filtros selecionados.")

    clientes_alvo = df_filtrado['Cliente / Destino'].dropna().unique()

    if len(clientes_alvo) == 0:
        st.warning("Nenhum registo encontrado para os filtros selecionados.")
    else:
        for cli in sorted(clientes_alvo):
            df_cli = df_filtrado[df_filtrado['Cliente / Destino'] == cli]
            cli_tot = df_cli['VALOR TOTAL DO PEDIDO'].sum()
            cli_pend = df_cli[df_cli['PENDENTE X PAGO'].astype(str).str.contains('PENDENTE', na=False)]['VALOR A PAGAR'].sum()
            cli_pago = cli_tot - cli_pend
            if cli_pago < 0: cli_pago = 0

            with st.container():
                st.markdown(f"""
                    <div class="client-section">
                        <h4 style="margin:0; color:#fff;">📌 Cliente: {cli}</h4>
                        <p style="margin:4px 0 0 0; color:#adb5bd; font-size:13px;">
                            <b>Total:</b> R$ {cli_tot:,.2f} &nbsp;|&nbsp; 
                            <span style="color:#2ecc71;"><b>🟢 Pago:</b> R$ {cli_pago:,.2f}</span> &nbsp;|&nbsp; 
                            <span style="color:#e74c3c;"><b>🔴 Pendente:</b> R$ {cli_pend:,.2f}</span>
                        </p>
                    </div>
                """, unsafe_allow_html=True)

                colunas_exibir = ['OV', 'STATUS', 'Produto', 'Material', 'Qtd. Ordem', 'Venda watertec', 'VALOR TOTAL DO PEDIDO', 'VALOR A PAGAR', 'PENDENTE X PAGO']
                cols_disponiveis = [c for c in colunas_exibir if c in df_cli.columns]
                
                df_tabela_cli = df_cli[cols_disponiveis].copy()
                for c in ['VALOR TOTAL DO PEDIDO', 'VALOR A PAGAR', 'Venda watertec']:
                    if c in df_tabela_cli.columns:
                        df_tabela_cli[c] = df_tabela_cli[c].apply(lambda x: f"R$ {x:,.2f}")
                        
                st.dataframe(df_tabela_cli.astype(str), use_container_width=True, hide_index=True)
                st.markdown("<br>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro ao carregar o sistema: {e}. Verifique se a planilha CARTEIRA_FINANCEIRA.xlsx está fechada no Excel.")
