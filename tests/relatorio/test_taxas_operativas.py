"""Textos do relatório sobre as taxas operativas sem depender das etapas (spec da Geração do relatório, FR-071)."""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from src.relatorio.conteudo import linhas_tabela_taxas_operativas, nota_taxas_operativas, texto_taxas_operativas


def test_usina_com_as_oficiais_e_sem_as_operativas() -> None:
    res = SimpleNamespace(ons={"taxa_ultima": {"mes": pd.Timestamp("2026-09-01")}})
    assert nota_taxas_operativas(res) == ("Taxas operativas: as Taxas TEIFa Oper e TEIP Oper da usina não constam dos "
                                          "dados coletados.")
    assert linhas_tabela_taxas_operativas(res)[1] == [] and texto_taxas_operativas(res) == ""


def test_usina_sem_indicadores_sem_nota() -> None:
    assert nota_taxas_operativas(SimpleNamespace(ons={})) == ""


def _res_com_comparacao(teifa_oper: list) -> SimpleNamespace:
    from src.analises.indicadores import comparar_taxas_operativas

    meses = pd.date_range("2026-07-01", periods=len(teifa_oper), freq="MS")
    taxas = pd.DataFrame({"mes": meses, "teifa": [0.04] * len(meses), "teip": [0.05] * len(meses),
                          "teifa_oper": teifa_oper, "teip_oper": [0.05] * len(meses)})
    return SimpleNamespace(ons={"taxa_ultima": {"mes": meses[-1]}, "taxas_operativas": comparar_taxas_operativas(taxas)})


def test_frase_com_diferenca_abaixo_do_limiar_cita_a_maior() -> None:
    texto = texto_taxas_operativas(_res_com_comparacao([0.0398, 0.04]))
    assert "ficou abaixo de 1 p.p. em todos os meses; a maior diferença foi de −0,02 p.p. na TEIFa (jul/2026)" in texto


def test_frase_com_taxas_iguais() -> None:
    texto = texto_taxas_operativas(_res_com_comparacao([0.04, 0.04]))
    assert texto.endswith("as taxas operativas coincidem com as oficiais em todos os meses.")


def test_diferenca_que_arredonda_para_zero_sem_sinal() -> None:
    _, linhas = linhas_tabela_taxas_operativas(_res_com_comparacao([0.04, 0.0400127]))
    assert linhas[0][3] == "0,00 p.p."
