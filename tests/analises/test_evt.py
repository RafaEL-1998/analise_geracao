"""Testes dos indicadores, eventos, distribuições, extremos e constatações da base de EVT (Análises)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.analises.constatacoes import montar_achados
from src.analises.etapa import analisar
from src.analises.evt import calcular_horas_geracao_zero, identificar_eventos, mapear_extremos_historicos, preparar_dados
from src.comum.caminhos import ARQUIVOS_TRATAMENTO, pasta_etapa
from src.comum.formatacao import fmt_pct

EVT_TRATADA = pasta_etapa("sao_domingos", "tratamento") / ARQUIVOS_TRATAMENTO["evt_parquet"]


@pytest.fixture
def df_preparado(df_sintetico: pd.DataFrame) -> pd.DataFrame:
    return preparar_dados(df_sintetico)


@pytest.fixture
def resultados(df_preparado: pd.DataFrame, tmp_path: Path):
    # Auditoria inexistente e sem datas de obtenção: a análise não depende dos arquivos do projeto
    return analisar(df_preparado, {}, tmp_path / "sem_auditoria.csv")


def test_identificar_eventos_quebra_em_lacunas() -> None:
    instantes = pd.to_datetime(
        ["2024-01-01 00:00", "2024-01-01 01:00", "2024-01-01 02:00", "2024-01-01 05:00", "2024-01-01 06:00"]
    )
    df = pd.DataFrame({"din_instante": instantes, "v": [1, 1, 0, 1, 1]})
    eventos = identificar_eventos(df, df["v"] == 1, {"soma": ("v", "sum")})
    assert eventos["duracao_h"].tolist() == [2, 2]
    assert eventos["inicio"].tolist() == [instantes[0], instantes[3]]


def test_cobertura_e_eventos(resultados) -> None:
    c = resultados.cobertura
    assert c["inicio"] == pd.Timestamp("2023-11-01 00:00")
    assert c["fim"] == pd.Timestamp("2024-02-29 23:00")
    assert c["horas_faltantes"] == []
    assert c["anos_parciais"] == [2023, 2024]

    indisponibilidade = resultados.eventos_indisponibilidade_total
    assert indisponibilidade["duracao_h"].tolist() == [30]

    paradas = resultados.eventos_parada_com_evt
    assert paradas["duracao_h"].tolist() == [5]
    assert paradas["inicio"].iloc[0] == pd.Timestamp("2024-02-10 09:00")


def test_mudanca_de_classificacao(resultados) -> None:
    mc = resultados.mudanca_classificacao
    assert mc["mes"] == pd.Period("2024-01", freq="M")
    assert mc["nao_turbinavel_tipica_depois_m3s"] == pytest.approx(5.0)
    assert mc["turbinavel_tipica_antes_m3s"] == pytest.approx(6.0)


def test_indicadores_anuais(resultados, df_preparado) -> None:
    anuais = resultados.indicadores_anuais.set_index("ano")
    esperado_2024 = df_preparado[df_preparado["ano"] == 2024]
    assert anuais.loc[2024, "horas_parada_com_evt"] == 5
    assert anuais.loc[2024, "fator_capacidade_pct"] == pytest.approx(esperado_2024["val_geracao"].mean() / 48 * 100)
    assert anuais.loc[2023, "horas_indisponibilidade_total"] == 30
    assert anuais.loc[2024, "horas_com_anomalia"] == 1


def test_evt_por_faixa_soma_o_total(resultados) -> None:
    faixas = resultados.evt_por_faixa_geracao
    assert faixas["evt_mwh"].sum() == pytest.approx(resultados.globais["evt_mwh"])
    assert faixas["participacao_evt_pct"].sum() == pytest.approx(100.0)


def test_extremos_excluem_registros_sinalizados(df_preparado) -> None:
    extremos = mapear_extremos_historicos(df_preparado).set_index("variavel")
    assert extremos.loc["val_geracao", "maximo_historico"] == pytest.approx(30.0)  # o registro de 60 MW é anômalo


def test_horas_geracao_zero_por_mes(df_preparado) -> None:
    """30 h de indisponibilidade em nov/2023 e 5 h de parada em fev/2024; meses sem dados ficam vazios."""
    tabela = calcular_horas_geracao_zero(df_preparado).set_index("ano")
    assert tabela.loc[2023, "nov"] == 30
    assert tabela.loc[2024, "fev"] == 5
    assert pd.isna(tabela.loc[2023, "jan"])
    assert tabela.loc[2023, "com_disponibilidade_zero"] == 30
    assert tabela.loc[2024, "com_usina_disponivel"] == 5


def test_constatacoes_usam_os_valores_calculados(resultados) -> None:
    """As constatações citam os indicadores calculados e nenhuma conclusão antiga fixa."""
    g = resultados.globais
    texto = " ".join(t for _, t in resultados.achados)
    assert fmt_pct(g["disponibilidade_relativa_pct"]) in texto
    assert fmt_pct(g["fator_capacidade_pct"]) in texto
    assert fmt_pct(g["evt_parada_pct"]) in texto
    for proibido in ["96,1%", "Francis", "18/05/2018", "SATISFAT", "cumpre integralmente", "constrained"]:
        assert proibido not in texto


def test_dados_das_figuras_01_e_05(resultados, df_preparado) -> None:
    diario = resultados.serie_diaria
    assert list(diario.columns) == ["val_disponibilidade", "val_geracao", "val_energiavertidaturbinavel"]
    assert len(diario) == df_preparado["din_instante"].dt.normalize().nunique()
    vazoes = resultados.vazoes_anuais
    assert list(vazoes.index) == [2023, 2024]
    assert vazoes.loc[2024, "val_vazaovertidanaoturbinavel"] == pytest.approx(
        df_preparado.loc[df_preparado["ano"] == 2024, "val_vazaovertidanaoturbinavel"].mean())


@pytest.mark.skipif(not EVT_TRATADA.exists(), reason="tratamento da São Domingos não executado")
def test_integracao_base_real() -> None:
    """Base real: totais consistentes com a própria base (sem fixar valores da série)."""
    df = pd.read_parquet(EVT_TRATADA)
    res = analisar(df, {}, {})
    assert res.globais["horas"] == len(df)
    assert res.globais["evt_mwh"] == pytest.approx(df["val_energiavertidaturbinavel"].sum())
    assert res.indicadores_anuais["horas_observadas"].sum() == len(df)
    assert len(res.achados) == 12
    assert res.horas_geracao_zero["total"].sum() == (df["val_geracao"] == 0).sum()


def test_sem_mudanca_de_classificacao_a_constatacao_nao_aparece(resultados) -> None:
    titulo = "Mudança de classificação do vertimento pelo ONS"
    assert titulo in [t for t, _ in resultados.achados]
    resultados.mudanca_classificacao = {**resultados.mudanca_classificacao, "mes": None}
    assert titulo not in [t for t, _ in montar_achados(resultados)]
