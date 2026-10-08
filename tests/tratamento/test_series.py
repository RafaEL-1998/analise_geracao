"""Testes das séries horárias no Tratamento de dados: hora de início, duplicatas, recorte, ausências e gravação."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import List

import pandas as pd

from src.coleta.conjuntos import DescricaoConjunto, Regra, extrair_conjunto
from src.tratamento.series import (
    COLUNAS_AUDITORIA,
    carregar_serie_processada,
    exportar_serie,
    hora_de_inicio,
    listar_ausencias,
    montar_serie,
)

DESC = DescricaoConjunto(
    pacote="conjunto_teste",
    pasta="conjunto_teste",
    identificador=Regra("id_ons", "MSUHSD"),
    conferencias=(Regra("ceg", "UHE.PH.MS.028761-0.01"), Regra("id_estado", "MS")),
    colunas_valor=("val_a", "val_b"),
)


def _linhas_usina(inicio: str, horas: int, valor: float = 10.0) -> List[dict]:
    instantes = pd.date_range(inicio, periods=horas, freq="h")
    return [{"id_ons": "MSUHSD", "ceg": "UHE.PH.MS.028761-0.01", "id_estado": "MS", "nom_usina": "São Domingos",
             "din_instante": t.strftime("%Y-%m-%d %H:%M:%S"), "val_a": f"{valor:.2f}", "val_b": "1.00"} for t in instantes]


def _homonimos(instante: str) -> List[dict]:
    return [{"id_ons": "GOUSD", "ceg": "UHE.PH.GO.027665-0.01", "id_estado": "GO", "nom_usina": "São Domingos I",
             "din_instante": instante, "val_a": "1", "val_b": "1"}]


def _gravar(pasta: Path, nome: str, linhas: List[dict]) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / nome
    pd.DataFrame(linhas).to_csv(caminho, sep=";", index=False, encoding="utf-8")
    return caminho


def _serie(desc: DescricaoConjunto, pasta: Path, inicio: str, fim: str, falhas=None):
    inicio_ts, fim_ts = pd.Timestamp(inicio), pd.Timestamp(fim)
    extraido, auditoria = extrair_conjunto(desc, pasta, inicio_ts, fim_ts, falhas)
    return montar_serie(desc, extraido, auditoria, inicio_ts, fim_ts)


def test_hora_de_inicio_na_convencao_de_fim_de_hora() -> None:
    publicados = pd.to_datetime(pd.Series(["2025-01-01 01:00:00", "2025-01-01 15:00:00", "2025-01-01 23:59:00"]))
    assert hora_de_inicio(publicados).dt.strftime("%Y-%m-%d %H:%M").tolist() == [
        "2025-01-01 00:00", "2025-01-01 14:00", "2025-01-01 23:00"]


def test_montagem_deduplica_e_lista_ausencias(tmp_path: Path) -> None:
    pasta = tmp_path / "conjunto_teste"
    # janeiro completo menos 3 horas; fevereiro com arquivo mas sem a usina; março sem arquivo
    janeiro = [l for i, l in enumerate(_linhas_usina("2025-01-01 00:00", 31 * 24)) if i not in (10, 11, 500)]
    _gravar(pasta, "D_2025_01.csv", janeiro)
    _gravar(pasta, "D_2025_02.csv", _homonimos("2025-02-01 00:00:00"))
    # arquivo publicado depois, repetindo a última hora de janeiro com outro valor
    _gravar(pasta, "D_2025_04.csv", _linhas_usina("2025-01-31 23:00", 1, valor=99.0) + _linhas_usina("2025-04-01 00:00", 2))
    (pasta / "_manifesto_ons.json").write_text(json.dumps({
        "D_2025_01.csv": {"ultima_modificacao": "2025-02-01T00:00:00", "recursos_duplicados_catalogo": 1},
        "D_2025_02.csv": {"ultima_modificacao": "2025-03-01T00:00:00"},
        "D_2025_04.csv": {"ultima_modificacao": "2025-05-01T00:00:00"},
    }), encoding="utf-8")
    serie = _serie(DESC, pasta, "2025-01-01 00:00", "2025-04-01 01:00")

    h = serie.horaria.set_index("din_instante")
    assert h.loc[pd.Timestamp("2025-01-31 23:00"), "val_a"] == 99.0  # prevalece o arquivo mais recente
    assert h.loc[pd.Timestamp("2025-01-31 23:00"), "arquivo_origem"] == "D_2025_04.csv"
    assert h.index.is_unique and h.index.min() >= pd.Timestamp("2025-01-01") and h.index.max() <= pd.Timestamp("2025-04-01 01:00")

    assert list(serie.auditoria.columns) == COLUNAS_AUDITORIA
    aud = serie.auditoria.set_index("arquivo")
    assert aud.loc["D_2025_01.csv", "duplicatas_conflitantes"] == 1
    assert aud.loc["D_2025_01.csv", "recursos_duplicados_catalogo"] == 1
    assert aud.loc["D_2025_01.csv", "horas_usina"] == 31 * 24 - 3
    assert aud.loc["D_2025_02.csv", "status"] == "SEM_REGISTROS" and aud.loc["D_2025_02.csv", "horas_usina"] == 0

    aus = serie.ausencias
    assert aus[aus["tipo"] == "HORAS"][["horas"]].squeeze().tolist() == [2, 1]
    assert aus[aus["tipo"] == "MES_SEM_USINA"]["inicio"].dt.month.tolist() == [2]
    sem_arquivo = aus[aus["tipo"] == "MES_SEM_ARQUIVO"]
    assert sem_arquivo["inicio"].dt.month.tolist() == [3] and sem_arquivo["horas"].tolist() == [31 * 24]


def test_convencao_de_fim_de_hora_guarda_o_instante_publicado(tmp_path: Path) -> None:
    pasta = tmp_path / "hidrologia"
    linhas = _linhas_usina("2025-01-01 01:00", 23)
    linhas.append({**linhas[-1], "din_instante": "2025-01-01 23:59:00"})
    _gravar(pasta, "H_2025_01.csv", linhas)
    serie = _serie(replace(DESC, convencao_hora="fim"), pasta, "2025-01-01 00:00", "2025-01-01 23:00")
    h = serie.horaria
    assert list(h.columns[:2]) == ["din_instante", "din_instante_publicado"]
    assert h["din_instante"].iloc[0] == pd.Timestamp("2025-01-01 00:00")
    assert h["din_instante"].iloc[-1] == pd.Timestamp("2025-01-01 23:00")
    assert h["din_instante_publicado"].iloc[-1] == pd.Timestamp("2025-01-01 23:59")
    assert serie.ausencias.empty and serie.auditoria.loc[0, "horas_usina"] == 24


def test_falhas_de_download_entram_na_auditoria(tmp_path: Path) -> None:
    pasta = tmp_path / "conjunto_teste"
    _gravar(pasta, "D_2025_01.csv", _linhas_usina("2025-01-01 00:00", 2))
    falhas = [{"arquivo": "D_2025_02.csv", "formato": "CSV", "periodo": "2025-02", "status": "FALHA",
               "mensagem": "HTTP 500"}]
    serie = _serie(DESC, pasta, "2025-01-01", "2025-01-01 01:00", falhas)
    aud = serie.auditoria.set_index("arquivo")
    assert aud.loc["D_2025_02.csv", "status"] == "FALHA" and aud.loc["D_2025_02.csv", "horas_usina"] == 0
    assert aud.loc["D_2025_02.csv", "mensagem"] == "HTTP 500"


def test_listar_ausencias_agrupa_horas_continuas() -> None:
    presentes = pd.Series(pd.date_range("2025-01-01", "2025-01-01 23:00", freq="h").delete([5, 6, 7, 20]))
    aus = listar_ausencias(presentes, pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-01 23:00"), {(2025, 1)})
    assert aus[["inicio", "fim", "horas"]].astype(str).values.tolist() == [
        ["2025-01-01 05:00:00", "2025-01-01 07:00:00", "3"], ["2025-01-01 20:00:00", "2025-01-01 20:00:00", "1"]]


def test_exportar_e_carregar_ignorando_bak_e_tmp(tmp_path: Path) -> None:
    pasta = tmp_path / "conjunto_teste"
    _gravar(pasta, "D_2025_01.csv", _linhas_usina("2025-01-01 00:00", 2))
    serie = _serie(DESC, pasta, "2025-01-01", "2025-01-01 01:00")
    saida = tmp_path / "tratamento"
    arquivos = {"horaria": saida / "h.csv", "ausencias": saida / "a.csv", "auditoria": saida / "r.csv"}
    exportar_serie(serie, arquivos)
    (saida / "h.csv.bak").write_text("lixo", encoding="utf-8")
    (saida / "h.csv.tmp").write_text("lixo", encoding="utf-8")
    lida = carregar_serie_processada(arquivos)
    assert lida is not None and len(lida.horaria) == 2
    assert not any(c.startswith("_") for c in lida.horaria.columns)
    assert lida.horaria["din_instante"].dtype.kind == "M"
    assert carregar_serie_processada({"horaria": saida / "nao_existe.csv"}) is None
