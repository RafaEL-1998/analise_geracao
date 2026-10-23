"""Conferências entre fontes: G3 e G4 das térmicas (FR-020 e FR-021; decisão D13) e G1, G2 e G5 das eólicas e
solares (FR-023 a FR-025).

- **G3** (``programacao_despacho``): a Programação diária (média horária dos patamares) × a geração programada do
  despacho (``val_proggeracao``), hora a hora, só com a programação no nível da usina.
- **G4** (``verificada_despacho``): a geração verificada do despacho (``val_verifgeracao``) × a Geração por usina, hora a
  hora, no nível da usina. A G4 também mede a coincidência com uma hora de deslocamento: se ela melhorar, a convenção
  de hora declarada está errada e vira correção, nunca ajuste automático (spec do Tratamento de dados, FR-037).

- **G1** (``geracao_fontes``): a geração da usina entre as fontes que a trazem (Geração por usina, Fator de capacidade e
  as duas restrições, estas em hora cheia), sempre duas a duas e no mesmo nível; par de níveis diferentes não é
  comparado.
- **G2** (``soma_conjunto``): a soma das usinas do conjunto (restrição com detalhe, em hora cheia) × a Geração por
  usina do conjunto, só nas horas com todas as usinas da composição vigente.
- **G5** (``programacao_renovaveis``): a Programação diária × a geração programada do Fator de capacidade, no mesmo
  nível (a aplicabilidade confere o nível).

Todas usam a tolerância de hoje (0,01 MW) e só registram, sem meta (decisão D13).
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from src.comum.logger import setup_logger
from src.comum.periodos import periodos_continuos
from src.comum.regras import TOLERANCIA_COINCIDENCIA_MW
from src.conferencia.resultado import ResultadoConferencia, diferenca_absoluta, nao_aplicavel

logger = setup_logger("conferencia")

BASES_G3 = ("Programação diária (média horária dos patamares)",
            "Geração térmica por motivo de despacho (val_proggeracao)")
BASES_G4 = ("Geração térmica por motivo de despacho (val_verifgeracao)", "Geração por usina (val_geracao)")
BASES_G1 = ("Geração da usina em cada fonte (Geração por usina, Fator de capacidade e restrições)",
            "a mesma geração em outra fonte, no mesmo nível")
BASES_G2 = ("Soma das usinas do conjunto (restrição com detalhe, média horária)", "Geração por usina do conjunto")
BASES_G5 = ("Programação diária (média horária dos patamares)", "Fator de capacidade (val_geracaoprogramada)")
FONTES_G1: Dict[str, str] = {"geracao": "Geração por usina", "fator_capacidade": "Fator de capacidade",
                             "restricao_detalhe": "Restrição com detalhe", "restricao_razao": "Restrição com a razão"}
COLUNAS_MENSAL = ["mes", "energia_a_mwh", "energia_b_mwh", "diferenca_mwh", "horas_comuns", "horas_divergentes",
                  "horas_so_a", "horas_so_b"]
COLUNAS_PAR = ["fonte_a", "fonte_b", "nivel"]


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
    comuns = _periodo_comum(a, b)
    return ResultadoConferencia(
        id=id, bases=bases, unidade="horas", periodo=(comuns.min(), comuns.max()),
        comparados=resumo["horas_comuns"], coincidentes=resumo["coincidentes"], divergentes=resumo["divergentes"],
        tolerancia=TOLERANCIA_COINCIDENCIA_MW, tabelas={"resumo": resumo, "mensal": mensal, "divergencias": divergencias},
    )


def _periodo_comum(a: pd.DataFrame, b: pd.DataFrame) -> pd.Series:
    return a.dropna().merge(b.dropna(), on="din_instante")["din_instante"]


def conferencia_programacao_despacho(programacao: Any, despacho: Any) -> ResultadoConferencia:
    """G3: Programação diária × geração programada do despacho (decisão D13)."""
    if programacao is None or not len(programacao.horaria) or despacho is None or not len(despacho.horario):
        return nao_aplicavel("programacao_despacho", BASES_G3, "horas",
                             "Programação diária ou despacho sem horas no período", tolerancia=TOLERANCIA_COINCIDENCIA_MW)
    a = programacao.horaria[["din_instante", "geracao_programada_mw"]].rename(columns={"geracao_programada_mw": "valor_a"})
    b = despacho.horario[["din_instante", "val_proggeracao"]].rename(columns={"val_proggeracao": "valor_b"})
    return _resultado("programacao_despacho", BASES_G3, a, b,
                      "nenhuma hora com a Programação diária e o programado do despacho")


def conferencia_verificada_despacho(base: Optional[pd.DataFrame], despacho: Any) -> ResultadoConferencia:
    """G4: geração verificada do despacho × Geração por usina, no nível da usina (decisão D13)."""
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


# ---------------------------------------------------------------------------
# Eólicas e solares
# ---------------------------------------------------------------------------


def conferencia_geracao_fontes(fontes: Dict[str, Optional[pd.DataFrame]]) -> ResultadoConferencia:
    """G1: ``fontes`` traz, por chave de ``FONTES_G1``, a geração em hora cheia (``din_instante``, ``valor``,
    ``nivel``). Cada par de fontes é comparado em cada nível que as duas têm."""
    chaves = [k for k in FONTES_G1 if fontes.get(k) is not None and len(fontes[k])]
    pares: List[Dict[str, Any]] = []
    mensais, divergencias, comuns = [], [], []
    for i, ka in enumerate(chaves):
        for kb in chaves[i + 1:]:
            for nivel in ("usina", "conjunto"):
                a = fontes[ka][fontes[ka]["nivel"] == nivel].rename(columns={"valor": "valor_a"})
                b = fontes[kb][fontes[kb]["nivel"] == nivel].rename(columns={"valor": "valor_b"})
                if a.empty or b.empty:
                    continue
                par = {"fonte_a": FONTES_G1[ka], "fonte_b": FONTES_G1[kb], "nivel": nivel}
                resumo, mensal, div = conferir_series(a, b)
                pares.append({**par, **{k: v for k, v in resumo.items() if k != "tolerancia_mw"}})
                mensais.append(mensal.assign(**par))
                divergencias.append(div.assign(**par))
                comuns.append(_periodo_comum(a[["din_instante", "valor_a"]], b[["din_instante", "valor_b"]]))
    tabela = pd.DataFrame(pares)
    comparados = int(tabela["horas_comuns"].sum()) if len(tabela) else 0
    if not comparados:
        return nao_aplicavel("geracao_fontes", BASES_G1, "horas",
                             "nenhuma hora com duas fontes da geração no mesmo nível",
                             tolerancia=TOLERANCIA_COINCIDENCIA_MW, tabelas={"pares": tabela})
    instantes = pd.concat(comuns)
    mensal = pd.concat(mensais, ignore_index=True)
    return ResultadoConferencia(
        id="geracao_fontes", bases=BASES_G1, unidade="horas", periodo=(instantes.min(), instantes.max()),
        comparados=comparados, coincidentes=int(tabela["coincidentes"].sum()),
        divergentes=int(tabela["divergentes"].sum()), tolerancia=TOLERANCIA_COINCIDENCIA_MW,
        tabelas={"pares": tabela, "mensal": mensal[COLUNAS_PAR + COLUNAS_MENSAL],
                 "divergencias": pd.concat(divergencias, ignore_index=True)},
    )


def _vigente(membro: Any, instantes: pd.Series) -> pd.Series:
    dias = instantes.dt.normalize()
    vigente = dias >= pd.Timestamp(membro.inicio)
    if membro.fim:
        vigente &= dias <= pd.Timestamp(membro.fim)
    return vigente


def soma_do_conjunto(propria: Optional[pd.DataFrame], id_proprio: str, membros_horaria: Optional[pd.DataFrame],
                     membros: Iterable[Any]) -> Tuple[pd.DataFrame, int]:
    """Soma horária das usinas do conjunto (a própria e os membros do perfil), só nas horas com todas as usinas da
    composição vigente; devolve também as horas com alguma delas sem valor (contadas, fora da soma)."""
    partes = []
    if propria is not None and len(propria):
        partes.append(propria[["din_instante", "val_geracaoverificada"]].assign(id_ons=id_proprio))
    if membros_horaria is not None and len(membros_horaria):
        partes.append(membros_horaria[["din_instante", "id_ons", "val_geracaoverificada"]])
    if not partes:
        return pd.DataFrame(columns=["din_instante", "valor_a", "usinas"]), 0
    largas = pd.concat(partes, ignore_index=True).pivot_table(index="din_instante", columns="id_ons",
                                                             values="val_geracaoverificada", aggfunc="first")
    instantes = largas.index.to_series()
    completa = pd.Series(True, index=largas.index)
    usinas = pd.Series(0, index=largas.index)
    composicao = {m.id_ons: m for m in membros}
    for id_ons in dict.fromkeys([id_proprio, *composicao]):
        vigente = _vigente(composicao[id_ons], instantes) if id_ons in composicao else \
            pd.Series(True, index=largas.index)
        com_valor = largas[id_ons].notna() if id_ons in largas.columns else pd.Series(False, index=largas.index)
        completa &= ~vigente | com_valor
        usinas += vigente.astype(int)
    soma = largas.fillna(0.0).sum(axis=1)
    tabela = pd.DataFrame({"din_instante": largas.index, "valor_a": soma.values, "usinas": usinas.values})
    return tabela[completa.values].reset_index(drop=True), int((~completa).sum())


def conferencia_soma_conjunto(soma: pd.DataFrame, horas_incompletas: int,
                              conjunto: Optional[pd.DataFrame]) -> ResultadoConferencia:
    """G2: a soma das usinas do conjunto × a Geração por usina do conjunto (``din_instante``, ``valor_b``)."""
    if soma is None or soma.empty or conjunto is None or conjunto.empty:
        return nao_aplicavel("soma_conjunto", BASES_G2, "horas",
                             "nenhuma hora com todas as usinas do conjunto e a Geração por usina do conjunto",
                             tolerancia=TOLERANCIA_COINCIDENCIA_MW,
                             tabelas={"resumo": {"horas_incompletas": horas_incompletas}})
    r = _resultado("soma_conjunto", BASES_G2, soma[["din_instante", "valor_a"]], conjunto[["din_instante", "valor_b"]],
                   "nenhuma hora com a soma das usinas e a Geração por usina do conjunto")
    r.tabelas.setdefault("resumo", {})["horas_incompletas"] = horas_incompletas
    return r


def conferencia_programacao_renovaveis(programacao: Any, fator_capacidade: Optional[pd.DataFrame]
                                       ) -> ResultadoConferencia:
    """G5: Programação diária × geração programada do Fator de capacidade (decisão D13)."""
    if programacao is None or not len(programacao.horaria) or fator_capacidade is None or not len(fator_capacidade):
        return nao_aplicavel("programacao_renovaveis", BASES_G5, "horas",
                             "Programação diária ou Fator de capacidade sem horas no período",
                             tolerancia=TOLERANCIA_COINCIDENCIA_MW)
    a = programacao.horaria[["din_instante", "geracao_programada_mw"]].rename(
        columns={"geracao_programada_mw": "valor_a"})
    b = fator_capacidade[["din_instante", "val_geracaoprogramada"]].rename(
        columns={"val_geracaoprogramada": "valor_b"})
    return _resultado("programacao_renovaveis", BASES_G5, a, b,
                      "nenhuma hora com a Programação diária e o programado do Fator de capacidade")
