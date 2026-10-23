"""Conferências entre fontes das eólicas e solares: G1, G2 e G5 (spec da Conferência, FR-023 a FR-025; decisão D13).

- G1: a geração entre as fontes, duas a duas e só no mesmo nível;
- G2: a soma das usinas do conjunto só nas horas com toda a composição vigente, contra a geração do conjunto;
- G5: a programação contra a geração programada do Fator de capacidade, no mesmo nível;
- a aplicabilidade de cada uma pelos níveis das bases, com o motivo.
"""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from src.comum.perfil import Membro
from src.comum.regras import TOLERANCIA_COINCIDENCIA_MW
from src.conferencia.aplicabilidade import aplicaveis, tabela_nao_aplicaveis
from src.conferencia.fontes import (
    conferencia_geracao_fontes,
    conferencia_programacao_renovaveis,
    conferencia_soma_conjunto,
    soma_do_conjunto,
)

HORAS = pd.date_range("2024-02-01 00:00", periods=4, freq="h")


def _fonte(valores, nivel: str) -> pd.DataFrame:
    return pd.DataFrame({"din_instante": HORAS[:len(valores)], "valor": valores, "nivel": nivel})


def _perfil(cobertura: dict, id_conjunto: str = "CJU_GOX", membros=()) -> SimpleNamespace:
    return SimpleNamespace(
        usina=SimpleNamespace(tipo="UFV", slug="ufv", estado="GO", modalidade="TIPO II-C", subsistema=None),
        identificacao=SimpleNamespace(ceg="UFV.RS.GO.000070-0.01", id_ons="GOUFX", id_conjunto=id_conjunto,
                                      membros=tuple(membros), cod_usina=None, nome_ons=None, id_reservatorio=None,
                                      cod_programacao="GOUFX", codigos_programacao=("GOUFX",), planejamento=()),
        cobertura=cobertura)


def test_g1_pares_do_mesmo_nivel() -> None:
    r = conferencia_geracao_fontes({
        "geracao": _fonte([10.0, 20.0, 30.0, 40.0], "conjunto"),
        "fator_capacidade": _fonte([10.0, 20.0, 30.5, 40.0], "conjunto"),  # uma hora divergente
        "restricao_detalhe": _fonte([5.0, 6.0, 7.0, 8.0], "usina"),  # só ela na usina: sem par
        "restricao_razao": _fonte([10.0, 20.0, 30.0], "conjunto"),
    })
    assert r.aplicavel and r.unidade == "horas" and r.tolerancia == TOLERANCIA_COINCIDENCIA_MW
    pares = r.tabelas["pares"]
    assert pares[["fonte_a", "fonte_b", "nivel"]].values.tolist() == [
        ["Geração por usina", "Fator de capacidade", "conjunto"],
        ["Geração por usina", "Restrição com a razão", "conjunto"],
        ["Fator de capacidade", "Restrição com a razão", "conjunto"]]
    assert pares["horas_comuns"].tolist() == [4, 3, 3] and pares["divergentes"].tolist() == [1, 0, 1]
    assert (r.comparados, r.coincidentes, r.divergentes) == (10, 8, 2)
    assert list(r.tabelas["mensal"].columns[:3]) == ["fonte_a", "fonte_b", "nivel"]
    assert len(r.tabelas["divergencias"]) == 2 and r.periodo == (HORAS[0], HORAS[3])


def test_g1_sem_par_no_mesmo_nivel_nao_se_aplica() -> None:
    r = conferencia_geracao_fontes({"geracao": _fonte([10.0], "conjunto"), "restricao_detalhe": _fonte([10.0], "usina")})
    assert not r.aplicavel and "mesmo nível" in r.motivo


