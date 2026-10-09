"""Cobertura da base de EVT: período, anos completos e parciais, arquivos lidos e manifesto."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from src.analises.comum import horas_no_ano


def _periodo_do_arquivo(nome_arquivo: str) -> str:
    """Extrai '2015' ou '01/2024' do nome ENERGIA_VERTIDA_TURBINAVEL_<periodo>.csv."""
    base = Path(str(nome_arquivo)).stem
    periodo = base.rsplit("TURBINAVEL_", 1)[-1]
    partes = periodo.split("_")
    if len(partes) == 2:
        return f"{partes[1]}/{partes[0]}"
    return periodo


def _resumo_auditoria(caminho_auditoria: Optional[Path]) -> Dict[str, Any]:
    caminho = Path(caminho_auditoria) if caminho_auditoria else None
    if caminho is None or not caminho.exists():
        return {}
    aud = pd.read_csv(caminho, sep=";")
    status = aud.get("status_processamento", pd.Series(dtype=str))
    divergencias = 0
    for coluna in ("registros_codigo_sem_nome", "registros_nome_sem_codigo"):
        if coluna in aud.columns:
            divergencias += int(aud[coluna].sum())
    return {
        "total": len(aud),
        "com_registros": int((status == "PROCESSADO").sum()),
        "sem_registros": [_periodo_do_arquivo(n) for n in aud.loc[status == "SEM_REGISTROS", "nome_arquivo"]],
        "falhas": aud.loc[status == "FALHA", "nome_arquivo"].tolist(),
        "divergencias": divergencias,
    }


def _resumo_manifesto(datas_evt: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Arquivos da EVT registrados no manifesto e datas mais recentes, da linha da EVT no ``datas_obtencao.csv``."""
    if not datas_evt or not int(datas_evt.get("arquivos_registrados") or 0):
        return {}
    return {
        "arquivos": int(datas_evt["arquivos_registrados"]),
        "ultima_modificacao_mais_recente": str(datas_evt.get("publicacao_mais_recente") or ""),
        "registro_mais_recente_utc": str(datas_evt.get("obtencao_mais_recente") or ""),
    }


def analisar_cobertura(
    df: pd.DataFrame,
    caminho_auditoria: Optional[Path] = None,
    datas_evt: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Período coberto, horas ausentes, anos parciais, agentes e arquivos de origem.

    ``datas_evt``: a linha da EVT no ``datas_obtencao.csv`` da Coleta (arquivos registrados e datas).
    """
    inicio = df["din_instante"].min()
    fim = df["din_instante"].max()
    grade = pd.date_range(inicio, fim, freq="h")
    faltantes = grade.difference(pd.DatetimeIndex(df["din_instante"]))

    linhas = []
    for ano, g in df.groupby("ano"):
        primeiro = g["din_instante"].min()
        ultimo = g["din_instante"].max()
        parcial = primeiro > pd.Timestamp(int(ano), 1, 1, 0) or ultimo < pd.Timestamp(int(ano), 12, 31, 23)
        linhas.append(
            {
                "ano": int(ano),
                "primeiro_registro": primeiro,
                "ultimo_registro": ultimo,
                "horas_observadas": len(g),
                "horas_calendario": horas_no_ano(int(ano)),
                "cobertura_pct": len(g) / horas_no_ano(int(ano)) * 100.0,
                "ano_parcial": bool(parcial),
            }
        )
    por_ano = pd.DataFrame(linhas)

    agentes = (
        df.groupby("nom_agente")["din_instante"]
        .agg(["min", "max", "count"])
        .sort_values("min")
        .reset_index()
        .rename(columns={"min": "primeiro_registro", "max": "ultimo_registro", "count": "horas"})
    )
    identificacao = {
        coluna: " / ".join(sorted(df[coluna].astype(str).unique()))
        for coluna in ["id_subsistema", "nom_subsistema", "nom_bacia", "nom_rio", "nom_reservatorio", "cod_usina"]
        if coluna in df.columns
    }

    return {
        "inicio": inicio,
        "fim": fim,
        "horas_observadas": len(df),
        "horas_esperadas": len(grade),
        "horas_faltantes": list(faltantes),
        "duplicadas": int(df["din_instante"].duplicated().sum()),
        "por_ano": por_ano,
        "anos_parciais": por_ano.loc[por_ano["ano_parcial"], "ano"].tolist(),
        "anos_completos": por_ano.loc[~por_ano["ano_parcial"], "ano"].tolist(),
        "agentes": agentes,
        "identificacao": identificacao,
        "arquivos": _resumo_auditoria(caminho_auditoria),
        "manifesto": _resumo_manifesto(datas_evt),
    }
