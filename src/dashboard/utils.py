"""
Funções utilitárias para o Dashboard RecifeSafe
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Dict, List, Optional
import numpy as np


def create_alert_box(message: str, alert_type: str = 'info', icon: str = 'lightbulb') -> None:
    """
    Cria uma caixa de alerta customizada com ícone Font Awesome
    
    Args:
        message: Texto da mensagem
        alert_type: Tipo do alerta ('error', 'warning', 'success', 'info')
        icon: Nome do ícone Font Awesome (sem prefixo 'fa-')
    """
    alert_styles = {
        'error': {
            'bg': '#f8d7da',
            'border': '#dc3545',
            'text': '#721c24',
            'icon_color': '#dc3545'
        },
        'warning': {
            'bg': '#fff3cd',
            'border': '#ffc107',
            'text': '#856404',
            'icon_color': '#ffc107'
        },
        'success': {
            'bg': '#d4edda',
            'border': '#28a745',
            'text': '#155724',
            'icon_color': '#28a745'
        },
        'info': {
            'bg': '#d1ecf1',
            'border': '#0c5460',
            'text': '#0c5460',
            'icon_color': '#0c5460'
        }
    }
    
    style = alert_styles.get(alert_type, alert_styles['info'])
    
    html = f'''
    <div style="padding: 1rem; background-color: {style['bg']}; 
         border-left: 4px solid {style['border']}; border-radius: 4px; margin: 1rem 0;">
        <p style="margin: 0; color: {style['text']};">
            <i class="fas fa-{icon}" style="margin-right: 8px; color: {style['icon_color']};"></i>
            {message}
        </p>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


def create_interpretation_box(message: str) -> None:
    """Cria uma caixa de interpretação com ícone de lâmpada"""
    create_alert_box(f'<strong>Interpretação:</strong> {message}', 'info', 'lightbulb')


def apply_plotly_theme(fig: go.Figure, height: int = 400) -> go.Figure:
    """
    Aplica tema consistente a gráficos Plotly
    
    Args:
        fig: Figura Plotly
        height: Altura do gráfico
        
    Returns:
        Figura com tema aplicado
    """
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, system-ui, -apple-system, sans-serif')
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    return fig


def calculate_z_score(value: float, array: np.ndarray) -> float:
    """
    Calcula z-score de forma robusta
    
    Args:
        value: Valor a normalizar
        array: Array de referência
        
    Returns:
        Z-score calculado
    """
    mean = array.mean()
    std = array.std()
    
    if std < 1e-9:
        return 0.0
    
    z = (value - mean) / std
    return float(np.clip(z, -3, 3))  # Clipa em ±3 desvios padrão


def calculate_risk_score(ocorrencias: float, vulnerabilidade: float, 
                         chuva_mm: float, mare_m: float,
                         weights: Optional[Dict[str, float]] = None) -> float:
    """
    Calcula score de risco composto
    
    Args:
        ocorrencias: Número de ocorrências
        vulnerabilidade: Índice de vulnerabilidade (0-1)
        chuva_mm: Precipitação em mm
        mare_m: Nível de maré em metros
        weights: Dicionário com pesos personalizados
        
    Returns:
        Score de risco calculado
    """
    if weights is None:
        weights = {
            'occurrences': 0.4,
            'vulnerability': 0.3,
            'rainfall': 0.2,
            'tide': 0.1
        }
    
    score = (
        ocorrencias * weights['occurrences'] +
        vulnerabilidade * 100 * weights['vulnerability'] +
        chuva_mm * weights['rainfall'] +
        mare_m * 10 * weights['tide']
    )
    
    return float(score)


def format_metric_value(value: float, format_type: str = 'float') -> str:
    """
    Formata valores de métricas de forma consistente
    
    Args:
        value: Valor a formatar
        format_type: Tipo de formatação ('float', 'int', 'percent')
        
    Returns:
        String formatada
    """
    if format_type == 'int':
        return f"{int(value)}"
    elif format_type == 'percent':
        return f"{value:.0%}"
    elif format_type == 'float':
        return f"{value:.2f}"
    else:
        return str(value)


def get_risk_level(probability: float) -> Dict[str, str]:
    """
    Determina nível de risco baseado em probabilidade
    
    Args:
        probability: Probabilidade de risco (0-1)
        
    Returns:
        Dicionário com informações do nível de risco
    """
    if probability > 0.7:
        return {
            'level': 'RISCO ALTO',
            'color': '#dc3545',
            'bg_color': '#f8d7da',
            'icon': 'exclamation-circle',
            'message': 'Condições de alto risco! Recomenda-se atenção especial e possível evacuação de áreas vulneráveis.'
        }
    elif probability > 0.5:
        return {
            'level': 'RISCO MODERADO',
            'color': '#ffc107',
            'bg_color': '#fff3cd',
            'icon': 'exclamation-triangle',
            'message': 'Risco moderado. Monitorar situação e preparar medidas preventivas.'
        }
    else:
        return {
            'level': 'RISCO BAIXO',
            'color': '#28a745',
            'bg_color': '#d4edda',
            'icon': 'check-circle',
            'message': 'Condições dentro da normalidade. Manter monitoramento de rotina.'
        }


def display_risk_badge(probability: float) -> None:
    """
    Exibe badge visual de nível de risco
    
    Args:
        probability: Probabilidade de risco (0-1)
    """
    risk_info = get_risk_level(probability)
    
    html = f'''
    <div style="text-align: center; padding: 20px; background: {risk_info['bg_color']}; 
         border-radius: 8px; border-left: 4px solid {risk_info['color']};">
        <i class="fas fa-{risk_info['icon']}" style="font-size: 2em; color: {risk_info['color']};"></i>
        <br>
        <strong style="color: #333;">{risk_info['level']}</strong>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


def validate_input_range(value: float, min_val: float, max_val: float, name: str) -> float:
    """
    Valida e ajusta valor de input dentro de range
    
    Args:
        value: Valor a validar
        min_val: Valor mínimo permitido
        max_val: Valor máximo permitido
        name: Nome do parâmetro (para mensagens de erro)
        
    Returns:
        Valor validado e clipado
    """
    if value < min_val or value > max_val:
        st.warning(f"{name} ajustado para faixa válida ({min_val}-{max_val})")
        return float(np.clip(value, min_val, max_val))
    return float(value)


def create_metric_card(label: str, value: str, icon: str, 
                      icon_color: str = '#17a2b8') -> None:
    """
    Cria card de métrica com ícone
    
    Args:
        label: Rótulo da métrica
        value: Valor da métrica
        icon: Nome do ícone Font Awesome
        icon_color: Cor do ícone
    """
    st.markdown(
        f'<p style="font-size: 0.9em; color: #666;">'
        f'<i class="fas fa-{icon} metric-icon" style="color: {icon_color};"></i>'
        f'{label}</p>', 
        unsafe_allow_html=True
    )
    st.metric(label, value, label_visibility="collapsed")


def add_reference_lines(fig: go.Figure, x_median: float, y_median: float,
                        x_label: str = '', y_label: str = '') -> go.Figure:
    """
    Adiciona linhas de referência (mediana) a gráfico scatter
    
    Args:
        fig: Figura Plotly
        x_median: Valor da mediana no eixo X
        y_median: Valor da mediana no eixo Y
        x_label: Label do eixo X
        y_label: Label do eixo Y
        
    Returns:
        Figura com linhas de referência
    """
    fig.add_hline(y=y_median, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=x_median, line_dash="dash", line_color="gray", opacity=0.5)
    return fig
