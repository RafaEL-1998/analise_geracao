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


def _patamares(dia: str, codigos: dict) -> pd.DataFrame:
    return pd.DataFrame([{"dia": pd.Timestamp(dia), "num_patamar": n, "geracao_programada_mw": valor,
                          "cod_exibicaousina": codigo}
                         for codigo, valor in codigos.items() for n in (1, 2)])


def test_soma_dos_codigos_vigentes_no_dia_quando_o_conjunto_troca_os_codigos() -> None:
    """FR-026 (o Conj. Chapadão trocou os quatro códigos em 07/2025): cada código vale do primeiro ao último
    dia em que aparece; o patamar soma os códigos vigentes no dia, e o código vigente sem valor deixa a soma ausente."""
    from src.tratamento.programacao import somar_codigos

    patamares = pd.concat([
        _patamares("2025-07-01", {"A-1": 10.0, "A-2": 5.0}),
        _patamares("2025-07-02", {"A-1": 10.0}),  # A-2 vigente (aparece depois) e sem a linha: soma ausente
        _patamares("2025-07-03", {"A-1": 10.0, "A-2": 5.0}),
        _patamares("2025-07-05", {"B-1": 7.0, "B-2": 8.0}),  # os códigos novos, sem os antigos
        _patamares("2025-07-06", {"B-1": 7.0, "B-2": float("nan")}),  # B-2 sem valor: soma ausente
        _patamares("2025-07-07", {"B-1": 7.0, "B-2": 8.0}),
    ], ignore_index=True)
    somas = somar_codigos(patamares).groupby("dia")["geracao_programada_mw"].first()
    assert somas[pd.Timestamp("2025-07-01")] == 15.0 and somas[pd.Timestamp("2025-07-05")] == 15.0
    assert pd.isna(somas[pd.Timestamp("2025-07-02")]) and pd.isna(somas[pd.Timestamp("2025-07-06")])
    assert somas[pd.Timestamp("2025-07-07")] == 15.0
