"""Módulo de filtragem em streaming dos dados CSV do ONS (User Story 2).

Um registro é extraído quando o cod_usina e o nome do reservatório conferem. Linhas em
que apenas um dos dois confere não são extraídas, mas são contadas no relatório de
auditoria para que uma mudança de código ou de nome no ONS fique visível.
"""

import csv
import unicodedata
from pathlib import Path
from typing import List, Tuple, Optional

from src.config import (
    RAW_DATA_DIR,
    COD_USINA_ONS,
    NOME_RESERVATORIO_REFERENCIA,
)
from src.models import RegistroEnergiaVertida, AuditoriaArquivo
from src.logger import setup_logger, FilterError

logger = setup_logger("filter")


def normalize_text(text: str) -> str:
    """Normaliza texto removendo acentos e convertendo para maiúsculas."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return ascii_text.strip().upper()


def safe_float(val: Optional[str]) -> Optional[float]:
    """Converte string para float com segurança, suportando ponto e vírgula decimal."""
    if not val or val.strip() == "" or val.strip().lower() in ("null", "none", "nan"):
        return None
    try:
        clean_val = val.strip().replace(",", ".")
        return float(clean_val)
    except (ValueError, TypeError):
        return None


def parse_line_to_record(
    header: List[str],
    values: List[str],
    source_filename: str,
    match_type: str,
) -> Optional[RegistroEnergiaVertida]:
    """Converte valores de uma linha CSV em uma instância de RegistroEnergiaVertida."""
    row_dict = {h.strip(): v.strip() for h, v in zip(header, values) if h}

    try:
        return RegistroEnergiaVertida(
            id_subsistema=row_dict.get("id_subsistema", ""),
            nom_subsistema=row_dict.get("nom_subsistema", ""),
            nom_bacia=row_dict.get("nom_bacia", ""),
            nom_rio=row_dict.get("nom_rio", ""),
            nom_agente=row_dict.get("nom_agente", ""),
            nom_reservatorio=row_dict.get("nom_reservatorio", ""),
            cod_usina=row_dict.get("cod_usina", ""),
            din_instante=row_dict.get("din_instante", ""),
            val_geracao=safe_float(row_dict.get("val_geracao")),
            val_disponibilidade=safe_float(row_dict.get("val_disponibilidade")),
            val_vazaoturbinada=safe_float(row_dict.get("val_vazaoturbinada")),
            val_vazaovertida=safe_float(row_dict.get("val_vazaovertida")),
            val_vazaovertidanaoturbinavel=safe_float(row_dict.get("val_vazaovertidanaoturbinavel")),
            val_produtividade=safe_float(row_dict.get("val_produtividade")),
            val_folgadegeracao=safe_float(row_dict.get("val_folgadegeracao")),
            val_energiavertida=safe_float(row_dict.get("val_energiavertida")),
            val_vazaovertidaturbinavel=safe_float(row_dict.get("val_vazaovertidaturbinavel")),
            val_energiavertidaturbinavel=safe_float(row_dict.get("val_energiavertidaturbinavel")),
            arquivo_origem=source_filename,
            tipo_match=match_type,
        )
    except Exception as e:
        logger.warning("Falha ao converter linha no arquivo %s: %s", source_filename, e)
        return None


def _scan_file(
    file_path: Path,
    encoding: str,
    cod_usina: str,
    nome_normalizado: str,
) -> Tuple[List[RegistroEnergiaVertida], AuditoriaArquivo]:
    """Percorre o arquivo com a codificação informada (UnicodeDecodeError propaga)."""
    records: List[RegistroEnergiaVertida] = []
    total_lines = 0
    codigo_sem_nome = 0
    nome_sem_codigo = 0
    irregulares: List[int] = []  # números das linhas com nº de campos diferente do cabeçalho
    # Pré-teste barato pela última palavra do nome antes da normalização completa
    termo_rapido = nome_normalizado.split()[-1]

    with open(file_path, "r", encoding=encoding, newline="") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader, None)
        if header is None:
            logger.warning("Arquivo vazio: %s", file_path.name)
            return records, AuditoriaArquivo(
                nome_arquivo=file_path.name,
                periodo_referencia=file_path.stem,
                codificacao=encoding,
                status_processamento="FALHA",
            )

        header = [h.strip() for h in header]
        try:
            idx_codigo = header.index("cod_usina")
            idx_reservatorio = header.index("nom_reservatorio")
        except ValueError as e:
            raise FilterError(f"Cabeçalho de {file_path.name} sem cod_usina/nom_reservatorio: {header}") from e

        for row in reader:
            if not row or not any(row):
                continue
            total_lines += 1
            if len(row) != len(header):
                irregulares.append(reader.line_num)
                continue

            codigo_confere = row[idx_codigo].strip() == cod_usina
            reservatorio = row[idx_reservatorio]
            nome_confere = termo_rapido in reservatorio.upper() and nome_normalizado in normalize_text(reservatorio)

            if codigo_confere and nome_confere:
                rec = parse_line_to_record(header, row, file_path.name, "CODIGO_E_NOME")
                if rec:
                    records.append(rec)
            elif codigo_confere:
                codigo_sem_nome += 1
            elif nome_confere:
                nome_sem_codigo += 1

    if irregulares:
        logger.warning(
            "Arquivo %s: %d linhas com formato irregular (nº de campos diferente do cabeçalho) não extraídas; "
            "primeiras linhas: %s",
            file_path.name,
            len(irregulares),
            ", ".join(str(n) for n in irregulares[:5]),
        )
    status = "PROCESSADO" if records else "SEM_REGISTROS"
    audit = AuditoriaArquivo(
        nome_arquivo=file_path.name,
        periodo_referencia=file_path.stem,
        total_linhas_arquivo=total_lines,
        registros_extraidos=len(records),
        registros_codigo_sem_nome=codigo_sem_nome,
        registros_nome_sem_codigo=nome_sem_codigo,
        codificacao=encoding,
        status_processamento=status,
        registros_formato_irregular=len(irregulares),
    )
    return records, audit


def filter_csv_file(
    file_path: Path,
    cod_usina: int = COD_USINA_ONS,
    nome_reservatorio: str = NOME_RESERVATORIO_REFERENCIA,
) -> Tuple[List[RegistroEnergiaVertida], AuditoriaArquivo]:
    """Inspeciona um arquivo CSV via streaming, extraindo os registros da usina."""
    codigo = str(int(cod_usina))
    nome_normalizado = normalize_text(nome_reservatorio)

    try:
        try:
            records, audit = _scan_file(file_path, "utf-8", codigo, nome_normalizado)
        except UnicodeDecodeError:
            logger.info("Arquivo %s não é UTF-8 válido; relendo como Latin-1.", file_path.name)
            records, audit = _scan_file(file_path, "latin-1", codigo, nome_normalizado)
    except Exception as e:
        logger.error("Erro ao processar arquivo %s: %s", file_path.name, e)
        return [], AuditoriaArquivo(
            nome_arquivo=file_path.name,
            periodo_referencia=file_path.stem,
            status_processamento="FALHA",
        )

    logger.info(
        "Arquivo %s processado: %d linhas | %d extraídos | %d só com código | %d só com nome",
        file_path.name,
        audit.total_linhas_arquivo,
        audit.registros_extraidos,
        audit.registros_codigo_sem_nome,
        audit.registros_nome_sem_codigo,
    )
    if audit.registros_codigo_sem_nome or audit.registros_nome_sem_codigo:
        logger.warning(
            "Divergência de identificação em %s: cod_usina %s com outro reservatório (%d) ou "
            "reservatório com outro cod_usina (%d). Verificar mudança de cadastro no ONS.",
            file_path.name,
            codigo,
            audit.registros_codigo_sem_nome,
            audit.registros_nome_sem_codigo,
        )
    return records, audit


def filter_all_raw_files(
    raw_dir: Path = RAW_DATA_DIR,
    cod_usina: int = COD_USINA_ONS,
    nome_reservatorio: str = NOME_RESERVATORIO_REFERENCIA,
) -> Tuple[List[RegistroEnergiaVertida], List[AuditoriaArquivo]]:
    """Varre e filtra todos os arquivos CSV presentes no diretório de dados brutos."""
    all_records: List[RegistroEnergiaVertida] = []
    audits: List[AuditoriaArquivo] = []

    csv_files = sorted(list(raw_dir.glob("*.csv")))
    if not csv_files:
        logger.warning("Nenhum arquivo CSV encontrado em %s para filtragem.", raw_dir)
        return all_records, audits

    logger.info("Iniciando filtragem exaustiva de %d arquivos CSV em %s", len(csv_files), raw_dir)

    for idx, f in enumerate(csv_files, start=1):
        logger.info("[%d/%d] Inspecionando arquivo: %s", idx, len(csv_files), f.name)
        file_records, file_audit = filter_csv_file(
            f, cod_usina=cod_usina, nome_reservatorio=nome_reservatorio
        )
        all_records.extend(file_records)
        audits.append(file_audit)

    logger.info(
        "Varredura concluída. Total de registros extraídos: %d em %d arquivos inspecionados.",
        len(all_records),
        len(csv_files),
    )
    return all_records, audits
