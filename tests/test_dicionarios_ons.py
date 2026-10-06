"""Testes dos dicionários de dados dos conjuntos do ONS (spec 006, US2: FR-013 a FR-015)."""

from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path
from typing import Dict, Iterable, Tuple
from unittest.mock import patch

import pandas as pd
import pytest

from src.config import CONJUNTO_EVT, CONJUNTO_HIDROLOGIA, CONJUNTO_PROGRAMACAO_DIARIA, CONJUNTOS_PIPELINE
from src.dicionarios_ons import (
    COLUNAS_REGISTRO,
    atualizar_dicionarios,
    executar_dicionarios_ons,
    montar_registro,
    pasta_dicionarios,
    selecionar_dicionarios,
    sincronizar_dicionarios,
)

NOMES = {"PDF": "Dicionário de Dados", "JSON": "Dicionário de Dados Json"}


class _Resposta(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class PortalSimulado:
    """Catálogo CKAN e arquivos do ONS simulados (só a camada de rede é trocada)."""

    def __init__(self) -> None:
        self.formatos: Dict[str, Tuple[str, ...]] = {}
        self.conteudo: Dict[str, bytes] = {}
        self.falhar: set = set()
        self.baixados: list = []

    @staticmethod
    def url(conjunto: str, formato: str) -> str:
        return f"https://ons.example/{conjunto}/DicionarioDados_{conjunto}.{formato.lower()}"

    def metadados(self, conjunto: str) -> dict:
        recursos = [{"id": f"{conjunto}-dados", "name": "Dados 2025", "format": "CSV", "size": 10,
                     "url": f"https://ons.example/{conjunto}/DADOS_2025.csv"},
                    {"id": f"{conjunto}-outro", "name": "Dicionário em planilha", "format": "XLSX", "size": 10,
                     "url": f"https://ons.example/{conjunto}/Dicionario.xlsx"}]
        for formato in self.formatos.get(conjunto, ("PDF", "JSON")):
            recursos.append({"id": f"{conjunto}-{formato}", "name": NOMES[formato], "format": formato, "size": None,
                             "last_modified": None, "url": self.url(conjunto, formato)})
        return {"success": True, "result": {"resources": recursos}}

    def urlopen(self, requisicao, timeout=None):
        url = getattr(requisicao, "full_url", requisicao)
        if "package_show" in url:
            return _Resposta(json.dumps(self.metadados(url.rsplit("=", 1)[-1])).encode("utf-8"))
        if url in self.falhar:
            raise urllib.error.URLError("HTTP 500")
        self.baixados.append(url)
        return _Resposta(self.conteudo.get(url, b"dicionario versao 1"))


@pytest.fixture
def portal():
    p = PortalSimulado()
    with patch("src.collector.urllib.request.urlopen", side_effect=p.urlopen), patch("src.collector.time.sleep"):
        yield p


def _resultados(registro: pd.DataFrame, conjunto: str) -> Dict[str, str]:
    linhas = registro[registro["conjunto"] == conjunto]
    return dict(zip(linhas["formato"], linhas["resultado_ultima_obtencao"]))


def test_selecao_so_pdf_e_json_com_dicionario_no_nome(portal) -> None:
    recursos = selecionar_dicionarios(portal.metadados(CONJUNTO_HIDROLOGIA))
    assert sorted(r.formato for r in recursos) == ["JSON", "PDF"]
    assert all("Dicion" in r.nome_recurso for r in recursos)


def test_novo_inalterado_e_alterado_com_versao_preservada(portal, tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    sincronizar_dicionarios([CONJUNTO_HIDROLOGIA], raw)
    assert _resultados(montar_registro(raw), CONJUNTO_HIDROLOGIA) == {"PDF": "NOVO", "JSON": "NOVO"}

    sincronizar_dicionarios([CONJUNTO_HIDROLOGIA], raw)
    assert _resultados(montar_registro(raw), CONJUNTO_HIDROLOGIA) == {"PDF": "INALTERADO", "JSON": "INALTERADO"}

    portal.conteudo[portal.url(CONJUNTO_HIDROLOGIA, "JSON")] = b"dicionario versao 2"
    sincronizar_dicionarios([CONJUNTO_HIDROLOGIA], raw)
    registro = montar_registro(raw)
    assert _resultados(registro, CONJUNTO_HIDROLOGIA) == {"PDF": "INALTERADO", "JSON": "ALTERADO"}
    pasta = pasta_dicionarios(CONJUNTO_HIDROLOGIA, raw)
    assert pasta == raw / "dados_hidrologicos_ho" / "_dicionarios"
    preservados = list((pasta / "_versoes_anteriores").iterdir())
    assert len(preservados) == 1 and preservados[0].read_bytes() == b"dicionario versao 1"
    linha = registro[(registro["conjunto"] == CONJUNTO_HIDROLOGIA) & (registro["formato"] == "JSON")].iloc[0]
    assert linha["versoes_anteriores"] == 1 and linha["ultima_versao_anterior"].startswith("_versoes_anteriores/")
    assert (pasta / Path(portal.url(CONJUNTO_HIDROLOGIA, "JSON")).name).read_bytes() == b"dicionario versao 2"


def test_falha_mantem_a_copia_valida_e_nao_interrompe(portal, tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    sincronizar_dicionarios([CONJUNTO_HIDROLOGIA], raw)
    portal.falhar.add(portal.url(CONJUNTO_HIDROLOGIA, "PDF"))
    resultados = sincronizar_dicionarios([CONJUNTO_HIDROLOGIA], raw)  # não levanta exceção
    assert {r["formato"]: r["resultado"] for r in resultados} == {"PDF": "FALHA", "JSON": "INALTERADO"}
    pasta = pasta_dicionarios(CONJUNTO_HIDROLOGIA, raw)
    assert (pasta / Path(portal.url(CONJUNTO_HIDROLOGIA, "PDF")).name).read_bytes() == b"dicionario versao 1"
    assert _resultados(montar_registro(raw), CONJUNTO_HIDROLOGIA)["PDF"] == "FALHA"


def test_formato_nao_publicado_e_conjunto_nao_obtido(portal, tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    portal.formatos[CONJUNTO_PROGRAMACAO_DIARIA] = ("PDF",)
    sincronizar_dicionarios([CONJUNTO_PROGRAMACAO_DIARIA], raw)
    registro = montar_registro(raw)
    assert list(registro.columns) == COLUNAS_REGISTRO
    assert len(registro) == 2 * len(CONJUNTOS_PIPELINE) == 20
    assert _resultados(registro, CONJUNTO_PROGRAMACAO_DIARIA) == {"PDF": "NOVO", "JSON": "NAO_PUBLICADO"}
    assert _resultados(registro, CONJUNTO_HIDROLOGIA) == {"PDF": "NAO_OBTIDO", "JSON": "NAO_OBTIDO"}


def test_execucao_parcial_nao_apaga_os_outros_conjuntos(portal, tmp_path: Path) -> None:
    raw, saida = tmp_path / "raw", tmp_path / "processed"
    assert executar_dicionarios_ons([CONJUNTO_HIDROLOGIA], pasta_raw=raw, pasta_saida=saida) == 0
    assert executar_dicionarios_ons([CONJUNTO_PROGRAMACAO_DIARIA], pasta_raw=raw, pasta_saida=saida) == 0
    registro = pd.read_csv(saida / "relatorio_dicionarios_ons.csv", sep=";")
    assert _resultados(registro, CONJUNTO_HIDROLOGIA) == {"PDF": "NOVO", "JSON": "NOVO"}
    assert _resultados(registro, CONJUNTO_PROGRAMACAO_DIARIA) == {"PDF": "NOVO", "JSON": "NOVO"}


def test_dicionario_da_evt_nao_baixa_os_dados(portal, tmp_path: Path) -> None:
    raw, saida = tmp_path / "raw", tmp_path / "processed"
    dados = raw / "ENERGIA_VERTIDA_TURBINAVEL_2025_01.csv"
    dados.parent.mkdir(parents=True)
    dados.write_text("conteudo local", encoding="utf-8")
    antes = dados.stat().st_mtime_ns
    with patch("src.collector.discover_and_download_all") as coleta:
        atualizar_dicionarios([CONJUNTO_EVT], raiz_raw=raw, pasta_saida=saida)
    coleta.assert_not_called()
    assert dados.stat().st_mtime_ns == antes and dados.read_text(encoding="utf-8") == "conteudo local"
    assert all("DADOS_2025" not in url for url in portal.baixados)
    assert sorted(p.suffix for p in (raw / "_dicionarios").glob("DicionarioDados_*")) == [".json", ".pdf"]
    assert (saida / "relatorio_dicionarios_ons.csv").exists()


def test_falha_no_catalogo_nao_interrompe(portal, tmp_path: Path) -> None:
    raw, saida = tmp_path / "raw", tmp_path / "processed"
    with patch("src.dicionarios_ons.fetch_ckan_package_metadata", side_effect=OSError("portal fora do ar")):
        atualizar_dicionarios([CONJUNTO_HIDROLOGIA], raiz_raw=raw, pasta_saida=saida)
        assert executar_dicionarios_ons([CONJUNTO_HIDROLOGIA], pasta_raw=raw, pasta_saida=saida) == 0
    registro = pd.read_csv(saida / "relatorio_dicionarios_ons.csv", sep=";")
    assert _resultados(registro, CONJUNTO_HIDROLOGIA) == {"PDF": "FALHA", "JSON": "FALHA"}
