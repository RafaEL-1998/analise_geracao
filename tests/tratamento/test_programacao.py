"""Testes da programação horária no Tratamento de dados."""

from __future__ import annotations

import pandas as pd
import pytest

from src.tratamento.programacao import programacao_horaria


def test_programacao_horaria_usa_a_media_dos_patamares() -> None:
    patamares = pd.DataFrame({
        "dia": pd.Timestamp("2026-07-01"),
        "num_patamar": [1, 2, 3],
        "geracao_programada_mw": [10.0, 20.0, 22.0],
        "arquivo_origem": "x",
    })
    h = programacao_horaria(patamares).set_index("din_instante")
    assert h.loc["2026-07-01 00:00", "geracao_programada_mw"] == pytest.approx(15.0)
    assert h.loc["2026-07-01 00:00", "patamares"] == 2
    assert h.loc["2026-07-01 01:00", "patamares"] == 1
