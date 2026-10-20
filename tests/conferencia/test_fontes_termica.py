"""Conferências das térmicas: G3, G4, DISPF × horas e taxas (spec 006, fase B; decisão R13; tarefa T080).

- G3 (Programação diária × programado do despacho) e G4 (verificado do despacho × Geração por usina), com a tolerância
  de 0,01 MW e sem meta;
- DISPF × horas e TEIFa/TEIP pelo CEG numa térmica;
- TEIFa e TEIP como não aplicáveis, com o motivo, quando a usina falta nas taxas (achado A12).
"""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from src.comum.perfil import Planejamento
from src.comum.regras import TOLERANCIA_COINCIDENCIA_MW
from src.conferencia.aplicabilidade import aplicaveis, tabela_nao_aplicaveis
from src.conferencia.fontes import conferencia_programacao_despacho, conferencia_verificada_despacho
from src.conferencia.indicadores import conferencia_teifa_teip
from src.tratamento.indicadores import IndicadoresONS
from src.tratamento.termica import DespachoTratado

HORAS = pd.date_range("2024-01-01 00:00", periods=6, freq="h")


def _despacho(programado, verificado) -> DespachoTratado:
    horario = pd.DataFrame({"din_instante": HORAS, "unidades": 1, "codigos": "902", "val_proggeracao": programado,
                            "val_verifgeracao": verificado})
    return DespachoTratado(unidades=pd.DataFrame(), horario=horario)


def _perfil(cobertura) -> SimpleNamespace:
    ident = SimpleNamespace(ceg="UTE.GN.GO.000104-0.01", id_ons="GOUTFI", cod_usina=None, nome_ons=None,
                            id_reservatorio=None, cod_programacao="GOUTFI", codigos_programacao=("GOUTFI",),
                            id_conjunto="CJU_GOCJFI", planejamento=(Planejamento(902, "2024-01", ""),), membros=())
    usina = SimpleNamespace(estado="GO", tipo="UTE", modalidade="TIPO I", subsistema="SE")
    return SimpleNamespace(identificacao=ident, usina=usina, cobertura=cobertura)


def test_g3_programacao_diaria_e_programado_do_despacho_com_a_tolerancia() -> None:
    programacao = SimpleNamespace(horaria=pd.DataFrame({"din_instante": HORAS[:5],
                                                        "geracao_programada_mw": [100.0, 100.0, 100.0, 50.0, 0.0]}))
    r = conferencia_programacao_despacho(programacao, _despacho([100.0, 100.01, 100.02, 50.0, 0.0, 10.0], 0.0))
    assert r.aplicavel and r.tolerancia == TOLERANCIA_COINCIDENCIA_MW and r.meta is None
    assert (r.comparados, r.coincidentes, r.divergentes) == (5, 4, 1)  # 0,01 MW coincide; 0,02 MW diverge
    assert r.tabelas["resumo"]["so_b"] == 1  # a hora só no despacho é contada, não comparada
    assert list(r.tabelas["mensal"]["horas_divergentes"]) == [1]
    assert conferencia_programacao_despacho(None, _despacho(1.0, 1.0)).aplicavel is False


def test_g4_verificado_do_despacho_e_geracao_por_usina_com_o_deslocamento() -> None:
    geracao = [0.0, 0.0, 80.0, 80.0, 80.0, 0.0]
    base = pd.DataFrame({"din_instante": HORAS, "nivel": "usina", "geracao_mw": geracao})
    r = conferencia_verificada_despacho(base, _despacho(80.0, geracao))
    assert (r.comparados, r.coincidentes, r.divergentes) == (6, 6, 0)
    # o despacho uma hora adiantado: a coincidência melhora com o deslocamento, e a G4 o registra (FR-037)
    adiantado = conferencia_verificada_despacho(base, _despacho(80.0, geracao[1:] + [0.0]))
    assert adiantado.divergentes == 2
    resumo = adiantado.tabelas["resumo"]
    assert resumo["pct_coincidentes_deslocada"]["-1 h"] == 100.0 > resumo["pct_coincidentes"]
    conjunto = base.assign(nivel="conjunto")
    assert conferencia_verificada_despacho(conjunto, _despacho(80.0, geracao)).aplicavel is False


