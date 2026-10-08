"""Funções auxiliares das Análises: máscaras das horas da base de EVT, médias, razões e rótulos."""

from __future__ import annotations

import calendar
import math
from typing import Any, Dict, List

import pandas as pd

from src.comum.formatacao import fmt_data
from src.comum.perfil import perfil_ativo
from src.comum.regras import LIMIAR_GERACAO_PARADA_MW, LIMIAR_INDISPONIBILIDADE_TOTAL_MW
from src.tratamento.series import SerieConjunto


def horas_no_ano(ano: int) -> int:
    return 8784 if calendar.isleap(int(ano)) else 8760


def _mascara_evt(df: pd.DataFrame) -> pd.Series:
    return df["val_energiavertidaturbinavel"] > 0


def _mascara_parada_com_evt(df: pd.DataFrame) -> pd.Series:
    return (df["val_geracao"] <= LIMIAR_GERACAO_PARADA_MW) & _mascara_evt(df)


def _mascara_vertimento_minimo(df: pd.DataFrame) -> pd.Series:
    return df["val_vazaovertida"] <= perfil_ativo().analises.vertimento_minimo_m3s


def _mascara_indisponibilidade_total(df: pd.DataFrame) -> pd.Series:
    return df["val_disponibilidade"] <= LIMIAR_INDISPONIBILIDADE_TOTAL_MW


def _media(serie: pd.Series) -> float:
    return float(serie.mean()) if len(serie) else math.nan


def _razao(numerador: float, denominador: float) -> float:
    if denominador is None or math.isnan(denominador) or denominador == 0:
        return math.nan
    return float(numerador) / float(denominador)


def _pct(parte: float, todo: float) -> float:
    return _razao(parte, todo) * 100.0


def _rotulo_janela(horas: List[int]) -> str:
    return f"{horas[0]}h às {horas[-1]}h"


def _data_obtencao_texto(obtido_em: str) -> str:
    return f"obtido em {fmt_data(obtido_em)}" if obtido_em else "data de obtenção não registrada"


def _resumo_serie(serie: SerieConjunto) -> Dict[str, Any]:
    """Cobertura de uma série das bases complementares: período, horas, sinalizadas, meses e horas ausentes."""
    h, aus = serie.horaria, serie.ausencias
    meses = aus[aus["tipo"] != "HORAS"] if len(aus) else aus
    return {
        "inicio": h["din_instante"].min(),
        "fim": h["din_instante"].max(),
        "horas": len(h),
        "horas_sinalizadas": int(h["qualidade"].ne("OK").sum()) if "qualidade" in h.columns else 0,
        "meses_sem_usina": [pd.Timestamp(x) for x in meses["inicio"]] if len(meses) else [],
        "horas_ausentes": int(aus.loc[aus["tipo"] == "HORAS", "horas"].sum()) if len(aus) else 0,
    }


def _rotulo_ano(ano: Any, parcial: Any) -> str:
    return f"{int(ano)}{'*' if bool(parcial) else ''}"
