"""Séries horárias dos conjuntos do ONS no Tratamento de dados: disponibilidade, hidrologia e geração.

A partir das linhas extraídas pela Coleta de dados (instante como publicado, arquivo de origem e auditoria da extração):
convenção de hora de início → uma hora por instante (a do arquivo publicado por último; as repetições com valores
diferentes são contadas na auditoria) → recorte no período da base de EVT → meses e horas ausentes listados, nunca
interpolados. A auditoria final soma às contagens da extração as horas da usina e as duplicatas conflitantes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

from src.coleta.conjuntos import COLUNA_INSTANTE, COLUNA_NAO_NUMERICO, DescricaoConjunto, meses_do_periodo, \
    periodo_do_arquivo
from src.comum.logger import setup_logger
from src.comum.persistencia import ResultadoGravacao, gravar_csv

logger = setup_logger("tratamento")

COLUNA_INSTANTE_PUBLICADO = "din_instante_publicado"
COLUNAS_AUDITORIA: List[str] = [
    "arquivo", "formato", "periodo", "linhas_lidas", "linhas_formato_irregular", "linhas_usina",
    "linhas_so_identificador", "linhas_so_conferencia", "horas_usina", "valores_invalidos", "duplicatas_conflitantes",
    "recursos_duplicados_catalogo", "status", "mensagem",
]
COLUNAS_AUSENCIAS: List[str] = ["tipo", "inicio", "fim", "horas"]


@dataclass
class SerieConjunto:
    """Série horária da usina, meses e horas ausentes e auditoria por arquivo."""

    horaria: pd.DataFrame
    ausencias: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=COLUNAS_AUSENCIAS))
    auditoria: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=COLUNAS_AUDITORIA))


def hora_de_inicio(instantes: pd.Series) -> pd.Series:
    """Converte a convenção de fim de hora para a de início: (instante arredondado para cima) − 1 h.

    Ex.: 01:00 → 00:00; 15:00 → 14:00; 23:59 (última hora do dia) → 23:00 do mesmo dia.
    """
    return instantes.dt.ceil("h") - pd.Timedelta(hours=1)


def listar_ausencias(
    instantes: pd.Series,
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
    meses_com_arquivo: Set[Tuple[int, int]],
) -> pd.DataFrame:
    """Meses inteiros (sem arquivo ou sem a usina) e intervalos contínuos de horas ausentes."""
    esperado = pd.date_range(pd.Timestamp(inicio).floor("h"), pd.Timestamp(fim).floor("h"), freq="h")
    faltantes = esperado.difference(pd.DatetimeIndex(pd.Series(instantes).dropna().unique()))
    linhas: List[Dict[str, Any]] = []
    if len(faltantes):
        mes_esperado = esperado.to_period("M")
        mes_faltante = faltantes.to_period("M")
        for mes in mes_faltante.unique():
            horas_mes = esperado[mes_esperado == mes]
            faltam = faltantes[mes_faltante == mes]
            if len(faltam) == len(horas_mes):
                tipo = "MES_SEM_USINA" if (mes.year, mes.month) in meses_com_arquivo else "MES_SEM_ARQUIVO"
                linhas.append({"tipo": tipo, "inicio": horas_mes[0], "fim": horas_mes[-1], "horas": len(horas_mes)})
                continue
            serie = faltam.to_series()
            grupos = (serie.diff() != pd.Timedelta(hours=1)).cumsum()
            for _, bloco in serie.groupby(grupos.values):
                linhas.append({"tipo": "HORAS", "inicio": bloco.iloc[0], "fim": bloco.iloc[-1], "horas": len(bloco)})
    return pd.DataFrame(linhas, columns=COLUNAS_AUSENCIAS)


def _na_convencao_de_inicio(desc: DescricaoConjunto, extraido: pd.DataFrame) -> pd.DataFrame:
    """Linhas extraídas com o instante na convenção de hora de início (o publicado fica ao lado, se convertido)."""
    dados = extraido.copy()
    instantes = pd.to_datetime(dados[COLUNA_INSTANTE])
    if desc.convencao_hora == "fim":
        dados = dados.rename(columns={COLUNA_INSTANTE: COLUNA_INSTANTE_PUBLICADO})
        dados[COLUNA_INSTANTE_PUBLICADO] = instantes
        dados.insert(0, COLUNA_INSTANTE, hora_de_inicio(instantes))
    else:
        dados[COLUNA_INSTANTE] = instantes
    return dados[dados[COLUNA_INSTANTE].notna()].reset_index(drop=True)


def montar_serie(
    desc: DescricaoConjunto,
    extraido: pd.DataFrame,
    auditoria_coleta: pd.DataFrame,
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
) -> SerieConjunto:
    """Série horária da usina a partir da extração da Coleta (linhas e auditoria, na ordem de leitura dos arquivos)."""
    lidos = auditoria_coleta[auditoria_coleta["obtido"].astype(bool)]
    ordem = {arquivo: i for i, arquivo in enumerate(lidos["arquivo"])}
    meses_com_arquivo: Set[Tuple[int, int]] = set()
    for arquivo in lidos["arquivo"]:
        chave = periodo_do_arquivo(arquivo)
        if chave is not None:
            meses_com_arquivo |= meses_do_periodo(chave)

    colunas = [COLUNA_INSTANTE, *([COLUNA_INSTANTE_PUBLICADO] if desc.convencao_hora == "fim" else []),
               *desc.colunas_valor, COLUNA_NAO_NUMERICO, "arquivo_origem", "_ordem"]
    horaria = _na_convencao_de_inicio(desc, extraido) if len(extraido) else pd.DataFrame(columns=colunas)
    horaria["_ordem"] = horaria["arquivo_origem"].map(ordem)
    horas_por_arquivo = horaria.groupby("arquivo_origem")[COLUNA_INSTANTE].nunique() if len(horaria) else {}

    auditoria = auditoria_coleta.drop(columns=["data_publicacao", "obtido"]).copy()
    auditoria["horas_usina"] = [
        int(horas_por_arquivo.get(a, 0)) if obtido else 0
        for a, obtido in zip(auditoria_coleta["arquivo"], auditoria_coleta["obtido"].astype(bool))
    ]
    auditoria["duplicatas_conflitantes"] = 0
    auditoria = auditoria.reindex(columns=COLUNAS_AUDITORIA).reset_index(drop=True)

    if len(horaria):
        horaria = horaria.sort_values([COLUNA_INSTANTE, "_ordem"], kind="stable").reset_index(drop=True)
        repetidas = horaria.duplicated(COLUNA_INSTANTE, keep="last")
        if repetidas.any():
            mantidas = horaria[~repetidas].set_index(COLUNA_INSTANTE)
            descartadas = horaria[repetidas]
            valores = list(desc.colunas_valor)
            ref = mantidas.loc[descartadas[COLUNA_INSTANTE], valores].to_numpy()
            atual = descartadas[valores].to_numpy()
            diferentes = ~((ref == atual) | (pd.isna(ref) & pd.isna(atual))).all(axis=1)
            conflitos = descartadas.loc[diferentes, "arquivo_origem"].value_counts()
            for arquivo, quantidade in conflitos.items():
                auditoria.loc[auditoria["arquivo"] == arquivo, "duplicatas_conflitantes"] = int(quantidade)
            if int(diferentes.sum()):
                logger.warning("%s: %d horas repetidas com valores diferentes; mantido o arquivo publicado por último.",
                               desc.pacote, int(diferentes.sum()))
            horaria = horaria[~repetidas]
        dentro = (horaria[COLUNA_INSTANTE] >= inicio) & (horaria[COLUNA_INSTANTE] <= fim)
        horaria = horaria[dentro].reset_index(drop=True)
    horaria = horaria[colunas]
    ausencias = listar_ausencias(horaria[COLUNA_INSTANTE], inicio, fim, meses_com_arquivo)
    for coluna in ("linhas_lidas", "linhas_usina", "linhas_so_identificador", "linhas_so_conferencia", "horas_usina",
                   "valores_invalidos", "duplicatas_conflitantes", "recursos_duplicados_catalogo"):
        auditoria[coluna] = pd.to_numeric(auditoria[coluna], errors="coerce").fillna(0).astype(int)
    auditoria["mensagem"] = auditoria["mensagem"].fillna("")
    logger.info("%s: %d horas da usina em %d arquivos; %d intervalos ausentes.", desc.pacote, len(horaria),
                len(lidos), len(ausencias))
    return SerieConjunto(horaria=horaria, ausencias=ausencias, auditoria=auditoria)


# ---------------------------------------------------------------------------
# Gravação e leitura
# ---------------------------------------------------------------------------


def exportar_serie(serie: SerieConjunto, arquivos: Dict[str, Path]) -> Dict[str, ResultadoGravacao]:
    """Grava as tabelas da série via persistência; colunas internas (prefixo ``_``) ficam de fora."""
    tabelas = {
        "horaria": serie.horaria[[c for c in serie.horaria.columns if not str(c).startswith("_")]],
        "ausencias": serie.ausencias,
        "auditoria": serie.auditoria,
    }
    return {nome: gravar_csv(tabelas[nome], caminho) for nome, caminho in arquivos.items() if nome in tabelas}


_COLUNAS_DATA = (COLUNA_INSTANTE, COLUNA_INSTANTE_PUBLICADO, "inicio", "fim")


def _ler_processado(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        return pd.DataFrame()
    try:
        tabela = pd.read_csv(caminho, sep=";")
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    for coluna in _COLUNAS_DATA:
        if coluna in tabela.columns:
            tabela[coluna] = pd.to_datetime(tabela[coluna])
    return tabela


def carregar_serie_processada(arquivos: Dict[str, Path]) -> Optional[SerieConjunto]:
    """Lê as tabelas gravadas; None se a série horária ainda não foi gerada."""
    if "horaria" not in arquivos or not Path(arquivos["horaria"]).exists():
        return None
    serie = SerieConjunto(horaria=_ler_processado(Path(arquivos["horaria"])))
    if "ausencias" in arquivos and Path(arquivos["ausencias"]).exists():
        serie.ausencias = _ler_processado(Path(arquivos["ausencias"]))
    if "auditoria" in arquivos and Path(arquivos["auditoria"]).exists():
        serie.auditoria = _ler_processado(Path(arquivos["auditoria"]))
    return serie
