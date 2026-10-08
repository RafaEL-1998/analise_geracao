"""Tabela de parâmetros do relatório: do perfil, das regras gerais e das datas de obtenção (spec das Análises, FR-042)."""

from __future__ import annotations


import pandas as pd

from src.analises.resultados import ResultadosAnalise
from src.analises.comum import _data_obtencao_texto, _rotulo_janela
from src.comum.formatacao import fmt_data, fmt_num, fmt_pct
from src.comum.perfil import perfil_ativo
from src.comum.regras import (
    CONJUNTO_CADASTRO,
    CONJUNTO_DISPONIBILIDADE,
    CONJUNTO_GERACAO,
    CONJUNTO_HIDROLOGIA,
    CONJUNTO_PROGRAMACAO_DIARIA,
    CONJUNTOS_INDICADORES_ONS,
    FAIXA_PRODUTIVIDADE_RELATIVA,
    FRACAO_PLENA_CARGA,
    HORAS_DIURNAS,
    HORAS_NOTURNAS,
    LIMIAR_DESVIO_PROGRAMACAO_MW,
    LIMIAR_GERACAO_PARADA_MW,
    LIMIAR_INDISPONIBILIDADE_TOTAL_MW,
    LIMIAR_SINCRONIZADA_MW,
    META_ALINHAMENTO_HIDROLOGIA_PCT,
    ONS_DATASET_URL,
    ONS_PORTAL_DATASET_URL,
    TOLERANCIA_COINCIDENCIA_MW,
    TOLERANCIA_COINCIDENCIA_VAZAO_M3S,
    TOLERANCIA_DIVERGENCIA_HORAS,
    TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW,
    TOLERANCIA_LIMITES_FISICOS,
)
from src.tratamento.validacao import faixa_produtividade


