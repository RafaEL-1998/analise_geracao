"""Ponto de entrada CLI e orquestração do pipeline de coleta e filtragem ONS."""

import argparse
import sys
from pathlib import Path

from src.config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    COD_USINA_ONS,
    NOME_RESERVATORIO_REFERENCIA,
    ONS_CKAN_PACKAGE_URL,
    CONSOLIDATED_FILE,
    AUDIT_REPORT_FILE,
    INDICADORES_RAW_DIR,
    PROGRAMACAO_RAW_DIR,
    CONJUNTO_EVT,
    DISPONIBILIDADE_RAW_DIR,
    HIDROLOGIA_RAW_DIR,
    GERACAO_RAW_DIR,
    CADASTRO_RAW_DIR,
)
import pandas as pd

from src.collector import discover_and_download_all
from src.dicionarios_ons import atualizar_dicionarios, executar_dicionarios_ons
from src.filter import filter_all_raw_files
from src.indicadores_ons import executar_indicadores_ons
from src.programacao_ons import executar_programacao_ons
from src.disponibilidade_ons import executar_disponibilidade_ons
from src.hidrologia_ons import executar_hidrologia_ons
from src.geracao_ons import executar_geracao_ons
from src.cadastro_ons import executar_cadastro_ons
from src.consolidator import (
    consolidate_records,
    save_consolidated_records,
    save_audit_report,
)
from src.logger import configurar_nivel_log, setup_logger, ONSError

logger = setup_logger("main")


