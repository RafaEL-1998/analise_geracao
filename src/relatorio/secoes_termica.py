"""Seções de térmica do relatório (spec 006, fase B; rascunho 005, FR-044; decisão R18).

Nas UTE e UTN com o despacho, em ordem fixa, entre o perfil horário e a programação diária:

1. geração por motivo de despacho e inflexibilidade;
2. atendimento ao despacho;
3. disponível sem despacho e CVU × CMO (esta parte só com o CVU e o CMO).

Blocos (texto, tabelas e figuras) comuns ao PDF e ao Markdown, montados só a partir de ``res.termica``; os textos não
julgam o despacho nem afirmam causa (princípio II).
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

import pandas as pd

from src.analises.resultados import ResultadosAnalise
from src.comum.formatacao import fmt_data, fmt_data_hora, fmt_int, fmt_lista, fmt_mes_ano, fmt_num, fmt_pct, plural
from src.comum.perfil import perfil_ativo
from src.comum.regras import (
    LIMIAR_DESVIO_DESPACHO_MW,
    LIMIAR_GERACAO_PARADA_MW,
    LIMIAR_INDISPONIBILIDADE_TOTAL_MW,
    NUMERO_EVENTOS_RELATORIO,
)

SECOES_TERMICA: Tuple[str, ...] = ("despacho_motivo", "atendimento_despacho", "disponivel_sem_despacho")
TITULO_DISPONIVEL = "Disponível sem despacho"
TITULO_DISPONIVEL_CVU = "Disponível sem despacho e CVU × CMO"


def titulo_disponivel(res: ResultadosAnalise) -> str:
    """Título da terceira seção: com o CVU × CMO só quando ele foi calculado."""
    return TITULO_DISPONIVEL_CVU if (getattr(res, "termica", None) or {}).get("cvu_cmo") else TITULO_DISPONIVEL


def _mwh(valor: float) -> str:
    return "—" if valor is None or (isinstance(valor, float) and math.isnan(valor)) else fmt_num(valor, 0)


def _pct_ou_traco(valor: float) -> str:
    return "—" if valor is None or (isinstance(valor, float) and math.isnan(valor)) else fmt_pct(valor)


def _ano(ano: object, parciais: List[int]) -> str:
    return f"{ano}*" if int(ano) in parciais else str(ano)


def codigos_texto(res: ResultadosAnalise) -> str:
    """Códigos de planejamento do perfil com o período: "34 (01/2013 a 08/2018); 334 (desde 07/2021)"."""
    partes = []
    for p in getattr(perfil_ativo().identificacao, "planejamento", ()) or ():
        inicio = f"{p.inicio[5:7]}/{p.inicio[:4]}"
        partes.append(f"{p.codigo} ({inicio} a {p.fim[5:7]}/{p.fim[:4]})" if p.fim else f"{p.codigo} (desde {inicio})")
    return "; ".join(partes)


# ---------------------------------------------------------------------------
# Linhas das tabelas
# ---------------------------------------------------------------------------


def linhas_tabela_motivos(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Energia de cada motivo no período do despacho, com a parcela na geração total publicada."""
    m = res.termica["motivos_anual"]
    cabecalho = ["Motivo", "Programada (MWh)", "Verificada (MWh)", "% da programada", "% da verificada"]
    soma = m.groupby(["motivo", "grupo"], sort=False)[["programado_mwh", "verificado_mwh"]].sum(min_count=1)
    total = soma.xs("total", level="grupo").iloc[0]
    linhas = []
    for (motivo, grupo), r in soma.iterrows():
        rotulo = motivo if grupo != "detalhe" else f"{motivo} (detalhe)"
        if grupo == "total":
            parcela_p = parcela_v = "100,0%" if total["verificado_mwh"] or total["programado_mwh"] else "—"
        else:
            parcela_p = _pct_ou_traco(r["programado_mwh"] / total["programado_mwh"] * 100
                                      if total["programado_mwh"] else math.nan)
            parcela_v = _pct_ou_traco(r["verificado_mwh"] / total["verificado_mwh"] * 100
                                      if total["verificado_mwh"] else math.nan)
        linhas.append([rotulo, _mwh(r["programado_mwh"]), _mwh(r["verificado_mwh"]), parcela_p, parcela_v])
    return cabecalho, linhas