def tabela_parametros(com_indicadores: bool = False, com_programacao: bool = False) -> pd.DataFrame:
    """Parâmetros da usina e da análise, com a respectiva origem."""
    prod_min, prod_max = faixa_produtividade(perfil_ativo())
    calculado = "Calculado a partir dos parâmetros acima"
    analise = "Parâmetro de análise"
    rf = perfil_ativo().parametros.fontes.geral
    linhas = [
        ("Usina", "Potência instalada", fmt_num(perfil_ativo().parametros.potencia_instalada_mw, 1), "MW", rf),
        ("Usina", "Unidades geradoras", f"{perfil_ativo().parametros.unidades_geradoras} × {fmt_num(perfil_ativo().parametros.potencia_unitaria_mw, 1)}", "MW", rf),
        ("Usina", "Tipo de turbina", perfil_ativo().parametros.tipo_turbina, "", rf),
        ("Usina", "Engolimento nominal por unidade", fmt_num(perfil_ativo().parametros.engolimento_nominal_ug_m3s, 1), "m³/s", rf),
        ("Usina", "Garantia física", fmt_num(perfil_ativo().parametros.garantia_fisica_mwmed, 1), "MWmed", perfil_ativo().parametros.fontes.garantia_fisica),
        ("Usina", "Indisponibilidade programada de referência (IP)", fmt_num(perfil_ativo().parametros.ip_referencia * 100, 3), "%", rf),
        ("Usina", "Indisponibilidade forçada de referência (TEIF)", fmt_num(perfil_ativo().parametros.teif_referencia * 100, 3), "%", rf),
        ("Usina", "Queda bruta", fmt_num(perfil_ativo().parametros.queda_bruta_m, 2), "m", rf),
        ("Usina", "Perda hidráulica", fmt_num(perfil_ativo().parametros.perda_hidraulica_m, 3), "m", rf),
        ("Usina", "Rendimento turbina e gerador", fmt_num(perfil_ativo().parametros.rendimento_turbina_gerador * 100, 2), "%", rf),
        ("Usina", "Vazão remanescente", fmt_num(perfil_ativo().parametros.vazao_remanescente_m3s, 2), "m³/s", rf),
        ("Usina", "Início da operação comercial", str(perfil_ativo().usina.inicio_operacao_comercial), "", perfil_ativo().parametros.fontes.inicio_operacao_comercial or ""),
        ("Derivado", "Engolimento máximo da usina", fmt_num(perfil_ativo().engolimento_maximo_m3s, 1), "m³/s", f"{calculado}: unidades × engolimento nominal"),
        ("Derivado", "Disponibilidade de referência da GF", fmt_num(perfil_ativo().disponibilidade_referencia * 100, 2), "%", f"{calculado}: (1 − IP) × (1 − TEIF)"),
        ("Derivado", "Produtividade nominal teórica", fmt_num(perfil_ativo().produtividade_nominal_mw_m3s, 4), "MW/(m³/s)", f"{calculado}: 9,81 × (queda bruta − perda) × rendimento ÷ 1.000"),
        ("Análise", "Usina parada", f"geração ≤ {fmt_num(LIMIAR_GERACAO_PARADA_MW, 1)}", "MW", analise),
        ("Análise", "Plena carga", f"geração ≥ {fmt_num(FRACAO_PLENA_CARGA * perfil_ativo().parametros.potencia_instalada_mw, 1)}", "MW", f"{analise}: {fmt_pct(FRACAO_PLENA_CARGA * 100, 0)} da potência instalada"),
        ("Análise", "Vertimento mínimo (patamar contínuo)", f"vazão vertida ≤ {fmt_num(perfil_ativo().analises.vertimento_minimo_m3s, 1)}", "m³/s", f"{analise}: {perfil_ativo().analises.fontes.vertimento_minimo}" if perfil_ativo().analises.fontes.vertimento_minimo else analise),
        ("Análise", "Indisponibilidade total", f"disponibilidade ≤ {fmt_num(LIMIAR_INDISPONIBILIDADE_TOTAL_MW, 3)}", "MW", analise),
        ("Análise", "Janela diurna / noturna", f"{_rotulo_janela(HORAS_DIURNAS)} / {_rotulo_janela(HORAS_NOTURNAS)}", "", analise),
        ("Validação", "Tolerância sobre limites nominais (R6)", fmt_num(TOLERANCIA_LIMITES_FISICOS * 100, 0), "%", analise),
        ("Validação", "Faixa de produtividade (R8)", f"{fmt_num(prod_min, 3)} a {fmt_num(prod_max, 3)}", "MW/(m³/s)", f"{analise}: {fmt_pct(FAIXA_PRODUTIVIDADE_RELATIVA[0] * 100, 0)} a {fmt_pct(FAIXA_PRODUTIVIDADE_RELATIVA[1] * 100, 0)} da nominal"),
        ("Validação", "Tolerância de geração acima da disponibilidade (R7)", fmt_num(TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW, 1), "MW", analise),
        ("Fonte", "Conjunto de dados", "Energia Vertida Turbinável (ONS)", "", ONS_DATASET_URL),
    ]
    if com_indicadores:
        linhas.append(("Fonte", "Identificação nos indicadores do ONS", f"CEG {perfil_ativo().identificacao.ceg} · id ONS {perfil_ativo().identificacao.id_ons}", "",
                       "Conjuntos de indicadores por unidade geradora do ONS"))
        linhas += [
            ("Fonte", "Conjunto de dados", descricao, "", f"{ONS_PORTAL_DATASET_URL}{conjunto}")
            for conjunto, descricao in CONJUNTOS_INDICADORES_ONS.items()
        ]
        linhas.append(("Validação", "Tolerância entre indicador DISPF e horas do TEIP",
                       fmt_num(TOLERANCIA_DIVERGENCIA_HORAS, 1), "h", analise))
    if com_programacao:
        linhas += [
            ("Fonte", "Conjunto de dados", f"Dados dos Valores da Programação Diária (ONS), usina {perfil_ativo().identificacao.cod_programacao}",
             "", f"{ONS_PORTAL_DATASET_URL}{CONJUNTO_PROGRAMACAO_DIARIA}"),
            ("Análise", "Programação zero", f"programação ≤ {fmt_num(LIMIAR_GERACAO_PARADA_MW, 1)}", "MW",
             f"{analise}: mesmo limiar de usina parada"),
            ("Análise", "Desvio da programação", f"usina parada com programação > {fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 1)}",
             "MW", analise),
        ]
    return pd.DataFrame(linhas, columns=["grupo", "parametro", "valor", "unidade", "origem"])


ORIGEM_ANALISE = "Parâmetro de análise"


