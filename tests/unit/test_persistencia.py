"""Testes de contrato da gravação com cópia de segurança (spec 006, US1; contracts/persistencia-contract.md)."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from openpyxl import load_workbook

from src.persistencia import (
    ErroPersistencia,
    ResultadoGravacao,
    gravar_csv,
    gravar_linhas_csv,
    gravar_parquet,
    gravar_planilha,
    gravar_texto,
)


def _hash(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _tabela(fator: float = 1.0, linhas: int = 3) -> pd.DataFrame:
    return pd.DataFrame({
        "din_instante": pd.date_range("2026-01-01", periods=linhas, freq="h"),
        "valor": [i * fator for i in range(linhas)],
        "texto": ["a"] * linhas,
    })


def _temporarios(pasta: Path) -> list:
    return sorted(p.name for p in pasta.glob("*.tmp"))


def test_primeira_gravacao_e_novo_sem_copia(tmp_path: Path) -> None:
    destino = tmp_path / "x.csv"
    assert gravar_csv(_tabela(), destino) is ResultadoGravacao.NOVO
    assert pd.read_csv(destino, sep=";").shape == (3, 3)
    assert not (tmp_path / "x.csv.bak").exists()
    assert _temporarios(tmp_path) == []


def test_conteudo_diferente_guarda_a_versao_anterior(tmp_path: Path) -> None:
    destino = tmp_path / "x.csv"
    gravar_csv(_tabela(), destino)
    anterior = destino.read_bytes()
    assert gravar_csv(_tabela(fator=2.0), destino) is ResultadoGravacao.ALTERADO
    assert (tmp_path / "x.csv.bak").read_bytes() == anterior
    assert destino.read_bytes() != anterior
    assert _temporarios(tmp_path) == []


def test_conteudo_identico_nao_toca_arquivo_nem_copia(tmp_path: Path) -> None:
    destino, copia = tmp_path / "x.csv", tmp_path / "x.csv.bak"
    gravar_csv(_tabela(), destino)
    gravar_csv(_tabela(fator=2.0), destino)
    antes = (_hash(destino), _hash(copia), destino.stat().st_mtime_ns, copia.stat().st_mtime_ns)
    time.sleep(0.05)
    assert gravar_csv(_tabela(fator=2.0), destino) is ResultadoGravacao.INALTERADO
    assert (_hash(destino), _hash(copia), destino.stat().st_mtime_ns, copia.stat().st_mtime_ns) == antes
    assert _temporarios(tmp_path) == []


def test_falha_na_troca_mantem_arquivo_e_copia(tmp_path: Path) -> None:
    destino, copia = tmp_path / "x.csv", tmp_path / "x.csv.bak"
    gravar_csv(_tabela(), destino)
    gravar_csv(_tabela(fator=2.0), destino)
    arquivo, bak = destino.read_bytes(), copia.read_bytes()
    with patch("src.persistencia.Path.replace", side_effect=OSError("arquivo aberto em outro programa")):
        with pytest.raises(ErroPersistencia) as erro:
            gravar_csv(_tabela(fator=3.0), destino)
    assert erro.value.destino == destino
    assert destino.read_bytes() == arquivo
    assert copia.read_bytes() == bak  # a versão anterior à última alteração continua recuperável
    assert _temporarios(tmp_path) == []


def test_falha_na_conferencia_do_temporario_nao_altera_nada(tmp_path: Path) -> None:
    destino = tmp_path / "x.csv"
    gravar_csv(_tabela(), destino)
    antes = destino.read_bytes()
    with patch("src.persistencia._conferir_csv", side_effect=ValueError("linhas diferentes")):
        with pytest.raises(ErroPersistencia):
            gravar_csv(_tabela(fator=3.0), destino)
    assert destino.read_bytes() == antes
    assert not (tmp_path / "x.csv.bak").exists()
    assert _temporarios(tmp_path) == []


def test_falha_na_conferencia_final_restaura_versao_anterior(tmp_path: Path) -> None:
    destino, copia = tmp_path / "x.csv", tmp_path / "x.csv.bak"
    gravar_csv(_tabela(), destino)
    gravar_csv(_tabela(fator=2.0), destino)
    arquivo, bak = destino.read_bytes(), copia.read_bytes()
    with patch("src.persistencia._sha256", side_effect=["a" * 64, "b" * 64]):
        with pytest.raises(ErroPersistencia):
            gravar_csv(_tabela(fator=3.0), destino)
    assert destino.read_bytes() == arquivo
    assert copia.read_bytes() == bak
    assert _temporarios(tmp_path) == []


def test_falha_em_arquivo_novo_nao_deixa_arquivo_invalido(tmp_path: Path) -> None:
    destino = tmp_path / "novo.csv"
    with patch("src.persistencia._sha256", side_effect=["a" * 64, "b" * 64]):
        with pytest.raises(ErroPersistencia):
            gravar_csv(_tabela(), destino)
    assert not destino.exists()
    assert _temporarios(tmp_path) == []


def test_planilha_com_os_mesmos_dados_fica_inalterada(tmp_path: Path) -> None:
    destino = tmp_path / "p.xlsx"
    abas = {"A": _tabela(), "B": pd.DataFrame(columns=["z"])}
    assert gravar_planilha(abas, destino) is ResultadoGravacao.NOVO
    antes = _hash(destino)
    time.sleep(1.1)  # as datas internas do pacote mudariam a cada gravação
    assert gravar_planilha(abas, destino) is ResultadoGravacao.INALTERADO
    assert _hash(destino) == antes
    assert not (tmp_path / "p.xlsx.bak").exists()
    abas["A"] = _tabela(fator=5.0)
    assert gravar_planilha(abas, destino) is ResultadoGravacao.ALTERADO
    assert _hash(tmp_path / "p.xlsx.bak") == antes
    assert list(pd.read_excel(destino, sheet_name=None)) == ["A", "B"]
    assert _temporarios(tmp_path) == []


def test_planilha_aplica_a_formatacao(tmp_path: Path) -> None:
    destino = tmp_path / "p.xlsx"

    def formatar(writer) -> None:
        writer.sheets["A"].freeze_panes = "A2"

    gravar_planilha({"A": _tabela()}, destino, formatar=formatar)
    assert load_workbook(destino)["A"].freeze_panes == "A2"


def test_linhas_csv_confere_registros_e_cabecalho(tmp_path: Path) -> None:
    destino = tmp_path / "c.csv"
    assert gravar_linhas_csv(["a", "b"], [[1, 2], [3, ""]], destino) is ResultadoGravacao.NOVO
    assert destino.read_text(encoding="utf-8").splitlines() == ["a;b", "1;2", "3;"]
    assert gravar_linhas_csv(["a", "b"], iter([[1, 2], [3, ""]]), destino) is ResultadoGravacao.INALTERADO


def test_parquet_deterministico(tmp_path: Path) -> None:
    destino = tmp_path / "t.parquet"
    assert gravar_parquet(_tabela(), destino) is ResultadoGravacao.NOVO
    assert gravar_parquet(_tabela(), destino) is ResultadoGravacao.INALTERADO
    assert gravar_parquet(_tabela(fator=2.0), destino) is ResultadoGravacao.ALTERADO
    assert pd.read_parquet(destino)["valor"].tolist() == [0.0, 2.0, 4.0]


def test_texto(tmp_path: Path) -> None:
    destino = tmp_path / "r.md"
    assert gravar_texto("# título\nlinha\n", destino) is ResultadoGravacao.NOVO
    assert gravar_texto("# título\nlinha\n", destino) is ResultadoGravacao.INALTERADO
    assert gravar_texto("# outro\n", destino) is ResultadoGravacao.ALTERADO
    assert (tmp_path / "r.md.bak").read_text(encoding="utf-8") == "# título\nlinha\n"


def test_tabelas_vazias(tmp_path: Path) -> None:
    assert gravar_csv(pd.DataFrame(), tmp_path / "v.csv") is ResultadoGravacao.NOVO
    assert gravar_csv(pd.DataFrame(columns=["a", "b"]), tmp_path / "w.csv") is ResultadoGravacao.NOVO
    assert gravar_csv(pd.DataFrame({"a": [None, None]}), tmp_path / "u.csv") is ResultadoGravacao.NOVO
