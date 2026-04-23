"""Configurações centralizadas do Gerador de Patrimônio NTI."""

# ==============================================================================
# 1. EQUIPAMENTOS E UNIDADES
# ==============================================================================
TIPOS_EQUIPAMENTO: list[dict[str, str]] = [
    {"key": "C", "label": "Desktop (C)"},
    {"key": "M", "label": "Monitor (M)"},
    {"key": "N", "label": "Notebook (N)"},
]

UNIDADES: list[dict[str, str]] = [
    {"key": "305", "label": "305 - Orlando Gomes"},
    {"key": "326", "label": "326 - Park"},
]

# ==============================================================================
# 2. BANCO DE DADOS
# ==============================================================================
# (Migrado integralmente para Supabase, o banco local foi desativado e removido)


# ==============================================================================
# 3. JANELA
# ==============================================================================
WINDOW_WIDTH: int = 600
WINDOW_HEIGHT: int = 460
WINDOW_MIN_WIDTH: int = 500
WINDOW_MIN_HEIGHT: int = 420

# ==============================================================================
# 4. GERAÇÃO DE CÓDIGOS
# ==============================================================================
SEED_MIN: int = 0
SEED_MAX: int = 99_999
CODIGO_ZFILL: int = 5
HISTORICO_SESSAO_MAX: int = 5

# ==============================================================================
# 5. ASSETS
# ==============================================================================
ASSETS_DIR: str = "assets"
ICON_SOURCE: str = "assets/icon.png"
ICON_FILE: str = "icone.ico"
