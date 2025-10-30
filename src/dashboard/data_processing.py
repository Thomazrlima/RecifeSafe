"""
Funções de processamento de dados para o Dashboard RecifeSafe
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional


def load_and_prepare_data(csv_path: str) -> pd.DataFrame:
    """
    Carrega e prepara dados para análise
    
    Args:
        csv_path: Caminho para arquivo CSV
        
    Returns:
        DataFrame processado
    """
    df = pd.read_csv(csv_path, parse_dates=['date'])
    df['date'] = pd.to_datetime(df['date'])
    if 'bairro' in df.columns:
        df['bairro'] = df['bairro'].astype('category')
    df = df.sort_values('date')
    
    return df


def filter_data_by_neighborhood(df: pd.DataFrame, bairro: str) -> pd.DataFrame:
    """
    Filtra dados por bairro de forma eficiente
    
    Args:
        df: DataFrame completo
        bairro: Nome do bairro
        
    Returns:
        DataFrame filtrado
    """
    return df.query('bairro == @bairro').copy()


def calculate_neighborhood_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula estatísticas agregadas por bairro
    
    Args:
        df: DataFrame com dados
        
    Returns:
        DataFrame com estatísticas por bairro
    """
    stats = df.groupby('bairro').agg({
        'ocorrencias': ['sum', 'mean', 'std', 'max'],
        'vulnerabilidade': 'first',
        'chuva_mm': ['mean', 'max'],
        'mare_m': ['mean', 'max']
    }).round(2)
    
    stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
    stats = stats.reset_index()
    
    return stats


def calculate_risk_ranking(df: pd.DataFrame, 
                          weights: Optional[Dict[str, float]] = None) -> pd.DataFrame:
    """
    Calcula ranking de bairros por risco
    
    Args:
        df: DataFrame com dados
        weights: Dicionário com pesos personalizados
        
    Returns:
        DataFrame com ranking ordenado
    """
    if weights is None:
        weights = {
            'occurrences': 0.4,
            'vulnerability': 0.3,
            'rainfall': 0.2,
            'tide': 0.1
        }
    
    stats = df.groupby('bairro').agg({
        'ocorrencias': 'sum',
        'vulnerabilidade': 'first',
        'chuva_mm': 'mean',
        'mare_m': 'mean'
    })
    
    stats['risk_score'] = (
        stats['ocorrencias'] * weights['occurrences'] +
        stats['vulnerabilidade'] * 100 * weights['vulnerability'] +
        stats['chuva_mm'] * weights['rainfall'] +
        stats['mare_m'] * 10 * weights['tide']
    )
    stats = stats.sort_values('risk_score', ascending=False).reset_index()
    stats['rank'] = range(1, len(stats) + 1)
    
    return stats


def get_temporal_trends(df: pd.DataFrame, neighborhoods: List[str],
                       metric: str = 'ocorrencias',
                       resample_freq: str = 'W') -> pd.DataFrame:
    """
    Calcula tendências temporais para bairros selecionados
    
    Args:
        df: DataFrame com dados
        neighborhoods: Lista de bairros
        metric: Métrica a analisar
        resample_freq: Frequência de reamostragem ('D', 'W', 'M')
        
    Returns:
        DataFrame com tendências temporais
    """
    filtered = df[df['bairro'].isin(neighborhoods)].copy()
    
    trends = filtered.groupby(['date', 'bairro'])[metric].sum().reset_index()
    
    trends_pivot = trends.pivot(index='date', columns='bairro', values=metric)
    
    if resample_freq != 'D':
        trends_pivot = trends_pivot.resample(resample_freq).sum()
    
    return trends_pivot.reset_index()


