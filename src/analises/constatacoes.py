"""Constatações: títulos fixos e textos montados só a partir dos resultados, do perfil e das regras gerais (spec das Análises, FR-043 e FR-044)."""

from __future__ import annotations

from typing import List, Optional, Tuple

import pandas as pd

from src.analises.comum import _data_obtencao_texto, _pct, _rotulo_ano, _rotulo_janela
from src.analises.hidrologia import (
    ACIMA_ENGOLIMENTO_USINA,
    ATE_UMA_UNIDADE,
    COM_PARADA_EVT,
    DEMAIS_DIAS,
    entre_unidades,
    unidades_por_extenso,
    SEM_DADO_HIDROLOGICO,
)
from src.analises.indicadores import DESCRICAO_PARCELA
from src.analises.resultados import ResultadosAnalise
from src.comum.formatacao import fmt_data, fmt_data_hora, fmt_int, fmt_lista, fmt_mes_ano, fmt_num, fmt_pct, plural
from src.comum.perfil import perfil_ativo
from src.comum.regras import (
    DURACAO_MINIMA_EVENTO_RELATORIO_H,
    HORAS_DIURNAS,
    HORAS_NOTURNAS,
    JANELA_TAXAS_MESES,
    LIMIAR_DESVIO_PROGRAMACAO_MW,
    LIMIAR_GERACAO_PARADA_MW,
    RAZAO_DIURNA_RELEVANTE,
    TOLERANCIA_DIVERGENCIA_HORAS,
    TOLERANCIA_REPRODUCAO_TAXAS_PP,
)
from src.tratamento.validacao import COLUNA_QUALIDADE


MESES_MAIO_A_OUTUBRO: List[int] = [5, 6, 7, 8, 9, 10]
MESES_JANEIRO_A_ABRIL: List[int] = [1, 2, 3, 4]


def _divergencia_geracao(res: "ResultadosAnalise") -> bool:
    c = res.geracao_oficial.get("conferencia", {})
    return bool(c) and (c["divergentes"] > 0 or c["so_ons_geracao"] > 0 or c["so_base_evt"] > 0)


def _achado_cobertura(res: ResultadosAnalise) -> Tuple[str, str]:
    c = res.cobertura
    faltantes = c["horas_faltantes"]
    if faltantes:
        lista = fmt_lista(fmt_data_hora(t) for t in faltantes[:5]) + ("…" if len(faltantes) > 5 else "")
        txt_faltantes = f", com {fmt_int(len(faltantes))} {plural(len(faltantes), 'hora ausente', 'horas ausentes')} ({lista})"
    else:
        txt_faltantes = ", sem horas ausentes"
    partes = [
        f"A série do ONS para a usina (cod_usina {perfil_ativo().identificacao.cod_usina}) vai de {fmt_data_hora(c['inicio'])} "
        f"a {fmt_data_hora(c['fim'])}: {fmt_int(c['horas_observadas'])} registros horários{txt_faltantes}."
    ]
    arquivos = c.get("arquivos") or {}
    if arquivos.get("sem_registros"):
        n = len(arquivos["sem_registros"])
        partes.append(
            f"{plural(n, 'O arquivo', 'Os arquivos')} de {fmt_lista(arquivos['sem_registros'])} "
            f"não {plural(n, 'contém', 'contêm')} registros da usina."
        )
    if c["inicio"].year > perfil_ativo().usina.inicio_operacao_comercial:
        partes.append(
            f"Como a operação comercial começou em {perfil_ativo().usina.inicio_operacao_comercial}, o período anterior a "
            f"{fmt_data(c['inicio'])} não é coberto por esta fonte."
        )
    parciais = c["por_ano"][c["por_ano"]["ano_parcial"]]
    if len(parciais):
        itens = [f"{int(r.ano)} ({fmt_pct(r.cobertura_pct)} das horas do ano)" for r in parciais.itertuples()]
        partes.append(
            f"{plural(len(itens), 'O ano', 'Os anos')} {fmt_lista(itens)} "
            f"{plural(len(itens), 'é parcial', 'são parciais')}; as comparações entre anos usam apenas anos completos."
        )
    return "Cobertura dos dados", " ".join(partes)


def _achado_disponibilidade(res: ResultadosAnalise) -> Tuple[str, str]:
    g = res.globais
    anuais = res.indicadores_anuais
    desvio = g["desvio_disponibilidade_referencia_pp"]
    texto = (
        f"A disponibilidade média declarada foi de {fmt_num(g['disponibilidade_media_mwmed'], 1)} MW "
        f"({fmt_pct(g['disponibilidade_relativa_pct'])} da potência instalada), {fmt_num(abs(desvio), 1)} p.p. "
        f"{'abaixo' if desvio < 0 else 'acima'} da disponibilidade de referência da garantia física "
        f"({fmt_pct(g['disponibilidade_referencia_pct'])})."
    )
    completos = anuais[~anuais["ano_parcial"]]
    if len(completos):
        abaixo = completos[completos["desvio_disponibilidade_referencia_pp"] < 0]
        if len(abaixo):
            itens = [f"{int(r.ano)} ({fmt_pct(r.disponibilidade_relativa_pct)})" for r in abaixo.itertuples()]
            texto += f" Entre os anos completos, ficaram abaixo da referência: {fmt_lista(itens)}."
        else:
            texto += " Nenhum ano completo ficou abaixo da referência."
    return "Disponibilidade", texto


def _acima_abaixo(valor: float, referencia: float) -> str:
    return "abaixo" if valor < referencia else "acima"


