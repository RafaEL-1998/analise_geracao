"""Teste de integração ponta a ponta para o pipeline ONS (User Stories 1, 2 e 3)."""

from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.main import run_pipeline, parse_arguments
from tests.conftest import (
    ONS_CSV_HEADER,
    SAMPLE_CODIGO_OUTRO_RESERVATORIO_LINE,
    SAMPLE_OTHER_LINE,
    SAMPLE_SAO_DOMINGOS_LINE,
)


def test_full_pipeline_integration(tmp_path: Path):
    """Executa o pipeline completo em diretórios temporários e valida os artefatos de saída."""
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)

    (raw_dir / "ENERGIA_VERTIDA_TURBINAVEL_2015.csv").write_text(
        "\n".join([ONS_CSV_HEADER, SAMPLE_OTHER_LINE]), encoding="utf-8"
    )
    (raw_dir / "ENERGIA_VERTIDA_TURBINAVEL_2026_08.csv").write_text(
        "\n".join([ONS_CSV_HEADER, SAMPLE_SAO_DOMINGOS_LINE, SAMPLE_CODIGO_OUTRO_RESERVATORIO_LINE, SAMPLE_OTHER_LINE]),
        encoding="utf-8",
    )

    args = parse_arguments([
        "--full-pipeline",
        "--raw-dir", str(raw_dir),
        "--processed-dir", str(processed_dir),
    ])

    with patch("src.main.discover_and_download_all") as mock_discover, \
            patch("src.main.atualizar_dicionarios") as mock_dicionarios, \
            patch("src.main.executar_indicadores_ons", return_value=0) as mock_indicadores, \
            patch("src.main.executar_programacao_ons", return_value=0) as mock_programacao, \
            patch("src.main.executar_disponibilidade_ons", return_value=0) as mock_disponibilidade, \
            patch("src.main.executar_hidrologia_ons", return_value=0) as mock_hidrologia, \
            patch("src.main.executar_geracao_ons", return_value=0) as mock_geracao, \
            patch("src.main.executar_cadastro_ons", return_value=0) as mock_cadastro:
        mock_discover.return_value = []
        exit_code = run_pipeline(args)
        mock_discover.assert_called_once()
    assert exit_code == 0

    # Etapa 1: dicionário da EVT obtido na própria pasta bruta, sem novo download dos dados (spec 006, US2)
    mock_dicionarios.assert_called_once_with(["energia-vertida-turbinavel"], raiz_raw=raw_dir,
                                             pasta_saida=processed_dir)

    # Etapa 3: indicadores no período da base consolidada e nas pastas do próprio pipeline (nunca nas do projeto)
    mock_indicadores.assert_called_once()
    kwargs = mock_indicadores.call_args.kwargs
    assert kwargs["periodo"] == (pd.Timestamp("2026-08-01 00:00"), pd.Timestamp("2026-08-01 00:00"))
    assert kwargs["pasta_raw"] == raw_dir / "indicadores_ons"
    assert kwargs["pasta_saida"] == processed_dir

    # Etapa 4: programação diária no mesmo período e nas pastas do pipeline
    mock_programacao.assert_called_once()
    kwargs = mock_programacao.call_args.kwargs
    assert kwargs["periodo"] == (pd.Timestamp("2026-08-01 00:00"), pd.Timestamp("2026-08-01 00:00"))
    assert kwargs["pasta_raw"] == raw_dir / "programacao_diaria"
    assert kwargs["pasta_saida"] == processed_dir

    # Etapa 5: disponibilidade horária no mesmo período e nas pastas do pipeline (spec 006)
    mock_disponibilidade.assert_called_once()
    kwargs = mock_disponibilidade.call_args.kwargs
    assert kwargs["periodo"] == (pd.Timestamp("2026-08-01 00:00"), pd.Timestamp("2026-08-01 00:00"))
    assert kwargs["pasta_raw"] == raw_dir / "disponibilidade_usina"
    assert kwargs["pasta_saida"] == processed_dir
    assert kwargs["baixar"] is True and kwargs["dicionarios"] is True

    # Etapa 6: dados hidrológicos no mesmo período e nas pastas do pipeline (spec 006)
    kwargs = mock_hidrologia.call_args.kwargs
    assert kwargs["periodo"] == (pd.Timestamp("2026-08-01 00:00"), pd.Timestamp("2026-08-01 00:00"))
    assert kwargs["pasta_raw"] == raw_dir / "dados_hidrologicos_ho"
    assert kwargs["pasta_saida"] == processed_dir

    # Etapas 7 e 8: geração por usina e cadastro, nas pastas do pipeline (spec 006)
    assert mock_geracao.call_args.kwargs["pasta_raw"] == raw_dir / "geracao_usina_2"
    assert mock_geracao.call_args.kwargs["periodo"] == kwargs["periodo"]
    assert mock_cadastro.call_args.kwargs["pasta_raw"] == raw_dir / "modalidade_usina"
    assert mock_cadastro.call_args.kwargs["pasta_saida"] == processed_dir

    consolidated_file = processed_dir / "uhe_sao_domingos_energia_vertida_consolidado.csv"
    audit_file = processed_dir / "relatorio_auditoria_varredura.csv"

    cons_lines = consolidated_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(cons_lines) == 2  # Cabeçalho + 1 linha da usina (a de outro reservatório fica de fora)
    assert ";153;" in cons_lines[1]
    assert "ENERGIA_VERTIDA_TURBINAVEL_2026_08.csv" in cons_lines[1]
    assert cons_lines[1].endswith("CODIGO_E_NOME")

    audit_lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
    header = audit_lines[0].split(";")
    linhas = [dict(zip(header, linha.split(";"))) for linha in audit_lines[1:]]
    assert [l["status_processamento"] for l in linhas] == ["SEM_REGISTROS", "PROCESSADO"]
    assert linhas[1]["registros_codigo_sem_nome"] == "1"


