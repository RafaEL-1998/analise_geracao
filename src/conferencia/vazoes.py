"""Conferência das vazões: turbinada e vertida da base de EVT × Dados hidrológicos horários (FR-012 e FR-013).

A hidrologia chega do Tratamento já na hora de início (deslocamento de −1 h). A meta é de 99 % das horas comuns com
as duas vazões coincidentes; abaixo dela, a etapa termina com o código 3 e os cruzamentos hidrológicos não são
publicados.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from src.comum.regras import META_ALINHAMENTO_HIDROLOGIA_PCT, TOLERANCIA_COINCIDENCIA_VAZAO_M3S
from src.conferencia.resultado import ResultadoConferencia, diferenca_absoluta, nao_aplicavel
from src.tratamento.hidrologia import limpos
from src.tratamento.series import SerieConjunto

BASES = ("base de EVT (val_vazaoturbinada, val_vazaovertida)", "Dados hidrológicos horários (mesmas vazões)")
COLUNAS = ["din_instante", "val_vazaoturbinada", "val_vazaovertida"]


def _comuns(hid: pd.DataFrame, evt: pd.DataFrame) -> pd.DataFrame:
    return limpos(hid)[COLUNAS].merge(evt[COLUNAS], on="din_instante", how="inner", suffixes=("_hid", "_evt")).dropna()


def alinhar_com_evt(
    hid: pd.DataFrame,
    evt: pd.DataFrame,
    tolerancia: float = TOLERANCIA_COINCIDENCIA_VAZAO_M3S,
    meta: float = META_ALINHAMENTO_HIDROLOGIA_PCT,
) -> pd.DataFrame:
    """Coincidência das vazões turbinada e vertida (hidrologia × base de EVT) nas horas comuns (uma linha)."""
    j = _comuns(hid, evt)
    turbinada = diferenca_absoluta(j["val_vazaoturbinada_hid"] - j["val_vazaoturbinada_evt"]) <= tolerancia
    vertida = diferenca_absoluta(j["val_vazaovertida_hid"] - j["val_vazaovertida_evt"]) <= tolerancia
    ambas = int((turbinada & vertida).sum())
    pct = 100.0 * ambas / len(j) if len(j) else float("nan")
    return pd.DataFrame([{
        "horas_comuns": len(j),
        "coincidentes_turbinada": int(turbinada.sum()),
        "coincidentes_vertida": int(vertida.sum()),
        "coincidentes_ambas": ambas,
        "pct_coincidencia": pct,
        "meta_pct": meta,
        "tolerancia_m3s": tolerancia,
        "deslocamento_aplicado_h": -1,
        "confirmado": bool(len(j)) and pct >= meta,
    }])


def conferencia_vazoes(serie: Optional[SerieConjunto], evt: pd.DataFrame) -> ResultadoConferencia:
    """Resultado da conferência das vazões, com a meta; não aplicável sem a hidrologia no período."""
    if serie is None or not len(serie.horaria):
        return nao_aplicavel("vazoes", BASES, "horas", "Dados hidrológicos horários sem dados da usina no período",
                             tolerancia=TOLERANCIA_COINCIDENCIA_VAZAO_M3S, meta=META_ALINHAMENTO_HIDROLOGIA_PCT)
    alinhamento = alinhar_com_evt(serie.horaria, evt)
    a = alinhamento.iloc[0]
    comuns = _comuns(serie.horaria, evt)["din_instante"]
    return ResultadoConferencia(
        id="vazoes", bases=BASES, unidade="horas",
        periodo=(comuns.min(), comuns.max()) if len(comuns) else None,
        comparados=int(a["horas_comuns"]), coincidentes=int(a["coincidentes_ambas"]),
        divergentes=int(a["horas_comuns"]) - int(a["coincidentes_ambas"]),
        tolerancia=TOLERANCIA_COINCIDENCIA_VAZAO_M3S, meta=META_ALINHAMENTO_HIDROLOGIA_PCT,
        meta_atingida=bool(a["confirmado"]),
        tabelas={"alinhamento": alinhamento},
    )
