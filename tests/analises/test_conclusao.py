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


# ---------------------------------------------------------------------------
# Catálogo da conclusão por tipo (plano das Análises, D18; data-model das Análises, seção 3.11)
# ---------------------------------------------------------------------------

REGRAS_COMUNS = {"C2", "C5", "C8", "C10", "C20"}  # C20: taxas operativas (spec das Análises, FR-063)
REGRAS_TERMICAS = {"C12", "C13", "C14", "C15"}  # térmicas (decisão D18)
REGRAS_RENOVAVEIS = {"C16", "C17", "C18", "C19"}  # eólicas e solares


def test_catalogo_declara_os_campos_de_cada_regra() -> None:
    from src.analises.conclusao import CATALOGO_CONCLUSAO, REGRAS_CONCLUSAO
    from src.coleta.registro import RENOVAVEIS, TERMICAS
    from src.comum import regras

    assert [r.codigo for r in CATALOGO_CONCLUSAO] == [f"C{i}" for i in range(1, 21)]
    for r in CATALOGO_CONCLUSAO:
        assert r.tipos and set(r.listas) <= set(LISTAS) and r.nivel_exigido == "usina", r.codigo
        assert (callable(r.funcao) or r.codigo in REGRAS_TERMICAS | REGRAS_RENOVAVEIS) and r.secoes, r.codigo
        assert all(hasattr(regras, nome) for nome in r.limiares), r.codigo
        # C1 a C11 sem período mínimo novo (decisões D16 e D19); C18 só em anos completos
        assert r.periodo_minimo_meses == (12 if r.codigo == "C18" else None), r.codigo
    assert {r.codigo for r in CATALOGO_CONCLUSAO if r.funcao_comum is not None} == \
        REGRAS_COMUNS | REGRAS_TERMICAS | REGRAS_RENOVAVEIS
    assert all(r.tipos == TERMICAS and r.funcao is None for r in CATALOGO_CONCLUSAO if r.codigo in REGRAS_TERMICAS)
    assert all(r.tipos == RENOVAVEIS and r.funcao is None for r in CATALOGO_CONCLUSAO if r.codigo in REGRAS_RENOVAVEIS)
    # as regras comuns não valem para eólicas e solares
    assert not any(set(r.tipos) & set(RENOVAVEIS) for r in CATALOGO_CONCLUSAO if r.codigo in REGRAS_COMUNS)
    assert len(REGRAS_CONCLUSAO) == 12  # o caminho da EVT: C1 a C11 (decisão D16) e a C20 (spec das Análises, FR-063)


def test_itens_so_nas_listas_declaradas_e_na_ordem_de_hoje(df_base: pd.DataFrame) -> None:
    from src.analises.conclusao import CATALOGO_CONCLUSAO, regras_omitidas

    res = _tudo(df_base)
    listas = {r.codigo: set(r.listas) for r in CATALOGO_CONCLUSAO}
    itens = montar_conclusao(res)
    assert all(i["lista"] in listas[i["regra"]] for i in itens)
    ordem = [(LISTAS.index(i["lista"]), int(i["regra"][1:])) for i in itens]
    assert ordem == sorted(ordem)
    assert regras_omitidas(res) == []  # nas hidrelétricas com EVT, as onze regras são avaliadas


def _disponibilidade_do_mes_todo(raw) -> None:
    """Disponibilidade da UTE fictícia em todo 09/2026: 50 MW contra 100 MW de geração (regra R7 em 720 h)."""
    from tests.fixtures import brutos_catalogo as bc

    horas = pd.date_range("2026-09-01", "2026-09-30 23:00", freq="h")
    pd.DataFrame({"id_estado": "GO", "id_ons": bc.UTE["id_ons"], "ceg": bc.UTE["ceg"], "din_instante": horas,
                  "val_dispoperacional": 50.0, "val_dispsincronizada": 40.0}).to_parquet(
        raw / "disponibilidade_usina" / "DISPONIBILIDADE_USINA_2026_09.parquet", index=False)


