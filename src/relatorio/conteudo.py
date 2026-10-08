"""Conteúdo comum ao PDF e ao Markdown: linhas das tabelas, textos, legendas, notas e blocos da capa."""

from __future__ import annotations

from typing import Callable, Dict, List, Sequence, Tuple

import pandas as pd

from src.analises.comum import _data_obtencao_texto, _pct, _rotulo_ano, _rotulo_janela
from src.analises.conclusao import LISTAS_CONCLUSAO
from src.analises.constatacoes import _texto_alinhamento
from src.analises.disponibilidade import SEM_PROGRAMACAO
from src.analises.hidrologia import (
    ACIMA_ENGOLIMENTO_USINA,
    ATE_UMA_UNIDADE,
    COM_PARADA_EVT,
    DEMAIS_DIAS,
    entre_unidades,
    faixas_afluencia,
    unidades_por_extenso,
    SEM_DADO_HIDROLOGICO,
)
from src.analises.indicadores import DESCRICAO_PARCELA
from src.analises.programacao import DESCRICAO_CLASSES
from src.analises.resultados import ResultadosAnalise
from src.comum.formatacao import (
    fmt_data,
    fmt_data_hora,
    fmt_int,
    fmt_lista,
    fmt_mes_ano,
    fmt_num,
    fmt_pct,
    fmt_pp,
    fmt_utc,
    MESES_ABREVIADOS,
    plural,
)
from src.comum.logger import setup_logger
from src.comum.perfil import perfil_ativo
from src.comum.regras import (
    CONJUNTO_CADASTRO,
    CONJUNTO_DISPONIBILIDADE,
    CONJUNTO_GERACAO,
    CONJUNTO_HIDROLOGIA,
    CONJUNTO_PROGRAMACAO_DIARIA,
    CONJUNTOS_INDICADORES_ONS,
    DURACAO_MINIMA_EVENTO_RELATORIO_H,
    FRACAO_PLENA_CARGA,
    HORAS_DIURNAS,
    HORAS_NOTURNAS,
    JANELA_TAXAS_MESES,
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
    LIMIAR_SINCRONIZADA_MW,
    MAXIMO_ITENS_CONCLUSAO,
    NUMERO_EVENTOS_RELATORIO,
    ONS_DATASET_URL,
    ONS_PORTAL_DATASET_URL,
    RAZAO_DIURNA_RELEVANTE,
    TOLERANCIA_COINCIDENCIA_MW,
    TOLERANCIA_DIVERGENCIA_HORAS,
)
from src.relatorio.estrutura import secoes_presentes
from src.tratamento.indicadores import INSUMOS_HORAS, TOLERANCIA_IDENTIDADE_HORAS
from src.tratamento.validacao import faixa_produtividade

logger = setup_logger("relatorio")


def orgao_garantia_fisica() -> str:
    """Órgão citado ao lado da garantia física na capa: a fonte do perfil até a primeira vírgula."""
    return perfil_ativo().parametros.fontes.garantia_fisica.split(",")[0].strip()


def _rotulo_secoes(chaves: Sequence[str], numeros: Dict[str, int]) -> str:
    presentes = sorted({numeros[c] for c in chaves if c in numeros})
    if not presentes:
        return ""
    return f"{plural(len(presentes), 'seção', 'seções')} {fmt_lista(presentes)}"


def listas_conclusao(res: ResultadosAnalise) -> List[Tuple[str, List[str]]]:
    """Listas da conclusão como aparecem no PDF e no Markdown: título e até ``MAXIMO_ITENS_CONCLUSAO`` itens."""
    numeros = {s.chave: n for n, s in secoes_presentes(res)}
    saida: List[Tuple[str, List[str]]] = []
    for chave, titulo in LISTAS_CONCLUSAO:
        itens = [i for i in res.conclusao if i["lista"] == chave][:MAXIMO_ITENS_CONCLUSAO]
        if itens:
            textos = []
            for i in itens:
                rotulo = _rotulo_secoes(i["secoes"], numeros)
                textos.append(f"{i['texto']} ({rotulo})." if rotulo else f"{i['texto']}.")
            saida.append((titulo, textos))
    return saida


def tabela_conclusao(res: ResultadosAnalise) -> pd.DataFrame:
    """Aba CONCLUSAO: todos os itens gerados, inclusive os que passam do limite por lista."""
    titulos = dict(LISTAS_CONCLUSAO)
    nomes = {s.chave: f"{n}. {s.titulo}" for n, s in secoes_presentes(res)}
    linhas = [{"lista": titulos[i["lista"]], "ordem": i["ordem"], "regra": i["regra"], "texto": i["texto"],
               "secoes": "; ".join(nomes[c] for c in i["secoes"] if c in nomes)} for i in res.conclusao]
    return pd.DataFrame(linhas, columns=["lista", "ordem", "regra", "texto", "secoes"])


def nota_conclusao() -> str:
    """Item das notas metodológicas com as regras (C1 a C11) e os limiares da conclusão."""
    fracao = LIMIAR_CONCLUSAO_PARTICIPACAO_TEIFA
    participacao = "2/3" if abs(fracao - 2 / 3) < 1e-9 else fmt_pct(fracao * 100, 0)
    regras = [
        f"C1 EVT com a usina parada ≥ {fmt_pct(LIMIAR_CONCLUSAO_EVT_PARADA_PCT, 0)} da EVT (a programação de até "
        f"{fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW é citada se ocorrer em ≥ {fmt_pct(LIMIAR_CONCLUSAO_PROGRAMACAO_ZERO_PCT, 0)} "
        "dessas horas)",
        f"C2 unidade com ≥ {participacao} da TEIFa, acima da referência, ou com limitação forçada de potência em ≥ "
        f"{fmt_pct(LIMIAR_CONCLUSAO_MESES_LIMITACAO_PCT, 0)} dos meses",
        f"C3 afluência até o engolimento máximo em ≥ {fmt_pct(LIMIAR_CONCLUSAO_AFLUENCIA_ENGOLIMENTO_PCT, 0)} das horas com EVT",
        f"C4 razão diurna/noturna da EVT ≥ {fmt_num(RAZAO_DIURNA_RELEVANTE, 0)} num dos dois últimos anos",
        "C5 disponibilidade ou taxas piores que as referências",
        f"C6 usina parada com programação acima de {fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 0)} MW",
        f"C7 diferença anual ≥ {fmt_num(LIMIAR_CONCLUSAO_DIFERENCA_RESERVA_GWH, 0)} GWh entre capacidade não sincronizada e "
        "reserva desligada, ou DISPF e horas por estado operativo divergentes",
        f"C8 geração acima da disponibilidade declarada em ≥ {fmt_int(LIMIAR_CONCLUSAO_R7_HORAS)} h",
        "C9 geração abaixo da garantia física, ou EVT do último ano completo como a maior",
        f"C10 indisponibilidade total ≥ {fmt_int(LIMIAR_CONCLUSAO_INDISPONIBILIDADE_DIAS)} dias, ou programada ≥ "
        f"{fmt_pct(LIMIAR_CONCLUSAO_PROGRAMADA_UG_PCT, 0)} numa unidade num ano completo",
        f"C11 dados hidrológicos sinalizados, ou geração com vazão turbinada nula em ≥ {fmt_int(LIMIAR_CONCLUSAO_R9_HORAS)} h",
    ]
    return (
        "Conclusão: indícios gerados por regras fixas, iguais para qualquer usina, a partir dos resultados das seções: "
        + "; ".join(regras)
        + f". O relatório mostra até {MAXIMO_ITENS_CONCLUSAO} itens por lista, na ordem das regras; todos estão na aba "
        "CONCLUSAO da planilha."
    )


