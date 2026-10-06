"""Testes unitários para o módulo coletor (User Story 1)."""

from pathlib import Path
from unittest.mock import patch, MagicMock
from src.models import RecursoONS
from src.collector import parse_ckan_resources, download_resource, load_manifest, save_manifest


def _mock_download(conteudo: bytes):
    mock_response = MagicMock()
    mock_response.read.side_effect = [conteudo, b""]
    contexto = MagicMock()
    contexto.__enter__.return_value = mock_response
    return contexto


def _recurso(nome: str, tamanho: int, ultima_modificacao: str = "2026-09-30T15:05:02") -> RecursoONS:
    return RecursoONS(
        id_recurso=f"id-{nome}",
        nome_recurso=nome,
        url_download=f"https://fake-url.com/{nome}.csv",
        formato="CSV",
        tamanho_bytes=tamanho,
        ultima_modificacao=ultima_modificacao,
    )


def test_parse_ckan_resources(mock_ckan_response):
    """Apenas CSVs são identificados, com tamanho e last_modified publicados."""
    resources = parse_ckan_resources(mock_ckan_response)
    assert len(resources) == 2
    assert all(r.formato.upper() == "CSV" for r in resources)
    assert resources[0].nome_recurso == "Energia_Vertida_Turbinavel-2015"
    assert resources[1].ultima_modificacao == "2026-09-30T15:06:00.141888"
    assert resources[1].tamanho_bytes == 800000


def test_download_resource_new_file(tmp_path):
    """Arquivo novo é baixado e registrado no manifesto."""
    conteudo = b"linha1;coluna\nlinha2;coluna\n"
    recurso = _recurso("arquivo", len(conteudo))
    manifesto = {}

    with patch("urllib.request.urlopen", return_value=_mock_download(conteudo)):
        status = download_resource(recurso, destination_dir=tmp_path, manifest=manifesto)

    assert status == "DOWNLOADED"
    assert Path(recurso.arquivo_local).read_bytes() == conteudo
    assert manifesto["arquivo.csv"]["ultima_modificacao"] == recurso.ultima_modificacao
    assert manifesto["arquivo.csv"]["tamanho_bytes"] == len(conteudo)


def test_download_resource_sem_manifesto_aceita_arquivo_com_tamanho_publicado(tmp_path):
    """Sem manifesto, arquivo local com o tamanho publicado é reaproveitado e registrado."""
    existente = tmp_path / "arquivo_existente.csv"
    existente.write_bytes(b"dados_ja_existentes")
    recurso = _recurso("arquivo_existente", len(b"dados_ja_existentes"))
    manifesto = {}

    with patch("urllib.request.urlopen") as mock_urlopen:
        status = download_resource(recurso, destination_dir=tmp_path, manifest=manifesto)
        mock_urlopen.assert_not_called()

    assert status == "CACHED"
    assert manifesto["arquivo_existente.csv"]["origem_registro"] == "ARQUIVO_EXISTENTE"


def test_download_resource_rebaixa_quando_ons_revisa_arquivo(tmp_path):
    """Mesmo tamanho, mas last_modified diferente do manifesto: o arquivo é baixado de novo."""
    existente = tmp_path / "arquivo.csv"
    existente.write_bytes(b"versao_antiga")
    manifesto = {"arquivo.csv": {"ultima_modificacao": "2026-09-01T10:00:00", "tamanho_bytes": len(b"versao_antiga")}}
    recurso = _recurso("arquivo", len(b"versao_nova!!"), ultima_modificacao="2026-09-30T15:05:02")

    with patch("urllib.request.urlopen", return_value=_mock_download(b"versao_nova!!")):
        status = download_resource(recurso, destination_dir=tmp_path, manifest=manifesto)

    assert status == "UPDATED"
    assert existente.read_bytes() == b"versao_nova!!"
    assert manifesto["arquivo.csv"]["ultima_modificacao"] == "2026-09-30T15:05:02"


