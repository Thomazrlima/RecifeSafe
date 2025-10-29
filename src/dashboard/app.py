from pathlib import Path
import sys
import argparse
import warnings
import json

warnings.filterwarnings(
    "ignore",
    message="The keyword arguments have been deprecated and will be removed in a future release. Use `config` instead to specify Plotly configuration options."
)

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--instructions", action="store_true", help="Print Windows PowerShell instructions to set up venv and run the app")
parser.add_argument("--open-html", action="store_true", help="When running with python (no streamlit), generate/open the fallback HTML map")
args, _ = parser.parse_known_args()

try:
    import streamlit as st
    from streamlit.components.v1 import html
    try:
        from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx
    except Exception:
        get_script_run_ctx = None
    if get_script_run_ctx is not None:
        ctx = get_script_run_ctx()
        if ctx is None and not args.open_html:
            print("Streamlit importado, mas o app não foi iniciado com 'streamlit run'.")
            print("Inicie assim para evitar warnings e executar o app interativo:")
            print("  streamlit run src\\dashboard\\app.py")
            print("Ou rode: python src\\dashboard\\app.py --open-html para gerar/abrir o HTML fallback")
            sys.exit(0)
except Exception:
    st = None
    def html(*args, **kwargs):
        return None

try:
    import pandas as pd
    import numpy as np
except Exception:
    pd = None
    np = None

try:
    import plotly.express as px
except Exception:
    px = None

try:
    import folium
except Exception:
    folium = None

try:
    import joblib
except Exception:
    joblib = None

