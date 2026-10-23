"""Coleta da usina em conjunto (spec da Coleta de dados, FR-054 e FR-060).

Sobre os brutos das usinas fictícias, com a PCH fictícia (em conjunto, sem série própria):
- a usina fora da composição do conjunto declarado no perfil: a Coleta para com o código 2 e a mensagem;
- as unidades das usinas do conjunto (``capacidade_membros.csv``) conferidas pelo subsistema da composição, com as
  linhas em que só o CEG confere contadas na auditoria (princípio IV).
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pandas as pd

from src.__main__ import main
from src.comum import caminhos
from src.comum import perfil as modulo_perfil
from tests.fixtures import brutos_ficticios as bf

PERFIL_PCH = Path(__file__).resolve().parents[1] / "fixtures" / "usinas_ficticias" / "pch" / "perfil.toml"


def _projeto(raiz: Path, monkeypatch, ajustar) -> Path:
    raw = raiz / "data" / "raw"
    bf.gerar_brutos_tipos(raw)
    ajustar(raw)
    (raiz / "usinas" / "pch_ficticia").mkdir(parents=True)
    shutil.copy(PERFIL_PCH, raiz / "usinas" / "pch_ficticia" / "perfil.toml")
    monkeypatch.setattr(caminhos, "DATA_DIR", raiz / "data")
    monkeypatch.setattr(caminhos, "RAW_DATA_DIR", raw)
    monkeypatch.setattr(caminhos, "REPORTS_DIR", raiz / "reports")
    monkeypatch.setattr(modulo_perfil, "RAIZ_PROJETO", raiz)
    return raiz / "data" / "usinas" / "pch_ficticia" / "coleta"


def test_usina_fora_da_composicao_do_conjunto(tmp_path: Path, monkeypatch, caplog) -> None:
    """Sem a linha da usina na Composição dos conjuntos, a série do conjunto não tem hora da usina."""
    def sem_a_pch(raw: Path) -> None:
        arquivo = raw / "usina_conjunto" / "USINA_CONJUNTO.parquet"
        tabela = pd.read_parquet(arquivo)
        tabela[tabela["ceg"] != bf.FICTICIAS["pch"]["ceg"]].to_parquet(arquivo, index=False)

    coleta = _projeto(tmp_path, monkeypatch, sem_a_pch)
    with caplog.at_level(logging.ERROR):
        codigo = main(["coleta", "--usina", "pch_ficticia", "--sem-portal"])
    assert codigo == 2
    erros = " ".join(r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR)
    assert (f"A usina (CEG {bf.FICTICIAS['pch']['ceg']}) não está na Composição dos conjuntos do conjunto "
            f"{bf.CONJUNTO['id_ons']} declarado no perfil") in erros
    assert not (coleta / caminhos.ARQUIVOS_COLETA["trechos"]).exists()  # os demais conjuntos não são coletados


def test_unidades_das_usinas_do_conjunto_conferidas_pelo_subsistema(tmp_path: Path, monkeypatch) -> None:
    """A unidade da térmica do conjunto cadastrada em outro subsistema fica fora e é contada na auditoria."""
    def outro_subsistema(raw: Path) -> None:
        arquivo = raw / "capacidade_geracao" / "CAPACIDADE_GERACAO.parquet"
        tabela = pd.read_parquet(arquivo)
        troca = (tabela["ceg"] == bf.MEMBRO_UTE["ceg"]) & (tabela["num_unidadegeradora"] == "2")
        tabela.loc[troca, "id_subsistema"] = "S"
        tabela.to_parquet(arquivo, index=False)

    coleta = _projeto(tmp_path, monkeypatch, outro_subsistema)
    assert main(["coleta", "--usina", "pch_ficticia", "--sem-portal"]) == 0
    membros = pd.read_csv(coleta / caminhos.ARQUIVOS_COLETA["capacidade_membros"], sep=";", dtype=str,
                          keep_default_na=False)
    ute = membros[membros["ceg"] == bf.MEMBRO_UTE["ceg"]]
    assert list(ute["num_unidadegeradora"]) == ["1"]  # a unidade 2, de outro subsistema, não entra
    auditoria = pd.read_csv(coleta / caminhos.ARQUIVOS_COLETA["auditoria_capacidade_membros"], sep=";",
                            keep_default_na=False)
    assert (int(auditoria.iloc[0]["linhas_usina"]), int(auditoria.iloc[0]["linhas_so_identificador"])) == (
        len(membros), 1)
    assert auditoria.iloc[0]["status"] == "PROCESSADO"
    assert "usinas da composição no período: 3; com unidades: 2" in auditoria.iloc[0]["mensagem"]