@pytest.fixture(scope="module")
def sem_evt(tmp_path_factory):
    from src.analises.resultados import carregar_resultados
    from src.comum.perfil import carregar_perfil
    from tests.fixtures.sem_evt import projeto_sem_evt

    raiz = tmp_path_factory.mktemp("projeto")
    usinas = projeto_sem_evt(raiz, ["coleta", "tratamento", "conferencia", "analises"],
                             preparar=_disponibilidade_do_mes_todo)
    return {slug: (carregar_resultados(u["pasta"] / "analises" / "resultados.pkl"), carregar_perfil(slug, raiz))
            for slug, u in usinas.items()}


def _ativar(perfil) -> None:
    from src.comum.perfil import definir_perfil_ativo

    definir_perfil_ativo(perfil)  # a fixture automática volta à São Domingos no fim do teste


def test_termica_com_as_regras_comuns_na_base_horaria(sem_evt) -> None:
    from src.analises.conclusao import regras_omitidas

    res, perfil = sem_evt["ute_beta"]
    _ativar(perfil)
    c8 = {i["lista"]: i for i in res.conclusao if i["regra"] == "C8"}
    assert set(c8) == {"possiveis_problemas", "confirmar_agente"}  # sem a C7, a pergunta ao agente fica na C8
    assert "720 h" in c8["possiveis_problemas"]["texto"] and c8["possiveis_problemas"]["secoes"] == ["qualidade_comum"]
    assert {i["regra"] for i in res.conclusao} <= REGRAS_COMUNS
    omitidas = {o["item"]: o["motivo"] for o in regras_omitidas(res)}
    assert "C2" in omitidas and "Indicadores" in omitidas["C2"]
    assert "C5" in omitidas and "IP e TEIF de referência" in omitidas["C5"]
    assert not any(c in omitidas for c in ("C1", "C3", "C4", "C6", "C7", "C9", "C11"))  # regras só de hidrelétricas
    assert {o["item"] for o in res.omitidos if o["tipo"] == "regra"} == set(omitidas)


def test_regra_com_entrada_de_nivel_conjunto_nao_e_avaliada(sem_evt) -> None:
    from src.analises.conclusao import frase_sem_itens, regras_omitidas

    res, perfil = sem_evt["pch_alfa"]
    _ativar(perfil)
    assert res.conclusao == [] and montar_conclusao(res) == []
    omitidas = {o["item"]: o["motivo"] for o in regras_omitidas(res)}
    assert REGRAS_COMUNS <= set(omitidas)
    assert all("nível da usina" in omitidas[c] for c in REGRAS_COMUNS)
    assert all("EVT" in omitidas[c] for c in ("C1", "C3", "C4", "C6", "C7", "C9", "C11"))
    frase = frase_sem_itens(res)
    assert "conjunto" in frase and "nível da usina" in frase


def test_nota_da_conclusao_por_caminho(sem_evt) -> None:
    from src.relatorio.conteudo import nota_conclusao, nota_conclusao_catalogo

    texto_uhe = nota_conclusao()
    assert texto_uhe.startswith("Conclusão: indícios gerados por regras fixas") and "C11" in texto_uhe
    res, perfil = sem_evt["ute_beta"]
    _ativar(perfil)
    nota = nota_conclusao_catalogo(res)
    assert nota.startswith("Conclusão: indícios gerados pelas regras do catálogo para UTE")
    for codigo in REGRAS_COMUNS:
        assert f"{codigo} " in nota
    assert "C1 " not in nota and "Não avaliadas" in nota


def test_c10_das_usinas_sem_evt_agrupa_unidades_e_anos() -> None:
    """Nas usinas sem EVT, as paradas programadas longas saem agrupadas (texto da UHE sem mudança)."""
    from src.analises.conclusao import _unidades_agrupadas

    linhas = [{"ano": a, "ug": u} for a in (2022, 2023, 2024) for u in range(1, 6)] + [{"ano": 2025, "ug": 1}]
    assert _unidades_agrupadas(pd.DataFrame(linhas), 5) == ("de todas as unidades em 2022, 2023 e 2024; "
                                                             "da UG1 em 2025")
    assert _unidades_agrupadas(pd.DataFrame([{"ano": 2022, "ug": 2}, {"ano": 2022, "ug": 3}]), 5) == \
        "das UG2 e UG3 em 2022"


# ---------------------------------------------------------------------------
# Regras das térmicas: C12 a C15 e as comuns numa térmica (spec das Análises, FR-057)
# ---------------------------------------------------------------------------


