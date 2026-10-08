"""Geração por usina conferida com a base de EVT: resumos mensal e anual (spec das Análises, FR-039)."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from src.analises.comum import _resumo_serie
from src.coleta.conjuntos import data_obtencao
from src.comum import caminhos
from src.comum.regras import PASTA_GERACAO_RAW
from src.tratamento.series import SerieConjunto


def analisar_geracao_oficial(serie: SerieConjunto, df: pd.DataFrame, cobertura: Dict[str, Any],
                             conferencia: Dict[str, Any], mensal: pd.DataFrame,
                             divergencias: pd.DataFrame) -> Dict[str, Any]:
    """Geração da base de EVT conferida com a série oficial de geração por usina (FR-039).

    ``conferencia``, ``mensal`` e ``divergencias`` vêm da Conferência (geração da base de EVT × Geração por usina).
    """
    anual = mensal.assign(ano=mensal["mes"].str[:4]).groupby("ano").agg(
        energia_base_evt_mwh=("energia_base_evt_mwh", "sum"),
        energia_ons_geracao_mwh=("energia_ons_geracao_mwh", "sum"),
        diferenca_mwh=("diferenca_mwh", "sum"),
        horas_so_base_evt=("horas_so_base_evt", "sum"),
        horas_so_ons_geracao=("horas_so_ons_geracao", "sum"),
    ).reset_index()
    anual["ano_parcial"] = anual["ano"].isin({str(a) for a in cobertura.get("anos_parciais", [])})
    return {
        "resumo": _resumo_serie(serie),
        "conferencia": conferencia,
        "mensal": mensal,
        "anual": anual,
        "divergencias": divergencias,
        "auditoria": serie.auditoria,
        "ausencias": serie.ausencias,
        "obtido_em": data_obtencao(caminhos.RAW_DATA_DIR / PASTA_GERACAO_RAW),
    }
