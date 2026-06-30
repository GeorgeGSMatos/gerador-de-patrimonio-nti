"""Módulo de interface do usuário para o Gerador de Patrimônio NTI."""

# ==============================================================================
# 1. IMPORTS E DEPENDÊNCIAS
# ==============================================================================
import logging
import threading

import flet as ft

from config import (
    CODIGO_ZFILL,
    HISTORICO_SESSAO_MAX,
    SEED_MAX,
    SEED_MIN,
    TIPOS_EQUIPAMENTO,
    UNIDADES,
    WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_WIDTH,
)
from controllers.patrimonio_controller import PatrimonioController
from models.patrimonio_model import _get_usuario

logger = logging.getLogger(__name__)


# ==============================================================================
# 2. FUNÇÃO PRINCIPAL DE VIEW
# ==============================================================================
def main(page: ft.Page) -> None:
    """Configura e desenha a janela gráfica central de operação do gerador.

    Args:
        page: Instância base representativa da sessão ativa do controlador visual.
    """
    page.title = "Gerador de Patrimônio NTI"
    page.window_width = WINDOW_WIDTH
    page.window_height = WINDOW_HEIGHT
    page.window_min_width = WINDOW_MIN_WIDTH
    page.window_min_height = WINDOW_MIN_HEIGHT
    page.bgcolor = ft.colors.WHITE
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # --- 2.1. Inicialização do Controller ---
    controller: PatrimonioController | None = None
    try:
        controller = PatrimonioController()
    except RuntimeError as e:
        erro_str = str(e)
        erros_conexao_kw = ("getaddrinfo", "pausado", "conectar", "supabase")
        if any(kw in erro_str.lower() for kw in erros_conexao_kw):
            _exibir_tela_pausado(page)
        else:
            _exibir_erro_critico(page, erro_str)
        return

    # Estado de controle anti-duplo-clique
    _gerando = threading.Event()

    # --- 2.2. Componentes da Aba "Gerar" ---
    combo_tipo = ft.Dropdown(
        label="Tipo de Equipamento",
        options=[ft.dropdown.Option(t["key"], t["label"]) for t in TIPOS_EQUIPAMENTO],
        value=TIPOS_EQUIPAMENTO[0]["key"],
        filled=True,
        bgcolor="#f8fafc",
        border_color="#e2e8f0",
        focused_border_color="#132D5C",
        border_radius=12,
        content_padding=15,
        text_size=14,
        expand=True,
    )

    combo_unidade = ft.Dropdown(
        label="Unidade",
        options=[ft.dropdown.Option(u["key"], u["label"]) for u in UNIDADES],
        value=UNIDADES[0]["key"],
        filled=True,
        bgcolor="#f8fafc",
        border_color="#e2e8f0",
        focused_border_color="#132D5C",
        border_radius=12,
        content_padding=15,
        text_size=14,
        expand=True,
    )

    texto_codigo = ft.Text(
        "---",
        size=32,
        weight=ft.FontWeight.W_900,
        color="#047857",
        font_family="monospace",
    )

    texto_erro = ft.Text("", color="#dc2626", size=13, weight=ft.FontWeight.W_500)
    container_erro = ft.Container(
        content=ft.Row([ft.Icon(ft.icons.ERROR_OUTLINE, color="#dc2626"), texto_erro]),
        bgcolor="#fef2f2",
        border=ft.border.all(1, "#fee2e2"),
        border_radius=12,
        padding=10,
        visible=False,
    )

    # --- Banner: Supabase Pausado ---
    _reconectando = threading.Event()

    def _tentar_reconectar(e: ft.ControlEvent) -> None:
        """Tenta reinicializar o controller em background após o usuário despausar."""
        if _reconectando.is_set():
            return
        _reconectando.set()
        btn_reconectar.disabled = True
        ring_reconectar.visible = True
        txt_reconectar_status.value = "Tentando conectar..."
        page.update()

        def _reconectar_bg() -> None:
            nonlocal controller
            try:
                novo_controller = PatrimonioController()
                controller = novo_controller
                page.controls.clear()
                page.update()
                main(page)
            except Exception as exc:
                logger.warning("Reconexão falhou: %s", exc)
                btn_reconectar.disabled = False
                ring_reconectar.visible = False
                txt_reconectar_status.value = "Ainda sem conexão. Verifique o Supabase e tente novamente."
                _reconectando.clear()
                page.update()

        threading.Thread(target=_reconectar_bg, daemon=True).start()

    ring_reconectar = ft.ProgressRing(width=16, height=16, color="#b45309", visible=False)
    btn_reconectar = ft.ElevatedButton(
        content=ft.Row(
            [ft.Icon(ft.icons.REFRESH, color="white", size=16),
             ft.Text("Reconectar", color="white", weight=ft.FontWeight.BOLD, size=13),
             ring_reconectar],
            spacing=6,
            tight=True,
        ),
        bgcolor="#b45309",
        height=38,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=_tentar_reconectar,
    )
    txt_reconectar_status = ft.Text(
        "Despause o projeto em app.supabase.com e clique em Reconectar.",
        size=12,
        color="#92400e",
    )
    banner_pausado = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.icons.CLOUD_OFF, color="#b45309", size=20),
                        ft.Text(
                            "Supabase pausado",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color="#92400e",
                        ),
                    ],
                    spacing=8,
                ),
                txt_reconectar_status,
                btn_reconectar,
            ],
            spacing=8,
        ),
        bgcolor="#fffbeb",
        border=ft.border.all(1, "#fde68a"),
        border_radius=12,
        padding=14,
        visible=False,
    )

    btn_copiar_main = ft.IconButton(
        icon=ft.icons.COPY, icon_color="#059669", tooltip="Copiar Cód."
    )

    result_container = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "CÓDIGO GERADO", color="#059669", size=11, weight=ft.FontWeight.BOLD
                ),
                ft.Row(
                    [texto_codigo, btn_copiar_main],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=float("inf"),
        bgcolor="#ecfdf5",
        border=ft.border.all(1, "#d1fae5"),
        border_radius=16,
        padding=20,
        alignment=ft.alignment.center,
        visible=False,
    )

    # --- 2.3. Handlers e Callbacks ---
    def update_feedback(msg: str = "", is_error: bool = True) -> None:
        """Exibe ou limpa a faixa de feedback visual (erro ou sucesso)."""
        if msg:
            texto_erro.value = msg
            icon: ft.Icon = container_erro.content.controls[0]
            texto_erro.color = "#dc2626" if is_error else "#059669"
            container_erro.bgcolor = "#fef2f2" if is_error else "#ecfdf5"
            container_erro.border = ft.border.all(
                1, "#fee2e2" if is_error else "#d1fae5"
            )
            icon.name = ft.icons.ERROR_OUTLINE if is_error else ft.icons.INFO_OUTLINE
            icon.color = "#dc2626" if is_error else "#059669"
            container_erro.visible = True
            if is_error:
                result_container.visible = False
        else:
            container_erro.visible = False
        page.update()

    def copiar_codigo(e: ft.ControlEvent) -> None:
        """Copia o código do evento para a área de transferência."""
        page.set_clipboard(e.control.data)
        page.snack_bar = ft.SnackBar(
            ft.Text("Copiado para a área de transferência!", color="white"),
            bgcolor="#059669",
        )
        page.snack_bar.open = True
        page.update()

    btn_copiar_main.on_click = copiar_codigo

    # --- 2.4. Aba Histórico ---
    historico_list = ft.Column(spacing=5)
    texto_contador = ft.Text(
        "Carregando histórico...", size=11, color="#9ca3af"
    )

    def _atualizar_historico() -> None:
        """Busca os últimos códigos no banco de dados e atualiza a interface."""
        historicos = controller.get_ultimos_historicos(HISTORICO_SESSAO_MAX)
        historico_list.controls.clear()

        for item in historicos:
            codigo = item.get("Codigo_Patrimonio", "---")
            usuario_db = item.get("Usuario", "desconhecido")
            data_hora = item.get("Data_Hora", "")

            historico_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(
                                        codigo,
                                        font_family="monospace",
                                        weight=ft.FontWeight.BOLD,
                                        color="#1e293b",
                                        size=13,
                                    ),
                                    ft.Text(
                                        f"Gerado por: {usuario_db}  •  {data_hora}",
                                        size=10,
                                        color="#64748b",
                                        italic=True,
                                    ),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.icons.COPY,
                                icon_size=14,
                                data=codigo,
                                on_click=copiar_codigo,
                                tooltip="Copiar",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    bgcolor="white",
                    border=ft.border.all(1, "#e2e8f0"),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                )
            )

        total = len(historico_list.controls)
        texto_contador.value = f"Mostrando os últimos {total} código(s)"
        page.update()

    # --- 2.5. Geração de Código ---
    def _executar_geracao() -> None:
        """Executa a geração do código em thread separada para não bloquear a UI."""
        resultado = controller.gerar(
            {
                "tipo": str(combo_tipo.value),
                "unidade": str(combo_unidade.value),
            }
        )

        if resultado.get("pausado"):
            banner_pausado.visible = True
            txt_reconectar_status.value = "Despause o projeto em app.supabase.com e clique em Reconectar."
            btn_reconectar.disabled = False
            ring_reconectar.visible = False
            container_erro.visible = False
            result_container.visible = False
        elif "error" in resultado:
            banner_pausado.visible = False
            update_feedback(resultado["error"])
        else:
            banner_pausado.visible = False
            codigo: str = resultado["codigo"]
            texto_codigo.value = codigo
            btn_copiar_main.data = codigo
            result_container.visible = True
            _atualizar_historico()
            update_feedback()

        btn_gerar.disabled = False
        progress_ring.visible = False
        _gerando.clear()
        page.update()

    def handle_gerar(e: ft.ControlEvent) -> None:
        """Inicia a geração de código se não houver operação em andamento."""
        if _gerando.is_set():
            return

        _gerando.set()
        btn_gerar.disabled = True
        progress_ring.visible = True
        update_feedback()
        page.update()

        threading.Thread(target=_executar_geracao, daemon=True).start()

    # --- 2.6. Botão de Gerar ---
    progress_ring = ft.ProgressRing(width=20, height=20, color="white", visible=False)
    btn_gerar = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.icons.CHECK_CIRCLE, color="white"),
                ft.Text(
                    "Gerar Código", color="white", weight=ft.FontWeight.BOLD, size=16
                ),
                progress_ring,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor="#059669",
        height=56,
        on_click=handle_gerar,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=16), animation_duration=200
        ),
    )

    btn_container = ft.Container(content=btn_gerar, width=float("inf"))

    # --- 2.7. Dialog de Configuração (Salvar seed + Excluir + Reset) ---
    cfg_tipo = ft.Dropdown(
        options=[
            ft.dropdown.Option(t["key"], t["label"].split(" (")[0])
            for t in TIPOS_EQUIPAMENTO
        ],
        value=TIPOS_EQUIPAMENTO[0]["key"],
        filled=True,
        bgcolor="#f8fafc",
        border_radius=8,
        border_color="#e2e8f0",
        focused_border_color="#132D5C",
        content_padding=15,
        text_size=13,
    )

    cfg_seed = ft.TextField(
        prefix_text="BT",
        keyboard_type=ft.KeyboardType.NUMBER,
        filled=True,
        bgcolor="#f8fafc",
        border_radius=8,
        border_color="#e2e8f0",
        focused_border_color="#132D5C",
        content_padding=15,
    )

    cfg_excluir_codigo = ft.TextField(
        hint_text="Ex: N305-BT100123",
        keyboard_type=ft.KeyboardType.TEXT,
        filled=True,
        bgcolor="#f8fafc",
        border_radius=8,
        border_color="#e2e8f0",
        focused_border_color="#dc2626",
        content_padding=15,
    )

    # --- Dialogs de confirmação ---
    dlg_confirmacao = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            [
                ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="#d97706"),
                ft.Text(
                    "Confirmar alteração",
                    color="#1e293b",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                ),
            ]
        ),
        content=ft.Text("", size=14),
        shape=ft.RoundedRectangleBorder(radius=16),
    )

    dlg_confirmar_exclusao = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            [
                ft.Icon(ft.icons.DELETE_FOREVER, color="#dc2626"),
                ft.Text(
                    "Confirmar exclusão",
                    color="#dc2626",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                ),
            ]
        ),
        content=ft.Text("", size=14),
        shape=ft.RoundedRectangleBorder(radius=16),
    )

    dlg_confirmar_reset = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            [
                ft.Icon(ft.icons.DANGEROUS, color="#991b1b"),
                ft.Text("Aviso de Exclusão Total", color="#991b1b", size=18, weight=ft.FontWeight.BOLD),
            ]
        ),
        content=ft.Text(
            "Atenção: Você está prestes a apagar TODOS os patrimônios gerados e zerar as contagens de todos os equipamentos.\n\n"
            "Ao confirmar, o sistema ficará completamente vazio, como se nunca tivesse sido usado. Essa ação não pode ser desfeita.\n\n"
            "Deseja realmente apagar tudo?",
            size=14, color="#1e293b"
        ),
        shape=ft.RoundedRectangleBorder(radius=16),
    )

    def fechar_dlg_reset(e: ft.ControlEvent) -> None:
        dlg_confirmar_reset.open = False
        page.update()

    def _confirmar_e_resetar(e: ft.ControlEvent) -> None:
        dlg_confirmar_reset.open = False
        page.update()
        
        resultado = controller.resetar_banco()
        if "error" in resultado:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao resetar: {resultado['error']}"), bgcolor="#dc2626")
            page.snack_bar.open = True
            page.update()
            return
            
        dlg_config.open = False
        _atualizar_historico()
        page.snack_bar = ft.SnackBar(
            ft.Text("Banco de dados resetado com sucesso! Tudo foi zerado."),
            bgcolor="#059669"
        )
        page.snack_bar.open = True
        page.update()

    def abrir_dialog_reset() -> None:
        dlg_confirmar_reset.actions = [
            ft.TextButton("Cancelar", on_click=fechar_dlg_reset),
            ft.ElevatedButton("Sim, Apagar Tudo", bgcolor="#991b1b", color="white", on_click=_confirmar_e_resetar)
        ]
        dlg_confirmar_reset.actions_padding = 10
        dlg_confirmar_reset.open = True
        page.update()

    def fechar_dlg(e: ft.ControlEvent) -> None:
        """Fecha o dialog de configuração."""
        dlg_config.open = False
        cfg_seed.error_text = None
        cfg_excluir_codigo.error_text = None
        page.update()

    def fechar_dlg_confirmacao(e: ft.ControlEvent) -> None:
        """Fecha o dialog de confirmação sem salvar."""
        dlg_confirmacao.open = False
        page.update()

    def fechar_dlg_exclusao(e: ft.ControlEvent) -> None:
        """Fecha o dialog de confirmação de exclusão."""
        dlg_confirmar_exclusao.open = False
        page.update()

    def _confirmar_e_salvar(tipo: str, seed_num: int) -> None:
        """Persiste a seed após confirmação e exibe snackbar de resultado."""
        dlg_confirmacao.open = False
        resultado = controller.configurar({"tipo": tipo, "seed": seed_num})

        if "error" in resultado:
            cfg_seed.error_text = f"Erro ao salvar: {resultado['error']}"
            page.update()
            return

        cfg_seed.value = ""
        dlg_config.open = False
        page.snack_bar = ft.SnackBar(
            ft.Text(f"Seed para '{tipo}' atualizada para {seed_num:0{CODIGO_ZFILL}d}!"),
            bgcolor="#059669",
        )
        page.snack_bar.open = True
        page.update()

    def _confirmar_e_excluir(tipo: str, codigo_num: int) -> None:
        """Executa a exclusão após confirmação e exibe snackbar de resultado."""
        dlg_confirmar_exclusao.open = False
        page.update()

        resultado = controller.excluir({"tipo": tipo, "codigo_num": codigo_num})

        if "error" in resultado:
            cfg_excluir_codigo.error_text = f"Erro: {resultado['error']}"
            page.update()
            return

        qtd = resultado.get("qtd", 0)
        cfg_excluir_codigo.value = ""
        dlg_config.open = False
        _atualizar_historico()
        page.snack_bar = ft.SnackBar(
            ft.Text(f"Excluídos {qtd} registro(s). Seed rebobinada com sucesso!"),
            bgcolor="#059669",
        )
        page.snack_bar.open = True
        page.update()

    def salvar_config(e: ft.ControlEvent) -> None:
        """Valida a seed informada e abre dialog de confirmação antes de persistir."""
        cfg_seed.error_text = None

        if not cfg_seed.value:
            cfg_seed.error_text = "O campo não pode estar vazio."
            page.update()
            return

        seed_text = str(cfg_seed.value).strip()
        if not seed_text.isdigit():
            cfg_seed.error_text = "Insira apenas números."
            page.update()
            return

        seed_num = int(seed_text)
        if not (SEED_MIN <= seed_num <= SEED_MAX):
            cfg_seed.error_text = f"Valor deve estar entre {SEED_MIN} e {SEED_MAX:,}."
            page.update()
            return

        tipo = str(cfg_tipo.value)

        # Buscar valor atual para exibir no dialog
        configs = controller.get_configuracoes()
        atual = next(
            (c["Ultimo_Codigo"] for c in configs if c["Tipo_Equip"] == tipo),
            "não configurado",
        )

        dlg_confirmacao.content = ft.Text(
            f"Tipo: {tipo}\n\nValor atual: {atual}\nNovo valor: {seed_num:0{CODIGO_ZFILL}d}\n\n"
            "Confirma a substituição?",
            size=14,
        )
        dlg_confirmacao.actions = [
            ft.TextButton("Cancelar", on_click=fechar_dlg_confirmacao),
            ft.ElevatedButton(
                "Confirmar",
                bgcolor="#059669",
                color="white",
                on_click=lambda _: _confirmar_e_salvar(tipo, seed_num),
            ),
        ]
        dlg_confirmacao.actions_padding = 10
        dlg_confirmacao.open = True
        page.update()

    def excluir_patrimonio(e: ft.ControlEvent) -> None:
        """Valida o código de exclusão completo e abre dialog de confirmação."""
        cfg_excluir_codigo.error_text = None

        if not cfg_excluir_codigo.value:
            cfg_excluir_codigo.error_text = "Informe o código completo."
            page.update()
            return

        cod_text = str(cfg_excluir_codigo.value).strip().upper()
        if "-" not in cod_text:
            cfg_excluir_codigo.error_text = "Formato inválido. Ex: N305-BT100123"
            page.update()
            return

        partes = cod_text.split("-")
        prefixo = partes[0]
        numero_str = partes[1]

        numero_str_limpo = numero_str.replace("BT", "")
        if not numero_str_limpo.isdigit():
            cfg_excluir_codigo.error_text = "O final do código deve conter apenas números após BT."
            page.update()
            return

        codigo_num = int(numero_str_limpo)
        
        # Parse Unidade
        unidade_encontrada = None
        from config import UNIDADES, TIPOS_EQUIPAMENTO
        for u in UNIDADES:
            if prefixo.endswith(u["key"]):
                unidade_encontrada = u
                break
        
        if not unidade_encontrada:
            cfg_excluir_codigo.error_text = "Unidade não reconhecida no código."
            page.update()
            return

        # Parse Tipo
        tipo_str = prefixo[:-len(unidade_encontrada["key"])]
        
        tipo_encontrado = None
        for t in TIPOS_EQUIPAMENTO:
            if t["key"] == tipo_str:
                tipo_encontrado = t
                break
                
        if not tipo_encontrado:
            cfg_excluir_codigo.error_text = "Tipo de equipamento não reconhecido."
            page.update()
            return
            
        tipo = tipo_encontrado["key"]
        nome_tipo = tipo_encontrado["label"].split(" (")[0]
        nome_unidade = unidade_encontrada["label"]

        # Validação para só excluir o que já existe
        configs = controller.get_configuracoes()
        ultimo_codigo = next(
            (c["Ultimo_Codigo"] for c in configs if c["Tipo_Equip"] == tipo),
            0,
        )

        if codigo_num > ultimo_codigo:
            cfg_excluir_codigo.error_text = f"Erro: Último número de {nome_tipo} foi {ultimo_codigo}."
            page.update()
            return

        dlg_confirmar_exclusao.content = ft.Text(
            f"Equipamento: {nome_tipo}\n"
            f"Unidade: {nome_unidade}\n\n"
            f"Atenção: O patrimônio {cod_text} e todos os {nome_tipo}s com número maior que ele serão apagados do sistema.\n\n"
            f"A contagem voltará a partir do número {max(0, codigo_num - 1):0{CODIGO_ZFILL}d}.\n\n"
            "Essa ação não pode ser desfeita. Tem certeza?",
            size=14,
        )
        dlg_confirmar_exclusao.actions = [
            ft.TextButton("Cancelar", on_click=fechar_dlg_exclusao),
            ft.ElevatedButton(
                "Sim, Apagar",
                bgcolor="#dc2626",
                color="white",
                on_click=lambda _: _confirmar_e_excluir(tipo, codigo_num),
            ),
        ]
        dlg_confirmar_exclusao.actions_padding = 10
        dlg_confirmar_exclusao.open = True
        page.update()

    # --- Seções Minimalistas do Dialog ---
    btn_salvar_cfg = ft.ElevatedButton(
        "Salvar Novo Número", on_click=salvar_config, bgcolor="#059669", color="white",
        height=48,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )

    col_tipo = ft.Column([
        ft.Text("Tipo de Equipamento", size=12, color="#64748b", weight=ft.FontWeight.W_500),
        cfg_tipo
    ], spacing=4, expand=2)

    col_numero = ft.Column([
        ft.Text("Novo Número", size=12, color="#64748b", weight=ft.FontWeight.W_500),
        cfg_seed
    ], spacing=4, expand=3)

    col_btn_salvar = ft.Column([
        ft.Text(" ", size=12),  # Espaçador invisível para empurrar o botão para baixo e alinhar
        btn_salvar_cfg
    ], spacing=4)

    secao_seed = ft.Column(
        [
            ft.Text("Mudar Início da Contagem", size=15, weight=ft.FontWeight.BOLD, color="#1e293b"),
            ft.Text("Define manualmente qual será o próximo número de patrimônio gerado para o equipamento escolhido.", size=12, color="#64748b"),
            ft.Row([col_tipo, col_numero, col_btn_salvar], spacing=15, vertical_alignment=ft.CrossAxisAlignment.START)
        ],
        spacing=8
    )

    btn_excluir_cfg = ft.ElevatedButton(
        "Apagar a partir deste", on_click=excluir_patrimonio, color="#dc2626", bgcolor="#fee2e2",
        height=48,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )

    col_excluir_codigo = ft.Column([
        ft.Text("Código Completo", size=12, color="#64748b", weight=ft.FontWeight.W_500),
        cfg_excluir_codigo
    ], spacing=4, expand=True)

    col_btn_excluir = ft.Column([
        ft.Text(" ", size=12),
        btn_excluir_cfg
    ], spacing=4)

    secao_excluir = ft.Column(
        [
            ft.Text("Apagar Patrimônios Errados", size=15, weight=ft.FontWeight.BOLD, color="#1e293b"),
            ft.Text("Apaga o número informado e todos os números maiores que ele. A contagem voltará ao normal.", size=12, color="#64748b"),
            ft.Row([col_excluir_codigo, col_btn_excluir], spacing=15, vertical_alignment=ft.CrossAxisAlignment.START)
        ],
        spacing=8
    )

    btn_reset_db = ft.ElevatedButton(
        "Zerar o Sistema",
        icon=ft.icons.WARNING_AMBER,
        icon_color="white",
        color="white",
        bgcolor="#991b1b",
        height=48,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=lambda _: abrir_dialog_reset()
    )

    secao_perigo = ft.Column(
        [
            ft.Text("Restaurar Sistema", size=15, weight=ft.FontWeight.BOLD, color="#991b1b"),
            ft.Text("Apaga permanentemente todo o histórico gerado e reinicia a contagem de todos os equipamentos.", size=12, color="#991b1b"),
            ft.Row([btn_reset_db], alignment=ft.MainAxisAlignment.START)
        ],
        spacing=8
    )

    btn_fechar_cfg_dialog = ft.TextButton("Fechar Configurações", on_click=fechar_dlg)

    dlg_config = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            [
                ft.Icon(ft.icons.SETTINGS, color="#132D5C"),
                ft.Text("Configurações do Sistema", color="#132D5C", size=18, weight=ft.FontWeight.BOLD),
            ]
        ),
        content=ft.Container(
            content=ft.Column(
                [
                    secao_seed,
                    ft.Divider(height=30, color="#e2e8f0"),
                    secao_excluir,
                    ft.Divider(height=30, color="#e2e8f0"),
                    secao_perigo
                ],
                tight=True,
                spacing=0,
                scroll=ft.ScrollMode.AUTO
            ),
            width=650,
            padding=10,
        ),
        actions=[btn_fechar_cfg_dialog],
        actions_padding=10,
        shape=ft.RoundedRectangleBorder(radius=16),
    )

    # Registrar todos os dialogs no overlay para evitar conflitos
    page.overlay.extend([dlg_config, dlg_confirmacao, dlg_confirmar_exclusao, dlg_confirmar_reset])

    def abrir_config(e: ft.ControlEvent) -> None:
        """Abre o painel de configuração de seed."""
        dlg_config.open = True
        page.update()

    # --- 2.8. Callback de mudança de aba ---
    def on_tab_change(e: ft.ControlEvent) -> None:
        """Atualiza o histórico automaticamente ao mudar para a aba Histórico."""
        if e.control.selected_index == 1:
            _atualizar_historico()

    # --- 2.9. Montagem Principal de Seções Gráficas ---
    header = ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(
                            "Gerador de Patrimônio",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color="white",
                        ),
                        ft.Text(
                            "Suporte NTI - CIMATEC", size=13, color=ft.colors.WHITE70
                        ),
                    ],
                    spacing=0,
                ),
                ft.IconButton(
                    ft.icons.SETTINGS, icon_color="white", on_click=abrir_config
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        bgcolor="#132D5C",
        padding=ft.padding.all(20),
        border_radius=ft.border_radius.only(bottom_left=16, bottom_right=16),
    )

    # --- Aba Gerar ---
    tab_gerar = ft.Tab(
        text="Gerar",
        icon=ft.icons.QR_CODE,
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Row([combo_tipo, combo_unidade], spacing=15),
                    btn_container,
                    banner_pausado,
                    container_erro,
                    result_container,
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
        ),
    )

    # --- Aba Histórico ---
    tab_historico = ft.Tab(
        text="Histórico",
        icon=ft.icons.HISTORY,
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.HISTORY, size=16, color="#9ca3af"),
                            ft.Text(
                                "HISTÓRICO DE PATRIMÔNIOS",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color="#9ca3af",
                            ),
                            ft.IconButton(
                                icon=ft.icons.REFRESH,
                                icon_size=14,
                                icon_color="#9ca3af",
                                tooltip="Atualizar histórico",
                                on_click=lambda e: _atualizar_historico(),
                            ),
                            ft.Container(expand=True),
                            texto_contador,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    historico_list,
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
        ),
    )

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[tab_gerar, tab_historico],
        expand=True,
        on_change=on_tab_change,
    )

    page.add(ft.Column([header, tabs], spacing=0, expand=True))

    # Atualiza o histórico ao iniciar a aplicação
    _atualizar_historico()


