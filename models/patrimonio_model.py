"""Modelo de dados para integração e controle de concorrência no SQLite."""

# ==============================================================================
# 1. IMPORTS E DEPENDÊNCIAS
# ==============================================================================
import os
import sys
import socket
import sqlite3
import logging
import time
import configparser
import contextlib
from typing import Any

if os.name == 'nt':
    import msvcrt
else:
    msvcrt = None

from config import DB_FILENAME, DB_BUSY_TIMEOUT_MS, DB_TIMEOUT, CODIGO_ZFILL, SETTINGS_FILENAME

logger = logging.getLogger(__name__)

# ==============================================================================
# 2. CLASSES DE MODELO
# ==============================================================================
class PatrimonioModel:
    """Classe responsável pelo mapeamento transacional e sequencial do patrimônio."""

    def __init__(self) -> None:
        """Inicializa as instâncias de conexão e cria o banco em caso de inexistência.

        Raises:
            RuntimeError: Se o banco de dados não puder ser acessado ou criado.
        """
        self.db_path: str = self._get_db_path()
        try:
            self._init_db()
        except sqlite3.OperationalError as e:
            logger.critical("Falha ao inicializar o banco de dados: %s", e)
            raise RuntimeError(
                f"Não foi possível acessar o banco de dados em:\n{self.db_path}\n\n"
                "Verifique se o arquivo existe e se você tem permissão de escrita."
            ) from e

    def _get_exe_dir(self) -> str:
        """Retorna o diretório base onde o executável (ou script) está localizado.

        Returns:
            Caminho absoluto do diretório de execução.
        """
        if getattr(sys, 'frozen', False):
            return os.path.abspath(os.path.dirname(sys.executable))
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _get_db_path(self) -> str:
        """Resolve o caminho do banco via settings.ini, com fallback para a pasta do exe.

        Lógica de resolução (em ordem de prioridade):
        1. Valor de [database] db_path no settings.ini (caminho de rede configurado).
        2. Pasta do executável/script como fallback automático.

        Ao usar o fallback, cria (ou atualiza) o settings.ini com o caminho
        padrão para facilitar a configuração pelo administrador.

        Returns:
            Caminho absoluto para o arquivo do banco de dados.
        """
        exe_dir = self._get_exe_dir()
        settings_path = os.path.join(exe_dir, SETTINGS_FILENAME)

        cfg = configparser.ConfigParser()
        cfg.read(settings_path, encoding='utf-8')

        db_path_cfg = cfg.get('database', 'db_path', fallback=None)

        if db_path_cfg and db_path_cfg.strip():
            resolved = db_path_cfg.strip()
            if not os.path.isabs(resolved):
                resolved = os.path.join(exe_dir, resolved)
            logger.info("Banco configurado via settings.ini: %s", resolved)
            return resolved

        # Fallback: pasta do exe — cria/atualiza settings.ini para o admin configurar
        default_path = os.path.join(exe_dir, DB_FILENAME)
        self._criar_settings_padrao(settings_path, default_path)
        logger.info("Banco usando caminho padrão (pasta do exe): %s", default_path)
        return default_path

    def _criar_settings_padrao(self, settings_path: str, db_path: str) -> None:
        """Cria o settings.ini com instruções para o administrador configurar o caminho de rede.

        Args:
            settings_path: Caminho completo onde o settings.ini será gravado.
            db_path:       Caminho padrão preenchido como exemplo editavel.
        """
        cfg = configparser.ConfigParser()
        cfg['database'] = {
            'db_path': db_path,
        }
        cfg.add_section('instrucoes')
        cfg.set(
            'instrucoes',
            '; altere db_path para o caminho de rede compartilhada',
            ''
        )
        cfg.set(
            'instrucoes',
            '; exemplo de rede',
            r'\\servidor\nti\patrimonios_nti.db'
        )
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                cfg.write(f)
            logger.info("settings.ini criado/atualizado em: %s", settings_path)
        except OSError as e:
            logger.warning("Não foi possível criar settings.ini: %s", e)

    def _acquire_network_lock(self):
        """Context manager para criar um lock atômico de rede via arquivo, 
        prevenindo erros no lock nativo do SQLite sobre SMB/redes."""
        @contextlib.contextmanager
        def network_lock():
            lock_path = self.db_path + ".lock"
            f_lock = None
            locked = False
            if msvcrt:
                try:
                    f_lock = open(lock_path, 'a')
                    start_time = time.time()
                    while time.time() - start_time < DB_TIMEOUT:
                        try:
                            # Tenta travar exclusivamente o 1º byte
                            msvcrt.locking(f_lock.fileno(), msvcrt.LK_NBLCK, 1)
                            locked = True
                            break
                        except OSError:
                            time.sleep(0.5)
                            
                    if not locked:
                        raise RuntimeError("Sistema em uso por outro usuário na rede. Tente gerá-lo de novo em instantes.")
                    yield
                finally:
                    if f_lock:
                        if locked:
                            try:
                                msvcrt.locking(f_lock.fileno(), msvcrt.LK_UNLCK, 1)
                            except OSError:
                                pass
                        f_lock.close()
            else:
                yield
        return network_lock()

    def _conectar(self) -> sqlite3.Connection:
        """Abre uma conexão SQLite com os pragmas de segurança aplicados.

        Returns:
            Conexão configurada e pronta para uso.
        """
        conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT, isolation_level=None)
        conn.execute(f'PRAGMA busy_timeout = {DB_BUSY_TIMEOUT_MS};')
        conn.execute('PRAGMA journal_mode=DELETE;')
        conn.execute('PRAGMA synchronous=FULL;')
        return conn

    def _init_db(self) -> None:
        """Cria as tabelas com pragmas seguros para uso em rede.

        Usa journal_mode=DELETE (padrão SQLite), que é o único modo
        confiável sobre drives de rede (SMB/CIFS). WAL usa memória
        compartilhada entre processos locais e não funciona em rede.
        """
        with self._conectar() as conn:
            conn.execute('BEGIN')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Controle_Sequencia_V2 (
                    Tipo_Equip TEXT PRIMARY KEY,
                    Ultimo_Codigo INTEGER
                );
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Historico_Patrimonio (
                    ID_Gerado    INTEGER PRIMARY KEY AUTOINCREMENT,
                    Codigo_Patrimonio TEXT UNIQUE,
                    Usuario      TEXT,
                    Maquina      TEXT,
                    Data_Hora    DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            self._migrar_colunas_auditoria(conn)
            conn.execute('COMMIT')

    def _migrar_colunas_auditoria(self, conn: sqlite3.Connection) -> None:
        """Adiciona colunas de auditoria em bancos criados antes desta versão.

        Args:
            conn: Conexão SQLite ativa para execução dos DDL de migração.
        """
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(Historico_Patrimonio)")
        colunas_existentes = {row[1] for row in cursor.fetchall()}

        for coluna, tipo in [("Usuario", "TEXT"), ("Maquina", "TEXT")]:
            if coluna not in colunas_existentes:
                conn.execute(f"ALTER TABLE Historico_Patrimonio ADD COLUMN {coluna} {tipo};")
                logger.info("Coluna '%s' adicionada via migração.", coluna)

    def get_configuracoes(self) -> list[dict[str, Any]]:
        """Busca todas as configurações de sequência cadastradas.

        Returns:
            Lista de dicionários com Tipo_Equip e Ultimo_Codigo.
        """
        conn = self._conectar()
        try:
            conn.row_factory = sqlite3.Row
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('SELECT * FROM Controle_Sequencia_V2')
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def set_configuracao(self, tipo: str, seed: int) -> None:
        """Insere ou substitui a seed de sequência para um tipo de equipamento.

        Args:
            tipo: Código do tipo de equipamento (ex: 'C', 'M', 'N').
            seed: Último número utilizado na sequência.
        """
        with self._acquire_network_lock():
            conn = self._conectar()
            try:
                conn.execute('BEGIN EXCLUSIVE')
                conn.execute(
                    'REPLACE INTO Controle_Sequencia_V2 (Tipo_Equip, Ultimo_Codigo) VALUES (?, ?)',
                    (tipo, seed)
                )
                conn.execute('COMMIT')
                logger.info("Seed do tipo '%s' atualizada para %d.", tipo, seed)
            except Exception as e:
                conn.execute('ROLLBACK')
                raise
            finally:
                conn.close()

    def gerar_codigo(self, tipo: str, unidade: str) -> str:
        """Gera atomicamente um novo código de patrimônio sob transação exclusiva.

        Args:
            tipo: Código do tipo de equipamento.
            unidade: Código numérico da unidade.

        Returns:
            Código formatado (ex: 'C305-BT1000001').

        Raises:
            ValueError: Se o tipo não tiver seed configurada.
            RuntimeError: Em caso de colisão de código já existente.
        """
        usuario = _get_usuario()
        maquina = socket.gethostname()

        with self._acquire_network_lock():
            conn: sqlite3.Connection = self._conectar()
            try:
                conn.execute('BEGIN EXCLUSIVE')
                cursor: sqlite3.Cursor = conn.cursor()

                cursor.execute(
                    'SELECT Ultimo_Codigo FROM Controle_Sequencia_V2 WHERE Tipo_Equip = ?', (tipo,)
                )
                row = cursor.fetchone()

                if not row:
                    raise ValueError(
                        f"Tipo '{tipo}' sem seed configurada. Configure antes de gerar."
                    )

                ultimo_num_bd: int = row[0]
                novo_num: int = ultimo_num_bd + 1
                codigo: str = f"{tipo}{unidade}-BT1{str(novo_num).zfill(CODIGO_ZFILL)}"

                cursor.execute(
                    'SELECT 1 FROM Historico_Patrimonio WHERE Codigo_Patrimonio = ?', (codigo,)
                )
                if cursor.fetchone():
                    raise RuntimeError(f"Ocorreu uma concorrência de rede. O código '{codigo}' já existe. Tente Novamente.")

                cursor.execute(
                    'UPDATE Controle_Sequencia_V2 SET Ultimo_Codigo = ? WHERE Tipo_Equip = ? AND Ultimo_Codigo = ?',
                    (novo_num, tipo, ultimo_num_bd)
                )
                
                if cursor.rowcount == 0:
                    raise RuntimeError("A sequência foi alterada por outro usuário neste instante. Tente novamente.")

                cursor.execute(
                    'INSERT INTO Historico_Patrimonio (Codigo_Patrimonio, Usuario, Maquina) VALUES (?, ?, ?)',
                    (codigo, usuario, maquina)
                )
                conn.execute('COMMIT')
                logger.info("Código gerado: %s | Usuário: %s | Máquina: %s", codigo, usuario, maquina)
                return codigo

            except Exception as e:
                conn.execute('ROLLBACK')
                logger.error("Falha ao gerar código para tipo='%s': %s", tipo, e)
                raise
            finally:
                conn.close()


# ==============================================================================
# 3. FUNÇÕES AUXILIARES
# ==============================================================================
def _get_usuario() -> str:
    """Retorna o nome do usuário do sistema operacional de forma segura.

    Returns:
        Nome do usuário ou 'desconhecido' em caso de falha.
    """
    try:
        return os.getlogin()
    except OSError:
        return os.environ.get("USERNAME", os.environ.get("USER", "desconhecido"))
