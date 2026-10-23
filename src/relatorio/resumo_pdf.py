"""Resumo executivo em PDF: A4 retrato, sem figuras (spec da Geração do relatório, resumo executivo).

Desenha o ``ResumoExecutivo`` montado em ``src.relatorio.resumo`` com a fonte, as cores, as margens e o rodapé do
relatório completo; o PDF do relatório (``src.relatorio.pdf``) não muda. A regra das duas páginas fica em
``src.relatorio.resumo``, que conta as páginas com ``paginas_do_pdf``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Sequence
from xml.sax.saxutils import escape

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

from src.comum.logger import setup_logger
from src.comum.regras import RESUMO_CORPO_PT, RESUMO_TABELA_PT
from src.relatorio.pdf import (
    AZUL_TITULO,
    FUNDO_CABECALHO,
    FUNDO_ZEBRA,
    LINHA,
    MARGEM_INFERIOR,
    MARGEM_LATERAL,
    MARGEM_SUPERIOR,
    TINTA,
    TINTA_SECUNDARIA,
    _canvas_numerado,
    _registrar_fontes,
)

if TYPE_CHECKING:  # só para as anotações: resumo.py importa este módulo
    from src.relatorio.resumo import ResumoExecutivo, Tabela

logger = setup_logger("relatorio")

LARGURA_UTIL = A4[0] - 2 * MARGEM_LATERAL
ENTRELINHA_CORPO = 13.0
# Fração da largura útil de cada coluna dos indicadores-chave (indicador, valor, detalhe)
LARGURAS_INDICADORES = (0.29, 0.12, 0.59)
FRACAO_COLUNA_ANO = 0.10  # primeira coluna da evolução anual; as demais dividem o resto


def paginas_do_pdf(caminho: Path) -> int:
    """Quantidade de páginas: objetos de página do PDF (o objeto da árvore de páginas é /Pages)."""
    return len(re.findall(rb"/Type\s*/Page(?![a-z])", Path(caminho).read_bytes()))


def _estilos(fonte: str, negrito: str) -> Dict[str, ParagraphStyle]:
    base = dict(fontName=fonte, textColor=TINTA, alignment=TA_LEFT)
    corpo = dict(fontSize=RESUMO_CORPO_PT, leading=ENTRELINHA_CORPO)
    tabela = dict(fontSize=RESUMO_TABELA_PT, leading=RESUMO_TABELA_PT * 1.2)
    return {
        "titulo": ParagraphStyle("titulo", **{**base, "fontName": negrito}, fontSize=15, leading=19, spaceAfter=3),
        "subtitulo": ParagraphStyle("subtitulo", **{**base, "textColor": TINTA_SECUNDARIA}, **corpo, spaceAfter=4),
        "corpo": ParagraphStyle("corpo", **base, **corpo, spaceAfter=3),
        "aviso": ParagraphStyle("aviso", **{**base, "textColor": TINTA_SECUNDARIA}, **corpo, spaceAfter=3),
        "secao": ParagraphStyle("secao", **{**base, "fontName": negrito, "textColor": AZUL_TITULO}, fontSize=12.5,
                                leading=16, spaceBefore=8, spaceAfter=4, keepWithNext=1),
        # título de cada lista da conclusão junto do primeiro item (plano da Geração do relatório, D30)
        "lista": ParagraphStyle("lista", **{**base, "fontName": negrito}, fontSize=RESUMO_CORPO_PT + 0.5,
                                leading=ENTRELINHA_CORPO + 0.5, spaceBefore=4, spaceAfter=2, keepWithNext=1),
        "item": ParagraphStyle("item", **base, **corpo, spaceAfter=2, leftIndent=10, firstLineIndent=-10),
        "cab": ParagraphStyle("cab", **{**base, "fontName": negrito}, **tabela),
        "cab_dir": ParagraphStyle("cab_dir", **{**base, "fontName": negrito, "alignment": TA_RIGHT}, **tabela),
        "celula": ParagraphStyle("celula", **base, **tabela),
        "celula_dir": ParagraphStyle("celula_dir", **{**base, "alignment": TA_RIGHT}, **tabela),
    }


def _tabela(t: "Tabela", larguras: Sequence[float], numericas: Sequence[int], estilos: Dict[str, ParagraphStyle]) -> Table:
    """Tabela no estilo das do relatório completo: cabeçalho com fundo, linhas finas e zebra."""
    dados = [[Paragraph(escape(str(h)), estilos["cab_dir" if i in numericas else "cab"]) for i, h in enumerate(t.cabecalho)]]
    dados += [[Paragraph(escape(str(v)), estilos["celula_dir" if i in numericas else "celula"]) for i, v in enumerate(linha)]
              for linha in t.linhas]
    tabela = Table(dados, colWidths=list(larguras), repeatRows=1, hAlign="LEFT")
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), FUNDO_CABECALHO),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#c3c2b7")),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    estilo += [("BACKGROUND", (0, i), (-1, i), FUNDO_ZEBRA) for i in range(2, len(dados), 2)]
    tabela.setStyle(TableStyle(estilo))
    return tabela


def _larguras_anuais(colunas: int) -> List[float]:
    primeira = FRACAO_COLUNA_ANO * LARGURA_UTIL
    return [primeira] + [(LARGURA_UTIL - primeira) / (colunas - 1)] * (colunas - 1)


def gerar_resumo_pdf(resumo: "ResumoExecutivo", caminho: Path, invariante: bool) -> List[str]:
    """Grava o PDF do resumo e devolve os títulos dos blocos emitidos, na ordem (os mesmos do Markdown).

    Com ``invariante`` (data de geração fixa), o PDF sai igual byte a byte, como o do relatório completo.
    """
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fonte, negrito = _registrar_fontes()
    estilos = _estilos(fonte, negrito)
    p = lambda texto, estilo="corpo": Paragraph(escape(texto), estilos[estilo])  # noqa: E731

    story: List[Any] = [p(resumo.titulo, "titulo"), p(resumo.subtitulo, "subtitulo")]
    story += [p(linha) for linha in resumo.identificacao]
    story.append(p(resumo.referencia_relatorio))
    if resumo.termos:
        story.append(Paragraph(f"<b>Termos.</b> {escape(resumo.texto_termos())}", estilos["corpo"]))
    emitidos: List[str] = []
    for chave, titulo in resumo.blocos():
        emitidos.append(titulo)
        story.append(p(titulo, "secao"))
        if chave == "conclusao":
            story += [p(resumo.aviso_secoes, "aviso"), p(resumo.frase_conclusao)]
            for titulo_lista, itens in resumo.listas_conclusao:
                story.append(p(titulo_lista, "lista"))
                story += [p(f"• {item}", "item") for item in itens]
        elif chave == "indicadores":
            larguras = [fracao * LARGURA_UTIL for fracao in LARGURAS_INDICADORES]
            story += [_tabela(resumo.indicadores, larguras, (1,), estilos), p(resumo.indicadores.nota)]
        elif chave == "evolucao_anual":
            t = resumo.evolucao_anual
            if t is None:
                story.append(p(resumo.remissao_anual))
            else:
                colunas = len(t.cabecalho)
                story += [_tabela(t, _larguras_anuais(colunas), range(1, colunas), estilos), p(t.nota)]
        elif chave == "sobre_os_dados":
            story += [p(paragrafo) for paragrafo in resumo.sobre_os_dados]

    doc = SimpleDocTemplate(
        str(destino), pagesize=A4, leftMargin=MARGEM_LATERAL, rightMargin=MARGEM_LATERAL, topMargin=MARGEM_SUPERIOR,
        bottomMargin=MARGEM_INFERIOR, title=resumo.titulo, subject=resumo.cabecalho_pagina,
        author=f"Pipeline de análise {resumo.nome_usina} (dados ONS)",
    )
    invariante_antes = rl_config.invariant
    if invariante:
        rl_config.invariant = 1
    try:
        doc.build(story, canvasmaker=_canvas_numerado(resumo.cabecalho_pagina, fonte))
    finally:
        rl_config.invariant = invariante_antes
    logger.info("Resumo executivo em PDF gravado: %s (%d bytes)", destino, destino.stat().st_size)
    return emitidos
