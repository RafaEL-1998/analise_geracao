"""Conclusão do relatório: regras C1 a C11, que apontam indícios sem afirmar causa (spec das Análises, FR-045)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from src.analises.comum import _pct, _rotulo_ano, _rotulo_janela
from src.analises.hidrologia import ATE_UMA_UNIDADE, entre_unidades
from src.analises.indicadores import DESCRICAO_PARCELA
from src.analises.resultados import ResultadosAnalise
from src.comum.formatacao import fmt_data, fmt_data_hora, fmt_int, fmt_lista, fmt_mes_ano, fmt_num, fmt_pct, plural
from src.comum.perfil import perfil_ativo
from src.comum.regras import (
    HORAS_DIURNAS,
    LIMIAR_CONCLUSAO_AFLUENCIA_ENGOLIMENTO_PCT,
    LIMIAR_CONCLUSAO_DIFERENCA_RESERVA_GWH,
    LIMIAR_CONCLUSAO_EVT_PARADA_PCT,
    LIMIAR_CONCLUSAO_INDISPONIBILIDADE_DIAS,
    LIMIAR_CONCLUSAO_MESES_LIMITACAO_PCT,
    LIMIAR_CONCLUSAO_PARTICIPACAO_TEIFA,
    LIMIAR_CONCLUSAO_PROGRAMACAO_ZERO_PCT,
    LIMIAR_CONCLUSAO_PROGRAMADA_UG_PCT,
    LIMIAR_CONCLUSAO_R7_HORAS,
    LIMIAR_CONCLUSAO_R9_HORAS,
    LIMIAR_DESVIO_PROGRAMACAO_MW,
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
    teifa_acima = bool(t) and t["teifa_pct"] > perfil_ativo().parametros.teif_referencia * 100.0
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


def _regra_c10(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """Indisponibilidade longa: total ≥ 30 dias, ou programada ≥ 20 % numa unidade num ano completo."""
    partes: List[str] = []
    secoes: List[str] = []
    anos: set = set()
    eventos = res.eventos_indisponibilidade_total
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
            grupos = [f"{' e '.join(f'da UG{int(u)}' for u in sorted(g['ug']))} em {int(ano)}"
                      for ano, g in sel.groupby("ano")]
            partes.append(f"das paradas programadas longas {fmt_lista(grupos)}")
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


REGRAS_CONCLUSAO = (_regra_c1, _regra_c2, _regra_c3, _regra_c4, _regra_c5, _regra_c6, _regra_c7, _regra_c8, _regra_c9,
                    _regra_c10, _regra_c11)


def montar_conclusao(res: ResultadosAnalise) -> List[Dict[str, Any]]:
    """Itens da conclusão, gerados pelas regras C1 a C11 a partir dos resultados (spec das Análises, US4).

    Cada item tem lista, ordem (na ordem do catálogo, dentro da lista), regra, texto de uma frase sem ponto final e as
    chaves das seções de origem. Uma regra cujas condições ou bases faltam não gera item.
    """
    itens = [item for regra in REGRAS_CONCLUSAO for item in regra(res)]
    ordem_lista = {chave: i for i, (chave, _) in enumerate(LISTAS_CONCLUSAO)}
    itens.sort(key=lambda i: (ordem_lista[i["lista"]], int(i["regra"][1:])))
    contagem: Dict[str, int] = {}
    saida = []
    for item in itens:
        contagem[item["lista"]] = contagem.get(item["lista"], 0) + 1
        saida.append({"lista": item["lista"], "ordem": contagem[item["lista"]], "regra": item["regra"],
                      "texto": item["texto"], "secoes": item["secoes"]})
    return saida