def parse_arguments(args=None) -> argparse.Namespace:
    """Configura e processa os argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Pipeline de Coleta e Filtragem de Dados do ONS - UHE São Domingos (Spec Kit SDD)"
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--full-pipeline",
        action="store_true",
        help="Executa o pipeline completo: descoberta, download, filtragem e consolidação.",
    )
    mode_group.add_argument(
        "--download-only",
        action="store_true",
        help="Executa apenas a descoberta e download de arquivos CSV para a pasta raw.",
    )
    mode_group.add_argument(
        "--filter-only",
        action="store_true",
        help="Executa apenas a filtragem e consolidação a partir dos arquivos já existentes na pasta raw.",
    )
    mode_group.add_argument(
        "--indicadores-only",
        action="store_true",
        help=(
            "Atualiza apenas os indicadores oficiais do ONS por unidade geradora (DISPF, TEIFa/TEIP e horas por "
            "estado operativo), no período da base de EVT já existente."
        ),
    )
    mode_group.add_argument(
        "--programacao-only",
        action="store_true",
        help=(
            "Atualiza apenas a programação diária do ONS para a usina (spec 004), no período da base de EVT "
            "já existente."
        ),
    )
    mode_group.add_argument(
        "--complementares-only",
        action="store_true",
        help=(
            "Atualiza só as bases complementares do ONS (spec 006) e seus dicionários, no período da base de EVT "
            "existente, sem tocar a base de EVT. Comando recomendado para as bases novas."
        ),
    )
    mode_group.add_argument(
        "--disponibilidade-only",
        action="store_true",
        help="Atualiza só a disponibilidade horária (operacional e sincronizada) do ONS (spec 006, etapa 5).",
    )
    mode_group.add_argument(
        "--hidrologia-only",
        action="store_true",
        help="Atualiza só os dados hidrológicos horários do ONS (spec 006, etapa 6).",
    )
    mode_group.add_argument(
        "--geracao-only",
        action="store_true",
        help="Atualiza só a geração horária oficial (geração por usina do ONS; spec 006, etapa 7).",
    )
    mode_group.add_argument(
        "--cadastro-only",
        action="store_true",
        help="Atualiza só a ficha cadastral da usina no ONS (modalidade das usinas; spec 006, etapa 8).",
    )
    mode_group.add_argument(
        "--dicionarios-only",
        action="store_true",
        help="Obtém apenas os dicionários de dados (PDF e JSON) dos 10 conjuntos do pipeline, sem baixar dados.",
    )
    parser.add_argument(
        "--sem-dicionarios",
        action="store_true",
        help="Não obtém os dicionários de dados nesta execução (uso excepcional; registrado como aviso).",
    )
    parser.add_argument(
        "--sem-geracao",
        action="store_true",
        help="Não baixa nem processa a geração por usina do ONS (etapa 7).",
    )
    parser.add_argument(
        "--sem-cadastro",
        action="store_true",
        help="Não baixa nem processa o cadastro de modalidade das usinas do ONS (etapa 8).",
    )
    parser.add_argument(
        "--sem-hidrologia",
        action="store_true",
        help="Não baixa nem processa os dados hidrológicos horários do ONS (etapa 6).",
    )
    parser.add_argument(
        "--sem-disponibilidade",
        action="store_true",
        help="Não baixa nem processa a disponibilidade horária do ONS (etapa 5).",
    )
    parser.add_argument(
        "--sem-indicadores",
        action="store_true",
        help="Não baixa nem processa os indicadores oficiais do ONS por unidade geradora.",
    )
    parser.add_argument(
        "--sem-programacao",
        action="store_true",
        help="Não baixa nem processa a programação diária do ONS.",
    )

    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DATA_DIR,
        help="Diretório onde os arquivos brutos CSV do ONS são armazenados (padrão: data/raw).",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=PROCESSED_DATA_DIR,
        help="Diretório de saída para a base consolidada e relatório de auditoria (padrão: data/processed).",
    )
    parser.add_argument(
        "--cod-usina",
        type=int,
        default=COD_USINA_ONS,
        help="cod_usina da usina nos arquivos do ONS (padrão: 153).",
    )
    parser.add_argument(
        "--nome-reservatorio",
        type=str,
        default=NOME_RESERVATORIO_REFERENCIA,
        help="Nome do reservatório usado para conferir o cod_usina (padrão: SAO DOMINGOS).",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Força novo download de todos os arquivos mesmo se já existirem localmente.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Nível de detalhamento do log (padrão: INFO).",
    )

    return parser.parse_args(args)


def _etapas_complementares(args: argparse.Namespace):
    """Etapas das bases complementares (spec 006): (rótulo, nome da opção, função, subpasta bruta).

    A lista é montada na hora da chamada para que as funções possam ser substituídas nos testes.
    """
    return [
        ("ETAPA 5: Disponibilidade horária por usina (ONS)", "disponibilidade", executar_disponibilidade_ons,
         DISPONIBILIDADE_RAW_DIR.name),
        ("ETAPA 6: Dados hidrológicos horários (ONS)", "hidrologia", executar_hidrologia_ons,
         HIDROLOGIA_RAW_DIR.name),
        ("ETAPA 7: Geração por usina (ONS)", "geracao", executar_geracao_ons, GERACAO_RAW_DIR.name),
        ("ETAPA 8: Modalidade das usinas, ficha cadastral (ONS)", "cadastro", executar_cadastro_ons,
         CADASTRO_RAW_DIR.name),
    ]


def _executar_complementares(args: argparse.Namespace, periodo, baixar: bool, dicionarios: bool,
                             somente: str = "") -> int:
    """Executa as etapas complementares (ou só ``somente``); para na primeira que não terminar com 0."""
    for rotulo, nome, funcao, subpasta in _etapas_complementares(args):
        if (somente and nome != somente) or (not somente and getattr(args, f"sem_{nome}", False)):
            continue
        logger.info("=== %s ===", rotulo)
        codigo = funcao(
            baixar=baixar,
            force=args.force_download,
            periodo=periodo,
            pasta_raw=args.raw_dir / subpasta,
            pasta_saida=args.processed_dir,
            dicionarios=dicionarios,
        )
        if codigo != 0:
            logger.error("Falha na etapa %s (código %d).", rotulo, codigo)
            return codigo
    return 0


def run_pipeline(args: argparse.Namespace) -> int:
    """Orquestra a execução das etapas do pipeline com base nos argumentos."""
    configurar_nivel_log(args.log_level)
    logger.info("Iniciando pipeline ONS - UHE São Domingos")
    logger.info("Diretório de dados brutos: %s", args.raw_dir)
    logger.info("Diretório de saída: %s", args.processed_dir)

    dicionarios = not args.sem_dicionarios
    if not dicionarios:
        logger.warning("Dicionários de dados não serão obtidos nesta execução (--sem-dicionarios).")
    if args.dicionarios_only:
        logger.info("=== Dicionários de dados dos conjuntos do pipeline ===")
        return executar_dicionarios_ons(pasta_raw=args.raw_dir, pasta_saida=args.processed_dir)
    if args.complementares_only:
        logger.info("=== Bases complementares do ONS (período da base de EVT existente; a EVT não é baixada) ===")
        return _executar_complementares(args, None, True, dicionarios)
    if args.disponibilidade_only:
        return _executar_complementares(args, None, True, dicionarios, somente="disponibilidade")
    if args.hidrologia_only:
        return _executar_complementares(args, None, True, dicionarios, somente="hidrologia")
    if args.geracao_only:
        return _executar_complementares(args, None, True, dicionarios, somente="geracao")
    if args.cadastro_only:
        return _executar_complementares(args, None, True, dicionarios, somente="cadastro")

    # Define comportamento padrão: se nenhum modo específico for passado, executa full-pipeline
    if args.indicadores_only:
        logger.info("=== Indicadores oficiais do ONS por unidade geradora (período da base de EVT existente) ===")
        return executar_indicadores_ons(
            force=args.force_download,
            pasta_raw=args.raw_dir / INDICADORES_RAW_DIR.name,
            pasta_saida=args.processed_dir,
            dicionarios=dicionarios,
        )
    if args.programacao_only:
        logger.info("=== Programação diária do ONS (período da base de EVT existente) ===")
        return executar_programacao_ons(
            force=args.force_download,
            pasta_raw=args.raw_dir / PROGRAMACAO_RAW_DIR.name,
            pasta_saida=args.processed_dir,
            dicionarios=dicionarios,
        )
    do_download = args.full_pipeline or args.download_only or (not args.filter_only)
    do_filter = args.full_pipeline or args.filter_only or (not args.download_only)

    try:
        # Etapa 1: Download
        if do_download:
            logger.info("=== ETAPA 1: Descoberta e Download de Arquivos (User Story 1) ===")
            discover_and_download_all(
                package_url=ONS_CKAN_PACKAGE_URL,
                destination_dir=args.raw_dir,
                force=args.force_download,
            )
            # Dicionário da EVT: obtido a cada coleta, sem baixar de novo os arquivos de dados (spec 006, US2)
            if dicionarios:
                atualizar_dicionarios([CONJUNTO_EVT], raiz_raw=args.raw_dir, pasta_saida=args.processed_dir)

        # Etapa 2: Filtragem e Consolidação
        if do_filter:
            logger.info("=== ETAPA 2: Filtragem Exaustiva e Consolidação (User Stories 2 e 3) ===")
            raw_records, audit_records = filter_all_raw_files(
                raw_dir=args.raw_dir,
                cod_usina=args.cod_usina,
                nome_reservatorio=args.nome_reservatorio,
            )

            consolidated = consolidate_records(raw_records)
            output_consolidated = args.processed_dir / CONSOLIDATED_FILE.name
            output_audit = args.processed_dir / AUDIT_REPORT_FILE.name

            save_consolidated_records(consolidated, output_path=output_consolidated)
            save_audit_report(audit_records, output_path=output_audit)

            logger.info("=== RESUMO FINAL ===")
            logger.info("Arquivos inspecionados: %d", len(audit_records))
            falhas = [a.nome_arquivo for a in audit_records if a.status_processamento == "FALHA"]
            if falhas:
                logger.error("Arquivos com falha de leitura: %s", falhas)
            divergencias = sum(a.registros_codigo_sem_nome + a.registros_nome_sem_codigo for a in audit_records)
            if divergencias:
                logger.warning("Linhas com cod_usina ou nome divergentes (não extraídas): %d", divergencias)
            logger.info("Total de registros consolidados: %d", len(consolidated))
            logger.info("Base consolidada gerada: %s", output_consolidated)
            logger.info("Relatório de auditoria gerado: %s", output_audit)
            if falhas:
                logger.error("Pipeline concluído com arquivos não lidos; a base consolidada está incompleta.")
                return 2

            # Etapa 3: indicadores oficiais por unidade geradora, no período da base recém-consolidada
            if consolidated and not args.sem_indicadores:
                logger.info("=== ETAPA 3: Indicadores oficiais do ONS por unidade geradora ===")
                instantes = pd.to_datetime([r.din_instante for r in consolidated])
                codigo = executar_indicadores_ons(
                    baixar=do_download,
                    force=args.force_download,
                    periodo=(instantes.min(), instantes.max()),
                    pasta_raw=args.raw_dir / INDICADORES_RAW_DIR.name,
                    pasta_saida=args.processed_dir,
                    dicionarios=dicionarios,
                )
                if codigo != 0:
                    logger.error("Falha na etapa de indicadores oficiais (código %d).", codigo)
                    return codigo

            # Etapa 4: programação diária do ONS, no mesmo período (spec 004)
            if consolidated and not args.sem_programacao:
                logger.info("=== ETAPA 4: Programação diária do ONS ===")
                instantes = pd.to_datetime([r.din_instante for r in consolidated])
                codigo = executar_programacao_ons(
                    baixar=do_download,
                    force=args.force_download,
                    periodo=(instantes.min(), instantes.max()),
                    pasta_raw=args.raw_dir / PROGRAMACAO_RAW_DIR.name,
                    pasta_saida=args.processed_dir,
                    dicionarios=dicionarios,
                )
                if codigo != 0:
                    logger.error("Falha na etapa de programação diária (código %d).", codigo)
                    return codigo

            # Etapas 5 a 8: bases complementares do ONS, no mesmo período (spec 006)
            if consolidated:
                instantes = pd.to_datetime([r.din_instante for r in consolidated])
                codigo = _executar_complementares(args, (instantes.min(), instantes.max()), do_download, dicionarios)
                if codigo != 0:
                    return codigo

        logger.info("Pipeline concluído com sucesso!")
        return 0

    except ONSError as e:
        logger.error("Erro no pipeline ONS: %s", e)
        return 1
    except KeyboardInterrupt:
        logger.warning("Execução interrompida pelo usuário.")
        return 1
    except Exception as e:
        logger.exception("Erro fatal não esperado: %s", e)
        return 1


def main():
    """Função de entrada do módulo CLI."""
    args = parse_arguments()
    exit_code = run_pipeline(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
