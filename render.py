from __future__ import annotations

import tkinter as tk

from PIL import ImageTk

import objects


class SpriteRenderer:
    def __init__(
        self,
        canvas: tk.Canvas,
        escala: int = 4,
    ) -> None:

        self.canvas = canvas

        self.escala_padrao = escala
        self.escala = escala

        self.sprite = None

        self.tk_imagem = None

        self.inicio_x = 0
        self.inicio_y = 0

        self.hover_x = -1
        self.hover_y = -1

        self.mostrar_grade = True

    def alterar_pixel(
        self,
        x: int,
        y: int,
        cor: int,
    ) -> bool:

        if self.sprite is None:
            return False

        indice = (
            y * self.sprite.largura
            + x
        )

        if self.sprite.pixels[indice] == cor:
            return False

        self.sprite.pixels[indice] = cor
        self.sprite.alterado = True

        self.redesenhar()

        return True                      

    def carregar(
        self,
        sprite: objects.SpriteExtraido,
    ) -> None:

        self.sprite = sprite

        self.restaurar_zoom()

        self.redesenhar()  

    def restaurar_zoom(self) -> None:
        self.escala = self.escala_padrao        

    def aumentar_zoom(self) -> None:
        if self.escala < 32:
            self.escala *= 2
            self.redesenhar()

    def definir_zoom(
        self,
        escala: int,
    ) -> None:

        self.escala = max(
            1,
            min(32, escala),
        )

        self.redesenhar()

    def diminuir_zoom(self) -> None:
        if self.escala > 1:
            self.escala //= 2
            self.redesenhar()                

    def renderizar_sprite(self) -> None:
        if self.sprite is None:
            return

        sprite = self.sprite

        imagem = objects.sprite_para_imagem(
            sprite,
            escala=self.escala,
        )

        self.tk_imagem = ImageTk.PhotoImage(imagem)

        self.canvas.delete("sprite")

        largura_canvas = self.canvas.winfo_width()
        altura_canvas = self.canvas.winfo_height()

        largura_imagem = sprite.largura * self.escala
        altura_imagem = sprite.altura * self.escala

        largura_area = max(
            largura_canvas,
            largura_imagem,
        )

        altura_area = max(
            altura_canvas,
            altura_imagem,
        )

        self.inicio_x = (
            largura_area - largura_imagem
        ) // 2

        self.inicio_y = (
            altura_area - altura_imagem
        ) // 2

        self.canvas.configure(
            scrollregion=(
                0,
                0,
                largura_area,
                altura_area,
            )
        )

        self.canvas.create_image(
            self.inicio_x,
            self.inicio_y,
            image=self.tk_imagem,
            anchor="nw",
            tags=("sprite",),
        )


    def renderizar_overlay(self) -> None:
        self.canvas.delete("overlay")

        if self.sprite is None:
            return

        if self.hover_x < 0 or self.hover_y < 0:
            return

        x = self.inicio_x + (
            self.hover_x * self.escala
        )

        y = self.inicio_y + (
            self.hover_y * self.escala
        )

        if (
            self.mostrar_grade
            and self.escala >= 8
            and self.sprite is not None
        ):

            largura = self.sprite.largura * self.escala
            altura = self.sprite.altura * self.escala

            for coluna in range(self.sprite.largura + 1):

                xx = self.inicio_x + (coluna * self.escala)

                self.canvas.create_line(
                    xx,
                    self.inicio_y,
                    xx,
                    self.inicio_y + altura,
                    fill="#555",
                    tags=("overlay",),
                )

            for linha in range(self.sprite.altura + 1):

                yy = self.inicio_y + (linha * self.escala)

                self.canvas.create_line(
                    self.inicio_x,
                    yy,
                    self.inicio_x + largura,
                    yy,
                    fill="#555",
                    tags=("overlay",),
                )        

        self.canvas.create_rectangle(
            x,
            y,
            x + self.escala,
            y + self.escala,
            outline="yellow",
            width=2,
            tags=("overlay",),
        )


    def redesenhar(self) -> None:
        self.renderizar_sprite()
        self.renderizar_overlay()      

    def obter_pixel(
        self,
        x_canvas: int,
        y_canvas: int,
    ) -> tuple[int, int] | None:

        if self.sprite is None:
            return None

        pixel_x = (
            x_canvas - self.inicio_x
        ) // self.escala

        pixel_y = (
            y_canvas - self.inicio_y
        ) // self.escala

        if not (
            0 <= pixel_x < self.sprite.largura
            and 0 <= pixel_y < self.sprite.altura
        ):
            return None

        return (
            pixel_x,
            pixel_y,
        )
    
    def atualizar_hover(
        self,
        x_canvas: int,
        y_canvas: int,
    ) -> None:

        resultado = self.obter_pixel(
            x_canvas,
            y_canvas,
        )

        if resultado is None:

            if self.hover_x != -1 or self.hover_y != -1:

                self.hover_x = -1
                self.hover_y = -1

                self.renderizar_overlay()

            return

        pixel_x, pixel_y = resultado

        if (
            pixel_x == self.hover_x
            and pixel_y == self.hover_y
        ):
            return

        self.hover_x = pixel_x
        self.hover_y = pixel_y

        self.renderizar_overlay()  