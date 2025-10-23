# Atualizar bloco de imports para ser tolerante a ambientes sem dependências
import os
from pathlib import Path

try:
    import joblib
except Exception:
    joblib = None

import numpy as np
import pandas as pd

try:
    from sklearn.linear_model import LinearRegression, LogisticRegression  # type: ignore
    from sklearn.preprocessing import StandardScaler  # type: ignore
    from sklearn.model_selection import train_test_split  # type: ignore
except Exception:
    # sklearn ausente: funções de treino irão falhar mais adiante com mensagem informativa
    LinearRegression = None
    LogisticRegression = None
    StandardScaler = None
    train_test_split = None

try:
    import folium  # usado apenas para gerar mapa HTML opcional
except Exception:
    folium = None

def prepare_features(df):
    df = df.copy()
    # agregação por bairro/date já presente; usamos padrões simples
    df['chuva_mm_z'] = (df['chuva_mm'] - df['chuva_mm'].mean()) / (df['chuva_mm'].std()+1e-9)
    df['mare_m_z'] = (df['mare_m'] - df['mare_m'].mean()) / (df['mare_m'].std()+1e-9)
    df['vulnerabilidade_z'] = (df['vulnerabilidade'] - df['vulnerabilidade'].mean()) / (df['vulnerabilidade'].std()+1e-9)
    return df

def train_and_save_models(csv_path, models_dir):
    if LinearRegression is None or LogisticRegression is None:
        raise RuntimeError("scikit-learn não está disponível no ambiente. Instale com: pip install scikit-learn")
    if joblib is None:
        raise RuntimeError("joblib não está disponível no ambiente. Instale com: pip install joblib")
    df = pd.read_csv(csv_path, parse_dates=['date'])
    df = prepare_features(df)
    # Regressão: chuva -> ocorrencias
    X_reg = df[['chuva_mm_z']].values
    y_reg = df['ocorrencias'].values
    lr = LinearRegression()
    lr.fit(X_reg, y_reg)
    # Classificação: risco_alto (threshold simples)
    threshold = 2
    df['risco_alto'] = ((df['ocorrencias'] >= threshold) | ((df['chuva_mm'] > df['chuva_mm'].quantile(0.9)) & (df['vulnerabilidade']>0.6))).astype(int)
    features = ['chuva_mm_z','mare_m_z','vulnerabilidade_z']
    X_clf = df[features].values
    y_clf = df['risco_alto'].values
    clf = LogisticRegression(max_iter=200)
    clf.fit(X_clf, y_clf)
    # Salvar modelos e scalers
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(lr, models_dir / 'linear_regression_occ.joblib')
    joblib.dump(clf, models_dir / 'logistic_risk.joblib')
    # Também salvar a lista de features
    joblib.dump(features, models_dir / 'features_list.joblib')
    print(f"Models saved to: {models_dir}")