# ==============================================================================
# 3. FUNÇÕES AUXILIARES DE VIEW
# ==============================================================================
def _exibir_erro_critico(page: ft.Page, mensagem: str) -> None:
    """Renderiza uma tela de erro fatal quando o banco de dados não pode ser acessado.

    Args:
        page: Instância da página Flet ativa.
        mensagem: Descrição do erro a ser exibido para o usuário.
    """
    logger.critical("Erro crítico na inicialização da view: %s", mensagem)
    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.icons.ERROR, color="#dc2626", size=64),
                    ft.Text(
                        "Falha ao inicializar o sistema",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color="#1e293b",
                    ),
                    ft.Text(
                        mensagem,
                        size=13,
                        color="#64748b",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            expand=True,
            alignment=ft.alignment.center,
            padding=40,
        )
    )
    page.update()


def _exibir_tela_pausado(page: ft.Page) -> None:
    """Renderiza uma tela dedicada informando que o Supabase está pausado.

    Exibe um botão de reconexão que, ao ser clicado, tenta reinicializar
    a aplicação completa após o usuário despausar o projeto.

    Args:
        page: Instância da página Flet ativa.
    """
    logger.warning("Supabase pausado detectado na inicialização.")

    _reconectando = threading.Event()
    ring = ft.ProgressRing(width=18, height=18, color="white", visible=False)
    txt_status = ft.Text(
        "Despause o projeto em app.supabase.com e clique em Reconectar.",
        size=12,
        color="#92400e",
        text_align=ft.TextAlign.CENTER,
    )
    btn = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.icons.REFRESH, color="white", size=16),
                ft.Text("Reconectar", color="white", weight=ft.FontWeight.BOLD, size=14),
                ring,
            ],
            spacing=8,
            tight=True,
        ),
        bgcolor="#b45309",
        height=44,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
    )

    def _tentar(e: ft.ControlEvent) -> None:
        if _reconectando.is_set():
            return
        _reconectando.set()
        btn.disabled = True
        ring.visible = True
        txt_status.value = "Tentando conectar ao Supabase..."
        page.update()

        def _bg() -> None:
            try:
                PatrimonioController()  # testa conexão
                page.controls.clear()
                page.update()
                main(page)
            except Exception as exc:
                logger.warning("Reconexão falhou: %s", exc)
                btn.disabled = False
                ring.visible = False
                txt_status.value = "Ainda sem conexão. Verifique o Supabase e tente novamente."
                _reconectando.clear()
                page.update()

        threading.Thread(target=_bg, daemon=True).start()

    btn.on_click = _tentar

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.icons.CLOUD_OFF, color="#b45309", size=64),
                    ft.Text(
                        "Supabase pausado",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color="#92400e",
                    ),
                    ft.Text(
                        "O banco de dados está pausado por inatividade (plano gratuito).",
                        size=13,
                        color="#64748b",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    txt_status,
                    btn,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
            ),
            expand=True,
            alignment=ft.alignment.center,
            padding=40,
        )
    )
    page.update()
