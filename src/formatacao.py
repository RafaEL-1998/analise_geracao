"""Formatação de números, datas e listas no padrão brasileiro para os relatórios."""

from __future__ import annotations

import math
from typing import Any, Iterable, List

import pandas as pd

MESES_ABREVIADOS: List[str] = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
MESES_EXTENSO: List[str] = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]
SEM_VALOR = "–"


def _como_float(valor: Any) -> float:
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return math.nan
    return v


def fmt_num(valor: Any, casas: int = 1) -> str:
    """Número com separador de milhar '.' e decimal ','; ausente vira '–'."""
    v = _como_float(valor)
    if math.isnan(v) or math.isinf(v):
        return SEM_VALOR
    texto = f"{v:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_int(valor: Any) -> str:
    return fmt_num(valor, 0)


def fmt_pct(valor: Any, casas: int = 1) -> str:
    texto = fmt_num(valor, casas)
    return texto if texto == SEM_VALOR else f"{texto}%"


def fmt_pp(valor: Any, casas: int = 1) -> str:
    """Diferença em pontos percentuais com sinal explícito."""
    v = _como_float(valor)
    if math.isnan(v):
        return SEM_VALOR
    sinal = "+" if v > 0 else ("−" if v < 0 else "")
    return f"{sinal}{fmt_num(abs(v), casas)} p.p."


def fmt_data(valor: Any) -> str:
    ts = pd.Timestamp(valor)
    return ts.strftime("%d/%m/%Y")


def fmt_data_hora(valor: Any) -> str:
    ts = pd.Timestamp(valor)
    return ts.strftime("%d/%m/%Y %Hh")


def fmt_mes_ano(valor: Any) -> str:
    periodo = pd.Period(valor, freq="M")
    return f"{MESES_ABREVIADOS[periodo.month - 1]}/{periodo.year}"


def fmt_lista(itens: Iterable[Any]) -> str:
    """Junta itens como 'a, b e c'."""
    textos = [str(i) for i in itens]
    if not textos:
        return ""
    if len(textos) == 1:
        return textos[0]
    return ", ".join(textos[:-1]) + " e " + textos[-1]


def plural(quantidade: int, singular: str, plural_: str) -> str:
    return singular if quantidade == 1 else plural_
