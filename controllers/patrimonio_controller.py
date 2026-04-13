"""Controlador para gerenciar regras de comunicação entre a interface visual e o banco."""

# ==============================================================================
# 1. IMPORTS E DEPENDÊNCIAS
# ==============================================================================
from typing import Any
from models.patrimonio_model import PatrimonioModel

# ==============================================================================
# 2. CLASSES DE CONTROLE
# ==============================================================================
class PatrimonioController:
    """Controlador responsável pela manipulação das requisições de geração de patrimônio."""

    def __init__(self) -> None:
        """Inicializa a conexão com o modelo de dados."""
        self.model = PatrimonioModel()

    def get_configuracoes(self) -> list[dict[str, Any]] | dict[str, str]:
        """Recupera as configurações atuais de sequenciamento.

        Returns:
            Lista de propriedades e estados atuantes ou dicionário com indicação de falha.
        """
        try:
            return self.model.get_configuracoes()
        except Exception as e:
            return {'error': str(e)}

    def configurar(self, config_data: dict[str, Any]) -> dict[str, Any]:
        """Atualiza os parâmetros de configuração da sequência inicial.

        Args:
            config_data: Dicionário contendo as chaves necessárias para a atribuição.

        Returns:
            Dicionário de status da operação para propagação do sucesso ou notificação visual.
        """
        try:
            tipo: str | None = config_data.get('tipo')
            seed: Any = config_data.get('seed')
            
            if not tipo or seed is None:
                return {'error': 'Dados inválidos para configuração.'}
                
            seed_num: int = int(seed)
            self.model.set_configuracao(tipo, seed_num)
            return {'success': True}
        except ValueError:
            return {'error': 'A seed fornecida não é um número válido.'}
        except Exception as e:
            return {'error': str(e)}

    def gerar(self, data: dict[str, Any]) -> dict[str, str]:
        """Gera e registra um novo código de patrimônio com base no log do formulário.

        Args:
            data: Dicionário contendo atributos originados da interação com o flet.

        Returns:
            Dicionário contendo a chave vinculada ao código pronto ou erro gerado.
        """
        try:
            tipo: str | None = data.get('tipo')
            unidade: str | None = data.get('unidade')
            
            if not tipo or not unidade:
                return {'error': 'Tipo e Unidade são obrigatórios.'}
                
            codigo: str = self.model.gerar_codigo(tipo, unidade)
            return {'codigo': codigo}
        except Exception as e:
            return {'error': str(e)}
