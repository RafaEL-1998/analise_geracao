"""Seções de eólica e solar do relatório (spec da Geração do relatório, FR-045; plano, D19).

Nas EOL e UFV com as bases, em ordem fixa, depois do perfil horário (item 8 da FR-041):

1. fator de capacidade (o publicado, com o nível, e o calculado da série própria);
2. energia cortada por restrição de operação (constrained-off), por mês e por razão;
3. recurso × geração.

A aderência à programação fica na seção comum de programação, com os maiores desvios. Blocos (texto, tabelas e
figuras) comuns ao PDF e ao Markdown, montados só a partir de ``res.renovavel``; os números do conjunto ficam
identificados como tais e os textos não afirmam causa (princípio II).
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.analises.comum import _rotulo_ano
from src.analises.renovavel import TITULO_CORTE, TITULO_FATOR_CAPACIDADE, TITULO_RECURSO
from src.analises.resultados import ResultadosAnalise
from src.coleta import registro
from src.coleta.serie_referencia import escolher
from src.comum.formatacao import fmt_data, fmt_data_hora, fmt_int, fmt_mes_ano, fmt_num, fmt_pct
from src.comum.perfil import perfil_ativo
from src.comum.regras import NUMERO_EVENTOS_RELATORIO, TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW

SECOES_RENOVAVEL: Tuple[str, ...] = ("fator_capacidade", "energia_cortada", "recurso_geracao")
_VARIANTES = {"restricao_detalhe": registro.VARIANTES_RESTRICAO_DETALHE,
              "restricao_razao": registro.VARIANTES_RESTRICAO_RAZAO}
TITULOS: Dict[str, str] = {"fator_capacidade": TITULO_FATOR_CAPACIDADE, "energia_cortada": TITULO_CORTE,
                           "recurso_geracao": TITULO_RECURSO}
# Gênero da grandeza do recurso nos textos ("o vento válido", "a irradiância válida")
_GENERO = {"vento": ("o", "válido", "inválido"), "irradiância": ("a", "válida", "inválida")}


def referencia_restricao() -> bool:
    """A série de referência da usina ativa é a restrição com detalhe (plano da Coleta de dados, D24)."""
    try:
        return escolher(perfil_ativo()).conjunto == "restricao_detalhe"
    except ValueError:
        return False


def pacote_variante(chave: str) -> str:
    """Pacote do ONS da restrição ``chave`` na variante do tipo da usina ativa (eólica ou fotovoltaica); vazio nos
    demais tipos."""
    variantes = _VARIANTES[chave]
    return variantes.get(registro.tipo_da_usina(perfil_ativo()), ("", ""))[0]


def _r(res: ResultadosAnalise) -> Dict:
    return getattr(res, "renovavel", None) or {}


def _traco(valor: Optional[float], casas: int = 0, pct: bool = False) -> str:
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "—"
    return fmt_pct(valor) if pct else fmt_num(valor, casas)


def nivel_texto(res: ResultadosAnalise, nivel: str) -> str:
    """"usina" ou "conjunto de usinas <nome> (<id>)"."""
    if nivel != "conjunto":
        return "usina"
    ident = perfil_ativo().identificacao
    nome = (res.niveis.get("geracao") or {}).get("nome") or ""
    return f"conjunto de usinas {nome}, id ONS {ident.id_conjunto}" if nome else \
        f"conjunto de usinas, id ONS {ident.id_conjunto}"


def _ano_parcial_semi(periodo: object, semi_horas: int) -> bool:
    ano = int(periodo)
    horas = (pd.Timestamp(ano + 1, 1, 1) - pd.Timestamp(ano, 1, 1)) / pd.Timedelta(hours=1)
    return semi_horas < 2 * horas


def _fc_calculado(res: ResultadosAnalise) -> Dict[int, float]:
    """Fator de capacidade calculado neste relatório, por ano, da série própria (indicadores anuais comuns)."""
    a = res.comum.get("anuais")
    if a is None or not len(a):
        return {}
    usina = a[(a["nivel"] == "usina") & a["fator_capacidade_pct"].notna()]
    return {int(r.ano): float(r.fator_capacidade_pct) for r in usina.itertuples()}


def _genero(grandeza: str) -> Tuple[str, str, str]:
    return _GENERO.get(grandeza, ("o", "válido", "inválido"))


# ---------------------------------------------------------------------------
# Linhas das tabelas
# ---------------------------------------------------------------------------


def linhas_tabela_fc_anual(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    anual = _r(res)["fator_capacidade"]["anual"]
    calculado = _fc_calculado(res)
    cabecalho = ["Ano", "Nível", "Horas", "Geração verificada (MWh)", "Capacidade média (MW)", "FC publicado"]
    if calculado:
        cabecalho.append("FC calculado (usina)")
    cabecalho += ["Horas com FC fora de 0 a 1", "Horas acima da capacidade"]
    linhas = []
    for r in anual.itertuples():
        linha = [_rotulo_ano(r.periodo, r.ano_parcial), "conjunto" if r.nivel == "conjunto" else "usina",
                 fmt_int(r.horas), fmt_num(r.geracao_verificada_mwh, 0), fmt_num(r.capacidade_media_mw, 1),
                 _traco(r.fator_capacidade_pct, pct=True)]
        if calculado:
            linha.append(_traco(calculado.get(int(r.periodo)), pct=True))
        linha += [fmt_int(r.horas_fc_fora_0_1), fmt_int(r.horas_acima_capacidade)]
        linhas.append(linha)
    return cabecalho, linhas


def linhas_tabela_corte_anual(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    anual = _r(res)["restricao"]["anual"]
    cabecalho = ["Ano", "Verificada (MWh)", "Estimada (MWh)", "Cortada (MWh)", "% da estimada", "Horas restritas",
                 "Restritas sem estimativa", "Semi-horas sem a marca", "Diferença bruta (MWh)"]
    linhas = [[_rotulo_ano(r.periodo, _ano_parcial_semi(r.periodo, r.semi_horas)), fmt_num(r.energia_verificada_mwh, 0),
               fmt_num(r.energia_estimada_mwh, 0), fmt_num(r.energia_cortada_mwh, 0), _traco(r.pct_estimada, pct=True),
               fmt_num(r.horas_restritas, 1), fmt_int(r.semi_horas_restritas_sem_estimativa),
               fmt_int(r.semi_horas_sem_marca), fmt_num(r.diferenca_bruta_mwh, 0)]
              for r in anual.itertuples()]
    return cabecalho, linhas


def linhas_tabela_corte_razao(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    t = _r(res)["restricao"]["por_razao"]
    return (["Razão", "Semi-horas restritas", "Energia cortada (MWh)", "% da cortada"],
            [[str(r.descricao), fmt_int(r.semi_horas), fmt_num(r.energia_cortada_mwh, 0), _traco(r.pct_cortada, pct=True)]
             for r in t.itertuples()])


def linhas_tabela_recurso(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    rec = _r(res)["recurso"]
    casas = 0 if float(rec["largura"]).is_integer() else 1
    return ([f"Faixa de {rec['grandeza']} ({rec['unidade']})", "Semi-horas", "Geração verificada média (MW)",
             "Geração estimada média (MW)"],
            [[f"{fmt_num(r.faixa_inicio, casas)} a {fmt_num(r.faixa_fim, casas)}", fmt_int(r.semi_horas),
              fmt_num(r.geracao_media_mw, 1), fmt_num(r.estimada_media_mw, 1)] for r in rec["faixas"].itertuples()])


def linhas_tabela_desvios_programacao(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    d = _r(res)["programacao"]["maiores_desvios"]
    return (["Hora", "Programada (MW)", "Verificada (MW)", "Desvio (MW)"],
            [[fmt_data_hora(r.din_instante), fmt_num(r.geracao_programada_mw, 1), fmt_num(r.geracao_mw, 1),
              fmt_num(r.desvio_mw, 1)] for r in d.itertuples()])


# ---------------------------------------------------------------------------
# Textos das tabelas, legendas e nota
# ---------------------------------------------------------------------------


def _razao_do_conjunto(res: ResultadosAnalise) -> str:
    c = _r(res).get("restricao") or {}
    if c.get("nivel_razao") != "conjunto":
        return ""
    return f" A razão é a do {nivel_texto(res, 'conjunto')}; a energia cortada é a da usina."


def textos_tabelas(res: ResultadosAnalise) -> Dict[str, Tuple[str, str]]:
    """Subtítulo e nota das tabelas das seções de eólica e solar."""
    r = _r(res)
    textos: Dict[str, Tuple[str, str]] = {}
    if r.get("fator_capacidade"):
        textos["tab_fc_anual"] = ("Fator de capacidade por ano", (
            "* Ano parcial. FC publicado = Σ geração verificada ÷ Σ capacidade instalada nas horas com os dois dados, "
            "no nível publicado pelo ONS"
            + ("; FC calculado = geração média da usina na série de referência ÷ potência instalada do perfil"
               if _fc_calculado(res) else "")
            + f". Horas com FC fora de 0 a 1 ou geração acima da capacidade (folga de "
              f"{fmt_num(TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW, 0)} MW) são sinalizadas e ficam nos totais."))
    if r.get("restricao"):
        textos["tab_corte_anual"] = ("Energia cortada por restrição de operação por ano", (
            "* Ano parcial. Verificada e estimada nas semi-horas com a estimativa do ONS (estimada 0 com a usina "
            "gerando = estimativa ausente). Cortada = Σ máx(estimada − verificada, 0) × 0,5 h nas semi-horas com a "
            "marca de restrição; % sobre a estimada das semi-horas com a marca; restritas sem estimativa = semi-horas "
            "com a marca em que o corte não pôde ser calculado; diferença bruta = o mesmo cálculo em todas as "
            "semi-horas com estimativa, para comparação."))
        textos["tab_corte_razao"] = ("Energia cortada por razão da restrição", (
            "Razão de cada semi-hora restrita na Restrição com a razão; sem razão publicada = semi-hora restrita sem o "
            "código." + _razao_do_conjunto(res)))
    if r.get("recurso"):
        rec = r["recurso"]
        textos["tab_recurso_faixas"] = (f"Geração por faixa de {rec['grandeza']}", (
            f"Só as semi-horas com {_genero(rec['grandeza'])[0]} {rec['grandeza']} {_genero(rec['grandeza'])[1]}, até o "
            f"limite físico de {fmt_num(rec['limite'], 0)} {rec['unidade']}, e a geração verificada; o valor negativo "
            "(ruído de medição) entra na primeira faixa."))
    if r.get("programacao"):
        textos["tab_desvios_programacao_renovavel"] = (
            "Maiores desvios entre a geração verificada e a programada",
            f"Até {NUMERO_EVENTOS_RELATORIO} horas, as de maior desvio absoluto, no nível da programação; a lista "
            "completa está na planilha.")
    return textos


def legenda_figura(res: ResultadosAnalise, chave: str) -> str:
    r = _r(res)
    if chave == "fc_mensal":
        fc = r["fator_capacidade"]
        p = fc["resumo"]
        calculado = " e o calculado neste relatório da geração da usina e da potência instalada do perfil" \
            if _fc_calculado(res) else ""
        return (f"Fator de capacidade mensal publicado pelo ONS ({nivel_texto(res, fc['nivel'])}){calculado} (%), de "
                f"{fmt_mes_ano(p['inicio'])} a {fmt_mes_ano(p['fim'])}.")
    if chave == "corte_razao_mensal":
        return ("Energia cortada por restrição de operação em cada mês (MWh), por razão, só nas semi-horas com a marca "
                "de restrição." + _razao_do_conjunto(res))
    if chave == "recurso_geracao":
        rec = r["recurso"]
        artigo, _, invalido = _genero(rec["grandeza"])
        return (f"Geração verificada e estimada médias por faixa de {rec['grandeza']} ({rec['unidade']}), sem as "
                f"semi-horas com {artigo} {rec['grandeza']} {invalido} ou acima de {fmt_num(rec['limite'], 0)} "
                f"{rec['unidade']}.")
    if chave == "desvio_programacao":
        return ("Desvio médio e desvio médio absoluto mensais entre a geração verificada e a programada (MW), nas horas "
                "comuns às duas, no nível da programação.")
    return ""


def nota(res: ResultadosAnalise) -> str:
    """Nota metodológica das seções de eólica e solar."""
    r = _r(res)
    partes = []
    if r.get("restricao"):
        partes.append("Energia cortada: só nas semi-horas com a marca de restrição da Restrição com detalhe, pela "
                      "geração estimada menos a verificada, sem valores negativos; a semi-hora sem a marca (arquivo "
                      "publicado sem a coluna) fica fora do total e é contada.")
        if r["restricao"]["resumo"]["semi_horas_sem_estimativa"]:
            partes.append("A geração estimada 0 com a usina gerando é estimativa que o ONS não calculou: fica fora dos "
                          "totais e das médias da estimada e, nas semi-horas com a marca de restrição, o corte não é "
                          "calculado.")
        partes.append("As semi-horas são levadas à hora cheia pela média das duas meias-horas só nos cruzamentos com "
                      "séries horárias; a hora com uma só meia-hora fica ausente.")
    if r.get("recurso"):
        rec = r["recurso"]
        partes.append(f"O recurso marcado como inválido pelo ONS ou acima do limite físico ({fmt_num(rec['limite'], 0)} "
                      f"{rec['unidade']}) fica fora das faixas do recurso × geração.")
    return " ".join(partes)


# ---------------------------------------------------------------------------
# Blocos
# ---------------------------------------------------------------------------


def blocos(res: ResultadosAnalise, chave: str) -> list:
    """Blocos de cada seção de eólica e solar, na ordem em que o PDF e o Markdown os mostram."""
    from src.relatorio.comum import Bloco, _numericas, _tabela

    r = _r(res)
    b = []
    if chave == "fator_capacidade":  # o publicado e o nível estão na constatação; aqui, só o calculado
        if _fc_calculado(res):
            b.append(Bloco("texto", textos=[
                f"O fator de capacidade calculado neste relatório, da geração da usina e da potência instalada do perfil "
                f"({fmt_num(perfil_ativo().parametros.potencia_instalada_mw, 1)} MW), fica na tabela ao lado do "
                "publicado."]))
        cab, linhas = linhas_tabela_fc_anual(res)
        b.append(_tabela("tab_fc_anual", (cab, linhas), [0.6, 0.8] + [1.0] * (len(cab) - 2), _numericas(cab, 2)))
        b.append(Bloco("figura", "fc_mensal"))
    elif chave == "energia_cortada":
        c = r["restricao"]["resumo"]  # a energia e as parcelas estão na constatação
        texto = (f"Restrição com detalhe de {fmt_data(c['inicio'])} a {fmt_data(c['fim'])} "
                 f"({fmt_int(c['semi_horas'])} semi-horas), com a marca de restrição em "
                 f"{fmt_int(c['semi_horas_restritas'])} ({fmt_num(c['horas_restritas'], 1)} horas). Fora das semi-horas "
                 "restritas, a diferença entre a estimada e a verificada é erro da estimativa e não entra no corte.")
        b.append(Bloco("texto", textos=[texto + _razao_do_conjunto(res)]))
        cab, linhas = linhas_tabela_corte_anual(res)
        b.append(_tabela("tab_corte_anual", (cab, linhas), [0.6] + [1.0] * (len(cab) - 1), _numericas(cab, 1)))
        cab, linhas = linhas_tabela_corte_razao(res)
        if linhas:
            b.append(_tabela("tab_corte_razao", (cab, linhas), [2.2, 1.0, 1.0, 0.8], _numericas(cab, 1)))
            b.append(Bloco("figura", "corte_razao_mensal"))
        else:
            b.append(Bloco("sem_linhas", "tab_corte_razao", textos=["Nenhuma semi-hora com a marca de restrição."]))
    elif chave == "recurso_geracao":
        rec = r["recurso"]
        s = rec["resumo"]
        artigo, valido, _ = _genero(rec["grandeza"])  # as semi-horas inválidas estão na constatação
        b.append(Bloco("texto", textos=[
            f"Geração por faixa de {rec['grandeza']} ({fmt_num(rec['largura'], 0)} {rec['unidade']} por faixa), nas "
            f"{fmt_int(s['semi_horas_validas'])} semi-horas com {artigo} {rec['grandeza']} {valido}."]))
        cab, linhas = linhas_tabela_recurso(res)
        if linhas:
            b.append(_tabela("tab_recurso_faixas", (cab, linhas), [1.2, 0.8, 1.2, 1.2], _numericas(cab, 1)))
            b.append(Bloco("figura", "recurso_geracao"))
    return b


def blocos_programacao(res: ResultadosAnalise) -> list:
    """Aderência à programação das eólicas e solares, na seção comum de programação: os maiores desvios."""
    from src.relatorio.comum import Bloco, _numericas, _tabela

    p = _r(res).get("programacao") or {}
    if not p or not len(p["maiores_desvios"]):
        return []
    cab, linhas = linhas_tabela_desvios_programacao(res)
    return [_tabela("tab_desvios_programacao_renovavel", (cab, linhas), [1.4, 1.0, 1.0, 1.0], _numericas(cab, 1)),
            Bloco("figura", "desvio_programacao")]
