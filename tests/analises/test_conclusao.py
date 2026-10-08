"""Conclusão do relatório: regras C1 a C11, limite por lista, linguagem de indício e ordem (Análises)."""

from __future__ import annotations

import re
from typing import Any, Dict

import pandas as pd
import pytest

from src.analises.conclusao import montar_conclusao
from src.analises.etapa import analisar
from src.analises.evt import preparar_dados
from src.analises.hidrologia import (
    ACIMA_ENGOLIMENTO_USINA,
    ATE_UMA_UNIDADE,
    entre_unidades,
    SEM_DADO_HIDROLOGICO,
)

LISTAS = ("pontos_atencao", "possiveis_problemas", "confirmar_agente", "verificar_campo")
PROIBIDOS = ("satisfatório", "insatisfatório", "descumpr", "deficiente", "falha do agente", "culpa")


@pytest.fixture
def df_base(df_sintetico: pd.DataFrame) -> pd.DataFrame:
    return preparar_dados(df_sintetico)


def _neutro(df: pd.DataFrame):
    """Resultados sintéticos em que nenhuma regra da conclusão dispara."""
    res = analisar(df, {})
    res.globais = {**res.globais, "evt_parada_pct": 0.0, "evt_parada_mwh": 0.0, "horas_parada_com_evt": 0,
                   "desvio_disponibilidade_referencia_pp": 1.0, "geracao_sobre_garantia_fisica_pct": 120.0}
    anuais = res.indicadores_anuais.copy()
    anuais["razao_evt_diurna_noturna"] = 1.0
    anuais["razao_geracao_diurna_noturna"] = 1.0
    anuais["evt_mwh"] = [float(len(anuais) - i) for i in range(len(anuais))]  # o último ano não é o de maior EVT
    anuais["evt_parada_mwh"] = 0.0
    res.indicadores_anuais = anuais
    res.resumo_anomalias = res.resumo_anomalias.assign(horas=0)
    res.eventos_indisponibilidade_total = res.eventos_indisponibilidade_total.iloc[0:0]
    res.ons, res.programacao, res.disponibilidade, res.hidrologia = {}, {}, {}, {}
    return res


def _por_regra(res, regra: str) -> Dict[str, Dict[str, Any]]:
    return {i["lista"]: i for i in montar_conclusao(res) if i["regra"] == regra}


def _ons(teifa: float = 4.11, participacao_hedf_ug2: float = 87.3, meses_hedf_ug2: int = 78,
         ug_anual: pd.DataFrame | None = None, divergencias: int = 0) -> Dict[str, Any]:
    """Indicadores do ONS no formato de ``analisar_indicadores_ons``, com números da base real."""
    decomposicao = pd.DataFrame([
        {"taxa": "TEIFa", "ug": 1, "parcela": "HDF", "horas": 256.1, "contribuicao_pp": 0.307, "participacao_pct": 7.5},
        {"taxa": "TEIFa", "ug": 1, "parcela": "HEDF", "horas": 46.7, "contribuicao_pp": 0.056, "participacao_pct": 1.4},
        {"taxa": "TEIFa", "ug": 2, "parcela": "HDF", "horas": 134.3, "contribuicao_pp": 0.161, "participacao_pct": 3.9},
        {"taxa": "TEIFa", "ug": 2, "parcela": "HEDF", "horas": 2991.7, "contribuicao_pp": 3.585,
         "participacao_pct": participacao_hedf_ug2},
    ])
    meses = pd.date_range("2020-01-01", periods=80, freq="MS")
    horas = pd.DataFrame([
        {"mes": m, "ug": ug, "HDF": 1.0,
         "HEDF": 40.0 if (ug == 2 and i < meses_hedf_ug2) else (2.0 if (ug == 1 and i < 21) else 0.0)}
        for i, m in enumerate(meses) for ug in (1, 2)
    ])
    ons = {"taxa_ultima": {"mes": pd.Timestamp("2026-08-01"), "teifa_pct": teifa, "teip_pct": 4.79,
                           "disponibilidade_verificada_pct": 91.3},
           "decomposicao": decomposicao, "horas_mensal": horas,
           "divergencias": pd.DataFrame({"mes": [pd.Timestamp("2024-03-01")] * divergencias, "ug": [2] * divergencias})}
    if ug_anual is not None:
        ons["ug_anual"] = ug_anual
    return ons


