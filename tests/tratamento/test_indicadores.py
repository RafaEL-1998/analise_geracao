"""Testes do tratamento dos indicadores por unidade geradora e das taxas TEIFa e TEIP."""

from __future__ import annotations

import logging

import pandas as pd
import pytest

from src.tratamento.indicadores import (
    IndicadoresONS,
    carregar_indicadores_tratados,
    chave_ug,
    exportar_indicadores,
    juntar_taxas_operativas,
    nome_ug,
    recortar_periodo,
    rotulo_no_nome,
    tipar_ug,
    tratar_horas_estado,
    tratar_indicadores_ug,
    tratar_taxas,
)


def test_rotulo_da_unidade_no_nome() -> None:
    assert rotulo_no_nome("UG   24 MW SAO DOMINGOS              2 MS") == "2"
    assert rotulo_no_nome("UG 10P3 MW CURUA-UNA                 3 PA   ") == "3"
    assert rotulo_no_nome("UG   40 MW APARECIDA                07 AM") == "7"  # sem o zero à esquerda, como o número
    assert rotulo_no_nome("UG 57P8 MW TRES LAGOAS              2A MS") == "2A"
    assert rotulo_no_nome("UG  700 MW ITAIPU 60 HZ           G18A PR") == "G18A"  # o mesmo do num_unidadegeradora
    assert rotulo_no_nome("UG 28,0 MW SANTA BRANCA UG1 SP") == "1"  # o mesmo de 'UG 28P0 MW SANTA BRANCA 1 SP'
    assert rotulo_no_nome("UG SEM ROTULO") is None


def test_ug_inteiro_quando_os_rotulos_sao_so_algarismos() -> None:
    """As usinas de hoje (unidades numeradas) continuam com a unidade inteira: as referências não mudam."""
    ug = tipar_ug(pd.Series(["1", " 2 ", "07", None]))
    assert str(ug.dtype) == "Int64" and list(ug[:3]) == [1, 2, 7] and pd.isna(ug[3])


def test_ordem_natural_e_nome_da_unidade() -> None:
    assert sorted(["10", "2", "G18A", "18A", "18", "9A", "1"], key=chave_ug) == ["1", "2", "9A", "10", "18", "18A", "G18A"]
    assert sorted(["TG10", "TG4", "2A", "1C", "1A"], key=chave_ug) == ["1A", "1C", "2A", "TG4", "TG10"]
    assert [nome_ug(u) for u in (2, 2.0, "1A", "TG10")] == ["UG2", "UG2", "UG1A", "UG TG10"]


# Unidades da UTE Três Lagoas nos indicadores de 2026 (código do equipamento, rótulo, potência)
_TRES_LAGOAS = [("MSTLA-0UG1", "1A", "58.3"), ("MSTLA-0UG2", "1B", "58.1"), ("MSTLA-0UG5", "2A", "57.8"),
                ("MSTLA-0UG6", "2B", "60.9"), ("MSLCP-0UG1C", "1C", "57.3"), ("MSLCP-0UG2C", "2C", "57.3")]


def _indicadores_publicados(unidades: list, mes: str = "2026-03-01") -> pd.DataFrame:
    return pd.DataFrame([{
        "num_unidadegeradora": f"{rotulo}    ", "cod_equipamento": codigo, "val_potencia": potencia,
        "dat_mesreferencia": mes, "val_dispf": "100", "val_indisppf": "0", "val_indispff": "0", "val_dmdff": "0",
        "val_fdff": "0", "val_tdff": "0", "id_usina": "MSUTLG", "nom_agenteproprietario": "AGENTE",
        "nom_modalidadeoperacao": "TIPO I", "arquivo_origem": "IND_2026.csv",
    } for codigo, rotulo, potencia in unidades])


def _horas_publicadas(rotulos: list, mes: str = "03/2026") -> pd.DataFrame:
    return pd.DataFrame([{"nom_unidadegeradora": f"UG 58P3 MW TRES LAGOAS              {rotulo} MS", "dat_periodo": mes,
                          "nom_tpinsumo": "HP", "val_parametro": "744.0", "num_versao": "1.0"} for rotulo in rotulos])


