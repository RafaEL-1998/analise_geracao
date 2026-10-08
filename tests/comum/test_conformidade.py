"""Conformidade com a constituição: figuras em seaborn, nível de log único, ponto de entrada único, loggers declarados,
dependências fiéis ao uso e gravação dos dados das etapas só pela persistência."""

from __future__ import annotations

import ast
import inspect
import logging
import sys
from pathlib import Path

import pytest

from src import pipeline
from src.__main__ import main
from src.comum.logger import LOGGERS_PIPELINE, configurar_nivel_log, setup_logger
from src.relatorio import figuras

RAIZ = Path(__file__).resolve().parents[2]
FONTES = sorted(p for p in (RAIZ / "src").rglob("*.py") if "__pycache__" not in p.parts)


# ---------------------------------------------------------------------------
# Figuras em seaborn
# ---------------------------------------------------------------------------


def test_todas_as_funcoes_de_grafico_usam_seaborn() -> None:
    funcoes = [f for nome, f in inspect.getmembers(figuras, inspect.isfunction) if nome.startswith("_grafico_")]
    assert len(figuras.NOMES_FIGURAS) == 5
    assert len(funcoes) == len(figuras.NOMES_FIGURAS) + len(figuras.NOMES_FIGURAS_OPCIONAIS)
    assert set(figuras.NOMES_FIGURAS_OPCIONAIS) == set(figuras._GERADORES_OPCIONAIS)
    for funcao in funcoes:
        assert "sns." in inspect.getsource(funcao), funcao.__name__


# ---------------------------------------------------------------------------
# Nível de log único, loggers declarados e ponto de entrada único
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


def test_linha_de_comando_aplica_o_nivel_a_todos(restaura_niveis, monkeypatch) -> None:
    monkeypatch.setattr(pipeline, "executar_etapa", lambda *args, **kwargs: 0)
    assert main(["tratamento", "--usina", "sao_domingos", "--log-level", "WARNING"]) == 0
    assert set(_niveis().values()) == {logging.WARNING}


def test_loggers_do_codigo_estao_declarados() -> None:
    usados = set()
    for arquivo in FONTES:
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if isinstance(no, ast.Call) and getattr(no.func, "id", "") == "setup_logger" and no.args:
                assert isinstance(no.args[0], ast.Constant), arquivo.name
                usados.add(no.args[0].value)
    assert usados and usados <= set(LOGGERS_PIPELINE)


def test_ponto_de_entrada_unico() -> None:
    """Só ``python -m src``: nenhum outro módulo tem linha de comando própria."""
    for arquivo in FONTES:
        if arquivo == RAIZ / "src" / "__main__.py":
            continue
        fonte = arquivo.read_text(encoding="utf-8")
        assert '__name__ == "__main__"' not in fonte, arquivo.name
        assert "argparse" not in fonte, arquivo.name


# ---------------------------------------------------------------------------
# Dependências fiéis ao uso
# ---------------------------------------------------------------------------


def _pacotes_importados() -> set:
    nomes = set()
    for pasta in ("src", "tests"):
        for arquivo in (RAIZ / pasta).rglob("*.py"):
            if "__pycache__" in arquivo.parts:
                continue
            for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
                if isinstance(no, ast.Import):
                    nomes.update(a.name.split(".")[0] for a in no.names)
                elif isinstance(no, ast.ImportFrom) and no.level == 0 and no.module:
                    nomes.add(no.module.split(".")[0])
    return {n for n in nomes if n not in sys.stdlib_module_names and n not in {"src", "tests"}}


def _pacotes_declarados() -> set:
    pacotes = set()
    for linha in (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines():
        linha = linha.split("#")[0].strip()
        if linha:
            for sep in (">=", "==", "<=", "~=", ">", "<"):
                linha = linha.split(sep)[0]
            pacotes.add(linha.strip().lower())
    return pacotes


def test_requirements_corresponde_aos_imports() -> None:
    assert _pacotes_importados() == _pacotes_declarados()


# ---------------------------------------------------------------------------
# Dados das etapas gravados só pela persistência (cópia .bak, conferência e restauração em falha)
# ---------------------------------------------------------------------------


def test_etapas_gravam_dados_so_pela_persistencia() -> None:
    arquivos = [p for pacote in ("coleta", "tratamento", "conferencia", "analises")
                for p in sorted((RAIZ / "src" / pacote).glob("*.py"))]
    assert arquivos
    proibidos = (".to_csv(", ".to_parquet(", ".to_excel(", "ExcelWriter(", "pickle.dump(", 'mode="w"',
                 ".write_text(", ".write_bytes(")
    for arquivo in arquivos:
        fonte = arquivo.read_text(encoding="utf-8")
        for padrao in proibidos:
            assert padrao not in fonte, f"{arquivo.name} usa {padrao} fora da persistência"


def test_nenhum_bak_solto_no_codigo_nas_specs_e_nos_relatorios() -> None:
    """Cópia .bak só nos dados da Coleta e do Tratamento (data/usinas/<slug>/<etapa>/), nunca nas pastas versionadas."""
    pastas = ("src", "tests", "specs", ".specify", "usinas", "reports")
    soltos = [str(p.relative_to(RAIZ)) for pasta in pastas if (RAIZ / pasta).exists()
              for p in (RAIZ / pasta).rglob("*.bak")]
    soltos += [p.name for p in RAIZ.glob("*.bak")]
    assert soltos == []


def test_logger_configurado_depois_da_linha_de_comando_mantem_o_nivel(restaura_niveis) -> None:
    """As etapas são importadas só na execução, depois de --log-level: o logger delas não volta a INFO."""
    configurar_nivel_log("WARNING")
    for nome in LOGGERS_PIPELINE:
        setup_logger(nome)
    assert set(_niveis().values()) == {logging.WARNING}
