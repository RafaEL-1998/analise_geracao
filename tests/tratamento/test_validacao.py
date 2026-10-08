"""Testes da validação física da base de EVT no Tratamento de dados (regras R1 a R9)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.comum.caminhos import ARQUIVOS_COLETA, dicionario_evt, pasta_etapa
from src.comum.perfil import carregar_perfil
from src.comum.regras import OPERATIONAL_METRIC_COLUMNS
from src.tratamento.validacao import (
    carregar_base_consolidada,
    carregar_dicionario_dados,
    faixa_produtividade,
    gerar_relatorio_validacao_md,
    sinalizar_anomalias,
    validar_regras_fisicas,
    versao_dicionario_dados,
)

PERFIL = carregar_perfil("sao_domingos")
EVT_EXTRAIDA = pasta_etapa("sao_domingos", "coleta") / ARQUIVOS_COLETA["evt"]


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
    if not dicionario_evt().exists():
        pytest.skip("dicionário da EVT ainda não baixado nesta máquina")
    dic = carregar_dicionario_dados()
    assert len(dic) >= 18
    for coluna in OPERATIONAL_METRIC_COLUMNS:
        assert coluna in dic
    assert "2.0" in versao_dicionario_dados()


def test_faixa_de_produtividade_pelo_perfil() -> None:
    minimo, maximo = faixa_produtividade(PERFIL)
    assert minimo == pytest.approx(0.70 * PERFIL.produtividade_nominal_mw_m3s)
    assert maximo == pytest.approx(1.30 * PERFIL.produtividade_nominal_mw_m3s)


def test_regras_linha_conforme() -> None:
    _, resultados = validar_regras_fisicas(_linha(), PERFIL)
    assert len(resultados) == 9
    for r in resultados:
        assert r.violacoes == 0, r.codigo_regra
        assert r.status == "CONFORME"


def test_r1_conta_registros_e_nao_celulas() -> None:
    """Uma linha com dois valores negativos é um único registro violado."""
    _, resultados = validar_regras_fisicas(_linha(val_geracao=-5.0, val_vazaoturbinada=-1.0), PERFIL)
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
    _, resultados = validar_regras_fisicas(_linha(**valores), PERFIL)
    assert _regra(resultados, codigo).violacoes == 1
    assert _regra(resultados, codigo).status == "VIOLADA"


def test_r6_geracao_acima_da_potencia_instalada() -> None:
    _, resultados = validar_regras_fisicas(_linha(val_geracao=68.7), PERFIL)
    assert _regra(resultados, "R6").violacoes == 1


def test_r7_tolerancia_de_geracao_acima_da_disponibilidade() -> None:
    _, dentro = validar_regras_fisicas(_linha(val_geracao=47.3), PERFIL)  # 0,5 MW acima
    _, fora = validar_regras_fisicas(_linha(val_geracao=48.5), PERFIL)  # 1,7 MW acima
    assert _regra(dentro, "R7").violacoes == 0
    assert _regra(fora, "R7").violacoes == 1


def test_r8_produtividade_so_avaliada_com_vazao_turbinada() -> None:
    _, com_vazao = validar_regras_fisicas(_linha(val_produtividade=0.9), PERFIL)
    _, sem_vazao = validar_regras_fisicas(_linha(val_produtividade=0.9, val_vazaoturbinada=0.0, val_geracao=0.0,
                                                 val_folgadegeracao=46.8), PERFIL)
    assert _regra(com_vazao, "R8").violacoes == 1
    assert _regra(sem_vazao, "R8").violacoes == 0


def test_r9_geracao_com_vazao_turbinada_nula() -> None:
    _, resultados = validar_regras_fisicas(_linha(val_vazaoturbinada=0.0), PERFIL)
    assert _regra(resultados, "R9").violacoes == 1


def test_valores_ausentes_nao_violam() -> None:
    _, resultados = validar_regras_fisicas(_linha(val_geracao=float("nan")), PERFIL)
    assert all(r.violacoes == 0 for r in resultados)


def test_sinalizar_anomalias() -> None:
    df = pd.concat([_linha(), _linha(val_geracao=68.7, val_produtividade=0.9)], ignore_index=True)
    sinalizado = sinalizar_anomalias(df, PERFIL)
    assert list(sinalizado["qualidade_registro"]) == ["OK", "R6;R7;R8"]
    assert sinalizado["anomalia_limite_fisico"].tolist() == [False, True]


def test_relatorio_md_reflete_resultado_e_o_perfil(tmp_path) -> None:
    df = pd.concat([_linha(), _linha(val_geracao=68.7)], ignore_index=True)
    df_res, _ = validar_regras_fisicas(df, PERFIL)
    caminho = gerar_relatorio_validacao_md(df_res, PERFIL, tmp_path / "v.md", sinalizar_anomalias(df, PERFIL))
    texto = caminho.read_text(encoding="utf-8")
    assert texto.startswith(f"# Relatório de Validação dos Dados - {PERFIL.usina.nome}")
    assert f"(cod_usina {PERFIL.identificacao.cod_usina} nos arquivos do ONS)" in texto
    assert "**R6** (Valor acima do limite físico da usina): 1 registro viola a regra" in texto
    assert "**R2** (Energia vertida turbinável contida na energia vertida): nenhuma violação" in texto


@pytest.mark.skipif(not EVT_EXTRAIDA.exists(), reason="coleta da São Domingos não executada")
def test_base_real_estrutura() -> None:
    """Base real: uma única usina e nenhum horário duplicado (sem fixar contagens da série)."""
    df_real = carregar_base_consolidada(EVT_EXTRAIDA)
    assert df_real["cod_usina"].nunique() == 1
    assert not df_real["din_instante"].duplicated().any()
    df_res, _ = validar_regras_fisicas(df_real, PERFIL)
    assert set(df_res["codigo_regra"]) == {f"R{i}" for i in range(1, 10)}
