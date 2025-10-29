"""
Configurações centralizadas do Dashboard RecifeSafe
"""

# Constantes de Risco
RISK_THRESHOLDS = {
    'low': 0.5,
    'moderate': 0.7,
    'high': 1.0
}

# Pesos para cálculo de score composto
RISK_WEIGHTS = {
    'occurrences': 0.4,
    'vulnerability': 0.3,
    'rainfall': 0.2,
    'tide': 0.1
}

# Limites de inputs
INPUT_LIMITS = {
    'rainfall_max': 200.0,  # mm
    'tide_max': 3.0,        # metros
    'z_score_clip': 3.0     # desvios padrão
}

# Faixas de classificação de chuva
RAINFALL_CATEGORIES = {
    'bins': [0, 10, 25, 50, 999],
    'labels': ['Leve (<10mm)', 'Moderada (10-25mm)', 'Forte (25-50mm)', 'Intensa (>50mm)']
}

# Paleta de cores
COLOR_SCHEME = {
    'primary': '#dc3545',
    'secondary': '#c82333',
    'success': '#28a745',
    'warning': '#ffc107',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40',
    'risk_low': '#90EE90',
    'risk_moderate': '#FFD700',
    'risk_high': '#FF6B6B',
    'gradient_primary': 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)',
    'gradient_secondary': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
}

# Configurações de gráficos Plotly
PLOTLY_CONFIG = {
    'displayModeBar': False,
    'staticPlot': False
}

PLOTLY_LAYOUT_BASE = {
    'margin': dict(l=20, r=20, t=40, b=20),
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'font': dict(family='Inter, system-ui, -apple-system, sans-serif')
}

# Configurações de cache
CACHE_TTL = 3600  # 1 hora em segundos

# Mensagens de interpretação
INTERPRETATIONS = {
    'tides_temporal': 'As linhas mostram como chuva e maré variam ao longo do tempo. Picos simultâneos (ambas altas) indicam maior risco de alagamento.',
    'tides_scatter': 'Cada ponto representa um dia em um bairro. Pontos vermelhos (alto risco) tendem a aparecer quando **maré E chuva** são altas simultaneamente.',
    'weather_impact': 'Cada ponto representa um dia/bairro. A linha de tendência mostra que **quanto maior a chuva, maior o número de ocorrências**. Pontos mais vermelhos indicam áreas mais vulneráveis.',
    'weather_distribution': 'As caixas mostram a variação típica de ocorrências para cada faixa de chuva. **Chuvas intensas** (>50mm) geram consistentemente mais ocorrências, com valores máximos muito superiores.',
    'vulnerability_heatmap': 'Áreas mais escuras concentram maior número de ocorrências. Observa-se que **bairros mais vulneráveis** (à direita) sofrem mais impacto, mesmo com chuvas moderadas.',
    'precipitation_histogram': 'O histograma mostra a frequência de diferentes volumes de chuva. A maioria dos dias tem chuva leve a moderada, mas eventos extremos (picos à direita) são os mais críticos.',
    'ranking_score': 'O score de risco é calculado considerando: **40% ocorrências**, **30% vulnerabilidade**, **20% precipitação média** e **10% nível de maré**. Quanto maior o score, maior a prioridade de atenção.',
    'ranking_matrix': 'Bairros no **quadrante superior direito** (alta ocorrência + alta vulnerabilidade) são os mais críticos e demandam atenção prioritária. O tamanho das bolhas representa o score composto de risco.',
    'ranking_temporal': 'Acompanhe a variação de ocorrências ao longo do tempo nos 5 bairros mais críticos. Identifique padrões sazonais e picos de eventos.'
}

# Textos de alertas
ALERT_MESSAGES = {
    'high_risk': 'Condições de alto risco! Recomenda-se atenção especial e possível evacuação de áreas vulneráveis.',
    'moderate_risk': 'Risco moderado. Monitorar situação e preparar medidas preventivas.',
    'low_risk': 'Condições dentro da normalidade. Manter monitoramento de rotina.',
    'critical_days': 'Foram identificados **{dias} dias críticos** no período, representando {percentual:.1f}% do tempo. Nestes momentos, a combinação de maré alta e chuva intensa eleva significativamente o risco de alagamento, especialmente em áreas litorâneas e ribeirinhas.',
    'favorable_conditions': 'Não houve momentos críticos com picos simultâneos no período analisado.'
}

# Configurações de periodicidade
PERIOD_DAYS = {
    'Últimos 7 dias': 7,
    'Últimos 30 dias': 30,
    'Últimos 90 dias': 90
}

# Help texts para inputs
HELP_TEXTS = {
    'rainfall': 'Precipitação esperada em milímetros (0-200mm)',
    'tide': 'Nível de maré esperado em metros (0-3m)',
    'vulnerability': 'Índice de vulnerabilidade do bairro (0=baixa, 1=alta)'
}
