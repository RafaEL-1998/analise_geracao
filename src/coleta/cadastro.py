"""Ficha cadastral da usina no ONS na Coleta de dados: modalidade de operação, centro de operação e ponto de conexão.

Conjunto "modalidade-usina" (FR-045): um único arquivo, sem série histórica (o ONS o regrava diariamente). A ficha é
localizada pelo CEG do perfil; o id ONS e o estado diferentes do perfil não excluem a linha, que é extraída e examinada
pela Conferência (FR-036), assim como a potência autorizada. Os homônimos são contados, não extraídos. As versões
anteriores do cadastro ficam preservadas pelo catálogo, o que dá o histórico.

A leitura tem auditoria própria (FR-046): linhas lidas, linhas de formato irregular (não extraídas e avisadas no log),
linhas com o CEG do perfil, identificação parcial e situação.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from src.coleta.catalogo import _local_filename, download_resource, fetch_ckan_package_metadata, load_manifest, save_manifest
from src.coleta.conjuntos import _normalizar, avisar_linhas_irregulares, ler_csv_texto, numero_publicado
from src.coleta.registro import normalizar_texto
from src.comum.caminhos import RAW_MANIFEST_FILE
from src.comum.formatacao import fmt_num
from src.comum.logger import setup_logger
from src.comum.modelos import RecursoONS
from src.comum.regras import CONJUNTO_CADASTRO, ONS_CKAN_PACKAGE_SHOW_URL

logger = setup_logger("coleta")

COLUNAS_FICHA: List[str] = [
    "nom_usina", "ceg", "id_ons", "nom_modalidadeoperacao", "sgl_centrooperacao", "nom_pontoconexao",
    "val_potenciaautorizada", "id_estado", "sts_aneel", "data_consulta_utc", "arquivo_origem", "homonimos",
    "linhas_so_identificador", "linhas_so_conferencia", "linhas_ceg",
]
COLUNAS_AUDITORIA_CADASTRO: List[str] = [
    "arquivo", "formato", "data_publicacao", "obtido", "linhas_lidas", "linhas_formato_irregular", "linhas_usina",
    "linhas_so_identificador", "linhas_so_conferencia", "status", "mensagem",
]
COLUNAS_OBRIGATORIAS: Tuple[str, ...] = ("nom_usina", "ceg", "id_ons", "id_estado")


def selecionar_recurso(metadados: Dict[str, Any]) -> Optional[RecursoONS]:
    """Recurso CSV do cadastro (o dicionário de dados é tratado em ``src.coleta.dicionarios``)."""
    for r in metadados.get("result", {}).get("resources", []):
        formato = (r.get("format") or "").strip().upper()
        nome = (r.get("name") or "").strip()
        if formato == "CSV" and "DICIONARIO" not in _normalizar(pd.Series([nome])).iloc[0]:
            return RecursoONS(
                id_recurso=(r.get("id") or "").strip(), nome_recurso=nome, url_download=(r.get("url") or "").strip(),
                formato="CSV", tamanho_bytes=int(r.get("size") or 0),
                ultima_modificacao=(r.get("last_modified") or r.get("metadata_modified") or r.get("created") or "").strip(),
            )
    return None


def sincronizar_cadastro(pasta_raw: Path, force: bool = False) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    """Baixa o cadastro se a versão publicada mudou; devolve o nome do arquivo e as falhas de download.

    Catálogo inacessível levanta exceção (código 1). Sem recurso CSV no catálogo, o nome volta None.
    """
    pasta_raw = Path(pasta_raw)
    pasta_raw.mkdir(parents=True, exist_ok=True)
    recurso = selecionar_recurso(fetch_ckan_package_metadata(f"{ONS_CKAN_PACKAGE_SHOW_URL}{CONJUNTO_CADASTRO}"))
    if recurso is None:
        logger.error("Cadastro de modalidade das usinas: nenhum recurso CSV publicado no catálogo.")
        return None, []
    nome = _local_filename(recurso)
    manifesto_path = pasta_raw / RAW_MANIFEST_FILE.name
    manifesto = load_manifest(manifesto_path)
    falhas: List[Dict[str, Any]] = []
    try:
        download_resource(recurso, destination_dir=pasta_raw, force=force, manifest=manifesto)
    except Exception as exc:
        logger.error("Cadastro de modalidade das usinas não obtido (%s); a cópia local, se houver, será lida.", exc)
        falhas.append({"arquivo": nome, "formato": "CSV", "status": "FALHA", "mensagem": str(exc)})
    finally:
        save_manifest(manifesto, manifesto_path)
    return nome, falhas


def ler_cadastro(caminho: Path) -> Tuple[pd.DataFrame, List[int]]:
    """Cadastro completo, com textos sem espaços nas pontas, e os números das linhas de formato irregular.

    O arquivo do ONS completa campos com espaços. Linhas com nº de campos diferente do cabeçalho ficam fora da
    tabela e são avisadas no log; uma linha irregular de outra usina não interrompe a leitura.
    """
    tabela, irregulares = ler_csv_texto(Path(caminho))
    avisar_linhas_irregulares(CONJUNTO_CADASTRO, Path(caminho).name, irregulares)
    tabela.columns = [c.strip() for c in tabela.columns]
    faltantes = [c for c in COLUNAS_OBRIGATORIAS if c not in tabela.columns]
    if faltantes:
        raise ValueError(f"colunas ausentes no cadastro: {faltantes}")
    return tabela.apply(lambda coluna: coluna.str.strip()), irregulares


def _mascaras(cadastro: pd.DataFrame, ceg: str, id_ons: str, estado: str,
              nome_ons: str) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Linhas com o CEG do perfil, linhas com a conferência (id ONS e estado) e homônimos (nome sem o CEG)."""
    alvo = normalizar_texto(nome_ons)
    com_ceg = _normalizar(cadastro["ceg"]) == normalizar_texto(ceg)
    conferencia = ((_normalizar(cadastro["id_ons"]) == normalizar_texto(id_ons))
                   & (_normalizar(cadastro["id_estado"]) == normalizar_texto(estado)))
    homonimos = _normalizar(cadastro["nom_usina"]).str.contains(alvo, regex=False) & ~com_ceg
    return com_ceg, conferencia, homonimos


