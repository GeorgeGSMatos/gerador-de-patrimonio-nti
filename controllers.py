from models import PatrimonioModel

class PatrimonioController:
    def __init__(self):
        self.model = PatrimonioModel()

    def get_configuracoes(self):
        try:
            return self.model.get_configuracoes()
        except Exception as e:
            return {'error': str(e)}

    def configurar(self, config_data):
        try:
            tipo = config_data.get('tipo')
            unidade = config_data.get('unidade')
            seed = config_data.get('seed')
            
            if not tipo or not unidade or seed is None:
                return {'error': 'Dados inválidos para configuração.'}
                
            seed_num = int(seed)
            self.model.set_configuracao(tipo, unidade, seed_num)
            return {'success': True}
        except ValueError:
            return {'error': 'A seed fornecida não é um número válido.'}
        except Exception as e:
            return {'error': str(e)}

    def gerar(self, data):
        try:
            tipo = data.get('tipo')
            unidade = data.get('unidade')
            
            if not tipo or not unidade:
                return {'error': 'Tipo e Unidade são obrigatórios.'}
                
            codigo = self.model.gerar_codigo(tipo, unidade)
            return {'codigo': codigo}
        except Exception as e:
            return {'error': str(e)}