def _res_termica(termica, disponibilidade=None):
    from src.analises.resultados import ResultadosAnalise

    vazio = pd.DataFrame()
    res = ResultadosAnalise(
        cobertura={}, globais={}, indicadores_anuais=vazio, evt_mensal=vazio, distribuicao_mes_do_ano=vazio,
        evt_por_faixa_geracao=vazio, perfil_horario_geracao=vazio, perfil_horario_evt=vazio,
        eventos_parada_com_evt=vazio, eventos_indisponibilidade_total=vazio, mudanca_classificacao={}, anomalias=vazio,
        resumo_anomalias=vazio, extremos=vazio, perfil_estatistico=vazio)
    res.tipo = "UTE"
    res.comum = {"cobertura": {"inicio": pd.Timestamp("2024-01-01")}, "qualidade": {},
                 "disponibilidade": disponibilidade or {}}
    res.termica = termica
    return res


def _termica(abaixo=0, sem_programacao=0, nao_verificada_pct=float("nan"), horas_cvu=0):
    return {
        "atendimento": {"resumo": {"horas_abaixo": abaixo, "energia_abaixo_mwh": abaixo * 60.0,
                                   "horas_sem_programacao": sem_programacao,
                                   "energia_sem_programacao_mwh": sem_programacao * 50.0}},
        "inflexibilidade_resumo": {"programada_mwh": 1000.0, "nao_verificada_mwh": 10.0 * nao_verificada_pct,
                                   "nao_verificada_pct": nao_verificada_pct},
        "cvu_cmo": {"horas_disponivel_cvu_abaixo": horas_cvu, "semanas_disponivel_cvu_abaixo": 2},
        "disponivel_sem_despacho": {"resumo": {"horas": horas_cvu}},
    }


def test_c12_a_c15_disparam_e_nao_disparam() -> None:
    from src.comum.regras import (
        LIMIAR_CONCLUSAO_DESPACHO_ABAIXO_HORAS as H12,
        LIMIAR_CONCLUSAO_DISPONIVEL_CVU_HORAS as H13,
        LIMIAR_CONCLUSAO_INFLEXIBILIDADE_PCT as P14,
        LIMIAR_CONCLUSAO_SEM_PROGRAMACAO_HORAS as H15,
    )

    no_limiar = montar_conclusao(_res_termica(_termica(H12, H15, P14, H13)))
    regras = {(i["regra"], i["lista"]) for i in no_limiar}
    assert {("C12", "possiveis_problemas"), ("C12", "confirmar_agente"), ("C13", "confirmar_agente"),
            ("C14", "pontos_atencao"), ("C15", "confirmar_agente")} <= regras
    abaixo = montar_conclusao(_res_termica(_termica(H12 - 1, H15 - 1, P14 - 0.1, H13 - 1)))
    assert not {i["regra"] for i in abaixo} & REGRAS_TERMICAS
    textos = {i["regra"]: i["texto"] for i in no_limiar if i["lista"] != "confirmar_agente"}
    assert f"{H12} h" in textos["C12"] and "abaixo da programada" in textos["C12"]
    secoes = {i["regra"]: i["secoes"] for i in no_limiar}
    assert secoes["C12"] == ["atendimento_despacho"] and secoes["C13"] == ["disponivel_sem_despacho"]
    assert secoes["C14"] == ["despacho_motivo"]
    for item in no_limiar:  # nenhum termo de parecer
        assert not any(p in item["texto"].lower() for p in PROIBIDOS), item


def test_termica_sem_referencias_e_sem_despacho(tmp_path) -> None:
    import shutil
    from pathlib import Path

    from src.analises.conclusao import regras_omitidas
    from src.comum.perfil import carregar_perfil

    origem = Path(__file__).resolve().parents[1] / "fixtures" / "usinas_ficticias" / "ute" / "perfil.toml"
    (tmp_path / "usinas" / "ute_ficticia").mkdir(parents=True)
    shutil.copy(origem, tmp_path / "usinas" / "ute_ficticia" / "perfil.toml")
    _ativar(carregar_perfil("ute_ficticia", tmp_path))  # sem IP e TEIF de referência
    eventos = pd.DataFrame({"inicio": [pd.Timestamp("2024-01-01")], "fim": [pd.Timestamp("2024-02-15 23:00")],
                            "duracao_h": [46 * 24], "geracao_media_mw": [0.0]})
    disponibilidade = {"resumo": {"disponibilidade_relativa_pct": 50.0}, "eventos_indisponibilidade_total": eventos}
    res = _res_termica({}, disponibilidade)
    itens = montar_conclusao(res)
    assert {i["regra"] for i in itens} == {"C10"}  # C10 sobre a base horária comum, numa térmica
    omitidas = {o["item"]: o["motivo"] for o in regras_omitidas(res)}
    assert "IP e TEIF de referência" in omitidas["C5"] and "Indicadores" in omitidas["C2"]
    assert all("Geração térmica por motivo de despacho" in omitidas[c] for c in ("C12", "C14", "C15"))
    assert "CVU e o CMO" in omitidas["C13"]


