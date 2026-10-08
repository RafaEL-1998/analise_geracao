"""Programação diária do ONS no Tratamento de dados: base horária e dias sem arquivo.

A partir dos patamares de 30 minutos extraídos pela Coleta: média dos patamares de cada hora (convenção de hora de
início), recorte no período da base de EVT e lista dos dias do período sem arquivo publicado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import pandas as pd

from src.comum.caminhos import ARQUIVOS_TRATAMENTO
from src.comum.logger import setup_logger
from src.comum.persistencia import gravar_csv

logger = setup_logger("tratamento")

# Colunas da auditoria dos arquivos mostradas no relatório (aba PROG_AUDITORIA_ARQUIVOS)
COLUNAS_AUDITORIA_RELATORIO: List[str] = [
    "arquivo", "dia", "linhas_lidas", "linhas_usina", "linhas_codigo_sem_conferencia", "patamares",
    "data_interna_confere", "status",
]


@dataclass
class ProgramacaoONS:
    """Programação horária da usina, dias sem arquivo e auditoria dos arquivos lidos (da Coleta)."""

    horaria: pd.DataFrame
    dias_ausentes: pd.DataFrame = field(default_factory=pd.DataFrame)
    auditoria: pd.DataFrame = field(default_factory=pd.DataFrame)


def programacao_horaria(patamares: pd.DataFrame) -> pd.DataFrame:
    """Média dos patamares de cada hora; hora = (patamar − 1) ÷ 2, convenção de hora de início."""
    if patamares.empty:
        return pd.DataFrame(columns=["din_instante", "geracao_programada_mw", "patamares"])
    p = patamares.dropna(subset=["num_patamar"]).copy()
    p["din_instante"] = p["dia"] + pd.to_timedelta((p["num_patamar"].astype(int) - 1) // 2, unit="h")
    horaria = p.groupby("din_instante").agg(
        geracao_programada_mw=("geracao_programada_mw", "mean"),
        patamares=("num_patamar", "size"),
    )
    return horaria.reset_index()


def montar_programacao(
    patamares: pd.DataFrame,
    auditoria_coleta: pd.DataFrame,
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
) -> ProgramacaoONS:
    """Programação horária no período e dias sem arquivo (do primeiro dia com arquivo ao fim do período)."""
    d1 = pd.Timestamp(fim).normalize()
    horaria = programacao_horaria(patamares)
    if len(horaria):
        horaria = horaria[(horaria["din_instante"] >= inicio) & (horaria["din_instante"] <= fim)].reset_index(drop=True)
    lidos = auditoria_coleta[auditoria_coleta["obtido"].astype(bool)] if len(auditoria_coleta) else auditoria_coleta
    dias_com_arquivo = pd.DatetimeIndex(pd.to_datetime(lidos["dia"])) if len(lidos) else pd.DatetimeIndex([])
    if len(dias_com_arquivo):
        grade = pd.date_range(dias_com_arquivo.min(), d1, freq="D")
        ausentes = grade.difference(dias_com_arquivo)
    else:
        ausentes = pd.DatetimeIndex([])
    logger.info("Programação: %d horas, %d dias sem arquivo.", len(horaria), len(ausentes))
    return ProgramacaoONS(horaria=horaria, dias_ausentes=pd.DataFrame({"dia": ausentes}),
                          auditoria=auditoria_relatorio(auditoria_coleta))


def auditoria_relatorio(auditoria_coleta: pd.DataFrame) -> pd.DataFrame:
    """Auditoria da Coleta nas colunas mostradas no relatório."""
    if auditoria_coleta.empty:
        return pd.DataFrame(columns=COLUNAS_AUDITORIA_RELATORIO)
    return auditoria_coleta[COLUNAS_AUDITORIA_RELATORIO].reset_index(drop=True)


def exportar_programacao(prog: ProgramacaoONS, pasta: Path) -> List[Path]:
    saidas = {
        Path(pasta) / ARQUIVOS_TRATAMENTO["programacao_horaria"]: prog.horaria,
        Path(pasta) / ARQUIVOS_TRATAMENTO["programacao_dias_ausentes"]: prog.dias_ausentes,
    }
    for caminho, tabela in saidas.items():
        gravar_csv(tabela, caminho, sep=";", index=False, encoding="utf-8", date_format="%Y-%m-%d %H:%M:%S")
    return list(saidas)


def carregar_programacao_tratada(pasta: Path, auditoria_coleta: Optional[pd.DataFrame] = None
                                 ) -> Optional[ProgramacaoONS]:
    """Programação tratada (com a auditoria da Coleta, se informada); None se ainda não foi tratada."""
    horaria_path = Path(pasta) / ARQUIVOS_TRATAMENTO["programacao_horaria"]
    if not horaria_path.exists():
        return None

    def _ler(caminho: Path, datas: List[str]) -> pd.DataFrame:
        if not caminho.exists():
            return pd.DataFrame()
        try:
            t = pd.read_csv(caminho, sep=";")
        except pd.errors.EmptyDataError:  # tabela gravada sem colunas (ex.: nenhum dia ausente)
            return pd.DataFrame()
        for coluna in datas:
            if coluna in t.columns:
                t[coluna] = pd.to_datetime(t[coluna])
        return t

    return ProgramacaoONS(
        horaria=_ler(horaria_path, ["din_instante"]),
        dias_ausentes=_ler(Path(pasta) / ARQUIVOS_TRATAMENTO["programacao_dias_ausentes"], ["dia"]),
        auditoria=auditoria_relatorio(auditoria_coleta) if auditoria_coleta is not None else pd.DataFrame(),
    )