def test_unidades_com_letra_ficam_separadas_em_ordem_natural() -> None:
    """Ciclo combinado (UTE Três Lagoas): cada unidade com o rótulo publicado, nas duas bases, para a junção da
    Conferência por mês e unidade (bug unidade-com-letra)."""
    mensal = tratar_indicadores_ug(_indicadores_publicados(_TRES_LAGOAS), anual=False)
    assert list(mensal["ug"]) == ["1A", "1B", "1C", "2A", "2B", "2C"]
    horas = tratar_horas_estado(_horas_publicadas([rotulo for _, rotulo, _ in reversed(_TRES_LAGOAS)]))
    assert list(horas["ug"]) == ["1A", "1B", "1C", "2A", "2B", "2C"]
    assert len(horas.merge(mensal[["mes", "ug", "potencia_mw"]], on=["mes", "ug"])) == 6


def test_unidade_com_prefixo_ug_no_nome_e_o_numero() -> None:
    """UHE Santa Branca: os parâmetros das taxas publicam 'UG1' até 2025 e '1' em 2026, como os indicadores. As duas
    formas são a mesma unidade, inteira, e juntam com os indicadores por mês e unidade."""
    horas = tratar_horas_estado(pd.concat([_horas_publicadas(["UG1", "UG2"], mes="12/2025"),
                                           _horas_publicadas(["1", "2"], mes="01/2026")], ignore_index=True))
    assert str(horas["ug"].dtype) == "Int64" and list(horas["ug"]) == [1, 2, 1, 2]
    unidades = [("RJSBRA0UG1", "1", "28"), ("RJSBRA0UG2", "2", "28")]
    mensal = tratar_indicadores_ug(pd.concat([_indicadores_publicados(unidades, mes=m)
                                              for m in ("2025-12-01", "2026-01-01")], ignore_index=True), anual=False)
    assert len(horas.merge(mensal[["mes", "ug", "potencia_mw"]], on=["mes", "ug"])) == 4


def test_linha_sem_rotulo_da_unidade_e_avisada(caplog) -> None:
    bruto = pd.concat([_horas_publicadas(["1A"]), _horas_publicadas(["1A"]).assign(nom_unidadegeradora="UG SEM ROTULO")])
    with caplog.at_level(logging.WARNING):
        tratar_horas_estado(bruto)
    assert any("1 linhas sem o rótulo da unidade geradora" in r.getMessage() for r in caplog.records)


def test_unidade_com_o_mesmo_tipo_em_todas_as_tabelas_gravadas(tmp_path) -> None:
    """Itaipu tem 1 a 18, '9A' e 'G18A'. A tabela só com algarismos passa a texto, como as outras, ao ser lida de
    volta, para a junção por mês e unidade."""
    mensal = tratar_indicadores_ug(_indicadores_publicados([("PRIT600", r, "700") for r in ("10", "9A", "2", "G18A")]),
                                   anual=False)
    horas = tratar_horas_estado(_horas_publicadas(["10", "2"]))
    assert list(mensal["ug"]) == ["2", "9A", "10", "G18A"] and str(horas["ug"].dtype) == "Int64"
    exportar_indicadores(IndicadoresONS(ug_mensal=mensal, ug_anual=pd.DataFrame(), horas_estado=horas,
                                        taxas=pd.DataFrame()), tmp_path)
    lido = carregar_indicadores_tratados(tmp_path)
    assert list(lido.ug_mensal["ug"]) == ["2", "9A", "10", "G18A"]
    assert list(lido.horas_estado["ug"]) == ["2", "10"]
    assert len(lido.horas_estado.merge(lido.ug_mensal, on=["mes", "ug"])) == 2


def test_horas_estado_usa_a_versao_mais_recente() -> None:
    bruto = pd.DataFrame({
        "nom_unidadegeradora": ["UG   24 MW SAO DOMINGOS              1 MS"] * 4,
        "dat_periodo": ["03/2026"] * 4,
        "nom_tpinsumo": ["HP", "HS", "HDF", "HDF"],
        "val_parametro": ["744.0", "740.0", "9.0", "4.0"],
        "num_versao": ["1.0", "1.0", "1.0", "2.0"],
    })
    horas = tratar_horas_estado(bruto)
    linha = horas.iloc[0]
    assert linha["mes"] == pd.Timestamp("2026-03-01") and linha["ug"] == 1
    assert linha["HDF"] == 4.0 and linha["num_versao"] == 2.0
    assert linha["residuo_identidade_h"] == pytest.approx(0.0)


def test_taxas_usam_a_versao_mais_recente() -> None:
    bruto = pd.DataFrame({
        "din_mes": ["2026-08-01"] * 3,
        "nom_taxa": ["TEIFa", "TEIFa", "TEIP"],
        "val_taxa": ["0.05", "0.041", "0.048"],
        "num_versao": ["1.0", "2.0", "1.0"],
        "din_calculo": ["2026-09-01 10:00:00", "2026-09-11 16:55:06", "2026-09-11 16:55:06"],
    })
    taxas = tratar_taxas(bruto)
    assert len(taxas) == 1
    assert taxas.iloc[0]["teifa"] == pytest.approx(0.041)
    assert taxas.iloc[0]["teip"] == pytest.approx(0.048)


