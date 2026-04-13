"""Módulo de inicialização do aplicativo Gerador de Patrimônio NTI."""

# ==============================================================================
# 1. IMPORTS E DEPENDÊNCIAS
# ==============================================================================
import os
import flet as ft

from views.main_view import main

# ==============================================================================
# 2. LIMPEZA DE AMBIENTE
# ==============================================================================
# --- 2.1. Arquivos Obsoletos ---
for stale_file in ['models.py', 'controllers.py']:
    path: str = os.path.join(os.path.dirname(__file__), stale_file)
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass

# ==============================================================================
# 3. EXECUÇÃO PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    ft.app(target=main)
