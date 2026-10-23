"""Conferências do catálogo que não se aplicam à usina (plano da Conferência, D11; data-model, seções 2.12 e 3.7).

``nao_aplicaveis.csv`` registra, com o motivo, todas as conferências do catálogo que não se aplicam à usina, inclusive
na UHE. O relatório e a planilha das hidrelétricas com EVT não o leem e continuam com as seis conferências de hoje
(decisão D12); nas usinas sem EVT, ``conferencias.pkl`` traz só as conferências aplicadas.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict

import pandas as pd
import pytest

from src.comum import caminhos
from src.comum.perfil import carregar_perfil
from src.conferencia.aplicabilidade import (
    CATALOGO_CONFERENCIAS,
    COLUNAS_NAO_APLICAVEIS,
    aplicaveis,
    tabela_nao_aplicaveis,
)
from src.conferencia.resultado import ResultadoConferencia, carregar_conferencias, nao_aplicavel
from tests.fixtures.sem_evt import projeto_sem_evt

PERFIL_UHE = carregar_perfil("sao_domingos")
SEIS_DE_HOJE = ["geracao", "disponibilidade", "vazoes", "dispf_horas", "teifa_teip", "cadastro"]
NOVAS = ["geracao_fontes", "soma_conjunto", "programacao_despacho", "verificada_despacho", "programacao_renovaveis"]
# FR-026: só nas hidrelétricas; nos demais tipos, sem linha em nao_aplicaveis.csv
HIDRO = ["alinhamento_hidrologia"]


def _aplicada(id_conferencia: str) -> ResultadoConferencia:
    return ResultadoConferencia(id=id_conferencia, bases=("a", "b"), unidade="horas", comparados=1, coincidentes=1,
                                meta_atingida=True)


@pytest.fixture(scope="module")
def usinas(tmp_path_factory) -> Dict[str, Dict[str, Any]]:
    return projeto_sem_evt(tmp_path_factory.mktemp("projeto"), ["coleta", "tratamento", "conferencia"])


def _nao_aplicaveis(usina: Dict[str, Any]) -> pd.DataFrame:
    return pd.read_csv(usina["pasta"] / "conferencia" / caminhos.ARQUIVOS_CONFERENCIA["nao_aplicaveis"], sep=";",
                       dtype=str, keep_default_na=False)


def test_catalogo_com_as_seis_de_hoje_e_as_novas() -> None:
    assert [c.id for c in CATALOGO_CONFERENCIAS] == SEIS_DE_HOJE + NOVAS + HIDRO
    for c in CATALOGO_CONFERENCIAS:
        assert c.tipos and c.descricao, c.id


def test_uhe_aplica_as_seis_de_hoje_e_registra_as_novas() -> None:
    assert aplicaveis(PERFIL_UHE) == SEIS_DE_HOJE
    tabela = tabela_nao_aplicaveis(PERFIL_UHE, {i: _aplicada(i) for i in SEIS_DE_HOJE})
    assert list(tabela.columns) == COLUNAS_NAO_APLICAVEIS == ["conferencia", "motivo"]
    assert list(tabela["conferencia"]) == NOVAS + HIDRO
    motivos = dict(tabela.values.tolist())
    assert all("UHE" in motivos[i] for i in NOVAS)
    assert motivos["alinhamento_hidrologia"] == ("na hidrelétrica com EVT, a hora da hidrologia é conferida pelas vazões "
                                                 "da base de EVT")


def test_conferencia_de_hoje_sem_base_entra_com_o_motivo_do_resultado() -> None:
    resultados = {i: _aplicada(i) for i in SEIS_DE_HOJE}
    resultados["teifa_teip"] = nao_aplicavel("teifa_teip", ("a", "b"), "meses", "a usina não está nas taxas do ONS")
    tabela = tabela_nao_aplicaveis(PERFIL_UHE, resultados)
    assert list(tabela["conferencia"]) == ["teifa_teip", *NOVAS, *HIDRO]  # na ordem do catálogo
    assert tabela.iloc[0]["motivo"] == "a usina não está nas taxas do ONS"


def test_eolica_em_conjunto_sem_membros_no_perfil() -> None:
    perfil = SimpleNamespace(
        usina=SimpleNamespace(tipo="EOL", slug="eol", estado="MT"),
        identificacao=SimpleNamespace(ceg="EOL.CV.MT.000060-0.01", id_ons=None, id_conjunto="CJU_MTX", membros=()),
        cobertura={"geracao": "conjunto", "programacao": "conjunto"})
    motivos = dict(tabela_nao_aplicaveis(perfil, {}).values.tolist())
    assert "membros" in motivos["soma_conjunto"]
    assert "UHE" not in motivos["geracao_fontes"] and "EOL" not in motivos["geracao_fontes"]  # falta a base, não o tipo
    assert set(aplicaveis(perfil)) == {"cadastro"}


def test_termica_sem_indicadores(usinas) -> None:
    u = usinas["ute_beta"]
    assert u["codigos"]["conferencia"] == 0, u["manifestos"]
    motivos = dict(_nao_aplicaveis(u).values.tolist())
    assert list(motivos) == ["geracao", "disponibilidade", "vazoes", "dispf_horas", "teifa_teip", *NOVAS]
    assert "UTE" in motivos["vazoes"] and "UTE" in motivos["geracao_fontes"]
    assert "Indicadores" in motivos["dispf_horas"] and "ausente" in motivos["dispf_horas"]
    assert "despacho" in motivos["programacao_despacho"].lower()
    pasta = u["pasta"] / "conferencia"
    assert set(carregar_conferencias(pasta / caminhos.ARQUIVOS_CONFERENCIA["resultados"])) == {"cadastro"}
    assert (pasta / caminhos.ARQUIVOS_CONFERENCIA["cadastro"]).exists()
    assert not (pasta / caminhos.ARQUIVOS_CONFERENCIA["vazoes"]).exists()
    resumo = u["manifestos"]["conferencia"]["resumo"]
    assert set(resumo) == {"cadastro", "nao_aplicaveis"} and resumo["nao_aplicaveis"] == list(motivos)


def test_pch_em_conjunto_sem_evt(usinas) -> None:
    u = usinas["pch_alfa"]
    assert u["codigos"]["conferencia"] == 0, u["manifestos"]
    motivos = dict(_nao_aplicaveis(u).values.tolist())
    assert list(motivos) == ["geracao", "disponibilidade", "vazoes", "dispf_horas", "teifa_teip", *NOVAS, *HIDRO]
    assert "Energia Vertida Turbinável" in motivos["geracao"] and "ausente" in motivos["geracao"]
    assert "Dados hidrológicos não coletado" in motivos["alinhamento_hidrologia"]
    assert "PCH" in motivos["programacao_despacho"]


def test_etapa_da_uhe_grava_o_arquivo_sem_mudar_as_seis(tmp_path: Path, monkeypatch) -> None:
    from src.conferencia import etapa
    monkeypatch.setattr(caminhos, "DATA_DIR", tmp_path / "data")
    resultados = {i: _aplicada(i) for i in SEIS_DE_HOJE}
    resultados["disponibilidade"] = nao_aplicavel("disponibilidade", ("a", "b"), "horas", "sem a disponibilidade")
    monkeypatch.setattr(etapa, "conferir", lambda perfil: resultados)
    r = etapa.executar_conferencia(PERFIL_UHE)
    pasta = caminhos.pasta_etapa("sao_domingos", "conferencia")
    assert set(carregar_conferencias(pasta / "conferencias.pkl")) == set(SEIS_DE_HOJE)  # as seis, como hoje
    tabela = pd.read_csv(pasta / "nao_aplicaveis.csv", sep=";", dtype=str)
    assert list(tabela["conferencia"]) == ["disponibilidade", *NOVAS, *HIDRO]
    assert pasta / "nao_aplicaveis.csv" in r.arquivos


def test_relatorio_nao_le_o_arquivo() -> None:
    """O relatório só lê os resultados das Análises; o arquivo não aparece no código do relatório (decisão D12)."""
    pasta = Path(__file__).resolve().parents[2] / "src" / "relatorio"
    for arquivo in pasta.glob("*.py"):
        texto = arquivo.read_text(encoding="utf-8")
        assert "nao_aplicaveis.csv" not in texto and 'ARQUIVOS_CONFERENCIA["nao_aplicaveis"]' not in texto, arquivo


def test_alinhamento_da_hidrologia_so_registrado_nas_hidreletricas(usinas) -> None:
    """Fase D: na térmica, nenhuma linha nova (a conferência das vazões já registra o tipo); o relatório aprovado da
    térmica não muda."""
    assert "alinhamento_hidrologia" not in dict(_nao_aplicaveis(usinas["ute_beta"]).values.tolist())
