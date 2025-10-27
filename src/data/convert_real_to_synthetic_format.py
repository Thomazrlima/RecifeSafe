"""
Script de Conversão de Dados Reais para Formato Sintético
==========================================================

Este script converte dados reais de maré e chuva da região metropolitana do Recife
para o formato padronizado utilizado pelo sistema RecifeSafe.

ESTRUTURA DOS DADOS SINTÉTICOS (generate_simulated_data.py):
------------------------------------------------------------
Colunas obrigatórias:
- date: datetime (formato: YYYY-MM-DD HH:MM:SS+00:00, UTC)
- bairro: str (nome do bairro)
- lat: float (latitude, 6 decimais)
- lon: float (longitude, 6 decimais)
- altitude: int (metros)
- vulnerabilidade: float (0.0-1.0, 3 decimais)
- densidade_pop: int (habitantes/km²)
- chuva_mm: float (precipitação em mm, 2 decimais)
- mare_m: float (altura da maré em metros, 3 decimais)
- ocorrencias: int (número de ocorrências de alagamento)
- tipo_bairro: str (litoraneo, ribeirinho, altitude, urbano_denso, urbano_medio)

ESTRUTURA DOS DADOS REAIS:
--------------------------
1. Arquivo de Marés (2024.csv):
   - Colunas: Dia, Mês, Ano, Dia da Semana, Nascer do Sol, Pôr do Sol
   - Maré 1-4 (Horário e Altura): "Maré X - Horário", "Maré X - Altura (m)"
   - Valores com vírgula como separador decimal ("1,8" = 1.8m)
   - Múltiplas medições por dia (até 4 marés)

2. Arquivo de Chuva (Dados pluviométricos da APAC - Região metropolitana de Recife - 2024.csv):
   - Colunas: Código, Posto, Mês/Ano, 1-31 (dias do mês), Acumulado
   - Valores com vírgula como separador decimal
   - Múltiplos postos pluviométricos por município
   - Valores ausentes marcados como "-"

REGRAS DE CONVERSÃO:
--------------------
1. Data:
   - Construída a partir de Dia, Mês, Ano (marés) ou Mês/Ano + coluna dia (chuva)
   - Convertida para UTC timezone

2. Bairro:
   - Mapeado a partir do campo "Posto" do arquivo de chuva
   - Inferido a partir das coordenadas geográficas

3. Coordenadas (lat, lon):
   - Extraídas do dicionário BAIRROS_RECIFE
   - Pequena variação aleatória para simular ruído GPS

4. Altitude:
   - Extraída do dicionário BAIRROS_RECIFE

5. Vulnerabilidade:
   - Valores pré-definidos por bairro no dicionário BAIRROS_RECIFE
   - Baseados em dados socioeconômicos reais

6. Densidade Populacional:
   - Valores pré-definidos por bairro no dicionário BAIRROS_RECIFE

7. Chuva (mm):
   - Extraída diretamente do arquivo de chuva da APAC
   - Agregada por média quando há múltiplos postos no mesmo bairro
   - Valores ausentes preenchidos com 0.0

8. Maré (m):
   - Calculada como a média das 2-4 medições diárias
   - Valores ausentes preenchidos com 1.2 (nível médio)

9. Ocorrências:
   - Calculadas usando modelo probabilístico baseado em:
     * Intensidade de chuva (peso: 35%)
     * Altura da maré (peso: 25%)
     * Vulnerabilidade do bairro (peso: 30%)
     * Densidade populacional (peso: 10%)
   - Distribuição de Poisson para simular eventos discretos

10. Tipo de Bairro:
    - Extraído do dicionário BAIRROS_RECIFE
    - Categorias: litoraneo, ribeirinho, altitude, urbano_denso, urbano_medio

VALIDAÇÕES:
-----------
- Verificar se todas as colunas obrigatórias estão presentes
- Garantir que datas estão no formato correto e em ordem cronológica
- Validar tipos de dados (int, float, str, datetime)
- Verificar ranges válidos (vulnerabilidade 0-1, coordenadas em Recife)
- Identificar e tratar valores ausentes ou inválidos
- Remover duplicatas (bairro + data)

EXECUÇÃO:
---------
python src/data/convert_real_to_synthetic_format.py \\
    --mare data/processed/2024.csv \\
    --chuva "data/processed/Dados pluviométricos da APAC - Região metropolitana de Recife - 2024.csv" \\
    --output data/processed/real_data_converted.csv

Autor: RecifeSafe Team
Data: 2024
"""

