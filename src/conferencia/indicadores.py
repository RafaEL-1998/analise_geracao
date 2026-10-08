"""Conferências dos indicadores oficiais: DISPF × horas por estado operativo e TEIFa e TEIP recalculadas.

Spec da Conferência, FR-014 a FR-016. A indisponibilidade programada e a forçada (INDISPPF e INDISPFF), em horas, são
comparadas com as horas de desligamento programado e forçado (HDP e HDF); a TEIFa e a TEIP são refeitas com as horas
da janela móvel de 60 meses, ponderadas pela potência de cada unidade.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from src.comum.regras import JANELA_TAXAS_MESES, TOLERANCIA_DIVERGENCIA_HORAS, TOLERANCIA_REPRODUCAO_TAXAS_PP
from src.conferencia.resultado import ResultadoConferencia, diferenca_absoluta, nao_aplicavel
from src.tratamento.indicadores import IndicadoresONS

BASES_DISPF = ("Indicadores por unidade geradora, base mensal (INDISPPF e INDISPFF)",
               "Parâmetros das taxas TEIFa e TEIP (HDP e HDF)")
BASES_TAXAS = ("TEIFa e TEIP recalculadas a partir das horas por estado operativo",
               "Taxas TEIFa e TEIP publicadas")
# Valores sem os quais o mês-unidade (DISPF × horas) ou o mês (TEIFa e TEIP) não é comparado, e sim contado à parte
VALORES_DISPF = ["HP", "HDP", "HDF", "indisppf", "indispff"]
VALORES_TAXAS = ["teifa_publicada", "teifa_recalculada", "teip_publicada", "teip_recalculada"]


def comparar_indicadores_e_horas(ug_mensal: pd.DataFrame, horas: pd.DataFrame,
                                  tolerancia_h: float = TOLERANCIA_DIVERGENCIA_HORAS) -> pd.DataFrame:
    """Meses em que INDISPPF/INDISPFF (em horas) e as horas HDP/HDF do TEIP não conferem."""
    colunas = ["mes", "ug", "HP", "HS", "HRD", "HDP", "horas_programadas_indisppf", "HDF",
               "horas_forcadas_indispff", "diferenca_programada_h", "diferenca_forcada_h"]
    if ug_mensal.empty or horas.empty:
        return pd.DataFrame(columns=colunas)
    m = horas.merge(ug_mensal[["mes", "ug", "indisppf", "indispff"]], on=["mes", "ug"], how="inner")
    m = m.dropna(subset=VALORES_DISPF)  # mês-unidade com valor ausente não é comparado (contado à parte)
    m["horas_programadas_indisppf"] = m["indisppf"] / 100.0 * m["HP"]
    m["horas_forcadas_indispff"] = m["indispff"] / 100.0 * m["HP"]
    m["diferenca_programada_h"] = m["horas_programadas_indisppf"] - m["HDP"]
    m["diferenca_forcada_h"] = m["horas_forcadas_indispff"] - m["HDF"]
    fora = ((diferenca_absoluta(m["diferenca_programada_h"]) > tolerancia_h)
            | (diferenca_absoluta(m["diferenca_forcada_h"]) > tolerancia_h))
    return m.loc[fora, colunas].reset_index(drop=True)


def janela(horas: pd.DataFrame, mes_fim: pd.Timestamp, meses: int) -> pd.DataFrame:
    """Horas por estado operativo dos ``meses`` que terminam em ``mes_fim``."""
    inicio = pd.Timestamp(mes_fim) - pd.DateOffset(months=meses - 1)
    return horas[(horas["mes"] >= inicio) & (horas["mes"] <= mes_fim)]


def janela_completa(mes: Any, primeiro_mes: Any, janela_meses: int = JANELA_TAXAS_MESES) -> bool:
    """O mês tem as horas da janela inteira: os ``janela_meses`` meses que terminam nele."""
    return pd.Timestamp(mes) - pd.DateOffset(months=janela_meses - 1) >= pd.Timestamp(primeiro_mes)


def peso(h: pd.DataFrame) -> pd.Series:
    """Potência de cada unidade (ponderação das taxas); 1 se a potência não estiver disponível."""
    if "potencia_mw" in h.columns:
        return h["potencia_mw"].fillna(1.0)
    return pd.Series(1.0, index=h.index)


def _taxas_da_janela(h: pd.DataFrame) -> Tuple[float, float]:
    """TEIFa = Σ P·(HDF + HEDF) ÷ Σ P·(HP − HDP − HEDP); TEIP = Σ P·(HDP + HEDP) ÷ Σ P·HP."""
    p = peso(h)
    base_teifa = float((p * (h["HP"] - h["HDP"] - h["HEDP"])).sum())
    base_teip = float((p * h["HP"]).sum())
    teifa = float((p * (h["HDF"] + h["HEDF"])).sum()) / base_teifa if base_teifa else float("nan")
    teip = float((p * (h["HDP"] + h["HEDP"])).sum()) / base_teip if base_teip else float("nan")
    return teifa, teip


def recalcular_taxas(horas: pd.DataFrame, taxas: pd.DataFrame, janela_meses: int = JANELA_TAXAS_MESES) -> pd.DataFrame:
    """Recalcula TEIFa e TEIP de cada mês publicado a partir das horas por estado operativo.

    Só há recálculo quando as horas cobrem a janela inteira; nos demais meses as colunas
    recalculadas ficam vazias.
    """
    colunas = ["mes", "meses_na_janela", "teifa_publicada", "teifa_recalculada", "teip_publicada",
               "teip_recalculada", "diferenca_teifa_pp", "diferenca_teip_pp"]
    if horas.empty or taxas.empty:
        return pd.DataFrame(columns=colunas)
    primeiro_mes = horas["mes"].min()
    linhas = []
    for r in taxas.itertuples():
        jan = janela(horas, r.mes, janela_meses)
        completa = janela_completa(r.mes, primeiro_mes, janela_meses)
        teifa, teip = _taxas_da_janela(jan) if completa else (float("nan"), float("nan"))
        linhas.append({
            "mes": r.mes,
            "meses_na_janela": int(jan["mes"].nunique()),
            "teifa_publicada": r.teifa,
            "teifa_recalculada": teifa,
            "teip_publicada": r.teip,
            "teip_recalculada": teip,
            "diferenca_teifa_pp": (teifa - r.teifa) * 100.0,
            "diferenca_teip_pp": (teip - r.teip) * 100.0,
        })
    return pd.DataFrame(linhas, columns=colunas)


def reproducao_das_taxas(recalculo: pd.DataFrame, primeiro_mes: Any) -> Dict[str, Any]:
    """Meses de janela completa: comparados (com as quatro taxas), reproduzidos, sem valor e a maior diferença (p.p.)."""
    mascara = recalculo["mes"].map(lambda m: janela_completa(m, primeiro_mes)).astype(bool)
    completos = recalculo[mascara]
    comparaveis = completos.dropna(subset=VALORES_TAXAS)
    diferencas = comparaveis[["diferenca_teifa_pp", "diferenca_teip_pp"]].abs()
    return {
        "completos": len(completos),
        "comparaveis": comparaveis,
        "meses": len(comparaveis),
        "reproduzidos": int((diferenca_absoluta(diferencas) <= TOLERANCIA_REPRODUCAO_TAXAS_PP).all(axis=1).sum()),
        "sem_valor": len(completos) - len(comparaveis),
        "diferenca_maxima_pp": float(diferencas.max().max()) if len(comparaveis) else math.nan,
    }


def conferencia_dispf_horas(ind: Optional[IndicadoresONS]) -> ResultadoConferencia:
    """DISPF × horas por estado operativo, por mês e unidade presentes nas duas bases."""
    if ind is None or ind.ug_mensal.empty or ind.horas_estado.empty:
        return nao_aplicavel("dispf_horas", BASES_DISPF, "meses-unidade",
                             "indicadores mensais por unidade ou horas por estado operativo sem dados no período",
                             tolerancia=TOLERANCIA_DIVERGENCIA_HORAS)
    divergencias = comparar_indicadores_e_horas(ind.ug_mensal, ind.horas_estado)
    comuns = ind.horas_estado.merge(ind.ug_mensal[["mes", "ug", "indisppf", "indispff"]], on=["mes", "ug"], how="inner")
    validos = comuns.dropna(subset=VALORES_DISPF)  # com valor ausente, o mês-unidade fica fora e é contado à parte
    return ResultadoConferencia(
        id="dispf_horas", bases=BASES_DISPF, unidade="meses-unidade",
        periodo=(validos["mes"].min(), validos["mes"].max()) if len(validos) else None,
        comparados=len(validos), coincidentes=len(validos) - len(divergencias), divergentes=len(divergencias),
        tolerancia=TOLERANCIA_DIVERGENCIA_HORAS,
        tabelas={"divergencias": divergencias, "sem_valor": len(comuns) - len(validos)},
    )


def conferencia_teifa_teip(ind: Optional[IndicadoresONS]) -> ResultadoConferencia:
    """TEIFa e TEIP recalculadas × publicadas; só os meses com a janela de 60 meses completa são comparados."""
    if ind is None or ind.horas_estado.empty or ind.taxas.empty:
        return nao_aplicavel("teifa_teip", BASES_TAXAS, "meses",
                             "horas por estado operativo ou taxas TEIFa e TEIP sem dados no período",
                             tolerancia=TOLERANCIA_REPRODUCAO_TAXAS_PP)
    recalculo = recalcular_taxas(ind.horas_estado, ind.taxas)
    rep = reproducao_das_taxas(recalculo, ind.horas_estado["mes"].min())
    if not rep["completos"]:
        return nao_aplicavel("teifa_teip", BASES_TAXAS, "meses",
                             f"nenhum mês com a janela de {JANELA_TAXAS_MESES} meses completa",
                             tolerancia=TOLERANCIA_REPRODUCAO_TAXAS_PP, tabelas={"recalculo": recalculo})
    comparaveis = rep["comparaveis"]  # mês com taxa ausente fica fora e é contado à parte (sem_valor)
    return ResultadoConferencia(
        id="teifa_teip", bases=BASES_TAXAS, unidade="meses",
        periodo=(comparaveis["mes"].min(), comparaveis["mes"].max()) if len(comparaveis) else None,
        comparados=rep["meses"], coincidentes=rep["reproduzidos"], divergentes=rep["meses"] - rep["reproduzidos"],
        tolerancia=TOLERANCIA_REPRODUCAO_TAXAS_PP,
        tabelas={"recalculo": recalculo, "diferenca_maxima_pp": rep["diferenca_maxima_pp"],
                 "sem_valor": rep["sem_valor"]},
    )