def test_download_resource_rebaixa_quando_tamanho_difere_sem_manifesto(tmp_path):
    """Sem manifesto e com tamanho diferente do publicado, a cópia local é substituída."""
    existente = tmp_path / "arquivo.csv"
    existente.write_bytes(b"curto")
    recurso = _recurso("arquivo", len(b"conteudo publicado"))

    with patch("urllib.request.urlopen", return_value=_mock_download(b"conteudo publicado")):
        status = download_resource(recurso, destination_dir=tmp_path, manifest={})

    assert status == "UPDATED"
    assert existente.read_bytes() == b"conteudo publicado"


def test_manifesto_ida_e_volta(tmp_path):
    caminho = tmp_path / "_manifesto_ons.json"
    save_manifest({"a.csv": {"tamanho_bytes": 10}}, caminho)
    assert load_manifest(caminho) == {"a.csv": {"tamanho_bytes": 10}}
    assert load_manifest(tmp_path / "inexistente.json") == {}


def test_recursos_e_nomes_no_formato_compacto():
    """Spec 004: recursos Parquet selecionados por formato e gravados com a extensão original."""
    from src.collector import _local_filename

    ckan = {"result": {"resources": [
        {"id": "a", "name": "Programacao-2026-07-01", "format": "PARQUET",
         "url": "https://ons/programacao_diaria/PROGRAMACAO_DIARIA_2026_07_01.parquet", "size": 10},
        {"id": "b", "name": "Programacao-2026-07-01", "format": "CSV",
         "url": "https://ons/programacao_diaria/PROGRAMACAO_DIARIA_2026_07_01.csv", "size": 20},
    ]}}
    parquet = parse_ckan_resources(ckan, "PARQUET")
    assert [r.formato for r in parquet] == ["PARQUET"]
    assert _local_filename(parquet[0]) == "PROGRAMACAO_DIARIA_2026_07_01.parquet"
    csv = parse_ckan_resources(ckan)
    assert [r.formato for r in csv] == ["CSV"]
    assert _local_filename(csv[0]) == "PROGRAMACAO_DIARIA_2026_07_01.csv"


# ---------------------------------------------------------------------------
# Spec 005, US1: versões anteriores de arquivos republicados pelo ONS
# ---------------------------------------------------------------------------


def _baixar(recurso, pasta, manifesto, conteudo, force=False):
    with patch("urllib.request.urlopen", return_value=_mock_download(conteudo)):
        return download_resource(recurso, destination_dir=pasta, force=force, manifest=manifesto)


def test_republicacao_com_conteudo_diferente_preserva_a_versao_anterior(tmp_path):
    existente = tmp_path / "arquivo.csv"
    existente.write_bytes(b"versao_antiga")
    manifesto = {"arquivo.csv": {"ultima_modificacao": "2026-09-01T10:00:00", "tamanho_bytes": 13}}
    recurso = _recurso("arquivo", 12, ultima_modificacao="2026-09-30T15:05:02")

    assert _baixar(recurso, tmp_path, manifesto, b"versao_nova!") == "UPDATED"

    preservado = tmp_path / "_versoes_anteriores" / "arquivo__pub_20260901T100000.csv"
    assert preservado.read_bytes() == b"versao_antiga"
    assert existente.read_bytes() == b"versao_nova!"
    versoes = manifesto["arquivo.csv"]["versoes_anteriores"]
    assert len(versoes) == 1
    v = versoes[0]
    assert v["arquivo_preservado"] == "_versoes_anteriores/arquivo__pub_20260901T100000.csv"
    assert v["ultima_modificacao"] == "2026-09-01T10:00:00"
    assert v["tamanho_bytes"] == 13
    assert len(v["sha256"]) == 64 and v["arquivado_em_utc"]
    assert manifesto["arquivo.csv"]["ultima_modificacao"] == "2026-09-30T15:05:02"


