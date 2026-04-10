import flet as ft
from models import PatrimonioModel

def main(page: ft.Page):
    # App Settings
    page.title = "Gerador de Patrimônio NTI"
    page.window.width = 600
    page.window.height = 480
    page.window.min_width = 500
    page.window.min_height = 430
    page.bgcolor = ft.Colors.WHITE
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # Model Initialization
    model = PatrimonioModel()

    # == UI Elements for Main View ==
    
    # Dropdowns
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

    # Generated Code display
    texto_codigo = ft.Text("---", size=32, weight=ft.FontWeight.W_900, color="#047857", font_family="monospace")
    
    # Error Display
    texto_erro = ft.Text("", color="#dc2626", size=13, weight=ft.FontWeight.W_500)
    container_erro = ft.Container(
        content=ft.Row([ft.Icon(ft.icons.ERROR_OUTLINE, color="#dc2626"), texto_erro]),
        bgcolor="#fef2f2",
        border=ft.border.all(1, "#fee2e2"),
        border_radius=12,
        padding=10,
        visible=False
    )

    result_container = ft.Container(
        content=ft.Column([
            ft.Text("CÓDIGO GERADO", color="#059669", size=11, weight=ft.FontWeight.BOLD),
            texto_codigo
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=float('inf'),
        bgcolor="#ecfdf5",
        border=ft.border.all(1, "#d1fae5"),
        border_radius=16,
        padding=20,
        alignment=ft.alignment.center,
        visible=False
    )

    # == Handlers ==
    def update_error(msg=""):
        if msg:
            texto_erro.value = msg
            container_erro.visible = True
            result_container.visible = False
        else:
            container_erro.visible = False
        page.update()

    def handle_gerar(e):
        tipo = combo_tipo.value
        unidade = combo_unidade.value
        
        btn_gerar.disabled = True
        progress_ring.visible = True
        update_error()
        page.update()

        try:
            codigo = model.gerar_codigo(tipo, unidade)
            texto_codigo.value = codigo
            result_container.visible = True
            update_filas()
        except Exception as ex:
            update_error(str(ex))
        finally:
            btn_gerar.disabled = False
            progress_ring.visible = False
            page.update()

    # == Components ==
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
    
    # Wrapped in container to simulate 100% width block
    btn_container = ft.Container(content=btn_gerar, width=float('inf'))

    # == Config Dialog Elements ==
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
        text_size=13,
        expand=True
    )
    cfg_unidade = ft.Dropdown(
        label="Unidade",
        options=[
            ft.dropdown.Option("305", "305 - OG"),
            ft.dropdown.Option("326", "326 - Park")
        ],
        value="305",
        bgcolor="#f8fafc",
        border_radius=12,
        border_color="#e2e8f0",
        focused_border_color="#132D5C",
        content_padding=15,
        text_size=13,
        expand=True
    )
    cfg_seed = ft.TextField(
        label="Último Número (6 dígitos)", 
        prefix_text="BT", 
        keyboard_type=ft.KeyboardType.NUMBER,
        bgcolor="#f8fafc",
        border_radius=12,
        border_color="#e2e8f0",
        focused_border_color="#132D5C",
        content_padding=15,
    )
    
    def fechar_dlg(e):
        dlg_config.open = False
        page.update()

    def salvar_config(e):
        if not cfg_seed.value:
            return
        try:
            seed_num = int(cfg_seed.value)
            model.set_configuracao(cfg_tipo.value, cfg_unidade.value, seed_num)
            cfg_seed.value = ""
            fechar_dlg(e)
            update_filas()
        except Exception as ex:
            print("Erro:", ex)
            
    btn_salvar_cfg = ft.ElevatedButton("Salvar", on_click=salvar_config, bgcolor="#059669", color="white")
    btn_fechar_cfg = ft.TextButton("Cancelar", on_click=fechar_dlg)

    dlg_config = ft.AlertDialog(
        modal=True,
        title=ft.Row([ft.Icon(ft.icons.SETTINGS, color="#132D5C"), ft.Text("Configurar Seed", color="#132D5C", size=18, weight=ft.FontWeight.BOLD)]),
        content=ft.Container(
            content=ft.Column([
                ft.Row([cfg_tipo, cfg_unidade], spacing=10),
                cfg_seed
            ], tight=True, spacing=15),
            width=350,
            padding=5
        ),
        actions=[btn_fechar_cfg, btn_salvar_cfg],
        actions_padding=10,
        shape=ft.RoundedRectangleBorder(radius=16)
    )

    def abrir_config(e):
        page.dialog = dlg_config
        dlg_config.open = True
        page.update()

    filas_view = ft.Row(wrap=True, spacing=10)

    def update_filas():
        filas = model.get_configuracoes()
        filas_view.controls.clear()
        
        if not filas:
            filas_view.controls.append(ft.Text("Nenhuma fila configurada.", italic=True, size=12, color="#6b7280"))
        else:
            for fila in filas:
                filas_view.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"{fila['Tipo_Equip']}{fila['Unidade']}", size=10, weight=ft.FontWeight.BOLD, color="#6b7280"),
                            ft.Text(f"BT{str(fila['Ultimo_Codigo']).zfill(6)}", size=14, weight=ft.FontWeight.W_800, font_family="monospace")
                        ], spacing=0),
                        bgcolor="#f8fafc", 
                        border=ft.border.all(1, "#f1f5f9"), 
                        border_radius=12, 
                        padding=12,
                        width=180
                    )
                )
        page.update()

    # == Page Layout ==
    header = ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Text("Gerador de Patrimônio", size=22, weight=ft.FontWeight.BOLD, color="white"),
                ft.Text("Suporte NTI - CIMATEC", size=13, color=ft.Colors.WHITE70)
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
            ft.Container(height=10),
            btn_container,
            ft.Container(height=5),
            container_erro,
            result_container,
            ft.Divider(height=25, color=ft.Colors.TRANSPARENT),
            ft.Row([
                ft.Icon(ft.icons.HISTORY, size=16, color="#9ca3af"),
                ft.Text("STATUS DAS FILAS", size=11, weight=ft.FontWeight.BOLD, color="#9ca3af")
            ]),
            filas_view
        ], spacing=10, scroll=ft.ScrollMode.HIDDEN),
        padding=20,
        expand=True
    )

    page.add(ft.Column([header, body], spacing=0, expand=True))
    update_filas()


if __name__ == "__main__":
    ft.app(target=main)
