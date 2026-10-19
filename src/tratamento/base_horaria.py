"""Base horária comum das usinas sem EVT (spec 006, decisão R30; data-model 6.2).

Uma linha por hora da série de referência tratada (a Geração por usina, da usina ou do conjunto), com o nível de
cada hora, a disponibilidade operacional e a sincronizada (quando há cobertura), a geração programada (quando há), o
trecho (decisão R7) e as sinalizações. É a base das seções comuns do relatório e das regras comuns da conclusão
(decisões R14 e R16) nas usinas sem EVT; as hidrelétricas com EVT continuam com a base de EVT.

Sinalização não exclui registro (princípio V): a hora sinalizada fica na base, com os códigos separados por vírgula.
As horas ausentes da série de referência ficam listadas em ``geracao_ausencias.csv``, nunca preenchidas.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from src.comum.caminhos import ARQUIVOS_TRATAMENTO
from src.comum.persistencia import ResultadoGravacao, gravar_csv
from src.comum.regras import TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW
from src.tratamento.series import SerieConjunto

COLUNAS_BASE_HORARIA = ["din_instante", "geracao_mw", "nivel", "disponibilidade_operacional_mw",
                        "disponibilidade_sincronizada_mw", "geracao_programada_mw", "trecho", "sinalizacoes"]
# Regra R7 (a mesma da base de EVT): geração acima da disponibilidade declarada, só com as duas da usina
REGRA_GERACAO_ACIMA_DISPONIBILIDADE = "R7"
FORMATO_DATA = "%Y-%m-%d %H:%M:%S"


def _codigos_qualidade(serie: pd.Series) -> pd.Series:
    """Os códigos de uma coluna ``qualidade`` ("OK" vira vazio)."""
    return serie.fillna("OK").astype(str).replace("OK", "")


def _trecho_por_hora(instantes: pd.Series, trechos: pd.DataFrame) -> pd.Series:
    """Número do trecho de cada hora (``trechos.csv`` da Coleta); vazio fora de todo trecho ou sem trechos."""
    saida = pd.Series(pd.NA, index=instantes.index, dtype="Int64")
    if trechos is None or not len(trechos):
        return saida
    for linha in trechos.to_dict("records"):
        inicio = pd.to_datetime(linha.get("inicio") or None)
        fim = pd.to_datetime(linha.get("fim") or None)
        dentro = pd.Series(True, index=instantes.index)
        if inicio is not None and not pd.isna(inicio):
            dentro &= instantes >= inicio
        if fim is not None and not pd.isna(fim):
            dentro &= instantes <= fim
        saida[dentro & saida.isna()] = int(linha["trecho"])
    return saida


def montar_base_horaria(
    geracao: SerieConjunto,
    complemento: Optional[pd.DataFrame],
    trechos: Optional[pd.DataFrame],
    disponibilidade: Optional[SerieConjunto] = None,
    programacao: Optional[pd.DataFrame] = None,
    nivel_padrao: str = "usina",
) -> pd.DataFrame:
    """Base horária comum a partir das séries tratadas (geração com ``qualidade``; disponibilidade com ``qualidade``;
    programação horária com ``geracao_programada_mw``) e dos arquivos da Coleta (complemento e trechos).

    O nível de cada hora vem do complemento (``geracao_complemento.parquet``); sem ele, ``nivel_padrao``.
    """
    h = geracao.horaria
    base = pd.DataFrame({"din_instante": pd.to_datetime(h["din_instante"]),
                         "geracao_mw": pd.to_numeric(h["val_geracao"], errors="coerce")})
    codigos = [_codigos_qualidade(h["qualidade"]) if "qualidade" in h.columns
               else pd.Series("", index=h.index)]

    base["nivel"] = nivel_padrao
    if complemento is not None and len(complemento) and "nivel" in complemento.columns:
        nivel = complemento.assign(din_instante=pd.to_datetime(complemento["din_instante"])) \
            .drop_duplicates("din_instante").set_index("din_instante")["nivel"]
        base["nivel"] = base["din_instante"].map(nivel).fillna(nivel_padrao).astype(str)

    base["disponibilidade_operacional_mw"] = float("nan")
    base["disponibilidade_sincronizada_mw"] = float("nan")
    if disponibilidade is not None and len(disponibilidade.horaria):
        d = disponibilidade.horaria.assign(din_instante=pd.to_datetime(disponibilidade.horaria["din_instante"]))
        d = d.drop_duplicates("din_instante").set_index("din_instante")
        base["disponibilidade_operacional_mw"] = base["din_instante"].map(d["val_dispoperacional"]).astype(float)
        base["disponibilidade_sincronizada_mw"] = base["din_instante"].map(d["val_dispsincronizada"]).astype(float)
        if "qualidade" in d.columns:
            codigos.append(_codigos_qualidade(base["din_instante"].map(d["qualidade"])))

    base["geracao_programada_mw"] = float("nan")
    if programacao is not None and len(programacao):
        p = programacao.assign(din_instante=pd.to_datetime(programacao["din_instante"]))
        p = p.drop_duplicates("din_instante").set_index("din_instante")["geracao_programada_mw"]
        base["geracao_programada_mw"] = base["din_instante"].map(p).astype(float)

    base["trecho"] = _trecho_por_hora(base["din_instante"], trechos)

    acima = ((base["nivel"] == "usina")
             & (base["geracao_mw"] > base["disponibilidade_operacional_mw"]
                + TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW)).fillna(False)
    codigos.append(acima.map({True: REGRA_GERACAO_ACIMA_DISPONIBILIDADE, False: ""}))

    juntos = pd.concat(codigos, axis=1).astype(str)
    base["sinalizacoes"] = juntos.apply(lambda linha: ",".join(c for c in linha if c), axis=1) if len(juntos) \
        else pd.Series(dtype=str)
    return base[COLUNAS_BASE_HORARIA].sort_values("din_instante", kind="stable").reset_index(drop=True)


def resumo_base_horaria(base: pd.DataFrame, ausencias: pd.DataFrame) -> Dict[str, Any]:
    """Resumo para o ``etapa.json`` do Tratamento: horas, horas ausentes, horas por nível e por sinalização."""
    codigos = Counter(c for texto in base["sinalizacoes"] for c in str(texto).split(",") if c)
    horas_ausentes = int(pd.to_numeric(ausencias.get("horas", pd.Series(dtype=int))).sum()) if len(ausencias) else 0
    return {
        "horas": len(base),
        "horas_ausentes": horas_ausentes,
        "niveis": {str(k): int(v) for k, v in base["nivel"].value_counts().sort_index().items()},
        "sinalizacoes": dict(sorted(codigos.items())),
        "trechos": int(base["trecho"].nunique()),
    }


def exportar_base_horaria(base: pd.DataFrame, pasta: Path) -> ResultadoGravacao:
    """Grava ``base_horaria.csv`` pela persistência."""
    return gravar_csv(base, Path(pasta) / ARQUIVOS_TRATAMENTO["base_horaria"], date_format=FORMATO_DATA)


def carregar_base_horaria(pasta: Path) -> Optional[pd.DataFrame]:
    """Base gravada; None nas usinas com EVT (que não a têm) ou antes do Tratamento."""
    caminho = Path(pasta) / ARQUIVOS_TRATAMENTO["base_horaria"]
    if not caminho.exists():
        return None
    base = pd.read_csv(caminho, sep=";", keep_default_na=False, na_values=[""],
                       dtype={"nivel": str, "sinalizacoes": str})
    base["din_instante"] = pd.to_datetime(base["din_instante"])
    base["sinalizacoes"] = base["sinalizacoes"].fillna("")
    base["trecho"] = pd.to_numeric(base["trecho"], errors="coerce").astype("Int64")
    return base
