"""Seções de eólica e solar das Análises (spec das Análises, FR-058; plano das Análises, D21).

A partir das tabelas do Tratamento (fator de capacidade horário, restrição com detalhe por semi-hora, com a razão de
cada semi-hora) e da base horária comum, monta o campo ``renovavel`` de ``ResultadosAnalise``:

- **fator de capacidade publicado**: Σ geração verificada ÷ Σ capacidade instalada nas horas com as duas, por mês e
  por ano, com o nível (usina ou conjunto); o calculado da série própria fica nos indicadores anuais comuns;
- **energia cortada**: só nas semi-horas com a marca de restrição (decisão D21), por mês e por razão (REL, CNF, ENE);
  as semi-horas sem a marca ficam contadas e fora do total; a diferença bruta (estimada − verificada em todas as
  semi-horas) é mostrada à parte, para comparação; a verificada e a estimada somam as mesmas semi-horas, as com
  estimativa (a estimada 0 com a usina gerando é estimativa ausente, contada à parte, com o corte não calculado nas
  restritas; decisão do usuário de 21/10/2026);
- **recurso × geração**: geração verificada média por faixa de vento ou de irradiância, sem as semi-horas com o
  recurso marcado como inválido pelo ONS, contadas;
- **aderência à programação**: os maiores desvios entre a geração verificada e a programada, no nível da programação.

Nenhuma divisão por zero: parcela de total nulo fica ausente. Os números do conjunto ficam identificados pelo nível.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.analises.comum_tipos import NOME_NIVEL, _ano_parcial, _cobertura_texto
from src.coleta import registro
from src.comum.formatacao import fmt_data, fmt_int, fmt_num, fmt_pct, plural
from src.comum.regras import (
    DURACAO_SEMI_HORA_H,
    FAIXA_IRRADIANCIA_WM2,
    FAIXA_VENTO_MS,
    LIMITE_IRRADIANCIA_PLAUSIVEL_WM2,
    LIMITE_VENTO_PLAUSIVEL_MS,
    NUMERO_EVENTOS_RELATORIO,
)

TITULO_FATOR_CAPACIDADE = "Fator de capacidade"
TITULO_CORTE = "Energia cortada por restrição de operação (constrained-off)"
TITULO_RECURSO = "Recurso × geração"
# Razões da restrição publicadas pelo ONS (código -> descrição); a semi-hora restrita sem código fica "sem razão"
RAZOES: Dict[str, str] = {"REL": "indisponibilidade externa (REL)", "CNF": "confiabilidade elétrica (CNF)",
                          "ENE": "razão energética (ENE)"}
SEM_RAZAO = "sem razão publicada"
COLUNA_RAZAO: Dict[str, str] = {"REL": "cortada_rel_mwh", "CNF": "cortada_cnf_mwh", "ENE": "cortada_ene_mwh",
                                SEM_RAZAO: "cortada_sem_razao_mwh"}
# Grandeza, unidade, largura das faixas e limite físico do recurso por tipo
RECURSO: Dict[str, Tuple[str, str, float, float]] = {
    "EOL": ("vento", "m/s", FAIXA_VENTO_MS, LIMITE_VENTO_PLAUSIVEL_MS),
    "UFV": ("irradiância", "W/m²", FAIXA_IRRADIANCIA_WM2, LIMITE_IRRADIANCIA_PLAUSIVEL_WM2)}
COLUNAS_FC = ["periodo", "nivel", "horas", "geracao_verificada_mwh", "capacidade_media_mw", "fator_capacidade_pct",
              "horas_fc_fora_0_1", "horas_acima_capacidade"]
COLUNAS_CORTE = ["periodo", "semi_horas", "semi_horas_restritas", "horas_restritas", "semi_horas_sem_marca",
                 "semi_horas_sem_estimativa", "semi_horas_restritas_sem_estimativa", "energia_verificada_mwh",
                 "energia_estimada_mwh", "energia_estimada_com_marca_mwh", "energia_cortada_mwh", "pct_estimada",
                 "diferenca_bruta_mwh"]
COLUNAS_FAIXAS = ["faixa_inicio", "faixa_fim", "semi_horas", "geracao_media_mw", "estimada_media_mw"]
COLUNAS_DESVIOS = ["din_instante", "geracao_programada_mw", "geracao_mw", "desvio_mw"]


def _pct(parte: float, total: float) -> float:
    return float(parte) / float(total) * 100.0 if total and not math.isnan(float(total)) else math.nan


def _periodo(instantes: pd.Series, freq: str) -> pd.Series:
    return instantes.dt.year if freq == "Y" else instantes.dt.to_period("M").dt.to_timestamp()


# ---------------------------------------------------------------------------
# Fator de capacidade publicado
# ---------------------------------------------------------------------------


def fator_capacidade_publicado(fc: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Fator de capacidade publicado por mês (``freq="M"``) ou por ano (``"Y"``) e nível, nas horas com a geração e a
    capacidade; no ano, ``ano_parcial`` marca o ano incompleto."""
    t = fc.dropna(subset=["val_geracaoverificada", "val_capacidadeinstalada"])
    if t.empty:
        return pd.DataFrame(columns=COLUNAS_FC + (["ano_parcial"] if freq == "Y" else []))
    linhas = []
    for (periodo, nivel), g in t.groupby([_periodo(t["din_instante"], freq), "nivel"], sort=True):
        capacidade = float(g["val_capacidadeinstalada"].sum())
        linha = {"periodo": periodo, "nivel": nivel, "horas": len(g),
                 "geracao_verificada_mwh": float(g["val_geracaoverificada"].sum()),
                 "capacidade_media_mw": float(g["val_capacidadeinstalada"].mean()),
                 "fator_capacidade_pct": _pct(float(g["val_geracaoverificada"].sum()), capacidade),
                 "horas_fc_fora_0_1": int(g["sinal_fc_fora_0_1"].astype(bool).sum()),
                 "horas_acima_capacidade": int(g["sinal_acima_capacidade"].astype(bool).sum())}
        if freq == "Y":
            linha["ano_parcial"] = _ano_parcial(g, int(periodo))
        linhas.append(linha)
    return pd.DataFrame(linhas)


