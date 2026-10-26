"""Indicadores da carteira (spec das Análises, FR-062; plano das Análises, D24).

Reúne, para o relatório de carteira, números que as Análises já calculam para o relatório da usina, no último ano
completo da série (sem ano completo, no ano parcial mais recente, marcado como parcial):
- fator de capacidade e disponibilidade, da tabela anual (a de EVT ou a comum, só no nível da usina);
- TEIFa publicada pelo ONS para dezembro, no ano completo (vazia sem dezembro); no ano parcial, a do último mês
  publicado;
- energia cortada, em % da energia estimada nas semi-horas com a marca de restrição (eólicas e solares);
- atendimento ao despacho: horas com programação em que a geração ficou a até ``LIMIAR_DESVIO_DESPACHO_MW`` da
  programada, em % das horas com programação (térmicas), o único cálculo novo.

Cada indicador traz ``valor``, ``nivel`` (o do dado de origem) e ``unidade``; quando não se aplica ao tipo ou falta a
base, fica None, e nunca zero. A conclusão entra pela quantidade de todos os itens de cada lista, como na aba
CONCLUSAO, com as regras avaliadas e as não avaliadas; sem nenhuma regra avaliada com dado da usina (FR-054), as
quantidades ficam None.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.analises.conclusao import CATALOGO_CONCLUSAO, LISTAS_CONCLUSAO, regras_do_tipo
from src.analises.resultados import ResultadosAnalise, sem_evt

INDICADORES_CARTEIRA: Tuple[str, ...] = ("fator_capacidade", "disponibilidade", "teifa", "energia_cortada",
                                         "atendimento_despacho")
UNIDADE_PCT = "%"


def ano_dos_indicadores(cobertura: Dict[str, Any]) -> Tuple[Optional[int], bool]:
    """O último ano completo da série; sem ano completo, o ano parcial mais recente (``ano_parcial`` verdadeiro)."""
    completos = [int(a) for a in cobertura.get("anos_completos") or []]
    if completos:
        return max(completos), False
    parciais = [int(a) for a in cobertura.get("anos_parciais") or []]
    return (max(parciais), True) if parciais else (None, False)


def _indicador(valor: Any, nivel: str = "usina", **detalhe: Any) -> Optional[Dict[str, Any]]:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numero):
        return None
    return {"valor": numero, "nivel": nivel, "unidade": UNIDADE_PCT, **detalhe}


def _linha_do_ano(tabela: Optional[pd.DataFrame], ano: Optional[int], coluna_ano: str = "ano",
                  **filtro: Any) -> Optional[pd.Series]:
    if ano is None or tabela is None or len(tabela) == 0 or coluna_ano not in tabela.columns:
        return None
    sel = tabela[pd.to_numeric(tabela[coluna_ano], errors="coerce") == ano]
    for coluna, valor in filtro.items():
        sel = sel[sel[coluna] == valor]
    return sel.iloc[0] if len(sel) else None


def _teifa(res: ResultadosAnalise, ano: Optional[int], parcial: bool) -> Optional[Dict[str, Any]]:
    taxas = (res.ons or {}).get("taxas")
    if ano is None or taxas is None or len(taxas) == 0:
        return None
    t = taxas.dropna(subset=["teifa"]).assign(_mes=lambda d: pd.to_datetime(d["mes"]))
    t = t[t["_mes"].dt.year == ano]
    if not parcial:  # no ano completo, só a de dezembro (a janela de 60 meses fechada no fim do ano)
        t = t[t["_mes"].dt.month == 12]
    if t.empty:
        return None
    ultima = t.sort_values("_mes").iloc[-1]
    return _indicador(float(ultima["teifa"]) * 100.0, mes=pd.Timestamp(ultima["_mes"]))


def _atendimento(res: ResultadosAnalise, ano: Optional[int]) -> Optional[Dict[str, Any]]:
    a = (getattr(res, "termica", None) or {}).get("atendimento") or {}
    linha = _linha_do_ano(a.get("anual"), ano)
    if linha is None or int(linha["horas_programadas"]) == 0:
        return None
    programadas = int(linha["horas_programadas"])
    dentro = programadas - int(linha["horas_abaixo"]) - int(linha["horas_acima"])
    return _indicador(dentro / programadas * 100.0, horas_dentro=dentro, horas_programadas=programadas)


def contagens_conclusao(res: ResultadosAnalise) -> Dict[str, Optional[int]]:
    """Itens de cada lista da conclusão (todos, e não só os exibidos) e as regras avaliadas e não avaliadas.

    Nas hidrelétricas com EVT, as regras são C1 a C11 e a C20; nas demais, as do tipo, menos as que estão em ``omitidos``.
    """
    do_tipo = ([r.codigo for r in regras_do_tipo(res)] if sem_evt(res)
               else [r.codigo for r in CATALOGO_CONCLUSAO if r.funcao is not None])
    omitidas = {o["item"] for o in getattr(res, "omitidos", []) if o.get("tipo") == "regra"}
    avaliadas = [c for c in do_tipo if c not in omitidas]
    listas: List[str] = [chave for chave, _ in LISTAS_CONCLUSAO]
    saida: Dict[str, Optional[int]] = {
        chave: (sum(1 for item in res.conclusao if item["lista"] == chave) if avaliadas else None) for chave in listas}
    saida["regras_avaliadas"] = len(avaliadas)
    saida["regras_nao_avaliadas"] = len(do_tipo) - len(avaliadas)
    return saida


def indicadores_carteira(res: ResultadosAnalise) -> Dict[str, Any]:
    """Campo ``indicadores_carteira`` dos resultados, com as chaves fixas da decisão D24."""
    cobertura = res.cobertura or {}
    ano, parcial = ano_dos_indicadores(cobertura)
    if sem_evt(res):
        anual = _linha_do_ano(res.comum.get("anuais"), ano, nivel="usina")
    else:
        anual = _linha_do_ano(res.indicadores_anuais, ano)
    restricao = ((getattr(res, "renovavel", None) or {}).get("restricao") or {}).get("anual")
    corte = _linha_do_ano(restricao, ano, coluna_ano="periodo")
    return {
        "tipo": res.tipo,
        "periodo": {"inicio": cobertura.get("inicio"), "fim": cobertura.get("fim")},
        "ano": ano,
        "ano_parcial": parcial,
        "fator_capacidade": _indicador(anual["fator_capacidade_pct"]) if anual is not None else None,
        "disponibilidade": _indicador(anual["disponibilidade_relativa_pct"]) if anual is not None else None,
        "teifa": _teifa(res, ano, parcial),
        "energia_cortada": _indicador(corte["pct_estimada"]) if corte is not None else None,
        "atendimento_despacho": _atendimento(res, ano),
        "conclusao": contagens_conclusao(res),
    }
