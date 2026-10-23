"""Base horária comum das usinas sem EVT (plano do Tratamento de dados, D15; data-model, seção 2.7).

O Tratamento grava ``base_horaria.csv`` com a geração da série de referência (com o nível), a disponibilidade, a
programação, o trecho e as sinalizações de cada hora. Sinalização não exclui registro (princípio V); as horas ausentes
ficam listadas em ``geracao_ausencias.csv``, nunca preenchidas.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import pytest

from src.comum import caminhos
from src.tratamento.base_horaria import COLUNAS_BASE_HORARIA, montar_base_horaria
from src.tratamento.programacao import programacao_horaria
from src.tratamento.series import SerieConjunto
from tests.fixtures import brutos_catalogo as bc
from tests.fixtures.sem_evt import projeto_sem_evt

HORAS_AUSENTES = pd.date_range("2026-03-10 00:00", periods=6, freq="h")  # tiradas da geração da UTE


def _tirar_horas_da_ute(raw: Path) -> None:
    arquivo = raw / "geracao_usina_2" / "GERACAO_USINA-2_2026_03.parquet"
    tabela = pd.read_parquet(arquivo)
    fora = (tabela["id_ons"] == bc.UTE["id_ons"]) & tabela["din_instante"].isin(HORAS_AUSENTES)
    tabela[~fora].to_parquet(arquivo, index=False)


@pytest.fixture(scope="module")
def usinas(tmp_path_factory) -> Dict[str, Dict[str, Any]]:
    return projeto_sem_evt(tmp_path_factory.mktemp("projeto"), ["coleta", "tratamento"], preparar=_tirar_horas_da_ute)


def _base(usina: Dict[str, Any]) -> pd.DataFrame:
    caminho = usina["pasta"] / "tratamento" / caminhos.ARQUIVOS_TRATAMENTO["base_horaria"]
    return pd.read_csv(caminho, sep=";", keep_default_na=False, na_values=[""], parse_dates=["din_instante"])


# ---------------------------------------------------------------------------
# Na etapa (Coleta e Tratamento das usinas fictícias)
# ---------------------------------------------------------------------------


def test_colunas_e_horas_da_termica(usinas) -> None:
    u = usinas["ute_beta"]
    assert u["codigos"] == {"coleta": 0, "tratamento": 0}, u["manifestos"]
    base = _base(u)
    assert list(base.columns) == COLUNAS_BASE_HORARIA == [
        "din_instante", "geracao_mw", "nivel", "disponibilidade_operacional_mw", "disponibilidade_sincronizada_mw",
        "geracao_programada_mw", "trecho", "sinalizacoes"]
    assert len(base) == 9480 - len(HORAS_AUSENTES)
    assert set(base["nivel"]) == {"usina"} and set(base["geracao_mw"]) == {100.0}
    assert set(base["trecho"]) == {1}
    assert base["din_instante"].is_monotonic_increasing and not base["din_instante"].duplicated().any()


def test_disponibilidade_e_sinalizacao_sem_excluir(usinas) -> None:
    base = _base(usinas["ute_beta"])
    com_disp = base[base["disponibilidade_operacional_mw"].notna()]
    assert len(com_disp) == 24  # o arquivo de disponibilidade traz as primeiras 24 horas de 09/2026
    assert set(com_disp["disponibilidade_operacional_mw"]) == {50.0}
    assert set(com_disp["disponibilidade_sincronizada_mw"]) == {40.0}
    # geração 100 MW acima da disponibilidade declarada de 50 MW: regra R7, sinalizada e mantida (princípio V)
    assert set(com_disp["sinalizacoes"]) == {"R7"}
    assert set(base.loc[base["disponibilidade_operacional_mw"].isna(), "sinalizacoes"].fillna("")) == {""}
    assert base["geracao_programada_mw"].isna().all()  # a programação sintética é de 10/2026, fora do período


def test_ausencias_listadas_e_nao_preenchidas(usinas) -> None:
    u = usinas["ute_beta"]
    base = _base(u)
    assert not base["din_instante"].isin(HORAS_AUSENTES).any()
    ausencias = pd.read_csv(u["pasta"] / "tratamento" / caminhos.ARQUIVOS_TRATAMENTO["geracao_ausencias"], sep=";")
    horas = ausencias[ausencias["tipo"] == "HORAS"]
    assert list(horas["horas"]) == [len(HORAS_AUSENTES)]
    assert pd.Timestamp(horas.iloc[0]["inicio"]) == HORAS_AUSENTES[0]
    resumo = u["manifestos"]["tratamento"]["resumo"]
    assert resumo["base_horaria"]["horas"] == len(base)
    assert resumo["base_horaria"]["horas_ausentes"] == len(HORAS_AUSENTES)
    assert resumo["base_horaria"]["sinalizacoes"] == {"R7": 24}
    assert resumo["base_horaria"]["niveis"] == {"usina": len(base)}


def test_sem_arquivos_de_evt_nas_usinas_sem_evt(usinas) -> None:
    for slug, u in usinas.items():
        pasta = u["pasta"] / "tratamento"
        assert not (pasta / caminhos.ARQUIVOS_TRATAMENTO["evt_parquet"]).exists(), slug
        assert not (pasta / caminhos.ARQUIVOS_TRATAMENTO["validacao_csv"]).exists(), slug
        resumo = u["manifestos"]["tratamento"]["resumo"]
        assert "evt" not in resumo and resumo["periodo"] == u["manifestos"]["coleta"]["resumo"]["periodo"]


def test_pch_em_conjunto_com_nivel_conjunto(usinas) -> None:
    u = usinas["pch_alfa"]
    assert u["codigos"] == {"coleta": 0, "tratamento": 0}, u["manifestos"]
    base = _base(u)
    assert len(base) == 9480
    assert set(base["nivel"]) == {"conjunto"} and set(base["geracao_mw"]) == {20.0}
    assert base["disponibilidade_operacional_mw"].isna().all()  # sem disponibilidade: cobertura ausente
    assert set(base["sinalizacoes"].fillna("")) == {""}
    resumo = u["manifestos"]["tratamento"]["resumo"]
    assert set(resumo) >= {"periodo", "base_horaria", "geracao", "programacao"}
    assert "disponibilidade" not in resumo and "indicadores" not in resumo  # conjuntos não coletados


# ---------------------------------------------------------------------------
# Montagem (unidade)
# ---------------------------------------------------------------------------


def _serie(valores: Dict[str, Any], horas: pd.DatetimeIndex, qualidade: Any = "OK") -> SerieConjunto:
    return SerieConjunto(horaria=pd.DataFrame({"din_instante": horas, **valores, "qualidade": qualidade}))


def test_nivel_trecho_e_sinalizacoes_por_hora() -> None:
    horas = pd.date_range("2026-01-01", periods=6, freq="h")
    geracao = _serie({"val_geracao": [10.0, 10.0, np.nan, 60.0, 10.0, 10.0]}, horas,
                     ["OK", "OK", "G1", "OK", "OK", "OK"])
    complemento = pd.DataFrame({"din_instante": horas, "cod_modalidadeoperacao": "TIPO I",
                                "nivel": ["usina", "usina", "usina", "usina", "conjunto", "conjunto"]})
    trechos = pd.DataFrame({"trecho": [1, 2], "inicio": ["2026-01-01 00:00:00", "2026-01-01 04:00:00"],
                            "fim": ["2026-01-01 03:00:00", "2026-01-01 05:00:00"]})
    disponibilidade = _serie({"val_dispoperacional": [50.0] * 6, "val_dispsincronizada": [40.0, 40.0, 40.0, 40.0,
                                                                                         60.0, 40.0]}, horas,
                             ["OK", "OK", "OK", "OK", "D1", "OK"])
    programacao = pd.DataFrame({"din_instante": horas[:3], "geracao_programada_mw": [12.0, 11.0, 0.0]})
    base = montar_base_horaria(geracao, complemento, trechos, disponibilidade, programacao)
    assert list(base.columns) == COLUNAS_BASE_HORARIA
    assert list(base["trecho"]) == [1, 1, 1, 1, 2, 2]
    assert list(base["nivel"]) == ["usina", "usina", "usina", "usina", "conjunto", "conjunto"]
    # G1 (não numérico), R7 só com geração e disponibilidade da usina, D1 da disponibilidade mantida
    assert list(base["sinalizacoes"]) == ["", "", "G1", "R7", "D1", ""]
    assert base["geracao_programada_mw"].iloc[:3].tolist() == [12.0, 11.0, 0.0]
    assert base["geracao_programada_mw"].iloc[3:].isna().all()
    assert math.isnan(base["geracao_mw"].iloc[2])  # o valor ausente fica ausente


def test_sem_complemento_usa_o_nivel_padrao_e_sem_trechos_fica_vazio() -> None:
    horas = pd.date_range("2026-01-01", periods=3, freq="h")
    base = montar_base_horaria(_serie({"val_geracao": [1.0, 2.0, 3.0]}, horas), pd.DataFrame(), pd.DataFrame(),
                               nivel_padrao="conjunto")
    assert set(base["nivel"]) == {"conjunto"}
    assert base["trecho"].isna().all()
    assert base["disponibilidade_operacional_mw"].isna().all() and base["geracao_programada_mw"].isna().all()


def test_programacao_com_varios_codigos_soma_por_patamar() -> None:
    dia = pd.Timestamp("2026-01-01")
    patamares = pd.DataFrame({
        "dia": dia, "num_patamar": [1, 2, 1, 2, 3, 4, 3],
        "geracao_programada_mw": [10.0, 12.0, 5.0, 7.0, 4.0, 4.0, np.nan],
        "cod_exibicaousina": ["A", "A", "B", "B", "A", "A", "B"],
    })
    horaria = programacao_horaria(patamares)
    # hora 0: (10 + 5 + 12 + 7) / 2; hora 1: o patamar 3 sem o valor de B e o 4 sem a linha de B não somam
    assert horaria["geracao_programada_mw"].iloc[0] == pytest.approx(17.0)
    assert math.isnan(horaria["geracao_programada_mw"].iloc[1])
    assert list(horaria["patamares"]) == [2, 2]


def test_programacao_de_um_codigo_como_hoje() -> None:
    patamares = pd.DataFrame({"dia": pd.Timestamp("2026-01-01"), "num_patamar": [1, 2],
                              "geracao_programada_mw": [10.0, 20.0]})
    horaria = programacao_horaria(patamares)
    assert horaria["geracao_programada_mw"].tolist() == [15.0] and horaria["patamares"].tolist() == [2]
