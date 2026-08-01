from __future__ import annotations

import csv
import html
import struct
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

PASTA_SAIDA = Path("sprites_objects_todos")

INDICE_PALETA = 3
INDICE_TRANSPARENTE = 0

OFFSET_QUANTIDADE = 0x1A0
OFFSET_REGISTROS = 0x1A4
TAMANHO_REGISTRO = 5

# Aceita blocos com até esta quantidade de bytes sobrando.
MAX_BYTES_EXTRAS = 4

# Evita tratar ponteiros para dentro do cabeçalho/tabela como sprites.
IGNORAR_OFFSETS_ANTES_DA_TABELA = True

# Limites básicos de segurança.
LARGURA_MAXIMA = 320
ALTURA_MAXIMA = 240


# =============================================================================
# MODELOS
# =============================================================================

@dataclass(frozen=True)
class Registro:
    indice: int
    flags: int
    offset: int


@dataclass
class SpriteExtraido:
    numero: int
    offset: int
    fim: int
    largura: int
    altura: int
    tamanho_bloco: int
    tamanho_esperado: int
    bytes_extras: bytes
    registros: list[int]
    flags: list[int]
    bmp: str
    png: str
    pixels: bytes
    alterado: bool = False


# =============================================================================
# LEITURA
# =============================================================================

def u32(dados: bytes, offset: int) -> int:
    return struct.unpack_from("<I", dados, offset)[0]


def rgb6_para_rgb8(valor: int) -> int:
    valor = max(0, min(63, valor))
    return round(valor * 255 / 63)


def carregar_paleta(
    caminho_paleta: Path,
) -> list[tuple[int, int, int]]:

    if not caminho_paleta.exists():
        raise FileNotFoundError(
            f"Paleta não encontrada: {caminho_paleta}"
        )

    dados = caminho_paleta.read_bytes()
    bytes_por_paleta = 256 * 3

    inicio = INDICE_PALETA * bytes_por_paleta
    fim = inicio + bytes_por_paleta

    if fim > len(dados):
        raise ValueError(
            f"Paleta {INDICE_PALETA} não existe em {caminho_paleta}"
        )

    paleta: list[tuple[int, int,int]] = []

    for indice in range(256):
        posicao = inicio + indice * 3

        paleta.append(
            (
                rgb6_para_rgb8(dados[posicao]),
                rgb6_para_rgb8(dados[posicao + 1]),
                rgb6_para_rgb8(dados[posicao + 2]),
            )
        )

    return paleta

def sprite_para_imagem(
    sprite: SpriteExtraido,
    caminho_paleta: Path,
    escala: int = 4,
) -> Image.Image:

    paleta = carregar_paleta(
        caminho_paleta
    )

    rgba = bytearray()

    for indice in sprite.pixels:
        r, g, b = paleta[indice]

        alpha = (
            0
            if indice == INDICE_TRANSPARENTE
            else 255
        )

        rgba.extend(
            (
                r,
                g,
                b,
                alpha,
            )
        )

    imagem = Image.frombytes(
        "RGBA",
        (
            sprite.largura,
            sprite.altura,
        ),
        bytes(rgba),
    )

    if escala > 1:
        imagem = imagem.resize(
            (
                sprite.largura * escala,
                sprite.altura * escala,
            ),
            Image.NEAREST,
        )

    return imagem