def _programacao(eventos: int = 68, pct_zero: float = 91.1) -> Dict[str, Any]:
    maior = {"inicio": pd.Timestamp("2026-05-01 21:00"), "fim": pd.Timestamp("2026-05-02 09:00"), "duracao_h": 13,
             "programacao_media_mw": 21.2} if eventos else None
    return {"periodo": {"horas_desvio": 182 if eventos else 0, "eventos_desvio": eventos, "maior_evento": maior,
                        "pct_horas_programacao_zero": pct_zero, "horas_parada_com_evt": 1908,
                        "horas_parada_evt_programacao_zero": 1739}}


def _hidrologia(cabia: bool = True, sinalizadas: int = 0) -> Dict[str, Any]:
    faixas = ({ATE_UMA_UNIDADE: 14633, entre_unidades(): 42091, ACIMA_ENGOLIMENTO_USINA: 4010,
               SEM_DADO_HIDROLOGICO: 333} if cabia else
              {ATE_UMA_UNIDADE: 1000, entre_unidades(): 2000, ACIMA_ENGOLIMENTO_USINA: 58000,
               SEM_DADO_HIDROLOGICO: 333})
    return {"publicado": True, "resumo": {"horas_por_faixa": faixas, "horas_evt": sum(faixas.values()),
                                          "horas_sinalizadas": sinalizadas}}


def _anomalias(res, r7: int = 0, r9: int = 0) -> pd.DataFrame:
    t = res.resumo_anomalias.copy()
    t.loc[t["regra"] == "R7", "horas"] = r7
    t.loc[t["regra"] == "R9", "horas"] = r9
    return t


def _tudo(df: pd.DataFrame):
    """Resultados em que todas as regras disparam, com números da base real."""
    res = _neutro(df)
    res.globais.update(evt_parada_pct=28.4, evt_parada_mwh=41_900.0, horas_parada_com_evt=2141,
                       desvio_disponibilidade_referencia_pp=-3.2, disponibilidade_relativa_pct=87.8,
                       disponibilidade_referencia_pct=91.0, geracao_sobre_garantia_fisica_pct=74.4)
    anuais = res.indicadores_anuais
    anuais["razao_evt_diurna_noturna"] = 5.5
    anuais["razao_geracao_diurna_noturna"] = 0.6
    anuais.loc[anuais.index[-1], "evt_parada_mwh"] = 41_900.0
    ug_anual = pd.DataFrame([{"ano": 2019, "ug": 1, "dispf": 74.37, "indisppf": 25.35, "indispff": 0.28, "dmdff": 1.4,
                              "ano_parcial": False}])
    res.ons = _ons(ug_anual=ug_anual, divergencias=4)
    res.programacao = _programacao()
    res.hidrologia = _hidrologia(sinalizadas=13)
    res.disponibilidade = {"anual": pd.DataFrame({"periodo": ["2024", "2025"], "ano_parcial": [False, False],
                                                  "reserva_desligada_teif_mwh": [50_000.0, 60_000.0],
                                                  "diferenca_mwh": [-11_700.0, -12_400.0]})}
    res.resumo_anomalias = _anomalias(res, r7=293, r9=63)
    res.eventos_indisponibilidade_total = pd.DataFrame({"inicio": [pd.Timestamp("2019-09-25 10:00")],
                                                        "fim": [pd.Timestamp("2019-12-24 23:00")],
                                                        "duracao_h": [2174]})
    return res


def test_nenhuma_regra_dispara(df_base: pd.DataFrame) -> None:
    assert montar_conclusao(_neutro(df_base)) == []


def test_c1_paradas_com_evt(df_base: pd.DataFrame) -> None:
    res = _neutro(df_base)
    res.globais.update(evt_parada_pct=28.4, evt_parada_mwh=41_900.0, horas_parada_com_evt=2141)
    res.indicadores_anuais.loc[res.indicadores_anuais.index[-1], "evt_parada_mwh"] = 41_900.0
    itens = _por_regra(res, "C1")
    assert set(itens) == {"pontos_atencao", "confirmar_agente", "verificar_campo"}
    assert "41,9 GWh" in itens["pontos_atencao"]["texto"] and "28,4%" in itens["pontos_atencao"]["texto"]
    assert "programação" not in itens["pontos_atencao"]["texto"]
    res.programacao = _programacao()
    assert "91,1%" in _por_regra(res, "C1")["pontos_atencao"]["texto"]
    res.programacao = _programacao(pct_zero=40.0)
    assert "91,1%" not in _por_regra(res, "C1")["pontos_atencao"]["texto"]
    res.globais.update(evt_parada_pct=9.9)
    assert _por_regra(res, "C1") == {}


