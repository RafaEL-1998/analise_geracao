"""Indicadores, eventos, distribuições, perfis, extremos e anomalias da base de EVT (spec das Análises, US1)."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from src.analises.comum import (
    _mascara_evt,
    _mascara_indisponibilidade_total,
    _mascara_parada_com_evt,
    _mascara_vertimento_minimo,
    _media,
    _pct,
    _razao,
    horas_no_ano,
)
from src.comum.formatacao import fmt_num, MESES_ABREVIADOS, MESES_EXTENSO
from src.comum.logger import setup_logger
from src.comum.perfil import perfil_ativo
from src.comum.regras import (
    FRACAO_PLENA_CARGA,
    HORAS_DIURNAS,
    HORAS_NOTURNAS,
    LIMIAR_GERACAO_PARADA_MW,
    LIMIAR_INDISPONIBILIDADE_TOTAL_MW,
    OPERATIONAL_METRIC_COLUMNS,
)
from src.tratamento.validacao import (
    COLUNA_QUALIDADE,
    COLUNAS_ANOMALIA,
    DESCRICAO_ANOMALIA,
    QUALIDADE_OK,
    sinalizar_anomalias,
)

logger = setup_logger("analises")


UNIDADES: Dict[str, str] = {
    "val_geracao": "MWmed",
    "val_disponibilidade": "MWmed",
    "val_vazaoturbinada": "m³/s",
    "val_vazaovertida": "m³/s",
    "val_vazaovertidanaoturbinavel": "m³/s",
    "val_produtividade": "MW/(m³/s)",
    "val_folgadegeracao": "MWmed",
    "val_energiavertida": "MWmed",
    "val_vazaovertidaturbinavel": "m³/s",
    "val_energiavertidaturbinavel": "MWmed",
}


def preparar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena, cria colunas de calendário e garante as colunas de qualidade."""
    df = df.copy()
    df["din_instante"] = pd.to_datetime(df["din_instante"])
    df = df.sort_values("din_instante").reset_index(drop=True)
    df["ano"] = df["din_instante"].dt.year
    df["mes"] = df["din_instante"].dt.month
    df["hora"] = df["din_instante"].dt.hour
    if COLUNA_QUALIDADE not in df.columns:
        df = sinalizar_anomalias(df, perfil_ativo())
    return df


def calcular_indicadores_anuais(df: pd.DataFrame, cobertura: Dict[str, Any]) -> pd.DataFrame:
    """Indicadores por ano civil (anos parciais sinalizados)."""
    P = perfil_ativo().parametros.potencia_instalada_mw
    parciais = set(cobertura["anos_parciais"])
    linhas = []
    for ano, g in df.groupby("ano"):
        horas = len(g)
        ger_med = _media(g["val_geracao"])
        disp_med = _media(g["val_disponibilidade"])
        energia = float(g["val_geracao"].sum())
        evt = float(g["val_energiavertidaturbinavel"].sum())
        evt_minimo = float(g.loc[_mascara_vertimento_minimo(g), "val_energiavertidaturbinavel"].sum())
        parada = _mascara_parada_com_evt(g)
        diurno = g["hora"].isin(HORAS_DIURNAS)
        noturno = g["hora"].isin(HORAS_NOTURNAS)
        disp = g["val_disponibilidade"]
        linhas.append(
            {
                "ano": int(ano),
                "ano_parcial": int(ano) in parciais,
                "horas_observadas": horas,
                "cobertura_pct": horas / horas_no_ano(int(ano)) * 100.0,
                "geracao_media_mwmed": ger_med,
                "disponibilidade_media_mwmed": disp_med,
                "fator_capacidade_pct": ger_med / P * 100.0,
                "disponibilidade_relativa_pct": disp_med / P * 100.0,
                "desvio_disponibilidade_referencia_pp": disp_med / P * 100.0 - perfil_ativo().disponibilidade_referencia * 100.0,
                "geracao_sobre_garantia_fisica_pct": ger_med / perfil_ativo().parametros.garantia_fisica_mwmed * 100.0,
                "energia_gerada_mwh": energia,
                "evt_mwh": evt,
                "evt_vertimento_minimo_mwh": evt_minimo,
                "evt_demais_horas_mwh": evt - evt_minimo,
                "participacao_vertimento_minimo_pct": _pct(evt_minimo, evt),
                "indice_evt_pct": _pct(evt, energia + evt),
                "horas_com_evt": int(_mascara_evt(g).sum()),
                "horas_com_evt_pct": _pct(int(_mascara_evt(g).sum()), horas),
                "horas_parada_com_evt": int(parada.sum()),
                "evt_parada_mwh": float(g.loc[parada, "val_energiavertidaturbinavel"].sum()),
                "horas_indisponibilidade_total": int(_mascara_indisponibilidade_total(g).sum()),
                "horas_disponibilidade_ate_metade": int(((disp > LIMIAR_INDISPONIBILIDADE_TOTAL_MW) & (disp <= P / 2)).sum()),
                "evt_media_diurna_mw": _media(g.loc[diurno, "val_energiavertidaturbinavel"]),
                "evt_media_noturna_mw": _media(g.loc[noturno, "val_energiavertidaturbinavel"]),
                "razao_evt_diurna_noturna": _razao(
                    _media(g.loc[diurno, "val_energiavertidaturbinavel"]),
                    _media(g.loc[noturno, "val_energiavertidaturbinavel"]),
                ),
                "geracao_media_diurna_mw": _media(g.loc[diurno, "val_geracao"]),
                "geracao_media_noturna_mw": _media(g.loc[noturno, "val_geracao"]),
                "razao_geracao_diurna_noturna": _razao(
                    _media(g.loc[diurno, "val_geracao"]), _media(g.loc[noturno, "val_geracao"])
                ),
                "horas_com_anomalia": int((g[COLUNA_QUALIDADE] != QUALIDADE_OK).sum()),
            }
        )
    return pd.DataFrame(linhas)


