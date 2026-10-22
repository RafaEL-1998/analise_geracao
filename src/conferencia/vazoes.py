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


# ---------------------------------------------------------------------------
# Hidrelétricas sem EVT (spec 006, fase D; rascunho 003, FR-026; tarefa T150)
# ---------------------------------------------------------------------------

BASES_ALINHAMENTO = ("Dados hidrológicos horários (val_vazaoturbinada)", "Geração por usina (geração da usina)")
DESLOCAMENTOS_ALINHAMENTO_H = (-1, 0, 1)


def _correlacao(a: pd.Series, b: pd.Series) -> float:
    """Correlação de Pearson; indefinida (NaN) com menos de duas horas ou série constante, sem divisão por zero."""
    if len(a) < 2 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(a.corr(b))


def alinhar_com_geracao(hid: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    """Correlação entre a vazão turbinada (já na hora de início) e a geração da usina, com a hidrologia deslocada de
    −1, 0 e +1 hora; uma linha por deslocamento, com as horas comuns."""
    geracao = base.loc[base["nivel"] == "usina", ["din_instante", "geracao_mw"]].dropna()
    turbinada = limpos(hid)[["din_instante", "val_vazaoturbinada"]].dropna()
    linhas = []
    for deslocamento in DESLOCAMENTOS_ALINHAMENTO_H:
        j = geracao.merge(turbinada.assign(din_instante=turbinada["din_instante"] + pd.Timedelta(hours=deslocamento)),
                          on="din_instante", how="inner")
        linhas.append({"deslocamento_h": deslocamento, "horas_comuns": len(j),
                       "correlacao": _correlacao(j["geracao_mw"], j["val_vazaoturbinada"])})
    return pd.DataFrame(linhas)


def conferencia_alinhamento_hidrologia(serie: Optional[SerieConjunto], base: Optional[pd.DataFrame]
                                       ) -> ResultadoConferencia:
    """A hora da hidrologia conferida pela geração da usina, sem a EVT (FR-026): confirmada quando a maior correlação
    é a do deslocamento 0. Sem meta (decisão R13): o resultado só é registrado; a convenção nunca é ajustada."""
    if serie is None or not len(serie.horaria):
        return nao_aplicavel("alinhamento_hidrologia", BASES_ALINHAMENTO, "horas",
                             "Dados hidrológicos horários sem dados da usina no período")
    if base is None or not (base["nivel"] == "usina").any():
        return nao_aplicavel("alinhamento_hidrologia", BASES_ALINHAMENTO, "horas",
                             "sem a geração no nível da usina no período")
    deslocamentos = alinhar_com_geracao(serie.horaria, base)
    por_deslocamento = deslocamentos.set_index("deslocamento_h")["correlacao"]
    zero = por_deslocamento.get(0, float("nan"))
    outros = [v for d, v in por_deslocamento.items() if d != 0 and pd.notna(v)]
    confirmado = bool(pd.notna(zero) and all(zero > v for v in outros))
    comuns = int(deslocamentos.loc[deslocamentos["deslocamento_h"] == 0, "horas_comuns"].iloc[0])
    alinhamento = pd.DataFrame([{
        "horas_comuns": comuns, "correlacao_0h": zero, "correlacao_menos_1h": por_deslocamento.get(-1, float("nan")),
        "correlacao_mais_1h": por_deslocamento.get(1, float("nan")), "deslocamento_aplicado_h": -1,
        "confirmado": confirmado,
    }])
    return ResultadoConferencia(
        id="alinhamento_hidrologia", bases=BASES_ALINHAMENTO, unidade="horas", comparados=comuns,
        coincidentes=comuns if confirmado else 0, divergentes=0 if confirmado else comuns,
        tabelas={"alinhamento": alinhamento, "deslocamentos": deslocamentos},
    )