def auditoria_cadastro(
    arquivo: str,
    ceg: str,
    id_ons: str,
    estado: str,
    nome_ons: str,
    cadastro: Optional[pd.DataFrame] = None,
    irregulares: Iterable[int] = (),
    erro: str = "",
    data_publicacao: str = "",
) -> Dict[str, Any]:
    """Auditoria da leitura do cadastro (uma linha).

    ``linhas_usina`` conta as linhas com o CEG do perfil, que localiza a ficha; mais de uma indica CEG repetido. Sem
    ``cadastro`` (arquivo que não pôde ser lido), a situação é ``FALHA``; sem o CEG no arquivo, ``SEM_REGISTROS``.
    """
    irregulares = list(irregulares)
    linha: Dict[str, Any] = {
        "arquivo": arquivo, "formato": "CSV", "data_publicacao": data_publicacao, "obtido": True, "linhas_lidas": 0,
        "linhas_formato_irregular": len(irregulares), "linhas_usina": 0, "linhas_so_identificador": 0,
        "linhas_so_conferencia": 0, "status": "FALHA", "mensagem": erro,
    }
    if cadastro is not None:
        com_ceg, conferencia, _ = _mascaras(cadastro, ceg, id_ons, estado, nome_ons)
        linha.update(
            linhas_lidas=len(cadastro) + len(irregulares), linhas_usina=int(com_ceg.sum()),
            linhas_so_identificador=int((com_ceg & ~conferencia).sum()),
            linhas_so_conferencia=int((~com_ceg & conferencia).sum()),
            status="PROCESSADO" if com_ceg.any() else "SEM_REGISTROS",
        )
    return linha


