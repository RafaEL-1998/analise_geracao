"""Hidrologia: faixas de afluência nas horas com EVT, perfil por hora do dia e resumos (spec das Análises, US2, FR-034 a FR-038)."""

from __future__ import annotations

import unicodedata
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from src.analises.comum import _resumo_serie
from src.comum.formatacao import numero_por_extenso
from src.comum.perfil import perfil_ativo
from src.comum.regras import LIMIAR_GERACAO_PARADA_MW
from src.tratamento.hidrologia import limpos
from src.tratamento.series import SerieConjunto


ACIMA_ENGOLIMENTO_USINA = "ACIMA_ENGOLIMENTO_USINA"
ATE_UMA_UNIDADE = "ATE_UMA_UNIDADE"
SEM_DADO_HIDROLOGICO = "SEM_DADO_HIDROLOGICO"
COM_PARADA_EVT = "COM_PARADA_EVT"
DEMAIS_DIAS = "DEMAIS"


def unidades_por_extenso() -> str:
    """Número de unidades geradoras do perfil, por extenso e no feminino ("duas", "três")."""
    return numero_por_extenso(perfil_ativo().parametros.unidades_geradoras, feminino=True)


def entre_unidades() -> str:
    """Faixa entre o engolimento de uma unidade e o da usina: ``ENTRE_UMA_E_<N por extenso>_UNIDADES``."""
    extenso = "".join(c for c in unicodedata.normalize("NFKD", unidades_por_extenso()) if not unicodedata.combining(c))
    return f"ENTRE_UMA_E_{extenso.upper()}_UNIDADES"


def faixas_afluencia() -> Tuple[str, ...]:
    """Faixas de afluência, da menor para a maior, e as horas sem dado hidrológico."""
    return ATE_UMA_UNIDADE, entre_unidades(), ACIMA_ENGOLIMENTO_USINA, SEM_DADO_HIDROLOGICO


def _no_periodo_da_hidrologia(df: pd.DataFrame, hid: pd.DataFrame) -> pd.DataFrame:
    if hid.empty:
        return df.iloc[0:0]
    return df[(df["din_instante"] >= hid["din_instante"].min()) & (df["din_instante"] <= hid["din_instante"].max())]