def test_republicacao_com_conteudo_identico_nao_cria_copia(tmp_path):
    (tmp_path / "arquivo.csv").write_bytes(b"mesmo_conteudo")
    manifesto = {"arquivo.csv": {"ultima_modificacao": "2026-09-01T10:00:00", "tamanho_bytes": 14}}
    recurso = _recurso("arquivo", 14, ultima_modificacao="2026-09-30T15:05:02")

    _baixar(recurso, tmp_path, manifesto, b"mesmo_conteudo")

    assert not (tmp_path / "_versoes_anteriores").exists()
    assert manifesto["arquivo.csv"].get("versoes_anteriores", []) == []
    assert manifesto["arquivo.csv"]["ultima_modificacao"] == "2026-09-30T15:05:02"


def test_republicacoes_sucessivas_preservam_todas_as_versoes(tmp_path):
    (tmp_path / "arquivo.csv").write_bytes(b"v1")
    manifesto = {"arquivo.csv": {"ultima_modificacao": "2026-08-01T00:00:00", "tamanho_bytes": 2}}
    _baixar(_recurso("arquivo", 2, "2026-09-01T00:00:00"), tmp_path, manifesto, b"v2")
    _baixar(_recurso("arquivo", 2, "2026-10-01T00:00:00"), tmp_path, manifesto, b"v3")

    pasta = tmp_path / "_versoes_anteriores"
    assert (pasta / "arquivo__pub_20260801T000000.csv").read_bytes() == b"v1"
    assert (pasta / "arquivo__pub_20260901T000000.csv").read_bytes() == b"v2"
    assert (tmp_path / "arquivo.csv").read_bytes() == b"v3"
    assert [v["ultima_modificacao"] for v in manifesto["arquivo.csv"]["versoes_anteriores"]] == [
        "2026-08-01T00:00:00", "2026-09-01T00:00:00"]


def test_falha_no_download_mantem_a_versao_corrente(tmp_path):
    existente = tmp_path / "arquivo.csv"
    existente.write_bytes(b"versao_corrente")
    manifesto = {"arquivo.csv": {"ultima_modificacao": "2026-09-01T10:00:00", "tamanho_bytes": 15}}
    recurso = _recurso("arquivo", 15, ultima_modificacao="2026-09-30T15:05:02")

    with patch("urllib.request.urlopen", side_effect=OSError("sem rede")), patch("src.collector.time.sleep"):
        try:
            download_resource(recurso, destination_dir=tmp_path, manifest=manifesto)
        except Exception:
            pass

    assert existente.read_bytes() == b"versao_corrente"
    assert not (tmp_path / "_versoes_anteriores").exists()


def test_download_forcado_sem_manifesto_usa_data_de_arquivamento(tmp_path):
    (tmp_path / "arquivo.csv").write_bytes(b"local_sem_registro")
    recurso = _recurso("arquivo", 10, ultima_modificacao="2026-09-30T15:05:02")

    _baixar(recurso, tmp_path, {}, b"publicado!", force=True)

    copias = list((tmp_path / "_versoes_anteriores").iterdir())
    assert len(copias) == 1
    assert copias[0].name.startswith("arquivo__arq_") and copias[0].suffix == ".csv"
    assert copias[0].read_bytes() == b"local_sem_registro"


def test_filtragem_ignora_versoes_anteriores(tmp_path):
    from src.filter import filter_all_raw_files
    from tests.conftest import ONS_CSV_HEADER, SAMPLE_SAO_DOMINGOS_LINE

    (tmp_path / "ARQ.csv").write_text("\n".join([ONS_CSV_HEADER, SAMPLE_SAO_DOMINGOS_LINE]), encoding="utf-8")
    antigas = tmp_path / "_versoes_anteriores"
    antigas.mkdir()
    (antigas / "ARQ__pub_20260901T000000.csv").write_text(
        "\n".join([ONS_CSV_HEADER, SAMPLE_SAO_DOMINGOS_LINE]), encoding="utf-8")

    registros, auditoria = filter_all_raw_files(raw_dir=tmp_path)
    assert len(registros) == 1
    assert [a.nome_arquivo for a in auditoria] == ["ARQ.csv"]