def imagem_para_sprite(
    sprite: SpriteExtraido,
    imagem: Image.Image,
    caminho_paleta: Path,
) -> None:

    if imagem.size != (
        sprite.largura,
        sprite.altura,
    ):
        raise ValueError(
            (
                "Resolução incompatível.\n\n"
                f"Sprite: {sprite.largura} x {sprite.altura}\n"
                f"PNG: {imagem.width} x {imagem.height}"
            )
        )

    paleta = carregar_paleta(
        caminho_paleta
    )

    mapa_paleta: dict[
        tuple[int, int, int],
        int,
    ] = {}

    for indice, cor in enumerate(paleta):
        if cor not in mapa_paleta:
            mapa_paleta[cor] = indice

    imagem_rgba = imagem.convert("RGBA")
    novos_pixels = bytearray()

    cache_cores: dict[
        tuple[int, int, int],
        int,
    ] = {}

    for vermelho, verde, azul, alfa in imagem_rgba.getdata():

        if alfa < 128:
            novos_pixels.append(
                INDICE_TRANSPARENTE
            )
            continue

        cor = (
            vermelho,
            verde,
            azul,
        )

        indice = mapa_paleta.get(cor)

        if indice is None:
            indice = cache_cores.get(cor)

        if indice is None:

            menor_distancia = None
            indice_mais_proximo = 0

            for indice_paleta, cor_paleta in enumerate(paleta):

                paleta_r, paleta_g, paleta_b = cor_paleta

                distancia = (
                    (vermelho - paleta_r) ** 2
                    + (verde - paleta_g) ** 2
                    + (azul - paleta_b) ** 2
                )

                if (
                    menor_distancia is None
                    or distancia < menor_distancia
                ):
                    menor_distancia = distancia
                    indice_mais_proximo = indice_paleta

                    if distancia == 0:
                        break

            indice = indice_mais_proximo
            cache_cores[cor] = indice

        novos_pixels.append(indice)

    quantidade_esperada = (
        sprite.largura
        * sprite.altura
    )

    if len(novos_pixels) != quantidade_esperada:
        raise ValueError(
            (
                "Falha ao converter os pixels.\n\n"
                f"Convertidos: {len(novos_pixels)}\n"
                f"Esperados: {quantidade_esperada}"
            )
        )

    sprite.pixels = novos_pixels
    sprite.alterado = True


def ler_registros(dados: bytes) -> tuple[list[Registro], int]:
    if len(dados) < OFFSET_REGISTROS:
        raise ValueError("Arquivo pequeno demais para conter a tabela.")

    quantidade_dword = u32(dados, OFFSET_QUANTIDADE)
    quantidade = quantidade_dword & 0xFF

    fim_tabela = OFFSET_REGISTROS + quantidade * TAMANHO_REGISTRO

    if fim_tabela > len(dados):
        raise ValueError(
            f"Tabela ultrapassa o arquivo: fim 0x{fim_tabela:X}"
        )

    registros: list[Registro] = []

    for indice in range(quantidade):
        endereco = OFFSET_REGISTROS + indice * TAMANHO_REGISTRO

        flags = dados[endereco]
        offset = u32(dados, endereco + 1)

        registros.append(
            Registro(
                indice=indice,
                flags=flags,
                offset=offset,
            )
        )

    return registros, fim_tabela


# =============================================================================
# IMAGENS
# =============================================================================

def salvar_bmp_8bits(
    caminho: Path,
    largura: int,
    altura: int,
    pixels: bytes,
    paleta: list[tuple[int, int, int]],
) -> None:
    if len(pixels) != largura * altura:
        raise ValueError(
            f"{caminho.name}: pixels recebidos={len(pixels)}, "
            f"esperados={largura * altura}"
        )

    stride = (largura + 3) & ~3
    padding = stride - largura

    offset_pixels = 14 + 40 + 256 * 4
    tamanho_imagem = stride * altura
    tamanho_arquivo = offset_pixels + tamanho_imagem

    caminho.parent.mkdir(parents=True, exist_ok=True)

    with caminho.open("wb") as arquivo:
        arquivo.write(b"BM")
        arquivo.write(struct.pack("<I", tamanho_arquivo))
        arquivo.write(struct.pack("<HH", 0, 0))
        arquivo.write(struct.pack("<I", offset_pixels))

        arquivo.write(struct.pack("<I", 40))
        arquivo.write(struct.pack("<i", largura))
        arquivo.write(struct.pack("<i", altura))
        arquivo.write(struct.pack("<H", 1))
        arquivo.write(struct.pack("<H", 8))
        arquivo.write(struct.pack("<I", 0))
        arquivo.write(struct.pack("<I", tamanho_imagem))
        arquivo.write(struct.pack("<i", 2835))
        arquivo.write(struct.pack("<i", 2835))
        arquivo.write(struct.pack("<I", 256))
        arquivo.write(struct.pack("<I", 256))

        for r, g, b in paleta:
            arquivo.write(bytes((b, g, r, 0)))

        for y in range(altura - 1, -1, -1):
            inicio = y * largura
            arquivo.write(pixels[inicio:inicio + largura])

            if padding:
                arquivo.write(b"\x00" * padding)

