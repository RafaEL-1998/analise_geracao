"""Versões anteriores de arquivos brutos: no máximo duas por arquivo, as mais recentes, com a exclusão registrada
no manifesto (spec da Coleta de dados, FR-027 a FR-029)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.coleta.catalogo import DIRETORIO_VERSOES_ANTERIORES, download_resource, load_manifest
from src.coleta.dicionarios import montar_registro, pasta_dicionarios, sincronizar_dicionarios
from src.comum.caminhos import RAW_MANIFEST_FILE
from src.comum.logger import DownloadError
from src.comum.modelos import RecursoONS
from src.comum.regras import CONJUNTO_HIDROLOGIA, MAXIMO_VERSOES_ANTERIORES
from tests.coleta.test_dicionarios import PortalSimulado

PUBLICACOES = ["2026-06-01T00:00:00", "2026-07-01T00:00:00", "2026-08-01T00:00:00",
               "2026-09-01T00:00:00", "2026-10-01T00:00:00"]


def _recurso(publicacao: str, tamanho: int) -> RecursoONS:
    return RecursoONS(id_recurso="id-arquivo", nome_recurso="arquivo", url_download="https://ons.example/arquivo.csv",
                      formato="CSV", tamanho_bytes=tamanho, ultima_modificacao=publicacao)


def _publicar(pasta: Path, manifesto: dict, publicacao: str, conteudo: bytes) -> str:
    resposta = MagicMock()
    resposta.read.side_effect = [conteudo, b""]
    contexto = MagicMock()
    contexto.__enter__.return_value = resposta
    with patch("urllib.request.urlopen", return_value=contexto):
        return download_resource(_recurso(publicacao, len(conteudo)), destination_dir=pasta, manifest=manifesto)


def _republicar(pasta: Path, vezes: int) -> dict:
    """``arquivo.csv`` (v1, publicado em PUBLICACOES[0]) republicado ``vezes`` vezes com conteúdo diferente."""
    (pasta / "arquivo.csv").write_bytes(b"v1")
    manifesto = {"arquivo.csv": {"ultima_modificacao": PUBLICACOES[0], "tamanho_bytes": 2}}
    for i in range(1, vezes + 1):
        assert _publicar(pasta, manifesto, PUBLICACOES[i], f"v{i + 1}".encode()) == "UPDATED"
    return manifesto


def _versoes(pasta: Path) -> list:
    return sorted(p.name for p in (pasta / DIRETORIO_VERSOES_ANTERIORES).iterdir())


def test_limite_de_duas_versoes() -> None:
    assert MAXIMO_VERSOES_ANTERIORES == 2


def test_ate_duas_versoes_nada_e_excluido(tmp_path: Path) -> None:
    manifesto = _republicar(tmp_path, 2)
    assert _versoes(tmp_path) == ["arquivo__pub_20260601T000000.csv", "arquivo__pub_20260701T000000.csv"]
    assert "versoes_excluidas" not in manifesto["arquivo.csv"]


def test_terceira_versao_exclui_a_mais_antiga_e_registra_a_exclusao(tmp_path: Path) -> None:
    manifesto = _republicar(tmp_path, 3)

    assert _versoes(tmp_path) == ["arquivo__pub_20260701T000000.csv", "arquivo__pub_20260801T000000.csv"]
    assert (tmp_path / DIRETORIO_VERSOES_ANTERIORES / "arquivo__pub_20260701T000000.csv").read_bytes() == b"v2"
    assert (tmp_path / DIRETORIO_VERSOES_ANTERIORES / "arquivo__pub_20260801T000000.csv").read_bytes() == b"v3"
    assert (tmp_path / "arquivo.csv").read_bytes() == b"v4"
    entrada = manifesto["arquivo.csv"]
    assert [v["ultima_modificacao"] for v in entrada["versoes_anteriores"]] == PUBLICACOES[1:3]
    [excluida] = entrada["versoes_excluidas"]
    assert excluida["arquivo_preservado"] == "_versoes_anteriores/arquivo__pub_20260601T000000.csv"
    assert excluida["ultima_modificacao"] == PUBLICACOES[0]
    assert len(excluida["sha256"]) == 64 and excluida["excluido_em_utc"]


def test_exclusoes_sucessivas_ficam_todas_registradas(tmp_path: Path) -> None:
    manifesto = _republicar(tmp_path, 4)

    assert _versoes(tmp_path) == ["arquivo__pub_20260801T000000.csv", "arquivo__pub_20260901T000000.csv"]
    entrada = manifesto["arquivo.csv"]
    assert [v["ultima_modificacao"] for v in entrada["versoes_anteriores"]] == PUBLICACOES[2:4]
    assert [v["ultima_modificacao"] for v in entrada["versoes_excluidas"]] == PUBLICACOES[0:2]


def test_conteudo_identico_nao_gera_versao_nem_exclui(tmp_path: Path) -> None:
    manifesto = _republicar(tmp_path, 2)

    assert _publicar(tmp_path, manifesto, PUBLICACOES[3], b"v3") == "UPDATED"

    assert _versoes(tmp_path) == ["arquivo__pub_20260601T000000.csv", "arquivo__pub_20260701T000000.csv"]
    assert len(manifesto["arquivo.csv"]["versoes_anteriores"]) == 2
    assert "versoes_excluidas" not in manifesto["arquivo.csv"]


def test_falha_no_download_nao_exclui_nenhuma_versao(tmp_path: Path) -> None:
    manifesto = _republicar(tmp_path, 2)

    with patch("urllib.request.urlopen", side_effect=OSError("sem rede")), patch("src.coleta.catalogo.time.sleep"):
        with pytest.raises(DownloadError):
            download_resource(_recurso(PUBLICACOES[3], 2), destination_dir=tmp_path, manifest=manifesto)

    assert (tmp_path / "arquivo.csv").read_bytes() == b"v3"
    assert _versoes(tmp_path) == ["arquivo__pub_20260601T000000.csv", "arquivo__pub_20260701T000000.csv"]
    assert "versoes_excluidas" not in manifesto["arquivo.csv"]


def test_poda_nao_toca_versoes_de_outros_arquivos(tmp_path: Path) -> None:
    pasta_versoes = tmp_path / DIRETORIO_VERSOES_ANTERIORES
    pasta_versoes.mkdir()
    (pasta_versoes / "outro__pub_20260101T000000.csv").write_bytes(b"outro")

    _republicar(tmp_path, 3)

    assert "outro__pub_20260101T000000.csv" in _versoes(tmp_path)
    assert len(_versoes(tmp_path)) == 3


def test_registro_com_mais_de_duas_versoes_e_ajustado_na_proxima_preservacao(tmp_path: Path) -> None:
    pasta_versoes = tmp_path / DIRETORIO_VERSOES_ANTERIORES
    pasta_versoes.mkdir()
    anteriores = []
    for i, publicacao in enumerate(PUBLICACOES[:3]):
        nome = f"arquivo__pub_2026{i + 6:02d}01T000000.csv"
        (pasta_versoes / nome).write_bytes(f"v{i + 1}".encode())
        anteriores.append({"arquivo_preservado": f"{DIRETORIO_VERSOES_ANTERIORES}/{nome}",
                           "ultima_modificacao": publicacao, "sha256": "0" * 64})
    (tmp_path / "arquivo.csv").write_bytes(b"v4")
    manifesto = {"arquivo.csv": {"ultima_modificacao": PUBLICACOES[3], "tamanho_bytes": 2,
                                 "versoes_anteriores": anteriores}}

    _publicar(tmp_path, manifesto, PUBLICACOES[4], b"v5")

    assert _versoes(tmp_path) == ["arquivo__pub_20260801T000000.csv", "arquivo__pub_20260901T000000.csv"]
    assert [v["ultima_modificacao"] for v in manifesto["arquivo.csv"]["versoes_excluidas"]] == PUBLICACOES[0:2]


def test_exclusao_fica_restrita_a_pasta_de_versoes(tmp_path: Path) -> None:
    """Um registro adulterado no manifesto não leva a poda a excluir arquivo fora de _versoes_anteriores/."""
    (tmp_path / "importante.csv").write_bytes(b"dados")
    (tmp_path / "arquivo.csv").write_bytes(b"v1")
    (tmp_path / DIRETORIO_VERSOES_ANTERIORES).mkdir()
    (tmp_path / DIRETORIO_VERSOES_ANTERIORES / "arquivo__pub_20260501T000000.csv").write_bytes(b"v0")
    anteriores = [{"arquivo_preservado": "../importante.csv", "ultima_modificacao": "", "sha256": "0" * 64},
                  {"arquivo_preservado": "importante.csv", "ultima_modificacao": "", "sha256": "0" * 64},
                  {"arquivo_preservado": f"{DIRETORIO_VERSOES_ANTERIORES}/arquivo__pub_20260501T000000.csv",
                   "ultima_modificacao": "2026-05-01T00:00:00", "sha256": "0" * 64}]
    manifesto = {"arquivo.csv": {"ultima_modificacao": PUBLICACOES[0], "tamanho_bytes": 2,
                                 "versoes_anteriores": anteriores}}

    _publicar(tmp_path, manifesto, PUBLICACOES[1], b"v2")

    assert (tmp_path / "importante.csv").read_bytes() == b"dados"
    assert [v["arquivo_preservado"] for v in manifesto["arquivo.csv"]["versoes_excluidas"]] == [
        "../importante.csv", "importante.csv"]
    assert _versoes(tmp_path) == ["arquivo__pub_20260501T000000.csv", "arquivo__pub_20260601T000000.csv"]


@pytest.fixture
def portal():
    p = PortalSimulado()
    with patch("src.coleta.catalogo.urllib.request.urlopen", side_effect=p.urlopen), patch("src.coleta.catalogo.time.sleep"):
        yield p


def test_dicionarios_tambem_ficam_com_duas_versoes(portal, tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    url = portal.url(CONJUNTO_HIDROLOGIA, "JSON")
    for versao in range(1, 5):
        portal.conteudo[url] = f"dicionario versao {versao}".encode()
        sincronizar_dicionarios([CONJUNTO_HIDROLOGIA], raw)

    pasta = pasta_dicionarios(CONJUNTO_HIDROLOGIA, raw)
    manifesto = load_manifest(pasta / RAW_MANIFEST_FILE.name)
    entrada = manifesto[Path(url).name]
    conteudos = [(pasta / v["arquivo_preservado"]).read_bytes() for v in entrada["versoes_anteriores"]]
    assert conteudos == [b"dicionario versao 2", b"dicionario versao 3"]
    assert len(list((pasta / DIRETORIO_VERSOES_ANTERIORES).iterdir())) == 2
    assert len(entrada["versoes_excluidas"]) == 1
    registro = montar_registro(raw)
    linha = registro[(registro["conjunto"] == CONJUNTO_HIDROLOGIA) & (registro["formato"] == "JSON")].iloc[0]
    assert linha["versoes_anteriores"] == 2 and linha["resultado_ultima_obtencao"] == "ALTERADO"
