import copy
import tkinter as tk

from pathlib import Path
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from render import SpriteRenderer
import shutil

from PIL import Image
from PIL import ImageTk

import objects

class SpeedRacerEditor:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root

        self.root.title("Speed Racer Resource Editor")
        self.root.geometry("1000x650")
        self.root.minsize(800, 500)

        self.escala = 4
        self.cor_atual = 0
        self.desenhando = False

        self.idioma_var = tk.StringVar(
            value="en"
        )

        self.idioma_atual = "en"  

        self.textos = {
            "en": {
                "abrir": "Open OBJECTS*.BIN",
                "salvar": "Save",
                "exportar": "Export",
                "importar": "Import",
                "instrucoes": "Instructions",
                "nenhum_arquivo": "No file opened",
                "sprites": "Sprites",
                "numero": "#",
                "tamanho": "Size",
                "visualizacao": "Preview",
                "pronto": "Ready",
                "import_title": "Import",
                "import_no_sprite": "No sprite selected.",
                "import_select_png": "Select a sprite PNG",
                "png_file": "PNG image",
                "import_success": "Sprite imported successfully!",
                "import_memory": (
                    "The change is currently stored only in memory.\n"
                    "Click Save to write it to the OBJECTS.BIN file."
                ),
                "import_pending": "PNG imported — not saved yet",  
                "creditos": "Developed by FQ",     
                "export_title": "Export",
                "export_dialog_title": "Export Sprites",
                "export_no_file": "No file has been opened.",
                "export_question": "What do you want to export?",
                "export_selected": "Selected sprite",
                "export_all": "All sprites",
                "export_scale": "Scale",
                "export_button": "Export",
                "cancel_button": "Cancel",
                "export_no_sprite": "No sprite selected.",
                "export_select_file": "Export sprite",
                "export_select_folder": "Choose a folder to export the sprites",
                "png_file": "PNG image",
                "export_error_title": "Export error",
                "export_sprite_error": (
                    "The sprite could not be exported.\n\n{erro}"
                ),
                "export_all_error": (
                    "The export was interrupted after "
                    "{quantidade} sprites.\n\n{erro}"
                ),
                "export_complete_title": "Export complete",
                "export_sprite_success": "Sprite exported successfully!",
                "export_all_success": (
                    "{quantidade} sprites exported successfully!"
                ),                         
            },
            "pt": {
                "abrir": "Abrir OBJECTS*.BIN",
                "salvar": "Salvar",
                "exportar": "Exportar",
                "importar": "Importar",
                "instrucoes": "Instruções",
                "nenhum_arquivo": "Nenhum arquivo aberto",
                "sprites": "Sprites",
                "numero": "#",
                "tamanho": "Tamanho",
                "visualizacao": "Visualização",
                "pronto": "Pronto",
                "import_title": "Importar",
                "import_no_sprite": "Nenhum sprite selecionado.",
                "import_select_png": "Selecione um sprite PNG",
                "png_file": "Imagem PNG",
                "import_success": "Sprite importado com sucesso!",
                "import_memory": (
                    "A alteração está apenas na memória.\n"
                    "Clique em Salvar para gravar no OBJECTS.BIN."
                ),
                "import_pending": "PNG importado — ainda não salvo",      
                "creditos": "Desenvolvido por FQ",       
                "export_title": "Exportar",
                "export_dialog_title": "Exportar Sprites",
                "export_no_file": "Nenhum arquivo foi aberto.",
                "export_question": "O que deseja exportar?",
                "export_selected": "Sprite selecionado",
                "export_all": "Todos os sprites",
                "export_scale": "Escala",
                "export_button": "Exportar",
                "cancel_button": "Cancelar",
                "export_no_sprite": "Nenhum sprite selecionado.",
                "export_select_file": "Exportar sprite",
                "export_select_folder": "Escolha uma pasta para exportar os sprites",
                "png_file": "Imagem PNG",
                "export_error_title": "Erro na exportação",
                "export_sprite_error": (
                    "Não foi possível exportar o sprite.\n\n{erro}"
                ),
                "export_all_error": (
                    "A exportação foi interrompida após "
                    "{quantidade} sprites.\n\n{erro}"
                ),
                "export_complete_title": "Exportação concluída",
                "export_sprite_success": "Sprite exportado com sucesso!",
                "export_all_success": (
                    "{quantidade} sprites exportados com sucesso!"
                ),  
            },
        }        

        pasta_assets = Path(__file__).resolve().parent / "assets"

        self.imagem_flag_us = ImageTk.PhotoImage(
            Image.open(
                pasta_assets / "flag_us.png"
            )
        )

        self.imagem_flag_br = ImageTk.PhotoImage(
            Image.open(
                pasta_assets / "flag_br.png"
            )
        )              

        self.criar_interface()

        self.root.bind(
            "<Control-plus>",
            self.zoom_mais,
        )

        self.root.bind(
            "<Control-minus>",
            self.zoom_menos,
        )

        self.lista_sprites.bind(
            "<<TreeviewSelect>>",
            self.sprite_selecionado,
        )

        self.alteracoes_pendentes = False        

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.fechar_editor,
        )        

    def importar_sprite(self) -> None:

        from PIL import Image

        textos = self.textos[
            self.idioma_atual
        ]

        selecao = self.lista_sprites.selection()

        if not selecao:
            messagebox.showwarning(
                textos["import_title"],
                textos["import_no_sprite"],
            )
            return

        item_selecionado = selecao[0]
        indice_sprite = int(item_selecionado)

        sprite = self.sprites[
            indice_sprite
        ]

        arquivo = filedialog.askopenfilename(
            title=textos["import_select_png"],
            filetypes=[
                (
                    textos["png_file"],
                    "*.png",
                ),
            ],
        )

        if not arquivo:
            return

        try:
            with Image.open(arquivo) as imagem:
                objects.imagem_para_sprite(
                    sprite,
                    imagem,
                )

            self.marcar_alterado()

        except Exception as erro:
            messagebox.showerror(
                textos["import_title"],
                str(erro),
            )
            return

        self.lista_sprites.selection_remove(
            item_selecionado
        )

        self.lista_sprites.selection_set(
            item_selecionado
        )

        self.lista_sprites.focus(
            item_selecionado
        )

        self.lista_sprites.event_generate(
            "<<TreeviewSelect>>"
        )

        self.status_var.set(
            (
                f"{self.arquivo_atual.name} | "
                f"Sprite {sprite.numero:03d} | "
                f"{sprite.largura}x{sprite.altura} | "
                f"{textos['import_pending']}"
            )
        )

        messagebox.showinfo(
            textos["import_title"],
            (
                f"{textos['import_success']}\n\n"
                f"{textos['import_memory']}"
            ),
        )

    def marcar_alterado(self):

        self.alteracoes_pendentes = True

        if self.arquivo_atual:

            self.root.title(
                f"Speed Racer Resource Editor - {self.arquivo_atual.name} *"
            )

        else:

            self.root.title(
                "Speed Racer Resource Editor *"
            )


    def limpar_alterado(self):

        self.alteracoes_pendentes = False

        if self.arquivo_atual:

            self.root.title(
                f"Speed Racer Resource Editor - {self.arquivo_atual.name}"
            )

        else:

            self.root.title(
                "Speed Racer Resource Editor"
            )        

    def fechar_editor(self):

        if not self.alteracoes_pendentes:
            self.root.destroy()
            return

        resposta = messagebox.askyesnocancel(
            "Alterações não salvas",
            (
                "Existem alterações não salvas.\n\n"
                "Deseja salvar antes de sair?"
            ),
        )

        if resposta is None:
            return

        if resposta:

            self.salvar_objects()

            if self.alteracoes_pendentes:
                return

        self.root.destroy()            

    def salvar_backup(self) -> bool:

        destino = self.arquivo_atual.with_suffix(
            self.arquivo_atual.suffix + ".bkp"
        )

        if destino.exists():

            continuar = messagebox.askokcancel(
                "Backup já existe",
                (
                    "Já existe um backup para este arquivo.\n\n"
                    f"{destino}\n\n"
                    "O backup existente NÃO será sobrescrito.\n\n"
                    "Clique em OK para continuar salvando\n"
                    "ou em Cancelar para cancelar a operação."
                ),
            )

            return continuar

        resposta = messagebox.askyesno(
            "Criar backup",
            (
                "Deseja criar um backup antes de salvar?\n\n"
                f"{destino}"
            ),
        )

        if resposta:

            shutil.copy2(
                self.arquivo_atual,
                destino,
            )

            messagebox.showinfo(
                "Backup criado",
                (
                    "Backup criado com sucesso:\n\n"
                    f"{destino}"
                ),
            )

        return True     

    def atualizar_status(
        self,
        texto: str,
    ) -> None:

        self.status_var.set(texto)        

    def zoom_mais(self, event=None) -> None:
        self.renderer.aumentar_zoom()
        self.atualizar_status_editor()


    def zoom_menos(self, event=None) -> None:
        self.renderer.diminuir_zoom()
        self.atualizar_status_editor()       

    def zoom_mouse(self, event) -> None:
        if event.delta > 0:
            self.renderer.aumentar_zoom()
        else:
            self.renderer.diminuir_zoom()

        self.atualizar_status_editor()            
        
    def confirmar_backup(self) -> bool:
        if not hasattr(self, "arquivo_atual"):
            messagebox.showerror(
                "Erro",
                "Nenhum arquivo OBJECTS*.BIN está aberto.",
            )
            return False

        caminho_backup = Path(
            str(self.arquivo_atual) + ".bkp"
        )

        if caminho_backup.exists():
            return True

        criar = messagebox.askyesno(
            "Criar backup",
            (
                "Deseja criar um backup antes de modificar o arquivo?\n\n"
                f"Arquivo:\n{self.arquivo_atual.name}\n\n"
                f"Backup:\n{caminho_backup.name}"
            ),
        )

        if criar:
            try:
                caminho_backup.write_bytes(
                    self.arquivo_atual.read_bytes()
                )

                messagebox.showinfo(
                    "Backup criado",
                    f"Backup criado com sucesso:\n\n{caminho_backup.name}",
                )

            except OSError as erro:
                messagebox.showerror(
                    "Erro ao criar backup",
                    str(erro),
                )
                return False

        return True        
    
    def paleta_click(self, event) -> None:
        tamanho = 16

        coluna = event.x // tamanho
        linha = event.y // tamanho

        indice = linha * 16 + coluna

        if not (0 <= indice < 256):
            return

        self.cor_atual = indice

        self.desenhar_paleta()

        self.atualizar_status_editor()    

    def conta_gotas(self, event) -> None:
        resultado = self.renderer.obter_pixel(
            event.x,
            event.y,
        )

        if resultado is None:
            return

        pixel_x, pixel_y = resultado

        sprite = self.renderer.sprite

        indice = (
            pixel_y * sprite.largura
            + pixel_x
        )

        self.cor_atual = sprite.pixels[indice]

        self.desenhar_paleta()

        self.atualizar_status_editor()  

    def iniciar_desenho(self, event) -> None:
        self.desenhando = True
        self.desenhar_mouse(event)


    def finalizar_desenho(self, event) -> None:
        self.desenhando = False


    def desenhar_mouse(self, event) -> None:
        if not self.desenhando:
            return

        resultado = self.renderer.obter_pixel(
            event.x,
            event.y,
        )

        if resultado is None:
            return

        pixel_x, pixel_y = resultado

        if self.renderer.alterar_pixel(
            pixel_x,
            pixel_y,
            self.cor_atual,
        ):
            self.marcar_alterado()

            self.atualizar_lista_sprites()
            self.atualizar_status_editor() 

    def salvar_objects(self) -> None:
        if self.arquivo_atual is None:
            return

        if not self.salvar_backup():
            return

        objects.salvar_objects(
            self.arquivo_atual,
            self.sprites,
        )

        self.limpar_alterado()        

        for sprite in self.sprites:
            sprite.alterado = False

        self.atualizar_lista_sprites()

        self.atualizar_status(
            f"{self.arquivo_atual.name} salvo com sucesso."
        )    

    def exportar_sprite(self) -> None:

        textos = self.textos[
            self.idioma_atual
        ]

        if not self.sprites:
            messagebox.showwarning(
                textos["export_title"],
                textos["export_no_file"],
            )
            return

        janela = tk.Toplevel(
            self.root
        )

        janela.title(
            textos["export_dialog_title"]
        )

        janela.resizable(
            False,
            False,
        )

        janela.transient(
            self.root
        )

        janela.grab_set()

        modo = tk.StringVar(
            value="selecionado"
        )

        escala = tk.IntVar(
            value=1
        )

        frame = ttk.Frame(
            janela,
            padding=15,
        )

        frame.pack(
            fill="both",
            expand=True,
        )

        ttk.Label(
            frame,
            text=textos["export_question"],
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
        ).pack(
            anchor="w"
        )

        ttk.Radiobutton(
            frame,
            text=textos["export_selected"],
            variable=modo,
            value="selecionado",
        ).pack(
            anchor="w"
        )

        ttk.Radiobutton(
            frame,
            text=textos["export_all"],
            variable=modo,
            value="todos",
        ).pack(
            anchor="w"
        )

        ttk.Separator(
            frame,
            orient="horizontal",
        ).pack(
            fill="x",
            pady=10,
        )

        ttk.Label(
            frame,
            text=textos["export_scale"],
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
        ).pack(
            anchor="w"
        )

        for valor in (
            1,
            2,
            4,
            8,
            16,
        ):
            ttk.Radiobutton(
                frame,
                text=f"{valor}x",
                variable=escala,
                value=valor,
            ).pack(
                anchor="w"
            )

        ttk.Separator(
            frame,
            orient="horizontal",
        ).pack(
            fill="x",
            pady=10,
        )

        botoes = ttk.Frame(
            frame
        )

        botoes.pack(
            fill="x"
        )

        ttk.Button(
            botoes,
            text=textos["cancel_button"],
            command=janela.destroy,
        ).pack(
            side="right"
        )

        ttk.Button(
            botoes,
            text=textos["export_button"],
            command=lambda: self.executar_exportacao(
                janela,
                modo.get(),
                escala.get(),
            ),
        ).pack(
            side="right",
            padx=(0, 5),
        )

        janela.update_idletasks()

        largura = janela.winfo_width()
        altura = janela.winfo_height()

        x = (
            self.root.winfo_x()
            + (
                self.root.winfo_width()
                - largura
            ) // 2
        )

        y = (
            self.root.winfo_y()
            + (
                self.root.winfo_height()
                - altura
            ) // 2
        )

        janela.geometry(
            f"+{x}+{y}"
        )

        janela.focus_set() 

    def executar_exportacao(
        self,
        janela,
        modo: str,
        escala: int,
    ) -> None:

        textos = self.textos[
            self.idioma_atual
        ]

        if modo == "selecionado":

            selecao = (
                self.lista_sprites.selection()
            )

            if not selecao:
                messagebox.showwarning(
                    textos["export_title"],
                    textos["export_no_sprite"],
                    parent=janela,
                )
                return

            indice_sprite = int(
                selecao[0]
            )

            sprite = self.sprites[
                indice_sprite
            ]

            arquivo = (
                filedialog.asksaveasfilename(
                    parent=janela,
                    title=textos[
                        "export_select_file"
                    ],
                    defaultextension=".png",
                    initialfile=(
                        f"sprite_"
                        f"{sprite.numero:03d}_"
                        f"{sprite.largura * escala}x"
                        f"{sprite.altura * escala}_"
                        f"{escala}x.png"
                    ),
                    filetypes=[
                        (
                            textos["png_file"],
                            "*.png",
                        ),
                    ],
                )
            )

            if not arquivo:
                return

            try:
                imagem = (
                    objects.sprite_para_imagem(
                        sprite,
                        escala=escala,
                    )
                )

                imagem.save(
                    arquivo,
                    format="PNG",
                )

            except Exception as erro:
                messagebox.showerror(
                    textos[
                        "export_error_title"
                    ],
                    textos[
                        "export_sprite_error"
                    ].format(
                        erro=erro
                    ),
                    parent=janela,
                )
                return

            messagebox.showinfo(
                textos[
                    "export_complete_title"
                ],
                textos[
                    "export_sprite_success"
                ],
                parent=janela,
            )

        else:

            pasta = filedialog.askdirectory(
                parent=janela,
                title=textos[
                    "export_select_folder"
                ],
            )

            if not pasta:
                return

            pasta_destino = Path(
                pasta
            )

            quantidade = 0

            try:
                for sprite in self.sprites:

                    nome_arquivo = (
                        f"sprite_"
                        f"{sprite.numero:03d}_"
                        f"{sprite.largura * escala}x"
                        f"{sprite.altura * escala}_"
                        f"{escala}x.png"
                    )

                    caminho = (
                        pasta_destino
                        / nome_arquivo
                    )

                    imagem = (
                        objects.sprite_para_imagem(
                            sprite,
                            escala=escala,
                        )
                    )

                    imagem.save(
                        caminho,
                        format="PNG",
                    )

                    quantidade += 1

            except Exception as erro:
                messagebox.showerror(
                    textos[
                        "export_error_title"
                    ],
                    textos[
                        "export_all_error"
                    ].format(
                        quantidade=quantidade,
                        erro=erro,
                    ),
                    parent=janela,
                )
                return

            messagebox.showinfo(
                textos[
                    "export_complete_title"
                ],
                textos[
                    "export_all_success"
                ].format(
                    quantidade=quantidade
                ),
                parent=janela,
            )

        janela.destroy()

    def abrir_instrucoes(self) -> None:

        idioma = self.idioma_atual

        textos_janela = {
            "en": {
                "titulo_janela": (
                    "Instructions — Speed Racer Resource Editor"
                ),
                "titulo": "Speed Racer Resource Editor",
                "subtitulo": (
                    "Sprite and resource editor for OBJECTS*.BIN files"
                ),
                "fechar": "Close",
                "conteudo": """
    ABOUT THE GAME

    Speed Racer in The Challenge of Racer X is a racing game released for MS-DOS computers during the early 1990s.

    Inspired by the classic Speed Racer animated series, the game places the player in fast races involving dangerous tracks, obstacles, rival drivers and special vehicles.

    Its graphics use indexed pixel art, with images stored as numerical references to colors from the game's original palette.

    Many of the game's visual resources are stored inside binary files such as OBJECTS1.BIN, OBJECTS2.BIN and OBJECTS3.BIN.

    The Speed Racer Resource Editor was created to help study, preserve, visualize and modify these resources safely.


    ABOUT THE EDITOR

    The Speed Racer Resource Editor can:

    • Open OBJECTS*.BIN files;
    • Automatically locate compatible sprites;
    • Display sprite information;
    • Preview sprites using the original game palette;
    • Edit individual pixels;
    • Select colors from the palette;
    • Use an eyedropper tool;
    • Import PNG images;
    • Export individual sprites;
    • Export all sprites;
    • Save modified sprites back into the binary file;
    • Create backups before saving;
    • Warn about unsaved changes.


    OPENING A FILE

    1. Click “Open OBJECTS*.BIN”.

    2. Select a compatible file, such as:

    OBJECTS1.BIN
    OBJECTS2.BIN
    OBJECTS3.BIN

    3. After loading, the sprites found inside the file will appear in the list on the left side.

    4. Click a sprite to display it.

    The information panel shows:

    • Sprite number;
    • Offset inside the binary file;
    • Width and height;
    • Block size;
    • Extra bytes;
    • Records that reference the sprite;
    • Associated flags.


    SPRITE LIST

    The left panel contains all sprites detected in the opened file.

    Each entry displays:

    • Sprite number;
    • Sprite dimensions.

    When a sprite is modified, it is internally marked as changed.

    Only modified sprites are written back when the file is saved.


    VIEW AND ZOOM

    Use the mouse wheel over the preview area to increase or decrease the zoom.

    Keyboard shortcuts:

    Ctrl + Plus
    Increase zoom.

    Ctrl + Minus
    Decrease zoom.

    When the image becomes larger than the available area, use the horizontal and vertical scrollbars.

    At higher zoom levels, the editor displays a grid that makes individual pixels easier to identify.


    COLOR PALETTE

    The panel at the bottom displays the game's 256-color palette.

    Click a color using the left mouse button to select it.

    The selected color is highlighted.

    The status bar displays the selected palette index in hexadecimal format.

    Examples:

    Color 0x00
    Color 0x86
    Color 0xFF


    EYEDROPPER

    Click a pixel using the right mouse button to select its color.

    The selected color becomes the current drawing color.

    This is useful when continuing an existing shape or restoring details using colors already present in the sprite.


    DRAWING

    1. Select a color from the palette.

    2. Click a pixel using the left mouse button.

    3. Hold the mouse button and move the cursor to paint multiple pixels.

    When a pixel is changed:

    • The sprite is marked as modified;
    • An asterisk appears in the window title;
    • The change remains only in memory until the file is saved.

    Example:

    Speed Racer Resource Editor - OBJECTS3.BIN *


    IMPORTING A PNG

    The Import button replaces the pixels of the selected sprite with pixels from a PNG image.

    Procedure:

    1. Select the sprite that will be replaced.

    2. Click “Import”.

    3. Select a PNG image.

    4. The PNG must have exactly the same dimensions as the selected sprite.

    Example:

    If the sprite is 73 × 46 pixels, the PNG must also be 73 × 46 pixels.

    Images exported at 2x, 4x, 8x or 16x cannot be imported directly because their dimensions are larger than the original sprite.

    During import, every PNG color is converted to the closest available color in the original game palette.

    Fully transparent pixels are converted to the transparent palette index.

    After importing:

    • The preview is updated immediately;
    • The sprite is marked as modified;
    • The change is not written to the binary file until Save is used.


    RECOMMENDED PNG WORKFLOW

    1. Select a sprite.

    2. Export it at 1x scale.

    3. Open the PNG in a pixel-art editor.

    4. Preserve its original dimensions.

    5. Edit the image without smoothing.

    6. Save it as PNG.

    7. Import it back into the same sprite.

    8. Check the result in the preview.

    9. Save the OBJECTS*.BIN file.

    10. Test the modified file in a separate copy of the game.


    EXPORTING THE SELECTED SPRITE

    1. Select a sprite.

    2. Click “Export”.

    3. Choose “Selected sprite”.

    4. Select the desired scale:

    1x — original resolution;
    2x — twice the original resolution;
    4x — four times the original resolution;
    8x — eight times the original resolution;
    16x — sixteen times the original resolution.

    5. Click “Export”.

    The suggested filename includes:

    • Sprite number;
    • Final resolution;
    • Selected scale.

    Examples:

    sprite_017_73x46_1x.png

    sprite_017_584x368_8x.png


    EXPORTING ALL SPRITES

    1. Click “Export”.

    2. Choose “All sprites”.

    3. Select the scale.

    4. Choose a destination folder.

    Every detected sprite will be exported as an individual PNG file.


    SAVING CHANGES

    Click “Save” to write modified sprites back into the opened OBJECTS*.BIN file.

    Only sprites marked as modified are written.

    Before saving, the editor can create a backup.

    Example backup filename:

    OBJECTS3.BIN.bkp

    An existing backup is not automatically overwritten.


    UNSAVED CHANGES

    When changes are pending, an asterisk appears in the window title.

    When the editor is closed with unsaved changes, three options are displayed:

    Yes
    Save the changes before closing.

    No
    Close without saving.

    Cancel
    Return to the editor without closing.


    LANGUAGE SELECTION

    Use the flag buttons in the upper-right corner to change the interface language.

    United States flag:
    English.

    Brazil flag:
    Portuguese.

    The selected flag remains pressed while the other remains released.

    The default language is English.


    SAFETY RECOMMENDATIONS

    • Keep an untouched copy of the original game files.

    • Do not work directly on your only game installation.

    • Create a backup before saving.

    • Test modified files in a separate copy of the game.

    • Do not change sprite dimensions.

    • Prefer importing PNG files originally exported by this editor.

    • Do not resize pixel art using smoothing filters.

    • When resizing for external use, choose nearest-neighbor scaling.

    • Never replace an original file without keeping a recoverable copy.


    RECOMMENDED IMAGE EDITORS

    Compatible PNG files can be edited using programs such as:

    • Aseprite;
    • LibreSprite;
    • GIMP;
    • Paint.NET;
    • Photoshop;
    • Krita.

    Disable interpolation and smoothing whenever editing or resizing pixel art.


    IMPORTANT NOTE

    This is an independent, unofficial tool created for study, preservation, research and modification of game resources.

    It is not an official product of the game's original developers, publishers or the owners of the Speed Racer franchise.
    """,
            },

            "pt": {
                "titulo_janela": (
                    "Instruções — Speed Racer Resource Editor"
                ),
                "titulo": "Speed Racer Resource Editor",
                "subtitulo": (
                    "Editor de sprites e recursos para arquivos OBJECTS*.BIN"
                ),
                "fechar": "Fechar",
                "conteudo": """
    SOBRE O JOGO

    Speed Racer in The Challenge of Racer X é um jogo de corrida lançado para computadores MS-DOS no início da década de 1990.

    Inspirado na clássica animação Speed Racer, conhecida no Brasil por personagens e veículos como o Mach 5 e o Corredor X, o jogo coloca o jogador em corridas rápidas, com pistas perigosas, obstáculos, adversários e veículos especiais.

    Seus gráficos utilizam pixel art indexada. Cada pixel armazena uma referência numérica para uma cor existente na paleta original do jogo.

    Muitos dos recursos visuais ficam armazenados em arquivos binários como OBJECTS1.BIN, OBJECTS2.BIN e OBJECTS3.BIN.

    O Speed Racer Resource Editor foi criado para ajudar no estudo, preservação, visualização e modificação desses recursos de maneira segura.


    SOBRE O EDITOR

    O Speed Racer Resource Editor permite:

    • Abrir arquivos OBJECTS*.BIN;
    • Localizar automaticamente sprites compatíveis;
    • Exibir informações dos sprites;
    • Visualizar os sprites usando a paleta original;
    • Editar pixels individualmente;
    • Selecionar cores da paleta;
    • Utilizar uma ferramenta conta-gotas;
    • Importar imagens PNG;
    • Exportar um sprite individual;
    • Exportar todos os sprites;
    • Salvar os sprites modificados no arquivo binário;
    • Criar backups antes do salvamento;
    • Avisar sobre alterações não salvas.


    ABRINDO UM ARQUIVO

    1. Clique em “Abrir OBJECTS*.BIN”.

    2. Escolha um arquivo compatível, como:

    OBJECTS1.BIN
    OBJECTS2.BIN
    OBJECTS3.BIN

    3. Depois do carregamento, os sprites encontrados aparecerão na lista localizada no lado esquerdo.

    4. Clique em um sprite para visualizá-lo.

    O painel de informações mostra:

    • Número do sprite;
    • Offset dentro do arquivo binário;
    • Largura e altura;
    • Tamanho do bloco;
    • Bytes extras;
    • Registros que utilizam o sprite;
    • Flags associadas.


    LISTA DE SPRITES

    O painel esquerdo apresenta todos os sprites detectados no arquivo aberto.

    Cada item mostra:

    • Número do sprite;
    • Dimensões do sprite.

    Quando um sprite é modificado, ele fica internamente marcado como alterado.

    Ao salvar, somente os sprites modificados são gravados novamente.


    VISUALIZAÇÃO E ZOOM

    Utilize a roda do mouse sobre a área de visualização para aumentar ou diminuir o zoom.

    Atalhos:

    Ctrl + Mais
    Aumenta o zoom.

    Ctrl + Menos
    Diminui o zoom.

    Quando a imagem fica maior que a área disponível, utilize as barras de rolagem horizontal e vertical.

    Nos níveis maiores de zoom, o editor apresenta uma grade que facilita a identificação de cada pixel.


    PALETA DE CORES

    O painel inferior apresenta as 256 cores da paleta do jogo.

    Clique com o botão esquerdo sobre uma cor para selecioná-la.

    A cor selecionada fica destacada.

    A barra inferior mostra o índice da cor em formato hexadecimal.

    Exemplos:

    Cor 0x00
    Cor 0x86
    Cor 0xFF


    CONTA-GOTAS

    Clique com o botão direito sobre um pixel para selecionar sua cor.

    Essa cor passa a ser a cor atual de desenho.

    A ferramenta é útil para continuar uma forma existente ou recuperar detalhes utilizando cores que já fazem parte do sprite.


    DESENHANDO

    1. Selecione uma cor na paleta.

    2. Clique sobre um pixel usando o botão esquerdo.

    3. Mantenha o botão pressionado e mova o cursor para pintar vários pixels.

    Quando um pixel é alterado:

    • O sprite é marcado como modificado;
    • Um asterisco aparece no título da janela;
    • A alteração permanece somente na memória até que o arquivo seja salvo.

    Exemplo:

    Speed Racer Resource Editor - OBJECTS3.BIN *


    IMPORTANDO UM PNG

    O botão Importar substitui os pixels do sprite selecionado pelos pixels de uma imagem PNG.

    Procedimento:

    1. Selecione o sprite que será substituído.

    2. Clique em “Importar”.

    3. Escolha uma imagem PNG.

    4. O PNG precisa ter exatamente as mesmas dimensões do sprite selecionado.

    Exemplo:

    Se o sprite possui 73 × 46 pixels, o PNG também precisa possuir 73 × 46 pixels.

    Imagens exportadas em 2x, 4x, 8x ou 16x não podem ser importadas diretamente, pois possuem dimensões maiores que o sprite original.

    Durante a importação, cada cor do PNG é convertida para a cor mais próxima disponível na paleta original do jogo.

    Pixels totalmente transparentes são convertidos para o índice transparente da paleta.

    Depois da importação:

    • O preview é atualizado imediatamente;
    • O sprite é marcado como modificado;
    • A alteração ainda não foi gravada no arquivo binário.


    FLUXO RECOMENDADO PARA PNG

    1. Selecione um sprite.

    2. Exporte-o na escala 1x.

    3. Abra o PNG em um editor de pixel art.

    4. Preserve as dimensões originais.

    5. Edite a imagem sem suavização.

    6. Salve novamente como PNG.

    7. Importe o arquivo no mesmo sprite.

    8. Confira o resultado no preview.

    9. Salve o OBJECTS*.BIN.

    10. Teste o arquivo modificado em uma cópia separada do jogo.


    EXPORTANDO O SPRITE SELECIONADO

    1. Selecione um sprite.

    2. Clique em “Exportar”.

    3. Escolha “Sprite selecionado”.

    4. Selecione a escala:

    1x — resolução original;
    2x — dobro da resolução;
    4x — quatro vezes a resolução;
    8x — oito vezes a resolução;
    16x — dezesseis vezes a resolução.

    5. Clique em “Exportar”.

    O nome sugerido inclui:

    • Número do sprite;
    • Resolução final;
    • Escala selecionada.

    Exemplos:

    sprite_017_73x46_1x.png

    sprite_017_584x368_8x.png


    EXPORTANDO TODOS OS SPRITES

    1. Clique em “Exportar”.

    2. Escolha “Todos os sprites”.

    3. Selecione a escala.

    4. Escolha uma pasta de destino.

    Todos os sprites detectados serão exportados individualmente como arquivos PNG.


    SALVANDO ALTERAÇÕES

    Clique em “Salvar” para gravar os sprites modificados no arquivo OBJECTS*.BIN aberto.

    Somente os sprites marcados como modificados são gravados.

    Antes de salvar, o editor pode criar um backup.

    Exemplo:

    OBJECTS3.BIN.bkp

    Um backup existente não é sobrescrito automaticamente.


    ALTERAÇÕES NÃO SALVAS

    Quando existem alterações pendentes, um asterisco aparece no título da janela.

    Ao tentar fechar o editor com alterações não salvas, três opções são apresentadas:

    Sim
    Salva as alterações antes de fechar.

    Não
    Fecha sem salvar.

    Cancelar
    Retorna ao editor sem fechar.


    SELEÇÃO DE IDIOMA

    Utilize os botões com bandeiras no canto superior direito para trocar o idioma da interface.

    Bandeira dos Estados Unidos:
    Inglês.

    Bandeira do Brasil:
    Português.

    A bandeira selecionada permanece pressionada enquanto a outra fica solta.

    O idioma padrão é o inglês.


    RECOMENDAÇÕES DE SEGURANÇA

    • Mantenha uma cópia intacta dos arquivos originais.

    • Não trabalhe diretamente sobre sua única instalação do jogo.

    • Crie um backup antes de salvar.

    • Teste arquivos modificados em uma cópia separada do jogo.

    • Não altere as dimensões dos sprites.

    • Prefira importar PNGs exportados pelo próprio editor.

    • Não redimensione pixel art usando filtros de suavização.

    • Ao redimensionar para uso externo, utilize o método de vizinho mais próximo.

    • Nunca substitua um arquivo original sem manter uma cópia recuperável.


    PROGRAMAS RECOMENDADOS

    Os PNGs podem ser editados em programas como:

    • Aseprite;
    • LibreSprite;
    • GIMP;
    • Paint.NET;
    • Photoshop;
    • Krita.

    Desative interpolação e suavização ao editar ou redimensionar pixel art.


    OBSERVAÇÃO IMPORTANTE

    Esta é uma ferramenta independente e não oficial, criada para estudo, preservação, pesquisa e modificação dos recursos do jogo.

    Ela não é um produto oficial dos desenvolvedores, distribuidores ou proprietários da franquia Speed Racer.
    """,
            },
        }

        dados = textos_janela[idioma]

        janela = tk.Toplevel(self.root)

        janela.title(
            dados["titulo_janela"]
        )

        janela.geometry("820x650")
        janela.minsize(650, 450)
        janela.transient(self.root)
        janela.grab_set()

        frame_principal = ttk.Frame(
            janela,
            padding=15,
        )

        frame_principal.pack(
            fill="both",
            expand=True,
        )

        ttk.Label(
            frame_principal,
            text=dados["titulo"],
            font=("Segoe UI", 16, "bold"),
        ).pack(
            anchor="center",
            pady=(0, 4),
        )

        ttk.Label(
            frame_principal,
            text=dados["subtitulo"],
            font=("Segoe UI", 10),
        ).pack(
            anchor="center",
            pady=(0, 15),
        )

        frame_texto = ttk.Frame(
            frame_principal,
        )

        frame_texto.pack(
            fill="both",
            expand=True,
        )

        barra_vertical = ttk.Scrollbar(
            frame_texto,
            orient="vertical",
        )

        barra_vertical.pack(
            side="right",
            fill="y",
        )

        texto = tk.Text(
            frame_texto,
            wrap="word",
            font=("Segoe UI", 10),
            padx=15,
            pady=15,
            spacing1=2,
            spacing2=2,
            spacing3=8,
            yscrollcommand=barra_vertical.set,
        )

        texto.pack(
            side="left",
            fill="both",
            expand=True,
        )

        barra_vertical.config(
            command=texto.yview,
        )

        texto.insert(
            "1.0",
            dados["conteudo"].strip(),
        )

        texto.config(
            state="disabled",
        )

        frame_botoes = ttk.Frame(
            frame_principal,
        )

        frame_botoes.pack(
            fill="x",
            pady=(12, 0),
        )

        ttk.Button(
            frame_botoes,
            text=dados["fechar"],
            command=janela.destroy,
        ).pack(
            side="right",
        )

        janela.update_idletasks()

        largura = janela.winfo_width()
        altura = janela.winfo_height()

        x = (
            self.root.winfo_x()
            + (
                self.root.winfo_width()
                - largura
            ) // 2
        )

        y = (
            self.root.winfo_y()
            + (
                self.root.winfo_height()
                - altura
            ) // 2
        )

        janela.geometry(
            f"{largura}x{altura}+{x}+{y}"
        )

        janela.focus_set()       

    def alterar_idioma(
        self,
        idioma: str,
    ) -> None:

        if idioma not in (
            "en",
            "pt",
        ):
            return

        self.idioma_atual = idioma
        self.idioma_var.set(idioma)

        self.aplicar_idioma() 

    def aplicar_idioma(self) -> None:

        textos = self.textos[
            self.idioma_atual
        ]

        self.botao_abrir.config(
            text=textos["abrir"],
        )

        self.botao_salvar.config(
            text=textos["salvar"],
        )

        self.botao_exportar.config(
            text=textos["exportar"],
        )

        self.botao_importar.config(
            text=textos["importar"],
        )

        self.botao_instrucoes.config(
            text=textos["instrucoes"],
        )

        self.painel_visualizacao.config(
            text=textos["visualizacao"],
        )

        self.lista_sprites.heading(
            "#0",
            text=textos["numero"],
        )

        self.lista_sprites.heading(
            "tam",
            text=textos["tamanho"],
        )

        quantidade = (
            len(self.sprites)
            if hasattr(self, "sprites")
            else 0
        )

        self.painel_esquerdo.config(
            text=(
                f"{textos['sprites']} "
                f"({quantidade})"
            ),
        )

        if (
            not hasattr(self, "arquivo_atual")
            or self.arquivo_atual is None
        ):
            self.status.config(
                text=textos["nenhum_arquivo"],
            )

        self.label_creditos.config(
            text=textos["creditos"],
        )

        self.status_var.set(
            textos["pronto"]
        )      
            

    def criar_interface(self) -> None:
        barra_superior = ttk.Frame(self.root, padding=10)
        barra_superior.pack(fill="x")

        self.botao_abrir = ttk.Button(
            barra_superior,
            text="Open OBJECTS*.BIN",
            command=self.abrir_objects,
        )

        self.botao_abrir.pack(
            side="left",
        )

        self.botao_salvar = ttk.Button(
            barra_superior,
            text="Salvar",
            command=self.salvar_objects,
            state="disabled",
        )

        self.botao_salvar.pack(
            side="left",
            padx=(5, 0),
        )

        self.botao_exportar = ttk.Button(
            barra_superior,
            text="Exportar",
            command=self.exportar_sprite,
            state="disabled",
        )

        self.botao_exportar.pack(
            side="left",
            padx=(5, 0),
        )

        self.botao_importar = ttk.Button(
            barra_superior,
            text="Importar",
            command=self.importar_sprite,
            state="disabled",
        )

        self.botao_importar.pack(
            side="left",
            padx=(5, 0),
        )

        self.botao_instrucoes = ttk.Button(
            barra_superior,
            text="Instructions",
            command=self.abrir_instrucoes,
        )

        self.botao_instrucoes.pack(
            side="left",
            padx=(5, 0),
        )  

        separador_idioma = ttk.Separator(
            barra_superior,
            orient="vertical",
        )

        separador_idioma.pack(
            side="right",
            fill="y",
            padx=(8, 5),
        )

        self.botao_portugues = ttk.Radiobutton(
            barra_superior,
            image=self.imagem_flag_br,
            variable=self.idioma_var,
            value="pt",
            style="Toolbutton",
            command=lambda: self.alterar_idioma("pt"),
        )

        self.botao_portugues.pack(
            side="right",
            padx=(2, 0),
        )

        self.botao_ingles = ttk.Radiobutton(
            barra_superior,
            image=self.imagem_flag_us,
            variable=self.idioma_var,
            value="en",
            style="Toolbutton",
            command=lambda: self.alterar_idioma("en"),
        )

        self.botao_ingles.pack(
            side="right",
            padx=(2, 0),
        )    

        self.status = ttk.Label(
            barra_superior,
            text="No file opened",
        )
        self.status.pack(side="left", padx=15)

        area_principal = ttk.Frame(
            self.root,
            padding=(10, 0, 10, 10),
        )
        area_principal.pack(
            fill="both",
            expand=True,
        )

        self.painel_esquerdo = ttk.LabelFrame(
            area_principal,
            text="Sprites — 0",
            padding=10,
        )
        self.painel_esquerdo.pack(
            side="left",
            fill="y",
        )

        frame_lista = ttk.Frame(
            self.painel_esquerdo,
        )
        frame_lista.pack(
            fill="both",
            expand=True,
        )

        self.lista_sprites = ttk.Treeview(
            frame_lista,
            columns=("tam",),
            show="tree headings",
            selectmode="browse",
        )

        self.lista_sprites.heading(
            "#0",
            text="#",
        )

        self.lista_sprites.heading(
            "tam",
            text="Tamanho",
        )

        self.lista_sprites.column(
            "#0",
            width=70,
            anchor="center",
        )

        self.lista_sprites.column(
            "tam",
            width=90,
            anchor="center",
        )

        scroll_vertical = ttk.Scrollbar(
            frame_lista,
            orient="vertical",
            command=self.lista_sprites.yview,
        )

        self.lista_sprites.configure(
            yscrollcommand=scroll_vertical.set,
        )

        self.lista_sprites.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scroll_vertical.pack(
            side="right",
            fill="y",
        )

        self.painel_visualizacao = ttk.LabelFrame(
            area_principal,
            text="Visualização",
            padding=10,
        )
        self.painel_visualizacao.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(10, 0),
        )

        frame_canvas = ttk.Frame(
            self.painel_visualizacao,
        )

        frame_canvas.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(10, 5),
        )

        self.canvas = tk.Canvas(
            frame_canvas,
            bg="black",
            highlightthickness=1,
            highlightbackground="#666",
        )

        self.scroll_vertical_canvas = ttk.Scrollbar(
            frame_canvas,
            orient="vertical",
            command=self.canvas.yview,
        )

        self.scroll_horizontal_canvas = ttk.Scrollbar(
            frame_canvas,
            orient="horizontal",
            command=self.canvas.xview,
        )

        self.canvas.configure(
            xscrollcommand=self.scroll_horizontal_canvas.set,
            yscrollcommand=self.scroll_vertical_canvas.set,
        )

        self.canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.scroll_vertical_canvas.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.scroll_horizontal_canvas.grid(
            row=1,
            column=0,
            sticky="ew",
        )

        frame_canvas.rowconfigure(
            0,
            weight=1,
        )

        frame_canvas.columnconfigure(
            0,
            weight=1,
        )

        self.canvas.bind(
            "<MouseWheel>",
            self.zoom_mouse,
        )

        self.canvas.bind(
            "<Motion>",
            self.mouse_move,
        )

        self.renderer = SpriteRenderer(
            self.canvas,
            escala=self.escala,
        )

        self.canvas.bind(
            "<ButtonPress-1>",
            self.iniciar_desenho,
        )

        self.canvas.bind(
            "<B1-Motion>",
            self.desenhar_mouse,
        )

        self.canvas.bind(
            "<ButtonRelease-1>",
            self.finalizar_desenho,
        )

        self.canvas.bind(
            "<Button-3>",
            self.conta_gotas,
        )

        self.info = tk.Text(
            self.painel_visualizacao,
            height=8,
            font=("Consolas", 10),
        )

        self.info.pack(
            fill="x",
            padx=10,
            pady=(0, 10),
        )

        self.paleta = tk.Canvas(
            self.painel_visualizacao,
            height=140,
            bg="#2b2b2b",
            highlightthickness=1,
            highlightbackground="#666",
        )

        self.paleta.pack(
            fill="x",
            padx=10,
            pady=(0, 10),
        )

        self.paleta.bind(
            "<Button-1>",
            self.paleta_click,
        )

        self.status_var = tk.StringVar()

        self.status_var.set(
            self.textos[
                self.idioma_atual
            ]["pronto"]
        )

        barra_status = ttk.Frame(
            self.root,
            relief="sunken",
            borderwidth=1,
        )

        barra_status.pack(
            side="bottom",
            fill="x",
        )

        self.label_status = ttk.Label(
            barra_status,
            textvariable=self.status_var,
            anchor="w",
        )

        self.label_status.pack(
            side="left",
            padx=8,
            pady=4,
        )

        self.label_creditos = ttk.Label(
            barra_status,
            text="Developed by FQ",
            anchor="e",
            foreground="#666666",
        )

        self.label_creditos.pack(
            side="right",
            padx=8,
            pady=4,
        )

        self.desenhar_paleta()

        self.aplicar_idioma()

    def mouse_move(self, event) -> None:
        self.renderer.atualizar_hover(
            event.x,
            event.y,
        )     

    def desenhar_paleta(self) -> None:
        self.paleta.delete("all")

        paleta = objects.carregar_paleta()

        tamanho = 16

        for indice, (r, g, b) in enumerate(paleta):

            coluna = indice % 16
            linha = indice // 16

            x = coluna * tamanho
            y = linha * tamanho

            cor = f"#{r:02X}{g:02X}{b:02X}"

            self.paleta.create_rectangle(
                x,
                y,
                x + tamanho,
                y + tamanho,
                fill=cor,
                outline="#444",
            )       

            if indice == self.cor_atual:

                self.paleta.create_rectangle(
                    x,
                    y,
                    x + tamanho,
                    y + tamanho,
                    outline="white",
                    width=3,
                )

                self.paleta.create_rectangle(
                    x + 1,
                    y + 1,
                    x + tamanho - 1,
                    y + tamanho - 1,
                    outline="black",
                    width=1,
                ) 

    def abrir_objects(self) -> None:
        arquivo = filedialog.askopenfilename(
            title="Abrir OBJECTS*.BIN",
            initialdir=r"C:\dos\Games\SPEED",
            filetypes=[
                ("OBJECTS", "OBJECTS*.BIN"),
                ("BIN", "*.BIN"),
                ("Todos", "*.*"),
            ],
        )

        if not arquivo:
            return

        self.arquivo_atual = Path(arquivo)

        self.sprites_originais = objects.carregar_objects(
            self.arquivo_atual
        )

        self.sprites = copy.deepcopy(
            self.sprites_originais
        )

        self.atualizar_lista_sprites()

        self.atualizar_status_editor()
        

        self.botao_salvar.config(
            state="normal",
        )

        self.botao_exportar.config(
            state="normal",
        )        

        self.botao_importar.config(
            state="normal",
        )        

        self.status.config(
            text=self.arquivo_atual.name
        )        

        self.limpar_alterado()        

    def atualizar_status_editor(self) -> None:

        textos = self.textos[
            self.idioma_atual
        ]

        sprite = self.renderer.sprite

        if sprite is None:
            self.atualizar_status(
                textos["pronto"]
            )
            return

        nome_cor = (
            "Color"
            if self.idioma_atual == "en"
            else "Cor"
        )

        self.atualizar_status(
            (
                f"{self.arquivo_atual.name} | "
                f"Sprite {sprite.numero:03d} | "
                f"{sprite.largura}×{sprite.altura} | "
                f"Zoom {self.renderer.escala}x | "
                f"{nome_cor} 0x{self.cor_atual:02X}"
            )
        )  

    def atualizar_lista_sprites(self) -> None:
        for item in self.lista_sprites.get_children():
            self.lista_sprites.delete(item)

        for sprite in self.sprites:

            status = "●" if sprite.alterado else ""

            self.lista_sprites.insert(
                "",
                "end",
                iid=str(sprite.numero),
                text=f"{sprite.numero:03d}",
                values=(
                    f"{sprite.largura}×{sprite.altura}",
                ),
                tags=(status,),
            )

        self.painel_esquerdo.config(
            text=f"Sprites ({len(self.sprites)})"
        )      

    def carregar_sprite(
        self,
        sprite,
    ) -> None:
        self.renderer.carregar(sprite)

        self.atualizar_status_editor()

        texto = f"""Sprite #{sprite.numero:03d}

    Offset      : 0x{sprite.offset:08X}
    Dimensões   : {sprite.largura} x {sprite.altura}
    Bloco       : {sprite.tamanho_bloco} bytes
    Extras      : {len(sprite.bytes_extras)}
    Registros   : {sprite.registros}
    Flags       : {[hex(x) for x in sprite.flags]}
    """

        self.info.delete("1.0", tk.END)
        self.info.insert(tk.END, texto)        

    def sprite_selecionado(self, event=None) -> None:
        selecao = self.lista_sprites.selection()

        if not selecao:
            return

        indice = int(selecao[0])

        sprite = self.sprites[indice]

        self.carregar_sprite(sprite)