"""Conferências entre fontes das térmicas: G3 e G4 (spec 006, fase B; decisão R13; rascunho 003, FR-020 e FR-021).

- **G3** (``programacao_despacho``): a Programação diária (média horária dos patamares) × a geração programada do
  despacho (``val_proggeracao``), hora a hora, só com a programação no nível da usina.
- **G4** (``verificada_despacho``): a geração verificada do despacho (``val_verifgeracao``) × a Geração por usina, hora a
  hora, no nível da usina. A G4 também mede a coincidência com uma hora de deslocamento: se ela melhorar, a convenção
  de hora declarada está errada e vira correção, nunca ajuste automático (FR-037 do rascunho 002).

As duas usam a tolerância de hoje (0,01 MW) e só registram, sem meta (decisão R13).
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import pandas as pd

from src.comum.logger import setup_logger
from src.comum.periodos import periodos_continuos
from src.comum.regras import TOLERANCIA_COINCIDENCIA_MW
from src.conferencia.resultado import ResultadoConferencia, diferenca_absoluta, nao_aplicavel

logger = setup_logger("conferencia")

BASES_G3 = ("Programação diária (média horária dos patamares)",
            "Geração térmica por motivo de despacho (val_proggeracao)")
BASES_G4 = ("Geração térmica por motivo de despacho (val_verifgeracao)", "Geração por usina (val_geracao)")
COLUNAS_MENSAL = ["mes", "energia_a_mwh", "energia_b_mwh", "diferenca_mwh", "horas_comuns", "horas_divergentes",
                  "horas_so_a", "horas_so_b"]


def _coincidencia(a: pd.DataFrame, b: pd.DataFrame, tolerancia: float, horas: int = 0) -> Optional[float]:
    """% de horas comuns coincidentes com ``b`` deslocada de ``horas``."""
    deslocada = b.assign(din_instante=b["din_instante"] + pd.Timedelta(hours=horas))
    j = a.merge(deslocada, on="din_instante", how="inner")
    if j.empty:
        return None
    return float(100.0 * (diferenca_absoluta(j["valor_a"] - j["valor_b"]) <= tolerancia).mean())


def conferir_series(a: pd.DataFrame, b: pd.DataFrame, tolerancia: float = TOLERANCIA_COINCIDENCIA_MW,
                    deslocamento: bool = False) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """Duas séries horárias (``din_instante``, ``valor_a`` / ``valor_b``), hora a hora: resumo, tabela mensal e
    períodos divergentes. Só horas com valor nas duas são comparadas; as demais são contadas."""
    a = a[["din_instante", "valor_a"]].dropna()
    b = b[["din_instante", "valor_b"]].dropna()
    juntos = a.merge(b, on="din_instante", how="outer", indicator=True)
    comuns = juntos[juntos["_merge"] == "both"].copy()
    comuns["diferenca_mw"] = (comuns["valor_a"] - comuns["valor_b"]).abs()
    divergentes = comuns[diferenca_absoluta(comuns["diferenca_mw"]) > tolerancia]
    resumo: Dict[str, Any] = {
        "horas_comuns": len(comuns), "coincidentes": int(len(comuns) - len(divergentes)),
        "divergentes": int(len(divergentes)),
        "pct_coincidentes": float(100.0 * (len(comuns) - len(divergentes)) / len(comuns)) if len(comuns) else float("nan"),
        "so_a": int((juntos["_merge"] == "left_only").sum()), "so_b": int((juntos["_merge"] == "right_only").sum()),
        "energia_a_mwh": float(comuns["valor_a"].sum()), "energia_b_mwh": float(comuns["valor_b"].sum()),
        "tolerancia_mw": tolerancia,
    }
    if deslocamento:
        resumo["pct_coincidentes_deslocada"] = {"+1 h": _coincidencia(a, b, tolerancia, 1),
                                                "-1 h": _coincidencia(a, b, tolerancia, -1)}
    juntos["mes"] = juntos["din_instante"].dt.to_period("M").astype(str)
    juntos["_comum"] = juntos["_merge"] == "both"
    juntos["_divergente"] = juntos["din_instante"].isin(divergentes["din_instante"])
    juntos["_so_a"] = juntos["_merge"] == "left_only"
    juntos["_so_b"] = juntos["_merge"] == "right_only"
    juntos["_a"] = juntos["valor_a"].where(juntos["_comum"])
    juntos["_b"] = juntos["valor_b"].where(juntos["_comum"])
    mensal = juntos.groupby("mes").agg(
        energia_a_mwh=("_a", "sum"), energia_b_mwh=("_b", "sum"), horas_comuns=("_comum", "sum"),
        horas_divergentes=("_divergente", "sum"), horas_so_a=("_so_a", "sum"), horas_so_b=("_so_b", "sum"),
    ).reset_index()
    mensal["diferenca_mwh"] = mensal["energia_a_mwh"] - mensal["energia_b_mwh"]
    for coluna in ("horas_comuns", "horas_divergentes", "horas_so_a", "horas_so_b"):
        mensal[coluna] = mensal[coluna].astype(int)
    return resumo, mensal.reindex(columns=COLUNAS_MENSAL), periodos_continuos(divergentes, "diferenca_mw")


def _resultado(id: str, bases: Tuple[str, str], a: pd.DataFrame, b: pd.DataFrame, motivo_sem_base: str,
               deslocamento: bool = False) -> ResultadoConferencia:
    resumo, mensal, divergencias = conferir_series(a, b, deslocamento=deslocamento)
    if not resumo["horas_comuns"]:
        return nao_aplicavel(id, bases, "horas", motivo_sem_base, tolerancia=TOLERANCIA_COINCIDENCIA_MW,
                             tabelas={"resumo": resumo})
    comuns = a.dropna().merge(b.dropna(), on="din_instante")["din_instante"]
    return ResultadoConferencia(
        id=id, bases=bases, unidade="horas", periodo=(comuns.min(), comuns.max()),
        comparados=resumo["horas_comuns"], coincidentes=resumo["coincidentes"], divergentes=resumo["divergentes"],
        tolerancia=TOLERANCIA_COINCIDENCIA_MW, tabelas={"resumo": resumo, "mensal": mensal, "divergencias": divergencias},
    )


def conferencia_programacao_despacho(programacao: Any, despacho: Any) -> ResultadoConferencia:
    """G3: Programação diária × geração programada do despacho (decisão R13)."""
    if programacao is None or not len(programacao.horaria) or despacho is None or not len(despacho.horario):
        return nao_aplicavel("programacao_despacho", BASES_G3, "horas",
                             "Programação diária ou despacho sem horas no período", tolerancia=TOLERANCIA_COINCIDENCIA_MW)
    a = programacao.horaria[["din_instante", "geracao_programada_mw"]].rename(columns={"geracao_programada_mw": "valor_a"})
    b = despacho.horario[["din_instante", "val_proggeracao"]].rename(columns={"val_proggeracao": "valor_b"})
    return _resultado("programacao_despacho", BASES_G3, a, b,
                      "nenhuma hora com a Programação diária e o programado do despacho")


def conferencia_verificada_despacho(base: Optional[pd.DataFrame], despacho: Any) -> ResultadoConferencia:
    """G4: geração verificada do despacho × Geração por usina, no nível da usina (decisão R13)."""
    if base is None or base.empty or despacho is None or not len(despacho.horario):
        return nao_aplicavel("verificada_despacho", BASES_G4, "horas", "Geração por usina ou despacho sem horas no "
                                                                        "período", tolerancia=TOLERANCIA_COINCIDENCIA_MW)
    a = despacho.horario[["din_instante", "val_verifgeracao"]].rename(columns={"val_verifgeracao": "valor_a"})
    usina = base[base["nivel"] == "usina"]
    b = usina[["din_instante", "geracao_mw"]].rename(columns={"geracao_mw": "valor_b"})
    r = _resultado("verificada_despacho", BASES_G4, a, b,
                   "nenhuma hora com o verificado do despacho e a Geração por usina", deslocamento=True)
    resumo = r.tabelas.get("resumo", {})
    deslocadas = [v for v in (resumo.get("pct_coincidentes_deslocada") or {}).values() if v is not None]
    if r.aplicavel and deslocadas and max(deslocadas) > resumo["pct_coincidentes"]:
        logger.warning("G4: a coincidência do despacho com a Geração por usina melhora com uma hora de deslocamento "
                       "(%.1f%% contra %.1f%%); conferir a convenção de hora declarada e corrigi-la, sem ajuste "
                       "automático.", max(deslocadas), resumo["pct_coincidentes"])
    return r
