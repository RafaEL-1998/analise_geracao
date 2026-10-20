"""Seções de térmica das Análises (spec 006, fase B; decisão R18; rascunho 004, FR-056).

A partir do despacho tratado (soma das unidades de planejamento por hora e o detalhe por unidade), da base horária
comum (disponibilidade da usina) e do CVU e do CMO semanais, monta o campo ``termica`` de ``ResultadosAnalise``:

- **geração por motivo**: energia verificada e programada de cada motivo publicado, por mês e por ano, com a parcela
  na geração total publicada (os motivos do ONS podem se sobrepor: a soma das parcelas não é necessariamente 100 %);
- **inflexibilidade**: a programada e a verificada, por mês;
- **atendimento ao despacho**: nas horas com geração programada, o desvio verificada − programada; horas e energia
  abaixo e acima além do limiar; os maiores desvios; e as horas com geração acima da programada sem programação;
- **disponível sem despacho**: horas com a disponibilidade operacional acima do limiar, sem programação e sem geração,
  com a potência disponível média;
- **CVU × CMO**: por semana operativa, o CVU de cada unidade e o CMO médio semanal do subsistema, com a geração da
  unidade na semana, sem julgar o despacho.

Nenhuma divisão por zero: parcela de total nulo fica ausente. Hora sem valor numa das bases fica fora do cruzamento.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.comum.formatacao import fmt_data, fmt_int, fmt_lista, fmt_num, fmt_pct, plural
from src.comum.regras import (
    LIMIAR_DESVIO_DESPACHO_MW,
    LIMIAR_GERACAO_PARADA_MW,
    LIMIAR_INDISPONIBILIDADE_TOTAL_MW,
    NUMERO_EVENTOS_RELATORIO,
)
from src.tratamento.termica import SINAL_CVU_AUSENTE, SINAL_CVU_NEGATIVO, SINAL_CVU_ZERO

# Motivos do despacho (rótulo, coluna programada, coluna verificada): os que compõem a geração total publicada e, à
# parte, os que detalham ou se sobrepõem a outros (a inflexibilidade pura e a embutida no mérito, a ordem de demérito e o
# constrained-off), mostrados só nas tabelas
MOTIVOS: Tuple[Tuple[str, str, Optional[str]], ...] = (
    ("Ordem de mérito", "val_progordemmerito", "val_verifordemmerito"),
    ("Inflexibilidade", "val_proginflexibilidade", "val_verifinflexibilidade"),
    ("Razão elétrica", "val_prograzaoeletrica", "val_verifrazaoeletrica"),
    ("Garantia energética", "val_proggarantiaenergetica", "val_verifgarantiaenergetica"),
    ("Geração fora da ordem de mérito (GFOM)", "val_proggfom", "val_verifgfom"),
    ("Reposição de perdas", "val_progreposicaoperdas", "val_verifreposicaoperdas"),
    ("Exportação", "val_progexportacao", "val_verifexportacao"),
    ("Reserva de potência", "val_progreservapotencia", "val_verifreservapotencia"),
    ("Geração de substituição (GSUB)", "val_proggsub", "val_verifgsub"),
    ("Unit commitment", "val_progunitcommitment", "val_verifunitcommitment"),
)
DETALHES: Tuple[Tuple[str, str, Optional[str]], ...] = (
    ("Inflexibilidade pura", "val_proginflexpura", "val_verifinflexpura"),
    ("Inflexibilidade embutida no mérito", "val_proginflexembutmerito", "val_verifinflexembutmerito"),
    ("Ordem de demérito acima da inflexibilidade", "val_progordemdemeritoacimadainflex",
     "val_verifordemdemeritoacimadainflex"),
    ("Ordem de demérito de referência", "val_progordemdemeritoref", None),
    ("Inflexibilidade do DESSEM", "val_proginflexibilidadedessem", None),
    ("Constrained-off", "val_progconstrainedoff", "val_verifconstrainedoff"),
)
PROGRAMADO, VERIFICADO = "val_proggeracao", "val_verifgeracao"
COLUNAS_MOTIVOS = ["periodo", "motivo", "grupo", "programado_mwh", "verificado_mwh", "parcela_programado_pct",
                   "parcela_verificado_pct"]


def _pct(parte: float, total: float) -> float:
    return float(parte) / float(total) * 100.0 if total and not math.isnan(float(total)) else math.nan


def _soma(serie: pd.Series) -> float:
    return float(pd.to_numeric(serie, errors="coerce").sum(min_count=1)) if len(serie) else math.nan


# ---------------------------------------------------------------------------
# Geração por motivo e inflexibilidade
# ---------------------------------------------------------------------------


def geracao_por_motivo(horario: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Energia programada e verificada de cada motivo por período (``freq`` "Y" ou "M"), com a parcela na geração total
    publicada; só os motivos com energia no período da usina."""
    h = horario.assign(periodo=horario["din_instante"].dt.to_period(freq).astype(str))
    linhas: List[Dict[str, Any]] = []
    for periodo, g in h.groupby("periodo", sort=True):
        total_p, total_v = _soma(g[PROGRAMADO]), _soma(g[VERIFICADO])
        linhas.append({"periodo": periodo, "motivo": "Geração total", "grupo": "total", "programado_mwh": total_p,
                       "verificado_mwh": total_v, "parcela_programado_pct": math.nan,
                       "parcela_verificado_pct": math.nan})
        for grupo, motivos in (("motivo", MOTIVOS), ("detalhe", DETALHES)):
            for rotulo, prog, verif in motivos:
                p = _soma(g[prog]) if prog in g.columns else math.nan
                v = _soma(g[verif]) if verif and verif in g.columns else math.nan
                linhas.append({"periodo": periodo, "motivo": rotulo, "grupo": grupo, "programado_mwh": p,
                               "verificado_mwh": v, "parcela_programado_pct": _pct(p, total_p),
                               "parcela_verificado_pct": _pct(v, total_v)})
    t = pd.DataFrame(linhas, columns=COLUNAS_MOTIVOS)
    if t.empty:
        return t
    energia = t[["programado_mwh", "verificado_mwh"]].abs().fillna(0.0)
    com_energia = set(t.loc[(energia.sum(axis=1) > 0) & (t["grupo"] != "total"), "motivo"])
    return t[(t["grupo"] == "total") | t["motivo"].isin(com_energia)].reset_index(drop=True)


