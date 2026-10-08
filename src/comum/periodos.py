"""Agrupamento de horas consecutivas em períodos, usado pelas conferências e pelas análises."""

from __future__ import annotations

import pandas as pd


def periodos_continuos(horas: pd.DataFrame, coluna_diferenca: str) -> pd.DataFrame:
    """Agrupa horas consecutivas (passo de 1 h) em períodos, com a diferença média e máxima de cada um."""
    colunas = ["inicio", "fim", "horas", "diferenca_media_mw", "diferenca_maxima_mw"]
    if horas.empty:
        return pd.DataFrame(columns=colunas)
    h = horas.sort_values("din_instante")
    grupo = (h["din_instante"].diff() != pd.Timedelta(hours=1)).cumsum()
    blocos = h.groupby(grupo.values).agg(
        inicio=("din_instante", "min"), fim=("din_instante", "max"), horas=("din_instante", "size"),
        diferenca_media_mw=(coluna_diferenca, "mean"), diferenca_maxima_mw=(coluna_diferenca, "max"),
    )
    return blocos.reset_index(drop=True)[colunas]
