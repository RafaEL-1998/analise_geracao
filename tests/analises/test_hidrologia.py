"""Testes da análise hidrológica: faixas de afluência, perfil por hora do dia e resumos (Análises)."""

from __future__ import annotations

from typing import List

import pandas as pd
import pytest

from src.analises.hidrologia import (
    ACIMA_ENGOLIMENTO_USINA,
    ATE_UMA_UNIDADE,
    COM_PARADA_EVT,
    DEMAIS_DIAS,
    entre_unidades,
    SEM_DADO_HIDROLOGICO,
    classificar_faixas,
    perfil_hidrologico as perfil_hora_do_dia,
    resumir_faixas,
    resumo_mensal_hidrologia as resumo_mensal,
)


def _hid(valores: List[tuple], inicio: str = "2025-01-01 00:00") -> pd.DataFrame:
    """Série tratada (hora de início): (afluente, turbinada, vertida, nível) por hora."""
    instantes = pd.date_range(inicio, periods=len(valores), freq="h")
    return pd.DataFrame({"din_instante": instantes, "val_vazaoafluente": [v[0] for v in valores],
                         "val_vazaoturbinada": [v[1] for v in valores], "val_vazaovertida": [v[2] for v in valores],
                         "val_nivelmontante": [v[3] for v in valores], "val_niveljusante": 309.0, "val_volumeutil": 50.0,
                         "val_vazaodefluente": [v[1] + v[2] for v in valores], "val_vazaovertidanaoturbinavel": 0.0,
                         "qualidade": "OK"})


def _evt(valores: List[tuple], inicio: str = "2025-01-01 00:00") -> pd.DataFrame:
    """Base de EVT: (geração, EVT, turbinada, vertida) por hora."""
    instantes = pd.date_range(inicio, periods=len(valores), freq="h")
    return pd.DataFrame({"din_instante": instantes, "val_geracao": [v[0] for v in valores],
                         "val_energiavertidaturbinavel": [v[1] for v in valores],
                         "val_vazaoturbinada": [v[2] for v in valores], "val_vazaovertida": [v[3] for v in valores]})


def test_faixas_de_afluencia_nos_limites() -> None:
    hid = _hid([(163.01, 0, 100, 344.5), (163.0, 0, 100, 344.5), (81.51, 0, 50, 344.5), (81.5, 0, 50, 344.5),
                (None, 0, 50, 344.5), (60, 60, 0, 344.5)])
    evt = _evt([(0, 5.0, 0, 0), (0, 4.0, 0, 0), (0, 3.0, 0, 0), (0, 2.0, 0, 0), (0, 1.0, 0, 0), (20, 0.0, 0, 0)])
    faixas = classificar_faixas(hid, evt)
    assert faixas["faixa_afluencia"].tolist() == [ACIMA_ENGOLIMENTO_USINA, entre_unidades(),
                                                  entre_unidades(), ATE_UMA_UNIDADE, SEM_DADO_HIDROLOGICO]
    resumo = resumir_faixas(faixas, "Y")
    assert resumo["horas"].sum() == 5 and resumo["evt_mwh"].sum() == pytest.approx(15.0)
    assert set(resumo["faixa_afluencia"]) == {ACIMA_ENGOLIMENTO_USINA, entre_unidades(), ATE_UMA_UNIDADE,
                                              SEM_DADO_HIDROLOGICO}


def test_perfil_por_hora_do_dia_e_resumo_mensal() -> None:
    # 01/01: parada com EVT às 10h (nível sobe); 02/01: sem parada
    dia1 = [(100, 80, 20, 344.2 + 0.02 * h) for h in range(24)]
    dia2 = [(100, 100, 0, 344.2) for _ in range(24)]
    hid = _hid(dia1 + dia2)
    evt = _evt([(0 if h == 10 else 24, 3.0 if h == 10 else 0.0, 80, 20) for h in range(24)] + [(30, 0, 100, 0)] * 24)
    perfil = perfil_hora_do_dia(hid, evt)
    assert set(perfil["grupo_dias"]) == {COM_PARADA_EVT, DEMAIS_DIAS} and len(perfil) == 48
    linha = perfil[(perfil["grupo_dias"] == COM_PARADA_EVT) & (perfil["hora"] == 23)].iloc[0]
    assert linha["dias"] == 1 and linha["nivel_montante_medio_m"] == pytest.approx(344.2 + 0.46)
    mensal = resumo_mensal(hid).iloc[0]
    assert mensal["horas"] == 48 and mensal["afluencia_maxima_m3s"] == 100
    assert mensal["horas_afluencia_acima_engolimento"] == 0
    assert mensal["nivel_montante_min_m"] == pytest.approx(344.2)
