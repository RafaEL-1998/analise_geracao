"""Estrutura do relatório (spec da Geração do relatório, US2): seções em ordem, constatação → seção, sumário, PDF e Markdown iguais."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List

import pandas as pd
import pytest

from src.analises.evt import preparar_dados
from src.relatorio.estrutura import (
    COM_EVT,
    MAPA_CONSTATACOES,
    SECOES,
    SEM_EVT,
    constatacoes_da_secao,
    secoes_presentes,
    sumario,
)
from src.relatorio.figuras import gerar_graficos
from src.relatorio.markdown import gerar_relatorio_md
from tests.relatorio.apoio import analisar_com_bases
from tests.relatorio.test_complementar import _ficha, _geracao, _hidrologia, _serie_disponibilidade

CHAVES = ["cobertura", "indicadores_anuais", "disponibilidade_geracao", "indicadores_ons", "serie_temporal",
          "evt_mensal", "perfil_horario", "eventos", "programacao", "disponibilidade_sincronizada", "hidrologia",
          "geracao_zero", "vazoes", "geracao_oficial", "qualidade", "conclusao", "notas"]
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
    return analisar_com_bases(df, disponibilidade=_serie_disponibilidade(df), hidrologia=_hidrologia(df),
                    geracao=_geracao(df, divergente=True), cadastro=_ficha(potencia=47.5))


def test_secoes_em_ordem() -> None:
    """A hidrelétrica com EVT tem exatamente as 17 seções de hoje, na ordem de hoje (plano da Geração do relatório,
    D15 e D17)."""
    assert [s.chave for s in SECOES if COM_EVT in s.caminhos] == CHAVES
    assert SECOES[0].titulo == "Fonte e cobertura dos dados" and SECOES[-1].titulo == "Notas metodológicas e limitações"


def test_numeracao_sem_lacunas(df_base: pd.DataFrame) -> None:
    so_evt = secoes_presentes(analisar_com_bases(df_base))
    assert [n for n, _ in so_evt] == list(range(1, 13))
    assert {s.chave for _, s in so_evt}.isdisjoint({"indicadores_ons", "programacao",
                                                    "disponibilidade_sincronizada", "hidrologia", "geracao_oficial"})
    completo = secoes_presentes(_completo(df_base))
    assert [n for n, _ in completo] == list(range(1, 16))
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
    res = analisar_com_bases(df_base)
    res.achados = [*res.achados, ("Constatação nova", "texto")]
    with caplog.at_level(logging.WARNING):
        assert ("Constatação nova", "texto") in constatacoes_da_secao(res, "cobertura")
    assert any("Constatação nova" in r.getMessage() for r in caplog.records)


def _secoes_md(md: str) -> List[str]:
    return re.findall(r"^## \d+\. (.+)$", md, flags=re.M)


def test_conteudo_compartilhado(df_base: pd.DataFrame) -> None:
    """Indicadores, blocos, legendas das figuras e textos das tabelas usados pelo PDF e pelo Markdown."""
    from src.relatorio import conteudo as a
    from src.relatorio.fontes import MAPA_FONTES

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
    figuras = gerar_graficos(res, tmp_path / "figuras", dpi=40)
    return gerar_relatorio_md(res, figuras, tmp_path / "relatorio.md").read_text(encoding="utf-8"), figuras


def test_capa_do_markdown(df_base: pd.DataFrame, tmp_path: Path) -> None:
    """US2 (capa): título, data de geração, indicadores principais e sumário com links; nenhuma constatação na capa."""
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
    from src.relatorio.pdf import PDFReportGenerator

    res = _completo(df_base) if com_bases else analisar_com_bases(df_base)
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
    """US2 (FR-011 a FR-013): capa e sumário só na página 1. Paginação: tabela longa continua na página seguinte com o
    cabeçalho repetido, em vez de saltar inteira; figura com altura limitada, para caber com o título e as constatações."""
    from reportlab.platypus import CondPageBreak, Image, KeepTogether, Table

    from src.relatorio.pdf import ALTURA_MAXIMA_FIGURA, LINHAS_TABELA_INTEIRA, PDFReportGenerator

    res = _completo(df_base)
    figuras = gerar_graficos(res, tmp_path / "figuras", dpi=40)
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
    """FR-012: a ficha do cadastro vai para a capa, sem a data da consulta; a seção do cadastro
    sai; a constatação do cadastro (só com divergência) fica na seção de cobertura; a capa continua numa página."""
    from src.relatorio.pdf import PDFReportGenerator

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

    sem_cadastro, _ = _md(analisar_com_bases(df_base), df_base, tmp_path / "sem")
    assert "### Cadastro no ONS" not in sem_cadastro


def test_figuras_padronizadas_na_largura_util(df_base: pd.DataFrame, tmp_path: Path) -> None:
    """FR-036: série temporal, EVT mensal, disponibilidade sincronizada e vazões defluentes com o mesmo
    tamanho de PNG e, no PDF, com a mesma largura e altura, na largura útil da página."""
    from reportlab.platypus import Image
    from reportlab.lib.utils import ImageReader

    from src.relatorio.pdf import ALTURA_MAXIMA_FIGURA, FIGURAS_PADRONIZADAS, LARGURA_UTIL, PDFReportGenerator

    assert set(FIGURAS_PADRONIZADAS) == {"serie_temporal", "evt_mensal", "disponibilidade_sincronizada",
                                         "vazoes_defluentes"}
    res = _completo(df_base)
    figuras = gerar_graficos(res, tmp_path / "figuras", dpi=40)
    assert len({ImageReader(str(figuras[c])).getSize() for c in FIGURAS_PADRONIZADAS}) == 1
    gerador = PDFReportGenerator(res, figuras, tmp_path / "relatorio.pdf")
    tamanhos = {(round(i.drawWidth), round(i.drawHeight)) for c in FIGURAS_PADRONIZADAS
                for i in gerador._figura(c, "legenda") if isinstance(i, Image)}
    assert len(tamanhos) == 1
    largura, altura = tamanhos.pop()
    assert largura == round(LARGURA_UTIL - 10) and altura > ALTURA_MAXIMA_FIGURA


def test_conclusao_no_relatorio(df_base: pd.DataFrame, tmp_path: Path) -> None:
    """Spec da Geração do relatório (US4): seção "Conclusão" antes das notas, no PDF, no Markdown, no sumário e na planilha."""
    from src.analises.conclusao import FRASE_ABERTURA_CONCLUSAO, montar_conclusao
    from src.relatorio.conteudo import notas_metodologicas
    from src.relatorio.planilha import exportar_tabelas
    from src.comum.regras import MAXIMO_ITENS_CONCLUSAO
    from src.relatorio.pdf import PDFReportGenerator
    from tests.analises.test_conclusao import _anomalias

    res = _completo(df_base)  # bases completas, para as figuras e as seções; números que disparam as quatro listas
    res.globais.update(evt_parada_pct=28.4, evt_parada_mwh=41_900.0, horas_parada_com_evt=2141,
                       desvio_disponibilidade_referencia_pp=-3.2, disponibilidade_relativa_pct=87.8,
                       disponibilidade_referencia_pct=91.0, geracao_sobre_garantia_fisica_pct=74.4)
    res.indicadores_anuais = res.indicadores_anuais.assign(razao_evt_diurna_noturna=5.5,
                                                           razao_geracao_diurna_noturna=0.6)
    res.resumo_anomalias = _anomalias(res, r7=293, r9=63)
    res.conclusao = montar_conclusao(res)
    assert [s.chave for _, s in secoes_presentes(res)][-2:] == ["conclusao", "notas"]
    assert any(t == "Conclusão" for _, t in sumario(res))

    md, figuras = _md(res, df_base, tmp_path)
    corpo = re.split(r"^## \d+\. Conclusão$", md, flags=re.M)[1].split("\n## ")[0]
    assert FRASE_ABERTURA_CONCLUSAO in corpo
    titulos = re.findall(r"^### (.+)$", corpo, flags=re.M)
    assert titulos == ["Pontos de atenção", "Possíveis problemas", "A confirmar com o agente", "A verificar em campo"]
    for bloco in re.split(r"^### .+$", corpo, flags=re.M)[1:]:
        itens = [l for l in bloco.splitlines() if l.startswith("- ")]
        assert 1 <= len(itens) <= MAXIMO_ITENS_CONCLUSAO
        assert all(re.search(r"\(seç(ão|ões) [\d, e]+\)\.$", l) for l in itens), itens

    gerador = PDFReportGenerator(res, figuras, tmp_path / "relatorio.pdf")
    gerador.build_pdf()
    assert gerador.titulos_secoes[-2:] == ["Conclusão", "Notas metodológicas e limitações"]
    p = gerador.paginas_secoes
    assert p["Notas metodológicas e limitações"] - p["Conclusão"] <= 1  # a conclusão cabe em uma página

    xlsx, _ = exportar_tabelas(res, tmp_path / "tabelas.xlsx", tmp_path / "tabelas.csv")
    abas = pd.read_excel(xlsx, sheet_name=None)
    conclusao = abas["CONCLUSAO"]
    assert list(conclusao.columns) == ["lista", "ordem", "regra", "texto", "secoes"]
    assert len(conclusao) == len(res.conclusao)  # todos os itens, inclusive os que passam do limite
    fontes = abas["FONTES"].set_index("aba")
    assert fontes.loc["CONCLUSAO", "calculado_no_relatorio"] == "sim"
    assert any(n.startswith("Conclusão:") and "10%" in n for n in notas_metodologicas(res))


def test_figura_opcional_de_execucao_anterior_sai_da_pasta(tmp_path: Path, monkeypatch) -> None:
    """Spec da Geração do relatório (FR-003): figures/ só com as figuras desta execução."""
    from types import SimpleNamespace

    from src.relatorio import figuras

    def grava(res, caminho, dpi):
        caminho.write_bytes(b"png")

    for nome in ("_grafico_serie_temporal", "_grafico_evt_mensal", "_grafico_perfil_horario",
                 "_grafico_disponibilidade_anual", "_grafico_vazoes_defluentes"):
        monkeypatch.setattr(figuras, nome, grava)
    monkeypatch.setattr(figuras, "_GERADORES_OPCIONAIS",
                        {chave: (grava, lambda res: False) for chave in figuras.NOMES_FIGURAS_OPCIONAIS})
    antiga = tmp_path / figuras.NOMES_FIGURAS_OPCIONAIS["faixas_afluencia"]
    antiga.write_bytes(b"figura antiga")
    caminhos = figuras.gerar_graficos(SimpleNamespace(), tmp_path)
    assert not antiga.exists() and len(caminhos) == 5
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(figuras.NOMES_FIGURAS.values())


# ---------------------------------------------------------------------------
# Usinas sem EVT (plano da Geração do relatório, D15 e D16; data-model da Geração do relatório, seção 2.9)
# ---------------------------------------------------------------------------

SECOES_UTE = ["fonte_cobertura", "anuais_comum", "disponibilidade_geracao_comum", "serie_temporal_comum",
              "geracao_mensal", "perfil_horario_comum", "disponibilidade_sincronizada_comum", "qualidade_comum",
              "conclusao", "notas_comum"]
# FR-048: a PCH em conjunto sem série própria em duas partes, a usina e, antes da conclusão, o
# conjunto, com as seções dos números do conjunto como subseções
SECOES_PCH = ["fonte_cobertura", "usina_no_conjunto", "qualidade_comum", "parte_conjunto", "conclusao", "notas_comum"]


@pytest.fixture(scope="module")
def sem_evt_gerados(tmp_path_factory):
    """As duas usinas fictícias sem EVT, da Coleta ao relatório, com os perfis para reativar nos testes."""
    from src.comum.perfil import carregar_perfil
    from tests.fixtures.sem_evt import projeto_sem_evt

    raiz = tmp_path_factory.mktemp("projeto")
    usinas = projeto_sem_evt(raiz, ["coleta", "tratamento", "conferencia", "analises", "relatorio"])
    for slug, u in usinas.items():
        u["perfil"] = carregar_perfil(slug, raiz)
        u["relatorio"] = raiz / "reports" / slug
        u["md"] = (u["relatorio"] / "relatorio_analise_estatistica.md").read_text(encoding="utf-8")
    return usinas


def _resultados_sem_evt(u):
    from src.analises.resultados import carregar_resultados
    from src.comum.perfil import definir_perfil_ativo
    from src.relatorio.etapa import completar_resultados

    definir_perfil_ativo(u["perfil"])  # a fixture automática volta à São Domingos no fim do teste
    return completar_resultados(carregar_resultados(u["pasta"] / "analises" / "resultados.pkl"))


@pytest.mark.parametrize("slug, esperadas", [("ute_beta", SECOES_UTE), ("pch_alfa", SECOES_PCH)])
def test_usina_sem_evt_segue_a_tabela_da_decisao_r14(sem_evt_gerados, slug: str, esperadas: List[str]) -> None:
    u = sem_evt_gerados[slug]
    assert u["codigos"]["relatorio"] == 0, u["manifestos"]
    res = _resultados_sem_evt(u)
    presentes = secoes_presentes(res)
    assert [s.chave for _, s in presentes] == esperadas
    assert [n for n, _ in presentes] == list(range(1, len(esperadas) + 1))
    assert all(SEM_EVT in s.caminhos for _, s in presentes)
    assert [s.chave for _, s in presentes if COM_EVT in s.caminhos] == ["conclusao"]  # a única dos dois caminhos
    assert _secoes_md(u["md"]) == [titulo for _, titulo in sumario(res)]


def test_caminho_da_evt_sem_as_secoes_novas(df_base: pd.DataFrame) -> None:
    res = _completo(df_base)
    assert all(COM_EVT in s.caminhos for _, s in secoes_presentes(res))
    novas = {s.chave for s in SECOES if SEM_EVT in s.caminhos and COM_EVT not in s.caminhos}
    assert novas.isdisjoint(s.chave for _, s in secoes_presentes(res))


def test_titulo_e_capa_por_caminho(sem_evt_gerados, df_base: pd.DataFrame, tmp_path: Path) -> None:
    from src.relatorio.conteudo import titulo_capa_relatorio
    from src.relatorio.figuras_comum import NOMES_FIGURAS_COMUM
    from src.relatorio.pdf import PDFReportGenerator

    # na hidrelétrica com EVT (perfil ativo da São Domingos), os títulos de hoje
    md_uhe, _ = _md(_completo(df_base), df_base, tmp_path)
    assert md_uhe.startswith("# UHE São Domingos — energia vertida turbinável e desempenho operacional (dados ONS)")
    assert titulo_capa_relatorio() == "UHE São Domingos — Análise do desempenho operacional"
    u = sem_evt_gerados["pch_alfa"]
    capa = u["md"].split("\n## 1. ")[0]
    assert capa.startswith("# PCH ALFA — Análise do desempenho operacional\n")
    assert "série de referência, Geração por usina (conjunto de usinas, id ONS CJU_GOCJA)" in capa
    assert "| Tipo · modalidade | PCH · TIPO II-C |" in capa
    assert "| Conjunto de usinas | CJU_GOCJA (CONJ. HIDRAULICO ALFA) |" in capa
    assert "| Geração média do conjunto CONJ. HIDRAULICO ALFA | 20,0 MWmed |" in capa
    assert "cod_usina" not in capa and "Engolimento" not in capa  # sem os blocos hidráulicos da EVT
    res = _resultados_sem_evt(u)
    figuras = {chave: u["relatorio"] / "figures" / nome for chave, nome in NOMES_FIGURAS_COMUM.items()}
    gerador = PDFReportGenerator(res, figuras, tmp_path / "pch.pdf")
    gerador.build_pdf()
    assert gerador.titulos_secoes == _secoes_md(u["md"])
    assert "energia vertida" not in gerador.subtitulo_capa.lower()
    assert gerador._legendas == gerador._desenhados  # cada tabela, bloco e figura com a legenda de fonte
    assert sorted(gerador.constatacoes_emitidas) == sorted(t for t, _ in res.achados)


def test_legendas_com_o_identificador_e_o_nivel(sem_evt_gerados) -> None:
    pch, ute = sem_evt_gerados["pch_alfa"]["md"], sem_evt_gerados["ute_beta"]["md"]
    assert "Geração por usina (conjunto de usinas, id ONS CJU_GOCJA)" in pch
    assert "Geração por usina (id ONS GOUTEB)" in ute and "conjunto de usinas" not in ute
    for md in (pch, ute):
        assert "Energia Vertida Turbinável (cod_usina" not in md  # a EVT não é fonte de nada nas usinas sem EVT
        assert "não feita nesta execução" not in md


def test_notas_com_omissoes_niveis_e_nao_aplicaveis(sem_evt_gerados, df_base: pd.DataFrame, tmp_path: Path) -> None:
    pch, ute = sem_evt_gerados["pch_alfa"]["md"], sem_evt_gerados["ute_beta"]["md"]
    notas_pch = pch.split("Notas metodológicas e limitações\n")[-1]
    notas_ute = ute.split("Notas metodológicas e limitações\n")[-1]
    for notas in (notas_pch, notas_ute):
        assert "### Seções e regras sem base para a usina" in notas
        assert "### Conferências que não se aplicam à usina" in notas and "### Parâmetros utilizados" in notas
    assert "Granularidade: o ONS publica a geração do conjunto CONJ. HIDRAULICO ALFA" in notas_pch
    assert "Granularidade" not in notas_ute  # o parágrafo só entra com número do conjunto (D16)
    assert ("| Disponibilidade operacional e sincronizada | sem a Disponibilidade por usina (cobertura: ausente) |"
            in notas_pch)
    # na hidrelétrica com EVT, as notas de hoje, sem as tabelas novas
    md_uhe, _ = _md(_completo(df_base), df_base, tmp_path)
    assert "Granularidade" not in md_uhe and "Seções e regras sem base" not in md_uhe
    assert "Conferências que não se aplicam" not in md_uhe


def test_granularidade_com_a_geracao_da_usina_e_a_programacao_do_conjunto(sem_evt_gerados) -> None:
    """Bug nota-granularidade-conjunto: a nota cita a Programação diária do conjunto, com os códigos, e não diz que a
    geração é do conjunto (homologação de 26/10/2026: PCH Dreher e Kotzian, UTE Eldorado e Santa Luzia I)."""
    from src.relatorio.comum import notas

    res = _resultados_sem_evt(sem_evt_gerados["ute_beta"])
    res.niveis["programacao"] = {"nivel": "conjunto", "identificador": "GOCJU-1; GOCJU-2"}
    texto = next(n for n in notas(res) if n.startswith("Granularidade"))
    assert texto.startswith("Granularidade: a geração é a da própria usina, mas o ONS publica a Programação diária "
                            "(GOCJU-1; GOCJU-2) do conjunto, e não da usina isolada.")
    assert "publica a geração do conjunto" not in texto and "()" not in texto
