"""Gravadores dos dados das etapas com cópia de segurança (.bak da versão anterior, conteúdo igual não regravado)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable, Dict

import pandas as pd
import pytest

from src.coleta.evt import save_audit_report, save_consolidated_records
from src.comum.modelos import AuditoriaArquivo, RegistroEnergiaVertida
from src.comum.perfil import carregar_perfil
from src.tratamento.evt import exportar_csv, exportar_excel, exportar_parquet
from src.tratamento.indicadores import carregar_indicadores_tratados, exportar_indicadores
from src.tratamento.programacao import ProgramacaoONS, carregar_programacao_tratada, exportar_programacao
from src.tratamento.validacao import gerar_relatorio_validacao_csv, gerar_relatorio_validacao_md, validar_regras_fisicas
from tests.tratamento.test_indicadores import _indicadores_sinteticos

PERFIL = carregar_perfil("sao_domingos")


def _estado(pasta: Path) -> Dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(pasta.iterdir()) if p.is_file()}


def _registros(valor: float) -> list:
    return [RegistroEnergiaVertida("SE", "SUDESTE", "PARANA", "VERDE", "AXIA SUL", "SAO DOMINGOS", "153",
                                   f"2026-08-01 0{h}:00:00", val_geracao=valor + h, arquivo_origem="X.csv")
            for h in range(2)]


def _programacao(fator: float) -> ProgramacaoONS:
    horaria = pd.DataFrame({"din_instante": pd.date_range("2026-01-01", periods=3, freq="h"),
                            "geracao_programada_mw": [10.0 * fator, 0.0, 5.0]})
    return ProgramacaoONS(horaria=horaria, dias_ausentes=pd.DataFrame(columns=["dia"]),
                          auditoria=pd.DataFrame({"arquivo": ["P.parquet"], "status": ["PROCESSADO"]}))


def _gravadores(df_sintetico: pd.DataFrame) -> Dict[str, Callable[[Path, float], None]]:
    def tratado(fator: float) -> pd.DataFrame:
        df = df_sintetico.head(24).copy()
        df["val_geracao"] = df["val_geracao"] * fator
        return df

    def validacao(pasta: Path, fator: float) -> None:
        df_res, _ = validar_regras_fisicas(tratado(fator), PERFIL)
        gerar_relatorio_validacao_md(df_res, PERFIL, pasta / "relatorio_validacao_fisica.md", tratado(fator))
        gerar_relatorio_validacao_csv(df_res.assign(fator=fator), pasta / "relatorio_validacao_fisica.csv")

    def indicadores(pasta: Path, fator: float) -> None:
        ind = _indicadores_sinteticos()
        ind.ug_anual = ind.ug_anual.assign(dispf=ind.ug_anual["dispf"] * fator)
        exportar_indicadores(ind, pasta)

    return {
        "consolidacao": lambda pasta, fator: (
            save_consolidated_records(_registros(fator), pasta / "consolidado.csv"),
            save_audit_report([AuditoriaArquivo("X.csv", "2026-08", total_linhas_arquivo=int(fator),
                                                data_hora_processamento="2026-10-05 10:00:00")],
                              pasta / "auditoria.csv"),
        ),
        "tratado_csv": lambda pasta, fator: exportar_csv(tratado(fator), pasta / "tratado.csv"),
        "tratado_parquet": lambda pasta, fator: exportar_parquet(tratado(fator), pasta / "tratado.parquet"),
        "tratado_xlsx": lambda pasta, fator: exportar_excel(tratado(fator), pasta / "tratado.xlsx", "UHE_SAO_DOMINGOS"),
        "validacao": validacao,
        "indicadores": indicadores,
        "programacao": lambda pasta, fator: exportar_programacao(_programacao(fator), pasta),
    }


@pytest.mark.parametrize("nome", ["consolidacao", "tratado_csv", "tratado_parquet", "tratado_xlsx", "validacao",
                                  "indicadores", "programacao"])
def test_gravador_guarda_versao_anterior_e_nao_regrava_conteudo_igual(nome: str, df_sintetico: pd.DataFrame,
                                                                     tmp_path: Path) -> None:
    gravar = _gravadores(df_sintetico)[nome]
    gravar(tmp_path, 1.0)
    primeira = _estado(tmp_path)
    assert primeira and not any(n.endswith((".bak", ".tmp")) for n in primeira)

    gravar(tmp_path, 1.0)  # mesmo conteúdo: nada muda, nenhuma cópia
    assert _estado(tmp_path) == primeira

    gravar(tmp_path, 2.0)  # conteúdo novo: a versão anterior vai para <nome>.bak
    segunda = _estado(tmp_path)
    alterados = [n for n in primeira if segunda[n] != primeira[n]]
    assert alterados
    for arquivo in alterados:
        assert segunda[f"{arquivo}.bak"] == primeira[arquivo]
    assert not any(n.endswith(".tmp") for n in segunda)


def test_leitores_ignoram_bak_e_tmp(tmp_path: Path, df_sintetico: pd.DataFrame) -> None:
    exportar_indicadores(_indicadores_sinteticos(), tmp_path)
    exportar_programacao(_programacao(1.0), tmp_path)
    exportar_parquet(df_sintetico, tmp_path / "evt_tratado.parquet")
    for arquivo in list(tmp_path.iterdir()):
        (tmp_path / f"{arquivo.name}.bak").write_text("versão antiga corrompida", encoding="utf-8")
        (tmp_path / f"{arquivo.name}.tmp").write_text("gravação interrompida", encoding="utf-8")

    ind = carregar_indicadores_tratados(tmp_path)
    prog = carregar_programacao_tratada(tmp_path)
    assert ind is not None and len(ind.horas_estado) == len(_indicadores_sinteticos().horas_estado)
    assert prog is not None and len(prog.horaria) == 3
