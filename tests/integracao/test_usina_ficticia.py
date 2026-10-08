"""Usina fictícia de ponta a ponta: as cinco etapas com --sem-portal, só com o perfil e arquivos brutos sintéticos
(constituição, princípio III; spec da Geração do relatório, US7: outra usina analisada preenchendo só o perfil)."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pandas as pd
import pytest

from src.__main__ import main
from src.comum import caminhos
from src.comum import perfil as modulo_perfil
from src.relatorio import pdf as modulo_pdf
from tests.fixtures.brutos_ficticios import NOME, gerar_brutos

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "usina_ficticia" / "perfil.toml"
PROIBIDOS = ("São Domingos", "SAO DOMINGOS", "MSUHSD", "PRUHSD", "PNUHSD", "028761")


@pytest.fixture(scope="module")
def execucao(tmp_path_factory):
    """Executa o fluxo completo uma vez para a usina fictícia e devolve as pastas e os textos do PDF."""
    raiz = tmp_path_factory.mktemp("projeto")
    (raiz / "usinas" / "usina_ficticia").mkdir(parents=True)
    shutil.copy(FIXTURE, raiz / "usinas" / "usina_ficticia" / "perfil.toml")
    gerar_brutos(raiz / "data" / "raw")
    textos_pdf = []

    class _Paragrafo(modulo_pdf.Paragraph):
        def __init__(self, texto, *args, **kwargs):
            textos_pdf.append(str(texto))
            super().__init__(texto, *args, **kwargs)

    mp = pytest.MonkeyPatch()
    mp.setattr(caminhos, "DATA_DIR", raiz / "data")
    mp.setattr(caminhos, "RAW_DATA_DIR", raiz / "data" / "raw")
    mp.setattr(caminhos, "REPORTS_DIR", raiz / "reports")
    mp.setattr(modulo_perfil, "RAIZ_PROJETO", raiz)
    mp.setattr(modulo_pdf, "Paragraph", _Paragrafo)
    try:
        codigo = main(["completo", "--usina", "usina_ficticia", "--sem-portal", "--data-geracao", "08/10/2026 10:00"])
    finally:
        mp.undo()
    return {"codigo": codigo, "raiz": raiz, "textos_pdf": textos_pdf,
            "dados": raiz / "data" / "usinas" / "usina_ficticia", "relatorio": raiz / "reports" / "usina_ficticia"}


def test_cinco_etapas_concluidas_e_relatorio_completo(execucao) -> None:
    assert execucao["codigo"] == 0
    for etapa in ("coleta", "tratamento", "conferencia", "analises"):
        manifesto = json.loads((execucao["dados"] / etapa / "etapa.json").read_text(encoding="utf-8"))
        assert (manifesto["status"], manifesto["codigo_saida"]) == ("concluida", 0), etapa
    relatorio = execucao["relatorio"]
    manifesto = json.loads((relatorio / "etapa.json").read_text(encoding="utf-8"))
    assert manifesto["status"] == "concluida" and manifesto["resumo"]["figuras"] == 8
    for nome in ("relatorio_analise_estatistica.pdf", "relatorio_analise_estatistica.md",
                 "perfil_estatistico_anual.xlsx", "perfil_estatistico_anual.csv"):
        assert (relatorio / nome).stat().st_size > 1000, nome
    assert (relatorio / "relatorio_analise_estatistica.pdf").read_bytes()[:5] == b"%PDF-"


def test_relatorio_sem_mencao_a_sao_domingos(execucao) -> None:
    md = (execucao["relatorio"] / "relatorio_analise_estatistica.md").read_text(encoding="utf-8")
    pdf = (execucao["relatorio"] / "relatorio_analise_estatistica.pdf").read_bytes()
    assert md.startswith("# UHE Fictícia — ") and execucao["textos_pdf"]
    for literal in PROIBIDOS:
        assert literal not in md, literal
        assert not any(literal in t for t in execucao["textos_pdf"]), literal
        assert literal.encode("utf-8") not in pdf and literal.encode("latin-1", "ignore") not in pdf, literal


def test_faixas_de_afluencia_com_tres_unidades(execucao) -> None:
    md = (execucao["relatorio"] / "relatorio_analise_estatistica.md").read_text(encoding="utf-8")
    assert "entre uma e três unidades" in md
    assert "duas unidades" not in md and "nas duas" not in md
    faixas = pd.read_excel(execucao["relatorio"] / "perfil_estatistico_anual.xlsx", sheet_name="HID_FAIXAS_AFLUENCIA")
    assert "ENTRE_UMA_E_TRES_UNIDADES" in set(faixas["faixa_afluencia"])


def test_homonimo_fora_dos_extraidos_e_contado_na_auditoria(execucao) -> None:
    coleta = execucao["dados"] / "coleta"
    evt = pd.read_csv(coleta / "evt_extraido.csv", sep=";")
    assert len(evt) == 1440 and set(evt["nom_reservatorio"]) == {NOME} and set(evt["cod_usina"]) == {999}
    auditoria = pd.read_csv(coleta / "auditoria_evt.csv", sep=";")
    assert auditoria["registros_codigo_sem_nome"].sum() == 2  # um homônimo em cada arquivo mensal
    for conjunto in ("disponibilidade", "hidrologia", "geracao"):
        aud = pd.read_csv(coleta / f"auditoria_{conjunto}.csv", sep=";")
        assert aud["linhas_so_identificador"].tolist() == [1, 1], conjunto
    indicadores = pd.read_csv(coleta / "auditoria_indicadores.csv", sep=";")
    mensal = indicadores[indicadores["conjunto"] == "ind_disponibilidade_fgeracao_uge_mensal"]
    assert mensal["linhas_so_identificador"].tolist() == [1]
    ficha = pd.read_csv(coleta / "cadastro_ficha.csv", sep=";")
    assert ficha.loc[0, "homonimos"] == 1 and ficha.loc[0, "id_ons"] == "GOUHFI"


def test_secao_de_programacao_ausente(execucao) -> None:
    md = (execucao["relatorio"] / "relatorio_analise_estatistica.md").read_text(encoding="utf-8")
    secoes = re.findall(r"^## \d+\. (.+)$", md, flags=re.M)
    assert secoes and not any("rogramação" in s for s in secoes)
    assert len(secoes) == 16


def test_dados_das_etapas_sem_mencao_a_sao_domingos(execucao) -> None:
    """Os arquivos de texto das quatro primeiras etapas também só trazem a usina do perfil."""
    textos = [p for p in execucao["dados"].rglob("*") if p.suffix in (".csv", ".md", ".json")]
    assert textos
    for arquivo in textos:
        conteudo = arquivo.read_text(encoding="utf-8")
        for literal in PROIBIDOS:
            assert literal not in conteudo, (arquivo.name, literal)
