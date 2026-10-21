"""Eólicas e solares no Tratamento de dados (spec 006, fase C; decisões R11 e R12; rascunho 002, FR-041 a FR-044).

- **Restrição com detalhe** (semi-horária): uma linha por semi-hora, a do arquivo publicado por último, com o recurso
  (vento ou irradiância), a marca de restrição e a energia cortada = máx(estimada − verificada, 0) × 0,5 h só nas
  semi-horas restritas (``flg_geracaorestrita = 1``). A diferença fora delas é erro da estimativa e não entra; a
  semi-hora sem a marca fica com ``sem_marca_restricao``, contada e fora do total. A razão (REL, CNF, ENE) vem da
  restrição com a razão, na mesma semi-hora, com o nível dela (usina ou conjunto).
- **Estimativa ausente** (decisão do usuário de 21/10/2026): estimada 0 com geração verificada acima de 1 MW é
  estimativa que o ONS não calculou; vira ``sinal_estimada_ausente``, fica fora das médias e, na semi-hora restrita, o
  corte não é calculado (vazio).
- **Hora cheia**: a média das duas meias-horas, só para os cruzamentos com as séries horárias; a hora com uma só
  meia-hora fica ausente e é contada (FR-016).
- **Fator de capacidade** (horário): com o nível e as sinalizações ``sinal_fc_fora_0_1`` e ``sinal_acima_capacidade``.
- Sinalização não descarta (FR-017): o recurso marcado como inválido pelo ONS vira ``sinal_recurso_invalido``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from src.coleta.conjuntos import COLUNA_INSTANTE, COLUNA_NAO_NUMERICO
from src.coleta.registro import COLUNAS_RECURSO, COLUNAS_RESTRICAO_RAZAO
from src.comum.caminhos import ARQUIVOS_TRATAMENTO
from src.comum.logger import setup_logger
from src.comum.persistencia import gravar_csv
from src.comum.regras import (
    DURACAO_SEMI_HORA_H,
    LIMIAR_GERACAO_PARADA_MW,
    TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW,
)
from src.tratamento.series import COLUNAS_AUDITORIA, COLUNAS_AUSENCIAS, SerieConjunto, exportar_serie, \
    listar_ausencias, montar_serie
from src.tratamento.termica import _auditoria, _meses_com_arquivo, _ordem_dos_arquivos, _sem_repeticoes

logger = setup_logger("tratamento")

COLUNAS_SEMI_HORARIA = [COLUNA_INSTANTE, "val_geracaoverificada", "val_geracaoestimada", "val_recurso",
                        "flg_recurso_invalido", "flg_geracaorestrita", "sinal_recurso_invalido",
                        "sinal_estimada_ausente", "restrita", "sem_marca_restricao", "energia_cortada_mwh",
                        "cod_razaorestricao", "nivel_razao", "num_minutos_rel", "num_minutos_cnf", "num_minutos_ene",
                        "arquivo_origem"]
COLUNAS_HORARIA = [COLUNA_INSTANTE, "val_geracaoverificada", "val_geracaoestimada", "val_recurso",
                   "semi_horas_recurso_invalido", "semi_horas_estimada_ausente", "semi_horas_restritas",
                   "energia_cortada_mwh"]
COLUNAS_RAZAO = [COLUNA_INSTANTE, "nivel", *COLUNAS_RESTRICAO_RAZAO, "cod_razaorestricao", "arquivo_origem"]
COLUNAS_MEMBROS = [COLUNA_INSTANTE, "id_ons", "val_geracaoverificada"]


def _no_periodo(t: pd.DataFrame, inicio: pd.Timestamp, fim: pd.Timestamp) -> pd.DataFrame:
    """Semi-horas das horas do período (a série de referência pode terminar na meia-hora; as demais, na hora)."""
    if t.empty:
        return t
    instantes = pd.to_datetime(t[COLUNA_INSTANTE])
    return t[(instantes >= pd.Timestamp(inicio).floor("h"))
             & (instantes < pd.Timestamp(fim).floor("h") + pd.Timedelta(hours=1))].reset_index(drop=True)


def em_hora_cheia(semi: pd.DataFrame, colunas_media: Any, colunas_soma: Any = (),
                  completa: str = "val_geracaoverificada") -> pd.DataFrame:
    """Hora cheia pela média das duas meias-horas com valor em ``completa``; a hora com uma só meia-hora com valor
    fica fora (é contada nas ausências)."""
    if semi is None or semi.empty:
        return pd.DataFrame(columns=[COLUNA_INSTANTE, *colunas_media, *colunas_soma])
    t = semi.assign(_hora=pd.to_datetime(semi[COLUNA_INSTANTE]).dt.floor("h"))
    g = t.groupby("_hora")
    horaria = g[list(colunas_media)].mean()
    for coluna in colunas_soma:
        horaria[coluna] = g[coluna].sum(min_count=1)
    completas = g[completa].count() == 2
    return horaria[completas].rename_axis(COLUNA_INSTANTE).reset_index()


# ---------------------------------------------------------------------------
# Restrição com a razão e com detalhe
# ---------------------------------------------------------------------------


def montar_razao(extraido: pd.DataFrame, auditoria_coleta: pd.DataFrame, nivel: str, inicio: pd.Timestamp,
                 fim: pd.Timestamp) -> pd.DataFrame:
    """Restrição com a razão por semi-hora, a do arquivo publicado por último, com o nível (usina ou conjunto)."""
    if extraido is None or not len(extraido):
        return pd.DataFrame(columns=COLUNAS_RAZAO)
    t = extraido.copy()
    t[COLUNA_INSTANTE] = pd.to_datetime(t[COLUNA_INSTANTE])
    t, _ = _sem_repeticoes(t, [COLUNA_INSTANTE], list(COLUNAS_RESTRICAO_RAZAO), _ordem_dos_arquivos(auditoria_coleta))
    t["cod_razaorestricao"] = t["cod_razaorestricao"].fillna("").astype(str).str.strip().str.upper()
    t["nivel"] = nivel
    return _no_periodo(t, inicio, fim).reindex(columns=COLUNAS_RAZAO)


@dataclass
class RestricaoTratada:
    """Restrição com detalhe por semi-hora e por hora cheia, horas ausentes, auditoria e resumo."""

    semi_horaria: pd.DataFrame
    horaria: pd.DataFrame
    ausencias: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=COLUNAS_AUSENCIAS))
    auditoria: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=COLUNAS_AUDITORIA))
    resumo: Dict[str, Any] = field(default_factory=dict)


def montar_restricao(extraido: pd.DataFrame, auditoria_coleta: pd.DataFrame, tipo: str, inicio: pd.Timestamp,
                     fim: pd.Timestamp, razao: Optional[pd.DataFrame] = None) -> RestricaoTratada:
    """Restrição com detalhe tratada (decisão R12), com a razão da semi-hora quando há a restrição com a razão."""
    recurso, invalido = COLUNAS_RECURSO[tipo]
    ordem = _ordem_dos_arquivos(auditoria_coleta)
    if extraido is not None and len(extraido):
        t = extraido.rename(columns={recurso: "val_recurso", invalido: "flg_recurso_invalido"}).copy()
        t[COLUNA_INSTANTE] = pd.to_datetime(t[COLUNA_INSTANTE])
    else:
        t = pd.DataFrame(columns=[COLUNA_INSTANTE, "val_geracaoverificada", "val_geracaoestimada", "val_recurso",
                                  "flg_recurso_invalido", "flg_geracaorestrita", COLUNA_NAO_NUMERICO, "arquivo_origem"])
    registros = t.groupby("arquivo_origem")[COLUNA_INSTANTE].nunique().to_dict() if len(t) else {}
    valores = ["val_geracaoverificada", "val_geracaoestimada", "val_recurso", "flg_recurso_invalido",
               "flg_geracaorestrita"]
    t, conflitos = _sem_repeticoes(t, [COLUNA_INSTANTE], valores, ordem)
    t = _no_periodo(t, inicio, fim)
    for coluna in valores:
        t[coluna] = pd.to_numeric(t[coluna], errors="coerce")
    t["sinal_recurso_invalido"] = t["flg_recurso_invalido"] == 1
    # estimada 0 com a usina gerando: estimativa que o ONS não calculou (decisão do usuário de 21/10/2026)
    t["sinal_estimada_ausente"] = (t["val_geracaoestimada"] == 0) & (t["val_geracaoverificada"]
                                                                    > LIMIAR_GERACAO_PARADA_MW)
    t["restrita"] = t["flg_geracaorestrita"] == 1
    t["sem_marca_restricao"] = t["flg_geracaorestrita"].isna()
    corte = (t["val_geracaoestimada"] - t["val_geracaoverificada"]).clip(lower=0) * DURACAO_SEMI_HORA_H
    t["energia_cortada_mwh"] = (corte.where(t["restrita"], 0.0).where(~t["sem_marca_restricao"])
                                .where(~(t["restrita"] & t["sinal_estimada_ausente"])))  # corte não calculável
    if razao is not None and len(razao):
        r = razao.drop_duplicates(COLUNA_INSTANTE).set_index(COLUNA_INSTANTE)
        t["cod_razaorestricao"] = t[COLUNA_INSTANTE].map(r["cod_razaorestricao"]).fillna("")
        t["nivel_razao"] = t[COLUNA_INSTANTE].map(r["nivel"]).fillna("")
        for coluna in ("num_minutos_rel", "num_minutos_cnf", "num_minutos_ene"):
            t[coluna] = t[COLUNA_INSTANTE].map(r[coluna])
    else:
        t["cod_razaorestricao"], t["nivel_razao"] = "", ""
    semi = t.reindex(columns=COLUNAS_SEMI_HORARIA).sort_values(COLUNA_INSTANTE).reset_index(drop=True)
    contagens = {"semi_horas_recurso_invalido": semi["sinal_recurso_invalido"].astype(int),
                 "semi_horas_estimada_ausente": semi["sinal_estimada_ausente"].astype(int),
                 "semi_horas_restritas": semi["restrita"].astype(int)}
    # na hora cheia, a estimada ausente fica fora da média
    por_hora = semi.assign(val_geracaoestimada=semi["val_geracaoestimada"].where(~semi["sinal_estimada_ausente"]),
                           **contagens)
    horaria = em_hora_cheia(por_hora, ["val_geracaoverificada", "val_geracaoestimada", "val_recurso"],
                            [*contagens, "energia_cortada_mwh"])
    ausencias = listar_ausencias(horaria[COLUNA_INSTANTE], pd.Timestamp(inicio).floor("h"),
                                 pd.Timestamp(fim).floor("h"), _meses_com_arquivo(auditoria_coleta))
    resumo = {
        "semi_horas": len(semi), "horas": len(horaria),
        "horas_ausentes": int(pd.to_numeric(ausencias["horas"]).sum()) if len(ausencias) else 0,
        "semi_horas_restritas": int(semi["restrita"].sum()),
        "semi_horas_sem_marca": int(semi["sem_marca_restricao"].sum()),
        "semi_horas_recurso_invalido": int(semi["sinal_recurso_invalido"].sum()),
        "semi_horas_estimada_ausente": int(semi["sinal_estimada_ausente"].sum()),
        "semi_horas_restritas_sem_estimativa": int((semi["restrita"] & semi["sinal_estimada_ausente"]).sum()),
        "energia_cortada_mwh": float(semi["energia_cortada_mwh"].sum()),
        "duplicatas_conflitantes": int(conflitos.sum()) if len(conflitos) else 0,
    }
    logger.info("Restrição com detalhe: %d semi-horas, %d restritas, %.1f MWh cortados.", len(semi),
                resumo["semi_horas_restritas"], resumo["energia_cortada_mwh"])
    return RestricaoTratada(semi_horaria=semi, horaria=horaria, ausencias=ausencias,
                            auditoria=_auditoria(auditoria_coleta, registros, conflitos, "horas_usina",
                                                 COLUNAS_AUDITORIA), resumo=resumo)


def serie_da_referencia(restricao: RestricaoTratada) -> SerieConjunto:
    """A restrição com detalhe como série de referência da base horária comum (linha da fase C da decisão R6): a
    geração verificada da usina em hora cheia, com as horas ausentes."""
    h = restricao.horaria
    horaria = pd.DataFrame({COLUNA_INSTANTE: h[COLUNA_INSTANTE], "val_geracao": h["val_geracaoverificada"],
                            "qualidade": "OK", "arquivo_origem": ""})
    return SerieConjunto(horaria=horaria, ausencias=restricao.ausencias, auditoria=restricao.auditoria)


def montar_membros(extraido: Optional[pd.DataFrame], inicio: pd.Timestamp, fim: pd.Timestamp) -> pd.DataFrame:
    """Geração verificada das outras usinas do conjunto em hora cheia, por id ONS (só para a G2)."""
    if extraido is None or not len(extraido):
        return pd.DataFrame(columns=COLUNAS_MEMBROS)
    partes = []
    for id_ons, g in extraido.groupby("id_ons"):
        g = g.assign(din_instante=pd.to_datetime(g[COLUNA_INSTANTE])).drop_duplicates(COLUNA_INSTANTE, keep="last")
        horaria = em_hora_cheia(_no_periodo(g, inicio, fim), ["val_geracaoverificada"])
        partes.append(horaria.assign(id_ons=id_ons))
    return pd.concat(partes, ignore_index=True).reindex(columns=COLUNAS_MEMBROS)


# ---------------------------------------------------------------------------
# Fator de capacidade
# ---------------------------------------------------------------------------


def _arquivos_fc(pasta: Path) -> Dict[str, Path]:
    pasta = Path(pasta)
    return {"horaria": pasta / ARQUIVOS_TRATAMENTO["fator_capacidade_horario"],
            "ausencias": pasta / ARQUIVOS_TRATAMENTO["fator_capacidade_ausencias"],
            "auditoria": pasta / ARQUIVOS_TRATAMENTO["auditoria_fator_capacidade"]}


def tratar_fator_capacidade(desc: Any, extraido: pd.DataFrame, auditoria: pd.DataFrame, inicio: pd.Timestamp,
                            fim: pd.Timestamp, pasta: Path) -> SerieConjunto:
    """Fator de capacidade horário com o nível e as sinalizações (FR-044), gravado na pasta do tratamento."""
    serie = montar_serie(desc, extraido, auditoria, inicio, fim)
    h = serie.horaria
    posicao = h.columns.get_loc("arquivo_origem")
    h.insert(posicao, "sinal_acima_capacidade",
             (h["val_geracaoverificada"] > h["val_capacidadeinstalada"]
              + TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW).fillna(False))
    h.insert(posicao, "sinal_fc_fora_0_1", ((h["val_fatorcapacidade"] < 0) | (h["val_fatorcapacidade"] > 1)).fillna(False))
    h.insert(1, "nivel", desc.nivel)
    exportar_serie(serie, _arquivos_fc(pasta))
    return serie


# ---------------------------------------------------------------------------
# Gravação e leitura
# ---------------------------------------------------------------------------


def exportar_renovavel(pasta: Path, restricao: Optional[RestricaoTratada] = None,
                       razao: Optional[pd.DataFrame] = None, membros: Optional[pd.DataFrame] = None) -> None:
    """Grava a restrição tratada (semi-horária, horária, ausências e auditoria), a razão e os membros."""
    pasta, arq = Path(pasta), ARQUIVOS_TRATAMENTO
    if restricao is not None:
        gravar_csv(restricao.semi_horaria, pasta / arq["restricao_semi_horaria"])
        gravar_csv(restricao.horaria, pasta / arq["restricao_horaria"])
        gravar_csv(restricao.ausencias, pasta / arq["restricao_ausencias"])
        gravar_csv(restricao.auditoria, pasta / arq["auditoria_restricao_detalhe"])
    if razao is not None:
        gravar_csv(razao, pasta / arq["restricao_razao_semi_horaria"])
    if membros is not None and len(membros):
        gravar_csv(membros, pasta / arq["restricao_membros_horaria"])


def _ler(caminho: Path, datas=(COLUNA_INSTANTE,)) -> Optional[pd.DataFrame]:
    if not caminho.exists():
        return None
    try:
        tabela = pd.read_csv(caminho, sep=";", keep_default_na=True)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    for coluna in datas:
        if coluna in tabela.columns:
            tabela[coluna] = pd.to_datetime(tabela[coluna])
    return tabela


def carregar_renovavel(pasta: Path) -> Dict[str, Optional[pd.DataFrame]]:
    """Tabelas gravadas pelo Tratamento das eólicas e solares (None nas ausentes)."""
    pasta, arq = Path(pasta), ARQUIVOS_TRATAMENTO
    saida = {chave: _ler(pasta / arq[chave]) for chave in ("fator_capacidade_horario", "restricao_semi_horaria",
                                                           "restricao_horaria", "restricao_razao_semi_horaria",
                                                           "restricao_membros_horaria")}
    saida["restricao_ausencias"] = _ler(pasta / arq["restricao_ausencias"], ("inicio", "fim"))
    for chave in ("restricao_semi_horaria",):
        t = saida[chave]
        if t is not None and len(t):
            for coluna in ("sinal_recurso_invalido", "sinal_estimada_ausente", "restrita", "sem_marca_restricao"):
                t[coluna] = t[coluna].astype(str).str.lower().isin(["true", "1"])
            for coluna in ("cod_razaorestricao", "nivel_razao"):
                t[coluna] = t[coluna].fillna("").astype(str)
    return saida
