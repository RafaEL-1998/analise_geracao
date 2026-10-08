"""Linha de comando única (spec da Coleta de dados, FR-002 a FR-005; contrato da linha de comando)."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pytest

from src import pipeline
from src.__main__ import construir_parser, main
from src.comum import caminhos, perfil as modulo_perfil
from src.pipeline import ETAPAS, ResultadoEtapa, ler_manifesto


@pytest.fixture(autouse=True)
def pastas(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setattr(caminhos, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(caminhos, "REPORTS_DIR", tmp_path / "reports")
    yield tmp_path
    logging.getLogger("pipeline").setLevel(logging.INFO)


def _funcao(etapa: str, codigo: int = 0):
    def executar(perfil, **opcoes) -> ResultadoEtapa:
        pasta = caminhos.pasta_etapa(perfil.usina.slug, etapa)
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "saida.txt").write_text(repr(sorted(opcoes.items())), encoding="utf-8")
        return ResultadoEtapa(codigo=codigo, arquivos=[pasta / "saida.txt"])
    return executar


@pytest.mark.parametrize("argv", [
    ["coleta", "--usina", "sao_domingos"],
    ["coleta", "--usina", "sao_domingos", "--sem-portal", "--forcar-download"],
    ["tratamento", "--usina", "sao_domingos"],
    ["conferencia", "--usina", "sao_domingos"],
    ["analises", "--usina", "sao_domingos", "--log-level", "DEBUG"],
    ["relatorio", "--usina", "sao_domingos", "--data-geracao", "07/10/2026 08:53"],
    ["completo", "--usina", "sao_domingos", "--sem-portal", "--data-geracao", "07/10/2026 08:53"],
    ["copia-seguranca", "--motivo", "antes_ajuste_x"],
    ["comparar", "--usina", "sao_domingos", "--referencia", "pasta"],
])
def test_comandos_e_opcoes_do_contrato(argv) -> None:
    args = construir_parser().parse_args(argv)
    assert args.comando == argv[0]


@pytest.mark.parametrize("argv", [
    ["coleta"],  # --usina obrigatório
    ["comparar", "--usina", "sao_domingos"],  # --referencia obrigatório
    ["copia-seguranca"],  # --motivo obrigatório
    ["relatorio", "--usina", "sao_domingos", "--data-geracao", "2026-10-07"],
    ["coleta", "--usina", "sao_domingos", "--log-level", "TRACE"],
    # opções retiradas do fluxo antigo
    ["coleta", "--usina", "sao_domingos", "--full-pipeline"],
    ["coleta", "--usina", "sao_domingos", "--complementares-only"],
    ["coleta", "--usina", "sao_domingos", "--filter-only"],
    ["coleta", "--usina", "sao_domingos", "--sem-hidrologia"],
    ["coleta", "--usina", "sao_domingos", "--cod-usina", "153"],
    ["tratamento", "--usina", "sao_domingos", "--no-validate-physics"],
    ["relatorio", "--usina", "sao_domingos", "--no-generate-plots"],
    ["main"],
])
def test_opcao_invalida_ou_retirada_sai_com_2(argv) -> None:
    with pytest.raises(SystemExit) as saida:
        construir_parser().parse_args(argv)
    assert saida.value.code == 2


def test_perfil_invalido_sai_com_4_e_lista_os_problemas(tmp_path: Path, monkeypatch, capsys) -> None:
    destino = tmp_path / "usinas" / "ruim" / "perfil.toml"
    destino.parent.mkdir(parents=True)
    destino.write_text('[usina]\nslug = "ruim"\nestado = "xx"\n', encoding="utf-8")
    monkeypatch.setattr(modulo_perfil, "RAIZ_PROJETO", tmp_path)
    assert main(["coleta", "--usina", "ruim"]) == 4
    erro = capsys.readouterr().err
    assert erro.startswith("Perfil da usina 'ruim' inválido (usinas/ruim/perfil.toml):")
    assert "usina.estado: deve ter 2 letras maiúsculas" in erro and "usina.nome: campo obrigatório ausente" in erro
    assert not (tmp_path / "data").exists()


def test_etapa_sem_a_anterior_mostra_a_mensagem_e_sai_com_5(caplog) -> None:
    with caplog.at_level(logging.ERROR, logger="pipeline"):
        assert main(["analises", "--usina", "sao_domingos"]) == 5
    assert "Execute antes: python -m src conferencia --usina sao_domingos" in caplog.text


def test_completo_para_na_primeira_etapa_com_codigo_diferente_de_zero(monkeypatch) -> None:
    funcoes = {etapa: _funcao(etapa) for etapa in ETAPAS}
    funcoes["tratamento"] = _funcao("tratamento", codigo=1)
    monkeypatch.setattr(pipeline, "_funcao", lambda etapa: funcoes[etapa])
    assert main(["completo", "--usina", "sao_domingos", "--sem-portal"]) == 1
    assert ler_manifesto("sao_domingos", "tratamento")["status"] == "falha"
    assert ler_manifesto("sao_domingos", "conferencia") is None


def test_completo_passa_as_opcoes_a_coleta_e_ao_relatorio(monkeypatch) -> None:
    funcoes = {etapa: _funcao(etapa) for etapa in ETAPAS}
    monkeypatch.setattr(pipeline, "_funcao", lambda etapa: funcoes[etapa])
    assert main(["completo", "--usina", "sao_domingos", "--sem-portal", "--data-geracao", "07/10/2026 08:53"]) == 0
    coleta = (caminhos.pasta_etapa("sao_domingos", "coleta") / "saida.txt").read_text(encoding="utf-8")
    relatorio = (caminhos.pasta_relatorio("sao_domingos") / "saida.txt").read_text(encoding="utf-8")
    assert coleta == "[('forcar_download', False), ('sem_portal', True)]"
    assert relatorio == "[('data_geracao', datetime.datetime(2026, 10, 7, 8, 53))]"


def test_comparar_com_a_referencia(tmp_path: Path) -> None:
    atual = caminhos.pasta_relatorio("sao_domingos")
    atual.mkdir(parents=True)
    (atual / "relatorio_analise_estatistica.md").write_text("# Relatório\n", encoding="utf-8")
    referencia = tmp_path / "referencia"
    shutil.copytree(atual, referencia)
    assert main(["comparar", "--usina", "sao_domingos", "--referencia", str(referencia)]) == 0
    (referencia / "relatorio_analise_estatistica.md").write_text("# Outro\n", encoding="utf-8")
    assert main(["comparar", "--usina", "sao_domingos", "--referencia", str(referencia)]) == 6
    assert main(["comparar", "--usina", "sao_domingos", "--referencia", str(tmp_path / "nao_existe")]) == 1
