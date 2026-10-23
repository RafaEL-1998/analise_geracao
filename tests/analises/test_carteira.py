"""Indicadores da carteira (spec das Análises, FR-062; plano das Análises, D24).

- chaves fixas, cada indicador com valor, nível e unidade, do último ano completo (ou do ano parcial, marcado);
- vazio (None), e não zero, quando não se aplica ao tipo ou falta a base;
- quantidade de todos os itens de cada lista da conclusão, vazia quando nenhuma regra foi avaliada;
- o caminho com EVT, sobre a tabela anual de hoje.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
import pytest

from src.analises.carteira import INDICADORES_CARTEIRA, ano_dos_indicadores, indicadores_carteira
from src.comum.regras import MAXIMO_ITENS_CONCLUSAO
from tests.fixtures.carteira_ficticia import resultados_vazios

COLUNAS_ANUAIS = ["ano", "nivel", "ano_parcial", "fator_capacidade_pct", "disponibilidade_relativa_pct"]


def _itens(lista: str, n: int, regra: str = "C12") -> List[Dict[str, Any]]:
    return [{"lista": lista, "ordem": i + 1, "regra": regra, "texto": "item", "secoes": []} for i in range(n)]


def _sem_evt(tipo: str, anuais: List[list], completos: List[int], parciais: List[int], **campos: Any):
    res = resultados_vazios()
    res.tipo = tipo
    res.cobertura = {"inicio": pd.Timestamp("2024-01-01"), "fim": pd.Timestamp("2026-09-30 23:00"),
                     "anos_completos": completos, "anos_parciais": parciais}
    res.comum = {"anuais": pd.DataFrame(anuais, columns=COLUNAS_ANUAIS), "cobertura": res.cobertura}
    for nome, valor in campos.items():
        setattr(res, nome, valor)
    return res


def _taxas(meses: List[str], teifa: float = 0.305) -> pd.DataFrame:
    return pd.DataFrame({"mes": pd.to_datetime(meses), "teifa": teifa, "teip": 0.7})


def test_chaves_fixas_com_valor_nivel_e_unidade_na_termica() -> None:
    atendimento = pd.DataFrame({"ano": [2025, 2026], "horas_programadas": [32, 0], "horas_abaixo": [27, 0],
                                "horas_acima": [3, 0]})
    res = _sem_evt("UTE", [[2024, "usina", False, float("nan"), 5.0], [2025, "usina", False, float("nan"), 20.9],
                           [2026, "usina", True, float("nan"), 79.9]], [2024, 2025], [2026],
                   termica={"atendimento": {"anual": atendimento}},
                   ons={"taxas": _taxas(["2025-11-01", "2025-12-01", "2026-09-01"])},
                   conclusao=_itens("possiveis_problemas", 2) + _itens("confirmar_agente", 4),
                   omitidos=[{"item": "C5", "tipo": "regra", "motivo": "sem IP e TEIF de referência"}])
    i = indicadores_carteira(res)
    assert set(i) == {"tipo", "periodo", "ano", "ano_parcial", *INDICADORES_CARTEIRA, "conclusao"}
    assert (i["tipo"], i["ano"], i["ano_parcial"]) == ("UTE", 2025, False)
    assert i["periodo"] == {"inicio": pd.Timestamp("2024-01-01"), "fim": pd.Timestamp("2026-09-30 23:00")}
    assert i["disponibilidade"] == {"valor": pytest.approx(20.9), "nivel": "usina", "unidade": "%"}
    assert i["teifa"]["valor"] == pytest.approx(30.5) and i["teifa"]["mes"] == pd.Timestamp("2025-12-01")
    assert i["atendimento_despacho"] == {"valor": pytest.approx(6.25), "nivel": "usina", "unidade": "%",
                                         "horas_dentro": 2, "horas_programadas": 32}
    assert i["fator_capacidade"] is None and i["energia_cortada"] is None  # não se aplicam: vazios, e não zero
    c = i["conclusao"]
    assert (c["possiveis_problemas"], c["pontos_atencao"], c["confirmar_agente"], c["verificar_campo"]) == (2, 0, 4, 0)
    assert c["regras_nao_avaliadas"] == 1 and c["regras_avaliadas"] > 0


def test_ano_parcial_quando_a_serie_nao_tem_ano_completo() -> None:
    restricao = pd.DataFrame({"periodo": [2026], "pct_estimada": [16.3]})
    res = _sem_evt("UFV", [[2026, "usina", True, 17.2, float("nan")]], [], [2026],
                   renovavel={"restricao": {"anual": restricao}},
                   ons={"taxas": _taxas(["2026-07-01", "2026-08-01"], teifa=0.02)})
    i = indicadores_carteira(res)
    assert (i["ano"], i["ano_parcial"]) == (2026, True)
    assert i["fator_capacidade"]["valor"] == pytest.approx(17.2)
    assert i["energia_cortada"]["valor"] == pytest.approx(16.3)
    assert i["teifa"]["mes"] == pd.Timestamp("2026-08-01")  # no ano parcial, o último mês publicado
    assert i["disponibilidade"] is None and i["atendimento_despacho"] is None
    assert ano_dos_indicadores({}) == (None, False)


def test_teifa_de_dezembro_no_ano_completo() -> None:
    """No ano completo, só a TEIFa de dezembro; sem dezembro publicado, vazia (e não a de outro mês)."""
    res = _sem_evt("UTE", [[2025, "usina", False, float("nan"), 20.0]], [2025], [2026],
                   ons={"taxas": _taxas(["2025-10-01", "2025-11-01", "2026-09-01"])})
    assert indicadores_carteira(res)["teifa"] is None


def test_vazios_sem_a_base_da_usina_e_sem_hora_com_programacao() -> None:
    # usina em conjunto sem série própria: só a linha do conjunto na tabela anual
    res = _sem_evt("PCH", [[2025, "conjunto", False, float("nan"), float("nan")]], [2025], [2026])
    i = indicadores_carteira(res)
    assert all(i[chave] is None for chave in INDICADORES_CARTEIRA)
    atendimento = pd.DataFrame({"ano": [2025], "horas_programadas": [0], "horas_abaixo": [0], "horas_acima": [0]})
    ute = _sem_evt("UTE", [[2025, "usina", False, float("nan"), 0.0]], [2025], [],
                   termica={"atendimento": {"anual": atendimento}})
    i = indicadores_carteira(ute)
    assert i["atendimento_despacho"] is None  # sem hora com programação no ano: vazio, e não zero
    assert i["disponibilidade"] == {"valor": 0.0, "nivel": "usina", "unidade": "%"}  # zero medido continua zero


def test_contagem_de_todos_os_itens_de_cada_lista() -> None:
    n = MAXIMO_ITENS_CONCLUSAO + 3
    res = _sem_evt("UTE", [[2025, "usina", False, float("nan"), 50.0]], [2025], [],
                   conclusao=_itens("possiveis_problemas", n) + _itens("verificar_campo", 1, "C15"))
    c = indicadores_carteira(res)["conclusao"]
    assert c["possiveis_problemas"] == n  # todos, e não só os exibidos no relatório
    assert c["verificar_campo"] == 1


def test_contagens_vazias_sem_regra_avaliada_com_dado_da_usina() -> None:
    res = _sem_evt("PCH", [[2025, "conjunto", False, float("nan"), float("nan")]], [2025], [])
    res.omitidos = [{"item": f"C{k}", "tipo": "regra", "motivo": "só o conjunto"} for k in range(1, 12)]
    c = indicadores_carteira(res)["conclusao"]
    assert [c[k] for k in ("pontos_atencao", "possiveis_problemas", "confirmar_agente", "verificar_campo")] == [None] * 4
    assert (c["regras_avaliadas"], c["regras_nao_avaliadas"]) == (0, 11)


def test_caminho_com_evt_sobre_a_tabela_anual_de_hoje() -> None:
    res = resultados_vazios()
    res.tipo = "UHE"
    res.cobertura = {"inicio": pd.Timestamp("2018-01-01"), "fim": pd.Timestamp("2026-09-30 23:00"),
                     "anos_completos": [2024, 2025], "anos_parciais": [2026]}
    res.indicadores_anuais = pd.DataFrame({"ano": [2024, 2025, 2026], "ano_parcial": [False, False, True],
                                           "fator_capacidade_pct": [57.6, 49.2, 44.9],
                                           "disponibilidade_relativa_pct": [91.2, 91.2, 90.0]})
    res.ons = {"taxas": _taxas(["2025-12-01"], teifa=0.041)}
    res.conclusao = _itens("pontos_atencao", 5, "C1") + _itens("possiveis_problemas", 4, "C2")
    i = indicadores_carteira(res)
    assert i["fator_capacidade"]["valor"] == pytest.approx(49.2)
    assert i["disponibilidade"]["valor"] == pytest.approx(91.2)
    assert i["teifa"]["valor"] == pytest.approx(4.1)
    assert i["energia_cortada"] is None and i["atendimento_despacho"] is None
    c = i["conclusao"]
    assert (c["pontos_atencao"], c["possiveis_problemas"], c["regras_avaliadas"], c["regras_nao_avaliadas"]) == (
        5, 4, 11, 0)  # C1 a C11
