"""Análises: calcula, para a usina do perfil, tudo o que o relatório mostra (spec das Análises).

Parte só dos dados tratados, dos resultados da Conferência, do perfil e dos registros da Coleta, e grava
``data/usinas/<slug>/analises/resultados.pkl``. As conferências entram prontas, nos mesmos campos de antes, para que o
mapa de fontes e o relatório não mudem. A tabela de parâmetros e a origem dos dados ficam com a Geração do relatório.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from src.analises.cadastro import analisar_cadastro
from src.analises.cobertura import analisar_cobertura
from src.analises.conclusao import montar_conclusao
from src.analises.constatacoes import montar_achados
from src.analises.disponibilidade import analisar_disponibilidade
from src.analises.evt import (
    calcular_distribuicao_mes_do_ano,
    calcular_evt_mensal,
    calcular_evt_por_faixa_geracao,
    calcular_horas_geracao_zero,
    calcular_indicadores_anuais,
    calcular_indicadores_globais,
    calcular_perfil_estatistico_anual,
    calcular_perfil_horario,
    calcular_serie_diaria,
    calcular_vazoes_anuais,
    detectar_mudanca_classificacao,
    listar_anomalias,
    listar_eventos_indisponibilidade_total,
    listar_eventos_parada_com_evt,
    mapear_extremos_historicos,
    preparar_dados,
)
from src.analises.geracao import analisar_geracao_oficial
from src.analises.hidrologia import analisar_hidrologia
from src.analises.indicadores import analisar_indicadores_ons
from src.analises.programacao import analisar_programacao
from src.analises.resultados import ResultadosAnalise, salvar_resultados
from src.comum import caminhos
from src.comum.logger import setup_logger
from src.comum.regras import CONJUNTO_DISPONIBILIDADE, CONJUNTO_EVT, CONJUNTO_GERACAO, CONJUNTO_HIDROLOGIA
from src.comum.persistencia import registrar_gravacoes
from src.conferencia.resultado import ResultadoConferencia, carregar_conferencias
from src.pipeline import CODIGO_SUCESSO, ResultadoEtapa
from src.tratamento.disponibilidade import carregar_disponibilidade_tratada
from src.tratamento.geracao import carregar_geracao_tratada
from src.tratamento.hidrologia import carregar_hidrologia_tratada
from src.tratamento.indicadores import IndicadoresONS, carregar_indicadores_tratados
from src.tratamento.programacao import ProgramacaoONS, carregar_programacao_tratada
from src.tratamento.series import SerieConjunto
from src.comum.perfil import perfil_ativo
from src.tratamento.validacao import COLUNA_QUALIDADE, validar_regras_fisicas

logger = setup_logger("analises")

# Colunas da auditoria do cadastro mostradas no relatório (aba CAD_AUDITORIA)
COLUNAS_AUDITORIA_CADASTRO = ["arquivo", "formato", "linhas_lidas", "linhas_formato_irregular", "linhas_usina",
                              "linhas_so_identificador", "linhas_so_conferencia", "status", "mensagem"]


def analisar(
    df: pd.DataFrame,
    conferencias: Dict[str, ResultadoConferencia],
    caminho_auditoria: Optional[Path] = None,
    datas_obtencao: Optional[Dict[str, Dict[str, Any]]] = None,
    indicadores: Optional[IndicadoresONS] = None,
    programacao: Optional[ProgramacaoONS] = None,
    disponibilidade: Optional[SerieConjunto] = None,
    hidrologia: Optional[SerieConjunto] = None,
    geracao: Optional[SerieConjunto] = None,
    cadastro: Optional[pd.DataFrame] = None,
    dicionarios: Optional[pd.DataFrame] = None,
    auditoria_cadastro: Optional[pd.DataFrame] = None,
    validacao: Optional[pd.DataFrame] = None,
) -> ResultadosAnalise:
    """Calcula todos os resultados usados nas planilhas, no relatório e no PDF.

    As bases complementares são opcionais: sem elas, o relatório sai sem as seções correspondentes. As conferências
    (geração, disponibilidade, vazões, DISPF × horas, TEIFa e TEIP, cadastro) vêm prontas da Conferência.
    ``datas_obtencao`` é o ``datas_obtencao.csv`` da Coleta, por conjunto (spec 006, decisão R22).
    """
    if "ano" not in df.columns or COLUNA_QUALIDADE not in df.columns:
        df = preparar_dados(df)
    datas = datas_obtencao or {}
    cobertura = analisar_cobertura(df, caminho_auditoria, datas.get(CONJUNTO_EVT))
    anuais = calcular_indicadores_anuais(df, cobertura)
    lista_anomalias, resumo_anomalias = listar_anomalias(df)
    res = ResultadosAnalise(
        cobertura=cobertura,
        globais=calcular_indicadores_globais(df),
        indicadores_anuais=anuais,
        evt_mensal=calcular_evt_mensal(df),
        distribuicao_mes_do_ano=calcular_distribuicao_mes_do_ano(df, cobertura["anos_completos"]),
        evt_por_faixa_geracao=calcular_evt_por_faixa_geracao(df),
        perfil_horario_geracao=calcular_perfil_horario(df, "val_geracao"),
        perfil_horario_evt=calcular_perfil_horario(df, "val_energiavertidaturbinavel"),
        eventos_parada_com_evt=listar_eventos_parada_com_evt(df),
        eventos_indisponibilidade_total=listar_eventos_indisponibilidade_total(df),
        mudanca_classificacao=detectar_mudanca_classificacao(df),
        anomalias=lista_anomalias,
        resumo_anomalias=resumo_anomalias,
        extremos=mapear_extremos_historicos(df),
        perfil_estatistico=calcular_perfil_estatistico_anual(df),
    )
    # Resultado das regras R1 a R9 gravado pelo Tratamento; sem ele (chamada direta), as regras são avaliadas aqui
    res.validacao = validacao if validacao is not None else validar_regras_fisicas(df, perfil_ativo())[0]
    res.horas_geracao_zero = calcular_horas_geracao_zero(df)
    res.datas_obtencao = datas
    if indicadores is not None:
        dispf = conferencias.get("dispf_horas")
        indicadores.divergencias = dispf.tabelas.get("divergencias", pd.DataFrame()) if dispf else pd.DataFrame()
        taxas = conferencias.get("teifa_teip")
        recalculo = taxas.tabelas.get("recalculo") if taxas else None
        reproducao = ({"meses": taxas.comparados, "reproduzidos": taxas.coincidentes,
                       "diferenca_maxima_pp": taxas.tabelas.get("diferenca_maxima_pp", float("nan"))}
                      if taxas is not None and taxas.aplicavel else None)  # meses reproduzidos, da Conferência
        res.ons = analisar_indicadores_ons(indicadores, df, anuais, cobertura, recalculo, reproducao)
    if programacao is not None and len(programacao.horaria):
        res.programacao = analisar_programacao(programacao, df)
    if disponibilidade is not None and len(disponibilidade.horaria):
        c = conferencias["disponibilidade"]
        res.disponibilidade = analisar_disponibilidade(disponibilidade, df, indicadores, res.programacao, cobertura,
                                                       c.tabelas["resumo"], c.tabelas["divergencias"],
                                                       _obtido_em(datas, CONJUNTO_DISPONIBILIDADE))
    if hidrologia is not None and len(hidrologia.horaria):
        res.hidrologia = analisar_hidrologia(hidrologia, conferencias["vazoes"].tabelas["alinhamento"], df, cobertura,
                                             _obtido_em(datas, CONJUNTO_HIDROLOGIA))
    if geracao is not None and len(geracao.horaria):
        c = conferencias["geracao"]
        res.geracao_oficial = analisar_geracao_oficial(geracao, df, cobertura, c.tabelas["resumo"], c.tabelas["mensal"],
                                                       c.tabelas["divergencias"], _obtido_em(datas, CONJUNTO_GERACAO))
    if cadastro is not None and len(cadastro):
        res.cadastro = analisar_cadastro(cadastro, auditoria_cadastro)
    if dicionarios is not None and len(dicionarios):
        res.dicionarios = {"registro": dicionarios}
    res.achados = montar_achados(res)
    res.conclusao = montar_conclusao(res)
    res.serie_diaria = calcular_serie_diaria(df)
    res.vazoes_anuais = calcular_vazoes_anuais(df)
    return res


def _obtido_em(datas: Dict[str, Dict[str, Any]], conjunto: str) -> str:
    return str((datas.get(conjunto) or {}).get("obtencao_mais_recente") or "")


# ---------------------------------------------------------------------------
# Leitura das etapas anteriores
# ---------------------------------------------------------------------------


def _ler_csv(caminho: Path, **opcoes: Any) -> Optional[pd.DataFrame]:
    try:
        return pd.read_csv(caminho, sep=";", **opcoes)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return None


def ficha_do_cadastro(coleta: Path, conferencia: Optional[ResultadoConferencia]) -> Optional[pd.DataFrame]:
    """Ficha da Coleta com as divergências da Conferência, nas colunas mostradas no relatório (aba CAD_FICHA)."""
    ficha = _ler_csv(coleta / caminhos.ARQUIVOS_COLETA["cadastro_ficha"], keep_default_na=False)
    if ficha is None or not len(ficha):
        return None
    ficha = ficha.drop(columns=["linhas_ceg"], errors="ignore")
    ficha["divergencias"] = str(conferencia.tabelas.get("divergencias", "")) if conferencia else ""
    return ficha


def datas_da_coleta(coleta: Path) -> Dict[str, Dict[str, Any]]:
    """``datas_obtencao.csv`` da Coleta: conjunto -> arquivos registrados, publicação e obtenção mais recentes."""
    tabela = _ler_csv(coleta / caminhos.ARQUIVOS_COLETA["datas_obtencao"], dtype=str, keep_default_na=False)
    if tabela is None:
        return {}
    return {linha["conjunto"]: {"arquivos_registrados": int(linha["arquivos_registrados"] or 0),
                                "publicacao_mais_recente": linha["publicacao_mais_recente"],
                                "obtencao_mais_recente": linha["obtencao_mais_recente"]}
            for linha in tabela.to_dict("records")}


def carregar_entradas(slug: str) -> Dict[str, Any]:
    """Dados tratados, conferências e registros da Coleta da usina, prontos para ``analisar``."""
    coleta = caminhos.pasta_etapa(slug, "coleta")
    tratamento = caminhos.pasta_etapa(slug, "tratamento")
    conferencias = carregar_conferencias(caminhos.pasta_etapa(slug, "conferencia")
                                         / caminhos.ARQUIVOS_CONFERENCIA["resultados"])
    auditoria_prog = _ler_csv(coleta / caminhos.ARQUIVOS_COLETA["auditoria_programacao"])
    if auditoria_prog is not None:
        auditoria_prog["dia"] = pd.to_datetime(auditoria_prog["dia"])
    auditoria_cadastro = _ler_csv(coleta / caminhos.ARQUIVOS_COLETA["auditoria_cadastro"], keep_default_na=False)
    if auditoria_cadastro is not None:
        auditoria_cadastro = auditoria_cadastro[COLUNAS_AUDITORIA_CADASTRO]
    return {
        "df": pd.read_parquet(tratamento / caminhos.ARQUIVOS_TRATAMENTO["evt_parquet"]),
        "conferencias": conferencias,
        "caminho_auditoria": coleta / caminhos.ARQUIVOS_COLETA["auditoria_evt"],
        "datas_obtencao": datas_da_coleta(coleta),
        "indicadores": carregar_indicadores_tratados(tratamento),
        "programacao": carregar_programacao_tratada(tratamento, auditoria_prog),
        "disponibilidade": carregar_disponibilidade_tratada(tratamento),
        "hidrologia": carregar_hidrologia_tratada(tratamento),
        "geracao": carregar_geracao_tratada(tratamento),
        "cadastro": ficha_do_cadastro(coleta, conferencias.get("cadastro")),
        "dicionarios": _ler_csv(coleta / caminhos.ARQUIVOS_COLETA["dicionarios"], keep_default_na=False),
        "auditoria_cadastro": auditoria_cadastro,
        "validacao": _ler_csv(tratamento / caminhos.ARQUIVOS_TRATAMENTO["validacao_csv"]),
    }


def executar_analises(perfil: Any) -> ResultadoEtapa:
    """Calcula os resultados da usina e grava ``resultados.pkl`` (código 0)."""
    slug = perfil.usina.slug
    pasta = caminhos.pasta_etapa(slug, "analises")
    entradas = carregar_entradas(slug)
    for nome in ("indicadores", "programacao", "disponibilidade", "hidrologia", "geracao", "cadastro"):
        if entradas[nome] is None:
            logger.warning("Base '%s' sem dados tratados para a usina: o relatório sai sem a seção correspondente.",
                           nome)
    res = analisar(**entradas)
    with registrar_gravacoes() as gravacoes:
        salvar_resultados(res, pasta / caminhos.ARQUIVOS_ANALISES["resultados"])
    cobertura = res.cobertura
    resumo = {
        "periodo": {"inicio": str(cobertura.get("inicio")), "fim": str(cobertura.get("fim"))},
        "horas_analisadas": int(cobertura.get("horas_observadas", 0)),
        "constatacoes": len(res.achados),
        "conclusao": dict(sorted(Counter(item["lista"] for item in res.conclusao).items())),
        "regras_da_conclusao": sorted({item["regra"] for item in res.conclusao}, key=lambda r: int(r[1:])),
        "bases_complementares": {
            "indicadores": bool(res.ons), "programacao": bool(res.programacao),
            "disponibilidade": bool(res.disponibilidade), "hidrologia": bool(res.hidrologia),
            "geracao": bool(res.geracao_oficial), "cadastro": bool(res.cadastro),
        },
    }
    return ResultadoEtapa(codigo=CODIGO_SUCESSO, arquivos=[p for p, _ in gravacoes], resumo=resumo)
