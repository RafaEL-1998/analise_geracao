"""Estrutura do relatório (spec 008): seções em ordem, constatação → seção, sumário, PDF e Markdown iguais."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List

import pandas as pd
import pytest

from src.analyzer import analisar, gerar_graficos, gerar_relatorio_md, preparar_dados
from src.estrutura_relatorio import MAPA_CONSTATACOES, SECOES, constatacoes_da_secao, secoes_presentes, sumario
from tests.test_relatorio_complementar import _ficha, _geracao, _hidrologia, _serie_disponibilidade

CHAVES = ["cobertura", "indicadores_anuais", "disponibilidade_geracao", "indicadores_ons", "serie_temporal",
          "evt_mensal", "perfil_horario", "eventos", "programacao", "disponibilidade_sincronizada", "hidrologia",
          "geracao_zero", "vazoes", "geracao_oficial", "qualidade", "notas"]
TITULOS_CONSTATACOES = {
    "Cobertura dos dados", "Cadastro da usina no ONS", "Disponibilidade", "Indicadores oficiais de disponibilidade (ONS)",
    "Estados operativos das unidades geradoras (ONS)", "Indisponibilidades", "Geração e garantia física",
    "Energia vertida turbinável", "EVT e nível de geração", "EVT com a usina parada", "Programação diária do ONS",
    "Disponibilidade sincronizada", "Afluência e vertimento", "Horas com geração zero", "Concentração diurna",
    "Distribuição ao longo do ano", "Mudança de classificação do vertimento pelo ONS", "Conferência da geração",
    "Qualidade dos dados",
}


@pytest.fixture
def df_base(df_sintetico: pd.DataFrame) -> pd.DataFrame:
    return preparar_dados(df_sintetico)


def _completo(df: pd.DataFrame):
    """Resultados com as bases novas e com as constatações condicionais (divergências)."""
    return analisar(df, disponibilidade=_serie_disponibilidade(df), hidrologia=_hidrologia(df),
                    geracao=_geracao(df, divergente=True), cadastro=_ficha(potencia=47.5))


def test_secoes_em_ordem() -> None:
    assert [s.chave for s in SECOES] == CHAVES
    assert SECOES[0].titulo == "Fonte e cobertura dos dados" and SECOES[-1].titulo == "Notas metodológicas e limitações"


def test_numeracao_sem_lacunas(df_base: pd.DataFrame) -> None:
    so_evt = secoes_presentes(analisar(df_base))
    assert [n for n, _ in so_evt] == list(range(1, 12))
    assert {s.chave for _, s in so_evt}.isdisjoint({"indicadores_ons", "programacao",
                                                    "disponibilidade_sincronizada", "hidrologia", "geracao_oficial"})
    completo = secoes_presentes(_completo(df_base))
    assert [n for n, _ in completo] == list(range(1, 15))
    assert sumario(_completo(df_base)) == [(n, s.titulo) for n, s in completo]


def test_mapa_cobre_todas_as_constatacoes(df_base: pd.DataFrame) -> None:
    assert set(MAPA_CONSTATACOES) == TITULOS_CONSTATACOES
    assert set(MAPA_CONSTATACOES.values()) <= set(CHAVES)
    res = _completo(df_base)
    assert {t for t, _ in res.achados} <= set(MAPA_CONSTATACOES)


def test_cada_constatacao_em_uma_secao_na_ordem(df_base: pd.DataFrame) -> None:
    res = _completo(df_base)
    distribuidas = [c for _, s in secoes_presentes(res) for c in constatacoes_da_secao(res, s.chave)]
    assert sorted(distribuidas) == sorted(res.achados)
    ordem = [t for t, _ in res.achados]
    evt = [t for t, _ in constatacoes_da_secao(res, "evt_mensal")]
    assert evt == sorted(evt, key=ordem.index)


def test_constatacao_orfa_vai_para_cobertura(df_base: pd.DataFrame, caplog) -> None:
    res = analisar(df_base)
    res.achados = [*res.achados, ("Constatação nova", "texto")]
    with caplog.at_level(logging.WARNING):
        assert ("Constatação nova", "texto") in constatacoes_da_secao(res, "cobertura")
    assert any("Constatação nova" in r.getMessage() for r in caplog.records)


def _secoes_md(md: str) -> List[str]:
    return re.findall(r"^## \d+\. (.+)$", md, flags=re.M)


def test_conteudo_compartilhado(df_base: pd.DataFrame) -> None:
    """T005: indicadores, blocos, legendas das figuras e textos das tabelas usados pelo PDF e pelo Markdown."""
    from src import analyzer as a
    from src.fontes_relatorio import MAPA_FONTES

    res = _completo(df_base)
    tiles, nota = a.indicadores_capa(res)
    assert len(tiles) >= 4 and nota
    assert a.pares_identificacao(res)[0][0] == "cod_usina" and a.pares_parametros() and a.pares_cobertura(res)
    for chave in ("disponibilidade_anual", "serie_temporal", "evt_mensal", "perfil_horario", "vazoes_defluentes",
                  "disponibilidade_sincronizada", "faixas_afluencia", "perfil_hidrologico"):
        assert a.legenda_figura(res, chave), chave
    assert set(a.textos_tabelas(res)) <= set(MAPA_FONTES)
    for funcao in (a.linhas_tabela_eventos_indisponibilidade, a.linhas_tabela_evt_por_nivel, a.linhas_tabela_eventos_parada,
                   a.linhas_tabela_perfil_diurno, a.linhas_tabela_regras, a.linhas_tabela_registros_sinalizados,
                   a.linhas_tabela_extremos, a.linhas_tabela_parametros):
        cabecalho, linhas = funcao(res)
        assert cabecalho and all(len(l) == len(cabecalho) for l in linhas), funcao.__name__


def _md(res, df: pd.DataFrame, tmp_path: Path):
    figuras = gerar_graficos(df, res, tmp_path / "figuras", dpi=40)
    return gerar_relatorio_md(res, figuras, tmp_path / "relatorio.md").read_text(encoding="utf-8"), figuras


def test_capa_do_markdown(df_base: pd.DataFrame, tmp_path: Path) -> None:
    """US1: título, data de geração, indicadores principais e sumário com links; nenhuma constatação na capa."""
    res = _completo(df_base)
    md, _ = _md(res, df_base, tmp_path)
    capa = md.split("\n## 1. ")[0]
    assert "**Gerado em**:" in capa and "### Indicadores principais" in capa and "## Sumário" in capa
    for n, titulo in sumario(res):
        assert f"{n}. [{titulo}](#" in capa
    assert all(texto not in capa for _, texto in res.achados)
    assert "**Fontes**:" not in md


@pytest.mark.parametrize("com_bases", [False, True])
def test_cada_constatacao_uma_vez_e_mesma_estrutura(df_base: pd.DataFrame, tmp_path: Path, com_bases: bool) -> None:
    """US2: cada constatação uma vez, no início da sua seção; PDF e Markdown com as mesmas seções e tabelas."""
    from src.pdf_generator import PDFReportGenerator

    res = _completo(df_base) if com_bases else analisar(df_base)
    md, figuras = _md(res, df_base, tmp_path)
    partes = re.split(r"^## \d+\. ", md, flags=re.M)[1:]
    corpos = {p.partition("\n")[0].strip(): p.partition("\n")[2] for p in partes}
    titulo_da_secao = {s.chave: s.titulo for _, s in secoes_presentes(res)}
    for chave in titulo_da_secao:
        corpo = corpos[titulo_da_secao[chave]]
        conteudo = [i for i in (corpo.find("| ---"), corpo.find("![")) if i >= 0]
        for _, texto in constatacoes_da_secao(res, chave):
            assert md.count(texto) == 1
            assert corpo.index(texto) < min(conteudo, default=len(corpo))
    assert "Figuras" not in corpos and md.count("![") == len(figuras)
    assert "### Regras de validação" in md and "### Parâmetros utilizados" in md

    gerador = PDFReportGenerator(res, figuras, tmp_path / "relatorio.pdf")
    gerador.build_pdf()
    assert sorted(gerador.constatacoes_emitidas) == sorted(t for t, _ in res.achados)
    assert gerador.titulos_secoes == _secoes_md(md)
    assert "tab_registros_sinalizados" in gerador.legendas_emitidas
    if res.hidrologia:
        assert "tab_hidrologia_perfil" in gerador.legendas_emitidas


def test_pdf_capa_numa_pagina_e_paginacao_enxuta(df_base: pd.DataFrame, tmp_path: Path) -> None:
    """US1 (FR-001): capa e sumário só na página 1. Paginação: tabela longa continua na página seguinte com o
    cabeçalho repetido, em vez de saltar inteira; figura com altura limitada, para caber com o título e as constatações."""
    from reportlab.platypus import CondPageBreak, Image, KeepTogether, Table

    from src.pdf_generator import ALTURA_MAXIMA_FIGURA, LINHAS_TABELA_INTEIRA, PDFReportGenerator

    res = _completo(df_base)
    figuras = gerar_graficos(df_base, res, tmp_path / "figuras", dpi=40)
    gerador = PDFReportGenerator(res, figuras, tmp_path / "relatorio.pdf")
    gerador.build_pdf()
    assert gerador.sumario_entradas[0][2] == 2

    cabecalho = ["a", "b"]
    curta = gerador._bloco_tabela("tab_parametros", cabecalho, [["1", "2"]] * LINHAS_TABELA_INTEIRA, [100, 100])
    assert len(curta) == 1 and isinstance(curta[0], KeepTogether)
    longa = gerador._bloco_tabela("tab_parametros", cabecalho, [["1", "2"]] * (LINHAS_TABELA_INTEIRA + 1), [100, 100])
    assert isinstance(longa[0], CondPageBreak) and any(isinstance(f, Table) and f.repeatRows == 1 for f in longa)
    imagens = [f for f in gerador._figura("perfil_horario", "legenda") if isinstance(f, Image)]
    assert imagens and imagens[0].drawHeight <= ALTURA_MAXIMA_FIGURA


def test_ficha_do_cadastro_na_capa_e_sem_secao_propria(df_base: pd.DataFrame, tmp_path: Path) -> None:
    """Revisão de 07/10/2026 (FR-015): a ficha do cadastro vai para a capa, sem a data da consulta; a seção do cadastro
    sai; a constatação do cadastro (só com divergência) fica na seção de cobertura; a capa continua numa página."""
    from src.pdf_generator import PDFReportGenerator

    assert MAPA_CONSTATACOES["Cadastro da usina no ONS"] == "cobertura"
    res = _completo(df_base)
    texto = dict(res.achados)["Cadastro da usina no ONS"]
    assert ("Cadastro da usina no ONS", texto) in constatacoes_da_secao(res, "cobertura")
    md, figuras = _md(res, df_base, tmp_path)
    capa, corpo = md.split("\n## 1. ", 1)
    assert "### Cadastro no ONS" in capa and "| Modalidade de operação | TIPO II-A |" in capa
    assert "Data da consulta" not in md and "Identificação da usina no cadastro do ONS" not in md
    assert texto in corpo.split("\n## 2. ")[0]
    gerador = PDFReportGenerator(res, figuras, tmp_path / "relatorio.pdf")
    gerador.build_pdf()
    assert "bloco_cadastro" in gerador.legendas_emitidas
    assert "Identificação da usina no cadastro do ONS" not in gerador.titulos_secoes
    assert gerador.sumario_entradas[0][2] == 2

    sem_cadastro, _ = _md(analisar(df_base), df_base, tmp_path / "sem")
    assert "### Cadastro no ONS" not in sem_cadastro


def test_figuras_padronizadas_na_largura_util(df_base: pd.DataFrame, tmp_path: Path) -> None:
    """Revisão 2 (FR-016): série temporal, EVT mensal, disponibilidade sincronizada e vazões defluentes com o mesmo
    tamanho de PNG e, no PDF, com a mesma largura e altura, na largura útil da página."""
    from reportlab.platypus import Image
    from reportlab.lib.utils import ImageReader

    from src.pdf_generator import ALTURA_MAXIMA_FIGURA, FIGURAS_PADRONIZADAS, LARGURA_UTIL, PDFReportGenerator

    assert set(FIGURAS_PADRONIZADAS) == {"serie_temporal", "evt_mensal", "disponibilidade_sincronizada",
                                         "vazoes_defluentes"}
    res = _completo(df_base)
    figuras = gerar_graficos(df_base, res, tmp_path / "figuras", dpi=40)
    assert len({ImageReader(str(figuras[c])).getSize() for c in FIGURAS_PADRONIZADAS}) == 1
    gerador = PDFReportGenerator(res, figuras, tmp_path / "relatorio.pdf")
    tamanhos = {(round(i.drawWidth), round(i.drawHeight)) for c in FIGURAS_PADRONIZADAS
                for i in gerador._figura(c, "legenda") if isinstance(i, Image)}
    assert len(tamanhos) == 1
    largura, altura = tamanhos.pop()
    assert largura == round(LARGURA_UTIL - 10) and altura > ALTURA_MAXIMA_FIGURA
