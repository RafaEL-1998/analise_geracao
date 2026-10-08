"""Testes das seis conferências entre fontes e do resultado de conferência (spec da Conferência)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import List

import pandas as pd
import pytest

from src.comum import caminhos
from src.comum.perfil import carregar_perfil
from src.conferencia import etapa
from src.conferencia.cadastro import conferencia_cadastro
from src.conferencia.disponibilidade import conferencia_disponibilidade, conferir_com_evt
from src.conferencia.geracao import conferencia_geracao, conferir_geracao
from src.conferencia.indicadores import (
    comparar_indicadores_e_horas,
    conferencia_dispf_horas,
    conferencia_teifa_teip,
    recalcular_taxas,
)
from src.conferencia.resultado import (
    ResultadoConferencia,
    carregar_conferencias,
    diferenca_absoluta,
    nao_aplicavel,
)
from src.conferencia.vazoes import alinhar_com_evt, conferencia_vazoes
from src.pipeline import CODIGO_META_HIDROLOGIA
from src.tratamento.indicadores import IndicadoresONS
from src.tratamento.series import SerieConjunto

PERFIL = carregar_perfil("sao_domingos")


def _serie(horaria: pd.DataFrame) -> SerieConjunto:
    return SerieConjunto(horaria=horaria)


def _ger(valores: List[float], inicio: str = "2025-01-31 22:00") -> pd.DataFrame:
    return pd.DataFrame({"din_instante": pd.date_range(inicio, periods=len(valores), freq="h"), "val_geracao": valores,
                         "qualidade": "OK", "arquivo_origem": "G.parquet"})


def _disp(valores: List[tuple], inicio: str = "2025-01-01 00:00") -> pd.DataFrame:
    instantes = pd.date_range(inicio, periods=len(valores), freq="h")
    return pd.DataFrame({"din_instante": instantes, "val_potenciainstalada": 48.0,
                         "val_dispoperacional": [v[0] for v in valores], "val_dispsincronizada": [v[1] for v in valores],
                         "qualidade": "OK", "arquivo_origem": "D.csv"})


def _hid(valores: List[tuple], inicio: str = "2025-01-01 00:00") -> pd.DataFrame:
    instantes = pd.date_range(inicio, periods=len(valores), freq="h")
    return pd.DataFrame({"din_instante": instantes, "val_vazaoafluente": [v[0] for v in valores],
                         "val_vazaoturbinada": [v[1] for v in valores], "val_vazaovertida": [v[2] for v in valores],
                         "val_nivelmontante": [v[3] for v in valores], "val_niveljusante": 309.0, "val_volumeutil": 50.0,
                         "val_vazaodefluente": [v[1] + v[2] for v in valores], "val_vazaovertidanaoturbinavel": 0.0,
                         "qualidade": "OK"})


def _evt(geracao=None, disponibilidade=None, turbinada=None, vertida=None, inicio="2025-01-01 00:00",
         horas: int = 0) -> pd.DataFrame:
    n = horas or len(next(v for v in (geracao, disponibilidade, turbinada, vertida) if v is not None))
    return pd.DataFrame({
        "din_instante": pd.date_range(inicio, periods=n, freq="h"),
        "val_geracao": geracao if geracao is not None else [20.0] * n,
        "val_disponibilidade": disponibilidade if disponibilidade is not None else [43.75] * n,
        "val_vazaoturbinada": turbinada if turbinada is not None else [80.0] * n,
        "val_vazaovertida": vertida if vertida is not None else [20.0] * n,
    })


# ---------------------------------------------------------------------------
# Geração, disponibilidade e vazões
# ---------------------------------------------------------------------------


def test_conferencia_da_geracao_horaria_e_mensal() -> None:
    ger = _ger([30.0, 30.0, 20.0, 21.0, 10.0])  # 31/01 22h e 23h; 01/02 00h a 02h
    evt = _evt(geracao=[30.0, 30.005, 25.0, 21.0], inicio="2025-01-31 22:00")  # 01/02 02h só na série oficial
    resumo, mensal, divergencias = conferir_geracao(ger, evt)
    assert (resumo["horas_comuns"], resumo["coincidentes"], resumo["divergentes"]) == (4, 3, 1)
    assert (resumo["so_ons_geracao"], resumo["so_base_evt"]) == (1, 0)
    assert len(divergencias) == 1 and divergencias.iloc[0]["inicio"] == pd.Timestamp("2025-02-01 00:00")
    m = mensal.set_index("mes")
    assert m.loc["2025-01", "energia_base_evt_mwh"] == pytest.approx(60.005)
    assert m.loc["2025-02", "diferenca_mwh"] == pytest.approx(51.0 - 46.0)
    r = conferencia_geracao(_serie(ger), evt)
    assert (r.comparados, r.coincidentes, r.divergentes, r.unidade) == (4, 3, 1, "horas")
    assert r.periodo == (pd.Timestamp("2025-01-31 22:00"), pd.Timestamp("2025-02-01 01:00"))
    assert r.tabelas["resumo"] == resumo and r.tolerancia == 0.01


def test_conferencia_da_disponibilidade_declarada() -> None:
    disp = _disp([(43.75, 24.0), (43.75, 24.0), (40.0, 24.0), (41.0, 24.0), (43.75, 0.0), (43.75, 0.0)])
    evt = _evt(disponibilidade=[43.75, 43.755, 43.75, 43.75, 43.75])
    resumo, divergencias = conferir_com_evt(disp, evt)
    assert (resumo["horas_comuns"], resumo["coincidentes"], resumo["divergentes"]) == (5, 3, 2)
    assert (resumo["so_ons_disponibilidade"], resumo["so_base_evt"]) == (1, 0)
    linha = divergencias.iloc[0]
    assert (len(divergencias), linha["horas"]) == (1, 2)  # 02h e 03h formam um único período contínuo
    assert linha["diferenca_maxima_mw"] == pytest.approx(3.75)
    r = conferencia_disponibilidade(_serie(disp), evt)
    assert (r.comparados, r.coincidentes, r.divergentes) == (5, 3, 2)


def test_alinhamento_das_vazoes_com_a_meta() -> None:
    hid = _hid([(100, 80, 20, 344.5)] * 200)
    ok = alinhar_com_evt(hid, _evt(horas=200)).iloc[0]
    assert (ok["horas_comuns"], ok["coincidentes_ambas"], ok["confirmado"]) == (200, 200, True)
    assert (ok["meta_pct"], ok["tolerancia_m3s"], ok["deslocamento_aplicado_h"]) == (99.0, 0.5, -1)
    evt_ruim = _evt(turbinada=[80.0] * 197 + [70.0] * 3)  # 98,5% coincidentes
    r = conferencia_vazoes(_serie(hid), evt_ruim)
    assert r.tabelas["alinhamento"].iloc[0]["pct_coincidencia"] == pytest.approx(98.5)
    assert (r.comparados, r.coincidentes, r.divergentes) == (200, 197, 3)
    assert (r.meta, r.meta_atingida) == (99.0, False)
    assert r.resumo()["meta_atingida"] is False and r.resumo()["pct_coincidencia"] == pytest.approx(98.5)


def test_vazao_negativa_nao_entra_no_alinhamento() -> None:
    hid = _hid([(100, 80, 20, 344.5)] * 10 + [(100, -1, 20, 344.5)])
    r = conferencia_vazoes(_serie(hid), _evt(horas=11))
    assert r.comparados == 10 and r.meta_atingida


def test_conferencias_sem_a_base_nao_sao_aplicaveis() -> None:
    evt = _evt(horas=3)
    vazia = SerieConjunto(horaria=pd.DataFrame(columns=["din_instante", "qualidade"]))
    for r in (conferencia_geracao(None, evt), conferencia_disponibilidade(vazia, evt), conferencia_vazoes(None, evt),
              conferencia_dispf_horas(None), conferencia_teifa_teip(None), conferencia_cadastro(None, PERFIL)):
        assert not r.aplicavel and r.motivo
        assert r.resumo() == {"aplicavel": False, "motivo": r.motivo}
    assert conferencia_vazoes(None, evt).meta == 99.0


def test_resultado_confere_a_soma_e_o_nome() -> None:
    with pytest.raises(ValueError):
        ResultadoConferencia(id="geracao", bases=("a", "b"), unidade="horas", comparados=3, coincidentes=1,
                             divergentes=1)
    with pytest.raises(ValueError):
        nao_aplicavel("outra", ("a", "b"), "horas", "motivo")


# ---------------------------------------------------------------------------
# Indicadores oficiais
# ---------------------------------------------------------------------------


def _horas_sinteticas() -> pd.DataFrame:
    linhas = []
    for mes in pd.date_range("2019-03-01", "2024-02-01", freq="MS"):
        hp = mes.days_in_month * 24.0
        # UG1: 6 h programadas e 4 h forçadas por mês; UG2: 20 h equivalentes de limitação forçada e 50 h em reserva
        linhas.append({"mes": mes, "ug": 1, "HP": hp, "HS": hp - 10, "HRD": 0.0, "HDP": 6.0, "HDF": 4.0,
                       "HDCE": 0.0, "HEDP": 0.0, "HEDF": 0.0})
        linhas.append({"mes": mes, "ug": 2, "HP": hp, "HS": hp - 70, "HRD": 50.0, "HDP": 0.0, "HDF": 0.0,
                       "HDCE": 0.0, "HEDP": 0.0, "HEDF": 20.0})
    h = pd.DataFrame(linhas)
    h["num_versao"] = 1.0
    h["residuo_identidade_h"] = h["HP"] - h[["HS", "HRD", "HDP", "HDF", "HDCE", "HEDP", "HEDF"]].sum(axis=1)
    h["potencia_mw"] = 24.0
    return h


def _indicadores_sinteticos() -> IndicadoresONS:
    horas = _horas_sinteticas()
    h = horas[horas["mes"] >= "2023-11-01"]
    mensal = h[["mes", "ug", "HP", "HDP", "HDF"]].copy()
    mensal["indisppf"] = mensal["HDP"] / mensal["HP"] * 100
    mensal["indispff"] = mensal["HDF"] / mensal["HP"] * 100
    # jan/2024, UG2: as 50 h de reserva aparecem como indisponibilidade programada no DISPF
    sel = (mensal["mes"] == "2024-01-01") & (mensal["ug"] == 2)
    mensal.loc[sel, "indisppf"] = 50 / 744 * 100
    mensal = mensal.drop(columns=["HP", "HDP", "HDF"])
    w = horas.tail(120)
    teifa = (w["HDF"] + w["HEDF"]).sum() / (w["HP"] - w["HDP"] - w["HEDP"]).sum()
    teip = (w["HDP"] + w["HEDP"]).sum() / w["HP"].sum()
    taxas = pd.DataFrame({"mes": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")],
                          "teifa": [teifa, teifa], "teip": [teip, teip], "num_versao": [1.0, 1.0]})
    return IndicadoresONS(ug_mensal=mensal, ug_anual=pd.DataFrame(), horas_estado=horas, taxas=taxas)


def test_recalculo_das_taxas_so_com_a_janela_completa() -> None:
    ind = _indicadores_sinteticos()
    recalculo = recalcular_taxas(ind.horas_estado, ind.taxas).set_index("mes")
    assert pd.isna(recalculo.loc["2024-01-01", "teifa_recalculada"])  # jan/2024 não tem 60 meses de horas
    assert recalculo.loc["2024-02-01", "diferenca_teifa_pp"] == pytest.approx(0.0, abs=1e-9)
    assert recalculo.loc["2024-02-01", "diferenca_teip_pp"] == pytest.approx(0.0, abs=1e-9)
    r = conferencia_teifa_teip(ind)
    assert (r.comparados, r.coincidentes, r.divergentes, r.unidade) == (1, 1, 0, "meses")
    assert r.periodo == (pd.Timestamp("2024-02-01"), pd.Timestamp("2024-02-01"))
    assert r.tabelas["diferenca_maxima_pp"] == pytest.approx(0.0, abs=1e-9)


def test_taxas_sem_janela_completa_nao_sao_aplicaveis_mas_registram_a_tabela() -> None:
    ind = _indicadores_sinteticos()
    ind.taxas = ind.taxas.iloc[:1]
    r = conferencia_teifa_teip(ind)
    assert not r.aplicavel and "janela de 60 meses" in r.motivo and len(r.tabelas["recalculo"]) == 1


def test_divergencia_entre_dispf_e_horas() -> None:
    ind = _indicadores_sinteticos()
    div = comparar_indicadores_e_horas(ind.ug_mensal, ind.horas_estado)
    linha = div.iloc[0]
    assert len(div) == 1 and (linha["mes"], linha["ug"]) == (pd.Timestamp("2024-01-01"), 2)
    assert linha["horas_programadas_indisppf"] == pytest.approx(50.0)
    r = conferencia_dispf_horas(ind)
    assert (r.comparados, r.coincidentes, r.divergentes, r.unidade) == (8, 7, 1, "meses-unidade")


# ---------------------------------------------------------------------------
# Cadastro
# ---------------------------------------------------------------------------


def _ficha(**valores) -> pd.DataFrame:
    base = {"nom_usina": "UHE SÃO DOMINGOS", "ceg": PERFIL.identificacao.ceg, "id_ons": PERFIL.identificacao.id_ons,
            "val_potenciaautorizada": 48.0, "id_estado": PERFIL.usina.estado, "linhas_ceg": 1}
    base.update(valores)
    return pd.DataFrame([base])


def test_cadastro_sem_divergencia() -> None:
    r = conferencia_cadastro(_ficha(), PERFIL)
    assert (r.comparados, r.coincidentes, r.divergentes, r.unidade) == (4, 4, 0, "campos")
    assert r.tabelas["divergencias"] == "" and set(r.tabelas["campos"]["situacao"]) == {"CONFERE"}


@pytest.mark.parametrize("valores, trecho", [
    ({"val_potenciaautorizada": 47.5}, "potência autorizada de 47,5 MW (projeto: 48 MW)"),
    ({"val_potenciaautorizada": ""}, "potência autorizada de"),
    ({"id_estado": "GO"}, "estado GO (projeto: MS)"),
    ({"id_ons": ""}, "id ONS não informado (projeto: MSUHSD)"),
    ({"linhas_ceg": 2}, "2 linhas com o CEG do projeto (usada a primeira)"),
])
def test_cadastro_com_divergencias_do_perfil(valores, trecho) -> None:
    r = conferencia_cadastro(_ficha(**valores), PERFIL)
    assert r.divergentes == 1 and trecho in r.tabelas["divergencias"]


# ---------------------------------------------------------------------------
# Etapa
# ---------------------------------------------------------------------------


def test_etapa_grava_os_resultados_e_sai_com_3_abaixo_da_meta(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(caminhos, "DATA_DIR", tmp_path / "data")
    hid = _hid([(100, 80, 20, 344.5)] * 200)
    resultados = {
        "geracao": conferencia_geracao(_serie(_ger([30.0, 30.0])), _evt(geracao=[30.0, 30.0], inicio="2025-01-31 22:00")),
        "disponibilidade": conferencia_disponibilidade(None, _evt(horas=2)),
        "vazoes": conferencia_vazoes(_serie(hid), _evt(turbinada=[80.0] * 197 + [70.0] * 3)),
        "dispf_horas": conferencia_dispf_horas(_indicadores_sinteticos()),
        "teifa_teip": conferencia_teifa_teip(_indicadores_sinteticos()),
        "cadastro": conferencia_cadastro(_ficha(), PERFIL),
    }
    pasta = caminhos.pasta_etapa("sao_domingos", "conferencia")
    pasta.mkdir(parents=True)
    (pasta / "disponibilidade.csv").write_text("antigo", encoding="utf-8")  # de uma execução anterior
    monkeypatch.setattr(etapa, "conferir", lambda perfil: resultados)
    r = etapa.executar_conferencia(PERFIL)
    assert r.codigo == CODIGO_META_HIDROLOGIA
    assert r.resumo["vazoes"]["meta_atingida"] is False and r.resumo["disponibilidade"]["aplicavel"] is False
    nomes = sorted(p.name for p in r.arquivos)
    assert nomes == sorted(["conferencias.pkl", "geracao.csv", "geracao_divergencias.csv", "vazoes.csv",
                            "dispf_horas.csv", "teifa_teip.csv", "cadastro.csv"])
    assert not (pasta / "disponibilidade.csv").exists() and not list(pasta.glob("*.bak"))
    lidos = carregar_conferencias(pasta / "conferencias.pkl")
    assert set(lidos) == set(resultados) and lidos["vazoes"].meta_atingida is False


# ---------------------------------------------------------------------------
# Tolerâncias, horas sinalizadas e texto do cadastro
# ---------------------------------------------------------------------------


def test_diferenca_igual_a_tolerancia_coincide() -> None:
    """"Até 0,01 MW" inclui 0,01 MW: em ponto flutuante, 30,01 − 30,00 dá 0,010000000000001563."""
    assert abs(30.01 - 30.0) > 0.01 and diferenca_absoluta(30.01 - 30.0) == 0.01
    resumo, _, _ = conferir_geracao(_ger([30.0, 30.0]), _evt(geracao=[30.01, 30.02], inicio="2025-01-31 22:00"))
    assert (resumo["coincidentes"], resumo["divergentes"]) == (1, 1)
    resumo, _ = conferir_com_evt(_disp([(30.0, 0.0)]), _evt(disponibilidade=[30.01]))
    assert (resumo["coincidentes"], resumo["divergentes"]) == (1, 0)
    hid = _hid([(100, 64.4, 20, 344.5)] * 2)  # 64,4 − 63,9 dá 0,5000000000000071
    assert alinhar_com_evt(hid, _evt(turbinada=[63.9, 63.9])).iloc[0]["coincidentes_ambas"] == 2


def test_hora_sinalizada_da_disponibilidade_nao_conta_como_ausente() -> None:
    disp = _disp([(43.75, 24.0)] * 3)
    disp.loc[1, "qualidade"] = "D1"
    resumo, _ = conferir_com_evt(disp, _evt(disponibilidade=[43.75] * 3))
    assert (resumo["horas_comuns"], resumo["horas_sinalizadas_excluidas"], resumo["so_base_evt"]) == (2, 1, 0)


def test_potencia_do_perfil_com_casas_decimais_no_texto_da_divergencia() -> None:
    perfil = SimpleNamespace(potencia_autorizada_esperada_mw=29.5, usina=SimpleNamespace(estado=PERFIL.usina.estado),
                             identificacao=SimpleNamespace(id_ons=PERFIL.identificacao.id_ons))
    r = conferencia_cadastro(_ficha(val_potenciaautorizada=30.0), perfil)
    assert r.divergentes == 1 and "(projeto: 29,5 MW)" in r.tabelas["divergencias"]


def test_mes_unidade_com_valor_ausente_fica_fora_do_dispf_e_e_contado() -> None:
    """Decisão de 08/10/2026 (FR-014): sem um dos valores, o mês-unidade não é comparado e é contado à parte."""
    ind = _indicadores_sinteticos()
    sel = (ind.ug_mensal["mes"] == "2023-12-01") & (ind.ug_mensal["ug"] == 1)
    ind.ug_mensal.loc[sel, "indispff"] = float("nan")
    r = conferencia_dispf_horas(ind)
    assert (r.comparados, r.coincidentes, r.divergentes) == (7, 6, 1)
    assert r.tabelas["sem_valor"] == 1


def test_mes_com_taxa_publicada_ausente_fica_fora_e_e_contado() -> None:
    """Decisão de 08/10/2026 (FR-016): o mês de janela completa sem a taxa publicada não é comparado."""
    ind = _indicadores_sinteticos()
    ind.taxas.loc[ind.taxas["mes"] == "2024-02-01", "teip"] = float("nan")
    r = conferencia_teifa_teip(ind)
    assert r.aplicavel and (r.comparados, r.coincidentes, r.divergentes) == (0, 0, 0)
    assert r.tabelas["sem_valor"] == 1 and r.periodo is None


def test_mes_unidade_incompleto_nao_entra_nas_divergencias() -> None:
    """Sem HDP, o mês-unidade fica fora, mesmo com a diferença das horas forçadas acima de 1 h."""
    ind = _indicadores_sinteticos()
    sel = (ind.horas_estado["mes"] == "2023-12-01") & (ind.horas_estado["ug"] == 1)
    ind.horas_estado.loc[sel, "HDP"] = float("nan")
    ind.horas_estado.loc[sel, "HDF"] = 9.0  # 5 h além das 4 h publicadas no INDISPFF
    r = conferencia_dispf_horas(ind)
    assert (r.comparados, r.coincidentes, r.divergentes, r.tabelas["sem_valor"]) == (7, 6, 1, 1)
    assert pd.Timestamp("2023-12-01") not in set(r.tabelas["divergencias"]["mes"])
