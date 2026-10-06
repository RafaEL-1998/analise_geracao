"""Módulo de análise estatística, indicadores operacionais e gráficos da UHE São Domingos (Feature 003).

Todos os números e todas as frases de constatação produzidos aqui são calculados a partir
dos dados tratados. Os únicos valores fixos são parâmetros documentados em config.py
(características técnicas da usina, com a respectiva fonte, e limiares de análise).
"""

from __future__ import annotations

import argparse
import calendar
import json
import logging
import math
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from src.config import (  # noqa: E402
    ANO_INICIO_OPERACAO_COMERCIAL,
    AUDIT_REPORT_FILE,
    CEG_USINA,
    COD_EXIBICAO_USINA_PROGRAMACAO,
    COD_USINA_ONS,
    CONJUNTO_PROGRAMACAO_DIARIA,
    CONJUNTOS_INDICADORES_ONS,
    DEFAULT_PLOT_DPI,
    DISPONIBILIDADE_REFERENCIA,
    DURACAO_MINIMA_EVENTO_RELATORIO_H,
    ENGOLIMENTO_MAXIMO_USINA_M3S,
    ENGOLIMENTO_NOMINAL_UG_M3S,
    FAIXA_PRODUTIVIDADE_RELATIVA,
    FONTE_GARANTIA_FISICA,
    FONTE_PARAMETROS_USINA,
    FRACAO_PLENA_CARGA,
    GARANTIA_FISICA_MWMED,
    HORAS_DIURNAS,
    HORAS_NOTURNAS,
    ID_ONS_USINA,
    IP_REFERENCIA,
    LIMIAR_DESVIO_PROGRAMACAO_MW,
    LIMIAR_GERACAO_PARADA_MW,
    LIMIAR_INDISPONIBILIDADE_TOTAL_MW,
    LIMIAR_VERTIMENTO_MINIMO_M3S,
    NOMINAL_INSTALLED_CAPACITY_MW,
    NUMERO_EVENTOS_RELATORIO,
    NUMERO_UNIDADES_GERADORAS,
    ONS_DATASET_URL,
    ONS_PORTAL_DATASET_URL,
    OPERATIONAL_METRIC_COLUMNS,
    PDF_REPORT_PATH,
    PERDA_HIDRAULICA_M,
    POTENCIA_UNITARIA_MW,
    PRODUTIVIDADE_NOMINAL_MW_M3S,
    QUEDA_BRUTA_M,
    RAW_MANIFEST_FILE,
    RENDIMENTO_TURBINA_GERADOR,
    REPORTS_DIR,
    REPORTS_FIGURES_DIR,
    STATISTICAL_REPORT_CSV,
    STATISTICAL_REPORT_MD,
    STATISTICAL_REPORT_XLSX,
    TEIF_REFERENCIA,
    TIPO_TURBINA,
    TOLERANCIA_DIVERGENCIA_HORAS,
    TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW,
    TOLERANCIA_LIMITES_FISICOS,
    TREATED_FILE_PARQUET,
    TREATED_FILE_XLSX,
    VAZAO_REMANESCENTE_M3S,
)
from src.logger import configurar_nivel_log  # noqa: E402
from src.indicadores_ons import (  # noqa: E402
    INSUMOS_HORAS,
    TOLERANCIA_IDENTIDADE_HORAS,
    IndicadoresONS,
    carregar_indicadores_processados,
    decompor_taxas,
    recalcular_taxas,
)
from src.programacao_ons import (  # noqa: E402
    PARADA_EVT_PROGRAMACAO_POSITIVA,
    PARADA_EVT_PROGRAMACAO_ZERO,
    ProgramacaoONS,
    carregar_programacao_processada,
    classificar_horas,
    eventos_desvio,
    perfil_hora_do_dia,
    resumo_mensal,
)
from src.conjuntos_ons import SerieConjunto  # noqa: E402
from src.dicionarios_ons import carregar_registro as carregar_registro_dicionarios  # noqa: E402
from src.fontes_relatorio import (  # noqa: E402
    cabecalho_fontes,
    legenda_fonte,
    origem_dos_dados,
    tabela_fontes_abas,
)
from src.conjuntos_ons import data_obtencao  # noqa: E402
from src.geracao_ons import carregar_geracao_processada, conferir_geracao  # noqa: E402
from src.cadastro_ons import carregar_auditoria_cadastro, carregar_cadastro_processado  # noqa: E402
from src.config import (  # noqa: E402
    CONJUNTO_CADASTRO,
    CONJUNTO_DISPONIBILIDADE,
    CONJUNTO_GERACAO,
    CONJUNTO_HIDROLOGIA,
    DISPONIBILIDADE_RAW_DIR,
    ESTADO_USINA,
    GERACAO_RAW_DIR,
    HIDROLOGIA_RAW_DIR,
    ID_RESERVATORIO_ONS,
    LIMIAR_SINCRONIZADA_MW,
    META_ALINHAMENTO_HIDROLOGIA_PCT,
    TOLERANCIA_COINCIDENCIA_MW,
    TOLERANCIA_COINCIDENCIA_VAZAO_M3S,
)
from src.hidrologia_ons import (  # noqa: E402
    ACIMA_ENGOLIMENTO_USINA,
    ATE_UMA_UNIDADE,
    COM_PARADA_EVT,
    DEMAIS_DIAS,
    ENTRE_UMA_E_DUAS_UNIDADES,
    FAIXAS_AFLUENCIA,
    SEM_DADO_HIDROLOGICO,
    carregar_hidrologia_processada,
    classificar_faixas,
    perfil_hora_do_dia as perfil_hidrologico,
    resumir as resumir_hidrologia,
    resumir_faixas,
)
from src.disponibilidade_ons import (  # noqa: E402
    COM_EVT,
    NAO_SINCRONIZADA,
    SEM_PROGRAMACAO,
    carregar_disponibilidade_processada,
    classificar_horas_paradas,
    conferir_com_evt,
    resumir as resumir_disponibilidade,
)
from src.programacao_ons import DESCRICAO_CLASSES  # noqa: E402
from src.formatacao import (  # noqa: E402
    MESES_ABREVIADOS,
    MESES_EXTENSO,
    fmt_data,
    fmt_data_hora,
    fmt_int,
    fmt_lista,
    fmt_mes_ano,
    fmt_num,
    fmt_pct,
    fmt_pp,
    plural,
)
from src.validator import (  # noqa: E402
    COLUNA_QUALIDADE,
    COLUNAS_ANOMALIA,
    DESCRICAO_ANOMALIA,
    QUALIDADE_OK,
    faixa_produtividade,
    sinalizar_anomalias,
    validar_regras_fisicas,
)

logger = logging.getLogger("analyzer")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [analyzer] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Faixas intermediárias de geração usadas apenas na apresentação da EVT por nível de geração
FAIXAS_GERACAO_INTERMEDIARIAS_MW: List[float] = [10.0, 20.0, 30.0, 40.0]
# Razão EVT diurna/noturna a partir da qual o texto aponta concentração diurna
RAZAO_DIURNA_RELEVANTE: float = 2.0
MESES_MAIO_A_OUTUBRO: List[int] = [5, 6, 7, 8, 9, 10]
MESES_JANEIRO_A_ABRIL: List[int] = [1, 2, 3, 4]

