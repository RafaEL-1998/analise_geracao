"""Tratamento da base de EVT: tipagem numérica, validação física (R1 a R9), sinalização de anomalias e exportação.

As métricas operacionais são convertidas para float64 sem preencher valores ausentes (um dado ausente continua
ausente). A base tratada é exportada em Excel (.xlsx), Parquet (.parquet) e CSV, com as colunas de sinalização das
regras R6 a R9; a validação vai para ``validacao_fisica.csv`` e ``.md``. Violação da R1 (valor negativo) é erro.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from src.comum import caminhos
from src.comum.logger import setup_logger
from src.comum.persistencia import gravar_csv, gravar_parquet, gravar_planilha
from src.comum.regras import OPERATIONAL_METRIC_COLUMNS
from src.tratamento.validacao import (
    carregar_base_consolidada,
    carregar_dicionario_dados,
    gerar_relatorio_validacao_csv,
    gerar_relatorio_validacao_md,
    sinalizar_anomalias,
    validar_regras_fisicas,
    verificar_colunas_no_dicionario,
)

logger = setup_logger("tratamento")


# Caracteres que o Excel não aceita em nome de aba e o tamanho máximo do nome
CARACTERES_PROIBIDOS_ABA = "\\/?*:[]"
TAMANHO_MAXIMO_ABA = 31


def nome_aba(perfil: Any) -> str:
    """Aba da planilha tratada: o nome da usina sem acentos, em maiúsculas, com "_" no lugar dos espaços e dos
    caracteres que o Excel não aceita em nome de aba, cortado em 31 caracteres."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", perfil.usina.nome) if not unicodedata.combining(c))
    nome = "_".join(sem_acento.upper().split())
    return "".join("_" if c in CARACTERES_PROIBIDOS_ABA else c for c in nome)[:TAMANHO_MAXIMO_ABA]


def padronizar_tipagem_numerica(df: pd.DataFrame) -> pd.DataFrame:
    """Converte as colunas métricas para float64 e os campos de identificação para seus tipos.

    Trata vírgula decimal e espaços. Valores não numéricos ou ausentes permanecem NaN e são
    contabilizados em log; timestamps inválidos interrompem o processamento.
    """
    logger.info("Iniciando padronização e coerção estrita de tipos numéricos...")
    df_tratado = df.copy()

    # 1. Trata colunas de identificação e texto
    colunas_texto = [
        "id_subsistema",
        "nom_subsistema",
        "nom_bacia",
        "nom_rio",
        "nom_agente",
        "nom_reservatorio",
        "arquivo_origem",
        "tipo_match",
    ]
    for col in colunas_texto:
        if col in df_tratado.columns:
            df_tratado[col] = df_tratado[col].astype(str).str.strip()

    # 2. Trata cod_usina (inteiro anulável: um código inválido não vira 0)
    if "cod_usina" in df_tratado.columns:
        df_tratado["cod_usina"] = pd.to_numeric(df_tratado["cod_usina"], errors="coerce").astype("Int64")
        invalidos = int(df_tratado["cod_usina"].isna().sum())
        if invalidos:
            logger.warning("cod_usina inválido em %d registros.", invalidos)

    # 3. Trata din_instante como datetime naive (horário legal publicado pelo ONS)
    if "din_instante" in df_tratado.columns:
        instantes = pd.to_datetime(df_tratado["din_instante"], errors="coerce")
        invalidos = int(instantes.isna().sum())
        if invalidos:
            raise ValueError(f"{invalidos} registros com din_instante inválido; verifique a base consolidada.")
        df_tratado["din_instante"] = instantes

    # 4. Trata as 10 colunas operacionais contínuas
    for col in OPERATIONAL_METRIC_COLUMNS:
        if col in df_tratado.columns:
            # Se a coluna for string com vírgula regional, substitui por ponto
            if df_tratado[col].dtype == object or isinstance(df_tratado[col].dtype, pd.StringDtype):
                df_tratado[col] = df_tratado[col].astype(str).str.replace(",", ".", regex=False).str.strip()
            df_tratado[col] = pd.to_numeric(df_tratado[col], errors="coerce").astype("float64")
            ausentes = int(df_tratado[col].isna().sum())
            if ausentes:
                logger.warning("Coluna %s: %d valores ausentes ou não numéricos mantidos como NaN.", col, ausentes)

    logger.info("Padronização concluída: %d colunas métricas tipadas como float64.", len(OPERATIONAL_METRIC_COLUMNS))
    return df_tratado