def calcular_indicadores_globais(df: pd.DataFrame) -> Dict[str, Any]:
    """Indicadores do período completo, ponderados por hora."""
    P = perfil_ativo().parametros.potencia_instalada_mw
    horas = len(df)
    ger_med = _media(df["val_geracao"])
    disp_med = _media(df["val_disponibilidade"])
    energia = float(df["val_geracao"].sum())
    evt = float(df["val_energiavertidaturbinavel"].sum())
    com_evt = _mascara_evt(df)
    parada = _mascara_parada_com_evt(df)
    limiar_plena = FRACAO_PLENA_CARGA * P
    plena = df["val_geracao"] >= limiar_plena
    evt_plena = float(df.loc[plena & com_evt, "val_energiavertidaturbinavel"].sum())
    evt_parada = float(df.loc[parada, "val_energiavertidaturbinavel"].sum())
    excede_folga = int((df["val_energiavertidaturbinavel"] - df["val_folgadegeracao"] > 1e-6).sum())
    anomalos = df[COLUNA_QUALIDADE] != QUALIDADE_OK
    idx_ger_max = df["val_geracao"].idxmax()

    return {
        "horas": horas,
        "geracao_media_mwmed": ger_med,
        "disponibilidade_media_mwmed": disp_med,
        "fator_capacidade_pct": ger_med / P * 100.0,
        "disponibilidade_relativa_pct": disp_med / P * 100.0,
        "disponibilidade_referencia_pct": perfil_ativo().disponibilidade_referencia * 100.0,
        "desvio_disponibilidade_referencia_pp": disp_med / P * 100.0 - perfil_ativo().disponibilidade_referencia * 100.0,
        "geracao_sobre_garantia_fisica_pct": ger_med / perfil_ativo().parametros.garantia_fisica_mwmed * 100.0,
        "energia_gerada_mwh": energia,
        "evt_mwh": evt,
        "indice_evt_pct": _pct(evt, energia + evt),
        "horas_com_evt": int(com_evt.sum()),
        "horas_com_evt_pct": _pct(int(com_evt.sum()), horas),
        "folga_media_com_evt_mw": _media(df.loc[com_evt, "val_folgadegeracao"]),
        "limiar_plena_carga_mw": limiar_plena,
        "evt_plena_carga_mwh": evt_plena,
        "evt_plena_carga_pct": _pct(evt_plena, evt),
        "horas_evt_acima_folga": excede_folga,
        "horas_parada_com_evt": int(parada.sum()),
        "evt_parada_mwh": evt_parada,
        "evt_parada_pct": _pct(evt_parada, evt),
        "disponibilidade_media_nas_paradas_mw": _media(df.loc[parada, "val_disponibilidade"]),
        "horas_geracao_zero": int((df["val_geracao"] == 0).sum()),
        "horas_geracao_zero_com_evt": int(((df["val_geracao"] == 0) & com_evt).sum()),
        "horas_geracao_ate_limiar_positiva_com_evt": int(((df["val_geracao"] > 0) & parada).sum()),
        "horas_com_anomalia": int(anomalos.sum()),
        "evt_em_registros_anomalos_mwh": float(df.loc[anomalos, "val_energiavertidaturbinavel"].sum()),
        "geracao_maxima_registrada_mw": float(df.loc[idx_ger_max, "val_geracao"]),
        "instante_geracao_maxima": df.loc[idx_ger_max, "din_instante"],
    }


