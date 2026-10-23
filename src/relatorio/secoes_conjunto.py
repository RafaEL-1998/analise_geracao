"""Seção "Composição e geração do conjunto" do relatório (spec da Geração do relatório, FR-046; plano, D20).

Em toda usina em conjunto com a geração do conjunto, depois das seções do tipo (item 8 da FR-041): a geração do conjunto
por trecho de composição, a composição (uma linha por usina, com a potência) e a figura da geração mensal do conjunto
por trecho, com a potência somada de cada trecho. Blocos comuns ao PDF e ao Markdown, montados só a partir de
``res.conjunto``; os números são sempre "do conjunto", nunca divididos entre as usinas (princípio VIII).
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

import pandas as pd

from src.analises.resultados import ResultadosAnalise
from src.comum.formatacao import fmt_data, fmt_data_hora, fmt_int, fmt_num
from src.relatorio.secoes_renovavel import referencia_restricao

SECOES_CONJUNTO: Tuple[str, ...] = ("conjunto",)


def _c(res: ResultadosAnalise) -> Dict:
    return getattr(res, "conjunto", None) or {}


def _traco(valor: float, casas: int = 1) -> str:
    return "—" if valor is None or (isinstance(valor, float) and math.isnan(valor)) else fmt_num(valor, casas)


def _tipos(texto: str) -> str:
    return ", ".join(t for t in str(texto).split(";") if t)


def nome_do_conjunto(res: ResultadosAnalise) -> str:
    """"Conj. X (CJU_...)"; só o id quando a composição não traz o nome."""
    c = _c(res)
    return f"{c['nome']} ({c['id']})" if c.get("nome") else str(c.get("id", ""))


def rotulo_trecho(r) -> str:
    """Rótulo de um trecho de composição na figura e na planilha: "1: 22/08/2019 a 26/09/2019"."""
    return f"{int(r.trecho)}: {fmt_data(r.inicio)} a {fmt_data(r.fim)}"


# ---------------------------------------------------------------------------
# Tabelas
# ---------------------------------------------------------------------------


def linhas_tabela_trechos(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    c = _c(res)
    cabecalho = ["Trecho", "Início", "Fim", "Usinas", "Tipos", "Horas com valor", "Energia (MWh)", "Média (MWmed)",
                 "Máxima (MW)"]
    if c.get("com_capacidade"):
        cabecalho.append("Potência somada (MW)")
    linhas = []
    for r in c["trechos"].itertuples():
        linha = [str(r.trecho), fmt_data_hora(r.inicio), fmt_data_hora(r.fim), fmt_int(r.usinas), _tipos(r.tipos),
                 fmt_int(r.horas_com_valor), fmt_num(r.energia_mwh, 0), _traco(r.geracao_media_mw),
                 _traco(r.geracao_maxima_mw)]
        if c.get("com_capacidade"):
            linha.append(_traco(r.potencia_somada_mw))
        linhas.append(linha)
    return cabecalho, linhas


def membros(res: ResultadosAnalise) -> pd.DataFrame:
    """Uma linha por usina da composição no período, com a maior potência em operação entre os trechos dela."""
    t = _c(res)["composicao"]
    if not len(t):
        return t
    agrupado = t.groupby(["ceg", "usina", "tipo", "entrada", "saida"], as_index=False, dropna=False, sort=False).agg(
        potencia_mw=("potencia_mw", "max"))
    return agrupado.sort_values(["tipo", "entrada", "usina"], kind="stable").reset_index(drop=True)


def linhas_tabela_composicao(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    c = _c(res)
    cabecalho = ["Usina", "Tipo", "CEG", "Entrada no conjunto", "Saída"]
    if c.get("com_capacidade"):
        cabecalho.append("Potência (MW)")
    linhas = []
    for r in membros(res).itertuples():
        linha = [str(r.usina), str(r.tipo), str(r.ceg), fmt_data(r.entrada) if r.entrada else "—",
                 fmt_data(r.saida) if r.saida else "—"]
        if c.get("com_capacidade"):
            linha.append(_traco(r.potencia_mw))
        linhas.append(linha)
    return cabecalho, linhas


# ---------------------------------------------------------------------------
# Textos, legenda e nota
# ---------------------------------------------------------------------------


def textos_tabelas(res: ResultadosAnalise) -> Dict[str, Tuple[str, str]]:
    c = _c(res)
    if not c:
        return {}
    potencia = ("; potência somada = soma das unidades da Capacidade de geração em operação em algum momento do "
                "trecho, das usinas com unidade cadastrada (as demais aparecem com «—» na composição)"
                if c.get("com_capacidade") else "")
    return {
        "tab_conjunto_trechos": (f"Geração do conjunto {nome_do_conjunto(res)} por trecho de composição", (
            "Trecho novo a cada mudança da composição do conjunto (Composição dos conjuntos); horas e médias da série "
            f"do conjunto, sem divisão entre as usinas{potencia}.")),
        "tab_conjunto_composicao": ("Usinas da composição no período", (
            "Entrada e saída da usina no conjunto, como o ONS publica na Composição dos conjuntos; tipo pelo prefixo do "
            "CEG" + ("; potência = maior soma das unidades em operação num trecho em que a usina está no conjunto"
                     if c.get("com_capacidade") else "") + ".")),
    }


def legenda_figura(res: ResultadosAnalise, chave: str) -> str:
    if chave != "conjunto_mensal":
        return ""
    c = _c(res)
    potencia = (" Linhas tracejadas: potência somada das usinas de cada trecho (unidades em operação)."
                if c.get("com_capacidade") else "")
    return (f"Geração média mensal do conjunto {nome_do_conjunto(res)} (MWmed), uma cor por trecho de composição; "
            f"linhas verticais nas mudanças de composição.{potencia} Os números são do conjunto, como o ONS publica.")


def nota(res: ResultadosAnalise) -> str:
    """Nota metodológica da seção do conjunto (só quando ela aparece)."""
    c = _c(res)
    if not c:
        return ""
    partes = []
    if not referencia_restricao():
        partes.append("O período começa na entrada da usina no conjunto (Composição dos conjuntos): antes dela, a "
                      "geração do conjunto não inclui a usina.")
    partes.append("A composição de cada trecho vem da Composição dos conjuntos" + (
        " e a potência, das unidades da Capacidade de geração (pelo CEG de cada usina, inclusive as cadastradas em "
        "outro estado)" if c.get("com_capacidade") else "") + "; a geração do conjunto não é dividida pela potência "
        "somada nem entre as usinas.")
    return " ".join(partes)


# ---------------------------------------------------------------------------
# Blocos
# ---------------------------------------------------------------------------


def blocos(res: ResultadosAnalise, chave: str) -> list:
    """Blocos da seção do conjunto, na ordem em que o PDF e o Markdown os mostram."""
    from src.relatorio.comum import Bloco, _numericas, _tabela

    if chave != "conjunto" or not _c(res):
        return []
    b = []  # as composições e as médias estão na constatação, no início da seção
    cab, linhas = linhas_tabela_trechos(res)
    b.append(_tabela("tab_conjunto_trechos", (cab, linhas), [0.5, 1.1, 1.1, 0.6, 0.9] + [1.0] * (len(cab) - 5),
                     _numericas(cab, 5)))
    b.append(Bloco("figura", "conjunto_mensal"))
    cab, linhas = linhas_tabela_composicao(res)
    b.append(_tabela("tab_conjunto_composicao", (cab, linhas), [1.6, 0.5, 1.6, 1.0, 0.9] + [0.9] * (len(cab) - 5),
                     range(5, len(cab))))
    return b
