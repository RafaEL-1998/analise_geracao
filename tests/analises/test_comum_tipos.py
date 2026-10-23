"""Seções comuns das usinas sem EVT sobre a base horária comum (plano das Análises, D16 e D19; data-model das
Análises, seções 3.2 e 3.12 a 3.19).

Indicadores anuais, série diária, geração mensal, perfil horário e sazonalidade (só com 12 meses distintos), sem
misturar níveis; ``ResultadosAnalise`` com os campos novos e os de EVT vazios; nas hidrelétricas com EVT, o caminho de
hoje, sem as seções comuns.
"""

from __future__ import annotations

import math
from types import SimpleNamespace
from typing import Any, Dict

import numpy as np
import pandas as pd
import pytest

from src.analises.comum_tipos import TITULO_SAZONALIDADE, analisar_comum, programacao_comum
from src.analises.etapa import analisar
from src.analises.evt import preparar_dados
from src.analises.resultados import VERSAO_FORMATO, carregar_resultados, sem_evt
from src.tratamento.base_horaria import COLUNAS_BASE_HORARIA
from tests.fixtures.sem_evt import projeto_sem_evt


def _perfil(tipo: str = "UFV", potencia: float = 50.0, conjunto: str = "") -> Any:
    return SimpleNamespace(usina=SimpleNamespace(tipo=tipo, slug="ficticia", estado="GO", modalidade="TIPO I"),
                           identificacao=SimpleNamespace(id_conjunto=conjunto or None, id_ons="GOFIC"),
                           parametros=SimpleNamespace(potencia_instalada_mw=potencia),
                           cobertura={"geracao": "proprio", "programacao": "proprio"})


def _base(inicio: str, horas: int, geracao: Any = 10.0, nivel: Any = "usina", disponibilidade: Any = np.nan,
          programada: Any = np.nan) -> pd.DataFrame:
    instantes = pd.date_range(inicio, periods=horas, freq="h")
    base = pd.DataFrame({"din_instante": instantes, "geracao_mw": geracao, "nivel": nivel,
                         "disponibilidade_operacional_mw": disponibilidade,
                         "disponibilidade_sincronizada_mw": disponibilidade, "geracao_programada_mw": programada,
                         "trecho": 1, "sinalizacoes": ""})
    return base[COLUNAS_BASE_HORARIA]


# ---------------------------------------------------------------------------
# Seções comuns (unidade)
# ---------------------------------------------------------------------------


def test_indicadores_anuais_por_ano_e_nivel_sem_misturar() -> None:
    usina = _base("2025-12-31 22:00", 4, geracao=[10.0, 30.0, 0.5, np.nan], disponibilidade=40.0)
    conjunto = _base("2026-01-01 02:00", 2, geracao=80.0, nivel="conjunto", disponibilidade=40.0)
    comum, _ = analisar_comum(pd.concat([usina, conjunto], ignore_index=True), _perfil("UFV", 50.0), "UFV")
    anuais = comum["anuais"].set_index(["ano", "nivel"])
    assert list(anuais.index) == [(2025, "usina"), (2026, "conjunto"), (2026, "usina")]
    assert anuais.loc[(2025, "usina"), "geracao_media_mw"] == pytest.approx(20.0)
    assert anuais.loc[(2025, "usina"), "fator_capacidade_pct"] == pytest.approx(40.0)  # 20 / 50
    assert anuais.loc[(2026, "usina"), "horas"] == 2 and anuais.loc[(2026, "usina"), "horas_com_valor"] == 1
    assert anuais.loc[(2026, "usina"), "horas_paradas"] == 1  # 0,5 MW
    # no conjunto: sem fator de capacidade (a capacidade é da usina) e sem disponibilidade (que é da usina)
    assert math.isnan(anuais.loc[(2026, "conjunto"), "fator_capacidade_pct"])
    assert math.isnan(anuais.loc[(2026, "conjunto"), "disponibilidade_media_mw"])
    assert anuais.loc[(2025, "usina"), "disponibilidade_relativa_pct"] == pytest.approx(80.0)


def test_fator_de_capacidade_so_em_eolicas_e_solares() -> None:
    comum, _ = analisar_comum(_base("2026-01-01", 3), _perfil("UTE", 50.0), "UTE")
    assert comum["anuais"]["fator_capacidade_pct"].isna().all()