def test_complementares_only_nao_toca_a_base_evt(tmp_path: Path):
    """--complementares-only: só as etapas das bases novas, com download, no período da base existente."""
    raw_dir, processed_dir = tmp_path / "raw", tmp_path / "processed"
    args = parse_arguments(["--complementares-only", "--raw-dir", str(raw_dir), "--processed-dir", str(processed_dir)])
    with patch("src.main.discover_and_download_all") as mock_discover, \
            patch("src.main.filter_all_raw_files") as mock_filtro, \
            patch("src.main.executar_disponibilidade_ons", return_value=0) as mock_disponibilidade, \
            patch("src.main.executar_hidrologia_ons", return_value=0) as mock_hidrologia, \
            patch("src.main.executar_geracao_ons", return_value=0) as mock_geracao, \
            patch("src.main.executar_cadastro_ons", return_value=0) as mock_cadastro:
        assert run_pipeline(args) == 0
    mock_hidrologia.assert_called_once()
    mock_geracao.assert_called_once()
    mock_cadastro.assert_called_once()
    mock_discover.assert_not_called()
    mock_filtro.assert_not_called()
    kwargs = mock_disponibilidade.call_args.kwargs
    assert kwargs["periodo"] is None and kwargs["baixar"] is True
    assert kwargs["pasta_raw"] == raw_dir / "disponibilidade_usina" and kwargs["pasta_saida"] == processed_dir


def test_codigo_de_erro_de_etapa_complementar_e_propagado(tmp_path: Path):
    args = parse_arguments(["--disponibilidade-only", "--raw-dir", str(tmp_path), "--processed-dir", str(tmp_path)])
    with patch("src.main.executar_disponibilidade_ons", return_value=2):
        assert run_pipeline(args) == 2


def test_falha_de_alinhamento_da_hidrologia_interrompe_com_codigo_3(tmp_path: Path):
    args = parse_arguments(["--complementares-only", "--raw-dir", str(tmp_path), "--processed-dir", str(tmp_path)])
    with patch("src.main.executar_disponibilidade_ons", return_value=0), \
            patch("src.main.executar_hidrologia_ons", return_value=3):
        assert run_pipeline(args) == 3
