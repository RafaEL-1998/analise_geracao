"""Disponibilidade horária por usina no Tratamento de dados: série horária e sinalização de qualidade (D1 a D4).

A disponibilidade operacional é a mesma disponibilidade declarada da base de EVT (conferida hora a hora pela
Conferência); a informação nova é a disponibilidade sincronizada, que separa a usina disponível e desligada da usina
com unidade sincronizada à rede. Horas sinalizadas ficam na série e fora das análises.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from src.comum.caminhos import ARQUIVOS_TRATAMENTO
from src.comum.logger import setup_logger
from src.comum.regras import TOLERANCIA_QUALIDADE_DISPONIBILIDADE_MW
from src.tratamento.series import SerieConjunto, carregar_serie_processada, exportar_serie, montar_serie

logger = setup_logger("tratamento")

DESCRICAO_QUALIDADE: Dict[str, str] = {
    "D1": f"sincronizada > operacional + {TOLERANCIA_QUALIDADE_DISPONIBILIDADE_MW} MW",
    "D2": f"operacional > instalada + {TOLERANCIA_QUALIDADE_DISPONIBILIDADE_MW} MW",
    "D3": "algum valor negativo",
    "D4": "algum valor não numérico",
}


def arquivos_saida(pasta: Path) -> Dict[str, Path]:
    pasta = Path(pasta)
    return {"horaria": pasta / ARQUIVOS_TRATAMENTO["disponibilidade_horaria"],
            "ausencias": pasta / ARQUIVOS_TRATAMENTO["disponibilidade_ausencias"],
            "auditoria": pasta / ARQUIVOS_TRATAMENTO["auditoria_disponibilidade"]}


def qualidade(horaria: pd.DataFrame) -> pd.Series:
    """"OK" ou as regras violadas (D1 a D4), separadas por vírgula; horas sinalizadas ficam fora das análises."""
    tol = TOLERANCIA_QUALIDADE_DISPONIBILIDADE_MW
    inst, oper, sinc = (horaria[c] for c in ("val_potenciainstalada", "val_dispoperacional", "val_dispsincronizada"))
    regras = {
        "D1": sinc > oper + tol,
        "D2": oper > inst + tol,
        "D3": (inst < 0) | (oper < 0) | (sinc < 0),
        "D4": horaria["_nao_numerico"].astype(bool) if "_nao_numerico" in horaria.columns else pd.Series(False, index=horaria.index),
    }
    codigos = pd.Series("", index=horaria.index, dtype=object)
    for codigo, violada in regras.items():
        codigos = codigos.where(~violada.fillna(False), codigos + "," + codigo)
    codigos = codigos.str.strip(",")
    return codigos.where(codigos != "", "OK")


def tratar_disponibilidade(desc: Any, extraido: pd.DataFrame, auditoria: pd.DataFrame, inicio: pd.Timestamp,
                           fim: pd.Timestamp, pasta: Path) -> SerieConjunto:
    """Série horária com a qualidade de cada hora, gravada na pasta do tratamento."""
    serie = montar_serie(desc, extraido, auditoria, inicio, fim)
    serie.horaria.insert(serie.horaria.columns.get_loc("arquivo_origem"), "qualidade", qualidade(serie.horaria))
    exportar_serie(serie, arquivos_saida(pasta))
    sinalizadas = serie.horaria["qualidade"].ne("OK").sum()
    if sinalizadas:
        logger.warning("%d horas de disponibilidade sinalizadas (fora das análises): %s", sinalizadas,
                       serie.horaria.loc[serie.horaria["qualidade"] != "OK", "qualidade"].value_counts().to_dict())
    meses = serie.ausencias[serie.ausencias["tipo"] != "HORAS"]
    if len(meses):
        logger.warning("Meses sem a usina na disponibilidade: %s",
                       [f"{r.inicio:%Y-%m} ({r.tipo})" for r in meses.itertuples()])
    return serie


def carregar_disponibilidade_tratada(pasta: Path) -> Optional[SerieConjunto]:
    """Série gravada; None se o tratamento ainda não foi executado."""
    return carregar_serie_processada(arquivos_saida(pasta))
