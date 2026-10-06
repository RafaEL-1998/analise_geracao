"""Bases complementares do ONS no relatório: constatações, seções, abas, figuras e PDF (spec 006, FR-031 a FR-034)."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from src.analyzer import (
    NOMES_FIGURAS,
    analisar,
    exportar_tabelas,
    gerar_graficos,
    gerar_relatorio_md,
    notas_bases_complementares,
    preparar_dados,
)
from src.conjuntos_ons import SerieConjunto
from src.fontes_relatorio import PREFIXO_CALCULADO, PREFIXO_FONTE
from src.pdf_generator import PDFReportGenerator, nota_identificacao_cadastro, pares_identificacao_cadastro


def _serie_disponibilidade(df: pd.DataFrame) -> SerieConjunto:
    """Disponibilidade sintética: operacional = declarada; sincronizada zero com a usina parada."""
    horaria = pd.DataFrame({
        "din_instante": df["din_instante"],
        "val_potenciainstalada": 48.0,
        "val_dispoperacional": df["val_disponibilidade"],
        "val_dispsincronizada": (df["val_geracao"] > 1).map({True: 24.0, False: 0.0}),
        "qualidade": "OK",
        "arquivo_origem": "DISPONIBILIDADE_USINA_2024_01.csv",
    })
    horaria.loc[horaria.index[:3], "val_dispoperacional"] += 2.0  # 3 horas divergentes
    auditoria = pd.DataFrame({"arquivo": ["DISPONIBILIDADE_USINA_2024_01.csv"], "status": ["PROCESSADO"]})
    ausencias = pd.DataFrame(columns=["tipo", "inicio", "fim", "horas"])
    return SerieConjunto(horaria=horaria, ausencias=ausencias, auditoria=auditoria)


@pytest.fixture
def df_base(df_sintetico: pd.DataFrame) -> pd.DataFrame:
    return preparar_dados(df_sintetico)


def test_sem_bases_novas_o_relatorio_nao_muda(df_base: pd.DataFrame, tmp_path: Path) -> None:
    res = analisar(df_base)
    assert not res.disponibilidade and not res.hidrologia and not res.geracao_oficial and not res.cadastro
    assert "Disponibilidade sincronizada" not in dict(res.achados)
    figuras = gerar_graficos(df_base, res, tmp_path / "figuras", dpi=50)
    assert set(figuras) == set(NOMES_FIGURAS)


def test_disponibilidade_no_relatorio(df_base: pd.DataFrame, tmp_path: Path) -> None:
    res = analisar(df_base, disponibilidade=_serie_disponibilidade(df_base))
    d = res.disponibilidade
    assert d["conferencia"]["divergentes"] == 3 and d["conferencia"]["horas_comuns"] == len(df_base)
    paradas = d["horas_paradas"]
    assert d["classes"]["horas"].sum() == len(paradas) == d["resumo"]["horas_paradas"]
    texto = dict(res.achados)["Disponibilidade sincronizada"]
    assert "coincide com a disponibilidade declarada" in texto and "não o motivo da parada" in texto
    assert (res.parametros["valor"].str.contains("Disponibilidade por usina (ONS)", regex=False)).any()

    figuras = gerar_graficos(df_base, res, tmp_path / "figuras", dpi=50)
    assert figuras["disponibilidade_sincronizada"].exists()
    md = gerar_relatorio_md(res, figuras, tmp_path / "relatorio.md").read_text(encoding="utf-8")
    assert "Disponibilidade operacional e sincronizada (ONS)" in md
    assert texto in md
    xlsx, _ = exportar_tabelas(res, tmp_path / "tabelas.xlsx", tmp_path / "tabelas.csv")
    abas = pd.ExcelFile(xlsx).sheet_names
    assert {"DISP_CONFERENCIA", "DISP_DIVERGENCIAS", "DISP_HORAS_PARADAS", "DISP_MENSAL", "DISP_ANUAL"} <= set(abas)
    pdf = PDFReportGenerator(res, figuras, tmp_path / "relatorio.pdf").build_pdf()
    assert Path(pdf).exists() and Path(pdf).stat().st_size > 10000


def _hidrologia(df: pd.DataFrame, confirmado: bool = True):
    """Série hidrológica sintética (hora de início) coerente com a base de EVT e o alinhamento."""
    horaria = pd.DataFrame({
        "din_instante": df["din_instante"], "din_instante_publicado": df["din_instante"] + pd.Timedelta(hours=1),
        "val_vazaoafluente": df["val_vazaoturbinada"] + df["val_vazaovertida"],
        "val_vazaodefluente": df["val_vazaoturbinada"] + df["val_vazaovertida"],
        "val_vazaoturbinada": df["val_vazaoturbinada"], "val_vazaovertida": df["val_vazaovertida"],
        "val_vazaovertidanaoturbinavel": df["val_vazaovertidanaoturbinavel"], "val_vazaooutrasestruturas": None,
        "val_nivelmontante": 344.3, "val_niveljusante": 309.5, "val_volumeutil": 50.0, "qualidade": "OK",
        "arquivo_origem": "DADOS_HIDROLOGICOS_HO_2024_01.parquet",
    })
    serie = SerieConjunto(horaria=horaria, ausencias=pd.DataFrame(columns=["tipo", "inicio", "fim", "horas"]),
                          auditoria=pd.DataFrame({"arquivo": ["DADOS_HIDROLOGICOS_HO_2024_01.parquet"], "status": ["PROCESSADO"]}))
    alinhamento = pd.DataFrame([{"horas_comuns": len(df), "coincidentes_turbinada": len(df), "coincidentes_vertida": len(df),
                                 "coincidentes_ambas": len(df) if confirmado else 0,
                                 "pct_coincidencia": 100.0 if confirmado else 50.0, "meta_pct": 99.0,
                                 "tolerancia_m3s": 0.5, "deslocamento_aplicado_h": -1, "confirmado": confirmado}])
    return serie, alinhamento


def test_hidrologia_no_relatorio(df_base: pd.DataFrame, tmp_path: Path) -> None:
    res = analisar(df_base, hidrologia=_hidrologia(df_base))
    h = res.hidrologia
    assert h["publicado"] and h["resumo"]["horas_evt"] == int((df_base["val_energiavertidaturbinavel"] > 0).sum())
    assert sum(h["resumo"]["horas_por_faixa"].values()) == h["resumo"]["horas_evt"]
    assert "cabia nas turbinas" in dict(res.achados)["Afluência e vertimento"]
    # FR-031 (T062): a constatação que fala dos dias com parada traz a ressalva de que os dados não dão o motivo
    assert "mas não o motivo das paradas, que depende de informação do agente" in dict(res.achados)["Afluência e vertimento"]
    figuras = gerar_graficos(df_base, res, tmp_path / "figuras", dpi=50)
    assert figuras["faixas_afluencia"].exists() and figuras["perfil_hidrologico"].exists()
    md = gerar_relatorio_md(res, figuras, tmp_path / "relatorio.md").read_text(encoding="utf-8")
    assert "Afluência, vertimento e nível do reservatório (ONS)" in md and "não são consistidos pelo ONS" in md
    # FR-026 (T057): as legendas descrevem a exclusão campo a campo, não a da hora inteira
    assert "horas sem sinalização" not in md and "saem só do campo afetado" in md
    xlsx, _ = exportar_tabelas(res, tmp_path / "tabelas.xlsx", tmp_path / "tabelas.csv")
    assert {"HID_ALINHAMENTO", "HID_FAIXAS_AFLUENCIA", "HID_FAIXAS_ANUAL", "HID_MENSAL",
            "HID_PERFIL_HORA_DO_DIA"} <= set(pd.ExcelFile(xlsx).sheet_names)
    # FR-023 (T055): horas e EVT por faixa também por ano; em cada ano, a EVT das faixas soma a EVT das horas com EVT
    assert "### EVT por faixa de afluência (MWh)" in md
    anual = pd.read_excel(xlsx, sheet_name="HID_FAIXAS_ANUAL")
    com_evt = df_base[df_base["val_energiavertidaturbinavel"] > 0]
    esperado = com_evt.groupby(com_evt["din_instante"].dt.year)["val_energiavertidaturbinavel"].sum()
    obtido = anual.groupby("periodo")["evt_mwh"].sum()
    assert obtido.index.tolist() == esperado.index.tolist()
    assert obtido.to_numpy() == pytest.approx(esperado.to_numpy())
    assert Path(PDFReportGenerator(res, figuras, tmp_path / "relatorio.pdf").build_pdf()).exists()


def test_hidrologia_sem_alinhamento_nao_publica_cruzamentos(df_base: pd.DataFrame, tmp_path: Path) -> None:
    res = analisar(df_base, hidrologia=_hidrologia(df_base, confirmado=False))
    assert res.hidrologia and not res.hidrologia["publicado"] and "faixas" not in res.hidrologia
    assert "não foram cruzados com a base de EVT" in dict(res.achados)["Afluência e vertimento"]
    assert "motivo das paradas" not in dict(res.achados)["Afluência e vertimento"]  # sem cruzamento, sem paradas no texto
    figuras = gerar_graficos(df_base, res, tmp_path / "figuras", dpi=50)
    assert "faixas_afluencia" not in figuras and "perfil_hidrologico" not in figuras


def _geracao(df: pd.DataFrame, divergente: bool = False) -> SerieConjunto:
    horaria = pd.DataFrame({"din_instante": df["din_instante"], "val_geracao": df["val_geracao"], "qualidade": "OK",
                            "arquivo_origem": "GERACAO_USINA-2_2024_01.parquet"})
    if divergente:
        horaria.loc[horaria.index[10], "val_geracao"] += 5.0
    return SerieConjunto(horaria=horaria, ausencias=pd.DataFrame(columns=["tipo", "inicio", "fim", "horas"]),
                         auditoria=pd.DataFrame({"arquivo": ["GERACAO_USINA-2_2024_01.parquet"], "status": ["PROCESSADO"]}))


def _ficha(potencia: float = 48.0) -> pd.DataFrame:
    divergencias = "" if potencia == 48.0 else f"potência autorizada de {potencia} MW (projeto: 48 MW)"
    return pd.DataFrame([{"nom_usina": "UHE SÃO DOMINGOS", "ceg": "UHE.PH.MS.028761-0.01", "id_ons": "MSUHSD",
                          "nom_modalidadeoperacao": "TIPO II-A", "sgl_centrooperacao": "COSR-S",
                          "nom_pontoconexao": "SE ÁGUA CLARA 138 KV", "val_potenciaautorizada": potencia, "id_estado": "MS",
                          "sts_aneel": "A", "data_consulta_utc": "2026-10-05 13:00:00", "arquivo_origem": "MODALIDADE_USINA.csv",
                          "homonimos": 20, "linhas_so_identificador": 0, "linhas_so_conferencia": 0,
                          "divergencias": divergencias}])


def test_geracao_e_cadastro_sem_divergencia_nao_geram_constatacao(df_base: pd.DataFrame, tmp_path: Path) -> None:
    auditoria = pd.DataFrame([{"arquivo": "MODALIDADE_USINA.csv", "formato": "CSV", "linhas_lidas": 6018,
                               "linhas_formato_irregular": 0, "linhas_usina": 1, "linhas_so_identificador": 0,
                               "linhas_so_conferencia": 0, "status": "PROCESSADO", "mensagem": ""}])
    res = analisar(df_base, geracao=_geracao(df_base), cadastro=_ficha(), auditoria_cadastro=auditoria)
    titulos = dict(res.achados)
    assert "Conferência da geração" not in titulos and "Cadastro da usina no ONS" not in titulos
    md = gerar_relatorio_md(res, None, tmp_path / "relatorio.md").read_text(encoding="utf-8")
    assert "Identificação da usina no cadastro do ONS" in md and "TIPO II-A" in md
    assert "Conferência da geração com a série oficial (ONS)" in md and "coincide com a série oficial" in md
    xlsx, _ = exportar_tabelas(res, tmp_path / "tabelas.xlsx", tmp_path / "tabelas.csv")
    assert {"GER_CONFERENCIA", "GER_MENSAL", "GER_ANUAL", "CAD_FICHA", "CAD_AUDITORIA"} <= set(pd.ExcelFile(xlsx).sheet_names)
    assert Path(PDFReportGenerator(res, {}, tmp_path / "relatorio.pdf").build_pdf()).exists()


def test_geracao_e_cadastro_com_divergencia_geram_constatacao(df_base: pd.DataFrame) -> None:
    res = analisar(df_base, geracao=_geracao(df_base, divergente=True), cadastro=_ficha(potencia=47.5))
    titulos = dict(res.achados)
    assert "difere da série oficial" in titulos["Conferência da geração"]
    assert "potência autorizada de 47.5 MW" in titulos["Cadastro da usina no ONS"]
    assert res.geracao_oficial["conferencia"]["divergentes"] == 1


def test_relacao_de_fontes_inclui_as_bases_novas(df_base: pd.DataFrame, tmp_path: Path) -> None:
    """FR-034 (T056): a relação de fontes do Markdown traz cada base carregada, com link, período e obtenção."""
    assert notas_bases_complementares(analisar(df_base)) == []
    res = analisar(df_base, disponibilidade=_serie_disponibilidade(df_base), hidrologia=_hidrologia(df_base),
                   geracao=_geracao(df_base), cadastro=_ficha())
    md = gerar_relatorio_md(res, None, tmp_path / "relatorio.md").read_text(encoding="utf-8")
    notas = re.split(r"^## \d+\. Notas metodológicas e limitações$", md, flags=re.M)[1]
    for conjunto in ("disponibilidade_usina", "dados_hidrologicos_ho", "geracao-usina-2", "modalidade-usina"):
        assert f"https://dados.ons.org.br/dataset/{conjunto}" in notas
    inicio = df_base["din_instante"].min().strftime("%d/%m/%Y")
    assert notas.count(f"de {inicio} a ") == 3
    assert "cadastro sem série histórica, obtido em 05/10/2026" in notas and "não consistidos pelo ONS" in notas


def test_identificacao_do_cadastro_no_pdf(df_base: pd.DataFrame) -> None:
    """US6/AC4 (T058): data da consulta na tabela do PDF e ressalva da fonte mantida quando há divergência."""
    res = analisar(df_base, cadastro=_ficha())
    assert ("Data da consulta", "05/10/2026 13:00 UTC") in pares_identificacao_cadastro(res)
    assert nota_identificacao_cadastro(res) == "Cadastro sem série histórica; as versões anteriores do arquivo ficam preservadas."
    nota = nota_identificacao_cadastro(analisar(df_base, cadastro=_ficha(potencia=47.5)))
    assert "potência autorizada de 47.5 MW" in nota and "Cadastro sem série histórica" in nota


def _sem_legenda(md: str) -> list:
    """Tabelas e figuras do Markdown sem a linha de fonte logo abaixo (antes da próxima tabela ou título)."""
    linhas = md.splitlines()
    faltando = []
    for i, linha in enumerate(linhas):
        tabela = linha.startswith("| ---")
        figura = linha.startswith("![")
        if not (tabela or figura):
            continue
        j = i + 1
        while tabela and j < len(linhas) and linhas[j].startswith("|"):
            j += 1
        achou = False
        while j < len(linhas) and not linhas[j].startswith(("#", "|", "![")):
            if linhas[j].strip().startswith((PREFIXO_FONTE, PREFIXO_CALCULADO)):
                achou = True
                break
            j += 1
        if not achou:
            faltando.append(linhas[i - 1] if tabela else linha)
    return faltando


@pytest.mark.parametrize("com_bases", [False, True])
def test_toda_tabela_e_figura_do_markdown_tem_fonte(df_base: pd.DataFrame, tmp_path: Path, com_bases: bool) -> None:
    """Spec 007 (FR-001, SC-001): legenda de fonte em toda tabela e figura do Markdown."""
    bases = dict(disponibilidade=_serie_disponibilidade(df_base), hidrologia=_hidrologia(df_base),
                 geracao=_geracao(df_base), cadastro=_ficha()) if com_bases else {}
    res = analisar(df_base, **bases)
    figuras = gerar_graficos(df_base, res, tmp_path / "figuras", dpi=40)
    md = gerar_relatorio_md(res, figuras, tmp_path / "relatorio.md").read_text(encoding="utf-8")
    assert md.count("| ---") > 5 and _sem_legenda(md) == []


@pytest.mark.parametrize("confirmado", [True, False])
def test_pdf_com_bases_novas_tem_legenda_em_tudo(df_base: pd.DataFrame, tmp_path: Path, confirmado: bool) -> None:
    """Spec 007 (FR-001): contagem de legendas igual à de tabelas, blocos e figuras, inclusive sem alinhamento."""
    res = analisar(df_base, disponibilidade=_serie_disponibilidade(df_base),
                   hidrologia=_hidrologia(df_base, confirmado=confirmado), geracao=_geracao(df_base), cadastro=_ficha())
    figuras = gerar_graficos(df_base, res, tmp_path / "figuras", dpi=40)
    gerador = PDFReportGenerator(res, figuras, tmp_path / "relatorio.pdf")
    gerador.build_pdf()
    assert gerador._desenhados > 0 and gerador._legendas == gerador._desenhados


def test_cabecalho_do_markdown_sem_linha_de_fontes(df_base: pd.DataFrame, tmp_path: Path) -> None:
    """Spec 008 (FR-010): sem a linha "**Fontes**:"; data de geração no cabeçalho."""
    md = gerar_relatorio_md(analisar(df_base), None, tmp_path / "so_evt.md").read_text(encoding="utf-8")
    assert "**Fontes**:" not in md and "**Gerado em**:" in md


@pytest.mark.parametrize("com_bases", [False, True])
def test_aba_fontes_cobre_todas_as_abas(df_base: pd.DataFrame, tmp_path: Path, com_bases: bool) -> None:
    """Spec 007 (FR-011): aba FONTES por último, uma linha para cada outra aba, nenhuma sem origem."""
    bases = dict(disponibilidade=_serie_disponibilidade(df_base), hidrologia=_hidrologia(df_base),
                 geracao=_geracao(df_base), cadastro=_ficha()) if com_bases else {}
    res = analisar(df_base, **bases)
    xlsx, _ = exportar_tabelas(res, tmp_path / "tabelas.xlsx", tmp_path / "tabelas.csv")
    abas = pd.ExcelFile(xlsx).sheet_names
    assert abas[-1] == "FONTES"
    fontes = pd.read_excel(xlsx, sheet_name="FONTES")
    assert list(fontes.columns) == ["aba", "conjuntos_origem", "conferencias", "sem_outra_fonte", "calculado_no_relatorio"]
    assert fontes["aba"].tolist() == abas[:-1]
    assert not fontes["conjuntos_origem"].str.contains("origem não mapeada").any()
    assert set(fontes["calculado_no_relatorio"]) <= {"sim", "não"}


def test_notas_das_bases_novas_sem_a_parte_de_fonte(df_base: pd.DataFrame, tmp_path: Path) -> None:
    """Spec 008 (FR-013): sai "Fonte: conjunto … obtido em …"; as ressalvas ficam."""
    from src.analyzer import notas_disponibilidade, notas_hidrologia

    res = analisar(df_base, disponibilidade=_serie_disponibilidade(df_base), hidrologia=_hidrologia(df_base),
                   geracao=_geracao(df_base), cadastro=_ficha())
    assert notas_disponibilidade(res)[0].startswith("A disponibilidade operacional é a mesma informação")
    assert notas_hidrologia(res)[0].startswith("Os dados são informados pelos agentes e não são consistidos pelo ONS")
    md = gerar_relatorio_md(res, None, tmp_path / "relatorio.md").read_text(encoding="utf-8")
    secoes = re.split(r"^## \d+\. Notas metodológicas e limitações$", md, flags=re.M)[0]
    assert "Fonte: conjunto" not in secoes
    assert "Cadastro sem série histórica; as versões anteriores do arquivo ficam preservadas." in secoes