def salvar_objects(
    arquivo: Path,
    sprites: list[SpriteExtraido],
) -> None:

    with open(arquivo, "rb") as f:
        dados = bytearray(f.read())

    for sprite in sprites:

        if not sprite.alterado:
            continue

        inicio = sprite.offset + 2

        fim = inicio + (
            sprite.largura
            * sprite.altura
        )

        dados[inicio:fim] = sprite.pixels

    with open(arquivo, "wb") as f:
        f.write(dados)                


def salvar_png_transparente(
    caminho: Path,
    largura: int,
    altura: int,
    pixels: bytes,
    paleta: list[tuple[int, int, int]],
) -> bool:
    try:
        from PIL import Image
    except ImportError:
        return False

    rgba = bytearray()

    for indice in pixels:
        r, g, b = paleta[indice]
        alpha = 0 if indice == INDICE_TRANSPARENTE else 255
        rgba.extend((r, g, b, alpha))

    imagem = Image.frombytes(
        "RGBA",
        (largura, altura),
        bytes(rgba),
    )

    imagem.save(caminho)
    return True


# =============================================================================
# EXTRAÇÃO
# =============================================================================

def validar_dimensoes(
    largura: int,
    altura: int,
) -> bool:
    return (
        1 <= largura <= LARGURA_MAXIMA
        and 1 <= altura <= ALTURA_MAXIMA
    )


