"""Conferência da disponibilidade: declarada (base de EVT) × operacional (Disponibilidade por usina), hora a hora.

Spec da Conferência, FR-011. As horas sinalizadas pelo Tratamento (regras D1 a D4) ficam fora e são contadas.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import pandas as pd

from src.comum.periodos import periodos_continuos
from src.comum.regras import TOLERANCIA_COINCIDENCIA_MW
from src.conferencia.resultado import ResultadoConferencia, diferenca_absoluta, nao_aplicavel
from src.tratamento.series import SerieConjunto

BASES = ("base de EVT (val_disponibilidade)", "Disponibilidade por usina (val_dispoperacional)")


def validas(disp: pd.DataFrame) -> pd.DataFrame:
    """Horas de Disponibilidade por usina sem sinalização do Tratamento."""
    if "qualidade" in disp.columns:
        return disp[disp["qualidade"] == "OK"]
    return disp


def conferir_com_evt(
    disp: pd.DataFrame,
    df: pd.DataFrame,
    tolerancia: float = TOLERANCIA_COINCIDENCIA_MW,
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """Disponibilidade operacional (ONS) × disponibilidade declarada (base de EVT), hora a hora."""
    d = validas(disp)[["din_instante", "val_dispoperacional"]].dropna()
    e = df[["din_instante", "val_disponibilidade"]].dropna()
    juntos = d.merge(e, on="din_instante", how="inner")
    juntos["diferenca_mw"] = (juntos["val_dispoperacional"] - juntos["val_disponibilidade"]).abs()
    divergentes = juntos[diferenca_absoluta(juntos["diferenca_mw"]) > tolerancia]
    if len(d):
        e_no_periodo = e[(e["din_instante"] >= d["din_instante"].min()) & (e["din_instante"] <= d["din_instante"].max())]
    else:
        e_no_periodo = e.iloc[0:0]
    # A hora sinalizada fica fora da comparação e é contada à parte: não é hora que falta na Disponibilidade por usina
    sinalizadas = disp.loc[disp["qualidade"] != "OK", "din_instante"] if "qualidade" in disp.columns else d["din_instante"].iloc[0:0]
    resumo = {
        "horas_comuns": len(juntos),
        "coincidentes": int(len(juntos) - len(divergentes)),
        "divergentes": int(len(divergentes)),
        "pct_coincidentes": float(100.0 * (len(juntos) - len(divergentes)) / len(juntos)) if len(juntos) else float("nan"),
        "so_ons_disponibilidade": int((~d["din_instante"].isin(e["din_instante"])).sum()),
        "so_base_evt": int((~e_no_periodo["din_instante"].isin(d["din_instante"])
                            & ~e_no_periodo["din_instante"].isin(sinalizadas)).sum()),
        "horas_sinalizadas_excluidas": int(len(disp) - len(validas(disp))),
        "tolerancia_mw": tolerancia,
    }
    return resumo, periodos_continuos(divergentes, "diferenca_mw")


def conferencia_disponibilidade(serie: Optional[SerieConjunto], evt: pd.DataFrame) -> ResultadoConferencia:
    """Resultado da conferência da disponibilidade; não aplicável sem a série no período."""
    if serie is None or not len(serie.horaria):
        return nao_aplicavel("disponibilidade", BASES, "horas",
                             "Disponibilidade por usina sem dados da usina no período",
                             tolerancia=TOLERANCIA_COINCIDENCIA_MW)
    resumo, divergencias = conferir_com_evt(serie.horaria, evt)
    d = validas(serie.horaria).dropna(subset=["val_dispoperacional"])["din_instante"]
    comuns = d[d.isin(evt.dropna(subset=["val_disponibilidade"])["din_instante"])]
    return ResultadoConferencia(
        id="disponibilidade", bases=BASES, unidade="horas",
        periodo=(comuns.min(), comuns.max()) if len(comuns) else None,
        comparados=resumo["horas_comuns"], coincidentes=resumo["coincidentes"], divergentes=resumo["divergentes"],
        tolerancia=TOLERANCIA_COINCIDENCIA_MW,
        tabelas={"resumo": resumo, "divergencias": divergencias},
    )