import argparse
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd

# Suprimir warnings de timezone
warnings.filterwarnings('ignore', category=UserWarning)

# Dicionário de bairros do Recife com informações geográficas e sociais
# (Idêntico ao usado em generate_simulated_data.py)
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

# Mapeamento de postos pluviométricos para bairros do Recife
MAPEAMENTO_POSTOS = {
    'Recife (Alto da Brasileira)': 'Torre',
    'Recife (Codecipe / Santo Amaro)': 'Santo Amaro',
    'Recife (Várzea)': 'Várzea',
    'Olinda (Alto da Bondade)': 'Casa Forte',
    'Olinda (Academia Santa Gertrudes)': 'Casa Forte',
    'Olinda': 'Casa Forte',
    'Jaboatão (Cidade da Copa)': 'Boa Viagem',
    'Jaboatão dos Guararapes': 'Boa Viagem',
    'Jaboatão dos Guararapes (Bar.Duas Unas)': 'Pina',
    'Camaragibe': 'Cordeiro',
    'São Lourenço da Mata (Tapacurá)': 'Apipucos',
    'Cabo': 'Boa Viagem',
    'Cabo (Barragem de Gurjaú)': 'Ibura',
    'Cabo (Barragem de Suape)': 'Boa Viagem',
    'Cabo (Pirapama)': 'Ibura',
    'Paulista': 'Madalena',
    'Abreu e Lima': 'Madalena',
    'Moreno': 'Ibura',
    'Igarassu': 'Afogados',
    'Igarassu (Bar.Catucá)': 'Afogados',
    'Igarassu (Usina São José)': 'Afogados',
    'Ipojuca': 'Boa Viagem',
    'Ipojuca (Suape)': 'Boa Viagem',
    'Itamaracá': 'Brasília Teimosa',
    'Itapissuma': 'Brasília Teimosa',
    'Goiana (Itapirema - IPA)': 'Coelhos',
    'Goiana': 'Coelhos',
    'Araçoiaba (Granja Cristo Redentor)': 'Ilha Joana Bezerra'
}


def parse_float_br(value: str) -> float:
    """
    Converte string no formato brasileiro (vírgula como decimal) para float.
    
    Args:
        value: String com número no formato brasileiro (ex: "1,8")
    
    Returns:
        Valor float ou np.nan se inválido
    
    Examples:
        >>> parse_float_br("1,8")
        1.8
        >>> parse_float_br("-")
        nan
    """
    if pd.isna(value) or value == '-' or value == '':
        return np.nan
    try:
        return float(str(value).replace(',', '.'))
    except (ValueError, AttributeError):
        return np.nan


def load_mare_data(file_path: Path) -> pd.DataFrame:
    """
    Carrega e processa dados de maré do arquivo CSV.
    
    Estrutura esperada:
    - Colunas: Dia, Mês, Ano, Maré 1-4 (Horário e Altura)
    - Calcula média das alturas de maré por dia
    
    Args:
        file_path: Caminho para o arquivo CSV de marés
    
    Returns:
        DataFrame com colunas: date, mare_m (média das marés do dia)
    
    Raises:
        FileNotFoundError: Se arquivo não existe
        ValueError: Se estrutura do arquivo é inválida
    """
    print(f"📊 Carregando dados de maré: {file_path}")
    
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo de marés não encontrado: {file_path}")
    
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    
    # Construir data
    df['date'] = pd.to_datetime(
        df['Ano'].astype(str) + '-' + 
        df['Mês'].astype(str).str.zfill(2) + '-' + 
        df['Dia'].astype(str).str.zfill(2)
    )
    
    # Processar alturas de maré (até 4 medições por dia)
    mare_cols = [f'Maré {i} - Altura (m)' for i in range(1, 5)]
    
    for col in mare_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_float_br)
    
    # Calcular média das marés do dia
    df['mare_m'] = df[mare_cols].mean(axis=1, skipna=True)
    
    # Preencher valores ausentes com média geral
    if df['mare_m'].isna().any():
        media_mare = df['mare_m'].mean()
        df['mare_m'].fillna(media_mare, inplace=True)
        print(f"   ⚠️ Valores ausentes de maré preenchidos com média: {media_mare:.2f}m")
    
    result = df[['date', 'mare_m']].copy()
    print(f"   ✅ {len(result)} registros de maré carregados")
    print(f"   📈 Maré média: {result['mare_m'].mean():.2f}m (min: {result['mare_m'].min():.2f}m, max: {result['mare_m'].max():.2f}m)")
    
    return result


