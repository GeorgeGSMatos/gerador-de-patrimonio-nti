import os
import sys
import sqlite3

class PatrimonioModel:
    def __init__(self):
        self.db_path = self._get_db_path()
        self._init_db()

    def _get_db_path(self):
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running as normal script
            base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, 'patrimonios_nti.db')

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Controle_Sequencia (
                    Tipo_Equip TEXT,
                    Unidade TEXT,
                    Ultimo_Codigo INTEGER,
                    PRIMARY KEY(Tipo_Equip, Unidade)
                );
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Historico_Patrimonio (
                    ID_Gerado INTEGER PRIMARY KEY AUTOINCREMENT,
                    Codigo_Patrimonio TEXT UNIQUE,
                    Data_Hora DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            # Set pragmas for better concurrency since it's a shared network file
            conn.execute('PRAGMA journal_mode=WAL;')
            conn.execute('PRAGMA synchronous=NORMAL;')

    def get_configuracoes(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM Controle_Sequencia')
            return [dict(row) for row in cursor.fetchall()]

    def set_configuracao(self, tipo, unidade, seed):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO Controle_Sequencia (Tipo_Equip, Unidade, Ultimo_Codigo) 
                VALUES (?, ?, ?)
                ON CONFLICT(Tipo_Equip, Unidade) DO UPDATE SET Ultimo_Codigo = excluded.Ultimo_Codigo
            ''', (tipo, unidade, seed))
            conn.commit()

    def gerar_codigo(self, tipo, unidade):
        # We need isolation_level=None to handle our own transactions explicitly
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        try:
            # Lock the database. Very important for concurrent network access!
            conn.execute('BEGIN EXCLUSIVE TRANSACTION')
            cursor = conn.cursor()

            # 1. Read last code
            cursor.execute('SELECT Ultimo_Codigo FROM Controle_Sequencia WHERE Tipo_Equip = ? AND Unidade = ?', (tipo, unidade))
            row = cursor.fetchone()

            if not row:
                raise Exception('Ponto de partida não configurado para esta combinação.')

            ultimo_codigo = row[0]
            novo_codigo_num = ultimo_codigo + 1
            codigo_formatado = f"{tipo}{unidade}-BT{str(novo_codigo_num).zfill(6)}"

            # 2. Safety check in history
            cursor.execute('SELECT 1 FROM Historico_Patrimonio WHERE Codigo_Patrimonio = ?', (codigo_formatado,))
            if cursor.fetchone():
                raise Exception(f'O código {codigo_formatado} já existe no histórico.')

            # 3. Update sequence
            cursor.execute('UPDATE Controle_Sequencia SET Ultimo_Codigo = ? WHERE Tipo_Equip = ? AND Unidade = ?', (novo_codigo_num, tipo, unidade))

            # 4. Insert into history
            cursor.execute('INSERT INTO Historico_Patrimonio (Codigo_Patrimonio) VALUES (?)', (codigo_formatado,))

            conn.execute('COMMIT')
            return codigo_formatado

        except Exception as e:
            conn.execute('ROLLBACK')
            raise e
        finally:
            conn.close()
