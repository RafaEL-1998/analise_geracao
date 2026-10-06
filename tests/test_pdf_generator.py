"""Testes automatizados para o gerador de relatórios em PDF."""

from pathlib import Path

from src.analyzer import analisar, gerar_graficos, preparar_dados
from src.pdf_generator import PDFReportGenerator


def test_pdf_gerado_a_partir_dos_resultados(tmp_path: Path, df_sintetico) -> None:
    """O PDF é montado a partir de ResultadosAnalise e das figuras geradas."""
    df = preparar_dados(df_sintetico)
    res = analisar(df, tmp_path / "sem_auditoria.csv", tmp_path / "sem_manifesto.json")
    figuras = gerar_graficos(df, res, tmp_path / "figures", dpi=60)

    saida = PDFReportGenerator(res, figuras, tmp_path / "relatorio.pdf").build_pdf()

    assert saida.exists()
    assert saida.read_bytes()[:5] == b"%PDF-"
    assert saida.stat().st_size > 10_000


def test_pdf_sem_figuras_nao_falha(tmp_path: Path, df_sintetico) -> None:
    """Figuras ausentes geram aviso no documento em vez de erro."""
    df = preparar_dados(df_sintetico)
    res = analisar(df, tmp_path / "sem_auditoria.csv", tmp_path / "sem_manifesto.json")

    saida = PDFReportGenerator(res, {}, tmp_path / "relatorio.pdf").build_pdf()

    assert saida.exists()


def test_pdf_toda_tabela_e_figura_tem_legenda_de_fonte(tmp_path: Path, df_sintetico) -> None:
    """Spec 007 (FR-001): cada tabela, bloco e figura desenhados no PDF ganha a legenda de fonte."""
    df = preparar_dados(df_sintetico)
    res = analisar(df, tmp_path / "sem_auditoria.csv", tmp_path / "sem_manifesto.json")
    figuras = gerar_graficos(df, res, tmp_path / "figures", dpi=50)
    gerador = PDFReportGenerator(res, figuras, tmp_path / "relatorio.pdf")
    gerador.build_pdf()
    assert gerador._desenhados > 0 and gerador._legendas == gerador._desenhados


def test_rodape_so_com_a_numeracao() -> None:
    """Spec 008 (FR-009): o rodapé não tem frase de fontes nem data; só "Página X de Y"."""
    import inspect

    import src.pdf_generator as pdf

    assert list(inspect.signature(pdf._canvas_numerado).parameters) == ["cabecalho", "fonte"]


def test_capa_com_data_e_sumario_com_paginas(tmp_path: Path, df_sintetico) -> None:
    """Spec 008 (US1): "Gerado em" na capa; sumário com todas as seções presentes e a página real de cada uma."""
    from src.estrutura_relatorio import sumario

    df = preparar_dados(df_sintetico)
    res = analisar(df, tmp_path / "sem_auditoria.csv", tmp_path / "sem_manifesto.json")
    gerador = PDFReportGenerator(res, gerar_graficos(df, res, tmp_path / "figures", dpi=40), tmp_path / "r.pdf")
    gerador.build_pdf()
    assert "Gerado em" in gerador.subtitulo_capa
    assert [(n, t) for n, t, _ in gerador.sumario_entradas] == sumario(res)
    paginas = [p for _, _, p in gerador.sumario_entradas]
    assert paginas == sorted(paginas) and paginas[0] >= 1
    assert all(gerador.paginas_secoes[t] == p for _, t, p in gerador.sumario_entradas)