def extrair_ficha(cadastro: pd.DataFrame, data_consulta: str, arquivo: str, ceg: str, id_ons: str, estado: str,
                  nome_ons: str) -> pd.DataFrame:
    """Ficha da usina (uma linha, a primeira com o CEG do perfil) com homônimos e contagens; vazia sem o CEG."""
    com_ceg, conferencia, homonimos = _mascaras(cadastro, ceg, id_ons, estado, nome_ons)
    if not com_ceg.any():
        return pd.DataFrame(columns=COLUNAS_FICHA)
    linha = cadastro[com_ceg].iloc[0]
    ficha = {coluna: linha.get(coluna, "") for coluna in COLUNAS_FICHA}
    ficha.update(
        val_potenciaautorizada=numero_publicado(pd.Series([linha.get("val_potenciaautorizada", "")])).iloc[0],
        data_consulta_utc=data_consulta, arquivo_origem=arquivo, homonimos=int(homonimos.sum()),
        linhas_so_identificador=int((com_ceg & ~conferencia).sum()),
        linhas_so_conferencia=int((~com_ceg & conferencia).sum()), linhas_ceg=int(com_ceg.sum()),
    )
    return pd.DataFrame([ficha], columns=COLUNAS_FICHA)


def arquivo_local(pasta_raw: Path, nome: Optional[str] = None) -> Optional[str]:
    """Nome do arquivo do cadastro na pasta: o informado, se existir, ou o primeiro CSV em ordem de nome."""
    pasta_raw = Path(pasta_raw)
    if nome and (pasta_raw / nome).is_file():
        return nome
    locais = sorted(p.name for p in pasta_raw.glob("*.csv") if p.is_file()) if pasta_raw.exists() else []
    return locais[0] if locais else None


def extrair_cadastro(
    pasta_raw: Path,
    ceg: str,
    id_ons: str,
    estado: str,
    nome_ons: str,
    nome: Optional[str] = None,
    falhas: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Ficha da usina e auditoria da leitura do cadastro local (mais as falhas de download, se houver).

    A data da consulta é a de obtenção do arquivo, pelo manifesto. Sem arquivo local, a ficha fica vazia.
    """
    pasta_raw = Path(pasta_raw)
    linhas: List[Dict[str, Any]] = []
    ficha = pd.DataFrame(columns=COLUNAS_FICHA)
    nome = arquivo_local(pasta_raw, nome)
    if nome is None:
        logger.error("Cadastro de modalidade das usinas indisponível em %s.", pasta_raw)
    else:
        entrada = load_manifest(pasta_raw / RAW_MANIFEST_FILE.name).get(nome) or {}
        publicacao = str(entrada.get("ultima_modificacao") or "")
        try:
            cadastro, irregulares = ler_cadastro(pasta_raw / nome)
        except Exception as exc:
            logger.error("Cadastro de modalidade das usinas: não foi possível ler %s: %s", nome, exc)
            linhas.append(auditoria_cadastro(nome, ceg, id_ons, estado, nome_ons, erro=str(exc),
                                             data_publicacao=publicacao))
        else:
            ficha = extrair_ficha(cadastro, str(entrada.get("registrado_em_utc", "")), nome, ceg, id_ons, estado,
                                  nome_ons)
            linhas.append(auditoria_cadastro(nome, ceg, id_ons, estado, nome_ons, cadastro, irregulares,
                                             data_publicacao=publicacao))
    linhas += [{**f, "data_publicacao": "", "obtido": False} for f in (falhas or [])]
    auditoria = pd.DataFrame(linhas, columns=COLUNAS_AUDITORIA_CADASTRO)
    for coluna in ("linhas_lidas", "linhas_formato_irregular", "linhas_usina", "linhas_so_identificador",
                   "linhas_so_conferencia"):
        auditoria[coluna] = pd.to_numeric(auditoria[coluna], errors="coerce").fillna(0).astype(int)
    auditoria["obtido"] = auditoria["obtido"].astype(bool)
    if len(ficha):
        f = ficha.iloc[0]
        logger.info("Ficha cadastral: %s · %s · %s · %s · %s MW · %d homônimos.", f["nom_usina"],
                    f["nom_modalidadeoperacao"], f["sgl_centrooperacao"], f["nom_pontoconexao"],
                    fmt_num(f["val_potenciaautorizada"], 1), f["homonimos"])
    elif nome is not None and not (auditoria["status"] == "FALHA").any():
        logger.error("A usina (CEG %s) não consta do cadastro de modalidade das usinas do ONS.", ceg)
    return ficha, auditoria
