"""Módulo coletor: Descoberta via CKAN API e download idempotente em streaming (User Story 1).

O cache considera a versão publicada pelo ONS: um arquivo local só é reaproveitado se o
last_modified registrado no manifesto for o mesmo do catálogo (ou, na ausência de
manifesto, se o tamanho local for igual ao tamanho publicado). Arquivos revisados pelo
ONS são baixados novamente.
"""

import hashlib
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import (
    ONS_CKAN_PACKAGE_URL,
    RAW_DATA_DIR,
    RAW_MANIFEST_FILE,
    DOWNLOAD_CHUNK_SIZE,
    REQUEST_TIMEOUT,
    MAX_DOWNLOAD_RETRIES,
    RETRY_BACKOFF_FACTOR,
)
from src.models import RecursoONS
from src.logger import setup_logger, DownloadError

logger = setup_logger("collector")


def fetch_ckan_package_metadata(package_url: str = ONS_CKAN_PACKAGE_URL) -> Dict[str, Any]:
    """Consulta a API CKAN do ONS e retorna os metadados do pacote."""
    headers = {"User-Agent": "ONS-Collector-UHE-Sao-Domingos/1.0"}
    req = urllib.request.Request(package_url, headers=headers)

    for attempt in range(1, MAX_DOWNLOAD_RETRIES + 1):
        try:
            logger.info("Consultando catálogo CKAN do ONS: %s (tentativa %d)", package_url, attempt)
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                content = response.read().decode("utf-8")
                data = json.loads(content)
                if not data.get("success", False):
                    raise DownloadError(f"A API CKAN retornou insucesso: {data}")
                return data
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
            logger.warning("Falha na tentativa %d ao consultar API CKAN: %s", attempt, e)
            if attempt == MAX_DOWNLOAD_RETRIES:
                raise DownloadError(f"Falha definitiva ao consultar API CKAN após {MAX_DOWNLOAD_RETRIES} tentativas: {e}") from e
            time.sleep(RETRY_BACKOFF_FACTOR ** attempt)

    raise DownloadError("Falha inesperada ao consultar API CKAN.")


def parse_ckan_resources(ckan_data: Dict[str, Any], formato: str = "CSV") -> List[RecursoONS]:
    """Filtra e extrai os recursos de um formato (CSV por padrão) a partir da resposta da API CKAN."""
    formato = formato.strip().upper()
    extensao = f".{formato.lower()}"
    resources_data = ckan_data.get("result", {}).get("resources", [])
    csv_resources: List[RecursoONS] = []

    for r in resources_data:
        fmt = (r.get("format") or "").strip().upper()
        url = (r.get("url") or "").strip()
        name = (r.get("name") or "").strip()
        res_id = (r.get("id") or "").strip()
        size = int(r.get("size") or 0)
        last_modified = (r.get("last_modified") or r.get("metadata_modified") or r.get("created") or "").strip()

        # Aceita se o formato declarado conferir ou se a URL terminar na extensão do formato
        if fmt == formato or url.lower().endswith(extensao):
            csv_resources.append(
                RecursoONS(
                    id_recurso=res_id,
                    nome_recurso=name,
                    url_download=url,
                    formato=formato,
                    tamanho_bytes=size,
                    ultima_modificacao=last_modified,
                )
            )

    logger.info("Total de recursos %s descobertos no portal ONS: %d", formato, len(csv_resources))
    return csv_resources


def load_manifest(manifest_path: Path = RAW_MANIFEST_FILE) -> Dict[str, Dict[str, Any]]:
    """Lê o manifesto de versões baixadas; retorna dicionário vazio se não existir."""
    if not manifest_path.exists():
        return {}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Manifesto de versões ilegível (%s); será recriado.", e)
        return {}