def inflexibilidade_mensal(horario: pd.DataFrame) -> pd.DataFrame:
    """Inflexibilidade programada e verificada por mês, com a parte programada não verificada (base da C14)."""
    h = horario.dropna(subset=["val_proginflexibilidade", "val_verifinflexibilidade"], how="all")
    if h.empty:
        return pd.DataFrame(columns=["mes", "programada_mwh", "verificada_mwh", "nao_verificada_mwh"])
    falta = (h["val_proginflexibilidade"] - h["val_verifinflexibilidade"]).clip(lower=0)
    mes = h["din_instante"].dt.to_period("M").dt.to_timestamp()
    t = pd.DataFrame({"mes": mes, "programada_mwh": h["val_proginflexibilidade"],
                      "verificada_mwh": h["val_verifinflexibilidade"], "nao_verificada_mwh": falta})
    return t.groupby("mes", as_index=False).sum(min_count=1)


# ---------------------------------------------------------------------------
# Atendimento ao despacho
# ---------------------------------------------------------------------------


def atendimento_ao_despacho(horario: pd.DataFrame) -> Dict[str, Any]:
    """Desvio verificada − programada nas horas com geração programada (acima de ``LIMIAR_GERACAO_PARADA_MW``); horas
    e energia abaixo e acima além de ``LIMIAR_DESVIO_DESPACHO_MW``; e as horas sem programação com geração acima dela."""
    h = horario.dropna(subset=[PROGRAMADO, VERIFICADO]).copy()
    h["desvio_mw"] = h[VERIFICADO] - h[PROGRAMADO]
    com_programa = h[h[PROGRAMADO] > LIMIAR_GERACAO_PARADA_MW]
    abaixo = com_programa[com_programa["desvio_mw"] < -LIMIAR_DESVIO_DESPACHO_MW]
    acima = com_programa[com_programa["desvio_mw"] > LIMIAR_DESVIO_DESPACHO_MW]
    sem_programa = h[(h[PROGRAMADO] <= LIMIAR_GERACAO_PARADA_MW) & (h["desvio_mw"] > LIMIAR_DESVIO_DESPACHO_MW)]

    def por_ano(t: pd.DataFrame, nome: str, energia: pd.Series) -> pd.DataFrame:
        ano = t["din_instante"].dt.year
        return pd.DataFrame({"ano": ano, f"horas_{nome}": 1, f"energia_{nome}_mwh": energia}).groupby("ano").sum()

    anos = sorted(set(h["din_instante"].dt.year))
    anual = pd.DataFrame(index=pd.Index(anos, name="ano"))
    anual["horas_programadas"] = com_programa.groupby(com_programa["din_instante"].dt.year).size()
    for t, nome, energia in ((abaixo, "abaixo", -abaixo["desvio_mw"]), (acima, "acima", acima["desvio_mw"]),
                             (sem_programa, "sem_programacao", sem_programa["desvio_mw"])):
        anual = anual.join(por_ano(t, nome, energia))
    anual = anual.fillna(0).reset_index()
    for coluna in [c for c in anual.columns if c.startswith("horas")]:
        anual[coluna] = anual[coluna].astype(int)
    mes = lambda t: t["din_instante"].dt.to_period("M").dt.to_timestamp()  # noqa: E731
    mensal = pd.DataFrame({"energia_abaixo_mwh": (-abaixo["desvio_mw"]).groupby(mes(abaixo)).sum(),
                           "energia_acima_mwh": acima["desvio_mw"].groupby(mes(acima)).sum()})
    mensal = mensal.reindex(sorted(set(mes(h)))).fillna(0.0).rename_axis("mes").reset_index()
    maiores = com_programa.assign(_absoluto=com_programa["desvio_mw"].abs())  # empates em ordem cronológica
    maiores = maiores[maiores["_absoluto"] > LIMIAR_DESVIO_DESPACHO_MW].sort_values(
        ["_absoluto", "din_instante"], ascending=[False, True], kind="stable").head(NUMERO_EVENTOS_RELATORIO)
    return {
        "resumo": {
            "horas_comuns": len(h), "horas_programadas": len(com_programa),
            "horas_abaixo": len(abaixo), "energia_abaixo_mwh": float(-abaixo["desvio_mw"].sum()),
            "horas_acima": len(acima), "energia_acima_mwh": float(acima["desvio_mw"].sum()),
            "horas_sem_programacao": len(sem_programa), "energia_sem_programacao_mwh": float(sem_programa["desvio_mw"].sum()),
            "desvio_medio_mw": float(com_programa["desvio_mw"].mean()) if len(com_programa) else math.nan,
            "limiar_mw": LIMIAR_DESVIO_DESPACHO_MW,
        },
        "anual": anual,
        "mensal": mensal,
        "maiores_desvios": maiores[["din_instante", PROGRAMADO, VERIFICADO, "desvio_mw"]].rename(
            columns={PROGRAMADO: "programado_mw", VERIFICADO: "verificado_mw"}).reset_index(drop=True),
    }


