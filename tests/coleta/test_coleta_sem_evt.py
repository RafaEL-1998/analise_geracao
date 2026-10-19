"""Coleta das usinas sem EVT (spec 006, decisões R6 a R9; data-model, seções 5 e 6.1; tarefa T060).

O período vem da série de referência (Geração por usina, da usina ou do conjunto), varrida em todos os arquivos. Fora
das hidrelétricas com EVT, a Coleta grava também ``geracao_complemento.parquet``, ``trechos.csv``,
``composicao_conjunto.csv`` (usina em conjunto) e ``capacidade_ficha.csv``, e o resumo do ``etapa.json`` ganha o tipo,
a modalidade, a série de referência, os trechos, os conjuntos não aplicáveis e as linhas próprias sem valor.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import pytest

from tests.fixtures import brutos_catalogo as bc
from tests.fixtures.sem_evt import projeto_sem_evt


@pytest.fixture(scope="module")
def coletas(tmp_path_factory) -> Dict[str, Dict[str, Any]]:
    usinas = projeto_sem_evt(tmp_path_factory.mktemp("projeto"), ["coleta"])
    return {slug: {"codigo": u["codigos"]["coleta"], "pasta": u["pasta"] / "coleta",
                   "manifesto": u["manifestos"]["coleta"]} for slug, u in usinas.items()}


def test_termica_com_geracao_propria(coletas) -> None:
    c = coletas["ute_beta"]
    assert c["codigo"] == 0, c["manifesto"]["resumo"]
    resumo = c["manifesto"]["resumo"]
    assert (resumo["tipo"], resumo["modalidade"]) == ("UTE", "TIPO I")
    assert resumo["serie_referencia"] == {
        "conjunto": "geracao", "identificador": f"id_ons={bc.UTE['id_ons']}", "inicio": "2025-09-01 00:00:00",
        "fim": "2026-09-30 23:00:00", "arquivos_varridos": 13,
        "motivo": "geração própria: Geração por usina, pelo id ONS da usina"}
    assert resumo["periodo"] == {"inicio": "2025-09-01 00:00:00", "fim": "2026-09-30 23:00:00"}
    assert resumo["conjuntos_nao_aplicaveis"] == ["indicadores"]
    assert resumo["trechos"] == 1 and resumo["linhas_usina_sem_valor"] == 0
    geracao = pd.read_parquet(c["pasta"] / "geracao_extraido.parquet")
    assert list(geracao.columns) == ["din_instante", "val_geracao", "_nao_numerico", "arquivo_origem"]
    assert len(geracao) == 9480 and set(geracao["val_geracao"]) == {100.0}
    complemento = pd.read_parquet(c["pasta"] / "geracao_complemento.parquet")
    assert set(complemento["nivel"]) == {"usina"} and set(complemento["cod_modalidadeoperacao"]) == {"TIPO I"}
    trechos = pd.read_csv(c["pasta"] / "trechos.csv", sep=";", dtype=str, keep_default_na=False)
    assert len(trechos) == 1 and trechos.iloc[0]["mostrar"] == "False"
    capacidade = pd.read_csv(c["pasta"] / "capacidade_ficha.csv", sep=";", dtype=str)
    assert len(capacidade) == 4 and "val_potenciaefetiva" in capacidade.columns  # as unidades do CEG, com as datas
    assert not (c["pasta"] / "composicao_conjunto.csv").exists()  # fora de conjunto
    assert not (c["pasta"] / "evt_extraido.csv").exists()


def test_pch_em_conjunto_pela_geracao_do_conjunto(coletas) -> None:
    c = coletas["pch_alfa"]
    assert c["codigo"] == 0, c["manifesto"]["resumo"]
    resumo = c["manifesto"]["resumo"]
    assert resumo["serie_referencia"]["identificador"] == f"id_ons={bc.PCH['conjunto']}"
    assert resumo["conjuntos_nao_aplicaveis"] == ["evt", "indicadores", "disponibilidade", "hidrologia"]
    assert resumo["linhas_usina_sem_valor"] == 9480  # as linhas próprias da PCH, todas sem valor
    geracao = pd.read_parquet(c["pasta"] / "geracao_extraido.parquet")
    assert set(geracao["val_geracao"]) == {20.0}  # a série do conjunto
    complemento = pd.read_parquet(c["pasta"] / "geracao_complemento.parquet")
    assert set(complemento["nivel"]) == {"conjunto"}
    composicao = pd.read_csv(c["pasta"] / "composicao_conjunto.csv", sep=";", dtype=str, keep_default_na=False)
    assert set(composicao["ceg"]) == {bc.PCH["ceg"], bc.UTE_ANTIGA["ceg"]}
    trechos = pd.read_csv(c["pasta"] / "trechos.csv", sep=";", dtype=str, keep_default_na=False)
    assert list(trechos["composicao"]) == [bc.PCH["ceg"]]  # a térmica saiu antes do período
    assert list(trechos["nivel_geracao"]) == ["conjunto"]
    programacao = pd.read_parquet(c["pasta"] / "programacao_extraido.parquet")
    assert "cod_exibicaousina" in programacao.columns  # mais de um código


def test_datas_de_obtencao_com_os_conjuntos_da_usina(coletas) -> None:
    datas = pd.read_csv(coletas["pch_alfa"]["pasta"] / "datas_obtencao.csv", sep=";", dtype=str, keep_default_na=False)
    assert {"geracao-usina-2", "programacao_diaria", "modalidade-usina", "usina_conjunto",
            "capacidade-geracao"} <= set(datas["conjunto"])
    assert "reservatorio" not in set(datas["conjunto"])
