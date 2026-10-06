"""Testes do mapa de fontes do relatório (spec 007): catálogo, textos das legendas, rodapé e aba FONTES."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any, Dict

import pandas as pd
import pytest

from src.fontes_relatorio import (
    CONFERENCIAS,
    CONJUNTOS,
    MAPA_FONTES,
    cabecalho_fontes,
    conjuntos_carregados,
    legenda_fonte,
    rodape_fontes,
    tabela_fontes_abas,
    texto_conferencia,
)

IDS = {"evt", "dispf_mensal", "dispf_anual", "teif_teip", "teif_teip_parametro", "programacao", "disponibilidade",
       "hidrologia", "geracao", "cadastro"}


def _conferencia(comuns: int = 70895, divergentes: int = 0) -> Dict[str, Any]:
    return {"horas_comuns": comuns, "coincidentes": comuns - divergentes, "divergentes": divergentes,
            "pct_coincidentes": 100.0 * (comuns - divergentes) / comuns, "so_ons_geracao": 0, "so_ons_disponibilidade": 0,
            "so_base_evt": 0}


def _res(completo: bool = True, **mudancas: Any) -> SimpleNamespace:
    """ResultadosAnalise mínimo: só a base de EVT, ou com todas as bases."""
    res = SimpleNamespace(ons={}, programacao={}, disponibilidade={}, hidrologia={}, geracao_oficial={}, cadastro={},
                          fontes={"obtencao": {"evt": "2026-10-01 12:00:00"}})
    if completo:
        recalculo = pd.DataFrame({"teifa_recalculada": [0.04, 0.05, None], "diferenca_teifa_pp": [0.0, 0.0002, None],
                                  "diferenca_teip_pp": [0.0, -0.0001, None]})
        res.ons = {"divergencias": pd.DataFrame({"mes": ["2024-03", "2025-04", "2025-08", "2026-08"]}),
                   "recalculo_taxas": recalculo}
        res.programacao = {"periodo": {}}
        res.disponibilidade = {"conferencia": _conferencia()}
        res.hidrologia = {"alinhamento": pd.DataFrame([{"horas_comuns": 70731, "coincidentes_ambas": 70731,
                                                        "pct_coincidencia": 100.0, "confirmado": True}])}
        res.geracao_oficial = {"conferencia": _conferencia()}
        res.cadastro = {"divergencias": ""}
        res.fontes["obtencao"].update({i: "2026-10-05 15:07:29" for i in IDS - {"evt"}})
    for chave, valor in mudancas.items():
        setattr(res, chave, valor)
    res.fontes["carregados"] = conjuntos_carregados(res)
    return res


def test_catalogo_e_mapa_consistentes() -> None:
    assert set(CONJUNTOS) == IDS | {"projeto"}
    for chave, entrada in MAPA_FONTES.items():
        assert set(entrada.conjuntos) <= set(CONJUNTOS), chave
        assert set(entrada.conferencias) <= set(CONFERENCIAS), chave


def test_conjuntos_carregados() -> None:
    assert conjuntos_carregados(_res(completo=False)) == ["evt"]
    assert set(conjuntos_carregados(_res())) == IDS


def test_legenda_com_conjunto_data_e_conferencias() -> None:
    texto = legenda_fonte(_res(), "serie_temporal")
    assert texto.startswith("Calculado neste relatório a partir de: Energia Vertida Turbinável (cod_usina 153), "
                            "obtido em 01/10/2026.")
    assert legenda_fonte(_res(), "tab_ons_ug_anual").startswith(
        "Fonte dos dados: Indicadores de disponibilidade por unidade geradora, base anual")
    assert "geração conferida com Geração por usina: 70.895 de 70.895 horas coincidentes (100,0%)" in texto
    assert "disponibilidade declarada conferida com Disponibilidade por usina" in texto
    assert "Sem outra fonte para conferir: energia vertida turbinável (EVT)." in texto


def test_legenda_calculada_e_sem_data() -> None:
    res = _res()
    res.fontes["obtencao"]["evt"] = ""
    texto = legenda_fonte(res, "evt_mensal")
    assert texto.startswith("Calculado neste relatório a partir de: Energia Vertida Turbinável (cod_usina 153), "
                            "data de obtenção não registrada.")


def test_conferencia_nao_feita_sem_a_base() -> None:
    texto = legenda_fonte(_res(completo=False), "serie_temporal")
    assert "geração: conferência com Geração por usina não feita nesta execução" in texto


def test_conferencias_com_divergencias_e_taxas() -> None:
    res = _res(geracao_oficial={"conferencia": _conferencia(divergentes=3)})
    assert "3 divergências, listadas na aba GER_DIVERGENCIAS" in texto_conferencia(res, "geracao")
    assert "4 divergências (meses-unidade), listadas na aba ONS_DIVERGENCIAS" in texto_conferencia(res, "dispf_horas")
    taxas = texto_conferencia(res, "teifa_teip")
    assert "2 de 2 meses reproduzidos (diferença máxima de 0,000 p.p.)" in taxas
    assert "sem divergência" in texto_conferencia(res, "cadastro")


def test_rodape_e_cabecalho_com_n_conjuntos() -> None:
    quando = datetime(2026, 10, 6, 9, 30)
    assert rodape_fontes(_res(), quando) == (
        "Fontes: ONS – Dados Abertos, 10 conjuntos; fonte de cada figura e tabela na legenda; relação completa nas "
        "Notas metodológicas. Gerado em 06/10/2026 09:30.")
    assert "Dados Abertos, 1 conjunto;" in rodape_fontes(_res(completo=False), quando)
    assert cabecalho_fontes(_res()) == (
        "**Fontes**: ONS – Dados Abertos, 10 conjuntos; fonte de cada figura e tabela na legenda; relação completa nas "
        "notas metodológicas.")


def test_aba_fontes() -> None:
    tabela = tabela_fontes_abas(_res(), ["INDICADORES_ANUAIS", "GER_CONFERENCIA", "CAD_FICHA", "DICIONARIOS"])
    assert list(tabela.columns) == ["aba", "conjuntos_origem", "conferencias", "sem_outra_fonte", "calculado_no_relatorio"]
    assert tabela["aba"].tolist() == ["INDICADORES_ANUAIS", "GER_CONFERENCIA", "CAD_FICHA", "DICIONARIOS"]
    assert set(tabela["calculado_no_relatorio"]) <= {"sim", "não"}
    assert "Geração por usina" in tabela.loc[1, "conjuntos_origem"]
    assert not tabela["conjuntos_origem"].str.contains("origem não mapeada").any()


@pytest.mark.parametrize("chave", sorted(MAPA_FONTES))
def test_todas_as_chaves_geram_texto(chave: str) -> None:
    for res in (_res(), _res(completo=False)):
        texto = legenda_fonte(res, chave)
        assert texto.startswith(("Fonte dos dados:", "Calculado neste relatório a partir de:")), chave


def test_legendas_especificas() -> None:
    """T009: EVT sem outra fonte; divergências do DISPF com a aba; cadastro conferido com o projeto."""
    res = _res()
    assert legenda_fonte(res, "evt_mensal").endswith("Sem outra fonte para conferir: energia vertida turbinável (EVT).")
    assert "4 divergências (meses-unidade), listadas na aba ONS_DIVERGENCIAS" in legenda_fonte(res, "tab_ons_divergencias")
    assert "Modalidade das usinas (CEG UHE.PH.MS.028761-0.01), obtido em 05/10/2026" in legenda_fonte(res, "bloco_cadastro")
