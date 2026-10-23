"""Relatório de carteira em PDF: A4 retrato (spec 006, decisão R21; rascunho 005 da Geração do relatório, FR-049).

Desenha o ``Documento`` montado em ``src.relatorio.carteira``, bloco a bloco e na mesma ordem do Markdown, com a fonte,
as cores, as margens, o estilo das tabelas e o rodapé do resumo executivo. Cada figura fica na página da sua legenda.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List
from xml.sax.saxutils import escape

from reportlab import rl_config
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer

from src.comum.logger import setup_logger
from src.relatorio.pdf import MARGEM_INFERIOR, MARGEM_LATERAL, MARGEM_SUPERIOR, _canvas_numerado, _registrar_fontes
from src.relatorio.resumo_pdf import LARGURA_UTIL, _estilos, _tabela

if TYPE_CHECKING:  # só para as anotações: carteira.py importa este módulo
    from src.relatorio.carteira import Documento

logger = setup_logger("relatorio")

ALTURA_MAXIMA_FIGURA = 330  # pontos; a figura da ordenação cresce com a quantidade de usinas
TABELA_PT = 8.0  # corpo das tabelas da carteira, em pontos


def _figura(caminho: Path, legendas: List[Paragraph]) -> KeepTogether:
    """A figura com o título e a legenda de fonte logo abaixo, na mesma página."""
    largura_px, altura_px = ImageReader(str(caminho)).getSize()
    largura = LARGURA_UTIL
    altura = largura * altura_px / largura_px
    if altura > ALTURA_MAXIMA_FIGURA:
        largura, altura = largura * ALTURA_MAXIMA_FIGURA / altura, ALTURA_MAXIMA_FIGURA
    return KeepTogether([Image(str(caminho), width=largura, height=altura), Spacer(1, 3), *legendas])


def gerar_pdf_carteira(documento: "Documento", figuras: Dict[str, Path], caminho: Path, invariante: bool) -> Path:
    """Grava o PDF; com ``invariante`` (data de geração fixa), sai igual byte a byte."""
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fonte, negrito = _registrar_fontes()
    estilos = _estilos(fonte, negrito)
    for nome in ("cab", "cab_dir", "celula", "celula_dir"):  # tabelas largas e longas: corpo menor que o do resumo
        estilos[nome] = ParagraphStyle(nome, parent=estilos[nome], fontSize=TABELA_PT, leading=TABELA_PT * 1.2)
    p = lambda texto, estilo="corpo": Paragraph(escape(texto), estilos[estilo])  # noqa: E731

    story: List[Any] = [p(documento.titulo, "titulo"), p(documento.subtitulo, "subtitulo")]
    for bloco in documento.blocos:
        if bloco.tipo == "secao":
            story.append(p(bloco.texto, "secao"))
        elif bloco.tipo == "paragrafo":
            story.append(p(bloco.texto))
        elif bloco.tipo == "tabela":
            t = bloco.tabela
            story.append(_tabela(t, [fracao * LARGURA_UTIL for fracao in t.larguras], t.numericas, estilos))
            story.append(p(t.fonte, "aviso"))  # a legenda de fonte logo abaixo da tabela (princípio VII)
            if t.nota:
                story.append(p(t.nota, "aviso"))
            story.append(Spacer(1, 4))
        elif bloco.tipo == "figura":
            story.append(_figura(figuras[bloco.figura], [p(bloco.texto, "aviso"), p(bloco.fonte, "aviso")]))

    doc = SimpleDocTemplate(
        str(destino), pagesize=A4, leftMargin=MARGEM_LATERAL, rightMargin=MARGEM_LATERAL, topMargin=MARGEM_SUPERIOR,
        bottomMargin=MARGEM_INFERIOR, title=documento.titulo, subject=documento.cabecalho_pagina,
        author="Pipeline de análise de usinas (dados ONS)",
    )
    invariante_antes = rl_config.invariant
    if invariante:
        rl_config.invariant = 1
    try:
        doc.build(story, canvasmaker=_canvas_numerado(documento.cabecalho_pagina, fonte))
    finally:
        rl_config.invariant = invariante_antes
    logger.info("Relatório de carteira em PDF gravado: %s (%d bytes)", destino, destino.stat().st_size)
    return destino
