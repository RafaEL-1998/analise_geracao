"""Módulo consolidador: Ordenação temporal, deduplicação e relatórios de auditoria (User Story 2 e 3)."""

from pathlib import Path
from typing import List, Dict, Tuple

from src.config import CONSOLIDATED_FILE, AUDIT_REPORT_FILE
from src.models import RegistroEnergiaVertida, AuditoriaArquivo
from src.logger import setup_logger
from src.persistencia import gravar_linhas_csv

logger = setup_logger("consolidator")

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
    output_path: Path = CONSOLIDATED_FILE,
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
    output_path: Path = AUDIT_REPORT_FILE,
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
            ]

    gravar_linhas_csv(AUDIT_CSV_COLUMNS, linhas(), output_path)
    logger.info("Relatório de auditoria gravado com sucesso em: %s (%d arquivos)", output_path, len(audits))
    return output_path
