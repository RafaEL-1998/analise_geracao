"""Geração por usina no Tratamento de dados: série horária oficial e sinalização de valor não numérico (G1)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from src.comum.caminhos import ARQUIVOS_TRATAMENTO
from src.tratamento.series import SerieConjunto, carregar_serie_processada, exportar_serie, montar_serie


def arquivos_saida(pasta: Path) -> Dict[str, Path]:
    pasta = Path(pasta)
    return {"horaria": pasta / ARQUIVOS_TRATAMENTO["geracao_horaria"],
            "ausencias": pasta / ARQUIVOS_TRATAMENTO["geracao_ausencias"],
            "auditoria": pasta / ARQUIVOS_TRATAMENTO["auditoria_geracao"]}


def qualidade(horaria: pd.DataFrame) -> pd.Series:
    """"OK" ou "G1" (valor não numérico); horas sinalizadas ficam fora da conferência."""
    nao_numerico = horaria["_nao_numerico"].astype(bool) if "_nao_numerico" in horaria.columns \
        else pd.Series(False, index=horaria.index)
    return nao_numerico.map({True: "G1", False: "OK"})


def tratar_geracao(desc: Any, extraido: pd.DataFrame, auditoria: pd.DataFrame, inicio: pd.Timestamp,
                   fim: pd.Timestamp, pasta: Path) -> SerieConjunto:
    """Série horária com a qualidade de cada hora, gravada na pasta do tratamento."""
    serie = montar_serie(desc, extraido, auditoria, inicio, fim)
    serie.horaria.insert(serie.horaria.columns.get_loc("arquivo_origem"), "qualidade", qualidade(serie.horaria))
    exportar_serie(serie, arquivos_saida(pasta))
    return serie


def carregar_geracao_tratada(pasta: Path) -> Optional[SerieConjunto]:
    """Série gravada; None se o tratamento ainda não foi executado."""
    return carregar_serie_processada(arquivos_saida(pasta))
