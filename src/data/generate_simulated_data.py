import os
from pathlib import Path
import numpy as np
import pandas as pd

def generate_data(n_days=365, seed=42, out_csv=None):
    np.random.seed(seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=n_days, freq='D', tz='UTC')
    bairros = ['Boa Viagem','Ilha do Leite','Graças','Cidade Universitária','Várzea','Ibura']
    rows = []
    for bairro in bairros:
        lat = -8.0 + np.random.rand()*0.2
        lon = -34.9 + np.random.rand()*0.2
        vuln = np.round(np.random.rand(),3)
        for d in dates:
            chuva = max(0, np.random.gamma(2,5))
            mare = 0.5 + 1.0*np.sin((d.dayofyear/365)*2*np.pi) + np.random.normal(0,0.15)
            lam = 0.02*chuva + 1.5*vuln
            ocorrencias = np.random.poisson(lam)
            rows.append({
                'date': d,
                'bairro': bairro,
                'lat': lat,
                'lon': lon,
                'vulnerabilidade': vuln,
                'chuva_mm': round(chuva,2),
                'mare_m': round(mare,3),
                'ocorrencias': int(ocorrencias)
            })
    df = pd.DataFrame(rows)
    df['date'] = pd.to_datetime(df['date'], utc=True)
    df = df.drop_duplicates().dropna()
    if out_csv:
        out_path = Path(out_csv)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        print(f"Simulated data saved to: {out_path}")
    return df

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    out_csv = repo_root / 'data' / 'processed' / 'simulated_daily.csv'
    generate_data(out_csv=out_csv)
