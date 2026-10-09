"""Programação diária do ONS na Coleta de dados (FR-043).

Conjunto "Dados dos Valores da Programação Diária": um arquivo por dia (desde 01/10/2024) com a geração programada de
cada usina em 48 patamares de 30 minutos. A coleta obtém os arquivos dos dias do período da base de EVT e extrai os
patamares da usina, identificada pelo código de exibição e conferida pelo nome e pelo estado (FR-034). A conversão dos
patamares em horas, o recorte do período e a lista dos dias sem arquivo são do Tratamento de dados.

Limites do dado: é a programação do dia (não registra reprogramações em tempo real) e, para usinas hidráulicas, os
campos de motivo (ordem de mérito, inflexibilidade, razão elétrica) e a disponibilidade programada vêm vazios ou zerados.
"""

from __future__ import annotations

import concurrent.futures
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from src.coleta.catalogo import (
    _local_filename,
    download_resource,
    escolher_entre_repetidos,
    fetch_ckan_package_metadata,
    load_manifest,
    parse_ckan_resources,
    registrar_repetidos,
    save_manifest,
)
from src.coleta.conjuntos import _normalizar, numero_publicado
from src.coleta.indicadores import url_pacote
from src.coleta.registro import normalizar_texto
from src.comum.caminhos import RAW_MANIFEST_FILE
from src.comum.logger import setup_logger
from src.comum.modelos import RecursoONS
from src.comum.regras import CONJUNTO_PROGRAMACAO_DIARIA, FORMATO_PROGRAMACAO_DIARIA, PATAMARES_POR_DIA

logger = setup_logger("coleta")

_RE_DATA_ARQUIVO = re.compile(r"_(\d{4})_(\d{2})_(\d{2})\.", re.IGNORECASE)
_RE_DATA_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
_RE_DATA_BR = re.compile(r"^(\d{2})/(\d{2})/(\d{4})")
COLUNAS_LIDAS = ["din_programacaodia", "num_patamar", "cod_exibicaousina", "nom_usina", "id_estado", "val_geracaoprogramada"]
COLUNAS_EXTRAIDAS = ["dia", "num_patamar", "geracao_programada_mw", "arquivo_origem"]
DOWNLOADS_SIMULTANEOS = 8

# Auditoria: uma linha por dia do período com arquivo publicado, lido ou não obtido
COLUNAS_AUDITORIA_PROGRAMACAO: List[str] = [
    "arquivo", "dia", "formato", "data_publicacao", "obtido", "linhas_lidas", "linhas_usina",
    "linhas_codigo_sem_conferencia", "linhas_so_conferencia", "valores_invalidos", "patamares", "data_interna_confere",
    "status", "mensagem",
]


# ---------------------------------------------------------------------------
# Datas e seleção de arquivos
# ---------------------------------------------------------------------------


def dia_do_arquivo(nome_arquivo: str) -> Optional[pd.Timestamp]:
    """Dia em nomes como PROGRAMACAO_DIARIA_2026_07_01.parquet."""
    achado = _RE_DATA_ARQUIVO.search(nome_arquivo)
    if not achado:
        return None
    ano, mes, dia = (int(g) for g in achado.groups())
    return pd.Timestamp(ano, mes, dia)