# ---------------------------------------------------------------------------
# Regras das eólicas e solares: C16 a C19 (spec das Análises, FR-059)
# ---------------------------------------------------------------------------


def _res_renovavel(renovavel, meses_distintos: int = 12):
    res = _res_termica({})
    res.tipo, res.termica, res.renovavel = "EOL", {}, renovavel
    res.cobertura = {"meses_distintos": meses_distintos}
    return res


def _renovavel(pct_cortada=float("nan"), pct_invalidas=float("nan"), fc_anual=(), nivel_fc="usina",
               desvio_pct=float("nan"), nivel_prog="usina"):
    anual = pd.DataFrame([{"periodo": ano, "nivel": nivel_fc, "fator_capacidade_pct": fc, "ano_parcial": parcial}
                          for ano, fc, parcial in fc_anual],
                         columns=["periodo", "nivel", "fator_capacidade_pct", "ano_parcial"])
    return {
        "restricao": {"resumo": {"pct_estimada": pct_cortada, "energia_cortada_mwh": 1000.0 * pct_cortada}},
        "recurso": {"grandeza": "vento", "resumo": {"pct_invalidas": pct_invalidas, "semi_horas": 1000,
                                                    "semi_horas_invalidas": int(10 * pct_invalidas
                                                                                if pct_invalidas == pct_invalidas else 0)}},
        "fator_capacidade": {"nivel": nivel_fc, "anual": anual} if len(anual) else {},
        "programacao": {"nivel": nivel_prog, "desvio_medio_absoluto_mw": 2.0, "desvio_medio_absoluto_pct": desvio_pct,
                        "horas": 500},
    }


def _referencia_c18() -> float:
    from src.comum.perfil import perfil_ativo

    p = perfil_ativo().parametros
    return 100.0 * p.garantia_fisica_mwmed / p.potencia_instalada_mw


def test_c16_a_c19_disparam_e_nao_disparam() -> None:
    from src.comum.regras import (
        LIMIAR_CONCLUSAO_DESVIO_PROGRAMACAO_PCT as P19,
        LIMIAR_CONCLUSAO_ENERGIA_CORTADA_PCT as P16,
        LIMIAR_CONCLUSAO_RECURSO_INVALIDO_PCT as P17,
    )

    ref = _referencia_c18()
    no_limiar = montar_conclusao(_res_renovavel(_renovavel(P16, P17, [(2024, ref - 1, False)], desvio_pct=P19)))
    assert {(i["regra"], i["lista"]) for i in no_limiar} == {
        ("C16", "pontos_atencao"), ("C17", "verificar_campo"), ("C18", "pontos_atencao"), ("C19", "confirmar_agente")}
    secoes = {i["regra"]: i["secoes"] for i in no_limiar}
    assert secoes == {"C16": ["energia_cortada"], "C17": ["recurso_geracao"], "C18": ["fator_capacidade"],
                      "C19": ["programacao_comum"]}
    textos = {i["regra"]: i["texto"] for i in no_limiar}
    assert "2024" in textos["C18"] and "garantia física" in textos["C18"] and "vento" in textos["C17"]
    abaixo = montar_conclusao(_res_renovavel(_renovavel(P16 - 0.1, P17 - 0.1, [(2024, ref + 1, False)],
                                                        desvio_pct=P19 - 0.1)))
    assert not {i["regra"] for i in abaixo} & REGRAS_RENOVAVEIS
    for item in no_limiar:  # nenhum termo de parecer
        assert not any(p in item["texto"].lower() for p in PROIBIDOS), item


