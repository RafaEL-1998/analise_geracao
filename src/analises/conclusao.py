"""Conclusão do relatório: regras C1 a C20, que apontam indícios sem afirmar causa (spec das Análises, FR-045).

As regras formam um catálogo declarado (plano das Análises, D18): cada uma diz os tipos de usina, as listas em que pode
gerar itens, o nível exigido (só dado da usina), os limiares, o período mínimo e as seções de origem. Nas hidrelétricas
com EVT, C1 a C11 continuam como antes, com a mesma ordem, texto, limiares e listas (decisão D16). Nas usinas sem EVT,
as regras comuns (C2, C5, C8 e C10) são avaliadas sobre a base horária comum, só com dados da usina; nas térmicas, também
C12 a C15, sobre o despacho, o CVU e o CMO (decisão D18); nas eólicas e solares, só C16 a C19, sobre a
restrição de operação, o recurso, o fator de capacidade e a programação da usina. Nas hidrelétricas e térmicas,
com ou sem EVT, também a C20, sobre as taxas operativas (spec das Análises, FR-063). O que não é avaliado vai para
``omitidos``, com o motivo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from src.analises.comum import _pct, _rotulo_ano, _rotulo_janela
from src.analises.hidrologia import ATE_UMA_UNIDADE, entre_unidades
from src.analises.indicadores import DESCRICAO_PARCELA
from src.analises.resultados import ResultadosAnalise, sem_evt
from src.coleta.registro import HIDRELETRICAS, RENOVAVEIS, TERMICAS
from src.comum.formatacao import (fmt_data, fmt_data_hora, fmt_int, fmt_lista, fmt_mes_ano, fmt_num, fmt_pct,
                                   fmt_pp, plural)
from src.comum.perfil import perfil_ativo
from src.comum.regras import (
    HORAS_DIURNAS,
    LIMIAR_CONCLUSAO_AFLUENCIA_ENGOLIMENTO_PCT,
    LIMIAR_CONCLUSAO_DESPACHO_ABAIXO_HORAS,
    LIMIAR_CONCLUSAO_DIFERENCA_RESERVA_GWH,
    LIMIAR_CONCLUSAO_DESVIO_PROGRAMACAO_PCT,
    LIMIAR_CONCLUSAO_DISPONIVEL_CVU_HORAS,
    LIMIAR_CONCLUSAO_ENERGIA_CORTADA_PCT,
    LIMIAR_CONCLUSAO_EVT_PARADA_PCT,
    LIMIAR_CONCLUSAO_INDISPONIBILIDADE_DIAS,
    LIMIAR_CONCLUSAO_INFLEXIBILIDADE_PCT,
    LIMIAR_CONCLUSAO_MESES_LIMITACAO_PCT,
    LIMIAR_CONCLUSAO_PARTICIPACAO_TEIFA,
    LIMIAR_CONCLUSAO_PROGRAMACAO_ZERO_PCT,
    LIMIAR_CONCLUSAO_PROGRAMADA_UG_PCT,
    LIMIAR_CONCLUSAO_R7_HORAS,
    LIMIAR_CONCLUSAO_R9_HORAS,
    LIMIAR_CONCLUSAO_RECURSO_INVALIDO_PCT,
    LIMIAR_CONCLUSAO_SEM_PROGRAMACAO_HORAS,
    LIMIAR_DESVIO_DESPACHO_MW,
    LIMIAR_DESVIO_PROGRAMACAO_MW,
    LIMIAR_DIFERENCA_TAXAS_OPERATIVAS_PP,
    LIMIAR_GERACAO_PARADA_MW,
    RAZAO_DIURNA_RELEVANTE,
)


LISTAS_CONCLUSAO: Tuple[Tuple[str, str], ...] = (
    ("pontos_atencao", "Pontos de atenção"),
    ("possiveis_problemas", "Possíveis problemas"),
    ("confirmar_agente", "A confirmar com o agente"),
    ("verificar_campo", "A verificar em campo"),
)
FRASE_ABERTURA_CONCLUSAO = (
    "Indícios a confirmar, gerados pelas regras descritas nas notas metodológicas a partir dos resultados das seções "
    "indicadas; não afirmam causa nem avaliam o desempenho da usina."
)
FRASE_CONCLUSAO_VAZIA = "Os dados não indicaram pontos de atenção pelos critérios das regras da conclusão."


def _item(lista: str, regra: str, texto: str, secoes: Sequence[str]) -> Dict[str, Any]:
    return {"lista": lista, "regra": regra, "texto": texto, "secoes": list(secoes)}


def _maiuscula(texto: str) -> str:
    return texto[:1].upper() + texto[1:]


def _horas_regra(res: ResultadosAnalise, codigo: str) -> int:
    t = res.resumo_anomalias
    if t is None or not len(t) or "regra" not in t.columns:
        return 0
    return int(t.loc[t["regra"] == codigo, "horas"].sum())


def _periodo_programacao(res: ResultadosAnalise) -> Optional[Dict[str, Any]]:
    return res.programacao.get("periodo") if res.programacao else None


def _regra_c1(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """Paradas com EVT: EVT com a usina parada ≥ 10 % da EVT."""
    g = res.globais
    if g.get("evt_parada_pct", 0.0) < LIMIAR_CONCLUSAO_EVT_PARADA_PCT:
        return []
    anuais = res.indicadores_anuais
    total = float(anuais["evt_parada_mwh"].sum()) if "evt_parada_mwh" in anuais.columns else 0.0
    anos: List[int] = []
    if total > 0:
        acumulado = 0.0
        for r in anuais.sort_values("evt_parada_mwh", ascending=False).itertuples():
            anos.append(int(r.ano))
            acumulado += float(r.evt_parada_mwh)
            if acumulado >= total / 2:
                break
    texto = (f"{fmt_num(g['evt_parada_mwh'] / 1000, 1)} GWh de EVT ({fmt_pct(g['evt_parada_pct'])} do total) ocorreram "
             f"com a usina parada, em {fmt_int(g['horas_parada_com_evt'])} h")
    if anos:
        texto += f", sobretudo em {fmt_lista(sorted(anos))}"
    secoes = ["eventos"]
    p = _periodo_programacao(res)
    programacao = bool(p) and p.get("pct_horas_programacao_zero", 0.0) >= LIMIAR_CONCLUSAO_PROGRAMACAO_ZERO_PCT
    if programacao:
        texto += (f"; no período com programação diária, {fmt_pct(p['pct_horas_programacao_zero'])} dessas horas tinham "
                  f"programação do ONS de até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW")
        secoes.append("programacao")
    motivo = ("Motivo das paradas com vertimento turbinável"
              + (f" e programação de até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW" if programacao else "")
              + " (ordens do ONS, restrições elétricas ou energéticas), com os registros dos maiores eventos")
    return [
        _item("pontos_atencao", "C1", texto, secoes),
        _item("confirmar_agente", "C1", motivo, secoes),
        _item("verificar_campo", "C1", "Livro de operação e supervisório nas datas dos maiores eventos de parada com EVT: "
              "ordens recebidas, comandos de parada e abertura do vertedouro", ["eventos"]),
    ]


def _regra_c2(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """Unidade geradora: ≥ 2/3 da TEIFa (acima da referência) ou limitação forçada em ≥ 50 % dos meses."""
    o = res.ons or {}
    horas = o.get("horas_mensal")
    if horas is None or not len(horas):
        return []
    t = o.get("taxa_ultima") or {}
    teif = perfil_ativo().parametros.teif_referencia  # sem a TEIF de referência, só a limitação recorrente (D18)
    teifa_acima = bool(t) and teif is not None and t["teifa_pct"] > teif * 100.0
    participacao: Dict[int, float] = {}
    parcela_dominante: Dict[int, str] = {}
    dec = o.get("decomposicao")
    if dec is not None and len(dec):
        teifa = dec[dec["taxa"] == "TEIFa"]
        participacao = {int(u): float(v) for u, v in teifa.groupby("ug")["participacao_pct"].sum().items()}
        parcela_dominante = {int(u): str(g.loc[g["participacao_pct"].idxmax(), "parcela"]) for u, g in teifa.groupby("ug")}
    por_ug = horas.groupby("ug").agg(meses=("mes", "nunique"), meses_hedf=("HEDF", lambda s: int((s > 0).sum())),
                                     hedf=("HEDF", "sum"))
    itens: List[Dict[str, Any]] = []
    for ug, r in por_ug.iterrows():
        ug = int(ug)
        dominante = teifa_acima and participacao.get(ug, 0.0) >= LIMIAR_CONCLUSAO_PARTICIPACAO_TEIFA * 100.0
        recorrente = bool(r["meses"]) and r["meses_hedf"] / r["meses"] * 100.0 >= LIMIAR_CONCLUSAO_MESES_LIMITACAO_PCT
        if not (dominante or recorrente):
            continue
        limitacao = recorrente or parcela_dominante.get(ug) == "HEDF"
        partes = [f"UG{ug}: indício de problema na unidade"]
        if recorrente:
            outras = por_ug.drop(index=ug)
            partes[0] += (f", com limitação forçada de potência em {fmt_int(r['meses_hedf'])} dos {fmt_int(r['meses'])} "
                          f"meses ({fmt_int(r['hedf'])} h equivalentes"
                          + "".join(f"; UG{int(u)}: {fmt_int(v)} h" for u, v in outras["hedf"].items()) + ")")
        if dominante:
            parte = f"responde por {fmt_pct(participacao[ug], 0)} da TEIFa de {fmt_mes_ano(t['mes'])}"
            taxa = f"{fmt_pct(t['teifa_pct'], 2)}, acima da referência de {fmt_pct(perfil_ativo().parametros.teif_referencia * 100, 3)}"
            if recorrente:
                partes.append(f"{parte}, que ficou em {taxa}")
            else:
                descricao = DESCRICAO_PARCELA.get(parcela_dominante.get(ug, ""), "horas forçadas")
                partes.append(f"{parte}, sobretudo por {descricao}; a TEIFa ficou em {taxa}")
        objeto = "da limitação forçada de potência" if limitacao else "dos desligamentos forçados"
        campo = (f"UG{ug}: potência máxima que a unidade alcança hoje e registros de limitação no supervisório e no livro de "
                 "operação" if limitacao else
                 f"UG{ug}: registros dos desligamentos forçados no supervisório e no livro de operação")
        itens += [
            _item("possiveis_problemas", "C2", "; ".join(partes), ["indicadores_ons"]),
            _item("confirmar_agente", "C2", f"Causa, histórico e situação atual {objeto} da UG{ug}: ocorrências, ordens de "
                  "serviço e correção prevista", ["indicadores_ons"]),
            _item("verificar_campo", "C2", campo, ["indicadores_ons"]),
        ]
    return itens


def _regra_c3(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """Afluência que cabia nas turbinas em ≥ 80 % das horas com EVT."""
    h = res.hidrologia
    if not h or not h.get("publicado"):
        return []
    r = h["resumo"]
    faixas, total = r["horas_por_faixa"], r["horas_evt"]
    cabia = _pct(faixas[ATE_UMA_UNIDADE] + faixas[entre_unidades()], total)
    if cabia < LIMIAR_CONCLUSAO_AFLUENCIA_ENGOLIMENTO_PCT:
        return []
    return [_item("pontos_atencao", "C3", f"Em {fmt_pct(cabia)} das horas com EVT, a afluência cabia nas turbinas da usina, "
                  f"cujo engolimento máximo é de {fmt_num(perfil_ativo().engolimento_maximo_m3s, 1)} m³/s", ["hidrologia"])]


def _regra_c4(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """Concentração diurna: razão diurna/noturna da EVT ≥ 2 em algum dos dois últimos anos."""
    anuais = res.indicadores_anuais
    if "razao_evt_diurna_noturna" not in anuais.columns:
        return []
    ultimos = anuais.tail(2)
    relevantes = ultimos[ultimos["razao_evt_diurna_noturna"] >= RAZAO_DIURNA_RELEVANTE]
    if not len(relevantes):
        return []
    anos = fmt_lista(f"{int(r.ano)}{' (parcial)' if r.ano_parcial else ''}" for r in relevantes.itertuples())
    geracao = fmt_lista(fmt_pct(v * 100, 0) for v in relevantes["razao_geracao_diurna_noturna"])
    return [_item("pontos_atencao", "C4", f"Em {anos}, a EVT concentrou-se na janela das {_rotulo_janela(HORAS_DIURNAS)}, "
                  f"com a geração diurna em {geracao} da noturna", ["perfil_horario"])]


def _regra_c5(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """Disponibilidade abaixo da referência da garantia física ou taxas acima das referências."""
    g = res.globais
    partes: List[str] = []
    secoes: List[str] = []
    desvio = g.get("desvio_disponibilidade_referencia_pp", 0.0)
    if desvio < 0:
        partes.append(f"disponibilidade declarada média de {fmt_pct(g['disponibilidade_relativa_pct'])}, "
                      f"{fmt_num(abs(desvio), 1)} p.p. abaixo da referência da garantia física, de "
                      f"{fmt_pct(g['disponibilidade_referencia_pct'])}")
        secoes.append("indicadores_anuais")
    o = res.ons or {}
    referencia = perfil_ativo().disponibilidade_referencia * 100.0
    p = o.get("disp_periodo")
    if p and p["dispf_pct"] < referencia:
        partes.append(f"DISPF médio de {fmt_pct(p['dispf_pct'])}, abaixo da referência de {fmt_pct(referencia)}")
    t = o.get("taxa_ultima")
    if t and t["teifa_pct"] > perfil_ativo().parametros.teif_referencia * 100.0:
        partes.append(f"TEIFa de {fmt_pct(t['teifa_pct'], 2)} em {fmt_mes_ano(t['mes'])}, acima da TEIF de referência "
                      f"de {fmt_pct(perfil_ativo().parametros.teif_referencia * 100, 3)}")
    if t and t["teip_pct"] > perfil_ativo().parametros.ip_referencia * 100.0:
        partes.append(f"TEIP de {fmt_pct(t['teip_pct'], 2)} em {fmt_mes_ano(t['mes'])}, acima do IP de referência "
                      f"de {fmt_pct(perfil_ativo().parametros.ip_referencia * 100, 3)}")
    if not partes:
        return []
    if len(partes) > len(secoes):
        secoes.append("indicadores_ons")
    return [_item("pontos_atencao", "C5", _maiuscula("; ".join(partes)), secoes)]


def _regra_c6(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """Parada com geração programada: ≥ 1 evento de usina parada com programação acima de 5 MW."""
    p = _periodo_programacao(res)
    if not p or not p.get("eventos_desvio"):
        return []
    n = int(p["eventos_desvio"])
    limiar = fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 0)
    texto = (f"{fmt_int(p['horas_desvio'])} h em {fmt_int(n)} {plural(n, 'evento', 'eventos')} com a usina parada e "
             f"programação do ONS acima de {limiar} MW")
    maior = p.get("maior_evento")
    if maior is not None:
        texto += (f"; o mais longo, de {fmt_data_hora(maior['inicio'])} a {fmt_data_hora(maior['fim'])}, durou "
                  f"{fmt_int(maior['duracao_h'])} h")
    return [
        _item("possiveis_problemas", "C6", texto, ["programacao"]),
        _item("confirmar_agente", "C6", f"Ocorrências nos {fmt_int(n)} {plural(n, 'evento', 'eventos')} de parada com "
              f"programação acima de {limiar} MW, listados na aba PROG_EVENTOS_DESVIO da planilha", ["programacao"]),
        _item("verificar_campo", "C6", f"Registros de ocorrência no livro de operação nos eventos de parada com programação "
              f"acima de {limiar} MW", ["programacao"]),
    ]


def _divergencias_classificacao(res: ResultadosAnalise) -> Tuple[List[str], List[str]]:
    """Partes do texto e seções da regra C7 (vazias se ela não dispara)."""
    partes: List[str] = []
    secoes: List[str] = []
    anual = (res.disponibilidade or {}).get("anual")
    if anual is not None and len(anual) and "diferenca_mwh" in anual.columns:
        fora = anual[anual["diferenca_mwh"].abs() >= LIMIAR_CONCLUSAO_DIFERENCA_RESERVA_GWH * 1000.0]
        if len(fora):
            anos = fmt_lista(
                f"{_rotulo_ano(r.periodo, r.ano_parcial)} ({'+' if r.diferenca_mwh > 0 else '−'}"
                f"{fmt_num(abs(r.diferenca_mwh) / 1000, 1)} GWh)" for r in fora.itertuples()
            )
            partes.append(f"capacidade não sincronizada diferente da reserva desligada informada ao ONS em {anos}")
            secoes.append("disponibilidade_sincronizada")
    div = (res.ons or {}).get("divergencias")
    if div is not None and len(div):
        partes.append(f"{fmt_int(len(div))} {plural(len(div), 'mês-unidade', 'meses-unidade')} em que o DISPF e as horas "
                      "por estado operativo classificam o tempo parado de forma diferente")
        secoes.append("indicadores_ons")
    return partes, secoes


def _regra_c7(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """Classificação de estados: não sincronizada × reserva ≥ 5 GWh num ano, ou DISPF × TEIP divergentes.

    O item "a confirmar" junta a C8 (geração acima da disponibilidade declarada), quando as duas disparam.
    """
    partes, secoes = _divergencias_classificacao(res)
    if not partes:
        return []
    horas_r7 = _horas_regra(res, "R7")
    confirmar = "Classificação dos estados das unidades (reserva desligada e desligamento programado)"
    if horas_r7 >= LIMIAR_CONCLUSAO_R7_HORAS:
        confirmar += (f" e declarações de disponibilidade informadas ao ONS, inclusive as {fmt_int(horas_r7)} h com "
                      "geração acima da disponibilidade declarada")
        secoes_confirmar = secoes + ["qualidade"]
    else:
        confirmar += " informada ao ONS"
        secoes_confirmar = secoes
    return [
        _item("possiveis_problemas", "C7", _maiuscula("; ".join(partes)), secoes),
        _item("confirmar_agente", "C7", confirmar, secoes_confirmar),
    ]


def _regra_c8(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """Geração acima da disponibilidade declarada (R7) em ≥ 100 h."""
    horas = _horas_regra(res, "R7")
    if horas < LIMIAR_CONCLUSAO_R7_HORAS:
        return []
    itens = [_item("possiveis_problemas", "C8", f"Geração acima da disponibilidade declarada em {fmt_int(horas)} h, "
                   "segundo a regra R7", ["qualidade"])]
    if not _divergencias_classificacao(res)[0]:  # sem a C7, a pergunta ao agente fica nesta regra
        itens.append(_item("confirmar_agente", "C8", "Critério e horário da declaração de disponibilidade ao ONS, dado que "
                           f"a geração superou a disponibilidade declarada em {fmt_int(horas)} h", ["qualidade"]))
    return itens


def _regra_c9(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """Geração abaixo da garantia física, ou EVT do último ano completo como a maior da série."""
    g = res.globais
    partes: List[str] = []
    razao = g.get("geracao_sobre_garantia_fisica_pct", 100.0)
    if razao < 100.0:
        partes.append(f"geração média de {fmt_pct(razao)} da garantia física ({fmt_num(perfil_ativo().parametros.garantia_fisica_mwmed, 1)} MWmed)")
    anuais = res.indicadores_anuais
    completos = anuais[~anuais["ano_parcial"]] if "ano_parcial" in anuais.columns else anuais.iloc[0:0]
    if len(completos) >= 2:
        ultimo = completos.iloc[-1]
        if float(ultimo["evt_mwh"]) >= float(completos["evt_mwh"].max()):
            partes.append(f"a EVT de {int(ultimo['ano'])} ({fmt_num(float(ultimo['evt_mwh']) / 1000, 1)} GWh) foi a maior "
                          "dos anos completos")
    if not partes:
        return []
    return [_item("pontos_atencao", "C9", _maiuscula("; ".join(partes)), ["indicadores_anuais"])]


def _unidades_agrupadas(sel: pd.DataFrame, total_unidades: int) -> str:
    """Unidades e anos das paradas programadas longas, com os anos seguidos de mesmas unidades juntos:
    "de todas as unidades em 2022, 2023 e 2024; da UG1 em 2025" (usinas sem EVT, com muitas unidades)."""
    blocos: List[Tuple[Tuple[int, ...], List[int]]] = []
    for ano, g in sel.groupby("ano"):
        unidades = tuple(sorted(int(u) for u in g["ug"]))
        if blocos and blocos[-1][0] == unidades:
            blocos[-1][1].append(int(ano))
        else:
            blocos.append((unidades, [int(ano)]))
    textos = []
    for unidades, anos in blocos:
        if len(unidades) == total_unidades > 1:
            quem = "de todas as unidades"
        elif len(unidades) == 1:
            quem = f"da UG{unidades[0]}"
        else:
            quem = "das " + fmt_lista(f"UG{u}" for u in unidades)
        textos.append(f"{quem} em {fmt_lista(str(a) for a in anos)}")
    return "; ".join(textos)


def _regra_c10(res: ResultadosAnalise, eventos: Optional[pd.DataFrame] = None,
               agrupar_unidades: bool = False) -> List[Dict[str, Any]]:
    """Indisponibilidade longa: total ≥ 30 dias, ou programada ≥ 20 % numa unidade num ano completo.

    ``eventos``: os de indisponibilidade total; sem eles, os da base de EVT (nas usinas sem EVT, vêm da base comum).
    ``agrupar_unidades``: unidades e anos agrupados no texto (usinas sem EVT); o texto de hoje sem ele.
    """
    partes: List[str] = []
    secoes: List[str] = []
    anos: set = set()
    eventos = res.eventos_indisponibilidade_total if eventos is None else eventos
    if len(eventos):
        longos = eventos[eventos["duracao_h"] >= LIMIAR_CONCLUSAO_INDISPONIBILIDADE_DIAS * 24]
        if len(longos):
            maior = longos.loc[longos["duracao_h"].idxmax()]
            partes.append(f"da indisponibilidade total de {fmt_data(maior['inicio'])} a {fmt_data(maior['fim'])}, "
                          f"com {fmt_int(maior['duracao_h'])} h")
            secoes.append("disponibilidade_geracao")
            anos.add(pd.Timestamp(maior["inicio"]).year)
    ug_anual = (res.ons or {}).get("ug_anual")
    if ug_anual is not None and len(ug_anual):
        completos = ug_anual[~ug_anual["ano_parcial"]] if "ano_parcial" in ug_anual.columns else ug_anual
        sel = completos[completos["indisppf"] >= LIMIAR_CONCLUSAO_PROGRAMADA_UG_PCT]
        if len(sel):
            if agrupar_unidades:
                quem = _unidades_agrupadas(sel, ug_anual["ug"].nunique())
            else:
                quem = fmt_lista(f"{' e '.join(f'da UG{int(u)}' for u in sorted(g['ug']))} em {int(ano)}"
                                 for ano, g in sel.groupby("ano"))
            partes.append(f"das paradas programadas longas {quem}")
            secoes.append("indicadores_ons")
            anos |= {int(a) for a in sel["ano"]}
    if not partes:
        return []
    return [
        _item("confirmar_agente", "C10", "Causa e documentação " + ", e ".join(partes), secoes),
        _item("verificar_campo", "C10", "Plano e registros de manutenção preventiva e corretiva das unidades geradoras"
              + (f", em especial de {fmt_lista(sorted(anos))}" if anos else ""), secoes),
    ]


def _regra_c11(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """Instrumentação e medição: dados hidrológicos sinalizados, ou geração com vazão turbinada nula ≥ 24 h."""
    partes: List[str] = []
    secoes: List[str] = []
    h = res.hidrologia
    if h and (h.get("resumo") or {}).get("horas_sinalizadas", 0) > 0:
        partes.append("instrumentação de nível e de vazão (réguas e sensores) que gera os dados hidrológicos informados "
                      "ao ONS")
        secoes.append("hidrologia")
    horas_r9 = _horas_regra(res, "R9")
    if horas_r9 >= LIMIAR_CONCLUSAO_R9_HORAS:
        partes.append(f"medição da vazão turbinada, dado que houve geração com vazão turbinada nula em {fmt_int(horas_r9)} h")
        secoes.append("qualidade")
    if not partes:
        return []
    return [_item("verificar_campo", "C11", _maiuscula("; ".join(partes)), secoes)]


# ---------------------------------------------------------------------------
# Regras comuns sobre a base horária comum (usinas sem EVT; plano das Análises, D16 e D18)
# ---------------------------------------------------------------------------

# Seção de origem no caminho sem EVT (decisão D16), para os itens das regras comuns
SECOES_SEM_EVT: Dict[str, str] = {
    "indicadores_ons": "indicadores_ons_comum", "qualidade": "qualidade_comum",
    "disponibilidade_geracao": "disponibilidade_geracao_comum", "indicadores_anuais": "anuais_comum",
}


def _referencias() -> Optional[Tuple[float, float]]:
    p = perfil_ativo().parametros
    return None if p.ip_referencia is None or p.teif_referencia is None else (p.ip_referencia, p.teif_referencia)


def _regra_c5_comum(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """C5 sobre a base comum: disponibilidade operacional da usina e taxas do ONS contra as referências."""
    ip, teif = _referencias()
    referencia = (1.0 - ip) * (1.0 - teif) * 100.0
    partes: List[str] = []
    secoes: List[str] = []
    d = (res.comum.get("disponibilidade") or {}).get("resumo")
    if d and d["disponibilidade_relativa_pct"] < referencia:
        partes.append(f"disponibilidade operacional média de {fmt_pct(d['disponibilidade_relativa_pct'])}, "
                      f"{fmt_num(referencia - d['disponibilidade_relativa_pct'], 1)} p.p. abaixo da referência da "
                      f"garantia física, de {fmt_pct(referencia)}")
        secoes.append("disponibilidade_geracao")
    o = res.ons or {}
    p = o.get("disp_periodo")
    if p and p["dispf_pct"] < referencia:
        partes.append(f"DISPF médio de {fmt_pct(p['dispf_pct'])}, abaixo da referência de {fmt_pct(referencia)}")
    t = o.get("taxa_ultima")
    if t and t["teifa_pct"] > teif * 100.0:
        partes.append(f"TEIFa de {fmt_pct(t['teifa_pct'], 2)} em {fmt_mes_ano(t['mes'])}, acima da TEIF de referência "
                      f"de {fmt_pct(teif * 100, 3)}")
    if t and t["teip_pct"] > ip * 100.0:
        partes.append(f"TEIP de {fmt_pct(t['teip_pct'], 2)} em {fmt_mes_ano(t['mes'])}, acima do IP de referência "
                      f"de {fmt_pct(ip * 100, 3)}")
    if not partes:
        return []
    if len(partes) > len(secoes):
        secoes.append("indicadores_ons")
    return [_item("pontos_atencao", "C5", _maiuscula("; ".join(partes)), secoes)]


def _horas_r7_comum(res: ResultadosAnalise) -> int:
    s = (res.comum.get("qualidade") or {}).get("sinalizacoes")
    if s is None or not len(s):
        return 0
    return int(s.loc[s["codigo"] == "R7", "horas"].sum())


def _regra_c8_comum(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """C8 sobre a base comum: geração da usina acima da disponibilidade declarada (R7); sem a C7, a pergunta ao
    agente fica nesta regra."""
    horas = _horas_r7_comum(res)
    if horas < LIMIAR_CONCLUSAO_R7_HORAS:
        return []
    return [
        _item("possiveis_problemas", "C8", f"Geração acima da disponibilidade declarada em {fmt_int(horas)} h, "
              "segundo a regra R7", ["qualidade"]),
        _item("confirmar_agente", "C8", "Critério e horário da declaração de disponibilidade ao ONS, dado que a geração "
              f"superou a disponibilidade declarada em {fmt_int(horas)} h", ["qualidade"]),
    ]


def _regra_c10_comum(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """C10 sobre a base comum: os eventos de indisponibilidade total da usina; a parte do ONS como na C10."""
    eventos = (res.comum.get("disponibilidade") or {}).get("eventos_indisponibilidade_total")
    return _regra_c10(res, eventos if eventos is not None else pd.DataFrame(), agrupar_unidades=True)


# ---------------------------------------------------------------------------
# Regras das térmicas (plano das Análises, D18): só com o despacho, o CVU e o CMO da usina
# ---------------------------------------------------------------------------


def _regra_c12(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """C12: geração verificada abaixo da programada pelo ONS em horas recorrentes."""
    a = (res.termica.get("atendimento") or {}).get("resumo") or {}
    horas = int(a.get("horas_abaixo", 0))
    if horas < LIMIAR_CONCLUSAO_DESPACHO_ABAIXO_HORAS:
        return []
    fato = (f"geração verificada mais de {fmt_num(LIMIAR_DESVIO_DESPACHO_MW, 0)} MW abaixo da programada pelo ONS em "
            f"{fmt_int(horas)} h ({fmt_num(a['energia_abaixo_mwh'], 0)} MWh)")
    return [_item("possiveis_problemas", "C12", _maiuscula(fato), ["atendimento_despacho"]),
            _item("confirmar_agente", "C12", f"Motivo da {fato}", ["atendimento_despacho"])]


def _regra_c13(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """C13: horas disponíveis sem despacho nas semanas com o CVU de alguma unidade abaixo do CMO do subsistema."""
    c = res.termica.get("cvu_cmo") or {}
    horas = int(c.get("horas_disponivel_cvu_abaixo", 0))
    if horas < LIMIAR_CONCLUSAO_DISPONIVEL_CVU_HORAS:
        return []
    semanas = int(c.get("semanas_disponivel_cvu_abaixo", 0))
    return [_item("confirmar_agente", "C13", (
        f"Condição de despacho da usina nas {fmt_int(semanas)} {plural(semanas, 'semana', 'semanas')} com o CVU abaixo "
        f"do CMO do subsistema, em que ficou disponível, sem programação e sem geração, por {fmt_int(horas)} h"),
        ["disponivel_sem_despacho"])]


def _regra_c14(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """C14: inflexibilidade verificada abaixo da programada."""
    r = res.termica.get("inflexibilidade_resumo") or {}
    pct = r.get("nao_verificada_pct", float("nan"))
    if not (pct >= LIMIAR_CONCLUSAO_INFLEXIBILIDADE_PCT):
        return []
    return [_item("pontos_atencao", "C14", (
        f"Inflexibilidade programada não verificada de {fmt_num(r['nao_verificada_mwh'], 0)} MWh, "
        f"{fmt_pct(pct)} dos {fmt_num(r['programada_mwh'], 0)} MWh de inflexibilidade programada"),
        ["despacho_motivo"])]


def _regra_c15(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """C15: geração acima da programada, sem programação correspondente, em horas recorrentes."""
    a = (res.termica.get("atendimento") or {}).get("resumo") or {}
    horas = int(a.get("horas_sem_programacao", 0))
    if horas < LIMIAR_CONCLUSAO_SEM_PROGRAMACAO_HORAS:
        return []
    return [_item("confirmar_agente", "C15", (
        f"Programação do ONS correspondente à geração verificada em {fmt_int(horas)} h sem programação, com "
        f"{fmt_num(a['energia_sem_programacao_mwh'], 0)} MWh acima da programada"), ["atendimento_despacho"])]


# ---------------------------------------------------------------------------
# Regras das eólicas e solares (plano das Análises, D18): só com dados da usina
# ---------------------------------------------------------------------------


def _regra_c16(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """C16: energia cortada por restrição de operação acima de um limiar da energia estimada."""
    r = (res.renovavel.get("restricao") or {}).get("resumo") or {}
    pct = r.get("pct_estimada", float("nan"))
    if not (pct >= LIMIAR_CONCLUSAO_ENERGIA_CORTADA_PCT):
        return []
    return [_item("pontos_atencao", "C16", (
        f"Energia cortada por restrição de operação de {fmt_num(r['energia_cortada_mwh'], 0)} MWh, {fmt_pct(pct)} da "
        f"energia estimada nas semi-horas com a marca de restrição"), ["energia_cortada"])]


def _regra_c17(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """C17: recurso (vento ou irradiância) marcado como inválido em parte relevante das semi-horas da usina."""
    rec = res.renovavel.get("recurso") or {}
    r = rec.get("resumo") or {}
    pct = r.get("pct_invalidas", float("nan"))
    if not (pct >= LIMIAR_CONCLUSAO_RECURSO_INVALIDO_PCT):
        return []
    return [_item("verificar_campo", "C17", (
        f"Medição de {rec['grandeza']} marcada como inválida pelo ONS em {fmt_int(r['semi_horas_invalidas'])} das "
        f"{fmt_int(r['semi_horas'])} semi-horas da usina ({fmt_pct(pct)})"), ["recurso_geracao"])]


def _regra_c18(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """C18: fator de capacidade publicado da usina, num ano completo, abaixo da razão garantia física ÷ potência."""
    p = perfil_ativo().parametros
    fc = res.renovavel.get("fator_capacidade") or {}
    anual = fc.get("anual")
    if anual is None or not len(anual) or not p.garantia_fisica_mwmed:
        return []
    referencia = _pct(p.garantia_fisica_mwmed, p.potencia_instalada_mw)
    abaixo = anual[(anual["nivel"] == "usina") & ~anual["ano_parcial"].astype(bool)
                   & (anual["fator_capacidade_pct"] < referencia)]
    if abaixo.empty:
        return []
    anos = [f"{fmt_pct(r.fator_capacidade_pct)} em {int(r.periodo)}" for r in abaixo.itertuples()]
    return [_item("pontos_atencao", "C18", (
        f"Fator de capacidade publicado pelo ONS de {fmt_lista(anos)}, abaixo da razão entre a garantia física e a "
        f"potência instalada ({fmt_pct(referencia)})"), ["fator_capacidade"])]


def _regra_c19(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """C19: desvio médio absoluto entre a geração programada e a verificada da usina acima de um limiar."""
    prog = res.renovavel.get("programacao") or {}
    pct = prog.get("desvio_medio_absoluto_pct", float("nan"))
    if prog.get("nivel") != "usina" or not (pct >= LIMIAR_CONCLUSAO_DESVIO_PROGRAMACAO_PCT):
        return []
    return [_item("confirmar_agente", "C19", (
        f"Diferença entre a geração programada pelo ONS e a verificada da usina, com desvio médio absoluto de "
        f"{fmt_num(prog['desvio_medio_absoluto_mw'], 1)} MW ({fmt_pct(pct)} da potência instalada) em "
        f"{fmt_int(prog['horas'])} h"), ["programacao_comum"])]


# ---------------------------------------------------------------------------
# Hidrelétricas e térmicas: taxas operativas × oficiais (spec das Análises, FR-063)
# ---------------------------------------------------------------------------


def _regra_c20(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """C20: taxa operativa do mês mais recente a pelo menos o limiar da oficial; cita só as taxas que diferem."""
    c = (res.ons or {}).get("taxas_operativas")
    if not c:
        return []
    partes = [f"{nome} operativa de {fmt_pct(c[f'{t}_oper_pct'], 2)} e oficial de {fmt_pct(c[f'{t}_pct'], 2)} "
              f"(diferença de {fmt_pp(c[f'dif_{t}_pp'], 2)})"
              for t, nome in (("teifa", "TEIFa"), ("teip", "TEIP"))
              if abs(c[f"dif_{t}_pp"]) >= LIMIAR_DIFERENCA_TAXAS_OPERATIVAS_PP - 1e-9]  # NaN não dispara
    if not partes:
        return []
    return [_item("confirmar_agente", "C20", (
        f"Motivo da diferença entre as taxas operativas e as oficiais do ONS em {fmt_mes_ano(c['mes'])}: "
        + "; ".join(partes)), ["indicadores_ons"])]


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RegraConclusao:
    """Regra do catálogo da conclusão (data-model das Análises, seção 3.11; plano das Análises, D18).

    ``funcao`` é a regra de hoje, sobre a base de EVT (None nas regras só das usinas sem EVT, C12 em diante);
    ``funcao_comum``, quando há, a regra sobre a base horária comum e as bases do tipo das usinas sem EVT, avaliada só com alguma das ``bases_comuns`` no nível da usina (e com o IP e a TEIF de
    referência no perfil, quando ``exige_referencias``). ``descricao`` é o texto da nota da conclusão das usinas sem
    EVT, com os limiares.
    """

    codigo: str
    tipos: Tuple[str, ...]
    listas: Tuple[str, ...]
    funcao: Optional[Callable[[ResultadosAnalise], List[Dict[str, Any]]]]
    secoes: Tuple[str, ...]
    limiares: Tuple[str, ...] = ()
    nivel_exigido: str = "usina"
    periodo_minimo_meses: Optional[int] = None
    funcao_comum: Optional[Callable[[ResultadosAnalise], List[Dict[str, Any]]]] = None
    bases_comuns: Tuple[str, ...] = ()
    exige_referencias: bool = False
    descricao: Optional[Callable[[], str]] = None
    exige_garantia_fisica: bool = False


_COM_DISPONIBILIDADE = HIDRELETRICAS + TERMICAS

CATALOGO_CONCLUSAO: Tuple[RegraConclusao, ...] = (
    RegraConclusao("C1", HIDRELETRICAS, ("pontos_atencao", "confirmar_agente", "verificar_campo"), _regra_c1,
                   ("eventos", "programacao"), ("LIMIAR_CONCLUSAO_EVT_PARADA_PCT", "LIMIAR_CONCLUSAO_PROGRAMACAO_ZERO_PCT",
                                                "LIMIAR_GERACAO_PARADA_MW")),
    RegraConclusao("C2", _COM_DISPONIBILIDADE, ("possiveis_problemas", "confirmar_agente", "verificar_campo"), _regra_c2,
                   ("indicadores_ons",), ("LIMIAR_CONCLUSAO_PARTICIPACAO_TEIFA", "LIMIAR_CONCLUSAO_MESES_LIMITACAO_PCT"),
                   funcao_comum=_regra_c2, bases_comuns=("indicadores",),
                   descricao=lambda: (f"C2 unidade com limitação forçada de potência em ≥ "
                                      f"{fmt_pct(LIMIAR_CONCLUSAO_MESES_LIMITACAO_PCT, 0)} dos meses ou, com a TEIF de "
                                      "referência no perfil, com ≥ 2/3 da TEIFa acima dela")),
    RegraConclusao("C3", HIDRELETRICAS, ("pontos_atencao",), _regra_c3, ("hidrologia",),
                   ("LIMIAR_CONCLUSAO_AFLUENCIA_ENGOLIMENTO_PCT",)),
    RegraConclusao("C4", HIDRELETRICAS, ("pontos_atencao",), _regra_c4, ("perfil_horario",), ("RAZAO_DIURNA_RELEVANTE",)),
    RegraConclusao("C5", _COM_DISPONIBILIDADE, ("pontos_atencao",), _regra_c5, ("indicadores_anuais", "indicadores_ons"),
                   funcao_comum=_regra_c5_comum, bases_comuns=("disponibilidade", "indicadores"),
                   exige_referencias=True,
                   descricao=lambda: "C5 disponibilidade operacional, DISPF ou taxas piores que as referências do perfil"),
    RegraConclusao("C6", HIDRELETRICAS, ("possiveis_problemas", "confirmar_agente", "verificar_campo"), _regra_c6,
                   ("programacao",), ("LIMIAR_DESVIO_PROGRAMACAO_MW",)),
    RegraConclusao("C7", HIDRELETRICAS, ("possiveis_problemas", "confirmar_agente"), _regra_c7,
                   ("disponibilidade_sincronizada", "indicadores_ons", "qualidade"),
                   ("LIMIAR_CONCLUSAO_DIFERENCA_RESERVA_GWH", "LIMIAR_CONCLUSAO_R7_HORAS")),
    RegraConclusao("C8", _COM_DISPONIBILIDADE, ("possiveis_problemas", "confirmar_agente"), _regra_c8, ("qualidade",),
                   ("LIMIAR_CONCLUSAO_R7_HORAS",), funcao_comum=_regra_c8_comum, bases_comuns=("disponibilidade",),
                   descricao=lambda: (f"C8 geração acima da disponibilidade declarada em ≥ "
                                      f"{fmt_int(LIMIAR_CONCLUSAO_R7_HORAS)} h")),
    RegraConclusao("C9", HIDRELETRICAS, ("pontos_atencao",), _regra_c9, ("indicadores_anuais",)),
    RegraConclusao("C10", _COM_DISPONIBILIDADE, ("confirmar_agente", "verificar_campo"), _regra_c10,
                   ("disponibilidade_geracao", "indicadores_ons"),
                   ("LIMIAR_CONCLUSAO_INDISPONIBILIDADE_DIAS", "LIMIAR_CONCLUSAO_PROGRAMADA_UG_PCT"),
                   funcao_comum=_regra_c10_comum, bases_comuns=("disponibilidade", "indicadores"),
                   descricao=lambda: (f"C10 indisponibilidade total ≥ {fmt_int(LIMIAR_CONCLUSAO_INDISPONIBILIDADE_DIAS)} "
                                      f"dias, ou programada ≥ {fmt_pct(LIMIAR_CONCLUSAO_PROGRAMADA_UG_PCT, 0)} numa "
                                      "unidade num ano completo")),
    RegraConclusao("C11", HIDRELETRICAS, ("verificar_campo",), _regra_c11, ("hidrologia", "qualidade"),
                   ("LIMIAR_CONCLUSAO_R9_HORAS",)),
    # Térmicas: limiares iniciais em regras.py, calibrados na UTE William Arjona
    RegraConclusao("C12", TERMICAS, ("possiveis_problemas", "confirmar_agente"), None, ("atendimento_despacho",),
                   ("LIMIAR_DESVIO_DESPACHO_MW", "LIMIAR_CONCLUSAO_DESPACHO_ABAIXO_HORAS"), funcao_comum=_regra_c12,
                   bases_comuns=("despacho",),
                   descricao=lambda: (f"C12 geração verificada mais de {fmt_num(LIMIAR_DESVIO_DESPACHO_MW, 0)} MW abaixo "
                                      f"da programada em ≥ {fmt_int(LIMIAR_CONCLUSAO_DESPACHO_ABAIXO_HORAS)} h")),
    RegraConclusao("C13", TERMICAS, ("confirmar_agente",), None, ("disponivel_sem_despacho",),
                   ("LIMIAR_CONCLUSAO_DISPONIVEL_CVU_HORAS",), funcao_comum=_regra_c13, bases_comuns=("cvu_cmo",),
                   descricao=lambda: (f"C13 disponível sem despacho em ≥ {fmt_int(LIMIAR_CONCLUSAO_DISPONIVEL_CVU_HORAS)} h "
                                      "nas semanas com o CVU de alguma unidade abaixo do CMO")),
    RegraConclusao("C14", TERMICAS, ("pontos_atencao",), None, ("despacho_motivo",),
                   ("LIMIAR_CONCLUSAO_INFLEXIBILIDADE_PCT",), funcao_comum=_regra_c14, bases_comuns=("despacho",),
                   descricao=lambda: (f"C14 inflexibilidade programada não verificada ≥ "
                                      f"{fmt_pct(LIMIAR_CONCLUSAO_INFLEXIBILIDADE_PCT, 0)} da programada")),
    RegraConclusao("C15", TERMICAS, ("confirmar_agente",), None, ("atendimento_despacho",),
                   ("LIMIAR_DESVIO_DESPACHO_MW", "LIMIAR_CONCLUSAO_SEM_PROGRAMACAO_HORAS"), funcao_comum=_regra_c15,
                   bases_comuns=("despacho",),
                   descricao=lambda: (f"C15 geração mais de {fmt_num(LIMIAR_DESVIO_DESPACHO_MW, 0)} MW acima da "
                                      f"programada, sem programação, em ≥ "
                                      f"{fmt_int(LIMIAR_CONCLUSAO_SEM_PROGRAMACAO_HORAS)} h")),
    # Eólicas e solares: limiares iniciais em regras.py, calibrados na Seriemas 1 e na Praia Formosa
    RegraConclusao("C16", RENOVAVEIS, ("pontos_atencao",), None, ("energia_cortada",),
                   ("LIMIAR_CONCLUSAO_ENERGIA_CORTADA_PCT",), funcao_comum=_regra_c16, bases_comuns=("restricao",),
                   descricao=lambda: (f"C16 energia cortada por restrição de operação ≥ "
                                      f"{fmt_pct(LIMIAR_CONCLUSAO_ENERGIA_CORTADA_PCT, 0)} da energia estimada")),
    RegraConclusao("C17", RENOVAVEIS, ("verificar_campo",), None, ("recurso_geracao",),
                   ("LIMIAR_CONCLUSAO_RECURSO_INVALIDO_PCT",), funcao_comum=_regra_c17, bases_comuns=("recurso",),
                   descricao=lambda: (f"C17 recurso (vento ou irradiância) inválido em ≥ "
                                      f"{fmt_pct(LIMIAR_CONCLUSAO_RECURSO_INVALIDO_PCT, 0)} das semi-horas")),
    RegraConclusao("C18", RENOVAVEIS, ("pontos_atencao",), None, ("fator_capacidade",), (), periodo_minimo_meses=12,
                   funcao_comum=_regra_c18, bases_comuns=("fator_capacidade",), exige_garantia_fisica=True,
                   descricao=lambda: ("C18 fator de capacidade publicado da usina, num ano completo, abaixo da razão "
                                      "entre a garantia física e a potência instalada")),
    RegraConclusao("C19", RENOVAVEIS, ("confirmar_agente",), None, ("programacao_comum",),
                   ("LIMIAR_CONCLUSAO_DESVIO_PROGRAMACAO_PCT",), funcao_comum=_regra_c19,
                   bases_comuns=("programacao",),
                   descricao=lambda: (f"C19 desvio médio absoluto entre a geração programada e a verificada ≥ "
                                      f"{fmt_pct(LIMIAR_CONCLUSAO_DESVIO_PROGRAMACAO_PCT, 0)} da potência instalada")),
    # Spec das Análises, FR-063: nas duas trilhas (com e sem EVT)
    RegraConclusao("C20", _COM_DISPONIBILIDADE, ("confirmar_agente",), _regra_c20, ("indicadores_ons",),
                   ("LIMIAR_DIFERENCA_TAXAS_OPERATIVAS_PP",), funcao_comum=_regra_c20,
                   bases_comuns=("taxas_operativas",),
                   descricao=lambda: (f"C20 TEIFa ou TEIP operativa do mês mais recente a "
                                      f"{fmt_num(LIMIAR_DIFERENCA_TAXAS_OPERATIVAS_PP, 0)} p.p. ou mais da oficial")),
)
# As funções do caminho da EVT, na ordem do catálogo: C1 a C11 e a C20 (spec das Análises, FR-063)
REGRAS_CONCLUSAO = tuple(r.funcao for r in CATALOGO_CONCLUSAO if r.funcao is not None)

NOMES_BASES = {"disponibilidade": "a Disponibilidade por usina", "indicadores": "os Indicadores de desempenho do ONS",
               "despacho": "a Geração térmica por motivo de despacho",
               "cvu_cmo": "o CVU e o CMO cruzados com a disponibilidade e o despacho",
               "restricao": "a Restrição com detalhe", "recurso": "o recurso válido da Restrição com detalhe",
               "fator_capacidade": "o Fator de capacidade", "programacao": "a Programação diária",
               "taxas_operativas": "as Taxas TEIFa Oper e TEIP Oper"}


def _bases_da_usina(res: ResultadosAnalise) -> Dict[str, bool]:
    """Bases das regras presentes no nível da usina (a disponibilidade, os indicadores e o despacho são sempre da
    usina; o CMO é contexto do subsistema)."""
    t = getattr(res, "termica", None) or {}
    r = getattr(res, "renovavel", None) or {}
    fc = r.get("fator_capacidade") or {}
    return {"disponibilidade": bool(res.comum.get("disponibilidade")), "indicadores": bool(res.ons),
            "despacho": bool(t), "cvu_cmo": bool(t.get("cvu_cmo")) and bool(t.get("disponivel_sem_despacho")),
            # a restrição com detalhe é sempre da usina; o fator de capacidade e a programação, só no nível dela
            "restricao": bool(r.get("restricao")), "recurso": bool(r.get("recurso")),
            "fator_capacidade": fc.get("nivel") == "usina",
            "programacao": (r.get("programacao") or {}).get("nivel") == "usina",
            "taxas_operativas": bool((res.ons or {}).get("taxas_operativas"))}


def _motivo(regra: RegraConclusao, res: ResultadosAnalise) -> Optional[str]:
    """Motivo pelo qual a regra não é avaliada na usina sem EVT; None quando é avaliada."""
    if regra.funcao_comum is None:
        return "regra da base de EVT, que a usina não tem"
    presentes = _bases_da_usina(res)
    if not any(presentes[b] for b in regra.bases_comuns):
        nomes = [NOMES_BASES[b] for b in regra.bases_comuns]
        return f"sem {' nem '.join(nomes)} no nível da usina"
    if regra.exige_referencias and _referencias() is None:
        return "sem IP e TEIF de referência no perfil da usina"
    if regra.exige_garantia_fisica and not perfil_ativo().parametros.garantia_fisica_mwmed:
        return "sem a garantia física no perfil da usina"
    meses = int((res.cobertura or {}).get("meses_distintos") or 0)
    if regra.periodo_minimo_meses and meses < regra.periodo_minimo_meses:
        return f"a série tem {fmt_int(meses)} meses distintos, menos que o período mínimo de {regra.periodo_minimo_meses}"
    return None


def regras_do_tipo(res: ResultadosAnalise) -> List[RegraConclusao]:
    return [r for r in CATALOGO_CONCLUSAO if res.tipo in r.tipos]


def regras_omitidas(res: ResultadosAnalise) -> List[Dict[str, str]]:
    """Regras do tipo não avaliadas na usina sem EVT, com o motivo (``omitidos``); vazia nas hidrelétricas com EVT."""
    if not sem_evt(res):
        return []
    return [{"item": r.codigo, "tipo": "regra", "motivo": motivo} for r in regras_do_tipo(res)
            if (motivo := _motivo(r, res)) is not None]


def _avaliar(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    if not sem_evt(res):
        return [item for regra in REGRAS_CONCLUSAO for item in regra(res)]
    itens = []
    for regra in regras_do_tipo(res):
        if _motivo(regra, res) is None:
            for item in regra.funcao_comum(res):
                itens.append({**item, "secoes": [SECOES_SEM_EVT.get(s, s) for s in item["secoes"]]})
    return itens


def frase_sem_itens(res: ResultadosAnalise) -> str:
    """Frase da conclusão sem itens: a de hoje nas hidrelétricas com EVT; nas usinas sem EVT, o motivo (D18, D22)."""
    if not sem_evt(res):
        return FRASE_CONCLUSAO_VAZIA
    regras = regras_do_tipo(res)
    if not regras:
        return f"Sem itens: o catálogo da conclusão ainda não tem regras para usinas do tipo {res.tipo}."
    if len(regras_omitidas(res)) < len(regras):
        return FRASE_CONCLUSAO_VAZIA
    g = res.niveis.get("geracao", {})
    if "conjunto" in str(g.get("nivel", "")):
        nome = g.get("nome") or g.get("identificador_conjunto") or ""
        return ("Sem itens: as regras da conclusão usam só dados do nível da usina, e o ONS publica para esta usina só "
                f"os números do conjunto {nome}; os motivos estão nas notas metodológicas.")
    return (f"Sem itens: nenhuma regra da conclusão do tipo {res.tipo} tem base para a usina; os motivos estão nas "
            "notas metodológicas.")


def montar_conclusao(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """Itens da conclusão, gerados pelas regras do catálogo a partir dos resultados (spec das Análises, US4).

    Cada item tem lista, ordem (na ordem do catálogo, dentro da lista), regra, texto de uma frase sem ponto final e as
    chaves das seções de origem. Uma regra cujas condições ou bases faltam não gera item.
    """
    itens = _avaliar(res)
    ordem_lista = {chave: i for i, (chave, _) in enumerate(LISTAS_CONCLUSAO)}
    itens.sort(key=lambda i: (ordem_lista[i["lista"]], int(i["regra"][1:])))
    contagem: Dict[str, int] = {}
    saida = []
    for item in itens:
        contagem[item["lista"]] = contagem.get(item["lista"], 0) + 1
        saida.append({"lista": item["lista"], "ordem": contagem[item["lista"]], "regra": item["regra"],
                      "texto": item["texto"], "secoes": item["secoes"]})
    return saida
