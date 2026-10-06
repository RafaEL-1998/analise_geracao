"""Geração do relatório em PDF (A4 paisagem) a partir dos resultados calculados em analyzer.py.

O PDF não contém números nem conclusões fixos: textos, tabelas e legendas das figuras
são montados a partir de ``ResultadosAnalise``.
"""

from __future__ import annotations

import argparse
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from xml.sax.saxutils import escape

import matplotlib
import pandas as pd
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
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.analyzer import (
    NOMES_FIGURAS,
    NOMES_FIGURAS_OPCIONAIS,
    ResultadosAnalise,
    analisar,
    carregar_dados_tratados,
    linhas_tabela_anual,
    linhas_tabela_disponibilidade_anual,
    linhas_tabela_disponibilidade_divergencias,
    linhas_tabela_disponibilidade_paradas,
    linhas_tabela_faixas_afluencia,
    linhas_tabela_faixas_afluencia_evt,
    linhas_tabela_geracao_anual,
    linhas_tabela_hidrologia_anual,
    notas_disponibilidade,
    notas_hidrologia,
    texto_conferencia_geracao,
    linhas_tabela_geracao_zero,
    linhas_tabela_ons_decomposicao,
    linhas_tabela_ons_disponibilidade,
    linhas_tabela_ons_divergencias,
    linhas_tabela_ons_horas,
    linhas_tabela_ons_ug_anual,
    linhas_tabela_programacao_eventos,
    linhas_tabela_programacao_mensal,
    linhas_tabela_programacao_perfil,
    notas_metodologicas,
    texto_taxas_ons,
)
from src.indicadores_ons import INSUMOS_HORAS, carregar_indicadores_processados
from src.logger import NIVEIS_LOG, configurar_nivel_log
from src.programacao_ons import carregar_programacao_processada
from src.disponibilidade_ons import carregar_disponibilidade_processada
from src.hidrologia_ons import carregar_hidrologia_processada
from src.geracao_ons import carregar_geracao_processada
from src.cadastro_ons import carregar_cadastro_processado
from src.fontes_relatorio import legenda_fonte, rodape_fontes
from src.dicionarios_ons import carregar_registro as carregar_registro_dicionarios
from src.config import (
    COD_USINA_ONS,
    DISPONIBILIDADE_REFERENCIA,
    DURACAO_MINIMA_EVENTO_RELATORIO_H,
    ENGOLIMENTO_MAXIMO_USINA_M3S,
    ENGOLIMENTO_NOMINAL_UG_M3S,
    GARANTIA_FISICA_MWMED,
    HORAS_DIURNAS,
    HORAS_NOTURNAS,
    IP_REFERENCIA,
    LIMIAR_VERTIMENTO_MINIMO_M3S,
    NOMINAL_INSTALLED_CAPACITY_MW,
    NUMERO_EVENTOS_RELATORIO,
    NUMERO_UNIDADES_GERADORAS,
    ONS_DATASET_URL,
    PDF_REPORT_PATH,
    POTENCIA_UNITARIA_MW,
    REPORTS_FIGURES_DIR,
    TEIF_REFERENCIA,
    TIPO_TURBINA,
)
from src.formatacao import (
    fmt_data,
    fmt_data_hora,
    fmt_int,
    fmt_lista,
    fmt_mes_ano,
    fmt_num,
    fmt_pct,
    plural,
)

logger = logging.getLogger("uhe_sao_domingos.pdf_generator")

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


def _canvas_numerado(cabecalho: str, rodape: str, fonte: str):
    """Canvas de dois passos que escreve cabeçalho, rodapé e 'Página X de Y'."""

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
            self.drawString(MARGEM_LATERAL, 19, rodape)
            self.drawRightString(largura - MARGEM_LATERAL, 19, f"Página {self._pageNumber} de {total}")
            self.restoreState()

    return CanvasNumerado


def _fmt_utc(valor: str) -> str:
    """Formata o last_modified do CKAN ('2026-09-30T15:05:02.533') como '30/09/2026 15:05 UTC'."""
    if not valor:
        return ""
    try:
        return pd.Timestamp(valor).strftime("%d/%m/%Y %H:%M") + " UTC"
    except (ValueError, TypeError):
        return str(valor)


def pares_identificacao_cadastro(res: ResultadosAnalise) -> List[Tuple[str, str]]:
    """Linhas da tabela de identificação da usina no PDF (US6/AC4), com a data da consulta ao cadastro."""
    f = res.cadastro["ficha"]
    return [
        ("Usina", f"{f.get('nom_usina', '')} · CEG {f.get('ceg', '')} · id ONS {f.get('id_ons', '')}"),
        ("Modalidade de operação", str(f.get("nom_modalidadeoperacao", ""))),
        ("Centro de operação", str(f.get("sgl_centrooperacao", ""))),
        ("Ponto de conexão", str(f.get("nom_pontoconexao", ""))),
        ("Potência autorizada", f"{fmt_num(f.get('val_potenciaautorizada'), 1)} MW"),
        ("Estado · situação na ANEEL", f"{f.get('id_estado', '')} · {f.get('sts_aneel', '')}"),
        ("Homônimos no cadastro (excluídos pelo CEG)", fmt_int(f.get("homonimos", 0))),
        ("Data da consulta", _fmt_utc(res.cadastro["obtido_em"]) or "não registrada"),
    ]


def nota_identificacao_cadastro(res: ResultadosAnalise) -> str:
    """Nota da tabela: a fonte, com a ressalva de cadastro sem histórico, precedida das divergências, se houver."""
    nota = "Fonte: conjunto Modalidade das usinas do ONS (cadastro sem série histórica; versões anteriores preservadas)."
    if res.cadastro["divergencias"]:
        nota = f"Divergências com os parâmetros do projeto: {res.cadastro['divergencias']}. {nota}"
    return nota


