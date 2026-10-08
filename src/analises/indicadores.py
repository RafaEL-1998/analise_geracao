"""Indicadores oficiais de disponibilidade por unidade geradora: resumos, horas por estado operativo, TEIFa e TEIP e a decomposição das taxas (spec das Análises, US2, FR-023 a FR-025)."""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

import pandas as pd

from src.comum.perfil import perfil_ativo
from src.comum.regras import JANELA_TAXAS_MESES
from src.conferencia.indicadores import janela as _janela, peso as _peso, reproducao_das_taxas
from src.tratamento.indicadores import IndicadoresONS, INSUMOS_HORAS, TOLERANCIA_IDENTIDADE_HORAS


def decompor_taxas(horas: pd.DataFrame, mes_fim: pd.Timestamp, janela_meses: int = 60) -> pd.DataFrame:
    """Contribuição de cada unidade e de cada parcela de horas para a TEIFa e a TEIP do mês."""
    colunas = ["taxa", "ug", "parcela", "horas", "contribuicao_pp", "participacao_pct"]
    janela = _janela(horas, mes_fim, janela_meses)
    if janela.empty:
        return pd.DataFrame(columns=colunas)
    p = _peso(janela)
    bases = {
        "TEIFa": (float((p * (janela["HP"] - janela["HDP"] - janela["HEDP"])).sum()), ["HDF", "HEDF"]),
        "TEIP": (float((p * janela["HP"]).sum()), ["HDP", "HEDP"]),
    }
    linhas = []
    for taxa, (base, parcelas) in bases.items():
        total = sum(float((p * janela[c]).sum()) for c in parcelas) / base * 100.0 if base else float("nan")
        for ug, g in janela.groupby("ug"):
            pg = _peso(g)
            for parcela in parcelas:
                contribuicao = float((pg * g[parcela]).sum()) / base * 100.0 if base else float("nan")
                linhas.append({
                    "taxa": taxa,
                    "ug": int(ug),
                    "parcela": parcela,
                    "horas": float(g[parcela].sum()),
                    "contribuicao_pp": contribuicao,
                    "participacao_pct": contribuicao / total * 100.0 if total else float("nan"),
                })
    return pd.DataFrame(linhas, columns=colunas)


# Descrição curta das parcelas de horas usadas nas taxas (texto das constatações e tabelas)
DESCRICAO_PARCELA: Dict[str, str] = {
    "HDF": "desligamentos forçados",
    "HEDF": "operação com limitação forçada de potência",
    "HDP": "desligamentos programados",
    "HEDP": "operação com limitação programada de potência",
}


def _media_ponderada(g: pd.DataFrame, coluna: str) -> float:
    peso = g["peso"]
    return float((g[coluna] * peso).sum() / peso.sum()) if peso.sum() else math.nan