def extrair_arquivo(
    caminho_objects: Path,
    paleta: list[tuple[int, int, int]],
) -> dict[str, object]:
    dados = caminho_objects.read_bytes()
    registros, fim_tabela = ler_registros(dados)

    registros_por_offset: dict[int, list[Registro]] = defaultdict(list)

    for registro in registros:
        if not 0 < registro.offset < len(dados):
            continue

        if (
            IGNORAR_OFFSETS_ANTES_DA_TABELA
            and registro.offset < fim_tabela
        ):
            continue

        registros_por_offset[registro.offset].append(registro)

    offsets = sorted(registros_por_offset)

    pasta_arquivo = PASTA_SAIDA / caminho_objects.stem
    pasta_arquivo.mkdir(parents=True, exist_ok=True)

    sprites: list[SpriteExtraido] = []
    rejeitados: list[list[object]] = []

    print()
    print("-" * 100)
    print(caminho_objects.name)
    print("-" * 100)
    print(f"Tamanho              : {len(dados):,} bytes")
    print(f"Registros            : {len(registros)}")
    print(f"Fim da tabela        : 0x{fim_tabela:08X}")
    print(f"Offsets candidatos   : {len(offsets)}")
    print()

    for numero, offset in enumerate(offsets):
        fim = (
            offsets[numero + 1]
            if numero + 1 < len(offsets)
            else len(dados)
        )

        bloco = dados[offset:fim]

        if len(bloco) < 2:
            rejeitados.append(
                [
                    numero,
                    f"0x{offset:08X}",
                    f"0x{fim:08X}",
                    len(bloco),
                    "bloco menor que 2 bytes",
                ]
            )
            continue

        largura = bloco[0]
        altura = bloco[1]

        if not validar_dimensoes(largura, altura):
            rejeitados.append(
                [
                    numero,
                    f"0x{offset:08X}",
                    f"0x{fim:08X}",
                    len(bloco),
                    f"dimensões inválidas: {largura}x{altura}",
                ]
            )
            continue

        pixels_esperados = largura * altura
        tamanho_esperado = 2 + pixels_esperados
        sobra = len(bloco) - tamanho_esperado

        if not 0 <= sobra <= MAX_BYTES_EXTRAS:
            rejeitados.append(
                [
                    numero,
                    f"0x{offset:08X}",
                    f"0x{fim:08X}",
                    len(bloco),
                    (
                        f"header={largura}x{altura}; "
                        f"esperado={tamanho_esperado}; "
                        f"sobra={sobra}"
                    ),
                ]
            )

            print(
                f"[--] 0x{offset:08X} | "
                f"{largura:3d}x{altura:3d} | "
                f"bloco={len(bloco):5d} | "
                f"esperado={tamanho_esperado:5d} | "
                f"sobra={sobra}"
            )
            continue

        pixels = bloco[2:2 + pixels_esperados]
        extras = bloco[2 + pixels_esperados:]

        registros_usando = registros_por_offset[offset]
        indices = sorted(registro.indice for registro in registros_usando)
        flags = sorted({registro.flags for registro in registros_usando})

        nome_base = (
            f"sprite_{len(sprites):03d}_"
            f"off_{offset:08X}_"
            f"{largura}x{altura}"
        )

        caminho_bmp = pasta_arquivo / f"{nome_base}.bmp"
        caminho_png = pasta_arquivo / f"{nome_base}.png"

        salvar_bmp_8bits(
            caminho_bmp,
            largura,
            altura,
            pixels,
            paleta,
        )

        png_criado = salvar_png_transparente(
            caminho_png,
            largura,
            altura,
            pixels,
            paleta,
        )

        if extras:
            caminho_extras = pasta_arquivo / f"{nome_base}_extras.bin"
            caminho_extras.write_bytes(extras)

        sprite = SpriteExtraido(
            numero=len(sprites),
            offset=offset,
            fim=fim,
            largura=largura,
            altura=altura,
            tamanho_bloco=len(bloco),
            tamanho_esperado=tamanho_esperado,
            bytes_extras=extras,
            registros=indices,
            flags=flags,
            bmp=caminho_bmp.name,
            png=caminho_png.name if png_criado else "",
        )

        sprites.append(sprite)

        marcador = "OK+" if extras else "OK "

        print(
            f"[{marcador}] 0x{offset:08X} | "
            f"{largura:3d}x{altura:3d} | "
            f"{len(bloco):5d} bytes | "
            f"extras={len(extras)}"
        )

    gerar_csv_arquivo(
        pasta_arquivo,
        sprites,
        rejeitados,
    )

    gerar_html_arquivo(
        caminho_objects,
        pasta_arquivo,
        sprites,
        fim_tabela,
        len(registros),
    )

    return {
        "arquivo": caminho_objects.name,
        "tamanho": len(dados),
        "registros": len(registros),
        "fim_tabela": fim_tabela,
        "offsets": len(offsets),
        "sprites": len(sprites),
        "rejeitados": len(rejeitados),
        "pasta": pasta_arquivo,
    }


# =============================================================================
# RELATÓRIOS
# =============================================================================