def identificar_eventos(
    df: pd.DataFrame,
    mascara: pd.Series,
    agregacoes: Dict[str, Tuple[str, str]],
) -> pd.DataFrame:
    """Agrupa horas consecutivas em que a máscara é verdadeira (lacunas de horário quebram o evento)."""
    base = df.sort_values("din_instante")
    m = mascara.reindex(base.index).fillna(False).astype(bool)
    continuidade = base["din_instante"].diff().eq(pd.Timedelta(hours=1))
    inicio_evento = m & ~(m.shift(fill_value=False) & continuidade)
    grupo = inicio_evento.cumsum()
    selecao = base.loc[m].assign(_evento=grupo[m])
    colunas = ["inicio", "fim", "duracao_h", *agregacoes.keys()]
    if selecao.empty:
        return pd.DataFrame(columns=colunas)
    eventos = selecao.groupby("_evento").agg(
        inicio=("din_instante", "min"),
        fim=("din_instante", "max"),
        duracao_h=("din_instante", "size"),
        **agregacoes,
    )
    return eventos.reset_index(drop=True)[colunas]


def listar_eventos_parada_com_evt(df: pd.DataFrame) -> pd.DataFrame:
    """Eventos em que a usina ficou parada com vertimento turbinável."""
    return identificar_eventos(
        df,
        _mascara_parada_com_evt(df),
        {
            "geracao_media_mw": ("val_geracao", "mean"),
            "disponibilidade_media_mw": ("val_disponibilidade", "mean"),
            "vazao_vertida_media_m3s": ("val_vazaovertida", "mean"),
            "evt_mwh": ("val_energiavertidaturbinavel", "sum"),
        },
    )


def listar_eventos_indisponibilidade_total(df: pd.DataFrame) -> pd.DataFrame:
    """Eventos com disponibilidade declarada igual a zero."""
    return identificar_eventos(
        df,
        _mascara_indisponibilidade_total(df),
        {
            "vazao_vertida_media_m3s": ("val_vazaovertida", "mean"),
            "geracao_media_mw": ("val_geracao", "mean"),
        },
    )


def detectar_mudanca_classificacao(df: pd.DataFrame) -> Dict[str, Any]:
    """Detecta o mês a partir do qual a vazão vertida não turbinável passa a ser sempre positiva.

    Regra: mediana mensal de val_vazaovertidanaoturbinavel > 0 em todos os meses a partir
    do mês detectado e igual a zero no mês anterior.
    """
    periodo = df["din_instante"].dt.to_period("M")
    mediana = df.groupby(periodo)["val_vazaovertidanaoturbinavel"].median()
    positivos = (mediana > 0).to_numpy()
    zeros = np.flatnonzero(~positivos)
    if len(zeros) == 0 or zeros[-1] == len(positivos) - 1:
        return {"mes": None}

    mes = mediana.index[zeros[-1] + 1]
    minimo = _mascara_vertimento_minimo(df)
    antes = df[(periodo < mes) & minimo]
    depois = df[(periodo >= mes) & minimo]
    horas_antes = int((periodo < mes).sum())
    return {
        "mes": mes,
        "meses_antes": int((mediana.index < mes).sum()),
        "meses_depois": int((mediana.index >= mes).sum()),
        "turbinavel_tipica_antes_m3s": float(antes["val_vazaovertidaturbinavel"].median()) if len(antes) else math.nan,
        "nao_turbinavel_tipica_depois_m3s": float(depois["val_vazaovertidanaoturbinavel"].median()) if len(depois) else math.nan,
        "evt_media_vertimento_minimo_antes_mw": _media(antes["val_energiavertidaturbinavel"]),
        "pct_horas_vertimento_minimo_turbinavel_antes": _pct(
            int((antes["val_vazaovertidaturbinavel"] > 0).sum()), horas_antes
        ),
    }


def calcular_evt_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """EVT, geração e disponibilidade por mês, separando a EVT das horas de vertimento mínimo."""
    periodo = df["din_instante"].dt.to_period("M")
    evt_minimo = df["val_energiavertidaturbinavel"].where(_mascara_vertimento_minimo(df), 0.0)
    tabela = (
        df.assign(_periodo=periodo, _evt_minimo=evt_minimo)
        .groupby("_periodo")
        .agg(
            horas=("din_instante", "size"),
            energia_gerada_mwh=("val_geracao", "sum"),
            geracao_media_mw=("val_geracao", "mean"),
            disponibilidade_media_mw=("val_disponibilidade", "mean"),
            evt_mwh=("val_energiavertidaturbinavel", "sum"),
            evt_vertimento_minimo_mwh=("_evt_minimo", "sum"),
        )
    )
    tabela["evt_demais_horas_mwh"] = tabela["evt_mwh"] - tabela["evt_vertimento_minimo_mwh"]
    tabela.index = tabela.index.to_timestamp()
    tabela.index.name = "mes"
    return tabela.reset_index()


