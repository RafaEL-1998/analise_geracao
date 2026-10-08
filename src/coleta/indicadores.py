"""Indicadores de disponibilidade por unidade geradora e taxas TEIFa e TEIP na Coleta de dados (FR-042).

Quatro conjuntos do Portal de Dados Abertos do ONS, com a usina localizada pelo CEG (FR-034 a FR-036):

- ind_disponibilidade_fgeracao_uge_mensal e _anual: DISPF, INDISPPF, INDISPFF, DMDFF, FDFF e TDFF por unidade
  geradora (Submódulo 9.2 dos Procedimentos de Rede), conferidos pelo id ONS (``id_usina``);
- taxa_teif_teip_parametro: horas mensais de cada unidade geradora por estado operativo;
- taxa_teif_teip: TEIFa e TEIP da usina (janela de 60 meses).

Os dois conjuntos de taxas não publicam o id ONS: a extração usa só o CEG. As colunas ficam como publicadas (texto sem
espaços nas pontas); a conversão em número, a escolha da versão mais recente e o recorte do período são do Tratamento
de dados. Os arquivos brutos ficam em ``data/raw/indicadores_ons/<conjunto>/``, cada conjunto com seu manifesto.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.coleta.catalogo import (
    _local_filename,
    download_resource,
    fetch_ckan_package_metadata,
    load_manifest,
    parse_ckan_resources,
    save_manifest,
)
from src.coleta.conjuntos import Regra, _corresponde, avisar_linhas_irregulares, ler_csv_texto
from src.comum.caminhos import RAW_MANIFEST_FILE
from src.comum.logger import setup_logger
from src.comum.modelos import RecursoONS
from src.comum.regras import CONJUNTOS_INDICADORES_ONS, ONS_CKAN_PACKAGE_SHOW_URL

logger = setup_logger("coleta")

MENSAL = "ind_disponibilidade_fgeracao_uge_mensal"
ANUAL = "ind_disponibilidade_fgeracao_uge_anual"
PARAMETROS = "taxa_teif_teip_parametro"
TAXAS = "taxa_teif_teip"

# Coluna que traz o CEG em cada conjunto e, nos indicadores por unidade geradora, a do id ONS (conferência)
COLUNA_CEG: Dict[str, str] = {MENSAL: "ceg", ANUAL: "ceg", PARAMETROS: "cod_ceg", TAXAS: "cod_ceg"}
COLUNA_CONFERENCIA: Dict[str, str] = {MENSAL: "id_usina", ANUAL: "id_usina"}
COLUNA_CONJUNTO = "conjunto"

COLUNAS_AUDITORIA_INDICADORES: List[str] = [
    "conjunto", "arquivo", "formato", "periodo", "data_publicacao", "obtido", "linhas_lidas",
    "linhas_formato_irregular", "linhas_usina", "linhas_so_identificador", "linhas_so_conferencia", "status", "mensagem",
]

_RE_ANO_ARQUIVO = re.compile(r"_(\d{4})\.csv$", re.IGNORECASE)


def url_pacote(conjunto: str) -> str:
    return f"{ONS_CKAN_PACKAGE_SHOW_URL}{conjunto}"


def ano_do_arquivo(nome: str) -> Optional[int]:
    """Ano no nome do arquivo (ex.: ..._MENSAL_2024.csv); None para arquivos únicos."""
    achado = _RE_ANO_ARQUIVO.search(nome)
    return int(achado.group(1)) if achado else None


def ano_do_recurso(recurso: RecursoONS) -> Optional[int]:
    return ano_do_arquivo(recurso.url_download.split("/")[-1].split("?")[0])


def selecionar_recursos(recursos: List[RecursoONS], ano_inicio: int, ano_fim: int) -> List[RecursoONS]:
    """Mantém os arquivos anuais dentro do período e os arquivos únicos (sem ano no nome)."""
    selecionados = []
    for r in recursos:
        ano = ano_do_recurso(r)
        if ano is None or ano_inicio <= ano <= ano_fim:
            selecionados.append(r)
    return selecionados


def sincronizar_indicadores(
    ano_inicio: int,
    ano_fim: int,
    destino: Path,
    force: bool = False,
) -> List[Dict[str, Any]]:
    """Baixa os CSVs dos quatro conjuntos que cobrem os anos informados (cache por versão).

    Catálogo inacessível levanta exceção (código 1). Um arquivo não obtido não interrompe os demais: volta como falha,
    no formato das linhas de auditoria (FR-026).
    """
    falhas: List[Dict[str, Any]] = []
    for conjunto in CONJUNTOS_INDICADORES_ONS:
        pasta = Path(destino) / conjunto
        pasta.mkdir(parents=True, exist_ok=True)
        recursos = selecionar_recursos(
            parse_ckan_resources(fetch_ckan_package_metadata(url_pacote(conjunto))), ano_inicio, ano_fim
        )
        manifesto_path = pasta / RAW_MANIFEST_FILE.name
        manifesto = load_manifest(manifesto_path)
        try:
            for idx, r in enumerate(recursos, start=1):
                logger.info("[%s %d/%d] Sincronizando %s", conjunto, idx, len(recursos), r.nome_recurso)
                try:
                    download_resource(r, destination_dir=pasta, force=force, manifest=manifesto)
                except Exception as exc:  # o arquivo vai para a auditoria como FALHA
                    nome = _local_filename(r)
                    logger.error("%s: falha ao obter %s: %s", conjunto, nome, exc)
                    ano = ano_do_arquivo(nome)
                    falhas.append({"conjunto": conjunto, "arquivo": nome, "formato": "CSV",
                                   "periodo": "" if ano is None else f"{ano:04d}", "status": "FALHA",
                                   "mensagem": str(exc)})
        finally:
            save_manifest(manifesto, manifesto_path)
    return falhas


def filtrar_csv(caminho: Path, conjunto: str, ceg: str, id_ons: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Linhas da usina num CSV do conjunto (todas as colunas, texto sem espaços nas pontas) e a auditoria do arquivo.

    A usina é localizada pelo CEG e, nos indicadores por unidade geradora, conferida pelo id ONS; as linhas que
    conferem só em parte não são extraídas e são contadas (nas taxas, as contagens parciais não se aplicam).
    """
    coluna = COLUNA_CEG[conjunto]
    conferencia = COLUNA_CONFERENCIA.get(conjunto)
    ano = ano_do_arquivo(caminho.name)
    auditoria: Dict[str, Any] = {
        "conjunto": conjunto, "arquivo": caminho.name, "formato": "CSV", "periodo": "" if ano is None else f"{ano:04d}",
        "data_publicacao": "", "obtido": True, "linhas_lidas": 0, "linhas_formato_irregular": 0, "linhas_usina": 0,
        "linhas_so_identificador": 0 if conferencia else pd.NA, "linhas_so_conferencia": 0 if conferencia else pd.NA,
        "status": "PROCESSADO", "mensagem": "",
    }
    try:
        bruto, irregulares = ler_csv_texto(caminho)
        bruto.columns = [c.strip() for c in bruto.columns]
        auditoria.update(linhas_lidas=len(bruto) + len(irregulares), linhas_formato_irregular=len(irregulares))
        avisar_linhas_irregulares(conjunto, caminho.name, irregulares)
        faltantes = [c for c in (coluna, conferencia) if c and c not in bruto.columns]
        if faltantes:
            raise ValueError(f"colunas ausentes no arquivo: {faltantes}")
    except Exception as exc:  # arquivo corrompido, vazio ou sem as colunas de identificação
        logger.error("%s: não foi possível ler %s: %s", conjunto, caminho.name, exc)
        auditoria.update(status="FALHA", mensagem=str(exc))
        return pd.DataFrame(), auditoria

    ident = _corresponde(bruto, Regra(coluna, ceg))
    conf = _corresponde(bruto, Regra(conferencia, id_ons)) if conferencia else pd.Series(True, index=bruto.index)
    if conferencia:
        auditoria.update(linhas_so_identificador=int((ident & ~conf).sum()),
                         linhas_so_conferencia=int((~ident & conf).sum()))
        if auditoria["linhas_so_identificador"] or auditoria["linhas_so_conferencia"]:
            logger.warning("%s: arquivo %s com linhas que conferem só em parte (só CEG: %d; só id ONS: %d); "
                           "verificar mudança de cadastro no ONS.", conjunto, caminho.name,
                           auditoria["linhas_so_identificador"], auditoria["linhas_so_conferencia"])
    linhas = bruto[ident & conf].copy()
    for c in linhas.columns:
        linhas[c] = linhas[c].str.strip()
    linhas["arquivo_origem"] = caminho.name
    auditoria["linhas_usina"] = len(linhas)
    if not len(linhas):
        auditoria["status"] = "SEM_REGISTROS"
    return linhas, auditoria


