"""Manifesto da etapa e pré-requisitos (spec da Coleta de dados, FR-011 a FR-013)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from src import pipeline
from src.comum import caminhos
from src.comum.perfil import carregar_perfil
from src.pipeline import ETAPAS, ResultadoEtapa, executar_completo, executar_etapa, ler_manifesto

PERFIL = carregar_perfil("sao_domingos")
SLUG = PERFIL.usina.slug


@pytest.fixture(autouse=True)
def pastas(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setattr(caminhos, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(caminhos, "REPORTS_DIR", tmp_path / "reports")
    return tmp_path


def _funcao(etapa: str, codigo: int = 0):
    def executar(perfil, **opcoes) -> ResultadoEtapa:
        pasta = caminhos.pasta_etapa(perfil.usina.slug, etapa)
        pasta.mkdir(parents=True, exist_ok=True)
        arquivo = pasta / f"{etapa}.csv"
        arquivo.write_text("a;b\n1;2\n", encoding="utf-8")
        return ResultadoEtapa(codigo=codigo, arquivos=[arquivo], resumo={"linhas": 1, "opcoes": dict(opcoes)})
    return executar


def _falha(perfil, **opcoes) -> ResultadoEtapa:
    raise RuntimeError("erro simulado")


def test_manifesto_com_todos_os_campos() -> None:
    assert executar_etapa("coleta", PERFIL, funcao=_funcao("coleta"), sem_portal=True) == 0
    m = ler_manifesto(SLUG, "coleta")
    assert set(m) == {"etapa", "usina", "versao_formato", "iniciada_em", "concluida_em", "status", "codigo_saida",
                      "etapa_anterior", "arquivos", "resumo"}
    assert (m["etapa"], m["usina"], m["status"], m["codigo_saida"], m["etapa_anterior"]) == (
        "coleta", SLUG, "concluida", 0, None)
    assert m["versao_formato"] == pipeline.VERSAO_FORMATO["coleta"]
    assert m["arquivos"] == [{"nome": "coleta.csv", "bytes": 10, "sha256": pipeline._sha256(
        caminhos.pasta_etapa(SLUG, "coleta") / "coleta.csv")}]
    assert m["resumo"] == {"linhas": 1, "opcoes": {"sem_portal": True}}


def test_etapa_sem_a_anterior_sai_com_5_sem_gravar(caplog) -> None:
    with caplog.at_level(logging.ERROR, logger="pipeline"):
        assert executar_etapa("tratamento", PERFIL, funcao=_funcao("tratamento")) == 5
    assert not caminhos.pasta_etapa(SLUG, "tratamento").exists()
    assert ("A etapa 'tratamento' precisa da etapa 'coleta' concluída para a usina 'sao_domingos'. "
            "Execute antes: python -m src coleta --usina sao_domingos") in caplog.text


def test_seguinte_registra_a_anterior_usada() -> None:
    executar_etapa("coleta", PERFIL, funcao=_funcao("coleta"))
    assert executar_etapa("tratamento", PERFIL, funcao=_funcao("tratamento")) == 0
    anterior = ler_manifesto(SLUG, "tratamento")["etapa_anterior"]
    assert anterior == {"etapa": "coleta", "concluida_em": ler_manifesto(SLUG, "coleta")["concluida_em"]}


def test_reexecutar_marca_as_seguintes_desatualizadas() -> None:
    for etapa in ("coleta", "tratamento", "conferencia"):
        assert executar_etapa(etapa, PERFIL, funcao=_funcao(etapa)) == 0
    assert executar_etapa("coleta", PERFIL, funcao=_funcao("coleta")) == 0
    assert ler_manifesto(SLUG, "tratamento")["status"] == "desatualizada"
    assert ler_manifesto(SLUG, "conferencia")["status"] == "desatualizada"
    assert executar_etapa("conferencia", PERFIL, funcao=_funcao("conferencia")) == 5
    assert executar_etapa("tratamento", PERFIL, funcao=_funcao("tratamento")) == 0
    assert executar_etapa("conferencia", PERFIL, funcao=_funcao("conferencia")) == 0


def test_erro_grava_falha_e_bloqueia_a_seguinte() -> None:
    assert executar_etapa("coleta", PERFIL, funcao=_falha) == 1
    m = ler_manifesto(SLUG, "coleta")
    assert (m["status"], m["codigo_saida"]) == ("falha", 1)
    assert executar_etapa("tratamento", PERFIL, funcao=_funcao("tratamento")) == 5


def test_codigo_2_grava_falha() -> None:
    assert executar_etapa("coleta", PERFIL, funcao=_funcao("coleta", codigo=2)) == 2
    assert ler_manifesto(SLUG, "coleta")["status"] == "falha"
    assert executar_etapa("tratamento", PERFIL, funcao=_funcao("tratamento")) == 5


def test_codigo_3_conclui_e_a_seguinte_aceita() -> None:
    for etapa in ("coleta", "tratamento"):
        executar_etapa(etapa, PERFIL, funcao=_funcao(etapa))
    assert executar_etapa("conferencia", PERFIL, funcao=_funcao("conferencia", codigo=3)) == 3
    m = ler_manifesto(SLUG, "conferencia")
    assert (m["status"], m["codigo_saida"]) == ("concluida", 3)
    assert executar_etapa("analises", PERFIL, funcao=_funcao("analises")) == 0


def test_formato_antigo_da_anterior_e_recusado() -> None:
    executar_etapa("coleta", PERFIL, funcao=_funcao("coleta"))
    caminho = pipeline.arquivo_manifesto(SLUG, "coleta")
    m = json.loads(caminho.read_text(encoding="utf-8"))
    m["versao_formato"] = 0
    caminho.write_text(json.dumps(m), encoding="utf-8")
    assert executar_etapa("tratamento", PERFIL, funcao=_funcao("tratamento")) == 5


def test_completo_para_na_primeira_etapa_com_codigo_diferente_de_zero(monkeypatch) -> None:
    funcoes = {etapa: _funcao(etapa) for etapa in ETAPAS}
    funcoes["conferencia"] = _funcao("conferencia", codigo=3)
    monkeypatch.setattr(pipeline, "_funcao", lambda etapa: funcoes[etapa])
    assert executar_completo(PERFIL, sem_portal=True) == 3
    assert ler_manifesto(SLUG, "analises") is None and ler_manifesto(SLUG, "relatorio") is None
    assert ler_manifesto(SLUG, "coleta")["resumo"]["opcoes"] == {"sem_portal": True, "forcar_download": False}


def test_completo_passa_as_opcoes_de_cada_etapa(monkeypatch) -> None:
    from datetime import datetime

    funcoes = {etapa: _funcao(etapa) for etapa in ETAPAS}
    monkeypatch.setattr(pipeline, "_funcao", lambda etapa: funcoes[etapa])
    data = datetime(2026, 10, 7, 8, 53)
    assert executar_completo(PERFIL, data_geracao=data) == 0
    assert all(ler_manifesto(SLUG, e)["status"] == "concluida" for e in ETAPAS)
    assert ler_manifesto(SLUG, "relatorio")["resumo"]["opcoes"] == {"data_geracao": str(data)}
    assert ler_manifesto(SLUG, "tratamento")["resumo"]["opcoes"] == {}


def _interrompida(perfil, **opcoes) -> ResultadoEtapa:
    raise KeyboardInterrupt


def test_interrupcao_pelo_usuario_grava_falha_com_codigo_1() -> None:
    """Ctrl+C durante a etapa: código 1 e manifesto em falha, para a seguinte não usar resultados pela metade."""
    assert executar_etapa("coleta", PERFIL, funcao=_funcao("coleta")) == 0
    assert executar_etapa("coleta", PERFIL, funcao=_interrompida) == 1
    m = ler_manifesto(SLUG, "coleta")
    assert (m["status"], m["codigo_saida"], m["resumo"]) == ("falha", 1, {"erro": "interrompida pelo usuário"})
    assert executar_etapa("tratamento", PERFIL, funcao=_funcao("tratamento")) == 5
