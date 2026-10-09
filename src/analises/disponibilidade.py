"""Disponibilidade operacional e sincronizada: horas paradas, resumos mensal e anual (spec das Análises, US2, FR-030 a FR-033)."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from src.analises.comum import _pct
from src.analises.programacao import PARADA_EVT_PROGRAMACAO_ZERO
from src.comum.regras import LIMIAR_GERACAO_PARADA_MW, LIMIAR_SINCRONIZADA_MW
from src.conferencia.disponibilidade import validas
from src.tratamento.indicadores import IndicadoresONS
from src.tratamento.series import SerieConjunto


SINCRONIZADA = "SINCRONIZADA"
NAO_SINCRONIZADA = "NAO_SINCRONIZADA"
COM_EVT = "COM_EVT"
SEM_EVT = "SEM_EVT"
SEM_PROGRAMACAO = "SEM_PROGRAMACAO"


def classificar_horas_paradas(
    disp: pd.DataFrame,
    df: pd.DataFrame,
    classificadas_programacao: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Horas comuns com a usina parada (geração até 1 MW), por sincronização, EVT e classe da programação."""
    operacao = df[["din_instante", "val_geracao", "val_energiavertidaturbinavel"]]
    j = operacao.merge(validas(disp)[["din_instante", "val_dispoperacional", "val_dispsincronizada"]],
                       on="din_instante", how="inner")
    paradas = j[j["val_geracao"] <= LIMIAR_GERACAO_PARADA_MW].copy()
    paradas["sincronizacao"] = (paradas["val_dispsincronizada"] > LIMIAR_SINCRONIZADA_MW).map(
        {True: SINCRONIZADA, False: NAO_SINCRONIZADA})
    paradas["evt"] = (paradas["val_energiavertidaturbinavel"] > 0).map({True: COM_EVT, False: SEM_EVT})
    if classificadas_programacao is not None and len(classificadas_programacao):
        classes = classificadas_programacao[["din_instante", "classe"]].rename(columns={"classe": "classe_programacao"})
        paradas = paradas.merge(classes, on="din_instante", how="left")
    else:
        paradas["classe_programacao"] = pd.NA
    paradas["classe_programacao"] = paradas["classe_programacao"].fillna(SEM_PROGRAMACAO)
    colunas = ["din_instante", "val_geracao", "val_dispoperacional", "val_dispsincronizada",
               "val_energiavertidaturbinavel", "sincronizacao", "evt", "classe_programacao"]
    return paradas.sort_values("din_instante").reset_index(drop=True)[colunas]


def resumir_disponibilidade(
    disp: pd.DataFrame,
    df: pd.DataFrame,
    horas_estado: Optional[pd.DataFrame],
    freq: str,
) -> pd.DataFrame:
    """Resumo por mês (``freq="M"``) ou ano (``"Y"``), com a comparação com a reserva desligada (HRD) do TEIFa/TEIP."""
    j = df[["din_instante", "val_geracao", "val_disponibilidade"]].merge(
        validas(disp)[["din_instante", "val_dispoperacional", "val_dispsincronizada"]], on="din_instante", how="inner")
    j["periodo"] = j["din_instante"].dt.to_period(freq).astype(str)
    j["nao_sincronizada"] = j["val_dispoperacional"] - j["val_dispsincronizada"]
    parada = j["val_geracao"] <= LIMIAR_GERACAO_PARADA_MW
    sinc = j["val_dispsincronizada"] > LIMIAR_SINCRONIZADA_MW
    j["parada"] = parada
    j["parada_sem_sincronizacao"] = parada & ~sinc
    j["parada_sincronizada"] = parada & sinc
    resumo = j.groupby("periodo").agg(
        horas_comuns=("din_instante", "size"),
        disp_operacional_media_mw=("val_dispoperacional", "mean"),
        disp_declarada_media_mw=("val_disponibilidade", "mean"),
        disp_sincronizada_media_mw=("val_dispsincronizada", "mean"),
        geracao_media_mw=("val_geracao", "mean"),
        capacidade_nao_sincronizada_media_mw=("nao_sincronizada", "mean"),
        capacidade_nao_sincronizada_mwh=("nao_sincronizada", "sum"),
        horas_paradas=("parada", "sum"),
        horas_paradas_sem_sincronizacao=("parada_sem_sincronizacao", "sum"),
        horas_paradas_sincronizadas=("parada_sincronizada", "sum"),
    ).reset_index()
    if horas_estado is not None and len(horas_estado) and {"HRD", "potencia_mw"} <= set(horas_estado.columns):
        h = horas_estado.copy()
        h["periodo"] = pd.to_datetime(h["mes"]).dt.to_period(freq).astype(str)
        h["reserva_mwh"] = h["HRD"] * h["potencia_mw"]
        reserva = h.groupby("periodo")["reserva_mwh"].sum().rename("reserva_desligada_teif_mwh")
        resumo = resumo.merge(reserva, on="periodo", how="left")
    else:
        resumo["reserva_desligada_teif_mwh"] = float("nan")
    resumo["diferenca_mwh"] = resumo["capacidade_nao_sincronizada_mwh"] - resumo["reserva_desligada_teif_mwh"]
    for coluna in ("horas_paradas", "horas_paradas_sem_sincronizacao", "horas_paradas_sincronizadas"):
        resumo[coluna] = resumo[coluna].astype(int)
    return resumo