def calculate_correlation_matrix(df: pd.DataFrame, 
                                 columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Calcula matriz de correlação para colunas especificadas
    
    Args:
        df: DataFrame com dados
        columns: Lista de colunas (None = todas numéricas)
        
    Returns:
        DataFrame com matriz de correlação
    """
    if columns is None:
        # Seleciona apenas colunas numéricas
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    return df[columns].corr().round(3)


def detect_outliers(df: pd.DataFrame, column: str, 
                   method: str = 'iqr',
                   threshold: float = 1.5) -> pd.Series:
    """
    Detecta outliers em uma coluna
    
    Args:
        df: DataFrame com dados
        column: Nome da coluna
        method: Método ('iqr' ou 'zscore')
        threshold: Limite para detecção
        
    Returns:
        Series booleana indicando outliers
    """
    if method == 'iqr':
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - threshold * IQR
        upper = Q3 + threshold * IQR
        return (df[column] < lower) | (df[column] > upper)
    
    elif method == 'zscore':
        z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
        return z_scores > threshold
    
    else:
        raise ValueError(f"Método desconhecido: {method}")


def aggregate_by_category(df: pd.DataFrame, 
                         value_column: str,
                         category_bins: List[float],
                         category_labels: List[str]) -> pd.DataFrame:
    """
    Agrega valores por categorias definidas
    
    Args:
        df: DataFrame com dados
        value_column: Coluna com valores a categorizar
        category_bins: Limites das categorias
        category_labels: Rótulos das categorias
        
    Returns:
        DataFrame com contagens por categoria
    """
    df['category'] = pd.cut(df[value_column], 
                           bins=category_bins, 
                           labels=category_labels,
                           include_lowest=True)
    
    result = df.groupby('category').size().reset_index(name='count')
    return result


def calculate_moving_average(df: pd.DataFrame, 
                            column: str,
                            window: int = 7) -> pd.Series:
    """
    Calcula média móvel de uma série temporal
    
    Args:
        df: DataFrame com dados
        column: Coluna a processar
        window: Tamanho da janela
        
    Returns:
        Series com média móvel
    """
    return df[column].rolling(window=window, min_periods=1).mean()


def get_top_n_neighborhoods(df: pd.DataFrame, 
                           metric: str = 'ocorrencias',
                           n: int = 10,
                           ascending: bool = False) -> List[str]:
    """
    Retorna top N bairros por métrica
    
    Args:
        df: DataFrame com dados
        metric: Métrica para ordenação
        n: Número de bairros
        ascending: Ordem ascendente ou descendente
        
    Returns:
        Lista de nomes de bairros
    """
    agg = df.groupby('bairro')[metric].sum().sort_values(ascending=ascending)
    return agg.head(n).index.tolist()


def prepare_prediction_features(chuva: float, 
                                mare: float,
                                vulnerabilidade: float,
                                mes: int,
                                df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepara features para predição de modelos
    
    Args:
        chuva: Precipitação (mm)
        mare: Nível da maré (m)
        vulnerabilidade: Índice de vulnerabilidade
        mes: Mês (1-12)
        df: DataFrame de referência para normalização
        
    Returns:
        Tupla com arrays de features (regressão, classificação)
    """
    chuva_z = (chuva - df['chuva_mm'].mean()) / df['chuva_mm'].std()
    mare_z = (mare - df['mare_m'].mean()) / df['mare_m'].std()
    
    chuva_z = np.clip(chuva_z, -3, 3)
    mare_z = np.clip(mare_z, -3, 3)
    
    X_reg = np.array([[chuva_z, mare_z, vulnerabilidade, mes]])
    
    X_clf = np.array([[chuva_z, mare_z, vulnerabilidade, mes, chuva_z * mare_z]])
    
    return X_reg, X_clf


def calculate_summary_metrics(df: pd.DataFrame, 
                              bairro: Optional[str] = None) -> Dict[str, float]:
    """
    Calcula métricas resumidas para dashboard
    
    Args:
        df: DataFrame com dados
        bairro: Filtrar por bairro específico (None = todos)
        
    Returns:
        Dicionário com métricas
    """
    if bairro:
        df = df.query('bairro == @bairro')
    
    metrics = {
        'total_occurrences': int(df['ocorrencias'].sum()),
        'avg_rainfall': float(df['chuva_mm'].mean()),
        'max_rainfall': float(df['chuva_mm'].max()),
        'avg_tide': float(df['mare_m'].mean()),
        'max_tide': float(df['mare_m'].max()),
        'avg_vulnerability': float(df['vulnerabilidade'].mean()),
        'days_analyzed': int(df['date'].nunique()),
        'neighborhoods_count': int(df['bairro'].nunique())
    }
    
    return metrics
