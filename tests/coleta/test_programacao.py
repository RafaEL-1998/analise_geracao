"""Testes da extração da Programação diária na Coleta de dados (FR-043)."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd

from src.coleta.programacao import (
    COLUNAS_AUDITORIA_PROGRAMACAO,
    COLUNAS_EXTRAIDAS,
    data_interna_confere,
    dia_do_arquivo,
    extrair_programacao,
    ler_arquivo,
    selecionar_recursos_periodo,
)
from src.comum.modelos import RecursoONS

IDENTIFICACAO = ("PRUHSD", "SAO DOMINGOS", "MS")


def _gravar_dia(pasta: Path, dia: str, valores: Optional[List[float]] = None, data_interna: Optional[str] = None,
                patamares: int = 48, extras: Optional[List[dict]] = None) -> Path:
    """Arquivo diário sintético no formato do ONS, com a usina, um homônimo e outra usina."""
    d = pd.Timestamp(dia)
    valores = valores if valores is not None else [22.0] * patamares
    data_interna = data_interna or d.strftime("%Y-%m-%d")
    linhas = []
    for p in range(1, patamares + 1):
        linhas.append({"din_programacaodia": data_interna, "num_patamar": p, "cod_exibicaousina": "PRUHSD",
                       "nom_usina": "SAO DOMINGOS", "id_estado": "MS", "val_geracaoprogramada": f"{valores[p - 1]:.2f}"})
        linhas.append({"din_programacaodia": data_interna, "num_patamar": p, "cod_exibicaousina": "GOUSD",
                       "nom_usina": "UHE SAO DOMINGOS", "id_estado": "GO", "val_geracaoprogramada": "5.00"})
        linhas.append({"din_programacaodia": data_interna, "num_patamar": p, "cod_exibicaousina": "OUTRA",
                       "nom_usina": "OUTRA USINA", "id_estado": "SP", "val_geracaoprogramada": "100.00"})
    linhas += extras or []
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"PROGRAMACAO_DIARIA_{d.strftime('%Y_%m_%d')}.parquet"
    pd.DataFrame(linhas).to_parquet(caminho, index=False)
    return caminho


def test_datas_do_nome_e_data_interna() -> None:
    dia = dia_do_arquivo("PROGRAMACAO_DIARIA_2026_07_01.parquet")
    assert dia == pd.Timestamp("2026-07-01")
    assert data_interna_confere(pd.Series(["2026-07-01"]), dia)
    assert data_interna_confere(pd.Series(["01/07/2026"]), dia)
    assert data_interna_confere(pd.Series(["2026-07-01 00:00:00"]), dia)
    assert not data_interna_confere(pd.Series(["07/01/2026"]), dia)
    assert dia_do_arquivo("TAXA_TEIF_TEIP.parquet") is None


def test_selecao_de_recursos_pelo_periodo() -> None:
    recursos = [RecursoONS("id", n, f"https://ons/x/{n}", "PARQUET")
                for n in ("PROGRAMACAO_DIARIA_2024_09_30.parquet", "PROGRAMACAO_DIARIA_2024_10_01.parquet",
                          "PROGRAMACAO_DIARIA_2026_09_28.parquet", "PROGRAMACAO_DIARIA_2026_09_29.parquet")]
    selecionados = selecionar_recursos_periodo(recursos, pd.Timestamp("2024-10-01 05:00"), pd.Timestamp("2026-09-28 23:00"))
    assert [r.nome_recurso for r in selecionados] == ["PROGRAMACAO_DIARIA_2024_10_01.parquet",
                                                       "PROGRAMACAO_DIARIA_2026_09_28.parquet"]


def test_extracao_ignora_homonimos_e_aceita_data_brasileira(tmp_path: Path) -> None:
    caminho = _gravar_dia(tmp_path, "2026-07-01", data_interna="01/07/2026")
    linhas, auditoria = ler_arquivo(caminho, *IDENTIFICACAO)
    assert list(linhas.columns) == COLUNAS_EXTRAIDAS and len(linhas) == 48
    assert set(linhas["geracao_programada_mw"]) == {22.0}
    assert auditoria["status"] == "PROCESSADO"
    assert auditoria["linhas_lidas"] == 144 and auditoria["linhas_usina"] == 48
    assert auditoria["data_interna_confere"] is True


def test_identificacao_parcial_e_valor_invalido(tmp_path: Path) -> None:
    extras = [
        # código confere, estado não (só identificador)
        {"din_programacaodia": "2026-07-04", "num_patamar": 1, "cod_exibicaousina": "PRUHSD",
         "nom_usina": "SAO DOMINGOS", "id_estado": "GO", "val_geracaoprogramada": "1.00"},
        # nome e estado conferem, código não (só conferência)
        {"din_programacaodia": "2026-07-04", "num_patamar": 1, "cod_exibicaousina": "MSUHSX",
         "nom_usina": "SÃO DOMINGOS", "id_estado": "MS", "val_geracaoprogramada": "1.00"},
    ]
    valores = [22.0] * 48
    caminho = _gravar_dia(tmp_path, "2026-07-04", valores=valores, extras=extras)
    tabela = pd.read_parquet(caminho)
    tabela.loc[(tabela["cod_exibicaousina"] == "PRUHSD") & (tabela["num_patamar"] == 2)
               & (tabela["id_estado"] == "MS"), "val_geracaoprogramada"] = "n/d"
    tabela.to_parquet(caminho, index=False)
    linhas, auditoria = ler_arquivo(caminho, *IDENTIFICACAO)
    assert (auditoria["linhas_codigo_sem_conferencia"], auditoria["linhas_so_conferencia"]) == (1, 1)
    assert auditoria["valores_invalidos"] == 1 and auditoria["linhas_lidas"] == 146
    assert pd.isna(linhas.loc[linhas["num_patamar"] == 2, "geracao_programada_mw"]).all()


def test_dia_incompleto_e_data_divergente(tmp_path: Path) -> None:
    caminho = _gravar_dia(tmp_path, "2026-07-02", data_interna="2026-07-03", patamares=46)
    _, auditoria = ler_arquivo(caminho, *IDENTIFICACAO)
    assert auditoria["status"] == "INCOMPLETO"
    assert auditoria["patamares"] == 46
    assert auditoria["data_interna_confere"] is False


def test_extracao_do_periodo_com_falha_e_arquivo_corrompido(tmp_path: Path) -> None:
    _gravar_dia(tmp_path, "2026-07-01")
    _gravar_dia(tmp_path, "2026-07-03", data_interna="03/07/2026")
    _gravar_dia(tmp_path, "2026-07-05")  # fora do período
    (tmp_path / "PROGRAMACAO_DIARIA_2026_07_02.parquet").write_bytes(b"corrompido")
    falhas = [{"arquivo": "PROGRAMACAO_DIARIA_2026_07_04.parquet", "dia": pd.Timestamp("2026-07-04"),
               "formato": "PARQUET", "status": "FALHA", "mensagem": "HTTP 500"}]
    extraido, auditoria = extrair_programacao(tmp_path, pd.Timestamp("2026-07-01"), pd.Timestamp("2026-07-04 23:00"),
                                              *IDENTIFICACAO, falhas=falhas)
    assert list(auditoria.columns) == COLUNAS_AUDITORIA_PROGRAMACAO
    assert auditoria["status"].tolist() == ["PROCESSADO", "FALHA", "PROCESSADO", "FALHA"]
    assert auditoria["obtido"].tolist() == [True, True, True, False]
    assert auditoria["dia"].dt.day.tolist() == [1, 2, 3, 4]
    assert len(extraido) == 96 and set(extraido["dia"].dt.day) == {1, 3}


def test_identificacao_parcial_e_avisada_no_log(tmp_path: Path, caplog) -> None:
    """Spec da Coleta de dados (FR-036): linhas só com o código ou só com a conferência são avisadas, com o arquivo."""
    import logging

    extras = [{"din_programacaodia": "2026-07-04", "num_patamar": 1, "cod_exibicaousina": "PRUHSD",
               "nom_usina": "SAO DOMINGOS", "id_estado": "GO", "val_geracaoprogramada": "1.00"}]
    caminho = _gravar_dia(tmp_path, "2026-07-04", extras=extras)
    with caplog.at_level(logging.WARNING, logger="coleta"):
        ler_arquivo(caminho, *IDENTIFICACAO)
    assert caminho.name in caplog.text and "verificar mudança de cadastro" in caplog.text
