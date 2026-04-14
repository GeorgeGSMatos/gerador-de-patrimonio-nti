"""Módulo de inicialização do aplicativo Gerador de Patrimônio NTI."""

# ==============================================================================
# 1. IMPORTS E DEPENDÊNCIAS
# ==============================================================================
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

import flet as ft

from config import LOG_FILENAME, LOG_MAX_BYTES, LOG_BACKUP_COUNT, ASSETS_DIR, ICON_FILE
from views.main_view import main

# ==============================================================================
# 2. CONFIGURAÇÃO DE LOGGING
# ==============================================================================
def _configurar_logging() -> None:
    """Configura o logging global com saída em arquivo rotativo e no console."""
    if getattr(sys, 'frozen', False):
        log_dir: str = os.path.dirname(sys.executable)
    else:
        log_dir: str = os.path.dirname(os.path.abspath(__file__))

    log_path: str = os.path.join(log_dir, LOG_FILENAME)

    handlers: list[logging.Handler] = [
        RotatingFileHandler(
            log_path,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8"
        ),
        logging.StreamHandler(sys.stdout),
    ]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers
    )
    logging.info("Logging inicializado. Arquivo: %s", log_path)

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