def classificar_faixas(hid: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Horas com EVT do período comum, classificadas pela afluência em relação ao engolimento das unidades."""
    evt = _no_periodo_da_hidrologia(df, hid)
    evt = evt.loc[evt["val_energiavertidaturbinavel"] > 0, ["din_instante", "val_geracao", "val_energiavertidaturbinavel"]]
    m = evt.merge(limpos(hid)[["din_instante", "val_vazaoafluente"]], on="din_instante", how="left")
    afluencia = m["val_vazaoafluente"]
    m["faixa_afluencia"] = np.select(
        [afluencia > perfil_ativo().engolimento_maximo_m3s, afluencia > perfil_ativo().parametros.engolimento_nominal_ug_m3s, afluencia <= perfil_ativo().parametros.engolimento_nominal_ug_m3s],
        [ACIMA_ENGOLIMENTO_USINA, entre_unidades(), ATE_UMA_UNIDADE],
        default=SEM_DADO_HIDROLOGICO,
    )
    return m.sort_values("din_instante").reset_index(drop=True)[
        ["din_instante", "val_vazaoafluente", "faixa_afluencia", "val_energiavertidaturbinavel", "val_geracao"]]


def resumir_faixas(classificadas: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Horas e EVT (MWh) por faixa de afluência, por mês (``"M"``) ou ano (``"Y"``), em formato longo."""
    c = classificadas.assign(periodo=classificadas["din_instante"].dt.to_period(freq).astype(str))
    resumo = c.groupby(["periodo", "faixa_afluencia"]).agg(
        horas=("din_instante", "size"), evt_mwh=("val_energiavertidaturbinavel", "sum")).reset_index()
    completo = pd.MultiIndex.from_product([sorted(c["periodo"].unique()), faixas_afluencia()],
                                          names=["periodo", "faixa_afluencia"])
    resumo = resumo.set_index(["periodo", "faixa_afluencia"]).reindex(completo, fill_value=0).reset_index()
    resumo["horas"] = resumo["horas"].astype(int)
    return resumo


def perfil_hidrologico(hid: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Médias por hora do dia, separando os dias com ao menos uma hora de parada com EVT dos demais dias."""
    evt = _no_periodo_da_hidrologia(df, hid)
    paradas = evt[(evt["val_geracao"] <= LIMIAR_GERACAO_PARADA_MW) & (evt["val_energiavertidaturbinavel"] > 0)]
    dias_com_parada = set(paradas["din_instante"].dt.normalize())
    h = limpos(hid).copy()
    h["dia"] = h["din_instante"].dt.normalize()
    h["grupo_dias"] = np.where(h["dia"].isin(dias_com_parada), COM_PARADA_EVT, DEMAIS_DIAS)
    h["hora"] = h["din_instante"].dt.hour
    return h.groupby(["grupo_dias", "hora"]).agg(
        dias=("dia", "nunique"),
        nivel_montante_medio_m=("val_nivelmontante", "mean"),
        afluencia_media_m3s=("val_vazaoafluente", "mean"),
        turbinada_media_m3s=("val_vazaoturbinada", "mean"),
        vertida_media_m3s=("val_vazaovertida", "mean"),
    ).reset_index()


def resumo_mensal_hidrologia(hid: pd.DataFrame) -> pd.DataFrame:
    """Afluência, vazões, níveis e volume útil por mês (valores sinalizados excluídos só no campo afetado)."""
    return resumir_hidrologia(hid, "M", "mes")


def resumir_hidrologia(hid: pd.DataFrame, freq: str, coluna: str = "periodo") -> pd.DataFrame:
    """Afluência, vazões, níveis e volume útil por mês (``"M"``) ou ano (``"Y"``).

    Os valores sinalizados (H1 a H4) saem só do campo afetado (``_limpos``, FR-035); a hora continua nas médias
    dos demais campos.
    """
    h = limpos(hid).copy()
    h[coluna] = h["din_instante"].dt.to_period(freq).astype(str)
    h["acima_engolimento"] = h["val_vazaoafluente"] > perfil_ativo().engolimento_maximo_m3s
    resumo = h.groupby(coluna).agg(
        horas=("din_instante", "size"),
        afluencia_media_m3s=("val_vazaoafluente", "mean"),
        afluencia_maxima_m3s=("val_vazaoafluente", "max"),
        turbinada_media_m3s=("val_vazaoturbinada", "mean"),
        vertida_media_m3s=("val_vazaovertida", "mean"),
        vertida_nao_turbinavel_media_m3s=("val_vazaovertidanaoturbinavel", "mean"),
        nivel_montante_min_m=("val_nivelmontante", "min"),
        nivel_montante_medio_m=("val_nivelmontante", "mean"),
        nivel_montante_max_m=("val_nivelmontante", "max"),
        nivel_jusante_medio_m=("val_niveljusante", "mean"),
        volume_util_medio_pct=("val_volumeutil", "mean"),
        horas_afluencia_acima_engolimento=("acima_engolimento", "sum"),
    ).reset_index()
    resumo["horas_afluencia_acima_engolimento"] = resumo["horas_afluencia_acima_engolimento"].astype(int)
    return resumo


def analisar_hidrologia(
    serie: SerieConjunto,
    alinhamento: pd.DataFrame,
    df: pd.DataFrame,
    cobertura: Dict[str, Any],
    obtido_em: str = "",
) -> Dict[str, Any]:
    """Afluência, vertimento e nível do reservatório cruzados com a base de EVT (US2).

    Sem o alinhamento confirmado (FR-034), só a cobertura e o alinhamento são devolvidos.
    """
    resumo = _resumo_serie(serie)
    qualidade_h = serie.horaria["qualidade"] if "qualidade" in serie.horaria.columns else pd.Series(dtype=object)
    resumo["sinalizadas_por_regra"] = {
        regra: {"horas": int(qualidade_h.str.contains(regra).sum()),
                "anos": serie.horaria.loc[qualidade_h.str.contains(regra), "din_instante"].dt.year.value_counts().sort_index().to_dict()}
        for regra in ("H1", "H2", "H3", "H4")
    }
    resultado: Dict[str, Any] = {
        "resumo": resumo,
        "alinhamento": alinhamento,
        "auditoria": serie.auditoria,
        "ausencias": serie.ausencias,
        "obtido_em": obtido_em,
        "publicado": bool(alinhamento.iloc[0]["confirmado"]),
    }
    if not resultado["publicado"]:
        return resultado
    hid = serie.horaria
    parciais = {str(a) for a in cobertura.get("anos_parciais", [])}
    faixas = classificar_faixas(hid, df)
    faixas_anual = resumir_faixas(faixas, "Y")
    faixas_anual["ano_parcial"] = faixas_anual["periodo"].isin(parciais)
    anual = resumir_hidrologia(hid, "Y")
    anual["ano_parcial"] = anual["periodo"].isin(parciais)
    perfil = perfil_hidrologico(hid, df)
    por_faixa = faixas.groupby("faixa_afluencia").agg(horas=("din_instante", "size"),
                                                       evt_mwh=("val_energiavertidaturbinavel", "sum"))
    por_faixa = por_faixa.reindex(faixas_afluencia(), fill_value=0)
    amplitude = (perfil.groupby("grupo_dias")["nivel_montante_medio_m"].agg(["min", "max"])
                 .assign(amplitude=lambda t: t["max"] - t["min"]))
    resultado["resumo"].update({
        "horas_evt": len(faixas),
        "evt_mwh": float(faixas["val_energiavertidaturbinavel"].sum()),
        "horas_por_faixa": por_faixa["horas"].astype(int).to_dict(),
        "evt_por_faixa_mwh": por_faixa["evt_mwh"].astype(float).to_dict(),
        "horas_afluencia_acima_engolimento": int((hid["val_vazaoafluente"] > perfil_ativo().engolimento_maximo_m3s).sum()),
        "dias_com_parada_evt": int(perfil.loc[perfil["grupo_dias"] == COM_PARADA_EVT, "dias"].max())
        if (perfil["grupo_dias"] == COM_PARADA_EVT).any() else 0,
        "nivel_amplitude_m": amplitude["amplitude"].to_dict(),
        "nivel_min_m": amplitude["min"].to_dict(),
        "nivel_max_m": amplitude["max"].to_dict(),
    })
    pico = hid.loc[hid["val_vazaoafluente"].idxmax()] if hid["val_vazaoafluente"].notna().any() else None
    resultado["resumo"]["pico_afluencia"] = None if pico is None else {
        "instante": pico["din_instante"], "afluencia_m3s": float(pico["val_vazaoafluente"]),
        "defluencia_m3s": float(pico["val_vazaodefluente"]) if pd.notna(pico.get("val_vazaodefluente")) else float("nan"),
    }
    resultado.update({
        "faixas": faixas,
        "faixas_anual": faixas_anual,
        "faixas_mensal": resumir_faixas(faixas, "M"),
        "perfil": perfil,
        "mensal": resumir_hidrologia(hid, "M", "mes"),
        "anual": anual,
    })
    return resultado