def test_c2_unidade_geradora(df_base: pd.DataFrame) -> None:
    res = _neutro(df_base)
    res.ons = _ons()
    itens = _por_regra(res, "C2")
    assert set(itens) == {"possiveis_problemas", "confirmar_agente", "verificar_campo"}
    texto = itens["possiveis_problemas"]["texto"]
    assert "UG2" in texto and "UG1:" not in texto.split("(")[0]
    assert "78 dos 80 meses" in texto and "91%" in texto  # 3,9 + 87,3 % da TEIFa
    assert all("UG2" in itens[lista]["texto"] for lista in ("confirmar_agente", "verificar_campo"))
    # Só pelos meses de limitação forçada (TEIFa abaixo da referência)
    res.ons = _ons(teifa=2.0)
    assert "UG2" in _por_regra(res, "C2")["possiveis_problemas"]["texto"]
    # Só pela participação na TEIFa (poucos meses de limitação)
    res.ons = _ons(meses_hedf_ug2=10, participacao_hedf_ug2=70.0)
    assert "UG2" in _por_regra(res, "C2")["possiveis_problemas"]["texto"]
    # Nem participação dominante nem limitação na maioria dos meses: a UG1, com 21 dos 80 meses, nunca é apontada
    res.ons = _ons(meses_hedf_ug2=30, participacao_hedf_ug2=50.0)
    assert _por_regra(res, "C2") == {}


def test_c3_afluencia_que_cabia_nas_turbinas(df_base: pd.DataFrame) -> None:
    res = _neutro(df_base)
    res.hidrologia = _hidrologia()
    texto = _por_regra(res, "C3")["pontos_atencao"]["texto"]
    assert "92,9%" in texto
    res.hidrologia = _hidrologia(cabia=False)
    assert _por_regra(res, "C3") == {}


def test_c4_concentracao_diurna(df_base: pd.DataFrame) -> None:
    res = _neutro(df_base)
    anuais = res.indicadores_anuais
    anuais["razao_evt_diurna_noturna"] = 5.52
    anuais["razao_geracao_diurna_noturna"] = 0.71
    assert set(_por_regra(res, "C4")) == {"pontos_atencao"}
    anuais["razao_evt_diurna_noturna"] = 1.66
    assert _por_regra(res, "C4") == {}


def test_c5_disponibilidade_e_taxas(df_base: pd.DataFrame) -> None:
    res = _neutro(df_base)
    res.globais.update(desvio_disponibilidade_referencia_pp=-3.2, disponibilidade_relativa_pct=87.8,
                       disponibilidade_referencia_pct=91.0)
    texto = _por_regra(res, "C5")["pontos_atencao"]["texto"]
    assert "87,8%" in texto and "3,2 p.p." in texto
    res.globais.update(desvio_disponibilidade_referencia_pp=1.0)
    assert _por_regra(res, "C5") == {}
    res.ons = _ons(teifa=4.11)  # TEIFa acima da TEIF de referência
    assert "4,11%" in _por_regra(res, "C5")["pontos_atencao"]["texto"]


def test_c6_parada_com_geracao_programada(df_base: pd.DataFrame) -> None:
    res = _neutro(df_base)
    res.programacao = _programacao()
    itens = _por_regra(res, "C6")
    assert set(itens) == {"possiveis_problemas", "confirmar_agente", "verificar_campo"}
    assert "182 h" in itens["possiveis_problemas"]["texto"] and "68 eventos" in itens["possiveis_problemas"]["texto"]
    res.programacao = _programacao(eventos=0)
    assert _por_regra(res, "C6") == {}


