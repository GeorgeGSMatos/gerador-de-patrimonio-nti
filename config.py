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
DB_FILENAME: str = "patrimonios_nti.db"
SETTINGS_FILENAME: str = "settings.ini"
DB_TIMEOUT: int = 15  # segundos — timeout de conexão Python
DB_BUSY_TIMEOUT_MS: int = 15_000  # milissegundos — busy_timeout interno do SQLite

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
# 5. LOGGING
# ==============================================================================
LOG_FILENAME: str = "patrimonio.log"
LOG_MAX_BYTES: int = 1_048_576  # 1 MB
LOG_BACKUP_COUNT: int = 3

# ==============================================================================
# 6. ASSETS
# ==============================================================================
ASSETS_DIR: str = "assets"
ICON_SOURCE: str = "assets/icon.png"
ICON_FILE: str = "icone.ico"
