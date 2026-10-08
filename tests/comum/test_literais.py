"""Nenhum valor próprio da São Domingos no código: eles ficam só no perfil da usina e nos testes (constituição, princípio III; spec da Geração do relatório, FR-019)."""

from __future__ import annotations

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
PROIBIDOS = ("Domingos", "DOMINGOS", "MSUHSD", "PRUHSD", "PNUHSD", "028761", "Kaplan", "AGEPAN")
FONTES = sorted(p for p in (RAIZ / "src").rglob("*.py") if "__pycache__" not in p.parts)


@pytest.mark.parametrize("literal", PROIBIDOS)
def test_codigo_sem_valores_da_sao_domingos(literal: str) -> None:
    achados = [f"{p.relative_to(RAIZ).as_posix()}:{n}" for p in FONTES
               for n, linha in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1) if literal in linha]
    assert not achados, f"{literal!r} no código: {achados}"


def test_valores_ficam_no_perfil() -> None:
    perfil = (RAIZ / "usinas" / "sao_domingos" / "perfil.toml").read_text(encoding="utf-8")
    for literal in ("SAO DOMINGOS", "MSUHSD", "PRUHSD", "PNUHSD", "028761", "Kaplan", "AGEPAN"):
        assert literal in perfil, literal