def _formatar_planilha_tratada(colunas, aba: str):
    """Largura das colunas pelo cabeçalho e painel congelado na primeira linha."""

    def formatar(writer) -> None:
        worksheet = writer.sheets[aba]
        for col_idx, col_name in enumerate(colunas, start=1):
            max_len = max(len(str(col_name)), 12)
            col_letter = worksheet.cell(row=1, column=col_idx).column_letter
            worksheet.column_dimensions[col_letter].width = max_len + 3
        worksheet.freeze_panes = "A2"

    return formatar


def exportar_excel(df: pd.DataFrame, caminho_saida: Path, aba: str) -> Path:
    """Exporta a base tratada para planilha Excel nativa (.xlsx) via openpyxl."""
    destino = Path(caminho_saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Exportando base tratada para Excel (.xlsx) em: %s", destino)
    gravar_planilha({aba: df}, destino, formatar=_formatar_planilha_tratada(df.columns, aba))
    return destino


def exportar_parquet(df: pd.DataFrame, caminho_saida: Path) -> Path:
    """Exporta a base tratada para Apache Parquet (.parquet) com tipos DOUBLE e TIMESTAMP."""
    destino = Path(caminho_saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Exportando base tratada para Parquet (.parquet) em: %s", destino)
    gravar_parquet(df, destino)
    return destino


def exportar_csv(df: pd.DataFrame, caminho_saida: Path) -> Path:
    """Exporta a base tratada para CSV com delimitador ';', ponto decimal e precisão integral."""
    destino = Path(caminho_saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Exportando base tratada para CSV (.csv) em: %s", destino)
    gravar_csv(df, destino, sep=";", index=False, encoding="utf-8", date_format="%Y-%m-%d %H:%M:%S")
    return destino


def tratar_evt(perfil: Any, entrada: Path, arquivos: Dict[str, Path]) -> Tuple[int, List[Path], Dict[str, Any]]:
    """Trata a EVT extraída pela Coleta e grava a base tratada e a validação física.

    ``arquivos`` traz os destinos ``evt_parquet``, ``evt_csv``, ``evt_xlsx``, ``validacao_csv`` e ``validacao_md``.
    Devolve o código (0 sucesso; 1 com violação da R1, valor negativo publicado), os arquivos gravados e o resumo
    (período, registros, violações por regra, registros sinalizados e valores ausentes nas grandezas). O dicionário
    de dados é a cópia gravada pela Coleta ao lado da ``entrada``, nunca o de ``data/raw/`` (spec 006, decisão R22).
    """
    dicionario = Path(entrada).parent / caminhos.ARQUIVOS_COLETA["dicionario_evt"]
    df_bruto = carregar_base_consolidada(entrada)
    verificar_colunas_no_dicionario(OPERATIONAL_METRIC_COLUMNS, carregar_dicionario_dados(dicionario))
    df_tratado = padronizar_tipagem_numerica(df_bruto)
    resumo: Dict[str, Any] = {
        "inicio": df_tratado["din_instante"].min(),
        "fim": df_tratado["din_instante"].max(),
        "registros": len(df_tratado),
        "valores_ausentes": int(df_tratado[OPERATIONAL_METRIC_COLUMNS].isna().sum().sum()),
    }

    logger.info("Executando validação das regras R1 a R9...")
    df_res_validacao, resultados = validar_regras_fisicas(df_tratado, perfil)
    for r in resultados:
        logger.info("%s %s: %d violações (%s)", r.codigo_regra, r.nome_regra, r.violacoes, r.status)
    resumo["violacoes"] = {r.codigo_regra: int(r.violacoes) for r in resultados}
    if any(r.codigo_regra == "R1" and r.violacoes > 0 for r in resultados):
        logger.error("Violação da R1 (valores negativos na EVT) em %d registros: a base não é tratada.",
                     resumo["violacoes"]["R1"])
        return 1, [], resumo

    df_tratado = sinalizar_anomalias(df_tratado, perfil)
    resumo["sinalizados"] = int((df_tratado["qualidade_registro"] != "OK").sum())
    gerar_relatorio_validacao_md(df_res_validacao, perfil, arquivos["validacao_md"], df_tratado,
                                 dicionario=dicionario)
    gerar_relatorio_validacao_csv(df_res_validacao, arquivos["validacao_csv"])
    exportar_excel(df_tratado, arquivos["evt_xlsx"], nome_aba(perfil))
    exportar_parquet(df_tratado, arquivos["evt_parquet"])
    exportar_csv(df_tratado, arquivos["evt_csv"])
    logger.info("Base de EVT tratada: %d registros.", len(df_tratado))
    return 0, [arquivos[c] for c in ("evt_parquet", "evt_csv", "evt_xlsx", "validacao_csv", "validacao_md")], resumo
