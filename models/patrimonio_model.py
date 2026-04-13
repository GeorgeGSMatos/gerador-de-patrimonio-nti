"""Modelo de dados para integração e controle de concorrência no SQLite."""

# ==============================================================================
# 1. IMPORTS E DEPENDÊNCIAS
# ==============================================================================
import os
import sys
import sqlite3
from typing import Any

# ==============================================================================
# 2. CLASSES DE MODELO
# ==============================================================================
class PatrimonioModel:
    """Classe responsável pelo mapeamento transacional e sequencial do patrimônio."""

    def __init__(self) -> None:
        """Inicializa as instâncias de conexão e cria o banco em caso de inexistência."""
        self.db_path: str = self._get_db_path()
        self._init_db()

    def _get_db_path(self) -> str:
        """Resolve e recupera o caminho absoluto para o asssentamento do banco local ou rede.

        Returns:
            Caminho absoluto preenchido para o arquivo do SQLite contendo as informações.
        """
        if getattr(sys, 'frozen', False):
            base_dir: str = os.path.dirname(sys.executable)
        else:
            base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, 'patrimonios_nti.db')

    def _init_db(self) -> None:
        """Cria o arranjo estrutural do banco e suas tabelas com pragmas de concorrência."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Controle_Sequencia_V2 (
                    Tipo_Equip TEXT PRIMARY KEY,
                    Ultimo_Codigo INTEGER
                );
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Historico_Patrimonio (
                    ID_Gerado INTEGER PRIMARY KEY AUTOINCREMENT,
                    Codigo_Patrimonio TEXT UNIQUE,
                    Data_Hora DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            conn.execute('PRAGMA journal_mode=WAL;')
            conn.execute('PRAGMA synchronous=NORMAL;')

    def get_configuracoes(self) -> list[dict[str, Any]]:
        """Busca todas as métricas em relação às chaves pré-estabelecidas e suas contagens.

        Returns:
            Lista de propriedades e estados atuantes em formato de dicionários.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('SELECT * FROM Controle_Sequencia_V2')
            return [dict(row) for row in cursor.fetchall()]

    def set_configuracao(self, tipo: str, seed: int) -> None:
        """Insere ou modifica os status do índice de sequência final para inicialização padrão.

        Args:
            tipo: Etiqueta textual representativa correspondente à unidade computacional.
            seed: Contagem inicial do parâmetro atrelado para uso pelo construtor.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO Controle_Sequencia_V2 (Tipo_Equip, Ultimo_Codigo) 
                VALUES (?, ?)
                ON CONFLICT(Tipo_Equip) DO UPDATE SET Ultimo_Codigo = excluded.Ultimo_Codigo
            ''', (tipo, seed))
            conn.commit()

    def gerar_codigo(self, tipo: str, unidade: str) -> str:
        """Monta isoladamente sob concorrência rigorosa um indicativo patrimonial sequenciado.

        Args:
            tipo: Formato identificativo da estrutura.
            unidade: Rumo local de pertencimento.

        Returns:
            Formato legível textual consolidado contendo a mescla para catalogação.

        Raises:
            Exception: Ativado perante recusas da integridade, concorrência ou conflito sequencial.
        """
        conn: sqlite3.Connection = sqlite3.connect(self.db_path, isolation_level=None)
        try:
            conn.execute('BEGIN EXCLUSIVE TRANSACTION')
            cursor: sqlite3.Cursor = conn.cursor()

            cursor.execute('SELECT Ultimo_Codigo FROM Controle_Sequencia_V2 WHERE Tipo_Equip = ?', (tipo,))
            row: tuple[int] | None = cursor.fetchone()

            if not row:
                raise Exception('Ponto de partida não configurado para este tipo de equipamento.')

            ultimo_codigo: int = row[0]
            novo_codigo_num: int = ultimo_codigo + 1
            codigo_formatado: str = f"{tipo}{unidade}-BT1{str(novo_codigo_num).zfill(6)}"

            cursor.execute('SELECT 1 FROM Historico_Patrimonio WHERE Codigo_Patrimonio = ?', (codigo_formatado,))
            if cursor.fetchone():
                raise Exception(f'O código {codigo_formatado} já existe no histórico.')

            cursor.execute('UPDATE Controle_Sequencia_V2 SET Ultimo_Codigo = ? WHERE Tipo_Equip = ?', (novo_codigo_num, tipo))
            cursor.execute('INSERT INTO Historico_Patrimonio (Codigo_Patrimonio) VALUES (?)', (codigo_formatado,))

            conn.execute('COMMIT')
            return codigo_formatado

        except Exception as e:
            conn.execute('ROLLBACK')
            raise e
        finally:
            conn.close()