def test_c7_c8_classificacao_e_declaracao(df_base: pd.DataFrame) -> None:
    res = _neutro(df_base)
    res.disponibilidade = {"anual": pd.DataFrame({"periodo": ["2024", "2025", "2026"], "ano_parcial": [False, False, True],
                                                  "reserva_desligada_teif_mwh": [1.0, 1.0, 1.0],
                                                  "diferenca_mwh": [-11_700.0, -12_400.0, 4_100.0]})}
    texto = _por_regra(res, "C7")["possiveis_problemas"]["texto"]
    assert "2024" in texto and "11,7 GWh" in texto and "4,1" not in texto  # 2026*: abaixo de 5 GWh
    res.resumo_anomalias = _anomalias(res, r7=293)
    assert "293 h" in _por_regra(res, "C8")["possiveis_problemas"]["texto"]
    confirmar = [i for i in montar_conclusao(res) if i["lista"] == "confirmar_agente" and i["regra"] in ("C7", "C8")]
    assert len(confirmar) == 1 and "293 h" in confirmar[0]["texto"]  # C8 entra no item da C7
    res.resumo_anomalias = _anomalias(res, r7=99)
    assert _por_regra(res, "C8") == {}
    res.disponibilidade = {}
    assert _por_regra(res, "C7") == {}
    res.ons = _ons(teifa=2.0, meses_hedf_ug2=0, participacao_hedf_ug2=10.0, divergencias=4)
    assert "4 meses-unidade" in _por_regra(res, "C7")["possiveis_problemas"]["texto"]


def test_c9_geracao_e_garantia_fisica(df_base: pd.DataFrame) -> None:
    res = _neutro(df_base)
    res.globais.update(geracao_sobre_garantia_fisica_pct=74.4)
    assert "74,4%" in _por_regra(res, "C9")["pontos_atencao"]["texto"]
    res.globais.update(geracao_sobre_garantia_fisica_pct=120.0)
    assert _por_regra(res, "C9") == {}


def test_c10_indisponibilidade_longa(df_base: pd.DataFrame) -> None:
    res = _neutro(df_base)
    res.eventos_indisponibilidade_total = pd.DataFrame({"inicio": [pd.Timestamp("2019-09-25 10:00")],
                                                        "fim": [pd.Timestamp("2019-12-24 23:00")], "duracao_h": [2174]})
    itens = _por_regra(res, "C10")
    assert set(itens) == {"confirmar_agente", "verificar_campo"} and "25/09/2019" in itens["confirmar_agente"]["texto"]
    res.eventos_indisponibilidade_total = res.eventos_indisponibilidade_total.assign(duracao_h=500)
    assert _por_regra(res, "C10") == {}
    res.ons = {"ug_anual": pd.DataFrame([{"ano": 2022, "ug": 2, "dispf": 74.18, "indisppf": 25.05, "indispff": 0.77,
                                          "dmdff": 4.2, "ano_parcial": False}])}
    assert "UG2 em 2022" in _por_regra(res, "C10")["confirmar_agente"]["texto"]


def test_c11_instrumentacao_e_medicao(df_base: pd.DataFrame) -> None:
    res = _neutro(df_base)
    res.hidrologia = _hidrologia(cabia=False, sinalizadas=13)
    assert set(_por_regra(res, "C11")) == {"verificar_campo"}
    res.hidrologia = _hidrologia(cabia=False, sinalizadas=0)
    assert _por_regra(res, "C11") == {}
    res.resumo_anomalias = _anomalias(res, r9=63)
    assert "63 h" in _por_regra(res, "C11")["verificar_campo"]["texto"]


def test_itens_completos_ordenados_e_sem_termos_de_avaliacao(df_base: pd.DataFrame) -> None:
    res = _tudo(df_base)
    itens = montar_conclusao(res)
    assert {"lista", "ordem", "regra", "texto", "secoes"} <= set(itens[0])
    assert {i["lista"] for i in itens} == set(LISTAS)
    for lista in LISTAS:
        da_lista = [i for i in itens if i["lista"] == lista]
        assert [i["ordem"] for i in da_lista] == list(range(1, len(da_lista) + 1))
        numeros = [int(i["regra"][1:]) for i in da_lista]
        assert numeros == sorted(numeros)
    for item in itens:
        texto = item["texto"].lower()
        assert not any(p in texto for p in PROIBIDOS), item
        assert item["secoes"] and not item["texto"].endswith(".")
        assert not re.search(r"\. [A-ZÁÉÍÓÚÂÊÔÃÕÇ]", item["texto"]), item  # uma frase ("p.p. abaixo" não conta)


def test_conclusao_nao_repete_constatacoes(df_base: pd.DataFrame) -> None:
    res = _tudo(df_base)
    frases = [f for _, texto in res.achados for f in re.split(r"(?<=\.) ", texto) if len(f) >= 40]
    for item in montar_conclusao(res):
        assert not any(f.rstrip(".") in item["texto"] for f in frases), item["texto"]


def test_analisar_preenche_a_conclusao(df_base: pd.DataFrame) -> None:
    res = analisar(df_base, {})
    assert isinstance(res.conclusao, list) and res.conclusao == montar_conclusao(res)
