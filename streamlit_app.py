"""
RecifeSafe - Sistema de Predição de Riscos de Alagamento e Deslizamento
Arquivo de entrada para deploy
"""

import sys
import os
from pathlib import Path

# Configurar o caminho antes de qualquer import do Streamlit
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))
os.chdir(str(repo_root))

# Agora importa o app principal (que já tem st.set_page_config)
import src.dashboard.app
