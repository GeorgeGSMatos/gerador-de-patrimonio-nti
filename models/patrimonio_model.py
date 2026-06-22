"""Modelo de dados para integração com o Supabase."""

# ==============================================================================
# 1. IMPORTS E DEPENDÊNCIAS
# ==============================================================================
import os
import sys
import socket
import logging
from typing import Any

from dotenv import load_dotenv
from supabase import create_client, Client

from config import CODIGO_ZFILL

logger = logging.getLogger(__name__)

# Palavras-chave que indicam falha de rede/DNS (Supabase pausado ou sem internet)
_ERROS_CONEXAO = (
    "getaddrinfo failed",
    "name or service not known",
    "nodename nor servname provided",
    "connection refused",
    "timed out",
    "network is unreachable",
    "supabase project is paused",
)


# ==============================================================================
# 2. EXCEÇÃO CUSTOMIZADA
# ==============================================================================
class SupabasePausadoError(Exception):
    """Levantada quando o Supabase está inacessível por pausa ou falha de rede."""


# ==============================================================================
# 2. CLASSES DE MODELO
# ==============================================================================
class PatrimonioModel:
    """Classe responsável pelo mapeamento transacional via Supabase."""

    def __init__(self) -> None:
        """Inicializa a conexão com o Supabase usando .env.

        Raises:
            RuntimeError: Se as credenciais não existirem ou a conexão falhar.
        """
        # Carrega as variáveis de ambiente a partir do arquivo .env
        exe_dir = self._get_exe_dir()
        env_path = os.path.join(exe_dir, '.env')
        load_dotenv(dotenv_path=env_path)

        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise RuntimeError(
                "As credenciais do Supabase (SUPABASE_URL e SUPABASE_KEY) não "
                "foram encontradas no arquivo .env."
            )

        try:
            self._supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("Conexão com Supabase inicializada com sucesso.")
        except Exception as e:
            logger.critical("Falha ao inicializar Supabase: %s", e)
            raise RuntimeError("Não foi possível conectar ao Supabase.") from e

    def _get_exe_dir(self) -> str:
        """Retorna o diretório base onde o executável (ou script) está localizado.
        
        Returns:
            O caminho absoluto do diretório onde o executável ou script se encontra.
        """
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def get_configuracoes(self) -> list[dict[str, Any]]:
        """Busca todas as configurações de sequência cadastradas.

        Returns:
            Lista de dicionários com Tipo_Equip e Ultimo_Codigo.
        """
        try:
            response = self._supabase.table("controle_sequencia").select("*").execute()
            # Mapeia as chaves lowercase do Supabase para o formato esperado (Uppercase)
            return [
                {
                    "Tipo_Equip": row["tipo_equip"],
                    "Ultimo_Codigo": row["ultimo_codigo"]
                }
                for row in response.data
            ]
        except Exception as e:
            logger.error("Erro ao buscar configurações no Supabase: %s", e)
            return []

    def set_configuracao(self, tipo: str, seed: int) -> None:
        """Insere ou substitui a seed de sequência para um tipo de equipamento.
        
        Args:
            tipo: Código do tipo de equipamento.
            seed: Valor da nova seed.
            
        Raises:
            RuntimeError: Em caso de falha de conexão ou execução no Supabase.
        """
        try:
            data = {"tipo_equip": tipo, "ultimo_codigo": seed}
            self._supabase.table("controle_sequencia").upsert(data).execute()
            logger.info("Seed do tipo '%s' atualizada para %d no Supabase.", tipo, seed)
        except Exception as e:
            logger.error("Erro ao salvar configuração tipo='%s': %s", tipo, e)
            raise RuntimeError(f"Erro ao salvar configuração: {e}") from e

    def gerar_codigo(self, tipo: str, unidade: str) -> str:
        """Gera atomicamente um novo código de patrimônio chamando uma RPC no Supabase.

        A concorrência é gerenciada nativamente pelo motor PostgreSQL.
        
        Args:
            tipo: O tipo de equipamento a ser gerado.
            unidade: A unidade de alocação do equipamento.
            
        Returns:
            O código gerado no formato patrimônio.
            
        Raises:
            ValueError: Se o tipo não possuir seed configurada.
            RuntimeError: Se ocorrer erro durante a execução da RPC.
        """
        usuario = _get_usuario()
        maquina = socket.gethostname()

        try:
            # Chama a função RPC (Stored Procedure) no banco de dados.
            # Essa função executa o 'SELECT FOR UPDATE', garantindo concorrência perfeita
            response = self._supabase.rpc(
                "gerar_codigo_patrimonio",
                {
                    "p_tipo": tipo,
                    "p_unidade": unidade,
                    "p_usuario": usuario,
                    "p_maquina": maquina
                }
            ).execute()

            codigo = response.data
            logger.info("Código gerado via Supabase: %s | Usuário: %s | Máquina: %s", codigo, usuario, maquina)
            return codigo

        except Exception as e:
            logger.error("Falha ao gerar código para tipo='%s': %s", tipo, e)
            error_msg = str(e).lower()
            if "sem seed configurada" in error_msg:
                raise ValueError(f"Tipo '{tipo}' sem seed configurada. Configure antes de gerar.") from e
            if any(kw in error_msg for kw in _ERROS_CONEXAO):
                raise SupabasePausadoError(
                    "Não foi possível conectar ao Supabase. O projeto pode estar pausado.\n"
                    "Acesse app.supabase.com e reactive o projeto, depois clique em Reconectar."
                ) from e
            raise RuntimeError(f"Erro ao gerar código no Supabase: {str(e)}") from e

    def get_ultimos_historicos(self, limite: int = 5) -> list[dict[str, Any]]:
        """Busca os últimos códigos gerados no banco de dados por qualquer usuário.
        
        Args:
            limite: Quantidade máxima de registros a retornar.
            
        Returns:
            Lista de históricos gerados com suas propriedades.
        """
        try:
            response = self._supabase.table("historico_patrimonio") \
                .select("*") \
                .order("id_gerado", desc=True) \
                .limit(limite) \
                .execute()
            
            # Mapeia as chaves para o formato esperado na view/controller
            return [
                {
                    "Codigo_Patrimonio": row["codigo_patrimonio"],
                    "Usuario": row["usuario"],
                    "Maquina": row["maquina"],
                    "Data_Hora": row["data_hora"]
                }
                for row in response.data
            ]
        except Exception as e:
            logger.error("Erro ao buscar histórico no Supabase: %s", e)
            return []

    def ping(self) -> bool:
        """Realiza uma consulta mínima para manter o projeto Supabase ativo.

        Returns:
            True se o ping foi bem-sucedido, False caso contrário.
        """
        try:
            self._supabase.table("controle_sequencia").select("tipo_equip").limit(1).execute()
            logger.info("[Keep-alive] Ping ao Supabase realizado com sucesso.")
            return True
        except Exception as e:
            logger.warning("[Keep-alive] Ping ao Supabase falhou: %s", e)
            return False


# ==============================================================================
# 3. FUNÇÕES AUXILIARES
# ==============================================================================
def _get_usuario() -> str:
    """Retorna o nome do usuário do sistema operacional de forma segura.
    
    Returns:
        O nome de usuário do sistema ou 'desconhecido' caso não seja possível obter.
    """
    try:
        return os.getlogin()
    except OSError:
        return os.environ.get("USERNAME", os.environ.get("USER", "desconhecido"))
