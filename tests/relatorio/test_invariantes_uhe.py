"""Invariantes do relatório da hidrelétrica com EVT (spec 006, decisão R29; tarefa T011).

A usina fictícia (UHE com EVT) roda de ponta a ponta e cada parte da saída é comparada com a fotografia
``tests/fixtures/invariantes_uhe.json``, tirada com o código aprovado antes da ampliação. Um teste por invariante,
para apontar a causa de uma diferença antes do ``comparar``. Refazer a fotografia exige a aprovação do usuário.
"""

from __future__ import annotations

import json

import pytest

from tests.fixtures.execucao_ficticia import ARQUIVO_INVARIANTES, executar_usina_ficticia, extrair_invariantes

# Arquivos que a Coleta da hidrelétrica com EVT pode ganhar na ampliação (formato 2; decisões R8 e R22)
ARQUIVOS_NOVOS_PERMITIDOS = {"datas_obtencao.csv", "dicionario_evt.json"}


@pytest.fixture(scope="module")
def fotografia():
    return json.loads(ARQUIVO_INVARIANTES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def atual(tmp_path_factory):
    execucao = executar_usina_ficticia(tmp_path_factory.mktemp("invariantes"))
    assert execucao["codigo"] == 0
    return extrair_invariantes(execucao)


def test_secoes_titulos_e_ordem(atual, fotografia) -> None:
    assert atual["secoes"] == fotografia["secoes"]


def test_capa_e_titulo(atual, fotografia) -> None:
    assert atual["capa"] == fotografia["capa"]


def test_legendas(atual, fotografia) -> None:
    assert atual["legendas"] == fotografia["legendas"]


def test_conferencias_citadas(atual, fotografia) -> None:
    """As conferências de hoje, sem G1 a G5 nem não aplicáveis no relatório (decisão R13)."""
    def conferencias(md: str) -> list:
        return [linha for linha in md.splitlines() if "Conferência" in linha or "conferência" in linha]

    assert conferencias(atual["md_completo"]) == conferencias(fotografia["md_completo"])
    assert "não aplicável" not in atual["md_completo"].lower()


def test_conclusao_itens_texto_e_nota(atual, fotografia) -> None:
    assert atual["conclusao_itens"] == fotografia["conclusao_itens"]
    assert atual["conclusao_md"] == fotografia["conclusao_md"]
    assert atual["nota_conclusao"] == fotografia["nota_conclusao"]


def test_sem_trechos_nem_granularidade(atual) -> None:
    md = atual["md_completo"].lower()
    assert "trecho" not in md
    assert "conjunto de usinas" not in md


def test_notas(atual, fotografia) -> None:
    assert atual["notas"] == fotografia["notas"]


def test_planilha_abas_colunas_e_dicionarios(atual, fotografia) -> None:
    assert atual["planilha_abas"] == fotografia["planilha_abas"]
    assert atual["dicionarios"] == fotografia["dicionarios"]


def test_coleta_arquivos_e_colunas(atual, fotografia) -> None:
    for nome, colunas in fotografia["coleta"].items():
        assert atual["coleta"].get(nome) == colunas, nome
    assert set(atual["coleta"]) - set(fotografia["coleta"]) <= ARQUIVOS_NOVOS_PERMITIDOS


def test_markdown_completo(atual, fotografia) -> None:
    """Rede de segurança: o Markdown inteiro, com as datas de obtenção normalizadas."""
    assert atual["md_completo"] == fotografia["md_completo"]
