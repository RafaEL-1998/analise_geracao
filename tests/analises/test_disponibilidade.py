"""Testes da análise da disponibilidade operacional e sincronizada (Análises)."""

from __future__ import annotations

from typing import List

import pandas as pd
import pytest

from src.analises.disponibilidade import classificar_horas_paradas, resumir_disponibilidade as resumir


def _disp(valores: List[tuple], inicio: str = "2025-01-01 00:00") -> pd.DataFrame:
    """Série horária tratada: (operacional, sincronizada) por hora, instalada 48 MW, qualidade OK."""
    instantes = pd.date_range(inicio, periods=len(valores), freq="h")
    return pd.DataFrame({"din_instante": instantes, "val_potenciainstalada": 48.0,
                         "val_dispoperacional": [v[0] for v in valores], "val_dispsincronizada": [v[1] for v in valores],
                         "qualidade": "OK", "arquivo_origem": "D.csv"})


def _evt(valores: List[tuple], inicio: str = "2025-01-01 00:00") -> pd.DataFrame:
    """Base de EVT: (geração, disponibilidade declarada, EVT) por hora."""
    instantes = pd.date_range(inicio, periods=len(valores), freq="h")
    return pd.DataFrame({"din_instante": instantes, "val_geracao": [v[0] for v in valores],
                         "val_disponibilidade": [v[1] for v in valores],
                         "val_energiavertidaturbinavel": [v[2] for v in valores]})


def test_classificacao_das_horas_paradas() -> None:
    disp = _disp([(43.0, 0.0), (43.0, 24.0), (43.0, 0.0), (43.0, 0.0), (43.0, 24.0), (43.0, 0.5)])
    disp.loc[5, "qualidade"] = "D1"  # hora sinalizada fica fora
    evt = _evt([(0, 43, 5.0), (0.5, 43, 0), (0, 43, 0), (30, 43, 2.0), (1.0, 43, 1.0), (0, 43, 1.0)])
    programacao = pd.DataFrame({"din_instante": pd.to_datetime(["2025-01-01 00:00", "2025-01-01 01:00"]),
                                "classe": ["PARADA_EVT_PROGRAMACAO_ZERO", "PARADA_SEM_EVT"]})
    paradas = classificar_horas_paradas(disp, evt, programacao)
    assert len(paradas) == 4  # 00h, 01h, 02h e 04h (03h está gerando; 05h tem qualidade D1)
    assert paradas["sincronizacao"].tolist() == ["NAO_SINCRONIZADA", "SINCRONIZADA", "NAO_SINCRONIZADA", "SINCRONIZADA"]
    assert paradas["evt"].tolist() == ["COM_EVT", "SEM_EVT", "SEM_EVT", "COM_EVT"]
    assert paradas["classe_programacao"].tolist() == ["PARADA_EVT_PROGRAMACAO_ZERO", "PARADA_SEM_EVT",
                                                      "SEM_PROGRAMACAO", "SEM_PROGRAMACAO"]
    assert paradas.groupby(["sincronizacao", "evt", "classe_programacao"]).size().sum() == len(paradas)


def test_resumo_mensal_com_reserva_desligada() -> None:
    disp = _disp([(48.0, 24.0)] * 24 + [(48.0, 48.0)] * 24, inicio="2025-01-31 00:00")  # 31/01 e 01/02
    evt = _evt([(24.0, 48.0, 0)] * 24 + [(0.0, 48.0, 0)] * 24, inicio="2025-01-31 00:00")
    horas_estado = pd.DataFrame({"mes": pd.to_datetime(["2025-01-01", "2025-01-01", "2025-02-01"]), "ug": [1, 2, 1],
                                 "HRD": [20.0, 4.0, 0.0], "potencia_mw": [24.0, 24.0, 24.0]})
    mensal = resumir(disp, evt, horas_estado, "M").set_index("periodo")
    jan, fev = mensal.loc["2025-01"], mensal.loc["2025-02"]
    assert jan["horas_comuns"] == 24 and jan["disp_sincronizada_media_mw"] == pytest.approx(24.0)
    assert jan["capacidade_nao_sincronizada_media_mw"] == pytest.approx(24.0)
    assert jan["capacidade_nao_sincronizada_mwh"] == pytest.approx(576.0)
    assert jan["reserva_desligada_teif_mwh"] == pytest.approx(576.0)  # (20 + 4) h × 24 MW
    assert jan["diferenca_mwh"] == pytest.approx(0.0)
    assert fev["horas_paradas"] == 24 and fev["horas_paradas_sincronizadas"] == 24
    assert fev["horas_paradas_sem_sincronizacao"] == 0
    anual = resumir(disp, evt, None, "Y")
    assert anual["periodo"].tolist() == ["2025"] and pd.isna(anual.loc[0, "reserva_desligada_teif_mwh"])
