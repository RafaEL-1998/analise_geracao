"""Testes da conferência da geração com a série oficial de geração por usina (spec 006, US5: FR-027 e FR-028)."""

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
import pytest

from src.conjuntos_ons import ler_arquivo, selecionar_recursos
from src.geracao_ons import DESCRICAO, carregar_geracao_processada, conferir_geracao, executar_geracao_ons, qualidade
from src.models import RecursoONS


def _linha(instante: str, valor: object = "30.000", id_ons: str = "MSUHSD", estado: str = "MS",
           ceg: str = "UHE.PH.MS.028761-0.01") -> dict:
    return {"din_instante": instante, "id_subsistema": "SE", "id_estado": estado, "nom_tipousina": "HIDROELÉTRICA",
            "nom_usina": "São Domingos", "id_ons": id_ons, "ceg": ceg, "val_geracao": valor}


def _gravar(pasta: Path, nome: str, linhas: List[dict]) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / nome
    pd.DataFrame(linhas).to_parquet(caminho, index=False)
    return caminho


def test_arquivos_anuais_ate_2021_e_mensais_depois() -> None:
    nomes = ["GERACAO_USINA-2_2017.parquet", "GERACAO_USINA-2_2018.parquet", "GERACAO_USINA-2_2021.parquet",
             "GERACAO_USINA-2_2022_01.parquet", "GERACAO_USINA-2_2026_09.parquet", "GERACAO_USINA-2_2026_10.parquet"]
    recursos = [RecursoONS(n, n, f"https://ons/g/{n}", "PARQUET", 100, "2026-10-01T00:00:00") for n in nomes]
    escolhidos, _ = selecionar_recursos(DESCRICAO, recursos, pd.Timestamp("2018-08-28"), pd.Timestamp("2026-09-28 23:00"))
    assert [r.nome_recurso for r in escolhidos] == nomes[1:5]


def test_identificacao_e_filtro_na_leitura(tmp_path: Path) -> None:
    linhas = [_linha("2025-01-01 00:00:00"), _linha("2025-01-01 01:00:00", valor="abc"),
              _linha("2025-01-01 00:00:00", estado="GO"),                                   # só o identificador
              _linha("2025-01-01 00:00:00", id_ons="OUTRA"),                                # só a conferência
              _linha("2025-01-01 00:00:00", id_ons="GOUSD", ceg="UHE.PH.GO.027665-0.01", estado="GO")]  # outra usina
    dados, auditoria = ler_arquivo(DESCRICAO, _gravar(tmp_path, "GERACAO_USINA-2_2025_01.parquet", linhas))
    assert auditoria["linhas_lidas"] == 5 and auditoria["linhas_usina"] == 2
    assert (auditoria["linhas_so_identificador"], auditoria["linhas_so_conferencia"]) == (1, 1)
    assert auditoria["valores_invalidos"] == 1
    assert qualidade(dados).tolist() == ["OK", "G1"]


def _ger(valores: List[float], inicio: str = "2025-01-31 22:00") -> pd.DataFrame:
    return pd.DataFrame({"din_instante": pd.date_range(inicio, periods=len(valores), freq="h"), "val_geracao": valores,
                         "qualidade": "OK", "arquivo_origem": "G.parquet"})


def _evt(valores: List[float], inicio: str = "2025-01-31 22:00") -> pd.DataFrame:
    return pd.DataFrame({"din_instante": pd.date_range(inicio, periods=len(valores), freq="h"), "val_geracao": valores})


def test_conferencia_horaria_e_mensal() -> None:
    ger = _ger([30.0, 30.0, 20.0, 21.0, 10.0])            # 31/01 22h e 23h; 01/02 00h a 02h
    evt = _evt([30.0, 30.005, 25.0, 21.0])                 # 01/02 02h só na série oficial
    resumo, mensal, divergencias = conferir_geracao(ger, evt)
    assert (resumo["horas_comuns"], resumo["coincidentes"], resumo["divergentes"]) == (4, 3, 1)
    assert (resumo["so_ons_geracao"], resumo["so_base_evt"]) == (1, 0)
    assert len(divergencias) == 1 and divergencias.iloc[0]["inicio"] == pd.Timestamp("2025-02-01 00:00")
    m = mensal.set_index("mes")
    assert m.loc["2025-01", "energia_base_evt_mwh"] == pytest.approx(60.005)
    assert m.loc["2025-02", "energia_ons_geracao_mwh"] == pytest.approx(51.0)
    assert m.loc["2025-02", "diferenca_mwh"] == pytest.approx(51.0 - 46.0)
    assert m.loc["2025-02", "horas_so_ons_geracao"] == 1


def test_execucao_sem_rede(tmp_path: Path) -> None:
    raw, saida = tmp_path / "raw", tmp_path / "processed"
    _gravar(raw, "GERACAO_USINA-2_2025_01.parquet",
            [_linha(t.strftime("%Y-%m-%d %H:%M:%S")) for t in pd.date_range("2025-01-01", periods=3, freq="h")])
    assert executar_geracao_ons(baixar=False, periodo=(pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-01 02:00")),
                                pasta_raw=raw, pasta_saida=saida) == 0
    serie = carregar_geracao_processada(saida)
    assert serie is not None and len(serie.horaria) == 3
    assert list(serie.horaria.columns) == ["din_instante", "val_geracao", "qualidade", "arquivo_origem"]
