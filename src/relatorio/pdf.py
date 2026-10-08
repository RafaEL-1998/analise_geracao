"""Geração do relatório em PDF (A4 paisagem) a partir dos resultados das Análises.

O PDF não contém números nem conclusões fixos: textos, tabelas e legendas das figuras
são montados a partir de ``ResultadosAnalise``. A ordem das seções e o lugar de cada constatação
vêm da estrutura do relatório (``src.relatorio.estrutura``), a mesma do Markdown.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from xml.sax.saxutils import escape

import matplotlib
from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    CondPageBreak,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from src.analises.conclusao import FRASE_ABERTURA_CONCLUSAO, FRASE_CONCLUSAO_VAZIA
from src.analises.constatacoes import texto_conferencia_geracao
from src.analises.resultados import ResultadosAnalise
from src.comum.formatacao import fmt_data, fmt_data_hora, fmt_int, fmt_lista, fmt_utc
from src.comum.logger import setup_logger
from src.comum.perfil import perfil_ativo
from src.relatorio.conteudo import (
    indicadores_capa,
    legenda_figura,
    linhas_tabela_anual,
    linhas_tabela_disponibilidade_anual,
    linhas_tabela_disponibilidade_divergencias,
    linhas_tabela_disponibilidade_paradas,
    linhas_tabela_eventos_indisponibilidade,
    linhas_tabela_eventos_parada,
    linhas_tabela_evt_por_nivel,
    linhas_tabela_extremos,
    linhas_tabela_faixas_afluencia,
    linhas_tabela_faixas_afluencia_evt,
    linhas_tabela_geracao_anual,
    linhas_tabela_geracao_zero,
    linhas_tabela_hidrologia_anual,
    linhas_tabela_ons_decomposicao,
    linhas_tabela_ons_disponibilidade,
    linhas_tabela_ons_divergencias,
    linhas_tabela_ons_horas,
    linhas_tabela_ons_ug_anual,
    linhas_tabela_parametros,
    linhas_tabela_perfil_diurno,
    linhas_tabela_perfil_hidrologico,
    linhas_tabela_programacao_eventos,
    linhas_tabela_programacao_mensal,
    linhas_tabela_programacao_perfil,
    linhas_tabela_registros_sinalizados,
    linhas_tabela_regras,
    listas_conclusao,
    notas_disponibilidade,
    notas_hidrologia,
    notas_metodologicas,
    pares_cobertura,
    pares_identificacao,
    pares_identificacao_cadastro,
    pares_parametros,
    texto_taxas_ons,
    textos_tabelas,
)
from src.relatorio.estrutura import constatacoes_da_secao, secoes_presentes, sumario
from src.relatorio.figuras import NOMES_FIGURAS
from src.relatorio.fontes import legenda_fonte
from src.tratamento.indicadores import INSUMOS_HORAS

logger = setup_logger("relatorio")


TINTA = colors.HexColor("#0b0b0b")
TINTA_SECUNDARIA = colors.HexColor("#52514e")
TINTA_SUAVE = colors.HexColor("#898781")
AZUL_TITULO = colors.HexColor("#184f95")
LINHA = colors.HexColor("#e1e0d9")
FUNDO_CABECALHO = colors.HexColor("#f0efec")
FUNDO_ZEBRA = colors.HexColor("#fafaf8")

MARGEM_LATERAL = 36
MARGEM_SUPERIOR = 50
MARGEM_INFERIOR = 42
LARGURA_UTIL = landscape(A4)[0] - 2 * MARGEM_LATERAL
ALTURA_QUADRO = landscape(A4)[1] - MARGEM_SUPERIOR - MARGEM_INFERIOR - 12
# Paginação: a figura cabe na página com o título e as constatações da seção; a tabela longa pode
# continuar na página seguinte, com o cabeçalho repetido, se o subtítulo e as primeiras linhas couberem.
ALTURA_MAXIMA_FIGURA = 285
# Figuras padronizadas (FR-036): mesma proporção do PNG e largura útil, fora do limite de altura
FIGURAS_PADRONIZADAS = ("serie_temporal", "evt_mensal", "disponibilidade_sincronizada", "vazoes_defluentes")
LINHAS_TABELA_INTEIRA = 12
LINHAS_MINIMAS_NA_PAGINA = 6
ALTURA_ABERTURA_CURTA = 150
# Capa com a ficha do cadastro (FR-012): fração da largura e coluna das chaves de cada bloco, para caber numa página
BLOCOS_CAPA_TRES = {"bloco_identificacao": (0.26, 62), "bloco_cadastro": (0.38, 112), "bloco_parametros": (0.36, 88)}


def _registrar_fontes() -> Tuple[str, str]:
    """Registra Arial (Windows) ou DejaVu Sans (distribuída com o matplotlib)."""
    pasta_windows = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    pasta_mpl = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    candidatos = [
        ("Arial", [pasta_windows / f for f in ("arial.ttf", "arialbd.ttf", "ariali.ttf", "arialbi.ttf")]),
        ("DejaVuSans", [pasta_mpl / f for f in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf",
                                                  "DejaVuSans-Oblique.ttf", "DejaVuSans-BoldOblique.ttf")]),
    ]
    for nome, arquivos in candidatos:
        if all(a.exists() for a in arquivos):
            variantes = [nome, f"{nome}-Bold", f"{nome}-Italic", f"{nome}-BoldItalic"]
            for variante, arquivo in zip(variantes, arquivos):
                if variante not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(variante, str(arquivo)))
            pdfmetrics.registerFontFamily(nome, normal=variantes[0], bold=variantes[1],
                                          italic=variantes[2], boldItalic=variantes[3])
            return nome, variantes[1]
    logger.warning("Fontes TrueType não encontradas; usando Helvetica (sem suporte a ≤, ≥ e −).")
    return "Helvetica", "Helvetica-Bold"


def _canvas_numerado(cabecalho: str, fonte: str):
    """Canvas de dois passos: cabeçalho (a partir da página 2) e 'Página X de Y' no rodapé (spec da Geração do relatório, FR-015)."""

    class CanvasNumerado(canvas.Canvas):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._estados: List[dict] = []

        def showPage(self) -> None:
            self._estados.append(dict(self.__dict__))
            self._startPage()

        def save(self) -> None:
            total = len(self._estados)
            for estado in self._estados:
                self.__dict__.update(estado)
                self._decorar(total)
                super().showPage()
            super().save()

        def _decorar(self, total: int) -> None:
            largura, altura = self._pagesize
            self.saveState()
            self.setFont(fonte, 7.5)
            self.setFillColor(TINTA_SECUNDARIA)
            self.setStrokeColor(LINHA)
            self.setLineWidth(0.6)
            if self._pageNumber > 1:
                self.drawString(MARGEM_LATERAL, altura - 30, cabecalho)
                self.line(MARGEM_LATERAL, altura - 36, largura - MARGEM_LATERAL, altura - 36)
            self.line(MARGEM_LATERAL, 30, largura - MARGEM_LATERAL, 30)
            self.drawRightString(largura - MARGEM_LATERAL, 19, f"Página {self._pageNumber} de {total}")
            self.restoreState()

    return CanvasNumerado


def _fmt_utc(valor: str) -> str:
    """Formata o last_modified do CKAN como '30/09/2026 15:05 UTC' (ver ``formatacao.fmt_utc``)."""
    return fmt_utc(valor)


def _altura(flowables: Sequence[Any]) -> float:
    """Altura ocupada por flowables na largura útil, com os espaços antes e depois."""
    return sum(f.wrap(LARGURA_UTIL - 12, ALTURA_QUADRO)[1] + f.getSpaceBefore() + f.getSpaceAfter() for f in flowables)


class _DocumentoComSumario(SimpleDocTemplate):
    """Documento que registra a página de cada título de seção e alimenta o sumário."""

    def __init__(self, *args: Any, gerador: "PDFReportGenerator", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._gerador = gerador

    def afterFlowable(self, flowable: Any) -> None:
        if isinstance(flowable, Paragraph) and flowable.style.name == "secao":
            texto = flowable.getPlainText()
            self._gerador.paginas_secoes[texto.partition(". ")[2]] = self.page
            self.notify("TOCEntry", (0, texto, self.page))


class _SumarioDuasColunas(TableOfContents):
    """Sumário da capa em duas colunas, com o título numerado e a página de cada seção (spec da Geração do relatório, FR-011)."""

    def __init__(self, previstos: Sequence[str], estilo: ParagraphStyle, estilo_pagina: ParagraphStyle) -> None:
        super().__init__()
        self._previstos = [(0, texto, 0, None) for texto in previstos]
        self._estilo, self._estilo_pagina = estilo, estilo_pagina

    def wrap(self, availWidth: float, availHeight: float) -> Tuple[float, float]:
        # Na primeira passagem as páginas ainda não são conhecidas; as entradas previstas mantêm a mesma altura.
        entradas = [(e[1], e[2]) for e in (self._lastEntries or self._previstos)]
        metade = (len(entradas) + 1) // 2
        colunas = (entradas[:metade], entradas[metade:])
        dados: List[List[Any]] = []
        for i in range(metade):
            linha: List[Any] = []
            for coluna in colunas:
                if i < len(coluna):
                    texto, pagina = coluna[i]
                    linha += [Paragraph(escape(texto), self._estilo),
                              Paragraph(str(pagina) if pagina else "", self._estilo_pagina)]
                else:
                    linha += ["", ""]
                linha.append("")
            dados.append(linha[:-1])
        largura = (availWidth - 30) / 2
        estilo = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 0.4),
                  ("BOTTOMPADDING", (0, 0), (-1, -1), 0.4), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                  ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("LINEBELOW", (0, 0), (1, -1), 0.3, LINHA),
                  # células vazias (espaço entre as colunas) não podem ditar a altura da linha
                  ("FONTSIZE", (0, 0), (-1, -1), 4), ("LEADING", (0, 0), (-1, -1), 4)]
        if colunas[1]:
            estilo.append(("LINEBELOW", (3, 0), (4, len(colunas[1]) - 1), 0.3, LINHA))
        self._table = Table(dados, colWidths=[largura - 28, 28, 30, largura - 28, 28], style=TableStyle(estilo),
                            hAlign="LEFT")
        self.width, self.height = self._table.wrapOn(self.canv, availWidth, availHeight)
        return self.width, self.height


class PDFReportGenerator:
    """Gerador do relatório em PDF a partir de ``ResultadosAnalise``."""

    def __init__(
        self,
        resultados: ResultadosAnalise,
        figuras: Optional[Dict[str, Path]],
        output_pdf: Path,
        data_geracao: Optional[datetime] = None,
        invariante: Optional[bool] = None,
    ) -> None:
        self.res = resultados
        # Data mostrada na capa; com --data-geracao, o PDF é reproduzível byte a byte (modo invariante)
        self.data_geracao = data_geracao
        self.invariante = data_geracao is not None if invariante is None else invariante
        self.figuras = figuras or {}
        self.output_pdf = Path(output_pdf)
        self.fonte, self.fonte_negrito = _registrar_fontes()
        self.estilos = self._criar_estilos()
        self._secao = 0
        # Tabelas, blocos e figuras desenhados × legendas de fonte emitidas (devem ser iguais)
        self._desenhados = 0
        self._legendas = 0
        # Estrutura emitida (seções, constatações, legendas) e sumário com as páginas
        self.titulos_secoes: List[str] = []
        self.constatacoes_emitidas: List[str] = []
        self.legendas_emitidas: List[str] = []
        self.paginas_secoes: Dict[str, int] = {}
        self.sumario_entradas: List[Tuple[int, str, int]] = []
        self.subtitulo_capa = ""
        self._textos: Dict[str, Tuple[str, str]] = {}

    # ------------------------------------------------------------------
    # Estilos e componentes
    # ------------------------------------------------------------------

    def _criar_estilos(self) -> Dict[str, ParagraphStyle]:
        base = dict(fontName=self.fonte, textColor=TINTA, alignment=TA_LEFT)
        return {
            "titulo": ParagraphStyle("titulo", **{**base, "fontName": self.fonte_negrito}, fontSize=17, leading=21, spaceAfter=3),
            "subtitulo": ParagraphStyle("subtitulo", **{**base, "textColor": TINTA_SECUNDARIA}, fontSize=9.5, leading=13, spaceAfter=5),
            "secao": ParagraphStyle("secao", **{**base, "fontName": self.fonte_negrito, "textColor": AZUL_TITULO},
                                    fontSize=12.5, leading=16, spaceBefore=8, spaceAfter=5),
            "subsecao": ParagraphStyle("subsecao", **{**base, "fontName": self.fonte_negrito}, fontSize=9.5, leading=12,
                                       spaceBefore=4, spaceAfter=3),
            "corpo": ParagraphStyle("corpo", **base, fontSize=9, leading=12.5, spaceAfter=4),
            "achado": ParagraphStyle("achado", **base, fontSize=8.8, leading=12, spaceAfter=5, leftIndent=14, firstLineIndent=-14),
            "legenda": ParagraphStyle("legenda", **{**base, "textColor": TINTA_SECUNDARIA}, fontSize=8, leading=10.5, spaceAfter=6),
            # Capa (spec da Geração do relatório, FR-012): nota e legendas um pouco menores, para a capa caber numa página com a ficha
            "legenda_capa": ParagraphStyle("legenda_capa", **{**base, "textColor": TINTA_SECUNDARIA}, fontSize=7.5,
                                           leading=9.5, spaceAfter=6),
            "nota": ParagraphStyle("nota", **{**base, "textColor": TINTA_SECUNDARIA}, fontSize=8, leading=10.5, spaceAfter=3,
                                   leftIndent=10, firstLineIndent=-10),
            "cab_tabela": ParagraphStyle("cab_tabela", **{**base, "fontName": self.fonte_negrito}, fontSize=7.3, leading=9),
            "cab_tabela_dir": ParagraphStyle("cab_tabela_dir", **{**base, "fontName": self.fonte_negrito, "alignment": TA_RIGHT},
                                             fontSize=7.3, leading=9),
            "celula": ParagraphStyle("celula", **base, fontSize=7.3, leading=9),
            "celula_dir": ParagraphStyle("celula_dir", **{**base, "alignment": TA_RIGHT}, fontSize=7.3, leading=9),
            "kpi_rotulo": ParagraphStyle("kpi_rotulo", **{**base, "textColor": TINTA_SECUNDARIA}, fontSize=8, leading=10),
            "kpi_valor": ParagraphStyle("kpi_valor", **{**base, "fontName": self.fonte_negrito}, fontSize=17, leading=21),
            "kpi_sub": ParagraphStyle("kpi_sub", **{**base, "textColor": TINTA_SECUNDARIA}, fontSize=7.5, leading=9.5),
        }

    def _p(self, texto: str, estilo: str = "corpo") -> Paragraph:
        return Paragraph(texto, self.estilos[estilo])

    def _titulo_secao(self, titulo: str) -> Paragraph:
        self._secao += 1
        self.titulos_secoes.append(titulo)
        return self._p(f"{self._secao}. {escape(titulo)}", "secao")

    def _tabela(
        self,
        cabecalho: Sequence[str],
        linhas: Sequence[Sequence[Any]],
        larguras: Sequence[float],
        colunas_numericas: Sequence[int] = (),
    ) -> Table:
        dados = [[self._p(escape(str(h)), "cab_tabela_dir" if i in colunas_numericas else "cab_tabela")
                  for i, h in enumerate(cabecalho)]]
        for linha in linhas:
            dados.append([
                self._p(escape(str(valor)), "celula_dir" if i in colunas_numericas else "celula")
                for i, valor in enumerate(linha)
            ])
        tabela = Table(dados, colWidths=list(larguras), repeatRows=1, hAlign="LEFT")
        self._desenhados += 1
        estilo = [
            ("BACKGROUND", (0, 0), (-1, 0), FUNDO_CABECALHO),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#c3c2b7")),
            ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINHA),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]
        for i in range(2, len(dados), 2):
            estilo.append(("BACKGROUND", (0, i), (-1, i), FUNDO_ZEBRA))
        tabela.setStyle(TableStyle(estilo))
        return tabela

    def _legenda_fonte(self, chave: str) -> Paragraph:
        """Legenda de fonte de uma tabela, bloco ou figura, com o texto do mapa de fontes."""
        self._legendas += 1
        self.legendas_emitidas.append(chave)
        return self._p(escape(legenda_fonte(self.res, chave)), "legenda")

    def _figura(self, chave: str, legenda: str, largura: float = LARGURA_UTIL - 10) -> List[Any]:
        caminho = self.figuras.get(chave)
        if caminho is None or not Path(caminho).exists():
            return [self._p(f"Figura não disponível ({escape(NOMES_FIGURAS.get(chave, chave))}).", "legenda")]
        largura_px, altura_px = ImageReader(str(caminho)).getSize()
        if chave in FIGURAS_PADRONIZADAS:
            largura = LARGURA_UTIL - 10
        altura = largura * altura_px / largura_px
        if altura > ALTURA_MAXIMA_FIGURA and chave not in FIGURAS_PADRONIZADAS:
            largura, altura = largura * ALTURA_MAXIMA_FIGURA / altura, ALTURA_MAXIMA_FIGURA
        self._desenhados += 1
        return [Image(str(caminho), width=largura, height=altura), Spacer(1, 3), self._p(legenda, "legenda"),
                self._legenda_fonte(chave)]

    def _bloco_chave_valor(
        self, titulo: str, pares: List[Tuple[str, str]], chave_fonte: str, nota: str = "",
        largura: float = LARGURA_UTIL / 2, largura_chave: float = 118,
    ) -> List[Any]:
        linhas = [[self._p(f"<b>{escape(k)}</b>", "celula"), self._p(escape(v), "celula")] for k, v in pares]
        tabela = Table(linhas, colWidths=[largura_chave, largura - largura_chave - 12])
        tabela.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINHA),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ]))
        self._desenhados += 1
        cabecalho = self._p(escape(titulo), "subsecao")
        cabecalho.style = ParagraphStyle("subsecao_bloco", parent=cabecalho.style, spaceBefore=0)
        bloco: List[Any] = [cabecalho, tabela]
        if nota:
            bloco += [Spacer(1, 2), self._p(nota, "legenda")]
        legenda = self._legenda_fonte(chave_fonte)
        legenda.style = ParagraphStyle("legenda_bloco", parent=self.estilos["legenda_capa"], spaceAfter=0)
        return bloco + [Spacer(1, 2), legenda]

    # ------------------------------------------------------------------
    # Componentes das seções
    # ------------------------------------------------------------------

    def _inicio_secao(self, story: List[Any], chave: str, titulo: str, espaco: float = 200) -> None:
        """Título da seção seguido das suas constatações, cada uma uma única vez no relatório."""
        story.append(CondPageBreak(espaco))
        story.append(self._titulo_secao(titulo))
        self._n_abertura = 2 + len(constatacoes_da_secao(self.res, chave))
        for titulo_c, texto in constatacoes_da_secao(self.res, chave):
            self.constatacoes_emitidas.append(titulo_c)
            story.append(self._p(f"<b>{escape(titulo_c)}.</b> {escape(texto)}", "corpo"))

    def _bloco_tabela(
        self,
        chave: str,
        cabecalho: Sequence[str],
        linhas: Sequence[Sequence[Any]],
        larguras: Sequence[float],
        colunas_numericas: Sequence[int] = (),
        intro: str = "",
    ) -> List[Any]:
        """Subtítulo, texto de abertura, tabela, nota e legenda de fonte.

        Até ``LINHAS_TABELA_INTEIRA`` linhas, tudo fica junto. A tabela mais longa começa na página corrente se
        couberem o subtítulo e ``LINHAS_MINIMAS_NA_PAGINA`` linhas, e continua na seguinte com o cabeçalho repetido.
        """
        subtitulo, nota = self._textos.get(chave, ("", ""))
        abertura: List[Any] = [Spacer(1, 4)]
        if subtitulo:
            abertura.append(self._p(escape(subtitulo), "subsecao"))
        if intro:
            abertura.append(self._p(escape(intro), "corpo"))
        tabela = self._tabela(cabecalho, linhas, larguras, colunas_numericas)
        fecho: List[Any] = [Spacer(1, 3)]
        if nota:
            fecho.append(self._p(escape(nota), "legenda"))
        fecho.append(self._legenda_fonte(chave))
        if len(linhas) <= LINHAS_TABELA_INTEIRA:
            return [KeepTogether(abertura + [tabela] + fecho)]
        tabela.wrap(LARGURA_UTIL, ALTURA_QUADRO)
        minimo = _altura(abertura) + sum(tabela._rowHeights[:1 + LINHAS_MINIMAS_NA_PAGINA])
        return [CondPageBreak(minimo + 4), *abertura, tabela, KeepTogether(fecho)]

    def _abertura_com_primeiro_bloco(self, itens: List[Any]) -> List[Any]:
        """Título e constatações da seção sempre juntos e, se curtos ou seguidos de figura, com o primeiro bloco.

        A figura tem altura limitada e cabe numa página com o título e as constatações. Abertura longa (mais de
        ``ALTURA_ABERTURA_CURTA``) pode ficar no pé da página, com a tabela na página seguinte, para não deixar
        meia página em branco.
        """
        n = getattr(self, "_n_abertura", 0)
        abertura, resto = itens[1:n], itens[n:]
        if not n or not resto:
            return itens
        primeiro, curta = resto[0], _altura(abertura) <= ALTURA_ABERTURA_CURTA
        if isinstance(primeiro, KeepTogether) and (curta or any(isinstance(f, Image) for f in primeiro._content)):
            return [KeepTogether(abertura + list(primeiro._content)), *resto[1:]]
        if isinstance(primeiro, CondPageBreak) and curta:
            return [CondPageBreak(_altura(abertura) + primeiro.height), *abertura, *resto[1:]]
        return [itens[0], KeepTogether(abertura), *resto]

    def _sem_linhas(self, chave: str, mensagem: str) -> List[Any]:
        subtitulo, _ = self._textos.get(chave, ("", ""))
        return ([self._p(escape(subtitulo), "subsecao")] if subtitulo else []) + [self._p(mensagem, "corpo")]

    @staticmethod
    def _escala(larguras: Sequence[float]) -> List[float]:
        return [w * LARGURA_UTIL / sum(larguras) for w in larguras]

    # ------------------------------------------------------------------
    # Capa
    # ------------------------------------------------------------------

    def _capa(self, story: List[Any]) -> None:
        c = self.res.cobertura
        story.append(self._p(f"{perfil_ativo().usina.nome} — energia vertida turbinável e desempenho operacional",
                             "titulo"))
        self.subtitulo_capa = (
            f"Análise dos dados abertos do ONS · {fmt_data_hora(c['inicio'])} a {fmt_data_hora(c['fim'])} · "
            f"{fmt_int(c['horas_observadas'])} registros horários · Gerado em "
            f"{(self.data_geracao or datetime.now()).strftime('%d/%m/%Y %H:%M')}"
        )
        story.append(self._p(self.subtitulo_capa, "subtitulo"))
        # Identificação, ficha do cadastro (se carregado; FR-012) e parâmetros, lado a lado
        conteudo = [("Identificação nos dados do ONS", pares_identificacao(self.res), "bloco_identificacao")]
        if self.res.cadastro:
            conteudo.append(("Cadastro no ONS", pares_identificacao_cadastro(self.res), "bloco_cadastro"))
        conteudo.append(("Parâmetros técnicos da usina", pares_parametros(), "bloco_parametros"))
        medidas = ([BLOCOS_CAPA_TRES[chave] for _, _, chave in conteudo] if len(conteudo) == 3
                   else [(1 / len(conteudo), 118)] * len(conteudo))
        larguras = [fracao * LARGURA_UTIL for fracao, _ in medidas]
        celulas = [self._bloco_chave_valor(titulo, pares, chave, largura=largura, largura_chave=largura_chave)
                   for (titulo, pares, chave), largura, (_, largura_chave) in zip(conteudo, larguras, medidas)]
        blocos = Table([celulas], colWidths=larguras)
        blocos.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 0),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
        story.append(blocos)
        story.append(Spacer(1, 5))

        tiles, nota_capa = indicadores_capa(self.res)
        celulas = [[
            [self._p(escape(rotulo), "kpi_rotulo"), self._p(escape(valor), "kpi_valor"), self._p(escape(sub), "kpi_sub")]
            for rotulo, valor, sub in tiles
        ]]
        tabela_kpi = Table(celulas, colWidths=[LARGURA_UTIL / len(tiles)] * len(tiles))
        tabela_kpi.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, LINHA),
            ("INNERGRID", (0, 0), (-1, -1), 0.6, LINHA),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ]))
        self._desenhados += 1
        story.append(tabela_kpi)
        story.append(Spacer(1, 4))
        story.append(self._p(nota_capa, "legenda_capa"))
        legenda = self._legenda_fonte("tab_capa_indicadores")
        legenda.style = self.estilos["legenda_capa"]
        story.append(legenda)

        # Sumário (FR-011): índice com a página de cada seção, preenchido na segunda passagem
        story.append(self._p("Sumário", "subsecao"))
        estilo = ParagraphStyle("sumario", fontName=self.fonte, fontSize=8, leading=9.5, textColor=TINTA)
        self.toc = _SumarioDuasColunas([f"{n}. {titulo}" for n, titulo in sumario(self.res)], estilo,
                                       ParagraphStyle("sumario_pagina", parent=estilo, alignment=TA_RIGHT))
        story += [self.toc, PageBreak()]

    # ------------------------------------------------------------------
    # Seções (ordem e títulos em estrutura_relatorio.SECOES)
    # ------------------------------------------------------------------

    def _secao_cobertura(self, story: List[Any], titulo: str) -> None:
        self._inicio_secao(story, "cobertura", titulo, 160)
        linhas = [[self._p(f"<b>{escape(k)}</b>", "celula"), self._p(escape(v), "celula")]
                  for k, v in pares_cobertura(self.res)]
        tabela = Table(linhas, colWidths=[130, LARGURA_UTIL - 130])
        tabela.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINHA),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        self._desenhados += 1
        story.append(tabela)
        story.append(Spacer(1, 3))
        story.append(self._legenda_fonte("tab_cobertura"))

    def _secao_indicadores_anuais(self, story: List[Any], titulo: str) -> None:
        self._inicio_secao(story, "indicadores_anuais", titulo, 260)
        cabecalho, linhas = linhas_tabela_anual(self.res)
        story += self._bloco_tabela("tab_indicadores_anuais", cabecalho, linhas,
                                    self._escala([40, 52, 72, 62, 64, 58, 60, 70, 56, 62, 70, 70]), range(1, 12))

    def _secao_disponibilidade_geracao(self, story: List[Any], titulo: str) -> None:
        self._inicio_secao(story, "disponibilidade_geracao", titulo, 330)
        story.append(KeepTogether(self._figura("disponibilidade_anual", legenda_figura(self.res, "disponibilidade_anual"))))
        cabecalho, linhas = linhas_tabela_eventos_indisponibilidade(self.res)
        if linhas:
            story += self._bloco_tabela("tab_eventos_indisponibilidade", cabecalho, linhas, [150, 150, 90, 90, 150],
                                        (2, 3, 4))
        else:
            story += self._sem_linhas("tab_eventos_indisponibilidade", "Nenhum período com essa duração.")

    def _secao_indicadores_ons(self, story: List[Any], titulo: str) -> None:
        self._inicio_secao(story, "indicadores_ons", titulo, 300)
        cabecalho, linhas = linhas_tabela_ons_disponibilidade(self.res)
        if linhas:
            story += self._bloco_tabela("tab_ons_disp_anual", cabecalho, linhas, [60, 150, 130, 110, 110, 120],
                                        range(1, 6))
        cabecalho, linhas = linhas_tabela_ons_decomposicao(self.res)
        if linhas:
            story += self._bloco_tabela("tab_ons_decomposicao", cabecalho, linhas, [60, 50, 300, 110, 120, 120],
                                        range(3, 6), intro=texto_taxas_ons(self.res))
        cabecalho, linhas = linhas_tabela_ons_ug_anual(self.res)
        if linhas:
            story += self._bloco_tabela("tab_ons_ug_anual", cabecalho, linhas, [70, 60, 110, 110, 110, 110], range(2, 6))
        cabecalho, linhas = linhas_tabela_ons_horas(self.res)
        if linhas:
            story += self._bloco_tabela("tab_ons_horas", cabecalho, linhas,
                                        self._escala([50, 45, 45] + [70] * len(INSUMOS_HORAS)),
                                        range(2, 3 + len(INSUMOS_HORAS)))
        cabecalho, linhas = linhas_tabela_ons_divergencias(self.res)
        if linhas:
            story += self._bloco_tabela("tab_ons_divergencias", cabecalho, linhas, [70, 45, 80, 80, 90, 130, 90, 130],
                                        range(2, 8))

    def _secao_figura(self, story: List[Any], chave_secao: str, titulo: str, figura: str,
                      largura: float = LARGURA_UTIL - 10) -> None:
        self._inicio_secao(story, chave_secao, titulo, 360)
        story.append(KeepTogether(self._figura(figura, legenda_figura(self.res, figura), largura=largura)))

    def _secao_serie_temporal(self, story: List[Any], titulo: str) -> None:
        self._secao_figura(story, "serie_temporal", titulo, "serie_temporal")

    def _secao_evt_mensal(self, story: List[Any], titulo: str) -> None:
        self._secao_figura(story, "evt_mensal", titulo, "evt_mensal")

    def _secao_perfil_horario(self, story: List[Any], titulo: str) -> None:
        self._secao_figura(story, "perfil_horario", titulo, "perfil_horario", largura=LARGURA_UTIL - 60)
        cabecalho, linhas = linhas_tabela_perfil_diurno(self.res)
        story += self._bloco_tabela("tab_perfil_horario", cabecalho, linhas, [60, 105, 105, 120, 105, 105, 120],
                                    range(1, 7))

    def _secao_eventos(self, story: List[Any], titulo: str) -> None:
        self._inicio_secao(story, "eventos", titulo, 200)
        cabecalho, linhas = linhas_tabela_evt_por_nivel(self.res)
        story += self._bloco_tabela("tab_evt_por_nivel", cabecalho, linhas, [190, 80, 100, 110, 110, 130], range(1, 6))
        cabecalho, linhas = linhas_tabela_eventos_parada(self.res)
        if linhas:
            story += self._bloco_tabela("tab_eventos_parada_evt", cabecalho, linhas, [130, 130, 80, 140, 140, 100],
                                        range(2, 6))
        else:
            story += self._sem_linhas("tab_eventos_parada_evt", "Nenhum evento.")

    def _secao_programacao(self, story: List[Any], titulo: str) -> None:
        self._inicio_secao(story, "programacao", titulo, 300)
        cabecalho, linhas = linhas_tabela_programacao_mensal(self.res)
        if linhas:
            story += self._bloco_tabela("tab_programacao_mensal", cabecalho, linhas, [60, 80, 85, 110, 115, 90, 125, 115],
                                        range(1, 8))
        cabecalho, linhas = linhas_tabela_programacao_perfil(self.res)
        if linhas:
            largura_hora = (LARGURA_UTIL - 50) / (len(cabecalho) - 1)
            story += self._bloco_tabela("tab_programacao_hora", cabecalho, linhas,
                                        [50] + [largura_hora] * (len(cabecalho) - 1), range(1, len(cabecalho)))
        cabecalho, linhas = linhas_tabela_programacao_eventos(self.res)
        if linhas:
            story += self._bloco_tabela("tab_programacao_eventos", cabecalho, linhas, [130, 130, 80, 140, 150, 110],
                                        range(2, 6))
        ausentes = self.res.programacao["periodo"]["lista_dias_ausentes"]
        if ausentes:
            story.append(self._p(
                f"Dias sem arquivo de programação no portal do ONS: {escape(fmt_lista(fmt_data(d) for d in ausentes))}.",
                "legenda",
            ))

    def _secao_disponibilidade_sincronizada(self, story: List[Any], titulo: str) -> None:
        self._inicio_secao(story, "disponibilidade_sincronizada", titulo, 300)
        cabecalho, linhas = linhas_tabela_disponibilidade_anual(self.res)
        if linhas:
            story += self._bloco_tabela("tab_disponibilidade_anual", cabecalho, linhas,
                                        [55, 55, 95, 100, 100, 85, 110, 150], range(1, 8))
        story.append(KeepTogether(self._figura("disponibilidade_sincronizada",
                                               legenda_figura(self.res, "disponibilidade_sincronizada"))))
        cabecalho, linhas = linhas_tabela_disponibilidade_paradas(self.res)
        if linhas:
            story += self._bloco_tabela("tab_disponibilidade_paradas", cabecalho, linhas, [150, 70, 280, 60, 90],
                                        range(3, 5))
        cabecalho, linhas = linhas_tabela_disponibilidade_divergencias(self.res)
        if linhas:
            story += self._bloco_tabela("tab_disponibilidade_divergencias", cabecalho, linhas, [130, 130, 70, 140, 140],
                                        range(2, 5))
        story.append(Spacer(1, 3))
        for nota in notas_disponibilidade(self.res):
            story.append(self._p(escape(nota), "legenda"))

    def _secao_hidrologia(self, story: List[Any], titulo: str) -> None:
        self._inicio_secao(story, "hidrologia", titulo, 300)
        if self.res.hidrologia["publicado"]:
            for chave, funcao in (("tab_faixas_afluencia", linhas_tabela_faixas_afluencia),
                                  ("tab_faixas_afluencia_evt", linhas_tabela_faixas_afluencia_evt)):
                cabecalho, linhas = funcao(self.res)
                if linhas:
                    story += self._bloco_tabela(chave, cabecalho, linhas, [60, 110, 110, 110, 80, 80, 120], range(1, 7))
            story.append(KeepTogether(self._figura("faixas_afluencia", legenda_figura(self.res, "faixas_afluencia"))))
            cabecalho, linhas = linhas_tabela_hidrologia_anual(self.res)
            if linhas:
                story += self._bloco_tabela("tab_hidrologia_anual", cabecalho, linhas,
                                            [50, 50, 90, 85, 80, 75, 110, 75, 105], range(1, 9))
            cabecalho, linhas = linhas_tabela_perfil_hidrologico(self.res)
            if linhas:
                story += self._bloco_tabela("tab_hidrologia_perfil", cabecalho, linhas,
                                            [60, 120, 115, 100, 120, 115, 100], range(1, 7))
            story.append(KeepTogether(self._figura("perfil_hidrologico", legenda_figura(self.res, "perfil_hidrologico"))))
        story.append(Spacer(1, 3))
        for nota in notas_hidrologia(self.res):
            story.append(self._p(escape(nota), "legenda"))

    def _secao_geracao_zero(self, story: List[Any], titulo: str) -> None:
        self._inicio_secao(story, "geracao_zero", titulo, 260)
        cabecalho, linhas = linhas_tabela_geracao_zero(self.res)
        story += self._bloco_tabela("tab_geracao_zero", cabecalho, linhas, self._escala([42] + [40] * 12 + [50, 66, 78]),
                                    range(1, 16))

    def _secao_vazoes(self, story: List[Any], titulo: str) -> None:
        self._secao_figura(story, "vazoes", titulo, "vazoes_defluentes")

    def _secao_geracao_oficial(self, story: List[Any], titulo: str) -> None:
        self._inicio_secao(story, "geracao_oficial", titulo, 200)
        if "Conferência da geração" not in dict(self.res.achados):
            story.append(self._p(escape(texto_conferencia_geracao(self.res)), "corpo"))
        cabecalho, linhas = linhas_tabela_geracao_anual(self.res)
        if linhas:
            story += self._bloco_tabela("tab_geracao_oficial", cabecalho, linhas, [60, 110, 130, 100, 130, 130],
                                        range(1, 6))

    def _secao_qualidade(self, story: List[Any], titulo: str) -> None:
        self._inicio_secao(story, "qualidade", titulo, 250)
        cabecalho, linhas = linhas_tabela_regras(self.res)
        if linhas:
            story += self._bloco_tabela("tab_regras_validacao", cabecalho, linhas, [45, 150, 300, 80, 90, 85], (3, 4))
        cabecalho, linhas = linhas_tabela_registros_sinalizados(self.res)
        if linhas:
            story += self._bloco_tabela("tab_registros_sinalizados", cabecalho, linhas, [45, 330, 70, 150, 150], (2,))
        cabecalho, linhas = linhas_tabela_extremos(self.res)
        if linhas:
            story += self._bloco_tabela("tab_extremos", cabecalho, linhas, [190, 80, 90, 130, 90, 130], (2, 4))

    def _secao_conclusao(self, story: List[Any], titulo: str) -> None:
        """Conclusão (spec da Geração do relatório, US4): frase de abertura e as quatro listas, juntas numa página."""
        self._inicio_secao(story, "conclusao", titulo, 200)
        listas = listas_conclusao(self.res)
        if not listas:
            story.append(self._p(escape(FRASE_CONCLUSAO_VAZIA), "corpo"))
            return
        bloco: List[Any] = [self._p(escape(FRASE_ABERTURA_CONCLUSAO), "corpo")]
        for titulo_lista, textos in listas:
            bloco.append(self._p(escape(titulo_lista), "subsecao"))
            bloco += [self._p(f"• {escape(texto)}", "nota") for texto in textos]
        story.append(KeepTogether(bloco))

    def _secao_notas(self, story: List[Any], titulo: str) -> None:
        self._inicio_secao(story, "notas", titulo, 200)
        for nota in notas_metodologicas(self.res):
            story.append(self._p(f"• {escape(nota)}", "nota"))
        cabecalho, linhas = linhas_tabela_parametros(self.res)
        # Coluna "Valor" larga o bastante para as descrições dos conjuntos de dados; "Origem" cabe a maior URL
        story += self._bloco_tabela("tab_parametros", cabecalho, linhas, [55, 190, 170, 50, 305])

    # ------------------------------------------------------------------
    # Montagem
    # ------------------------------------------------------------------

    def build_pdf(self) -> Path:
        """Compila o relatório completo em PDF: capa com sumário e as seções da estrutura do relatório."""
        logger.info("Iniciando compilação do relatório em PDF: %s", self.output_pdf)
        self.output_pdf.parent.mkdir(parents=True, exist_ok=True)
        self._secao = 0
        self._desenhados = self._legendas = 0
        self.titulos_secoes, self.constatacoes_emitidas, self.legendas_emitidas = [], [], []
        self.paginas_secoes = {}
        self._textos = textos_tabelas(self.res)
        c = self.res.cobertura

        cabecalho = (
            f"{perfil_ativo().usina.nome} — energia vertida turbinável (dados ONS) · "
            f"{fmt_data(c['inicio'])} a {fmt_data(c['fim'])}"
        )
        doc = _DocumentoComSumario(
            str(self.output_pdf),
            gerador=self,
            pagesize=landscape(A4),
            leftMargin=MARGEM_LATERAL,
            rightMargin=MARGEM_LATERAL,
            topMargin=MARGEM_SUPERIOR,
            bottomMargin=MARGEM_INFERIOR,
            title=f"{perfil_ativo().usina.nome} — energia vertida turbinável e desempenho operacional",
            subject=f"Análise dos dados abertos do ONS, {fmt_data(c['inicio'])} a {fmt_data(c['fim'])}",
            author=f"Pipeline de análise {perfil_ativo().usina.nome} (dados ONS)",
        )

        story: List[Any] = []
        self._capa(story)
        for _, secao in secoes_presentes(self.res):
            itens: List[Any] = []
            self._n_abertura = 0
            getattr(self, f"_secao_{secao.chave}")(itens, secao.titulo)
            story += self._abertura_com_primeiro_bloco(itens)

        # Com a data fixa, o modo invariante tira do PDF a data de criação e o identificador variáveis
        invariante_antes = rl_config.invariant
        if self.invariante:
            rl_config.invariant = 1
        try:
            doc.multiBuild(story, canvasmaker=_canvas_numerado(cabecalho, self.fonte))
        finally:
            rl_config.invariant = invariante_antes
        self.sumario_entradas = [(n, titulo, self.paginas_secoes.get(titulo, 0)) for n, titulo in sumario(self.res)]
        if self._legendas != self._desenhados:
            logger.warning("PDF com %d tabelas, blocos e figuras e %d legendas de fonte.",
                           self._desenhados, self._legendas)
        if len(set(self.constatacoes_emitidas)) != len(self.res.achados):
            logger.warning("PDF com %d constatações emitidas para %d calculadas.",
                           len(self.constatacoes_emitidas), len(self.res.achados))
        logger.info("Relatório PDF gerado: %s (%d bytes)", self.output_pdf, self.output_pdf.stat().st_size)
        return self.output_pdf
