"""Testes da disponibilidade operacional e sincronizada do ONS (spec 006, US3: FR-016 a FR-020)."""

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
import pytest

from src.conjuntos_ons import ler_arquivo, selecionar_recursos
from src.disponibilidade_ons import (
    DESCRICAO,
    carregar_disponibilidade_processada,
    classificar_horas_paradas,
    conferir_com_evt,
    executar_disponibilidade_ons,
    qualidade,
    resumir,
)
from src.models import RecursoONS


def _linha(instante: str, inst: object = "48.00", oper: object = "43.75", sinc: object = "24.00",
           id_ons: str = "MSUHSD", estado: str = "MS") -> dict:
    return {"id_subsistema": "SE", "id_estado": estado, "nom_usina": "São Domingos", "id_ons": id_ons,
            "ceg": "UHE.PH.MS.028761-0.01", "din_instante": instante, "val_potenciainstalada": inst,
            "val_dispoperacional": oper, "val_dispsincronizada": sinc}


def _gravar(pasta: Path, nome: str, linhas: List[dict]) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / nome
    tabela = pd.DataFrame(linhas)
    if caminho.suffix == ".parquet":
        tabela.to_parquet(caminho, index=False)
    else:
        tabela.to_csv(caminho, sep=";", index=False)
    return caminho


def _disp(valores: List[tuple], inicio: str = "2025-01-01 00:00") -> pd.DataFrame:
    """Série horária tratada: (operacional, sincronizada) por hora, instalada 48 MW, qualidade OK."""
    instantes = pd.date_range(inicio, periods=len(valores), freq="h")
    return pd.DataFrame({"din_instante": instantes, "val_potenciainstalada": 48.0,
                         "val_dispoperacional": [v[0] for v in valores], "val_dispsincronizada": [v[1] for v in valores],
                         "qualidade": "OK", "arquivo_origem": "D.csv"})


def _evt(valores: List[tuple], inicio: str = "2025-01-01 00:00") -> pd.DataFrame:
    """Base de EVT: (geração, disponibilidade declarada, EVT) por hora."""
    instantes = pd.date_range(inicio, periods=len(valores), freq="h")
    return pd.DataFrame({"din_instante": instantes, "val_geracao": [v[0] for v in valores],
                         "val_disponibilidade": [v[1] for v in valores],
                         "val_energiavertidaturbinavel": [v[2] for v in valores]})


def test_identificacao_pelo_id_ons_conferido_por_ceg_e_estado(tmp_path: Path) -> None:
    linhas = [_linha("2021-06-01 00:00:00"), _linha("2021-06-01 01:00:00"),
              _linha("2021-06-01 00:00:00", estado="GO"),  # só o identificador confere
              _linha("2021-06-01 00:00:00", id_ons="OUTRA")]  # só a conferência (CEG e estado) confere
    dados, auditoria = ler_arquivo(DESCRICAO, _gravar(tmp_path, "DISPONIBILIDADE_USINA_2021_06.csv", linhas))
    assert len(dados) == 2
    assert (auditoria["linhas_so_identificador"], auditoria["linhas_so_conferencia"]) == (1, 1)
    assert dados["val_dispsincronizada"].tolist() == [24.0, 24.0]


def test_csv_ate_2022_e_parquet_a_partir_de_2023() -> None:
    def recurso(nome: str, formato: str) -> RecursoONS:
        return RecursoONS(nome, nome, f"https://ons/d/{nome}", formato, 100, "2026-10-01T00:00:00")

    meses = pd.period_range("2018-07", "2023-03", freq="M")
    recursos = [recurso(f"DISPONIBILIDADE_USINA_{m.year}_{m.month:02d}.csv", "CSV") for m in meses]
    recursos += [recurso(f"DISPONIBILIDADE_USINA_{m}.parquet", "PARQUET") for m in ("2015_01", "2023_01", "2023_02", "2023_03")]
    escolhidos, _ = selecionar_recursos(DESCRICAO, recursos, pd.Timestamp("2018-08-28"), pd.Timestamp("2023-02-28 23:00"))
    formatos = {r.nome_recurso.split("_", 2)[2].rsplit(".", 1)[0]: r.formato for r in escolhidos}
    assert formatos["2018_08"] == "CSV" and formatos["2022_12"] == "CSV"
    assert formatos["2023_01"] == "PARQUET" and formatos["2023_02"] == "PARQUET"
    assert "2018_07" not in formatos and "2023_03" not in formatos and len(formatos) == 5 + 48 + 2


def test_regras_de_qualidade() -> None:
    horaria = pd.DataFrame({
        "val_potenciainstalada": [48.0, 48.0, 48.0, 48.0, 48.0, 48.0],
        "val_dispoperacional": [44.0, 44.0, 48.5, -1.0, 44.0, 44.005],
        "val_dispsincronizada": [24.0, 44.02, 24.0, -1.0, None, 44.01],
        "_nao_numerico": [False, False, False, False, True, False],
    })
    assert qualidade(horaria).tolist() == ["OK", "D1", "D2", "D3", "D4", "OK"]