def analisar_indicadores_ons(
    ind: IndicadoresONS,
    df: pd.DataFrame,
    indicadores_anuais: pd.DataFrame,
    cobertura: Dict[str, Any],
    recalculo: Optional[pd.DataFrame] = None,
    reproducao: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Resumo dos indicadores oficiais do ONS no período da base de EVT.

    A disponibilidade da usina pelo DISPF é a média das unidades ponderada pela potência e
    pelas horas da base de EVT em cada mês.
    """
    referencia = perfil_ativo().disponibilidade_referencia * 100.0
    parciais = set(cobertura["anos_parciais"])
    resultado: Dict[str, Any] = {}

    # Disponibilidade da usina pelo DISPF, por ano e no período
    mensal = ind.ug_mensal.copy()
    if len(mensal):
        horas_base = df.groupby(df["din_instante"].dt.to_period("M").dt.to_timestamp()).size().rename("horas_base")
        mensal = mensal.merge(horas_base, left_on="mes", right_index=True, how="inner")
        mensal["peso"] = mensal["horas_base"] * mensal["potencia_mw"].fillna(perfil_ativo().parametros.potencia_unitaria_mw)
        mensal["ano"] = mensal["mes"].dt.year
        declarada = indicadores_anuais.set_index("ano")["disponibilidade_relativa_pct"]
        linhas = []
        for ano, g in mensal.groupby("ano"):
            dispf = _media_ponderada(g, "dispf")
            linhas.append({
                "ano": int(ano),
                "ano_parcial": int(ano) in parciais,
                "disponibilidade_declarada_pct": float(declarada.get(ano, math.nan)),
                "dispf_pct": dispf,
                "indisppf_pct": _media_ponderada(g, "indisppf"),
                "indispff_pct": _media_ponderada(g, "indispff"),
                "desvio_dispf_referencia_pp": dispf - referencia,
            })
        resultado["disp_anual"] = pd.DataFrame(linhas)
        resultado["disp_periodo"] = {
            "mes_inicio": mensal["mes"].min(),
            "mes_fim": mensal["mes"].max(),
            "unidades": int(mensal["ug"].nunique()),
            "dispf_pct": _media_ponderada(mensal, "dispf"),
            "indisppf_pct": _media_ponderada(mensal, "indisppf"),
            "indispff_pct": _media_ponderada(mensal, "indispff"),
        }

    # Indicadores anuais oficiais por unidade (base anual do ONS)
    anual = ind.ug_anual.copy()
    if len(anual):
        anual["ano_parcial"] = anual["ano"].astype(int).isin(parciais)
        resultado["ug_anual"] = anual

    # Horas por estado operativo
    horas = ind.horas_estado.copy()
    if len(horas):
        horas["ano"] = horas["mes"].dt.year
        resultado["horas_mensal"] = horas
        soma = horas.groupby(["ano", "ug"])[list(INSUMOS_HORAS)].sum()
        soma["meses"] = horas.groupby(["ano", "ug"])["mes"].nunique()
        soma = soma.reset_index()
        soma["ano_parcial"] = soma["meses"] < 12
        resultado["horas_anual"] = soma
        resultado["horas_periodo"] = {
            "mes_inicio": horas["mes"].min(),
            "mes_fim": horas["mes"].max(),
            "identidade_fora": int((horas["residuo_identidade_h"].abs() > TOLERANCIA_IDENTIDADE_HORAS).sum()),
            "meses_unidade": len(horas),
        }

    # TEIFa e TEIP: valor mais recente, recálculo a partir das horas e decomposição
    taxas = ind.taxas.copy()
    if len(taxas):
        ultima = taxas.loc[taxas["mes"].idxmax()]
        teifa, teip = float(ultima["teifa"]), float(ultima["teip"])
        resultado["taxas"] = taxas
        resultado["taxa_ultima"] = {
            "mes": ultima["mes"],
            "teifa_pct": teifa * 100.0,
            "teip_pct": teip * 100.0,
            "disponibilidade_verificada_pct": (1.0 - teifa) * (1.0 - teip) * 100.0,
        }
        if len(horas) and recalculo is not None:  # recálculo da Conferência (TEIFa e TEIP)
            resultado["recalculo_taxas"] = recalculo
            completos = recalculo.dropna(subset=["teifa_recalculada"])
            if reproducao is None:  # chamada direta, sem os resultados gravados pela Conferência
                rep = reproducao_das_taxas(recalculo, horas["mes"].min())
                reproducao = {chave: rep[chave] for chave in ("meses", "reproduzidos", "diferenca_maxima_pp")}
            resultado["recalculo_resumo"] = dict(reproducao)
            if ultima["mes"] in set(completos["mes"]):
                resultado["decomposicao"] = decompor_taxas(horas, ultima["mes"], JANELA_TAXAS_MESES)

    if len(ind.divergencias):
        resultado["divergencias"] = ind.divergencias.copy()
    else:
        resultado["divergencias"] = pd.DataFrame()
    return resultado