def _secao_fator_capacidade(fc: Optional[pd.DataFrame]) -> Dict[str, Any]:
    if fc is None or fc.empty:
        return {}
    anual = fator_capacidade_publicado(fc, "Y")
    if anual.empty:
        return {}
    t = fc.dropna(subset=["val_geracaoverificada", "val_capacidadeinstalada"])
    return {
        "nivel": str(fc["nivel"].iloc[0]),
        "mensal": fator_capacidade_publicado(fc, "M"),
        "anual": anual,
        "resumo": {"inicio": t["din_instante"].min(), "fim": t["din_instante"].max(), "horas": len(t),
                   "fator_capacidade_pct": _pct(float(t["val_geracaoverificada"].sum()),
                                                float(t["val_capacidadeinstalada"].sum())),
                   "horas_fc_fora_0_1": int(anual["horas_fc_fora_0_1"].sum()),
                   "horas_acima_capacidade": int(anual["horas_acima_capacidade"].sum())},
    }


# ---------------------------------------------------------------------------
# Energia cortada por restrição de operação
# ---------------------------------------------------------------------------


def _estimada_ausente(semi: pd.DataFrame) -> pd.Series:
    if "sinal_estimada_ausente" not in semi.columns:
        return pd.Series(False, index=semi.index)
    return semi["sinal_estimada_ausente"].astype(bool)


def _com_energias(semi: pd.DataFrame) -> pd.DataFrame:
    marcada = ~semi["sem_marca_restricao"].astype(bool)
    restrita = semi["restrita"].astype(bool)
    com_estimativa = ~_estimada_ausente(semi) & semi["val_geracaoestimada"].notna()
    razao = semi["cod_razaorestricao"].fillna("").astype(str).str.upper()
    return semi.assign(
        _verificada=(semi["val_geracaoverificada"] * DURACAO_SEMI_HORA_H).where(com_estimativa),
        _estimada=(semi["val_geracaoestimada"] * DURACAO_SEMI_HORA_H).where(com_estimativa),
        _estimada_marca=(semi["val_geracaoestimada"] * DURACAO_SEMI_HORA_H).where(marcada & com_estimativa),
        _bruta=((semi["val_geracaoestimada"] - semi["val_geracaoverificada"]).clip(lower=0)
                * DURACAO_SEMI_HORA_H).where(com_estimativa),
        _restrita=restrita.astype(int), _sem_marca=(~marcada).astype(int),
        _sem_estimativa=(~com_estimativa).astype(int), _restrita_sem_estimativa=(restrita & ~com_estimativa).astype(int),
        _razao=razao.where(razao.isin(list(RAZOES)), SEM_RAZAO).where(restrita, ""),
    )