def notas_metodologicas(res: ResultadosAnalise) -> List[str]:
    """Notas sobre definições e limitações (sem valores de resultado)."""
    prod_min, prod_max = faixa_produtividade(perfil_ativo())
    parciais = res.cobertura["anos_parciais"]
    notas = [
        f"Fonte: conjunto de dados Energia Vertida Turbinável do Portal de Dados Abertos do ONS ({ONS_DATASET_URL}), "
        "em base horária; a hora 00h representa o intervalo de 00:00 a 00:59:59. Os dados passam por consistência "
        "recorrente e podem ser revisados pelo ONS após a publicação.",
        "Os horários são os publicados pelo ONS (horário legal). Até fevereiro de 2019 vigorava o horário de verão, "
        "o que pode produzir hora ausente no seu início.",
        "Disponibilidade relativa = média da disponibilidade horária declarada (val_disponibilidade) ÷ potência "
        "instalada. É um indicador aproximado e não substitui o FID regulatório (razão IDv/ID calculada com TEIP e "
        f"TEIFa apurados), que não consta deste conjunto de dados. A referência de {fmt_pct(perfil_ativo().disponibilidade_referencia * 100, 2)} "
        "é (1 − IP) × (1 − TEIF) com os valores usados no cálculo da garantia física.",
        f"A garantia física usada é de {fmt_num(perfil_ativo().parametros.garantia_fisica_mwmed, 1)} MWmed "
        f"({perfil_ativo().parametros.fontes.garantia_fisica})."
        + (f" O IP e o TEIF de referência são os do {perfil_ativo().parametros.fontes.ip_teif}; a revisão posterior pode "
           "ter alterado esses parâmetros e, com eles, a disponibilidade de referência."
           if perfil_ativo().parametros.fontes.ip_teif else ""),
        "Fator de capacidade = geração média ÷ potência instalada. A comparação com a garantia física é indicativa: "
        "não considera perdas até o centro de gravidade, a sazonalização da garantia física nem o MRE.",
        "A EVT é calculada pelo ONS como vazão vertida turbinável × produtividade e é limitada pela folga de geração "
        "(disponibilidade − geração). O conjunto de dados não informa a causa do vertimento nem da redução de geração "
        "(restrição interna da usina, restrição elétrica ou energética, ordem de despacho); a atribuição de causa "
        "depende de documentos do agente e do ONS.",
        f"Definições usadas: usina parada = geração ≤ {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW; plena carga = geração ≥ "
        f"{fmt_num(FRACAO_PLENA_CARGA * perfil_ativo().parametros.potencia_instalada_mw, 1)} MW; vertimento mínimo = vazão vertida ≤ "
        f"{fmt_num(perfil_ativo().analises.vertimento_minimo_m3s, 0)} m³/s"
        + (f" ({perfil_ativo().analises.descricao_vertimento_minimo} de "
           f"{fmt_num(perfil_ativo().parametros.vazao_remanescente_m3s, 2)} m³/s)"
           if perfil_ativo().analises.descricao_vertimento_minimo else "")
        + f"; janela diurna {_rotulo_janela(HORAS_DIURNAS)}; noturna "
        f"{_rotulo_janela(HORAS_NOTURNAS)}.",
        "Registros que violam as regras de plausibilidade física (R6 a R9) foram mantidos nos totais, por serem os "
        "dados publicados pelo ONS, sinalizados na coluna qualidade_registro e excluídos das tabelas de extremos e do "
        f"perfil estatístico. A faixa de produtividade aceita (R8) é de {fmt_num(prod_min, 3)} a {fmt_num(prod_max, 3)} MW/(m³/s).",
    ]
    if parciais:
        n = len(parciais)
        notas.append(
            f"{plural(n, 'O ano', 'Os anos')} {fmt_lista(parciais)} {plural(n, 'é parcial', 'são parciais')}: "
            f"{plural(n, 'aparece', 'aparecem')} nas tabelas com a cobertura correspondente, mas não "
            f"{plural(n, 'entra', 'entram')} nas comparações entre anos completos."
        )
    if res.ons:
        notas += notas_indicadores_ons()
    if res.programacao:
        notas += notas_programacao()
    return notas + notas_bases_complementares(res) + [nota_conclusao()]


def notas_bases_complementares(res: ResultadosAnalise) -> List[str]:
    """Relação de fontes das bases complementares do ONS carregadas (spec da Geração do relatório, FR-020).

    Cada base traz o link do conjunto, o identificador da usina (com a conferência), o período coberto e a data de
    obtenção, como já fazem EVT, indicadores e programação; sem a base, nenhuma linha.
    """
    notas: List[str] = []
    d = res.disponibilidade
    if d:
        r = d["resumo"]
        notas.append(
            f"Disponibilidade por usina: conjunto Disponibilidade por usina do ONS ({ONS_PORTAL_DATASET_URL}"
            f"{CONJUNTO_DISPONIBILIDADE}), usina {perfil_ativo().identificacao.id_ons} (conferida pelo CEG {perfil_ativo().identificacao.ceg} e pelo estado "
            f"{perfil_ativo().usina.estado}), de {fmt_data(r['inicio'])} a {fmt_data(r['fim'])}, {_data_obtencao_texto(d['obtido_em'])}."
        )
    h = res.hidrologia
    if h:
        r = h["resumo"]
        notas.append(
            f"Dados hidrológicos: conjunto Dados hidrológicos horários do ONS ({ONS_PORTAL_DATASET_URL}"
            f"{CONJUNTO_HIDROLOGIA}), cod_usina {perfil_ativo().identificacao.cod_usina} (conferido pelo nome e pelo código {perfil_ativo().identificacao.id_reservatorio} "
            f"do reservatório), de {fmt_data(r['inicio'])} a {fmt_data(r['fim'])}, "
            f"{_data_obtencao_texto(h['obtido_em'])}; dados informados pelos agentes e não consistidos pelo ONS."
        )
    g = res.geracao_oficial
    if g:
        r = g["resumo"]
        notas.append(
            f"Geração por usina: conjunto Geração por usina do ONS ({ONS_PORTAL_DATASET_URL}{CONJUNTO_GERACAO}), usina "
            f"{perfil_ativo().identificacao.id_ons} (conferida pelo CEG e pelo estado {perfil_ativo().usina.estado}), de {fmt_data(r['inicio'])} a "
            f"{fmt_data(r['fim'])}, {_data_obtencao_texto(g['obtido_em'])}."
        )
    c = res.cadastro
    if c:
        notas.append(
            f"Cadastro: conjunto Modalidade das usinas do ONS ({ONS_PORTAL_DATASET_URL}{CONJUNTO_CADASTRO}), CEG "
            f"{perfil_ativo().identificacao.ceg} (conferido pelo id ONS {perfil_ativo().identificacao.id_ons} e pelo estado {perfil_ativo().usina.estado}), cadastro sem série "
            f"histórica, {_data_obtencao_texto(c['obtido_em'])}."
        )
    return notas


def notas_indicadores_ons() -> List[str]:
    """Notas sobre os conjuntos de indicadores oficiais do ONS (sem valores de resultado)."""
    conjuntos = "; ".join(f"{d} ({ONS_PORTAL_DATASET_URL}{c})" for c, d in CONJUNTOS_INDICADORES_ONS.items())
    siglas = "; ".join(f"{s} = {d}" for s, d in INSUMOS_HORAS.items())
    return [
        f"Indicadores oficiais do ONS: {conjuntos}. A usina é identificada pelo CEG {perfil_ativo().identificacao.ceg} (id ONS {perfil_ativo().identificacao.id_ons}); "
        "os meses e anos são recortados no período da base de EVT e, quando o ONS publica mais de uma versão, vale a "
        "mais recente (num_versao).",
        "DISPF, INDISPPF e INDISPFF são percentuais do tempo do mês (ou do ano) em que a unidade esteve disponível, em "
        "desligamento programado ou em desligamento forçado, conforme o Submódulo 9.2 dos Procedimentos de Rede; não "
        "descontam a operação com potência limitada. A disponibilidade da usina pelo DISPF é a média das unidades, "
        "ponderada pela potência e pelas horas da base de EVT em cada mês.",
        f"Horas por estado operativo (dicionário do ONS sem definição das siglas; descrições pela nomenclatura da "
        f"metodologia de apuração das taxas): {siglas}. Em cada mês, HP = HS + HRD + HDP + HDF + HDCE + HEDP + HEDF "
        f"(conferido com tolerância de {fmt_num(TOLERANCIA_IDENTIDADE_HORAS, 1)} h).",
        f"TEIFa e TEIP recalculadas com janela móvel de {JANELA_TAXAS_MESES} meses, ponderadas pela potência das unidades: "
        "TEIFa = Σ(HDF + HEDF) ÷ Σ(HP − HDP − HEDP); TEIP = Σ(HDP + HEDP) ÷ ΣHP. A decomposição por unidade e parcela "
        "divide cada termo do numerador pelo mesmo denominador. Desligamentos por causa externa (HDCE) não entram em "
        "nenhuma das duas taxas.",
        "Os conjuntos de indicadores não informam a causa nem os eventos individuais de desligamento (data e hora de "
        "início e fim, motivo); essa informação depende dos registros do agente e do ONS.",
    ]


