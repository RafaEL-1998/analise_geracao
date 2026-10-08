"""Relatório a partir dos resultados: Markdown, figuras, listas da conclusão e seções das bases (Geração do relatório)."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from src.analises.conclusao import montar_conclusao
from src.analises.evt import preparar_dados
from src.comum.formatacao import fmt_pct
from src.comum.regras import MAXIMO_ITENS_CONCLUSAO
from src.relatorio.conteudo import (
    linhas_tabela_anual,
    linhas_tabela_ons_disponibilidade,
    linhas_tabela_programacao_mensal,
    listas_conclusao,
)
from src.relatorio.etapa import completar_resultados
from src.relatorio.figuras import gerar_graficos
from src.relatorio.markdown import gerar_relatorio_md
from src.relatorio.pdf import PDFReportGenerator
from tests.analises.test_conclusao import _tudo, df_base  # noqa: F401 (fixture)
from tests.analises.test_indicadores import resultados_com_indicadores  # noqa: F401 (fixture)
from tests.analises.test_programacao import resultados_com_programacao  # noqa: F401 (fixture)
from tests.relatorio.apoio import analisar_com_bases


@pytest.fixture
def resultados(df_sintetico: pd.DataFrame, tmp_path: Path):
    return analisar_com_bases(preparar_dados(df_sintetico), tmp_path / "sem_auditoria.csv",
                              tmp_path / "sem_manifesto.json")


def test_markdown_usa_os_valores_calculados(resultados, tmp_path: Path) -> None:
    """O Markdown traz as linhas da tabela anual e nenhuma conclusão antiga fixa."""
    md = gerar_relatorio_md(resultados, None, tmp_path / "relatorio.md").read_text(encoding="utf-8")
    for proibido in ["96,1%", "Francis", "18/05/2018", "SATISFAT", "cumpre integralmente", "constrained"]:
        assert proibido not in md
    assert fmt_pct(resultados.globais["disponibilidade_relativa_pct"]) in md
    _, linhas = linhas_tabela_anual(resultados)
    for linha in linhas:
        assert f"| {' | '.join(linha)} |" in md


def test_gerar_graficos_so_com_os_resultados(tmp_path: Path, resultados) -> None:
    figuras = gerar_graficos(resultados, tmp_path / "figures", dpi=60)
    assert len(figuras) == 5
    for caminho in figuras.values():
        assert caminho.exists() and caminho.stat().st_size > 1000


def test_limite_de_itens_por_lista_e_secoes_citadas(df_base: pd.DataFrame) -> None:
    res = _tudo(df_base)
    res.conclusao = montar_conclusao(res)
    listas = listas_conclusao(res)
    assert [t for t, _ in listas] == ["Pontos de atenção", "Possíveis problemas", "A confirmar com o agente",
                                      "A verificar em campo"]
    for _, textos in listas:
        assert 1 <= len(textos) <= MAXIMO_ITENS_CONCLUSAO
        assert all(re.search(r"\(seç(ão|ões) [\d, e]+\)\.$", t) for t in textos), textos


def test_relatorios_com_indicadores(resultados_com_indicadores, tmp_path: Path) -> None:
    res = completar_resultados(resultados_com_indicadores)
    md = gerar_relatorio_md(res, None, tmp_path / "relatorio.md").read_text(encoding="utf-8")
    assert "## 3. Disponibilidade e geração por ano" in md
    assert "## 4. Indicadores oficiais do ONS por unidade geradora" in md
    assert "### Períodos de indisponibilidade total" in md
    _, linhas = linhas_tabela_ons_disponibilidade(res)
    for linha in linhas:
        assert f"| {' | '.join(linha)} |" in md

    saida = PDFReportGenerator(res, {}, tmp_path / "relatorio.pdf").build_pdf()
    assert saida.read_bytes()[:5] == b"%PDF-"


def test_analise_sem_indicadores_mantem_o_relatorio_anterior(df_sintetico: pd.DataFrame, tmp_path: Path) -> None:
    res = analisar_com_bases(preparar_dados(df_sintetico), tmp_path / "a.csv", tmp_path / "m.json")
    assert res.ons == {}
    assert len(res.achados) == 12
    md = gerar_relatorio_md(res, None, tmp_path / "relatorio.md").read_text(encoding="utf-8")
    assert "Indicadores oficiais do ONS" not in md
    assert "## 3. Disponibilidade e geração por ano" in md
    assert "### Períodos de indisponibilidade total" in md


def test_relatorios_com_programacao(resultados_com_programacao, tmp_path: Path) -> None:
    res = completar_resultados(resultados_com_programacao)
    md = gerar_relatorio_md(res, None, tmp_path / "relatorio.md").read_text(encoding="utf-8")
    assert "Operação verificada e programação diária do ONS" in md
    _, linhas = linhas_tabela_programacao_mensal(res)
    for linha in linhas:
        assert f"| {' | '.join(linha)} |" in md
    assert "20/01/2024" in md  # dia sem arquivo listado
    saida = PDFReportGenerator(res, {}, tmp_path / "relatorio.pdf").build_pdf()
    assert saida.read_bytes()[:5] == b"%PDF-"