def test_aplicabilidade_das_conferencias_da_termica() -> None:
    completo = {"geracao": "proprio", "programacao": "proprio", "disponibilidade": "proprio", "indicadores": "proprio",
                "despacho": "proprio", "cvu": "proprio"}
    assert aplicaveis(_perfil(completo)) == ["dispf_horas", "teifa_teip", "cadastro", "programacao_despacho",
                                             "verificada_despacho"]
    sem_despacho = tabela_nao_aplicaveis(_perfil({**completo, "despacho": "ausente"}), {}).set_index("conferencia")
    assert "Geração térmica por motivo de despacho não coletado" in sem_despacho.loc["programacao_despacho", "motivo"]
    assert "cobertura: ausente" in sem_despacho.loc["verificada_despacho", "motivo"]
    prog_conjunto = tabela_nao_aplicaveis(_perfil({**completo, "programacao": "conjunto"}), {}).set_index("conferencia")
    assert prog_conjunto.loc["programacao_despacho", "motivo"].startswith("Programação diária só no nível do conjunto")


def test_taxas_nao_aplicaveis_quando_a_usina_falta_nas_taxas() -> None:
    horas = pd.DataFrame({"mes": [pd.Timestamp("2024-01-01")], "ug": ["UG1"], "HP": [744.0]})
    ind = IndicadoresONS(ug_mensal=pd.DataFrame({"mes": [pd.Timestamp("2024-01-01")]}), ug_anual=pd.DataFrame(),
                         horas_estado=horas, taxas=pd.DataFrame())
    r = conferencia_teifa_teip(ind)
    assert not r.aplicavel and r.motivo == "a usina não consta das taxas TEIFa e TEIP publicadas pelo ONS no período"
    assert "sem dados no período" in conferencia_teifa_teip(None).motivo


def test_dispf_e_horas_por_estado_numa_termica() -> None:
    """DISPF × horas pelo CEG numa térmica, como nas hidrelétricas (T080, T154; FR-018). Nas térmicas, o HP soma também
    as horas equivalentes (HEDP e HEDF), o que não muda a comparação de HDP e HDF com INDISPPF e INDISPFF."""
    from src.conferencia.indicadores import conferencia_dispf_horas

    meses = [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")]
    horas = pd.DataFrame([
        {"mes": m, "ug": ug, "HP": hp, "HS": hp - 60.0 - hdf, "HRD": 0.0, "HDP": 40.0, "HDF": hdf, "HDCE": 0.0,
         "HEDP": 0.0, "HEDF": 20.0}
        for m, hp in zip(meses, (744.0, 696.0)) for ug, hdf in (("UG1", 50.0), ("UG2", 0.0))])
    ug_mensal = pd.DataFrame([
        {"mes": r.mes, "ug": r.ug, "indisppf": r.HDP / r.HP * 100.0,
         "indispff": (r.HDF + (24.0 if (r.ug == "UG1" and r.mes == meses[1]) else 0.0)) / r.HP * 100.0}
        for r in horas.itertuples()])
    ind = IndicadoresONS(ug_mensal=ug_mensal, ug_anual=pd.DataFrame(), horas_estado=horas, taxas=pd.DataFrame())
    r = conferencia_dispf_horas(ind)
    assert r.aplicavel and (r.comparados, r.coincidentes, r.divergentes) == (4, 3, 1)
    divergente = r.tabelas["divergencias"].iloc[0]
    assert (divergente["ug"], divergente["mes"], round(divergente["diferenca_forcada_h"], 6)) == ("UG1", meses[1], 24.0)
