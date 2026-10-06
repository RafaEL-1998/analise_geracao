"""Testes dos indicadores oficiais do ONS por unidade geradora e da sua integração ao relatório."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.analyzer import analisar, gerar_relatorio_md, linhas_tabela_ons_disponibilidade, preparar_dados
from src.config import CEG_USINA
from src.indicadores_ons import (
    PARAMETROS,
    IndicadoresONS,
    ano_do_recurso,
    carregar_indicadores_processados,
    comparar_indicadores_e_horas,
    decompor_taxas,
    executar_indicadores_ons,
    filtrar_csv,
    numero_ug,
    recalcular_taxas,
    recortar_periodo,
    selecionar_recursos,
    tratar_horas_estado,
    tratar_taxas,
)
from src.models import RecursoONS
from src.pdf_generator import PDFReportGenerator

OUTRO_CEG = "UHE.PH.RS.000012-4.01"


def _recurso(nome_arquivo: str) -> RecursoONS:
    return RecursoONS("id", nome_arquivo, f"https://ons/dataset/x/{nome_arquivo}", "CSV")


def test_selecao_de_arquivos_por_ano() -> None:
    recursos = [_recurso(f"IND_MENSAL_{ano}.csv") for ano in (2017, 2018, 2026)] + [_recurso("TAXA_TEIF_TEIP.csv")]
    assert [ano_do_recurso(r) for r in recursos] == [2017, 2018, 2026, None]
    nomes = [r.nome_recurso for r in selecionar_recursos(recursos, 2018, 2026)]
    assert nomes == ["IND_MENSAL_2018.csv", "IND_MENSAL_2026.csv", "TAXA_TEIF_TEIP.csv"]


def test_numero_da_unidade_no_nome() -> None:
    assert numero_ug("UG   24 MW SAO DOMINGOS              2 MS") == 2
    assert numero_ug("UG 10P3 MW CURUA-UNA                 3 PA   ") == 3


def test_filtro_por_ceg_remove_espacos(tmp_path: Path) -> None:
    arquivo = tmp_path / "TAXA_TEIF_TEIP_PARAM_2026.csv"
    arquivo.write_text(
        "nom_usina;id_tipousina;nom_unidadegeradora;cod_ceg;dat_periodo;din_parametro;nom_tpinsumo;val_parametro;num_versao\n"
        f"14 DE JULHO;Hidroelétrica   ;UG   50 MW 14 DE JULHO   1 RS;{OUTRO_CEG};01/2026;2026-01-01;HDF;0.0;1.0\n"
        f"SAO DOMINGOS;Hidroelétrica   ;UG   24 MW SAO DOMINGOS   1 MS;{CEG_USINA};01/2026;2026-01-01;HDF;4.7;1.0\n",
        encoding="utf-8",
    )
    linhas, auditoria = filtrar_csv(arquivo, PARAMETROS)
    assert len(linhas) == 1
    assert linhas.iloc[0]["id_tipousina"] == "Hidroelétrica"
    assert auditoria == {"conjunto": PARAMETROS, "arquivo": arquivo.name, "linhas_lidas": 2, "linhas_usina": 1,
                         "status": "PROCESSADO"}


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


def test_execucao_completa_em_pastas_temporarias(tmp_path: Path) -> None:
    """Sem rede: lê os CSVs da pasta informada e grava só na pasta de saída informada."""
    raw = tmp_path / "raw"
    saida = tmp_path / "processed"
    saida.mkdir()
    ug = "UG   24 MW SAO DOMINGOS              1 MS"
    arquivos = {
        "ind_disponibilidade_fgeracao_uge_mensal/IND_MENSAL_2026.csv": (
            "id_subsistema;nom_subsistema;id_estado;nom_estado;nom_modalidadeoperacao;nom_agenteproprietario;"
            "id_tipousina;id_usina;nom_usina;ceg;cod_equipamento;num_unidadegeradora;nom_unidadegeradora;val_potencia;"
            "dat_mesreferencia;val_dispf;val_indisppf;val_indispff;val_dmdff;val_fdff;val_tdff\n"
            f"SE ;Sudeste;MS;MS;Tipo II-A;AXIA SUL;UHE;MSUHSD;São Domingos;{CEG_USINA};MSUHSD0UG1   ;1   ;{ug};24.0;"
            "2026-08-01;98.0;2.0;0.0;0.0;0.0;0.0\n"
            f"SE ;Sudeste;MS;MS;Tipo II-A;AXIA SUL;UHE;MSUHSD;São Domingos;{CEG_USINA};MSUHSD0UG1   ;1   ;{ug};24.0;"
            "2026-05-01;100.0;0.0;0.0;0.0;0.0;0.0\n"
        ),
        "ind_disponibilidade_fgeracao_uge_anual/IND_ANUAL.csv": (
            "id_subsistema;nom_subsistema;estad_id;nom_estado;nom_modalidadeoperacao;nom_agenteproprietario;"
            "id_tipousina;id_usina;nom_usina;ceg;cod_equipamento;num_unidadegeradora;nom_unidadegeradora;val_potencia;"
            "din_ano;val_dispf;val_indisppf;val_indispff;val_dmdff;val_fdff;val_tdff\n"
            f"SE;Sudeste;MS;MS;Tipo II-A;AXIA SUL;UHE;MSUHSD;São Domingos;{CEG_USINA};MSUHSD0UG1 ;1 ;{ug};24.0;"
            "2026;99.0;1.0;0.0;0.0;0.0;0.0\n"
        ),
        "taxa_teif_teip_parametro/TAXA_TEIF_TEIP_PARAM_2026.csv": (
            "nom_usina;id_tipousina;nom_unidadegeradora;cod_ceg;dat_periodo;din_parametro;nom_tpinsumo;val_parametro;num_versao\n"
            + "".join(
                f"SAO DOMINGOS;Hidroelétrica   ;{ug};{CEG_USINA};08/2026;2026-08-01;{s};{v};1.0\n"
                for s, v in [("HP", 744), ("HS", 729.12), ("HRD", 0), ("HDP", 14.88), ("HDF", 0), ("HDCE", 0),
                             ("HEDP", 0), ("HEDF", 0)]
            )
        ),
        "taxa_teif_teip/TAXA_TEIF_TEIP.csv": (
            "nom_usina;cod_ceg;tip_usina;din_mes;nom_taxa;val_taxa;num_versao;din_calculo\n"
            f"SAO DOMINGOS;{CEG_USINA};Hidroelétrica   ;2026-08-01;TEIFa;0.04;1.0;2026-09-11 16:55:06.803\n"
            f"SAO DOMINGOS;{CEG_USINA};Hidroelétrica   ;2026-08-01;TEIP;0.05;1.0;2026-09-11 16:55:06.803\n"
        ),
    }
    for nome, conteudo in arquivos.items():
        caminho = raw / nome
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(conteudo, encoding="utf-8")

    codigo = executar_indicadores_ons(
        baixar=False, periodo=(pd.Timestamp("2026-08-28"), pd.Timestamp("2026-09-28 23:00")),
        pasta_raw=raw, pasta_saida=saida,
    )
    assert codigo == 0
    ind = carregar_indicadores_processados(saida)
    assert list(ind.ug_mensal["mes"]) == [pd.Timestamp("2026-08-01")]  # maio/2026 fica fora do período
    assert ind.horas_estado.loc[0, "HDP"] == pytest.approx(14.88)
    assert ind.divergencias.empty  # 2% de 744 h = 14,88 h, igual ao HDP
    assert ind.taxas.loc[0, "teifa"] == pytest.approx(0.04)
    assert (saida / "uhe_sao_domingos_indicadores_ons.xlsx").exists()


# ---------------------------------------------------------------------------
# Indicadores sintéticos coerentes entre si (60 meses de horas, 4 meses de DISPF)
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
                          divergencias=comparar_indicadores_e_horas(mensal, horas))


def test_recalculo_e_decomposicao_das_taxas() -> None:
    ind = _indicadores_sinteticos()
    recalculo = recalcular_taxas(ind.horas_estado, ind.taxas).set_index("mes")
    # jan/2024 não tem 60 meses de horas; fev/2024 tem
    assert pd.isna(recalculo.loc["2024-01-01", "teifa_recalculada"])
    assert recalculo.loc["2024-02-01", "diferenca_teifa_pp"] == pytest.approx(0.0, abs=1e-9)
    assert recalculo.loc["2024-02-01", "diferenca_teip_pp"] == pytest.approx(0.0, abs=1e-9)

    dec = decompor_taxas(ind.horas_estado, pd.Timestamp("2024-02-01"))
    teifa = dec[dec["taxa"] == "TEIFa"]
    assert teifa["contribuicao_pp"].sum() == pytest.approx(ind.taxas["teifa"].iloc[-1] * 100)
    assert teifa["participacao_pct"].sum() == pytest.approx(100.0)
    maior = teifa.loc[teifa["contribuicao_pp"].idxmax()]
    assert (maior["ug"], maior["parcela"]) == (2, "HEDF")


def test_divergencia_entre_dispf_e_horas() -> None:
    div = _indicadores_sinteticos().divergencias
    assert len(div) == 1
    linha = div.iloc[0]
    assert (linha["mes"], linha["ug"]) == (pd.Timestamp("2024-01-01"), 2)
    assert linha["horas_programadas_indisppf"] == pytest.approx(50.0)


def test_recorte_no_periodo_da_base() -> None:
    recortado = recortar_periodo(_indicadores_sinteticos(), pd.Timestamp("2023-11-15 05:00"), pd.Timestamp("2024-01-10"))
    assert recortado.horas_estado["mes"].min() == pd.Timestamp("2023-11-01")
    assert recortado.horas_estado["mes"].max() == pd.Timestamp("2024-01-01")
    assert sorted(recortado.ug_anual["ano"].unique()) == [2023, 2024]
    assert list(recortado.taxas["mes"]) == [pd.Timestamp("2024-01-01")]


# ---------------------------------------------------------------------------
# Integração com a análise, o Markdown e o PDF
# ---------------------------------------------------------------------------


@pytest.fixture
def resultados_com_indicadores(df_sintetico: pd.DataFrame, tmp_path: Path):
    df = preparar_dados(df_sintetico)
    return analisar(df, tmp_path / "sem_auditoria.csv", tmp_path / "sem_manifesto.json",
                    indicadores=_indicadores_sinteticos())


def test_analise_inclui_constatacoes_dos_indicadores(resultados_com_indicadores) -> None:
    res = resultados_com_indicadores
    titulos = [t for t, _ in res.achados]
    assert len(titulos) == 14
    assert titulos[2:4] == ["Indicadores oficiais de disponibilidade (ONS)", "Estados operativos das unidades geradoras (ONS)"]
    textos = dict(res.achados)
    assert "UG2" in textos["Estados operativos das unidades geradoras (ONS)"]
    assert "reserva desligada" in textos["Estados operativos das unidades geradoras (ONS)"]

    # DISPF da usina = média ponderada por horas e potência; UG1 perde 10 h/mês, UG2 perde 50 h em jan/2024
    horas_meses = {"2023-11-01": 720, "2023-12-01": 744, "2024-01-01": 744, "2024-02-01": 696}
    perdido = 10 * 4 + 50
    esperado = 100 - perdido / (2 * sum(horas_meses.values())) * 100
    assert res.ons["disp_periodo"]["dispf_pct"] == pytest.approx(esperado)
    assert res.ons["recalculo_resumo"]["meses"] == 1


def test_relatorios_com_indicadores(resultados_com_indicadores, tmp_path: Path) -> None:
    res = resultados_com_indicadores
    md = gerar_relatorio_md(res, None, tmp_path / "relatorio.md").read_text(encoding="utf-8")
    assert "## 3. Disponibilidade e geração por ano" in md
    assert "## 4. Indicadores oficiais do ONS por unidade geradora" in md
    assert "### Períodos de indisponibilidade total" in md
    _, linhas = linhas_tabela_ons_disponibilidade(res)
    for linha in linhas:
        assert f"| {' | '.join(linha)} |" in md

    saida = PDFReportGenerator(res, {}, tmp_path / "relatorio.pdf").build_pdf()
    assert saida.read_bytes()[:5] == b"%PDF-"


def test_analise_sem_indicadores_mantem_o_relatorio_anterior(df_sintetico: pd.DataFrame, tmp_path: Path) -> None:
    res = analisar(preparar_dados(df_sintetico), tmp_path / "a.csv", tmp_path / "m.json")
    assert res.ons == {}
    assert len(res.achados) == 12
    md = gerar_relatorio_md(res, None, tmp_path / "relatorio.md").read_text(encoding="utf-8")
    assert "Indicadores oficiais do ONS" not in md
    assert "## 3. Disponibilidade e geração por ano" in md
    assert "### Períodos de indisponibilidade total" in md
