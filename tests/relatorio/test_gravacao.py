"""Gravação do relatório: as saídas são geradas numa pasta temporária, conferidas e só então substituem as anteriores
(constituição, Requisito Técnico 3; spec da Geração do relatório, FR-003)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from openpyxl import Workbook

from src.comum import caminhos
from src.relatorio import etapa as etapa_relatorio

PERFIL = type("Perfil", (), {"usina": type("Usina", (), {"slug": "usina_teste"})()})()


def _preparar(tmp_path: Path, monkeypatch, versao: str, falhar_pdf: bool = False) -> Path:
    monkeypatch.setattr(caminhos, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(caminhos, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(etapa_relatorio, "carregar_resultados", lambda caminho: object())
    monkeypatch.setattr(etapa_relatorio, "completar_resultados", lambda res: res)
    monkeypatch.setattr(etapa_relatorio, "secoes_presentes", lambda res: ["a", "b"])
    monkeypatch.setattr(etapa_relatorio, "paginas_do_pdf", lambda caminho: 1)

    def figuras(res, pasta, dpi):
        pasta.mkdir(parents=True, exist_ok=True)
        figura = pasta / "01_serie_temporal_disponibilidade_geracao_evt.png"
        figura.write_bytes(f"png {versao}".encode())
        return {"serie_temporal": figura}

    def tabelas(res, xlsx, csv):
        planilha = Workbook()
        planilha.active.title = versao
        planilha.save(xlsx)
        csv.write_text(f"versao\n{versao}\n", encoding="utf-8")
        return xlsx, csv

    def markdown(res, figs, destino, data_geracao=None):
        destino.write_text(f"# relatório {versao}\n", encoding="utf-8")
        return destino

    class Pdf:
        def __init__(self, res, figs, destino, data_geracao=None, invariante=None):
            self.destino = Path(destino)

        def build_pdf(self):
            if falhar_pdf:
                raise RuntimeError("falha simulada no PDF")
            self.destino.write_bytes(f"%PDF-1.4 {versao}".encode())
            return self.destino

    monkeypatch.setattr(etapa_relatorio, "gerar_graficos", figuras)
    monkeypatch.setattr(etapa_relatorio, "exportar_tabelas", tabelas)
    monkeypatch.setattr(etapa_relatorio, "gerar_relatorio_md", markdown)
    monkeypatch.setattr(etapa_relatorio, "PDFReportGenerator", Pdf)
    return tmp_path / "reports" / "usina_teste"


def _conteudo(pasta: Path) -> dict:
    return {p.relative_to(pasta).as_posix(): p.read_bytes() for p in sorted(pasta.rglob("*")) if p.is_file()}


def test_saidas_trocadas_so_no_fim_e_sem_pasta_temporaria(tmp_path: Path, monkeypatch) -> None:
    pasta = _preparar(tmp_path, monkeypatch, "v1")
    resultado = etapa_relatorio.executar_relatorio(PERFIL)
    assert resultado.codigo == 0 and resultado.resumo["abas_planilha"] == 1
    assert sorted(p.relative_to(pasta).as_posix() for p in resultado.arquivos) == [
        "figures/01_serie_temporal_disponibilidade_geracao_evt.png", "perfil_estatistico_anual.csv",
        "perfil_estatistico_anual.xlsx", "relatorio_analise_estatistica.md", "relatorio_analise_estatistica.pdf"]
    assert not (pasta / etapa_relatorio.PASTA_TEMPORARIA).exists()
    assert (pasta / "relatorio_analise_estatistica.pdf").read_bytes() == b"%PDF-1.4 v1"


def test_falha_na_geracao_mantem_as_saidas_anteriores(tmp_path: Path, monkeypatch) -> None:
    pasta = _preparar(tmp_path, monkeypatch, "v1")
    etapa_relatorio.executar_relatorio(PERFIL)
    antes = _conteudo(pasta)
    _preparar(tmp_path, monkeypatch, "v2", falhar_pdf=True)
    with pytest.raises(RuntimeError):
        etapa_relatorio.executar_relatorio(PERFIL)
    assert _conteudo(pasta) == antes
    assert not (pasta / etapa_relatorio.PASTA_TEMPORARIA).exists()


def test_falha_na_troca_restaura_as_saidas_anteriores(tmp_path: Path, monkeypatch) -> None:
    pasta = _preparar(tmp_path, monkeypatch, "v1")
    etapa_relatorio.executar_relatorio(PERFIL)
    antes = _conteudo(pasta)
    _preparar(tmp_path, monkeypatch, "v2")
    original = os.replace

    def replace(origem, destino):  # o Markdown novo não consegue substituir o anterior
        novo = etapa_relatorio.PASTA_TEMPORARIA in str(origem) and ".anteriores" not in str(origem)
        if Path(destino).name == "relatorio_analise_estatistica.md" and novo:
            raise OSError("arquivo aberto em outro programa")
        return original(origem, destino)

    monkeypatch.setattr(etapa_relatorio.os, "replace", replace)
    with pytest.raises(OSError):
        etapa_relatorio.executar_relatorio(PERFIL)
    monkeypatch.setattr(etapa_relatorio.os, "replace", original)
    assert _conteudo(pasta) == antes  # o PDF, já trocado, voltou à versão anterior
    assert not (pasta / etapa_relatorio.PASTA_TEMPORARIA).exists()


def test_restauracao_incompleta_preserva_a_versao_anterior(tmp_path: Path, monkeypatch) -> None:
    pasta = _preparar(tmp_path, monkeypatch, "v1")
    etapa_relatorio.executar_relatorio(PERFIL)
    _preparar(tmp_path, monkeypatch, "v2")
    original = os.replace

    def replace(origem, destino):  # o Markdown fica bloqueado: nem o novo entra nem o anterior volta
        if Path(destino).name == "relatorio_analise_estatistica.md" and etapa_relatorio.PASTA_TEMPORARIA in str(origem):
            raise OSError("arquivo aberto em outro programa")
        return original(origem, destino)

    monkeypatch.setattr(etapa_relatorio.os, "replace", replace)
    with pytest.raises(OSError):
        etapa_relatorio.executar_relatorio(PERFIL)
    monkeypatch.setattr(etapa_relatorio.os, "replace", original)
    assert (pasta / "relatorio_analise_estatistica.pdf").read_bytes() == b"%PDF-1.4 v1"
    [preservadas] = list(pasta.glob(".anteriores_*"))
    assert (preservadas / "relatorio_analise_estatistica.md").read_text(encoding="utf-8").startswith("# relatório v1")
    assert not (pasta / etapa_relatorio.PASTA_TEMPORARIA).exists()
