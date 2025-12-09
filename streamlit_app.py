"""
RecifeSafe - Sistema de Predição de Riscos de Alagamento e Deslizamento
Arquivo de entrada para deploy no Streamlit Cloud
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

# Importa e executa o app principal
from src.dashboard.app import *
