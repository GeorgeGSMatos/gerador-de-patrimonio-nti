"""Módulo de inicialização do aplicativo Gerador de Patrimônio NTI."""

# ==============================================================================
# 1. IMPORTS E DEPENDÊNCIAS
# ==============================================================================
import os
import sys
import logging

import flet as ft

from config import ASSETS_DIR, ICON_FILE
from views.main_view import main

# ==============================================================================
# 2. CONFIGURAÇÃO DE LOGGING
# ==============================================================================
def _configurar_logging() -> None:
    """Configura o logging global estritamente em memória/console
    para não sujar a pasta de rede da aplicação."""
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
    ]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers
    )
    logging.info("Logging inicializado no modo estrito de console.")

# ==============================================================================
# 3. LIMPEZA DE AMBIENTE
# ==============================================================================
def _limpar_arquivos_obsoletos() -> None:
    """Remove arquivos legados que não fazem mais parte da estrutura do projeto."""
    base: str = os.path.dirname(os.path.abspath(__file__))
    for filename in ('models.py', 'controllers.py'):
        path: str = os.path.join(base, filename)
        if os.path.exists(path):
            try:
                os.remove(path)
                logging.info("Arquivo obsoleto removido: %s", filename)
            except OSError as e:
                logging.warning("Não foi possível remover '%s': %s", filename, e)

# ==============================================================================
# 4. EXECUÇÃO PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    _configurar_logging()
    _limpar_arquivos_obsoletos()
    ft.app(
        target=main,
        assets_dir=ASSETS_DIR,
    )
