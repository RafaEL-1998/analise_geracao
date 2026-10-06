"""Testes unitários e de integração para o módulo validator.py."""

from __future__ import annotations

import pandas as pd
import pytest

from src.config import CONSOLIDATED_FILE, OPERATIONAL_METRIC_COLUMNS
from src.validator import (
    carregar_base_consolidada,
    carregar_dicionario_dados,
    gerar_relatorio_validacao_md,
    sinalizar_anomalias,
    validar_regras_fisicas,
    versao_dicionario_dados,
)


def _linha(**valores) -> pd.DataFrame:
    """Linha conforme (identidades do ONS e limites da usina respeitados), com sobrescritas."""
    base = {
        "val_geracao": 30.5,
        "val_disponibilidade": 46.8,
        "val_vazaoturbinada": 100.0,
        "val_vazaovertida": 6.0,
        "val_vazaovertidanaoturbinavel": 5.0,
        "val_produtividade": 0.305,
        "val_folgadegeracao": 16.3,
        "val_energiavertida": 1.83,
        "val_vazaovertidaturbinavel": 1.0,
        "val_energiavertidaturbinavel": 0.305,
    }
    base.update(valores)
    return pd.DataFrame([{"din_instante": "2024-01-01 00:00:00", **base}])


def _regra(resultados, codigo):
    return next(r for r in resultados if r.codigo_regra == codigo)


def test_carregar_dicionario_dados() -> None:
    dic = carregar_dicionario_dados()
    assert len(dic) >= 18
    for coluna in OPERATIONAL_METRIC_COLUMNS:
        assert coluna in dic
    assert "2.0" in versao_dicionario_dados()


def test_regras_linha_conforme() -> None:
    df_res, resultados = validar_regras_fisicas(_linha())
    assert len(resultados) == 9
    for r in resultados:
        assert r.violacoes == 0, r.codigo_regra
        assert r.status == "CONFORME"


def test_r1_conta_registros_e_nao_celulas() -> None:
    """Uma linha com dois valores negativos é um único registro violado."""
    _, resultados = validar_regras_fisicas(_linha(val_geracao=-5.0, val_vazaoturbinada=-1.0))
    assert _regra(resultados, "R1").violacoes == 1


@pytest.mark.parametrize(
    "codigo, valores",
    [
        ("R2", {"val_energiavertida": 0.1}),
        ("R3", {"val_vazaovertidanaoturbinavel": 5.5}),
        ("R4", {"val_energiavertidaturbinavel": 0.5}),
        ("R5", {"val_folgadegeracao": 2.0}),
    ],
)
def test_identidades_do_ons(codigo, valores) -> None:
    _, resultados = validar_regras_fisicas(_linha(**valores))
    assert _regra(resultados, codigo).violacoes == 1
    assert _regra(resultados, codigo).status == "VIOLADA"


def test_r6_geracao_acima_da_potencia_instalada() -> None:
    _, resultados = validar_regras_fisicas(_linha(val_geracao=68.7))
    assert _regra(resultados, "R6").violacoes == 1


def test_r7_tolerancia_de_geracao_acima_da_disponibilidade() -> None:
    _, dentro = validar_regras_fisicas(_linha(val_geracao=47.3))  # 0,5 MW acima
    _, fora = validar_regras_fisicas(_linha(val_geracao=48.5))  # 1,7 MW acima
    assert _regra(dentro, "R7").violacoes == 0
    assert _regra(fora, "R7").violacoes == 1


def test_r8_produtividade_so_avaliada_com_vazao_turbinada() -> None:
    _, com_vazao = validar_regras_fisicas(_linha(val_produtividade=0.9))
    _, sem_vazao = validar_regras_fisicas(_linha(val_produtividade=0.9, val_vazaoturbinada=0.0, val_geracao=0.0,
                                                 val_folgadegeracao=46.8))
    assert _regra(com_vazao, "R8").violacoes == 1
    assert _regra(sem_vazao, "R8").violacoes == 0


def test_r9_geracao_com_vazao_turbinada_nula() -> None:
    _, resultados = validar_regras_fisicas(_linha(val_vazaoturbinada=0.0))
    assert _regra(resultados, "R9").violacoes == 1


def test_valores_ausentes_nao_violam() -> None:
    _, resultados = validar_regras_fisicas(_linha(val_geracao=float("nan")))
    assert all(r.violacoes == 0 for r in resultados)


def test_sinalizar_anomalias() -> None:
    df = pd.concat([_linha(), _linha(val_geracao=68.7, val_produtividade=0.9)], ignore_index=True)
    sinalizado = sinalizar_anomalias(df)
    assert list(sinalizado["qualidade_registro"]) == ["OK", "R6;R7;R8"]
    assert sinalizado["anomalia_limite_fisico"].tolist() == [False, True]


def test_relatorio_md_reflete_resultado(tmp_path) -> None:
    df = pd.concat([_linha(), _linha(val_geracao=68.7)], ignore_index=True)
    df_res, _ = validar_regras_fisicas(df)
    caminho = gerar_relatorio_validacao_md(df_res, sinalizar_anomalias(df), tmp_path / "v.md")
    texto = caminho.read_text(encoding="utf-8")
    assert "**R6** (Valor acima do limite físico da usina): 1 registro viola a regra" in texto
    assert "**R2** (Energia vertida turbinável contida na energia vertida): nenhuma violação" in texto


@pytest.mark.skipif(not CONSOLIDATED_FILE.exists(), reason="base consolidada não gerada")
def test_base_real_estrutura() -> None:
    """Base real: uma única usina e nenhum horário duplicado (sem fixar contagens da série)."""
    df_real = carregar_base_consolidada()
    assert df_real["cod_usina"].nunique() == 1
    assert not df_real["din_instante"].duplicated().any()
    df_res, _ = validar_regras_fisicas(df_real)
    assert set(df_res["codigo_regra"]) == {f"R{i}" for i in range(1, 10)}
