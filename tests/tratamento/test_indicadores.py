"""Testes do tratamento dos indicadores por unidade geradora e das taxas TEIFa e TEIP."""

from __future__ import annotations

import pandas as pd
import pytest

from src.tratamento.indicadores import (
    IndicadoresONS,
    juntar_taxas_operativas,
    numero_ug,
    recortar_periodo,
    tratar_horas_estado,
    tratar_taxas,
)


def test_numero_da_unidade_no_nome() -> None:
    assert numero_ug("UG   24 MW SAO DOMINGOS              2 MS") == 2
    assert numero_ug("UG 10P3 MW CURUA-UNA                 3 PA   ") == 3


def test_horas_estado_usa_a_versao_mais_recente() -> None:
    bruto = pd.DataFrame({
        "nom_unidadegeradora": ["UG   24 MW SAO DOMINGOS              1 MS"] * 4,
        "dat_periodo": ["03/2026"] * 4,
        "nom_tpinsumo": ["HP", "HS", "HDF", "HDF"],
        "val_parametro": ["744.0", "740.0", "9.0", "4.0"],
        "num_versao": ["1.0", "1.0", "1.0", "2.0"],
    })
    horas = tratar_horas_estado(bruto)
    linha = horas.iloc[0]
    assert linha["mes"] == pd.Timestamp("2026-03-01") and linha["ug"] == 1
    assert linha["HDF"] == 4.0 and linha["num_versao"] == 2.0
    assert linha["residuo_identidade_h"] == pytest.approx(0.0)


def test_taxas_usam_a_versao_mais_recente() -> None:
    bruto = pd.DataFrame({
        "din_mes": ["2026-08-01"] * 3,
        "nom_taxa": ["TEIFa", "TEIFa", "TEIP"],
        "val_taxa": ["0.05", "0.041", "0.048"],
        "num_versao": ["1.0", "2.0", "1.0"],
        "din_calculo": ["2026-09-01 10:00:00", "2026-09-11 16:55:06", "2026-09-11 16:55:06"],
    })
    taxas = tratar_taxas(bruto)
    assert len(taxas) == 1
    assert taxas.iloc[0]["teifa"] == pytest.approx(0.041)
    assert taxas.iloc[0]["teip"] == pytest.approx(0.048)


def _taxas_publicadas(nomes: tuple, meses: list, valores: list) -> pd.DataFrame:
    linhas = [{"din_mes": mes, "nom_taxa": nome, "val_taxa": valor, "num_versao": "1.0",
               "din_calculo": "2026-09-11 16:55:06"}
              for mes, par in zip(meses, valores) for nome, valor in zip(nomes, par)]
    return pd.DataFrame(linhas)


def test_taxas_operativas_com_sufixo_em_qualquer_caixa() -> None:
    bruto = _taxas_publicadas(("TEIFa_oper", "TEIP_Oper"), ["2026-08-01"], [("0.12", "0.59")])
    oper = tratar_taxas(bruto, sufixo="_oper")
    assert list(oper.columns) == ["mes", "teifa_oper", "teip_oper", "num_versao_oper", "din_calculo_oper"]
    assert oper.iloc[0]["teifa_oper"] == pytest.approx(0.12)
    assert oper.iloc[0]["teip_oper"] == pytest.approx(0.59)


def test_juncao_pelos_meses_das_oficiais() -> None:
    oficiais = tratar_taxas(_taxas_publicadas(("TEIFa", "TEIP"), ["2026-07-01", "2026-08-01"],
                                              [("0.30", "0.70"), ("0.31", "0.71")]))
    oper = tratar_taxas(_taxas_publicadas(("TEIFa_oper", "TEIP_oper"), ["2026-07-01", "2026-06-01"],
                                          [("0.13", "0.59"), ("0.12", "0.58")]), sufixo="_oper")
    juntas = juntar_taxas_operativas(oficiais, oper)
    assert list(juntas["mes"]) == [pd.Timestamp("2026-07-01"), pd.Timestamp("2026-08-01")]
    assert juntas.iloc[0]["teifa_oper"] == pytest.approx(0.13)
    assert pd.isna(juntas.iloc[1]["teifa_oper"])  # mês da oficial sem a operativa


