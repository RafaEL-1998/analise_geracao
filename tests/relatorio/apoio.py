"""Apoio aos testes do relatório: resultados das Análises a partir de bases sintéticas, com as conferências montadas
a partir das mesmas bases e a tabela de parâmetros e a origem dos dados completadas como na Geração do relatório."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Tuple

import pandas as pd

from src.analises.etapa import analisar
from src.analises.resultados import ResultadosAnalise
from src.conferencia.disponibilidade import conferencia_disponibilidade
from src.conferencia.geracao import conferencia_geracao
from src.conferencia.indicadores import conferencia_dispf_horas, conferencia_teifa_teip
from src.conferencia.resultado import ResultadoConferencia
from src.relatorio.etapa import completar_resultados
from src.tratamento.series import SerieConjunto


def _vazoes(alinhamento: pd.DataFrame) -> ResultadoConferencia:
    a = alinhamento.iloc[0]
    comuns, coincidentes = int(a["horas_comuns"]), int(a["coincidentes_ambas"])
    return ResultadoConferencia(id="vazoes", bases=("base de EVT", "Dados hidrológicos horários"), unidade="horas",
                                comparados=comuns, coincidentes=coincidentes, divergentes=comuns - coincidentes,
                                tolerancia=float(a["tolerancia_m3s"]), meta=float(a["meta_pct"]),
                                meta_atingida=bool(a["confirmado"]), tabelas={"alinhamento": alinhamento})


def analisar_com_bases(
    df: pd.DataFrame,
    caminho_auditoria: Optional[Path] = None,
    caminho_manifesto: Optional[Path] = None,
    indicadores: Any = None,
    programacao: Any = None,
    disponibilidade: Optional[SerieConjunto] = None,
    hidrologia: Optional[Tuple[SerieConjunto, pd.DataFrame]] = None,
    geracao: Optional[SerieConjunto] = None,
    **outros: Any,
) -> ResultadosAnalise:
    """Como o ``analisar`` anterior à reorganização: a hidrologia vem como (série, alinhamento)."""
    conferencias = {}
    if disponibilidade is not None:
        conferencias["disponibilidade"] = conferencia_disponibilidade(disponibilidade, df)
    if geracao is not None:
        conferencias["geracao"] = conferencia_geracao(geracao, df)
    serie_hidrologia = None
    if hidrologia is not None:
        serie_hidrologia, alinhamento = hidrologia
        conferencias["vazoes"] = _vazoes(alinhamento)
    if indicadores is not None:
        conferencias["dispf_horas"] = conferencia_dispf_horas(indicadores)
        conferencias["teifa_teip"] = conferencia_teifa_teip(indicadores)
    res = analisar(df, conferencias, caminho_auditoria, caminho_manifesto, indicadores=indicadores,
                   programacao=programacao, disponibilidade=disponibilidade, hidrologia=serie_hidrologia,
                   geracao=geracao, **outros)
    return completar_resultados(res)