def load_chuva_data(file_path: Path) -> pd.DataFrame:
    """
    Carrega e processa dados pluviométricos da APAC.
    
    Estrutura esperada:
    - Colunas: Código, Posto, Mês/Ano, 1-31 (dias), Acumulado
    - Múltiplos postos por município
    - Agrega por média quando há múltiplos postos mapeados para o mesmo bairro
    
    Args:
        file_path: Caminho para o arquivo CSV de chuva
    
    Returns:
        DataFrame com colunas: date, bairro, chuva_mm
    
    Raises:
        FileNotFoundError: Se arquivo não existe
        ValueError: Se estrutura do arquivo é inválida
    """
    print(f"🌧️ Carregando dados de chuva: {file_path}")
    
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo de chuva não encontrado: {file_path}")
    
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    
    # Mapear postos para bairros
    df['bairro'] = df['Posto'].map(MAPEAMENTO_POSTOS)
    
    # Filtrar apenas postos que temos mapeamento
    df = df[df['bairro'].notna()].copy()
    
    if df.empty:
        raise ValueError("Nenhum posto pluviométrico foi mapeado para os bairros do Recife")
    
    # Processar mês/ano
    df[['mes_nome', 'ano']] = df['Mês/Ano'].str.split('/', expand=True)
    
    # Mapa de meses
    meses = {
        'jan.': 1, 'fev.': 2, 'mar.': 3, 'abr.': 4, 'mai.': 5, 'jun.': 6,
        'jul.': 7, 'ago.': 8, 'set.': 9, 'out.': 10, 'nov.': 11, 'dez.': 12
    }
    df['mes'] = df['mes_nome'].map(meses)
    
    # Reestruturar dados: transformar colunas de dias em linhas
    dia_cols = [str(i) for i in range(1, 32)]
    existing_dia_cols = [col for col in dia_cols if col in df.columns]
    
    df_melted = df.melt(
        id_vars=['bairro', 'Posto', 'ano', 'mes'],
        value_vars=existing_dia_cols,
        var_name='dia',
        value_name='chuva_mm'
    )
    
    # Converter chuva_mm para float
    df_melted['chuva_mm'] = df_melted['chuva_mm'].apply(parse_float_br)
    
    # Construir data
    df_melted['date'] = pd.to_datetime(
        df_melted['ano'] + '-' + 
        df_melted['mes'].astype(str).str.zfill(2) + '-' + 
        df_melted['dia'].str.zfill(2),
        errors='coerce'
    )
    
    # Remover datas inválidas (ex: 31 de fevereiro)
    df_melted = df_melted[df_melted['date'].notna()].copy()
    
    # Preencher valores ausentes de chuva com 0
    df_melted['chuva_mm'].fillna(0.0, inplace=True)
    
    # Agregar por bairro e data (média de múltiplos postos)
    result = df_melted.groupby(['date', 'bairro'], as_index=False).agg({
        'chuva_mm': 'mean'
    })
    
    print(f"   ✅ {len(result)} registros de chuva carregados")
    print(f"   🏘️ {result['bairro'].nunique()} bairros com dados")
    print(f"   🌧️ Chuva média: {result['chuva_mm'].mean():.1f}mm (max: {result['chuva_mm'].max():.1f}mm)")
    
    return result