def data_interna_confere(valores: pd.Series, dia: pd.Timestamp) -> bool:
    """Confere a coluna din_programacaodia, publicada como AAAA-MM-DD ou DD/MM/AAAA."""
    for valor in pd.Series(valores).astype(str).str.strip().unique():
        iso = _RE_DATA_ISO.match(valor)
        br = _RE_DATA_BR.match(valor)
        if iso:
            data = pd.Timestamp(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
        elif br:
            data = pd.Timestamp(int(br.group(3)), int(br.group(2)), int(br.group(1)))
        else:
            return False
        if data != dia:
            return False
    return True


def selecionar_recursos_periodo(recursos: List[RecursoONS], inicio: pd.Timestamp, fim: pd.Timestamp) -> List[RecursoONS]:
    """Recursos diários cujo dia está entre o dia de ``inicio`` e o de ``fim``."""
    d0, d1 = pd.Timestamp(inicio).normalize(), pd.Timestamp(fim).normalize()
    selecionados = []
    for r in recursos:
        dia = dia_do_arquivo(r.url_download.split("/")[-1])
        if dia is not None and d0 <= dia <= d1:
            selecionados.append(r)
    return selecionados


def sincronizar_programacao(
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
    destino: Path,
    force: bool = False,
) -> List[Dict[str, Any]]:
    """Baixa (ou reaproveita, se a versão local for a publicada) os arquivos diários do período.

    Catálogo inacessível levanta exceção (código 1); os arquivos não obtidos voltam como falhas, no formato das linhas
    de auditoria (FR-026).
    """
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    metadados = fetch_ckan_package_metadata(url_pacote(CONJUNTO_PROGRAMACAO_DIARIA))
    recursos, duplicados = escolher_entre_repetidos(
        selecionar_recursos_periodo(parse_ckan_resources(metadados, FORMATO_PROGRAMACAO_DIARIA), inicio, fim),
        "Programação diária")
    manifesto_path = destino / RAW_MANIFEST_FILE.name
    manifesto = load_manifest(manifesto_path)
    logger.info("Programação diária: %d arquivos publicados no período.", len(recursos))
    falhas: List[Dict[str, Any]] = []

    def baixar(recurso: RecursoONS) -> None:
        try:
            download_resource(recurso, destination_dir=destino, force=force, manifest=manifesto)
        except Exception as exc:  # cada arquivo é tentado; a falha vai para a auditoria
            nome = _local_filename(recurso)
            logger.error("Programação diária: falha ao obter %s: %s", nome, exc)
            falhas.append({"arquivo": nome, "dia": dia_do_arquivo(nome), "formato": FORMATO_PROGRAMACAO_DIARIA,
                           "status": "FALHA", "mensagem": str(exc)})

    try:
        with concurrent.futures.ThreadPoolExecutor(DOWNLOADS_SIMULTANEOS) as executor:
            list(executor.map(baixar, recursos))
    finally:
        registrar_repetidos(manifesto, duplicados)
        save_manifest(manifesto, manifesto_path)
    resumo: Dict[str, int] = {}
    for r in recursos:
        resumo[r.status_sincronizacao] = resumo.get(r.status_sincronizacao, 0) + 1
    logger.info("Sincronização da programação concluída: %s", resumo)
    return sorted(falhas, key=lambda f: f["arquivo"])


# ---------------------------------------------------------------------------
# Leitura e extração
# ---------------------------------------------------------------------------


def _igual(coluna: pa.ChunkedArray, valor: str) -> pa.ChunkedArray:
    """Linhas cujo valor normalizado é o de ``valor`` (correção P3), pelo filtro do pyarrow.

    A normalização é feita uma vez por valor distinto da coluna; o filtro usa os valores publicados que conferem.
    """
    texto = pc.cast(coluna, pa.string())
    alvo = normalizar_texto(valor)
    conferem = [v for v in pc.unique(texto).to_pylist() if v is not None and normalizar_texto(v) == alvo]
    return pc.is_in(texto, value_set=pa.array(conferem, type=pa.string()))


def _preenchido(serie: pd.Series) -> pd.Series:
    return serie.notna() & (serie.astype(str).str.strip() != "")


def ler_arquivo(caminho: Path, cod_programacao: str, nome_ons: str, estado: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Patamares da usina num arquivo diário e a auditoria do arquivo.

    A usina é identificada pelo código de exibição e conferida pelo nome (contém ``nome_ons``) e pelo estado. Num
    patamar repetido no arquivo prevalece a última ocorrência; sem os 48 patamares, o arquivo fica ``INCOMPLETO``.
    """
    dia = dia_do_arquivo(caminho.name)
    auditoria: Dict[str, Any] = {
        "arquivo": caminho.name, "dia": dia, "formato": FORMATO_PROGRAMACAO_DIARIA, "data_publicacao": "",
        "obtido": True, "mensagem": "",
    }
    vazio = pd.DataFrame(columns=COLUNAS_EXTRAIDAS)
    try:
        tabela = pq.read_table(caminho, columns=COLUNAS_LIDAS)
        # Só as linhas com o código ou com o estado da usina podem conferir em todo ou em parte
        interesse = pc.or_kleene(_igual(tabela["cod_exibicaousina"], cod_programacao),
                                 _igual(tabela["id_estado"], estado))
        bruto = tabela.filter(interesse).to_pandas()
    except Exception as e:  # arquivo corrompido ou sem as colunas esperadas
        logger.error("Falha ao ler %s: %s", caminho.name, e)
        return vazio, {**auditoria, "linhas_lidas": 0, "linhas_usina": 0, "linhas_codigo_sem_conferencia": 0,
                       "linhas_so_conferencia": 0, "valores_invalidos": 0, "patamares": 0,
                       "data_interna_confere": False, "status": "FALHA", "mensagem": str(e)}

    alvo = normalizar_texto(nome_ons)
    codigo = _normalizar(bruto["cod_exibicaousina"]) == normalizar_texto(cod_programacao)
    nomes = bruto["nom_usina"].astype(str)
    contem = {nome: alvo in normalizar_texto(nome) for nome in nomes.unique()}  # um nome por usina, 48 linhas cada
    conferencia = nomes.map(contem).astype(bool) & (_normalizar(bruto["id_estado"]) == normalizar_texto(estado))
    sel = bruto[codigo & conferencia]
    patamares = numero_publicado(sel["num_patamar"]).astype("Int64")
    geracao = numero_publicado(sel["val_geracaoprogramada"])
    invalidos = int((patamares.isna() & _preenchido(sel["num_patamar"])).sum()
                    + (geracao.isna() & _preenchido(sel["val_geracaoprogramada"])).sum())
    linhas = pd.DataFrame({
        "dia": dia,
        "num_patamar": patamares.to_numpy(),
        "geracao_programada_mw": geracao.to_numpy(),
        "arquivo_origem": caminho.name,
    })
    duplicados = int(linhas["num_patamar"].duplicated().sum())
    if duplicados:
        logger.warning("%s: %d patamares repetidos; prevalece a última ocorrência.", caminho.name, duplicados)
        linhas = linhas.drop_duplicates("num_patamar", keep="last")
    n_patamares = int(linhas["num_patamar"].nunique())
    confere = data_interna_confere(sel["din_programacaodia"], dia) if len(sel) else True
    if not confere:
        logger.warning("%s: data interna diferente da data do nome do arquivo.", caminho.name)
    if not len(sel):
        status = "SEM_REGISTROS"
    elif n_patamares != PATAMARES_POR_DIA:
        status = "INCOMPLETO"
    else:
        status = "PROCESSADO"
    so_codigo, so_conferencia = int((codigo & ~conferencia).sum()), int((~codigo & conferencia).sum())
    if so_codigo or so_conferencia:
        logger.warning("%s: %d linhas só com o código da usina e %d só com a conferência (nome e estado), não "
                       "extraídas; verificar mudança de cadastro no ONS.", caminho.name, so_codigo, so_conferencia)
    return linhas.reset_index(drop=True), {
        **auditoria,
        "linhas_lidas": tabela.num_rows,
        "linhas_usina": len(sel),
        "linhas_codigo_sem_conferencia": so_codigo,
        "linhas_so_conferencia": so_conferencia,
        "valores_invalidos": invalidos,
        "patamares": n_patamares,
        "data_interna_confere": confere,
        "status": status,
    }


def arquivos_locais(pasta: Path, inicio: pd.Timestamp, fim: pd.Timestamp) -> List[Path]:
    """Arquivos diários da pasta (sem subpastas) dos dias do período, em ordem de nome."""
    d0, d1 = pd.Timestamp(inicio).normalize(), pd.Timestamp(fim).normalize()
    pasta = Path(pasta)
    if not pasta.exists():
        return []
    arquivos = []
    for caminho in sorted(pasta.glob(f"*.{FORMATO_PROGRAMACAO_DIARIA.lower()}")):
        dia = dia_do_arquivo(caminho.name)
        if caminho.is_file() and dia is not None and d0 <= dia <= d1:
            arquivos.append(caminho)
    return arquivos


def extrair_programacao(
    pasta: Path,
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
    cod_programacao: str,
    nome_ons: str,
    estado: str,
    falhas: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Patamares da usina em todos os arquivos locais do período e a auditoria (uma linha por arquivo)."""
    manifesto = load_manifest(Path(pasta) / RAW_MANIFEST_FILE.name)
    arquivos = arquivos_locais(pasta, inicio, fim)
    partes, auditorias = [], []
    for caminho in arquivos:
        linhas, auditoria = ler_arquivo(caminho, cod_programacao, nome_ons, estado)
        auditoria["data_publicacao"] = (manifesto.get(caminho.name) or {}).get("ultima_modificacao") or ""
        auditorias.append(auditoria)
        if len(linhas):
            partes.append(linhas)
    auditorias += [{**f, "obtido": False} for f in (falhas or [])]
    auditoria = pd.DataFrame(auditorias, columns=COLUNAS_AUDITORIA_PROGRAMACAO)
    for coluna in ("linhas_lidas", "linhas_usina", "linhas_codigo_sem_conferencia", "linhas_so_conferencia",
                   "valores_invalidos", "patamares"):
        auditoria[coluna] = pd.to_numeric(auditoria[coluna], errors="coerce").fillna(0).astype(int)
    for coluna in ("data_publicacao", "mensagem"):
        auditoria[coluna] = auditoria[coluna].fillna("")
    auditoria["data_interna_confere"] = auditoria["data_interna_confere"].eq(True)
    auditoria["obtido"] = auditoria["obtido"].astype(bool)
    auditoria["dia"] = pd.to_datetime(auditoria["dia"])
    extraido = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLUNAS_EXTRAIDAS)
    logger.info("Programação: %d arquivos lidos, %d patamares da usina, %d arquivos com status diferente de "
                "PROCESSADO.", len(arquivos), len(extraido), int((auditoria["status"] != "PROCESSADO").sum()))
    return extraido, auditoria
