"""Tratamento de dados: prepara o que a Coleta extraiu da usina para a Conferência e as Análises.

Lê só a pasta da Coleta da usina (e o dicionário de dados da EVT) e grava ``data/usinas/<slug>/tratamento/``:
base de EVT tratada e validação física; indicadores e taxas; programação horária; séries horárias de disponibilidade,
hidrologia e geração, com ausências e auditoria completa (spec do Tratamento de dados). O cadastro não tem tratamento.

Nas usinas sem EVT (spec 006, decisão R30), o período vem da série de referência da Coleta, só os conjuntos coletados
são tratados e a base horária comum (``base_horaria.csv``) fica no lugar da base de EVT.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from src.coleta.registro import conjuntos_da_usina, descricoes
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
from src.tratamento.series import SerieConjunto

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
    """Usinas sem EVT (decisão R30): o período da série de referência, os conjuntos coletados e a base horária."""
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
    arq_coleta = caminhos.ARQUIVOS_COLETA
    complemento = _ler_opcional(coleta / arq_coleta["geracao_complemento"], pd.read_parquet)
    trechos = _ler_opcional(coleta / arq_coleta["trechos"],
                            lambda c: pd.read_csv(c, sep=";", dtype=str, keep_default_na=False))
    base = montar_base_horaria(series["geracao"], complemento, trechos, series.get("disponibilidade"),
                               prog.horaria if prog is not None else None, escolher(perfil).niveis[0])
    exportar_base_horaria(base, pasta)
    resumo["base_horaria"] = resumo_base_horaria(base, series["geracao"].ausencias)


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