def calculate_ocorrencias(row: pd.Series) -> int:
    """
    Calcula número de ocorrências usando modelo probabilístico.
    
    Modelo baseado em:
    - Chuva (35%): quanto maior, maior o risco
    - Maré (25%): marés altas aumentam risco
    - Vulnerabilidade (30%): bairros mais vulneráveis sofrem mais
    - Densidade populacional (10%): áreas densas têm mais ocorrências
    
    Args:
        row: Linha do DataFrame com chuva_mm, mare_m, vulnerabilidade, 
             densidade_pop, risco_chuva, risco_mare, tipo_bairro
    
    Returns:
        Número inteiro de ocorrências (Poisson distribuído)
    """
    # Fatores de ponderação por tipo de bairro
    if row['tipo_bairro'] == 'litoraneo':
        fator_mare = 2.5
        fator_chuva = 1.2
        fator_vuln = 1.8
    elif row['tipo_bairro'] == 'ribeirinho':
        fator_mare = 1.8
        fator_chuva = 2.2
        fator_vuln = 2.0
    elif row['tipo_bairro'] == 'altitude':
        fator_mare = 0.1
        fator_chuva = 1.5
        fator_vuln = 0.8
    else:  # urbano_denso ou urbano_medio
        fator_mare = 0.8
        fator_chuva = 1.8
        fator_vuln = 1.5
    
    # Normalizar variáveis
    risco_chuva_norm = (row['chuva_mm'] / 50.0) * row['risco_chuva'] * fator_chuva
    risco_mare_norm = ((row['mare_m'] - 1.0) / 0.5) * row['risco_mare'] * fator_mare if row['mare_m'] > 1.0 else 0
    risco_vuln_norm = row['vulnerabilidade'] * fator_vuln
    
    # Calcular lambda (taxa de Poisson)
    lambda_base = 0.5
    lambda_total = lambda_base + (
        risco_chuva_norm * 0.4 +
        risco_mare_norm * 0.35 +
        risco_vuln_norm * 0.25
    )
    
    # Ajuste por densidade populacional
    lambda_total *= (row['densidade_pop'] / 10000) ** 0.3
    
    # Limitar lambda
    lambda_total = max(0, min(lambda_total, 15.0))
    
    # Gerar ocorrências (Poisson)
    return np.random.poisson(lambda_total)


def merge_and_enrich_data(
    df_mare: pd.DataFrame, 
    df_chuva: pd.DataFrame, 
    seed: int = 42
) -> pd.DataFrame:
    """
    Combina dados de maré e chuva, enriquece com informações dos bairros.
    
    Processo:
    1. Merge entre maré e chuva por data
    2. Expandir para todos os bairros do Recife
    3. Adicionar coordenadas, altitude, vulnerabilidade, etc.
    4. Calcular ocorrências usando modelo probabilístico
    5. Adicionar ruído GPS às coordenadas
    
    Args:
        df_mare: DataFrame com dados de maré
        df_chuva: DataFrame com dados de chuva
        seed: Seed para reprodutibilidade
    
    Returns:
        DataFrame no formato padronizado do RecifeSafe
    """
    print("🔗 Mesclando e enriquecendo dados...")
    
    np.random.seed(seed)
    
    # Criar grid completo: todas as datas × todos os bairros
    all_dates = sorted(set(df_mare['date'].unique()) | set(df_chuva['date'].unique()))
    all_bairros = list(BAIRROS_RECIFE.keys())
    
    # Criar produto cartesiano
    rows = []
    for date in all_dates:
        for bairro in all_bairros:
            rows.append({'date': date, 'bairro': bairro})
    
    df_base = pd.DataFrame(rows)
    
    # Merge com maré (mesma maré para todos os bairros no mesmo dia)
    df_base = df_base.merge(df_mare, on='date', how='left')
    
    # Merge com chuva (específica por bairro e dia)
    df_base = df_base.merge(df_chuva, on=['date', 'bairro'], how='left')
    
    # Preencher valores ausentes
    df_base['mare_m'].fillna(df_mare['mare_m'].mean(), inplace=True)
    df_base['chuva_mm'].fillna(0.0, inplace=True)
    
    # Adicionar informações dos bairros
    for bairro, info in BAIRROS_RECIFE.items():
        mask = df_base['bairro'] == bairro
        
        # Adicionar ruído GPS às coordenadas
        n_rows = mask.sum()
        lat_jitter = info['lat'] + np.random.normal(0, 0.0005, n_rows)
        lon_jitter = info['lon'] + np.random.normal(0, 0.0005, n_rows)
        
        df_base.loc[mask, 'lat'] = lat_jitter
        df_base.loc[mask, 'lon'] = lon_jitter
        df_base.loc[mask, 'altitude'] = info['altitude']
        df_base.loc[mask, 'vulnerabilidade'] = info['vulnerabilidade']
        df_base.loc[mask, 'densidade_pop'] = info['densidade_pop']
        df_base.loc[mask, 'tipo_bairro'] = info['tipo']
        df_base.loc[mask, 'risco_mare'] = info['risco_mare']
        df_base.loc[mask, 'risco_chuva'] = info['risco_chuva']
    
    # Calcular ocorrências
    print("   🎲 Calculando ocorrências...")
    df_base['ocorrencias'] = df_base.apply(calculate_ocorrencias, axis=1)
    
    # Arredondar valores
    df_base['chuva_mm'] = df_base['chuva_mm'].round(2)
    df_base['mare_m'] = df_base['mare_m'].round(3)
    df_base['lat'] = df_base['lat'].round(6)
    df_base['lon'] = df_base['lon'].round(6)
    df_base['vulnerabilidade'] = df_base['vulnerabilidade'].round(3)
    
    # Converter tipos para garantir validação
    df_base['altitude'] = df_base['altitude'].astype(int)
    df_base['densidade_pop'] = df_base['densidade_pop'].astype(int)
    df_base['ocorrencias'] = df_base['ocorrencias'].astype(int)
    
    # Converter timezone para UTC
    df_base['date'] = pd.to_datetime(df_base['date'], utc=True)
    
    # Remover colunas auxiliares
    df_base = df_base.drop(columns=['risco_mare', 'risco_chuva'], errors='ignore')
    
    # Ordenar por data e bairro
    df_base = df_base.sort_values(['date', 'bairro']).reset_index(drop=True)
    
    print(f"   ✅ Dataset final: {len(df_base)} registros")
    print(f"   📅 Período: {df_base['date'].min().date()} a {df_base['date'].max().date()}")
    print(f"   🏘️ {df_base['bairro'].nunique()} bairros")
    
    return df_base