def analisar_disponibilidade(
    serie: SerieConjunto,
    df: pd.DataFrame,
    indicadores: Optional[IndicadoresONS],
    programacao: Dict[str, Any],
    cobertura: Dict[str, Any],
    conferencia: Dict[str, Any],
    divergencias: pd.DataFrame,
    obtido_em: str = "",
) -> Dict[str, Any]:
    """Disponibilidade horária do ONS (operacional e sincronizada) cruzada com a base de EVT (US2).

    ``conferencia`` e ``divergencias`` vêm da Conferência (disponibilidade declarada × operacional);
    ``obtido_em``, do ``datas_obtencao.csv`` da Coleta.
    """
    disp = serie.horaria
    paradas = classificar_horas_paradas(disp, df, programacao.get("classificadas") if programacao else None)
    classes = (paradas.groupby(["sincronizacao", "evt", "classe_programacao"])
               .agg(horas=("din_instante", "size"), evt_mwh=("val_energiavertidaturbinavel", "sum"))
               .reset_index())
    horas_estado = indicadores.horas_estado if indicadores is not None else None
    mensal = resumir_disponibilidade(disp, df, horas_estado, "M")
    anual = resumir_disponibilidade(disp, df, horas_estado, "Y")
    anual["ano_parcial"] = anual["periodo"].isin({str(a) for a in cobertura.get("anos_parciais", [])})

    sem_sinc = paradas["sincronizacao"] == NAO_SINCRONIZADA
    com_evt = paradas["evt"] == COM_EVT
    prog_zero = paradas["classe_programacao"] == PARADA_EVT_PROGRAMACAO_ZERO
    aus = serie.ausencias
    meses = aus[aus["tipo"] != "HORAS"] if len(aus) else aus
    resumo = {
        "inicio": disp["din_instante"].min(),
        "fim": disp["din_instante"].max(),
        "horas": len(disp),
        "horas_sinalizadas": int(disp["qualidade"].ne("OK").sum()) if "qualidade" in disp.columns else 0,
        "meses_sem_usina": [pd.Timestamp(x) for x in meses["inicio"]] if len(meses) else [],
        "horas_ausentes": int(aus.loc[aus["tipo"] == "HORAS", "horas"].sum()) if len(aus) else 0,
        "horas_paradas": len(paradas),
        "horas_paradas_sem_sincronizacao": int(sem_sinc.sum()),
        "horas_paradas_sincronizadas": int((~sem_sinc).sum()),
        "pct_paradas_sem_sincronizacao": _pct(int(sem_sinc.sum()), len(paradas)),
        "horas_parada_evt": int(com_evt.sum()),
        "horas_parada_evt_sem_sincronizacao": int((com_evt & sem_sinc).sum()),
        "horas_parada_evt_programacao_zero": int((com_evt & prog_zero).sum()),
        "horas_parada_evt_programacao_zero_sem_sincronizacao": int((com_evt & prog_zero & sem_sinc).sum()),
    }
    return {
        "resumo": resumo,
        "conferencia": conferencia,
        "divergencias": divergencias,
        "horas_paradas": paradas,
        "classes": classes,
        "mensal": mensal,
        "anual": anual,
        "auditoria": serie.auditoria,
        "ausencias": aus,
        "obtido_em": obtido_em,
    }