def gerar_csv_arquivo(
    pasta: Path,
    sprites: list[SpriteExtraido],
    rejeitados: list[list[object]],
) -> None:
    with (
        pasta / "sprites.csv"
    ).open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as arquivo:
        writer = csv.writer(arquivo, delimiter=";")

        writer.writerow(
            [
                "Número",
                "Offset",
                "Fim",
                "Largura",
                "Altura",
                "Tamanho do bloco",
                "Tamanho esperado",
                "Bytes extras",
                "Registros",
                "Flags",
                "BMP",
                "PNG",
            ]
        )

        for sprite in sprites:
            writer.writerow(
                [
                    sprite.numero,
                    f"0x{sprite.offset:08X}",
                    f"0x{sprite.fim:08X}",
                    sprite.largura,
                    sprite.altura,
                    sprite.tamanho_bloco,
                    sprite.tamanho_esperado,
                    len(sprite.bytes_extras),
                    ", ".join(str(x) for x in sprite.registros),
                    ", ".join(f"0x{x:02X}" for x in sprite.flags),
                    sprite.bmp,
                    sprite.png,
                ]
            )

    with (
        pasta / "rejeitados.csv"
    ).open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as arquivo:
        writer = csv.writer(arquivo, delimiter=";")

        writer.writerow(
            [
                "Número",
                "Offset",
                "Fim",
                "Tamanho",
                "Motivo",
            ]
        )

        writer.writerows(rejeitados)


def gerar_html_arquivo(
    caminho_objects: Path,
    pasta: Path,
    sprites: list[SpriteExtraido],
    fim_tabela: int,
    quantidade_registros: int,
) -> None:
    partes: list[str] = []

    partes.append(
        """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Sprites extraídos</title>
<style>
body {
    background: #111;
    color: #eee;
    font-family: Segoe UI, Arial, sans-serif;
    margin: 24px;
}
.grade {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
}
.card {
    background: #222;
    border: 1px solid #555;
    padding: 10px;
    max-width: 360px;
}
.card img {
    image-rendering: pixelated;
    image-rendering: crisp-edges;
    max-width: 320px;
    max-height: 240px;
    background: repeating-conic-gradient(#777 0% 25%, #444 0% 50%) 50% / 16px 16px;
}
.meta {
    margin-top: 8px;
    font-family: Consolas, monospace;
    font-size: 12px;
    white-space: pre-wrap;
}
</style>
</head>
<body>
"""
    )

    partes.append(
        f"<h1>{html.escape(caminho_objects.name)}</h1>"
    )

    partes.append(
        f"<p>Registros: {quantidade_registros} | "
        f"Fim da tabela: 0x{fim_tabela:08X} | "
        f"Sprites extraídos: {len(sprites)}</p>"
    )

    partes.append('<div class="grade">')

    for sprite in sprites:
        imagem = sprite.png or sprite.bmp

        meta = (
            f"#{sprite.numero:03d}\n"
            f"offset: 0x{sprite.offset:08X}\n"
            f"dimensões: {sprite.largura}×{sprite.altura}\n"
            f"bloco: {sprite.tamanho_bloco} bytes\n"
            f"extras: {len(sprite.bytes_extras)}\n"
            f"registros: {sprite.registros}\n"
            f"flags: {[f'0x{x:02X}' for x in sprite.flags]}"
        )

        partes.append('<div class="card">')
        partes.append(
            f'<a href="{html.escape(imagem)}">'
            f'<img src="{html.escape(imagem)}"></a>'
        )
        partes.append(
            f'<div class="meta">{html.escape(meta)}</div>'
        )
        partes.append("</div>")

    partes.append("</div>")
    partes.append("</body></html>")

    (
        pasta / "00_CATALOGO.html"
    ).write_text(
        "\n".join(partes),
        encoding="utf-8",
    )


