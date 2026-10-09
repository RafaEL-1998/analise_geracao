"""As etapas 2 a 5 não leem ``data/raw/`` (constituição, princípio I; spec 006, achado B1 e decisão R22; tarefa T016).

Roda a Coleta da usina fictícia com os brutos e, depois, o Tratamento, a Conferência, as Análises e o Relatório com
``RAW_DATA_DIR`` apontando para uma pasta vazia. O relatório tem de sair igual ao do fluxo completo normal.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from src.__main__ import main
from src.comum import caminhos
from src.comum import perfil as modulo_perfil
from src.comum.comparacao import comparar
from tests.fixtures.execucao_ficticia import DATA_GERACAO, SLUG, executar_usina_ficticia


def test_etapas_2_a_5_sem_data_raw(tmp_path: Path, monkeypatch) -> None:
    normal = tmp_path / "normal"
    assert executar_usina_ficticia(normal)["codigo"] == 0
    isolada = tmp_path / "isolada"
    shutil.copytree(normal, isolada)
    shutil.rmtree(isolada / "reports")
    vazia = tmp_path / "raw_vazio"
    vazia.mkdir()
    monkeypatch.setattr(caminhos, "DATA_DIR", isolada / "data")
    monkeypatch.setattr(caminhos, "RAW_DATA_DIR", vazia)
    monkeypatch.setattr(caminhos, "REPORTS_DIR", isolada / "reports")
    monkeypatch.setattr(modulo_perfil, "RAIZ_PROJETO", isolada)
    for argumentos in (["tratamento"], ["conferencia"], ["analises"], ["relatorio", "--data-geracao", DATA_GERACAO]):
        assert main([argumentos[0], "--usina", SLUG, *argumentos[1:]]) == 0, argumentos[0]
    assert comparar(isolada / "reports" / SLUG, normal / "reports" / SLUG) == []
