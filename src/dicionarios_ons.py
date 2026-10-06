"""Dicionários de dados dos conjuntos do ONS usados no pipeline (spec 006, US2; constituição 1.2.0, princípio IV).

A cada coleta, os dicionários publicados de cada conjunto ("Dicionário de Dados" em PDF e "Dicionário
de Dados Json") são obtidos e guardados em ``<pasta bruta do conjunto>/_dicionarios/``. O catálogo
não informa data nem tamanho desses arquivos; por isso eles são sempre baixados e comparados pelo
conteúdo (SHA-256): NOVO, INALTERADO ou ALTERADO (a versão anterior vai para ``_versoes_anteriores/``,
mecanismo da spec 005). Falhas são registradas e não interrompem as demais etapas.
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from src.collector import _local_filename, _sha256, download_resource, fetch_ckan_package_metadata, load_manifest, save_manifest
from src.config import (
    CONJUNTOS_PIPELINE,
    DICIONARIOS_REGISTRO_FILE,
    DIRETORIO_DICIONARIOS,
    ONS_CKAN_PACKAGE_SHOW_URL,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    RAW_MANIFEST_FILE,
)
from src.logger import NIVEIS_LOG, configurar_nivel_log, setup_logger
from src.models import RecursoONS
from src.persistencia import gravar_csv

logger = setup_logger("dicionarios_ons")

FORMATOS_DICIONARIO = ("PDF", "JSON")
CHAVE_CONSULTA = "_consulta"  # entrada do manifesto com a data e o resultado da última consulta ao catálogo
COLUNAS_REGISTRO: List[str] = [
    "conjunto", "pasta", "formato", "arquivo", "url", "resultado_ultima_obtencao", "obtido_em_utc", "sha256",
    "tamanho_bytes", "versoes_anteriores", "ultima_versao_anterior",
]


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def pasta_dicionarios(conjunto: str, raiz_raw: Path = RAW_DATA_DIR) -> Path:
    """Pasta dos dicionários do conjunto: ``<raiz>/<subpasta do conjunto>/_dicionarios``."""
    return Path(raiz_raw) / CONJUNTOS_PIPELINE[conjunto] / DIRETORIO_DICIONARIOS


def selecionar_dicionarios(metadados: Dict[str, Any]) -> List[RecursoONS]:
    """Recursos de formato PDF ou JSON cujo nome, sem acentos, contém "dicionario"."""
    selecionados = []
    for r in metadados.get("result", {}).get("resources", []):
        formato = (r.get("format") or "").strip().upper()
        nome = (r.get("name") or "").strip()
        if formato in FORMATOS_DICIONARIO and "DICIONARIO" in _sem_acento(nome).upper():
            selecionados.append(RecursoONS(
                id_recurso=(r.get("id") or "").strip(),
                nome_recurso=nome,
                url_download=(r.get("url") or "").strip(),
                formato=formato,
                tamanho_bytes=int(r.get("size") or 0),
                ultima_modificacao=(r.get("last_modified") or r.get("metadata_modified") or r.get("created") or "").strip(),
            ))
    return selecionados


def _agora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def sincronizar_dicionarios(conjuntos: Iterable[str], raiz_raw: Path = RAW_DATA_DIR) -> List[Dict[str, Any]]:
    """Obtém os dicionários dos conjuntos e devolve o resultado de cada arquivo (nunca levanta exceção)."""
    resultados: List[Dict[str, Any]] = []
    for conjunto in conjuntos:
        pasta = pasta_dicionarios(conjunto, raiz_raw)
        pasta.mkdir(parents=True, exist_ok=True)
        manifesto_path = pasta / RAW_MANIFEST_FILE.name
        manifesto = load_manifest(manifesto_path)
        agora = _agora()
        try:
            recursos = selecionar_dicionarios(fetch_ckan_package_metadata(f"{ONS_CKAN_PACKAGE_SHOW_URL}{conjunto}"))
        except Exception as exc:
            logger.warning("Dicionários de %s: catálogo indisponível (%s); cópias locais mantidas.", conjunto, exc)
            manifesto[CHAVE_CONSULTA] = {"obtido_em_utc": agora, "formatos_publicados": [], "falha": str(exc)}
            for nome, entrada in manifesto.items():
                if nome != CHAVE_CONSULTA and isinstance(entrada, dict):
                    entrada.update(resultado_ultima_obtencao="FALHA", obtido_em_utc=agora)
            save_manifest(manifesto, manifesto_path)
            resultados += [{"conjunto": conjunto, "formato": f, "arquivo": "", "resultado": "FALHA"}
                           for f in FORMATOS_DICIONARIO]
            continue

        manifesto[CHAVE_CONSULTA] = {"obtido_em_utc": agora,
                                     "formatos_publicados": sorted({r.formato for r in recursos}), "falha": ""}
        try:
            for recurso in recursos:
                nome = _local_filename(recurso)
                local = pasta / nome
                antes = _sha256(local) if local.exists() else None
                try:
                    download_resource(recurso, destination_dir=pasta, force=True, manifest=manifesto)
                    depois: Optional[str] = _sha256(local)
                    resultado = "NOVO" if antes is None else ("INALTERADO" if antes == depois else "ALTERADO")
                except Exception as exc:
                    depois, resultado = antes, "FALHA"
                    logger.warning("Dicionário %s de %s não obtido (%s); cópia local mantida.", nome, conjunto, exc)
                entrada = manifesto.setdefault(nome, {})
                entrada.update(conjunto=conjunto, formato=recurso.formato, resultado_ultima_obtencao=resultado,
                               obtido_em_utc=agora)
                if depois:
                    entrada["sha256"] = depois
                if resultado == "ALTERADO":
                    logger.warning("Dicionário %s de %s mudou; versão anterior preservada em %s/.", nome, conjunto,
                                   "_versoes_anteriores")
                resultados.append({"conjunto": conjunto, "formato": recurso.formato, "arquivo": nome,
                                   "resultado": resultado})
        finally:
            save_manifest(manifesto, manifesto_path)
        faltam = set(FORMATOS_DICIONARIO) - {r.formato for r in recursos}
        if faltam:
            logger.warning("Dicionários de %s: formato(s) não publicado(s) no catálogo: %s", conjunto, sorted(faltam))
    contagem: Dict[str, int] = {}
    for r in resultados:
        contagem[r["resultado"]] = contagem.get(r["resultado"], 0) + 1
    logger.info("Dicionários de dados: %s", contagem)
    return resultados


def montar_registro(raiz_raw: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Registro de todos os conjuntos do pipeline, montado a partir dos manifestos (uma linha por formato)."""
    linhas = []
    for conjunto in CONJUNTOS_PIPELINE:
        pasta = pasta_dicionarios(conjunto, raiz_raw)
        manifesto = load_manifest(pasta / RAW_MANIFEST_FILE.name)
        consulta = manifesto.get(CHAVE_CONSULTA) or {}
        por_formato = {e.get("formato"): (nome, e) for nome, e in manifesto.items()
                       if nome != CHAVE_CONSULTA and isinstance(e, dict) and e.get("formato")}
        for formato in FORMATOS_DICIONARIO:
            linha: Dict[str, Any] = {c: "" for c in COLUNAS_REGISTRO}
            linha.update(conjunto=conjunto, pasta=str(Path(CONJUNTOS_PIPELINE[conjunto]) / DIRETORIO_DICIONARIOS).replace("\\", "/"),
                         formato=formato, versoes_anteriores=0, tamanho_bytes=0)
            if formato in por_formato:
                nome, e = por_formato[formato]
                anteriores = e.get("versoes_anteriores") or []
                linha.update(
                    arquivo=nome, url=e.get("url", ""), resultado_ultima_obtencao=e.get("resultado_ultima_obtencao", ""),
                    obtido_em_utc=e.get("obtido_em_utc", ""), sha256=e.get("sha256", ""),
                    tamanho_bytes=int(e.get("tamanho_bytes") or 0), versoes_anteriores=len(anteriores),
                    ultima_versao_anterior=anteriores[-1].get("arquivo_preservado", "") if anteriores else "",
                )
            elif not consulta:
                linha.update(resultado_ultima_obtencao="NAO_OBTIDO")
            elif consulta.get("falha"):
                linha.update(resultado_ultima_obtencao="FALHA", obtido_em_utc=consulta.get("obtido_em_utc", ""))
            else:
                linha.update(resultado_ultima_obtencao="NAO_PUBLICADO", obtido_em_utc=consulta.get("obtido_em_utc", ""))
            linhas.append(linha)
    return pd.DataFrame(linhas, columns=COLUNAS_REGISTRO)


