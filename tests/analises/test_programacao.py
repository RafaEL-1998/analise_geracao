"""Testes do cruzamento da programação diária com a operação verificada (Análises)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.analises.etapa import analisar
from src.analises.evt import preparar_dados
from src.analises.programacao import (
    GERANDO_COM_PROGRAMACAO,
    GERANDO_PROGRAMACAO_ZERO,
    PARADA_EVT_PROGRAMACAO_POSITIVA,
    PARADA_EVT_PROGRAMACAO_ZERO,
    PARADA_SEM_EVT,
    classificar_horas,
    eventos_desvio,
    perfil_hora_do_dia,
    resumo_mensal,
)
from src.tratamento.programacao import ProgramacaoONS


def _operacao_e_programacao() -> tuple:
    """Dez horas com todas as classes: 3 h paradas com EVT e programação zero (9h a 11h), 2 h de desvio."""
    t = pd.date_range("2026-07-01 08:00", periods=10, freq="h")
    ger = [20, 0, 0, 0, 0, 0, 0.5, 15, 15, 20]
    evt = [0, 2, 2, 2, 1, 0, 0, 0, 0, 0]
    prog = [22, 0, 0, 0, 22, 22, 0, 0, 22, 22]
    operacao = pd.DataFrame({"din_instante": t, "val_geracao": ger, "val_energiavertidaturbinavel": evt,
                             "val_disponibilidade": 46.0})
    horaria = pd.DataFrame({"din_instante": t, "geracao_programada_mw": prog, "patamares": 2})
    return operacao, horaria


def test_classificacao_resumo_eventos_e_perfil() -> None:
    operacao, horaria = _operacao_e_programacao()
    c = classificar_horas(operacao, horaria)
    assert c["classe"].tolist() == [
        GERANDO_COM_PROGRAMACAO, PARADA_EVT_PROGRAMACAO_ZERO, PARADA_EVT_PROGRAMACAO_ZERO, PARADA_EVT_PROGRAMACAO_ZERO,
        PARADA_EVT_PROGRAMACAO_POSITIVA, PARADA_SEM_EVT, PARADA_SEM_EVT, GERANDO_PROGRAMACAO_ZERO,
        GERANDO_COM_PROGRAMACAO, GERANDO_COM_PROGRAMACAO,
    ]
    m = resumo_mensal(c).iloc[0]
    assert m["horas_parada_com_evt"] == 4
    assert m["horas_parada_evt_programacao_zero"] == 3
    assert m["evt_parada_programacao_zero_mwh"] == pytest.approx(6.0)
    assert m["participacao_evt_programacao_zero_pct"] == pytest.approx(6 / 7 * 100)
    assert m["horas_desvio_programacao"] == 2

    eventos = eventos_desvio(c)
    assert eventos["duracao_h"].tolist() == [2]
    assert eventos["inicio"].iloc[0] == pd.Timestamp("2026-07-01 12:00")

    perfil = perfil_hora_do_dia(c).set_index("hora")
    assert perfil.loc[[9, 10, 11], "horas"].tolist() == [1, 1, 1]
    assert perfil["horas"].sum() == 3


@pytest.fixture
def resultados_com_programacao(df_sintetico: pd.DataFrame, tmp_path: Path):
    """Programação de 22 MW em todo o período, zero durante a parada de 10/02/2024 (9h a 13h)."""
    df = preparar_dados(df_sintetico)
    horaria = pd.DataFrame({"din_instante": df["din_instante"], "geracao_programada_mw": 22.0, "patamares": 2})
    parada = (horaria["din_instante"] >= "2024-02-10 09:00") & (horaria["din_instante"] <= "2024-02-10 13:00")
    horaria.loc[parada, "geracao_programada_mw"] = 0.0
    horaria = horaria[horaria["din_instante"] != pd.Timestamp("2024-01-15 10:00")]  # hora sem programação
    prog = ProgramacaoONS(horaria=horaria, dias_ausentes=pd.DataFrame({"dia": [pd.Timestamp("2024-01-20")]}),
                          auditoria=pd.DataFrame({"arquivo": ["x"], "status": ["PROCESSADO"]}))
    return analisar(df, {}, tmp_path / "a.csv", programacao=prog)


def test_analise_inclui_a_constatacao_da_programacao(resultados_com_programacao) -> None:
    res = resultados_com_programacao
    titulos = [t for t, _ in res.achados]
    assert len(titulos) == 13
    assert titulos[7] == "Programação diária do ONS"
    p = res.programacao["periodo"]
    assert p["horas_parada_evt_programacao_zero"] == 5
    assert p["pct_horas_programacao_zero"] == pytest.approx(100.0)
    assert p["horas_base_sem_programacao"] == 1
    # 30 h de indisponibilidade total com programação de 22 MW = um evento de desvio
    assert p["eventos_desvio"] == 1 and p["horas_desvio"] == 30
    texto = dict(res.achados)["Programação diária do ONS"]
    assert "ficou parada com EVT em 5 h; em 5 delas (100,0%)" in texto
    assert "reprogramações em tempo real" in texto
