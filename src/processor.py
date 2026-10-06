"""Módulo de processamento, padronização de tipos numéricos e exportação multi-formato.

As métricas operacionais são convertidas para float64 sem preencher valores ausentes
(um dado ausente continua ausente) e a base é exportada em Excel (.xlsx), Parquet
(.parquet) e CSV, acompanhada das colunas de sinalização de anomalias (regras R6 a R9).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

from src.config import (
    CONSOLIDATED_FILE,
    OPERATIONAL_METRIC_COLUMNS,
    PHYSICAL_AUDIT_REPORT_CSV,
    PHYSICAL_AUDIT_REPORT_MD,
    PROCESSED_DATA_DIR,
    TREATED_FILE_CSV,
    TREATED_FILE_PARQUET,
    TREATED_FILE_XLSX,
)
from src.logger import configurar_nivel_log
from src.persistencia import gravar_csv, gravar_parquet, gravar_planilha
from src.validator import (
    carregar_base_consolidada,
    carregar_dicionario_dados,
    gerar_relatorio_validacao_csv,
    gerar_relatorio_validacao_md,
    sinalizar_anomalias,
    validar_regras_fisicas,
    verificar_colunas_no_dicionario,
)

logger = logging.getLogger("processor")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [processor] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


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


def _formatar_planilha_tratada(colunas):
    """Largura das colunas pelo cabeçalho e painel congelado na primeira linha."""

    def formatar(writer) -> None:
        worksheet = writer.sheets["UHE_SAO_DOMINGOS"]
        for col_idx, col_name in enumerate(colunas, start=1):
            max_len = max(len(str(col_name)), 12)
            col_letter = worksheet.cell(row=1, column=col_idx).column_letter
            worksheet.column_dimensions[col_letter].width = max_len + 3
        worksheet.freeze_panes = "A2"

    return formatar


def exportar_excel(
    df: pd.DataFrame,
    caminho_saida: Optional[Path] = None,
) -> Path:
    """Exporta o dataset tratado para planilha Excel nativa (.xlsx) via openpyxl."""
    destino = caminho_saida or TREATED_FILE_XLSX
    destino.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Exportando base tratada para Excel (.xlsx) em: %s", destino)

    gravar_planilha({"UHE_SAO_DOMINGOS": df}, destino, formatar=_formatar_planilha_tratada(df.columns))

    logger.info("Exportação para Excel (.xlsx) concluída com sucesso.")
    return destino


def exportar_parquet(
    df: pd.DataFrame,
    caminho_saida: Optional[Path] = None,
) -> Path:
    """Exporta o dataset tratado para Apache Parquet (.parquet) com tipos DOUBLE e TIMESTAMP."""
    destino = caminho_saida or TREATED_FILE_PARQUET
    destino.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Exportando base tratada para Parquet (.parquet) em: %s", destino)

    gravar_parquet(df, destino)
    logger.info("Exportação para Parquet (.parquet) concluída com sucesso.")
    return destino


def exportar_csv(
    df: pd.DataFrame,
    caminho_saida: Optional[Path] = None,
) -> Path:
    """Exporta o dataset tratado para CSV com delimitador ';', ponto decimal e precisão integral."""
    destino = caminho_saida or TREATED_FILE_CSV
    destino.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Exportando base tratada para CSV (.csv) em: %s", destino)

    gravar_csv(df, destino, sep=";", index=False, encoding="utf-8", date_format="%Y-%m-%d %H:%M:%S")
    logger.info("Exportação para CSV (.csv) concluída com sucesso.")
    return destino


def executar_pipeline_tratamento(
    input_file: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    export_formats: Optional[List[str]] = None,
    validate_physics: bool = True,
    generate_report: bool = True,
) -> int:
    """Executa tratamento, validação, sinalização de anomalias e exportação multi-formato.

    Retorna o código de saída (0 sucesso, 1 erro, 3 valores negativos detectados).
    """
    caminho_entrada = input_file or CONSOLIDATED_FILE
    diretorio_saida = output_dir or PROCESSED_DATA_DIR
    diretorio_saida.mkdir(parents=True, exist_ok=True)

    formatos = set(f.strip().lower() for f in (export_formats or ["xlsx", "parquet", "csv"]))

    logger.info("=== INICIANDO PIPELINE DE TRATAMENTO DE DADOS (UHE SÃO DOMINGOS) ===")
    logger.info("Entrada: %s", caminho_entrada)
    logger.info("Destino: %s", diretorio_saida)
    logger.info("Formatos selecionados: %s", formatos)

    try:
        # 1. Carregamento da base consolidada e conferência com o dicionário do ONS
        df_bruto = carregar_base_consolidada(caminho_entrada)
        verificar_colunas_no_dicionario(OPERATIONAL_METRIC_COLUMNS, carregar_dicionario_dados())

        # 2. Padronização e tipagem numérica
        df_tratado = padronizar_tipagem_numerica(df_bruto)

        # 3. Validação das regras (se solicitada)
        if validate_physics:
            logger.info("Executando validação das regras R1 a R9...")
            df_res_validacao, resultados = validar_regras_fisicas(df_tratado)
            for r in resultados:
                logger.info("%s %s: %d violações (%s)", r.codigo_regra, r.nome_regra, r.violacoes, r.status)

            violacoes_criticas = [r for r in resultados if r.codigo_regra == "R1" and r.violacoes > 0]
            if violacoes_criticas:
                logger.error("ALERTA CRÍTICO: Violações de não-negatividade detectadas!")
                return 3

        # 4. Sinalização de anomalias de plausibilidade (colunas exportadas junto com a base)
        df_tratado = sinalizar_anomalias(df_tratado)

        # 5. Relatórios de validação
        if validate_physics and generate_report:
            gerar_relatorio_validacao_md(df_res_validacao, df_tratado, diretorio_saida / PHYSICAL_AUDIT_REPORT_MD.name)
            gerar_relatorio_validacao_csv(df_res_validacao, diretorio_saida / PHYSICAL_AUDIT_REPORT_CSV.name)

        # 6. Exportação multi-formato
        if "xlsx" in formatos:
            exportar_excel(df_tratado, diretorio_saida / TREATED_FILE_XLSX.name)
        if "parquet" in formatos:
            exportar_parquet(df_tratado, diretorio_saida / TREATED_FILE_PARQUET.name)
        if "csv" in formatos:
            exportar_csv(df_tratado, diretorio_saida / TREATED_FILE_CSV.name)

        logger.info("=== PIPELINE DE TRATAMENTO CONCLUÍDO COM SUCESSO! ===")
        return 0

    except FileNotFoundError as fnf_err:
        logger.error("Arquivo não encontrado: %s", fnf_err)
        return 1
    except Exception as exc:
        logger.exception("Erro durante o processamento dos dados: %s", exc)
        return 1


def main() -> None:
    """Ponto de entrada da CLI."""
    parser = argparse.ArgumentParser(
        description="Pipeline de tratamento, validação física e exportação multi-formato para a UHE São Domingos."
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        default=CONSOLIDATED_FILE,
        help="Caminho do arquivo consolidado de entrada.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROCESSED_DATA_DIR,
        help="Diretório de saída para os arquivos tratados e relatórios.",
    )
    parser.add_argument(
        "--export-formats",
        type=str,
        default="xlsx,parquet,csv",
        help="Formatos de exportação separados por vírgula (ex: xlsx,parquet,csv).",
    )
    parser.add_argument(
        "--validate-physics",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Executa as regras de validação R1 a R9 (use --no-validate-physics para pular).",
    )
    parser.add_argument(
        "--generate-report",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Gera os relatórios de validação em Markdown e CSV (use --no-generate-report para pular).",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Nível de detalhamento do log.",
    )

    args = parser.parse_args()

    configurar_nivel_log(args.log_level)
    formatos = [f.strip() for f in args.export_formats.split(",") if f.strip()]

    exit_code = executar_pipeline_tratamento(
        input_file=args.input_file,
        output_dir=args.output_dir,
        export_formats=formatos,
        validate_physics=args.validate_physics,
        generate_report=args.generate_report,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
