"""Extração e consolidação da Energia Vertida Turbinável (spec da Coleta de dados, FR-041).

Um registro é extraído quando o código da usina (``identificacao.cod_usina`` do perfil) e o nome do reservatório
(``identificacao.nome_ons``) conferem. Linhas em que apenas um dos dois confere não são extraídas, mas são contadas na
auditoria, para que uma mudança de código ou de nome no ONS fique visível. A consolidação deixa um registro por
(``cod_usina``, ``din_instante``), o do arquivo lido por último, em ordem cronológica.
"""

import csv
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.coleta.catalogo import (
    _local_filename,
    download_resource,
    fetch_ckan_package_metadata,
    load_manifest,
    parse_ckan_resources,
    save_manifest,
)
from src.comum.caminhos import RAW_MANIFEST_FILE
from src.comum.logger import FilterError, setup_logger
from src.comum.modelos import AuditoriaArquivo, RegistroEnergiaVertida
from src.comum.persistencia import gravar_linhas_csv
from src.comum.regras import ONS_CKAN_PACKAGE_URL, OPERATIONAL_METRIC_COLUMNS

logger = setup_logger("coleta")


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


def valor_invalido(val: Optional[str]) -> bool:
    """Valor preenchido que não é número: fica vazio no registro e é contado na auditoria."""
    texto = (val or "").strip()
    return bool(texto) and texto.lower() not in ("null", "none", "nan") and safe_float(texto) is None


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
    invalidos = 0  # valores numéricos ilegíveis nas linhas extraídas
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
        idx_valores = [i for i, h in enumerate(header) if h in OPERATIONAL_METRIC_COLUMNS]

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
                    invalidos += sum(valor_invalido(row[i]) for i in idx_valores)
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
    if invalidos:
        logger.warning("Arquivo %s: %d valores numéricos ilegíveis nas linhas da usina; ficam vazios.",
                       file_path.name, invalidos)
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
        valores_invalidos=invalidos,
    )
    return records, audit


