"""Relatório em Markdown, com as mesmas seções, tabelas e figuras do PDF."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.analises.conclusao import FRASE_ABERTURA_CONCLUSAO, FRASE_CONCLUSAO_VAZIA
from src.analises.constatacoes import texto_conferencia_geracao
from src.analises.resultados import ResultadosAnalise
from src.comum.formatacao import fmt_data, fmt_data_hora, fmt_int, fmt_lista
from src.comum.logger import setup_logger
from src.comum.perfil import perfil_ativo
from src.relatorio.conteudo import (
    indicadores_capa,
    legenda_figura,
    linhas_tabela_anual,
    linhas_tabela_disponibilidade_anual,
    linhas_tabela_disponibilidade_divergencias,
    linhas_tabela_disponibilidade_paradas,
    linhas_tabela_eventos_indisponibilidade,
    linhas_tabela_eventos_parada,
    linhas_tabela_evt_por_nivel,
    linhas_tabela_extremos,
    linhas_tabela_faixas_afluencia,
    linhas_tabela_faixas_afluencia_evt,
    linhas_tabela_geracao_anual,
    linhas_tabela_geracao_zero,
    linhas_tabela_hidrologia_anual,
    linhas_tabela_ons_decomposicao,
    linhas_tabela_ons_disponibilidade,
    linhas_tabela_ons_divergencias,
    linhas_tabela_ons_horas,
    linhas_tabela_ons_ug_anual,
    linhas_tabela_parametros,
    linhas_tabela_perfil_diurno,
    linhas_tabela_perfil_hidrologico,
    linhas_tabela_programacao_eventos,
    linhas_tabela_programacao_mensal,
    linhas_tabela_programacao_perfil,
    linhas_tabela_registros_sinalizados,
    linhas_tabela_regras,
    listas_conclusao,
    notas_disponibilidade,
    notas_hidrologia,
    notas_metodologicas,
    pares_cobertura,
    pares_identificacao,
    pares_identificacao_cadastro,
    pares_parametros,
    texto_taxas_ons,
    textos_tabelas,
)
from src.relatorio.estrutura import constatacoes_da_secao, secoes_presentes, sumario
from src.relatorio.fontes import legenda_fonte

logger = setup_logger("relatorio")


def _tabela_md(cabecalho: List[str], linhas: List[List[str]]) -> List[str]:
    saida = ["| " + " | ".join(cabecalho) + " |", "| " + " | ".join(["---"] * len(cabecalho)) + " |"]
    saida += ["| " + " | ".join(linha) + " |" for linha in linhas]
    return saida


def _fonte_md(res: ResultadosAnalise, chave: str) -> List[str]:
    """Legenda de fonte logo abaixo de uma tabela do Markdown, seguida de linha em branco."""
    return [legenda_fonte(res, chave), ""]


def _ancora_md(titulo: str) -> str:
    """Âncora de um título "## n. Título" no padrão do GitHub (minúsculas, sem pontuação, hífens)."""
    return re.sub(r"[^\w\- ]", "", titulo.strip().lower()).replace(" ", "-")


def _nota_md(texto: str) -> str:
    return texto.replace("*", "\\*")


def _md_tabela(res: ResultadosAnalise, textos: Dict[str, Tuple[str, str]], chave: str, cabecalho: List[str],
               linhas: List[List[str]], intro: str = "") -> List[str]:
    """Subtítulo, texto de abertura, tabela, nota e legenda de fonte (mesmos textos do PDF)."""
    subtitulo, nota = textos.get(chave, ("", ""))
    saida: List[str] = [f"### {subtitulo}", ""] if subtitulo else []
    if intro:
        saida += [intro, ""]
    saida += _tabela_md(cabecalho, linhas) + [""]
    if nota:
        saida += [_nota_md(nota), ""]
    return saida + _fonte_md(res, chave)


def _md_chave_valor(res: ResultadosAnalise, titulo: str, pares: List[Tuple[str, str]], chave: str,
                    nota: str = "") -> List[str]:
    saida = ([f"### {titulo}", ""] if titulo else []) + _tabela_md(["Item", "Valor"], [[k, v] for k, v in pares]) + [""]
    if nota:
        saida += [nota, ""]
    return saida + _fonte_md(res, chave)


def _md_figura(res: ResultadosAnalise, figuras: Optional[Dict[str, Path]], chave: str, titulo: str) -> List[str]:
    """Figura no corpo da seção, com a legenda descritiva e a legenda de fonte (FR-017)."""
    caminho = (figuras or {}).get(chave)
    if caminho is None:
        return []
    return [f"![{titulo}](figures/{Path(caminho).name})", "", legenda_figura(res, chave), "", legenda_fonte(res, chave), ""]


def _md_conteudo_secao(res: ResultadosAnalise, chave: str, titulo: str, figuras: Optional[Dict[str, Path]],
                       textos: Dict[str, Tuple[str, str]]) -> List[str]:
    """Tabelas, figuras e notas de cada seção, na mesma ordem do PDF."""
    tab = lambda c, cl, intro="": _md_tabela(res, textos, c, cl[0], cl[1], intro)  # noqa: E731
    fig = lambda c: _md_figura(res, figuras, c, titulo)  # noqa: E731
    saida: List[str] = []
    if chave == "cobertura":
        saida += _md_chave_valor(res, "", pares_cobertura(res), "tab_cobertura")
    elif chave == "indicadores_anuais":
        saida += tab("tab_indicadores_anuais", linhas_tabela_anual(res))
    elif chave == "disponibilidade_geracao":
        saida += fig("disponibilidade_anual")
        cabecalho, linhas = linhas_tabela_eventos_indisponibilidade(res)
        if linhas:
            saida += tab("tab_eventos_indisponibilidade", (cabecalho, linhas))
        else:
            saida += [f"### {textos['tab_eventos_indisponibilidade'][0]}", "", "Nenhum período com essa duração.", ""]
    elif chave == "indicadores_ons":
        for c, funcao in (("tab_ons_disp_anual", linhas_tabela_ons_disponibilidade),
                          ("tab_ons_decomposicao", linhas_tabela_ons_decomposicao),
                          ("tab_ons_ug_anual", linhas_tabela_ons_ug_anual), ("tab_ons_horas", linhas_tabela_ons_horas),
                          ("tab_ons_divergencias", linhas_tabela_ons_divergencias)):
            cabecalho, linhas = funcao(res)
            if linhas:
                saida += tab(c, (cabecalho, linhas), texto_taxas_ons(res) if c == "tab_ons_decomposicao" else "")
    elif chave in ("serie_temporal", "evt_mensal"):
        saida += fig(chave)
    elif chave == "perfil_horario":
        saida += fig("perfil_horario") + tab("tab_perfil_horario", linhas_tabela_perfil_diurno(res))
    elif chave == "eventos":
        saida += tab("tab_evt_por_nivel", linhas_tabela_evt_por_nivel(res))
        cabecalho, linhas = linhas_tabela_eventos_parada(res)
        saida += (tab("tab_eventos_parada_evt", (cabecalho, linhas)) if linhas
                  else [f"### {textos['tab_eventos_parada_evt'][0]}", "", "Nenhum evento.", ""])
    elif chave == "programacao":
        for c, funcao in (("tab_programacao_mensal", linhas_tabela_programacao_mensal),
                          ("tab_programacao_hora", linhas_tabela_programacao_perfil),
                          ("tab_programacao_eventos", linhas_tabela_programacao_eventos)):
            cabecalho, linhas = funcao(res)
            if linhas:
                saida += tab(c, (cabecalho, linhas))
        ausentes = res.programacao["periodo"]["lista_dias_ausentes"]
        if ausentes:
            saida += [f"Dias sem arquivo de programação no portal do ONS: {fmt_lista(fmt_data(d) for d in ausentes)}.", ""]
    elif chave == "disponibilidade_sincronizada":
        cabecalho, linhas = linhas_tabela_disponibilidade_anual(res)
        if linhas:
            saida += tab("tab_disponibilidade_anual", (cabecalho, linhas))
        saida += fig("disponibilidade_sincronizada")
        for c, funcao in (("tab_disponibilidade_paradas", linhas_tabela_disponibilidade_paradas),
                          ("tab_disponibilidade_divergencias", linhas_tabela_disponibilidade_divergencias)):
            cabecalho, linhas = funcao(res)
            if linhas:
                saida += tab(c, (cabecalho, linhas))
        saida += [f"- {nota}" for nota in notas_disponibilidade(res)] + [""]
    elif chave == "hidrologia":
        if res.hidrologia["publicado"]:
            for c, funcao in (("tab_faixas_afluencia", linhas_tabela_faixas_afluencia),
                              ("tab_faixas_afluencia_evt", linhas_tabela_faixas_afluencia_evt)):
                cabecalho, linhas = funcao(res)
                if linhas:
                    saida += tab(c, (cabecalho, linhas))
            saida += fig("faixas_afluencia")
            for c, funcao in (("tab_hidrologia_anual", linhas_tabela_hidrologia_anual),
                              ("tab_hidrologia_perfil", linhas_tabela_perfil_hidrologico)):
                cabecalho, linhas = funcao(res)
                if linhas:
                    saida += tab(c, (cabecalho, linhas))
            saida += fig("perfil_hidrologico")
        saida += [f"- {nota}" for nota in notas_hidrologia(res)] + [""]
    elif chave == "geracao_zero":
        saida += tab("tab_geracao_zero", linhas_tabela_geracao_zero(res))
    elif chave == "vazoes":
        saida += fig("vazoes_defluentes")
    elif chave == "geracao_oficial":
        if "Conferência da geração" not in dict(res.achados):
            saida += [texto_conferencia_geracao(res), ""]
        cabecalho, linhas = linhas_tabela_geracao_anual(res)
        if linhas:
            saida += tab("tab_geracao_oficial", (cabecalho, linhas))
    elif chave == "qualidade":
        for c, funcao in (("tab_regras_validacao", linhas_tabela_regras),
                          ("tab_registros_sinalizados", linhas_tabela_registros_sinalizados),
                          ("tab_extremos", linhas_tabela_extremos)):
            cabecalho, linhas = funcao(res)
            if linhas:
                saida += tab(c, (cabecalho, linhas))
    elif chave == "conclusao":
        listas = listas_conclusao(res)
        if listas:
            saida += [FRASE_ABERTURA_CONCLUSAO, ""]
            for titulo_lista, textos_lista in listas:
                saida += [f"### {titulo_lista}", ""] + [f"- {texto}" for texto in textos_lista] + [""]
        else:
            saida += [FRASE_CONCLUSAO_VAZIA, ""]
    elif chave == "notas":
        saida += [f"- {nota}" for nota in notas_metodologicas(res)] + [""]
        saida += tab("tab_parametros", linhas_tabela_parametros(res))
    return saida


def gerar_relatorio_md(
    res: ResultadosAnalise,
    figuras: Optional[Dict[str, Path]],
    caminho_md: Path,
    data_geracao: Optional[datetime] = None,
) -> Path:
    """Gera o relatório em Markdown com a mesma estrutura do PDF (spec da Geração do relatório, FR-017); todo número e frase vêm de ``res``.

    ``data_geracao`` fixa o "Gerado em" (``--data-geracao``); sem ela, vale a hora da execução.

    Capa com período, data de geração, identificação, parâmetros, indicadores principais e sumário; depois, cada
    seção com as suas constatações (uma única vez no relatório), tabelas, figuras, notas e legendas de fonte.
    """
    destino = Path(caminho_md)
    destino.parent.mkdir(parents=True, exist_ok=True)
    c = res.cobertura
    textos = textos_tabelas(res)
    tiles, nota_capa = indicadores_capa(res)

    linhas: List[str] = [
        f"# {perfil_ativo().usina.nome} — energia vertida turbinável e desempenho operacional (dados ONS)",
        "",
        f"**Período**: {fmt_data_hora(c['inicio'])} a {fmt_data_hora(c['fim'])} "
        f"({fmt_int(c['horas_observadas'])} registros horários)",
        f"**Gerado em**: {(data_geracao or datetime.now()).strftime('%d/%m/%Y %H:%M')}",
        "",
    ]
    linhas += _md_chave_valor(res, "Identificação nos dados do ONS", pares_identificacao(res), "bloco_identificacao")
    if res.cadastro:
        linhas += _md_chave_valor(res, "Cadastro no ONS", pares_identificacao_cadastro(res), "bloco_cadastro")
    linhas += _md_chave_valor(res, "Parâmetros técnicos da usina", pares_parametros(), "bloco_parametros")
    linhas += ["### Indicadores principais", ""]
    linhas += _tabela_md(["Indicador", "Valor", "Detalhe"], [[r, v, s] for r, v, s in tiles]) + ["", nota_capa, ""]
    linhas += _fonte_md(res, "tab_capa_indicadores")
    linhas += ["## Sumário", ""]
    linhas += [f"{n}. [{titulo}](#{_ancora_md(f'{n}. {titulo}')})" for n, titulo in sumario(res)]

    for n, secao in secoes_presentes(res):
        linhas += ["", f"## {n}. {secao.titulo}", ""]
        for titulo_c, texto in constatacoes_da_secao(res, secao.chave):
            linhas += [f"**{titulo_c}.** {texto}", ""]
        linhas += _md_conteudo_secao(res, secao.chave, secao.titulo, figuras, textos)
    linhas.append("")

    with open(destino, mode="w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    logger.info("Relatório em Markdown gravado em: %s", destino)
    return destino