# ---------------------------------------------------------------------------
# Disponível sem despacho
# ---------------------------------------------------------------------------


def horas_disponiveis_sem_despacho(base: pd.DataFrame, horario: pd.DataFrame) -> pd.DataFrame:
    """Horas comuns à disponibilidade da usina e ao despacho, com a marca ``disponivel_sem_despacho``: disponibilidade
    operacional acima de ``LIMIAR_INDISPONIBILIDADE_TOTAL_MW``, programação e geração até ``LIMIAR_GERACAO_PARADA_MW``."""
    disp = base[(base["nivel"] == "usina") & base["disponibilidade_operacional_mw"].notna()][
        ["din_instante", "disponibilidade_operacional_mw"]]
    j = disp.merge(horario[["din_instante", PROGRAMADO, VERIFICADO]].dropna(), on="din_instante", how="inner")
    j["disponivel_sem_despacho"] = ((j["disponibilidade_operacional_mw"] > LIMIAR_INDISPONIBILIDADE_TOTAL_MW)
                                    & (j[PROGRAMADO] <= LIMIAR_GERACAO_PARADA_MW)
                                    & (j[VERIFICADO] <= LIMIAR_GERACAO_PARADA_MW))
    return j


def disponivel_sem_despacho(horas: pd.DataFrame) -> Dict[str, Any]:
    """Horas disponíveis sem despacho e a potência disponível média nelas, no período e por ano."""
    if horas.empty:
        return {}
    sem = horas[horas["disponivel_sem_despacho"]]
    ano = horas["din_instante"].dt.year
    anual = pd.DataFrame({"ano": ano, "horas_comuns": 1, "horas_disponivel_sem_despacho":
                          horas["disponivel_sem_despacho"].astype(int),
                          "_disp": horas["disponibilidade_operacional_mw"].where(horas["disponivel_sem_despacho"])})
    anual = anual.groupby("ano").agg(horas_comuns=("horas_comuns", "sum"),
                                     horas_disponivel_sem_despacho=("horas_disponivel_sem_despacho", "sum"),
                                     potencia_disponivel_media_mw=("_disp", "mean")).reset_index()
    return {
        "resumo": {"horas_comuns": len(horas), "horas": len(sem),
                   "pct_horas": _pct(len(sem), len(horas)),
                   "potencia_disponivel_media_mw": float(sem["disponibilidade_operacional_mw"].mean())
                   if len(sem) else math.nan,
                   "inicio": horas["din_instante"].min(), "fim": horas["din_instante"].max()},
        "anual": anual,
    }