def test_c18_so_em_ano_completo_com_fc_proprio_e_garantia_fisica() -> None:
    from dataclasses import replace

    from src.analises.conclusao import regras_omitidas
    from src.comum.perfil import perfil_ativo

    ref = _referencia_c18()
    parcial = _res_renovavel(_renovavel(fc_anual=[(2024, ref - 5, True)]))
    assert not montar_conclusao(parcial)  # o ano parcial não é avaliado
    do_conjunto = _res_renovavel(_renovavel(fc_anual=[(2024, ref - 5, False)], nivel_fc="conjunto"))
    assert not montar_conclusao(do_conjunto)
    assert "Fator de capacidade no nível da usina" in {o["item"]: o["motivo"] for o in regras_omitidas(do_conjunto)}["C18"]
    curta = _res_renovavel(_renovavel(fc_anual=[(2024, ref - 5, False)]), meses_distintos=5)
    assert "período mínimo de 12" in {o["item"]: o["motivo"] for o in regras_omitidas(curta)}["C18"]
    perfil = perfil_ativo()
    _ativar(replace(perfil, parametros=replace(perfil.parametros, garantia_fisica_mwmed=None)))
    sem_gf = _res_renovavel(_renovavel(fc_anual=[(2024, 1.0, False)]))
    assert not montar_conclusao(sem_gf)
    assert "garantia física" in {o["item"]: o["motivo"] for o in regras_omitidas(sem_gf)}["C18"]


def test_c19_so_com_a_programacao_da_usina() -> None:
    from src.analises.conclusao import regras_omitidas
    from src.comum.regras import LIMIAR_CONCLUSAO_DESVIO_PROGRAMACAO_PCT as P19

    res = _res_renovavel(_renovavel(desvio_pct=P19 + 5, nivel_prog="conjunto"))
    assert not montar_conclusao(res)
    assert "Programação diária no nível da usina" in {o["item"]: o["motivo"] for o in regras_omitidas(res)}["C19"]


# ---------------------------------------------------------------------------
# C20: taxas operativas × oficiais (spec das Análises, FR-063)
# ---------------------------------------------------------------------------


def _ons_com_operativas(teifa_oper: float, teip_oper: float) -> dict:
    from src.analises.indicadores import comparar_taxas_operativas

    taxas = pd.DataFrame({"mes": [pd.Timestamp("2026-08-01"), pd.Timestamp("2026-09-01")], "teifa": [0.30, 0.3007],
                          "teip": [0.70, 0.703], "teifa_oper": [0.13, teifa_oper], "teip_oper": [0.59, teip_oper]})
    return {"taxa_ultima": {"mes": pd.Timestamp("2026-09-01")}, "taxas_operativas": comparar_taxas_operativas(taxas)}


def test_c20_cita_so_as_taxas_que_diferem_no_mes_mais_recente() -> None:
    from src.analises.conclusao import _regra_c20

    res = _res_termica(_termica())
    res.ons = _ons_com_operativas(0.1289, 0.703)
    itens = _regra_c20(res)
    assert [(i["lista"], i["regra"]) for i in itens] == [("confirmar_agente", "C20")]
    assert "set/2026" in itens[0]["texto"] and "TEIFa operativa de 12,89% e oficial de 30,07%" in itens[0]["texto"]
    assert "−17,18 p.p." in itens[0]["texto"] and "TEIP" not in itens[0]["texto"]


def test_c20_nao_dispara_abaixo_do_limiar() -> None:
    from src.analises.conclusao import _regra_c20

    res = _res_termica(_termica())
    res.ons = _ons_com_operativas(0.3057, 0.70)  # 0,5 p.p. e 0,3 p.p.: abaixo de 1 p.p.
    assert _regra_c20(res) == []


def test_c20_nao_avaliada_sem_as_taxas_operativas() -> None:
    from src.analises.conclusao import regras_omitidas

    res = _res_termica(_termica())
    res.ons = {"taxa_ultima": {"mes": pd.Timestamp("2026-09-01")}}
    motivos = {o["item"]: o["motivo"] for o in regras_omitidas(res)}
    assert motivos["C20"] == "sem as Taxas TEIFa Oper e TEIP Oper no nível da usina"
