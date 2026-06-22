"""Controlador para gerenciar regras de comunicação entre a interface visual e o banco."""

# ==============================================================================
# 1. IMPORTS E DEPENDÊNCIAS
# ==============================================================================
import logging
import threading
from typing import Any

from config import SEED_MIN, SEED_MAX
from models.patrimonio_model import PatrimonioModel, SupabasePausadoError

logger = logging.getLogger(__name__)

# Intervalo do keep-alive: 4 dias em segundos
_KEEPALIVE_INTERVALO = 4 * 24 * 60 * 60

# ==============================================================================
# 2. CLASSES DE CONTROLE
# ==============================================================================
class PatrimonioController:
    """Controlador responsável pela manipulação das requisições de geração de patrimônio."""

    def __init__(self) -> None:
        """Inicializa a conexão com o modelo de dados e inicia o keep-alive.

        Raises:
            RuntimeError: Propagado do model se o banco for inacessível.
        """
        self.model = PatrimonioModel()
        self._iniciar_keepalive()

    def _iniciar_keepalive(self) -> None:
        """Inicia a thread de keep-alive que faz ping ao Supabase a cada 4 dias.

        A thread é daemon, portanto encerra automaticamente com o app.
        """
        def _loop_keepalive() -> None:
            # Aguarda 4 dias antes do primeiro ping (o app já fez requisições ao iniciar)
            evento = threading.Event()
            while not evento.wait(timeout=_KEEPALIVE_INTERVALO):
                try:
                    self.model.ping()
                except Exception as e:
                    logger.warning("[Keep-alive] Erro inesperado no ping: %s", e)

        t = threading.Thread(target=_loop_keepalive, daemon=True, name="supabase-keepalive")
        t.start()
        logger.info("[Keep-alive] Thread iniciada. Próximo ping em 4 dias.")

    def get_configuracoes(self) -> list[dict[str, Any]] | dict[str, str]:
        """Recupera as configurações atuais de sequenciamento.

        Returns:
            Lista de configurações ou dicionário com chave 'error'.
        """
        try:
            return self.model.get_configuracoes()
        except Exception as e:
            logger.error("Erro ao buscar configurações: %s", e)
            return {'error': str(e)}

    def configurar(self, config_data: dict[str, Any]) -> dict[str, Any]:
        """Valida e persiste a seed de sequência de um tipo de equipamento.

        Args:
            config_data: Dicionário com as chaves 'tipo' (str) e 'seed' (int ou str).

        Returns:
            {'success': True} em caso de êxito ou {'error': str} em caso de falha.
        """
        tipo: str | None = config_data.get('tipo')
        seed: Any = config_data.get('seed')

        if not tipo or seed is None:
            return {'error': 'Tipo e seed são obrigatórios.'}

        try:
            seed_num: int = int(str(seed).strip())
        except ValueError:
            return {'error': 'A seed fornecida não é um número válido.'}

        if not (SEED_MIN <= seed_num <= SEED_MAX):
            return {
                'error': (
                    f"A seed deve estar entre {SEED_MIN:,} e {SEED_MAX:,}. "
                    f"Valor recebido: {seed_num:,}."
                )
            }

        try:
            self.model.set_configuracao(tipo, seed_num)
            return {'success': True}
        except Exception as e:
            logger.error("Erro ao salvar configuração tipo='%s': %s", tipo, e)
            return {'error': str(e)}

    def gerar(self, data: dict[str, Any]) -> dict[str, str]:
        """Gera e registra um novo código de patrimônio.

        Args:
            data: Dicionário com as chaves 'tipo' (str) e 'unidade' (str).

        Returns:
            {'codigo': str} em caso de êxito ou {'error': str} em caso de falha.
        """
        tipo: str | None = data.get('tipo')
        unidade: str | None = data.get('unidade')

        if not tipo or not unidade:
            return {'error': 'Tipo e Unidade são obrigatórios.'}

        try:
            codigo: str = self.model.gerar_codigo(tipo, unidade)
            return {'codigo': codigo}
        except SupabasePausadoError as e:
            logger.warning("Supabase pausado ao tentar gerar código: %s", e)
            return {'pausado': True, 'error': str(e)}
        except (ValueError, RuntimeError) as e:
            return {'error': str(e)}
        except Exception as e:
            logger.error("Erro inesperado ao gerar código: %s", e)
            return {'error': f"Erro inesperado: {e}"}

    def get_ultimos_historicos(self, limite: int = 5) -> list[dict[str, Any]]:
        """Recupera os últimos códigos gerados no banco de dados.

        Args:
            limite: Quantidade máxima de registros a retornar.

        Returns:
            Lista de históricos.
        """
        try:
            return self.model.get_ultimos_historicos(limite)
        except Exception as e:
            logger.error("Erro ao buscar históricos globais: %s", e)
            return []