# ---------------------------------------------------------------------------
# CVU × CMO
# ---------------------------------------------------------------------------


def cvu_cmo(cvu: Optional[pd.DataFrame], cmo: Optional[pd.DataFrame], unidades: pd.DataFrame,
            horas: pd.DataFrame) -> Dict[str, Any]:
    """Por semana operativa e unidade: o CVU, o CMO médio semanal do subsistema e a relação entre eles, com a geração
    verificada da unidade na semana; e as horas disponíveis sem despacho nas semanas com algum CVU abaixo do CMO (base
    da C13). Sem julgamento do despacho (US2-3)."""
    if cvu is None or cvu.empty or cmo is None or cmo.empty:
        return {}
    c = cvu[["codigo", "semana_inicio", "semana_fim", "val_cvu", "sinal_cvu"]].copy()
    c["sinal_cvu"] = c["sinal_cvu"].fillna("")
    s = c.merge(cmo[["semana_inicio", "val_cmomediasemanal"]], on="semana_inicio", how="left")
    s = s.rename(columns={"val_cvu": "cvu", "val_cmomediasemanal": "cmo"})
    valido = (s["sinal_cvu"] == "") & s["cvu"].notna() & s["cmo"].notna()
    s["relacao"] = "sem comparação"
    s.loc[valido & (s["cvu"] < s["cmo"]), "relacao"] = "abaixo"
    s.loc[valido & (s["cvu"] > s["cmo"]), "relacao"] = "acima"
    s.loc[valido & (s["cvu"] == s["cmo"]), "relacao"] = "igual"
    u = unidades.dropna(subset=[VERIFICADO]) if len(unidades) else pd.DataFrame(columns=["din_instante", "codigo",
                                                                                        VERIFICADO])
    if len(u):
        semana = u["din_instante"].dt.normalize() - pd.to_timedelta((u["din_instante"].dt.weekday - 5) % 7, unit="D")
        geracao = u.assign(semana_inicio=semana).groupby(["codigo", "semana_inicio"])[VERIFICADO].sum()
        s["geracao_mwh"] = [float(geracao.get((int(cod), sem), 0.0)) for cod, sem in zip(s["codigo"], s["semana_inicio"])]
    else:
        s["geracao_mwh"] = math.nan
    if len(horas):
        semana_h = horas["din_instante"].dt.normalize() - pd.to_timedelta((horas["din_instante"].dt.weekday - 5) % 7,
                                                                           unit="D")
        sem_despacho = horas.assign(semana_inicio=semana_h).groupby("semana_inicio")["disponivel_sem_despacho"].sum()
    else:
        sem_despacho = pd.Series(dtype=int)
    s["horas_disponivel_sem_despacho"] = s["semana_inicio"].map(sem_despacho).fillna(0).astype(int)
    semanas_abaixo = sorted(set(s.loc[s["relacao"] == "abaixo", "semana_inicio"]))
    horas_c13 = int(sem_despacho.reindex(semanas_abaixo).fillna(0).sum()) if semanas_abaixo else 0
    resumo = []
    for codigo, g in s.groupby("codigo", sort=True):
        linha = {"codigo": int(codigo), "semanas": len(g)}
        for relacao in ("abaixo", "acima"):
            r = g[g["relacao"] == relacao]
            linha[f"semanas_{relacao}"] = len(r)
            linha[f"geracao_{relacao}_mwh"] = float(r["geracao_mwh"].sum())
        linha["semanas_igual"] = int((g["relacao"] == "igual").sum())
        linha["semanas_sem_comparacao"] = int((g["relacao"] == "sem comparação").sum())
        linha["semanas_cvu_sinalizado"] = int((g["sinal_cvu"] != "").sum())  # ausente, zero ou negativo
        resumo.append(linha)
    return {
        "semanal": s.sort_values(["semana_inicio", "codigo"]).reset_index(drop=True),
        "resumo": pd.DataFrame(resumo),
        "semanas_cvu_abaixo": len(semanas_abaixo),
        "horas_disponivel_cvu_abaixo": horas_c13,
        "semanas_disponivel_cvu_abaixo": int((sem_despacho.reindex(semanas_abaixo).fillna(0) > 0).sum())
        if semanas_abaixo else 0,
    }


