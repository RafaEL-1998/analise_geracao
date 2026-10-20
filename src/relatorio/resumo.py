"""Resumo executivo da usina (spec da Geração do relatório, resumo executivo): até duas páginas, em PDF e em Markdown.

Monta o ``ResumoExecutivo`` com os mesmos resultados e as mesmas funções do relatório completo, sem recalcular nada,
nesta ordem:
- cabeçalho, com a referência ao relatório completo e a linha de termos;
- os indicadores da capa;
- as colunas principais da tabela anual;
- "Sobre os dados": cobertura, sinalizações, conferências, limites e fontes, no lugar das legendas por tabela
  (constituição, princípio VII);
- a conclusão, copiada igual (listas, itens, ordem e texto), que fecha o documento.

O PDF (``src.relatorio.resumo_pdf``) e o Markdown saem do mesmo objeto, com o mesmo conteúdo e na mesma ordem. Se o PDF
passar de duas páginas, a evolução anual sai; se ainda passar, é erro, e a etapa não troca nenhuma saída.

Vale para os dois caminhos da spec 006: nas usinas sem EVT, os indicadores, a tabela anual e os textos vêm de
``src.relatorio.comum``, e os números do conjunto aparecem como do conjunto, como no relatório completo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.analises.comum import _pct
from src.analises.conclusao import FRASE_ABERTURA_CONCLUSAO, frase_sem_itens
from src.analises.resultados import ResultadosAnalise, sem_evt
from src.comum.formatacao import fmt_data, fmt_data_hora, fmt_int, fmt_lista, fmt_num, fmt_pct, plural
from src.comum.logger import setup_logger
from src.comum.perfil import perfil_ativo
from src.comum.regras import (
    GLOSSARIO_RESUMO,
    RESUMO_MAXIMO_PAGINAS,
    RESUMO_MAXIMO_PALAVRAS,
    RESUMO_MAXIMO_PALAVRAS_DADOS,
)
from src.relatorio.conteudo import (
    indicadores_capa,
    linhas_tabela_anual,
    listas_conclusao,
    pares_identificacao,
    titulo_capa_relatorio,
)
from src.relatorio import comum
from src.relatorio.estrutura import secoes_presentes
from src.relatorio.fontes import (
    CONFERENCIAS,
    CONFERENCIAS_SEM_EVT,
    conjuntos_carregados,
    fontes_resumo,
    texto_conferencia_curto,
)
from src.relatorio.resumo_pdf import gerar_resumo_pdf, paginas_do_pdf

logger = setup_logger("relatorio")

CAMINHO_EVT = "evt"  # hidrelétrica com série própria na Energia Vertida Turbinável
CAMINHO_SEM_EVT = "sem_evt"  # demais usinas, sobre a base horária comum (spec 006, decisão R30)
# Colunas da tabela anual do relatório que entram no resumo, por caminho (no máximo seis). No caminho sem EVT, as que a
# tabela da usina tem, nesta ordem (decisão R6 da spec 007): o nível do número, a geração, a energia, o fator de
# capacidade (eólicas e solares), a disponibilidade (quando o ONS a publica) e o indicador de perda do tipo (nas
# térmicas, as horas disponíveis sem despacho; fase B da 006).
COLUNAS_RESUMO_ANUAL: Dict[str, List[str]] = {
    CAMINHO_EVT: ["Ano", "Disp. média (% Pinst)", "Fator de capacidade", "Geração / GF", "EVT (MWh)",
                  "Horas parada c/ EVT"],
    CAMINHO_SEM_EVT: ["Ano", "Nível", "Geração média (MWmed)", "Energia (MWh)", "Fator de capacidade",
                      "Disp. (% Pinst)", "Disp. sem despacho (h)"],
}
TITULOS_BLOCOS: Tuple[Tuple[str, str], ...] = (  # ordem fixa do documento; a conclusão fecha o resumo
    ("indicadores", "Indicadores-chave"),
    ("evolucao_anual", "Evolução anual"),
    ("sobre_os_dados", "Sobre os dados"),
    ("conclusao", "Conclusão"),
)
AVISO_SECOES = "As seções e as notas metodológicas citadas são as do relatório completo."
NOTA_INDICADORES = "Seção de origem: capa do relatório completo."
FRASE_LIMITES = ("Os dados abertos do ONS não informam a causa das paradas nem os eventos individuais de "
                 "desligamento.")


@dataclass(frozen=True)
class Tabela:
    """Tabela do resumo: cabeçalho, linhas já formatadas (as mesmas do relatório completo) e nota."""

    cabecalho: List[str]
    linhas: List[List[str]]
    nota: str = ""


@dataclass
class ResumoExecutivo:
    """Conteúdo do resumo executivo, na ordem do documento (data-model da spec 007, seção 1)."""

    nome_usina: str
    titulo: str
    subtitulo: str
    cabecalho_pagina: str  # cabeçalho das páginas seguintes à primeira, no PDF
    identificacao: List[str]
    referencia_relatorio: str
    frase_conclusao: str
    listas_conclusao: List[Tuple[str, List[str]]]
    indicadores: Tabela
    evolucao_anual: Optional[Tabela]
    remissao_anual: str  # no lugar da evolução anual, quando ela sai pela regra das duas páginas
    sobre_os_dados: List[str]
    aviso_secoes: str = AVISO_SECOES
    termos: List[Tuple[str, str]] = field(default_factory=list)

    def blocos(self) -> List[Tuple[str, str]]:
        """Blocos presentes (chave, título), na ordem fixa; a evolução anual só falta quando não há tabela anual."""
        return [(chave, titulo) for chave, titulo in TITULOS_BLOCOS
                if chave != "evolucao_anual" or self.evolucao_anual is not None or self.remissao_anual]

    def texto_termos(self) -> str:
        return "; ".join(f"{sigla}: {texto}" for sigla, texto in self.termos) + "."


# ---------------------------------------------------------------------------
# Montagem
# ---------------------------------------------------------------------------


def primeira_ocorrencia(texto: str, sigla: str) -> int:
    """Posição da primeira ocorrência da sigla como palavra (também seguida de algarismos, como em UG2); -1 se não há."""
    m = re.search(rf"(?<![A-Za-zÀ-ÿ]){re.escape(sigla)}(?![A-Za-zÀ-ÿ])", texto)
    return m.start() if m else -1


def texto_corrido(resumo: ResumoExecutivo) -> str:
    """Todo o texto do resumo, na ordem de leitura dos blocos, sem a linha de termos (base da escolha dos termos)."""
    partes: List[str] = [resumo.titulo, resumo.subtitulo, *resumo.identificacao, resumo.referencia_relatorio]
    for chave, _ in resumo.blocos():
        if chave == "conclusao":
            partes += [resumo.aviso_secoes, resumo.frase_conclusao]
            for titulo, itens in resumo.listas_conclusao:
                partes += [titulo, *itens]
        elif chave in ("indicadores", "evolucao_anual"):
            tabela = resumo.indicadores if chave == "indicadores" else resumo.evolucao_anual
            if tabela is None:
                partes.append(resumo.remissao_anual)
            else:
                partes += [" ".join(tabela.cabecalho), *(" ".join(linha) for linha in tabela.linhas), tabela.nota]
        elif chave == "sobre_os_dados":
            partes += resumo.sobre_os_dados
    return "\n".join(p for p in partes if p)


def palavras(linhas: Iterable[str]) -> int:
    """Palavras (separadas por espaço) de um texto em Markdown, sem as marcas de título, de item, de negrito e de
    escape; datas, números e códigos contam como uma palavra cada."""
    total = 0
    for linha in linhas:
        texto = re.sub(r"^\s*(#+|-)\s+", "", linha).replace("**", "").replace("\\", "")
        total += len(texto.split())
    return total


def palavras_fora_das_tabelas(markdown: str) -> int:
    return palavras(linha for linha in markdown.splitlines() if not linha.startswith("|"))


def _caminho(res: ResultadosAnalise) -> str:
    """Caminho da usina, pelo mesmo critério do relatório completo (spec 006, decisão R14)."""
    return CAMINHO_SEM_EVT if sem_evt(res) else CAMINHO_EVT


def _identificacao(res: ResultadosAnalise) -> List[str]:
    """Tipo, estado, modalidade e potência; agentes com o período de cada um, como na capa do relatório (caminho da
    EVT, que os traz da base de EVT); nas usinas sem EVT, o agente atual da Capacidade de geração."""
    perfil = perfil_ativo()
    usina = perfil.usina
    potencia = f"{fmt_num(perfil.parametros.potencia_instalada_mw, 1)} MW"
    tipo = getattr(res, "tipo", "") or usina.tipo
    linhas = [" · ".join(p for p in (tipo, usina.estado, usina.modalidade, potencia) if p)]
    if sem_evt(res):  # o agente atual da Capacidade de geração, sem o histórico (decisão do usuário de 19/10/2026)
        agentes = comum.texto_agentes(res)
        return linhas + ([f"Agente atual (Capacidade de geração do ONS): {agentes}"] if agentes else [])
    agentes = dict(pares_identificacao(res)).get("Agente")
    if agentes:
        quantidade = len(res.cobertura.get("agentes", []))
        linhas.append(f"{plural(quantidade, 'Agente', 'Agentes')}: {agentes}")
    return linhas


def _evolucao_anual(res: ResultadosAnalise, secao: Optional[int],
                    com_evolucao_anual: bool) -> Tuple[Optional[Tabela], str]:
    caminho = _caminho(res)
    cabecalho, linhas = comum.linhas_tabela_anuais(res) if caminho == CAMINHO_SEM_EVT else linhas_tabela_anual(res)
    if not linhas:
        return None, ""
    if not com_evolucao_anual:
        return None, f"A evolução anual está na seção {secao} do relatório completo."
    colunas = COLUNAS_RESUMO_ANUAL[caminho]
    if caminho == CAMINHO_SEM_EVT:  # as colunas que a tabela da usina tem
        colunas = [c for c in colunas if c in cabecalho]
    ausentes = [c for c in colunas if c not in cabecalho]
    if ausentes:
        raise KeyError(f"colunas do resumo ausentes na tabela anual do relatório: {', '.join(ausentes)}")
    indices = [cabecalho.index(c) for c in colunas]
    escolhidas = [[linha[i] for i in indices] for linha in linhas]
    parcial = "* Ano parcial. " if any(linha[0].endswith("*") for linha in escolhidas) else ""
    return Tabela(colunas, escolhidas, f"{parcial}Colunas e definições na seção {secao} do relatório completo."), ""


def _dados_sem_evt(res: ResultadosAnalise) -> str:
    """Parágrafo "Dados" das usinas sem EVT: a série de referência, com o nível, e as horas sinalizadas."""
    c, q = res.cobertura, res.comum["qualidade"]
    dados = (f"Dados: série horária de referência, {comum.serie_referencia_texto(res)}, de "
             f"{fmt_data_hora(c['inicio'])} a {fmt_data_hora(c['fim'])}, com {fmt_int(c['horas_observadas'])} registros")
    parciais = [str(a) for a in c.get("anos_parciais", [])]
    if parciais:
        dados += f"; {fmt_lista(parciais)} {plural(len(parciais), 'é ano parcial', 'são anos parciais')}"
    if c.get("horas_ausentes"):
        dados += f"; {fmt_int(c['horas_ausentes'])} horas ausentes, não preenchidas"
    total = q["horas_sinalizadas"]
    if total:
        return dados + (f". {fmt_int(total)} horas ({fmt_pct(_pct(total, c['horas_observadas']), 2)}) estão sinalizadas "
                        "e foram mantidas nos totais.")
    return dados + ". Nenhuma hora sinalizada."


def _sobre_os_dados(res: ResultadosAnalise) -> List[str]:
    """Três parágrafos: dados (cobertura e sinalizações), conferências e limites, fontes (data-model 1.2)."""
    if sem_evt(res):
        carregados = (getattr(res, "fontes", None) or {}).get("carregados") or conjuntos_carregados(res)
        feitas = [texto_conferencia_curto(res, cid) for cid in CONFERENCIAS_SEM_EVT
                  if CONFERENCIAS[cid].base in carregados]
        conferencias = (f"Conferências: {'; '.join(feitas)}. " if feitas else "") + FRASE_LIMITES
        return _limitar([_dados_sem_evt(res), conferencias, f"Fontes: {'; '.join(fontes_resumo(res))}."])
    c, g, anuais = res.cobertura, res.globais, res.indicadores_anuais
    dados = (f"Dados: série horária de {fmt_data_hora(c['inicio'])} a {fmt_data_hora(c['fim'])}, com "
             f"{fmt_int(c['horas_observadas'])} registros")
    parciais = [str(int(a)) for a in anuais.loc[anuais["ano_parcial"].astype(bool), "ano"]] if len(anuais) else []
    if parciais:
        dados += f"; {fmt_lista(parciais)} {plural(len(parciais), 'é ano parcial', 'são anos parciais')}"
    total = g["horas_com_anomalia"]
    if total:
        dados += (f". {fmt_int(total)} registros ({fmt_pct(_pct(total, g['horas']), 2)}) violam ao menos uma regra de "
                  "plausibilidade física e foram mantidos nos totais, sinalizados.")
    else:
        dados += ". Nenhum registro viola as regras de plausibilidade física."
    carregados = (getattr(res, "fontes", None) or {}).get("carregados") or conjuntos_carregados(res)
    feitas = [texto_conferencia_curto(res, cid) for cid, conf in CONFERENCIAS.items() if conf.base in carregados]
    conferencias = (f"Conferências: {'; '.join(feitas)}. " if feitas else "") + FRASE_LIMITES
    return _limitar([dados, conferencias, f"Fontes: {'; '.join(fontes_resumo(res))}."])


def _limitar(paragrafos: List[str]) -> List[str]:
    total_palavras = palavras(paragrafos)
    if total_palavras > RESUMO_MAXIMO_PALAVRAS_DADOS:
        raise ValueError(f"'Sobre os dados' com {total_palavras} palavras, acima do máximo de "
                         f"{RESUMO_MAXIMO_PALAVRAS_DADOS}")
    return paragrafos


def montar_resumo(res: ResultadosAnalise, paginas_relatorio: int, data_geracao: datetime,
                  com_evolucao_anual: bool = True) -> ResumoExecutivo:
    """Resumo executivo a partir dos resultados, com as funções do relatório completo (nenhum valor fixo)."""
    c = res.cobertura
    nome = perfil_ativo().usina.nome
    numeros = {s.chave: n for n, s in secoes_presentes(res)}
    listas = listas_conclusao(res)
    sem = sem_evt(res)
    tiles, _ = comum.indicadores_capa(res) if sem else indicadores_capa(res)
    evolucao, remissao = _evolucao_anual(res, numeros.get("anuais_comum" if sem else "indicadores_anuais"),
                                         com_evolucao_anual)
    resumo = ResumoExecutivo(
        nome_usina=nome,
        titulo=f"{nome} — resumo executivo",
        subtitulo=(f"{fmt_data_hora(c['inicio'])} a {fmt_data_hora(c['fim'])} ({fmt_int(c['horas_observadas'])} "
                   f"registros horários) · Gerado em {data_geracao.strftime('%d/%m/%Y %H:%M')}"),
        cabecalho_pagina=f"Resumo executivo — {nome} · {fmt_data(c['inicio'])} a {fmt_data(c['fim'])}",
        identificacao=_identificacao(res),
        referencia_relatorio=(f'Resume o relatório completo "{titulo_capa_relatorio()}", de '
                              f"{fmt_int(paginas_relatorio)} páginas, gerado na mesma data."),
        frase_conclusao=FRASE_ABERTURA_CONCLUSAO if listas else frase_sem_itens(res),
        listas_conclusao=listas,
        indicadores=Tabela(["Indicador", "Valor", "Detalhe"], [list(t) for t in tiles], NOTA_INDICADORES),
        evolucao_anual=evolucao,
        remissao_anual=remissao,
        sobre_os_dados=_sobre_os_dados(res),
    )
    corpo = texto_corrido(resumo)
    presentes = [(primeira_ocorrencia(corpo, sigla), sigla, texto) for sigla, texto in GLOSSARIO_RESUMO.items()]
    resumo.termos = [(sigla, texto) for posicao, sigla, texto in sorted(presentes) if posicao >= 0]
    return resumo


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------


def _tabela_md(t: Tabela) -> List[str]:
    saida = ["| " + " | ".join(t.cabecalho) + " |", "| " + " | ".join(["---"] * len(t.cabecalho)) + " |"]
    return saida + ["| " + " | ".join(linha) + " |" for linha in t.linhas]


def gerar_resumo_md(resumo: ResumoExecutivo, caminho: Path) -> Path:
    """Grava o resumo em Markdown; o bloco da conclusão tem as mesmas linhas da seção de conclusão do relatório."""
    linhas: List[str] = [f"# {resumo.titulo}", "", resumo.subtitulo, ""]
    for linha in resumo.identificacao:
        linhas += [linha, ""]
    linhas += [resumo.referencia_relatorio, ""]
    if resumo.termos:
        linhas += [f"**Termos.** {resumo.texto_termos()}", ""]
    for chave, titulo in resumo.blocos():
        linhas += [f"## {titulo}", ""]
        if chave == "conclusao":
            linhas += [resumo.aviso_secoes, "", resumo.frase_conclusao, ""]
            for titulo_lista, itens in resumo.listas_conclusao:
                linhas += [f"### {titulo_lista}", ""] + [f"- {item}" for item in itens] + [""]
        elif chave == "indicadores":
            linhas += _tabela_md(resumo.indicadores) + ["", resumo.indicadores.nota, ""]
        elif chave == "evolucao_anual":
            t = resumo.evolucao_anual
            linhas += ([resumo.remissao_anual, ""] if t is None
                       else _tabela_md(t) + ["", t.nota.replace("*", "\\*"), ""])
        elif chave == "sobre_os_dados":
            for paragrafo in resumo.sobre_os_dados:
                linhas += [paragrafo, ""]
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(linhas), encoding="utf-8")
    logger.info("Resumo executivo em Markdown gravado: %s", destino)
    return destino


# ---------------------------------------------------------------------------
# Geração com a regra das duas páginas
# ---------------------------------------------------------------------------


def gerar_resumo(res: ResultadosAnalise, caminho_pdf: Path, caminho_md: Path, data_geracao: datetime,
                 invariante: bool, paginas_relatorio: int) -> Tuple[Path, Path, Dict[str, Any]]:
    """Gera o PDF e o Markdown do resumo (FR-006 da spec 007; decisão R10).

    Passando de duas páginas, gera de novo sem a evolução anual; se ainda passar, levanta ``RuntimeError`` antes de
    gravar o Markdown. Devolve os dois caminhos e o resumo do ``etapa.json``: páginas, presença da evolução anual e
    palavras fora das tabelas.
    """
    resumo = montar_resumo(res, paginas_relatorio, data_geracao)
    gerar_resumo_pdf(resumo, caminho_pdf, invariante)
    paginas = paginas_do_pdf(caminho_pdf)
    if paginas > RESUMO_MAXIMO_PAGINAS:
        logger.warning("Resumo executivo com %d páginas; gerado de novo sem a evolução anual.", paginas)
        resumo = montar_resumo(res, paginas_relatorio, data_geracao, com_evolucao_anual=False)
        gerar_resumo_pdf(resumo, caminho_pdf, invariante)
        paginas = paginas_do_pdf(caminho_pdf)
        if paginas > RESUMO_MAXIMO_PAGINAS:
            raise RuntimeError(f"resumo executivo com {paginas} páginas, acima do máximo de {RESUMO_MAXIMO_PAGINAS}, "
                               "mesmo sem a evolução anual")
    gerar_resumo_md(resumo, caminho_md)
    total_palavras = palavras_fora_das_tabelas(Path(caminho_md).read_text(encoding="utf-8"))
    if total_palavras > RESUMO_MAXIMO_PALAVRAS:
        logger.warning("Resumo executivo com %d palavras fora das tabelas, acima de %d.", total_palavras,
                       RESUMO_MAXIMO_PALAVRAS)
    info = {"paginas": paginas, "evolucao_anual": resumo.evolucao_anual is not None, "palavras": total_palavras}
    logger.info("Resumo executivo: %d páginas, %d palavras fora das tabelas%s.", paginas, total_palavras,
                "" if info["evolucao_anual"] else ", sem a evolução anual")
    return Path(caminho_pdf), Path(caminho_md), info