class PDFReportGenerator:
    """Gerador do relatório em PDF a partir de ``ResultadosAnalise``."""

    def __init__(
        self,
        resultados: ResultadosAnalise,
        figuras: Optional[Dict[str, Path]] = None,
        output_pdf: Optional[Path] = None,
    ) -> None:
        self.res = resultados
        self.figuras = figuras if figuras is not None else {
            chave: REPORTS_FIGURES_DIR / nome for chave, nome in {**NOMES_FIGURAS, **NOMES_FIGURAS_OPCIONAIS}.items()
        }
        self.output_pdf = output_pdf or PDF_REPORT_PATH
        self.fonte, self.fonte_negrito = _registrar_fontes()
        self.estilos = self._criar_estilos()
        self._secao = 0
        # Spec 007: tabelas, blocos e figuras desenhados × legendas de fonte emitidas (devem ser iguais)
        self._desenhados = 0
        self._legendas = 0
        self.rodape = ""

    # ------------------------------------------------------------------
    # Estilos e componentes
    # ------------------------------------------------------------------

    def _criar_estilos(self) -> Dict[str, ParagraphStyle]:
        base = dict(fontName=self.fonte, textColor=TINTA, alignment=TA_LEFT)
        return {
            "titulo": ParagraphStyle("titulo", **{**base, "fontName": self.fonte_negrito}, fontSize=17, leading=21, spaceAfter=3),
            "subtitulo": ParagraphStyle("subtitulo", **{**base, "textColor": TINTA_SECUNDARIA}, fontSize=9.5, leading=13, spaceAfter=8),
            "secao": ParagraphStyle("secao", **{**base, "fontName": self.fonte_negrito, "textColor": AZUL_TITULO},
                                    fontSize=12.5, leading=16, spaceBefore=8, spaceAfter=5),
            "subsecao": ParagraphStyle("subsecao", **{**base, "fontName": self.fonte_negrito}, fontSize=9.5, leading=12,
                                       spaceBefore=4, spaceAfter=3),
            "corpo": ParagraphStyle("corpo", **base, fontSize=9, leading=12.5, spaceAfter=4),
            "achado": ParagraphStyle("achado", **base, fontSize=8.8, leading=12, spaceAfter=5, leftIndent=14, firstLineIndent=-14),
            "legenda": ParagraphStyle("legenda", **{**base, "textColor": TINTA_SECUNDARIA}, fontSize=8, leading=10.5, spaceAfter=6),
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
        """Legenda de fonte (spec 007) de uma tabela, bloco ou figura, com o texto do mapa de fontes."""
        self._legendas += 1
        return self._p(escape(legenda_fonte(self.res, chave)), "legenda")

    def _figura(self, chave: str, legenda: str, largura: float = LARGURA_UTIL - 10) -> List[Any]:
        caminho = self.figuras.get(chave)
        if caminho is None or not Path(caminho).exists():
            return [self._p(f"Figura não disponível ({escape(NOMES_FIGURAS.get(chave, chave))}).", "legenda")]
        largura_px, altura_px = ImageReader(str(caminho)).getSize()
        altura = largura * altura_px / largura_px
        self._desenhados += 1
        return [Image(str(caminho), width=largura, height=altura), Spacer(1, 3), self._p(legenda, "legenda"),
                self._legenda_fonte(chave)]

    def _bloco_chave_valor(
        self, titulo: str, pares: List[Tuple[str, str]], chave_fonte: str, nota: str = ""
    ) -> List[Any]:
        linhas = [[self._p(f"<b>{escape(k)}</b>", "celula"), self._p(escape(v), "celula")] for k, v in pares]
        tabela = Table(linhas, colWidths=[118, LARGURA_UTIL / 2 - 118 - 12])
        tabela.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINHA),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ]))
        self._desenhados += 1
        bloco: List[Any] = [self._p(escape(titulo), "subsecao"), tabela]
        if nota:
            bloco += [Spacer(1, 2), self._p(nota, "legenda")]
        return bloco + [Spacer(1, 2), self._legenda_fonte(chave_fonte)]

    # ------------------------------------------------------------------
    # Seções
    # ------------------------------------------------------------------

    def _capa(self, story: List[Any]) -> None:
        c = self.res.cobertura
        g = self.res.globais
        ident = c["identificacao"]
        story.append(self._p("UHE São Domingos — energia vertida turbinável e desempenho operacional", "titulo"))
        story.append(self._p(
            f"Análise dos dados abertos do ONS (conjunto Energia Vertida Turbinável) · "
            f"{fmt_data_hora(c['inicio'])} a {fmt_data_hora(c['fim'])} · {fmt_int(c['horas_observadas'])} registros horários",
            "subtitulo",
        ))

        agentes = "; ".join(
            f"{r.nom_agente} ({fmt_data(r.primeiro_registro)} a {fmt_data(r.ultimo_registro)})"
            for r in c["agentes"].itertuples()
        )
        esquerda = self._bloco_chave_valor("Identificação nos dados do ONS", chave_fonte="bloco_identificacao", pares=[
            ("cod_usina", f"{ident.get('cod_usina', '')} (código nos modelos de otimização)"),
            ("Reservatório", ident.get("nom_reservatorio", "")),
            ("Rio / bacia", f"{ident.get('nom_rio', '')} / {ident.get('nom_bacia', '')}"),
            ("Subsistema", f"{ident.get('nom_subsistema', '')} ({ident.get('id_subsistema', '')})"),
            ("Agente", agentes),
        ])
        direita = self._bloco_chave_valor("Parâmetros técnicos da usina", chave_fonte="bloco_parametros", pares=[
            ("Potência instalada", f"{fmt_num(NOMINAL_INSTALLED_CAPACITY_MW, 1)} MW "
                                   f"({NUMERO_UNIDADES_GERADORAS} × {fmt_num(POTENCIA_UNITARIA_MW, 1)} MW)"),
            ("Turbinas", TIPO_TURBINA),
            ("Engolimento nominal", f"{NUMERO_UNIDADES_GERADORAS} × {fmt_num(ENGOLIMENTO_NOMINAL_UG_M3S, 1)} m³/s "
                                    f"({fmt_num(ENGOLIMENTO_MAXIMO_USINA_M3S, 1)} m³/s)"),
            ("Garantia física", f"{fmt_num(GARANTIA_FISICA_MWMED, 1)} MWmed (ANEEL)"),
            ("IP / TEIF de referência", f"{fmt_pct(IP_REFERENCIA * 100, 3)} / {fmt_pct(TEIF_REFERENCIA * 100, 3)} "
                                        f"(disponibilidade de referência {fmt_pct(DISPONIBILIDADE_REFERENCIA * 100, 2)})"),
        ])
        blocos = Table([[esquerda, direita]], colWidths=[LARGURA_UTIL / 2, LARGURA_UTIL / 2])
        blocos.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 12)]))
        story.append(blocos)
        story.append(Spacer(1, 10))

        tiles = [
            ("Disponibilidade média declarada", fmt_pct(g["disponibilidade_relativa_pct"]),
             f"da potência instalada; referência da garantia física: {fmt_pct(g['disponibilidade_referencia_pct'])}"),
            ("Fator de capacidade", fmt_pct(g["fator_capacidade_pct"]),
             f"geração média de {fmt_num(g['geracao_media_mwmed'], 1)} MWmed, "
             f"{fmt_pct(g['geracao_sobre_garantia_fisica_pct'])} da garantia física"),
            ("Energia vertida turbinável", f"{fmt_num(g['evt_mwh'] / 1000, 1)} GWh",
             f"{fmt_pct(g['indice_evt_pct'])} de geração + EVT; presente em {fmt_pct(g['horas_com_evt_pct'])} das horas"),
            ("EVT com a usina parada", f"{fmt_num(g['evt_parada_mwh'] / 1000, 1)} GWh",
             f"{fmt_pct(g['evt_parada_pct'])} da EVT, em {fmt_int(g['horas_parada_com_evt'])} h com geração até 1 MW"),
        ]
        p = self.res.ons.get("disp_periodo")
        t = self.res.ons.get("taxa_ultima")
        if p and t:
            tiles.insert(1, (
                "Disponibilidade apurada pelo ONS (DISPF)", fmt_pct(p["dispf_pct"]),
                f"média das unidades; TEIFa {fmt_pct(t['teifa_pct'], 2)} e TEIP {fmt_pct(t['teip_pct'], 2)} "
                f"em {fmt_mes_ano(t['mes'])}",
            ))
        celulas = [[
            [self._p(escape(rotulo), "kpi_rotulo"), self._p(escape(valor), "kpi_valor"), self._p(escape(sub), "kpi_sub")]
            for rotulo, valor, sub in tiles
        ]]
        largura_tile = LARGURA_UTIL / len(tiles)
        tabela_kpi = Table(celulas, colWidths=[largura_tile] * len(tiles))
        tabela_kpi.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, LINHA),
            ("INNERGRID", (0, 0), (-1, -1), 0.6, LINHA),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ]))
        self._desenhados += 1
        story.append(tabela_kpi)
        story.append(Spacer(1, 4))
        if self.res.ons:
            nota_capa = (
                "A disponibilidade declarada e o fator de capacidade são calculados a partir do conjunto de EVT; o DISPF, "
                "a TEIFa e a TEIP são os indicadores apurados pelo ONS (seção de indicadores oficiais). O FID não é "
                "publicado pelo ONS. Ver notas metodológicas."
            )
        else:
            nota_capa = (
                "Os indicadores de disponibilidade e fator de capacidade são aproximações calculadas a partir dos dados "
                "do ONS e não substituem os índices regulatórios (FID, TEIP, TEIFa). Ver notas metodológicas."
            )
        story.append(self._p(nota_capa, "legenda"))
        story.append(self._legenda_fonte("tab_capa_indicadores"))

    def _constatacoes(self, story: List[Any]) -> None:
        story.append(self._titulo_secao("Principais constatações"))
        for i, (titulo, texto) in enumerate(self.res.achados, start=1):
            story.append(self._p(f"<b>{i}. {escape(titulo)}.</b> {escape(texto)}", "achado"))

    def _secao_cobertura(self, story: List[Any]) -> None:
        c = self.res.cobertura
        arq = c.get("arquivos") or {}
        man = c.get("manifesto") or {}
        faltantes = c["horas_faltantes"]
        pares = [
            ("Conjunto de dados", f"Energia Vertida Turbinável — ONS ({ONS_DATASET_URL})"),
            ("Critério de extração", f"cod_usina = {COD_USINA_ONS} e nome do reservatório conferido"),
        ]
        if arq:
            pares.append(("Arquivos lidos", (
                f"{fmt_int(arq['total'])} arquivos CSV; {fmt_int(arq['com_registros'])} com registros da usina; "
                f"sem registros: {fmt_lista(arq['sem_registros']) or 'nenhum'}; "
                f"falhas de leitura: {fmt_lista(arq['falhas']) or 'nenhuma'}; "
                f"linhas com código ou nome divergentes: {fmt_int(arq['divergencias'])}"
            )))
        if man:
            pares.append(("Versão dos arquivos", (
                f"{fmt_int(man['arquivos'])} arquivos registrados no manifesto; publicação mais recente no portal: "
                f"{_fmt_utc(man['ultima_modificacao_mais_recente'])}"
            )))
        pares += [
            ("Período", f"{fmt_data_hora(c['inicio'])} a {fmt_data_hora(c['fim'])}"),
            ("Registros", (
                f"{fmt_int(c['horas_observadas'])} de {fmt_int(c['horas_esperadas'])} horas esperadas; "
                f"horas ausentes: {fmt_lista(fmt_data_hora(t) for t in faltantes[:10]) or 'nenhuma'}; "
                f"horários duplicados: {fmt_int(c['duplicadas'])}"
            )),
            ("Anos parciais", fmt_lista(
                f"{int(r.ano)} ({fmt_pct(r.cobertura_pct)} das horas)" for r in c["por_ano"].itertuples() if r.ano_parcial
            ) or "nenhum"),
        ]
        story.append(CondPageBreak(160))
        story.append(self._titulo_secao("Fonte e cobertura dos dados"))
        linhas = [[self._p(f"<b>{escape(k)}</b>", "celula"), self._p(escape(v), "celula")] for k, v in pares]
        tabela = Table(linhas, colWidths=[130, LARGURA_UTIL - 130])
        tabela.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINHA),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        self._desenhados += 1
        story.append(tabela)
        story.append(self._legenda_fonte("tab_cobertura"))

    def _secao_indicadores(self, story: List[Any]) -> None:
        cabecalho, linhas = linhas_tabela_anual(self.res)
        larguras = [40, 52, 72, 62, 64, 58, 60, 70, 56, 62, 70, 70]
        escala = LARGURA_UTIL / sum(larguras)
        tabela = self._tabela(cabecalho, linhas, [w * escala for w in larguras], colunas_numericas=range(1, 12))
        titulo = self._titulo_secao("Indicadores anuais")
        nota = self._p(
            "* Ano parcial. Disp. média = disponibilidade média declarada ÷ potência instalada; Δ vs ref. GF = diferença "
            f"para a disponibilidade de referência da garantia física ({fmt_pct(DISPONIBILIDADE_REFERENCIA * 100, 2)}); "
            "fator de capacidade = geração média ÷ potência instalada; Geração / GF = geração média ÷ garantia física; "
            f"EVT no vert. mínimo = parcela da EVT ocorrida em horas com vertimento de até {fmt_num(LIMIAR_VERTIMENTO_MINIMO_M3S, 0)} m³/s; "
            "índice EVT = EVT ÷ (geração + EVT); horas parada c/ EVT = horas com geração até 1 MW e EVT positiva; "
            "horas indisp. total = horas com disponibilidade zero.",
            "legenda",
        )
        story.append(KeepTogether([titulo, tabela, Spacer(1, 4), nota, self._legenda_fonte("tab_indicadores_anuais")]))

    def _secao_disponibilidade(self, story: List[Any]) -> None:
        referencia = DISPONIBILIDADE_REFERENCIA * 100
        gf_rel = GARANTIA_FISICA_MWMED / NOMINAL_INSTALLED_CAPACITY_MW * 100
        legenda = (
            "Barras: disponibilidade média declarada e geração média, em % da potência instalada. Linha tracejada: "
            f"disponibilidade de referência da garantia física ({fmt_pct(referencia)}); linha pontilhada: garantia física "
            f"({fmt_pct(gf_rel)} da potência instalada)."
        )
        bloco: List[Any] = [self._titulo_secao("Disponibilidade e geração por ano")]
        bloco += self._figura("disponibilidade_anual", legenda)
        story.append(CondPageBreak(330))
        story.append(KeepTogether(bloco))

        eventos = self.res.eventos_indisponibilidade_total
        longos = eventos[eventos["duracao_h"] >= DURACAO_MINIMA_EVENTO_RELATORIO_H] if len(eventos) else eventos
        story.append(self._p(
            f"Períodos de indisponibilidade total (disponibilidade zero) com pelo menos {DURACAO_MINIMA_EVENTO_RELATORIO_H} h",
            "subsecao",
        ))
        if len(longos):
            linhas = [
                [fmt_data_hora(r.inicio), fmt_data_hora(r.fim), fmt_int(r.duracao_h), fmt_num(r.duracao_h / 24, 1),
                 fmt_num(r.vazao_vertida_media_m3s, 1)]
                for r in longos.itertuples()
            ]
            story.append(self._tabela(
                ["Início", "Fim", "Duração (h)", "Duração (dias)", "Vazão vertida média (m³/s)"],
                linhas, [150, 150, 90, 90, 150], colunas_numericas=(2, 3, 4),
            ))
            story.append(Spacer(1, 3))
            story.append(self._p(
                f"Total de eventos com disponibilidade zero (qualquer duração): {fmt_int(len(eventos))}. "
                "A lista completa está na aba EVENTOS_INDISP_TOTAL da planilha.",
                "legenda",
            ))
            story.append(self._legenda_fonte("tab_eventos_indisponibilidade"))
        else:
            story.append(self._p("Nenhum período com essa duração.", "corpo"))

    def _secao_indicadores_ons(self, story: List[Any]) -> None:
        """Indicadores oficiais do ONS por unidade geradora (omitida se não houver indicadores)."""
        if not self.res.ons:
            return
        textos = dict(self.res.achados)
        story.append(CondPageBreak(300))
        story.append(self._titulo_secao("Indicadores oficiais do ONS por unidade geradora"))
        texto = textos.get("Indicadores oficiais de disponibilidade (ONS)", "")
        if texto:
            story.append(self._p(escape(texto), "corpo"))

        cabecalho, linhas = linhas_tabela_ons_disponibilidade(self.res)
        if linhas:
            story.append(KeepTogether([
                self._p("Disponibilidade da usina por ano: declarada no conjunto de EVT e DISPF apurado pelo ONS", "subsecao"),
                self._tabela(cabecalho, linhas, [60, 150, 130, 110, 110, 120], colunas_numericas=range(1, 6)),
                Spacer(1, 3),
                self._p("* Ano parcial. DISPF da usina = média das unidades ponderada pela potência e pelas horas da base "
                        "de EVT em cada mês; Δ = diferença para a disponibilidade de referência da garantia física "
                        f"({fmt_pct(DISPONIBILIDADE_REFERENCIA * 100, 2)}).", "legenda"),
                self._legenda_fonte("tab_ons_disp_anual"),
            ]))

        cabecalho, linhas = linhas_tabela_ons_decomposicao(self.res)
        if linhas:
            story.append(Spacer(1, 6))
            story.append(KeepTogether([
                self._p("TEIFa e TEIP mais recentes: contribuição de cada unidade e parcela de horas", "subsecao"),
                self._p(escape(texto_taxas_ons(self.res)), "corpo"),
                self._tabela(cabecalho, linhas, [60, 50, 300, 110, 120, 120], colunas_numericas=range(3, 6)),
                Spacer(1, 3),
                self._p("Contribuição = horas da parcela na janela de 60 meses (ponderadas pela potência) ÷ denominador da "
                        "taxa; as contribuições somam a taxa publicada.", "legenda"),
                self._legenda_fonte("tab_ons_decomposicao"),
            ]))

        cabecalho, linhas = linhas_tabela_ons_ug_anual(self.res)
        if linhas:
            story.append(Spacer(1, 6))
            story.append(KeepTogether([
                self._p("Indicadores anuais por unidade geradora (base anual do ONS)", "subsecao"),
                self._tabela(cabecalho, linhas, [70, 60, 110, 110, 110, 110], colunas_numericas=range(2, 6)),
                Spacer(1, 3),
                self._p("* Ano parcial. DISPF, INDISPPF e INDISPFF em % do tempo; DMDFF = duração média dos desligamentos "
                        "forçados (h). Não descontam a operação com potência limitada.", "legenda"),
                self._legenda_fonte("tab_ons_ug_anual"),
            ]))

        cabecalho, linhas = linhas_tabela_ons_horas(self.res)
        if linhas:
            larguras = [50, 45, 45] + [70] * len(INSUMOS_HORAS)
            escala = LARGURA_UTIL / sum(larguras)
            story.append(Spacer(1, 6))
            story.append(KeepTogether([
                self._p("Horas por estado operativo, por ano e unidade geradora", "subsecao"),
                self._tabela(cabecalho, linhas, [w * escala for w in larguras], colunas_numericas=range(2, 3 + len(INSUMOS_HORAS))),
                Spacer(1, 3),
                self._p("* Ano parcial. " + escape("; ".join(f"{s} = {d}" for s, d in INSUMOS_HORAS.items()))
                        + ". HP = HS + HRD + HDP + HDF + HDCE + HEDP + HEDF.", "legenda"),
                self._legenda_fonte("tab_ons_horas"),
            ]))

        cabecalho, linhas = linhas_tabela_ons_divergencias(self.res)
        if linhas:
            story.append(Spacer(1, 6))
            story.append(KeepTogether([
                self._p("Meses em que o indicador DISPF e as horas do TEIP divergem", "subsecao"),
                self._tabela(cabecalho, linhas, [70, 45, 80, 80, 90, 130, 90, 130], colunas_numericas=range(2, 8)),
                Spacer(1, 3),
                self._legenda_fonte("tab_ons_divergencias"),
            ]))

        texto = textos.get("Estados operativos das unidades geradoras (ONS)", "")
        if texto:
            story.append(Spacer(1, 4))
            story.append(self._p(escape(texto), "corpo"))

    def _secao_serie_temporal(self, story: List[Any]) -> None:
        c = self.res.cobertura
        eventos = self.res.eventos_indisponibilidade_total
        longos = eventos[eventos["duracao_h"] >= DURACAO_MINIMA_EVENTO_RELATORIO_H] if len(eventos) else eventos
        legenda = (
            f"Médias diárias de {fmt_data(c['inicio'])} a {fmt_data(c['fim'])}. Faixas cinza: indisponibilidade total com "
            f"pelo menos {DURACAO_MINIMA_EVENTO_RELATORIO_H} h ({fmt_int(len(longos))} "
            f"{plural(len(longos), 'período', 'períodos')}). Linha tracejada: potência instalada "
            f"({fmt_num(NOMINAL_INSTALLED_CAPACITY_MW, 0)} MW); linha pontilhada: garantia física "
            f"({fmt_num(GARANTIA_FISICA_MWMED, 1)} MWmed)."
        )
        bloco: List[Any] = [self._titulo_secao("Série temporal de disponibilidade, geração e EVT")]
        bloco += self._figura("serie_temporal", legenda)
        story.append(CondPageBreak(360))
        story.append(KeepTogether(bloco))

    def _secao_evt_mensal(self, story: List[Any]) -> None:
        m = self.res.evt_mensal
        mc = self.res.mudanca_classificacao
        legenda = (
            f"EVT mensal em MWh. Cinza: parcela ocorrida em horas com vertimento de até "
            f"{fmt_num(LIMIAR_VERTIMENTO_MINIMO_M3S, 0)} m³/s (patamar contínuo); laranja: demais horas."
        )
        if mc.get("mes") is not None:
            legenda += (
                f" Linha vertical: {fmt_mes_ano(mc['mes'])}, mês a partir do qual parte do vertimento contínuo passa a ser "
                "registrada como não turbinável."
            )
        if len(m):
            maior = m.loc[m["evt_mwh"].idxmax()]
            legenda += f" Maior EVT mensal: {fmt_int(maior['evt_mwh'])} MWh em {fmt_mes_ano(maior['mes'])}."
        bloco: List[Any] = [self._titulo_secao("Energia vertida turbinável mensal")]
        bloco += self._figura("evt_mensal", legenda)
        story.append(CondPageBreak(360))
        story.append(KeepTogether(bloco))

        titulo_mc, texto_mc = next(
            ((t, x) for t, x in self.res.achados if t.startswith("Mudança de classificação")), ("", "")
        )
        if texto_mc:
            story.append(self._p(f"<b>{escape(titulo_mc)}.</b> {escape(texto_mc)}", "corpo"))

    def _secao_perfil_horario(self, story: List[Any]) -> None:
        legenda = (
            "Média por ano e hora do dia: à esquerda, geração (MW); à direita, EVT (MWmed). A tabela "
            f"compara a janela diurna ({HORAS_DIURNAS[0]}h às {HORAS_DIURNAS[-1]}h) com a noturna "
            f"({HORAS_NOTURNAS[0]}h às {HORAS_NOTURNAS[-1]}h)."
        )
        bloco: List[Any] = [self._titulo_secao("Perfil horário da geração e da EVT")]
        bloco += self._figura("perfil_horario", legenda, largura=LARGURA_UTIL - 60)
        story.append(CondPageBreak(360))
        story.append(KeepTogether(bloco))

        anuais = self.res.indicadores_anuais
        linhas = [
            [f"{int(r.ano)}{'*' if r.ano_parcial else ''}", fmt_num(r.evt_media_diurna_mw, 2), fmt_num(r.evt_media_noturna_mw, 2),
             fmt_num(r.razao_evt_diurna_noturna, 2), fmt_num(r.geracao_media_diurna_mw, 1), fmt_num(r.geracao_media_noturna_mw, 1),
             fmt_pct(r.razao_geracao_diurna_noturna * 100, 0)]
            for r in anuais.itertuples()
        ]
        tabela = self._tabela(
            ["Ano", "EVT diurna (MWmed)", "EVT noturna (MWmed)", "Razão EVT diurna/noturna",
             "Geração diurna (MW)", "Geração noturna (MW)", "Geração diurna ÷ noturna"],
            linhas, [60, 105, 105, 120, 105, 105, 120], colunas_numericas=range(1, 7),
        )
        story.append(KeepTogether([tabela, Spacer(1, 3), self._legenda_fonte("tab_perfil_horario")]))

    def _secao_eventos(self, story: List[Any]) -> None:
        faixas = self.res.evt_por_faixa_geracao
        linhas_faixas = [
            [r.faixa_geracao, fmt_int(r.horas), fmt_num(r.evt_mwh, 1), fmt_pct(r.participacao_evt_pct),
             fmt_num(r.geracao_media_mw, 1), fmt_num(r.disponibilidade_media_mw, 1)]
            for r in faixas.itertuples()
        ]
        bloco: List[Any] = [
            self._titulo_secao("EVT por nível de geração e eventos de usina parada"),
            self._p("Distribuição das horas com EVT pelo nível de geração no mesmo horário", "subsecao"),
            self._tabela(
                ["Geração na hora", "Horas", "EVT (MWh)", "Participação na EVT", "Geração média (MW)", "Disponibilidade média (MW)"],
                linhas_faixas, [190, 80, 100, 110, 110, 130], colunas_numericas=range(1, 6),
            ),
            Spacer(1, 3),
            self._legenda_fonte("tab_evt_por_nivel"),
        ]
        story.append(CondPageBreak(200))
        story.append(KeepTogether(bloco))

        eventos = self.res.eventos_parada_com_evt
        story.append(Spacer(1, 6))
        story.append(self._p(
            f"Maiores eventos de usina parada (geração até 1 MW) com EVT — {NUMERO_EVENTOS_RELATORIO} maiores por EVT",
            "subsecao",
        ))
        if len(eventos):
            top = eventos.nlargest(NUMERO_EVENTOS_RELATORIO, "evt_mwh")
            linhas = [
                [fmt_data_hora(r.inicio), fmt_data_hora(r.fim), fmt_int(r.duracao_h), fmt_num(r.disponibilidade_media_mw, 1),
                 fmt_num(r.vazao_vertida_media_m3s, 1), fmt_num(r.evt_mwh, 1)]
                for r in top.itertuples()
            ]
            story.append(self._tabela(
                ["Início", "Fim", "Duração (h)", "Disponibilidade média (MW)", "Vazão vertida média (m³/s)", "EVT (MWh)"],
                linhas, [130, 130, 80, 140, 140, 100], colunas_numericas=range(2, 6),
            ))
            por_ano = eventos.assign(ano=pd.to_datetime(eventos["inicio"]).dt.year).groupby("ano").size()
            story.append(Spacer(1, 3))
            story.append(self._p(
                f"Total: {fmt_int(len(eventos))} eventos ({'; '.join(f'{a}: {fmt_int(n)}' for a, n in por_ano.items())}). "
                "A lista completa está na aba EVENTOS_PARADA_COM_EVT da planilha. O conjunto de dados não informa a causa "
                "das paradas.",
                "legenda",
            ))
            story.append(self._legenda_fonte("tab_eventos_parada_evt"))
        else:
            story.append(self._p("Nenhum evento.", "corpo"))

    def _secao_programacao(self, story: List[Any]) -> None:
        """Operação verificada × programação diária do ONS (omitida se não houver programação)."""
        if not self.res.programacao:
            return
        story.append(CondPageBreak(300))
        story.append(self._titulo_secao("Operação verificada e programação diária do ONS"))
        texto = dict(self.res.achados).get("Programação diária do ONS", "")
        if texto:
            story.append(self._p(escape(texto), "corpo"))

        cabecalho, linhas = linhas_tabela_programacao_mensal(self.res)
        if linhas:
            story.append(self._p("Horas paradas com EVT por mês e programação do ONS", "subsecao"))
            story.append(self._tabela(cabecalho, linhas, [60, 80, 85, 110, 115, 90, 125, 115],
                                      colunas_numericas=range(1, 8)))
            story.append(Spacer(1, 3))
            story.append(self._p(
                "Horas comuns à base de EVT e à programação. Usina parada = geração até 1 MW; programação ≤ 1 MW = o ONS "
                "não programou geração; > 5 MW = a usina parou com geração programada. Classificação hora a hora na aba "
                "PROG_HORAS_CLASSIFICADAS da planilha.",
                "legenda",
            ))
            story.append(self._legenda_fonte("tab_programacao_mensal"))

        cabecalho, linhas = linhas_tabela_programacao_perfil(self.res)
        if linhas:
            largura_hora = (LARGURA_UTIL - 50) / (len(cabecalho) - 1)
            story.append(Spacer(1, 6))
            story.append(KeepTogether([
                self._p("Horas paradas com EVT e programação de até 1 MW, por hora do dia", "subsecao"),
                self._tabela(cabecalho, linhas, [50] + [largura_hora] * (len(cabecalho) - 1),
                             colunas_numericas=range(1, len(cabecalho))),
                Spacer(1, 3),
                self._legenda_fonte("tab_programacao_hora"),
            ]))

        cabecalho, linhas = linhas_tabela_programacao_eventos(self.res)
        if linhas:
            p = self.res.programacao["periodo"]
            story.append(Spacer(1, 6))
            story.append(KeepTogether([
                self._p(f"Maiores eventos de usina parada com programação acima de 5 MW ({fmt_int(p['eventos_desvio'])} "
                        f"eventos, {fmt_int(p['horas_desvio'])} h no total)", "subsecao"),
                self._tabela(cabecalho, linhas, [130, 130, 80, 140, 150, 110], colunas_numericas=range(2, 6)),
                Spacer(1, 3),
                self._p("Ordenados por duração. Lista completa na aba PROG_EVENTOS_DESVIO da planilha.", "legenda"),
                self._legenda_fonte("tab_programacao_eventos"),
            ]))

        ausentes = self.res.programacao["periodo"]["lista_dias_ausentes"]
        if ausentes:
            story.append(Spacer(1, 3))
            story.append(self._p(
                f"Dias sem arquivo de programação no portal do ONS: {escape(fmt_lista(fmt_data(d) for d in ausentes))}.",
                "legenda",
            ))

    def _secao_disponibilidade_sincronizada(self, story: List[Any]) -> None:
        """Disponibilidade operacional e sincronizada do ONS (spec 006, US3; omitida sem os dados)."""
        if not self.res.disponibilidade:
            return
        story.append(CondPageBreak(300))
        story.append(self._titulo_secao("Disponibilidade operacional e sincronizada (ONS)"))
        texto = dict(self.res.achados).get("Disponibilidade sincronizada", "")
        if texto:
            story.append(self._p(escape(texto), "corpo"))

        cabecalho, linhas = linhas_tabela_disponibilidade_anual(self.res)
        if linhas:
            story.append(KeepTogether([
                self._p("Disponibilidade média por ano", "subsecao"),
                self._tabela(cabecalho, linhas, [55, 55, 95, 100, 100, 85, 110, 150], colunas_numericas=range(1, 8)),
                Spacer(1, 3),
                self._p("Médias nas horas comuns à base de EVT e à disponibilidade do ONS. * ano parcial; – = sem apuração "
                        "TEIFa/TEIP no ano.", "legenda"),
                self._legenda_fonte("tab_disponibilidade_anual"),
            ]))
        story += self._figura(
            "disponibilidade_sincronizada",
            "Médias mensais da disponibilidade operacional e sincronizada publicadas pelo ONS e da geração. A operacional "
            "coincide com a disponibilidade declarada da base de EVT; a sincronizada mostra a capacidade das unidades "
            f"ligadas à rede. Linha tracejada: potência instalada ({fmt_num(NOMINAL_INSTALLED_CAPACITY_MW, 0)} MW).",
        )
        cabecalho, linhas = linhas_tabela_disponibilidade_paradas(self.res)
        if linhas:
            story.append(KeepTogether([
                self._p("Horas com a usina parada, por sincronização, EVT e programação do ONS", "subsecao"),
                self._tabela(cabecalho, linhas, [150, 70, 280, 60, 90], colunas_numericas=range(3, 5)),
                Spacer(1, 3),
                self._legenda_fonte("tab_disponibilidade_paradas"),
            ]))
        cabecalho, linhas = linhas_tabela_disponibilidade_divergencias(self.res)
        if linhas:
            story.append(Spacer(1, 6))
            story.append(KeepTogether([
                self._p("Maiores períodos de divergência entre a disponibilidade operacional e a declarada", "subsecao"),
                self._tabela(cabecalho, linhas, [130, 130, 70, 140, 140], colunas_numericas=range(2, 5)),
                Spacer(1, 3),
                self._legenda_fonte("tab_disponibilidade_divergencias"),
            ]))
        story.append(Spacer(1, 3))
        for nota in notas_disponibilidade(self.res):
            story.append(self._p(escape(nota), "legenda"))

    def _secao_hidrologia(self, story: List[Any]) -> None:
        """Afluência, vertimento e nível do reservatório (spec 006, US4; omitida sem os dados)."""
        h = self.res.hidrologia
        if not h:
            return
        story.append(CondPageBreak(300))
        story.append(self._titulo_secao("Afluência, vertimento e nível do reservatório (ONS)"))
        texto = dict(self.res.achados).get("Afluência e vertimento", "")
        if texto:
            story.append(self._p(escape(texto), "corpo"))
        if h["publicado"]:
            cabecalho, linhas = linhas_tabela_faixas_afluencia(self.res)
            if linhas:
                story.append(KeepTogether([
                    self._p("Horas com EVT por faixa de afluência", "subsecao"),
                    self._tabela(cabecalho, linhas, [60, 110, 110, 110, 80, 80, 120], colunas_numericas=range(1, 7)),
                    Spacer(1, 3),
                    self._p("Cabia nas turbinas = afluência até o engolimento máximo da usina. * ano parcial.", "legenda"),
                    self._legenda_fonte("tab_faixas_afluencia"),
                ]))
            cabecalho, linhas = linhas_tabela_faixas_afluencia_evt(self.res)
            if linhas:
                story.append(KeepTogether([
                    self._p("EVT por faixa de afluência (MWh)", "subsecao"),
                    self._tabela(cabecalho, linhas, [60, 110, 110, 110, 80, 80, 120], colunas_numericas=range(1, 7)),
                    Spacer(1, 3),
                    self._p("Energia vertida turbinável das horas de cada faixa. Cabia nas turbinas = parcela da EVT com "
                            "afluência até o engolimento máximo da usina. * ano parcial.", "legenda"),
                    self._legenda_fonte("tab_faixas_afluencia_evt"),
                ]))
            story += self._figura(
                "faixas_afluencia",
                "Horas com energia vertida turbinável por faixa de afluência ao reservatório. Tons de laranja mais escuros "
                "indicam afluência maior; cinza, horas sem dado hidrológico. Número no topo: total de horas com EVT no ano.",
            )
            cabecalho, linhas = linhas_tabela_hidrologia_anual(self.res)
            if linhas:
                story.append(KeepTogether([
                    self._p("Afluência, vazões, nível e volume útil por ano", "subsecao"),
                    self._tabela(cabecalho, linhas, [50, 50, 90, 85, 80, 75, 110, 75, 105], colunas_numericas=range(1, 9)),
                    Spacer(1, 3),
                    self._legenda_fonte("tab_hidrologia_anual"),
                ]))
            story += self._figura(
                "perfil_hidrologico",
                "Médias por hora do dia nos dias com ao menos uma hora de parada com EVT (linhas cheias) e nos demais dias "
                "(tracejadas). Faixa cinza: janela diurna usada no relatório. Valores na aba HID_PERFIL_HORA_DO_DIA.",
            )
        story.append(Spacer(1, 3))
        for nota in notas_hidrologia(self.res):
            story.append(self._p(escape(nota), "legenda"))

    def _secao_cadastro(self, story: List[Any]) -> None:
        """Identificação da usina no cadastro do ONS (spec 006, US6; omitida sem os dados)."""
        if not self.res.cadastro:
            return
        story.append(KeepTogether(self._bloco_chave_valor(
            "Identificação da usina no cadastro do ONS", pares_identificacao_cadastro(self.res), "bloco_cadastro",
            nota=escape(nota_identificacao_cadastro(self.res)),
        )))

    def _secao_geracao_oficial(self, story: List[Any]) -> None:
        """Conferência da geração com a série oficial de geração por usina (spec 006, US5; omitida sem os dados)."""
        if not self.res.geracao_oficial:
            return
        story.append(CondPageBreak(200))
        story.append(self._titulo_secao("Conferência da geração com a série oficial (ONS)"))
        story.append(self._p(escape(texto_conferencia_geracao(self.res)), "corpo"))
        cabecalho, linhas = linhas_tabela_geracao_anual(self.res)
        if linhas:
            story.append(KeepTogether([
                self._tabela(cabecalho, linhas, [60, 110, 130, 100, 130, 130], colunas_numericas=range(1, 6)),
                Spacer(1, 3),
                self._p("* ano parcial. Diferença = série oficial − base de EVT. Coincidência = diferença de até 0,01 MW na "
                        "mesma hora.", "legenda"),
                self._legenda_fonte("tab_geracao_oficial"),
            ]))

    def _secao_geracao_zero(self, story: List[Any]) -> None:
        cabecalho, linhas = linhas_tabela_geracao_zero(self.res)
        larguras = [42] + [40] * 12 + [50, 66, 78]
        escala = LARGURA_UTIL / sum(larguras)
        tabela = self._tabela(cabecalho, linhas, [w * escala for w in larguras], colunas_numericas=range(1, 16))
        texto = next((x for t, x in self.res.achados if t == "Horas com geração zero"), "")
        bloco: List[Any] = [
            self._titulo_secao("Horas com geração zero por mês"),
            tabela,
            Spacer(1, 3),
            self._p(
                "Horas em que val_geracao é exatamente zero. * ano parcial; – = mês sem dados na série. "
                "Com disp. zero = horas com disponibilidade declarada zero (indisponibilidade total); "
                "com usina disponível = demais horas com geração zero.",
                "legenda",
            ),
            self._legenda_fonte("tab_geracao_zero"),
        ]
        if texto:
            bloco.append(self._p(escape(texto), "corpo"))
        story.append(CondPageBreak(260))
        story.append(KeepTogether(bloco))

    def _secao_vazoes(self, story: List[Any]) -> None:
        mc = self.res.mudanca_classificacao
        legenda = (
            "Médias anuais das vazões defluentes (turbinada, vertida turbinável e vertida não turbinável). Linha tracejada: "
            f"engolimento máximo ({NUMERO_UNIDADES_GERADORAS} × {fmt_num(ENGOLIMENTO_NOMINAL_UG_M3S, 1)} m³/s)."
        )
        if mc.get("mes") is not None:
            legenda += (
                f" A parcela não turbinável contínua aparece a partir de {fmt_mes_ano(mc['mes'])}, "
                "quando muda a classificação do vertimento contínuo."
            )
        bloco: List[Any] = [self._titulo_secao("Vazões defluentes por ano")]
        bloco += self._figura("vazoes_defluentes", legenda)
        story.append(CondPageBreak(330))
        story.append(KeepTogether(bloco))

    def _secao_qualidade(self, story: List[Any]) -> None:
        story.append(CondPageBreak(250))
        story.append(self._titulo_secao("Qualidade dos dados"))
        titulo_q, texto_q = next(((t, x) for t, x in self.res.achados if t == "Qualidade dos dados"), ("", ""))
        if texto_q:
            story.append(self._p(escape(texto_q), "corpo"))

        validacao = self.res.validacao
        if len(validacao):
            linhas = [
                [r.codigo_regra, r.grupo, r.nome_regra, fmt_int(r.violacoes),
                 fmt_pct(r.violacoes / r.total_linhas * 100 if r.total_linhas else 0, 3), r.status]
                for r in validacao.itertuples()
            ]
            story.append(self._p("Regras de validação (R1 a R5: consistência interna; R6 a R9: plausibilidade física)", "subsecao"))
            story.append(self._tabela(
                ["Regra", "Grupo", "Descrição", "Registros com violação", "% dos registros", "Status"],
                linhas, [45, 150, 300, 80, 90, 85], colunas_numericas=(3, 4),
            ))
            story.append(Spacer(1, 3))
            story.append(self._legenda_fonte("tab_regras_validacao"))

        extremos = self.res.extremos
        if len(extremos):
            linhas = [
                [r.variavel, r.unidade, fmt_num(r.maximo_historico, 3), fmt_data_hora(r.data_hora_max),
                 fmt_num(r.minimo_historico, 3), fmt_data_hora(r.data_hora_min)]
                for r in extremos.itertuples()
            ]
            bloco = [
                self._p("Extremos do período, excluídos os registros sinalizados", "subsecao"),
                self._tabela(
                    ["Grandeza", "Unidade", "Máximo", "Data/hora do máximo", "Mínimo", "Data/hora do mínimo"],
                    linhas, [190, 80, 90, 130, 90, 130], colunas_numericas=(2, 4),
                ),
                Spacer(1, 3),
                self._legenda_fonte("tab_extremos"),
            ]
            story.append(Spacer(1, 6))
            story.append(KeepTogether(bloco))

    def _secao_notas(self, story: List[Any]) -> None:
        story.append(CondPageBreak(200))
        story.append(self._titulo_secao("Notas metodológicas e limitações"))
        for nota in notas_metodologicas(self.res):
            story.append(self._p(f"• {escape(nota)}", "nota"))

        parametros = self.res.parametros
        linhas = [[r.grupo, r.parametro, r.valor, r.unidade, r.origem] for r in parametros.itertuples()]
        story.append(Spacer(1, 6))
        story.append(CondPageBreak(120))
        story.append(self._p("Parâmetros utilizados", "subsecao"))
        story.append(self._tabela(["Grupo", "Parâmetro", "Valor", "Unidade", "Origem"], linhas, [60, 200, 110, 60, 340]))
        story.append(Spacer(1, 3))
        story.append(self._legenda_fonte("tab_parametros"))

    # ------------------------------------------------------------------
    # Montagem
    # ------------------------------------------------------------------

    def build_pdf(self) -> Path:
        """Compila o relatório completo em PDF."""
        logger.info("Iniciando compilação do relatório em PDF: %s", self.output_pdf)
        self.output_pdf.parent.mkdir(parents=True, exist_ok=True)
        self._secao = 0
        self._desenhados = self._legendas = 0
        c = self.res.cobertura

        cabecalho = (
            f"UHE São Domingos — energia vertida turbinável (dados ONS) · "
            f"{fmt_data(c['inicio'])} a {fmt_data(c['fim'])}"
        )
        # Spec 007 (FR-009): o rodapé cita os conjuntos carregados; a fonte de cada figura e tabela fica na legenda
        rodape = self.rodape = rodape_fontes(self.res, datetime.now())

        doc = SimpleDocTemplate(
            str(self.output_pdf),
            pagesize=landscape(A4),
            leftMargin=MARGEM_LATERAL,
            rightMargin=MARGEM_LATERAL,
            topMargin=MARGEM_SUPERIOR,
            bottomMargin=MARGEM_INFERIOR,
            title="UHE São Domingos — energia vertida turbinável e desempenho operacional",
            subject=f"Análise dos dados abertos do ONS, {fmt_data(c['inicio'])} a {fmt_data(c['fim'])}",
            author="Pipeline de análise UHE São Domingos (dados ONS)",
        )

        story: List[Any] = []
        self._capa(story)
        self._constatacoes(story)
        self._secao_cobertura(story)
        self._secao_cadastro(story)
        self._secao_indicadores(story)
        self._secao_disponibilidade(story)
        self._secao_indicadores_ons(story)
        self._secao_serie_temporal(story)
        self._secao_evt_mensal(story)
        self._secao_perfil_horario(story)
        self._secao_eventos(story)
        self._secao_programacao(story)
        self._secao_disponibilidade_sincronizada(story)
        self._secao_hidrologia(story)
        self._secao_geracao_zero(story)
        self._secao_vazoes(story)
        self._secao_geracao_oficial(story)
        self._secao_qualidade(story)
        self._secao_notas(story)

        doc.build(story, canvasmaker=_canvas_numerado(cabecalho, rodape, self.fonte))
        if self._legendas != self._desenhados:
            logger.warning("PDF com %d tabelas, blocos e figuras e %d legendas de fonte (spec 007).",
                           self._desenhados, self._legendas)
        logger.info("Relatório PDF gerado: %s (%d bytes)", self.output_pdf, self.output_pdf.stat().st_size)
        return self.output_pdf


def main() -> None:
    """Gera o PDF a partir da base tratada e das figuras já existentes."""
    parser = argparse.ArgumentParser(description="Gera o relatório PDF a partir da base tratada e das figuras existentes.")
    parser.add_argument("--log-level", choices=NIVEIS_LOG, default="INFO", help="Nível de log de todos os módulos.")
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level, format="%(asctime)s [%(levelname)s] %(message)s")
    configurar_nivel_log(args.log_level)
    res = analisar(carregar_dados_tratados(), indicadores=carregar_indicadores_processados(),
                   programacao=carregar_programacao_processada(),
                   disponibilidade=carregar_disponibilidade_processada(),
                   hidrologia=carregar_hidrologia_processada(),
                   geracao=carregar_geracao_processada(),
                   cadastro=carregar_cadastro_processado(),
                   dicionarios=carregar_registro_dicionarios())
    out = PDFReportGenerator(res).build_pdf()
    print(f"Relatório PDF gerado com sucesso em: {out}")


if __name__ == "__main__":
    main()
