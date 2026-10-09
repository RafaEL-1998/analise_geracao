"""Resultados das Análises (``resultados.pkl``): tudo o que a Geração do relatório mostra."""

from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from src.comum.persistencia import ResultadoGravacao, gravar_bytes

# Muda quando os campos mudam; a Geração do relatório recusa um formato diferente.
# 2: datas de obtenção da Coleta em ``datas_obtencao`` (spec 006, decisão R22).
VERSAO_FORMATO = 2


@dataclass
class ResultadosAnalise:
    """Resultados calculados que alimentam planilha, relatório Markdown e PDF."""

    cobertura: Dict[str, Any]
    globais: Dict[str, Any]
    indicadores_anuais: pd.DataFrame
    evt_mensal: pd.DataFrame
    distribuicao_mes_do_ano: pd.DataFrame
    evt_por_faixa_geracao: pd.DataFrame
    perfil_horario_geracao: pd.DataFrame
    perfil_horario_evt: pd.DataFrame
    eventos_parada_com_evt: pd.DataFrame
    eventos_indisponibilidade_total: pd.DataFrame
    mudanca_classificacao: Dict[str, Any]
    anomalias: pd.DataFrame
    resumo_anomalias: pd.DataFrame
    extremos: pd.DataFrame
    perfil_estatistico: pd.DataFrame
    # Tabela de parâmetros e origem dos dados: montadas na Geração do relatório (spec das Análises, FR-042)
    parametros: pd.DataFrame = field(default_factory=pd.DataFrame)
    validacao: pd.DataFrame = field(default_factory=pd.DataFrame)
    horas_geracao_zero: pd.DataFrame = field(default_factory=pd.DataFrame)
    achados: List[Tuple[str, str]] = field(default_factory=list)
    # Conclusão (spec das Análises, US4): itens das regras C1 a C11
    conclusao: List[Dict[str, Any]] = field(default_factory=list)
    # Indicadores oficiais do ONS por unidade geradora (vazio se não foram gerados)
    ons: Dict[str, Any] = field(default_factory=dict)
    # Programação diária do ONS cruzada com a operação verificada (vazio se não foi gerada)
    programacao: Dict[str, Any] = field(default_factory=dict)
    # Bases complementares do ONS; vazios se a etapa correspondente não rodou
    disponibilidade: Dict[str, Any] = field(default_factory=dict)
    hidrologia: Dict[str, Any] = field(default_factory=dict)
    geracao_oficial: Dict[str, Any] = field(default_factory=dict)
    cadastro: Dict[str, Any] = field(default_factory=dict)
    dicionarios: Dict[str, Any] = field(default_factory=dict)
    # Datas de obtenção por conjunto, do ``datas_obtencao.csv`` da Coleta (arquivos registrados, publicação e
    # obtenção mais recentes, só dos arquivos do escopo da usina)
    datas_obtencao: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Origem dos dados (legendas de fonte do relatório): datas de obtenção por conjunto e conjuntos carregados
    fontes: Dict[str, Any] = field(default_factory=dict)
    # Dados das figuras 01 (médias diárias) e 05 (vazões médias anuais), para a Geração do relatório só desenhar
    serie_diaria: pd.DataFrame = field(default_factory=pd.DataFrame)
    vazoes_anuais: pd.DataFrame = field(default_factory=pd.DataFrame)


def salvar_resultados(res: ResultadosAnalise, destino: Path) -> ResultadoGravacao:
    """Grava ``resultados.pkl`` com a versão do formato (sem cópia ``.bak``: é refeito a partir dos dados)."""
    conteudo = pickle.dumps({"versao_formato": VERSAO_FORMATO, "resultados": res}, protocol=pickle.HIGHEST_PROTOCOL)
    return gravar_bytes(conteudo, destino, copia=False)


def carregar_resultados(caminho: Path) -> ResultadosAnalise:
    """Resultados gravados pelas Análises; formato diferente do atual é recusado."""
    with open(caminho, "rb") as f:
        dados = pickle.load(f)
    if not isinstance(dados, dict) or dados.get("versao_formato") != VERSAO_FORMATO:
        raise ValueError(f"{Path(caminho).name}: formato diferente do atual ({VERSAO_FORMATO}); refaça as Análises")
    return dados["resultados"]