def _taxas_publicadas(nomes: tuple, meses: list, valores: list) -> pd.DataFrame:
    linhas = [{"din_mes": mes, "nom_taxa": nome, "val_taxa": valor, "num_versao": "1.0",
               "din_calculo": "2026-09-11 16:55:06"}
              for mes, par in zip(meses, valores) for nome, valor in zip(nomes, par)]
    return pd.DataFrame(linhas)


def test_taxas_operativas_com_sufixo_em_qualquer_caixa() -> None:
    bruto = _taxas_publicadas(("TEIFa_oper", "TEIP_Oper"), ["2026-08-01"], [("0.12", "0.59")])
    oper = tratar_taxas(bruto, sufixo="_oper")
    assert list(oper.columns) == ["mes", "teifa_oper", "teip_oper", "num_versao_oper", "din_calculo_oper"]
    assert oper.iloc[0]["teifa_oper"] == pytest.approx(0.12)
    assert oper.iloc[0]["teip_oper"] == pytest.approx(0.59)


def test_juncao_pelos_meses_das_oficiais() -> None:
    oficiais = tratar_taxas(_taxas_publicadas(("TEIFa", "TEIP"), ["2026-07-01", "2026-08-01"],
                                              [("0.30", "0.70"), ("0.31", "0.71")]))
    oper = tratar_taxas(_taxas_publicadas(("TEIFa_oper", "TEIP_oper"), ["2026-07-01", "2026-06-01"],
                                          [("0.13", "0.59"), ("0.12", "0.58")]), sufixo="_oper")
    juntas = juntar_taxas_operativas(oficiais, oper)
    assert list(juntas["mes"]) == [pd.Timestamp("2026-07-01"), pd.Timestamp("2026-08-01")]
    assert juntas.iloc[0]["teifa_oper"] == pytest.approx(0.13)
    assert pd.isna(juntas.iloc[1]["teifa_oper"])  # mês da oficial sem a operativa


def test_sem_operativas_a_tabela_fica_como_a_das_oficiais() -> None:
    oficiais = tratar_taxas(_taxas_publicadas(("TEIFa", "TEIP"), ["2026-08-01"], [("0.04", "0.05")]))
    juntas = juntar_taxas_operativas(oficiais, tratar_taxas(pd.DataFrame(), sufixo="_oper"))
    assert list(juntas.columns) == ["mes", "teifa", "teip", "num_versao", "din_calculo"]


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
    mensal["dispf"] = 100 - mensal["indisppf"] - mensal["indispff"]
    mensal["potencia_mw"] = 24.0
    mensal = mensal.drop(columns=["HP", "HDP", "HDF"])
    anual = pd.DataFrame({"ano": [2023, 2023, 2024, 2024], "ug": [1, 2, 1, 2], "dispf": [98.6, 100, 98.6, 96.4],
                          "indisppf": [0.8, 0, 0.8, 3.6], "indispff": [0.6, 0, 0.6, 0], "dmdff": [4.0, 0, 4.0, 0]})
    w = horas.tail(120)
    teifa = (w["HDF"] + w["HEDF"]).sum() / (w["HP"] - w["HDP"] - w["HEDP"]).sum()
    teip = (w["HDP"] + w["HEDP"]).sum() / w["HP"].sum()
    taxas = pd.DataFrame({"mes": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")],
                          "teifa": [teifa, teifa], "teip": [teip, teip], "num_versao": [1.0, 1.0]})
    return IndicadoresONS(ug_mensal=mensal, ug_anual=anual, horas_estado=horas, taxas=taxas,
                          )


def test_recorte_no_periodo_da_base() -> None:
    recortado = recortar_periodo(_indicadores_sinteticos(), pd.Timestamp("2023-11-15 05:00"), pd.Timestamp("2024-01-10"))
    assert recortado.horas_estado["mes"].min() == pd.Timestamp("2023-11-01")
    assert recortado.horas_estado["mes"].max() == pd.Timestamp("2024-01-01")
    assert sorted(recortado.ug_anual["ano"].unique()) == [2023, 2024]
    assert list(recortado.taxas["mes"]) == [pd.Timestamp("2024-01-01")]