def test_g2_soma_so_com_toda_a_composicao_vigente() -> None:
    propria = pd.DataFrame({"din_instante": HORAS, "val_geracaoverificada": [4.0, 4.0, 4.0, 4.0]})
    membros_horaria = pd.DataFrame({
        "din_instante": [HORAS[0], HORAS[1], HORAS[3]], "id_ons": "GOUFMB", "val_geracaoverificada": [6.0, 6.0, 6.0]})
    # o membro entra em 01/02 e fica: a hora 02h sem ele não é somada, é contada
    membros = (Membro("GOUFMB", "UFV.RS.GO.000071-0.01", "2024-02-01"),)
    soma, incompletas = soma_do_conjunto(propria, "GOUFX", membros_horaria, membros)
    assert soma["din_instante"].tolist() == [HORAS[0], HORAS[1], HORAS[3]] and incompletas == 1
    assert soma["valor_a"].tolist() == [10.0, 10.0, 10.0] and soma["usinas"].tolist() == [2, 2, 2]
    conjunto = pd.DataFrame({"din_instante": HORAS, "valor_b": [10.0, 10.0, 15.0, 9.0]})
    r = conferencia_soma_conjunto(soma, incompletas, conjunto)
    assert (r.comparados, r.coincidentes, r.divergentes) == (3, 2, 1)
    assert r.tabelas["resumo"]["horas_incompletas"] == 1 and r.tabelas["resumo"]["so_b"] == 1


def test_g2_membro_fora_da_vigencia_nao_exige_valor() -> None:
    propria = pd.DataFrame({"din_instante": HORAS[:2], "val_geracaoverificada": [4.0, 4.0]})
    membros = (Membro("GOUFMB", "UFV.RS.GO.000071-0.01", "2024-03-01"),)  # ainda não fazia parte do conjunto
    soma, incompletas = soma_do_conjunto(propria, "GOUFX", None, membros)
    assert soma["valor_a"].tolist() == [4.0, 4.0] and soma["usinas"].tolist() == [1, 1] and incompletas == 0
    r = conferencia_soma_conjunto(soma.iloc[0:0], 0, None)
    assert not r.aplicavel


def test_g5_programacao_x_fator_de_capacidade() -> None:
    programacao = SimpleNamespace(horaria=pd.DataFrame({"din_instante": HORAS, "geracao_programada_mw": 12.0}))
    fc = pd.DataFrame({"din_instante": HORAS[1:], "val_geracaoprogramada": [12.0, 12.0, 13.0]})
    r = conferencia_programacao_renovaveis(programacao, fc)
    assert r.id == "programacao_renovaveis" and (r.comparados, r.divergentes) == (3, 1)
    assert r.tabelas["resumo"]["so_a"] == 1
    assert not conferencia_programacao_renovaveis(programacao, None).aplicavel


def test_aplicabilidade_pelos_niveis() -> None:
    membros = (Membro("GOUFMB", "UFV.RS.GO.000071-0.01", "2024-01-01"),)
    # a UFV do conjunto: geração, fator de capacidade, razão e programação do conjunto; detalhe próprio
    completa = _perfil({"geracao": "conjunto", "fator_capacidade": "conjunto", "restricao_detalhe": "proprio",
                        "restricao_razao": "conjunto", "programacao": "conjunto"}, membros=membros)
    assert {"geracao_fontes", "soma_conjunto", "programacao_renovaveis"} <= set(aplicaveis(completa))
    # programação da usina e fator de capacidade do conjunto: a G5 não compara níveis diferentes
    niveis = _perfil({"geracao": "conjunto", "fator_capacidade": "conjunto", "programacao": "proprio"})
    motivos = dict(tabela_nao_aplicaveis(niveis, {}).values.tolist())
    assert "níveis diferentes" in motivos["programacao_renovaveis"]
    assert "membros" in motivos["soma_conjunto"]
    # só o detalhe na usina e a geração no conjunto: G1 sem par; a G2 sem a geração do conjunto
    sem_par = _perfil({"geracao": "proprio", "restricao_detalhe": "proprio"}, membros=membros)
    motivos = dict(tabela_nao_aplicaveis(sem_par, {}).values.tolist())
    assert "geracao_fontes" not in motivos  # geração e detalhe da usina: um par
    assert "nível do conjunto" in motivos["soma_conjunto"]
    so_um = _perfil({"geracao": "conjunto", "restricao_detalhe": "proprio"})
    assert "mesmo nível" in dict(tabela_nao_aplicaveis(so_um, {}).values.tolist())["geracao_fontes"]