def save_manifest(manifest: Dict[str, Dict[str, Any]], manifest_path: Path = RAW_MANIFEST_FILE) -> None:
    """Grava o manifesto de versões de forma atômica."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = manifest_path.with_suffix(".json.part")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
    temp_path.replace(manifest_path)


def _local_filename(recurso: RecursoONS) -> str:
    url_filename = recurso.url_download.split("/")[-1].split("?")[0]
    extensao = f".{(recurso.formato or 'CSV').lower()}"
    if not url_filename.lower().endswith(extensao):
        url_filename = f"{recurso.nome_recurso}{extensao}"
    return url_filename


def _is_local_copy_current(recurso: RecursoONS, entry: Optional[Dict[str, Any]], local_size: int) -> bool:
    """Decide se a cópia local corresponde à versão publicada no catálogo."""
    if entry:
        same_size = int(entry.get("tamanho_bytes", -1)) == local_size
        if recurso.ultima_modificacao:
            return same_size and entry.get("ultima_modificacao") == recurso.ultima_modificacao
        return same_size
    # Sem manifesto (primeira execução): aceita o arquivo se o tamanho bater com o publicado
    if recurso.tamanho_bytes > 0:
        return local_size == recurso.tamanho_bytes
    return True


def _register_version(
    manifest: Dict[str, Dict[str, Any]],
    filename: str,
    recurso: RecursoONS,
    local_size: int,
    origem: str,
    versao_preservada: Optional[Dict[str, Any]] = None,
) -> None:
    """Registra a versão corrente do arquivo, mantendo a lista de versões anteriores preservadas."""
    anteriores = list((manifest.get(filename) or {}).get("versoes_anteriores", []))
    if versao_preservada:
        anteriores.append(versao_preservada)
    manifest[filename] = {
        "url": recurso.url_download,
        "ultima_modificacao": recurso.ultima_modificacao,
        "tamanho_publicado_bytes": recurso.tamanho_bytes,
        "tamanho_bytes": local_size,
        "registrado_em_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "origem_registro": origem,  # DOWNLOAD ou ARQUIVO_EXISTENTE
    }
    if anteriores:
        manifest[filename]["versoes_anteriores"] = anteriores


# Subpasta (não percorrida pelos leitores) com as versões anteriores de arquivos republicados pelo ONS
DIRETORIO_VERSOES_ANTERIORES = "_versoes_anteriores"


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(DOWNLOAD_CHUNK_SIZE), b""):
            h.update(bloco)
    return h.hexdigest()


def _carimbo(valor: str) -> str:
    """'2026-09-01T10:00:00.123' -> '20260901T100000'; vazio se a data não puder ser lida."""
    try:
        return datetime.fromisoformat(valor.strip()[:19]).strftime("%Y%m%dT%H%M%S")
    except (ValueError, AttributeError):
        return ""


def _preservar_versao_anterior(
    local_path: Path,
    filename: str,
    sha256: str,
    manifest: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Move a cópia local para _versoes_anteriores/ e devolve o registro da versão preservada.

    O nome leva a data de publicação registrada no manifesto (``__pub_``) ou, se ela não for
    conhecida, a data do arquivamento (``__arq_``); nomes repetidos recebem sufixo numérico.
    """
    entrada = manifest.get(filename) or {}
    publicacao = entrada.get("ultima_modificacao") or ""
    agora = datetime.now(timezone.utc)
    carimbo = _carimbo(publicacao)
    rotulo = f"pub_{carimbo}" if carimbo else f"arq_{agora.strftime('%Y%m%dT%H%M%S')}"
    pasta = local_path.parent / DIRETORIO_VERSOES_ANTERIORES
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{local_path.stem}__{rotulo}{local_path.suffix}"
    n = 2
    while destino.exists():
        destino = pasta / f"{local_path.stem}__{rotulo}_{n}{local_path.suffix}"
        n += 1
    tamanho = local_path.stat().st_size
    local_path.replace(destino)
    logger.info("Versão anterior preservada: %s -> %s/%s", filename, DIRETORIO_VERSOES_ANTERIORES, destino.name)
    return {
        "arquivo_preservado": f"{DIRETORIO_VERSOES_ANTERIORES}/{destino.name}",
        "ultima_modificacao": publicacao,
        "tamanho_bytes": tamanho,
        "sha256": sha256,
        "arquivado_em_utc": agora.strftime("%Y-%m-%d %H:%M:%S"),
    }


