<div align="center">
  ![Capa do Projeto](link_da_imagem_aqui)
</div>

# Gerador de Patrimônio NTI

## Problema de Negócio
No ambiente de suporte de TI (NTI - CIMATEC), a gestão de ativos exige a geração e atribuição de códigos de patrimônio únicos para novos equipamentos (Desktops, Monitores, Notebooks). Como múltiplos técnicos podem atuar simultaneamente no recebimento e preparação de equipamentos, o uso de planilhas ou sistemas sem controle de concorrência frequentemente causava a duplicação ou o salto indesejado nas sequências dos códigos de patrimônio.

## Objetivo do Projeto
Automatizar, centralizar e padronizar a geração sequencial de códigos de patrimônio (ex: `C305-BT1000001`), proporcionando uma interface de usuário simples e limpa. O sistema deve garantir a integridade dos dados e impedir a geração de códigos duplicados quando múltiplos clientes (técnicos) executam a aplicação ou acessam o banco de dados simultaneamente em um ambiente de rede compartilhada.

## Estratégia da Solução
A aplicação foi construída com foco em simplicidade de execução, adotando o padrão **MVC (Model-View-Controller)** para total separação das responsabilidades.
A estratégia chave para a concorrência sem depender de servidores robustos foi o uso otimizado do **SQLite**. O banco de dados foi configurado em modo de registro de gravação antecipada (`WAL`) e impõe transações exclusivas (`BEGIN EXCLUSIVE TRANSACTION`) no momento crítico da geração do número. Isso permite que a aplicação seja empacotada em um executável autônomo, acessando um banco de dados em um drive de rede, resolvendo os acessos paralelos sem crashs.
A interface visual foi desenvolvida em **Flet**, garantindo uma aplicação fluida, responsiva e com princípios de design moderno.

## Tecnologias Utilizadas
* **Linguagem Backend:** Python 3.x
* **Interface de Usuário (UI):** Flet (Framework moderno em Python)
* **Banco de Dados:** SQLite (Modo compartilhado em rede com pragmas `WAL` e `synchronous=NORMAL`)
* **Padrão de Projeto:** MVC (Model, View e Controller)

## Etapas do Projeto
1. **Estruturação do Banco de Dados:** Criação das tabelas de estado (Controle de Sequência) e de auditoria (Histórico de Patrimônios).
2. **Modelagem de Dados e Controle Transacional:** Implementação da classe `PatrimonioModel` com controle de locks e rollback automático para lidar com a concorrência na gravação.
3. **Desenvolvimento de Interface (Flet):** Criação de uma interface com tratamento de estados em tempo real, validações de erro amigáveis, e o histórico temporário da sessão.
4. **Integração MVC:** Adaptação da camada lógica (Controllers) para centralizar a comunicação entre a interface visual e o banco.
5. **Limpeza e Preparação para Deploy:** Remoção de arquivos duplicados da fase inicial e ajuste dos caminhos relativos de importação, permitindo o empacotamento com o PyInstaller.

## Principais Insights
* O SQLite pode operar perfeitamente bem como banco compartilhado em rede para pequenas aplicações se utilizado com os pragmas corretos (`journal_mode=WAL`) associado à requisição de transação bloqueante pontual (`BEGIN EXCLUSIVE TRANSACTION`).
* Arquitetura MVC, apesar de vista como excessiva para projetos diminutos, se provou essencial para isolar as lógicas exclusivas e críticas de SQL da complexidade de renderização assíncrona dos controles do Flet.

## Resultados
O workflow de suporte do NTI obteve uma ferramenta extremamente leve, com visual premium e direto ao ponto. Eliminaram-se os gargalos de códigos duplicados, garantindo rastreabilidade histórica e facilitando a atribuição sem necessidade de treinamento complexo dos técnicos.
