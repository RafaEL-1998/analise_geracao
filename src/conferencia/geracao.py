"""Conferência da geração: base de EVT × Geração por usina, hora a hora (spec da Conferência, FR-010)."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import pandas as pd

from src.comum.periodos import periodos_continuos
from src.comum.regras import TOLERANCIA_COINCIDENCIA_MW
from src.conferencia.resultado import ResultadoConferencia, diferenca_absoluta, nao_aplicavel
from src.tratamento.series import SerieConjunto

BASES = ("base de EVT (val_geracao)", "Geração por usina (val_geracao)")


def conferir_geracao(
    ger: pd.DataFrame,
    df: pd.DataFrame,
    tolerancia: float = TOLERANCIA_COINCIDENCIA_MW,
) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """Geração da base de EVT × série oficial de geração por usina: resumo, tabela mensal e divergências."""
    g = ger[ger["qualidade"] == "OK"] if "qualidade" in ger.columns else ger
    g = g[["din_instante", "val_geracao"]].dropna()
    e = df[["din_instante", "val_geracao"]].dropna()
    if len(g):
        e = e[(e["din_instante"] >= g["din_instante"].min()) & (e["din_instante"] <= g["din_instante"].max())]
    juntos = g.merge(e, on="din_instante", how="outer", suffixes=("_ons", "_evt"), indicator=True)
    comuns = juntos[juntos["_merge"] == "both"].copy()
    comuns["diferenca_mw"] = (comuns["val_geracao_ons"] - comuns["val_geracao_evt"]).abs()
    divergentes = comuns[diferenca_absoluta(comuns["diferenca_mw"]) > tolerancia]
    resumo = {
        "horas_comuns": len(comuns),
        "coincidentes": int(len(comuns) - len(divergentes)),
        "divergentes": int(len(divergentes)),
        "pct_coincidentes": float(100.0 * (len(comuns) - len(divergentes)) / len(comuns)) if len(comuns) else float("nan"),
        "so_ons_geracao": int((juntos["_merge"] == "left_only").sum()),
        "so_base_evt": int((juntos["_merge"] == "right_only").sum()),
        "energia_ons_geracao_mwh": float(g["val_geracao"].sum()),
        "energia_base_evt_mwh": float(e["val_geracao"].sum()),
        "tolerancia_mw": tolerancia,
    }
    juntos["mes"] = juntos["din_instante"].dt.to_period("M").astype(str)
    juntos["so_ons"] = juntos["_merge"] == "left_only"
    juntos["so_evt"] = juntos["_merge"] == "right_only"
    mensal = juntos.groupby("mes").agg(
        energia_base_evt_mwh=("val_geracao_evt", "sum"),
        energia_ons_geracao_mwh=("val_geracao_ons", "sum"),
        horas_so_base_evt=("so_evt", "sum"),
        horas_so_ons_geracao=("so_ons", "sum"),
    ).reset_index()
    mensal["diferenca_mwh"] = mensal["energia_ons_geracao_mwh"] - mensal["energia_base_evt_mwh"]
    for coluna in ("horas_so_base_evt", "horas_so_ons_geracao"):
        mensal[coluna] = mensal[coluna].astype(int)
    mensal = mensal[["mes", "energia_base_evt_mwh", "energia_ons_geracao_mwh", "diferenca_mwh",
                     "horas_so_base_evt", "horas_so_ons_geracao"]]
    return resumo, mensal, periodos_continuos(divergentes, "diferenca_mw")


def conferencia_geracao(serie: Optional[SerieConjunto], evt: pd.DataFrame) -> ResultadoConferencia:
    """Resultado da conferência da geração; não aplicável sem a série de Geração por usina no período."""
    if serie is None or not len(serie.horaria):
        return nao_aplicavel("geracao", BASES, "horas", "Geração por usina sem dados da usina no período",
                             tolerancia=TOLERANCIA_COINCIDENCIA_MW)
    resumo, mensal, divergencias = conferir_geracao(serie.horaria, evt)
    g = serie.horaria
    g = g[g["qualidade"] == "OK"] if "qualidade" in g.columns else g
    comuns = g.dropna(subset=["val_geracao"])["din_instante"]
    comuns = comuns[comuns.isin(evt.dropna(subset=["val_geracao"])["din_instante"])]
    return ResultadoConferencia(
        id="geracao", bases=BASES, unidade="horas",
        periodo=(comuns.min(), comuns.max()) if len(comuns) else None,
        comparados=resumo["horas_comuns"], coincidentes=resumo["coincidentes"], divergentes=resumo["divergentes"],
        tolerancia=TOLERANCIA_COINCIDENCIA_MW,
        tabelas={"resumo": resumo, "mensal": mensal, "divergencias": divergencias},
    )
