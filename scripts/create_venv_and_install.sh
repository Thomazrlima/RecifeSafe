#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${1:-.venv}"

cd "$REPO_ROOT"
echo "Usando diretório: $REPO_ROOT"
if [ ! -d "$VENV_DIR" ]; then
  echo "Criando virtualenv em $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
else
  echo "Virtualenv já existe em $VENV_DIR"
fi

# ativar e instalar
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
  echo "Dependências instaladas."
else
  echo "requirements.txt não encontrado em $REPO_ROOT"
fi

echo "Para ativar o ambiente:"
echo "  source $VENV_DIR/bin/activate"
