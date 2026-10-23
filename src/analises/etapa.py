"""Análises: calcula, para a usina do perfil, tudo o que o relatório mostra (spec das Análises).

Parte só dos dados tratados, dos resultados da Conferência, do perfil e dos registros da Coleta, e grava
``data/usinas/<slug>/analises/resultados.pkl``. As conferências entram prontas, nos mesmos campos de antes, para que o
mapa de fontes e o relatório não mudem. A tabela de parâmetros e a origem dos dados ficam com a Geração do relatório.

O caminho segue a presença da EVT (plano das Análises, D16): nas hidrelétricas com EVT, as análises de hoje sobre a base
de EVT; nas demais usinas, as seções comuns sobre a base horária comum, com os campos de EVT vazios.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Dict, Optional

import json

import pandas as pd

from src.analises.cadastro import analisar_cadastro
from src.analises.carteira import indicadores_carteira
from src.analises.comum_tipos import agentes_atuais, analisar_comum, base_programacao_conjunto, cobertura_comum
from src.analises.conjunto import analisar_conjunto
from src.analises.cobertura import analisar_cobertura
from src.analises.conclusao import montar_conclusao, regras_omitidas
from src.analises.constatacoes import montar_achados, montar_achados_comum
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
from src.analises.hidrologia import analisar_hidrologia, analisar_hidrologia_sem_evt
from src.analises.indicadores import analisar_indicadores_ons
from src.analises.programacao import analisar_programacao
from src.analises.resultados import ResultadosAnalise, salvar_resultados
from src.analises.renovavel import analisar_renovavel, omissoes_renovavel
from src.analises.termica import analisar_termica
from src.coleta import registro
from src.coleta.serie_referencia import escolher
from src.comum import caminhos
from src.comum.logger import setup_logger
from src.comum.regras import CONJUNTO_DISPONIBILIDADE, CONJUNTO_EVT, CONJUNTO_GERACAO, CONJUNTO_HIDROLOGIA
from src.comum.persistencia import registrar_gravacoes
from src.conferencia.resultado import ResultadoConferencia, carregar_conferencias
from src.pipeline import CODIGO_SUCESSO, ResultadoEtapa
from src.tratamento.base_horaria import carregar_base_horaria
from src.tratamento.disponibilidade import carregar_disponibilidade_tratada
from src.tratamento.geracao import carregar_geracao_tratada
from src.tratamento.hidrologia import carregar_hidrologia_tratada
from src.tratamento.indicadores import IndicadoresONS, carregar_indicadores_tratados
from src.tratamento.programacao import ProgramacaoONS, carregar_programacao_tratada
from src.tratamento.series import SerieConjunto
from src.tratamento.renovavel import carregar_renovavel
from src.tratamento.termica import DespachoTratado, SemanalTratado, carregar_despacho_tratado, carregar_semanal_tratado
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
    ``datas_obtencao`` é o ``datas_obtencao.csv`` da Coleta, por conjunto (plano das Análises, D25).
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


def serie_do_conjunto(perfil: Any, base: pd.DataFrame, geracao: Optional[SerieConjunto]) -> Optional[pd.DataFrame]:
    """Geração do conjunto hora a hora (``din_instante``, ``geracao_mw``) da usina em conjunto: as horas do
    nível do conjunto da base horária, quando a série de referência é a do conjunto; senão, a Geração por usina do
    conjunto (eólica ou solar com série própria). None fora de conjunto."""
    if not getattr(perfil.identificacao, "id_conjunto", None):
        return None
    if escolher(perfil).conjunto == "geracao":
        return base.loc[base["nivel"] == "conjunto", ["din_instante", "geracao_mw"]]
    if geracao is None or not len(geracao.horaria) or registro.nivel_coletado(perfil, "geracao") != "conjunto":
        return None
    h = geracao.horaria
    return pd.DataFrame({"din_instante": pd.to_datetime(h["din_instante"]),
                         "geracao_mw": pd.to_numeric(h["val_geracao"], errors="coerce")})


def niveis_da_usina(perfil: Any, composicao: Optional[pd.DataFrame] = None) -> Dict[str, Dict[str, str]]:
    """Nível e identificador da série de referência, da programação e da disponibilidade (decisão D17)."""
    ident = perfil.identificacao
    niveis_ref = escolher(perfil).niveis
    nome = ""
    if composicao is not None and len(composicao) and "nom_conjunto" in composicao.columns:
        nome = str(composicao["nom_conjunto"].iloc[0] or "").strip()
    saida: Dict[str, Dict[str, str]] = {"geracao": {
        "nivel": " e ".join(niveis_ref),
        "identificador_usina": str(ident.id_ons or "") if "usina" in niveis_ref else "",
        "identificador_conjunto": str(getattr(ident, "id_conjunto", "") or "") if "conjunto" in niveis_ref else "",
        "nome": nome,
    }}
    if escolher(perfil).conjunto == "restricao_detalhe":  # a série de referência é a restrição com detalhe
        saida["geracao"]["fonte"] = "restricao_detalhe"
    nivel_programacao = registro.nivel_coletado(perfil, "programacao")
    if nivel_programacao:
        codigos = getattr(ident, "codigos_programacao", ()) or (ident.cod_programacao,)
        saida["programacao"] = {"nivel": nivel_programacao, "identificador": "; ".join(codigos)}
    if registro.nivel_coletado(perfil, "disponibilidade"):
        saida["disponibilidade"] = {"nivel": "usina", "identificador": str(ident.id_ons or "")}
    for chave in ("fator_capacidade", "restricao_razao"):  # eólicas e solares: usina ou conjunto, identificados
        nivel = registro.nivel_coletado(perfil, chave)
        if nivel:
            saida[chave] = {"nivel": nivel, "identificador": str(getattr(ident, "id_conjunto", "") or "")
                            if nivel == "conjunto" else str(ident.id_ons or "")}
    return saida


def analisar_sem_evt(
    base: pd.DataFrame,
    perfil: Any,
    conferencias: Dict[str, ResultadoConferencia],
    datas_obtencao: Optional[Dict[str, Dict[str, Any]]] = None,
    indicadores: Optional[IndicadoresONS] = None,
    programacao: Optional[ProgramacaoONS] = None,
    ausencias_geracao: Optional[pd.DataFrame] = None,
    linhas_usina_sem_valor: int = 0,
    trechos: Optional[pd.DataFrame] = None,
    composicao: Optional[pd.DataFrame] = None,
    cadastro: Optional[pd.DataFrame] = None,
    dicionarios: Optional[pd.DataFrame] = None,
    auditoria_cadastro: Optional[pd.DataFrame] = None,
    nao_aplicaveis: Optional[pd.DataFrame] = None,
    capacidade: Optional[pd.DataFrame] = None,
    despacho: Optional[DespachoTratado] = None,
    cvu: Optional[SemanalTratado] = None,
    cmo: Optional[SemanalTratado] = None,
    renovavel: Optional[Dict[str, Optional[pd.DataFrame]]] = None,
    geracao_conjunto: Optional[SerieConjunto] = None,
    linhas_usina_sem_valor_periodo: Optional[Dict[str, str]] = None,
    capacidade_membros: Optional[pd.DataFrame] = None,
    tipo_publicado: Optional[pd.DataFrame] = None,
    hidrologia: Optional[SerieConjunto] = None,
) -> ResultadosAnalise:
    """Resultados das usinas sem EVT: as seções comuns sobre a base horária comum (decisão D16).

    Os campos de EVT ficam vazios; ``cobertura`` traz o período da série de referência, e ``comum``, as seções. Na
    usina em conjunto, também a composição e a geração do conjunto (decisão D22); na hidrelétrica com os Dados
    hidrológicos, a afluência sem os cruzamentos com a EVT (decisão D23).
    """
    tipo = registro.tipo_da_usina(perfil)
    niveis = niveis_da_usina(perfil, composicao)
    conjunto = analisar_conjunto(serie_do_conjunto(perfil, base, geracao_conjunto), trechos, composicao,
                                 capacidade_membros, tipo_publicado, str(getattr(perfil.identificacao, "id_conjunto", "")
                                                                         or ""), niveis["geracao"].get("nome", ""),
                                 str(perfil.identificacao.ceg))
    hidro = (analisar_hidrologia_sem_evt(hidrologia, conferencias.get("alinhamento_hidrologia"),
                                         cobertura_comum(base, ausencias_geracao),
                                         _obtido_em(datas_obtencao or {}, CONJUNTO_HIDROLOGIA))
             if tipo in registro.HIDRELETRICAS else {})
    tem_indicadores = indicadores is not None and len(indicadores.ug_mensal) > 0
    nivel_programacao = registro.nivel_coletado(perfil, "programacao") if programacao is not None else None
    base_programacao = None  # base da usina (restrição com detalhe) e programação do conjunto
    if (escolher(perfil).conjunto == "restricao_detalhe" and nivel_programacao == "conjunto" and programacao is not None
            and geracao_conjunto is not None and len(geracao_conjunto.horaria)):
        base_programacao = base_programacao_conjunto(geracao_conjunto.horaria, programacao.horaria)
    comum, omitidos = analisar_comum(
        base, perfil, tipo, ausencias_geracao, linhas_usina_sem_valor, nivel_programacao,
        programacao.dias_ausentes if programacao is not None else None,
        len(programacao.horaria) if programacao is not None else 0,
        indicadores=tem_indicadores, hidrologia=registro.nivel_coletado(perfil, "hidrologia") is not None,
        base_programacao=base_programacao, linhas_usina_sem_valor_periodo=linhas_usina_sem_valor_periodo,
        conjunto=bool(conjunto), hidrologia_presente=bool(hidro))
    comum["conferencias_nao_aplicaveis"] = nao_aplicaveis if nao_aplicaveis is not None else pd.DataFrame(
        columns=["conferencia", "motivo"])
    comum["agentes"] = agentes_atuais(capacidade, comum["cobertura"]["fim"])
    vazio = pd.DataFrame()
    res = ResultadosAnalise(
        cobertura=comum["cobertura"], globais={}, indicadores_anuais=vazio, evt_mensal=vazio,
        distribuicao_mes_do_ano=vazio, evt_por_faixa_geracao=vazio, perfil_horario_geracao=vazio,
        perfil_horario_evt=vazio, eventos_parada_com_evt=vazio, eventos_indisponibilidade_total=vazio,
        mudanca_classificacao={}, anomalias=vazio, resumo_anomalias=vazio, extremos=vazio, perfil_estatistico=vazio,
    )
    res.tipo, res.modalidade = tipo, str(getattr(perfil.usina, "modalidade", "") or "")
    res.niveis = niveis
    res.trechos = trechos if trechos is not None else pd.DataFrame()
    res.conjunto, res.hidrologia = conjunto, hidro
    res.comum, res.omitidos = comum, omitidos
    res.datas_obtencao = datas_obtencao or {}
    if tipo in registro.TERMICAS:  # seções de térmica (decisão D20)
        res.termica = analisar_termica(despacho, base, cvu, cmo)
        if res.termica:  # G3 e G4, para as legendas de fonte e o resumo executivo
            res.termica["conferencias"] = {
                i: {"aplicavel": r.aplicavel, "motivo": r.motivo, "comparados": r.comparados,
                    "coincidentes": r.coincidentes, "divergentes": r.divergentes, **r.tabelas.get("resumo", {}),
                    "mensal": r.tabelas.get("mensal"), "divergencias": r.tabelas.get("divergencias")}
                for i, r in conferencias.items() if i in ("programacao_despacho", "verificada_despacho")}
        if despacho is not None and not res.termica:
            res.omitidos.append({"item": "Seções de térmica", "tipo": "secao",
                                 "motivo": "o despacho não tem horas no período da série de referência"})
        elif res.termica and cvu is not None and cmo is not None and not res.termica.get("cvu_cmo"):
            res.omitidos.append({"item": "CVU × CMO", "tipo": "secao",
                                 "motivo": "o CVU e o CMO não têm semanas comuns no período"})
    if tipo in registro.RENOVAVEIS:  # seções de eólica e solar (decisão D21)
        res.renovavel = analisar_renovavel(renovavel or {}, base if base_programacao is None else base_programacao, tipo,
                                           float(perfil.parametros.potencia_instalada_mw), comum.get("programacao"))
        if res.renovavel:  # G1, G2 e G5, para as legendas de fonte e a planilha
            res.renovavel["conferencias"] = {
                i: {"aplicavel": r.aplicavel, "motivo": r.motivo, "comparados": r.comparados,
                    "coincidentes": r.coincidentes, "divergentes": r.divergentes, **r.tabelas.get("resumo", {}),
                    "pares": r.tabelas.get("pares"), "mensal": r.tabelas.get("mensal"),
                    "divergencias": r.tabelas.get("divergencias")}
                for i, r in conferencias.items() if i in ("geracao_fontes", "soma_conjunto", "programacao_renovaveis")}
        res.omitidos = res.omitidos + omissoes_renovavel(perfil, res.renovavel)
    if tem_indicadores:
        anuais = comum["anuais"]
        da_usina = anuais[anuais["nivel"] == "usina"][["ano", "disponibilidade_relativa_pct"]]
        dispf = conferencias.get("dispf_horas")
        indicadores.divergencias = dispf.tabelas.get("divergencias", pd.DataFrame()) if dispf else pd.DataFrame()
        taxas = conferencias.get("teifa_teip")
        recalculo = taxas.tabelas.get("recalculo") if taxas else None
        reproducao = ({"meses": taxas.comparados, "reproduzidos": taxas.coincidentes,
                       "diferenca_maxima_pp": taxas.tabelas.get("diferenca_maxima_pp", float("nan"))}
                      if taxas is not None and taxas.aplicavel else None)
        res.ons = analisar_indicadores_ons(indicadores, base[base["nivel"] == "usina"], da_usina, res.cobertura,
                                           recalculo, reproducao)
    if cadastro is not None and len(cadastro):
        res.cadastro = analisar_cadastro(cadastro, auditoria_cadastro)
    if dicionarios is not None and len(dicionarios):
        res.dicionarios = {"registro": dicionarios}
    res.achados = montar_achados_comum(res)
    res.conclusao = montar_conclusao(res)
    res.omitidos = res.omitidos + regras_omitidas(res)
    res.indicadores_carteira = indicadores_carteira(res)  # decisão D24
    return res


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


def _ler_csv_texto(caminho: Path) -> Optional[pd.DataFrame]:
    return _ler_csv(caminho, dtype=str, keep_default_na=False)


def carregar_entradas_sem_evt(slug: str, referencia: str = "geracao") -> Dict[str, Any]:
    """Base horária comum, conferências e registros da Coleta da usina sem EVT, prontos para ``analisar_sem_evt``;
    as horas ausentes são as da série de referência (``referencia``: a Geração por usina ou a restrição com detalhe)."""
    coleta = caminhos.pasta_etapa(slug, "coleta")
    tratamento = caminhos.pasta_etapa(slug, "tratamento")
    conferencia = caminhos.pasta_etapa(slug, "conferencia")
    conferencias = carregar_conferencias(conferencia / caminhos.ARQUIVOS_CONFERENCIA["resultados"])
    resumo_coleta = json.loads((coleta / caminhos.MANIFESTO_ETAPA).read_text(encoding="utf-8")).get("resumo", {})
    auditoria_prog = _ler_csv(coleta / caminhos.ARQUIVOS_COLETA["auditoria_programacao"])
    if auditoria_prog is not None and "dia" in auditoria_prog.columns:
        auditoria_prog["dia"] = pd.to_datetime(auditoria_prog["dia"])
    auditoria_cadastro = _ler_csv(coleta / caminhos.ARQUIVOS_COLETA["auditoria_cadastro"], keep_default_na=False)
    if auditoria_cadastro is not None:
        auditoria_cadastro = auditoria_cadastro[COLUNAS_AUDITORIA_CADASTRO]
    chave_ausencias = "restricao_ausencias" if referencia == "restricao_detalhe" else "geracao_ausencias"
    ausencias = _ler_csv(tratamento / caminhos.ARQUIVOS_TRATAMENTO[chave_ausencias])
    if ausencias is not None:
        for coluna in ("inicio", "fim"):
            ausencias[coluna] = pd.to_datetime(ausencias[coluna])
    return {
        "base": carregar_base_horaria(tratamento),
        "conferencias": conferencias,
        "datas_obtencao": datas_da_coleta(coleta),
        "indicadores": carregar_indicadores_tratados(tratamento),
        "programacao": carregar_programacao_tratada(tratamento, auditoria_prog),
        "ausencias_geracao": ausencias,
        "linhas_usina_sem_valor": int(resumo_coleta.get("linhas_usina_sem_valor") or 0),
        "linhas_usina_sem_valor_periodo": resumo_coleta.get("linhas_usina_sem_valor_periodo") or {},
        # as unidades das usinas do conjunto e o tipo publicado (ausentes nas Coletas anteriores)
        "capacidade_membros": _ler_csv_texto(coleta / caminhos.ARQUIVOS_COLETA["capacidade_membros"]),
        "tipo_publicado": _ler_csv_texto(coleta / caminhos.ARQUIVOS_COLETA["tipo_publicado"]),
        "hidrologia": carregar_hidrologia_tratada(tratamento),
        "trechos": _ler_csv_texto(coleta / caminhos.ARQUIVOS_COLETA["trechos"]),
        "composicao": _ler_csv_texto(coleta / caminhos.ARQUIVOS_COLETA["composicao"]),
        "cadastro": ficha_do_cadastro(coleta, conferencias.get("cadastro")),
        "dicionarios": _ler_csv(coleta / caminhos.ARQUIVOS_COLETA["dicionarios"], keep_default_na=False),
        "auditoria_cadastro": auditoria_cadastro,
        "nao_aplicaveis": _ler_csv_texto(conferencia / caminhos.ARQUIVOS_CONFERENCIA["nao_aplicaveis"]),
        "capacidade": _ler_csv_texto(coleta / caminhos.ARQUIVOS_COLETA["capacidade"]),
        "despacho": carregar_despacho_tratado(tratamento),
        "cvu": carregar_semanal_tratado(tratamento, "cvu"),
        "cmo": carregar_semanal_tratado(tratamento, "cmo"),
        "renovavel": carregar_renovavel(tratamento),
        # a Geração por usina do conjunto, para a comparação com a programação do conjunto e a seção do conjunto
        "geracao_conjunto": carregar_geracao_tratada(tratamento) if referencia == "restricao_detalhe" else None,
    }


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


def _executar_sem_evt(perfil: Any, pasta: Path) -> ResultadoEtapa:
    entradas = carregar_entradas_sem_evt(perfil.usina.slug, escolher(perfil).conjunto)
    res = analisar_sem_evt(perfil=perfil, **entradas)
    with registrar_gravacoes() as gravacoes:
        salvar_resultados(res, pasta / caminhos.ARQUIVOS_ANALISES["resultados"])
    cobertura = res.cobertura
    resumo = {
        "tipo": res.tipo,
        "periodo": {"inicio": str(cobertura.get("inicio")), "fim": str(cobertura.get("fim"))},
        "horas_analisadas": int(cobertura.get("horas_observadas", 0)),
        "niveis": cobertura.get("niveis", {}),
        "constatacoes": len(res.achados),
        "conclusao": dict(sorted(Counter(item["lista"] for item in res.conclusao).items())),
        "regras_da_conclusao": sorted({item["regra"] for item in res.conclusao}, key=lambda r: int(r[1:])),
        "omitidos": [item["item"] for item in res.omitidos],
        "bases_complementares": {
            "indicadores": bool(res.ons), "programacao": bool(res.comum.get("programacao")),
            "disponibilidade": bool(res.comum.get("disponibilidade")), "cadastro": bool(res.cadastro),
            **({"despacho": bool(res.termica), "cvu_cmo": bool(res.termica.get("cvu_cmo"))}
               if res.tipo in registro.TERMICAS else {}),
            **({k: bool((res.renovavel or {}).get(k)) for k in ("fator_capacidade", "restricao", "recurso")}
               if res.tipo in registro.RENOVAVEIS else {}),
            # a seção do conjunto e a de afluência sem EVT
            **({"conjunto": bool(res.conjunto)} if getattr(perfil.identificacao, "id_conjunto", None) else {}),
            **({"hidrologia": bool(res.hidrologia)} if res.tipo in registro.HIDRELETRICAS else {}),
        },
    }
    return ResultadoEtapa(codigo=CODIGO_SUCESSO, arquivos=[p for p, _ in gravacoes], resumo=resumo)


def executar_analises(perfil: Any) -> ResultadoEtapa:
    """Calcula os resultados da usina e grava ``resultados.pkl`` (código 0)."""
    slug = perfil.usina.slug
    pasta = caminhos.pasta_etapa(slug, "analises")
    if escolher(perfil).conjunto != "evt":
        return _executar_sem_evt(perfil, pasta)
    entradas = carregar_entradas(slug)
    for nome in ("indicadores", "programacao", "disponibilidade", "hidrologia", "geracao", "cadastro"):
        if entradas[nome] is None:
            logger.warning("Base '%s' sem dados tratados para a usina: o relatório sai sem a seção correspondente.",
                           nome)
    res = analisar(**entradas)
    res.tipo = registro.tipo_da_usina(perfil)
    res.modalidade = str(getattr(perfil.usina, "modalidade", "") or "")
    res.indicadores_carteira = indicadores_carteira(res)  # decisão D24: só o campo novo muda
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
