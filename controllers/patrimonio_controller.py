"""Controlador para gerenciar regras de comunicação entre a interface visual e o banco."""

# ==============================================================================
# 1. IMPORTS E DEPENDÊNCIAS
# ==============================================================================
import logging
from typing import Any

from config import SEED_MIN, SEED_MAX
from models.patrimonio_model import PatrimonioModel

logger = logging.getLogger(__name__)

# ==============================================================================
# 2. CLASSES DE CONTROLE
# ==============================================================================
class PatrimonioController:
    """Controlador responsável pela manipulação das requisições de geração de patrimônio."""

    def __init__(self) -> None:
        """Inicializa a conexão com o modelo de dados.

        Raises:
            RuntimeError: Propagado do model se o banco for inacessível.
        """
        self.model = PatrimonioModel()

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
        except (ValueError, RuntimeError) as e:
            return {'error': str(e)}
        except Exception as e:
            logger.error("Erro inesperado ao gerar código: %s", e)
            return {'error': f"Erro inesperado: {e}"}