def _achado_indicadores_ons(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    o = res.ons
    p = o.get("disp_periodo")
    if not p:
        return None
    g = res.globais
    referencia = perfil_ativo().disponibilidade_referencia * 100.0
    desvio = p["dispf_pct"] - referencia
    texto = (
        f"Pelo indicador de disponibilidade das unidades geradoras apurado pelo ONS (DISPF, Submódulo 9.2 dos "
        f"Procedimentos de Rede), a disponibilidade média das {p['unidades']} unidades de {fmt_mes_ano(p['mes_inicio'])} "
        f"a {fmt_mes_ano(p['mes_fim'])} foi de {fmt_pct(p['dispf_pct'])} (indisponibilidade programada de "
        f"{fmt_pct(p['indisppf_pct'])} e forçada de {fmt_pct(p['indispff_pct'])}), {fmt_num(abs(desvio), 1)} p.p. "
        f"{_acima_abaixo(p['dispf_pct'], referencia)} da disponibilidade de referência da garantia física "
        f"({fmt_pct(referencia)}); a disponibilidade declarada no conjunto de EVT foi de "
        f"{fmt_pct(g['disponibilidade_relativa_pct'])}. As duas medidas são diferentes: o DISPF conta o tempo em que cada "
        f"unidade esteve disponível, sem descontar a operação com potência limitada; a disponibilidade declarada é a "
        f"potência que a usina informou poder gerar a cada hora."
    )
    anual = o.get("disp_anual", pd.DataFrame())
    completos = anual[~anual["ano_parcial"]] if len(anual) else anual
    if len(completos):
        abaixo = completos[completos["desvio_dispf_referencia_pp"] < 0]
        if len(abaixo):
            itens = [f"{int(r.ano)} ({fmt_pct(r.dispf_pct)})" for r in abaixo.itertuples()]
            texto += f" Pelo DISPF, ficaram abaixo da referência os anos completos {fmt_lista(itens)}."
        else:
            texto += " Pelo DISPF, nenhum ano completo ficou abaixo da referência."
    t = o.get("taxa_ultima")
    if t:
        texto += (
            f" A TEIFa apurada pelo ONS para {fmt_mes_ano(t['mes'])} (janela de {JANELA_TAXAS_MESES} meses) é de "
            f"{fmt_pct(t['teifa_pct'], 2)}, {_acima_abaixo(t['teifa_pct'], perfil_ativo().parametros.teif_referencia * 100)} da TEIF de referência "
            f"({fmt_pct(perfil_ativo().parametros.teif_referencia * 100, 3)}), e a TEIP, de {fmt_pct(t['teip_pct'], 2)}, "
            f"{_acima_abaixo(t['teip_pct'], perfil_ativo().parametros.ip_referencia * 100)} do IP de referência ({fmt_pct(perfil_ativo().parametros.ip_referencia * 100, 3)}). "
            f"Com as taxas apuradas, (1 − TEIFa) × (1 − TEIP) = {fmt_pct(t['disponibilidade_verificada_pct'], 2)}, "
            f"contra {fmt_pct(referencia, 2)} de referência."
        )
    return "Indicadores oficiais de disponibilidade (ONS)", texto


def _horas_por_ano_texto(horas_anual: pd.DataFrame, ug: int, coluna: str) -> str:
    sel = horas_anual[horas_anual["ug"] == ug]
    return "; ".join(
        f"{int(r.ano)}{' (parcial)' if r.ano_parcial else ''}: {fmt_int(getattr(r, coluna))} h" for r in sel.itertuples()
    )


def _achado_estados_operativos(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    o = res.ons
    hp = o.get("horas_periodo")
    if not hp:
        return None
    horas = o["horas_mensal"]
    horas_anual = o["horas_anual"]
    partes = [
        f"O ONS publica as horas mensais de cada unidade por estado operativo ({fmt_mes_ano(hp['mes_inicio'])} a "
        f"{fmt_mes_ano(hp['mes_fim'])} no período da base)."
    ]
    if hp["identidade_fora"]:
        partes.append(
            f"Em {fmt_int(hp['identidade_fora'])} de {fmt_int(hp['meses_unidade'])} meses-unidade as parcelas não somam as "
            "horas do período."
        )
    rr = o.get("recalculo_resumo")
    if rr and rr["meses"]:
        dif = rr["diferenca_maxima_pp"]
        txt_dif = "inferior a 0,0001 p.p." if dif < 1e-4 else f"de {fmt_num(dif, 4)} p.p."
        reproduzidos = rr.get("reproduzidos", rr["meses"])
        if reproduzidos == rr["meses"]:
            partes.append(
                f"Com a fórmula das notas metodológicas, essas horas reproduzem a TEIFa e a TEIP publicadas nos "
                f"{fmt_int(rr['meses'])} meses com janela de {JANELA_TAXAS_MESES} meses completa (diferença máxima {txt_dif})."
            )
        else:
            partes.append(
                f"Com a fórmula das notas metodológicas, essas horas reproduzem a TEIFa e a TEIP publicadas em "
                f"{fmt_int(reproduzidos)} dos {fmt_int(rr['meses'])} meses com janela de {JANELA_TAXAS_MESES} meses "
                f"completa (tolerância de {fmt_num(TOLERANCIA_REPRODUCAO_TAXAS_PP, 3)} p.p.; diferença máxima {txt_dif})."
            )
    dec = o.get("decomposicao")
    t = o.get("taxa_ultima")
    if dec is not None and len(dec) and t:
        teifa = dec[dec["taxa"] == "TEIFa"]
        maior = teifa.loc[teifa["contribuicao_pp"].idxmax()]
        partes.append(
            f"Da TEIFa de {fmt_pct(t['teifa_pct'], 2)} em {fmt_mes_ano(t['mes'])}, {fmt_num(maior['contribuicao_pp'], 2)} p.p. "
            f"({fmt_pct(maior['participacao_pct'], 0)}) vêm de {DESCRICAO_PARCELA[maior['parcela']]} da UG{int(maior['ug'])}; "
            f"sem essa parcela, a TEIFa seria de {fmt_pct(t['teifa_pct'] - maior['contribuicao_pp'], 2)}."
        )
    # Unidade com mais horas equivalentes de limitação forçada
    por_ug = horas.groupby("ug").agg(hedf=("HEDF", "sum"), meses=("mes", "nunique"),
                                     meses_hedf=("HEDF", lambda s: int((s > 0).sum())))
    if por_ug["hedf"].max() > 0:
        ug = int(por_ug["hedf"].idxmax())
        r = por_ug.loc[ug]
        outras = por_ug.drop(index=ug)
        partes.append(
            f"A UG{ug} registrou limitação forçada de potência em {fmt_int(r['meses_hedf'])} dos {fmt_int(r['meses'])} meses, "
            f"somando {fmt_int(r['hedf'])} horas equivalentes"
            + (f" (UG{', UG'.join(str(int(u)) for u in outras.index)}: {fmt_lista(fmt_int(v) + ' h' for v in outras['hedf'])})"
               if len(outras) else "")
            + "."
        )
    ugs = sorted(int(u) for u in horas_anual["ug"].unique())
    partes.append(
        "Horas em reserva desligada (unidade disponível, parada), por ano: "
        + " | ".join(f"UG{u} — {_horas_por_ano_texto(horas_anual, u, 'HRD')}" for u in ugs)
        + "."
    )
    externa = horas.groupby("ug")["HDCE"].sum()
    if externa.sum() > 0:
        partes.append(
            "Desligamentos por causa externa: "
            + fmt_lista(f"UG{int(u)}: {fmt_num(v, 1)} h" for u, v in externa.items())
            + "."
        )
    div = o.get("divergencias", pd.DataFrame())
    if len(div):
        itens = [
            f"{fmt_mes_ano(r.mes)} UG{int(r.ug)}: {fmt_int(r.horas_programadas_indisppf)} h programadas pelo DISPF e "
            f"{fmt_int(r.HDP)} h pelo TEIP"
            for r in div.itertuples()
        ]
        contida = bool(((div["horas_programadas_indisppf"] - div["HDP"]) <= div["HRD"] + TOLERANCIA_DIVERGENCIA_HORAS).all())
        partes.append(
            f"Em {fmt_int(len(div))} {plural(len(div), 'mês-unidade', 'meses-unidade')}, os dois conjuntos do ONS classificam "
            f"o tempo parado de forma diferente ({'; '.join(itens)})"
            + ("; a diferença está contida nas horas que o conjunto do TEIP registra como reserva desligada." if contida else ".")
        )
    partes.append("Os conjuntos informam a duração de cada estado, não a causa nem os eventos individuais de desligamento.")
    return "Estados operativos das unidades geradoras (ONS)", " ".join(partes)


def _achado_indisponibilidade(res: ResultadosAnalise) -> Tuple[str, str]:
    eventos = res.eventos_indisponibilidade_total
    longos = eventos[eventos["duracao_h"] >= DURACAO_MINIMA_EVENTO_RELATORIO_H] if len(eventos) else eventos
    if len(longos):
        maior = longos.loc[longos["duracao_h"].idxmax()]
        n = len(longos)
        texto = (
            f"Houve {n} {plural(n, 'período', 'períodos')} de indisponibilidade total (disponibilidade zero) "
            f"com pelo menos {DURACAO_MINIMA_EVENTO_RELATORIO_H} h, somando {fmt_int(longos['duracao_h'].sum())} h. "
            f"O mais longo foi de {fmt_data_hora(maior['inicio'])} a {fmt_data_hora(maior['fim'])} "
            f"({fmt_int(maior['duracao_h'])} h, cerca de {fmt_int(maior['duracao_h'] / 24)} dias)."
        )
    else:
        texto = f"Não houve período de indisponibilidade total com pelo menos {DURACAO_MINIMA_EVENTO_RELATORIO_H} h."
    anuais = res.indicadores_anuais
    metade = anuais["horas_disponibilidade_ate_metade"]
    if metade.sum() > 0:
        idx = metade.idxmax()
        texto += (
            f" Em {fmt_int(metade.sum())} h a disponibilidade ficou acima de zero e igual ou inferior à metade da "
            f"potência instalada ({fmt_num(perfil_ativo().parametros.potencia_instalada_mw / 2, 0)} MW); o ano com mais horas nessa "
            f"condição foi {int(anuais.loc[idx, 'ano'])} ({fmt_int(metade[idx])} h)."
        )
    return "Indisponibilidades", texto


def _achado_geracao(res: ResultadosAnalise) -> Tuple[str, str]:
    g = res.globais
    anuais = res.indicadores_anuais
    texto = (
        f"A geração média foi de {fmt_num(g['geracao_media_mwmed'], 1)} MWmed (fator de capacidade de "
        f"{fmt_pct(g['fator_capacidade_pct'])}), o equivalente a {fmt_pct(g['geracao_sobre_garantia_fisica_pct'])} "
        f"da garantia física ({fmt_num(perfil_ativo().parametros.garantia_fisica_mwmed, 1)} MWmed)."
    )
    completos = anuais[~anuais["ano_parcial"]]
    if len(completos):
        mn = completos.loc[completos["geracao_sobre_garantia_fisica_pct"].idxmin()]
        mx = completos.loc[completos["geracao_sobre_garantia_fisica_pct"].idxmax()]
        texto += (
            f" Nos anos completos, a razão entre geração média e garantia física variou de "
            f"{fmt_pct(mn['geracao_sobre_garantia_fisica_pct'])} ({int(mn['ano'])}) a "
            f"{fmt_pct(mx['geracao_sobre_garantia_fisica_pct'])} ({int(mx['ano'])})."
        )
    ultimo = anuais.iloc[-1]
    if bool(ultimo["ano_parcial"]):
        texto += f" Em {int(ultimo['ano'])} (parcial), foi de {fmt_pct(ultimo['geracao_sobre_garantia_fisica_pct'])}."
    return "Geração e garantia física", texto


def _achado_evt(res: ResultadosAnalise) -> Tuple[str, str]:
    g = res.globais
    anuais = res.indicadores_anuais
    itens = [
        f"{int(r.ano)}: {fmt_num(r.evt_mwh / 1000, 1)} GWh" + (" (parcial)" if r.ano_parcial else "")
        for r in anuais.itertuples()
    ]
    texto = (
        f"A energia vertida turbinável (EVT) somou {fmt_num(g['evt_mwh'] / 1000, 1)} GWh, o equivalente a "
        f"{fmt_pct(g['indice_evt_pct'])} da soma entre geração e EVT, e ocorreu em {fmt_pct(g['horas_com_evt_pct'])} "
        f"das horas. Nas horas com EVT, a folga média de geração (disponibilidade menos geração) foi de "
        f"{fmt_num(g['folga_media_com_evt_mw'], 1)} MW. Por ano: {'; '.join(itens)}."
    )
    return "Energia vertida turbinável", texto


def _achado_evt_nivel_geracao(res: ResultadosAnalise) -> Tuple[str, str]:
    g = res.globais
    texto = (
        f"Somente {fmt_pct(g['evt_plena_carga_pct'])} da EVT ocorreu com a usina próxima da plena carga "
        f"(geração igual ou superior a {fmt_num(g['limiar_plena_carga_mw'], 1)} MW)."
    )
    if g["horas_evt_acima_folga"] == 0:
        texto += (
            " Em todas as horas, a EVT não ultrapassa a folga de geração: quando a usina gera tudo o que "
            "declarou disponível, a EVT é nula."
        )
    else:
        texto += f" Em {fmt_int(g['horas_evt_acima_folga'])} horas a EVT ultrapassa a folga de geração."
    texto += (
        f" Já {fmt_pct(g['evt_parada_pct'])} da EVT ({fmt_num(g['evt_parada_mwh'] / 1000, 1)} GWh, em "
        f"{fmt_int(g['horas_parada_com_evt'])} h) ocorreu com a usina parada (geração até "
        f"{fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW) e disponibilidade média de "
        f"{fmt_num(g['disponibilidade_media_nas_paradas_mw'], 1)} MW."
    )
    return "EVT e nível de geração", texto


def _achado_paradas(res: ResultadosAnalise) -> Tuple[str, str]:
    anuais = res.indicadores_anuais
    itens = [
        f"{int(r.ano)}: {fmt_int(r.horas_parada_com_evt)} h" + (" (parcial)" if r.ano_parcial else "")
        for r in anuais.itertuples()
    ]
    texto = f"Horas com a usina parada e EVT, por ano: {'; '.join(itens)}."
    if anuais["evt_parada_mwh"].sum() > 0:
        mx = anuais.loc[anuais["evt_parada_mwh"].idxmax()]
        texto += (
            f" O maior volume foi em {int(mx['ano'])}, com {fmt_num(mx['evt_parada_mwh'] / 1000, 1)} GWh de EVT "
            f"nessas horas. A lista completa de eventos está na aba EVENTOS_PARADA_COM_EVT da planilha."
        )
    return "EVT com a usina parada", texto


def _achado_programacao(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    p = res.programacao.get("periodo")
    if not p:
        return None
    n_aus = p["dias_ausentes"]
    texto = (
        f"A programação diária do ONS para a usina cobre de {fmt_data(p['primeiro_dia'])} a {fmt_data(p['ultimo_dia'])} "
        f"no período da base ({fmt_int(p['dias_com_arquivo'])} dias com arquivo; {fmt_int(n_aus)} "
        f"{plural(n_aus, 'dia', 'dias')} sem arquivo no portal, cujas {fmt_int(p['horas_base_sem_programacao'])} horas ficam "
        f"fora do cruzamento). Nas {fmt_int(p['horas_comuns'])} horas comuns, a usina ficou parada com EVT em "
        f"{fmt_int(p['horas_parada_com_evt'])} h; em {fmt_int(p['horas_parada_evt_programacao_zero'])} delas "
        f"({fmt_pct(p['pct_horas_programacao_zero'])}) a programação do ONS era de até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW, "
        f"com disponibilidade declarada média de {fmt_num(p['disponibilidade_media_programacao_zero_mw'], 1)} MW. Essas horas "
        f"somam {fmt_num(p['evt_programacao_zero_mwh'] / 1000, 1)} GWh de EVT ({fmt_pct(p['pct_evt_programacao_zero'])} da EVT "
        f"das horas comuns), e {fmt_pct(p['pct_horas_zero_janela_diurna'])} delas ocorreram na janela das {_rotulo_janela(HORAS_DIURNAS)}."
    )
    maior = p["maior_evento"]
    if p["horas_desvio"] and maior is not None:
        texto += (
            f" Em {fmt_int(p['horas_desvio'])} h a usina ficou parada com programação acima de "
            f"{fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 0)} MW ({fmt_int(p['eventos_desvio'])} "
            f"{plural(p['eventos_desvio'], 'evento', 'eventos')}; o mais longo, de {fmt_data_hora(maior['inicio'])} a "
            f"{fmt_data_hora(maior['fim'])}, durou {fmt_int(maior['duracao_h'])} h com programação média de "
            f"{fmt_num(maior['programacao_media_mw'], 1)} MW)."
        )
    else:
        texto += f" Não houve hora com a usina parada e programação acima de {fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 0)} MW."
    texto += (
        f" Em {fmt_int(p['horas_gerando_programacao_zero'])} h a usina gerou acima de {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW "
        f"com programação de até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW. A correlação horária entre a geração verificada e a "
        f"programada foi de {fmt_num(p['correlacao_geracao_programacao'], 2)}. A programação diária não registra "
        "reprogramações em tempo real nem, para usinas hidráulicas, o motivo da programação."
    )
    return "Programação diária do ONS", texto


def _achado_disponibilidade_sincronizada(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    d = res.disponibilidade
    if not d:
        return None
    r, c = d["resumo"], d["conferencia"]
    texto = (
        f"A disponibilidade horária publicada pelo ONS para a usina cobre de {fmt_data(r['inicio'])} a "
        f"{fmt_data(r['fim'])} ({fmt_int(r['horas'])} horas). A disponibilidade operacional coincide com a disponibilidade "
        f"declarada da base de EVT em {fmt_int(c['coincidentes'])} das {fmt_int(c['horas_comuns'])} horas comuns "
        f"({fmt_pct(c['pct_coincidentes'])}; diferença de até {fmt_num(c['tolerancia_mw'], 2)} MW)"
    )
    texto += "." if not c["divergentes"] else f"; {fmt_int(c['divergentes'])} {plural(c['divergentes'], 'hora diverge', 'horas divergem')}."
    if r["horas_paradas"]:
        texto += (
            f" Nas {fmt_int(r['horas_paradas'])} horas comuns com a usina parada, nenhuma unidade estava sincronizada à rede "
            f"em {fmt_int(r['horas_paradas_sem_sincronizacao'])} ({fmt_pct(r['pct_paradas_sem_sincronizacao'])}); nas outras "
            f"{fmt_int(r['horas_paradas_sincronizadas'])} havia unidade sincronizada sem gerar acima de "
            f"{fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW."
        )
    if r["horas_parada_evt"]:
        texto += (
            f" Das {fmt_int(r['horas_parada_evt'])} horas paradas com EVT, {fmt_int(r['horas_parada_evt_sem_sincronizacao'])} "
            "foram com as unidades desligadas da rede"
        )
        if r["horas_parada_evt_programacao_zero"]:
            texto += (
                f"; no período da programação diária, {fmt_int(r['horas_parada_evt_programacao_zero_sem_sincronizacao'])} "
                f"das {fmt_int(r['horas_parada_evt_programacao_zero'])} horas paradas com EVT e programação de até "
                f"{fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW tinham as unidades desligadas"
            )
        texto += "."
    anual = d["anual"]
    completos = anual[~anual["ano_parcial"]]
    if len(completos) >= 2:
        menor = completos.loc[completos["disp_sincronizada_media_mw"].idxmin()]
        maior = completos.loc[completos["disp_sincronizada_media_mw"].idxmax()]
        texto += (
            f" Nos anos completos, a disponibilidade sincronizada média variou de {fmt_num(menor['disp_sincronizada_media_mw'], 1)} MW "
            f"({menor['periodo']}) a {fmt_num(maior['disp_sincronizada_media_mw'], 1)} MW ({maior['periodo']}), com a "
            f"operacional entre {fmt_num(completos['disp_operacional_media_mw'].min(), 1)} e "
            f"{fmt_num(completos['disp_operacional_media_mw'].max(), 1)} MW"
        )
        ultimo = anual.iloc[-1]
        if bool(ultimo["ano_parcial"]) and ultimo["periodo"] not in set(completos["periodo"]):
            texto += (f"; em {_rotulo_ano(ultimo['periodo'], True)}, a sincronizada média foi de "
                      f"{fmt_num(ultimo['disp_sincronizada_media_mw'], 1)} MW")
        texto += "."
    comparaveis = anual.dropna(subset=["reserva_desligada_teif_mwh"])
    if len(comparaveis):
        iguais = comparaveis[comparaveis["diferenca_mwh"].abs() <= 100]
        diferentes = comparaveis[comparaveis["diferenca_mwh"].abs() > 100]
        texto += (
            f" A capacidade disponível não sincronizada coincide com a reserva desligada apurada nos parâmetros TEIFa/TEIP "
            f"(horas em reserva desligada × potência) em {fmt_int(len(iguais))} dos {fmt_int(len(comparaveis))} anos com as "
            "duas apurações (diferença de até 0,1 GWh)"
        )
        if len(diferentes):
            texto += "; diverge em " + fmt_lista(
                f"{_rotulo_ano(r.periodo, r.ano_parcial)} ({'+' if r.diferenca_mwh > 0 else '−'}"
                f"{fmt_num(abs(r.diferenca_mwh) / 1000, 1)} GWh)"
                for r in diferentes.itertuples()
            ) + " (diferença = não sincronizada − reserva desligada); a causa da diferença não está nos dados abertos"
        texto += "."
    texto += " A sincronização mostra se as unidades estavam ligadas à rede, mas não o motivo da parada."
    return "Disponibilidade sincronizada", texto


def texto_conferencia_geracao(res: ResultadosAnalise) -> str:
    """Resultado da conferência da geração com a série oficial (seção e, havendo divergência, constatação)."""
    g = res.geracao_oficial
    r, c = g["resumo"], g["conferencia"]
    periodo = f"de {fmt_data(r['inicio'])} a {fmt_data(r['fim'])}"
    energia = (f"a energia do período é de {fmt_num(c['energia_base_evt_mwh'] / 1000, 3)} GWh na base de EVT e de "
               f"{fmt_num(c['energia_ons_geracao_mwh'] / 1000, 3)} GWh na série oficial")
    if not _divergencia_geracao(res):
        return (f"A geração horária da base de EVT coincide com a série oficial de geração por usina do ONS (id ONS "
                f"{perfil_ativo().identificacao.id_ons}) em todas as {fmt_int(c['horas_comuns'])} horas comuns, {periodo} (diferença de até "
                f"{fmt_num(c['tolerancia_mw'], 2)} MW); {energia}.")
    texto = (f"A geração horária da base de EVT difere da série oficial de geração por usina do ONS (id ONS {perfil_ativo().identificacao.id_ons}) "
             f"em {fmt_int(c['divergentes'])} das {fmt_int(c['horas_comuns'])} horas comuns, {periodo} (diferença acima de "
             f"{fmt_num(c['tolerancia_mw'], 2)} MW)")
    if c["so_ons_geracao"] or c["so_base_evt"]:
        texto += (f"; {fmt_int(c['so_ons_geracao'])} {plural(c['so_ons_geracao'], 'hora consta', 'horas constam')} só da "
                  f"série oficial e {fmt_int(c['so_base_evt'])} só da base de EVT")
    return texto + f"; {energia}. Lista completa nas abas GER_DIVERGENCIAS e GER_MENSAL."


def _achado_conferencia_geracao(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    if not res.geracao_oficial or not _divergencia_geracao(res):
        return None
    return "Conferência da geração", texto_conferencia_geracao(res)


def texto_cadastro(res: ResultadosAnalise) -> str:
    """Constatação do cadastro do ONS, só havendo divergência com os parâmetros do projeto (a ficha fica na capa)."""
    f = res.cadastro["ficha"]
    texto = (
        f"No cadastro de modalidade das usinas do ONS ({_data_obtencao_texto(res.cadastro['obtido_em'])}), a usina consta "
        f"como {f.get('nom_usina', '')}, CEG {f.get('ceg', '')}, id ONS {f.get('id_ons', '')}, modalidade "
        f"{f.get('nom_modalidadeoperacao', '')}, centro de operação {f.get('sgl_centrooperacao', '')}, ponto de conexão "
        f"{f.get('nom_pontoconexao', '')}, potência autorizada de {fmt_num(f.get('val_potenciaautorizada'), 1)} MW, estado "
        f"{f.get('id_estado', '')} e situação na ANEEL \"{f.get('sts_aneel', '')}\". O cadastro tem "
        f"{fmt_int(f.get('homonimos', 0))} outras usinas com \"{perfil_ativo().usina.nome_curto}\" no nome, excluídas pelo CEG."
    )
    if res.cadastro["divergencias"]:
        texto += f" Divergências com os parâmetros do projeto: {res.cadastro['divergencias']}."
    return texto


def _achado_cadastro(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    if not res.cadastro or not res.cadastro["divergencias"]:
        return None
    return "Cadastro da usina no ONS", texto_cadastro(res)


def _texto_alinhamento(alinhamento: pd.DataFrame) -> str:
    a = alinhamento.iloc[0]
    return (f"as vazões turbinada e vertida coincidiram com a base de EVT em {fmt_pct(a['pct_coincidencia'])} das "
            f"{fmt_int(a['horas_comuns'])} horas comuns (diferença de até {fmt_num(a['tolerancia_m3s'], 1)} m³/s; meta de "
            f"{fmt_num(a['meta_pct'], 0)}%)")


def _achado_afluencia(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    h = res.hidrologia
    if not h:
        return None
    r = h["resumo"]
    cobertura = (f"Os dados hidrológicos horários do ONS para a usina cobrem de {fmt_data(r['inicio'])} a "
                 f"{fmt_data(r['fim'])} ({fmt_int(r['horas'])} horas, convertidas da hora de fim para a hora de início)")
    if not h["publicado"]:
        texto = (f"{cobertura}, mas não foram cruzados com a base de EVT: {_texto_alinhamento(h['alinhamento'])}, abaixo "
                 "da meta. Os dados hidrológicos são informados pelos agentes e não são consistidos pelo ONS.")
        return "Afluência e vertimento", texto
    f = r["horas_por_faixa"]
    total = r["horas_evt"]
    cabia = f[ATE_UMA_UNIDADE] + f[entre_unidades()]
    texto = (
        f"{cobertura}; {_texto_alinhamento(h['alinhamento'])}. Nas {fmt_int(total)} horas com EVT, a afluência estava "
        f"até o engolimento de uma unidade ({fmt_num(perfil_ativo().parametros.engolimento_nominal_ug_m3s, 1)} m³/s) em {fmt_int(f[ATE_UMA_UNIDADE])} "
        f"({fmt_pct(_pct(f[ATE_UMA_UNIDADE], total))}), entre uma e {unidades_por_extenso()} unidades em {fmt_int(f[entre_unidades()])} "
        f"({fmt_pct(_pct(f[entre_unidades()], total))}) e acima do engolimento máximo da usina "
        f"({fmt_num(perfil_ativo().engolimento_maximo_m3s, 1)} m³/s) em {fmt_int(f[ACIMA_ENGOLIMENTO_USINA])} "
        f"({fmt_pct(_pct(f[ACIMA_ENGOLIMENTO_USINA], total))})"
    )
    if f[SEM_DADO_HIDROLOGICO]:
        texto += f"; {fmt_int(f[SEM_DADO_HIDROLOGICO])} sem dado hidrológico"
    texto += (f". Em {fmt_pct(_pct(cabia, total))} das horas com EVT, portanto, a água que chegou ao reservatório "
              "cabia nas turbinas da usina.")
    perfil = h.get("perfil", pd.DataFrame())
    grupos = set(perfil["grupo_dias"]) if len(perfil) else set()
    if {COM_PARADA_EVT, DEMAIS_DIAS} <= grupos:
        com = perfil[perfil["grupo_dias"] == COM_PARADA_EVT].set_index("hora")["nivel_montante_medio_m"]
        demais = perfil[perfil["grupo_dias"] == DEMAIS_DIAS]["nivel_montante_medio_m"]
        antes = com.reindex([h_ for h_ in range(min(HORAS_DIURNAS) - 3, min(HORAS_DIURNAS))]).mean()
        janela = com.reindex(HORAS_DIURNAS).mean()
        texto += (
            f" Nos {fmt_int(r['dias_com_parada_evt'])} dias com ao menos uma hora de parada com EVT, o nível de montante "
            f"médio ficou em {fmt_num(com.mean(), 3)} m (amplitude de {fmt_num((com.max() - com.min()) * 100, 1)} cm ao longo "
            f"do dia; {fmt_num(antes, 3)} m entre {min(HORAS_DIURNAS) - 3}h e {min(HORAS_DIURNAS) - 1}h e "
            f"{fmt_num(janela, 3)} m na janela das {_rotulo_janela(HORAS_DIURNAS)}, quando a vazão vertida é maior), contra "
            f"{fmt_num(demais.mean(), 3)} m nos demais dias (amplitude de {fmt_num((demais.max() - demais.min()) * 100, 1)} cm)."
        )
    # FR-044: como no texto da disponibilidade, a ressalva de que nenhuma das bases informa o motivo das paradas
    texto += (" Os dados hidrológicos são informados pelos agentes e não são consistidos pelo ONS. A afluência e o nível "
              "mostram a água disponível e o comportamento do reservatório, mas não o motivo das paradas, que depende de "
              "informação do agente.")
    return "Afluência e vertimento", texto


def _achado_geracao_zero(res: ResultadosAnalise) -> Tuple[str, str]:
    g = res.globais
    tabela = res.horas_geracao_zero
    parciais = set(res.cobertura["anos_parciais"])
    total = int(tabela["total"].sum())
    disp_zero = int(tabela["com_disponibilidade_zero"].sum())
    itens = [
        f"{int(r.ano)}: {fmt_int(r.total)} h" + (" (parcial)" if int(r.ano) in parciais else "")
        for r in tabela.itertuples()
    ]
    texto = (
        f"A geração foi exatamente zero em {fmt_int(total)} h: {fmt_int(disp_zero)} h com disponibilidade zero "
        f"(indisponibilidade total) e {fmt_int(total - disp_zero)} h com a usina declarada disponível. Por ano: "
        f"{'; '.join(itens)}. Essa contagem difere das horas de usina parada com EVT: das {fmt_int(total)} h com "
        f"geração zero, {fmt_int(g['horas_geracao_zero_com_evt'])} h tiveram EVT positiva, e as horas de usina parada "
        f"com EVT incluem ainda {fmt_int(g['horas_geracao_ate_limiar_positiva_com_evt'])} h com geração entre 0 e "
        f"{fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW. A distribuição mensal está na aba HORAS_GERACAO_ZERO_MES da planilha."
    )
    return "Horas com geração zero", texto


def _achado_perfil_diurno(res: ResultadosAnalise) -> Tuple[str, str]:
    anuais = res.indicadores_anuais
    itens = [
        f"{int(r.ano)}: {fmt_num(r.razao_evt_diurna_noturna, 2)}" + ("*" if r.ano_parcial else "")
        for r in anuais.itertuples()
    ]
    texto = (
        f"Razão entre a EVT média das {_rotulo_janela(HORAS_DIURNAS)} e a das {_rotulo_janela(HORAS_NOTURNAS)}, "
        f"por ano (* parcial): {'; '.join(itens)}."
    )
    relevantes = anuais[anuais["razao_evt_diurna_noturna"] >= RAZAO_DIURNA_RELEVANTE]
    demais = anuais[anuais["razao_evt_diurna_noturna"] < RAZAO_DIURNA_RELEVANTE]
    if len(relevantes):
        texto += (
            f" Em {fmt_lista(int(a) for a in relevantes['ano'])}, a EVT se concentrou no período diurno e a geração "
            f"diurna ficou em {fmt_lista(fmt_pct(v * 100, 0) for v in relevantes['razao_geracao_diurna_noturna'])} "
            f"da noturna, respectivamente"
        )
        if len(demais):
            texto += (
                f"; nos demais anos, a geração diurna ficou entre "
                f"{fmt_pct(demais['razao_geracao_diurna_noturna'].min() * 100, 0)} e "
                f"{fmt_pct(demais['razao_geracao_diurna_noturna'].max() * 100, 0)} da noturna"
            )
        texto += "."
    return "Concentração diurna", texto


def _achado_sazonalidade(res: ResultadosAnalise) -> Tuple[str, str]:
    anos = res.cobertura["anos_completos"]
    dist = res.distribuicao_mes_do_ano
    if not anos or dist["evt_mwh"].sum() <= 0:
        return "Distribuição ao longo do ano", "Não há anos completos com EVT para avaliar a distribuição mensal."
    mai_out = dist[dist["mes"].isin(MESES_MAIO_A_OUTUBRO)]["participacao_pct"].sum()
    jan_abr = dist[dist["mes"].isin(MESES_JANEIRO_A_ABRIL)]["participacao_pct"].sum()
    top = dist.nlargest(3, "evt_mwh")["mes_nome"].tolist()
    texto = (
        f"Nos anos completos ({anos[0]} a {anos[-1]}), os meses de maio a outubro concentraram {fmt_pct(mai_out)} "
        f"da EVT e os de janeiro a abril, {fmt_pct(jan_abr)}. Os meses com maior EVT foram {fmt_lista(top)}."
    )
    return "Distribuição ao longo do ano", texto


def _achado_mudanca_classificacao(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    mc = res.mudanca_classificacao
    titulo = "Mudança de classificação do vertimento pelo ONS"
    if mc.get("mes") is None:
        return None  # sem mudança detectada, a constatação não aparece
    mes = mc["mes"]
    texto = (
        f"A partir de {fmt_mes_ano(mes)}, cerca de {fmt_num(mc['nao_turbinavel_tipica_depois_m3s'], 0)} m³/s do "
        f"vertimento contínuo passaram a ser registrados pelo ONS como vazão vertida não turbinável. Até "
        f"{fmt_mes_ano(mes - 1)}, o vertimento contínuo ({fmt_num(mc['turbinavel_tipica_antes_m3s'], 0)} m³/s) era "
        f"contado como turbinável em {fmt_pct(mc['pct_horas_vertimento_minimo_turbinavel_antes'])} das horas, "
        f"com EVT média de {fmt_num(mc['evt_media_vertimento_minimo_antes_mw'], 1)} MWmed nessas horas."
    )
    anuais = res.indicadores_anuais
    completos = anuais[~anuais["ano_parcial"]]
    antes = completos[completos["ano"] < mes.year]
    depois = completos[completos["ano"] > mes.year]
    if len(antes) and len(depois):
        texto += (
            f" Nos anos completos anteriores, de {fmt_pct(antes['participacao_vertimento_minimo_pct'].min())} a "
            f"{fmt_pct(antes['participacao_vertimento_minimo_pct'].max())} da EVT anual veio de horas com vertimento de "
            f"até {fmt_num(perfil_ativo().analises.vertimento_minimo_m3s, 0)} m³/s; nos posteriores, no máximo "
            f"{fmt_pct(depois['participacao_vertimento_minimo_pct'].max())}. A série de EVT, portanto, não é "
            f"homogênea entre os dois períodos."
        )
    return titulo, texto


def _achado_qualidade(res: ResultadosAnalise) -> Tuple[str, str]:
    g = res.globais
    total = g["horas_com_anomalia"]
    if total == 0:
        return "Qualidade dos dados", "Nenhum registro viola as regras de plausibilidade física (R6 a R9)."
    detalhes = [
        f"{r.regra}, {r.descricao.lower()}: {fmt_int(r.horas)} h"
        for r in res.resumo_anomalias.itertuples()
        if r.horas > 0
    ]
    texto = (
        f"{fmt_int(total)} registros ({fmt_pct(_pct(total, g['horas']), 2)}) violam ao menos uma regra de "
        f"plausibilidade física ({'; '.join(detalhes)})."
    )
    if g["geracao_maxima_registrada_mw"] > perfil_ativo().parametros.potencia_instalada_mw:
        texto += (
            f" O maior valor de geração registrado, {fmt_num(g['geracao_maxima_registrada_mw'], 1)} MW em "
            f"{fmt_data_hora(g['instante_geracao_maxima'])}, supera a potência instalada."
        )
    texto += (
        f" Esses registros foram mantidos nos totais (a EVT neles soma {fmt_num(g['evt_em_registros_anomalos_mwh'], 1)} MWh, "
        f"{fmt_pct(_pct(g['evt_em_registros_anomalos_mwh'], g['evt_mwh']), 2)} do total), sinalizados na coluna "
        f"{COLUNA_QUALIDADE} e excluídos da tabela de extremos."
    )
    return "Qualidade dos dados", texto


def montar_achados(res: ResultadosAnalise) -> List[Tuple[str, str]]:
    """Constatações em texto, todas derivadas dos resultados calculados."""
    oficiais = [a for a in (_achado_indicadores_ons(res), _achado_estados_operativos(res)) if a is not None]
    return [
        _achado_cobertura(res),
        *[a for a in (_achado_cadastro(res),) if a is not None],
        _achado_disponibilidade(res),
        *oficiais,
        _achado_indisponibilidade(res),
        _achado_geracao(res),
        _achado_evt(res),
        _achado_evt_nivel_geracao(res),
        _achado_paradas(res),
        *[a for a in (_achado_programacao(res), _achado_disponibilidade_sincronizada(res), _achado_afluencia(res))
          if a is not None],
        _achado_geracao_zero(res),
        _achado_perfil_diurno(res),
        _achado_sazonalidade(res),
        *[a for a in (_achado_mudanca_classificacao(res), _achado_conferencia_geracao(res)) if a is not None],
        _achado_qualidade(res),
    ]
