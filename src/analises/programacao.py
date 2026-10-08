"""Programação diária × operação verificada: classificação das horas, resumo mensal, eventos de desvio e perfil por hora do dia (spec das Análises, US2, FR-026 a FR-029)."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from src.analises.comum import _media, _pct
from src.comum.formatacao import fmt_num
from src.comum.regras import HORAS_DIURNAS, LIMIAR_DESVIO_PROGRAMACAO_MW, LIMIAR_GERACAO_PARADA_MW
from src.tratamento.programacao import ProgramacaoONS


# Classes das horas comuns à base de EVT e à programação
PARADA_EVT_PROGRAMACAO_ZERO = "PARADA_EVT_PROGRAMACAO_ZERO"


PARADA_EVT_PROGRAMACAO_POSITIVA = "PARADA_EVT_PROGRAMACAO_POSITIVA"
PARADA_SEM_EVT = "PARADA_SEM_EVT"
GERANDO_PROGRAMACAO_ZERO = "GERANDO_PROGRAMACAO_ZERO"
GERANDO_COM_PROGRAMACAO = "GERANDO_COM_PROGRAMACAO"
DESCRICAO_CLASSES: Dict[str, str] = {
    PARADA_EVT_PROGRAMACAO_ZERO: f"usina parada com EVT e programação de até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW",
    PARADA_EVT_PROGRAMACAO_POSITIVA: f"usina parada com EVT e programação acima de {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW",
    PARADA_SEM_EVT: "usina parada sem EVT",
    GERANDO_PROGRAMACAO_ZERO: f"usina gerando com programação de até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW",
    GERANDO_COM_PROGRAMACAO: f"usina gerando com programação acima de {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW",
}


def classificar_horas(operacao: pd.DataFrame, horaria: pd.DataFrame) -> pd.DataFrame:
    """Cruza a operação verificada (base de EVT) com a programação nas horas comuns e classifica cada hora."""
    colunas = ["din_instante", "val_geracao", "val_energiavertidaturbinavel", "val_disponibilidade"]
    m = operacao[colunas].merge(horaria[["din_instante", "geracao_programada_mw"]], on="din_instante", how="inner")
    m = m.dropna(subset=["geracao_programada_mw"])
    parada = m["val_geracao"] <= LIMIAR_GERACAO_PARADA_MW
    evt = m["val_energiavertidaturbinavel"] > 0
    prog_zero = m["geracao_programada_mw"] <= LIMIAR_GERACAO_PARADA_MW
    m["classe"] = GERANDO_COM_PROGRAMACAO
    m.loc[~parada & prog_zero, "classe"] = GERANDO_PROGRAMACAO_ZERO
    m.loc[parada & ~evt, "classe"] = PARADA_SEM_EVT
    m.loc[parada & evt & ~prog_zero, "classe"] = PARADA_EVT_PROGRAMACAO_POSITIVA
    m.loc[parada & evt & prog_zero, "classe"] = PARADA_EVT_PROGRAMACAO_ZERO
    m["desvio_programacao"] = parada & (m["geracao_programada_mw"] > LIMIAR_DESVIO_PROGRAMACAO_MW)
    return m.sort_values("din_instante").reset_index(drop=True)


def resumo_mensal(classificadas: pd.DataFrame) -> pd.DataFrame:
    """Horas por classe, EVT e desvios por mês (horas comuns às duas fontes)."""
    if classificadas.empty:
        return pd.DataFrame()
    c = classificadas.assign(mes=classificadas["din_instante"].dt.to_period("M").dt.to_timestamp())
    linhas = []
    for mes, g in c.groupby("mes"):
        gz = g[g["classe"] == PARADA_EVT_PROGRAMACAO_ZERO]
        evt = float(g["val_energiavertidaturbinavel"].sum())
        evt_zero = float(gz["val_energiavertidaturbinavel"].sum())
        linha = {"mes": mes, "horas_comuns": len(g)}
        for classe in DESCRICAO_CLASSES:
            linha[f"horas_{classe.lower()}"] = int((g["classe"] == classe).sum())
        linha.update({
            "horas_parada_com_evt": int(g["classe"].isin([PARADA_EVT_PROGRAMACAO_ZERO, PARADA_EVT_PROGRAMACAO_POSITIVA]).sum()),
            "evt_mwh": evt,
            "evt_parada_programacao_zero_mwh": evt_zero,
            "participacao_evt_programacao_zero_pct": evt_zero / evt * 100.0 if evt else float("nan"),
            "horas_desvio_programacao": int(g["desvio_programacao"].sum()),
            "disponibilidade_media_parada_programacao_zero_mw": float(gz["val_disponibilidade"].mean()) if len(gz) else float("nan"),
            "desvio_medio_absoluto_mw": float((g["val_geracao"] - g["geracao_programada_mw"]).abs().mean()),
        })
        linhas.append(linha)
    return pd.DataFrame(linhas)


def eventos_desvio(classificadas: pd.DataFrame) -> pd.DataFrame:
    """Horas consecutivas com a usina parada e programação acima do limiar de desvio."""
    colunas = ["inicio", "fim", "duracao_h", "programacao_media_mw", "disponibilidade_media_mw", "evt_mwh"]
    if classificadas.empty:
        return pd.DataFrame(columns=colunas)
    c = classificadas.sort_values("din_instante")
    m = c["desvio_programacao"].astype(bool)
    continuidade = c["din_instante"].diff().eq(pd.Timedelta(hours=1))
    inicio_evento = m & ~(m.shift(fill_value=False) & continuidade)
    grupo = inicio_evento.cumsum()
    sel = c[m].assign(_evento=grupo[m])
    if sel.empty:
        return pd.DataFrame(columns=colunas)
    eventos = sel.groupby("_evento").agg(
        inicio=("din_instante", "min"),
        fim=("din_instante", "max"),
        duracao_h=("din_instante", "size"),
        programacao_media_mw=("geracao_programada_mw", "mean"),
        disponibilidade_media_mw=("val_disponibilidade", "mean"),
        evt_mwh=("val_energiavertidaturbinavel", "sum"),
    )
    return eventos.reset_index(drop=True)[colunas]


def perfil_hora_do_dia(classificadas: pd.DataFrame) -> pd.DataFrame:
    """Horas de usina parada com EVT e programação zero (e a EVT correspondente) por hora do dia."""
    z = classificadas[classificadas["classe"] == PARADA_EVT_PROGRAMACAO_ZERO]
    horas = z.groupby(z["din_instante"].dt.hour).agg(
        horas=("din_instante", "size"), evt_mwh=("val_energiavertidaturbinavel", "sum")
    )
    horas = horas.reindex(range(24), fill_value=0)
    horas.index.name = "hora"
    return horas.reset_index()


def analisar_programacao(prog: ProgramacaoONS, df: pd.DataFrame) -> Dict[str, Any]:
    """Cruza a programação diária do ONS com a operação verificada nas horas comuns."""
    classificadas = classificar_horas(df, prog.horaria)
    mensal = resumo_mensal(classificadas)
    eventos = eventos_desvio(classificadas)
    perfil = perfil_hora_do_dia(classificadas)
    inicio, fim = prog.horaria["din_instante"].min(), prog.horaria["din_instante"].max()
    base_no_periodo = int(((df["din_instante"] >= inicio) & (df["din_instante"] <= fim)).sum())

    zero = classificadas["classe"] == PARADA_EVT_PROGRAMACAO_ZERO
    parada_evt = classificadas["classe"].isin([PARADA_EVT_PROGRAMACAO_ZERO, PARADA_EVT_PROGRAMACAO_POSITIVA])
    evt = float(classificadas["val_energiavertidaturbinavel"].sum())
    evt_zero = float(classificadas.loc[zero, "val_energiavertidaturbinavel"].sum())
    horas_zero = int(zero.sum())
    diurnas = int(perfil.loc[perfil["hora"].isin(HORAS_DIURNAS), "horas"].sum())
    maior = eventos.loc[eventos["duracao_h"].idxmax()] if len(eventos) else None
    dias_ausentes = prog.dias_ausentes.copy()
    periodo = {
        "primeiro_dia": inicio.normalize(),
        "ultimo_dia": fim.normalize(),
        "dias_com_arquivo": int(prog.horaria["din_instante"].dt.normalize().nunique()),
        "dias_ausentes": len(dias_ausentes),
        "lista_dias_ausentes": [pd.Timestamp(d) for d in dias_ausentes["dia"]] if len(dias_ausentes) else [],
        "horas_comuns": len(classificadas),
        "horas_base_sem_programacao": base_no_periodo - len(classificadas),
        "horas_parada_com_evt": int(parada_evt.sum()),
        "horas_parada_evt_programacao_zero": horas_zero,
        "pct_horas_programacao_zero": _pct(horas_zero, int(parada_evt.sum())),
        "disponibilidade_media_programacao_zero_mw": _media(classificadas.loc[zero, "val_disponibilidade"]),
        "evt_horas_comuns_mwh": evt,
        "evt_programacao_zero_mwh": evt_zero,
        "pct_evt_programacao_zero": _pct(evt_zero, evt),
        "pct_horas_zero_janela_diurna": _pct(diurnas, horas_zero),
        "horas_desvio": int(classificadas["desvio_programacao"].sum()),
        "eventos_desvio": len(eventos),
        "maior_evento": maior,
        "horas_gerando_programacao_zero": int((classificadas["classe"] == "GERANDO_PROGRAMACAO_ZERO").sum()),
        "correlacao_geracao_programacao": float(classificadas["val_geracao"].corr(classificadas["geracao_programada_mw"])),
        "desvio_medio_absoluto_mw": float((classificadas["val_geracao"] - classificadas["geracao_programada_mw"]).abs().mean()),
    }
    return {
        "periodo": periodo,
        "mensal": mensal,
        "eventos": eventos,
        "perfil": perfil,
        "dias_ausentes": dias_ausentes,
        "auditoria": prog.auditoria,
        "classificadas": classificadas,
    }