# ---------------------------------------------------------------------------
# Montagem
# ---------------------------------------------------------------------------


def analisar_termica(despacho: Any, base: pd.DataFrame, cvu: Any = None, cmo: Any = None) -> Dict[str, Any]:
    """Campo ``termica`` dos resultados (decisão R18); vazio sem o despacho ou sem horas dele no período."""
    if despacho is None or despacho.horario is None or despacho.horario.empty:
        return {}
    horario = despacho.horario
    horas = horas_disponiveis_sem_despacho(base, horario) if base is not None else pd.DataFrame()
    verificado = _soma(horario[VERIFICADO])
    inflex = inflexibilidade_mensal(horario)
    programada_inflex = _soma(inflex["programada_mwh"]) if len(inflex) else math.nan
    nao_verificada = _soma(inflex["nao_verificada_mwh"]) if len(inflex) else math.nan
    termica: Dict[str, Any] = {
        "periodo": {"inicio": horario["din_instante"].min(), "fim": horario["din_instante"].max(),
                    "horas": len(horario)},
        "codigos": sorted(int(c) for c in despacho.unidades["codigo"].dropna().unique())
        if despacho.unidades is not None and len(despacho.unidades) else [],
        "motivos_anual": geracao_por_motivo(horario, "Y"),
        "motivos_mensal": geracao_por_motivo(horario, "M"),
        "inflexibilidade": inflex,
        "inflexibilidade_resumo": {"programada_mwh": programada_inflex,
                                   "verificada_mwh": _soma(inflex["verificada_mwh"]) if len(inflex) else math.nan,
                                   "nao_verificada_mwh": nao_verificada,
                                   "nao_verificada_pct": _pct(nao_verificada, programada_inflex)},
        "atendimento": atendimento_ao_despacho(horario),
        "disponivel_sem_despacho": disponivel_sem_despacho(horas),
        "horas_com_despacho": int((horario[PROGRAMADO] > LIMIAR_GERACAO_PARADA_MW).sum()),
        "horas_com_despacho_anual": {str(a): int(n) for a, n in (horario[PROGRAMADO] > LIMIAR_GERACAO_PARADA_MW)
                                     .groupby(horario["din_instante"].dt.year).sum().items()},
        "geracao_verificada_mwh": verificado,
        "sem_geracao": not (verificado > LIMIAR_GERACAO_PARADA_MW),
        "cvu_cmo": cvu_cmo(cvu.semanal if cvu is not None else None, cmo.semanal if cmo is not None else None,
                           despacho.unidades if despacho.unidades is not None else pd.DataFrame(), horas),
        "cvu_coletado": cvu is not None,
        "cmo_coletado": cmo is not None,
    }
    if cvu is not None and len(cvu.semanal):
        sinais = cvu.semanal["sinal_cvu"].fillna("")
        termica["cvu_sinalizados"] = {s: int((sinais == s).sum())
                                      for s in (SINAL_CVU_AUSENTE, SINAL_CVU_ZERO, SINAL_CVU_NEGATIVO)}
    return termica


