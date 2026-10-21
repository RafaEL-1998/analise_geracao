"""Seções de eólica e solar das Análises (spec 006, fase C; decisão R19; tarefa T102).

- fator de capacidade publicado, com o nível, por mês e por ano;
- energia cortada só nas semi-horas restritas, por mês e por razão (a razão do conjunto, a energia da usina), com as
  semi-horas sem a marca contadas à parte e a diferença bruta para comparação;
- recurso × geração por faixa, sem as semi-horas com o recurso inválido, contadas;
- aderência à programação: os maiores desvios;
- seções sem base omitidas com o motivo; série curta sem a sazonalidade.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import pandas as pd
import pytest

from src.analises.comum_tipos import base_programacao_conjunto, programacao_comum, sazonalidade
from src.analises.renovavel import (
    SEM_RAZAO,
    TITULO_CORTE,
    TITULO_FATOR_CAPACIDADE,
    TITULO_RECURSO,
    achados_renovavel,
    analisar_renovavel,
    corte_por_razao,
    energia_cortada,
    fator_capacidade_publicado,
    maiores_desvios_programacao,
    omissoes_renovavel,
    recurso_por_faixa,
)

INICIO = pd.Timestamp("2024-01-31 23:00")


def _fc() -> pd.DataFrame:
    horas = pd.date_range(INICIO, periods=3, freq="h")  # 31/01 23h, 01/02 00h e 01h
    return pd.DataFrame({"din_instante": horas, "nivel": "conjunto", "val_geracaoprogramada": 10.0,
                         "val_geracaoverificada": [10.0, 20.0, 31.5], "val_capacidadeinstalada": 30.0,
                         "val_fatorcapacidade": [0.33, 0.67, 1.05], "sinal_fc_fora_0_1": [False, False, True],
                         "sinal_acima_capacidade": [False, False, True]})


def _semi() -> pd.DataFrame:
    linhas = [
        # instante, verificada, estimada, recurso, inválido, restrita, sem marca, cortada, razão, nível da razão
        ("2024-02-01 10:00", 10.0, 30.0, 9.0, False, True, False, 10.0, "REL", "conjunto"),
        ("2024-02-01 10:30", 10.0, 20.0, 9.0, False, True, False, 5.0, "CNF", "conjunto"),
        ("2024-02-01 11:00", 10.0, 14.0, 5.0, False, True, False, 2.0, "", "conjunto"),  # restrita sem código
        ("2024-02-01 11:30", 10.0, 30.0, 5.0, True, False, False, 0.0, "", "conjunto"),  # erro de estimativa
        ("2024-03-01 00:00", 4.0, 8.0, -0.5, False, False, True, math.nan, "", ""),  # sem a marca
        ("2024-03-01 00:30", 4.0, 4.0, 1.0, False, False, False, 0.0, "", ""),
    ]
    colunas = ["din_instante", "val_geracaoverificada", "val_geracaoestimada", "val_recurso",
               "sinal_recurso_invalido", "restrita", "sem_marca_restricao", "energia_cortada_mwh",
               "cod_razaorestricao", "nivel_razao"]
    t = pd.DataFrame(linhas, columns=colunas)
    t["din_instante"] = pd.to_datetime(t["din_instante"])
    return t


def test_fator_de_capacidade_publicado_com_o_nivel() -> None:
    anual = fator_capacidade_publicado(_fc(), "Y").set_index("periodo")
    assert anual.loc[2024, "fator_capacidade_pct"] == pytest.approx(61.5 / 90 * 100)  # Σ verificada ÷ Σ capacidade
    assert anual.loc[2024, "nivel"] == "conjunto" and bool(anual.loc[2024, "ano_parcial"])
    assert anual.loc[2024, "horas_fc_fora_0_1"] == 1 and anual.loc[2024, "horas_acima_capacidade"] == 1
    mensal = fator_capacidade_publicado(_fc(), "M")
    assert mensal["horas"].tolist() == [1, 2] and mensal["fator_capacidade_pct"].iloc[0] == pytest.approx(100 / 3)


def test_energia_cortada_por_mes_e_por_razao() -> None:
    mensal = energia_cortada(_semi(), "M").set_index("periodo")
    fev = mensal.loc[pd.Timestamp("2024-02-01")]
    assert fev["energia_cortada_mwh"] == 17.0 and fev["semi_horas_restritas"] == 3 and fev["horas_restritas"] == 1.5
    assert (fev["cortada_rel_mwh"], fev["cortada_cnf_mwh"], fev["cortada_sem_razao_mwh"]) == (10.0, 5.0, 2.0)
    assert fev["energia_estimada_com_marca_mwh"] == 47.0 and fev["pct_estimada"] == pytest.approx(17 / 47 * 100)
    assert fev["diferenca_bruta_mwh"] == 27.0  # inclui a diferença fora das semi-horas restritas
    mar = mensal.loc[pd.Timestamp("2024-03-01")]
    assert mar["semi_horas_sem_marca"] == 1 and mar["energia_estimada_com_marca_mwh"] == 2.0
    razoes = corte_por_razao(_semi()).set_index("razao")
    assert list(razoes.index) == ["REL", "CNF", SEM_RAZAO]
    assert razoes.loc["REL", "pct_cortada"] == pytest.approx(10 / 17 * 100)


def test_recurso_por_faixa_sem_as_invalidas() -> None:
    faixas = recurso_por_faixa(_semi(), 2.0).set_index("faixa_inicio")
    assert list(faixas.index) == [0.0, 4.0, 8.0]  # o recurso negativo entra na primeira faixa
    assert faixas.loc[4.0, "semi_horas"] == 1  # a semi-hora inválida da faixa 4–6 fica fora
    assert faixas.loc[0.0, "semi_horas"] == 2 and faixas.loc[8.0, "geracao_media_mw"] == 10.0


def test_maiores_desvios_da_programacao() -> None:
    horas = pd.date_range("2024-02-01", periods=4, freq="h")
    base = pd.DataFrame({"din_instante": horas, "nivel": "usina", "geracao_mw": [10.0, 5.0, 15.0, 20.0],
                         "geracao_programada_mw": [10.0, 10.0, 10.0, None]})
    desvios = maiores_desvios_programacao(base, "usina", 2)
    assert desvios["din_instante"].tolist() == [horas[1], horas[2]]  # empate em ordem cronológica
    assert desvios["desvio_mw"].tolist() == [-5.0, 5.0]
    assert maiores_desvios_programacao(base, "conjunto").empty


def test_campo_renovavel_e_constatacoes() -> None:
    base = pd.DataFrame(columns=["din_instante", "nivel", "geracao_mw", "geracao_programada_mw"])
    r = analisar_renovavel({"fator_capacidade_horario": _fc(), "restricao_semi_horaria": _semi()}, base, "EOL", 30.0)
    assert r["fator_capacidade"]["nivel"] == "conjunto" and r["restricao"]["nivel_razao"] == "conjunto"
    assert r["restricao"]["resumo"]["energia_cortada_mwh"] == 17.0 and r["recurso"]["unidade"] == "m/s"
    assert r["recurso"]["resumo"]["semi_horas_invalidas"] == 1 and r["programacao"] == {}
    titulos = [t for t, _ in achados_renovavel(r)]
    assert titulos == ["Fator de capacidade", "Energia cortada", "Recurso × geração"]
    assert analisar_renovavel({}, base, "UFV", 30.0) == {}


def _perfil(cobertura: dict) -> SimpleNamespace:
    return SimpleNamespace(
        usina=SimpleNamespace(tipo="EOL", slug="eol", estado="CE", modalidade="TIPO I", subsistema=None),
        identificacao=SimpleNamespace(ceg="EOL.CV.CE.000080-0.01", id_ons="CEEOX", id_conjunto=None, membros=(),
                                      cod_usina=None, nome_ons=None, id_reservatorio=None, cod_programacao="CEEOX",
                                      codigos_programacao=("CEEOX",), planejamento=()),
        cobertura=cobertura)


def test_secoes_sem_base_omitidas_com_o_motivo() -> None:
    motivos = {o["item"]: o["motivo"] for o in omissoes_renovavel(_perfil({"geracao": "proprio"}), {})}
    assert set(motivos) == {TITULO_FATOR_CAPACIDADE, TITULO_CORTE, TITULO_RECURSO}
    assert "sem o Fator de capacidade" in motivos[TITULO_FATOR_CAPACIDADE]
    assert "sem a Restrição com detalhe" in motivos[TITULO_CORTE]
    coletada = _perfil({"geracao": "proprio", "fator_capacidade": "proprio", "restricao_detalhe": "proprio"})
    motivos = {o["item"]: o["motivo"] for o in omissoes_renovavel(coletada, {"fator_capacidade": {"nivel": "usina"}})}
    assert set(motivos) == {TITULO_CORTE, TITULO_RECURSO} and "período" in motivos[TITULO_CORTE]


def test_serie_curta_sem_sazonalidade() -> None:
    horas = pd.date_range("2026-08-22", "2026-10-19 23:00", freq="h")
    base = pd.DataFrame({"din_instante": horas, "nivel": "usina", "geracao_mw": 1.0})
    _, sem = sazonalidade(base)
    assert sem == ["usina"]


def test_estimativa_ausente_fora_dos_totais_e_das_medias() -> None:
    """Verificada e estimada nas mesmas semi-horas; a restrita sem estimativa contada (decisão de 21/10/2026)."""
    semi = _semi().assign(sinal_estimada_ausente=[False, True, False, False, False, False])
    semi.loc[1, "val_geracaoestimada"], semi.loc[1, "energia_cortada_mwh"] = 0.0, float("nan")
    fev = energia_cortada(semi, "M").set_index("periodo").loc[pd.Timestamp("2024-02-01")]
    assert (fev["semi_horas_sem_estimativa"], fev["semi_horas_restritas_sem_estimativa"]) == (1, 1)
    assert fev["energia_verificada_mwh"] == 15.0 and fev["energia_estimada_mwh"] == 37.0  # sem a semi-hora das 10h30
    assert fev["energia_cortada_mwh"] == 12.0
    faixas = recurso_por_faixa(semi, 2.0).set_index("faixa_inicio")
    assert faixas.loc[8.0, "estimada_media_mw"] == 30.0  # a estimada 0 fica fora da média da faixa
    r = analisar_renovavel({"restricao_semi_horaria": semi}, pd.DataFrame(
        columns=["din_instante", "nivel", "geracao_mw", "geracao_programada_mw"]), "EOL", 30.0)
    assert "Sem a estimativa do ONS" in dict(achados_renovavel(r))["Energia cortada"]


def test_recurso_acima_do_limite_fisico_fora_das_faixas() -> None:
    """Decisão do usuário de 21/10/2026: vento acima de 40 m/s sem a marca do ONS fica fora das faixas, contado."""
    semi = _semi()
    semi.loc[5, "val_recurso"] = 120.0  # falha de medição não marcada
    faixas = recurso_por_faixa(semi, 2.0, 40.0)
    assert faixas["faixa_inicio"].max() < 40.0 and faixas["semi_horas"].sum() == 4
    r = analisar_renovavel({"restricao_semi_horaria": semi}, pd.DataFrame(
        columns=["din_instante", "nivel", "geracao_mw", "geracao_programada_mw"]), "EOL", 30.0)
    assert r["recurso"]["resumo"]["semi_horas_implausiveis"] == 1 and r["recurso"]["limite"] == 40.0
    assert "acima do limite físico" in dict(achados_renovavel(r))["Recurso × geração"]


def test_programacao_comparada_no_nivel_do_conjunto() -> None:
    """T157: com a base horária da usina, a programação do conjunto é comparada com a geração do conjunto."""
    horas = pd.date_range("2024-02-01", periods=3, freq="h")
    geracao = pd.DataFrame({"din_instante": horas, "val_geracao": [10.0, 20.0, 30.0]})
    programada = pd.DataFrame({"din_instante": horas[1:], "geracao_programada_mw": [18.0, 30.0]})
    base = base_programacao_conjunto(geracao, programada)
    assert set(base["nivel"]) == {"conjunto"} and base["geracao_programada_mw"].isna().sum() == 1
    p = programacao_comum(base, "conjunto")
    assert p["nivel"] == "conjunto" and p["resumo"]["horas_comuns"] == 2
    assert p["resumo"]["desvio_medio_absoluto_mw"] == 1.0
