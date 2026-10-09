"""Testes automatizados para o gerador de relatórios em PDF."""

from pathlib import Path

from src.analises.evt import preparar_dados
from src.relatorio.figuras import gerar_graficos
from src.relatorio.pdf import PDFReportGenerator
from tests.relatorio.apoio import analisar_com_bases


def test_pdf_gerado_a_partir_dos_resultados(tmp_path: Path, df_sintetico) -> None:
    """O PDF é montado a partir de ResultadosAnalise e das figuras geradas."""
    df = preparar_dados(df_sintetico)
    res = analisar_com_bases(df, tmp_path / "sem_auditoria.csv")
    figuras = gerar_graficos(res, tmp_path / "figures", dpi=60)

    saida = PDFReportGenerator(res, figuras, tmp_path / "relatorio.pdf").build_pdf()

    assert saida.exists()
    assert saida.read_bytes()[:5] == b"%PDF-"
    assert saida.stat().st_size > 10_000


def test_pdf_sem_figuras_nao_falha(tmp_path: Path, df_sintetico) -> None:
    """Figuras ausentes geram aviso no documento em vez de erro."""
    df = preparar_dados(df_sintetico)
    res = analisar_com_bases(df, tmp_path / "sem_auditoria.csv")

    saida = PDFReportGenerator(res, {}, tmp_path / "relatorio.pdf").build_pdf()

    assert saida.exists()


def test_pdf_toda_tabela_e_figura_tem_legenda_de_fonte(tmp_path: Path, df_sintetico) -> None:
    """Spec da Geração do relatório (FR-023): cada tabela, bloco e figura desenhados no PDF ganha a legenda de fonte."""
    df = preparar_dados(df_sintetico)
    res = analisar_com_bases(df, tmp_path / "sem_auditoria.csv")
    figuras = gerar_graficos(res, tmp_path / "figures", dpi=50)
    gerador = PDFReportGenerator(res, figuras, tmp_path / "relatorio.pdf")
    gerador.build_pdf()
    assert gerador._desenhados > 0 and gerador._legendas == gerador._desenhados


def test_rodape_so_com_a_numeracao() -> None:
    """Spec da Geração do relatório (FR-015): o rodapé não tem frase de fontes nem data; só "Página X de Y"."""
    import inspect

    import src.relatorio.pdf as pdf

    assert list(inspect.signature(pdf._canvas_numerado).parameters) == ["cabecalho", "fonte"]


def test_capa_com_data_e_sumario_com_paginas(tmp_path: Path, df_sintetico) -> None:
    """Spec da Geração do relatório (US2): "Gerado em" na capa; sumário com todas as seções presentes e a página real de cada uma."""
    from src.relatorio.estrutura import sumario

    df = preparar_dados(df_sintetico)
    res = analisar_com_bases(df, tmp_path / "sem_auditoria.csv")
    gerador = PDFReportGenerator(res, gerar_graficos(res, tmp_path / "figures", dpi=40), tmp_path / "r.pdf")
    gerador.build_pdf()
    assert "Gerado em" in gerador.subtitulo_capa
    assert [(n, t) for n, t, _ in gerador.sumario_entradas] == sumario(res)
    paginas = [p for _, _, p in gerador.sumario_entradas]
    assert paginas == sorted(paginas) and paginas[0] >= 1
    assert all(gerador.paginas_secoes[t] == p for _, t, p in gerador.sumario_entradas)


def test_data_geracao_fixa_torna_o_pdf_reproduzivel(tmp_path: Path, df_sintetico) -> None:
    """Spec da Geração do relatório (FR-004): com a mesma data de geração, dois PDFs são idênticos byte a byte, e a data aparece na capa."""
    from datetime import datetime

    from reportlab import rl_config

    df = preparar_dados(df_sintetico)
    res = analisar_com_bases(df, tmp_path / "sem_auditoria.csv")
    figuras = gerar_graficos(res, tmp_path / "figures", dpi=40)
    data = datetime(2026, 10, 7, 8, 53)
    a = PDFReportGenerator(res, figuras, tmp_path / "a.pdf", data_geracao=data)
    a.build_pdf()
    b = PDFReportGenerator(res, figuras, tmp_path / "b.pdf", data_geracao=data).build_pdf()
    assert "Gerado em 07/10/2026 08:53" in a.subtitulo_capa
    assert (tmp_path / "a.pdf").read_bytes() == b.read_bytes()
    assert rl_config.invariant == 0  # o modo invariante vale só durante a montagem


def test_data_geracao_no_markdown_e_na_linha_de_comando(tmp_path: Path, df_sintetico) -> None:
    """Spec da Geração do relatório (FR-004): o Markdown usa a data fixa; a opção recusa formato inválido."""
    import argparse
    from datetime import datetime

    import pytest

    from src.__main__ import ler_data_geracao
    from src.relatorio.markdown import gerar_relatorio_md

    df = preparar_dados(df_sintetico)
    res = analisar_com_bases(df, tmp_path / "sem_auditoria.csv")
    md = gerar_relatorio_md(res, {}, tmp_path / "r.md", data_geracao=datetime(2026, 10, 7, 8, 53))
    assert "**Gerado em**: 07/10/2026 08:53" in md.read_text(encoding="utf-8")
    assert ler_data_geracao("07/10/2026 08:53") == datetime(2026, 10, 7, 8, 53)
    with pytest.raises(argparse.ArgumentTypeError):
        ler_data_geracao("2026-10-07 08:53")