def gerar_resumo_geral(
    resultados: list[dict[str, object]],
) -> None:
    linhas_csv: list[list[object]] = []

    total_sprites = 0
    total_rejeitados = 0

    for resultado in resultados:
        total_sprites += int(resultado["sprites"])
        total_rejeitados += int(resultado["rejeitados"])

        linhas_csv.append(
            [
                resultado["arquivo"],
                resultado["tamanho"],
                resultado["registros"],
                f"0x{int(resultado['fim_tabela']):08X}",
                resultado["offsets"],
                resultado["sprites"],
                resultado["rejeitados"],
                str(resultado["pasta"]),
            ]
        )

    with (
        PASTA_SAIDA / "00_RESUMO_GERAL.csv"
    ).open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as arquivo:
        writer = csv.writer(arquivo, delimiter=";")

        writer.writerow(
            [
                "Arquivo",
                "Tamanho",
                "Registros",
                "Fim da tabela",
                "Offsets candidatos",
                "Sprites extraídos",
                "Rejeitados",
                "Pasta",
            ]
        )

        writer.writerows(linhas_csv)

    linhas_txt = [
        "=" * 100,
        "EXTRAÇÃO GERAL DOS OBJECTS*.BIN",
        "=" * 100,
        "",
        "Pasta do jogo       : definida pelo arquivo selecionado",
        "Paleta              : ROADPAL.BIN da pasta do arquivo selecionado",
        f"Paleta usada        : {INDICE_PALETA}",
        f"Arquivos processados: {len(resultados)}",
        f"Sprites extraídos   : {total_sprites}",
        f"Blocos rejeitados   : {total_rejeitados}",
        "",
        "RESULTADOS",
        "-" * 100,
    ]

    for resultado in resultados:
        linhas_txt.append(
            f"{str(resultado['arquivo']):<16} "
            f"sprites={int(resultado['sprites']):4d} | "
            f"rejeitados={int(resultado['rejeitados']):4d} | "
            f"registros={int(resultado['registros']):4d}"
        )

    linhas_txt.extend(
        [
            "",
            "Cada subpasta contém:",
            "- imagens BMP;",
            "- PNG transparente, se Pillow estiver instalado;",
            "- sprites.csv;",
            "- rejeitados.csv;",
            "- 00_CATALOGO.html.",
        ]
    )

    (
        PASTA_SAIDA / "00_RESUMO_GERAL.txt"
    ).write_text(
        "\n".join(linhas_txt),
        encoding="utf-8",
    )

def carregar_objects(caminho_objects: Path) -> list[SpriteExtraido]:
    dados = caminho_objects.read_bytes()
    registros, fim_tabela = ler_registros(dados)

    registros_por_offset: dict[int, list[Registro]] = defaultdict(list)

    for registro in registros:
        if not 0 < registro.offset < len(dados):
            continue

        if (
            IGNORAR_OFFSETS_ANTES_DA_TABELA
            and registro.offset < fim_tabela
        ):
            continue

        registros_por_offset[registro.offset].append(registro)

    offsets = sorted(registros_por_offset)
    sprites: list[SpriteExtraido] = []

    for offset in offsets:
        numero_offset = offsets.index(offset)

        fim = (
            offsets[numero_offset + 1]
            if numero_offset + 1 < len(offsets)
            else len(dados)
        )

        bloco = dados[offset:fim]

        if len(bloco) < 2:
            continue

        largura = bloco[0]
        altura = bloco[1]

        if not validar_dimensoes(largura, altura):
            continue

        pixels_esperados = largura * altura
        tamanho_esperado = 2 + pixels_esperados
        sobra = len(bloco) - tamanho_esperado

        if not 0 <= sobra <= MAX_BYTES_EXTRAS:
            continue
        pixels = bytearray(
            bloco[2:2 + pixels_esperados]
        )
        extras = bloco[2 + pixels_esperados:]

        registros_usando = registros_por_offset[offset]
        indices = sorted(
            registro.indice
            for registro in registros_usando
        )
        flags = sorted(
            {
                registro.flags
                for registro in registros_usando
            }
        )

        sprites.append(
            SpriteExtraido(
                numero=len(sprites),
                offset=offset,
                fim=fim,
                largura=largura,
                altura=altura,
                tamanho_bloco=len(bloco),
                tamanho_esperado=tamanho_esperado,
                bytes_extras=extras,
                registros=indices,
                flags=flags,
                bmp="",
                png="",
                pixels=pixels,
            )
        )

    return sprites