def test_sem_operativas_a_tabela_fica_como_a_das_oficiais() -> None:
    oficiais = tratar_taxas(_taxas_publicadas(("TEIFa", "TEIP"), ["2026-08-01"], [("0.04", "0.05")]))
    juntas = juntar_taxas_operativas(oficiais, tratar_taxas(pd.DataFrame(), sufixo="_oper"))
    assert list(juntas.columns) == ["mes", "teifa", "teip", "num_versao", "din_calculo"]


def _horas_sinteticas() -> pd.DataFrame:
    linhas = []
    for mes in pd.date_range("2019-03-01", "2024-02-01", freq="MS"):
        hp = mes.days_in_month * 24.0
        # UG1: 6 h programadas e 4 h forçadas por mês; UG2: 20 h equivalentes de limitação forçada e 50 h em reserva
        linhas.append({"mes": mes, "ug": 1, "HP": hp, "HS": hp - 10, "HRD": 0.0, "HDP": 6.0, "HDF": 4.0,
                       "HDCE": 0.0, "HEDP": 0.0, "HEDF": 0.0})
        linhas.append({"mes": mes, "ug": 2, "HP": hp, "HS": hp - 70, "HRD": 50.0, "HDP": 0.0, "HDF": 0.0,
                       "HDCE": 0.0, "HEDP": 0.0, "HEDF": 20.0})
    h = pd.DataFrame(linhas)
    h["num_versao"] = 1.0
    h["residuo_identidade_h"] = h["HP"] - h[["HS", "HRD", "HDP", "HDF", "HDCE", "HEDP", "HEDF"]].sum(axis=1)
    h["potencia_mw"] = 24.0
    return h


def _indicadores_sinteticos() -> IndicadoresONS:
    horas = _horas_sinteticas()
    h = horas[horas["mes"] >= "2023-11-01"]
    mensal = h[["mes", "ug", "HP", "HDP", "HDF"]].copy()
    mensal["indisppf"] = mensal["HDP"] / mensal["HP"] * 100
    mensal["indispff"] = mensal["HDF"] / mensal["HP"] * 100
    # jan/2024, UG2: as 50 h de reserva aparecem como indisponibilidade programada no DISPF
    sel = (mensal["mes"] == "2024-01-01") & (mensal["ug"] == 2)
    mensal.loc[sel, "indisppf"] = 50 / 744 * 100
    mensal["dispf"] = 100 - mensal["indisppf"] - mensal["indispff"]
    mensal["potencia_mw"] = 24.0
    mensal = mensal.drop(columns=["HP", "HDP", "HDF"])
    anual = pd.DataFrame({"ano": [2023, 2023, 2024, 2024], "ug": [1, 2, 1, 2], "dispf": [98.6, 100, 98.6, 96.4],
                          "indisppf": [0.8, 0, 0.8, 3.6], "indispff": [0.6, 0, 0.6, 0], "dmdff": [4.0, 0, 4.0, 0]})
    w = horas.tail(120)
    teifa = (w["HDF"] + w["HEDF"]).sum() / (w["HP"] - w["HDP"] - w["HEDP"]).sum()
    teip = (w["HDP"] + w["HEDP"]).sum() / w["HP"].sum()
    taxas = pd.DataFrame({"mes": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")],
                          "teifa": [teifa, teifa], "teip": [teip, teip], "num_versao": [1.0, 1.0]})
    return IndicadoresONS(ug_mensal=mensal, ug_anual=anual, horas_estado=horas, taxas=taxas,
                          )


def test_recorte_no_periodo_da_base() -> None:
    recortado = recortar_periodo(_indicadores_sinteticos(), pd.Timestamp("2023-11-15 05:00"), pd.Timestamp("2024-01-10"))
    assert recortado.horas_estado["mes"].min() == pd.Timestamp("2023-11-01")
    assert recortado.horas_estado["mes"].max() == pd.Timestamp("2024-01-01")
    assert sorted(recortado.ug_anual["ano"].unique()) == [2023, 2024]
    assert list(recortado.taxas["mes"]) == [pd.Timestamp("2024-01-01")]