def calcular_distribuicao_mes_do_ano(df: pd.DataFrame, anos: List[int]) -> pd.DataFrame:
    """Participação de cada mês do ano na EVT, somando apenas os anos informados."""
    sub = df[df["ano"].isin(anos)]
    soma = sub.groupby("mes")["val_energiavertidaturbinavel"].sum().reindex(range(1, 13), fill_value=0.0)
    total = float(soma.sum())
    return pd.DataFrame(
        {
            "mes": list(range(1, 13)),
            "mes_nome": MESES_EXTENSO,
            "evt_mwh": soma.to_numpy(),
            "participacao_pct": [_pct(v, total) for v in soma.to_numpy()],
        }
    )


def calcular_evt_por_faixa_geracao(df: pd.DataFrame) -> pd.DataFrame:
    """Distribuição das horas com EVT pelo nível de geração no mesmo horário."""
    com_evt = df[_mascara_evt(df)]
    limiar_plena = FRACAO_PLENA_CARGA * perfil_ativo().parametros.potencia_instalada_mw
    ger = com_evt["val_geracao"]

    condicoes = [ger <= LIMIAR_GERACAO_PARADA_MW]
    rotulos = [f"até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW (usina parada)"]
    anterior = LIMIAR_GERACAO_PARADA_MW
    for limite in list(perfil_ativo().analises.faixas_geracao_mw):
        condicoes.append((ger > anterior) & (ger <= limite))
        rotulos.append(f"de {fmt_num(anterior, 0)} a {fmt_num(limite, 0)} MW")
        anterior = limite
    condicoes.append((ger > anterior) & (ger < limiar_plena))
    rotulos.append(f"de {fmt_num(anterior, 0)} a {fmt_num(limiar_plena, 1)} MW")
    condicoes.append(ger >= limiar_plena)
    rotulos.append(f"{fmt_num(limiar_plena, 1)} MW ou mais (plena carga)")

    faixa = np.select(condicoes, rotulos, default="sem classificação")
    tabela = (
        com_evt.assign(faixa=faixa)
        .groupby("faixa")
        .agg(
            horas=("din_instante", "size"),
            evt_mwh=("val_energiavertidaturbinavel", "sum"),
            geracao_media_mw=("val_geracao", "mean"),
            disponibilidade_media_mw=("val_disponibilidade", "mean"),
        )
        .reindex(rotulos)
    )
    tabela[["horas", "evt_mwh"]] = tabela[["horas", "evt_mwh"]].fillna(0)
    tabela["participacao_evt_pct"] = [_pct(v, float(tabela["evt_mwh"].sum())) for v in tabela["evt_mwh"]]
    tabela.index.name = "faixa_geracao"
    return tabela.reset_index()


