"""Coleta no formato 2: datas de obtenção do escopo da usina e cópia do dicionário da EVT (spec 006, decisão R22;
tarefa T015)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from src import pipeline
from src.__main__ import main
from src.comum import caminhos
from src.comum import perfil as modulo_perfil
from tests.fixtures.brutos_ficticios import gerar_brutos
from tests.fixtures.execucao_ficticia import PERFIL_FICTICIO, SLUG

COLUNAS = ["conjunto", "arquivos_registrados", "publicacao_mais_recente", "obtencao_mais_recente"]


def _manifesto(pasta: Path, entradas: dict) -> None:
    (pasta / "_manifesto_ons.json").write_text(json.dumps(entradas), encoding="utf-8")


@pytest.fixture
def raiz(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / "usinas" / SLUG).mkdir(parents=True)
    shutil.copy(PERFIL_FICTICIO, tmp_path / "usinas" / SLUG / "perfil.toml")
    raw = tmp_path / "data" / "raw"
    gerar_brutos(raw)
    _manifesto(raw, {
        "ENERGIA_VERTIDA_TURBINAVEL_2024_01.csv": {"ultima_modificacao": "2024-02-05T10:00:00",
                                                   "registrado_em_utc": "2024-03-01 08:00:00"},
        "ENERGIA_VERTIDA_TURBINAVEL_2024_02.csv": {"ultima_modificacao": "2024-03-05T10:00:00",
                                                   "registrado_em_utc": "2024-03-01 09:00:00"},
    })
    _manifesto(raw / "geracao_usina_2", {
        "GERACAO_USINA-2_2024_01.parquet": {"ultima_modificacao": "2024-02-02T00:00:00",
                                            "registrado_em_utc": "2024-03-02 10:00:00"},
        "GERACAO_USINA-2_2024_02.parquet": {"ultima_modificacao": "2024-03-02T00:00:00",
                                            "registrado_em_utc": "2024-03-02 11:00:00"},
        # arquivo fora do escopo da usina (outro período, baixado por outra usina): não pode contar
        "GERACAO_USINA-2_2025_01.parquet": {"ultima_modificacao": "2025-02-02T00:00:00",
                                            "registrado_em_utc": "2025-03-02 11:00:00"},
    })
    monkeypatch.setattr(caminhos, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(caminhos, "RAW_DATA_DIR", raw)
    monkeypatch.setattr(caminhos, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(modulo_perfil, "RAIZ_PROJETO", tmp_path)
    assert main(["coleta", "--usina", SLUG, "--sem-portal"]) == 0
    return tmp_path


def _datas(raiz: Path) -> pd.DataFrame:
    return pd.read_csv(raiz / "data" / "usinas" / SLUG / "coleta" / "datas_obtencao.csv", sep=";",
                       keep_default_na=False, dtype=str)


def test_colunas_e_um_conjunto_por_linha(raiz: Path) -> None:
    datas = _datas(raiz)
    assert list(datas.columns) == COLUNAS
    assert datas["conjunto"].is_unique
    assert {"energia-vertida-turbinavel", "geracao-usina-2", "modalidade-usina"} <= set(datas["conjunto"])


def test_datas_so_com_os_arquivos_do_escopo(raiz: Path) -> None:
    datas = _datas(raiz).set_index("conjunto")
    assert datas.loc["geracao-usina-2", "arquivos_registrados"] == "2"
    assert datas.loc["geracao-usina-2", "publicacao_mais_recente"] == "2024-03-02T00:00:00"
    assert datas.loc["geracao-usina-2", "obtencao_mais_recente"] == "2024-03-02 11:00:00"
    assert datas.loc["energia-vertida-turbinavel", "arquivos_registrados"] == "2"
    assert datas.loc["energia-vertida-turbinavel", "obtencao_mais_recente"] == "2024-03-01 09:00:00"


def test_conjunto_sem_manifesto_fica_sem_datas(raiz: Path) -> None:
    datas = _datas(raiz).set_index("conjunto")
    assert datas.loc["disponibilidade_usina", "arquivos_registrados"] == "0"
    assert datas.loc["disponibilidade_usina", "obtencao_mais_recente"] == ""


def test_dicionario_da_evt_copiado(raiz: Path) -> None:
    copia = raiz / "data" / "usinas" / SLUG / "coleta" / "dicionario_evt.json"
    original = raiz / "data" / "raw" / "_dicionarios" / "DicionarioDados_EnergiaVertidaTurbinavel.json"
    assert copia.read_bytes() == original.read_bytes()


def test_formato_2_e_tratamento_recusa_o_formato_1(raiz: Path) -> None:
    assert pipeline.VERSAO_FORMATO["coleta"] == 2
    manifesto = raiz / "data" / "usinas" / SLUG / "coleta" / "etapa.json"
    dados = json.loads(manifesto.read_text(encoding="utf-8"))
    assert dados["versao_formato"] == 2
    dados["versao_formato"] = 1
    manifesto.write_text(json.dumps(dados), encoding="utf-8")
    assert main(["tratamento", "--usina", SLUG]) == 5