def parametros_geracao_cadastro(res: "ResultadosAnalise") -> pd.DataFrame:
    """Fontes da geração por usina e do cadastro (linhas da tabela de parâmetros)."""
    linhas = []
    g = res.geracao_oficial
    if g:
        r = g["resumo"]
        linhas.append(("Fonte", "Conjunto de dados",
                       f"Geração por usina (ONS), id ONS {perfil_ativo().identificacao.id_ons} · CEG {perfil_ativo().identificacao.ceg}; {fmt_data(r['inicio'])} a "
                       f"{fmt_data(r['fim'])}; {_data_obtencao_texto(g['obtido_em'])}", "",
                       f"{ONS_PORTAL_DATASET_URL}{CONJUNTO_GERACAO}"))
    c = res.cadastro
    if c:
        linhas.append(("Fonte", "Conjunto de dados",
                       f"Modalidade das usinas (ONS), CEG {perfil_ativo().identificacao.ceg}; cadastro sem série histórica; "
                       f"{_data_obtencao_texto(c['obtido_em'])}", "", f"{ONS_PORTAL_DATASET_URL}{CONJUNTO_CADASTRO}"))
    return pd.DataFrame(linhas, columns=["grupo", "parametro", "valor", "unidade", "origem"])


def parametros_hidrologia(res: "ResultadosAnalise") -> pd.DataFrame:
    """Fonte, faixas, tolerância e meta do alinhamento da hidrologia (linhas da tabela de parâmetros)."""
    r = res.hidrologia["resumo"]
    linhas = [
        ("Fonte", "Conjunto de dados",
         f"Dados hidrológicos horários (ONS), cod_usina {perfil_ativo().identificacao.cod_usina} · reservatório {perfil_ativo().identificacao.id_reservatorio}; "
         f"{fmt_data(r['inicio'])} a {fmt_data(r['fim'])}; {_data_obtencao_texto(res.hidrologia['obtido_em'])}",
         "", f"{ONS_PORTAL_DATASET_URL}{CONJUNTO_HIDROLOGIA}"),
        ("Análise", "Faixas de afluência nas horas com EVT",
         f"até {fmt_num(perfil_ativo().parametros.engolimento_nominal_ug_m3s, 1)} / até {fmt_num(perfil_ativo().engolimento_maximo_m3s, 1)} / acima", "m³/s",
         f"{ORIGEM_ANALISE}: engolimento de uma unidade e da usina"),
        ("Validação", "Alinhamento com a base de EVT (vazões turbinada e vertida)",
         f"coincidência ≥ {fmt_num(META_ALINHAMENTO_HIDROLOGIA_PCT, 0)}% com diferença ≤ "
         f"{fmt_num(TOLERANCIA_COINCIDENCIA_VAZAO_M3S, 1)} m³/s", "", ORIGEM_ANALISE),
    ]
    return pd.DataFrame(linhas, columns=["grupo", "parametro", "valor", "unidade", "origem"])


def parametros_disponibilidade(res: "ResultadosAnalise") -> pd.DataFrame:
    """Fonte, limiar e tolerância da disponibilidade (linhas da tabela de parâmetros)."""
    r = res.disponibilidade["resumo"]
    linhas = [
        ("Fonte", "Conjunto de dados",
         f"Disponibilidade por usina (ONS), id ONS {perfil_ativo().identificacao.id_ons} · CEG {perfil_ativo().identificacao.ceg}; {fmt_data(r['inicio'])} a "
         f"{fmt_data(r['fim'])}; {_data_obtencao_texto(res.disponibilidade['obtido_em'])}",
         "", f"{ONS_PORTAL_DATASET_URL}{CONJUNTO_DISPONIBILIDADE}"),
        ("Análise", "Unidade sincronizada", f"disponibilidade sincronizada > {fmt_num(LIMIAR_SINCRONIZADA_MW, 1)}", "MW",
         ORIGEM_ANALISE),
        ("Validação", "Coincidência entre fontes", f"diferença ≤ {fmt_num(TOLERANCIA_COINCIDENCIA_MW, 2)}", "MW",
         ORIGEM_ANALISE),
    ]
    return pd.DataFrame(linhas, columns=["grupo", "parametro", "valor", "unidade", "origem"])
