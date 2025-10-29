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
args, _ = parser.parse_known_args()

try:
    import streamlit as st
    from streamlit.components.v1 import html
except Exception:
    print("Streamlit não encontrado. Instale as dependências:")
    print("  pip install -r requirements.txt")
    print("  streamlit run src\\dashboard\\app.py")
    sys.exit(1)

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

repo_root = Path(__file__).resolve().parents[2]
logo_path = repo_root / 'img' / 'logo.png'

st.set_page_config(
    layout="wide", 
    page_title="RecifeSafe",
    page_icon=str(logo_path) if logo_path.exists() else "�"
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

    # Estilos CSS e Font Awesome
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
        .main .block-container { padding-top: 1rem; max-width: 100%; }
        [data-testid="stMetricValue"] { font-size: 1.5rem; }
        .stButton > button { 
            border-radius: 8px; 
            font-weight: 600; 
            transition: all 0.3s ease;
            padding: 0.75rem 1.5rem;
            font-size: 1.05rem;
        }
        .stButton > button:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 6px 16px rgba(0,0,0,0.2); 
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
            border: none;
        }
        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #c82333 0%, #bd2130 100%);
        }
        iframe { width: 100% !important; border: none; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .summary-box { background: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin-top: 1rem; }
        .nav-icon { margin-right: 8px; font-size: 1.1em; vertical-align: middle; }
        .section-icon { margin-right: 10px; color: #dc3545; font-size: 1.2em; }
        .metric-icon { font-size: 1.5em; margin-right: 8px; opacity: 0.8; }
        h1 i, h2 i, h3 i { margin-right: 12px; color: #dc3545; }
        [data-testid="stRadio"] label { font-size: 1.05em; padding: 8px; transition: all 0.2s ease; }
        [data-testid="stRadio"] label:hover { background-color: rgba(220, 53, 69, 0.05); border-radius: 4px; }
        /* Alinhamento dos botões de análise */
        [data-testid="column"] { 
            display: flex; 
            flex-direction: column; 
            justify-content: flex-start; 
        }
        [data-testid="column"] > div { 
            width: 100%; 
        }
        /* Alertas personalizados */
        .custom-alert {
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
            display: flex;
            align-items: flex-start;
            line-height: 1.6;
        }
        .custom-alert i {
            margin-right: 10px;
            font-size: 1.2em;
            margin-top: 2px;
        }
        </style>
    """, unsafe_allow_html=True)

    logobar_path = repo_root / 'img' / 'logobar.png'
    if logobar_path.exists():
        st.sidebar.image(str(logobar_path), width='stretch')
    else:
        st.sidebar.markdown('<h2 style="text-align: center;"><i class="fas fa-city"></i> RecifeSafe</h2>', unsafe_allow_html=True)
    
    # Navegação com ícones profissionais
    st.sidebar.markdown("---")
    page = st.sidebar.radio(
        "Navegação",
        [
            "Mapa de Risco",
            "Alertas e Previsões",
            "Análises"
        ],
        format_func=lambda x: {
            "Mapa de Risco": "Mapa de Risco",
            "Alertas e Previsões": "Alertas e Previsões", 
            "Análises": "Análises"
        }[x]
    )
    
    # Adicionar ícones via CSS antes dos labels da navegação
    st.sidebar.markdown("""
        <style>
        [data-testid="stRadio"] label:nth-child(1)::before { content: "\\f279"; font-family: "Font Awesome 6 Free"; font-weight: 900; margin-right: 8px; }
        [data-testid="stRadio"] label:nth-child(2)::before { content: "\\f0f3"; font-family: "Font Awesome 6 Free"; font-weight: 900; margin-right: 8px; }
        [data-testid="stRadio"] label:nth-child(3)::before { content: "\\f200"; font-family: "Font Awesome 6 Free"; font-weight: 900; margin-right: 8px; }
        </style>
    """, unsafe_allow_html=True)

    if page == "Mapa de Risco":
        st.markdown('<h1><i class="fas fa-map-marked-alt"></i> Mapa de Risco — Recife</h1>', unsafe_allow_html=True)
        
        st.sidebar.markdown("---")
        st.sidebar.markdown('<h3><i class="fas fa-filter"></i> Filtros</h3>', unsafe_allow_html=True)
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
        st.markdown('<h3><i class="fas fa-chart-bar"></i> Resumo dos Dados</h3>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown('<p style="font-size: 0.9em; color: #666;"><i class="fas fa-building metric-icon"></i>Bairros</p>', unsafe_allow_html=True)
            st.metric("Bairros", len(dff['bairro'].unique()) if not dff.empty else 0, label_visibility="collapsed")
        with col2:
            st.markdown('<p style="font-size: 0.9em; color: #666;"><i class="fas fa-exclamation-triangle metric-icon"></i>Ocorrências Totais</p>', unsafe_allow_html=True)
            st.metric("Ocorrências Totais", int(dff['ocorrencias'].sum()) if not dff.empty else 0, label_visibility="collapsed")
        with col3:
            st.markdown('<p style="font-size: 0.9em; color: #666;"><i class="fas fa-shield-alt metric-icon"></i>Vulnerabilidade Média</p>', unsafe_allow_html=True)
            st.metric("Vulnerabilidade Média", f"{dff['vulnerabilidade'].mean():.2f}" if not dff.empty else "0.00", label_visibility="collapsed")
        with col4:
            st.markdown('<p style="font-size: 0.9em; color: #666;"><i class="fas fa-calendar-alt metric-icon"></i>Registros</p>', unsafe_allow_html=True)
            st.metric("Registros", int(dff.shape[0]) if not dff.empty else 0, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    elif page == "Alertas e Previsões":
        st.markdown('<h1><i class="fas fa-bell"></i> Alertas e Previsões de Risco</h1>', unsafe_allow_html=True)
        
        st.markdown('<h3><i class="fas fa-calculator"></i> Calcular Risco Futuro</h3>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            chuva_in = st.number_input("Chuva (mm)", value=10.0, step=0.5, min_value=0.0)
        with col2:
            mare_in = st.number_input("Maré (m)", value=0.8, step=0.05, min_value=0.0)
        with col3:
            vuln_in = st.slider("Vulnerabilidade", 0.0, 1.0, 0.3, 0.01)
        
        if (models_dir / 'linear_regression_occ.joblib').exists() and (models_dir / 'logistic_risk.joblib').exists():
            # Adicionar ícone ao botão via CSS
            st.markdown("""
                <style>
                [data-testid="stButton"] button[kind="primary"] {
                    position: relative;
                }
                [data-testid="stButton"] button[kind="primary"]::before {
                    content: "\\f3a5";
                    font-family: "Font Awesome 6 Free";
                    font-weight: 900;
                    margin-right: 8px;
                }
                </style>
            """, unsafe_allow_html=True)
            if st.button("Calcular Risco", use_container_width=True, type="primary"):
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
                st.markdown('<h3><i class="fas fa-chart-line"></i> Resultado da Previsão</h3>', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown('<p style="font-size: 0.9em; color: #666;"><i class="fas fa-tachometer-alt metric-icon"></i>Ocorrências Previstas</p>', unsafe_allow_html=True)
                    st.metric("Ocorrências Previstas", f"{pred_occ:.1f}", label_visibility="collapsed")
                with col2:
                    st.markdown('<p style="font-size: 0.9em; color: #666;"><i class="fas fa-percentage metric-icon"></i>Probabilidade de Risco</p>', unsafe_allow_html=True)
                    st.metric("Probabilidade de Risco", f"{prob_risk:.0%}", label_visibility="collapsed")
                with col3:
                    if prob_risk > 0.7:
                        st.markdown('<div style="text-align: center; padding: 20px; background: #f8d7da; border-radius: 8px; border-left: 4px solid #dc3545;"><i class="fas fa-exclamation-circle" style="font-size: 2em; color: #dc3545;"></i><br><strong style="color: #721c24;">RISCO ALTO</strong></div>', unsafe_allow_html=True)
                    elif prob_risk > 0.5:
                        st.markdown('<div style="text-align: center; padding: 20px; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;"><i class="fas fa-exclamation-triangle" style="font-size: 2em; color: #ffc107;"></i><br><strong style="color: #856404;">RISCO MODERADO</strong></div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="text-align: center; padding: 20px; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745;"><i class="fas fa-check-circle" style="font-size: 2em; color: #28a745;"></i><br><strong style="color: #155724;">RISCO BAIXO</strong></div>', unsafe_allow_html=True)
                
                if prob_risk > 0.7:
                    st.markdown('<div style="padding: 1rem; background-color: #f8d7da; border-left: 4px solid #dc3545; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #721c24;"><i class="fas fa-exclamation-triangle" style="margin-right: 8px; color: #dc3545;"></i><strong>ALERTA:</strong> Condições de alto risco! Recomenda-se atenção especial e possível evacuação de áreas vulneráveis.</p></div>', unsafe_allow_html=True)
                elif prob_risk > 0.5:
                    st.markdown('<div style="padding: 1rem; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #856404;"><i class="fas fa-bolt" style="margin-right: 8px; color: #ffc107;"></i><strong>ATENÇÃO:</strong> Risco moderado. Monitorar situação e preparar medidas preventivas.</p></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="padding: 1rem; background-color: #d4edda; border-left: 4px solid #28a745; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #155724;"><i class="fas fa-check-circle" style="margin-right: 8px; color: #28a745;"></i><strong>SEGURO:</strong> Condições dentro da normalidade. Manter monitoramento de rotina.</p></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="padding: 1rem; background-color: #d1ecf1; border-left: 4px solid #0c5460; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #0c5460;"><i class="fas fa-info-circle" style="margin-right: 8px;"></i>Modelos não encontrados. Execute: <code>python src/models/train_models.py</code></p></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown('<h3><i class="fas fa-map-marker-alt"></i> Locais Monitorados (por risco)</h3>', unsafe_allow_html=True)
        
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
                    if row['risk_score'] > 15:
                        icon_html = '<i class="fas fa-circle" style="color: #dc3545;"></i>'
                    elif row['risk_score'] > 8:
                        icon_html = '<i class="fas fa-circle" style="color: #ffc107;"></i>'
                    else:
                        icon_html = '<i class="fas fa-circle" style="color: #28a745;"></i>'
                    st.markdown(f"{icon_html} **{row['bairro']}**", unsafe_allow_html=True)
                
                with col2:
                    st.caption(f"Ocorr: {int(row['ocorrencias'])}")
                
                with col3:
                    st.caption(f"Vuln: {row['vulnerabilidade']:.2f}")

    elif page == "Análises":
        st.markdown('<h1><i class="fas fa-chart-pie"></i> Análises Detalhadas</h1>', unsafe_allow_html=True)
        
        st.markdown('<h3><i class="fas fa-list-ul"></i> Selecione a análise:</h3>', unsafe_allow_html=True)
        
        # Botões de análise estilizados e alinhados
        st.markdown("""
            <style>
            .analysis-button-container {
                display: flex;
                gap: 1rem;
                margin: 1.5rem 0;
            }
            .analysis-button {
                flex: 1;
                padding: 1.2rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                text-align: center;
            }
            .analysis-button:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
            }
            .analysis-button.weather {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                box-shadow: 0 4px 15px rgba(240, 147, 251, 0.4);
            }
            .analysis-button.weather:hover {
                box-shadow: 0 6px 20px rgba(240, 147, 251, 0.6);
            }
            .analysis-button i {
                margin-right: 10px;
                font-size: 1.3em;
            }
            </style>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Marés × Chuva", use_container_width=True, type="primary", key="btn_tides"):
                st.session_state['analysis_view'] = 'tides'
        
        with col2:
            if st.button("Clima e Correlações", use_container_width=True, type="primary", key="btn_weather"):
                st.session_state['analysis_view'] = 'weather'
        
        if 'analysis_view' not in st.session_state:
            st.session_state['analysis_view'] = 'tides'
        
        st.markdown("---")
        
        st.sidebar.markdown("---")
        st.sidebar.markdown('<h3><i class="fas fa-sliders-h"></i> Filtros de Análise</h3>', unsafe_allow_html=True)
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
            st.markdown('<h2><i class="fas fa-water"></i> Análise: Marés × Chuva</h2>', unsafe_allow_html=True)
            st.markdown("_Compreenda como a combinação de chuva e maré influencia o risco de alagamento_")
            st.markdown("---")
            
            st.markdown('<h3><i class="fas fa-chart-area"></i> Evolução Temporal: Chuva e Maré</h3>', unsafe_allow_html=True)
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
                
                st.markdown('<div style="padding: 1rem; background-color: #d1ecf1; border-left: 4px solid #0c5460; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #0c5460;"><i class="fas fa-lightbulb" style="margin-right: 8px;"></i><strong>Interpretação:</strong> As linhas mostram como chuva e maré variam ao longo do tempo. Picos simultâneos (ambas altas) indicam maior risco de alagamento.</p></div>', unsafe_allow_html=True)
                
                st.markdown('<h3><i class="fas fa-project-diagram"></i> Relação: Maré × Chuva</h3>', unsafe_allow_html=True)
                
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
                
                st.markdown('<div style="padding: 1rem; background-color: #d1ecf1; border-left: 4px solid #0c5460; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #0c5460;"><i class="fas fa-lightbulb" style="margin-right: 8px;"></i><strong>Interpretação:</strong> Cada ponto representa um dia em um bairro. Pontos vermelhos (alto risco) tendem a aparecer quando <strong>maré E chuva</strong> são altas simultaneamente.</p></div>', unsafe_allow_html=True)
                
                st.markdown('<h3><i class="fas fa-exclamation-triangle"></i> Momentos Críticos: Picos Simultâneos</h3>', unsafe_allow_html=True)
                
                ts_picos = ts.copy()
                ts_picos['chuva_alta'] = ts_picos['chuva_mm'] > ts_picos['chuva_mm'].quantile(0.75)
                ts_picos['mare_alta'] = ts_picos['mare_m'] > ts_picos['mare_m'].quantile(0.75)
                ts_picos['pico_simultaneo'] = ts_picos['chuva_alta'] & ts_picos['mare_alta']
                
                dias_criticos = ts_picos[ts_picos['pico_simultaneo']].shape[0]
                total_dias = len(ts_picos)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown('<p style="font-size: 0.9em; color: #666;"><i class="fas fa-times-circle metric-icon" style="color: #dc3545;"></i>Dias Críticos</p>', unsafe_allow_html=True)
                    st.metric("Dias Críticos", f"{dias_criticos}", label_visibility="collapsed")
                    st.caption("Maré E chuva altas")
                with col2:
                    st.markdown('<p style="font-size: 0.9em; color: #666;"><i class="fas fa-calendar-check metric-icon"></i>Total de Dias</p>', unsafe_allow_html=True)
                    st.metric("Total de Dias", f"{total_dias}", label_visibility="collapsed")
                    st.caption("No período analisado")
                with col3:
                    perc_critico = (dias_criticos / total_dias * 100) if total_dias > 0 else 0
                    st.markdown('<p style="font-size: 0.9em; color: #666;"><i class="fas fa-bolt metric-icon" style="color: #ffc107;"></i>% Crítico</p>', unsafe_allow_html=True)
                    st.metric("% Crítico", f"{perc_critico:.1f}%", label_visibility="collapsed")
                    st.caption("Frequência de risco")
                
                if dias_criticos > 0:
                    st.markdown(f'<div style="padding: 1rem; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #856404;"><i class="fas fa-exclamation-triangle" style="margin-right: 8px; color: #ffc107;"></i><strong>Atenção:</strong> Foram identificados <strong>{dias_criticos} dias críticos</strong> no período, representando {perc_critico:.1f}% do tempo. Nestes momentos, a combinação de maré alta e chuva intensa eleva significativamente o risco de alagamento, especialmente em áreas litorâneas e ribeirinhas.</p></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="padding: 1rem; background-color: #d4edda; border-left: 4px solid #28a745; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #155724;"><i class="fas fa-check-circle" style="margin-right: 8px; color: #28a745;"></i><strong>Condições Favoráveis:</strong> Não houve momentos críticos com picos simultâneos no período analisado.</p></div>', unsafe_allow_html=True)
                
                st.markdown('<h3><i class="fas fa-chart-bar"></i> Estatísticas do Período</h3>', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown('<p style="font-size: 0.9em; color: #666;"><i class="fas fa-water metric-icon" style="color: #17a2b8;"></i>Maré Média</p>', unsafe_allow_html=True)
                    st.metric("Maré Média", f"{dff_analysis['mare_m'].mean():.2f}m", label_visibility="collapsed")
                with col2:
                    st.markdown('<p style="font-size: 0.9em; color: #666;"><i class="fas fa-arrow-up metric-icon" style="color: #dc3545;"></i>Maré Máxima</p>', unsafe_allow_html=True)
                    st.metric("Maré Máxima", f"{dff_analysis['mare_m'].max():.2f}m", label_visibility="collapsed")
                with col3:
                    st.markdown('<p style="font-size: 0.9em; color: #666;"><i class="fas fa-cloud-rain metric-icon" style="color: #6c757d;"></i>Chuva Média</p>', unsafe_allow_html=True)
                    st.metric("Chuva Média", f"{dff_analysis['chuva_mm'].mean():.1f}mm", label_visibility="collapsed")
                with col4:
                    st.markdown('<p style="font-size: 0.9em; color: #666;"><i class="fas fa-tint metric-icon" style="color: #007bff;"></i>Chuva Total</p>', unsafe_allow_html=True)
                    st.metric("Chuva Total", f"{dff_analysis['chuva_mm'].sum():.0f}mm", label_visibility="collapsed")
                
                if len(dff_analysis) > 1:
                    corr_value = dff_analysis[['mare_m', 'chuva_mm']].corr().iloc[0, 1]
                    
                    if corr_value > 0.3:
                        corr_msg = "forte relação positiva"
                        corr_icon = "fas fa-arrow-trend-up"
                        corr_color = "error"
                    elif corr_value > 0:
                        corr_msg = "relação positiva moderada"
                        corr_icon = "fas fa-chart-line"
                        corr_color = "warning"
                    else:
                        corr_msg = "relação fraca ou ausente"
                        corr_icon = "fas fa-minus"
                        corr_color = "info"
                    
                    if corr_color == "error":
                        st.markdown(f'<div style="padding: 1rem; background-color: #f8d7da; border-left: 4px solid #dc3545; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #721c24;"><i class="fas fa-chart-line" style="margin-right: 8px; color: #dc3545;"></i><strong>Correlação:</strong> {corr_value:.3f} - Indica {corr_msg}. Quando uma sobe, a outra tende a subir também.</p></div>', unsafe_allow_html=True)
                    elif corr_color == "warning":
                        st.markdown(f'<div style="padding: 1rem; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #856404;"><i class="fas fa-chart-line" style="margin-right: 8px; color: #ffc107;"></i><strong>Correlação:</strong> {corr_value:.3f} - Indica {corr_msg}. Há alguma tendência de variação conjunta.</p></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div style="padding: 1rem; background-color: #d1ecf1; border-left: 4px solid #0c5460; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #0c5460;"><i class="fas fa-chart-bar" style="margin-right: 8px;"></i><strong>Correlação:</strong> {corr_value:.3f} - Indica {corr_msg}. As variações são independentes.</p></div>', unsafe_allow_html=True)
            else:
                st.warning("Dados insuficientes para análise de marés.")
        
        elif st.session_state['analysis_view'] == 'weather':
            st.markdown('<h2><i class="fas fa-cloud-sun-rain"></i> Análise: Clima e Influência no Risco</h2>', unsafe_allow_html=True)
            st.markdown("_Entenda como as condições climáticas impactam as ocorrências de alagamento_")
            st.markdown("---")
            
            if not dff_analysis.empty:
                st.markdown('<h3><i class="fas fa-cloud-showers-heavy"></i> Impacto da Chuva no Risco</h3>', unsafe_allow_html=True)
                
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
                
                st.markdown('<div style="padding: 1rem; background-color: #d1ecf1; border-left: 4px solid #0c5460; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #0c5460;"><i class="fas fa-lightbulb" style="margin-right: 8px;"></i><strong>Interpretação:</strong> Cada ponto representa um dia/bairro. A linha de tendência mostra que <strong>quanto maior a chuva, maior o número de ocorrências</strong>. Pontos mais vermelhos indicam áreas mais vulneráveis.</p></div>', unsafe_allow_html=True)
                
                st.markdown('<h3><i class="fas fa-chart-box"></i> Distribuição de Risco por Intensidade de Chuva</h3>', unsafe_allow_html=True)
                
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
                
                st.markdown('<div style="padding: 1rem; background-color: #d1ecf1; border-left: 4px solid #0c5460; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #0c5460;"><i class="fas fa-lightbulb" style="margin-right: 8px;"></i><strong>Interpretação:</strong> As caixas mostram a variação típica de ocorrências para cada faixa de chuva. <strong>Chuvas intensas</strong> (>50mm) geram consistentemente mais ocorrências, com valores máximos muito superiores.</p></div>', unsafe_allow_html=True)
                
                st.markdown('<h3><i class="fas fa-chart-column"></i> Risco Médio por Condição Climática</h3>', unsafe_allow_html=True)
                
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
                    st.markdown(f'<div style="padding: 1rem; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #856404;"><i class="fas fa-star" style="margin-right: 8px; color: #ffc107;"></i><strong>Destaque:</strong> Chuvas intensas geram em média <strong>{fator:.1f}x mais ocorrências</strong> do que chuvas leves, evidenciando o impacto direto da precipitação no risco.</p></div>', unsafe_allow_html=True)
                
                st.markdown('<h3><i class="fas fa-crosshairs"></i> Relação: Vulnerabilidade × Precipitação</h3>', unsafe_allow_html=True)
                
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
                
                st.markdown('<div style="padding: 1rem; background-color: #d1ecf1; border-left: 4px solid #0c5460; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #0c5460;"><i class="fas fa-lightbulb" style="margin-right: 8px;"></i><strong>Interpretação:</strong> Áreas mais escuras concentram maior número de ocorrências. Observa-se que <strong>bairros mais vulneráveis</strong> (à direita) sofrem mais impacto, mesmo com chuvas moderadas.</p></div>', unsafe_allow_html=True)
                
                st.markdown('<h3><i class="fas fa-cloud-rain"></i> Distribuição de Precipitação</h3>', unsafe_allow_html=True)
                
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
                    st.markdown('<h4><i class="fas fa-chart-line"></i> Estatísticas</h4>', unsafe_allow_html=True)
                    st.markdown('<p style="font-size: 0.9em; color: #666;"><i class="fas fa-calendar-day metric-icon"></i>Dias com Chuva</p>', unsafe_allow_html=True)
                    st.metric("Dias com Chuva", int((dff_analysis['chuva_mm'] > 0).sum()), label_visibility="collapsed")
                    st.markdown('<p style="font-size: 0.9em; color: #666; margin-top: 10px;"><i class="fas fa-calculator metric-icon"></i>Média Diária</p>', unsafe_allow_html=True)
                    st.metric("Média Diária", f"{dff_analysis['chuva_mm'].mean():.1f}mm", label_visibility="collapsed")
                    st.markdown('<p style="font-size: 0.9em; color: #666; margin-top: 10px;"><i class="fas fa-wave-square metric-icon"></i>Desvio Padrão</p>', unsafe_allow_html=True)
                    st.metric("Desvio Padrão", f"{dff_analysis['chuva_mm'].std():.1f}mm", label_visibility="collapsed")
                    st.markdown('<p style="font-size: 0.9em; color: #666; margin-top: 10px;"><i class="fas fa-arrow-up-wide-short metric-icon"></i>Máximo Registrado</p>', unsafe_allow_html=True)
                    st.metric("Máximo Registrado", f"{dff_analysis['chuva_mm'].max():.1f}mm", label_visibility="collapsed")
                
                st.markdown('<div style="padding: 1rem; background-color: #d1ecf1; border-left: 4px solid #0c5460; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #0c5460;"><i class="fas fa-lightbulb" style="margin-right: 8px;"></i><strong>Interpretação:</strong> O histograma mostra a frequência de diferentes volumes de chuva. A maioria dos dias tem chuva leve a moderada, mas eventos extremos (picos à direita) são os mais críticos.</p></div>', unsafe_allow_html=True)
                
            else:
                st.markdown('<div style="padding: 1rem; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px; margin: 1rem 0;"><p style="margin: 0; color: #856404;"><i class="fas fa-exclamation-circle" style="margin-right: 8px; color: #ffc107;"></i>Dados insuficientes para análise climática.</p></div>', unsafe_allow_html=True)

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