def exportar_registro(raiz_raw: Path = RAW_DATA_DIR, pasta_saida: Path = PROCESSED_DATA_DIR) -> pd.DataFrame:
    """Grava ``relatorio_dicionarios_ons.csv`` (via persistência, com cópia da versão anterior)."""
    registro = montar_registro(raiz_raw)
    gravar_csv(registro, Path(pasta_saida) / DICIONARIOS_REGISTRO_FILE.name)
    return registro


def atualizar_dicionarios(
    conjuntos: Iterable[str],
    raiz_raw: Path = RAW_DATA_DIR,
    pasta_saida: Path = PROCESSED_DATA_DIR,
) -> None:
    """Obtém os dicionários e regrava o registro; usada dentro das etapas de coleta e nunca as interrompe."""
    try:
        sincronizar_dicionarios(list(conjuntos), raiz_raw)
        exportar_registro(raiz_raw, pasta_saida)
    except Exception as exc:
        logger.warning("Dicionários de dados não atualizados (%s); a coleta continua.", exc)


def carregar_registro(pasta: Path = PROCESSED_DATA_DIR) -> Optional[pd.DataFrame]:
    """Registro gravado; None se os dicionários ainda não foram obtidos."""
    caminho = Path(pasta) / DICIONARIOS_REGISTRO_FILE.name
    if not caminho.exists():
        return None
    return pd.read_csv(caminho, sep=";", keep_default_na=False)


def executar_dicionarios_ons(
    conjuntos: Optional[Iterable[str]] = None,
    pasta_raw: Path = RAW_DATA_DIR,
    pasta_saida: Path = PROCESSED_DATA_DIR,
) -> int:
    """Obtém os dicionários (padrão: os 10 conjuntos) e grava o registro. Falhas de obtenção não mudam o código."""
    try:
        sincronizar_dicionarios(list(conjuntos or CONJUNTOS_PIPELINE), pasta_raw)
        exportar_registro(pasta_raw, pasta_saida)
        return 0
    except Exception as exc:
        logger.exception("Erro ao registrar os dicionários de dados: %s", exc)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Dicionários de dados (PDF e JSON) dos conjuntos do ONS usados no pipeline.")
    parser.add_argument("--conjuntos", nargs="*", choices=list(CONJUNTOS_PIPELINE), default=None,
                        help="Conjuntos a consultar (padrão: os 10 do pipeline).")
    parser.add_argument("--log-level", choices=NIVEIS_LOG, default="INFO", help="Nível de log de todos os módulos.")
    args = parser.parse_args()
    configurar_nivel_log(args.log_level)
    sys.exit(executar_dicionarios_ons(args.conjuntos))


if __name__ == "__main__":
    main()