def filter_csv_file(
    file_path: Path,
    cod_usina: int,
    nome_reservatorio: str,
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
            mensagem=str(e),
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
    raw_dir: Path,
    cod_usina: int,
    nome_reservatorio: str,
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


# ---------------------------------------------------------------------------
# Consolidação e gravação
# ---------------------------------------------------------------------------

CONSOLIDATED_CSV_COLUMNS = [
    "id_subsistema",
    "nom_subsistema",
    "nom_bacia",
    "nom_rio",
    "nom_agente",
    "nom_reservatorio",
    "cod_usina",
    "din_instante",
    "val_geracao",
    "val_disponibilidade",
    "val_vazaoturbinada",
    "val_vazaovertida",
    "val_vazaovertidanaoturbinavel",
    "val_produtividade",
    "val_folgadegeracao",
    "val_energiavertida",
    "val_vazaovertidaturbinavel",
    "val_energiavertidaturbinavel",
    "arquivo_origem",
    "tipo_match",
]

AUDIT_CSV_COLUMNS = [
    "nome_arquivo",
    "periodo_referencia",
    "total_linhas_arquivo",
    "registros_extraidos",
    "registros_codigo_sem_nome",
    "registros_nome_sem_codigo",
    "codificacao",
    "status_processamento",
    "data_hora_processamento",
    "registros_formato_irregular",
    "valores_invalidos",
    "formato",
    "data_publicacao",
    "obtido",
    "mensagem",
]


def _valores_medicao(r: RegistroEnergiaVertida) -> tuple:
    return (
        r.val_geracao,
        r.val_disponibilidade,
        r.val_vazaoturbinada,
        r.val_vazaovertida,
        r.val_vazaovertidanaoturbinavel,
        r.val_produtividade,
        r.val_folgadegeracao,
        r.val_energiavertida,
        r.val_vazaovertidaturbinavel,
        r.val_energiavertidaturbinavel,
    )


def consolidate_records(records: List[RegistroEnergiaVertida]) -> List[RegistroEnergiaVertida]:
    """Ordena registros cronologicamente e remove duplicatas por (cod_usina, din_instante).

    Os arquivos são lidos em ordem de nome (anuais, depois mensais), então em caso de
    duplicata prevalece o registro do arquivo lido por último. Duplicatas com valores
    diferentes são contadas e registradas em log.
    """
    if not records:
        return []

    dedup_dict: Dict[Tuple[str, str], RegistroEnergiaVertida] = {}
    duplicatas_identicas = 0
    duplicatas_conflitantes = 0

    for r in records:
        if not r.din_instante:
            continue
        chave = (r.cod_usina.strip(), r.din_instante)
        existente = dedup_dict.get(chave)
        if existente is not None:
            if _valores_medicao(existente) == _valores_medicao(r):
                duplicatas_identicas += 1
            else:
                duplicatas_conflitantes += 1
                logger.warning(
                    "Registro duplicado com valores diferentes em %s (cod_usina %s): %s substitui %s.",
                    r.din_instante,
                    r.cod_usina,
                    r.arquivo_origem,
                    existente.arquivo_origem,
                )
        dedup_dict[chave] = r

    # Ordenação cronológica ascendente
    sorted_records = sorted(dedup_dict.values(), key=lambda x: (x.din_instante, x.cod_usina))
    logger.info(
        "Consolidação concluída: %d registros únicos (de %d lidos; %d duplicatas idênticas, %d conflitantes).",
        len(sorted_records),
        len(records),
        duplicatas_identicas,
        duplicatas_conflitantes,
    )
    return sorted_records


def save_consolidated_records(
    records: List[RegistroEnergiaVertida],
    output_path: Path,
) -> Path:
    """Grava a lista consolidada de registros em CSV (';'), com cópia de segurança da versão anterior."""

    def linhas():
        for r in records:
            yield [
                r.id_subsistema,
                r.nom_subsistema,
                r.nom_bacia,
                r.nom_rio,
                r.nom_agente,
                r.nom_reservatorio,
                r.cod_usina,
                r.din_instante,
                r.val_geracao if r.val_geracao is not None else "",
                r.val_disponibilidade if r.val_disponibilidade is not None else "",
                r.val_vazaoturbinada if r.val_vazaoturbinada is not None else "",
                r.val_vazaovertida if r.val_vazaovertida is not None else "",
                r.val_vazaovertidanaoturbinavel if r.val_vazaovertidanaoturbinavel is not None else "",
                r.val_produtividade if r.val_produtividade is not None else "",
                r.val_folgadegeracao if r.val_folgadegeracao is not None else "",
                r.val_energiavertida if r.val_energiavertida is not None else "",
                r.val_vazaovertidaturbinavel if r.val_vazaovertidaturbinavel is not None else "",
                r.val_energiavertidaturbinavel if r.val_energiavertidaturbinavel is not None else "",
                r.arquivo_origem,
                r.tipo_match,
            ]

    gravar_linhas_csv(CONSOLIDATED_CSV_COLUMNS, linhas(), output_path)
    logger.info("Base consolidada gravada com sucesso em: %s (%d linhas)", output_path, len(records))
    return output_path


def save_audit_report(
    audits: List[AuditoriaArquivo],
    output_path: Path,
) -> Path:
    """Grava o relatório de auditoria de 100% dos arquivos inspecionados em CSV, com cópia de segurança."""

    def linhas():
        for a in audits:
            yield [
                a.nome_arquivo,
                a.periodo_referencia,
                a.total_linhas_arquivo,
                a.registros_extraidos,
                a.registros_codigo_sem_nome,
                a.registros_nome_sem_codigo,
                a.codificacao,
                a.status_processamento,
                a.data_hora_processamento,
                a.registros_formato_irregular,
                a.valores_invalidos,
                a.formato,
                a.data_publicacao,
                a.obtido,
                a.mensagem,
            ]

    gravar_linhas_csv(AUDIT_CSV_COLUMNS, linhas(), output_path)
    logger.info("Relatório de auditoria gravado com sucesso em: %s (%d arquivos)", output_path, len(audits))
    return output_path


# ---------------------------------------------------------------------------
# Sincronização com o portal
# ---------------------------------------------------------------------------


def sincronizar_evt(pasta_raw: Path, force: bool = False) -> List[Dict[str, Any]]:
    """Baixa (ou reaproveita, se a versão local for a publicada) todos os arquivos publicados da EVT.

    Catálogo inacessível levanta exceção (código 1). Um arquivo não obtido não interrompe os demais: volta como falha,
    com o nome e o motivo (FR-026).
    """
    pasta_raw = Path(pasta_raw)
    recursos = parse_ckan_resources(fetch_ckan_package_metadata(ONS_CKAN_PACKAGE_URL))
    manifesto_path = pasta_raw / RAW_MANIFEST_FILE.name
    manifesto = load_manifest(manifesto_path)
    falhas: List[Dict[str, Any]] = []
    try:
        for idx, r in enumerate(recursos, start=1):
            logger.info("[%d/%d] Sincronizando recurso: %s", idx, len(recursos), r.nome_recurso)
            try:
                download_resource(r, destination_dir=pasta_raw, force=force, manifest=manifesto)
            except Exception as exc:  # o arquivo vai para a auditoria como FALHA
                nome = _local_filename(r)
                logger.error("Energia Vertida Turbinável: falha ao obter %s: %s", nome, exc)
                falhas.append({"arquivo": nome, "mensagem": str(exc)})
    finally:
        save_manifest(manifesto, manifesto_path)
    resumo: Dict[str, int] = {}
    for r in recursos:
        resumo[r.status_sincronizacao] = resumo.get(r.status_sincronizacao, 0) + 1
    logger.info("Energia Vertida Turbinável: %d recursos publicados | %s", len(recursos), resumo)
    return falhas