def notas_programacao() -> List[str]:
    """Notas sobre a programação diária do ONS (sem valores de resultado)."""
    return [
        f"Programação diária: conjunto Dados dos Valores da Programação Diária ({ONS_PORTAL_DATASET_URL}"
        f"{CONJUNTO_PROGRAMACAO_DIARIA}), um arquivo por dia desde 01/10/2024, usina {perfil_ativo().identificacao.cod_programacao} "
        "(conferida pelo nome e pelo estado). A data de cada dia vem do nome do arquivo; os 48 patamares de 30 minutos "
        "são convertidos em horas pela média dos dois patamares de cada hora (hora de início, como na base de EVT).",
        f"Classificação das horas comuns: usina parada = geração ≤ {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW; programação "
        f"zero = programação ≤ {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW; desvio = usina parada com programação acima de "
        f"{fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 0)} MW. Dias sem arquivo no portal não são interpolados.",
        "A programação diária é o planejamento do dia e não registra reprogramações nem ordens em tempo real. Para usinas "
        "hidráulicas, os campos de motivo (ordem de mérito, inflexibilidade, razão elétrica) vêm vazios e a disponibilidade "
        "programada vem zerada; o conjunto mostra se a usina seguiu a programação, não por que o ONS a programou.",
    ]


def linhas_tabela_anual(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Cabeçalho e linhas formatadas da tabela de indicadores anuais (usadas no MD e no PDF)."""
    cabecalho = [
        "Ano", "Cobertura", "Disp. média (% Pinst)", "Δ vs ref. GF", "Fator de capacidade", "Geração / GF",
        "EVT (MWh)", "EVT no vert. mínimo", "Índice EVT", "Horas c/ EVT", "Horas parada c/ EVT", "Horas indisp. total",
    ]
    linhas = []
    for r in res.indicadores_anuais.itertuples():
        linhas.append([
            f"{int(r.ano)}{'*' if r.ano_parcial else ''}",
            fmt_pct(r.cobertura_pct),
            fmt_pct(r.disponibilidade_relativa_pct),
            fmt_pp(r.desvio_disponibilidade_referencia_pp),
            fmt_pct(r.fator_capacidade_pct),
            fmt_pct(r.geracao_sobre_garantia_fisica_pct),
            fmt_int(r.evt_mwh),
            fmt_pct(r.participacao_vertimento_minimo_pct),
            fmt_pct(r.indice_evt_pct),
            fmt_int(r.horas_com_evt),
            fmt_int(r.horas_parada_com_evt),
            fmt_int(r.horas_indisponibilidade_total),
        ])
    return cabecalho, linhas


def linhas_tabela_geracao_zero(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Cabeçalho e linhas da tabela de horas com geração zero por mês (usadas no MD e no PDF)."""
    parciais = set(res.cobertura["anos_parciais"])
    cabecalho = ["Ano", *[m.capitalize() for m in MESES_ABREVIADOS], "Total", "Com disp. zero", "Com usina disponível"]
    linhas = []
    for r in res.horas_geracao_zero.to_dict("records"):
        linhas.append(
            [f"{int(r['ano'])}{'*' if int(r['ano']) in parciais else ''}"]
            + [fmt_int(r[m]) for m in MESES_ABREVIADOS]
            + [fmt_int(r["total"]), fmt_int(r["com_disponibilidade_zero"]), fmt_int(r["com_usina_disponivel"])]
        )
    return cabecalho, linhas


def linhas_tabela_ons_disponibilidade(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Disponibilidade declarada (EVT) e DISPF da usina por ano."""
    cabecalho = ["Ano", "Disp. declarada (EVT, % Pinst)", "DISPF (média das UGs)", "Indisp. programada",
                 "Indisp. forçada", "Δ DISPF vs ref. GF"]
    t = res.ons.get("disp_anual", pd.DataFrame())
    linhas = [
        [_rotulo_ano(r.ano, r.ano_parcial), fmt_pct(r.disponibilidade_declarada_pct), fmt_pct(r.dispf_pct),
         fmt_pct(r.indisppf_pct), fmt_pct(r.indispff_pct), fmt_pp(r.desvio_dispf_referencia_pp)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_ons_ug_anual(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Indicadores anuais oficiais por unidade geradora."""
    cabecalho = ["Ano", "UG", "DISPF", "INDISPPF", "INDISPFF", "DMDFF (h)"]
    t = res.ons.get("ug_anual", pd.DataFrame())
    linhas = [
        [_rotulo_ano(r.ano, r.ano_parcial), f"UG{int(r.ug)}", fmt_pct(r.dispf, 2), fmt_pct(r.indisppf, 2),
         fmt_pct(r.indispff, 2), fmt_num(r.dmdff, 1)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_ons_horas(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Horas por estado operativo, por ano e unidade."""
    cabecalho = ["Ano", "UG", "Meses", *INSUMOS_HORAS.keys()]
    t = res.ons.get("horas_anual", pd.DataFrame())
    linhas = [
        [_rotulo_ano(r["ano"], r["ano_parcial"]), f"UG{int(r['ug'])}", fmt_int(r["meses"]),
         *[fmt_int(r[s]) for s in INSUMOS_HORAS]]
        for r in t.to_dict("records")
    ]
    return cabecalho, linhas


def linhas_tabela_ons_decomposicao(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Contribuição de cada unidade e parcela de horas para a TEIFa e a TEIP mais recentes."""
    cabecalho = ["Taxa", "UG", "Parcela", "Horas na janela", "Contribuição (p.p.)", "Participação na taxa"]
    t = res.ons.get("decomposicao")
    if t is None:
        return cabecalho, []
    linhas = [
        [r.taxa, f"UG{int(r.ug)}", f"{r.parcela} ({DESCRICAO_PARCELA[r.parcela]})", fmt_num(r.horas, 1),
         fmt_num(r.contribuicao_pp, 3), fmt_pct(r.participacao_pct)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_ons_divergencias(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Meses-unidade em que o indicador DISPF e as horas do TEIP não conferem."""
    cabecalho = ["Mês", "UG", "HS", "HRD", "HDP (TEIP)", "Programadas pelo DISPF (h)", "HDF (TEIP)",
                 "Forçadas pelo DISPF (h)"]
    t = res.ons.get("divergencias", pd.DataFrame())
    linhas = [
        [fmt_mes_ano(r.mes), f"UG{int(r.ug)}", fmt_num(r.HS, 1), fmt_num(r.HRD, 1), fmt_num(r.HDP, 1),
         fmt_num(r.horas_programadas_indisppf, 1), fmt_num(r.HDF, 1), fmt_num(r.horas_forcadas_indispff, 1)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def texto_taxas_ons(res: ResultadosAnalise) -> str:
    """Resumo da TEIFa e da TEIP mais recentes frente às referências (MD e PDF)."""
    t = res.ons.get("taxa_ultima")
    if not t:
        return ""
    return (
        f"TEIFa e TEIP apuradas pelo ONS em {fmt_mes_ano(t['mes'])} (janela de {JANELA_TAXAS_MESES} meses): "
        f"TEIFa {fmt_pct(t['teifa_pct'], 3)} (referência TEIF {fmt_pct(perfil_ativo().parametros.teif_referencia * 100, 3)}); TEIP "
        f"{fmt_pct(t['teip_pct'], 3)} (referência IP {fmt_pct(perfil_ativo().parametros.ip_referencia * 100, 3)}); (1 − TEIFa) × (1 − TEIP) = "
        f"{fmt_pct(t['disponibilidade_verificada_pct'], 2)} (referência {fmt_pct(perfil_ativo().disponibilidade_referencia * 100, 2)})."
    )


def linhas_tabela_programacao_mensal(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Horas paradas com EVT por mês, segundo a programação diária do ONS."""
    parada, desvio = fmt_num(LIMIAR_GERACAO_PARADA_MW, 0), fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 0)
    cabecalho = ["Mês", "Horas comuns", "Paradas c/ EVT", f"c/ programação ≤ {parada} MW", "EVT nessas horas (MWh)",
                 "% da EVT do mês", f"Paradas c/ programação > {desvio} MW", f"Gerou c/ programação ≤ {parada} MW"]
    t = res.programacao.get("mensal", pd.DataFrame())
    linhas = [
        [fmt_mes_ano(r.mes), fmt_int(r.horas_comuns), fmt_int(r.horas_parada_com_evt),
         fmt_int(r.horas_parada_evt_programacao_zero), fmt_num(r.evt_parada_programacao_zero_mwh, 0),
         fmt_pct(r.participacao_evt_programacao_zero_pct), fmt_int(r.horas_desvio_programacao),
         fmt_int(r.horas_gerando_programacao_zero)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_programacao_eventos(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Maiores eventos de usina parada com programação acima do limiar de desvio."""
    cabecalho = ["Início", "Fim", "Duração (h)", "Programação média (MW)", "Disponibilidade média (MW)", "EVT (MWh)"]
    t = res.programacao.get("eventos", pd.DataFrame())
    if not len(t):
        return cabecalho, []
    top = t.sort_values(["duracao_h", "evt_mwh"], ascending=False).head(NUMERO_EVENTOS_RELATORIO)
    linhas = [
        [fmt_data_hora(r.inicio), fmt_data_hora(r.fim), fmt_int(r.duracao_h), fmt_num(r.programacao_media_mw, 1),
         fmt_num(r.disponibilidade_media_mw, 1), fmt_num(r.evt_mwh, 1)]
        for r in top.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_programacao_perfil(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Horas de usina parada com EVT e programação zero por hora do dia."""
    t = res.programacao.get("perfil", pd.DataFrame())
    if not len(t):
        return [], []
    cabecalho = ["Hora", *[f"{int(h)}h" for h in t["hora"]]]
    return cabecalho, [["Horas", *[fmt_int(v) for v in t["horas"]]]]


_ROTULOS_CLASSES_PARADA: Dict[str, str] = {
    "SINCRONIZADA": "alguma unidade sincronizada",
    "NAO_SINCRONIZADA": "nenhuma unidade sincronizada",
    "COM_EVT": "com EVT",
    "SEM_EVT": "sem EVT",
    SEM_PROGRAMACAO: "sem programação: fora do período ou sem valor programado",
    **DESCRICAO_CLASSES,
}


def linhas_tabela_disponibilidade_anual(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Médias anuais de disponibilidade operacional, declarada e sincronizada e de geração."""
    cabecalho = ["Ano", "Horas", "Operacional (MW)", "Declarada EVT (MW)", "Sincronizada (MW)", "Geração (MW)",
                 "Não sincronizada (GWh)", "Reserva desligada TEIFa/TEIP (GWh)"]
    t = res.disponibilidade.get("anual", pd.DataFrame())
    linhas = [
        [_rotulo_ano(r.periodo, r.ano_parcial), fmt_int(r.horas_comuns), fmt_num(r.disp_operacional_media_mw, 1),
         fmt_num(r.disp_declarada_media_mw, 1), fmt_num(r.disp_sincronizada_media_mw, 1), fmt_num(r.geracao_media_mw, 1),
         fmt_num(r.capacidade_nao_sincronizada_mwh / 1000, 1), fmt_num(r.reserva_desligada_teif_mwh / 1000, 1)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_disponibilidade_paradas(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Horas com a usina parada por sincronização, EVT e classe da programação."""
    cabecalho = ["Sincronização", "EVT", "Programação do ONS", "Horas", "EVT (MWh)"]
    t = res.disponibilidade.get("classes", pd.DataFrame())
    if t.empty:
        return cabecalho, []
    t = t.sort_values(["sincronizacao", "evt", "horas"], ascending=[True, True, False])
    linhas = [
        [_ROTULOS_CLASSES_PARADA.get(r.sincronizacao, r.sincronizacao), _ROTULOS_CLASSES_PARADA.get(r.evt, r.evt),
         _ROTULOS_CLASSES_PARADA.get(r.classe_programacao, r.classe_programacao), fmt_int(r.horas), fmt_num(r.evt_mwh, 1)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_disponibilidade_divergencias(
    res: ResultadosAnalise, limite: int = NUMERO_EVENTOS_RELATORIO
) -> Tuple[List[str], List[List[str]]]:
    """Maiores períodos de divergência entre a disponibilidade operacional e a declarada."""
    cabecalho = ["Início", "Fim", "Horas", "Diferença média (MW)", "Diferença máxima (MW)"]
    t = res.disponibilidade.get("divergencias", pd.DataFrame())
    if t.empty:
        return cabecalho, []
    t = t.nlargest(limite, "horas").sort_values("inicio")
    linhas = [[fmt_data_hora(r.inicio), fmt_data_hora(r.fim), fmt_int(r.horas), fmt_num(r.diferenca_media_mw, 2),
               fmt_num(r.diferenca_maxima_mw, 2)] for r in t.itertuples()]
    return cabecalho, linhas


def notas_disponibilidade(res: ResultadosAnalise) -> List[str]:
    """Ressalvas da seção de disponibilidade (MD e PDF)."""
    d = res.disponibilidade
    r = d["resumo"]
    notas = [
        # spec da Geração do relatório (FR-021): a fonte (conjunto, identificador e data de obtenção) está na legenda de cada tabela e figura
        "A disponibilidade operacional é a mesma informação da disponibilidade declarada da base de EVT; a sincronizada "
        "indica a capacidade das unidades ligadas à rede.",
        f"Usina parada = geração até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW; unidade sincronizada = disponibilidade "
        f"sincronizada acima de {fmt_num(LIMIAR_SINCRONIZADA_MW, 0)} MW. Não sincronizada = operacional − sincronizada; "
        "reserva desligada = horas em reserva desligada (HRD) das unidades × potência (parâmetros TEIFa/TEIP), apuração "
        "diferente e por isso só comparada, sem meta.",
    ]
    if r["horas_sinalizadas"]:
        notas.append(f"{fmt_int(r['horas_sinalizadas'])} horas com valores inconsistentes (regras D1 a D4) ficaram fora das "
                     "análises (coluna qualidade da série horária tratada).")
    if r["meses_sem_usina"] or r["horas_ausentes"]:
        meses = fmt_lista(fmt_mes_ano(m) for m in r["meses_sem_usina"]) if r["meses_sem_usina"] else "nenhum"
        notas.append(f"Meses sem a usina no conjunto: {meses}; horas ausentes em meses com dados: "
                     f"{fmt_int(r['horas_ausentes'])} (aba DISP_AUSENCIAS). Nada foi interpolado.")
    return notas


def _rotulos_faixas_curtos() -> Dict[str, str]:
    """Rótulos curtos das faixas de afluência, com o engolimento do perfil da usina."""
    unidade = perfil_ativo().parametros.engolimento_nominal_ug_m3s
    usina = perfil_ativo().engolimento_maximo_m3s
    return {
        ATE_UMA_UNIDADE: f"Até {fmt_num(unidade, 1)} m³/s",
        entre_unidades(): f"{fmt_num(unidade, 1)} a {fmt_num(usina, 0)} m³/s",
        ACIMA_ENGOLIMENTO_USINA: f"Acima de {fmt_num(usina, 0)} m³/s",
        SEM_DADO_HIDROLOGICO: "Sem dado",
    }


def _tabela_faixas_anual(
    res: ResultadosAnalise, valor: str, formatar: Callable[[float], str]
) -> Tuple[List[str], List[List[str]]]:
    """Linhas por ano e faixa de afluência de ``valor`` (``horas`` ou ``evt_mwh``), com total e parcela que cabia."""
    rotulos = _rotulos_faixas_curtos()
    cabecalho = ["Ano", *[rotulos[f] for f in faixas_afluencia()], "Total", "Cabia nas turbinas"]
    t = res.hidrologia.get("faixas_anual", pd.DataFrame())
    if t.empty:
        return cabecalho, []
    largo = t.pivot_table(index=["periodo", "ano_parcial"], columns="faixa_afluencia", values=valor,
                          aggfunc="sum", fill_value=0).reset_index()
    linhas = []
    for r in largo.itertuples(index=False):
        valores = {f: getattr(r, f, 0) for f in faixas_afluencia()}
        total = sum(valores.values())
        cabia = valores[ATE_UMA_UNIDADE] + valores[entre_unidades()]
        linhas.append([_rotulo_ano(r.periodo, r.ano_parcial), *[formatar(valores[f]) for f in faixas_afluencia()],
                       formatar(total), fmt_pct(_pct(cabia, total))])
    return cabecalho, linhas


def linhas_tabela_faixas_afluencia(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Horas com EVT por faixa de afluência e ano."""
    return _tabela_faixas_anual(res, "horas", lambda v: fmt_int(int(v)))


def linhas_tabela_faixas_afluencia_evt(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """EVT (MWh) por faixa de afluência e ano, na mesma estrutura da tabela de horas."""
    return _tabela_faixas_anual(res, "evt_mwh", lambda v: fmt_num(v, 0))


def linhas_tabela_hidrologia_anual(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Afluência, vazões, níveis e volume útil por ano."""
    cabecalho = ["Ano", "Horas", "Afluência média (m³/s)", "Afluência máx. (m³/s)", "Turbinada (m³/s)", "Vertida (m³/s)",
                 "Nível mont. mín.–máx. (m)", "Volume útil (%)", "Horas acima do engolimento"]
    t = res.hidrologia.get("anual", pd.DataFrame())
    linhas = [
        [_rotulo_ano(r.periodo, r.ano_parcial), fmt_int(r.horas), fmt_num(r.afluencia_media_m3s, 1),
         fmt_num(r.afluencia_maxima_m3s, 0), fmt_num(r.turbinada_media_m3s, 1), fmt_num(r.vertida_media_m3s, 1),
         f"{fmt_num(r.nivel_montante_min_m, 2)}–{fmt_num(r.nivel_montante_max_m, 2)}", fmt_num(r.volume_util_medio_pct, 1),
         fmt_int(r.horas_afluencia_acima_engolimento)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_perfil_hidrologico(res: ResultadosAnalise, passo: int = 3) -> Tuple[List[str], List[List[str]]]:
    """Vazões e nível médios em horas selecionadas do dia, por grupo de dias."""
    cabecalho = ["Hora", "Turbinada c/ parada (m³/s)", "Vertida c/ parada (m³/s)", "Nível c/ parada (m)",
                 "Turbinada demais (m³/s)", "Vertida demais (m³/s)", "Nível demais (m)"]
    p = res.hidrologia.get("perfil", pd.DataFrame())
    if p.empty:
        return cabecalho, []
    com = p[p["grupo_dias"] == COM_PARADA_EVT].set_index("hora")
    demais = p[p["grupo_dias"] == DEMAIS_DIAS].set_index("hora")
    linhas = []
    for hora in range(0, 24, passo):
        def _v(t: pd.DataFrame, coluna: str, casas: int) -> str:
            return fmt_num(t.loc[hora, coluna], casas) if hora in t.index else "–"
        linhas.append([f"{hora}h", _v(com, "turbinada_media_m3s", 1), _v(com, "vertida_media_m3s", 1),
                       _v(com, "nivel_montante_medio_m", 2), _v(demais, "turbinada_media_m3s", 1),
                       _v(demais, "vertida_media_m3s", 1), _v(demais, "nivel_montante_medio_m", 2)])
    return cabecalho, linhas


def notas_hidrologia(res: ResultadosAnalise) -> List[str]:
    """Ressalvas da seção hidrológica (MD e PDF)."""
    h = res.hidrologia
    r = h["resumo"]
    notas = [
        # spec da Geração do relatório (FR-021): a fonte está na legenda de cada tabela e figura; a ressalva fica
        "Os dados são informados pelos agentes e não são consistidos pelo ONS; valores fora da faixa física (vazão negativa, volume útil fora de 0 a 100%) "
        "são sinalizados e excluídos só no campo afetado, sem correção, e campos vazios não são tratados como zero.",
        "O conjunto marca o fim da hora (a última hora do dia aparece às 23:59); a série foi convertida para a hora de "
        f"início, como a base de EVT, e {_texto_alinhamento(h['alinhamento'])}.",
        f"Faixas: até {fmt_num(perfil_ativo().parametros.engolimento_nominal_ug_m3s, 1)} m³/s, a afluência cabia em uma unidade; até "
        f"{fmt_num(perfil_ativo().engolimento_maximo_m3s, 1)} m³/s, nas {unidades_por_extenso()}; acima disso, parte do vertimento era inevitável. "
        "A EVT de cada hora é a parcela turbinável informada na base de EVT.",
    ]
    if perfil_ativo().textos.ressalva_volume_util:  # ressalva própria da usina, quando o perfil a traz
        notas.append(perfil_ativo().textos.ressalva_volume_util)
    if r["horas_sinalizadas"]:
        descricao = {"H1": "vazão negativa", "H2": "volume útil fora de 0 a 100%", "H3": "valor não numérico",
                     "H4": "nível de montante ou de jusante muito afastado da mediana da série"}
        partes = []
        for regra, info in r.get("sinalizadas_por_regra", {}).items():
            if info["horas"]:
                anos = fmt_lista(f"{ano}: {fmt_int(n)} h" for ano, n in info["anos"].items())
                partes.append(f"{regra} ({descricao[regra]}) em {fmt_int(info['horas'])} horas ({anos})")
        notas.append("Sinalizações (coluna qualidade da série horária tratada): "
                     + "; ".join(partes) + ".")
    pico = r.get("pico_afluencia")
    if pico and pico["defluencia_m3s"] == pico["defluencia_m3s"] and pico["afluencia_m3s"] > 2 * perfil_ativo().engolimento_maximo_m3s:
        notas.append(
            f"A afluência horária tem picos isolados: a maior, {fmt_num(pico['afluencia_m3s'], 0)} m³/s em "
            f"{fmt_data_hora(pico['instante'])}, ocorreu com defluência de {fmt_num(pico['defluencia_m3s'], 0)} m³/s. Picos "
            "assim e as afluências negativas são típicos de afluência calculada por balanço hídrico com oscilações do "
            "nível; a afluência máxima anual pode refletir esses picos. A classificação por faixa usa o valor de cada hora."
        )
    if r["meses_sem_usina"] or r["horas_ausentes"]:
        meses = fmt_lista(fmt_mes_ano(m) for m in r["meses_sem_usina"]) if r["meses_sem_usina"] else "nenhum"
        notas.append(f"Meses sem a usina no conjunto: {meses}; horas ausentes em meses com dados: "
                     f"{fmt_int(r['horas_ausentes'])} (aba HID_AUSENCIAS). Nada foi interpolado.")
    return notas


def linhas_tabela_geracao_anual(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Energia anual da base de EVT e da série oficial de geração por usina."""
    cabecalho = ["Ano", "Base de EVT (GWh)", "Geração por usina (GWh)", "Diferença (MWh)", "Horas só na base de EVT",
                 "Horas só na série oficial"]
    t = res.geracao_oficial.get("anual", pd.DataFrame())
    linhas = [[_rotulo_ano(r.ano, r.ano_parcial), fmt_num(r.energia_base_evt_mwh / 1000, 3),
               fmt_num(r.energia_ons_geracao_mwh / 1000, 3), fmt_num(r.diferenca_mwh, 1), fmt_int(r.horas_so_base_evt),
               fmt_int(r.horas_so_ons_geracao)] for r in t.itertuples()]
    return cabecalho, linhas


def indicadores_capa(res: ResultadosAnalise) -> Tuple[List[Tuple[str, str, str]], str]:
    """Indicadores da capa (rótulo, valor, complemento) e a nota que os acompanha."""
    g = res.globais
    tiles = [
        ("Disponibilidade média declarada", fmt_pct(g["disponibilidade_relativa_pct"]),
         f"da potência instalada; referência da garantia física: {fmt_pct(g['disponibilidade_referencia_pct'])}"),
        ("Fator de capacidade", fmt_pct(g["fator_capacidade_pct"]),
         f"geração média de {fmt_num(g['geracao_media_mwmed'], 1)} MWmed, "
         f"{fmt_pct(g['geracao_sobre_garantia_fisica_pct'])} da garantia física"),
        ("Energia vertida turbinável", f"{fmt_num(g['evt_mwh'] / 1000, 1)} GWh",
         f"{fmt_pct(g['indice_evt_pct'])} de geração + EVT; presente em {fmt_pct(g['horas_com_evt_pct'])} das horas"),
        ("EVT com a usina parada", f"{fmt_num(g['evt_parada_mwh'] / 1000, 1)} GWh",
         f"{fmt_pct(g['evt_parada_pct'])} da EVT, em {fmt_int(g['horas_parada_com_evt'])} h com geração até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW"),
    ]
    p = res.ons.get("disp_periodo")
    t = res.ons.get("taxa_ultima")
    if p and t:
        tiles.insert(1, (
            "Disponibilidade apurada pelo ONS (DISPF)", fmt_pct(p["dispf_pct"]),
            f"média das unidades; TEIFa {fmt_pct(t['teifa_pct'], 2)} e TEIP {fmt_pct(t['teip_pct'], 2)} "
            f"em {fmt_mes_ano(t['mes'])}",
        ))
    if res.ons:
        nota = ("A disponibilidade declarada e o fator de capacidade são calculados a partir do conjunto de EVT; o DISPF, "
                "a TEIFa e a TEIP são os indicadores apurados pelo ONS (seção de indicadores oficiais). O FID não é "
                "publicado pelo ONS. Ver notas metodológicas.")
    else:
        nota = ("Os indicadores de disponibilidade e fator de capacidade são aproximações calculadas a partir dos dados "
                "do ONS e não substituem os índices regulatórios (FID, TEIP, TEIFa). Ver notas metodológicas.")
    return tiles, nota


def pares_identificacao(res: ResultadosAnalise) -> List[Tuple[str, str]]:
    """Bloco "Identificação nos dados do ONS" da capa."""
    c = res.cobertura
    ident = c["identificacao"]
    agentes = "; ".join(
        f"{r.nom_agente} ({fmt_data(r.primeiro_registro)} a {fmt_data(r.ultimo_registro)})" for r in c["agentes"].itertuples()
    )
    return [
        ("cod_usina", f"{ident.get('cod_usina', '')} (código nos modelos de otimização)"),
        ("Reservatório", ident.get("nom_reservatorio", "")),
        ("Rio / bacia", f"{ident.get('nom_rio', '')} / {ident.get('nom_bacia', '')}"),
        ("Subsistema", f"{ident.get('nom_subsistema', '')} ({ident.get('id_subsistema', '')})"),
        ("Agente", agentes),
    ]


def pares_parametros() -> List[Tuple[str, str]]:
    """Bloco "Parâmetros técnicos da usina" da capa."""
    return [
        ("Potência instalada", f"{fmt_num(perfil_ativo().parametros.potencia_instalada_mw, 1)} MW "
                               f"({perfil_ativo().parametros.unidades_geradoras} × {fmt_num(perfil_ativo().parametros.potencia_unitaria_mw, 1)} MW)"),
        ("Turbinas", perfil_ativo().parametros.tipo_turbina),
        ("Engolimento nominal", f"{perfil_ativo().parametros.unidades_geradoras} × {fmt_num(perfil_ativo().parametros.engolimento_nominal_ug_m3s, 1)} m³/s "
                                f"({fmt_num(perfil_ativo().engolimento_maximo_m3s, 1)} m³/s)"),
        ("Garantia física", f"{fmt_num(perfil_ativo().parametros.garantia_fisica_mwmed, 1)} MWmed ({orgao_garantia_fisica()})"),
        ("IP / TEIF de referência", f"{fmt_pct(perfil_ativo().parametros.ip_referencia * 100, 3)} / {fmt_pct(perfil_ativo().parametros.teif_referencia * 100, 3)} "
                                    f"(disponibilidade de referência {fmt_pct(perfil_ativo().disponibilidade_referencia * 100, 2)})"),
    ]


def pares_cobertura(res: ResultadosAnalise) -> List[Tuple[str, str]]:
    """Tabela da seção "Fonte e cobertura dos dados"."""
    c = res.cobertura
    arq = c.get("arquivos") or {}
    man = c.get("manifesto") or {}
    faltantes = c["horas_faltantes"]
    pares = [
        ("Conjunto de dados", f"Energia Vertida Turbinável — ONS ({ONS_DATASET_URL})"),
        ("Critério de extração", f"cod_usina = {perfil_ativo().identificacao.cod_usina} e nome do reservatório conferido"),
    ]
    if arq:
        pares.append(("Arquivos lidos", (
            f"{fmt_int(arq['total'])} arquivos CSV; {fmt_int(arq['com_registros'])} com registros da usina; "
            f"sem registros: {fmt_lista(arq['sem_registros']) or 'nenhum'}; "
            f"falhas de leitura: {fmt_lista(arq['falhas']) or 'nenhuma'}; "
            f"linhas com código ou nome divergentes: {fmt_int(arq['divergencias'])}"
        )))
    if man:
        pares.append(("Versão dos arquivos", (
            f"{fmt_int(man['arquivos'])} arquivos registrados no manifesto; publicação mais recente no portal: "
            f"{fmt_utc(man['ultima_modificacao_mais_recente'])}"
        )))
    pares += [
        ("Período", f"{fmt_data_hora(c['inicio'])} a {fmt_data_hora(c['fim'])}"),
        ("Registros", (
            f"{fmt_int(c['horas_observadas'])} de {fmt_int(c['horas_esperadas'])} horas esperadas; "
            f"horas ausentes: {fmt_lista(fmt_data_hora(t) for t in faltantes[:10]) or 'nenhuma'}; "
            f"horários duplicados: {fmt_int(c['duplicadas'])}"
        )),
        ("Anos parciais", fmt_lista(
            f"{int(r.ano)} ({fmt_pct(r.cobertura_pct)} das horas)" for r in c["por_ano"].itertuples() if r.ano_parcial
        ) or "nenhum"),
    ]
    return pares


def _eventos_longos(res: ResultadosAnalise) -> pd.DataFrame:
    eventos = res.eventos_indisponibilidade_total
    return eventos[eventos["duracao_h"] >= DURACAO_MINIMA_EVENTO_RELATORIO_H] if len(eventos) else eventos


def legenda_figura(res: ResultadosAnalise, chave: str) -> str:
    """Legenda descritiva de cada figura, igual no PDF e no Markdown."""
    c = res.cobertura
    mc = res.mudanca_classificacao
    if chave == "disponibilidade_anual":
        referencia = perfil_ativo().disponibilidade_referencia * 100
        gf_rel = perfil_ativo().parametros.garantia_fisica_mwmed / perfil_ativo().parametros.potencia_instalada_mw * 100
        return ("Barras: disponibilidade média declarada e geração média, em % da potência instalada. Linha tracejada: "
                f"disponibilidade de referência da garantia física ({fmt_pct(referencia)}); linha pontilhada: garantia "
                f"física ({fmt_pct(gf_rel)} da potência instalada).")
    if chave == "serie_temporal":
        longos = _eventos_longos(res)
        return (f"Médias diárias de {fmt_data(c['inicio'])} a {fmt_data(c['fim'])}. Faixas cinza: indisponibilidade total "
                f"com pelo menos {DURACAO_MINIMA_EVENTO_RELATORIO_H} h ({fmt_int(len(longos))} "
                f"{plural(len(longos), 'período', 'períodos')}). Linha tracejada: potência instalada "
                f"({fmt_num(perfil_ativo().parametros.potencia_instalada_mw, 0)} MW); linha pontilhada: garantia física "
                f"({fmt_num(perfil_ativo().parametros.garantia_fisica_mwmed, 1)} MWmed).")
    if chave == "evt_mensal":
        m = res.evt_mensal
        texto = (f"EVT mensal em MWh. Cinza: parcela ocorrida em horas com vertimento de até "
                 f"{fmt_num(perfil_ativo().analises.vertimento_minimo_m3s, 0)} m³/s (patamar contínuo); laranja: demais horas.")
        if mc.get("mes") is not None:
            texto += (f" Linha vertical: {fmt_mes_ano(mc['mes'])}, mês a partir do qual parte do vertimento contínuo passa "
                      "a ser registrada como não turbinável.")
        if len(m):
            maior = m.loc[m["evt_mwh"].idxmax()]
            texto += f" Maior EVT mensal: {fmt_int(maior['evt_mwh'])} MWh em {fmt_mes_ano(maior['mes'])}."
        return texto
    if chave == "perfil_horario":
        return ("Média por ano e hora do dia: à esquerda, geração (MW); à direita, EVT (MWmed). A tabela "
                f"compara a janela diurna ({HORAS_DIURNAS[0]}h às {HORAS_DIURNAS[-1]}h) com a noturna "
                f"({HORAS_NOTURNAS[0]}h às {HORAS_NOTURNAS[-1]}h).")
    if chave == "vazoes_defluentes":
        texto = ("Médias anuais das vazões defluentes (turbinada, vertida turbinável e vertida não turbinável). Linha "
                 f"tracejada: engolimento máximo ({perfil_ativo().parametros.unidades_geradoras} × {fmt_num(perfil_ativo().parametros.engolimento_nominal_ug_m3s, 1)} "
                 "m³/s).")
        if mc.get("mes") is not None:
            texto += (f" A parcela não turbinável contínua aparece a partir de {fmt_mes_ano(mc['mes'])}, "
                      "quando muda a classificação do vertimento contínuo.")
        return texto
    if chave == "disponibilidade_sincronizada":
        return ("Médias mensais da disponibilidade operacional e sincronizada publicadas pelo ONS e da geração. A "
                "operacional coincide com a disponibilidade declarada da base de EVT; a sincronizada mostra a capacidade "
                f"das unidades ligadas à rede. Linha tracejada: potência instalada ({fmt_num(perfil_ativo().parametros.potencia_instalada_mw, 0)} MW).")
    if chave == "faixas_afluencia":
        return ("Horas com energia vertida turbinável por faixa de afluência ao reservatório. Tons de laranja mais "
                "escuros indicam afluência maior; cinza, horas sem dado hidrológico. Número no topo: total de horas com "
                "EVT no ano.")
    if chave == "perfil_hidrologico":
        return ("Médias por hora do dia nos dias com ao menos uma hora de parada com EVT (linhas cheias) e nos demais "
                "dias (tracejadas). Faixa cinza: janela diurna usada no relatório. Valores na aba HID_PERFIL_HORA_DO_DIA.")
    logger.warning("Figura sem legenda descritiva: %s", chave)
    return ""


def textos_tabelas(res: ResultadosAnalise) -> Dict[str, Tuple[str, str]]:
    """Subtítulo e nota de cada tabela (chave do mapa de fontes de ``src/relatorio/fontes.py``), iguais no PDF e no Markdown."""
    eventos = res.eventos_indisponibilidade_total
    paradas = res.eventos_parada_com_evt
    por_ano = (paradas.assign(ano=pd.to_datetime(paradas["inicio"]).dt.year).groupby("ano").size()
               if len(paradas) else pd.Series(dtype=int))
    prog = res.programacao.get("periodo", {}) if res.programacao else {}
    referencia = fmt_pct(perfil_ativo().disponibilidade_referencia * 100, 2)
    return {
        "tab_indicadores_anuais": ("", (
            "* Ano parcial. Disp. média = disponibilidade média declarada ÷ potência instalada; Δ vs ref. GF = diferença "
            f"para a disponibilidade de referência da garantia física ({referencia}); fator de capacidade = geração média "
            "÷ potência instalada; Geração / GF = geração média ÷ garantia física; EVT no vert. mínimo = parcela da EVT "
            f"ocorrida em horas com vertimento de até {fmt_num(perfil_ativo().analises.vertimento_minimo_m3s, 0)} m³/s; índice EVT = EVT ÷ "
            f"(geração + EVT); horas parada c/ EVT = horas com geração até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW e EVT positiva; horas indisp. total = "
            "horas com disponibilidade zero.")),
        "tab_eventos_indisponibilidade": (
            "Períodos de indisponibilidade total (disponibilidade zero) com pelo menos "
            f"{DURACAO_MINIMA_EVENTO_RELATORIO_H} h",
            f"Total de eventos com disponibilidade zero (qualquer duração): {fmt_int(len(eventos))}. A lista completa está "
            "na aba EVENTOS_INDISP_TOTAL da planilha."),
        "tab_ons_disp_anual": (
            "Disponibilidade da usina por ano: declarada no conjunto de EVT e DISPF apurado pelo ONS",
            "* Ano parcial. DISPF da usina = média das unidades ponderada pela potência e pelas horas da base de EVT em "
            f"cada mês; Δ = diferença para a disponibilidade de referência da garantia física ({referencia})."),
        "tab_ons_decomposicao": (
            "TEIFa e TEIP mais recentes: contribuição de cada unidade e parcela de horas",
            f"Contribuição = horas da parcela na janela de {JANELA_TAXAS_MESES} meses (ponderadas pela potência) ÷ denominador da taxa; as "
            "contribuições somam a taxa publicada."),
        "tab_ons_ug_anual": (
            "Indicadores anuais por unidade geradora (base anual do ONS)",
            "* Ano parcial. DISPF, INDISPPF e INDISPFF em % do tempo; DMDFF = duração média dos desligamentos forçados "
            "(h). Não descontam a operação com potência limitada."),
        "tab_ons_horas": (
            "Horas por estado operativo, por ano e unidade geradora",
            "* Ano parcial. " + "; ".join(f"{s} = {d}" for s, d in INSUMOS_HORAS.items())
            + ". HP = HS + HRD + HDP + HDF + HDCE + HEDP + HEDF."),
        "tab_ons_divergencias": (
            "Meses em que o indicador DISPF e as horas do TEIP divergem",
            f"Diferença superior a {fmt_num(TOLERANCIA_DIVERGENCIA_HORAS, 0)} h entre as horas de indisponibilidade "
            "programada ou forçada do DISPF (percentual × horas do período) e as horas HDP ou HDF do conjunto do TEIP."),
        "tab_perfil_horario": ("", ""),
        "tab_evt_por_nivel": ("Distribuição das horas com EVT pelo nível de geração no mesmo horário", ""),
        "tab_eventos_parada_evt": (
            f"Maiores eventos de usina parada (geração até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW) com EVT — {NUMERO_EVENTOS_RELATORIO} maiores por EVT",
            f"Total: {fmt_int(len(paradas))} eventos ({'; '.join(f'{a}: {fmt_int(n)}' for a, n in por_ano.items())}). A "
            "lista completa está na aba EVENTOS_PARADA_COM_EVT da planilha. O conjunto de dados não informa a causa das "
            "paradas."),
        "tab_programacao_mensal": (
            "Horas paradas com EVT por mês e programação do ONS",
            f"Horas comuns à base de EVT e à programação. Usina parada = geração até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW; programação ≤ {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW = o ONS não "
            f"programou geração; > {fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 0)} MW = a usina parou com geração programada. Classificação hora a hora na aba "
            "PROG_HORAS_CLASSIFICADAS da planilha."),
        "tab_programacao_hora": (f"Horas paradas com EVT e programação de até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW, por hora do dia", ""),
        "tab_programacao_eventos": (
            f"Maiores eventos de usina parada com programação acima de {fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 0)} MW ({fmt_int(prog.get('eventos_desvio', 0))} "
            f"eventos, {fmt_int(prog.get('horas_desvio', 0))} h no total)",
            "Ordenados por duração. Lista completa na aba PROG_EVENTOS_DESVIO da planilha."),
        "tab_disponibilidade_anual": (
            "Disponibilidade média por ano",
            "Médias nas horas comuns à base de EVT e à disponibilidade do ONS. * ano parcial; – = sem apuração TEIFa/TEIP "
            "no ano."),
        "tab_disponibilidade_paradas": (
            "Horas com a usina parada, por sincronização, EVT e programação do ONS",
            "Classificação hora a hora na aba DISP_HORAS_PARADAS da planilha."),
        "tab_disponibilidade_divergencias": (
            "Maiores períodos de divergência entre a disponibilidade operacional e a declarada",
            "Lista completa na aba DISP_DIVERGENCIAS da planilha."),
        "tab_faixas_afluencia": (
            "Horas com EVT por faixa de afluência",
            "Cabia nas turbinas = afluência até o engolimento máximo da usina. * ano parcial. Classificação hora a hora na "
            "aba HID_HORAS_EVT da planilha."),
        "tab_faixas_afluencia_evt": (
            "EVT por faixa de afluência (MWh)",
            "Energia vertida turbinável das horas de cada faixa. Cabia nas turbinas = parcela da EVT com afluência até o "
            "engolimento máximo da usina. * ano parcial. Por mês na aba HID_FAIXAS_AFLUENCIA e por ano na aba "
            "HID_FAIXAS_ANUAL da planilha."),
        "tab_hidrologia_anual": (
            "Afluência, vazões, nível e volume útil por ano",
            "Médias sem os valores sinalizados, que saem só do campo afetado (a hora continua nos demais campos). * ano "
            "parcial."),
        "tab_hidrologia_perfil": (
            "Vazões e nível de montante médios por hora do dia",
            "\"c/ parada\" = dias com ao menos uma hora de parada com EVT; \"demais\" = outros dias. Perfil completo na aba "
            "HID_PERFIL_HORA_DO_DIA."),
        "tab_geracao_zero": ("", (
            "Horas em que val_geracao é exatamente zero. * ano parcial; – = mês sem dados na série. Com disp. zero = horas "
            "com disponibilidade declarada zero (indisponibilidade total); com usina disponível = demais horas com geração "
            "zero.")),
        "tab_geracao_oficial": ("", (
            "* ano parcial. Diferença = série oficial − base de EVT. Coincidência = diferença de até "
            f"{fmt_num(TOLERANCIA_COINCIDENCIA_MW, 2)} MW na mesma hora.")),
        "tab_regras_validacao": ("Regras de validação (R1 a R5: consistência interna; R6 a R9: plausibilidade física)", ""),
        "tab_registros_sinalizados": ("Registros sinalizados (plausibilidade física)", ""),
        "tab_extremos": ("Extremos do período, excluídos os registros sinalizados", ""),
        "tab_parametros": ("Parâmetros utilizados", ""),
    }


def linhas_tabela_eventos_indisponibilidade(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Períodos de indisponibilidade total com a duração mínima do relatório (versão do PDF)."""
    cabecalho = ["Início", "Fim", "Duração (h)", "Duração (dias)", "Vazão vertida média (m³/s)"]
    return cabecalho, [
        [fmt_data_hora(r.inicio), fmt_data_hora(r.fim), fmt_int(r.duracao_h), fmt_num(r.duracao_h / 24, 1),
         fmt_num(r.vazao_vertida_media_m3s, 1)]
        for r in _eventos_longos(res).itertuples()
    ]


def linhas_tabela_evt_por_nivel(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Horas com EVT pelo nível de geração na mesma hora (versão do PDF)."""
    cabecalho = ["Geração na hora", "Horas", "EVT (MWh)", "Participação na EVT", "Geração média (MW)",
                 "Disponibilidade média (MW)"]
    return cabecalho, [
        [r.faixa_geracao, fmt_int(r.horas), fmt_num(r.evt_mwh, 1), fmt_pct(r.participacao_evt_pct),
         fmt_num(r.geracao_media_mw, 1), fmt_num(r.disponibilidade_media_mw, 1)]
        for r in res.evt_por_faixa_geracao.itertuples()
    ]


def linhas_tabela_eventos_parada(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Maiores eventos de usina parada com EVT, por EVT."""
    cabecalho = ["Início", "Fim", "Duração (h)", "Disponibilidade média (MW)", "Vazão vertida média (m³/s)", "EVT (MWh)"]
    eventos = res.eventos_parada_com_evt
    if not len(eventos):
        return cabecalho, []
    return cabecalho, [
        [fmt_data_hora(r.inicio), fmt_data_hora(r.fim), fmt_int(r.duracao_h), fmt_num(r.disponibilidade_media_mw, 1),
         fmt_num(r.vazao_vertida_media_m3s, 1), fmt_num(r.evt_mwh, 1)]
        for r in eventos.nlargest(NUMERO_EVENTOS_RELATORIO, "evt_mwh").itertuples()
    ]


def linhas_tabela_perfil_diurno(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """EVT e geração nas janelas diurna e noturna, por ano."""
    cabecalho = ["Ano", "EVT diurna (MWmed)", "EVT noturna (MWmed)", "Razão EVT diurna/noturna", "Geração diurna (MW)",
                 "Geração noturna (MW)", "Geração diurna ÷ noturna"]
    return cabecalho, [
        [f"{int(r.ano)}{'*' if r.ano_parcial else ''}", fmt_num(r.evt_media_diurna_mw, 2), fmt_num(r.evt_media_noturna_mw, 2),
         fmt_num(r.razao_evt_diurna_noturna, 2), fmt_num(r.geracao_media_diurna_mw, 1), fmt_num(r.geracao_media_noturna_mw, 1),
         fmt_pct(r.razao_geracao_diurna_noturna * 100, 0)]
        for r in res.indicadores_anuais.itertuples()
    ]


def linhas_tabela_regras(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Regras de validação R1 a R9 e registros com violação."""
    cabecalho = ["Regra", "Grupo", "Descrição", "Registros com violação", "% dos registros", "Status"]
    return cabecalho, [
        [r.codigo_regra, r.grupo, r.nome_regra, fmt_int(r.violacoes),
         fmt_pct(r.violacoes / r.total_linhas * 100 if r.total_linhas else 0, 3), r.status]
        for r in res.validacao.itertuples()
    ]


def linhas_tabela_registros_sinalizados(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Resumo dos registros sinalizados por regra de plausibilidade física."""
    cabecalho = ["Regra", "Descrição", "Horas", "Primeira ocorrência", "Última ocorrência"]
    return cabecalho, [
        [r.regra, r.descricao, fmt_int(r.horas),
         fmt_data_hora(r.primeira_ocorrencia) if pd.notna(r.primeira_ocorrencia) else "–",
         fmt_data_hora(r.ultima_ocorrencia) if pd.notna(r.ultima_ocorrencia) else "–"]
        for r in res.resumo_anomalias.itertuples()
    ]


def linhas_tabela_extremos(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Máximos e mínimos do período, sem os registros sinalizados."""
    cabecalho = ["Grandeza", "Unidade", "Máximo", "Data/hora do máximo", "Mínimo", "Data/hora do mínimo"]
    return cabecalho, [
        [r.variavel, r.unidade, fmt_num(r.maximo_historico, 3), fmt_data_hora(r.data_hora_max),
         fmt_num(r.minimo_historico, 3), fmt_data_hora(r.data_hora_min)]
        for r in res.extremos.itertuples()
    ]


def linhas_tabela_parametros(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Parâmetros utilizados (grupo, parâmetro, valor, unidade, origem)."""
    cabecalho = ["Grupo", "Parâmetro", "Valor", "Unidade", "Origem"]
    return cabecalho, [[str(r.grupo), str(r.parametro), str(r.valor), str(r.unidade), str(r.origem)]
                       for r in res.parametros.itertuples()]


def pares_identificacao_cadastro(res: ResultadosAnalise) -> List[Tuple[str, str]]:
    """Ficha da usina no cadastro do ONS, no bloco "Cadastro no ONS" da capa (spec da Geração do relatório, FR-012).

    Sem a data da consulta (pedido do usuário em 07/10/2026); a data de obtenção fica na legenda de fonte do bloco.
    """
    f = res.cadastro["ficha"]
    return [
        ("Usina", f"{f.get('nom_usina', '')} · CEG {f.get('ceg', '')} · id ONS {f.get('id_ons', '')}"),
        ("Modalidade de operação", str(f.get("nom_modalidadeoperacao", ""))),
        ("Centro de operação", str(f.get("sgl_centrooperacao", ""))),
        ("Ponto de conexão", str(f.get("nom_pontoconexao", ""))),
        ("Potência autorizada", f"{fmt_num(f.get('val_potenciaautorizada'), 1)} MW"),
        ("Estado · situação na ANEEL", f"{f.get('id_estado', '')} · {f.get('sts_aneel', '')}"),
        ("Homônimos excluídos pelo CEG", fmt_int(f.get("homonimos", 0))),
    ]