def download_resource(
    recurso: RecursoONS,
    destination_dir: Path = RAW_DATA_DIR,
    force: bool = False,
    chunk_size: int = DOWNLOAD_CHUNK_SIZE,
    manifest: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """Baixa um arquivo do ONS em streaming, reaproveitando a cópia local se estiver atual."""
    destination_dir.mkdir(parents=True, exist_ok=True)
    manifest = manifest if manifest is not None else {}

    url_filename = _local_filename(recurso)
    local_path = destination_dir / url_filename
    recurso.arquivo_local = str(local_path)

    status_sucesso = "DOWNLOADED"
    if local_path.exists() and not force:
        local_size = local_path.stat().st_size
        entry = manifest.get(url_filename)
        if local_size > 0 and _is_local_copy_current(recurso, entry, local_size):
            logger.info("Arquivo local corresponde à versão publicada (Cache): %s (%d bytes)", local_path.name, local_size)
            if entry is None:
                _register_version(manifest, url_filename, recurso, local_size, "ARQUIVO_EXISTENTE")
            recurso.status_sincronizacao = "CACHED"
            return "CACHED"
        logger.info(
            "Versão local de %s difere da publicada (last_modified %s, %d bytes publicados); baixando novamente.",
            local_path.name,
            recurso.ultima_modificacao or "desconhecido",
            recurso.tamanho_bytes,
        )
        status_sucesso = "UPDATED"

    temp_path = destination_dir / f"{url_filename}.part"
    headers = {"User-Agent": "ONS-Collector-UHE-Sao-Domingos/1.0"}
    req = urllib.request.Request(recurso.url_download, headers=headers)

    for attempt in range(1, MAX_DOWNLOAD_RETRIES + 1):
        try:
            logger.info("Iniciando download: %s -> %s (tentativa %d)", recurso.url_download, local_path.name, attempt)
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                total_bytes = 0
                with open(temp_path, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        total_bytes += len(chunk)

            if recurso.tamanho_bytes > 0 and total_bytes != recurso.tamanho_bytes:
                logger.warning(
                    "Tamanho baixado de %s (%d bytes) difere do publicado no catálogo (%d bytes).",
                    local_path.name,
                    total_bytes,
                    recurso.tamanho_bytes,
                )

            # Versão local com conteúdo diferente do baixado é preservada antes da substituição
            versao_preservada = None
            if local_path.exists() and temp_path.exists():
                sha_local = _sha256(local_path)
                if sha_local != _sha256(temp_path):
                    versao_preservada = _preservar_versao_anterior(local_path, url_filename, sha_local, manifest)

            # Move arquivo temporário para o destino final (atômico)
            if temp_path.exists():
                temp_path.replace(local_path)

            _register_version(manifest, url_filename, recurso, total_bytes, "DOWNLOAD", versao_preservada)
            recurso.status_sincronizacao = status_sucesso
            logger.info("Download concluído com sucesso: %s (%d bytes)", local_path.name, total_bytes)
            return status_sucesso

        except Exception as e:
            logger.warning("Erro durante download de %s (tentativa %d): %s", recurso.nome_recurso, attempt, e)
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            if attempt == MAX_DOWNLOAD_RETRIES:
                recurso.status_sincronizacao = "FAILED"
                raise DownloadError(f"Falha definitiva ao baixar {recurso.nome_recurso}: {e}") from e
            time.sleep(RETRY_BACKOFF_FACTOR ** attempt)

    recurso.status_sincronizacao = "FAILED"
    return "FAILED"


def discover_and_download_all(
    package_url: str = ONS_CKAN_PACKAGE_URL,
    destination_dir: Path = RAW_DATA_DIR,
    force: bool = False,
) -> List[RecursoONS]:
    """Fluxo completo da User Story 1: descoberta e sincronização de 100% dos CSVs publicados."""
    logger.info("Iniciando descoberta e download de arquivos ONS...")
    metadata = fetch_ckan_package_metadata(package_url)
    resources = parse_ckan_resources(metadata)

    manifest_path = destination_dir / RAW_MANIFEST_FILE.name
    manifest = load_manifest(manifest_path)
    try:
        for idx, r in enumerate(resources, start=1):
            logger.info("[%d/%d] Sincronizando recurso: %s", idx, len(resources), r.nome_recurso)
            download_resource(r, destination_dir=destination_dir, force=force, manifest=manifest)
    finally:
        save_manifest(manifest, manifest_path)

    resumo: Dict[str, int] = {}
    for r in resources:
        resumo[r.status_sincronizacao] = resumo.get(r.status_sincronizacao, 0) + 1
    logger.info("Sincronização concluída. Total de recursos processados: %d | %s", len(resources), resumo)
    return resources
