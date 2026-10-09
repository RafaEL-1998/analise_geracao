"""Testes da análise dos indicadores oficiais: resumos, decomposição das taxas e constatações (Análises)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.analises.etapa import analisar
from src.analises.evt import preparar_dados
from src.analises.indicadores import decompor_taxas
from src.conferencia.indicadores import conferencia_dispf_horas, conferencia_teifa_teip, recalcular_taxas
from src.tratamento.indicadores import IndicadoresONS


def _conferencias(ind: IndicadoresONS) -> dict:
    return {"dispf_horas": conferencia_dispf_horas(ind), "teifa_teip": conferencia_teifa_teip(ind)}


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


def test_recalculo_e_decomposicao_das_taxas() -> None:
    ind = _indicadores_sinteticos()
    recalculo = recalcular_taxas(ind.horas_estado, ind.taxas).set_index("mes")
    # jan/2024 não tem 60 meses de horas; fev/2024 tem
    assert pd.isna(recalculo.loc["2024-01-01", "teifa_recalculada"])
    assert recalculo.loc["2024-02-01", "diferenca_teifa_pp"] == pytest.approx(0.0, abs=1e-9)
    assert recalculo.loc["2024-02-01", "diferenca_teip_pp"] == pytest.approx(0.0, abs=1e-9)

    dec = decompor_taxas(ind.horas_estado, pd.Timestamp("2024-02-01"))
    teifa = dec[dec["taxa"] == "TEIFa"]
    assert teifa["contribuicao_pp"].sum() == pytest.approx(ind.taxas["teifa"].iloc[-1] * 100)
    assert teifa["participacao_pct"].sum() == pytest.approx(100.0)
    maior = teifa.loc[teifa["contribuicao_pp"].idxmax()]
    assert (maior["ug"], maior["parcela"]) == (2, "HEDF")


@pytest.fixture
def resultados_com_indicadores(df_sintetico: pd.DataFrame, tmp_path: Path):
    df = preparar_dados(df_sintetico)
    ind = _indicadores_sinteticos()
    return analisar(df, _conferencias(ind), tmp_path / "sem_auditoria.csv", indicadores=ind)


def test_analise_inclui_constatacoes_dos_indicadores(resultados_com_indicadores) -> None:
    res = resultados_com_indicadores
    titulos = [t for t, _ in res.achados]
    assert len(titulos) == 14
    assert titulos[2:4] == ["Indicadores oficiais de disponibilidade (ONS)", "Estados operativos das unidades geradoras (ONS)"]
    textos = dict(res.achados)
    assert "UG2" in textos["Estados operativos das unidades geradoras (ONS)"]
    assert "reserva desligada" in textos["Estados operativos das unidades geradoras (ONS)"]

    # DISPF da usina = média ponderada por horas e potência; UG1 perde 10 h/mês, UG2 perde 50 h em jan/2024
    horas_meses = {"2023-11-01": 720, "2023-12-01": 744, "2024-01-01": 744, "2024-02-01": 696}
    perdido = 10 * 4 + 50
    esperado = 100 - perdido / (2 * sum(horas_meses.values())) * 100
    assert res.ons["disp_periodo"]["dispf_pct"] == pytest.approx(esperado)
    assert res.ons["recalculo_resumo"]["meses"] == 1


def test_frase_da_teifa_cita_os_meses_reproduzidos_pela_conferencia(resultados_com_indicadores) -> None:
    """Decisão de 08/10/2026 (FR-044): "em X dos N meses" quando a Conferência não reproduziu todos."""
    from src.analises.constatacoes import montar_achados

    res = resultados_com_indicadores
    assert res.ons["recalculo_resumo"] == {"meses": 1, "reproduzidos": 1,
                                           "diferenca_maxima_pp": pytest.approx(0.0, abs=1e-9)}
    res.ons["recalculo_resumo"] = {"meses": 21, "reproduzidos": 19, "diferenca_maxima_pp": 0.0123}
    texto = dict(montar_achados(res))["Estados operativos das unidades geradoras (ONS)"]
    assert "reproduzem a TEIFa e a TEIP publicadas em 19 dos 21 meses" in texto
    assert "tolerância de 0,001 p.p." in texto
