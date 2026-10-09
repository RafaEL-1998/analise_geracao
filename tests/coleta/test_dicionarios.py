"""Testes dos dicionários de dados dos conjuntos do ONS (spec da Coleta de dados, FR-031 a FR-033)."""

from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path
from typing import Dict, Tuple
from unittest.mock import patch

import pandas as pd
import pytest

from src.coleta.registro import CONJUNTOS_PIPELINE
from src.comum.regras import CONJUNTO_EVT, CONJUNTO_HIDROLOGIA, CONJUNTO_PROGRAMACAO_DIARIA
from src.coleta.dicionarios import (
    COLUNAS_REGISTRO,
    NOME_REGISTRO,
    exportar_registro,
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
    with patch("src.coleta.catalogo.urllib.request.urlopen", side_effect=p.urlopen), patch("src.coleta.catalogo.time.sleep"):
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
    raw, saida = tmp_path / "raw", tmp_path / "coleta"
    for conjunto in (CONJUNTO_HIDROLOGIA, CONJUNTO_PROGRAMACAO_DIARIA):
        sincronizar_dicionarios([conjunto], raw)
        exportar_registro(raw, saida)
    registro = pd.read_csv(saida / NOME_REGISTRO, sep=";")
    assert _resultados(registro, CONJUNTO_HIDROLOGIA) == {"PDF": "NOVO", "JSON": "NOVO"}
    assert _resultados(registro, CONJUNTO_PROGRAMACAO_DIARIA) == {"PDF": "NOVO", "JSON": "NOVO"}


def test_dicionario_da_evt_nao_baixa_os_dados(portal, tmp_path: Path) -> None:
    raw, saida = tmp_path / "raw", tmp_path / "coleta"
    dados = raw / "ENERGIA_VERTIDA_TURBINAVEL_2025_01.csv"
    dados.parent.mkdir(parents=True)
    dados.write_text("conteudo local", encoding="utf-8")
    antes = dados.stat().st_mtime_ns
    with patch("src.coleta.catalogo.discover_and_download_all") as coleta:
        sincronizar_dicionarios([CONJUNTO_EVT], raw)
        exportar_registro(raw, saida)
    coleta.assert_not_called()
    assert dados.stat().st_mtime_ns == antes and dados.read_text(encoding="utf-8") == "conteudo local"
    assert all("DADOS_2025" not in url for url in portal.baixados)
    assert sorted(p.suffix for p in (raw / "_dicionarios").glob("DicionarioDados_*")) == [".json", ".pdf"]
    assert (saida / NOME_REGISTRO).exists()


def test_falha_no_catalogo_nao_interrompe(portal, tmp_path: Path) -> None:
    raw, saida = tmp_path / "raw", tmp_path / "coleta"
    with patch("src.coleta.dicionarios.fetch_ckan_package_metadata", side_effect=OSError("portal fora do ar")):
        sincronizar_dicionarios([CONJUNTO_HIDROLOGIA], raw)  # a falha vai para o registro, sem exceção
        exportar_registro(raw, saida)
    registro = pd.read_csv(saida / NOME_REGISTRO, sep=";")
    assert _resultados(registro, CONJUNTO_HIDROLOGIA) == {"PDF": "FALHA", "JSON": "FALHA"}


def test_coleta_interrompida_tambem_obtem_os_dicionarios(tmp_path: Path, monkeypatch) -> None:
    """Spec da Coleta de dados (FR-031): a consulta ao portal obtém os dicionários mesmo quando a coleta para no código 2."""
    from src.coleta import etapa as etapa_coleta
    from src.comum import caminhos
    from src.comum.perfil import carregar_perfil

    monkeypatch.setattr(caminhos, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(caminhos, "RAW_DATA_DIR", tmp_path / "data" / "raw")
    chamadas = []
    monkeypatch.setattr(etapa_coleta, "_coletar_evt", lambda c: c.resultado(2))
    monkeypatch.setattr(etapa_coleta, "sincronizar_dicionarios", lambda conjuntos, raw: chamadas.append(raw) or [])
    resultado = etapa_coleta.executar_coleta(carregar_perfil("sao_domingos"), sem_portal=False)
    assert resultado.codigo == 2 and len(chamadas) == 1 and "dicionarios" in resultado.resumo
    assert any(Path(a).name == NOME_REGISTRO for a in resultado.arquivos)
