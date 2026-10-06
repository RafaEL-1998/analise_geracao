"""Testes unitários para o módulo de filtragem e consolidação (User Story 2)."""

from src.filter import filter_csv_file, parse_line_to_record
from src.consolidator import consolidate_records, save_consolidated_records
from src.models import RegistroEnergiaVertida


def _registro(instante: str, geracao: float, arquivo: str, cod_usina: str = "153") -> RegistroEnergiaVertida:
    return RegistroEnergiaVertida(
        id_subsistema="SE", nom_subsistema="SUDESTE", nom_bacia="PARANA", nom_rio="VERDE",
        nom_agente="AXIA SUL", nom_reservatorio="SAO DOMINGOS", cod_usina=cod_usina,
        din_instante=instante, val_geracao=geracao, arquivo_origem=arquivo,
    )


def test_parse_line_to_record():
    """Valida a conversão de uma linha CSV para o modelo RegistroEnergiaVertida."""
    header = [
        "id_subsistema", "nom_subsistema", "nom_bacia", "nom_rio", "nom_agente",
        "nom_reservatorio", "cod_usina", "din_instante", "val_geracao", "val_disponibilidade",
        "val_vazaoturbinada", "val_vazaovertida", "val_vazaovertidanaoturbinavel",
        "val_produtividade", "val_folgadegeracao", "val_energiavertida",
        "val_vazaovertidaturbinavel", "val_energiavertidaturbinavel"
    ]
    values = [
        "SE", "SUDESTE", "PARANA", "VERDE", "AXIA SUL", "SAO DOMINGOS", "153",
        "2026-08-01 00:00:00", "30.5", "46.8", "100.0", "6.0", "5.0", "0.305",
        "16.3", "1.83", "1.0", "0.305"
    ]

    record = parse_line_to_record(header, values, source_filename="teste.csv", match_type="CODIGO_E_NOME")

    assert record is not None
    assert record.cod_usina == "153"
    assert record.din_instante == "2026-08-01 00:00:00"
    assert record.val_geracao == 30.5
    assert record.val_energiavertidaturbinavel == 0.305
    assert record.arquivo_origem == "teste.csv"
    assert record.tipo_match == "CODIGO_E_NOME"


def test_filter_csv_file_extrai_por_codigo_e_nome(sample_csv_with_matches):
    """Extrai a usina pelos dois critérios, independentemente do nome do agente, e conta divergências."""
    records, audit = filter_csv_file(sample_csv_with_matches)

    assert len(records) == 2
    assert {r.nom_agente for r in records} == {"AXIA SUL", "CGT ELETROSUL"}
    assert all(r.cod_usina == "153" and r.nom_reservatorio == "SAO DOMINGOS" for r in records)
    assert audit.total_linhas_arquivo == 5  # Excluindo cabeçalho
    assert audit.registros_extraidos == 2
    assert audit.registros_codigo_sem_nome == 1
    assert audit.registros_nome_sem_codigo == 1
    assert audit.status_processamento == "PROCESSADO"


def test_filter_csv_file_without_matches(sample_csv_without_matches):
    """Verifica o comportamento para arquivos sem registros da UHE São Domingos (ex: 2015)."""
    records, audit = filter_csv_file(sample_csv_without_matches)

    assert len(records) == 0
    assert audit.total_linhas_arquivo == 1
    assert audit.registros_extraidos == 0
    assert audit.status_processamento == "SEM_REGISTROS"


def test_filter_csv_file_latin1(tmp_path):
    """Arquivo em Latin-1 com acento no nome do reservatório continua sendo extraído."""
    from tests.conftest import ONS_CSV_HEADER

    linha = "SE;SUDESTE;PARANÁ;VERDE;AXIA SUL;SÃO DOMINGOS;153;2026-08-01 00:00:00;30.5;46.8;100.0;6.0;5.0;0.305;16.3;1.83;1.0;0.305"
    arquivo = tmp_path / "latin1.csv"
    arquivo.write_bytes("\n".join([ONS_CSV_HEADER, linha]).encode("latin-1"))

    records, audit = filter_csv_file(arquivo)

    assert len(records) == 1
    assert audit.codificacao == "latin-1"


def test_consolidate_and_sort_records(tmp_path):
    """Verifica ordenação cronológica e deduplicação por (cod_usina, instante)."""
    r1 = _registro("2026-08-01 02:00:00", 40.0, "arquivo_b.csv")
    r2 = _registro("2026-08-01 01:00:00", 35.0, "arquivo_a.csv")
    r3 = _registro("2026-08-01 01:00:00", 35.0, "arquivo_b.csv")  # duplicata idêntica

    consolidated = consolidate_records([r1, r2, r3])
    assert len(consolidated) == 2
    assert consolidated[0].din_instante == "2026-08-01 01:00:00"
    assert consolidated[1].din_instante == "2026-08-01 02:00:00"

    output_csv = tmp_path / "consolidado.csv"
    save_consolidated_records(consolidated, output_path=output_csv)
    content = output_csv.read_text(encoding="utf-8")
    assert "2026-08-01 01:00:00" in content
    assert "2026-08-01 02:00:00" in content


def test_consolidate_duplicata_conflitante_prevalece_ultimo_arquivo():
    """Com valores diferentes no mesmo instante, prevalece o registro lido por último."""
    antigo = _registro("2026-08-01 01:00:00", 35.0, "ENERGIA_VERTIDA_TURBINAVEL_2026.csv")
    revisado = _registro("2026-08-01 01:00:00", 36.5, "ENERGIA_VERTIDA_TURBINAVEL_2026_08.csv")

    consolidated = consolidate_records([antigo, revisado])

    assert len(consolidated) == 1
    assert consolidated[0].val_geracao == 36.5


def test_consolidate_nao_mistura_usinas_no_mesmo_instante():
    """Registros de códigos diferentes no mesmo instante não são descartados um pelo outro."""
    a = _registro("2026-08-01 01:00:00", 35.0, "x.csv", cod_usina="153")
    b = _registro("2026-08-01 01:00:00", 10.0, "x.csv", cod_usina="999")

    assert len(consolidate_records([a, b])) == 2


def test_linhas_com_formato_irregular_sao_contadas_e_avisadas(tmp_path, caplog):
    """Spec 005, US4: linha curta e linha longa não são extraídas, são contadas e avisadas; linha vazia é ignorada."""
    import logging
    from tests.conftest import ONS_CSV_HEADER, SAMPLE_SAO_DOMINGOS_LINE, SAMPLE_SAO_DOMINGOS_AGENTE_ANTIGO_LINE

    curta = ";".join(SAMPLE_SAO_DOMINGOS_LINE.split(";")[:10])
    longa = SAMPLE_SAO_DOMINGOS_AGENTE_ANTIGO_LINE + ";campo_extra"
    arquivo = tmp_path / "irregular.csv"
    arquivo.write_text("\n".join([ONS_CSV_HEADER, SAMPLE_SAO_DOMINGOS_LINE, curta, "", longa]), encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="filter"):
        registros, auditoria = filter_csv_file(arquivo)

    assert len(registros) == 1
    assert auditoria.registros_formato_irregular == 2
    assert auditoria.total_linhas_arquivo == 3
    aviso = [r.getMessage() for r in caplog.records if "formato irregular" in r.getMessage()]
    assert aviso and "irregular.csv" in aviso[0] and "3" in aviso[0] and "5" in aviso[0]


def test_arquivo_regular_tem_zero_linhas_irregulares(sample_csv_with_matches):
    _, auditoria = filter_csv_file(sample_csv_with_matches)
    assert auditoria.registros_formato_irregular == 0
