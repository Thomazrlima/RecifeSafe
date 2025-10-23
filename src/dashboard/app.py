from pathlib import Path
import sys
import argparse

import warnings
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
            print("  streamlit run src/dashboard/app.py")
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

st.set_page_config(layout="wide", page_title="RecifeSafe")

repo_root = Path(__file__).resolve().parents[2]
data_csv = repo_root / 'data' / 'processed' / 'simulated_daily.csv'
models_dir = repo_root / 'models'

st.title("RecifeSafe")
st.markdown("Use os scripts em src/data e src/models para gerar dados e treinar modelos (ex.: python src/data/generate_simulated_data.py).", unsafe_allow_html=True)

if not data_csv.exists():
    st.warning(f"Dados não encontrados em {data_csv}. Rode: python src/data/generate_simulated_data.py")
else:
    df = pd.read_csv(data_csv, parse_dates=['date'])
    df['date'] = pd.to_datetime(df['date'])
    bairros = sorted(df['bairro'].unique())
    dff = df.copy()

    st.sidebar.header("Filtros Rápidos")
    period = st.sidebar.selectbox("Período", ["Últimos 7 dias","Últimos 30 dias","Últimos 90 dias"], index=1)
    bairros = sorted(df['bairro'].unique()) if (df is not None and 'bairro' in df.columns) else []
    sel_bairro = st.sidebar.multiselect("Bairros", options=bairros, default=bairros[:3], key="sel_bairros_sidebar")
    vuln_min = st.sidebar.slider("Vulnerabilidade (mín)", 0.0, 1.0, 0.0, 0.01)
    if st.sidebar.button("Aplicar Filtros"):
        st.experimental_rerun()
    st.sidebar.markdown("---")

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
    dff = df[mask].copy()

    if 'view' not in st.session_state:
        st.session_state['view'] = 'map'
    if 'selected_bairro' not in st.session_state:
        st.session_state['selected_bairro'] = None

    st.sidebar.markdown("### Locais Salvos")
    if df is not None and not df.empty:
        grouped_overall = df.groupby('bairro').agg({'lat':'first','lon':'first','ocorrencias':'sum','vulnerabilidade':'mean'}).reset_index()
        for i, row in grouped_overall.iterrows():
            label = f"{row['bairro']}"
            if row['ocorrencias'] >= 2 or row['vulnerabilidade'] > 0.6:
                label += " ⚠️"
            if st.sidebar.button(label, key=f"locbtn_{i}"):
                st.session_state['selected_bairro'] = row['bairro']
                st.session_state['view'] = 'local'
                st.experimental_rerun()
    else:
        st.sidebar.write("Sem locais para listar")

    st.sidebar.markdown("---")
    if st.sidebar.button("Voltar ao mapa"):
        st.session_state['selected_bairro'] = None
        st.session_state['view'] = 'map'
        st.experimental_rerun()

    left_col, center_col, right_col = st.columns([2,6,4])

    with left_col:
        st.markdown("### Painel rápido")
        st.metric("Registros (filtro)", int(dff.shape[0]) if not dff.empty else 0)
        st.metric("Ocorrências (soma)", int(dff['ocorrencias'].sum()) if not dff.empty else 0)
        if st.button("Gerar dados (simulado)"):
            st.info("Gere dados com: python src/data/generate_simulated_data.py")

    with center_col:
        if st.session_state.get('view') == 'local' and st.session_state.get('selected_bairro'):
            bairro_sel = st.session_state['selected_bairro']
            st.markdown(f"## Detalhes — {bairro_sel}")
            df_b = dff[dff['bairro'] == bairro_sel]
            if not df_b.empty and px is not None:
                ts_b = df_b.groupby('date').agg({'chuva_mm':'sum','ocorrencias':'sum'}).rolling(7, min_periods=1).mean().reset_index()
                fig_b = px.line(ts_b, x='date', y=['chuva_mm','ocorrencias'], labels={'date':'Data'}, title=f"Séries: {bairro_sel}")
                fig_b.update_layout(height=320, margin=dict(t=30,b=10,l=10,r=10))
                st.plotly_chart(fig_b, width="stretch")
            else:
                st.info("Sem dados históricos para este local.")
            st.markdown("---")

        st.markdown("### Mapa de Ocorrências")
        if not dff.empty and folium is not None:
            m = folium.Map(location=[float(dff['lat'].mean()), float(dff['lon'].mean())], zoom_start=12)
            grouped = dff.groupby('bairro').agg({'lat':'first','lon':'first','ocorrencias':'sum','vulnerabilidade':'mean'}).reset_index()
            for _, r in grouped.iterrows():
                color = 'green'
                if r['ocorrencias']>10 or r['vulnerabilidade']>0.6:
                    color='red'
                elif r['ocorrencias']>3:
                    color='orange'
                folium.CircleMarker(location=[float(r['lat']), float(r['lon'])],
                                    radius=8 + min(int(r['ocorrencias']),10),
                                    color=color, fill=True,
                                    tooltip=f"{r['bairro']}: ocorr={int(r['ocorrencias'])}, vuln={r['vulnerabilidade']:.2f}"
                                   ).add_to(m)
            html(m._repr_html_(), height=640)
        else:
            st.info("Sem dados georreferenciados para o período selecionado.")

    with right_col:
        tabs = st.tabs(["Mares","Clima"])
        with tabs[0]:
            st.markdown("#### Marés × Chuva (série)")
            ts = dff.groupby('date').agg({'chuva_mm':'mean','mare_m':'mean'}).rolling(7, min_periods=1).mean().reset_index()
            if not ts.empty and px is not None:
                fig = px.bar(ts, x='date', y='chuva_mm', labels={'chuva_mm':'Chuva (mm)','date':'Data'}, opacity=0.6)
                fig.add_traces(px.line(ts, x='date', y='mare_m', labels={'mare_m':'Maré (m)'}).data)
                fig.update_layout(height=360, margin=dict(t=30,b=20,l=20,r=10), legend=dict(orientation="h", y=1.02))
                st.plotly_chart(fig, width="stretch")
            else:
                st.write("Sem série suficiente para mares.")
        with tabs[1]:
            st.markdown("#### Correlações / Clima")
            corr_cols = ['chuva_mm','mare_m','vulnerabilidade','ocorrencias']
            if set(corr_cols).issubset(dff.columns) and not dff.empty:
                corr = dff[corr_cols].corr()
                fig = px.imshow(corr, text_auto=True, labels=dict(x="Variável", y="Variável"), color_continuous_scale='RdBu_r')
                fig.update_layout(height=360, margin=dict(t=10,b=10,l=10,r=10))
                st.plotly_chart(fig, width="stretch")
            else:
                st.write("Dados insuficientes para correlação.")

    with st.expander("Previsão e Alertas (simples)"):
        if (models_dir / 'linear_regression_occ.joblib').exists() and (models_dir / 'logistic_risk.joblib').exists():
            lr = joblib.load(models_dir / 'linear_regression_occ.joblib')
            clf = joblib.load(models_dir / 'logistic_risk.joblib')
            chuva_in = st.number_input("Chuva (mm)", value=10.0, step=0.1)
            mare_in = st.number_input("Maré (m)", value=0.8, step=0.01)
            vuln_in = st.slider("Vulnerabilidade (0-1)", 0.0, 1.0, 0.3, 0.01)
            def z(x, arr): return (x - arr.mean()) / (arr.std()+1e-9)
            chuva_z = z(chuva_in, df['chuva_mm'])
            mare_z = z(mare_in, df['mare_m'])
            vuln_z = z(vuln_in, df['vulnerabilidade'])
            pred_occ = lr.predict([[chuva_z]])[0]
            prob_risk = clf.predict_proba([[chuva_z, mare_z, vuln_z]])[0,1]
            st.write(f"Previsão ocorrências (média): {pred_occ:.2f}")
            st.write(f"Probabilidade risco alto: {prob_risk:.2%}")
        else:
            st.info("Modelos não encontrados. Rode: python src/models/train_models.py")

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
        "# Se preferir abrir o HTML fallback gerado:",
        "start \"\" \"%CD%\\src\\dashboard\\templates\\map_view.html\""
    ]
    print("\\nComandos PowerShell para Windows:\\n")
    for c in cmds:
        print(c)
    print("")

if args.instructions:
    print_windows_instructions()
    import sys
    sys.exit(0)
