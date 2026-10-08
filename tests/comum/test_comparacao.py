"""Comparação do relatório com uma referência (spec da Geração do relatório, US8: ferramenta comparar)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

from src.comum.comparacao import CODIGO_DIFERENCAS, CODIGO_ERRO, comparar, executar_comparacao


def _relatorio(pasta: Path, valor: float = 1.5) -> Path:
    (pasta / "figures").mkdir(parents=True)
    (pasta / "relatorio.md").write_text("# Relatório\n", encoding="utf-8")
    (pasta / "relatorio.pdf").write_bytes(b"%PDF-1.4 teste")
    (pasta / "figures" / "01.png").write_bytes(b"\x89PNG teste")
    with pd.ExcelWriter(pasta / "planilha.xlsx") as w:
        pd.DataFrame({"ano": [2024, 2025], "valor": [valor, 2.5]}).to_excel(w, sheet_name="INDICADORES", index=False)
        pd.DataFrame({"aba": ["INDICADORES"]}).to_excel(w, sheet_name="FONTES", index=False)
    (pasta / "etapa.json").write_text('{"etapa": "relatorio"}', encoding="utf-8")
    return pasta


def test_pastas_iguais_sem_diferenca(tmp_path: Path) -> None:
    a, b = _relatorio(tmp_path / "a"), _relatorio(tmp_path / "b")
    assert comparar(a, b) == []
    assert executar_comparacao(a, b) == 0


def test_planilha_regravada_com_os_mesmos_dados_nao_conta(tmp_path: Path) -> None:
    """Os bytes do XLSX mudam a cada gravação; o conteúdo é comparado célula a célula."""
    a, b = _relatorio(tmp_path / "a"), _relatorio(tmp_path / "b")
    assert comparar(a, b) == []


def test_celula_diferente_lista_aba_e_celula(tmp_path: Path) -> None:
    a, b = _relatorio(tmp_path / "a", valor=1.5), _relatorio(tmp_path / "b", valor=9.9)
    diferencas = comparar(a, b)
    assert diferencas == ["planilha.xlsx [INDICADORES] B2: 1.5 na atual, 9.9 na referência"]
    assert executar_comparacao(a, b) == CODIGO_DIFERENCAS


def test_byte_diferente_e_arquivo_so_numa_pasta(tmp_path: Path) -> None:
    a, b = _relatorio(tmp_path / "a"), _relatorio(tmp_path / "b")
    (a / "relatorio.md").write_text("# Relatório!\n", encoding="utf-8")
    (b / "figures" / "01.png").unlink()
    diferencas = comparar(a, b)
    assert any(d.startswith("relatorio.md: conteúdo diferente") for d in diferencas)
    assert "figures/01.png: só na pasta atual" in diferencas


def test_ordem_das_abas_conta(tmp_path: Path) -> None:
    a, b = _relatorio(tmp_path / "a"), tmp_path / "b"
    shutil.copytree(a, b)
    with pd.ExcelWriter(b / "planilha.xlsx") as w:
        pd.DataFrame({"aba": ["INDICADORES"]}).to_excel(w, sheet_name="FONTES", index=False)
        pd.DataFrame({"ano": [2024, 2025], "valor": [1.5, 2.5]}).to_excel(w, sheet_name="INDICADORES", index=False)
    assert any("abas diferentes ou em outra ordem" in d for d in comparar(a, b))


def test_etapa_json_fica_fora(tmp_path: Path) -> None:
    a, b = _relatorio(tmp_path / "a"), _relatorio(tmp_path / "b")
    (b / "etapa.json").write_text('{"etapa": "relatorio", "concluida_em": "outra"}', encoding="utf-8")
    assert comparar(a, b) == []


def test_referencia_inexistente_e_erro(tmp_path: Path) -> None:
    a = _relatorio(tmp_path / "a")
    with pytest.raises(FileNotFoundError):
        comparar(a, tmp_path / "nao_existe")
    assert executar_comparacao(a, tmp_path / "nao_existe") == CODIGO_ERRO


def test_celulas_numericas_iguais_ate_a_12a_casa() -> None:
    """Resto de ponto flutuante (ex.: número lido de CSV pelo leitor padrão do pandas) não é diferença."""
    from src.comum.comparacao import _iguais

    assert _iguais(-0.0001066700000009746, -0.0001066700000009)
    assert not _iguais(1.0, 1.0 + 1e-9)
    assert not _iguais(0.0, 1e-300) and _iguais(0, 0.0)
    assert _iguais(True, True) and not _iguais(True, False) and _iguais("a", "a") and not _iguais("a", "b")


def test_planilha_ilegivel_da_mensagem_e_codigo_1(tmp_path: Path, capsys) -> None:
    for pasta, conteudo in (("atual", b"lixo 1"), ("referencia", b"lixo 2")):
        (tmp_path / pasta).mkdir()
        (tmp_path / pasta / "p.xlsx").write_bytes(conteudo)
    assert executar_comparacao(tmp_path / "atual", tmp_path / "referencia") == CODIGO_ERRO
    assert "Erro na comparação" in capsys.readouterr().err
