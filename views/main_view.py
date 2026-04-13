"""Módulo de interface do usuário para o Gerador de Patrimônio NTI."""

# ==============================================================================
# 1. IMPORTS E DEPENDÊNCIAS
# ==============================================================================
import flet as ft
from models.patrimonio_model import PatrimonioModel

# ==============================================================================
# 2. FUNÇÃO PRINCIPAL DE VIEW
# ==============================================================================
def main(page: ft.Page) -> None:
    """Configura e desenha a janela gráfica central de operação do gerador.

    Args:
        page: Instância base representativa da sessão ativa do controlador visual.
    """
    page.title = "Gerador de Patrimônio NTI"
    page.window_width = 600
    page.window_height = 480
    page.window_min_width = 500
    page.window_min_height = 430
    page.bgcolor = ft.colors.WHITE
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    model = PatrimonioModel()

    # --- 2.1. Componentes Dependentes ---
    combo_tipo = ft.Dropdown(
        label="Tipo de Equipamento",
        options=[
            ft.dropdown.Option("C", "Desktop (C)"),
            ft.dropdown.Option("M", "Monitor (M)"),
            ft.dropdown.Option("N", "Notebook (N)")
        ],
        value="C",
        bgcolor="#f8fafc",
        border_color="#e2e8f0",
        focused_border_color="#132D5C",
        border_radius=12,
        content_padding=15,
        text_size=14,
        expand=True
    )
    
    combo_unidade = ft.Dropdown(
        label="Unidade",
        options=[
            ft.dropdown.Option("305", "305 - Orlando Gomes"),
            ft.dropdown.Option("326", "326 - Park")
        ],
        value="305",
        bgcolor="#f8fafc",
        border_color="#e2e8f0",
        focused_border_color="#132D5C",
        border_radius=12,
        content_padding=15,
        text_size=14,
        expand=True
    )

    texto_codigo = ft.Text("---", size=32, weight=ft.FontWeight.W_900, color="#047857", font_family="monospace")
    
    texto_erro = ft.Text("", color="#dc2626", size=13, weight=ft.FontWeight.W_500)
    container_erro = ft.Container(
        content=ft.Row([ft.Icon(ft.icons.ERROR_OUTLINE, color="#dc2626"), texto_erro]),
        bgcolor="#fef2f2",
        border=ft.border.all(1, "#fee2e2"),
        border_radius=12,
        padding=10,
        visible=False
    )

    btn_copiar_main = ft.IconButton(icon=ft.icons.COPY, icon_color="#059669", tooltip="Copiar Cód.")

    result_container = ft.Container(
        content=ft.Column([
            ft.Text("CÓDIGO GERADO", color="#059669", size=11, weight=ft.FontWeight.BOLD),
            ft.Row([texto_codigo, btn_copiar_main], alignment=ft.MainAxisAlignment.CENTER)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=float('inf'),
        bgcolor="#ecfdf5",
        border=ft.border.all(1, "#d1fae5"),
        border_radius=16,
        padding=20,
        alignment=ft.alignment.center,
        visible=False
    )

    # --- 2.2. Handlers e Callbacks ---
    def update_error(msg: str = "", is_error: bool = True) -> None:
        """Modifica a apresentação visual global do quadro de reporte situacional.

        Args:
            msg: Corpo da mensagem indicativa das reações do sistema.
            is_error: Confirmação estipulativa de falha, demarcando com estilo severo.
        """
        if msg:
            texto_erro.value = msg
            texto_erro.color = "#dc2626" if is_error else "#059669"
            container_erro.bgcolor = "#fef2f2" if is_error else "#ecfdf5"
            container_erro.border = ft.border.all(1, "#fee2e2" if is_error else "#d1fae5")
            container_erro.content.controls[0].name = ft.icons.ERROR_OUTLINE if is_error else ft.icons.INFO_OUTLINE
            container_erro.content.controls[0].color = "#dc2626" if is_error else "#059669"
            container_erro.visible = True
            if is_error:
                result_container.visible = False
        else:
            container_erro.visible = False
        page.update()

    def copiar_codigo(e: ft.ControlEvent) -> None:
        """Aloca em plano virtual o valor atual codificado em sistema de área de transferência.

        Args:
            e: Resposta do gatilho indicativo derivado do controlador de visualização.
        """
        page.set_clipboard(e.control.data)
        update_error("Copiado!", is_error=False)

    btn_copiar_main.on_click = copiar_codigo

    historico_list = ft.Column(spacing=5)

    def handle_gerar(e: ft.ControlEvent) -> None:
        """Direciona os parâmetros presentes nos controladores à confecção de log interno.

        Args:
            e: Resposta transicional indicativa de ação manual de requisição geradora.
        """
        tipo: str = str(combo_tipo.value)
        unidade: str = str(combo_unidade.value)
        
        btn_gerar.disabled = True
        progress_ring.visible = True
        update_error()
        page.update()

        try:
            codigo: str = model.gerar_codigo(tipo, unidade)
            texto_codigo.value = codigo
            btn_copiar_main.data = codigo
            result_container.visible = True
            
            historico_list.controls.insert(0, ft.Container(
                content=ft.Row([
                    ft.Text(codigo, font_family="monospace", weight=ft.FontWeight.BOLD, color="#1e293b", size=13),
                    ft.IconButton(icon=ft.icons.COPY, icon_size=14, data=codigo, on_click=copiar_codigo, tooltip="Copiar")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor="white", border=ft.border.all(1, "#e2e8f0"), border_radius=8, padding=ft.padding.symmetric(horizontal=10, vertical=0)
            ))
            if len(historico_list.controls) > 3:
                historico_list.controls.pop()
        except Exception as ex:
            update_error(str(ex))
        finally:
            btn_gerar.disabled = False
            progress_ring.visible = False
            page.update()

    # --- 2.3. Agregações Estendidas ---
    progress_ring = ft.ProgressRing(width=20, height=20, color="white", visible=False)
    btn_gerar = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.icons.CHECK_CIRCLE, color="white"),
            ft.Text("Gerar Código", color="white", weight=ft.FontWeight.BOLD, size=16),
            progress_ring
        ], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor="#059669",
        height=56,
        on_click=handle_gerar,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=16),
            animation_duration=200
        )
    )
    
    btn_container = ft.Container(content=btn_gerar, width=float('inf'))

    # --- 2.4. Caixas de Interações Contextuais ---
    cfg_tipo = ft.Dropdown(
        label="Tipo",
        options=[
            ft.dropdown.Option("C", "Desktop"),
            ft.dropdown.Option("M", "Monitor"),
            ft.dropdown.Option("N", "Notebook")
        ],
        value="C",
        bgcolor="#f8fafc",
        border_radius=12,
        border_color="#e2e8f0",
        focused_border_color="#132D5C",
        content_padding=15,
        text_size=13
    )
    
    cfg_seed = ft.TextField(
        label="Último Número (6 dígitos)", 
        prefix_text="BT1", 
        keyboard_type=ft.KeyboardType.NUMBER,
        bgcolor="#f8fafc",
        border_radius=12,
        border_color="#e2e8f0",
        focused_border_color="#132D5C",
        content_padding=15,
    )
    
    def fechar_dlg(e: ft.ControlEvent) -> None:
        """Interrompe ativamente a propagação da central visual do diálogo ativo.

        Args:
            e: Resposta situacional perante requisição final de suspensão.
        """
        dlg_config.open = False
        page.update()

    def salvar_config(e: ft.ControlEvent) -> None:
        """Confirmação central à confecção remota da gravação da estrutura condicional em tela.

        Args:
            e: Transição temporal perante aceite de armazenamento no repositório geral.
        """
        if not cfg_seed.value:
            return
        try:
            seed_num: int = int(str(cfg_seed.value))
            model.set_configuracao(str(cfg_tipo.value), seed_num)
            cfg_seed.value = ""
            fechar_dlg(e)
        except Exception as ex:
            print(f"Erro: {ex}")
            
    btn_salvar_cfg = ft.ElevatedButton("Salvar", on_click=salvar_config, bgcolor="#059669", color="white")
    btn_fechar_cfg = ft.TextButton("Cancelar", on_click=fechar_dlg)

    dlg_config = ft.AlertDialog(
        modal=True,
        title=ft.Row([ft.Icon(ft.icons.SETTINGS, color="#132D5C"), ft.Text("Configurar Seed", color="#132D5C", size=18, weight=ft.FontWeight.BOLD)]),
        content=ft.Container(
            content=ft.Column([
                cfg_tipo,
                cfg_seed
            ], tight=True, spacing=15),
            width=350,
            padding=5
        ),
        actions=[btn_fechar_cfg, btn_salvar_cfg],
        actions_padding=10,
        shape=ft.RoundedRectangleBorder(radius=16)
    )

    def abrir_config(e: ft.ControlEvent) -> None:
        """Ativa visualmente o painel condicional em sobreposição para alterações transacionais.

        Args:
            e: Registro pontual sobre gatilho do acionador superior visual estrito.
        """
        page.dialog = dlg_config
        dlg_config.open = True
        page.update()

    # --- 2.5. Montagem Principal de Seções Gráficas ---
    header = ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Text("Gerador de Patrimônio", size=22, weight=ft.FontWeight.BOLD, color="white"),
                ft.Text("Suporte NTI - CIMATEC", size=13, color=ft.colors.WHITE70)
            ], spacing=0),
            ft.IconButton(ft.icons.SETTINGS, icon_color="white", on_click=abrir_config)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor="#132D5C",
        padding=ft.padding.all(20),
        border_radius=ft.border_radius.only(bottom_left=16, bottom_right=16)
    )

    body = ft.Container(
        content=ft.Column([
            ft.Row([combo_tipo, combo_unidade], spacing=15),
            btn_container,
            container_erro,
            result_container,
            ft.Divider(height=10, color=ft.colors.TRANSPARENT),
            ft.Row([
                ft.Icon(ft.icons.HISTORY, size=16, color="#9ca3af"),
                ft.Text("HISTÓRICO DA SESSÃO", size=11, weight=ft.FontWeight.BOLD, color="#9ca3af")
            ]),
            historico_list
        ], spacing=10, scroll=ft.ScrollMode.HIDDEN),
        padding=20,
        expand=True
    )

    page.add(ft.Column([header, body], spacing=0, expand=True))