# Paleta (validada com o script do skill de dataviz sobre superfície branca)
COR_GERACAO = "#2a78d6"
COR_EVT = "#eb6834"
COR_DISPONIBILIDADE = "#1baf7a"
COR_CONTEXTO = "#b5b3ac"
COR_TINTA = "#0b0b0b"
COR_TINTA_SECUNDARIA = "#52514e"
COR_TINTA_SUAVE = "#898781"
COR_GRADE = "#e1e0d9"
COR_EIXO = "#c3c2b7"
COR_FAIXA_INDISPONIBILIDADE = "#e7e5de"
RAMPA_AZUL = ["#f3f8fe", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
RAMPA_LARANJA = ["#fdf3ee", "#f9d6c4", "#f4b08f", "#ef8a5d", "#eb6834", "#c24f1f", "#8c3612"]
# Bases complementares (spec 006). Cores validadas com o script da skill de visualização sobre fundo branco:
# disponibilidade sincronizada = posição 4 da ordem categórica (amarelo; contraste < 3:1 compensado por rótulo
# direto e tabela); vazão afluente = posição 7 (violeta), a única que passa em todos os pares com turbinada e
# vertida (linhas que se cruzam); faixas de afluência = rampa ordinal de laranja (horas com EVT), passos com
# contraste mínimo de 2,48:1 no passo claro.
COR_SINCRONIZADA = "#eda100"
COR_AFLUENCIA = "#4a3aa7"
RAMPA_FAIXAS_AFLUENCIA = [RAMPA_LARANJA[3], RAMPA_LARANJA[5], RAMPA_LARANJA[6]]

UNIDADES: Dict[str, str] = {
    "val_geracao": "MWmed",
    "val_disponibilidade": "MWmed",
    "val_vazaoturbinada": "m³/s",
    "val_vazaovertida": "m³/s",
    "val_vazaovertidanaoturbinavel": "m³/s",
    "val_produtividade": "MW/(m³/s)",
    "val_folgadegeracao": "MWmed",
    "val_energiavertida": "MWmed",
    "val_vazaovertidaturbinavel": "m³/s",
    "val_energiavertidaturbinavel": "MWmed",
}

NOMES_FIGURAS: Dict[str, str] = {
    "serie_temporal": "01_serie_temporal_disponibilidade_geracao_evt.png",
    "evt_mensal": "02_evt_mensal.png",
    "perfil_horario": "03_perfil_horario_geracao_evt.png",
    "disponibilidade_anual": "04_disponibilidade_geracao_anual.png",
    "vazoes_defluentes": "05_vazoes_defluentes_anuais.png",
}
# Figuras das bases complementares (spec 006): geradas só quando os dados correspondentes existem.
# Cada história acrescenta aqui a sua figura junto com a função _grafico_* correspondente.
NOMES_FIGURAS_OPCIONAIS: Dict[str, str] = {
    "disponibilidade_sincronizada": "06_disponibilidade_operacional_sincronizada_mensal.png",
    "faixas_afluencia": "07_evt_por_faixa_de_afluencia.png",
    "perfil_hidrologico": "08_perfil_horario_nivel_vazoes.png",
}


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
    parametros: pd.DataFrame
    validacao: pd.DataFrame = field(default_factory=pd.DataFrame)
    horas_geracao_zero: pd.DataFrame = field(default_factory=pd.DataFrame)
    achados: List[Tuple[str, str]] = field(default_factory=list)
    # Indicadores oficiais do ONS por unidade geradora (vazio se não foram gerados)
    ons: Dict[str, Any] = field(default_factory=dict)
    # Programação diária do ONS cruzada com a operação verificada (vazio se não foi gerada)
    programacao: Dict[str, Any] = field(default_factory=dict)
    # Bases complementares do ONS (spec 006); vazios se a etapa correspondente não rodou
    disponibilidade: Dict[str, Any] = field(default_factory=dict)
    hidrologia: Dict[str, Any] = field(default_factory=dict)
    geracao_oficial: Dict[str, Any] = field(default_factory=dict)
    cadastro: Dict[str, Any] = field(default_factory=dict)
    dicionarios: Dict[str, Any] = field(default_factory=dict)
    # Origem dos dados (spec 007): datas de obtenção por conjunto e conjuntos carregados
    fontes: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Carregamento
# ---------------------------------------------------------------------------


def preparar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena, cria colunas de calendário e garante as colunas de qualidade."""
    df = df.copy()
    df["din_instante"] = pd.to_datetime(df["din_instante"])
    df = df.sort_values("din_instante").reset_index(drop=True)
    df["ano"] = df["din_instante"].dt.year
    df["mes"] = df["din_instante"].dt.month
    df["hora"] = df["din_instante"].dt.hour
    if COLUNA_QUALIDADE not in df.columns:
        df = sinalizar_anomalias(df)
    return df


def carregar_dados_tratados(caminho_arquivo: Optional[Path] = None) -> pd.DataFrame:
    """Carrega os dados tratados do Parquet (preferencial), do Excel ou de CSV."""
    caminho = caminho_arquivo
    if caminho is None:
        if TREATED_FILE_PARQUET.exists():
            caminho = TREATED_FILE_PARQUET
        elif TREATED_FILE_XLSX.exists():
            caminho = TREATED_FILE_XLSX
        else:
            raise FileNotFoundError(
                "Nenhum arquivo de dados tratados encontrado em data/processed/. "
                "Execute a Feature 002 previamente."
            )

    logger.info("Carregando base de dados tratada de: %s", caminho)
    if str(caminho).endswith(".parquet"):
        df = pd.read_parquet(caminho)
    elif str(caminho).endswith((".xlsx", ".xls")):
        df = pd.read_excel(caminho)
    else:
        df = pd.read_csv(caminho, sep=";", low_memory=False)

    df = preparar_dados(df)
    logger.info("Base carregada com sucesso: %d registros horários.", len(df))
    return df


# ---------------------------------------------------------------------------
# Máscaras e utilitários
# ---------------------------------------------------------------------------


def horas_no_ano(ano: int) -> int:
    return 8784 if calendar.isleap(int(ano)) else 8760


def _mascara_evt(df: pd.DataFrame) -> pd.Series:
    return df["val_energiavertidaturbinavel"] > 0


def _mascara_parada_com_evt(df: pd.DataFrame) -> pd.Series:
    return (df["val_geracao"] <= LIMIAR_GERACAO_PARADA_MW) & _mascara_evt(df)


def _mascara_vertimento_minimo(df: pd.DataFrame) -> pd.Series:
    return df["val_vazaovertida"] <= LIMIAR_VERTIMENTO_MINIMO_M3S


def _mascara_indisponibilidade_total(df: pd.DataFrame) -> pd.Series:
    return df["val_disponibilidade"] <= LIMIAR_INDISPONIBILIDADE_TOTAL_MW


def _media(serie: pd.Series) -> float:
    return float(serie.mean()) if len(serie) else math.nan


def _razao(numerador: float, denominador: float) -> float:
    if denominador is None or math.isnan(denominador) or denominador == 0:
        return math.nan
    return float(numerador) / float(denominador)


def _pct(parte: float, todo: float) -> float:
    return _razao(parte, todo) * 100.0


def _rotulo_janela(horas: List[int]) -> str:
    return f"{horas[0]}h às {horas[-1]}h"


def _periodo_do_arquivo(nome_arquivo: str) -> str:
    """Extrai '2015' ou '01/2024' do nome ENERGIA_VERTIDA_TURBINAVEL_<periodo>.csv."""
    base = Path(str(nome_arquivo)).stem
    periodo = base.rsplit("TURBINAVEL_", 1)[-1]
    partes = periodo.split("_")
    if len(partes) == 2:
        return f"{partes[1]}/{partes[0]}"
    return periodo


# ---------------------------------------------------------------------------
# Cobertura dos dados
# ---------------------------------------------------------------------------


def _resumo_auditoria(caminho_auditoria: Optional[Path]) -> Dict[str, Any]:
    caminho = Path(caminho_auditoria) if caminho_auditoria else AUDIT_REPORT_FILE
    if not caminho.exists():
        return {}
    aud = pd.read_csv(caminho, sep=";")
    status = aud.get("status_processamento", pd.Series(dtype=str))
    divergencias = 0
    for coluna in ("registros_codigo_sem_nome", "registros_nome_sem_codigo"):
        if coluna in aud.columns:
            divergencias += int(aud[coluna].sum())
    return {
        "total": len(aud),
        "com_registros": int((status == "PROCESSADO").sum()),
        "sem_registros": [_periodo_do_arquivo(n) for n in aud.loc[status == "SEM_REGISTROS", "nome_arquivo"]],
        "falhas": aud.loc[status == "FALHA", "nome_arquivo"].tolist(),
        "divergencias": divergencias,
    }


def _resumo_manifesto(caminho_manifesto: Optional[Path]) -> Dict[str, Any]:
    caminho = Path(caminho_manifesto) if caminho_manifesto else RAW_MANIFEST_FILE
    if not caminho.exists():
        return {}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            entradas = list(json.load(f).values())
    except (OSError, json.JSONDecodeError):
        return {}
    if not entradas:
        return {}
    modificacoes = [e.get("ultima_modificacao", "") for e in entradas if e.get("ultima_modificacao")]
    registros = [e.get("registrado_em_utc", "") for e in entradas if e.get("registrado_em_utc")]
    return {
        "arquivos": len(entradas),
        "ultima_modificacao_mais_recente": max(modificacoes) if modificacoes else "",
        "registro_mais_recente_utc": max(registros) if registros else "",
    }


def analisar_cobertura(
    df: pd.DataFrame,
    caminho_auditoria: Optional[Path] = None,
    caminho_manifesto: Optional[Path] = None,
) -> Dict[str, Any]:
    """Período coberto, horas ausentes, anos parciais, agentes e arquivos de origem."""
    inicio = df["din_instante"].min()
    fim = df["din_instante"].max()
    grade = pd.date_range(inicio, fim, freq="h")
    faltantes = grade.difference(pd.DatetimeIndex(df["din_instante"]))

    linhas = []
    for ano, g in df.groupby("ano"):
        primeiro = g["din_instante"].min()
        ultimo = g["din_instante"].max()
        parcial = primeiro > pd.Timestamp(int(ano), 1, 1, 0) or ultimo < pd.Timestamp(int(ano), 12, 31, 23)
        linhas.append(
            {
                "ano": int(ano),
                "primeiro_registro": primeiro,
                "ultimo_registro": ultimo,
                "horas_observadas": len(g),
                "horas_calendario": horas_no_ano(int(ano)),
                "cobertura_pct": len(g) / horas_no_ano(int(ano)) * 100.0,
                "ano_parcial": bool(parcial),
            }
        )
    por_ano = pd.DataFrame(linhas)

    agentes = (
        df.groupby("nom_agente")["din_instante"]
        .agg(["min", "max", "count"])
        .sort_values("min")
        .reset_index()
        .rename(columns={"min": "primeiro_registro", "max": "ultimo_registro", "count": "horas"})
    )
    identificacao = {
        coluna: " / ".join(sorted(df[coluna].astype(str).unique()))
        for coluna in ["id_subsistema", "nom_subsistema", "nom_bacia", "nom_rio", "nom_reservatorio", "cod_usina"]
        if coluna in df.columns
    }

    return {
        "inicio": inicio,
        "fim": fim,
        "horas_observadas": len(df),
        "horas_esperadas": len(grade),
        "horas_faltantes": list(faltantes),
        "duplicadas": int(df["din_instante"].duplicated().sum()),
        "por_ano": por_ano,
        "anos_parciais": por_ano.loc[por_ano["ano_parcial"], "ano"].tolist(),
        "anos_completos": por_ano.loc[~por_ano["ano_parcial"], "ano"].tolist(),
        "agentes": agentes,
        "identificacao": identificacao,
        "arquivos": _resumo_auditoria(caminho_auditoria),
        "manifesto": _resumo_manifesto(caminho_manifesto),
    }


# ---------------------------------------------------------------------------
# Indicadores
# ---------------------------------------------------------------------------


def calcular_indicadores_anuais(df: pd.DataFrame, cobertura: Dict[str, Any]) -> pd.DataFrame:
    """Indicadores por ano civil (anos parciais sinalizados)."""
    P = NOMINAL_INSTALLED_CAPACITY_MW
    parciais = set(cobertura["anos_parciais"])
    linhas = []
    for ano, g in df.groupby("ano"):
        horas = len(g)
        ger_med = _media(g["val_geracao"])
        disp_med = _media(g["val_disponibilidade"])
        energia = float(g["val_geracao"].sum())
        evt = float(g["val_energiavertidaturbinavel"].sum())
        evt_minimo = float(g.loc[_mascara_vertimento_minimo(g), "val_energiavertidaturbinavel"].sum())
        parada = _mascara_parada_com_evt(g)
        diurno = g["hora"].isin(HORAS_DIURNAS)
        noturno = g["hora"].isin(HORAS_NOTURNAS)
        disp = g["val_disponibilidade"]
        linhas.append(
            {
                "ano": int(ano),
                "ano_parcial": int(ano) in parciais,
                "horas_observadas": horas,
                "cobertura_pct": horas / horas_no_ano(int(ano)) * 100.0,
                "geracao_media_mwmed": ger_med,
                "disponibilidade_media_mwmed": disp_med,
                "fator_capacidade_pct": ger_med / P * 100.0,
                "disponibilidade_relativa_pct": disp_med / P * 100.0,
                "desvio_disponibilidade_referencia_pp": disp_med / P * 100.0 - DISPONIBILIDADE_REFERENCIA * 100.0,
                "geracao_sobre_garantia_fisica_pct": ger_med / GARANTIA_FISICA_MWMED * 100.0,
                "energia_gerada_mwh": energia,
                "evt_mwh": evt,
                "evt_vertimento_minimo_mwh": evt_minimo,
                "evt_demais_horas_mwh": evt - evt_minimo,
                "participacao_vertimento_minimo_pct": _pct(evt_minimo, evt),
                "indice_evt_pct": _pct(evt, energia + evt),
                "horas_com_evt": int(_mascara_evt(g).sum()),
                "horas_com_evt_pct": _pct(int(_mascara_evt(g).sum()), horas),
                "horas_parada_com_evt": int(parada.sum()),
                "evt_parada_mwh": float(g.loc[parada, "val_energiavertidaturbinavel"].sum()),
                "horas_indisponibilidade_total": int(_mascara_indisponibilidade_total(g).sum()),
                "horas_disponibilidade_ate_metade": int(((disp > LIMIAR_INDISPONIBILIDADE_TOTAL_MW) & (disp <= P / 2)).sum()),
                "evt_media_diurna_mw": _media(g.loc[diurno, "val_energiavertidaturbinavel"]),
                "evt_media_noturna_mw": _media(g.loc[noturno, "val_energiavertidaturbinavel"]),
                "razao_evt_diurna_noturna": _razao(
                    _media(g.loc[diurno, "val_energiavertidaturbinavel"]),
                    _media(g.loc[noturno, "val_energiavertidaturbinavel"]),
                ),
                "geracao_media_diurna_mw": _media(g.loc[diurno, "val_geracao"]),
                "geracao_media_noturna_mw": _media(g.loc[noturno, "val_geracao"]),
                "razao_geracao_diurna_noturna": _razao(
                    _media(g.loc[diurno, "val_geracao"]), _media(g.loc[noturno, "val_geracao"])
                ),
                "horas_com_anomalia": int((g[COLUNA_QUALIDADE] != QUALIDADE_OK).sum()),
            }
        )
    return pd.DataFrame(linhas)


def calcular_indicadores_globais(df: pd.DataFrame) -> Dict[str, Any]:
    """Indicadores do período completo, ponderados por hora."""
    P = NOMINAL_INSTALLED_CAPACITY_MW
    horas = len(df)
    ger_med = _media(df["val_geracao"])
    disp_med = _media(df["val_disponibilidade"])
    energia = float(df["val_geracao"].sum())
    evt = float(df["val_energiavertidaturbinavel"].sum())
    com_evt = _mascara_evt(df)
    parada = _mascara_parada_com_evt(df)
    limiar_plena = FRACAO_PLENA_CARGA * P
    plena = df["val_geracao"] >= limiar_plena
    evt_plena = float(df.loc[plena & com_evt, "val_energiavertidaturbinavel"].sum())
    evt_parada = float(df.loc[parada, "val_energiavertidaturbinavel"].sum())
    excede_folga = int((df["val_energiavertidaturbinavel"] - df["val_folgadegeracao"] > 1e-6).sum())
    anomalos = df[COLUNA_QUALIDADE] != QUALIDADE_OK
    idx_ger_max = df["val_geracao"].idxmax()

    return {
        "horas": horas,
        "geracao_media_mwmed": ger_med,
        "disponibilidade_media_mwmed": disp_med,
        "fator_capacidade_pct": ger_med / P * 100.0,
        "disponibilidade_relativa_pct": disp_med / P * 100.0,
        "disponibilidade_referencia_pct": DISPONIBILIDADE_REFERENCIA * 100.0,
        "desvio_disponibilidade_referencia_pp": disp_med / P * 100.0 - DISPONIBILIDADE_REFERENCIA * 100.0,
        "geracao_sobre_garantia_fisica_pct": ger_med / GARANTIA_FISICA_MWMED * 100.0,
        "energia_gerada_mwh": energia,
        "evt_mwh": evt,
        "indice_evt_pct": _pct(evt, energia + evt),
        "horas_com_evt": int(com_evt.sum()),
        "horas_com_evt_pct": _pct(int(com_evt.sum()), horas),
        "folga_media_com_evt_mw": _media(df.loc[com_evt, "val_folgadegeracao"]),
        "limiar_plena_carga_mw": limiar_plena,
        "evt_plena_carga_mwh": evt_plena,
        "evt_plena_carga_pct": _pct(evt_plena, evt),
        "horas_evt_acima_folga": excede_folga,
        "horas_parada_com_evt": int(parada.sum()),
        "evt_parada_mwh": evt_parada,
        "evt_parada_pct": _pct(evt_parada, evt),
        "disponibilidade_media_nas_paradas_mw": _media(df.loc[parada, "val_disponibilidade"]),
        "horas_geracao_zero": int((df["val_geracao"] == 0).sum()),
        "horas_geracao_zero_com_evt": int(((df["val_geracao"] == 0) & com_evt).sum()),
        "horas_geracao_ate_limiar_positiva_com_evt": int(((df["val_geracao"] > 0) & parada).sum()),
        "horas_com_anomalia": int(anomalos.sum()),
        "evt_em_registros_anomalos_mwh": float(df.loc[anomalos, "val_energiavertidaturbinavel"].sum()),
        "geracao_maxima_registrada_mw": float(df.loc[idx_ger_max, "val_geracao"]),
        "instante_geracao_maxima": df.loc[idx_ger_max, "din_instante"],
    }


def identificar_eventos(
    df: pd.DataFrame,
    mascara: pd.Series,
    agregacoes: Dict[str, Tuple[str, str]],
) -> pd.DataFrame:
    """Agrupa horas consecutivas em que a máscara é verdadeira (lacunas de horário quebram o evento)."""
    base = df.sort_values("din_instante")
    m = mascara.reindex(base.index).fillna(False).astype(bool)
    continuidade = base["din_instante"].diff().eq(pd.Timedelta(hours=1))
    inicio_evento = m & ~(m.shift(fill_value=False) & continuidade)
    grupo = inicio_evento.cumsum()
    selecao = base.loc[m].assign(_evento=grupo[m])
    colunas = ["inicio", "fim", "duracao_h", *agregacoes.keys()]
    if selecao.empty:
        return pd.DataFrame(columns=colunas)
    eventos = selecao.groupby("_evento").agg(
        inicio=("din_instante", "min"),
        fim=("din_instante", "max"),
        duracao_h=("din_instante", "size"),
        **agregacoes,
    )
    return eventos.reset_index(drop=True)[colunas]


def listar_eventos_parada_com_evt(df: pd.DataFrame) -> pd.DataFrame:
    """Eventos em que a usina ficou parada com vertimento turbinável."""
    return identificar_eventos(
        df,
        _mascara_parada_com_evt(df),
        {
            "geracao_media_mw": ("val_geracao", "mean"),
            "disponibilidade_media_mw": ("val_disponibilidade", "mean"),
            "vazao_vertida_media_m3s": ("val_vazaovertida", "mean"),
            "evt_mwh": ("val_energiavertidaturbinavel", "sum"),
        },
    )


def listar_eventos_indisponibilidade_total(df: pd.DataFrame) -> pd.DataFrame:
    """Eventos com disponibilidade declarada igual a zero."""
    return identificar_eventos(
        df,
        _mascara_indisponibilidade_total(df),
        {
            "vazao_vertida_media_m3s": ("val_vazaovertida", "mean"),
            "geracao_media_mw": ("val_geracao", "mean"),
        },
    )


def detectar_mudanca_classificacao(df: pd.DataFrame) -> Dict[str, Any]:
    """Detecta o mês a partir do qual a vazão vertida não turbinável passa a ser sempre positiva.

    Regra: mediana mensal de val_vazaovertidanaoturbinavel > 0 em todos os meses a partir
    do mês detectado e igual a zero no mês anterior.
    """
    periodo = df["din_instante"].dt.to_period("M")
    mediana = df.groupby(periodo)["val_vazaovertidanaoturbinavel"].median()
    positivos = (mediana > 0).to_numpy()
    zeros = np.flatnonzero(~positivos)
    if len(zeros) == 0 or zeros[-1] == len(positivos) - 1:
        return {"mes": None}

    mes = mediana.index[zeros[-1] + 1]
    minimo = _mascara_vertimento_minimo(df)
    antes = df[(periodo < mes) & minimo]
    depois = df[(periodo >= mes) & minimo]
    horas_antes = int((periodo < mes).sum())
    return {
        "mes": mes,
        "meses_antes": int((mediana.index < mes).sum()),
        "meses_depois": int((mediana.index >= mes).sum()),
        "turbinavel_tipica_antes_m3s": float(antes["val_vazaovertidaturbinavel"].median()) if len(antes) else math.nan,
        "nao_turbinavel_tipica_depois_m3s": float(depois["val_vazaovertidanaoturbinavel"].median()) if len(depois) else math.nan,
        "evt_media_vertimento_minimo_antes_mw": _media(antes["val_energiavertidaturbinavel"]),
        "pct_horas_vertimento_minimo_turbinavel_antes": _pct(
            int((antes["val_vazaovertidaturbinavel"] > 0).sum()), horas_antes
        ),
    }


def calcular_evt_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """EVT, geração e disponibilidade por mês, separando a EVT das horas de vertimento mínimo."""
    periodo = df["din_instante"].dt.to_period("M")
    evt_minimo = df["val_energiavertidaturbinavel"].where(_mascara_vertimento_minimo(df), 0.0)
    tabela = (
        df.assign(_periodo=periodo, _evt_minimo=evt_minimo)
        .groupby("_periodo")
        .agg(
            horas=("din_instante", "size"),
            energia_gerada_mwh=("val_geracao", "sum"),
            geracao_media_mw=("val_geracao", "mean"),
            disponibilidade_media_mw=("val_disponibilidade", "mean"),
            evt_mwh=("val_energiavertidaturbinavel", "sum"),
            evt_vertimento_minimo_mwh=("_evt_minimo", "sum"),
        )
    )
    tabela["evt_demais_horas_mwh"] = tabela["evt_mwh"] - tabela["evt_vertimento_minimo_mwh"]
    tabela.index = tabela.index.to_timestamp()
    tabela.index.name = "mes"
    return tabela.reset_index()


def calcular_distribuicao_mes_do_ano(df: pd.DataFrame, anos: List[int]) -> pd.DataFrame:
    """Participação de cada mês do ano na EVT, somando apenas os anos informados."""
    sub = df[df["ano"].isin(anos)]
    soma = sub.groupby("mes")["val_energiavertidaturbinavel"].sum().reindex(range(1, 13), fill_value=0.0)
    total = float(soma.sum())
    return pd.DataFrame(
        {
            "mes": list(range(1, 13)),
            "mes_nome": MESES_EXTENSO,
            "evt_mwh": soma.to_numpy(),
            "participacao_pct": [_pct(v, total) for v in soma.to_numpy()],
        }
    )


def calcular_evt_por_faixa_geracao(df: pd.DataFrame) -> pd.DataFrame:
    """Distribuição das horas com EVT pelo nível de geração no mesmo horário."""
    com_evt = df[_mascara_evt(df)]
    limiar_plena = FRACAO_PLENA_CARGA * NOMINAL_INSTALLED_CAPACITY_MW
    ger = com_evt["val_geracao"]

    condicoes = [ger <= LIMIAR_GERACAO_PARADA_MW]
    rotulos = [f"até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW (usina parada)"]
    anterior = LIMIAR_GERACAO_PARADA_MW
    for limite in FAIXAS_GERACAO_INTERMEDIARIAS_MW:
        condicoes.append((ger > anterior) & (ger <= limite))
        rotulos.append(f"de {fmt_num(anterior, 0)} a {fmt_num(limite, 0)} MW")
        anterior = limite
    condicoes.append((ger > anterior) & (ger < limiar_plena))
    rotulos.append(f"de {fmt_num(anterior, 0)} a {fmt_num(limiar_plena, 1)} MW")
    condicoes.append(ger >= limiar_plena)
    rotulos.append(f"{fmt_num(limiar_plena, 1)} MW ou mais (plena carga)")

    faixa = np.select(condicoes, rotulos, default="sem classificação")
    tabela = (
        com_evt.assign(faixa=faixa)
        .groupby("faixa")
        .agg(
            horas=("din_instante", "size"),
            evt_mwh=("val_energiavertidaturbinavel", "sum"),
            geracao_media_mw=("val_geracao", "mean"),
            disponibilidade_media_mw=("val_disponibilidade", "mean"),
        )
        .reindex(rotulos)
    )
    tabela[["horas", "evt_mwh"]] = tabela[["horas", "evt_mwh"]].fillna(0)
    tabela["participacao_evt_pct"] = [_pct(v, float(tabela["evt_mwh"].sum())) for v in tabela["evt_mwh"]]
    tabela.index.name = "faixa_geracao"
    return tabela.reset_index()


def calcular_perfil_horario(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """Média por ano (linhas) e hora do dia (colunas)."""
    return df.pivot_table(index="ano", columns="hora", values=coluna, aggfunc="mean")


def calcular_horas_geracao_zero(df: pd.DataFrame) -> pd.DataFrame:
    """Horas com val_geracao igual a zero por ano (linhas) e mês (colunas), com totais.

    Meses sem nenhum registro na série ficam vazios (NaN), não zero.
    """
    zero = df["val_geracao"] == 0
    anos = sorted(df["ano"].unique())
    observadas = df.groupby(["ano", "mes"]).size().unstack().reindex(index=anos, columns=range(1, 13))
    contagem = (
        df[zero].groupby(["ano", "mes"]).size().unstack()
        .reindex(index=anos, columns=range(1, 13)).fillna(0)
    )
    tabela = contagem.where(observadas.notna())
    tabela.columns = MESES_ABREVIADOS
    tabela["total"] = contagem.sum(axis=1)
    tabela["com_disponibilidade_zero"] = (
        (zero & _mascara_indisponibilidade_total(df)).groupby(df["ano"]).sum().reindex(anos, fill_value=0)
    )
    tabela["com_usina_disponivel"] = tabela["total"] - tabela["com_disponibilidade_zero"]
    tabela.index.name = "ano"
    return tabela.reset_index()


def _registros_validos(df: pd.DataFrame) -> pd.DataFrame:
    return df[df[COLUNA_QUALIDADE] == QUALIDADE_OK]


def calcular_perfil_estatistico_anual(df: pd.DataFrame) -> pd.DataFrame:
    """Estatísticas anuais das 10 variáveis, excluindo registros sinalizados com anomalia."""
    logger.info("Calculando perfil estatístico anual das 10 variáveis contínuas...")
    validos = _registros_validos(df)
    linhas: List[Dict[str, Any]] = []

    for ano, df_ano in validos.groupby("ano"):
        for col in OPERATIONAL_METRIC_COLUMNS:
            serie = df_ano[col].dropna()
            if serie.empty:
                continue
            id_min = serie.idxmin()
            id_max = serie.idxmax()
            linhas.append(
                {
                    "ano": int(ano),
                    "variavel": col,
                    "unidade": UNIDADES.get(col, ""),
                    "registros_considerados": len(serie),
                    "media": round(float(serie.mean()), 4),
                    "desvio_padrao": round(float(serie.std(ddof=1)) if len(serie) > 1 else 0.0, 4),
                    "mediana": round(float(serie.median()), 4),
                    "percentil_25": round(float(serie.quantile(0.25)), 4),
                    "percentil_75": round(float(serie.quantile(0.75)), 4),
                    "soma_acumulada": round(float(serie.sum()), 2),
                    "valor_minimo": round(float(serie.loc[id_min]), 4),
                    "data_hora_min": str(df_ano.loc[id_min, "din_instante"]),
                    "valor_maximo": round(float(serie.loc[id_max]), 4),
                    "data_hora_max": str(df_ano.loc[id_max, "din_instante"]),
                }
            )

    return pd.DataFrame(linhas)


def mapear_extremos_historicos(df: pd.DataFrame) -> pd.DataFrame:
    """Máximos e mínimos do período, excluindo registros sinalizados com anomalia."""
    validos = _registros_validos(df)
    linhas: List[Dict[str, Any]] = []
    for col in OPERATIONAL_METRIC_COLUMNS:
        serie = validos[col].dropna()
        if serie.empty:
            continue
        id_max = serie.idxmax()
        id_min = serie.idxmin()
        linhas.append(
            {
                "variavel": col,
                "unidade": UNIDADES.get(col, ""),
                "maximo_historico": round(float(serie.loc[id_max]), 4),
                "data_hora_max": str(validos.loc[id_max, "din_instante"]),
                "minimo_historico": round(float(serie.loc[id_min]), 4),
                "data_hora_min": str(validos.loc[id_min, "din_instante"]),
            }
        )
    return pd.DataFrame(linhas)


def listar_anomalias(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Lista cronológica dos registros sinalizados e resumo por regra."""
    colunas = [
        "din_instante",
        COLUNA_QUALIDADE,
        "val_geracao",
        "val_disponibilidade",
        "val_vazaoturbinada",
        "val_produtividade",
        "val_energiavertida",
        "val_energiavertidaturbinavel",
    ]
    lista = df.loc[df[COLUNA_QUALIDADE] != QUALIDADE_OK, colunas].sort_values("din_instante").reset_index(drop=True)
    resumo = []
    for codigo, coluna in COLUNAS_ANOMALIA.items():
        sel = df[df[coluna].astype(bool)]
        resumo.append(
            {
                "regra": codigo,
                "descricao": DESCRICAO_ANOMALIA[codigo],
                "horas": len(sel),
                "primeira_ocorrencia": sel["din_instante"].min() if len(sel) else pd.NaT,
                "ultima_ocorrencia": sel["din_instante"].max() if len(sel) else pd.NaT,
                "evt_mwh": float(sel["val_energiavertidaturbinavel"].sum()),
            }
        )
    return lista, pd.DataFrame(resumo)


def tabela_parametros(com_indicadores: bool = False, com_programacao: bool = False) -> pd.DataFrame:
    """Parâmetros da usina e da análise, com a respectiva origem."""
    prod_min, prod_max = faixa_produtividade()
    calculado = "Calculado a partir dos parâmetros acima"
    analise = "Parâmetro de análise (src/config.py)"
    rf = FONTE_PARAMETROS_USINA
    linhas = [
        ("Usina", "Potência instalada", fmt_num(NOMINAL_INSTALLED_CAPACITY_MW, 1), "MW", rf),
        ("Usina", "Unidades geradoras", f"{NUMERO_UNIDADES_GERADORAS} × {fmt_num(POTENCIA_UNITARIA_MW, 1)}", "MW", rf),
        ("Usina", "Tipo de turbina", TIPO_TURBINA, "", rf),
        ("Usina", "Engolimento nominal por unidade", fmt_num(ENGOLIMENTO_NOMINAL_UG_M3S, 1), "m³/s", rf),
        ("Usina", "Garantia física", fmt_num(GARANTIA_FISICA_MWMED, 1), "MWmed", FONTE_GARANTIA_FISICA),
        ("Usina", "Indisponibilidade programada de referência (IP)", fmt_num(IP_REFERENCIA * 100, 3), "%", rf),
        ("Usina", "Indisponibilidade forçada de referência (TEIF)", fmt_num(TEIF_REFERENCIA * 100, 3), "%", rf),
        ("Usina", "Queda bruta", fmt_num(QUEDA_BRUTA_M, 2), "m", rf),
        ("Usina", "Perda hidráulica", fmt_num(PERDA_HIDRAULICA_M, 3), "m", rf),
        ("Usina", "Rendimento turbina e gerador", fmt_num(RENDIMENTO_TURBINA_GERADOR * 100, 2), "%", rf),
        ("Usina", "Vazão remanescente", fmt_num(VAZAO_REMANESCENTE_M3S, 2), "m³/s", rf),
        ("Usina", "Início da operação comercial", str(ANO_INICIO_OPERACAO_COMERCIAL), "", f"Despachos ANEEL nº 377/2013 e nº 2.692/2013, citados no {FONTE_PARAMETROS_USINA.split(',')[0]}"),
        ("Derivado", "Engolimento máximo da usina", fmt_num(ENGOLIMENTO_MAXIMO_USINA_M3S, 1), "m³/s", f"{calculado}: unidades × engolimento nominal"),
        ("Derivado", "Disponibilidade de referência da GF", fmt_num(DISPONIBILIDADE_REFERENCIA * 100, 2), "%", f"{calculado}: (1 − IP) × (1 − TEIF)"),
        ("Derivado", "Produtividade nominal teórica", fmt_num(PRODUTIVIDADE_NOMINAL_MW_M3S, 4), "MW/(m³/s)", f"{calculado}: 9,81 × (queda bruta − perda) × rendimento ÷ 1.000"),
        ("Análise", "Usina parada", f"geração ≤ {fmt_num(LIMIAR_GERACAO_PARADA_MW, 1)}", "MW", analise),
        ("Análise", "Plena carga", f"geração ≥ {fmt_num(FRACAO_PLENA_CARGA * NOMINAL_INSTALLED_CAPACITY_MW, 1)}", "MW", f"{analise}: {fmt_pct(FRACAO_PLENA_CARGA * 100, 0)} da potência instalada"),
        ("Análise", "Vertimento mínimo (patamar contínuo)", f"vazão vertida ≤ {fmt_num(LIMIAR_VERTIMENTO_MINIMO_M3S, 1)}", "m³/s", f"{analise}: patamar de 5 a 6 m³/s observado na série"),
        ("Análise", "Indisponibilidade total", f"disponibilidade ≤ {fmt_num(LIMIAR_INDISPONIBILIDADE_TOTAL_MW, 3)}", "MW", analise),
        ("Análise", "Janela diurna / noturna", f"{_rotulo_janela(HORAS_DIURNAS)} / {_rotulo_janela(HORAS_NOTURNAS)}", "", analise),
        ("Validação", "Tolerância sobre limites nominais (R6)", fmt_num(TOLERANCIA_LIMITES_FISICOS * 100, 0), "%", analise),
        ("Validação", "Faixa de produtividade (R8)", f"{fmt_num(prod_min, 3)} a {fmt_num(prod_max, 3)}", "MW/(m³/s)", f"{analise}: {fmt_pct(FAIXA_PRODUTIVIDADE_RELATIVA[0] * 100, 0)} a {fmt_pct(FAIXA_PRODUTIVIDADE_RELATIVA[1] * 100, 0)} da nominal"),
        ("Validação", "Tolerância de geração acima da disponibilidade (R7)", fmt_num(TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW, 1), "MW", analise),
        ("Fonte", "Conjunto de dados", "Energia Vertida Turbinável (ONS)", "", ONS_DATASET_URL),
    ]
    if com_indicadores:
        linhas.append(("Fonte", "Identificação nos indicadores do ONS", f"CEG {CEG_USINA} · id ONS {ID_ONS_USINA}", "",
                       "Conjuntos de indicadores por unidade geradora do ONS"))
        linhas += [
            ("Fonte", "Conjunto de dados", descricao, "", f"{ONS_PORTAL_DATASET_URL}{conjunto}")
            for conjunto, descricao in CONJUNTOS_INDICADORES_ONS.items()
        ]
        linhas.append(("Validação", "Tolerância entre indicador DISPF e horas do TEIP",
                       fmt_num(TOLERANCIA_DIVERGENCIA_HORAS, 1), "h", analise))
    if com_programacao:
        linhas += [
            ("Fonte", "Conjunto de dados", f"Dados dos Valores da Programação Diária (ONS), usina {COD_EXIBICAO_USINA_PROGRAMACAO}",
             "", f"{ONS_PORTAL_DATASET_URL}{CONJUNTO_PROGRAMACAO_DIARIA}"),
            ("Análise", "Programação zero", f"programação ≤ {fmt_num(LIMIAR_GERACAO_PARADA_MW, 1)}", "MW",
             f"{analise}: mesmo limiar de usina parada"),
            ("Análise", "Desvio da programação", f"usina parada com programação > {fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 1)}",
             "MW", analise),
        ]
    return pd.DataFrame(linhas, columns=["grupo", "parametro", "valor", "unidade", "origem"])


# ---------------------------------------------------------------------------
# Indicadores oficiais do ONS por unidade geradora
# ---------------------------------------------------------------------------

# Descrição curta das parcelas de horas usadas nas taxas (texto das constatações e tabelas)
DESCRICAO_PARCELA: Dict[str, str] = {
    "HDF": "desligamentos forçados",
    "HEDF": "operação com limitação forçada de potência",
    "HDP": "desligamentos programados",
    "HEDP": "operação com limitação programada de potência",
}
JANELA_TAXAS_MESES: int = 60


def _media_ponderada(g: pd.DataFrame, coluna: str) -> float:
    peso = g["peso"]
    return float((g[coluna] * peso).sum() / peso.sum()) if peso.sum() else math.nan


def analisar_indicadores_ons(
    ind: IndicadoresONS,
    df: pd.DataFrame,
    indicadores_anuais: pd.DataFrame,
    cobertura: Dict[str, Any],
) -> Dict[str, Any]:
    """Resumo dos indicadores oficiais do ONS no período da base de EVT.

    A disponibilidade da usina pelo DISPF é a média das unidades ponderada pela potência e
    pelas horas da base de EVT em cada mês.
    """
    referencia = DISPONIBILIDADE_REFERENCIA * 100.0
    parciais = set(cobertura["anos_parciais"])
    resultado: Dict[str, Any] = {}

    # Disponibilidade da usina pelo DISPF, por ano e no período
    mensal = ind.ug_mensal.copy()
    if len(mensal):
        horas_base = df.groupby(df["din_instante"].dt.to_period("M").dt.to_timestamp()).size().rename("horas_base")
        mensal = mensal.merge(horas_base, left_on="mes", right_index=True, how="inner")
        mensal["peso"] = mensal["horas_base"] * mensal["potencia_mw"].fillna(POTENCIA_UNITARIA_MW)
        mensal["ano"] = mensal["mes"].dt.year
        declarada = indicadores_anuais.set_index("ano")["disponibilidade_relativa_pct"]
        linhas = []
        for ano, g in mensal.groupby("ano"):
            dispf = _media_ponderada(g, "dispf")
            linhas.append({
                "ano": int(ano),
                "ano_parcial": int(ano) in parciais,
                "disponibilidade_declarada_pct": float(declarada.get(ano, math.nan)),
                "dispf_pct": dispf,
                "indisppf_pct": _media_ponderada(g, "indisppf"),
                "indispff_pct": _media_ponderada(g, "indispff"),
                "desvio_dispf_referencia_pp": dispf - referencia,
            })
        resultado["disp_anual"] = pd.DataFrame(linhas)
        resultado["disp_periodo"] = {
            "mes_inicio": mensal["mes"].min(),
            "mes_fim": mensal["mes"].max(),
            "unidades": int(mensal["ug"].nunique()),
            "dispf_pct": _media_ponderada(mensal, "dispf"),
            "indisppf_pct": _media_ponderada(mensal, "indisppf"),
            "indispff_pct": _media_ponderada(mensal, "indispff"),
        }

    # Indicadores anuais oficiais por unidade (base anual do ONS)
    anual = ind.ug_anual.copy()
    if len(anual):
        anual["ano_parcial"] = anual["ano"].astype(int).isin(parciais)
        resultado["ug_anual"] = anual

    # Horas por estado operativo
    horas = ind.horas_estado.copy()
    if len(horas):
        horas["ano"] = horas["mes"].dt.year
        resultado["horas_mensal"] = horas
        soma = horas.groupby(["ano", "ug"])[list(INSUMOS_HORAS)].sum()
        soma["meses"] = horas.groupby(["ano", "ug"])["mes"].nunique()
        soma = soma.reset_index()
        soma["ano_parcial"] = soma["meses"] < 12
        resultado["horas_anual"] = soma
        resultado["horas_periodo"] = {
            "mes_inicio": horas["mes"].min(),
            "mes_fim": horas["mes"].max(),
            "identidade_fora": int((horas["residuo_identidade_h"].abs() > TOLERANCIA_IDENTIDADE_HORAS).sum()),
            "meses_unidade": len(horas),
        }

    # TEIFa e TEIP: valor mais recente, recálculo a partir das horas e decomposição
    taxas = ind.taxas.copy()
    if len(taxas):
        ultima = taxas.loc[taxas["mes"].idxmax()]
        teifa, teip = float(ultima["teifa"]), float(ultima["teip"])
        resultado["taxas"] = taxas
        resultado["taxa_ultima"] = {
            "mes": ultima["mes"],
            "teifa_pct": teifa * 100.0,
            "teip_pct": teip * 100.0,
            "disponibilidade_verificada_pct": (1.0 - teifa) * (1.0 - teip) * 100.0,
        }
        if len(horas):
            recalculo = recalcular_taxas(horas, taxas, JANELA_TAXAS_MESES)
            resultado["recalculo_taxas"] = recalculo
            completos = recalculo.dropna(subset=["teifa_recalculada"])
            resultado["recalculo_resumo"] = {
                "meses": len(completos),
                "diferenca_maxima_pp": float(
                    completos[["diferenca_teifa_pp", "diferenca_teip_pp"]].abs().max().max()
                ) if len(completos) else math.nan,
            }
            if ultima["mes"] in set(completos["mes"]):
                resultado["decomposicao"] = decompor_taxas(horas, ultima["mes"], JANELA_TAXAS_MESES)

    if len(ind.divergencias):
        resultado["divergencias"] = ind.divergencias.copy()
    else:
        resultado["divergencias"] = pd.DataFrame()
    return resultado


# ---------------------------------------------------------------------------
# Programação diária do ONS (spec 004)
# ---------------------------------------------------------------------------


def analisar_programacao(prog: ProgramacaoONS, df: pd.DataFrame) -> Dict[str, Any]:
    """Cruza a programação diária do ONS com a operação verificada nas horas comuns."""
    classificadas = classificar_horas(df, prog.horaria)
    mensal = resumo_mensal(classificadas)
    eventos = eventos_desvio(classificadas)
    perfil = perfil_hora_do_dia(classificadas)
    inicio, fim = prog.horaria["din_instante"].min(), prog.horaria["din_instante"].max()
    base_no_periodo = int(((df["din_instante"] >= inicio) & (df["din_instante"] <= fim)).sum())

    zero = classificadas["classe"] == PARADA_EVT_PROGRAMACAO_ZERO
    parada_evt = classificadas["classe"].isin([PARADA_EVT_PROGRAMACAO_ZERO, PARADA_EVT_PROGRAMACAO_POSITIVA])
    evt = float(classificadas["val_energiavertidaturbinavel"].sum())
    evt_zero = float(classificadas.loc[zero, "val_energiavertidaturbinavel"].sum())
    horas_zero = int(zero.sum())
    diurnas = int(perfil.loc[perfil["hora"].isin(HORAS_DIURNAS), "horas"].sum())
    maior = eventos.loc[eventos["duracao_h"].idxmax()] if len(eventos) else None
    dias_ausentes = prog.dias_ausentes.copy()
    periodo = {
        "primeiro_dia": inicio.normalize(),
        "ultimo_dia": fim.normalize(),
        "dias_com_arquivo": int(prog.horaria["din_instante"].dt.normalize().nunique()),
        "dias_ausentes": len(dias_ausentes),
        "lista_dias_ausentes": [pd.Timestamp(d) for d in dias_ausentes["dia"]] if len(dias_ausentes) else [],
        "horas_comuns": len(classificadas),
        "horas_base_sem_programacao": base_no_periodo - len(classificadas),
        "horas_parada_com_evt": int(parada_evt.sum()),
        "horas_parada_evt_programacao_zero": horas_zero,
        "pct_horas_programacao_zero": _pct(horas_zero, int(parada_evt.sum())),
        "disponibilidade_media_programacao_zero_mw": _media(classificadas.loc[zero, "val_disponibilidade"]),
        "evt_horas_comuns_mwh": evt,
        "evt_programacao_zero_mwh": evt_zero,
        "pct_evt_programacao_zero": _pct(evt_zero, evt),
        "pct_horas_zero_janela_diurna": _pct(diurnas, horas_zero),
        "horas_desvio": int(classificadas["desvio_programacao"].sum()),
        "eventos_desvio": len(eventos),
        "maior_evento": maior,
        "horas_gerando_programacao_zero": int((classificadas["classe"] == "GERANDO_PROGRAMACAO_ZERO").sum()),
        "correlacao_geracao_programacao": float(classificadas["val_geracao"].corr(classificadas["geracao_programada_mw"])),
        "desvio_medio_absoluto_mw": float((classificadas["val_geracao"] - classificadas["geracao_programada_mw"]).abs().mean()),
    }
    return {
        "periodo": periodo,
        "mensal": mensal,
        "eventos": eventos,
        "perfil": perfil,
        "dias_ausentes": dias_ausentes,
        "auditoria": prog.auditoria,
        "classificadas": classificadas,
    }


# ---------------------------------------------------------------------------
# Bases complementares do ONS (spec 006)
# ---------------------------------------------------------------------------

ORIGEM_ANALISE = "Parâmetro de análise (src/config.py)"


def _data_obtencao_texto(obtido_em: str) -> str:
    return f"obtido em {fmt_data(obtido_em)}" if obtido_em else "data de obtenção não registrada"


def analisar_disponibilidade(
    serie: SerieConjunto,
    df: pd.DataFrame,
    indicadores: Optional[IndicadoresONS],
    programacao: Dict[str, Any],
    cobertura: Dict[str, Any],
) -> Dict[str, Any]:
    """Disponibilidade horária do ONS (operacional e sincronizada) cruzada com a base de EVT (US3)."""
    disp = serie.horaria
    conferencia, divergencias = conferir_com_evt(disp, df)
    paradas = classificar_horas_paradas(disp, df, programacao.get("classificadas") if programacao else None)
    classes = (paradas.groupby(["sincronizacao", "evt", "classe_programacao"])
               .agg(horas=("din_instante", "size"), evt_mwh=("val_energiavertidaturbinavel", "sum"))
               .reset_index())
    horas_estado = indicadores.horas_estado if indicadores is not None else None
    mensal = resumir_disponibilidade(disp, df, horas_estado, "M")
    anual = resumir_disponibilidade(disp, df, horas_estado, "Y")
    anual["ano_parcial"] = anual["periodo"].isin({str(a) for a in cobertura.get("anos_parciais", [])})

    sem_sinc = paradas["sincronizacao"] == NAO_SINCRONIZADA
    com_evt = paradas["evt"] == COM_EVT
    prog_zero = paradas["classe_programacao"] == PARADA_EVT_PROGRAMACAO_ZERO
    aus = serie.ausencias
    meses = aus[aus["tipo"] != "HORAS"] if len(aus) else aus
    resumo = {
        "inicio": disp["din_instante"].min(),
        "fim": disp["din_instante"].max(),
        "horas": len(disp),
        "horas_sinalizadas": int(disp["qualidade"].ne("OK").sum()) if "qualidade" in disp.columns else 0,
        "meses_sem_usina": [pd.Timestamp(x) for x in meses["inicio"]] if len(meses) else [],
        "horas_ausentes": int(aus.loc[aus["tipo"] == "HORAS", "horas"].sum()) if len(aus) else 0,
        "horas_paradas": len(paradas),
        "horas_paradas_sem_sincronizacao": int(sem_sinc.sum()),
        "horas_paradas_sincronizadas": int((~sem_sinc).sum()),
        "pct_paradas_sem_sincronizacao": _pct(int(sem_sinc.sum()), len(paradas)),
        "horas_parada_evt": int(com_evt.sum()),
        "horas_parada_evt_sem_sincronizacao": int((com_evt & sem_sinc).sum()),
        "horas_parada_evt_programacao_zero": int((com_evt & prog_zero).sum()),
        "horas_parada_evt_programacao_zero_sem_sincronizacao": int((com_evt & prog_zero & sem_sinc).sum()),
    }
    return {
        "resumo": resumo,
        "conferencia": conferencia,
        "divergencias": divergencias,
        "horas_paradas": paradas,
        "classes": classes,
        "mensal": mensal,
        "anual": anual,
        "auditoria": serie.auditoria,
        "ausencias": aus,
        "obtido_em": data_obtencao(DISPONIBILIDADE_RAW_DIR),
    }


def _resumo_serie(serie: SerieConjunto) -> Dict[str, Any]:
    """Cobertura de uma série das bases complementares: período, horas, sinalizadas, meses e horas ausentes."""
    h, aus = serie.horaria, serie.ausencias
    meses = aus[aus["tipo"] != "HORAS"] if len(aus) else aus
    return {
        "inicio": h["din_instante"].min(),
        "fim": h["din_instante"].max(),
        "horas": len(h),
        "horas_sinalizadas": int(h["qualidade"].ne("OK").sum()) if "qualidade" in h.columns else 0,
        "meses_sem_usina": [pd.Timestamp(x) for x in meses["inicio"]] if len(meses) else [],
        "horas_ausentes": int(aus.loc[aus["tipo"] == "HORAS", "horas"].sum()) if len(aus) else 0,
    }


def analisar_hidrologia(
    serie: SerieConjunto,
    alinhamento: pd.DataFrame,
    df: pd.DataFrame,
    cobertura: Dict[str, Any],
) -> Dict[str, Any]:
    """Afluência, vertimento e nível do reservatório cruzados com a base de EVT (US4).

    Sem o alinhamento confirmado (FR-022), só a cobertura e o alinhamento são devolvidos.
    """
    resumo = _resumo_serie(serie)
    qualidade_h = serie.horaria["qualidade"] if "qualidade" in serie.horaria.columns else pd.Series(dtype=object)
    resumo["sinalizadas_por_regra"] = {
        regra: {"horas": int(qualidade_h.str.contains(regra).sum()),
                "anos": serie.horaria.loc[qualidade_h.str.contains(regra), "din_instante"].dt.year.value_counts().sort_index().to_dict()}
        for regra in ("H1", "H2", "H3", "H4")
    }
    resultado: Dict[str, Any] = {
        "resumo": resumo,
        "alinhamento": alinhamento,
        "auditoria": serie.auditoria,
        "ausencias": serie.ausencias,
        "obtido_em": data_obtencao(HIDROLOGIA_RAW_DIR),
        "publicado": bool(alinhamento.iloc[0]["confirmado"]),
    }
    if not resultado["publicado"]:
        return resultado
    hid = serie.horaria
    parciais = {str(a) for a in cobertura.get("anos_parciais", [])}
    faixas = classificar_faixas(hid, df)
    faixas_anual = resumir_faixas(faixas, "Y")
    faixas_anual["ano_parcial"] = faixas_anual["periodo"].isin(parciais)
    anual = resumir_hidrologia(hid, "Y")
    anual["ano_parcial"] = anual["periodo"].isin(parciais)
    perfil = perfil_hidrologico(hid, df)
    por_faixa = faixas.groupby("faixa_afluencia").agg(horas=("din_instante", "size"),
                                                       evt_mwh=("val_energiavertidaturbinavel", "sum"))
    por_faixa = por_faixa.reindex(FAIXAS_AFLUENCIA, fill_value=0)
    amplitude = (perfil.groupby("grupo_dias")["nivel_montante_medio_m"].agg(["min", "max"])
                 .assign(amplitude=lambda t: t["max"] - t["min"]))
    resultado["resumo"].update({
        "horas_evt": len(faixas),
        "evt_mwh": float(faixas["val_energiavertidaturbinavel"].sum()),
        "horas_por_faixa": por_faixa["horas"].astype(int).to_dict(),
        "evt_por_faixa_mwh": por_faixa["evt_mwh"].astype(float).to_dict(),
        "horas_afluencia_acima_engolimento": int((hid["val_vazaoafluente"] > ENGOLIMENTO_MAXIMO_USINA_M3S).sum()),
        "dias_com_parada_evt": int(perfil.loc[perfil["grupo_dias"] == COM_PARADA_EVT, "dias"].max())
        if (perfil["grupo_dias"] == COM_PARADA_EVT).any() else 0,
        "nivel_amplitude_m": amplitude["amplitude"].to_dict(),
        "nivel_min_m": amplitude["min"].to_dict(),
        "nivel_max_m": amplitude["max"].to_dict(),
    })
    pico = hid.loc[hid["val_vazaoafluente"].idxmax()] if hid["val_vazaoafluente"].notna().any() else None
    resultado["resumo"]["pico_afluencia"] = None if pico is None else {
        "instante": pico["din_instante"], "afluencia_m3s": float(pico["val_vazaoafluente"]),
        "defluencia_m3s": float(pico["val_vazaodefluente"]) if pd.notna(pico.get("val_vazaodefluente")) else float("nan"),
    }
    resultado.update({
        "faixas": faixas,
        "faixas_anual": faixas_anual,
        "faixas_mensal": resumir_faixas(faixas, "M"),
        "perfil": perfil,
        "mensal": resumir_hidrologia(hid, "M", "mes"),
        "anual": anual,
    })
    return resultado


def analisar_geracao_oficial(serie: SerieConjunto, df: pd.DataFrame, cobertura: Dict[str, Any]) -> Dict[str, Any]:
    """Geração da base de EVT conferida com a série oficial de geração por usina (US5)."""
    conferencia, mensal, divergencias = conferir_geracao(serie.horaria, df)
    anual = mensal.assign(ano=mensal["mes"].str[:4]).groupby("ano").agg(
        energia_base_evt_mwh=("energia_base_evt_mwh", "sum"),
        energia_ons_geracao_mwh=("energia_ons_geracao_mwh", "sum"),
        diferenca_mwh=("diferenca_mwh", "sum"),
        horas_so_base_evt=("horas_so_base_evt", "sum"),
        horas_so_ons_geracao=("horas_so_ons_geracao", "sum"),
    ).reset_index()
    anual["ano_parcial"] = anual["ano"].isin({str(a) for a in cobertura.get("anos_parciais", [])})
    return {
        "resumo": _resumo_serie(serie),
        "conferencia": conferencia,
        "mensal": mensal,
        "anual": anual,
        "divergencias": divergencias,
        "auditoria": serie.auditoria,
        "ausencias": serie.ausencias,
        "obtido_em": data_obtencao(GERACAO_RAW_DIR),
    }


def analisar_cadastro(ficha: pd.DataFrame, auditoria: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Ficha cadastral da usina no ONS (US6), com a auditoria da leitura do cadastro (FR-005), se houver."""
    linha = ficha.iloc[0].to_dict()
    divergencias = str(linha.get("divergencias") or "").strip()
    return {"ficha": linha, "divergencias": divergencias, "obtido_em": str(linha.get("data_consulta_utc") or ""),
            "auditoria": auditoria if auditoria is not None else pd.DataFrame()}


def _divergencia_geracao(res: "ResultadosAnalise") -> bool:
    c = res.geracao_oficial.get("conferencia", {})
    return bool(c) and (c["divergentes"] > 0 or c["so_ons_geracao"] > 0 or c["so_base_evt"] > 0)


def parametros_geracao_cadastro(res: "ResultadosAnalise") -> pd.DataFrame:
    """Fontes da geração por usina e do cadastro (linhas da tabela de parâmetros)."""
    linhas = []
    g = res.geracao_oficial
    if g:
        r = g["resumo"]
        linhas.append(("Fonte", "Conjunto de dados",
                       f"Geração por usina (ONS), id ONS {ID_ONS_USINA} · CEG {CEG_USINA}; {fmt_data(r['inicio'])} a "
                       f"{fmt_data(r['fim'])}; {_data_obtencao_texto(g['obtido_em'])}", "",
                       f"{ONS_PORTAL_DATASET_URL}{CONJUNTO_GERACAO}"))
    c = res.cadastro
    if c:
        linhas.append(("Fonte", "Conjunto de dados",
                       f"Modalidade das usinas (ONS), CEG {CEG_USINA}; cadastro sem série histórica; "
                       f"{_data_obtencao_texto(c['obtido_em'])}", "", f"{ONS_PORTAL_DATASET_URL}{CONJUNTO_CADASTRO}"))
    return pd.DataFrame(linhas, columns=["grupo", "parametro", "valor", "unidade", "origem"])


def parametros_hidrologia(res: "ResultadosAnalise") -> pd.DataFrame:
    """Fonte, faixas, tolerância e meta do alinhamento da hidrologia (linhas da tabela de parâmetros)."""
    r = res.hidrologia["resumo"]
    linhas = [
        ("Fonte", "Conjunto de dados",
         f"Dados hidrológicos horários (ONS), cod_usina {COD_USINA_ONS} · reservatório {ID_RESERVATORIO_ONS}; "
         f"{fmt_data(r['inicio'])} a {fmt_data(r['fim'])}; {_data_obtencao_texto(res.hidrologia['obtido_em'])}",
         "", f"{ONS_PORTAL_DATASET_URL}{CONJUNTO_HIDROLOGIA}"),
        ("Análise", "Faixas de afluência nas horas com EVT",
         f"até {fmt_num(ENGOLIMENTO_NOMINAL_UG_M3S, 1)} / até {fmt_num(ENGOLIMENTO_MAXIMO_USINA_M3S, 1)} / acima", "m³/s",
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
         f"Disponibilidade por usina (ONS), id ONS {ID_ONS_USINA} · CEG {CEG_USINA}; {fmt_data(r['inicio'])} a "
         f"{fmt_data(r['fim'])}; {_data_obtencao_texto(res.disponibilidade['obtido_em'])}",
         "", f"{ONS_PORTAL_DATASET_URL}{CONJUNTO_DISPONIBILIDADE}"),
        ("Análise", "Unidade sincronizada", f"disponibilidade sincronizada > {fmt_num(LIMIAR_SINCRONIZADA_MW, 1)}", "MW",
         ORIGEM_ANALISE),
        ("Validação", "Coincidência entre fontes", f"diferença ≤ {fmt_num(TOLERANCIA_COINCIDENCIA_MW, 2)}", "MW",
         ORIGEM_ANALISE),
    ]
    return pd.DataFrame(linhas, columns=["grupo", "parametro", "valor", "unidade", "origem"])


# ---------------------------------------------------------------------------
# Constatações (texto gerado a partir dos resultados)
# ---------------------------------------------------------------------------


def _achado_cobertura(res: ResultadosAnalise) -> Tuple[str, str]:
    c = res.cobertura
    faltantes = c["horas_faltantes"]
    if faltantes:
        lista = fmt_lista(fmt_data_hora(t) for t in faltantes[:5]) + ("…" if len(faltantes) > 5 else "")
        txt_faltantes = f", com {fmt_int(len(faltantes))} {plural(len(faltantes), 'hora ausente', 'horas ausentes')} ({lista})"
    else:
        txt_faltantes = ", sem horas ausentes"
    partes = [
        f"A série do ONS para a usina (cod_usina {COD_USINA_ONS}) vai de {fmt_data_hora(c['inicio'])} "
        f"a {fmt_data_hora(c['fim'])}: {fmt_int(c['horas_observadas'])} registros horários{txt_faltantes}."
    ]
    arquivos = c.get("arquivos") or {}
    if arquivos.get("sem_registros"):
        n = len(arquivos["sem_registros"])
        partes.append(
            f"{plural(n, 'O arquivo', 'Os arquivos')} de {fmt_lista(arquivos['sem_registros'])} "
            f"não {plural(n, 'contém', 'contêm')} registros da usina."
        )
    if c["inicio"].year > ANO_INICIO_OPERACAO_COMERCIAL:
        partes.append(
            f"Como a operação comercial começou em {ANO_INICIO_OPERACAO_COMERCIAL}, o período anterior a "
            f"{fmt_data(c['inicio'])} não é coberto por esta fonte."
        )
    parciais = c["por_ano"][c["por_ano"]["ano_parcial"]]
    if len(parciais):
        itens = [f"{int(r.ano)} ({fmt_pct(r.cobertura_pct)} das horas do ano)" for r in parciais.itertuples()]
        partes.append(
            f"{plural(len(itens), 'O ano', 'Os anos')} {fmt_lista(itens)} "
            f"{plural(len(itens), 'é parcial', 'são parciais')}; as comparações entre anos usam apenas anos completos."
        )
    return "Cobertura dos dados", " ".join(partes)


def _achado_disponibilidade(res: ResultadosAnalise) -> Tuple[str, str]:
    g = res.globais
    anuais = res.indicadores_anuais
    desvio = g["desvio_disponibilidade_referencia_pp"]
    texto = (
        f"A disponibilidade média declarada foi de {fmt_num(g['disponibilidade_media_mwmed'], 1)} MW "
        f"({fmt_pct(g['disponibilidade_relativa_pct'])} da potência instalada), {fmt_num(abs(desvio), 1)} p.p. "
        f"{'abaixo' if desvio < 0 else 'acima'} da disponibilidade de referência da garantia física "
        f"({fmt_pct(g['disponibilidade_referencia_pct'])})."
    )
    completos = anuais[~anuais["ano_parcial"]]
    if len(completos):
        abaixo = completos[completos["desvio_disponibilidade_referencia_pp"] < 0]
        if len(abaixo):
            itens = [f"{int(r.ano)} ({fmt_pct(r.disponibilidade_relativa_pct)})" for r in abaixo.itertuples()]
            texto += f" Entre os anos completos, ficaram abaixo da referência: {fmt_lista(itens)}."
        else:
            texto += " Nenhum ano completo ficou abaixo da referência."
    return "Disponibilidade", texto


def _acima_abaixo(valor: float, referencia: float) -> str:
    return "abaixo" if valor < referencia else "acima"


def _achado_indicadores_ons(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    o = res.ons
    p = o.get("disp_periodo")
    if not p:
        return None
    g = res.globais
    referencia = DISPONIBILIDADE_REFERENCIA * 100.0
    desvio = p["dispf_pct"] - referencia
    texto = (
        f"Pelo indicador de disponibilidade das unidades geradoras apurado pelo ONS (DISPF, Submódulo 9.2 dos "
        f"Procedimentos de Rede), a disponibilidade média das {p['unidades']} unidades de {fmt_mes_ano(p['mes_inicio'])} "
        f"a {fmt_mes_ano(p['mes_fim'])} foi de {fmt_pct(p['dispf_pct'])} (indisponibilidade programada de "
        f"{fmt_pct(p['indisppf_pct'])} e forçada de {fmt_pct(p['indispff_pct'])}), {fmt_num(abs(desvio), 1)} p.p. "
        f"{_acima_abaixo(p['dispf_pct'], referencia)} da disponibilidade de referência da garantia física "
        f"({fmt_pct(referencia)}); a disponibilidade declarada no conjunto de EVT foi de "
        f"{fmt_pct(g['disponibilidade_relativa_pct'])}. As duas medidas são diferentes: o DISPF conta o tempo em que cada "
        f"unidade esteve disponível, sem descontar a operação com potência limitada; a disponibilidade declarada é a "
        f"potência que a usina informou poder gerar a cada hora."
    )
    anual = o.get("disp_anual", pd.DataFrame())
    completos = anual[~anual["ano_parcial"]] if len(anual) else anual
    if len(completos):
        abaixo = completos[completos["desvio_dispf_referencia_pp"] < 0]
        if len(abaixo):
            itens = [f"{int(r.ano)} ({fmt_pct(r.dispf_pct)})" for r in abaixo.itertuples()]
            texto += f" Pelo DISPF, ficaram abaixo da referência os anos completos {fmt_lista(itens)}."
        else:
            texto += " Pelo DISPF, nenhum ano completo ficou abaixo da referência."
    t = o.get("taxa_ultima")
    if t:
        texto += (
            f" A TEIFa apurada pelo ONS para {fmt_mes_ano(t['mes'])} (janela de {JANELA_TAXAS_MESES} meses) é de "
            f"{fmt_pct(t['teifa_pct'], 2)}, {_acima_abaixo(t['teifa_pct'], TEIF_REFERENCIA * 100)} da TEIF de referência "
            f"({fmt_pct(TEIF_REFERENCIA * 100, 3)}), e a TEIP, de {fmt_pct(t['teip_pct'], 2)}, "
            f"{_acima_abaixo(t['teip_pct'], IP_REFERENCIA * 100)} do IP de referência ({fmt_pct(IP_REFERENCIA * 100, 3)}). "
            f"Com as taxas apuradas, (1 − TEIFa) × (1 − TEIP) = {fmt_pct(t['disponibilidade_verificada_pct'], 2)}, "
            f"contra {fmt_pct(referencia, 2)} de referência."
        )
    return "Indicadores oficiais de disponibilidade (ONS)", texto


def _horas_por_ano_texto(horas_anual: pd.DataFrame, ug: int, coluna: str) -> str:
    sel = horas_anual[horas_anual["ug"] == ug]
    return "; ".join(
        f"{int(r.ano)}{' (parcial)' if r.ano_parcial else ''}: {fmt_int(getattr(r, coluna))} h" for r in sel.itertuples()
    )


def _achado_estados_operativos(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    o = res.ons
    hp = o.get("horas_periodo")
    if not hp:
        return None
    horas = o["horas_mensal"]
    horas_anual = o["horas_anual"]
    partes = [
        f"O ONS publica as horas mensais de cada unidade por estado operativo ({fmt_mes_ano(hp['mes_inicio'])} a "
        f"{fmt_mes_ano(hp['mes_fim'])} no período da base)."
    ]
    if hp["identidade_fora"]:
        partes.append(
            f"Em {fmt_int(hp['identidade_fora'])} de {fmt_int(hp['meses_unidade'])} meses-unidade as parcelas não somam as "
            "horas do período."
        )
    rr = o.get("recalculo_resumo")
    if rr and rr["meses"]:
        dif = rr["diferenca_maxima_pp"]
        txt_dif = "inferior a 0,0001 p.p." if dif < 1e-4 else f"de {fmt_num(dif, 4)} p.p."
        partes.append(
            f"Com a fórmula das notas metodológicas, essas horas reproduzem a TEIFa e a TEIP publicadas nos "
            f"{fmt_int(rr['meses'])} meses com janela de {JANELA_TAXAS_MESES} meses completa (diferença máxima {txt_dif})."
        )
    dec = o.get("decomposicao")
    t = o.get("taxa_ultima")
    if dec is not None and len(dec) and t:
        teifa = dec[dec["taxa"] == "TEIFa"]
        maior = teifa.loc[teifa["contribuicao_pp"].idxmax()]
        partes.append(
            f"Da TEIFa de {fmt_pct(t['teifa_pct'], 2)} em {fmt_mes_ano(t['mes'])}, {fmt_num(maior['contribuicao_pp'], 2)} p.p. "
            f"({fmt_pct(maior['participacao_pct'], 0)}) vêm de {DESCRICAO_PARCELA[maior['parcela']]} da UG{int(maior['ug'])}; "
            f"sem essa parcela, a TEIFa seria de {fmt_pct(t['teifa_pct'] - maior['contribuicao_pp'], 2)}."
        )
    # Unidade com mais horas equivalentes de limitação forçada
    por_ug = horas.groupby("ug").agg(hedf=("HEDF", "sum"), meses=("mes", "nunique"),
                                     meses_hedf=("HEDF", lambda s: int((s > 0).sum())))
    if por_ug["hedf"].max() > 0:
        ug = int(por_ug["hedf"].idxmax())
        r = por_ug.loc[ug]
        outras = por_ug.drop(index=ug)
        partes.append(
            f"A UG{ug} registrou limitação forçada de potência em {fmt_int(r['meses_hedf'])} dos {fmt_int(r['meses'])} meses, "
            f"somando {fmt_int(r['hedf'])} horas equivalentes"
            + (f" (UG{', UG'.join(str(int(u)) for u in outras.index)}: {fmt_lista(fmt_int(v) + ' h' for v in outras['hedf'])})"
               if len(outras) else "")
            + "."
        )
    ugs = sorted(int(u) for u in horas_anual["ug"].unique())
    partes.append(
        "Horas em reserva desligada (unidade disponível, parada), por ano: "
        + " | ".join(f"UG{u} — {_horas_por_ano_texto(horas_anual, u, 'HRD')}" for u in ugs)
        + "."
    )
    externa = horas.groupby("ug")["HDCE"].sum()
    if externa.sum() > 0:
        partes.append(
            "Desligamentos por causa externa: "
            + fmt_lista(f"UG{int(u)}: {fmt_num(v, 1)} h" for u, v in externa.items())
            + "."
        )
    div = o.get("divergencias", pd.DataFrame())
    if len(div):
        itens = [
            f"{fmt_mes_ano(r.mes)} UG{int(r.ug)}: {fmt_int(r.horas_programadas_indisppf)} h programadas pelo DISPF e "
            f"{fmt_int(r.HDP)} h pelo TEIP"
            for r in div.itertuples()
        ]
        contida = bool(((div["horas_programadas_indisppf"] - div["HDP"]) <= div["HRD"] + TOLERANCIA_DIVERGENCIA_HORAS).all())
        partes.append(
            f"Em {fmt_int(len(div))} {plural(len(div), 'mês-unidade', 'meses-unidade')}, os dois conjuntos do ONS classificam "
            f"o tempo parado de forma diferente ({'; '.join(itens)})"
            + ("; a diferença está contida nas horas que o conjunto do TEIP registra como reserva desligada." if contida else ".")
        )
    partes.append("Os conjuntos informam a duração de cada estado, não a causa nem os eventos individuais de desligamento.")
    return "Estados operativos das unidades geradoras (ONS)", " ".join(partes)


def _achado_indisponibilidade(res: ResultadosAnalise) -> Tuple[str, str]:
    eventos = res.eventos_indisponibilidade_total
    longos = eventos[eventos["duracao_h"] >= DURACAO_MINIMA_EVENTO_RELATORIO_H] if len(eventos) else eventos
    if len(longos):
        maior = longos.loc[longos["duracao_h"].idxmax()]
        n = len(longos)
        texto = (
            f"Houve {n} {plural(n, 'período', 'períodos')} de indisponibilidade total (disponibilidade zero) "
            f"com pelo menos {DURACAO_MINIMA_EVENTO_RELATORIO_H} h, somando {fmt_int(longos['duracao_h'].sum())} h. "
            f"O mais longo foi de {fmt_data_hora(maior['inicio'])} a {fmt_data_hora(maior['fim'])} "
            f"({fmt_int(maior['duracao_h'])} h, cerca de {fmt_int(maior['duracao_h'] / 24)} dias)."
        )
    else:
        texto = f"Não houve período de indisponibilidade total com pelo menos {DURACAO_MINIMA_EVENTO_RELATORIO_H} h."
    anuais = res.indicadores_anuais
    metade = anuais["horas_disponibilidade_ate_metade"]
    if metade.sum() > 0:
        idx = metade.idxmax()
        texto += (
            f" Em {fmt_int(metade.sum())} h a disponibilidade ficou acima de zero e igual ou inferior à metade da "
            f"potência instalada ({fmt_num(NOMINAL_INSTALLED_CAPACITY_MW / 2, 0)} MW); o ano com mais horas nessa "
            f"condição foi {int(anuais.loc[idx, 'ano'])} ({fmt_int(metade[idx])} h)."
        )
    return "Indisponibilidades", texto


def _achado_geracao(res: ResultadosAnalise) -> Tuple[str, str]:
    g = res.globais
    anuais = res.indicadores_anuais
    texto = (
        f"A geração média foi de {fmt_num(g['geracao_media_mwmed'], 1)} MWmed (fator de capacidade de "
        f"{fmt_pct(g['fator_capacidade_pct'])}), o equivalente a {fmt_pct(g['geracao_sobre_garantia_fisica_pct'])} "
        f"da garantia física ({fmt_num(GARANTIA_FISICA_MWMED, 1)} MWmed)."
    )
    completos = anuais[~anuais["ano_parcial"]]
    if len(completos):
        mn = completos.loc[completos["geracao_sobre_garantia_fisica_pct"].idxmin()]
        mx = completos.loc[completos["geracao_sobre_garantia_fisica_pct"].idxmax()]
        texto += (
            f" Nos anos completos, a razão entre geração média e garantia física variou de "
            f"{fmt_pct(mn['geracao_sobre_garantia_fisica_pct'])} ({int(mn['ano'])}) a "
            f"{fmt_pct(mx['geracao_sobre_garantia_fisica_pct'])} ({int(mx['ano'])})."
        )
    ultimo = anuais.iloc[-1]
    if bool(ultimo["ano_parcial"]):
        texto += f" Em {int(ultimo['ano'])} (parcial), foi de {fmt_pct(ultimo['geracao_sobre_garantia_fisica_pct'])}."
    return "Geração e garantia física", texto


def _achado_evt(res: ResultadosAnalise) -> Tuple[str, str]:
    g = res.globais
    anuais = res.indicadores_anuais
    itens = [
        f"{int(r.ano)}: {fmt_num(r.evt_mwh / 1000, 1)} GWh" + (" (parcial)" if r.ano_parcial else "")
        for r in anuais.itertuples()
    ]
    texto = (
        f"A energia vertida turbinável (EVT) somou {fmt_num(g['evt_mwh'] / 1000, 1)} GWh, o equivalente a "
        f"{fmt_pct(g['indice_evt_pct'])} da soma entre geração e EVT, e ocorreu em {fmt_pct(g['horas_com_evt_pct'])} "
        f"das horas. Nas horas com EVT, a folga média de geração (disponibilidade menos geração) foi de "
        f"{fmt_num(g['folga_media_com_evt_mw'], 1)} MW. Por ano: {'; '.join(itens)}."
    )
    return "Energia vertida turbinável", texto


def _achado_evt_nivel_geracao(res: ResultadosAnalise) -> Tuple[str, str]:
    g = res.globais
    texto = (
        f"Somente {fmt_pct(g['evt_plena_carga_pct'])} da EVT ocorreu com a usina próxima da plena carga "
        f"(geração igual ou superior a {fmt_num(g['limiar_plena_carga_mw'], 1)} MW)."
    )
    if g["horas_evt_acima_folga"] == 0:
        texto += (
            " Em todas as horas, a EVT não ultrapassa a folga de geração: quando a usina gera tudo o que "
            "declarou disponível, a EVT é nula."
        )
    else:
        texto += f" Em {fmt_int(g['horas_evt_acima_folga'])} horas a EVT ultrapassa a folga de geração."
    texto += (
        f" Já {fmt_pct(g['evt_parada_pct'])} da EVT ({fmt_num(g['evt_parada_mwh'] / 1000, 1)} GWh, em "
        f"{fmt_int(g['horas_parada_com_evt'])} h) ocorreu com a usina parada (geração até "
        f"{fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW) e disponibilidade média de "
        f"{fmt_num(g['disponibilidade_media_nas_paradas_mw'], 1)} MW."
    )
    return "EVT e nível de geração", texto


def _achado_paradas(res: ResultadosAnalise) -> Tuple[str, str]:
    anuais = res.indicadores_anuais
    itens = [
        f"{int(r.ano)}: {fmt_int(r.horas_parada_com_evt)} h" + (" (parcial)" if r.ano_parcial else "")
        for r in anuais.itertuples()
    ]
    texto = f"Horas com a usina parada e EVT, por ano: {'; '.join(itens)}."
    if anuais["evt_parada_mwh"].sum() > 0:
        mx = anuais.loc[anuais["evt_parada_mwh"].idxmax()]
        texto += (
            f" O maior volume foi em {int(mx['ano'])}, com {fmt_num(mx['evt_parada_mwh'] / 1000, 1)} GWh de EVT "
            f"nessas horas. A lista completa de eventos está na aba EVENTOS_PARADA_COM_EVT da planilha."
        )
    return "EVT com a usina parada", texto


def _achado_programacao(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    p = res.programacao.get("periodo")
    if not p:
        return None
    n_aus = p["dias_ausentes"]
    texto = (
        f"A programação diária do ONS para a usina cobre de {fmt_data(p['primeiro_dia'])} a {fmt_data(p['ultimo_dia'])} "
        f"no período da base ({fmt_int(p['dias_com_arquivo'])} dias com arquivo; {fmt_int(n_aus)} "
        f"{plural(n_aus, 'dia', 'dias')} sem arquivo no portal, cujas {fmt_int(p['horas_base_sem_programacao'])} horas ficam "
        f"fora do cruzamento). Nas {fmt_int(p['horas_comuns'])} horas comuns, a usina ficou parada com EVT em "
        f"{fmt_int(p['horas_parada_com_evt'])} h; em {fmt_int(p['horas_parada_evt_programacao_zero'])} delas "
        f"({fmt_pct(p['pct_horas_programacao_zero'])}) a programação do ONS era de até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW, "
        f"com disponibilidade declarada média de {fmt_num(p['disponibilidade_media_programacao_zero_mw'], 1)} MW. Essas horas "
        f"somam {fmt_num(p['evt_programacao_zero_mwh'] / 1000, 1)} GWh de EVT ({fmt_pct(p['pct_evt_programacao_zero'])} da EVT "
        f"das horas comuns), e {fmt_pct(p['pct_horas_zero_janela_diurna'])} delas ocorreram na janela das {_rotulo_janela(HORAS_DIURNAS)}."
    )
    maior = p["maior_evento"]
    if p["horas_desvio"] and maior is not None:
        texto += (
            f" Em {fmt_int(p['horas_desvio'])} h a usina ficou parada com programação acima de "
            f"{fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 0)} MW ({fmt_int(p['eventos_desvio'])} "
            f"{plural(p['eventos_desvio'], 'evento', 'eventos')}; o mais longo, de {fmt_data_hora(maior['inicio'])} a "
            f"{fmt_data_hora(maior['fim'])}, durou {fmt_int(maior['duracao_h'])} h com programação média de "
            f"{fmt_num(maior['programacao_media_mw'], 1)} MW)."
        )
    else:
        texto += f" Não houve hora com a usina parada e programação acima de {fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 0)} MW."
    texto += (
        f" Em {fmt_int(p['horas_gerando_programacao_zero'])} h a usina gerou acima de {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW "
        f"com programação de até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW. A correlação horária entre a geração verificada e a "
        f"programada foi de {fmt_num(p['correlacao_geracao_programacao'], 2)}. A programação diária não registra "
        "reprogramações em tempo real nem, para usinas hidráulicas, o motivo da programação."
    )
    return "Programação diária do ONS", texto


def _achado_disponibilidade_sincronizada(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    d = res.disponibilidade
    if not d:
        return None
    r, c = d["resumo"], d["conferencia"]
    texto = (
        f"A disponibilidade horária publicada pelo ONS para a usina cobre de {fmt_data(r['inicio'])} a "
        f"{fmt_data(r['fim'])} ({fmt_int(r['horas'])} horas). A disponibilidade operacional coincide com a disponibilidade "
        f"declarada da base de EVT em {fmt_int(c['coincidentes'])} das {fmt_int(c['horas_comuns'])} horas comuns "
        f"({fmt_pct(c['pct_coincidentes'])}; diferença de até {fmt_num(c['tolerancia_mw'], 2)} MW)"
    )
    texto += "." if not c["divergentes"] else f"; {fmt_int(c['divergentes'])} {plural(c['divergentes'], 'hora diverge', 'horas divergem')}."
    if r["horas_paradas"]:
        texto += (
            f" Nas {fmt_int(r['horas_paradas'])} horas comuns com a usina parada, nenhuma unidade estava sincronizada à rede "
            f"em {fmt_int(r['horas_paradas_sem_sincronizacao'])} ({fmt_pct(r['pct_paradas_sem_sincronizacao'])}); nas outras "
            f"{fmt_int(r['horas_paradas_sincronizadas'])} havia unidade sincronizada sem gerar acima de "
            f"{fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW."
        )
    if r["horas_parada_evt"]:
        texto += (
            f" Das {fmt_int(r['horas_parada_evt'])} horas paradas com EVT, {fmt_int(r['horas_parada_evt_sem_sincronizacao'])} "
            "foram com as unidades desligadas da rede"
        )
        if r["horas_parada_evt_programacao_zero"]:
            texto += (
                f"; no período da programação diária, {fmt_int(r['horas_parada_evt_programacao_zero_sem_sincronizacao'])} "
                f"das {fmt_int(r['horas_parada_evt_programacao_zero'])} horas paradas com EVT e programação de até "
                f"{fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW tinham as unidades desligadas"
            )
        texto += "."
    anual = d["anual"]
    completos = anual[~anual["ano_parcial"]]
    if len(completos) >= 2:
        menor = completos.loc[completos["disp_sincronizada_media_mw"].idxmin()]
        maior = completos.loc[completos["disp_sincronizada_media_mw"].idxmax()]
        texto += (
            f" Nos anos completos, a disponibilidade sincronizada média variou de {fmt_num(menor['disp_sincronizada_media_mw'], 1)} MW "
            f"({menor['periodo']}) a {fmt_num(maior['disp_sincronizada_media_mw'], 1)} MW ({maior['periodo']}), com a "
            f"operacional entre {fmt_num(completos['disp_operacional_media_mw'].min(), 1)} e "
            f"{fmt_num(completos['disp_operacional_media_mw'].max(), 1)} MW"
        )
        ultimo = anual.iloc[-1]
        if bool(ultimo["ano_parcial"]) and ultimo["periodo"] not in set(completos["periodo"]):
            texto += (f"; em {_rotulo_ano(ultimo['periodo'], True)}, a sincronizada média foi de "
                      f"{fmt_num(ultimo['disp_sincronizada_media_mw'], 1)} MW")
        texto += "."
    comparaveis = anual.dropna(subset=["reserva_desligada_teif_mwh"])
    if len(comparaveis):
        iguais = comparaveis[comparaveis["diferenca_mwh"].abs() <= 100]
        diferentes = comparaveis[comparaveis["diferenca_mwh"].abs() > 100]
        texto += (
            f" A capacidade disponível não sincronizada coincide com a reserva desligada apurada nos parâmetros TEIFa/TEIP "
            f"(horas em reserva desligada × potência) em {fmt_int(len(iguais))} dos {fmt_int(len(comparaveis))} anos com as "
            "duas apurações (diferença de até 0,1 GWh)"
        )
        if len(diferentes):
            texto += "; diverge em " + fmt_lista(
                f"{_rotulo_ano(r.periodo, r.ano_parcial)} ({'+' if r.diferenca_mwh > 0 else '−'}"
                f"{fmt_num(abs(r.diferenca_mwh) / 1000, 1)} GWh)"
                for r in diferentes.itertuples()
            ) + " (diferença = não sincronizada − reserva desligada); a causa da diferença não está nos dados abertos"
        texto += "."
    texto += " A sincronização mostra se as unidades estavam ligadas à rede, mas não o motivo da parada."
    return "Disponibilidade sincronizada", texto


def texto_conferencia_geracao(res: ResultadosAnalise) -> str:
    """Resultado da conferência da geração com a série oficial (seção e, havendo divergência, constatação)."""
    g = res.geracao_oficial
    r, c = g["resumo"], g["conferencia"]
    periodo = f"de {fmt_data(r['inicio'])} a {fmt_data(r['fim'])}"
    energia = (f"a energia do período é de {fmt_num(c['energia_base_evt_mwh'] / 1000, 3)} GWh na base de EVT e de "
               f"{fmt_num(c['energia_ons_geracao_mwh'] / 1000, 3)} GWh na série oficial")
    if not _divergencia_geracao(res):
        return (f"A geração horária da base de EVT coincide com a série oficial de geração por usina do ONS (id ONS "
                f"{ID_ONS_USINA}) em todas as {fmt_int(c['horas_comuns'])} horas comuns, {periodo} (diferença de até "
                f"{fmt_num(c['tolerancia_mw'], 2)} MW); {energia}.")
    texto = (f"A geração horária da base de EVT difere da série oficial de geração por usina do ONS (id ONS {ID_ONS_USINA}) "
             f"em {fmt_int(c['divergentes'])} das {fmt_int(c['horas_comuns'])} horas comuns, {periodo} (diferença acima de "
             f"{fmt_num(c['tolerancia_mw'], 2)} MW)")
    if c["so_ons_geracao"] or c["so_base_evt"]:
        texto += (f"; {fmt_int(c['so_ons_geracao'])} {plural(c['so_ons_geracao'], 'hora consta', 'horas constam')} só da "
                  f"série oficial e {fmt_int(c['so_base_evt'])} só da base de EVT")
    return texto + f"; {energia}. Lista completa nas abas GER_DIVERGENCIAS e GER_MENSAL."


def _achado_conferencia_geracao(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    if not res.geracao_oficial or not _divergencia_geracao(res):
        return None
    return "Conferência da geração", texto_conferencia_geracao(res)


def texto_cadastro(res: ResultadosAnalise) -> str:
    """Identificação da usina no cadastro do ONS (seção e, havendo divergência, constatação)."""
    f = res.cadastro["ficha"]
    texto = (
        f"No cadastro de modalidade das usinas do ONS ({_data_obtencao_texto(res.cadastro['obtido_em'])}), a usina consta "
        f"como {f.get('nom_usina', '')}, CEG {f.get('ceg', '')}, id ONS {f.get('id_ons', '')}, modalidade "
        f"{f.get('nom_modalidadeoperacao', '')}, centro de operação {f.get('sgl_centrooperacao', '')}, ponto de conexão "
        f"{f.get('nom_pontoconexao', '')}, potência autorizada de {fmt_num(f.get('val_potenciaautorizada'), 1)} MW, estado "
        f"{f.get('id_estado', '')} e situação na ANEEL \"{f.get('sts_aneel', '')}\". O cadastro tem "
        f"{fmt_int(f.get('homonimos', 0))} outras usinas com \"São Domingos\" no nome, excluídas pelo CEG."
    )
    if res.cadastro["divergencias"]:
        texto += f" Divergências com os parâmetros do projeto: {res.cadastro['divergencias']}."
    return texto


def _achado_cadastro(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    if not res.cadastro or not res.cadastro["divergencias"]:
        return None
    return "Cadastro da usina no ONS", texto_cadastro(res)


def _texto_alinhamento(alinhamento: pd.DataFrame) -> str:
    a = alinhamento.iloc[0]
    return (f"as vazões turbinada e vertida coincidiram com a base de EVT em {fmt_pct(a['pct_coincidencia'])} das "
            f"{fmt_int(a['horas_comuns'])} horas comuns (diferença de até {fmt_num(a['tolerancia_m3s'], 1)} m³/s; meta de "
            f"{fmt_num(a['meta_pct'], 0)}%)")


def _achado_afluencia(res: ResultadosAnalise) -> Optional[Tuple[str, str]]:
    h = res.hidrologia
    if not h:
        return None
    r = h["resumo"]
    cobertura = (f"Os dados hidrológicos horários do ONS para a usina cobrem de {fmt_data(r['inicio'])} a "
                 f"{fmt_data(r['fim'])} ({fmt_int(r['horas'])} horas, convertidas da hora de fim para a hora de início)")
    if not h["publicado"]:
        texto = (f"{cobertura}, mas não foram cruzados com a base de EVT: {_texto_alinhamento(h['alinhamento'])}, abaixo "
                 "da meta. Os dados hidrológicos são informados pelos agentes e não são consistidos pelo ONS.")
        return "Afluência e vertimento", texto
    f = r["horas_por_faixa"]
    total = r["horas_evt"]
    cabia = f[ATE_UMA_UNIDADE] + f[ENTRE_UMA_E_DUAS_UNIDADES]
    texto = (
        f"{cobertura}; {_texto_alinhamento(h['alinhamento'])}. Nas {fmt_int(total)} horas com EVT, a afluência estava "
        f"até o engolimento de uma unidade ({fmt_num(ENGOLIMENTO_NOMINAL_UG_M3S, 1)} m³/s) em {fmt_int(f[ATE_UMA_UNIDADE])} "
        f"({fmt_pct(_pct(f[ATE_UMA_UNIDADE], total))}), entre uma e duas unidades em {fmt_int(f[ENTRE_UMA_E_DUAS_UNIDADES])} "
        f"({fmt_pct(_pct(f[ENTRE_UMA_E_DUAS_UNIDADES], total))}) e acima do engolimento máximo da usina "
        f"({fmt_num(ENGOLIMENTO_MAXIMO_USINA_M3S, 1)} m³/s) em {fmt_int(f[ACIMA_ENGOLIMENTO_USINA])} "
        f"({fmt_pct(_pct(f[ACIMA_ENGOLIMENTO_USINA], total))})"
    )
    if f[SEM_DADO_HIDROLOGICO]:
        texto += f"; {fmt_int(f[SEM_DADO_HIDROLOGICO])} sem dado hidrológico"
    texto += (f". Em {fmt_pct(_pct(cabia, total))} das horas com EVT, portanto, a água que chegou ao reservatório "
              "cabia nas turbinas da usina.")
    perfil = h.get("perfil", pd.DataFrame())
    grupos = set(perfil["grupo_dias"]) if len(perfil) else set()
    if {COM_PARADA_EVT, DEMAIS_DIAS} <= grupos:
        com = perfil[perfil["grupo_dias"] == COM_PARADA_EVT].set_index("hora")["nivel_montante_medio_m"]
        demais = perfil[perfil["grupo_dias"] == DEMAIS_DIAS]["nivel_montante_medio_m"]
        antes = com.reindex([h_ for h_ in range(min(HORAS_DIURNAS) - 3, min(HORAS_DIURNAS))]).mean()
        janela = com.reindex(HORAS_DIURNAS).mean()
        texto += (
            f" Nos {fmt_int(r['dias_com_parada_evt'])} dias com ao menos uma hora de parada com EVT, o nível de montante "
            f"médio ficou em {fmt_num(com.mean(), 3)} m (amplitude de {fmt_num((com.max() - com.min()) * 100, 1)} cm ao longo "
            f"do dia; {fmt_num(antes, 3)} m entre {min(HORAS_DIURNAS) - 3}h e {min(HORAS_DIURNAS) - 1}h e "
            f"{fmt_num(janela, 3)} m na janela das {_rotulo_janela(HORAS_DIURNAS)}, quando a vazão vertida é maior), contra "
            f"{fmt_num(demais.mean(), 3)} m nos demais dias (amplitude de {fmt_num((demais.max() - demais.min()) * 100, 1)} cm)."
        )
    # FR-031: como no texto da disponibilidade, a ressalva de que nenhuma das bases informa o motivo das paradas
    texto += (" Os dados hidrológicos são informados pelos agentes e não são consistidos pelo ONS. A afluência e o nível "
              "mostram a água disponível e o comportamento do reservatório, mas não o motivo das paradas, que depende de "
              "informação do agente.")
    return "Afluência e vertimento", texto


def _achado_geracao_zero(res: ResultadosAnalise) -> Tuple[str, str]:
    g = res.globais
    tabela = res.horas_geracao_zero
    parciais = set(res.cobertura["anos_parciais"])
    total = int(tabela["total"].sum())
    disp_zero = int(tabela["com_disponibilidade_zero"].sum())
    itens = [
        f"{int(r.ano)}: {fmt_int(r.total)} h" + (" (parcial)" if int(r.ano) in parciais else "")
        for r in tabela.itertuples()
    ]
    texto = (
        f"A geração foi exatamente zero em {fmt_int(total)} h: {fmt_int(disp_zero)} h com disponibilidade zero "
        f"(indisponibilidade total) e {fmt_int(total - disp_zero)} h com a usina declarada disponível. Por ano: "
        f"{'; '.join(itens)}. Essa contagem difere das horas de usina parada com EVT: das {fmt_int(total)} h com "
        f"geração zero, {fmt_int(g['horas_geracao_zero_com_evt'])} h tiveram EVT positiva, e as horas de usina parada "
        f"com EVT incluem ainda {fmt_int(g['horas_geracao_ate_limiar_positiva_com_evt'])} h com geração entre 0 e "
        f"{fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW. A distribuição mensal está na aba HORAS_GERACAO_ZERO_MES da planilha."
    )
    return "Horas com geração zero", texto


def _achado_perfil_diurno(res: ResultadosAnalise) -> Tuple[str, str]:
    anuais = res.indicadores_anuais
    itens = [
        f"{int(r.ano)}: {fmt_num(r.razao_evt_diurna_noturna, 2)}" + ("*" if r.ano_parcial else "")
        for r in anuais.itertuples()
    ]
    texto = (
        f"Razão entre a EVT média das {_rotulo_janela(HORAS_DIURNAS)} e a das {_rotulo_janela(HORAS_NOTURNAS)}, "
        f"por ano (* parcial): {'; '.join(itens)}."
    )
    relevantes = anuais[anuais["razao_evt_diurna_noturna"] >= RAZAO_DIURNA_RELEVANTE]
    demais = anuais[anuais["razao_evt_diurna_noturna"] < RAZAO_DIURNA_RELEVANTE]
    if len(relevantes):
        texto += (
            f" Em {fmt_lista(int(a) for a in relevantes['ano'])}, a EVT se concentrou no período diurno e a geração "
            f"diurna ficou em {fmt_lista(fmt_pct(v * 100, 0) for v in relevantes['razao_geracao_diurna_noturna'])} "
            f"da noturna, respectivamente"
        )
        if len(demais):
            texto += (
                f"; nos demais anos, a geração diurna ficou entre "
                f"{fmt_pct(demais['razao_geracao_diurna_noturna'].min() * 100, 0)} e "
                f"{fmt_pct(demais['razao_geracao_diurna_noturna'].max() * 100, 0)} da noturna"
            )
        texto += "."
    return "Concentração diurna", texto


def _achado_sazonalidade(res: ResultadosAnalise) -> Tuple[str, str]:
    anos = res.cobertura["anos_completos"]
    dist = res.distribuicao_mes_do_ano
    if not anos or dist["evt_mwh"].sum() <= 0:
        return "Distribuição ao longo do ano", "Não há anos completos com EVT para avaliar a distribuição mensal."
    mai_out = dist[dist["mes"].isin(MESES_MAIO_A_OUTUBRO)]["participacao_pct"].sum()
    jan_abr = dist[dist["mes"].isin(MESES_JANEIRO_A_ABRIL)]["participacao_pct"].sum()
    top = dist.nlargest(3, "evt_mwh")["mes_nome"].tolist()
    texto = (
        f"Nos anos completos ({anos[0]} a {anos[-1]}), os meses de maio a outubro concentraram {fmt_pct(mai_out)} "
        f"da EVT e os de janeiro a abril, {fmt_pct(jan_abr)}. Os meses com maior EVT foram {fmt_lista(top)}."
    )
    return "Distribuição ao longo do ano", texto


def _achado_mudanca_classificacao(res: ResultadosAnalise) -> Tuple[str, str]:
    mc = res.mudanca_classificacao
    titulo = "Mudança de classificação do vertimento pelo ONS"
    if mc.get("mes") is None:
        return titulo, "Não foi detectada mudança na classificação do vertimento contínuo ao longo da série."
    mes = mc["mes"]
    texto = (
        f"A partir de {fmt_mes_ano(mes)}, cerca de {fmt_num(mc['nao_turbinavel_tipica_depois_m3s'], 0)} m³/s do "
        f"vertimento contínuo passaram a ser registrados pelo ONS como vazão vertida não turbinável. Até "
        f"{fmt_mes_ano(mes - 1)}, o vertimento contínuo ({fmt_num(mc['turbinavel_tipica_antes_m3s'], 0)} m³/s) era "
        f"contado como turbinável em {fmt_pct(mc['pct_horas_vertimento_minimo_turbinavel_antes'])} das horas, "
        f"com EVT média de {fmt_num(mc['evt_media_vertimento_minimo_antes_mw'], 1)} MWmed nessas horas."
    )
    anuais = res.indicadores_anuais
    completos = anuais[~anuais["ano_parcial"]]
    antes = completos[completos["ano"] < mes.year]
    depois = completos[completos["ano"] > mes.year]
    if len(antes) and len(depois):
        texto += (
            f" Nos anos completos anteriores, de {fmt_pct(antes['participacao_vertimento_minimo_pct'].min())} a "
            f"{fmt_pct(antes['participacao_vertimento_minimo_pct'].max())} da EVT anual veio de horas com vertimento de "
            f"até {fmt_num(LIMIAR_VERTIMENTO_MINIMO_M3S, 0)} m³/s; nos posteriores, no máximo "
            f"{fmt_pct(depois['participacao_vertimento_minimo_pct'].max())}. A série de EVT, portanto, não é "
            f"homogênea entre os dois períodos."
        )
    return titulo, texto


def _achado_qualidade(res: ResultadosAnalise) -> Tuple[str, str]:
    g = res.globais
    total = g["horas_com_anomalia"]
    if total == 0:
        return "Qualidade dos dados", "Nenhum registro viola as regras de plausibilidade física (R6 a R9)."
    detalhes = [
        f"{r.regra}, {r.descricao.lower()}: {fmt_int(r.horas)} h"
        for r in res.resumo_anomalias.itertuples()
        if r.horas > 0
    ]
    texto = (
        f"{fmt_int(total)} registros ({fmt_pct(_pct(total, g['horas']), 2)}) violam ao menos uma regra de "
        f"plausibilidade física ({'; '.join(detalhes)})."
    )
    if g["geracao_maxima_registrada_mw"] > NOMINAL_INSTALLED_CAPACITY_MW:
        texto += (
            f" O maior valor de geração registrado, {fmt_num(g['geracao_maxima_registrada_mw'], 1)} MW em "
            f"{fmt_data_hora(g['instante_geracao_maxima'])}, supera a potência instalada."
        )
    texto += (
        f" Esses registros foram mantidos nos totais (a EVT neles soma {fmt_num(g['evt_em_registros_anomalos_mwh'], 1)} MWh, "
        f"{fmt_pct(_pct(g['evt_em_registros_anomalos_mwh'], g['evt_mwh']), 2)} do total), sinalizados na coluna "
        f"{COLUNA_QUALIDADE} e excluídos da tabela de extremos."
    )
    return "Qualidade dos dados", texto


def montar_achados(res: ResultadosAnalise) -> List[Tuple[str, str]]:
    """Constatações em texto, todas derivadas dos resultados calculados."""
    oficiais = [a for a in (_achado_indicadores_ons(res), _achado_estados_operativos(res)) if a is not None]
    return [
        _achado_cobertura(res),
        *[a for a in (_achado_cadastro(res),) if a is not None],
        _achado_disponibilidade(res),
        *oficiais,
        _achado_indisponibilidade(res),
        _achado_geracao(res),
        _achado_evt(res),
        _achado_evt_nivel_geracao(res),
        _achado_paradas(res),
        *[a for a in (_achado_programacao(res), _achado_disponibilidade_sincronizada(res), _achado_afluencia(res))
          if a is not None],
        _achado_geracao_zero(res),
        _achado_perfil_diurno(res),
        _achado_sazonalidade(res),
        _achado_mudanca_classificacao(res),
        *[a for a in (_achado_conferencia_geracao(res),) if a is not None],
        _achado_qualidade(res),
    ]


def notas_metodologicas(res: ResultadosAnalise) -> List[str]:
    """Notas sobre definições e limitações (sem valores de resultado)."""
    prod_min, prod_max = faixa_produtividade()
    parciais = res.cobertura["anos_parciais"]
    notas = [
        f"Fonte: conjunto de dados Energia Vertida Turbinável do Portal de Dados Abertos do ONS ({ONS_DATASET_URL}), "
        "em base horária; a hora 00h representa o intervalo de 00:00 a 00:59:59. Os dados passam por consistência "
        "recorrente e podem ser revisados pelo ONS após a publicação.",
        "Os horários são os publicados pelo ONS (horário legal). Até fevereiro de 2019 vigorava o horário de verão, "
        "o que pode produzir hora ausente no seu início.",
        "Disponibilidade relativa = média da disponibilidade horária declarada (val_disponibilidade) ÷ potência "
        "instalada. É um indicador aproximado e não substitui o FID regulatório (razão IDv/ID calculada com TEIP e "
        f"TEIFa apurados), que não consta deste conjunto de dados. A referência de {fmt_pct(DISPONIBILIDADE_REFERENCIA * 100, 2)} "
        "é (1 − IP) × (1 − TEIF) com os valores usados no cálculo da garantia física.",
        f"A garantia física usada é de {fmt_num(GARANTIA_FISICA_MWMED, 1)} MWmed ({FONTE_GARANTIA_FISICA}). O IP e o TEIF de "
        f"referência são os do cálculo de garantia física registrado no {FONTE_PARAMETROS_USINA.split(',')[0]}, quando a "
        "garantia física era de 36,9 MWmed; a revisão posterior pode ter alterado esses parâmetros e, com eles, a "
        "disponibilidade de referência.",
        "Fator de capacidade = geração média ÷ potência instalada. A comparação com a garantia física é indicativa: "
        "não considera perdas até o centro de gravidade, a sazonalização da garantia física nem o MRE.",
        "A EVT é calculada pelo ONS como vazão vertida turbinável × produtividade e é limitada pela folga de geração "
        "(disponibilidade − geração). O conjunto de dados não informa a causa do vertimento nem da redução de geração "
        "(restrição interna da usina, restrição elétrica ou energética, ordem de despacho); a atribuição de causa "
        "depende de documentos do agente e do ONS.",
        f"Definições usadas: usina parada = geração ≤ {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW; plena carga = geração ≥ "
        f"{fmt_num(FRACAO_PLENA_CARGA * NOMINAL_INSTALLED_CAPACITY_MW, 1)} MW; vertimento mínimo = vazão vertida ≤ "
        f"{fmt_num(LIMIAR_VERTIMENTO_MINIMO_M3S, 0)} m³/s (patamar contínuo da série, da ordem da vazão remanescente de "
        f"{fmt_num(VAZAO_REMANESCENTE_M3S, 2)} m³/s); janela diurna {_rotulo_janela(HORAS_DIURNAS)}; noturna "
        f"{_rotulo_janela(HORAS_NOTURNAS)}.",
        "Registros que violam as regras de plausibilidade física (R6 a R9) foram mantidos nos totais, por serem os "
        "dados publicados pelo ONS, sinalizados na coluna qualidade_registro e excluídos das tabelas de extremos e do "
        f"perfil estatístico. A faixa de produtividade aceita (R8) é de {fmt_num(prod_min, 3)} a {fmt_num(prod_max, 3)} MW/(m³/s).",
    ]
    if parciais:
        n = len(parciais)
        notas.append(
            f"{plural(n, 'O ano', 'Os anos')} {fmt_lista(parciais)} {plural(n, 'é parcial', 'são parciais')}: "
            f"{plural(n, 'aparece', 'aparecem')} nas tabelas com a cobertura correspondente, mas não "
            f"{plural(n, 'entra', 'entram')} nas comparações entre anos completos."
        )
    if res.ons:
        notas += notas_indicadores_ons()
    if res.programacao:
        notas += notas_programacao()
    return notas + notas_bases_complementares(res)


def notas_bases_complementares(res: ResultadosAnalise) -> List[str]:
    """Relação de fontes das bases complementares do ONS carregadas (spec 006, FR-034).

    Cada base traz o link do conjunto, o identificador da usina (com a conferência), o período coberto e a data de
    obtenção, como já fazem EVT, indicadores e programação; sem a base, nenhuma linha.
    """
    notas: List[str] = []
    d = res.disponibilidade
    if d:
        r = d["resumo"]
        notas.append(
            f"Disponibilidade por usina: conjunto Disponibilidade por usina do ONS ({ONS_PORTAL_DATASET_URL}"
            f"{CONJUNTO_DISPONIBILIDADE}), usina {ID_ONS_USINA} (conferida pelo CEG {CEG_USINA} e pelo estado "
            f"{ESTADO_USINA}), de {fmt_data(r['inicio'])} a {fmt_data(r['fim'])}, {_data_obtencao_texto(d['obtido_em'])}."
        )
    h = res.hidrologia
    if h:
        r = h["resumo"]
        notas.append(
            f"Dados hidrológicos: conjunto Dados hidrológicos horários do ONS ({ONS_PORTAL_DATASET_URL}"
            f"{CONJUNTO_HIDROLOGIA}), cod_usina {COD_USINA_ONS} (conferido pelo nome e pelo código {ID_RESERVATORIO_ONS} "
            f"do reservatório), de {fmt_data(r['inicio'])} a {fmt_data(r['fim'])}, "
            f"{_data_obtencao_texto(h['obtido_em'])}; dados informados pelos agentes e não consistidos pelo ONS."
        )
    g = res.geracao_oficial
    if g:
        r = g["resumo"]
        notas.append(
            f"Geração por usina: conjunto Geração por usina do ONS ({ONS_PORTAL_DATASET_URL}{CONJUNTO_GERACAO}), usina "
            f"{ID_ONS_USINA} (conferida pelo CEG e pelo estado {ESTADO_USINA}), de {fmt_data(r['inicio'])} a "
            f"{fmt_data(r['fim'])}, {_data_obtencao_texto(g['obtido_em'])}."
        )
    c = res.cadastro
    if c:
        notas.append(
            f"Cadastro: conjunto Modalidade das usinas do ONS ({ONS_PORTAL_DATASET_URL}{CONJUNTO_CADASTRO}), CEG "
            f"{CEG_USINA} (conferido pelo id ONS {ID_ONS_USINA} e pelo estado {ESTADO_USINA}), cadastro sem série "
            f"histórica, {_data_obtencao_texto(c['obtido_em'])}."
        )
    return notas


def notas_indicadores_ons() -> List[str]:
    """Notas sobre os conjuntos de indicadores oficiais do ONS (sem valores de resultado)."""
    conjuntos = "; ".join(f"{d} ({ONS_PORTAL_DATASET_URL}{c})" for c, d in CONJUNTOS_INDICADORES_ONS.items())
    siglas = "; ".join(f"{s} = {d}" for s, d in INSUMOS_HORAS.items())
    return [
        f"Indicadores oficiais do ONS: {conjuntos}. A usina é identificada pelo CEG {CEG_USINA} (id ONS {ID_ONS_USINA}); "
        "os meses e anos são recortados no período da base de EVT e, quando o ONS publica mais de uma versão, vale a "
        "mais recente (num_versao).",
        "DISPF, INDISPPF e INDISPFF são percentuais do tempo do mês (ou do ano) em que a unidade esteve disponível, em "
        "desligamento programado ou em desligamento forçado, conforme o Submódulo 9.2 dos Procedimentos de Rede; não "
        "descontam a operação com potência limitada. A disponibilidade da usina pelo DISPF é a média das unidades, "
        "ponderada pela potência e pelas horas da base de EVT em cada mês.",
        f"Horas por estado operativo (dicionário do ONS sem definição das siglas; descrições pela nomenclatura da "
        f"metodologia de apuração das taxas): {siglas}. Em cada mês, HP = HS + HRD + HDP + HDF + HDCE + HEDP + HEDF "
        f"(conferido com tolerância de {fmt_num(TOLERANCIA_IDENTIDADE_HORAS, 1)} h).",
        f"TEIFa e TEIP recalculadas com janela móvel de {JANELA_TAXAS_MESES} meses, ponderadas pela potência das unidades: "
        "TEIFa = Σ(HDF + HEDF) ÷ Σ(HP − HDP − HEDP); TEIP = Σ(HDP + HEDP) ÷ ΣHP. A decomposição por unidade e parcela "
        "divide cada termo do numerador pelo mesmo denominador. Desligamentos por causa externa (HDCE) não entram em "
        "nenhuma das duas taxas.",
        "Os conjuntos de indicadores não informam a causa nem os eventos individuais de desligamento (data e hora de "
        "início e fim, motivo); essa informação depende dos registros do agente e do ONS.",
    ]


def notas_programacao() -> List[str]:
    """Notas sobre a programação diária do ONS (sem valores de resultado)."""
    return [
        f"Programação diária: conjunto Dados dos Valores da Programação Diária ({ONS_PORTAL_DATASET_URL}"
        f"{CONJUNTO_PROGRAMACAO_DIARIA}), um arquivo por dia desde 01/10/2024, usina {COD_EXIBICAO_USINA_PROGRAMACAO} "
        "(conferida pelo nome e pelo estado). A data de cada dia vem do nome do arquivo; os 48 patamares de 30 minutos "
        "são convertidos em horas pela média dos dois patamares de cada hora (hora de início, como na base de EVT).",
        f"Classificação das horas comuns: usina parada = geração ≤ {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW; programação "
        f"zero = programação ≤ {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW; desvio = usina parada com programação acima de "
        f"{fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 0)} MW. Dias sem arquivo no portal não são interpolados.",
        "A programação diária é o planejamento do dia e não registra reprogramações nem ordens em tempo real. Para usinas "
        "hidráulicas, os campos de motivo (ordem de mérito, inflexibilidade, razão elétrica) vêm vazios e a disponibilidade "
        "programada vem zerada; o conjunto mostra se a usina seguiu a programação, não por que o ONS a programou.",
    ]


# ---------------------------------------------------------------------------
# Orquestração da análise
# ---------------------------------------------------------------------------


def analisar(
    df: pd.DataFrame,
    caminho_auditoria: Optional[Path] = None,
    caminho_manifesto: Optional[Path] = None,
    indicadores: Optional[IndicadoresONS] = None,
    programacao: Optional[ProgramacaoONS] = None,
    disponibilidade: Optional[SerieConjunto] = None,
    hidrologia: Optional[Any] = None,
    geracao: Optional[SerieConjunto] = None,
    cadastro: Optional[pd.DataFrame] = None,
    dicionarios: Optional[pd.DataFrame] = None,
    auditoria_cadastro: Optional[pd.DataFrame] = None,
) -> ResultadosAnalise:
    """Calcula todos os resultados usados nas planilhas, no relatório e no PDF.

    As bases complementares (spec 006) são opcionais: disponibilidade e geração por usina
    (séries do motor comum), hidrologia (série e alinhamento), ficha cadastral e registro dos
    dicionários de dados. Sem elas, o relatório sai sem as seções correspondentes.

    ``indicadores`` são os indicadores oficiais do ONS por unidade geradora e ``programacao`` a
    programação diária do ONS (spec 004); sem eles, o relatório traz apenas a análise da base de EVT.
    """
    if "ano" not in df.columns or COLUNA_QUALIDADE not in df.columns:
        df = preparar_dados(df)
    cobertura = analisar_cobertura(df, caminho_auditoria, caminho_manifesto)
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
        parametros=tabela_parametros(com_indicadores=indicadores is not None, com_programacao=programacao is not None),
    )
    res.validacao = validar_regras_fisicas(df)[0]
    res.horas_geracao_zero = calcular_horas_geracao_zero(df)
    if indicadores is not None:
        res.ons = analisar_indicadores_ons(indicadores, df, anuais, cobertura)
    if programacao is not None and len(programacao.horaria):
        res.programacao = analisar_programacao(programacao, df)
    if disponibilidade is not None and len(disponibilidade.horaria):
        res.disponibilidade = analisar_disponibilidade(disponibilidade, df, indicadores, res.programacao, cobertura)
        res.parametros = pd.concat([res.parametros, parametros_disponibilidade(res)], ignore_index=True)
    if hidrologia is not None and len(hidrologia[0].horaria):
        res.hidrologia = analisar_hidrologia(hidrologia[0], hidrologia[1], df, cobertura)
        res.parametros = pd.concat([res.parametros, parametros_hidrologia(res)], ignore_index=True)
    if geracao is not None and len(geracao.horaria):
        res.geracao_oficial = analisar_geracao_oficial(geracao, df, cobertura)
    if cadastro is not None and len(cadastro):
        res.cadastro = analisar_cadastro(cadastro, auditoria_cadastro)
    if res.geracao_oficial or res.cadastro:
        res.parametros = pd.concat([res.parametros, parametros_geracao_cadastro(res)], ignore_index=True)
    if dicionarios is not None and len(dicionarios):
        res.dicionarios = {"registro": dicionarios}
    res.achados = montar_achados(res)
    res.fontes = origem_dos_dados(res)
    return res


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------


def _estilo_graficos() -> Dict[str, Any]:
    """Parâmetros visuais comuns às figuras (tipografia, eixos, grade e fundo)."""
    nomes = {f.name for f in font_manager.fontManager.ttflist}
    fonte = "Arial" if "Arial" in nomes else "DejaVu Sans"
    return {
        "font.family": fonte,
        "font.size": 9,
        "axes.titlesize": 10.5,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlecolor": COR_TINTA,
        "axes.titlepad": 10,
        "axes.labelsize": 9,
        "axes.labelcolor": COR_TINTA_SECUNDARIA,
        "axes.edgecolor": COR_EIXO,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": COR_GRADE,
        "grid.linewidth": 0.6,
        "grid.linestyle": "-",
        "xtick.color": COR_TINTA_SECUNDARIA,
        "ytick.color": COR_TINTA_SECUNDARIA,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "legend.frameon": False,
        "legend.fontsize": 8.5,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
    }


# Ordem categórica fixa (validada com o script da skill de visualização sobre fundo branco)
PALETA_CATEGORICA: List[str] = [COR_GERACAO, COR_DISPONIBILIDADE, COR_EVT]
# Intervalo na cor do fundo entre segmentos empilhados e barras vizinhas (pt)
LARGURA_INTERVALO_BARRAS = 0.8


@contextmanager
def _tema_graficos():
    """Tema único das figuras: seaborn com o estilo e a paleta do projeto; restaura o rc ao sair."""
    with plt.rc_context():
        sns.set_theme(style="ticks", palette=PALETA_CATEGORICA, rc=_estilo_graficos())
        yield


_FORMATADOR_PT = FuncFormatter(lambda v, _: fmt_num(v, 0))


def _rotulos_anos(anos: List[int], parciais: List[int]) -> List[str]:
    return [f"{int(a)}*" if int(a) in parciais else str(int(a)) for a in anos]


def _rotulo_referencia(ax: plt.Axes, y: float, texto: str) -> None:
    """Rótulo de linha de referência fora da área de plotagem, à direita."""
    ax.text(1.01, y, texto, transform=ax.get_yaxis_transform(), ha="left", va="center",
            fontsize=8, color=COR_TINTA_SECUNDARIA, clip_on=False)


def _grafico_serie_temporal(df: pd.DataFrame, res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    P = NOMINAL_INSTALLED_CAPACITY_MW
    diario = (
        df.set_index("din_instante")[["val_disponibilidade", "val_geracao", "val_energiavertidaturbinavel"]]
        .resample("D")
        .mean()
    )
    nomes = {
        "val_disponibilidade": "Disponibilidade declarada",
        "val_geracao": "Geração",
        "val_energiavertidaturbinavel": "Energia vertida turbinável (EVT)",
    }
    cores = {nomes["val_disponibilidade"]: COR_DISPONIBILIDADE, nomes["val_geracao"]: COR_GERACAO,
             nomes["val_energiavertidaturbinavel"]: COR_EVT}
    longo = (
        diario.reset_index()
        .melt(id_vars="din_instante", var_name="serie", value_name="mw")
        .assign(serie=lambda d: d["serie"].map(nomes))
    )
    fig, ax = plt.subplots(figsize=(11, 5.0))
    eventos = res.eventos_indisponibilidade_total
    longos = eventos[eventos["duracao_h"] >= DURACAO_MINIMA_EVENTO_RELATORIO_H] if len(eventos) else eventos
    for ev in longos.itertuples():
        ax.axvspan(ev.inicio, ev.fim, color=COR_FAIXA_INDISPONIBILIDADE, lw=0, zorder=0)
    ax.fill_between(diario.index, 0, diario["val_energiavertidaturbinavel"], color=COR_EVT, alpha=0.22, lw=0, zorder=1)
    sns.lineplot(data=longo, x="din_instante", y="mw", hue="serie", hue_order=list(cores), palette=cores,
                 estimator=None, errorbar=None, linewidth=1.0, legend=False, ax=ax)
    ax.axhline(P, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax.axhline(GARANTIA_FISICA_MWMED, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (1, 2)), zorder=1)
    _rotulo_referencia(ax, P, f"Potência instalada\n{fmt_num(P, 0)} MW")
    _rotulo_referencia(ax, GARANTIA_FISICA_MWMED, f"Garantia física\n{fmt_num(GARANTIA_FISICA_MWMED, 1)} MWmed")

    ax.set_xlim(diario.index.min(), diario.index.max())
    ax.set_ylim(0, P * 1.15)
    ax.set_xlabel("")
    ax.set_ylabel("MW médios (média diária)")
    ax.yaxis.set_major_formatter(_FORMATADOR_PT)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_title("Disponibilidade declarada, geração e energia vertida turbinável (médias diárias)")

    legendas = [
        plt.Line2D([], [], color=COR_DISPONIBILIDADE, lw=2, label="Disponibilidade declarada"),
        plt.Line2D([], [], color=COR_GERACAO, lw=2, label="Geração"),
        Patch(facecolor=COR_EVT, alpha=0.6, label="Energia vertida turbinável (EVT)"),
    ]
    if len(longos):
        legendas.append(Patch(facecolor=COR_FAIXA_INDISPONIBILIDADE,
                              label=f"Indisponibilidade total ≥ {DURACAO_MINIMA_EVENTO_RELATORIO_H} h"))
    ax.legend(handles=legendas, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=len(legendas))
    fig.subplots_adjust(left=0.07, right=0.86, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_evt_mensal(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    m = res.evt_mensal
    rotulo_minimo = f"EVT em horas com vertimento de até {fmt_num(LIMIAR_VERTIMENTO_MINIMO_M3S, 0)} m³/s (patamar contínuo)"
    rotulo_demais = "EVT nas demais horas"
    cores = {rotulo_minimo: COR_CONTEXTO, rotulo_demais: COR_EVT}
    longo = pd.concat([
        pd.DataFrame({"mes": m["mes"], "parcela": rotulo_minimo, "mwh": m["evt_vertimento_minimo_mwh"]}),
        pd.DataFrame({"mes": m["mes"], "parcela": rotulo_demais, "mwh": m["evt_demais_horas_mwh"]}),
    ], ignore_index=True)
    fig, ax = plt.subplots(figsize=(11, 5.0))
    if len(m):
        limites = list(m["mes"]) + [m["mes"].max() + pd.offsets.MonthBegin(1)]
        # o seaborn empilha da última categoria (base) para a primeira (topo)
        sns.histplot(data=longo, x="mes", weights="mwh", hue="parcela", hue_order=[rotulo_demais, rotulo_minimo],
                     palette=cores, multiple="stack", bins=[float(b) for b in mdates.date2num(limites)],
                     shrink=0.85, alpha=1, edgecolor="white", linewidth=0.3, legend=False, ax=ax)

    mc = res.mudanca_classificacao
    topo = float((m["evt_mwh"]).max()) * 1.12 if len(m) else 1.0
    if mc.get("mes") is not None:
        x = mc["mes"].start_time
        ax.axvline(x, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (4, 3)))
        ax.text(x, topo * 0.98, f"  {fmt_mes_ano(mc['mes'])}: parte do vertimento contínuo passa a\n"
                                f"  ser registrada como não turbinável", ha="left", va="top", fontsize=8,
                color=COR_TINTA_SECUNDARIA)
    if len(m):
        ax.set_xlim(m["mes"].min() - pd.Timedelta(days=5), m["mes"].max() + pd.Timedelta(days=36))
    ax.set_ylim(0, topo)
    ax.set_xlabel("")
    ax.set_ylabel("EVT mensal (MWh)")
    ax.yaxis.set_major_formatter(_FORMATADOR_PT)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(axis="x", visible=False)
    ax.set_title("Energia vertida turbinável mensal")
    ax.legend(handles=[Patch(facecolor=COR_CONTEXTO, label=rotulo_minimo), Patch(facecolor=COR_EVT, label=rotulo_demais)],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=2)
    fig.subplots_adjust(left=0.07, right=0.97, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_perfil_horario(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    parciais = res.cobertura["anos_parciais"]
    fig, eixos = plt.subplots(1, 2, figsize=(11, 4.4))
    paineis = [
        (res.perfil_horario_geracao, RAMPA_AZUL, "Geração média por hora do dia (MW)"),
        (res.perfil_horario_evt, RAMPA_LARANJA, "EVT média por hora do dia (MWmed)"),
    ]
    for ax, (tabela, rampa, titulo) in zip(eixos, paineis):
        mapa = LinearSegmentedColormap.from_list(titulo, rampa)
        sns.heatmap(tabela, cmap=mapa, vmin=0, ax=ax, cbar=True, cbar_kws={"fraction": 0.046, "pad": 0.02},
                    linewidths=0, xticklabels=False, yticklabels=False)
        ax.set_yticks([i + 0.5 for i in range(len(tabela.index))])
        ax.set_yticklabels(_rotulos_anos(list(tabela.index), parciais), rotation=0)
        ax.set_xticks([h + 0.5 for h in range(0, 24, 3)])
        ax.set_xticklabels([f"{h}h" for h in range(0, 24, 3)], rotation=0)
        ax.set_xlabel("Hora do dia")
        ax.set_ylabel("")
        ax.grid(False)
        for lado in ("left", "bottom"):
            ax.spines[lado].set_visible(False)
        ax.set_title(titulo)
        barra = ax.collections[0].colorbar
        barra.outline.set_visible(False)
        barra.ax.tick_params(labelsize=8, length=0)
        barra.ax.yaxis.set_major_formatter(_FORMATADOR_PT)
    if parciais:
        fig.text(0.01, 0.015, "* ano parcial", fontsize=8, color=COR_TINTA_SUAVE)
    fig.subplots_adjust(left=0.06, right=0.97, top=0.9, bottom=0.14, wspace=0.28)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_disponibilidade_anual(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    a = res.indicadores_anuais
    parciais = res.cobertura["anos_parciais"]
    rotulos = _rotulos_anos(a["ano"].tolist(), parciais)
    nomes = {"disponibilidade_relativa_pct": "Disponibilidade média declarada",
             "fator_capacidade_pct": "Geração média (fator de capacidade)"}
    cores = {nomes["disponibilidade_relativa_pct"]: COR_DISPONIBILIDADE, nomes["fator_capacidade_pct"]: COR_GERACAO}
    longo = (
        a.assign(rotulo=rotulos)
        .melt(id_vars="rotulo", value_vars=list(nomes), var_name="indicador", value_name="pct")
        .assign(indicador=lambda d: d["indicador"].map(nomes))
    )
    fig, ax = plt.subplots(figsize=(11, 4.6))
    sns.barplot(data=longo, x="rotulo", y="pct", hue="indicador", order=rotulos, hue_order=list(cores),
                palette=cores, errorbar=None, width=0.76, gap=0.06, saturation=1, legend=False, ax=ax)
    referencia = DISPONIBILIDADE_REFERENCIA * 100
    gf_rel = GARANTIA_FISICA_MWMED / NOMINAL_INSTALLED_CAPACITY_MW * 100
    ax.axhline(referencia, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (4, 3)))
    ax.axhline(gf_rel, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (1, 2)))
    _rotulo_referencia(ax, referencia, f"Disponibilidade de\nreferência (GF): {fmt_pct(referencia)}")
    _rotulo_referencia(ax, gf_rel, f"Garantia física:\n{fmt_pct(gf_rel)} da potência")
    ax.set_ylim(0, 105)
    ax.set_xlabel("")
    ax.set_ylabel("% da potência instalada")
    ax.yaxis.set_major_formatter(_FORMATADOR_PT)
    ax.grid(axis="x", visible=False)
    ax.set_title("Disponibilidade média e geração média por ano (% da potência instalada)")
    ax.legend(handles=[Patch(facecolor=c, label=n) for n, c in cores.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
    if parciais:
        fig.text(0.01, 0.02, "* ano parcial", fontsize=8, color=COR_TINTA_SUAVE)
    fig.subplots_adjust(left=0.07, right=0.84, top=0.89, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_vazoes_defluentes(df: pd.DataFrame, res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    parciais = res.cobertura["anos_parciais"]
    nomes = {
        "val_vazaoturbinada": "Vazão turbinada",
        "val_vazaovertidaturbinavel": "Vazão vertida turbinável",
        "val_vazaovertidanaoturbinavel": "Vazão vertida não turbinável",
    }
    cores = {nomes["val_vazaoturbinada"]: COR_GERACAO, nomes["val_vazaovertidaturbinavel"]: COR_EVT,
             nomes["val_vazaovertidanaoturbinavel"]: COR_CONTEXTO}
    v = df.groupby("ano")[list(nomes)].mean()
    longo = (
        v.reset_index()
        .melt(id_vars="ano", var_name="componente", value_name="m3s")
        .assign(componente=lambda d: d["componente"].map(nomes))
    )
    fig, ax = plt.subplots(figsize=(11, 4.6))
    # o seaborn empilha da última categoria (base) para a primeira (topo): turbinada na base
    sns.histplot(data=longo, x="ano", weights="m3s", hue="componente", hue_order=list(reversed(list(cores))),
                 palette=cores, multiple="stack", discrete=True, shrink=0.6, alpha=1, edgecolor="white",
                 linewidth=LARGURA_INTERVALO_BARRAS, legend=False, ax=ax)
    ax.axhline(ENGOLIMENTO_MAXIMO_USINA_M3S, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (4, 3)))
    _rotulo_referencia(ax, ENGOLIMENTO_MAXIMO_USINA_M3S,
                       f"Engolimento máximo\n{NUMERO_UNIDADES_GERADORAS} × {fmt_num(ENGOLIMENTO_NOMINAL_UG_M3S, 1)} m³/s")
    ax.set_xticks(list(v.index))
    ax.set_xticklabels(_rotulos_anos(v.index.tolist(), parciais))
    topo = float(v.sum(axis=1).max()) if len(v) else 0.0
    ax.set_ylim(0, max(topo, ENGOLIMENTO_MAXIMO_USINA_M3S) * 1.1)
    ax.set_xlabel("")
    ax.set_ylabel("m³/s (média anual)")
    ax.yaxis.set_major_formatter(_FORMATADOR_PT)
    ax.grid(axis="x", visible=False)
    ax.set_title("Vazões defluentes médias por ano: turbinada, vertida turbinável e vertida não turbinável")
    ax.legend(handles=[Patch(facecolor=c, label=n) for n, c in cores.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3)
    if parciais:
        fig.text(0.01, 0.02, "* ano parcial", fontsize=8, color=COR_TINTA_SUAVE)
    fig.subplots_adjust(left=0.07, right=0.84, top=0.89, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _rotulos_no_fim(ax: plt.Axes, pontos: List[Tuple[float, str]], x_fim: Any, folga_minima: float) -> None:
    """Rótulos diretos à direita do fim das linhas; omitidos se dois ficarem próximos demais (fica a legenda)."""
    valores = sorted(v for v, _ in pontos if pd.notna(v))
    if len(valores) < len(pontos) or any(b - a < folga_minima for a, b in zip(valores, valores[1:])):
        return
    for valor, texto in pontos:
        ax.annotate(texto, xy=(x_fim, valor), xytext=(6, 0), textcoords="offset points", ha="left", va="center",
                    fontsize=8, color=COR_TINTA_SECUNDARIA, annotation_clip=False)


def _grafico_disponibilidade_sincronizada(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    """Figura 06 (spec 006, US3): médias mensais de disponibilidade operacional e sincronizada e de geração."""
    m = res.disponibilidade["mensal"].copy()
    m["mes"] = pd.PeriodIndex(m["periodo"], freq="M").to_timestamp()
    series = {
        "Disponibilidade operacional": ("disp_operacional_media_mw", COR_DISPONIBILIDADE),
        "Disponibilidade sincronizada": ("disp_sincronizada_media_mw", COR_SINCRONIZADA),
        "Geração": ("geracao_media_mw", COR_GERACAO),
    }
    longo = pd.concat(
        [pd.DataFrame({"mes": m["mes"], "serie": nome, "mw": m[coluna]}) for nome, (coluna, _) in series.items()],
        ignore_index=True,
    )
    fig, ax = plt.subplots(figsize=(11, 4.6))
    sns.lineplot(data=longo, x="mes", y="mw", hue="serie", hue_order=list(series),
                 palette={nome: cor for nome, (_, cor) in series.items()}, linewidth=1.4, legend=False, ax=ax)
    ax.axhline(NOMINAL_INSTALLED_CAPACITY_MW, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    _rotulo_referencia(ax, NOMINAL_INSTALLED_CAPACITY_MW, f"Potência instalada\n{fmt_num(NOMINAL_INSTALLED_CAPACITY_MW, 0)} MW")
    if len(m):
        ultimo = m.iloc[-1]
        _rotulos_no_fim(ax, [(ultimo[c], n) for n, (c, _) in series.items()], ultimo["mes"], folga_minima=3.5)
        ax.set_xlim(m["mes"].min() - pd.Timedelta(days=20), m["mes"].max() + pd.Timedelta(days=20))
    ax.set_ylim(0, NOMINAL_INSTALLED_CAPACITY_MW * 1.08)
    ax.set_xlabel("")
    ax.set_ylabel("MW (média mensal)")
    ax.yaxis.set_major_formatter(_FORMATADOR_PT)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(axis="x", visible=False)
    ax.set_title("Disponibilidade operacional e sincronizada e geração: médias mensais (ONS)")
    ax.legend(handles=[plt.Line2D([], [], color=cor, lw=2, label=nome) for nome, (_, cor) in series.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=3)
    fig.subplots_adjust(left=0.07, right=0.80, top=0.89, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_faixas_afluencia(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    """Figura 07 (spec 006, US4): horas com EVT por faixa de afluência, por ano (rampa ordinal de laranja)."""
    t = res.hidrologia["faixas_anual"].copy()
    t["ano"] = t["periodo"].astype(int)
    rotulos = {
        ATE_UMA_UNIDADE: f"Afluência até {fmt_num(ENGOLIMENTO_NOMINAL_UG_M3S, 1)} m³/s (cabia em uma unidade)",
        ENTRE_UMA_E_DUAS_UNIDADES: f"{fmt_num(ENGOLIMENTO_NOMINAL_UG_M3S, 1)} a {fmt_num(ENGOLIMENTO_MAXIMO_USINA_M3S, 0)} m³/s "
                                   "(cabia nas duas)",
        ACIMA_ENGOLIMENTO_USINA: f"Acima de {fmt_num(ENGOLIMENTO_MAXIMO_USINA_M3S, 0)} m³/s (acima do engolimento máximo)",
        SEM_DADO_HIDROLOGICO: "Sem dado hidrológico",
    }
    cores = dict(zip([rotulos[f] for f in (ATE_UMA_UNIDADE, ENTRE_UMA_E_DUAS_UNIDADES, ACIMA_ENGOLIMENTO_USINA)],
                     RAMPA_FAIXAS_AFLUENCIA))
    cores[rotulos[SEM_DADO_HIDROLOGICO]] = COR_CONTEXTO
    t["faixa"] = t["faixa_afluencia"].map(rotulos)
    ordem_base_ao_topo = [rotulos[f] for f in FAIXAS_AFLUENCIA]
    fig, ax = plt.subplots(figsize=(11, 4.6))
    # o seaborn empilha da última categoria (base) para a primeira (topo): faixa de menor afluência na base
    sns.histplot(data=t, x="ano", weights="horas", hue="faixa", hue_order=list(reversed(ordem_base_ao_topo)),
                 palette=cores, multiple="stack", discrete=True, shrink=0.6, alpha=1, edgecolor="white",
                 linewidth=LARGURA_INTERVALO_BARRAS, legend=False, ax=ax)
    totais = t.groupby("ano")["horas"].sum()
    for ano, total in totais.items():
        ax.annotate(fmt_int(total), xy=(ano, total), xytext=(0, 3), textcoords="offset points", ha="center",
                    va="bottom", fontsize=8, color=COR_TINTA_SECUNDARIA)
    anos = totais.index.tolist()
    parciais = [int(a) for a in t.loc[t["ano_parcial"], "ano"].unique()]
    ax.set_xticks(anos)
    ax.set_xticklabels(_rotulos_anos(anos, parciais))
    ax.set_ylim(0, float(totais.max()) * 1.12 if len(totais) else 1)
    ax.set_xlabel("")
    ax.set_ylabel("Horas com EVT")
    ax.yaxis.set_major_formatter(_FORMATADOR_PT)
    ax.grid(axis="x", visible=False)
    ax.set_title("Horas com energia vertida turbinável por faixa de afluência ao reservatório")
    ax.legend(handles=[Patch(facecolor=cores[r], label=r) for r in ordem_base_ao_topo],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=2)
    if parciais:
        fig.text(0.01, 0.02, "* ano parcial", fontsize=8, color=COR_TINTA_SUAVE)
    fig.subplots_adjust(left=0.07, right=0.97, top=0.89, bottom=0.25)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_perfil_hidrologico(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    """Figura 08 (spec 006, US4): vazões e nível de montante médios por hora do dia, em dois painéis (sem eixo duplo)."""
    p = res.hidrologia["perfil"]
    grupos = {COM_PARADA_EVT: "Dias com parada com EVT", DEMAIS_DIAS: "Demais dias"}
    tracos = {grupos[COM_PARADA_EVT]: "", grupos[DEMAIS_DIAS]: (4, 2)}
    vazoes = {"afluencia_media_m3s": ("Vazão afluente", COR_AFLUENCIA),
              "turbinada_media_m3s": ("Vazão turbinada", COR_GERACAO),
              "vertida_media_m3s": ("Vazão vertida", COR_EVT)}
    longo = pd.concat([
        pd.DataFrame({"hora": p["hora"], "grupo": p["grupo_dias"].map(grupos), "variavel": nome, "m3s": p[coluna]})
        for coluna, (nome, _) in vazoes.items()
    ], ignore_index=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1.7, 1]})
    for ax in (ax1, ax2):
        ax.axvspan(min(HORAS_DIURNAS) - 0.5, max(HORAS_DIURNAS) + 0.5, color=COR_FAIXA_INDISPONIBILIDADE, lw=0, zorder=0)
    sns.lineplot(data=longo, x="hora", y="m3s", hue="variavel", style="grupo", palette={n: c for n, c in vazoes.values()},
                 dashes=tracos, hue_order=[n for n, _ in vazoes.values()], style_order=list(tracos), linewidth=1.4,
                 legend=False, ax=ax1)
    nivel = p.assign(grupo=p["grupo_dias"].map(grupos))
    sns.lineplot(data=nivel, x="hora", y="nivel_montante_medio_m", style="grupo", dashes=tracos,
                 style_order=list(tracos), color=COR_TINTA_SECUNDARIA, linewidth=1.4, legend=False, ax=ax2)
    for ax, titulo, rotulo_y in ((ax1, "Vazões médias por hora do dia", "m³/s"),
                                 (ax2, "Nível de montante médio por hora do dia", "m")):
        ax.set_title(titulo)
        ax.set_xlabel("Hora do dia")
        ax.set_ylabel(rotulo_y)
        ax.set_xticks(range(0, 24, 3))
        ax.set_xticklabels([f"{h}h" for h in range(0, 24, 3)])
        ax.set_xlim(-0.5, 23.5)
        ax.grid(axis="x", visible=False)
    ax1.set_ylim(bottom=0)
    ax1.yaxis.set_major_formatter(_FORMATADOR_PT)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_num(v, 2)))
    alcas = [plt.Line2D([], [], color=c, lw=2, label=n) for n, c in vazoes.values()]
    alcas += [plt.Line2D([], [], color=COR_TINTA_SECUNDARIA, lw=2, label="Nível de montante")]
    alcas += [plt.Line2D([], [], color=COR_TINTA_SUAVE, lw=1.6, ls="-", label=grupos[COM_PARADA_EVT]),
              plt.Line2D([], [], color=COR_TINTA_SUAVE, lw=1.6, ls=(0, (4, 2)), label=grupos[DEMAIS_DIAS]),
              Patch(facecolor=COR_FAIXA_INDISPONIBILIDADE, label=f"Janela das {_rotulo_janela(HORAS_DIURNAS)}")]
    fig.legend(handles=alcas, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 0.0), frameon=False)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.89, bottom=0.27, wspace=0.22)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def gerar_graficos(
    df: pd.DataFrame,
    res: ResultadosAnalise,
    diretorio_figuras: Optional[Path] = None,
    dpi: int = DEFAULT_PLOT_DPI,
) -> Dict[str, Path]:
    """Gera as 5 figuras do relatório com seaborn e retorna {chave: caminho}."""
    pasta = diretorio_figuras or REPORTS_FIGURES_DIR
    pasta.mkdir(parents=True, exist_ok=True)
    logger.info("Gerando gráficos analíticos (%d DPI) em: %s", dpi, pasta)
    caminhos = {chave: pasta / nome for chave, nome in NOMES_FIGURAS.items()}
    with _tema_graficos():
        _grafico_serie_temporal(df, res, caminhos["serie_temporal"], dpi)
        _grafico_evt_mensal(res, caminhos["evt_mensal"], dpi)
        _grafico_perfil_horario(res, caminhos["perfil_horario"], dpi)
        _grafico_disponibilidade_anual(res, caminhos["disponibilidade_anual"], dpi)
        _grafico_vazoes_defluentes(df, res, caminhos["vazoes_defluentes"], dpi)
        for chave, nome in NOMES_FIGURAS_OPCIONAIS.items():
            gerador, disponivel = _GERADORES_OPCIONAIS[chave]
            if disponivel(res):
                caminhos[chave] = pasta / nome
                gerador(res, caminhos[chave], dpi)
    logger.info("Gráficos gerados: %d", len(caminhos))
    return caminhos


# Figuras opcionais (spec 006): chave -> (função que gera, condição para gerar)
_GERADORES_OPCIONAIS: Dict[str, Tuple[Any, Any]] = {
    "disponibilidade_sincronizada": (_grafico_disponibilidade_sincronizada,
                                     lambda res: bool(res.disponibilidade) and len(res.disponibilidade["mensal"]) > 0),
    "faixas_afluencia": (_grafico_faixas_afluencia,
                         lambda res: bool(res.hidrologia.get("publicado")) and len(res.hidrologia["faixas_anual"]) > 0),
    "perfil_hidrologico": (_grafico_perfil_hidrologico,
                           lambda res: bool(res.hidrologia.get("publicado")) and len(res.hidrologia["perfil"]) > 0),
}


# ---------------------------------------------------------------------------
# Exportação de tabelas e relatório Markdown
# ---------------------------------------------------------------------------


def _globais_como_tabela(res: ResultadosAnalise) -> pd.DataFrame:
    linhas = []
    for chave, valor in res.globais.items():
        linhas.append({"indicador": chave, "valor": str(valor) if isinstance(valor, pd.Timestamp) else valor})
    c = res.cobertura
    linhas += [
        {"indicador": "inicio_serie", "valor": str(c["inicio"])},
        {"indicador": "fim_serie", "valor": str(c["fim"])},
        {"indicador": "horas_ausentes", "valor": ", ".join(str(t) for t in c["horas_faltantes"])},
        {"indicador": "anos_parciais", "valor": ", ".join(str(a) for a in c["anos_parciais"])},
        {"indicador": "mes_mudanca_classificacao_vertimento",
         "valor": str(res.mudanca_classificacao.get("mes") or "")},
    ]
    return pd.DataFrame(linhas)


def exportar_tabelas(
    res: ResultadosAnalise,
    caminho_xlsx: Optional[Path] = None,
    caminho_csv: Optional[Path] = None,
) -> Tuple[Path, Path]:
    """Exporta todas as tabelas calculadas para Excel e os indicadores anuais para CSV."""
    dest_xlsx = caminho_xlsx or STATISTICAL_REPORT_XLSX
    dest_csv = caminho_csv or STATISTICAL_REPORT_CSV
    dest_xlsx.parent.mkdir(parents=True, exist_ok=True)

    abas = {
        "CONSTATACOES": pd.DataFrame(res.achados, columns=["tema", "constatacao"]),
        "INDICADORES_ANUAIS": res.indicadores_anuais,
        "INDICADORES_GLOBAIS": _globais_como_tabela(res),
        "COBERTURA_POR_ANO": res.cobertura["por_ano"],
        "AGENTES": res.cobertura["agentes"],
        "EVT_MENSAL": res.evt_mensal,
        "EVT_MES_DO_ANO": res.distribuicao_mes_do_ano,
        "EVT_POR_FAIXA_GERACAO": res.evt_por_faixa_geracao,
        "PERFIL_HORARIO_GERACAO": res.perfil_horario_geracao.reset_index(),
        "PERFIL_HORARIO_EVT": res.perfil_horario_evt.reset_index(),
        "EVENTOS_PARADA_COM_EVT": res.eventos_parada_com_evt,
        "HORAS_GERACAO_ZERO_MES": res.horas_geracao_zero,
        "EVENTOS_INDISP_TOTAL": res.eventos_indisponibilidade_total,
        "ANOMALIAS": res.anomalias,
        "RESUMO_ANOMALIAS": res.resumo_anomalias,
        "VALIDACAO_REGRAS": res.validacao,
        "EXTREMOS": res.extremos,
        "PERFIL_ESTATISTICO_ANUAL": res.perfil_estatistico,
        "PARAMETROS": res.parametros,
    }
    o = res.ons
    abas_ons = {
        "ONS_DISP_ANUAL_USINA": o.get("disp_anual"),
        "ONS_UG_ANUAL": o.get("ug_anual"),
        "ONS_HORAS_UG_ANUAL": o.get("horas_anual"),
        "ONS_HORAS_UG_MENSAL": o.get("horas_mensal"),
        "ONS_TEIFA_TEIP": o.get("recalculo_taxas"),
        "ONS_DECOMPOSICAO_TAXAS": o.get("decomposicao"),
        "ONS_DIVERGENCIAS": o.get("divergencias"),
    }
    abas.update({nome: t for nome, t in abas_ons.items() if t is not None and len(t)})
    pr = res.programacao
    abas_programacao = {
        "PROG_RESUMO_MENSAL": pr.get("mensal"),
        "PROG_EVENTOS_DESVIO": pr.get("eventos"),
        "PROG_HORA_DO_DIA": pr.get("perfil"),
        "PROG_DIAS_AUSENTES": pr.get("dias_ausentes"),
        "PROG_AUDITORIA_ARQUIVOS": pr.get("auditoria"),
        "PROG_HORAS_CLASSIFICADAS": pr.get("classificadas"),
    }
    abas.update({nome: t for nome, t in abas_programacao.items() if t is not None and len(t)})
    di = res.disponibilidade
    if di:
        abas_disponibilidade = {
            "DISP_CONFERENCIA": pd.DataFrame([di["conferencia"]]),
            "DISP_DIVERGENCIAS": di["divergencias"],
            "DISP_CLASSES_PARADA": di["classes"],
            "DISP_HORAS_PARADAS": di["horas_paradas"],
            "DISP_MENSAL": di["mensal"],
            "DISP_ANUAL": di["anual"],
            "DISP_AUSENCIAS": di["ausencias"],
            "DISP_AUDITORIA": di["auditoria"],
        }
        abas.update({nome: t for nome, t in abas_disponibilidade.items() if t is not None and len(t)})
    hi = res.hidrologia
    if hi:
        abas_hidrologia = {
            "HID_ALINHAMENTO": hi["alinhamento"],
            "HID_FAIXAS_AFLUENCIA": hi.get("faixas_mensal"),
            "HID_FAIXAS_ANUAL": hi.get("faixas_anual"),
            "HID_HORAS_EVT": hi.get("faixas"),
            "HID_MENSAL": hi.get("mensal"),
            "HID_ANUAL": hi.get("anual"),
            "HID_PERFIL_HORA_DO_DIA": hi.get("perfil"),
            "HID_AUSENCIAS": hi["ausencias"],
            "HID_AUDITORIA": hi["auditoria"],
        }
        abas.update({nome: t for nome, t in abas_hidrologia.items() if t is not None and len(t)})
    ge = res.geracao_oficial
    if ge:
        abas_geracao = {
            "GER_CONFERENCIA": pd.DataFrame([ge["conferencia"]]),
            "GER_MENSAL": ge["mensal"],
            "GER_ANUAL": ge["anual"],
            "GER_DIVERGENCIAS": ge["divergencias"],
            "GER_AUSENCIAS": ge["ausencias"],
            "GER_AUDITORIA": ge["auditoria"],
        }
        abas.update({nome: t for nome, t in abas_geracao.items() if t is not None and len(t)})
    if res.cadastro:
        abas["CAD_FICHA"] = pd.DataFrame([res.cadastro["ficha"]])
        if len(res.cadastro.get("auditoria", [])):
            abas["CAD_AUDITORIA"] = res.cadastro["auditoria"]
    registro_dicionarios = res.dicionarios.get("registro")
    if registro_dicionarios is not None and len(registro_dicionarios):
        abas["DICIONARIOS"] = registro_dicionarios
    # Spec 007 (FR-011): origem e conferências de cada aba, por último
    abas["FONTES"] = tabela_fontes_abas(res, list(abas))
    logger.info("Exportando tabelas analíticas para Excel: %s", dest_xlsx)
    with pd.ExcelWriter(dest_xlsx, engine="openpyxl") as writer:
        for nome, tabela in abas.items():
            tabela.to_excel(writer, sheet_name=nome, index=False)
            planilha = writer.sheets[nome]
            for idx, coluna in enumerate(tabela.columns, start=1):
                letra = planilha.cell(row=1, column=idx).column_letter
                planilha.column_dimensions[letra].width = min(max(len(str(coluna)), 12) + 3, 60)
            planilha.freeze_panes = "A2"

    logger.info("Exportando indicadores anuais para CSV: %s", dest_csv)
    res.indicadores_anuais.to_csv(dest_csv, sep=";", index=False, encoding="utf-8")
    return dest_xlsx, dest_csv


def _tabela_md(cabecalho: List[str], linhas: List[List[str]]) -> List[str]:
    saida = ["| " + " | ".join(cabecalho) + " |", "| " + " | ".join(["---"] * len(cabecalho)) + " |"]
    saida += ["| " + " | ".join(linha) + " |" for linha in linhas]
    return saida


def _fonte_md(res: ResultadosAnalise, chave: str) -> List[str]:
    """Legenda de fonte (spec 007) logo abaixo de uma tabela do Markdown, seguida de linha em branco."""
    return [legenda_fonte(res, chave), ""]


def linhas_tabela_anual(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Cabeçalho e linhas formatadas da tabela de indicadores anuais (usadas no MD e no PDF)."""
    cabecalho = [
        "Ano", "Cobertura", "Disp. média (% Pinst)", "Δ vs ref. GF", "Fator de capacidade", "Geração / GF",
        "EVT (MWh)", "EVT no vert. mínimo", "Índice EVT", "Horas c/ EVT", "Horas parada c/ EVT", "Horas indisp. total",
    ]
    linhas = []
    for r in res.indicadores_anuais.itertuples():
        linhas.append([
            f"{int(r.ano)}{'*' if r.ano_parcial else ''}",
            fmt_pct(r.cobertura_pct),
            fmt_pct(r.disponibilidade_relativa_pct),
            fmt_pp(r.desvio_disponibilidade_referencia_pp),
            fmt_pct(r.fator_capacidade_pct),
            fmt_pct(r.geracao_sobre_garantia_fisica_pct),
            fmt_int(r.evt_mwh),
            fmt_pct(r.participacao_vertimento_minimo_pct),
            fmt_pct(r.indice_evt_pct),
            fmt_int(r.horas_com_evt),
            fmt_int(r.horas_parada_com_evt),
            fmt_int(r.horas_indisponibilidade_total),
        ])
    return cabecalho, linhas


def linhas_tabela_geracao_zero(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Cabeçalho e linhas da tabela de horas com geração zero por mês (usadas no MD e no PDF)."""
    parciais = set(res.cobertura["anos_parciais"])
    cabecalho = ["Ano", *[m.capitalize() for m in MESES_ABREVIADOS], "Total", "Com disp. zero", "Com usina disponível"]
    linhas = []
    for r in res.horas_geracao_zero.to_dict("records"):
        linhas.append(
            [f"{int(r['ano'])}{'*' if int(r['ano']) in parciais else ''}"]
            + [fmt_int(r[m]) for m in MESES_ABREVIADOS]
            + [fmt_int(r["total"]), fmt_int(r["com_disponibilidade_zero"]), fmt_int(r["com_usina_disponivel"])]
        )
    return cabecalho, linhas


def _rotulo_ano(ano: Any, parcial: Any) -> str:
    return f"{int(ano)}{'*' if bool(parcial) else ''}"


def linhas_tabela_ons_disponibilidade(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Disponibilidade declarada (EVT) e DISPF da usina por ano."""
    cabecalho = ["Ano", "Disp. declarada (EVT, % Pinst)", "DISPF (média das UGs)", "Indisp. programada",
                 "Indisp. forçada", "Δ DISPF vs ref. GF"]
    t = res.ons.get("disp_anual", pd.DataFrame())
    linhas = [
        [_rotulo_ano(r.ano, r.ano_parcial), fmt_pct(r.disponibilidade_declarada_pct), fmt_pct(r.dispf_pct),
         fmt_pct(r.indisppf_pct), fmt_pct(r.indispff_pct), fmt_pp(r.desvio_dispf_referencia_pp)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_ons_ug_anual(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Indicadores anuais oficiais por unidade geradora."""
    cabecalho = ["Ano", "UG", "DISPF", "INDISPPF", "INDISPFF", "DMDFF (h)"]
    t = res.ons.get("ug_anual", pd.DataFrame())
    linhas = [
        [_rotulo_ano(r.ano, r.ano_parcial), f"UG{int(r.ug)}", fmt_pct(r.dispf, 2), fmt_pct(r.indisppf, 2),
         fmt_pct(r.indispff, 2), fmt_num(r.dmdff, 1)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_ons_horas(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Horas por estado operativo, por ano e unidade."""
    cabecalho = ["Ano", "UG", "Meses", *INSUMOS_HORAS.keys()]
    t = res.ons.get("horas_anual", pd.DataFrame())
    linhas = [
        [_rotulo_ano(r["ano"], r["ano_parcial"]), f"UG{int(r['ug'])}", fmt_int(r["meses"]),
         *[fmt_int(r[s]) for s in INSUMOS_HORAS]]
        for r in t.to_dict("records")
    ]
    return cabecalho, linhas


def linhas_tabela_ons_decomposicao(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Contribuição de cada unidade e parcela de horas para a TEIFa e a TEIP mais recentes."""
    cabecalho = ["Taxa", "UG", "Parcela", "Horas na janela", "Contribuição (p.p.)", "Participação na taxa"]
    t = res.ons.get("decomposicao")
    if t is None:
        return cabecalho, []
    linhas = [
        [r.taxa, f"UG{int(r.ug)}", f"{r.parcela} ({DESCRICAO_PARCELA[r.parcela]})", fmt_num(r.horas, 1),
         fmt_num(r.contribuicao_pp, 3), fmt_pct(r.participacao_pct)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_ons_divergencias(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Meses-unidade em que o indicador DISPF e as horas do TEIP não conferem."""
    cabecalho = ["Mês", "UG", "HS", "HRD", "HDP (TEIP)", "Programadas pelo DISPF (h)", "HDF (TEIP)",
                 "Forçadas pelo DISPF (h)"]
    t = res.ons.get("divergencias", pd.DataFrame())
    linhas = [
        [fmt_mes_ano(r.mes), f"UG{int(r.ug)}", fmt_num(r.HS, 1), fmt_num(r.HRD, 1), fmt_num(r.HDP, 1),
         fmt_num(r.horas_programadas_indisppf, 1), fmt_num(r.HDF, 1), fmt_num(r.horas_forcadas_indispff, 1)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def texto_taxas_ons(res: ResultadosAnalise) -> str:
    """Resumo da TEIFa e da TEIP mais recentes frente às referências (MD e PDF)."""
    t = res.ons.get("taxa_ultima")
    if not t:
        return ""
    return (
        f"TEIFa e TEIP apuradas pelo ONS em {fmt_mes_ano(t['mes'])} (janela de {JANELA_TAXAS_MESES} meses): "
        f"TEIFa {fmt_pct(t['teifa_pct'], 3)} (referência TEIF {fmt_pct(TEIF_REFERENCIA * 100, 3)}); TEIP "
        f"{fmt_pct(t['teip_pct'], 3)} (referência IP {fmt_pct(IP_REFERENCIA * 100, 3)}); (1 − TEIFa) × (1 − TEIP) = "
        f"{fmt_pct(t['disponibilidade_verificada_pct'], 2)} (referência {fmt_pct(DISPONIBILIDADE_REFERENCIA * 100, 2)})."
    )


def linhas_tabela_programacao_mensal(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Horas paradas com EVT por mês, segundo a programação diária do ONS."""
    cabecalho = ["Mês", "Horas comuns", "Paradas c/ EVT", "c/ programação ≤ 1 MW", "EVT nessas horas (MWh)",
                 "% da EVT do mês", "Paradas c/ programação > 5 MW", "Gerou c/ programação ≤ 1 MW"]
    t = res.programacao.get("mensal", pd.DataFrame())
    linhas = [
        [fmt_mes_ano(r.mes), fmt_int(r.horas_comuns), fmt_int(r.horas_parada_com_evt),
         fmt_int(r.horas_parada_evt_programacao_zero), fmt_num(r.evt_parada_programacao_zero_mwh, 0),
         fmt_pct(r.participacao_evt_programacao_zero_pct), fmt_int(r.horas_desvio_programacao),
         fmt_int(r.horas_gerando_programacao_zero)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_programacao_eventos(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Maiores eventos de usina parada com programação acima do limiar de desvio."""
    cabecalho = ["Início", "Fim", "Duração (h)", "Programação média (MW)", "Disponibilidade média (MW)", "EVT (MWh)"]
    t = res.programacao.get("eventos", pd.DataFrame())
    if not len(t):
        return cabecalho, []
    top = t.sort_values(["duracao_h", "evt_mwh"], ascending=False).head(NUMERO_EVENTOS_RELATORIO)
    linhas = [
        [fmt_data_hora(r.inicio), fmt_data_hora(r.fim), fmt_int(r.duracao_h), fmt_num(r.programacao_media_mw, 1),
         fmt_num(r.disponibilidade_media_mw, 1), fmt_num(r.evt_mwh, 1)]
        for r in top.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_programacao_perfil(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Horas de usina parada com EVT e programação zero por hora do dia."""
    t = res.programacao.get("perfil", pd.DataFrame())
    if not len(t):
        return [], []
    cabecalho = ["Hora", *[f"{int(h)}h" for h in t["hora"]]]
    return cabecalho, [["Horas", *[fmt_int(v) for v in t["horas"]]]]


def secao_programacao_md(res: ResultadosAnalise, secao) -> List[str]:
    """Seção Markdown da programação diária do ONS (vazia se não houver programação)."""
    if not res.programacao:
        return []
    linhas: List[str] = ["", secao("Operação verificada e programação diária do ONS"), ""]
    texto = next((x for t, x in res.achados if t == "Programação diária do ONS"), "")
    if texto:
        linhas += [texto, ""]
    for titulo, funcao, nota in [
        ("Horas paradas com EVT por mês e programação do ONS", linhas_tabela_programacao_mensal,
         "Horas comuns à base de EVT e à programação. Usina parada = geração até 1 MW."),
        ("Horas paradas com EVT e programação de até 1 MW, por hora do dia", linhas_tabela_programacao_perfil, ""),
        (f"Maiores eventos de usina parada com programação acima de {fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 0)} MW",
         linhas_tabela_programacao_eventos, "Lista completa na aba PROG_EVENTOS_DESVIO da planilha."),
    ]:
        cabecalho, corpo = funcao(res)
        if not corpo:
            continue
        linhas += [f"### {titulo}", ""] + _tabela_md(cabecalho, corpo) + [""]
        if nota:
            linhas += [nota, ""]
        linhas += _fonte_md(res, _CHAVE_FONTE_TABELA[funcao])
    ausentes = res.programacao["periodo"]["lista_dias_ausentes"]
    if ausentes:
        linhas += [f"Dias sem arquivo de programação no portal: {fmt_lista(fmt_data(d) for d in ausentes)}.", ""]
    return linhas


_ROTULOS_CLASSES_PARADA: Dict[str, str] = {
    "SINCRONIZADA": "alguma unidade sincronizada",
    "NAO_SINCRONIZADA": "nenhuma unidade sincronizada",
    "COM_EVT": "com EVT",
    "SEM_EVT": "sem EVT",
    SEM_PROGRAMACAO: "fora do período da programação",
    **DESCRICAO_CLASSES,
}


def linhas_tabela_disponibilidade_anual(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Médias anuais de disponibilidade operacional, declarada e sincronizada e de geração (US3)."""
    cabecalho = ["Ano", "Horas", "Operacional (MW)", "Declarada EVT (MW)", "Sincronizada (MW)", "Geração (MW)",
                 "Não sincronizada (GWh)", "Reserva desligada TEIFa/TEIP (GWh)"]
    t = res.disponibilidade.get("anual", pd.DataFrame())
    linhas = [
        [_rotulo_ano(r.periodo, r.ano_parcial), fmt_int(r.horas_comuns), fmt_num(r.disp_operacional_media_mw, 1),
         fmt_num(r.disp_declarada_media_mw, 1), fmt_num(r.disp_sincronizada_media_mw, 1), fmt_num(r.geracao_media_mw, 1),
         fmt_num(r.capacidade_nao_sincronizada_mwh / 1000, 1), fmt_num(r.reserva_desligada_teif_mwh / 1000, 1)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_disponibilidade_paradas(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Horas com a usina parada por sincronização, EVT e classe da programação (US3)."""
    cabecalho = ["Sincronização", "EVT", "Programação do ONS", "Horas", "EVT (MWh)"]
    t = res.disponibilidade.get("classes", pd.DataFrame())
    if t.empty:
        return cabecalho, []
    t = t.sort_values(["sincronizacao", "evt", "horas"], ascending=[True, True, False])
    linhas = [
        [_ROTULOS_CLASSES_PARADA.get(r.sincronizacao, r.sincronizacao), _ROTULOS_CLASSES_PARADA.get(r.evt, r.evt),
         _ROTULOS_CLASSES_PARADA.get(r.classe_programacao, r.classe_programacao), fmt_int(r.horas), fmt_num(r.evt_mwh, 1)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_disponibilidade_divergencias(
    res: ResultadosAnalise, limite: int = NUMERO_EVENTOS_RELATORIO
) -> Tuple[List[str], List[List[str]]]:
    """Maiores períodos de divergência entre a disponibilidade operacional e a declarada (US3)."""
    cabecalho = ["Início", "Fim", "Horas", "Diferença média (MW)", "Diferença máxima (MW)"]
    t = res.disponibilidade.get("divergencias", pd.DataFrame())
    if t.empty:
        return cabecalho, []
    t = t.nlargest(limite, "horas").sort_values("inicio")
    linhas = [[fmt_data_hora(r.inicio), fmt_data_hora(r.fim), fmt_int(r.horas), fmt_num(r.diferenca_media_mw, 2),
               fmt_num(r.diferenca_maxima_mw, 2)] for r in t.itertuples()]
    return cabecalho, linhas


def notas_disponibilidade(res: ResultadosAnalise) -> List[str]:
    """Ressalvas da seção de disponibilidade (MD e PDF)."""
    d = res.disponibilidade
    r = d["resumo"]
    notas = [
        "Fonte: conjunto Disponibilidade por usina do ONS (id ONS MSUHSD, conferido pelo CEG e pelo estado MS), "
        f"{_data_obtencao_texto(d['obtido_em'])}. A disponibilidade operacional é a mesma informação da disponibilidade "
        "declarada da base de EVT; a sincronizada indica a capacidade das unidades ligadas à rede.",
        f"Usina parada = geração até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW; unidade sincronizada = disponibilidade "
        f"sincronizada acima de {fmt_num(LIMIAR_SINCRONIZADA_MW, 0)} MW. Não sincronizada = operacional − sincronizada; "
        "reserva desligada = horas em reserva desligada (HRD) das unidades × potência (parâmetros TEIFa/TEIP), apuração "
        "diferente e por isso só comparada, sem meta.",
    ]
    if r["horas_sinalizadas"]:
        notas.append(f"{fmt_int(r['horas_sinalizadas'])} horas com valores inconsistentes (regras D1 a D4) ficaram fora das "
                     "análises (coluna qualidade de data/processed/uhe_sao_domingos_ons_disponibilidade_horaria.csv).")
    if r["meses_sem_usina"] or r["horas_ausentes"]:
        meses = fmt_lista(fmt_mes_ano(m) for m in r["meses_sem_usina"]) if r["meses_sem_usina"] else "nenhum"
        notas.append(f"Meses sem a usina no conjunto: {meses}; horas ausentes em meses com dados: "
                     f"{fmt_int(r['horas_ausentes'])} (aba DISP_AUSENCIAS). Nada foi interpolado.")
    return notas


def secao_disponibilidade_md(res: ResultadosAnalise, secao) -> List[str]:
    """Seção Markdown da disponibilidade operacional e sincronizada (vazia sem os dados)."""
    if not res.disponibilidade:
        return []
    linhas: List[str] = ["", secao("Disponibilidade operacional e sincronizada (ONS)"), ""]
    texto = dict(res.achados).get("Disponibilidade sincronizada", "")
    if texto:
        linhas += [texto, ""]
    for titulo, funcao, nota in [
        ("Disponibilidade média por ano", linhas_tabela_disponibilidade_anual,
         "Médias nas horas comuns à base de EVT e à disponibilidade do ONS. \\* ano parcial; – = sem apuração TEIFa/TEIP."),
        ("Horas com a usina parada, por sincronização, EVT e programação do ONS", linhas_tabela_disponibilidade_paradas,
         "Classificação hora a hora na aba DISP_HORAS_PARADAS da planilha."),
        ("Maiores períodos de divergência entre a disponibilidade operacional e a declarada",
         linhas_tabela_disponibilidade_divergencias, "Lista completa na aba DISP_DIVERGENCIAS da planilha."),
    ]:
        cabecalho, corpo = funcao(res)
        if not corpo:
            continue
        linhas += [f"### {titulo}", ""] + _tabela_md(cabecalho, corpo) + [""]
        if nota:
            linhas += [nota, ""]
        linhas += _fonte_md(res, _CHAVE_FONTE_TABELA[funcao])
    linhas += [f"- {nota}" for nota in notas_disponibilidade(res)]
    return linhas


_ROTULOS_FAIXAS_CURTOS: Dict[str, str] = {
    ATE_UMA_UNIDADE: f"Até {fmt_num(ENGOLIMENTO_NOMINAL_UG_M3S, 1)} m³/s",
    ENTRE_UMA_E_DUAS_UNIDADES: f"{fmt_num(ENGOLIMENTO_NOMINAL_UG_M3S, 1)} a {fmt_num(ENGOLIMENTO_MAXIMO_USINA_M3S, 0)} m³/s",
    ACIMA_ENGOLIMENTO_USINA: f"Acima de {fmt_num(ENGOLIMENTO_MAXIMO_USINA_M3S, 0)} m³/s",
    SEM_DADO_HIDROLOGICO: "Sem dado",
}


def _tabela_faixas_anual(
    res: ResultadosAnalise, valor: str, formatar: Callable[[float], str]
) -> Tuple[List[str], List[List[str]]]:
    """Linhas por ano e faixa de afluência de ``valor`` (``horas`` ou ``evt_mwh``), com total e parcela que cabia."""
    cabecalho = ["Ano", *[_ROTULOS_FAIXAS_CURTOS[f] for f in FAIXAS_AFLUENCIA], "Total", "Cabia nas turbinas"]
    t = res.hidrologia.get("faixas_anual", pd.DataFrame())
    if t.empty:
        return cabecalho, []
    largo = t.pivot_table(index=["periodo", "ano_parcial"], columns="faixa_afluencia", values=valor,
                          aggfunc="sum", fill_value=0).reset_index()
    linhas = []
    for r in largo.itertuples(index=False):
        valores = {f: getattr(r, f, 0) for f in FAIXAS_AFLUENCIA}
        total = sum(valores.values())
        cabia = valores[ATE_UMA_UNIDADE] + valores[ENTRE_UMA_E_DUAS_UNIDADES]
        linhas.append([_rotulo_ano(r.periodo, r.ano_parcial), *[formatar(valores[f]) for f in FAIXAS_AFLUENCIA],
                       formatar(total), fmt_pct(_pct(cabia, total))])
    return cabecalho, linhas


def linhas_tabela_faixas_afluencia(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Horas com EVT por faixa de afluência e ano (US4)."""
    return _tabela_faixas_anual(res, "horas", lambda v: fmt_int(int(v)))


def linhas_tabela_faixas_afluencia_evt(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """EVT (MWh) por faixa de afluência e ano (US4, FR-023), na mesma estrutura da tabela de horas."""
    return _tabela_faixas_anual(res, "evt_mwh", lambda v: fmt_num(v, 0))


def linhas_tabela_hidrologia_anual(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Afluência, vazões, níveis e volume útil por ano (US4)."""
    cabecalho = ["Ano", "Horas", "Afluência média (m³/s)", "Afluência máx. (m³/s)", "Turbinada (m³/s)", "Vertida (m³/s)",
                 "Nível mont. mín.–máx. (m)", "Volume útil (%)", "Horas acima do engolimento"]
    t = res.hidrologia.get("anual", pd.DataFrame())
    linhas = [
        [_rotulo_ano(r.periodo, r.ano_parcial), fmt_int(r.horas), fmt_num(r.afluencia_media_m3s, 1),
         fmt_num(r.afluencia_maxima_m3s, 0), fmt_num(r.turbinada_media_m3s, 1), fmt_num(r.vertida_media_m3s, 1),
         f"{fmt_num(r.nivel_montante_min_m, 2)}–{fmt_num(r.nivel_montante_max_m, 2)}", fmt_num(r.volume_util_medio_pct, 1),
         fmt_int(r.horas_afluencia_acima_engolimento)]
        for r in t.itertuples()
    ]
    return cabecalho, linhas


def linhas_tabela_perfil_hidrologico(res: ResultadosAnalise, passo: int = 3) -> Tuple[List[str], List[List[str]]]:
    """Vazões e nível médios em horas selecionadas do dia, por grupo de dias (US4)."""
    cabecalho = ["Hora", "Turbinada c/ parada (m³/s)", "Vertida c/ parada (m³/s)", "Nível c/ parada (m)",
                 "Turbinada demais (m³/s)", "Vertida demais (m³/s)", "Nível demais (m)"]
    p = res.hidrologia.get("perfil", pd.DataFrame())
    if p.empty:
        return cabecalho, []
    com = p[p["grupo_dias"] == COM_PARADA_EVT].set_index("hora")
    demais = p[p["grupo_dias"] == DEMAIS_DIAS].set_index("hora")
    linhas = []
    for hora in range(0, 24, passo):
        def _v(t: pd.DataFrame, coluna: str, casas: int) -> str:
            return fmt_num(t.loc[hora, coluna], casas) if hora in t.index else "–"
        linhas.append([f"{hora}h", _v(com, "turbinada_media_m3s", 1), _v(com, "vertida_media_m3s", 1),
                       _v(com, "nivel_montante_medio_m", 2), _v(demais, "turbinada_media_m3s", 1),
                       _v(demais, "vertida_media_m3s", 1), _v(demais, "nivel_montante_medio_m", 2)])
    return cabecalho, linhas


def notas_hidrologia(res: ResultadosAnalise) -> List[str]:
    """Ressalvas da seção hidrológica (MD e PDF)."""
    h = res.hidrologia
    r = h["resumo"]
    notas = [
        f"Fonte: conjunto Dados hidrológicos horários do ONS (cod_usina {COD_USINA_ONS}, conferido pelo nome e pelo código "
        f"{ID_RESERVATORIO_ONS} do reservatório), {_data_obtencao_texto(h['obtido_em'])}. Os dados são informados pelos "
        "agentes e não são consistidos pelo ONS; valores fora da faixa física (vazão negativa, volume útil fora de 0 a 100%) "
        "são sinalizados e excluídos só no campo afetado, sem correção, e campos vazios não são tratados como zero.",
        "O conjunto marca o fim da hora (a última hora do dia aparece às 23:59); a série foi convertida para a hora de "
        f"início, como a base de EVT, e {_texto_alinhamento(h['alinhamento'])}.",
        f"Faixas: até {fmt_num(ENGOLIMENTO_NOMINAL_UG_M3S, 1)} m³/s, a afluência cabia em uma unidade; até "
        f"{fmt_num(ENGOLIMENTO_MAXIMO_USINA_M3S, 1)} m³/s, nas duas; acima disso, parte do vertimento era inevitável. "
        "A EVT de cada hora é a parcela turbinável informada na base de EVT.",
        "O volume útil é apresentado como informado; ele varia entre os anos sem variação correspondente do nível de "
        "montante, por isso o comportamento do reservatório é descrito pelo nível.",
    ]
    if r["horas_sinalizadas"]:
        descricao = {"H1": "vazão negativa", "H2": "volume útil fora de 0 a 100%", "H3": "valor não numérico",
                     "H4": "nível de montante ou de jusante muito afastado da mediana da série"}
        partes = []
        for regra, info in r.get("sinalizadas_por_regra", {}).items():
            if info["horas"]:
                anos = fmt_lista(f"{ano}: {fmt_int(n)} h" for ano, n in info["anos"].items())
                partes.append(f"{regra} ({descricao[regra]}) em {fmt_int(info['horas'])} horas ({anos})")
        notas.append("Sinalizações (coluna qualidade de data/processed/uhe_sao_domingos_ons_hidrologia_horaria.csv): "
                     + "; ".join(partes) + ".")
    pico = r.get("pico_afluencia")
    if pico and pico["defluencia_m3s"] == pico["defluencia_m3s"] and pico["afluencia_m3s"] > 2 * ENGOLIMENTO_MAXIMO_USINA_M3S:
        notas.append(
            f"A afluência horária tem picos isolados: a maior, {fmt_num(pico['afluencia_m3s'], 0)} m³/s em "
            f"{fmt_data_hora(pico['instante'])}, ocorreu com defluência de {fmt_num(pico['defluencia_m3s'], 0)} m³/s. Picos "
            "assim e as afluências negativas são típicos de afluência calculada por balanço hídrico com oscilações do "
            "nível; a afluência máxima anual pode refletir esses picos. A classificação por faixa usa o valor de cada hora."
        )
    if r["meses_sem_usina"] or r["horas_ausentes"]:
        meses = fmt_lista(fmt_mes_ano(m) for m in r["meses_sem_usina"]) if r["meses_sem_usina"] else "nenhum"
        notas.append(f"Meses sem a usina no conjunto: {meses}; horas ausentes em meses com dados: "
                     f"{fmt_int(r['horas_ausentes'])} (aba HID_AUSENCIAS). Nada foi interpolado.")
    return notas


def secao_hidrologia_md(res: ResultadosAnalise, secao) -> List[str]:
    """Seção Markdown de afluência, vertimento e nível do reservatório (vazia sem os dados)."""
    if not res.hidrologia:
        return []
    linhas: List[str] = ["", secao("Afluência, vertimento e nível do reservatório (ONS)"), ""]
    texto = dict(res.achados).get("Afluência e vertimento", "")
    if texto:
        linhas += [texto, ""]
    if res.hidrologia["publicado"]:
        for titulo, funcao, nota in [
            ("Horas com EVT por faixa de afluência", linhas_tabela_faixas_afluencia,
             "Cabia nas turbinas = afluência até o engolimento máximo da usina. \\* ano parcial. Classificação hora a hora "
             "na aba HID_HORAS_EVT da planilha."),
            ("EVT por faixa de afluência (MWh)", linhas_tabela_faixas_afluencia_evt,
             "Energia vertida turbinável das horas de cada faixa. Cabia nas turbinas = parcela da EVT com afluência até o "
             "engolimento máximo da usina. \\* ano parcial. Por mês na aba HID_FAIXAS_AFLUENCIA e por ano na aba "
             "HID_FAIXAS_ANUAL da planilha."),
            ("Afluência, vazões, nível e volume útil por ano", linhas_tabela_hidrologia_anual,
             "Médias sem os valores sinalizados, que saem só do campo afetado (a hora continua nos demais campos). "
             "\\* ano parcial."),
            ("Vazões e nível de montante médios por hora do dia", linhas_tabela_perfil_hidrologico,
             "\"c/ parada\" = dias com ao menos uma hora de parada com EVT; \"demais\" = outros dias. Perfil completo na "
             "aba HID_PERFIL_HORA_DO_DIA."),
        ]:
            cabecalho, corpo = funcao(res)
            if not corpo:
                continue
            linhas += [f"### {titulo}", ""] + _tabela_md(cabecalho, corpo) + [""]
            if nota:
                linhas += [nota, ""]
            linhas += _fonte_md(res, _CHAVE_FONTE_TABELA[funcao])
    linhas += [f"- {nota}" for nota in notas_hidrologia(res)]
    return linhas


def linhas_tabela_geracao_anual(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Energia anual da base de EVT e da série oficial de geração por usina (US5)."""
    cabecalho = ["Ano", "Base de EVT (GWh)", "Geração por usina (GWh)", "Diferença (MWh)", "Horas só na base de EVT",
                 "Horas só na série oficial"]
    t = res.geracao_oficial.get("anual", pd.DataFrame())
    linhas = [[_rotulo_ano(r.ano, r.ano_parcial), fmt_num(r.energia_base_evt_mwh / 1000, 3),
               fmt_num(r.energia_ons_geracao_mwh / 1000, 3), fmt_num(r.diferenca_mwh, 1), fmt_int(r.horas_so_base_evt),
               fmt_int(r.horas_so_ons_geracao)] for r in t.itertuples()]
    return cabecalho, linhas


def secao_geracao_oficial_md(res: ResultadosAnalise, secao) -> List[str]:
    """Seção Markdown da conferência da geração com a série oficial (vazia sem os dados)."""
    if not res.geracao_oficial:
        return []
    linhas: List[str] = ["", secao("Conferência da geração com a série oficial (ONS)"), "", texto_conferencia_geracao(res), ""]
    cabecalho, corpo = linhas_tabela_geracao_anual(res)
    if corpo:
        linhas += _tabela_md(cabecalho, corpo) + ["", "\\* ano parcial. Diferença = série oficial − base de EVT.", ""]
        linhas += _fonte_md(res, "tab_geracao_oficial")
    g = res.geracao_oficial
    linhas.append(f"- Fonte: conjunto Geração por usina do ONS (id ONS {ID_ONS_USINA}, conferido pelo CEG e pelo estado), "
                  f"{_data_obtencao_texto(g['obtido_em'])}; coincidência = diferença de até "
                  f"{fmt_num(g['conferencia']['tolerancia_mw'], 2)} MW na mesma hora.")
    return linhas


def secao_cadastro_md(res: ResultadosAnalise, secao) -> List[str]:
    """Seção Markdown da identificação da usina no cadastro do ONS (vazia sem os dados)."""
    if not res.cadastro:
        return []
    return ["", secao("Identificação da usina no cadastro do ONS"), "", texto_cadastro(res), "",
            "- Fonte: conjunto Modalidade das usinas do ONS (cadastro sem série histórica; as versões anteriores do "
            "arquivo ficam preservadas em data/raw/modalidade_usina/_versoes_anteriores/).", ""]


def secao_indicadores_ons_md(res: ResultadosAnalise, secao) -> List[str]:
    """Seção Markdown dos indicadores oficiais do ONS (vazia se não houver indicadores)."""
    if not res.ons:
        return []
    linhas: List[str] = [secao("Indicadores oficiais do ONS por unidade geradora"), ""]
    texto = next((x for t, x in res.achados if t == "Indicadores oficiais de disponibilidade (ONS)"), "")
    if texto:
        linhas += [texto, ""]
    for titulo, funcao, nota in [
        ("Disponibilidade da usina por ano: declarada (EVT) e DISPF", linhas_tabela_ons_disponibilidade,
         "\\* ano parcial. DISPF = média das unidades ponderada pela potência e pelas horas da base de EVT."),
        ("Indicadores anuais por unidade geradora (base anual do ONS)", linhas_tabela_ons_ug_anual,
         "\\* ano parcial. DMDFF = duração média dos desligamentos forçados."),
        ("Horas por estado operativo, por ano e unidade", linhas_tabela_ons_horas,
         "\\* ano parcial. " + "; ".join(f"{s} = {d}" for s, d in INSUMOS_HORAS.items()) + "."),
        ("Contribuição de cada unidade e parcela para a TEIFa e a TEIP mais recentes", linhas_tabela_ons_decomposicao,
         texto_taxas_ons(res)),
        ("Meses em que o indicador DISPF e as horas do TEIP divergem", linhas_tabela_ons_divergencias,
         f"Diferença superior a {fmt_num(TOLERANCIA_DIVERGENCIA_HORAS, 0)} h entre as horas de indisponibilidade "
         "programada ou forçada do DISPF (percentual × horas do período) e as horas HDP ou HDF do conjunto do TEIP."),
    ]:
        cabecalho, corpo = funcao(res)
        if not corpo:
            continue
        linhas += [f"### {titulo}", ""] + _tabela_md(cabecalho, corpo) + ["", nota, ""]
        linhas += _fonte_md(res, _CHAVE_FONTE_TABELA[funcao])
    texto = next((x for t, x in res.achados if t == "Estados operativos das unidades geradoras (ONS)"), "")
    if texto:
        linhas += [texto, ""]
    return linhas


def gerar_relatorio_md(
    res: ResultadosAnalise,
    figuras: Optional[Dict[str, Path]] = None,
    caminho_md: Optional[Path] = None,
) -> Path:
    """Gera o relatório em Markdown; todo número e frase vêm de ``res``."""
    destino = caminho_md or STATISTICAL_REPORT_MD
    destino.parent.mkdir(parents=True, exist_ok=True)
    c = res.cobertura
    ident = c["identificacao"]
    numero_secao = iter(range(1, 100))

    def secao(titulo: str) -> str:
        return f"## {next(numero_secao)}. {titulo}"

    linhas: List[str] = [
        "# UHE São Domingos — energia vertida turbinável e desempenho operacional (dados ONS)",
        "",
        f"**Período**: {fmt_data_hora(c['inicio'])} a {fmt_data_hora(c['fim'])} "
        f"({fmt_int(c['horas_observadas'])} registros horários)",
        f"**Identificação no ONS**: cod_usina {ident.get('cod_usina', '')} · reservatório {ident.get('nom_reservatorio', '')} "
        f"· rio {ident.get('nom_rio', '')} · bacia {ident.get('nom_bacia', '')} · subsistema {ident.get('nom_subsistema', '')}",
        "**Agentes na série**: " + "; ".join(
            f"{r.nom_agente} ({fmt_data(r.primeiro_registro)} a {fmt_data(r.ultimo_registro)})"
            for r in c["agentes"].itertuples()
        ),
        f"**Usina**: {fmt_num(NOMINAL_INSTALLED_CAPACITY_MW, 1)} MW, {NUMERO_UNIDADES_GERADORAS} unidades de "
        f"{fmt_num(POTENCIA_UNITARIA_MW, 1)} MW ({TIPO_TURBINA}); garantia física {fmt_num(GARANTIA_FISICA_MWMED, 1)} MWmed.",
        cabecalho_fontes(res),
        "",
        secao("Constatações"),
        "",
    ]
    for i, (titulo, texto) in enumerate(res.achados, start=1):
        linhas.append(f"{i}. **{titulo}.** {texto}")
    linhas += secao_cadastro_md(res, secao)
    linhas += ["", secao("Indicadores anuais"), ""]
    cabecalho, corpo = linhas_tabela_anual(res)
    linhas += _tabela_md(cabecalho, corpo)
    linhas += ["", "\\* ano parcial.", ""] + _fonte_md(res, "tab_indicadores_anuais")

    linhas += secao_indicadores_ons_md(res, secao)
    linhas += [secao("Eventos de indisponibilidade total"), ""]
    ev = res.eventos_indisponibilidade_total
    longos = ev[ev["duracao_h"] >= DURACAO_MINIMA_EVENTO_RELATORIO_H] if len(ev) else ev
    if len(longos):
        linhas += _tabela_md(
            ["Início", "Fim", "Duração (h)", "Vazão vertida média (m³/s)"],
            [[fmt_data_hora(r.inicio), fmt_data_hora(r.fim), fmt_int(r.duracao_h), fmt_num(r.vazao_vertida_media_m3s, 1)]
             for r in longos.itertuples()],
        )
        linhas += ["", *_fonte_md(res, "tab_eventos_indisponibilidade")]
    else:
        linhas.append(f"Nenhum evento com pelo menos {DURACAO_MINIMA_EVENTO_RELATORIO_H} h.")

    linhas += ["", secao(f"Maiores eventos de usina parada com EVT (top {NUMERO_EVENTOS_RELATORIO} por EVT)"), ""]
    top = res.eventos_parada_com_evt.nlargest(NUMERO_EVENTOS_RELATORIO, "evt_mwh") if len(res.eventos_parada_com_evt) else res.eventos_parada_com_evt
    if len(top):
        linhas += _tabela_md(
            ["Início", "Fim", "Duração (h)", "Disponibilidade média (MW)", "Vazão vertida média (m³/s)", "EVT (MWh)"],
            [[fmt_data_hora(r.inicio), fmt_data_hora(r.fim), fmt_int(r.duracao_h), fmt_num(r.disponibilidade_media_mw, 1),
              fmt_num(r.vazao_vertida_media_m3s, 1), fmt_num(r.evt_mwh, 1)] for r in top.itertuples()],
        )
        linhas += ["", *_fonte_md(res, "tab_eventos_parada_evt")]
    else:
        linhas.append("Nenhum evento.")

    linhas += secao_programacao_md(res, secao)
    linhas += secao_disponibilidade_md(res, secao)
    linhas += secao_hidrologia_md(res, secao)
    linhas += ["", secao("Horas com geração zero por mês"), ""]
    cab_zero, corpo_zero = linhas_tabela_geracao_zero(res)
    linhas += _tabela_md(cab_zero, corpo_zero)
    linhas += ["", "\\* ano parcial; – = mês sem dados na série.", ""] + _fonte_md(res, "tab_geracao_zero")
    linhas += ["", secao("EVT por nível de geração"), ""]
    linhas += _tabela_md(
        ["Geração na hora", "Horas", "EVT (MWh)", "Participação na EVT", "Disponibilidade média (MW)"],
        [[r.faixa_geracao, fmt_int(r.horas), fmt_num(r.evt_mwh, 1), fmt_pct(r.participacao_evt_pct),
          fmt_num(r.disponibilidade_media_mw, 1)] for r in res.evt_por_faixa_geracao.itertuples()],
    )
    linhas += ["", *_fonte_md(res, "tab_evt_por_nivel")]

    linhas += secao_geracao_oficial_md(res, secao)
    linhas += ["", secao("Registros sinalizados (plausibilidade física)"), ""]
    linhas += _tabela_md(
        ["Regra", "Descrição", "Horas", "Primeira ocorrência", "Última ocorrência"],
        [[r.regra, r.descricao, fmt_int(r.horas),
          fmt_data_hora(r.primeira_ocorrencia) if pd.notna(r.primeira_ocorrencia) else "–",
          fmt_data_hora(r.ultima_ocorrencia) if pd.notna(r.ultima_ocorrencia) else "–"]
         for r in res.resumo_anomalias.itertuples()],
    )
    linhas += ["", *_fonte_md(res, "tab_registros_sinalizados")]

    linhas += ["", secao("Extremos do período (registros sem anomalia)"), ""]
    linhas += _tabela_md(
        ["Grandeza", "Unidade", "Máximo", "Data/hora do máximo", "Mínimo", "Data/hora do mínimo"],
        [[f"`{r.variavel}`", r.unidade, fmt_num(r.maximo_historico, 3), fmt_data_hora(r.data_hora_max),
          fmt_num(r.minimo_historico, 3), fmt_data_hora(r.data_hora_min)] for r in res.extremos.itertuples()],
    )
    linhas += ["", *_fonte_md(res, "tab_extremos")]

    linhas += ["", secao("Notas metodológicas e limitações"), ""]
    linhas += [f"- {nota}" for nota in notas_metodologicas(res)]

    if figuras:
        linhas += ["", secao("Figuras"), ""]
        for chave, caminho in figuras.items():
            linhas.append(f"- `reports/figures/{Path(caminho).name}`")
            linhas.append(f"  {legenda_fonte(res, chave)}")
    linhas.append("")

    with open(destino, mode="w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    logger.info("Relatório em Markdown gravado em: %s", destino)
    return destino


def executar_pipeline_analise(
    input_file: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    figures_dir: Optional[Path] = None,
    dpi: int = DEFAULT_PLOT_DPI,
    generate_plots: bool = True,
    generate_report: bool = True,
) -> int:
    """Orquestra análise, planilhas, gráficos, relatório Markdown e PDF."""
    pasta_saida = output_dir or REPORTS_DIR
    pasta_figuras = figures_dir or REPORTS_FIGURES_DIR
    pasta_saida.mkdir(parents=True, exist_ok=True)
    pasta_figuras.mkdir(parents=True, exist_ok=True)

    logger.info("=== INICIANDO PIPELINE DE ANÁLISE (UHE SÃO DOMINGOS) ===")
    try:
        df = carregar_dados_tratados(input_file)
        indicadores = carregar_indicadores_processados()
        programacao = carregar_programacao_processada()
        disponibilidade = carregar_disponibilidade_processada()
        if disponibilidade is None:
            logger.warning(
                "Disponibilidade horária do ONS não encontrada em data/processed; o relatório sai sem essa seção. "
                "Para incluí-la, execute: python -m src.main --disponibilidade-only"
            )
        hidrologia = carregar_hidrologia_processada()
        if hidrologia is None:
            logger.warning(
                "Dados hidrológicos do ONS não encontrados em data/processed; o relatório sai sem essa seção. "
                "Para incluí-los, execute: python -m src.main --hidrologia-only"
            )
        geracao = carregar_geracao_processada()
        cadastro = carregar_cadastro_processado()
        for nome, valor, opcao in (("Geração por usina do ONS", geracao, "--geracao-only"),
                                   ("Ficha cadastral da usina no ONS", cadastro, "--cadastro-only")):
            if valor is None:
                logger.warning("%s não encontrada em data/processed; o relatório sai sem essa seção. Para incluí-la, "
                               "execute: python -m src.main %s", nome, opcao)
        dicionarios = carregar_registro_dicionarios()
        if dicionarios is None:
            logger.warning(
                "Registro dos dicionários de dados não encontrado em data/processed; a planilha sai sem a aba "
                "DICIONARIOS. Para gerá-lo, execute: python -m src.main --dicionarios-only"
            )
        if programacao is None:
            logger.warning(
                "Programação diária do ONS não encontrada em data/processed; o relatório sai sem essa seção. "
                "Para incluí-la, execute: python -m src.main --programacao-only"
            )
        if indicadores is None:
            logger.warning(
                "Indicadores oficiais do ONS por unidade geradora não encontrados em data/processed; o relatório sai "
                "sem essa seção. Para incluí-los, execute: python -m src.indicadores_ons"
            )
        res = analisar(df, indicadores=indicadores, programacao=programacao, disponibilidade=disponibilidade,
                       hidrologia=hidrologia, geracao=geracao, cadastro=cadastro, dicionarios=dicionarios,
                       auditoria_cadastro=carregar_auditoria_cadastro())

        if generate_plots:
            figuras = gerar_graficos(df, res, pasta_figuras, dpi=dpi)
        else:
            figuras = {k: pasta_figuras / n for k, n in {**NOMES_FIGURAS, **NOMES_FIGURAS_OPCIONAIS}.items()
                       if (pasta_figuras / n).exists()}

        if generate_report:
            exportar_tabelas(res, pasta_saida / STATISTICAL_REPORT_XLSX.name, pasta_saida / STATISTICAL_REPORT_CSV.name)
            gerar_relatorio_md(res, figuras, pasta_saida / STATISTICAL_REPORT_MD.name)

            from src.pdf_generator import PDFReportGenerator

            PDFReportGenerator(res, figuras, pasta_saida / PDF_REPORT_PATH.name).build_pdf()

        logger.info("=== PIPELINE ANALÍTICO CONCLUÍDO COM SUCESSO! ===")
        return 0

    except FileNotFoundError as fnf:
        logger.error("Arquivo de dados não encontrado: %s", fnf)
        return 1
    except Exception as exc:
        logger.exception("Erro durante a execução da análise: %s", exc)
        return 1


def main() -> None:
    """Ponto de entrada da CLI."""
    parser = argparse.ArgumentParser(
        description="Análise estatística, indicadores, gráficos e relatório PDF da UHE São Domingos."
    )
    parser.add_argument("--input-file", type=Path, default=None, help="Arquivo tratado (.parquet, .xlsx ou .csv).")
    parser.add_argument("--output-dir", type=Path, default=REPORTS_DIR, help="Diretório de saída dos relatórios.")
    parser.add_argument("--figures-dir", type=Path, default=REPORTS_FIGURES_DIR, help="Diretório das figuras.")
    parser.add_argument("--dpi", type=int, default=DEFAULT_PLOT_DPI, help="Resolução DPI dos gráficos (padrão: 300).")
    parser.add_argument(
        "--generate-plots",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Gera as figuras (use --no-generate-plots para reaproveitar as existentes).",
    )
    parser.add_argument(
        "--generate-report",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Gera planilha, relatório Markdown e PDF (use --no-generate-report para pular).",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Nível de log.",
    )

    args = parser.parse_args()
    configurar_nivel_log(args.log_level)

    code = executar_pipeline_analise(
        input_file=args.input_file,
        output_dir=args.output_dir,
        figures_dir=args.figures_dir,
        dpi=args.dpi,
        generate_plots=args.generate_plots,
        generate_report=args.generate_report,
    )
    sys.exit(code)


# Chave do mapa de fontes (spec 007) de cada tabela montada nos laços das seções do Markdown
_CHAVE_FONTE_TABELA: Dict[Callable[..., Any], str] = {
    linhas_tabela_programacao_mensal: "tab_programacao_mensal",
    linhas_tabela_programacao_perfil: "tab_programacao_hora",
    linhas_tabela_programacao_eventos: "tab_programacao_eventos",
    linhas_tabela_disponibilidade_anual: "tab_disponibilidade_anual",
    linhas_tabela_disponibilidade_paradas: "tab_disponibilidade_paradas",
    linhas_tabela_disponibilidade_divergencias: "tab_disponibilidade_divergencias",
    linhas_tabela_faixas_afluencia: "tab_faixas_afluencia",
    linhas_tabela_faixas_afluencia_evt: "tab_faixas_afluencia_evt",
    linhas_tabela_hidrologia_anual: "tab_hidrologia_anual",
    linhas_tabela_perfil_hidrologico: "tab_hidrologia_perfil",
    linhas_tabela_ons_disponibilidade: "tab_ons_disp_anual",
    linhas_tabela_ons_ug_anual: "tab_ons_ug_anual",
    linhas_tabela_ons_horas: "tab_ons_horas",
    linhas_tabela_ons_decomposicao: "tab_ons_decomposicao",
    linhas_tabela_ons_divergencias: "tab_ons_divergencias",
}


if __name__ == "__main__":
    main()