def _resumo_corte(g: pd.DataFrame) -> Dict[str, Any]:
    cortada = float(g["energia_cortada_mwh"].sum())
    estimada_marca = float(g["_estimada_marca"].sum())
    return {"semi_horas": len(g), "semi_horas_restritas": int(g["_restrita"].sum()),
            "horas_restritas": float(g["_restrita"].sum()) * DURACAO_SEMI_HORA_H,
            "semi_horas_sem_marca": int(g["_sem_marca"].sum()),
            "semi_horas_sem_estimativa": int(g["_sem_estimativa"].sum()),
            "semi_horas_restritas_sem_estimativa": int(g["_restrita_sem_estimativa"].sum()),
            "energia_verificada_mwh": float(g["_verificada"].sum()), "energia_estimada_mwh": float(g["_estimada"].sum()),
            "energia_estimada_com_marca_mwh": estimada_marca, "energia_cortada_mwh": cortada,
            "pct_estimada": _pct(cortada, estimada_marca), "diferenca_bruta_mwh": float(g["_bruta"].sum())}


def energia_cortada(semi: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Energias por mês (``"M"``) ou ano (``"Y"``); no mês, também a energia cortada de cada razão."""
    t = _com_energias(semi)
    linhas = []
    for periodo, g in t.groupby(_periodo(pd.to_datetime(t["din_instante"]), freq), sort=True):
        linha = {"periodo": periodo, **_resumo_corte(g)}
        if freq == "M":
            for razao, coluna in COLUNA_RAZAO.items():
                linha[coluna] = float(g.loc[g["_razao"] == razao, "energia_cortada_mwh"].sum())
        linhas.append(linha)
    return pd.DataFrame(linhas)


def corte_por_razao(semi: pd.DataFrame) -> pd.DataFrame:
    """Energia cortada e semi-horas restritas por razão, com a parcela na energia cortada total."""
    t = _com_energias(semi)
    t = t[t["_restrita"] == 1]
    total = float(t["energia_cortada_mwh"].sum())
    linhas = [{"razao": razao, "descricao": RAZOES.get(razao, razao), "semi_horas": int((t["_razao"] == razao).sum()),
               "energia_cortada_mwh": float(t.loc[t["_razao"] == razao, "energia_cortada_mwh"].sum())}
              for razao in COLUNA_RAZAO]
    tabela = pd.DataFrame(linhas)
    tabela["pct_cortada"] = [_pct(e, total) for e in tabela["energia_cortada_mwh"]]
    return tabela[tabela["semi_horas"] > 0].reset_index(drop=True)


def _secao_restricao(semi: Optional[pd.DataFrame]) -> Dict[str, Any]:
    if semi is None or semi.empty:
        return {}
    niveis = [n for n in semi["nivel_razao"].fillna("").astype(str).unique() if n]
    resumo = _resumo_corte(_com_energias(semi))
    resumo.update(inicio=semi["din_instante"].min(), fim=semi["din_instante"].max())
    return {"resumo": resumo, "mensal": energia_cortada(semi, "M"), "anual": energia_cortada(semi, "Y"),
            "por_razao": corte_por_razao(semi), "nivel_razao": niveis[0] if niveis else ""}


# ---------------------------------------------------------------------------
# Recurso × geração
# ---------------------------------------------------------------------------


def recurso_por_faixa(semi: pd.DataFrame, largura: float, limite: float = math.inf) -> pd.DataFrame:
    """Geração verificada e estimada médias por faixa do recurso, só nas semi-horas com o recurso válido e até o limite
    físico; o recurso negativo (ruído de medição) entra na primeira faixa."""
    validas = semi[~semi["sinal_recurso_invalido"].astype(bool) & semi["val_recurso"].notna()
                   & (semi["val_recurso"] <= limite) & semi["val_geracaoverificada"].notna()]
    if validas.empty:
        return pd.DataFrame(columns=COLUNAS_FAIXAS)
    # a estimada ausente (estimada 0 com a usina gerando) fica fora da média da estimada
    validas = validas.assign(val_geracaoestimada=validas["val_geracaoestimada"].where(~_estimada_ausente(validas)))
    inicio = (validas["val_recurso"].clip(lower=0) // largura) * largura
    g = validas.groupby(inicio)
    tabela = pd.DataFrame({"semi_horas": g.size(), "geracao_media_mw": g["val_geracaoverificada"].mean(),
                           "estimada_media_mw": g["val_geracaoestimada"].mean()}).rename_axis("faixa_inicio")
    tabela = tabela.reset_index()
    tabela["faixa_fim"] = tabela["faixa_inicio"] + largura
    return tabela[COLUNAS_FAIXAS]


def _secao_recurso(semi: Optional[pd.DataFrame], tipo: str) -> Dict[str, Any]:
    if semi is None or semi.empty or tipo not in RECURSO:
        return {}
    grandeza, unidade, largura, limite = RECURSO[tipo]
    faixas = recurso_por_faixa(semi, largura, limite)
    invalido = semi["sinal_recurso_invalido"].astype(bool)
    invalidas = int(invalido.sum())
    implausiveis = int((~invalido & (semi["val_recurso"] > limite)).sum())  # falha de medição não marcada pelo ONS
    sem_recurso = int((~invalido & semi["val_recurso"].isna()).sum())
    if faixas.empty and not invalidas:
        return {}
    return {"grandeza": grandeza, "unidade": unidade, "largura": largura, "limite": limite, "faixas": faixas,
            "resumo": {"semi_horas": len(semi), "semi_horas_validas": int(faixas["semi_horas"].sum()),
                       "semi_horas_invalidas": invalidas, "pct_invalidas": _pct(invalidas, len(semi)),
                       "semi_horas_implausiveis": implausiveis, "semi_horas_sem_recurso": sem_recurso}}


# ---------------------------------------------------------------------------
# Aderência à programação
# ---------------------------------------------------------------------------


def maiores_desvios_programacao(base: pd.DataFrame, nivel: str, n: int = NUMERO_EVENTOS_RELATORIO) -> pd.DataFrame:
    """As ``n`` horas com o maior desvio absoluto entre a geração verificada e a programada, no nível da programação
    (empates em ordem cronológica)."""
    j = base[(base["nivel"] == nivel) & base["geracao_programada_mw"].notna() & base["geracao_mw"].notna()]
    if j.empty:
        return pd.DataFrame(columns=COLUNAS_DESVIOS)
    j = j.assign(desvio_mw=j["geracao_mw"] - j["geracao_programada_mw"])
    j = j.assign(_abs=j["desvio_mw"].abs()).sort_values(["_abs", "din_instante"], ascending=[False, True],
                                                         kind="stable")
    return j.head(n)[COLUNAS_DESVIOS].reset_index(drop=True)


def _secao_programacao(base: pd.DataFrame, programacao: Dict[str, Any], potencia: float) -> Dict[str, Any]:
    if not programacao:
        return {}
    r = programacao["resumo"]
    return {"nivel": programacao["nivel"], "maiores_desvios": maiores_desvios_programacao(base, programacao["nivel"]),
            "desvio_medio_absoluto_mw": r["desvio_medio_absoluto_mw"],
            "desvio_medio_absoluto_pct": _pct(r["desvio_medio_absoluto_mw"], potencia), "horas": r["horas_comuns"]}


# ---------------------------------------------------------------------------
# Campo ``renovavel``
# ---------------------------------------------------------------------------


def analisar_renovavel(tabelas: Dict[str, Optional[pd.DataFrame]], base: pd.DataFrame, tipo: str, potencia: float,
                       programacao: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Campo ``renovavel`` dos resultados (decisão D21); as seções sem base ficam vazias (e são omitidas, com o
    motivo, por quem chama)."""
    semi = tabelas.get("restricao_semi_horaria")
    renovavel = {
        "tipo": tipo,
        "fator_capacidade": _secao_fator_capacidade(tabelas.get("fator_capacidade_horario")),
        "restricao": _secao_restricao(semi),
        "recurso": _secao_recurso(semi, tipo),
        "programacao": _secao_programacao(base, programacao or {}, potencia),
    }
    return renovavel if any(renovavel[k] for k in ("fator_capacidade", "restricao", "recurso", "programacao")) else {}


# ---------------------------------------------------------------------------
# Constatações das seções de eólica e solar
# ---------------------------------------------------------------------------


def achados_renovavel(renovavel: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Constatações das seções de eólica e solar (fatos, sem parecer nem causa)."""
    if not renovavel:
        return []
    achados: List[Tuple[str, str]] = []
    fc = renovavel.get("fator_capacidade") or {}
    if fc:
        r = fc["resumo"]
        achados.append(("Fator de capacidade", (
            f"Fator de capacidade publicado pelo ONS de {fmt_pct(r['fator_capacidade_pct'])} de {fmt_data(r['inicio'])} "
            f"a {fmt_data(r['fim'])}, no nível {NOME_NIVEL.get(fc['nivel'], fc['nivel'])}, em "
            f"{fmt_int(r['horas'])} horas.")))
    c = renovavel.get("restricao") or {}
    if c:
        r = c["resumo"]
        texto = (f"Energia cortada por restrição de operação de {fmt_num(r['energia_cortada_mwh'], 0)} MWh nas "
                 f"{fmt_int(r['semi_horas_restritas'])} semi-horas com a marca de restrição "
                 f"({fmt_pct(r['pct_estimada'])} da energia estimada nas semi-horas com a marca); diferença bruta entre a "
                 f"estimada e a verificada de {fmt_num(r['diferenca_bruta_mwh'], 0)} MWh em todas as semi-horas.")
        if r["semi_horas_sem_marca"]:
            texto += (f" {fmt_int(r['semi_horas_sem_marca'])} "
                      f"{plural(r['semi_horas_sem_marca'], 'semi-hora', 'semi-horas')} sem a marca, fora do total.")
        if r["semi_horas_sem_estimativa"]:
            texto += (f" Sem a estimativa do ONS (estimada 0 com a usina gerando) em "
                      f"{fmt_int(r['semi_horas_sem_estimativa'])} "
                      f"{plural(r['semi_horas_sem_estimativa'], 'semi-hora', 'semi-horas')}, "
                      f"{fmt_int(r['semi_horas_restritas_sem_estimativa'])} delas com a marca de restrição, em que o "
                      "corte não pôde ser calculado.")
        achados.append(("Energia cortada", texto))
    rec = renovavel.get("recurso") or {}
    if rec and (rec["resumo"]["semi_horas_invalidas"] or rec["resumo"]["semi_horas_implausiveis"]):
        r = rec["resumo"]
        texto = (f"Medição de {rec['grandeza']} marcada como inválida pelo ONS em "
                 f"{fmt_int(r['semi_horas_invalidas'])} das {fmt_int(r['semi_horas'])} semi-horas "
                 f"({fmt_pct(r['pct_invalidas'])}), fora das faixas.")
        if r["semi_horas_implausiveis"]:
            texto += (f" Também fora das faixas, sem a marca do ONS: "
                      f"{fmt_int(r['semi_horas_implausiveis'])} "
                      f"{plural(r['semi_horas_implausiveis'], 'semi-hora', 'semi-horas')} com {rec['grandeza']} acima de "
                      f"{fmt_num(rec['limite'], 0)} {rec['unidade']}, acima do limite físico.")
        achados.append(("Recurso × geração", texto))
    return achados


# ---------------------------------------------------------------------------
# Omissões
# ---------------------------------------------------------------------------


def omissoes_renovavel(perfil: Any, renovavel: Dict[str, Any]) -> List[Dict[str, str]]:
    """Seções de eólica e solar sem base para a usina, com o motivo (FR-005), na ordem do relatório."""
    saida: List[Dict[str, str]] = []
    fc = renovavel.get("fator_capacidade") if renovavel else None
    if not fc:
        motivo = (f"sem o Fator de capacidade ({_cobertura_texto(perfil, 'fator_capacidade')})"
                  if registro.nivel_coletado(perfil, "fator_capacidade") is None
                  else "o Fator de capacidade não tem horas no período da série de referência")
        saida.append({"item": TITULO_FATOR_CAPACIDADE, "tipo": "secao", "motivo": motivo})
    restricao = renovavel.get("restricao") if renovavel else None
    if registro.nivel_coletado(perfil, "restricao_detalhe") is None:
        sem = f"sem a Restrição com detalhe ({_cobertura_texto(perfil, 'restricao_detalhe')})"
        saida += [{"item": t, "tipo": "secao", "motivo": sem} for t in (TITULO_CORTE, TITULO_RECURSO)]
        return saida
    if not restricao:
        saida.append({"item": TITULO_CORTE, "tipo": "secao",
                      "motivo": "a Restrição com detalhe não tem semi-horas no período da série de referência"})
    if not (renovavel or {}).get("recurso"):
        saida.append({"item": TITULO_RECURSO, "tipo": "secao",
                      "motivo": "nenhuma semi-hora com o recurso e a geração verificada na Restrição com detalhe"})
    return saida