def calcular_perfil_horario(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """Média por ano (linhas) e hora do dia (colunas)."""
    return df.pivot_table(index="ano", columns="hora", values=coluna, aggfunc="mean")


def calcular_horas_geracao_zero(df: pd.DataFrame) -> pd.DataFrame:
    """Horas com val_geracao igual a zero por ano (linhas) e mês (colunas), com totais.

    Meses sem nenhum registro na série ficam vazios (NaN), não zero.
    """
    zero = df["val_geracao"] == 0
    anos = sorted(df["ano"].unique())
    observadas = df.groupby(["ano", "mes"]).size().unstack().reindex(index=anos, columns=range(1, 13))
    contagem = (
        df[zero].groupby(["ano", "mes"]).size().unstack()
        .reindex(index=anos, columns=range(1, 13)).fillna(0)
    )
    tabela = contagem.where(observadas.notna())
    tabela.columns = MESES_ABREVIADOS
    tabela["total"] = contagem.sum(axis=1)
    tabela["com_disponibilidade_zero"] = (
        (zero & _mascara_indisponibilidade_total(df)).groupby(df["ano"]).sum().reindex(anos, fill_value=0)
    )
    tabela["com_usina_disponivel"] = tabela["total"] - tabela["com_disponibilidade_zero"]
    tabela.index.name = "ano"
    return tabela.reset_index()


def _registros_validos(df: pd.DataFrame) -> pd.DataFrame:
    return df[df[COLUNA_QUALIDADE] == QUALIDADE_OK]


def calcular_perfil_estatistico_anual(df: pd.DataFrame) -> pd.DataFrame:
    """Estatísticas anuais das 10 variáveis, excluindo registros sinalizados com anomalia."""
    logger.info("Calculando perfil estatístico anual das 10 variáveis contínuas...")
    validos = _registros_validos(df)
    linhas: List[Dict[str, Any]] = []

    for ano, df_ano in validos.groupby("ano"):
        for col in OPERATIONAL_METRIC_COLUMNS:
            serie = df_ano[col].dropna()
            if serie.empty:
                continue
            id_min = serie.idxmin()
            id_max = serie.idxmax()
            linhas.append(
                {
                    "ano": int(ano),
                    "variavel": col,
                    "unidade": UNIDADES.get(col, ""),
                    "registros_considerados": len(serie),
                    "media": round(float(serie.mean()), 4),
                    "desvio_padrao": round(float(serie.std(ddof=1)) if len(serie) > 1 else 0.0, 4),
                    "mediana": round(float(serie.median()), 4),
                    "percentil_25": round(float(serie.quantile(0.25)), 4),
                    "percentil_75": round(float(serie.quantile(0.75)), 4),
                    "soma_acumulada": round(float(serie.sum()), 2),
                    "valor_minimo": round(float(serie.loc[id_min]), 4),
                    "data_hora_min": str(df_ano.loc[id_min, "din_instante"]),
                    "valor_maximo": round(float(serie.loc[id_max]), 4),
                    "data_hora_max": str(df_ano.loc[id_max, "din_instante"]),
                }
            )

    return pd.DataFrame(linhas)


def mapear_extremos_historicos(df: pd.DataFrame) -> pd.DataFrame:
    """Máximos e mínimos do período, excluindo registros sinalizados com anomalia."""
    validos = _registros_validos(df)
    linhas: List[Dict[str, Any]] = []
    for col in OPERATIONAL_METRIC_COLUMNS:
        serie = validos[col].dropna()
        if serie.empty:
            continue
        id_max = serie.idxmax()
        id_min = serie.idxmin()
        linhas.append(
            {
                "variavel": col,
                "unidade": UNIDADES.get(col, ""),
                "maximo_historico": round(float(serie.loc[id_max]), 4),
                "data_hora_max": str(validos.loc[id_max, "din_instante"]),
                "minimo_historico": round(float(serie.loc[id_min]), 4),
                "data_hora_min": str(validos.loc[id_min, "din_instante"]),
            }
        )
    return pd.DataFrame(linhas)


def listar_anomalias(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Lista cronológica dos registros sinalizados e resumo por regra."""
    colunas = [
        "din_instante",
        COLUNA_QUALIDADE,
        "val_geracao",
        "val_disponibilidade",
        "val_vazaoturbinada",
        "val_produtividade",
        "val_energiavertida",
        "val_energiavertidaturbinavel",
    ]
    lista = df.loc[df[COLUNA_QUALIDADE] != QUALIDADE_OK, colunas].sort_values("din_instante").reset_index(drop=True)
    resumo = []
    for codigo, coluna in COLUNAS_ANOMALIA.items():
        sel = df[df[coluna].astype(bool)]
        resumo.append(
            {
                "regra": codigo,
                "descricao": DESCRICAO_ANOMALIA[codigo],
                "horas": len(sel),
                "primeira_ocorrencia": sel["din_instante"].min() if len(sel) else pd.NaT,
                "ultima_ocorrencia": sel["din_instante"].max() if len(sel) else pd.NaT,
                "evt_mwh": float(sel["val_energiavertidaturbinavel"].sum()),
            }
        )
    return lista, pd.DataFrame(resumo)


def calcular_serie_diaria(df: pd.DataFrame) -> pd.DataFrame:
    """Médias diárias de disponibilidade declarada, geração e EVT (dados da figura 01)."""
    return (
        df.set_index("din_instante")[["val_disponibilidade", "val_geracao", "val_energiavertidaturbinavel"]]
        .resample("D")
        .mean()
    )


def calcular_vazoes_anuais(df: pd.DataFrame) -> pd.DataFrame:
    """Médias anuais das vazões turbinada, vertida turbinável e vertida não turbinável (dados da figura 05)."""
    return df.groupby("ano")[["val_vazaoturbinada", "val_vazaovertidaturbinavel", "val_vazaovertidanaoturbinavel"]].mean()
