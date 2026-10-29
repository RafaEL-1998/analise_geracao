"""Formatadores de número do relatório (bug zero-negativo-tabela; homologação de 26/10/2026)."""

from __future__ import annotations

import pytest

from src.comum.formatacao import SEM_VALOR, fmt_int, fmt_num, fmt_pct


@pytest.mark.parametrize("valor, casas, esperado", [
    (-0.04, 1, "0,0"),
    (-0.004, 2, "0,00"),
    (-0.4, 0, "0"),
    (-0.0, 1, "0,0"),
    (-0.06, 1, "-0,1"),
    (-1234.56, 1, "-1.234,6"),
    (1234.56, 2, "1.234,56"),
    (0.0, 1, "0,0"),
])
def test_fmt_num_sem_zero_negativo(valor: float, casas: int, esperado: str) -> None:
    assert fmt_num(valor, casas) == esperado


def test_fmt_pct_e_fmt_int_sem_zero_negativo() -> None:
    assert fmt_pct(-0.01, 1) == "0,0%"
    assert fmt_pct(-0.06, 1) == "-0,1%"
    assert fmt_int(-0.3) == "0"


@pytest.mark.parametrize("valor", [None, float("nan"), float("inf"), "texto"])
def test_fmt_num_sem_valor(valor) -> None:
    assert fmt_num(valor) == SEM_VALOR
