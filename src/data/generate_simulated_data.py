import os
from pathlib import Path
import numpy as np
import pandas as pd

BAIRROS_RECIFE = {
    'Brasília Teimosa': {
        'lat': -8.0891, 'lon': -34.8796,
        'altitude': 2, 'tipo': 'litoraneo',
        'vulnerabilidade': 0.82, 'densidade_pop': 18500,
        'risco_mare': 0.95, 'risco_chuva': 0.75
    },
    'Pina': {
        'lat': -8.0856, 'lon': -34.8831,
        'altitude': 3, 'tipo': 'litoraneo',
        'vulnerabilidade': 0.68, 'densidade_pop': 12200,
        'risco_mare': 0.90, 'risco_chuva': 0.70
    },
    'Boa Viagem': {
        'lat': -8.1228, 'lon': -34.8978,
        'altitude': 5, 'tipo': 'litoraneo',
        'vulnerabilidade': 0.45, 'densidade_pop': 9800,
        'risco_mare': 0.75, 'risco_chuva': 0.50
    },
    'Afogados': {
        'lat': -8.0531, 'lon': -34.9189,
        'altitude': 4, 'tipo': 'ribeirinho',
        'vulnerabilidade': 0.78, 'densidade_pop': 16700,
        'risco_mare': 0.65, 'risco_chuva': 0.85
    },
    'Ilha Joana Bezerra': {
        'lat': -8.0647, 'lon': -34.8972,
        'altitude': 2, 'tipo': 'ribeirinho',
        'vulnerabilidade': 0.85, 'densidade_pop': 19200,
        'risco_mare': 0.88, 'risco_chuva': 0.90
    },
    'Coelhos': {
        'lat': -8.0636, 'lon': -34.8717,
        'altitude': 3, 'tipo': 'ribeirinho',
        'vulnerabilidade': 0.72, 'densidade_pop': 14300,
        'risco_mare': 0.80, 'risco_chuva': 0.78
    },
    'Casa Forte': {
        'lat': -8.0189, 'lon': -34.9247,
        'altitude': 45, 'tipo': 'altitude',
        'vulnerabilidade': 0.25, 'densidade_pop': 5400,
        'risco_mare': 0.10, 'risco_chuva': 0.40
    },
    'Apipucos': {
        'lat': -8.0303, 'lon': -34.9431,
        'altitude': 50, 'tipo': 'altitude',
        'vulnerabilidade': 0.28, 'densidade_pop': 4800,
        'risco_mare': 0.08, 'risco_chuva': 0.45
    },
    'Várzea': {
        'lat': -8.0411, 'lon': -34.9536,
        'altitude': 55, 'tipo': 'altitude',
        'vulnerabilidade': 0.35, 'densidade_pop': 6200,
        'risco_mare': 0.05, 'risco_chuva': 0.50
    },
    'Santo Amaro': {
        'lat': -8.0469, 'lon': -34.8839,
        'altitude': 8, 'tipo': 'urbano_denso',
        'vulnerabilidade': 0.65, 'densidade_pop': 13800,
        'risco_mare': 0.45, 'risco_chuva': 0.70
    },
    'São José': {
        'lat': -8.0569, 'lon': -34.8819,
        'altitude': 6, 'tipo': 'urbano_denso',
        'vulnerabilidade': 0.62, 'densidade_pop': 12900,
        'risco_mare': 0.50, 'risco_chuva': 0.68
    },
    'Ibura': {
        'lat': -8.1189, 'lon': -34.9447,
        'altitude': 12, 'tipo': 'urbano_denso',
        'vulnerabilidade': 0.75, 'densidade_pop': 17500,
        'risco_mare': 0.30, 'risco_chuva': 0.80
    },
    'Cordeiro': {
        'lat': -8.0508, 'lon': -34.9378,
        'altitude': 25, 'tipo': 'urbano_medio',
        'vulnerabilidade': 0.48, 'densidade_pop': 8700,
        'risco_mare': 0.25, 'risco_chuva': 0.55
    },
    'Madalena': {
        'lat': -8.0547, 'lon': -34.9147,
        'altitude': 10, 'tipo': 'urbano_medio',
        'vulnerabilidade': 0.52, 'densidade_pop': 9800,
        'risco_mare': 0.35, 'risco_chuva': 0.60
    },
    'Torre': {
        'lat': -8.0456, 'lon': -34.9025,
        'altitude': 15, 'tipo': 'urbano_medio',
        'vulnerabilidade': 0.42, 'densidade_pop': 7600,
        'risco_mare': 0.28, 'risco_chuva': 0.52
    }
}