def arquivos_locais(conjunto: str, pasta_raiz: Path, ano_inicio: int, ano_fim: int) -> List[Path]:
    """CSVs da pasta do conjunto (sem subpastas) dos anos do período e os arquivos únicos, em ordem de nome."""
    pasta = Path(pasta_raiz) / conjunto
    if not pasta.exists():
        return []
    arquivos = []
    for caminho in sorted(pasta.glob("*.csv")):
        ano = ano_do_arquivo(caminho.name)
        if caminho.is_file() and (ano is None or ano_inicio <= ano <= ano_fim):
            arquivos.append(caminho)
    return arquivos


def extrair_indicadores(
    pasta_raiz: Path,
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
    ceg: str,
    id_ons: str,
    falhas: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Linhas da usina nos quatro conjuntos, com o conjunto de origem, e a auditoria (uma linha por arquivo).

    Os conjuntos são lidos na ordem do pipeline e os arquivos em ordem de nome; os não obtidos entram na auditoria.
    """
    partes: List[pd.DataFrame] = []
    auditorias: List[Dict[str, Any]] = []
    for conjunto in CONJUNTOS_INDICADORES_ONS:
        manifesto = load_manifest(Path(pasta_raiz) / conjunto / RAW_MANIFEST_FILE.name)
        arquivos = arquivos_locais(conjunto, pasta_raiz, pd.Timestamp(inicio).year, pd.Timestamp(fim).year)
        linhas_usina = 0
        for caminho in arquivos:
            linhas, auditoria = filtrar_csv(caminho, conjunto, ceg, id_ons)
            auditoria["data_publicacao"] = (manifesto.get(caminho.name) or {}).get("ultima_modificacao") or ""
            auditorias.append(auditoria)
            linhas_usina += int(auditoria["linhas_usina"])
            if len(linhas):
                linhas.insert(0, COLUNA_CONJUNTO, conjunto)
                partes.append(linhas)
        logger.info("%s: %d arquivos lidos, %d linhas da usina.", conjunto, len(arquivos), linhas_usina)
    auditorias += [{**f, "obtido": False} for f in (falhas or [])]
    auditoria = pd.DataFrame(auditorias, columns=COLUNAS_AUDITORIA_INDICADORES)
    for coluna in ("linhas_lidas", "linhas_formato_irregular", "linhas_usina"):
        auditoria[coluna] = pd.to_numeric(auditoria[coluna], errors="coerce").fillna(0).astype(int)
    for coluna in ("linhas_so_identificador", "linhas_so_conferencia"):
        auditoria[coluna] = pd.to_numeric(auditoria[coluna], errors="coerce").astype("Int64")
    for coluna in ("periodo", "data_publicacao", "mensagem"):
        auditoria[coluna] = auditoria[coluna].fillna("")
    auditoria["obtido"] = auditoria["obtido"].astype(bool)
    extraido = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=[COLUNA_CONJUNTO])
    return extraido, auditoria


def separar_conjuntos(extraido: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Linhas extraídas de cada conjunto, só com as colunas publicadas nele (vazio se o conjunto não teve linhas)."""
    tabelas: Dict[str, pd.DataFrame] = {}
    for conjunto in CONJUNTOS_INDICADORES_ONS:
        if extraido.empty or COLUNA_CONJUNTO not in extraido.columns:
            tabelas[conjunto] = pd.DataFrame()
            continue
        parte = extraido[extraido[COLUNA_CONJUNTO] == conjunto].drop(columns=COLUNA_CONJUNTO)
        tabelas[conjunto] = parte.dropna(axis=1, how="all").reset_index(drop=True) if len(parte) else pd.DataFrame()
    return tabelas
