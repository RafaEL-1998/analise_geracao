"""Cópia de segurança do projeto (spec da Coleta de dados, FR-014 e FR-015; constituição, Requisito Técnico 5): no máximo duas cópias."""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from src.comum import copia_seguranca
from src.comum.copia_seguranca import copias_existentes, criar_copia


def _projeto(raiz: Path) -> Path:
    for rel, texto in {
        "src/modulo.py": "x = 1\n",
        "tests/test_x.py": "def test(): pass\n",
        "specs/001/spec.md": "# Spec\n",
        "reports/relatorio.md": "# Relatório\n",
        ".specify/memory/constitution.md": "# Constituição\n",
        "README.md": "# Projeto\n",
        "requirements.txt": "pandas\n",
        "usinas/usina_a/perfil.toml": "[usina]\n",
        "usinas/usina_a/documentos/documento.pdf": "%PDF",
        "data/raw/bruto.csv": "a;b\n",
        "data/usinas/usina_a/coleta/evt_extraido.csv": "a;b\n",
        "src/__pycache__/modulo.cpython-314.pyc": "lixo",
    }.items():
        caminho = raiz / rel
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(texto, encoding="utf-8")
    return raiz


def test_copia_com_registro_conferido_e_sem_dados(tmp_path: Path) -> None:
    raiz = _projeto(tmp_path)
    assert criar_copia("teste", raiz=raiz, hoje=date(2026, 10, 7)) == 0
    copia = raiz / "_backup_2026-10-07_teste"
    assert {p.name for p in copia.iterdir()} >= {"LEIA-ME.txt", "conftest.py", "copia.json", "src", "usinas"}
    registro = json.loads((copia / "copia.json").read_text(encoding="utf-8"))
    nomes = {r["arquivo"] for r in registro}
    assert "usinas/usina_a/perfil.toml" in nomes and "README.md" in nomes
    assert not any(n.startswith(("data/", "usinas/usina_a/documentos")) or "__pycache__" in n for n in nomes)
    assert (copia / "conftest.py").read_text(encoding="utf-8") == 'collect_ignore_glob = ["*"]\n'


def test_ficam_as_duas_mais_recentes(tmp_path: Path) -> None:
    raiz = _projeto(tmp_path)
    assert criar_copia("primeira", raiz=raiz, hoje=date(2026, 10, 1)) == 0
    assert criar_copia("segunda", raiz=raiz, hoje=date(2026, 10, 2)) == 0
    assert criar_copia("terceira", raiz=raiz, hoje=date(2026, 10, 3)) == 0
    assert [p.name for p in copias_existentes(raiz)] == ["_backup_2026-10-02_segunda", "_backup_2026-10-03_terceira"]


def test_falha_apaga_a_copia_incompleta_e_nao_toca_nas_outras(tmp_path: Path, monkeypatch) -> None:
    raiz = _projeto(tmp_path)
    assert criar_copia("primeira", raiz=raiz, hoje=date(2026, 10, 1)) == 0
    assert criar_copia("segunda", raiz=raiz, hoje=date(2026, 10, 2)) == 0
    original = shutil.copy2

    def falha_no_readme(origem, destino, *args, **kwargs):
        if Path(origem).name == "README.md":
            raise OSError("disco cheio")
        return original(origem, destino, *args, **kwargs)

    monkeypatch.setattr(copia_seguranca.shutil, "copy2", falha_no_readme)
    assert criar_copia("terceira", raiz=raiz, hoje=date(2026, 10, 3)) == 1
    assert [p.name for p in copias_existentes(raiz)] == ["_backup_2026-10-01_primeira", "_backup_2026-10-02_segunda"]
    assert not (raiz / "_backup_2026-10-03_terceira").exists()


@pytest.mark.parametrize("motivo", ["", "com espaço", "barra/invalida"])
def test_motivo_invalido(tmp_path: Path, motivo: str) -> None:
    assert criar_copia(motivo, raiz=_projeto(tmp_path)) == 1


def test_copia_que_ja_existe_nao_e_sobrescrita(tmp_path: Path) -> None:
    raiz = _projeto(tmp_path)
    assert criar_copia("igual", raiz=raiz, hoje=date(2026, 10, 7)) == 0
    assert criar_copia("igual", raiz=raiz, hoje=date(2026, 10, 7)) == 1