def write_dashboard_app(repo_root: Path):
    """
    Cria um dashboard Streamlit mínimo em src/dashboard/app.py se o arquivo não existir.
    """
    content = '''import streamlit as st
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from streamlit.components.v1 import html
import joblib

st.set_page_config(layout="wide", page_title="RecifeSafe Dashboard (Fase 2)")

repo_root = Path(__file__).resolve().parents[2]
data_csv = repo_root / 'data' / 'processed' / 'simulated_daily.csv'
models_dir = repo_root / 'models'

st.title("RecifeSafe — Dashboard (Fase 2)")
st.markdown("Resumo rápido: filtros à esquerda, visualizações à direita. Use os scripts em src/data e src/models para gerar dados e treinar modelos.")

if not data_csv.exists():
    st.warning(f"Dados não encontrados em {data_csv}. Rode: python src/data/generate_simulated_data.py")
else:
    df = pd.read_csv(data_csv, parse_dates=['date'])
    df['date'] = pd.to_datetime(df['date'])
    bairros = sorted(df['bairro'].unique())
    # Sidebar filters
    st.sidebar.header("Filtros")
    sel_bairro = st.sidebar.multiselect("Bairro", options=bairros, default=bairros[:3])
    date_min = df['date'].min()
    date_max = df['date'].max()
    sel_period = st.sidebar.date_input("Período", value=(date_min.date(), date_max.date()))
    # apply filters
    mask = df['bairro'].isin(sel_bairro) & (df['date'].dt.date >= sel_period[0]) & (df['date'].dt.date <= sel_period[1])
    dff = df[mask]
    st.subheader("Visão Geral")
    col1, col2 = st.columns([2,1])
    with col1:
        # time series: chuva média vs ocorrências soma (7-day rolling)
        ts = dff.groupby('date').agg({'chuva_mm':'mean','ocorrencias':'sum'}).rolling(7, min_periods=1).mean()
        fig = px.line(ts.reset_index(), x='date', y=['chuva_mm','ocorrencias'], labels={'value':'Valor','date':'Data'}, title="Chuva (média 7d) × Ocorrências (soma 7d)")
        st.plotly_chart(fig, use_container_width=True)
        # scatter chuva x mare color risco proxy
        fig2 = px.scatter(dff, x='chuva_mm', y='mare_m', color='vulnerabilidade', size='ocorrencias', title='Dispersão: chuva × maré (vulnerabilidade colorida)')
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        st.markdown("### Estatísticas rápidas")
        st.metric("Registros", len(dff))
        st.metric("Ocorrências (total)", int(dff['ocorrencias'].sum()))
        st.metric("Chuva média (mm)", round(dff['chuva_mm'].mean(),2))
    # Boxplot chuva por bairro
    st.subheader("Boxplot: chuva por bairro")
    fig_box = px.box(dff, x='bairro', y='chuva_mm', color='bairro')
    st.plotly_chart(fig_box, use_container_width=True)
    # Map (folium)
    st.subheader("Mapa: bairros selecionados (centroide)")
    if not dff.empty:
        m = folium.Map(location=[float(dff['lat'].mean()), float(dff['lon'].mean())], zoom_start=12)
        grouped = dff.groupby('bairro').agg({'lat':'first','lon':'first','ocorrencias':'sum','vulnerabilidade':'mean'}).reset_index()
        for _, r in grouped.iterrows():
            color = 'green'
            if r['ocorrencias']>10 or r['vulnerabilidade']>0.6:
                color='red'
            elif r['ocorrencias']>3:
                color='orange'
            folium.CircleMarker(location=[r['lat'], r['lon']],
                                radius=6 + min(int(r['ocorrencias']),10),
                                color=color,
                                fill=True,
                                tooltip=f"{r['bairro']}: ocorr={int(r['ocorrencias'])}, vuln={r['vulnerabilidade']:.2f}"
                               ).add_to(m)
        html(m._repr_html_(), height=450)
    else:
        st.info("Sem dados para o período/bairro selecionado.")
    # Load models if available
    st.sidebar.header("Previsão em Tempo Real")
    if (models_dir / 'linear_regression_occ.joblib').exists() and (models_dir / 'logistic_risk.joblib').exists():
        lr = joblib.load(models_dir / 'linear_regression_occ.joblib')
        clf = joblib.load(models_dir / 'logistic_risk.joblib')
        # simple inputs
        chuva_in = st.sidebar.number_input("Chuva (mm)", value=10.0, step=0.1)
        mare_in = st.sidebar.number_input("Maré (m)", value=0.8, step=0.01)
        vuln_in = st.sidebar.slider("Vulnerabilidade (0-1)", min_value=0.0, max_value=1.0, value=0.3, step=0.01)
        # compute z-scores using dataset stats (simple)
        def z(x, arr): return (x - arr.mean()) / (arr.std()+1e-9)
        chuva_z = z(chuva_in, df['chuva_mm'])
        mare_z = z(mare_in, df['mare_m'])
        vuln_z = z(vuln_in, df['vulnerabilidade'])
        pred_occ = lr.predict(np.array([[chuva_z]]))[0]
        prob_risk = clf.predict_proba(np.array([[chuva_z, mare_z, vuln_z]]))[0,1]
        st.sidebar.markdown(f"**Previsão ocorrências (média):** {pred_occ:.2f}")
        st.sidebar.markdown(f"**Probabilidade risco alto:** {prob_risk:.2f}")
    else:
        st.sidebar.info("Modelos não encontrados. Rode: python src/models/train_models.py")
    # Alertas: bairros com risco alto (simples rule)
    st.subheader("Alertas — bairros com risco alto (regra simples)")
    if not dff.empty:
        grouped = dff.groupby('bairro').agg({'lat':'first','lon':'first','ocorrencias':'sum','vulnerabilidade':'mean'}).reset_index()
        alerts = grouped[(grouped['ocorrencias']>=2) | (grouped['vulnerabilidade']>0.6)]
        if alerts.empty:
            st.success("Nenhum bairro em risco alto no período selecionado")
        else:
            for _, r in alerts.iterrows():
                st.warning(f"{r['bairro']}: ocorrências={int(r['ocorrencias'])}, vulnerabilidade={r['vulnerabilidade']:.2f}")
    else:
        st.info("Sem registros agregados para alertas.")
'''
    out_path = repo_root / 'src' / 'dashboard' / 'app.py'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not out_path.exists():
        out_path.write_text(content, encoding='utf-8')
        print(f"Dashboard criado em: {out_path}")
    else:
        print(f"Dashboard já existe em: {out_path} (não sobrescrito)")