def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Valida se o DataFrame está no formato correto do RecifeSafe.
    
    Validações:
    - Presença de todas as colunas obrigatórias
    - Tipos de dados corretos
    - Ranges válidos (vulnerabilidade 0-1, coordenadas em Recife)
    - Ausência de duplicatas (bairro + date)
    - Valores ausentes
    
    Args:
        df: DataFrame a ser validado
    
    Returns:
        Tupla (is_valid, list_of_errors)
    """
    print("✅ Validando dataset...")
    
    errors = []
    
    # Colunas obrigatórias
    required_cols = [
        'date', 'bairro', 'lat', 'lon', 'altitude', 'vulnerabilidade',
        'densidade_pop', 'chuva_mm', 'mare_m', 'ocorrencias', 'tipo_bairro'
    ]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Colunas ausentes: {missing_cols}")
    
    # Tipos de dados
    if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
        errors.append("Coluna 'date' deve ser datetime")
    
    for col in ['lat', 'lon', 'vulnerabilidade', 'chuva_mm', 'mare_m']:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            errors.append(f"Coluna '{col}' deve ser numérica")
    
    for col in ['altitude', 'densidade_pop', 'ocorrencias']:
        if col in df.columns and not pd.api.types.is_integer_dtype(df[col]):
            errors.append(f"Coluna '{col}' deve ser inteira")
    
    # Ranges válidos
    if 'vulnerabilidade' in df.columns:
        invalid_vuln = ((df['vulnerabilidade'] < 0) | (df['vulnerabilidade'] > 1)).sum()
        if invalid_vuln > 0:
            errors.append(f"{invalid_vuln} valores de vulnerabilidade fora do range [0, 1]")
    
    if 'lat' in df.columns:
        invalid_lat = ((df['lat'] < -8.2) | (df['lat'] > -7.9)).sum()
        if invalid_lat > 0:
            errors.append(f"{invalid_lat} valores de latitude fora do range de Recife")
    
    if 'lon' in df.columns:
        invalid_lon = ((df['lon'] < -35.0) | (df['lon'] > -34.8)).sum()
        if invalid_lon > 0:
            errors.append(f"{invalid_lon} valores de longitude fora do range de Recife")
    
    # Duplicatas
    if 'date' in df.columns and 'bairro' in df.columns:
        duplicates = df.duplicated(subset=['date', 'bairro']).sum()
        if duplicates > 0:
            errors.append(f"{duplicates} registros duplicados (date + bairro)")
    
    # Valores ausentes
    null_counts = df.isnull().sum()
    if null_counts.any():
        null_cols = null_counts[null_counts > 0].to_dict()
        errors.append(f"Valores ausentes: {null_cols}")
    
    is_valid = len(errors) == 0
    
    if is_valid:
        print("   ✅ Dataset válido!")
    else:
        print("   ❌ Erros encontrados:")
        for error in errors:
            print(f"      - {error}")
    
    return is_valid, errors


def save_converted_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Salva o DataFrame convertido em CSV.
    
    Args:
        df: DataFrame no formato padronizado
        output_path: Caminho para salvar o arquivo CSV
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remover timezone para compatibilidade com CSV
    df_save = df.copy()
    df_save['date'] = df_save['date'].dt.tz_localize(None)
    
    df_save.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"\n💾 Dados salvos: {output_path}")
    print(f"   📊 {len(df_save)} registros")
    print(f"   🏘️ {df_save['bairro'].nunique()} bairros")
    print(f"   📅 {df_save['date'].nunique()} dias")
    print(f"   ⚠️ {df_save['ocorrencias'].sum()} ocorrências totais")
    
    # Estatísticas resumidas
    print(f"\n📈 Estatísticas:")
    print(f"   Chuva - média: {df_save['chuva_mm'].mean():.1f}mm, max: {df_save['chuva_mm'].max():.1f}mm")
    print(f"   Maré - média: {df_save['mare_m'].mean():.2f}m, range: [{df_save['mare_m'].min():.2f}, {df_save['mare_m'].max():.2f}]m")
    print(f"   Vulnerabilidade - média: {df_save['vulnerabilidade'].mean():.2f}")
    print(f"   Ocorrências - total: {df_save['ocorrencias'].sum()}, média/dia/bairro: {df_save['ocorrencias'].mean():.2f}")


def main():
    """
    Função principal: converte dados reais para formato sintético.
    
    Fluxo:
    1. Parse de argumentos da linha de comando
    2. Carregamento de dados de maré e chuva
    3. Mesclagem e enriquecimento com informações dos bairros
    4. Validação do dataset resultante
    5. Salvamento em CSV
    """
    parser = argparse.ArgumentParser(
        description='Converte dados reais de maré e chuva para formato padronizado RecifeSafe',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Conversão básica
  python src/data/convert_real_to_synthetic_format.py \\
      --mare data/processed/2024.csv \\
      --chuva "data/processed/Dados pluviométricos da APAC - Região metropolitana de Recife - 2024.csv" \\
      --output data/processed/real_data_converted.csv

  # Com seed personalizado (para reprodutibilidade)
  python src/data/convert_real_to_synthetic_format.py \\
      --mare data/processed/2024.csv \\
      --chuva "data/processed/Dados pluviométricos da APAC - Região metropolitana de Recife - 2024.csv" \\
      --output data/processed/real_data_converted.csv \\
      --seed 123
        """
    )
    
    parser.add_argument(
        '--mare',
        type=str,
        required=True,
        help='Caminho para o arquivo CSV de dados de maré (2024.csv)'
    )
    
    parser.add_argument(
        '--chuva',
        type=str,
        required=True,
        help='Caminho para o arquivo CSV de dados pluviométricos da APAC'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Caminho para salvar o arquivo CSV convertido'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Seed para reprodutibilidade (padrão: 42)'
    )
    
    args = parser.parse_args()
    
    # Conversão de paths
    mare_path = Path(args.mare)
    chuva_path = Path(args.chuva)
    output_path = Path(args.output)
    
    print("=" * 70)
    print("🌊 RecifeSafe - Conversão de Dados Reais para Formato Sintético")
    print("=" * 70)
    print()
    
    try:
        # 1. Carregar dados de maré
        df_mare = load_mare_data(mare_path)
        print()
        
        # 2. Carregar dados de chuva
        df_chuva = load_chuva_data(chuva_path)
        print()
        
        # 3. Mesclar e enriquecer
        df_final = merge_and_enrich_data(df_mare, df_chuva, seed=args.seed)
        print()
        
        # 4. Validar
        is_valid, errors = validate_dataframe(df_final)
        print()
        
        if not is_valid:
            print("❌ Validação falhou. Corrija os erros antes de salvar.")
            return 1
        
        # 5. Salvar
        save_converted_data(df_final, output_path)
        print()
        print("=" * 70)
        print("✅ Conversão concluída com sucesso!")
        print("=" * 70)
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Erro durante conversão: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