def linhas_tabela_despacho_anual(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Por ano: geração programada e verificada, horas com despacho e inflexibilidade programada e verificada."""
    t = res.termica
    parciais = res.cobertura.get("anos_parciais", [])
    m = t["motivos_anual"]
    total = m[m["grupo"] == "total"].set_index("periodo")
    inflex = m[m["motivo"] == "Inflexibilidade"].set_index("periodo")
    horas = t.get("horas_com_despacho_anual", {})
    cabecalho = ["Ano", "Programada (MWh)", "Verificada (MWh)", "Horas com despacho", "Inflexibilidade programada (MWh)",
                 "Inflexibilidade verificada (MWh)"]
    linhas = []
    for ano, r in total.iterrows():
        i = inflex.loc[ano] if ano in inflex.index else None
        linhas.append([_ano(ano, parciais), _mwh(r["programado_mwh"]), _mwh(r["verificado_mwh"]),
                       fmt_int(horas.get(str(ano), 0)),
                       _mwh(i["programado_mwh"]) if i is not None else "0",
                       _mwh(i["verificado_mwh"]) if i is not None else "0"])
    return cabecalho, linhas


def linhas_tabela_atendimento(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    a = res.termica["atendimento"]["anual"]
    parciais = res.cobertura.get("anos_parciais", [])
    cabecalho = ["Ano", "Horas com programação", "Horas abaixo", "Energia abaixo (MWh)", "Horas acima",
                 "Energia acima (MWh)", "Horas sem programação, com geração", "Energia sem programação (MWh)"]
    linhas = [[_ano(r.ano, parciais), fmt_int(r.horas_programadas), fmt_int(r.horas_abaixo),
               fmt_num(r.energia_abaixo_mwh, 0), fmt_int(r.horas_acima), fmt_num(r.energia_acima_mwh, 0),
               fmt_int(r.horas_sem_programacao), fmt_num(r.energia_sem_programacao_mwh, 0)] for r in a.itertuples()]
    return cabecalho, linhas


def linhas_tabela_maiores_desvios(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    d = res.termica["atendimento"]["maiores_desvios"]
    return (["Hora", "Programada (MW)", "Verificada (MW)", "Desvio (MW)"],
            [[fmt_data_hora(r.din_instante), fmt_num(r.programado_mw, 1), fmt_num(r.verificado_mw, 1),
              fmt_num(r.desvio_mw, 1)] for r in d.itertuples()])


def linhas_tabela_disponivel(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    d = res.termica["disponivel_sem_despacho"]["anual"]
    parciais = res.cobertura.get("anos_parciais", [])
    return (["Ano", "Horas com disponibilidade e despacho", "Horas disponíveis sem despacho", "% das horas",
             "Potência disponível média nelas (MW)"],
            [[_ano(r.ano, parciais), fmt_int(r.horas_comuns), fmt_int(r.horas_disponivel_sem_despacho),
              fmt_pct(r.horas_disponivel_sem_despacho / r.horas_comuns * 100 if r.horas_comuns else math.nan),
              "—" if pd.isna(r.potencia_disponivel_media_mw) else fmt_num(r.potencia_disponivel_media_mw, 1)]
             for r in d.itertuples()])


def linhas_tabela_cvu_cmo(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    r = res.termica["cvu_cmo"]["resumo"]
    return (["Unidade de planejamento", "Semanas", "CVU abaixo do CMO (semanas)", "Geração nessas semanas (MWh)",
             "CVU acima do CMO (semanas)", "Geração nessas semanas (MWh)", "CVU igual ao CMO (semanas)",
             "Sem comparação (semanas)"],
            [[str(x.codigo), fmt_int(x.semanas), fmt_int(x.semanas_abaixo), fmt_num(x.geracao_abaixo_mwh, 0),
              fmt_int(x.semanas_acima), fmt_num(x.geracao_acima_mwh, 0), fmt_int(x.semanas_igual),
              fmt_int(x.semanas_sem_comparacao)]
             for x in r.itertuples()])


# ---------------------------------------------------------------------------
# Textos das tabelas, legendas e nota
# ---------------------------------------------------------------------------


def textos_tabelas(res: ResultadosAnalise) -> Dict[str, Tuple[str, str]]:
    """Subtítulo e nota das tabelas das seções de térmica."""
    return {
        "tab_motivos_termica": ("Geração por motivo de despacho no período", (
            "Motivos e totais como publicados pelo ONS, somadas as unidades de planejamento. Os motivos podem se "
            "sobrepor (os marcados como detalhe compõem ou se sobrepõem a outros), e a soma das parcelas pode diferir "
            "de 100 %; a parcela é sobre a geração total publicada. Só os motivos com energia no período.")),
        "tab_despacho_anual": ("Geração programada e verificada do despacho por ano", (
            f"* Ano parcial. Horas com despacho = horas com geração programada acima de "
            f"{fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW.")),
        "tab_atendimento_anual": ("Atendimento ao despacho por ano", (
            f"* Ano parcial. Nas horas com geração programada acima de {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW, desvio "
            f"= verificada − programada; abaixo e acima = desvio além de {fmt_num(LIMIAR_DESVIO_DESPACHO_MW, 0)} MW. Sem "
            f"programação, com geração = programada até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW e verificada mais de "
            f"{fmt_num(LIMIAR_DESVIO_DESPACHO_MW, 0)} MW acima dela.")),
        "tab_maiores_desvios": ("Maiores desvios entre a geração verificada e a programada",
                                f"Até {NUMERO_EVENTOS_RELATORIO} horas, as de maior desvio absoluto; a lista completa "
                                "está na planilha."),
        "tab_disponivel_anual": ("Horas disponíveis sem despacho por ano", (
            f"* Ano parcial. Disponibilidade operacional acima de {fmt_num(LIMIAR_INDISPONIBILIDADE_TOTAL_MW, 3)} MW, "
            f"com programação e geração até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW.")),
        "tab_cvu_cmo": ("CVU de cada unidade × CMO médio semanal do subsistema", (
            "Por semana operativa (sábado a sexta). CVU da revisão mais recente; CVU ausente, zero ou negativo fica "
            "sem comparação. A comparação não avalia o despacho.")),
    }


def legenda_figura(res: ResultadosAnalise, chave: str) -> str:
    t = res.termica
    p = t.get("periodo", {})
    periodo = f"de {fmt_mes_ano(p['inicio'])} a {fmt_mes_ano(p['fim'])}" if p else ""
    if chave == "despacho_motivo_mensal":
        return (f"Geração verificada mensal por motivo de despacho (GWh), {periodo}, somadas as unidades de "
                "planejamento; o ponto marca a geração verificada total publicada.")
    if chave == "inflexibilidade_mensal":
        return f"Inflexibilidade programada e verificada por mês (GWh), {periodo}."
    if chave == "desvios_despacho":
        return (f"Energia mensal das horas com a geração verificada mais de {fmt_num(LIMIAR_DESVIO_DESPACHO_MW, 0)} MW "
                f"abaixo (barras para baixo) e acima (para cima) da programada, {periodo}.")
    if chave == "cvu_cmo":
        subsistema = perfil_ativo().usina.subsistema
        return (f"CVU semanal de cada unidade de planejamento e CMO médio semanal do subsistema {subsistema} "
                f"(R$/MWh), {periodo}; a linha se interrompe nas semanas com CVU ausente, zero ou negativo.")
    return ""


def nota(res: ResultadosAnalise) -> str:
    """Nota metodológica das seções de térmica."""
    texto = (f"Despacho térmico: Geração térmica por motivo de despacho, pelo CEG, com os códigos de planejamento do "
             f"perfil: {codigos_texto(res)}. As unidades são somadas por hora, na hora de início do intervalo.")
    if res.termica.get("cvu_coletado"):
        texto += (" CVU: o da revisão mais recente de cada semana operativa; CVU ausente, zero ou negativo é sinalizado "
                  "e mantido, sem comparação.")
    if res.termica.get("cmo_coletado"):
        texto += (f" CMO: o médio semanal do subsistema {perfil_ativo().usina.subsistema}, dado agregado, contexto do "
                  "subsistema e não da usina.")
    return texto


# ---------------------------------------------------------------------------
# Blocos
# ---------------------------------------------------------------------------


def blocos(res: ResultadosAnalise, chave: str) -> list:
    """Blocos de cada seção de térmica, na ordem em que o PDF e o Markdown os mostram."""
    from src.relatorio.comum import Bloco, _numericas, _tabela

    t = res.termica
    b = []
    if chave == "despacho_motivo":
        p = t["periodo"]
        b.append(Bloco("texto", textos=[
            f"Despacho de {fmt_data(p['inicio'])} a {fmt_data(p['fim'])} ({fmt_int(p['horas'])} horas), com "
            f"{plural(len(t['codigos']), 'a unidade de planejamento', 'as unidades de planejamento')} "
            f"{fmt_lista([str(c) for c in t['codigos']])}."]))
        cab, linhas = linhas_tabela_motivos(res)
        b.append(_tabela("tab_motivos_termica", (cab, linhas), [2.6, 1.0, 1.0, 0.9, 0.9], _numericas(cab, 1)))
        cab, linhas = linhas_tabela_despacho_anual(res)
        b.append(_tabela("tab_despacho_anual", (cab, linhas), [0.6, 1.0, 1.0, 0.9, 1.1, 1.1], _numericas(cab, 1)))
        if not t["sem_geracao"]:
            b.append(Bloco("figura", "despacho_motivo_mensal"))
        if (t["inflexibilidade_resumo"].get("programada_mwh") or 0) > 0 or \
                (t["inflexibilidade_resumo"].get("verificada_mwh") or 0) > 0:
            b.append(Bloco("figura", "inflexibilidade_mensal"))
    elif chave == "atendimento_despacho":
        cab, linhas = linhas_tabela_atendimento(res)
        b.append(_tabela("tab_atendimento_anual", (cab, linhas), [0.6] + [1.0] * (len(cab) - 1), _numericas(cab, 1)))
        cab, linhas = linhas_tabela_maiores_desvios(res)
        if linhas:
            b.append(_tabela("tab_maiores_desvios", (cab, linhas), [1.4, 1.0, 1.0, 1.0], _numericas(cab, 1)))
            b.append(Bloco("figura", "desvios_despacho"))
        else:
            b.append(Bloco("sem_linhas", "tab_maiores_desvios",
                           textos=[f"Nenhuma hora com desvio além de {fmt_num(LIMIAR_DESVIO_DESPACHO_MW, 0)} MW."]))
    elif chave == "disponivel_sem_despacho":
        if t.get("disponivel_sem_despacho"):
            cab, linhas = linhas_tabela_disponivel(res)
            b.append(_tabela("tab_disponivel_anual", (cab, linhas), [0.6, 1.1, 1.1, 0.8, 1.2], _numericas(cab, 1)))
        if t.get("cvu_cmo"):
            cab, linhas = linhas_tabela_cvu_cmo(res)
            b.append(_tabela("tab_cvu_cmo", (cab, linhas), [1.1, 0.7, 1.0, 1.0, 1.0, 1.0, 0.9, 0.9],
                             _numericas(cab, 1)))
            b.append(Bloco("figura", "cvu_cmo"))
    return b