def write_map_html(repo_root: Path):
    """
    Gera um mapa folium simples e salva em src/dashboard/templates/map_generated.html.
    Também cria um wrapper map_view.html que incorpora o mapa via iframe e <object> como fallback.
    Não sobrescreve arquivos já existentes.
    """
    out_dir = repo_root / 'src' / 'dashboard' / 'templates'
    out_dir.mkdir(parents=True, exist_ok=True)

    map_file = out_dir / 'map_generated.html'
    wrapper_file = out_dir / 'map_view.html'

    if not map_file.exists():
        # criar um mapa simples centrado em Recife (centro aproximado)
        m = folium.Map(location=[-8.05, -34.9], zoom_start=12)
        # marcador exemplo
        folium.Marker(location=[-8.05, -34.9], popup="Recife (centro aproximado)").add_to(m)
        m.save(str(map_file))
        print(f"Mapa gerado em: {map_file}")
    else:
        print(f"Mapa já existe em: {map_file} (não sobrescrito)")

    if not wrapper_file.exists():
        # usar URI absoluto para iframe src e adicionar fallback object + link
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
  <iframe class="frame" src="{map_file.as_uri()}" title="RecifeSafe Map (iframe)"></iframe>
  <div class="notice">
    <p>Se o mapa não aparecer, abra o arquivo diretamente:</p>
    <object class="frame" data="{map_file.as_uri()}" type="text/html">
      <p>Abra o mapa manualmente: <a href="{map_file.as_uri()}" target="_blank" rel="noopener">Abrir map_generated.html</a></p>
    </object>
    <p><a href="{map_file.as_uri()}" target="_blank" rel="noopener">Abrir map_generated.html</a></p>
  </div>
</body>
</html>
"""
        wrapper_file.write_text(wrapper_html, encoding='utf-8')
        print(f"Wrapper HTML criado em: {wrapper_file}")
    else:
        print(f"Wrapper HTML já existe em: {wrapper_file} (não sobrescrito)")

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    csv_path = repo_root / 'data' / 'processed' / 'simulated_daily.csv'
    models_dir = repo_root / 'models'

    # If data CSV missing: try to generate via src.data.generate_simulated_data, else create minimal simulated data inline
    if not csv_path.exists():
        print(f"Dados ausentes: {csv_path}. Tentando gerar dados simulados automaticamente...")
        try:
            # tentar importar a função geradora existente
            from src.data.generate_simulated_data import generate_data  # type: ignore
            generate_data(out_csv=csv_path)
            print(f"Dados simulados gerados por src.data.generate_simulated_data em: {csv_path}")
        except Exception as e:
            print("Não foi possível importar src.data.generate_simulated_data (ou ocorreu erro). Gerando dados simulados mínimo localmente.")
            # gerar arquivo mínimo similar ao esperado
            try:
                import numpy as _np
                import pandas as _pd
                _np.random.seed(42)
                n_days = 90
                dates = _pd.date_range(end=_pd.Timestamp.today().normalize(), periods=n_days, freq='D', tz='UTC')
                bairros = ['Boa Viagem','Ilha do Leite','Graças','Cidade Universitária','Várzea','Ibura']
                rows = []
                for bairro in bairros:
                    lat = -8.0 + _np.random.rand()*0.2
                    lon = -34.9 + _np.random.rand()*0.2
                    vuln = float(round(_np.random.rand(),3))
                    for d in dates:
                        chuva = max(0, _np.random.gamma(2,5))
                        mare = 0.5 + 1.0*_np.sin((d.dayofyear/365)*2*_np.pi) + _np.random.normal(0,0.15)
                        lam = 0.02*chuva + 1.5*vuln
                        ocorrencias = int(_np.random.poisson(lam))
                        rows.append({
                            'date': d,
                            'bairro': bairro,
                            'lat': lat,
                            'lon': lon,
                            'vulnerabilidade': vuln,
                            'chuva_mm': round(chuva,2),
                            'mare_m': round(mare,3),
                            'ocorrencias': ocorrencias
                        })
                _df = _pd.DataFrame(rows)
                csv_path.parent.mkdir(parents=True, exist_ok=True)
                _df.to_csv(csv_path, index=False)
                print(f"Dados simulados mínimos salvos em: {csv_path}")
            except Exception as e2:
                print("Falha ao gerar dados simulados localmente:", str(e2))
                raise FileNotFoundError(f"Data file not found and automatic generation failed: {csv_path}") from e2

    # Agora que o CSV existe (ou foi criado), prosseguir com o treino
    if not csv_path.exists():
        # segurança final
        raise FileNotFoundError(f"Data file not found after generation attempt: {csv_path}. Run generate_simulated_data.py first.")
    train_and_save_models(csv_path, models_dir)
    # cria um frontend básico se ainda não existir
    write_dashboard_app(repo_root)
    # cria arquivos HTML de visualização (mapa + wrapper) se não existirem
    write_map_html(repo_root)