if st is None:
    if not args.open_html:
        print("Streamlit não encontrado ou executando diretamente com 'python'.")
        print("Para iniciar o dashboard interativo instale dependências e execute via Streamlit:")
        print("  python -m venv .venv")
        print("  .\\.venv\\Scripts\\Activate.ps1")
        print("  pip install -r requirements.txt")
        print("  streamlit run src\\dashboard\\app.py")
        print("")
        print("Se quiser que o script gere/abra o HTML fallback automaticamente, execute:")
        print("  python src\\dashboard\\app.py --open-html")
        sys.exit(0)

    repo_root = Path(__file__).resolve().parents[2]
    templates_dir = repo_root / 'src' / 'dashboard' / 'templates'
    wrapper = templates_dir / 'map_view.html'
    map_file = templates_dir / 'map_generated.html'

    if wrapper.exists():
        print("Streamlit não encontrado. Abrindo versão HTML em seu navegador...")
        import webbrowser
        try:
            webbrowser.open_new_tab(wrapper.as_uri())
            print(f"Abrindo: {wrapper}")
        except Exception:
            print(f"Abrir manualmente o arquivo: {wrapper}")
        sys.exit(0)

    data_csv = repo_root / 'data' / 'processed' / 'simulated_daily.csv'
    if data_csv.exists() and pd is not None and folium is not None:
        try:
            templates_dir.mkdir(parents=True, exist_ok=True)
            df = pd.read_csv(data_csv, parse_dates=['date'])
            grouped = df.groupby('bairro').agg({'lat':'mean','lon':'mean','ocorrencias':'sum','vulnerabilidade':'mean'}).reset_index()
            if grouped.empty:
                raise RuntimeError("Dados lidos mas agregação retornou vazio.")
            center_lat = float(grouped['lat'].mean())
            center_lon = float(grouped['lon'].mean())
            m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
            for _, r in grouped.iterrows():
                color = 'green'
                if r['ocorrencias']>10 or r['vulnerabilidade']>0.6:
                    color='red'
                elif r['ocorrencias']>3:
                    color='orange'
                folium.CircleMarker(
                    location=[float(r['lat']), float(r['lon'])],
                    radius=6 + min(int(r['ocorrencias']), 10),
                    color=color, fill=True,
                    tooltip=f"{r['bairro']}: ocorr={int(r['ocorrencias'])}, vuln={r['vulnerabilidade']:.2f}"
                ).add_to(m)
            m.save(str(map_file))
            wrapper_html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>RecifeSafe — Map View</title>
  <style>
    body{{margin:0;font-family:Arial,Helvetica,sans-serif}}
    header{{padding:10px;background:#0b486b;color:#fff}}
    .frame{{border:none;width:100%;height:90vh}}
    .notice{{padding:16px;text-align:center;color:#444}}
  </style>
</head>
<body>
  <header><h2>RecifeSafe — Mapa Gerado</h2></header>
  <!-- Primary embed: iframe -->
  <iframe class="frame" src="{map_file.as_uri()}" title="RecifeSafe Map (iframe)"></iframe>
  <!-- Fallback: object embedding and direct link -->
  <div class="notice">
    <p>Se o mapa acima não carregar, tente o fallback abaixo ou abra o arquivo diretamente.</p>
    <object class="frame" data="{map_file.as_uri()}" type="text/html">
      <p>Seu navegador não consegue exibir o mapa embutido. <a href="{map_file.as_uri()}" target="_blank" rel="noopener">Abrir mapa em nova aba</a></p>
    </object>
    <p><a href="{map_file.as_uri()}" target="_blank" rel="noopener">Abrir map_generated.html diretamente</a></p>
  </div>
</body>
</html>"""
            wrapper.write_text(wrapper_html, encoding='utf-8')
            print(f"Mapa e wrapper gerados em: {templates_dir}")
            import webbrowser
            try:
                webbrowser.open_new_tab(wrapper.as_uri())
                print(f"Abrindo wrapper: {wrapper}")
            except Exception:
                print(f"Abrir manualmente o arquivo: {wrapper}")
            try:
                webbrowser.open_new_tab(map_file.as_uri())
                print(f"Tentativa adicional: abrindo mapa diretamente: {map_file}")
            except Exception:
                pass
            sys.exit(0)
        except Exception as e:
            print("Falha ao gerar mapa HTML automaticamente:", str(e))
            print("Verifique se pandas/folium estão instalados e se o CSV está correto.")
            print("Para executar o dashboard interativo, instale as dependências e inicie o Streamlit:")
            print("  pip install -r requirements.txt")
            print("  streamlit run src\\dashboard\\app.py")
            sys.exit(1)
    else:
        if not data_csv.exists():
            print(f"Dados ausentes: {data_csv}")
        if pd is None or folium is None:
            print("Bibliotecas necessárias para gerar o HTML não estão instaladas (pandas, folium).")
        print("Para executar o dashboard interativo, instale as dependências e inicie o Streamlit:")
        print("  pip install -r requirements.txt")
        print("  streamlit run src\\dashboard\\app.py")
        sys.exit(0)

repo_root = Path(__file__).resolve().parents[2]
logo_path = repo_root / 'img' / 'logo.png'

st.set_page_config(
    layout="wide", 
    page_title="RecifeSafe",
    page_icon=str(logo_path) if logo_path.exists() else "🏙️"
)

data_csv = repo_root / 'data' / 'processed' / 'simulated_daily.csv'
models_dir = repo_root / 'models'

if not data_csv.exists():
    st.title("RecifeSafe")
    st.warning(f"Dados não encontrados em {data_csv}. Rode: python src/data/generate_simulated_data.py")
else:
    df = pd.read_csv(data_csv, parse_dates=['date'])
    df['date'] = pd.to_datetime(df['date'])
    bairros = sorted(df['bairro'].unique())

    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1rem;
        max-width: 100%;
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    
    /* Botões */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
    }
    
    /* Mapa em tela cheia */
    iframe {
        width: 100% !important;
        border: none;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Seção de resumo */
    .summary-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    logobar_path = repo_root / 'img' / 'logobar.png'
    if logobar_path.exists():
        st.sidebar.image(str(logobar_path), use_container_width=True)
    else:
        st.sidebar.title("🏙️ RecifeSafe")
    
    page = st.sidebar.radio(
        "Navegação",
        ["🏠 Mapa de Risco", "⚠️ Alertas e Previsões", "📊 Análises Detalhadas"]
    )

    if page == "🏠 Mapa de Risco":
        st.title("🏠 Mapa de Risco — Recife")
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔍 Filtros")
        sel_bairro = st.sidebar.multiselect("Bairros", options=bairros, default=bairros[:3] if len(bairros) >= 3 else bairros)
        period = st.sidebar.selectbox("Período", ["Últimos 7 dias","Últimos 30 dias","Últimos 90 dias"], index=1)
        vuln_min = st.sidebar.slider("Vulnerabilidade (mín)", 0.0, 1.0, 0.0, 0.01)
        
        start_date = None
        if period == "Últimos 7 dias":
            start_date = df['date'].max() - pd.Timedelta(days=7)
        elif period == "Últimos 30 dias":
            start_date = df['date'].max() - pd.Timedelta(days=30)
        elif period == "Últimos 90 dias":
            start_date = df['date'].max() - pd.Timedelta(days=90)
        
        mask = pd.Series(True, index=df.index)
        if sel_bairro:
            mask = mask & df['bairro'].isin(sel_bairro)
        if start_date is not None:
            mask = mask & (df['date'] >= start_date)
        if vuln_min > 0:
            mask = mask & (df['vulnerabilidade'] >= vuln_min)
        dff = df[mask].copy()
        
        st.markdown("### Mapa de Ocorrências")
        if not df.empty and folium is not None:
            center_lat = float(df['lat'].mean())
            center_lon = float(df['lon'].mean())
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
            
            geojson_path = repo_root / 'data' / 'bairros' / 'bairros.geojson'
            if geojson_path.exists():
                with open(geojson_path, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                
                bairros_selecionados_upper = [b.upper() for b in sel_bairro] if sel_bairro else []
                
                def normalize_nome(nome):
                    return nome.upper().strip()
                
                def style_function(feature):
                    bairro_nome = normalize_nome(feature['properties'].get('EBAIRRNOME', ''))
                    
                    if bairros_selecionados_upper and bairro_nome in bairros_selecionados_upper:
                        return {
                            'fillColor': '#FF0000',
                            'color': '#000000',
                            'weight': 2,
                            'fillOpacity': 0.7
                        }
                    else:
                        return {
                            'fillColor': '#90EE90',
                            'color': '#000000',
                            'weight': 1,
                            'fillOpacity': 0.4
                        }
                
                def highlight_function(feature):
                    return {
                        'fillColor': '#FFFF00',
                        'color': '#FF8C00',
                        'weight': 3,
                        'fillOpacity': 0.9
                    }
                
                folium.GeoJson(
                    geojson_data,
                    style_function=style_function,
                    highlight_function=highlight_function,
                    tooltip=folium.GeoJsonTooltip(
                        fields=['EBAIRRNOME'],
                        aliases=['Bairro:'],
                        localize=True
                    )
                ).add_to(m)
            
            html(m._repr_html_(), height=600)
        else:
            st.info("Sem dados georreferenciados para o período selecionado.")
        
        st.markdown('<div class="summary-box">', unsafe_allow_html=True)
        st.markdown("### 📊 Resumo dos Dados")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏘️ Bairros", len(dff['bairro'].unique()) if not dff.empty else 0)
        with col2:
            st.metric("⚠️ Ocorrências Totais", int(dff['ocorrencias'].sum()) if not dff.empty else 0)
        with col3:
            st.metric("🌡️ Vulnerabilidade Média", f"{dff['vulnerabilidade'].mean():.2f}" if not dff.empty else "0.00")
        with col4:
            st.metric("📅 Registros", int(dff.shape[0]) if not dff.empty else 0)
        st.markdown('</div>', unsafe_allow_html=True)

    elif page == "⚠️ Alertas e Previsões":
        st.title("⚠️ Alertas e Previsões de Risco")
        
        st.markdown("### 🎯 Calcular Risco Futuro")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            chuva_in = st.number_input("Chuva (mm)", value=10.0, step=0.5, min_value=0.0)
        with col2:
            mare_in = st.number_input("Maré (m)", value=0.8, step=0.05, min_value=0.0)
        with col3:
            vuln_in = st.slider("Vulnerabilidade", 0.0, 1.0, 0.3, 0.01)
        
        if (models_dir / 'linear_regression_occ.joblib').exists() and (models_dir / 'logistic_risk.joblib').exists():
            if st.button("🎯 Calcular Risco", use_container_width=True, type="primary"):
                lr = joblib.load(models_dir / 'linear_regression_occ.joblib')
                clf = joblib.load(models_dir / 'logistic_risk.joblib')
                features_reg = joblib.load(models_dir / 'features_regression.joblib')
                features_clf = joblib.load(models_dir / 'features_classification.joblib')
                
                def z(x, arr): return (x - arr.mean()) / (arr.std()+1e-9)
                chuva_z = z(chuva_in, df['chuva_mm'])
                mare_z = z(mare_in, df['mare_m'])
                vuln_z = z(vuln_in, df['vulnerabilidade'])
                
                feature_dict_reg = {
                    'chuva_mm_z': chuva_z,
                    'mare_m_z': mare_z,
                    'vulnerabilidade_z': vuln_z,
                    'chuva_x_vuln': chuva_z * vuln_z,
                    'mare_x_vuln': mare_z * vuln_z,
                    'chuva_x_mare': chuva_z * mare_z,
                    'chuva_sq': chuva_z ** 2,
                    'mare_sq': mare_z ** 2,
                    'estacao_chuvosa': 1,
                    'densidade_pop_z': 0.0,
                    'altitude_z': 0.0
                }
                X_reg = [[feature_dict_reg.get(f, 0.0) for f in features_reg]]
                
                feature_dict_clf = {
                    'chuva_mm_z': chuva_z,
                    'mare_m_z': mare_z,
                    'vulnerabilidade_z': vuln_z,
                    'chuva_x_vuln': chuva_z * vuln_z,
                    'mare_x_vuln': mare_z * vuln_z,
                    'chuva_sq': chuva_z ** 2,
                    'estacao_chuvosa': 1,
                    'densidade_pop_z': 0.0,
                    'altitude_z': 0.0
                }
                X_clf = [[feature_dict_clf.get(f, 0.0) for f in features_clf]]
                
                pred_occ = lr.predict(X_reg)[0]
                prob_risk = clf.predict_proba(X_clf)[0,1]
                
                st.markdown("---")
                st.markdown("### 📈 Resultado da Previsão")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Ocorrências Previstas", f"{pred_occ:.1f}")
                with col2:
                    st.metric("Probabilidade de Risco", f"{prob_risk:.0%}")
                with col3:
                    if prob_risk > 0.7:
                        st.error("🔴 RISCO ALTO")
                    elif prob_risk > 0.5:
                        st.warning("🟡 RISCO MODERADO")
                    else:
                        st.success("🟢 RISCO BAIXO")
                
                if prob_risk > 0.7:
                    st.error("⚠️ **ALERTA:** Condições de alto risco! Recomenda-se atenção especial e possível evacuação de áreas vulneráveis.")
                elif prob_risk > 0.5:
                    st.warning("⚡ **ATENÇÃO:** Risco moderado. Monitorar situação e preparar medidas preventivas.")
                else:
                    st.success("✅ **SEGURO:** Condições dentro da normalidade. Manter monitoramento de rotina.")
        else:
            st.info("⚙️ Modelos não encontrados. Execute: `python src/models/train_models.py`")
        
        st.markdown("---")
        st.markdown("### 📍 Locais Monitorados (por risco)")
        
        if df is not None and not df.empty:
            grouped_overall = df.groupby('bairro').agg({
                'lat':'first',
                'lon':'first',
                'ocorrencias':'sum',
                'vulnerabilidade':'mean'
            }).reset_index()
            
            grouped_overall['risk_score'] = grouped_overall['ocorrencias'] + grouped_overall['vulnerabilidade'] * 10
            grouped_overall = grouped_overall.sort_values('risk_score', ascending=False)
            
            for i, row in grouped_overall.head(10).iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    icon = "🔴" if row['risk_score'] > 15 else "🟡" if row['risk_score'] > 8 else "🟢"
                    st.markdown(f"{icon} **{row['bairro']}**")
                
                with col2:
                    st.caption(f"Ocorr: {int(row['ocorrencias'])}")
                
                with col3:
                    st.caption(f"Vuln: {row['vulnerabilidade']:.2f}")

    elif page == "📊 Análises Detalhadas":
        st.title("📊 Análises Detalhadas")
        
        st.markdown("### Selecione a análise:")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🌊 Marés × Chuva", use_container_width=True, type="primary"):
                st.session_state['analysis_view'] = 'tides'
        
        with col2:
            if st.button("☁️ Clima e Correlações", use_container_width=True, type="primary"):
                st.session_state['analysis_view'] = 'weather'
        
        if 'analysis_view' not in st.session_state:
            st.session_state['analysis_view'] = 'tides'
        
        st.markdown("---")
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔍 Filtros de Análise")
        period_analysis = st.sidebar.selectbox("Período", ["Últimos 7 dias","Últimos 30 dias","Últimos 90 dias"], index=1, key="period_analysis")
        
        start_date = None
        if period_analysis == "Últimos 7 dias":
            start_date = df['date'].max() - pd.Timedelta(days=7)
        elif period_analysis == "Últimos 30 dias":
            start_date = df['date'].max() - pd.Timedelta(days=30)
        elif period_analysis == "Últimos 90 dias":
            start_date = df['date'].max() - pd.Timedelta(days=90)
        
        dff_analysis = df.copy()
        if start_date is not None:
            dff_analysis = dff_analysis[dff_analysis['date'] >= start_date]
        
        if st.session_state['analysis_view'] == 'tides':
            st.markdown("## 🌊 Análise: Marés × Chuva")
            st.markdown("_Compreenda como a combinação de chuva e maré influencia o risco de alagamento_")
            st.markdown("---")
            
            st.markdown("### 📈 Evolução Temporal: Chuva e Maré")
            ts = dff_analysis.groupby('date').agg({
                'chuva_mm': 'mean',
                'mare_m': 'mean',
                'ocorrencias': 'sum'
            }).reset_index()
            
            if not ts.empty and px is not None:
                fig = px.line(ts, x='date', y=['chuva_mm', 'mare_m'],
                             labels={'value': 'Valor', 'variable': 'Variável', 'date': 'Data'},
                             color_discrete_map={'chuva_mm': '#1f77b4', 'mare_m': '#ff7f0e'})
                fig.update_layout(
                    height=400,
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        title=None
                    )
                )
                fig.update_traces(line=dict(width=2.5))
                st.plotly_chart(fig, use_container_width=True)
                
                st.info("💡 **Interpretação:** As linhas mostram como chuva e maré variam ao longo do tempo. Picos simultâneos (ambas altas) indicam maior risco de alagamento.")
                
                st.markdown("### 🔵 Relação: Maré × Chuva")
                
                scatter_data = dff_analysis.copy()
                scatter_data['risco_nivel'] = pd.cut(
                    scatter_data['ocorrencias'],
                    bins=[-1, 0, 1, 999],
                    labels=['Sem ocorrências', 'Baixo', 'Alto']
                )
                
                fig_scatter = px.scatter(
                    scatter_data,
                    x='mare_m',
                    y='chuva_mm',
                    color='risco_nivel',
                    size='ocorrencias',
                    color_discrete_map={
                        'Sem ocorrências': '#90EE90',
                        'Baixo': '#FFD700',
                        'Alto': '#FF6B6B'
                    },
                    labels={
                        'mare_m': 'Nível de Maré (m)',
                        'chuva_mm': 'Chuva (mm)',
                        'risco_nivel': 'Nível de Risco'
                    },
                    opacity=0.6
                )
                fig_scatter.update_layout(height=450)
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                st.info("💡 **Interpretação:** Cada ponto representa um dia em um bairro. Pontos vermelhos (alto risco) tendem a aparecer quando **maré E chuva** são altas simultaneamente.")
                
                st.markdown("### ⚠️ Momentos Críticos: Picos Simultâneos")
                
                ts_picos = ts.copy()
                ts_picos['chuva_alta'] = ts_picos['chuva_mm'] > ts_picos['chuva_mm'].quantile(0.75)
                ts_picos['mare_alta'] = ts_picos['mare_m'] > ts_picos['mare_m'].quantile(0.75)
                ts_picos['pico_simultaneo'] = ts_picos['chuva_alta'] & ts_picos['mare_alta']
                
                dias_criticos = ts_picos[ts_picos['pico_simultaneo']].shape[0]
                total_dias = len(ts_picos)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🔴 Dias Críticos", f"{dias_criticos}")
                    st.caption("Maré E chuva altas")
                with col2:
                    st.metric("📊 Total de Dias", f"{total_dias}")
                    st.caption("No período analisado")
                with col3:
                    perc_critico = (dias_criticos / total_dias * 100) if total_dias > 0 else 0
                    st.metric("⚡ % Crítico", f"{perc_critico:.1f}%")
                    st.caption("Frequência de risco")
                
                if dias_criticos > 0:
                    st.warning(f"⚠️ **Atenção:** Foram identificados **{dias_criticos} dias críticos** no período, representando {perc_critico:.1f}% do tempo. Nestes momentos, a combinação de maré alta e chuva intensa eleva significativamente o risco de alagamento, especialmente em áreas litorâneas e ribeirinhas.")
                else:
                    st.success("✅ **Condições Favoráveis:** Não houve momentos críticos com picos simultâneos no período analisado.")
                
                st.markdown("### 📊 Estatísticas do Período")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🌊 Maré Média", f"{dff_analysis['mare_m'].mean():.2f}m")
                with col2:
                    st.metric("📈 Maré Máxima", f"{dff_analysis['mare_m'].max():.2f}m")
                with col3:
                    st.metric("🌧️ Chuva Média", f"{dff_analysis['chuva_mm'].mean():.1f}mm")
                with col4:
                    st.metric("💧 Chuva Total", f"{dff_analysis['chuva_mm'].sum():.0f}mm")
                
                if len(dff_analysis) > 1:
                    corr_value = dff_analysis[['mare_m', 'chuva_mm']].corr().iloc[0, 1]
                    
                    if corr_value > 0.3:
                        corr_msg = "forte relação positiva"
                        corr_color = "error"
                    elif corr_value > 0:
                        corr_msg = "relação positiva moderada"
                        corr_color = "warning"
                    else:
                        corr_msg = "relação fraca ou ausente"
                        corr_color = "info"
                    
                    if corr_color == "error":
                        st.error(f"📈 **Correlação:** {corr_value:.3f} - Indica {corr_msg}. Quando uma sobe, a outra tende a subir também.")
                    elif corr_color == "warning":
                        st.warning(f"📈 **Correlação:** {corr_value:.3f} - Indica {corr_msg}. Há alguma tendência de variação conjunta.")
                    else:
                        st.info(f"📈 **Correlação:** {corr_value:.3f} - Indica {corr_msg}. As variações são independentes.")
            else:
                st.warning("Dados insuficientes para análise de marés.")
        
        elif st.session_state['analysis_view'] == 'weather':
            st.markdown("## ☁️ Análise: Clima e Influência no Risco")
            st.markdown("_Entenda como as condições climáticas impactam as ocorrências de alagamento_")
            st.markdown("---")
            
            if not dff_analysis.empty:
                st.markdown("### 🌧️ Impacto da Chuva no Risco")
                
                scatter_chuva = dff_analysis.copy()
                scatter_chuva['faixa_chuva'] = pd.cut(
                    scatter_chuva['chuva_mm'],
                    bins=[0, 10, 25, 50, 999],
                    labels=['Leve (<10mm)', 'Moderada (10-25mm)', 'Forte (25-50mm)', 'Intensa (>50mm)']
                )
                
                fig_chuva = px.scatter(
                    scatter_chuva,
                    x='chuva_mm',
                    y='ocorrencias',
                    color='vulnerabilidade',
                    size='ocorrencias',
                    color_continuous_scale='Reds',
                    labels={
                        'chuva_mm': 'Precipitação (mm)',
                        'ocorrencias': 'Ocorrências',
                        'vulnerabilidade': 'Vulnerabilidade'
                    },
                    opacity=0.6,
                    trendline="lowess"
                )
                fig_chuva.update_layout(height=450)
                st.plotly_chart(fig_chuva, use_container_width=True)
                
                st.info("💡 **Interpretação:** Cada ponto representa um dia/bairro. A linha de tendência mostra que **quanto maior a chuva, maior o número de ocorrências**. Pontos mais vermelhos indicam áreas mais vulneráveis.")
                
                st.markdown("### 📦 Distribuição de Risco por Intensidade de Chuva")
                
                fig_box = px.box(
                    scatter_chuva,
                    x='faixa_chuva',
                    y='ocorrencias',
                    color='faixa_chuva',
                    labels={
                        'faixa_chuva': 'Intensidade da Chuva',
                        'ocorrencias': 'Número de Ocorrências'
                    },
                    color_discrete_sequence=['#90EE90', '#FFD700', '#FFA500', '#FF6B6B']
                )
                fig_box.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_box, use_container_width=True)
                
                st.info("💡 **Interpretação:** As caixas mostram a variação típica de ocorrências para cada faixa de chuva. **Chuvas intensas** (>50mm) geram consistentemente mais ocorrências, com valores máximos muito superiores.")
                
                st.markdown("### 📊 Risco Médio por Condição Climática")
                
                risco_por_faixa = scatter_chuva.groupby('faixa_chuva', observed=True).agg({
                    'ocorrencias': 'mean',
                    'vulnerabilidade': 'mean'
                }).reset_index()
                
                fig_bar = px.bar(
                    risco_por_faixa,
                    x='faixa_chuva',
                    y='ocorrencias',
                    color='ocorrencias',
                    labels={
                        'faixa_chuva': 'Intensidade da Chuva',
                        'ocorrencias': 'Ocorrências Médias'
                    },
                    color_continuous_scale='Reds',
                    text_auto='.2f'
                )
                fig_bar.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
                
                media_leve = risco_por_faixa[risco_por_faixa['faixa_chuva'] == 'Leve (<10mm)']['ocorrencias'].values
                media_intensa = risco_por_faixa[risco_por_faixa['faixa_chuva'] == 'Intensa (>50mm)']['ocorrencias'].values
                
                if len(media_leve) > 0 and len(media_intensa) > 0:
                    fator = media_intensa[0] / media_leve[0] if media_leve[0] > 0 else 0
                    st.warning(f"⚠️ **Destaque:** Chuvas intensas geram em média **{fator:.1f}x mais ocorrências** do que chuvas leves, evidenciando o impacto direto da precipitação no risco.")
                
                st.markdown("### 🎯 Relação: Vulnerabilidade × Precipitação")
                
                fig_vuln = px.density_heatmap(
                    dff_analysis,
                    x='vulnerabilidade',
                    y='chuva_mm',
                    z='ocorrencias',
                    color_continuous_scale='YlOrRd',
                    labels={
                        'vulnerabilidade': 'Vulnerabilidade do Bairro',
                        'chuva_mm': 'Precipitação (mm)',
                        'ocorrencias': 'Densidade de Ocorrências'
                    },
                    nbinsx=20,
                    nbinsy=20
                )
                fig_vuln.update_layout(height=450)
                st.plotly_chart(fig_vuln, use_container_width=True)
                
                st.info("💡 **Interpretação:** Áreas mais escuras concentram maior número de ocorrências. Observa-se que **bairros mais vulneráveis** (à direita) sofrem mais impacto, mesmo com chuvas moderadas.")
                
                st.markdown("### 🌧️ Distribuição de Precipitação")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig_hist = px.histogram(
                        dff_analysis,
                        x='chuva_mm',
                        nbins=30,
                        labels={'chuva_mm': 'Precipitação (mm)'},
                        color_discrete_sequence=['#1f77b4']
                    )
                    fig_hist.update_layout(height=350, showlegend=False)
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with col2:
                    st.markdown("#### 📈 Estatísticas")
                    st.metric("Dias com Chuva", int((dff_analysis['chuva_mm'] > 0).sum()))
                    st.metric("Média Diária", f"{dff_analysis['chuva_mm'].mean():.1f}mm")
                    st.metric("Desvio Padrão", f"{dff_analysis['chuva_mm'].std():.1f}mm")
                    st.metric("Máximo Registrado", f"{dff_analysis['chuva_mm'].max():.1f}mm")
                
                st.info("💡 **Interpretação:** O histograma mostra a frequência de diferentes volumes de chuva. A maioria dos dias tem chuva leve a moderada, mas eventos extremos (picos à direita) são os mais críticos.")
                
            else:
                st.warning("Dados insuficientes para análise climática.")

def print_windows_instructions():
    cmds = [
        "cd c:\\PENTES\\RecifeSafe",
        "python -m venv .venv",
        ".\\.venv\\Scripts\\Activate.ps1",
        "python -m pip install --upgrade pip",
        "pip install -r requirements.txt",
        "python src\\data\\generate_simulated_data.py",
        "python src\\models\\train_models.py",
        "streamlit run src\\dashboard\\app.py",
        "",
        "start \"\" \"%CD%\\src\\dashboard\\templates\\map_view.html\""
    ]
    print("\\nComandos PowerShell para Windows:\\n")
    for c in cmds:
        print(c)
    print("")

if args.instructions:
    print_windows_instructions()
    sys.exit(0)