def generate_data(n_days=365, seed=42, out_csv=None):
    """
    Gera dados simulados realistas para os bairros do Recife.
    
    Considera:
    - Coordenadas geográficas reais
    - Altitude e tipo de bairro (litorâneo, ribeirinho, altitude)
    - Vulnerabilidade social e densidade populacional
    - Sazonalidade de chuvas (período chuvoso: março-agosto)
    - Variação de marés astronômicas
    - Correlação realista entre variáveis ambientais e ocorrências
    """
    np.random.seed(seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=n_days, freq='D', tz='UTC')
    rows = []
    
    for bairro, info in BAIRROS_RECIFE.items():
        lat = info['lat']
        lon = info['lon']
        altitude = info['altitude']
        vuln_base = info['vulnerabilidade']
        densidade = info['densidade_pop']
        risco_mare = info['risco_mare']
        risco_chuva = info['risco_chuva']
        tipo = info['tipo']
        
        for d in dates:
            mes = d.month
            dia_ano = d.dayofyear
            
            # Chuva: sazonalidade realista (Recife: chuvas intensas mar-ago)
            if mes in [3, 4, 5, 6, 7, 8]:
                media_chuva = 25.0
                shape_chuva = 3.5
            else:
                media_chuva = 8.0
                shape_chuva = 2.0
            
            chuva = max(0, np.random.gamma(shape_chuva, media_chuva/shape_chuva))
            
            # Adicionar eventos extremos ocasionais (5% de chance)
            if np.random.rand() < 0.05:
                chuva *= np.random.uniform(2.0, 4.0)
            
            # Maré: ciclo astronômico + variação diária
            mare_base = 1.2 + 0.4 * np.sin((dia_ano / 365.25) * 2 * np.pi)
            mare_diaria = 0.3 * np.sin((dia_ano % 29.5) / 29.5 * 2 * np.pi)
            mare = mare_base + mare_diaria + np.random.normal(0, 0.08)
            mare = max(0.5, mare)
            
            # Cálculo de risco ponderado por tipo de bairro
            if tipo == 'litoraneo':
                fator_mare = 2.5
                fator_chuva = 1.2
                fator_vuln = 1.8
            elif tipo == 'ribeirinho':
                fator_mare = 1.8
                fator_chuva = 2.2
                fator_vuln = 2.0
            elif tipo == 'altitude':
                fator_mare = 0.1
                fator_chuva = 1.5
                fator_vuln = 0.8
            else:  # urbano_denso ou urbano_medio
                fator_mare = 0.8
                fator_chuva = 1.8
                fator_vuln = 1.5
            
            # Índice de risco normalizado
            risco_chuva_norm = (chuva / 50.0) * risco_chuva * fator_chuva
            risco_mare_norm = ((mare - 1.0) / 0.5) * risco_mare * fator_mare if mare > 1.0 else 0
            risco_vuln_norm = vuln_base * fator_vuln
            
            # Cálculo de ocorrências com modelo mais sofisticado
            lambda_base = 0.5
            lambda_total = lambda_base + (
                risco_chuva_norm * 0.4 +
                risco_mare_norm * 0.35 +
                risco_vuln_norm * 0.25
            )
            
            # Ajuste por densidade populacional
            lambda_total *= (densidade / 10000) ** 0.3
            
            # Limitar lambda para evitar valores irreais
            lambda_total = max(0, min(lambda_total, 15.0))
            
            ocorrencias = np.random.poisson(lambda_total)
            
            # Adicionar pequena variação nas coordenadas (ruído GPS)
            lat_jitter = lat + np.random.normal(0, 0.0005)
            lon_jitter = lon + np.random.normal(0, 0.0005)
            
            rows.append({
                'date': d,
                'bairro': bairro,
                'lat': round(lat_jitter, 6),
                'lon': round(lon_jitter, 6),
                'altitude': altitude,
                'vulnerabilidade': round(vuln_base, 3),
                'densidade_pop': densidade,
                'chuva_mm': round(chuva, 2),
                'mare_m': round(mare, 3),
                'ocorrencias': int(ocorrencias),
                'tipo_bairro': tipo
            })
    
    df = pd.DataFrame(rows)
    df['date'] = pd.to_datetime(df['date'], utc=True)
    df = df.drop_duplicates().dropna()
    
    if out_csv:
        out_path = Path(out_csv)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        print(f"✅ Dados simulados realistas salvos: {out_path}")
        print(f"   - {len(BAIRROS_RECIFE)} bairros")
        print(f"   - {n_days} dias")
        print(f"   - {len(df)} registros totais")
        
        # Estatísticas resumidas
        print(f"\n📊 Estatísticas:")
        print(f"   - Chuva média: {df['chuva_mm'].mean():.1f}mm (σ={df['chuva_mm'].std():.1f})")
        print(f"   - Maré média: {df['mare_m'].mean():.2f}m (σ={df['mare_m'].std():.2f})")
        print(f"   - Ocorrências totais: {df['ocorrencias'].sum()}")
        print(f"   - Vulnerabilidade média: {df['vulnerabilidade'].mean():.2f}")
    
    return df

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    out_csv = repo_root / 'data' / 'processed' / 'simulated_daily.csv'
    generate_data(out_csv=out_csv)
    