"""Tratamento de dados: prepara o que a Coleta extraiu da usina para a Conferência e as Análises.

Lê só a pasta da Coleta da usina (e o dicionário de dados da EVT) e grava ``data/usinas/<slug>/tratamento/``:
base de EVT tratada e validação física; indicadores e taxas; programação horária; séries horárias de disponibilidade,
hidrologia e geração, com ausências e auditoria completa (spec do Tratamento de dados). O cadastro não tem tratamento.

Nas usinas sem EVT (decisão D15), o período vem da série de referência da Coleta, só os conjuntos coletados
são tratados e a base horária comum (``base_horaria.csv``) fica no lugar da base de EVT. Nas eólicas e solares em
conjunto com série própria (decisão D19), a base horária vem da restrição com detalhe da usina, pela média das duas
meias-horas, com a disponibilidade e a programação só quando estão no nível da usina.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from src.coleta.registro import conjuntos_da_usina, descricoes, nivel_coletado, tipo_da_usina
from src.coleta.serie_referencia import escolher
from src.comum import caminhos
from src.comum.logger import setup_logger
from src.comum.persistencia import registrar_gravacoes
from src.pipeline import CODIGO_ERRO, CODIGO_SUCESSO, ResultadoEtapa
from src.tratamento.base_horaria import exportar_base_horaria, montar_base_horaria, resumo_base_horaria
from src.tratamento.disponibilidade import tratar_disponibilidade
from src.tratamento.evt import tratar_evt
from src.tratamento.geracao import tratar_geracao
from src.tratamento.hidrologia import tratar_hidrologia
from src.tratamento.indicadores import TOLERANCIA_IDENTIDADE_HORAS, exportar_indicadores, montar_indicadores
from src.tratamento.programacao import exportar_programacao, montar_programacao
from src.tratamento.renovavel import (
    exportar_renovavel,
    montar_membros,
    montar_razao,
    montar_restricao,
    serie_da_referencia,
    tratar_fator_capacidade,
)
from src.tratamento.series import SerieConjunto
from src.tratamento.termica import exportar_termica, montar_cmo, montar_cvu, montar_despacho

logger = setup_logger("tratamento")

FORMATO_DATA = "%Y-%m-%d %H:%M:%S"
_TEXTOS_AUDITORIA = {c: str for c in ("arquivo", "formato", "periodo", "data_publicacao", "status", "mensagem")}


def ler_auditoria_coleta(caminho: Path, datas: Sequence[str] = ()) -> pd.DataFrame:
    """Auditoria gravada pela Coleta, com os textos como gravados e as datas pedidas convertidas."""
    try:
        auditoria = pd.read_csv(caminho, sep=";", keep_default_na=False, dtype=_TEXTOS_AUDITORIA)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    if "obtido" in auditoria.columns:
        auditoria["obtido"] = auditoria["obtido"].astype(str).str.lower().isin(["true", "1"])
    for coluna in datas:
        if coluna in auditoria.columns:
            auditoria[coluna] = pd.to_datetime(auditoria[coluna].replace("", None))
    return auditoria


def _resumo_serie(serie: SerieConjunto) -> Dict[str, Any]:
    qualidade = serie.horaria["qualidade"] if "qualidade" in serie.horaria.columns else pd.Series(dtype=str)
    codigos = qualidade[qualidade != "OK"].str.split(",").explode().value_counts().sort_index()
    return {
        "horas": len(serie.horaria),
        "horas_ausentes": int(pd.to_numeric(serie.ausencias.get("horas", pd.Series(dtype=int))).sum()),
        "horas_sinalizadas": {str(k): int(v) for k, v in codigos.items()},
        "duplicatas_conflitantes": int(serie.auditoria["duplicatas_conflitantes"].sum()) if len(serie.auditoria) else 0,
    }


def _tratar_indicadores(coleta: Path, pasta: Path, inicio: pd.Timestamp, fim: pd.Timestamp) -> Dict[str, Any]:
    ind = montar_indicadores(pd.read_parquet(coleta / caminhos.ARQUIVOS_COLETA["indicadores"]), inicio, fim)
    exportar_indicadores(ind, pasta)
    residuos = ind.horas_estado["residuo_identidade_h"].abs() > TOLERANCIA_IDENTIDADE_HORAS \
        if len(ind.horas_estado) else pd.Series(dtype=bool)
    return {
        "linhas_mensais": len(ind.ug_mensal), "linhas_anuais": len(ind.ug_anual),
        "meses_unidade_horas_estado": len(ind.horas_estado), "meses_taxas": len(ind.taxas),
        "meses_unidade_residuo_acima_tolerancia": int(residuos.sum()),
    }


def _tratar_programacao(coleta: Path, pasta: Path, inicio: pd.Timestamp, fim: pd.Timestamp) -> Any:
    arq_coleta = caminhos.ARQUIVOS_COLETA
    prog = montar_programacao(pd.read_parquet(coleta / arq_coleta["programacao"]),
                              ler_auditoria_coleta(coleta / arq_coleta["auditoria_programacao"], ["dia"]),
                              inicio, fim)
    exportar_programacao(prog, pasta)
    return prog


def _tratar_serie(perfil: Any, nome: str, coleta: Path, pasta: Path, inicio: pd.Timestamp,
                  fim: pd.Timestamp) -> SerieConjunto:
    tratar = {"disponibilidade": tratar_disponibilidade, "hidrologia": tratar_hidrologia, "geracao": tratar_geracao}
    arq_coleta = caminhos.ARQUIVOS_COLETA
    return tratar[nome](descricoes(perfil)[nome], pd.read_parquet(coleta / arq_coleta[nome]),
                        ler_auditoria_coleta(coleta / arq_coleta[f"auditoria_{nome}"]), inicio, fim, pasta)


def _ler_opcional(caminho: Path, leitor: Any) -> pd.DataFrame:
    try:
        return leitor(caminho)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()


def _tratar_sem_evt(perfil: Any, coleta: Path, pasta: Path, resumo: Dict[str, Any]) -> None:
    """Usinas sem EVT (decisão D15): o período da série de referência, os conjuntos coletados e a base horária."""
    periodo = json.loads((coleta / caminhos.MANIFESTO_ETAPA).read_text(encoding="utf-8"))["resumo"]["periodo"]
    inicio, fim = pd.Timestamp(periodo["inicio"]), pd.Timestamp(periodo["fim"])
    resumo["periodo"] = {"inicio": inicio.strftime(FORMATO_DATA), "fim": fim.strftime(FORMATO_DATA)}
    chaves = {e.chave for e in conjuntos_da_usina(perfil)}
    if "indicadores" in chaves:
        resumo["indicadores"] = _tratar_indicadores(coleta, pasta, inicio, fim)
    prog = None
    if "programacao" in chaves:
        prog = _tratar_programacao(coleta, pasta, inicio, fim)
        resumo["programacao"] = {"horas": len(prog.horaria), "dias_ausentes": len(prog.dias_ausentes)}
    series: Dict[str, SerieConjunto] = {}
    for nome in ("disponibilidade", "hidrologia", "geracao"):
        if nome in chaves:
            series[nome] = _tratar_serie(perfil, nome, coleta, pasta, inicio, fim)
            resumo[nome] = _resumo_serie(series[nome])
    restricao = _tratar_renovavel(perfil, chaves, coleta, pasta, inicio, fim, resumo)
    escolha = escolher(perfil)
    referencia, disponibilidade = series.get("geracao"), series.get("disponibilidade")
    programada = prog.horaria if prog is not None else None
    if escolha.conjunto == "restricao_detalhe":  # a base é da usina: os dados do conjunto não entram nela
        referencia = serie_da_referencia(restricao)
        if nivel_coletado(perfil, "disponibilidade") != "usina":
            disponibilidade = None
        if nivel_coletado(perfil, "programacao") != "usina":
            programada = None
    arq_coleta = caminhos.ARQUIVOS_COLETA
    complemento = _ler_opcional(coleta / arq_coleta["geracao_complemento"], pd.read_parquet)
    trechos = _ler_opcional(coleta / arq_coleta["trechos"],
                            lambda c: pd.read_csv(c, sep=";", dtype=str, keep_default_na=False))
    base = montar_base_horaria(referencia, complemento, trechos, disponibilidade, programada, escolha.niveis[0])
    exportar_base_horaria(base, pasta)
    resumo["base_horaria"] = resumo_base_horaria(base, referencia.ausencias)
    _tratar_termica(perfil, chaves, coleta, pasta, inicio, fim, resumo)


def _tratar_termica(perfil: Any, chaves: set, coleta: Path, pasta: Path, inicio: pd.Timestamp, fim: pd.Timestamp,
                    resumo: Dict[str, Any]) -> None:
    """Despacho, CVU e CMO das térmicas, quando coletados (FR-037 a FR-040; decisão D16)."""
    arq = caminhos.ARQUIVOS_COLETA
    planejamento = getattr(perfil.identificacao, "planejamento", ()) or ()

    def entrada(nome: str):
        return pd.read_parquet(coleta / arq[nome]), ler_auditoria_coleta(coleta / arq[f"auditoria_{nome}"])

    despacho = cvu = cmo = None
    if "despacho" in chaves:
        despacho = montar_despacho(*entrada("despacho"), planejamento, inicio, fim)
        resumo["despacho"] = {
            "horas": len(despacho.horario), "horas_unidade": len(despacho.unidades),
            "codigos": sorted(int(c) for c in despacho.unidades["codigo"].unique()),
            "horas_ausentes": int(pd.to_numeric(despacho.ausencias["horas"]).sum()) if len(despacho.ausencias) else 0,
            "duplicatas_conflitantes": int(despacho.auditoria["duplicatas_conflitantes"].sum())
            if len(despacho.auditoria) else 0,
        }
    if "cvu" in chaves:
        cvu = montar_cvu(*entrada("cvu"), planejamento, inicio, fim)
        resumo["cvu"] = cvu.resumo
    if "cmo" in chaves:
        cmo = montar_cmo(*entrada("cmo"), str(perfil.usina.subsistema), inicio, fim)
        resumo["cmo"] = cmo.resumo
    exportar_termica(pasta, despacho, cvu, cmo)


def _tratar_renovavel(perfil: Any, chaves: set, coleta: Path, pasta: Path, inicio: pd.Timestamp, fim: pd.Timestamp,
                      resumo: Dict[str, Any]) -> Any:
    """Fator de capacidade, restrição com a razão e com detalhe e os membros do conjunto das eólicas e solares, quando
    coletados (FR-041 a FR-044; decisões D16 e D17). Devolve a restrição com detalhe tratada (ou None)."""
    arq = caminhos.ARQUIVOS_COLETA

    def entrada(nome: str):
        return pd.read_parquet(coleta / arq[nome]), ler_auditoria_coleta(coleta / arq[f"auditoria_{nome}"])

    if "fator_capacidade" in chaves:
        fc = tratar_fator_capacidade(descricoes(perfil)["fator_capacidade"], *entrada("fator_capacidade"), inicio,
                                     fim, pasta)
        resumo["fator_capacidade"] = {**_resumo_serie(fc), "nivel": nivel_coletado(perfil, "fator_capacidade"),
                                      "horas_fc_fora_0_1": int(fc.horaria["sinal_fc_fora_0_1"].sum()),
                                      "horas_acima_capacidade": int(fc.horaria["sinal_acima_capacidade"].sum())}
    razao = restricao = None
    if "restricao_razao" in chaves:
        razao = montar_razao(*entrada("restricao_razao"), nivel_coletado(perfil, "restricao_razao"), inicio, fim)
        codigos = razao["cod_razaorestricao"].replace("", "sem razão").value_counts().sort_index()
        resumo["restricao_razao"] = {"semi_horas": len(razao), "nivel": nivel_coletado(perfil, "restricao_razao"),
                                     "semi_horas_por_razao": {str(k): int(v) for k, v in codigos.items()}}
    if "restricao_detalhe" in chaves:
        restricao = montar_restricao(*entrada("restricao_detalhe"), tipo_da_usina(perfil), inicio, fim, razao)
        resumo["restricao_detalhe"] = restricao.resumo
    membros = None
    if (coleta / arq["restricao_membros"]).exists():
        membros = montar_membros(pd.read_parquet(coleta / arq["restricao_membros"]), inicio, fim)
        resumo["membros_restricao"] = {str(k): int(v) for k, v in membros.groupby("id_ons").size().items()}
    if razao is not None or restricao is not None or membros is not None:
        exportar_renovavel(pasta, restricao, razao, membros)
    return restricao


def executar_tratamento(perfil: Any) -> ResultadoEtapa:
    """Trata os conjuntos extraídos pela Coleta para a usina do perfil (código 0, ou 1 com violação da R1)."""
    slug = perfil.usina.slug
    coleta = caminhos.pasta_etapa(slug, "coleta")
    pasta = caminhos.pasta_etapa(slug, "tratamento")
    arq_coleta, arq = caminhos.ARQUIVOS_COLETA, caminhos.ARQUIVOS_TRATAMENTO
    resumo: Dict[str, Any] = {}
    if escolher(perfil).conjunto != "evt":
        with registrar_gravacoes() as gravacoes:
            _tratar_sem_evt(perfil, coleta, pasta, resumo)
        resumo["gravacoes"] = {str(k): v for k, v in sorted(Counter(r.value for _, r in gravacoes).items())}
        return ResultadoEtapa(codigo=CODIGO_SUCESSO, arquivos=[p for p, _ in gravacoes], resumo=resumo)
    with registrar_gravacoes() as gravacoes:
        # Base de EVT: tipagem, regras R1 a R9, sinalização e três formatos
        codigo, _, resumo_evt = tratar_evt(perfil, coleta / arq_coleta["evt"], {
            chave: pasta / arq[chave] for chave in ("evt_parquet", "evt_csv", "evt_xlsx", "validacao_csv", "validacao_md")
        })
        inicio, fim = resumo_evt.pop("inicio"), resumo_evt.pop("fim")
        resumo["periodo"] = {"inicio": inicio.strftime(FORMATO_DATA), "fim": fim.strftime(FORMATO_DATA)}
        resumo["evt"] = resumo_evt
        if codigo != CODIGO_SUCESSO:
            return ResultadoEtapa(codigo=CODIGO_ERRO, arquivos=[p for p, _ in gravacoes], resumo=resumo)

        # Indicadores e taxas
        resumo["indicadores"] = _tratar_indicadores(coleta, pasta, inicio, fim)

        # Programação diária
        prog = _tratar_programacao(coleta, pasta, inicio, fim)
        resumo["programacao"] = {"horas": len(prog.horaria), "dias_ausentes": len(prog.dias_ausentes)}

        # Séries horárias
        for nome in ("disponibilidade", "hidrologia", "geracao"):
            resumo[nome] = _resumo_serie(_tratar_serie(perfil, nome, coleta, pasta, inicio, fim))
    arquivos: List[Path] = [p for p, _ in gravacoes]
    resumo["gravacoes"] = {str(k): v for k, v in sorted(Counter(r.value for _, r in gravacoes).items())}
    return ResultadoEtapa(codigo=CODIGO_SUCESSO, arquivos=arquivos, resumo=resumo)