def test_conferencia_com_a_disponibilidade_declarada() -> None:
    disp = _disp([(43.75, 24.0), (43.75, 24.0), (40.0, 24.0), (41.0, 24.0), (43.75, 0.0), (43.75, 0.0)])
    evt = _evt([(20, 43.75, 0), (20, 43.755, 0), (20, 43.75, 0), (20, 43.75, 0), (0, 43.75, 0)])
    resumo, divergencias = conferir_com_evt(disp, evt)
    assert (resumo["horas_comuns"], resumo["coincidentes"], resumo["divergentes"]) == (5, 3, 2)
    assert (resumo["so_ons_disponibilidade"], resumo["so_base_evt"]) == (1, 0)
    assert len(divergencias) == 1  # 02h e 03h formam um único período contínuo
    linha = divergencias.iloc[0]
    assert (linha["inicio"], linha["fim"], linha["horas"]) == (pd.Timestamp("2025-01-01 02:00"),
                                                               pd.Timestamp("2025-01-01 03:00"), 2)
    assert linha["diferenca_maxima_mw"] == pytest.approx(3.75)


def test_classificacao_das_horas_paradas() -> None:
    disp = _disp([(43.0, 0.0), (43.0, 24.0), (43.0, 0.0), (43.0, 0.0), (43.0, 24.0), (43.0, 0.5)])
    disp.loc[5, "qualidade"] = "D1"  # hora sinalizada fica fora
    evt = _evt([(0, 43, 5.0), (0.5, 43, 0), (0, 43, 0), (30, 43, 2.0), (1.0, 43, 1.0), (0, 43, 1.0)])
    programacao = pd.DataFrame({"din_instante": pd.to_datetime(["2025-01-01 00:00", "2025-01-01 01:00"]),
                                "classe": ["PARADA_EVT_PROGRAMACAO_ZERO", "PARADA_SEM_EVT"]})
    paradas = classificar_horas_paradas(disp, evt, programacao)
    assert len(paradas) == 4  # 00h, 01h, 02h e 04h (03h está gerando; 05h tem qualidade D1)
    assert paradas["sincronizacao"].tolist() == ["NAO_SINCRONIZADA", "SINCRONIZADA", "NAO_SINCRONIZADA", "SINCRONIZADA"]
    assert paradas["evt"].tolist() == ["COM_EVT", "SEM_EVT", "SEM_EVT", "COM_EVT"]
    assert paradas["classe_programacao"].tolist() == ["PARADA_EVT_PROGRAMACAO_ZERO", "PARADA_SEM_EVT",
                                                      "SEM_PROGRAMACAO", "SEM_PROGRAMACAO"]
    assert paradas.groupby(["sincronizacao", "evt", "classe_programacao"]).size().sum() == len(paradas)


def test_resumo_mensal_com_reserva_desligada() -> None:
    disp = _disp([(48.0, 24.0)] * 24 + [(48.0, 48.0)] * 24, inicio="2025-01-31 00:00")  # 31/01 e 01/02
    evt = _evt([(24.0, 48.0, 0)] * 24 + [(0.0, 48.0, 0)] * 24, inicio="2025-01-31 00:00")
    horas_estado = pd.DataFrame({"mes": pd.to_datetime(["2025-01-01", "2025-01-01", "2025-02-01"]), "ug": [1, 2, 1],
                                 "HRD": [20.0, 4.0, 0.0], "potencia_mw": [24.0, 24.0, 24.0]})
    mensal = resumir(disp, evt, horas_estado, "M").set_index("periodo")
    jan, fev = mensal.loc["2025-01"], mensal.loc["2025-02"]
    assert jan["horas_comuns"] == 24 and jan["disp_sincronizada_media_mw"] == pytest.approx(24.0)
    assert jan["capacidade_nao_sincronizada_media_mw"] == pytest.approx(24.0)
    assert jan["capacidade_nao_sincronizada_mwh"] == pytest.approx(576.0)
    assert jan["reserva_desligada_teif_mwh"] == pytest.approx(576.0)  # (20 + 4) h × 24 MW
    assert jan["diferenca_mwh"] == pytest.approx(0.0)
    assert fev["horas_paradas"] == 24 and fev["horas_paradas_sincronizadas"] == 24
    assert fev["horas_paradas_sem_sincronizacao"] == 0
    anual = resumir(disp, evt, None, "Y")
    assert anual["periodo"].tolist() == ["2025"] and pd.isna(anual.loc[0, "reserva_desligada_teif_mwh"])


def test_execucao_sem_rede(tmp_path: Path) -> None:
    raw, saida = tmp_path / "raw", tmp_path / "processed"
    _gravar(raw, "DISPONIBILIDADE_USINA_2025_01.parquet",
            [_linha(t.strftime("%Y-%m-%d %H:%M:%S")) for t in pd.date_range("2025-01-01", periods=3, freq="h")])
    codigo = executar_disponibilidade_ons(baixar=False, periodo=(pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-01 03:00")),
                                          pasta_raw=raw, pasta_saida=saida)
    assert codigo == 0
    serie = carregar_disponibilidade_processada(saida)
    assert serie is not None and len(serie.horaria) == 3
    assert list(serie.horaria.columns) == ["din_instante", "val_potenciainstalada", "val_dispoperacional",
                                           "val_dispsincronizada", "qualidade", "arquivo_origem"]
    assert serie.ausencias["horas"].tolist() == [1]  # 03h ausente
    assert serie.auditoria["status"].tolist() == ["PROCESSADO"]

    (raw / "DISPONIBILIDADE_USINA_2025_02.parquet").write_bytes(b"corrompido")
    codigo = executar_disponibilidade_ons(baixar=False, periodo=(pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-01 00:00")),
                                          pasta_raw=raw, pasta_saida=saida)
    assert codigo == 2
