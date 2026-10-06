"""Módulo de logging estruturado e exceções do pipeline."""

import logging
import sys
from typing import Optional, Tuple


class ONSError(Exception):
    """Exceção base para erros do pipeline ONS."""
    pass


class DownloadError(ONSError):
    """Erro durante o download de arquivos do ONS."""
    pass


class FilterError(ONSError):
    """Erro durante o parsing ou filtragem de arquivos CSV."""
    pass


class DataValidationError(ONSError):
    """Erro de validação ou consistência dos dados."""
    pass


# Todos os loggers do pipeline. O nível escolhido em qualquer ponto de entrada vale para todos
# (constituição, princípio V).
LOGGERS_PIPELINE: Tuple[str, ...] = (
    "main",
    "collector",
    "filter",
    "consolidator",
    "indicadores_ons",
    "programacao_ons",
    "processor",
    "validator",
    "analyzer",
    "uhe_sao_domingos.pdf_generator",
    "persistencia",
    "dicionarios_ons",
    "conjuntos_ons",
    "disponibilidade_ons",
    "hidrologia_ons",
    "geracao_ons",
    "cadastro_ons",
    "fontes_relatorio",
    "estrutura_relatorio",
)
NIVEIS_LOG: Tuple[str, ...] = ("DEBUG", "INFO", "WARNING", "ERROR")


def configurar_nivel_log(nivel: str) -> None:
    """Aplica o nível de log a todos os loggers do pipeline."""
    numerico = getattr(logging, str(nivel).upper(), None)
    if not isinstance(numerico, int):
        raise ValueError(f"Nível de log inválido: {nivel}")
    for nome in LOGGERS_PIPELINE:
        logging.getLogger(nome).setLevel(numerico)


def setup_logger(name: str = "ons_pipeline", level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Configura e retorna um logger formatado."""
    logger = logging.getLogger(name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Evita duplicação de handlers se chamado múltiplas vezes
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