# ---------------------------------------------------------------------------
# Constatações das seções de térmica
# ---------------------------------------------------------------------------


def _codigos_texto(t: Dict[str, Any]) -> str:
    codigos = t.get("codigos") or []
    return (f"{plural(len(codigos), 'unidade de planejamento', 'unidades de planejamento')} "
            f"{fmt_lista([str(c) for c in codigos])}") if codigos else "despacho"


def achados_termica(termica: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Constatações das seções de térmica (fatos, sem parecer nem causa)."""
    if not termica:
        return []
    p = termica["periodo"]
    achados: List[Tuple[str, str]] = []
    d = termica.get("disponivel_sem_despacho") or {}
    if termica["sem_geracao"]:  # US2-5: usina sem geração no período
        texto = (f"A usina não gerou de {fmt_data(p['inicio'])} a {fmt_data(p['fim'])}: geração verificada do despacho "
                 f"até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW nas {fmt_int(p['horas'])} horas.")
        if d:
            r = d["resumo"]
            texto += (f" Ficou disponível e não foi despachada em {fmt_int(r['horas'])} horas, com a potência "
                      f"disponível média de {fmt_num(r['potencia_disponivel_media_mw'], 1)} MW.")
        achados.append(("Despacho por motivo", texto))
    else:
        anual = termica["motivos_anual"]
        motivos = anual[anual["grupo"] == "motivo"].groupby("motivo")["verificado_mwh"].sum()
        texto = (f"Geração verificada do despacho de {fmt_num(termica['geracao_verificada_mwh'], 0)} MWh de "
                 f"{fmt_data(p['inicio'])} a {fmt_data(p['fim'])} ({_codigos_texto(termica)}); geração programada em "
                 f"{fmt_int(termica['horas_com_despacho'])} horas.")
        if len(motivos) and motivos.max() > 0:
            principal = motivos.idxmax()
            texto += (f" Maior motivo verificado: {principal.lower()}, com "
                      f"{fmt_pct(_pct(motivos.max(), termica['geracao_verificada_mwh']))} da geração verificada.")
        achados.append(("Despacho por motivo", texto))
    a = termica["atendimento"]["resumo"]
    if a["horas_programadas"] or a["horas_sem_programacao"]:
        achados.append(("Atendimento ao despacho", (
            f"Nas {fmt_int(a['horas_programadas'])} horas com geração programada, a verificada ficou mais de "
            f"{fmt_num(a['limiar_mw'], 0)} MW abaixo da programada em {fmt_int(a['horas_abaixo'])} horas "
            f"({fmt_num(a['energia_abaixo_mwh'], 0)} MWh) e acima em {fmt_int(a['horas_acima'])} horas "
            f"({fmt_num(a['energia_acima_mwh'], 0)} MWh); sem programação, geração acima de {fmt_num(a['limiar_mw'], 0)} "
            f"MW em {fmt_int(a['horas_sem_programacao'])} horas.")))
    if d and not termica["sem_geracao"]:
        r = d["resumo"]
        achados.append(("Disponível sem despacho", (
            f"Disponível, sem programação e sem geração em {fmt_int(r['horas'])} das {fmt_int(r['horas_comuns'])} horas "
            f"com a disponibilidade e o despacho ({fmt_pct(r['pct_horas'])}), com a potência disponível média de "
            f"{fmt_num(r['potencia_disponivel_media_mw'], 1)} MW.")))
    c = termica.get("cvu_cmo") or {}
    if c:
        partes = [f"unidade {r.codigo}: CVU abaixo do CMO em {fmt_int(r.semanas_abaixo)} e acima em "
                  f"{fmt_int(r.semanas_acima)} das {fmt_int(r.semanas)} semanas"
                  for r in c["resumo"].itertuples()]
        texto = "; ".join(partes)
        achados.append(("CVU e CMO", texto[:1].upper() + texto[1:] + (
            f"; nas semanas com algum CVU abaixo do CMO, {fmt_int(c['horas_disponivel_cvu_abaixo'])} horas disponíveis "
            "sem despacho.")))
    return achados
