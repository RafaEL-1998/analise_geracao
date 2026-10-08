"""Testes unitários para o módulo de auditoria e conformidade (User Story 3)."""

from pathlib import Path
from src.comum.modelos import AuditoriaArquivo
from src.coleta.evt import save_audit_report, AUDIT_CSV_COLUMNS


def test_save_audit_report(tmp_path: Path):
    """Verifica a gravação correta do relatório de auditoria."""
    a1 = AuditoriaArquivo(
        nome_arquivo="ENERGIA_VERTIDA_TURBINAVEL_2015.csv",
        periodo_referencia="2015",
        total_linhas_arquivo=150000,
        registros_extraidos=0,
        status_processamento="SEM_REGISTROS",
    )
    a2 = AuditoriaArquivo(
        nome_arquivo="ENERGIA_VERTIDA_TURBINAVEL_2026_08.csv",
        periodo_referencia="2026_08",
        total_linhas_arquivo=200000,
        registros_extraidos=744,
        registros_codigo_sem_nome=2,
        registros_nome_sem_codigo=1,
        status_processamento="PROCESSADO",
    )

    report_path = tmp_path / "relatorio_auditoria.csv"
    save_audit_report([a1, a2], output_path=report_path)

    lines = report_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3  # Cabeçalho + 2 registros

    header = lines[0].split(";")
    assert header == AUDIT_CSV_COLUMNS

    row1 = dict(zip(header, lines[1].split(";")))
    assert row1["nome_arquivo"] == "ENERGIA_VERTIDA_TURBINAVEL_2015.csv"
    assert row1["status_processamento"] == "SEM_REGISTROS"

    row2 = dict(zip(header, lines[2].split(";")))
    assert row2["registros_extraidos"] == "744"
    assert row2["registros_codigo_sem_nome"] == "2"
    assert row2["registros_nome_sem_codigo"] == "1"
    assert row2["status_processamento"] == "PROCESSADO"
