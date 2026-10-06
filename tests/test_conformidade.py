"""Testes de conformidade com a constituição (specs 005 e 006): seaborn, nível de log e dependências."""

from __future__ import annotations

import ast
import inspect
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import src.analyzer as analyzer
from src.logger import LOGGERS_PIPELINE, configurar_nivel_log

RAIZ = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# US2 — gráficos com seaborn
# ---------------------------------------------------------------------------


def test_todas_as_funcoes_de_grafico_usam_seaborn() -> None:
    funcoes = [f for nome, f in inspect.getmembers(analyzer, inspect.isfunction) if nome.startswith("_grafico_")]
    assert len(analyzer.NOMES_FIGURAS) == 5
    assert len(funcoes) == len(analyzer.NOMES_FIGURAS) + len(analyzer.NOMES_FIGURAS_OPCIONAIS)
    assert set(analyzer.NOMES_FIGURAS_OPCIONAIS) == set(analyzer._GERADORES_OPCIONAIS)
    for funcao in funcoes:
        assert "sns." in inspect.getsource(funcao), funcao.__name__


# ---------------------------------------------------------------------------
# US3 — nível de log único
# ---------------------------------------------------------------------------


@pytest.fixture
def restaura_niveis():
    yield
    configurar_nivel_log("INFO")


def _niveis() -> dict:
    return {nome: logging.getLogger(nome).level for nome in LOGGERS_PIPELINE}


def test_configurar_nivel_log_ajusta_todos_os_loggers(restaura_niveis) -> None:
    configurar_nivel_log("WARNING")
    assert set(_niveis().values()) == {logging.WARNING}
    configurar_nivel_log("debug")
    assert set(_niveis().values()) == {logging.DEBUG}


def test_main_aplica_o_nivel_a_todos(restaura_niveis) -> None:
    from src.main import parse_arguments, run_pipeline

    with patch("src.main.executar_indicadores_ons", return_value=0):
        assert run_pipeline(parse_arguments(["--indicadores-only", "--log-level", "WARNING"])) == 0
    assert set(_niveis().values()) == {logging.WARNING}


@pytest.mark.parametrize("modulo, funcao", [
    ("src.processor", "executar_pipeline_tratamento"),
    ("src.analyzer", "executar_pipeline_analise"),
    ("src.indicadores_ons", "executar_indicadores_ons"),
    ("src.programacao_ons", "executar_programacao_ons"),
    ("src.dicionarios_ons", "executar_dicionarios_ons"),
    ("src.disponibilidade_ons", "executar_disponibilidade_ons"),
    ("src.hidrologia_ons", "executar_hidrologia_ons"),
    ("src.geracao_ons", "executar_geracao_ons"),
    ("src.cadastro_ons", "executar_cadastro_ons"),
])
def test_pontos_de_entrada_aceitam_e_aplicam_o_nivel(modulo, funcao, restaura_niveis) -> None:
    mod = __import__(modulo, fromlist=["main"])
    with patch.object(mod, funcao, return_value=0), patch.object(sys, "argv", [modulo, "--log-level", "WARNING"]):
        with pytest.raises(SystemExit) as saida:
            mod.main()
    assert saida.value.code == 0
    assert set(_niveis().values()) == {logging.WARNING}


def test_pdf_generator_aceita_e_aplica_o_nivel(restaura_niveis) -> None:
    import src.pdf_generator as pdf

    gerador = MagicMock()
    gerador.return_value.build_pdf.return_value = Path("relatorio.pdf")
    with patch.object(pdf, "carregar_dados_tratados"), patch.object(pdf, "analisar"), \
            patch.object(pdf, "carregar_indicadores_processados"), patch.object(pdf, "carregar_programacao_processada"), \
            patch.object(pdf, "carregar_disponibilidade_processada"), patch.object(pdf, "carregar_hidrologia_processada"), \
            patch.object(pdf, "carregar_geracao_processada"), patch.object(pdf, "carregar_cadastro_processado"), \
            patch.object(pdf, "carregar_registro_dicionarios"), \
            patch.object(pdf, "PDFReportGenerator", gerador), \
            patch.object(sys, "argv", ["src.pdf_generator", "--log-level", "WARNING"]):
        pdf.main()
    assert set(_niveis().values()) == {logging.WARNING}


# ---------------------------------------------------------------------------
# US5 — dependências fiéis ao uso
# ---------------------------------------------------------------------------


def _pacotes_importados() -> set:
    nomes = set()
    for pasta in ("src", "tests"):
        for arquivo in (RAIZ / pasta).rglob("*.py"):
            arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
            for no in ast.walk(arvore):
                if isinstance(no, ast.Import):
                    nomes.update(a.name.split(".")[0] for a in no.names)
                elif isinstance(no, ast.ImportFrom) and no.level == 0 and no.module:
                    nomes.add(no.module.split(".")[0])
    return {n for n in nomes if n not in sys.stdlib_module_names and n not in {"src", "tests"}}


def _pacotes_declarados() -> set:
    linhas = (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines()
    pacotes = set()
    for linha in linhas:
        linha = linha.split("#")[0].strip()
        if linha:
            for sep in (">=", "==", "<=", "~=", ">", "<"):
                linha = linha.split(sep)[0]
            pacotes.add(linha.strip().lower())
    return pacotes


def test_requirements_corresponde_aos_imports() -> None:
    assert _pacotes_importados() == _pacotes_declarados()


# ---------------------------------------------------------------------------
# Spec 006 — gravação em data/processed só pela persistência (Requisito Técnico 3)
# ---------------------------------------------------------------------------


def test_modulos_nao_gravam_dados_processados_diretamente() -> None:
    """Nenhum módulo grava CSV, Parquet, planilha ou texto em data/processed sem passar por src/persistencia.py."""
    gravadores = ("consolidator", "processor", "validator", "indicadores_ons", "programacao_ons", "dicionarios_ons",
                  "conjuntos_ons", "disponibilidade_ons", "hidrologia_ons", "geracao_ons", "cadastro_ons")
    proibidos = (".to_csv(", ".to_parquet(", ".to_excel(", "ExcelWriter(", 'open(output_path, "w"', 'mode="w"')
    for nome in gravadores:
        fonte = (RAIZ / "src" / f"{nome}.py").read_text(encoding="utf-8")
        for padrao in proibidos:
            assert padrao not in fonte, f"{nome}.py usa {padrao} fora da persistência"
