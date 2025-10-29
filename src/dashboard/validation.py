"""
Funções de validação para o Dashboard RecifeSafe
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict, Any
import streamlit as st


class ValidationError(Exception):
    """Exceção customizada para erros de validação"""
    pass


def validate_dataframe(df: pd.DataFrame, 
                      required_columns: Optional[list] = None) -> Tuple[bool, str]:
    """
    Valida estrutura básica do DataFrame
    
    Args:
        df: DataFrame a validar
        required_columns: Lista de colunas obrigatórias
        
    Returns:
        Tupla (válido, mensagem_erro)
    """
    if df is None or df.empty:
        return False, "DataFrame está vazio ou None"
    
    if required_columns:
        missing = set(required_columns) - set(df.columns)
        if missing:
            return False, f"Colunas faltando: {', '.join(missing)}"
    
    return True, ""


def validate_date_column(df: pd.DataFrame, column: str = 'date') -> Tuple[bool, str]:
    """
    Valida coluna de data
    
    Args:
        df: DataFrame
        column: Nome da coluna de data
        
    Returns:
        Tupla (válido, mensagem_erro)
    """
    if column not in df.columns:
        return False, f"Coluna '{column}' não encontrada"
    
    if not pd.api.types.is_datetime64_any_dtype(df[column]):
        return False, f"Coluna '{column}' não é tipo datetime"
    
    if df[column].isna().any():
        return False, f"Coluna '{column}' contém valores nulos"
    
    return True, ""


def validate_numeric_column(df: pd.DataFrame, 
                           column: str,
                           min_value: Optional[float] = None,
                           max_value: Optional[float] = None,
                           allow_null: bool = False) -> Tuple[bool, str]:
    """
    Valida coluna numérica
    
    Args:
        df: DataFrame
        column: Nome da coluna
        min_value: Valor mínimo permitido
        max_value: Valor máximo permitido
        allow_null: Permitir valores nulos
        
    Returns:
        Tupla (válido, mensagem_erro)
    """
    if column not in df.columns:
        return False, f"Coluna '{column}' não encontrada"
    
    if not pd.api.types.is_numeric_dtype(df[column]):
        return False, f"Coluna '{column}' não é numérica"
    
    if not allow_null and df[column].isna().any():
        return False, f"Coluna '{column}' contém valores nulos"
    
    if min_value is not None:
        if (df[column] < min_value).any():
            return False, f"Coluna '{column}' contém valores < {min_value}"
    
    if max_value is not None:
        if (df[column] > max_value).any():
            return False, f"Coluna '{column}' contém valores > {max_value}"
    
    return True, ""


def validate_input_rainfall(value: float) -> Tuple[bool, str, float]:
    """
    Valida input de precipitação
    
    Args:
        value: Valor de precipitação
        
    Returns:
        Tupla (válido, mensagem, valor_corrigido)
    """
    MIN_RAINFALL = 0.0
    MAX_RAINFALL = 200.0
    
    if not isinstance(value, (int, float)):
        return False, "Precipitação deve ser numérica", 0.0
    
    if value < MIN_RAINFALL:
        return False, f"Precipitação não pode ser negativa", MIN_RAINFALL
    
    if value > MAX_RAINFALL:
        return True, f"Precipitação ajustada para máximo ({MAX_RAINFALL}mm)", MAX_RAINFALL
    
    return True, "", float(value)


def validate_input_tide(value: float) -> Tuple[bool, str, float]:
    """
    Valida input de maré
    
    Args:
        value: Valor de maré
        
    Returns:
        Tupla (válido, mensagem, valor_corrigido)
    """
    MIN_TIDE = 0.0
    MAX_TIDE = 3.0
    
    if not isinstance(value, (int, float)):
        return False, "Maré deve ser numérica", 0.0
    
    if value < MIN_TIDE:
        return False, f"Maré não pode ser negativa", MIN_TIDE
    
    if value > MAX_TIDE:
        return True, f"Maré ajustada para máximo ({MAX_TIDE}m)", MAX_TIDE
    
    return True, "", float(value)


def validate_input_vulnerability(value: float) -> Tuple[bool, str, float]:
    """
    Valida input de vulnerabilidade
    
    Args:
        value: Valor de vulnerabilidade
        
    Returns:
        Tupla (válido, mensagem, valor_corrigido)
    """
    MIN_VULN = 0.0
    MAX_VULN = 1.0
    
    if not isinstance(value, (int, float)):
        return False, "Vulnerabilidade deve ser numérica", 0.5
    
    if value < MIN_VULN or value > MAX_VULN:
        corrected = np.clip(value, MIN_VULN, MAX_VULN)
        return True, f"Vulnerabilidade ajustada para range [0, 1]", corrected
    
    return True, "", float(value)


def validate_input_month(value: int) -> Tuple[bool, str, int]:
    """
    Valida input de mês
    
    Args:
        value: Valor do mês
        
    Returns:
        Tupla (válido, mensagem, valor_corrigido)
    """
    if not isinstance(value, int):
        return False, "Mês deve ser inteiro", 1
    
    if value < 1 or value > 12:
        corrected = np.clip(value, 1, 12)
        return True, f"Mês ajustado para range [1, 12]", corrected
    
    return True, "", int(value)


def validate_model_output(prediction: Any, 
                         expected_type: str = 'regression') -> Tuple[bool, str, float]:
    """
    Valida saída de modelo ML
    
    Args:
        prediction: Valor previsto pelo modelo
        expected_type: Tipo esperado ('regression', 'classification')
        
    Returns:
        Tupla (válido, mensagem, valor_corrigido)
    """
    try:
        value = float(prediction)
    except (ValueError, TypeError):
        return False, "Predição não é numérica", 0.0
    
    if np.isnan(value) or np.isinf(value):
        return False, "Predição contém NaN ou Inf", 0.0
    
    if expected_type == 'regression':
        if value < 0:
            return True, "Predição negativa ajustada para 0", 0.0
        return True, "", float(value)
    
    elif expected_type == 'classification':
        if value < 0 or value > 1:
            corrected = np.clip(value, 0, 1)
            return True, f"Probabilidade ajustada para range [0, 1]", corrected
        return True, "", float(value)
    
    else:
        return False, f"Tipo desconhecido: {expected_type}", 0.0


def validate_geojson_structure(geojson: dict) -> Tuple[bool, str]:
    """
    Valida estrutura básica de GeoJSON
    
    Args:
        geojson: Dicionário GeoJSON
        
    Returns:
        Tupla (válido, mensagem_erro)
    """
    if not isinstance(geojson, dict):
        return False, "GeoJSON não é um dicionário"
    
    if 'type' not in geojson:
        return False, "GeoJSON sem campo 'type'"
    
    if geojson['type'] != 'FeatureCollection':
        return False, f"Tipo GeoJSON inesperado: {geojson['type']}"
    
    if 'features' not in geojson:
        return False, "GeoJSON sem campo 'features'"
    
    if not isinstance(geojson['features'], list):
        return False, "'features' não é uma lista"
    
    if len(geojson['features']) == 0:
        return False, "GeoJSON sem features"
    
    return True, ""


def validate_model_features(X: np.ndarray, 
                           expected_shape: Tuple[int, ...]) -> Tuple[bool, str]:
    """
    Valida features de entrada para modelo
    
    Args:
        X: Array de features
        expected_shape: Shape esperado
        
    Returns:
        Tupla (válido, mensagem_erro)
    """
    if not isinstance(X, np.ndarray):
        return False, "Features devem ser numpy array"
    
    if X.shape != expected_shape:
        return False, f"Shape incorreto: esperado {expected_shape}, obtido {X.shape}"
    
    if np.isnan(X).any():
        return False, "Features contêm valores NaN"
    
    if np.isinf(X).any():
        return False, "Features contêm valores Inf"
    
    return True, ""


def safe_division(numerator: float, denominator: float, 
                 default: float = 0.0) -> float:
    """
    Divisão segura com tratamento de divisão por zero
    
    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor padrão se divisão inválida
        
    Returns:
        Resultado da divisão ou valor padrão
    """
    if abs(denominator) < 1e-9:
        return default
    
    result = numerator / denominator
    
    if np.isnan(result) or np.isinf(result):
        return default
    
    return result


def validate_all_inputs(chuva: float, mare: float, 
                       vulnerabilidade: float, mes: int) -> Dict[str, Any]:
    """
    Valida todos os inputs de uma vez
    
    Args:
        chuva: Precipitação
        mare: Maré
        vulnerabilidade: Vulnerabilidade
        mes: Mês
        
    Returns:
        Dicionário com resultados de validação
    """
    results = {
        'valid': True,
        'messages': [],
        'corrected_values': {}
    }
    
    # Valida chuva
    valid, msg, corrected = validate_input_rainfall(chuva)
    if not valid or msg:
        results['messages'].append(f"Precipitação: {msg}")
        results['corrected_values']['chuva'] = corrected
    
    # Valida maré
    valid, msg, corrected = validate_input_tide(mare)
    if not valid or msg:
        results['messages'].append(f"Maré: {msg}")
        results['corrected_values']['mare'] = corrected
    
    # Valida vulnerabilidade
    valid, msg, corrected = validate_input_vulnerability(vulnerabilidade)
    if not valid or msg:
        results['messages'].append(f"Vulnerabilidade: {msg}")
        results['corrected_values']['vulnerabilidade'] = corrected
    
    # Valida mês
    valid, msg, corrected = validate_input_month(mes)
    if not valid or msg:
        results['messages'].append(f"Mês: {msg}")
        results['corrected_values']['mes'] = corrected
    
    results['valid'] = len([m for m in results['messages'] if 'ajustada' not in m]) == 0
    
    return results


def display_validation_warnings(validation_results: Dict[str, Any]) -> None:
    """
    Exibe avisos de validação no Streamlit
    
    Args:
        validation_results: Resultados de validate_all_inputs
    """
    if validation_results['messages']:
        for msg in validation_results['messages']:
            if 'ajustada' in msg.lower():
                st.warning(f"⚠️ {msg}")
            else:
                st.error(f"❌ {msg}")
