"""Relatórios de referência: comando ``referencia`` e ``comparar --todas [--coleta]`` (spec 006, decisão R22;
contrato cli-referencias.md; tarefas T012 e T013).

A usina fictícia roda uma vez por módulo; cada teste trabalha numa cópia dessa raiz, com as pastas do fluxo
redirecionadas, sem rede.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date, datetime
from pathlib import Path

import pytest

from src.__main__ import main
from src.comum import caminhos, comparacao, referencias
from src.comum import perfil as modulo_perfil
from tests.fixtures.execucao_ficticia import DATA_GERACAO, SLUG, executar_usina_ficticia

DATA = datetime.strptime(DATA_GERACAO, "%d/%m/%Y %H:%M")
APROVADO = date(2026, 10, 9)


@pytest.fixture(scope="module")
def raiz_executada(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("referencias")
    assert executar_usina_ficticia(raiz)["codigo"] == 0
    return raiz


@pytest.fixture
def projeto(raiz_executada, tmp_path, monkeypatch):
    """Cópia da raiz executada, com as pastas do fluxo apontando para ela."""
    raiz = tmp_path / "projeto"
    shutil.copytree(raiz_executada, raiz)
    monkeypatch.setattr(caminhos, "DATA_DIR", raiz / "data")
    monkeypatch.setattr(caminhos, "RAW_DATA_DIR", raiz / "data" / "raw")
    monkeypatch.setattr(caminhos, "REPORTS_DIR", raiz / "reports")
    monkeypatch.setattr(caminhos, "USINAS_DIR", raiz / "usinas")
    monkeypatch.setattr(caminhos, "RELATORIOS_REFERENCIA_DIR", raiz / "relatorios_referencia")
    monkeypatch.setattr(modulo_perfil, "RAIZ_PROJETO", raiz)
    return raiz


def _sha(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _registrar(commitada: bool = True) -> int:
    return referencias.registrar_referencia(SLUG, DATA, APROVADO, referencia_commitada=lambda _pasta: commitada)


def _estado(raiz: Path) -> dict:
    """SHA-256 de todos os arquivos de dados, relatórios e brutos, para conferir que nada mudou."""
    return {p.relative_to(raiz).as_posix(): _sha(p) for pasta in ("data", "reports")
            for p in (raiz / pasta).rglob("*") if p.is_file()}


# ---------------------------------------------------------------------------
# referencia (T012)
# ---------------------------------------------------------------------------


def test_referencia_registrada_com_coleta_e_perfil_congelados(projeto: Path) -> None:
    assert _registrar() == 0
    pasta = projeto / "relatorios_referencia" / SLUG
    assert (pasta / "relatorio_analise_estatistica.pdf").is_file()
    assert (pasta / "relatorio_analise_estatistica.md").is_file()
    assert (pasta / "perfil.toml").read_bytes() == (projeto / "usinas" / SLUG / "perfil.toml").read_bytes()
    manifesto = json.loads((projeto / "data" / "usinas" / SLUG / "coleta" / "etapa.json").read_text(encoding="utf-8"))
    esperados = {a["nome"] for a in manifesto["arquivos"]} | {"etapa.json"}
    congelados = {p.name for p in (pasta / "coleta").iterdir()}
    assert congelados == esperados
    assert not any(n.endswith(".bak") for n in congelados)
    ref = json.loads((pasta / "referencia.json").read_text(encoding="utf-8"))
    assert set(ref) >= {"usina", "data_geracao", "aprovado_em", "periodo", "arquivos", "perfil", "coleta"}
    assert (ref["usina"], ref["data_geracao"], ref["aprovado_em"]) == (SLUG, DATA_GERACAO, "09/10/2026")
    assert ref["perfil"] == _sha(pasta / "perfil.toml")
    for item in ref["arquivos"]:
        assert _sha(pasta / item["nome"]) == item["sha256"]
    for item in ref["coleta"]:
        assert _sha(pasta / "coleta" / item["nome"]) == item["sha256"]
    assert ref["periodo"]["inicio"] and ref["periodo"]["fim"]


def test_referencia_com_outra_data_e_recusada(projeto: Path) -> None:
    codigo = referencias.registrar_referencia(SLUG, datetime(2026, 1, 1, 0, 0), APROVADO,
                                              referencia_commitada=lambda _p: True)
    assert codigo == 1
    assert not (projeto / "relatorios_referencia" / SLUG).exists()


def test_referencia_sem_relatorio_concluido(projeto: Path) -> None:
    (projeto / "reports" / SLUG / "etapa.json").unlink()
    assert _registrar() == 5


def test_referencia_com_coleta_em_formato_antigo(projeto: Path) -> None:
    manifesto = projeto / "data" / "usinas" / SLUG / "coleta" / "etapa.json"
    dados = json.loads(manifesto.read_text(encoding="utf-8"))
    dados["versao_formato"] = 1
    manifesto.write_text(json.dumps(dados), encoding="utf-8")
    assert _registrar() == 5


def test_substituir_referencia_nao_commitada_e_recusado(projeto: Path) -> None:
    assert _registrar() == 0
    pasta = projeto / "relatorios_referencia" / SLUG
    antes = _sha(pasta / "referencia.json")
    assert _registrar(commitada=False) == 1
    assert _sha(pasta / "referencia.json") == antes


def test_substituir_referencia_commitada(projeto: Path) -> None:
    assert _registrar() == 0
    assert _registrar(commitada=True) == 0


def test_referencia_pela_linha_de_comando_com_perfil_invalido(projeto: Path) -> None:
    assert main(["referencia", "--usina", "inexistente", "--data-geracao", DATA_GERACAO,
                 "--aprovado-em", "09/10/2026"]) == 4


# ---------------------------------------------------------------------------
# comparar --todas [--coleta] (T013)
# ---------------------------------------------------------------------------


def test_comparar_todas_sem_diferenca_e_sem_mexer_nos_dados(projeto: Path, capsys) -> None:
    assert _registrar() == 0
    antes = _estado(projeto)
    assert comparacao.executar_comparacao_todas() == 0
    assert _estado(projeto) == antes
    saida = capsys.readouterr().out
    assert f"{SLUG}: nenhuma diferença" in saida
    assert "Referências comparadas: 1; com diferença: 0." in saida


def test_comparar_todas_acusa_diferenca(projeto: Path, capsys) -> None:
    assert _registrar() == 0
    md = projeto / "relatorios_referencia" / SLUG / "relatorio_analise_estatistica.md"
    md.write_text(md.read_text(encoding="utf-8") + "\nlinha a mais\n", encoding="utf-8")
    assert comparacao.executar_comparacao_todas() == 6
    assert "com diferença: 1." in capsys.readouterr().out


def test_comparar_todas_usa_o_perfil_congelado_e_avisa(projeto: Path, capsys) -> None:
    assert _registrar() == 0
    perfil = projeto / "usinas" / SLUG / "perfil.toml"
    perfil.write_text(perfil.read_text(encoding="utf-8").replace("UHE Fictícia", "UHE Fictícia Alterada"),
                      encoding="utf-8")
    assert comparacao.executar_comparacao_todas() == 0
    assert "o perfil atual difere do congelado" in capsys.readouterr().out


def test_comparar_todas_com_coleta_congelada_alterada_e_erro(projeto: Path) -> None:
    assert _registrar() == 0
    congelado = projeto / "relatorios_referencia" / SLUG / "coleta" / "evt_extraido.csv"
    congelado.write_text(congelado.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert comparacao.executar_comparacao_todas() == 1


def test_comparar_todas_sem_referencias_e_erro(projeto: Path) -> None:
    assert comparacao.executar_comparacao_todas() == 1


def test_comparar_todas_com_coleta_sem_diferenca(projeto: Path, capsys) -> None:
    """Refaz a Coleta com --sem-portal; as colunas de execução e os registros informativos não contam."""
    assert _registrar() == 0
    assert comparacao.executar_comparacao_todas(coleta=True) == 0
    assert "com diferença: 0." in capsys.readouterr().out


def test_comparar_todas_com_coleta_acusa_bruto_alterado(projeto: Path, capsys) -> None:
    assert _registrar() == 0
    bruto = projeto / "data" / "raw" / "ENERGIA_VERTIDA_TURBINAVEL_2024_01.csv"
    texto = bruto.read_text(encoding="utf-8").splitlines()
    campos = texto[1].split(";")
    campos[8] = "71.0"  # val_geracao da primeira hora da usina
    texto[1] = ";".join(campos)
    bruto.write_text("\n".join(texto) + "\n", encoding="utf-8")
    assert comparacao.executar_comparacao_todas(coleta=True) == 6
    assert "Coleta: evt_extraido.csv" in capsys.readouterr().out


@pytest.mark.parametrize("argumentos", [["comparar", "--todas", "--usina", SLUG],
                                        ["comparar"],
                                        ["comparar", "--usina", SLUG]])
def test_comparar_opcoes_invalidas(argumentos) -> None:
    with pytest.raises(SystemExit) as erro:
        main(argumentos)
    assert erro.value.code == 2