def test_serie_diaria_mensal_e_perfil_horario() -> None:
    base = _base("2026-01-31 00:00", 48, geracao=list(range(48)), disponibilidade=40.0)
    comum, _ = analisar_comum(base, _perfil("UTE", 50.0), "UTE")
    diaria = comum["serie_diaria"]
    assert list(diaria["din_instante"]) == [pd.Timestamp("2026-01-31"), pd.Timestamp("2026-02-01")]
    assert list(diaria["geracao_mw"]) == [11.5, 35.5] and set(diaria["disponibilidade_operacional_mw"]) == {40.0}
    mensal = comum["mensal"]
    assert list(mensal["mes"]) == [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-02-01")]
    assert list(mensal["energia_mwh"]) == [sum(range(24)), sum(range(24, 48))]
    perfil = comum["perfil_horario"]
    assert len(perfil) == 24 and perfil.loc[perfil["hora"] == 0, "geracao_media_mw"].item() == 12.0


def test_sazonalidade_so_com_12_meses_distintos() -> None:
    curta = _base("2026-08-01", 24 * 45)  # cerca de 1,5 mês (decisão D19: série curta das UFV)
    comum, omitidos = analisar_comum(curta, _perfil(), "UFV")
    assert comum["sazonalidade"].empty
    itens = [o for o in omitidos if o["item"] == TITULO_SAZONALIDADE]
    assert len(itens) == 1 and "12 meses" in itens[0]["motivo"] and "(2)" in itens[0]["motivo"]
    longa = _base("2025-01-01", 24 * 365)
    comum, omitidos = analisar_comum(longa, _perfil(), "UFV")
    assert sorted(comum["sazonalidade"]["mes_do_ano"]) == list(range(1, 13))
    assert TITULO_SAZONALIDADE not in [o["item"] for o in omitidos]


def test_programacao_so_no_mesmo_nivel() -> None:
    base = _base("2026-01-01", 4, geracao=[10.0, 0.0, 12.0, 0.0], programada=[11.0, 8.0, 12.0, np.nan])
    p = programacao_comum(base, "usina")
    assert p["resumo"]["horas_comuns"] == 3
    assert p["resumo"]["desvio_medio_absoluto_mw"] == pytest.approx(3.0)  # (1 + 8 + 0) / 3
    assert p["resumo"]["horas_desvio_programacao"] == 1  # parada com programação de 8 MW
    assert programacao_comum(base, "conjunto") == {}


def test_disponibilidade_so_com_a_geracao_da_usina() -> None:
    base = _base("2026-01-01", 4, geracao=[10.0, 0.0, 0.0, 5.0], disponibilidade=[40.0, 0.0, 0.0, 40.0])
    comum, _ = analisar_comum(base, _perfil("UTE", 50.0), "UTE")
    d = comum["disponibilidade"]
    assert d["resumo"]["horas_indisponibilidade_total"] == 2 and d["resumo"]["eventos_indisponibilidade_total"] == 1
    assert d["eventos_indisponibilidade_total"].iloc[0]["duracao_h"] == 2
    conjunto = base.assign(nivel="conjunto")
    comum, omitidos = analisar_comum(conjunto, _perfil("UTE", 50.0), "UTE")
    assert comum["disponibilidade"] == {}
    assert "Disponibilidade e geração por ano" in [o["item"] for o in omitidos]


# ---------------------------------------------------------------------------
# ResultadosAnalise nas usinas fictícias e na hidrelétrica com EVT
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def usinas(tmp_path_factory) -> Dict[str, Dict[str, Any]]:
    return projeto_sem_evt(tmp_path_factory.mktemp("projeto"), ["coleta", "tratamento", "conferencia", "analises"])


def test_resultados_das_usinas_sem_evt(usinas) -> None:
    assert VERSAO_FORMATO == 3
    for slug, u in usinas.items():
        assert u["codigos"]["analises"] == 0, (slug, u["manifestos"])
        res = carregar_resultados(u["pasta"] / "analises" / "resultados.pkl")
        assert sem_evt(res)
        assert set(res.comum) >= {"cobertura", "anuais", "serie_diaria", "mensal", "sazonalidade", "perfil_horario",
                                  "qualidade", "conferencias_nao_aplicaveis"}
        assert res.evt_mensal.empty and res.indicadores_anuais.empty and not res.globais  # campos de EVT vazios
        assert len(res.trechos) == 1 and res.omitidos
        assert res.cobertura["horas_observadas"] == 9480


def test_niveis_e_constatacoes_do_conjunto(usinas) -> None:
    ute = carregar_resultados(usinas["ute_beta"]["pasta"] / "analises" / "resultados.pkl")
    assert (ute.tipo, ute.modalidade) == ("UTE", "TIPO I")
    assert ute.niveis["geracao"]["nivel"] == "usina" and ute.niveis["disponibilidade"]["identificador"] == "GOUTEB"
    pch = carregar_resultados(usinas["pch_alfa"]["pasta"] / "analises" / "resultados.pkl")
    assert pch.niveis["geracao"] == {"nivel": "conjunto", "identificador_usina": "", "identificador_conjunto": "CJU_GOCJA",
                                     "nome": "CONJ. HIDRAULICO ALFA"}
    assert pch.niveis["programacao"] == {"nivel": "conjunto", "identificador": "GOCJA-101; GOCJA-102"}
    geracao = dict(pch.achados)["Geração"]
    assert geracao.startswith("Geração média do conjunto CONJ. HIDRAULICO ALFA de 20,0 MWmed")
    assert "linhas próprias da usina sem valor" in dict(pch.achados)["Qualidade dos dados"]
    assert "Disponibilidade operacional e sincronizada" in [o["item"] for o in pch.omitidos]
    assert set(pch.comum["conferencias_nao_aplicaveis"]["conferencia"]) >= {"geracao", "vazoes"}


def test_hidreletrica_com_evt_no_caminho_de_hoje(df_sintetico: pd.DataFrame) -> None:
    res = analisar(preparar_dados(df_sintetico), {})
    assert not sem_evt(res)
    assert res.comum == {} and res.omitidos == [] and res.niveis == {} and res.trechos.empty
    assert len(res.evt_mensal) and len(res.indicadores_anuais)
