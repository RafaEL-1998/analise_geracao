"""Conjuntos horários do ONS na Coleta de dados: disponibilidade, hidrologia e geração por usina.

Fluxo (spec da Coleta de dados, FR-016 a FR-019, FR-034 a FR-040, FR-044 e FR-046): catálogo CKAN → arquivos que se
sobrepõem ao período da base de EVT → um formato por período → download com cache por versão → leitura só das linhas
da usina, identificadas pelo perfil (identificador e conferência), sem arredondamento → auditoria por arquivo.

A convenção de hora, as duplicatas entre arquivos, o recorte do período e as ausências são do Tratamento de dados.
"""

from __future__ import annotations

import concurrent.futures
import csv
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd
import pyarrow.parquet as pq

from src.coleta.catalogo import (
    _local_filename,
    download_resource,
    fetch_ckan_package_metadata,
    load_manifest,
    parse_ckan_resources,
    recurso_preferido,
    registrar_repetidos,
    save_manifest,
)
from src.coleta import registro
from src.coleta.registro import COLUNA_INSTANTE, DescricaoConjunto, Regra, normalizar_texto
from src.comum.caminhos import RAW_MANIFEST_FILE
from src.comum.logger import setup_logger
from src.comum.modelos import RecursoONS
from src.comum.regras import ONS_CKAN_PACKAGE_SHOW_URL

logger = setup_logger("coleta")

DOWNLOADS_SIMULTANEOS = 8
COLUNA_NAO_NUMERICO = "_nao_numerico"  # marca de valor não numérico na fonte; o Tratamento a transforma em sinalização
_RE_PERIODO = re.compile(r"_(\d{4})(?:_(\d{2}))?\.[A-Za-z0-9]+$")
EXTENSOES = {".parquet": "PARQUET", ".csv": "CSV"}

# Auditoria da extração (uma linha por arquivo do período, lido ou não obtido)
COLUNAS_AUDITORIA_COLETA: List[str] = [
    "arquivo", "formato", "periodo", "data_publicacao", "obtido", "linhas_lidas", "linhas_formato_irregular",
    "linhas_usina", "linhas_so_identificador", "linhas_so_conferencia", "valores_invalidos",
    "recursos_duplicados_catalogo", "status", "mensagem",
]


def descricoes(perfil: Any) -> Dict[str, DescricaoConjunto]:
    """Descrições dos conjuntos horários da usina, com a identificação do perfil (registro, decisão R8)."""
    return registro.descricoes(perfil)


# ---------------------------------------------------------------------------
# Período e seleção de recursos
# ---------------------------------------------------------------------------


def periodo_do_arquivo(nome: str) -> Optional[Tuple[int, Optional[int]]]:
    """(ano, mês) de arquivos mensais, (ano, None) de anuais; None se o nome não tiver período."""
    achado = _RE_PERIODO.search(nome)
    if not achado:
        return None
    return int(achado.group(1)), (int(achado.group(2)) if achado.group(2) else None)


def intervalo_do_periodo(chave: Tuple[int, Optional[int]]) -> Tuple[pd.Timestamp, pd.Timestamp]:
    ano, mes = chave
    if mes is None:
        return pd.Timestamp(year=ano, month=1, day=1), pd.Timestamp(year=ano, month=12, day=31, hour=23)
    inicio = pd.Timestamp(year=ano, month=mes, day=1)
    return inicio, inicio + pd.offsets.MonthEnd(0) + pd.Timedelta(hours=23)


def _sobrepoe(chave: Tuple[int, Optional[int]], inicio: pd.Timestamp, fim: pd.Timestamp) -> bool:
    a, b = intervalo_do_periodo(chave)
    return a <= fim and b >= inicio


def rotulo_periodo(chave: Optional[Tuple[int, Optional[int]]]) -> str:
    if chave is None:
        return ""
    return f"{chave[0]:04d}" if chave[1] is None else f"{chave[0]:04d}-{chave[1]:02d}"


def meses_do_periodo(chave: Tuple[int, Optional[int]]) -> Set[Tuple[int, int]]:
    ano, mes = chave
    return {(ano, m) for m in range(1, 13)} if mes is None else {(ano, mes)}


def selecionar_recursos(
    desc: DescricaoConjunto,
    recursos: Iterable[RecursoONS],
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
) -> Tuple[List[RecursoONS], Dict[str, int]]:
    """Um recurso por período que se sobrepõe a [início, fim], no formato preferido publicado.

    Entre recursos repetidos no catálogo, fica o que tem ``last_modified`` preenchido e, em empate,
    o maior. Devolve os escolhidos (em ordem de período) e {nome do arquivo: duplicados descartados}.
    """
    grupos: Dict[Tuple[Tuple[int, Optional[int]], str], List[RecursoONS]] = {}
    for r in recursos:
        chave = periodo_do_arquivo(_local_filename(r))
        formato = (r.formato or "").upper()
        if chave is None or formato not in desc.formatos_preferidos or not _sobrepoe(chave, inicio, fim):
            continue
        grupos.setdefault((chave, formato), []).append(r)

    escolhidos: List[RecursoONS] = []
    duplicados: Dict[str, int] = {}
    for chave in sorted({c for c, _ in grupos}, key=lambda c: (c[0], c[1] or 0)):
        formato = next(f for f in desc.formatos_preferidos if (chave, f) in grupos)
        candidatos = grupos[(chave, formato)]
        escolhido = recurso_preferido(candidatos)
        escolhidos.append(escolhido)
        if len(candidatos) > 1:
            duplicados[_local_filename(escolhido)] = len(candidatos) - 1
            logger.warning("%s: %d recursos repetidos no catálogo para %s; usado o de %s (%d bytes).",
                           desc.pacote, len(candidatos), _local_filename(escolhido),
                           escolhido.ultima_modificacao or "data não informada", escolhido.tamanho_bytes)
    return escolhidos, duplicados


def sincronizar_conjunto(
    desc: DescricaoConjunto,
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
    pasta_raw: Path,
    force: bool = False,
) -> List[Dict[str, Any]]:
    """Baixa (ou reaproveita, se a versão local for a publicada) os arquivos do período.

    Devolve as falhas de download, uma por arquivo, no formato das linhas de auditoria.
    """
    pasta_raw.mkdir(parents=True, exist_ok=True)
    metadados = fetch_ckan_package_metadata(f"{ONS_CKAN_PACKAGE_SHOW_URL}{desc.pacote}")
    recursos: List[RecursoONS] = []
    for formato in desc.formatos_preferidos:
        recursos += parse_ckan_resources(metadados, formato)
    escolhidos, duplicados = selecionar_recursos(desc, recursos, inicio, fim)
    logger.info("%s: %d arquivos publicados no período.", desc.pacote, len(escolhidos))

    manifesto_path = pasta_raw / RAW_MANIFEST_FILE.name
    manifesto = load_manifest(manifesto_path)
    falhas: List[Dict[str, Any]] = []

    def baixar(recurso: RecursoONS) -> None:
        try:
            download_resource(recurso, destination_dir=pasta_raw, force=force, manifest=manifesto)
        except Exception as exc:  # cada arquivo é tentado; a falha vai para a auditoria
            nome = _local_filename(recurso)
            logger.error("%s: falha ao obter %s: %s", desc.pacote, nome, exc)
            falhas.append({"arquivo": nome, "formato": recurso.formato.upper(),
                           "periodo": rotulo_periodo(periodo_do_arquivo(nome)), "status": "FALHA",
                           "mensagem": str(exc)})

    try:
        with concurrent.futures.ThreadPoolExecutor(DOWNLOADS_SIMULTANEOS) as executor:
            list(executor.map(baixar, escolhidos))
    finally:
        registrar_repetidos(manifesto, duplicados)
        save_manifest(manifesto, manifesto_path)
    resumo: Dict[str, int] = {}
    for r in escolhidos:
        resumo[r.status_sincronizacao] = resumo.get(r.status_sincronizacao, 0) + 1
    logger.info("%s: sincronização concluída %s", desc.pacote, resumo)
    return sorted(falhas, key=lambda f: f["arquivo"])


# ---------------------------------------------------------------------------
# Leitura, identificação e extração
# ---------------------------------------------------------------------------


def _normalizar(serie: pd.Series) -> pd.Series:
    """``normalizar_texto`` em cada valor (calculada uma vez por valor distinto)."""
    texto = serie.fillna("").astype(str)
    return texto.map({valor: normalizar_texto(valor) for valor in texto.unique()})


def numero_publicado(serie: pd.Series) -> pd.Series:
    """Números como publicados pelo ONS, com vírgula ou ponto decimal (correção P2); texto não numérico fica
    ausente."""
    if pd.api.types.is_numeric_dtype(serie) and not pd.api.types.is_bool_dtype(serie):
        return pd.to_numeric(serie, errors="coerce").astype("float64")
    texto = serie.astype("string").str.strip().str.replace(",", ".", regex=False)
    return pd.to_numeric(texto, errors="coerce").astype("float64")


def _corresponde(tabela: pd.DataFrame, regra: Regra) -> pd.Series:
    if regra.coluna not in tabela.columns:
        return pd.Series(False, index=tabela.index)
    if isinstance(regra.valor, (int, float)) and not isinstance(regra.valor, bool):
        return pd.to_numeric(tabela[regra.coluna], errors="coerce") == float(regra.valor)
    alvo = _normalizar(pd.Series([str(regra.valor)])).iloc[0]
    valores = _normalizar(tabela[regra.coluna])
    if regra.modo == "contem":
        return valores.str.contains(alvo, regex=False)
    return valores == alvo


def linhas_formato_irregular(caminho: Path, codificacao: str) -> List[int]:
    """Números (o cabeçalho é a linha 1) das linhas não vazias com nº de campos diferente do cabeçalho.

    Essas linhas não são extraídas, são contadas na auditoria e avisadas no log (FR-038).
    """
    irregulares: List[int] = []
    with open(caminho, encoding=codificacao, newline="") as f:
        leitor = csv.reader(f, delimiter=";")
        cabecalho = next(leitor, None)
        if cabecalho is None:
            return irregulares
        for campos in leitor:
            if campos and any(campos) and len(campos) != len(cabecalho):
                irregulares.append(leitor.line_num)
    return irregulares


def ler_csv_texto(caminho: Path, colunas: Optional[Iterable[str]] = None) -> Tuple[pd.DataFrame, List[int]]:
    """CSV ``;`` lido como texto (UTF-8, com releitura em Latin-1), sem as linhas de formato irregular.

    Devolve a tabela (só as ``colunas`` pedidas, se informadas) e os números das linhas irregulares, que ficam de
    fora da leitura: linha curta não entra com campos vazios e linha longa não tem o excedente descartado em silêncio.
    """
    filtro = None if colunas is None else set(colunas)
    ultimo_erro: Optional[Exception] = None
    for codificacao in ("utf-8-sig", "latin-1"):
        try:
            irregulares = linhas_formato_irregular(caminho, codificacao)
            tabela = pd.read_csv(caminho, sep=";", dtype=str, encoding=codificacao, keep_default_na=False,
                                 usecols=None if filtro is None else (lambda c: c.strip() in filtro),
                                 skiprows=[n - 1 for n in irregulares] or None)
            return tabela, irregulares
        except UnicodeDecodeError as exc:
            ultimo_erro = exc
    raise ultimo_erro  # type: ignore[misc]


def avisar_linhas_irregulares(pacote: str, arquivo: str, irregulares: List[int]) -> None:
    """Aviso no log com o arquivo, a quantidade e o número das primeiras linhas de formato irregular."""
    if irregulares:
        logger.warning(
            "%s: arquivo %s com %d linhas de formato irregular (nº de campos diferente do cabeçalho) não extraídas; "
            "primeiras linhas: %s", pacote, arquivo, len(irregulares), ", ".join(str(n) for n in irregulares[:5]),
        )


def _exigir_conferencias(desc: DescricaoConjunto, colunas: Iterable[str]) -> None:
    """Num conjunto com conferência declarada, a coluna ausente impede a leitura do arquivo (correção P4)."""
    presentes = set(colunas)
    ausentes = [r.coluna for r in desc.conferencias if r.coluna not in presentes]
    if ausentes:
        raise ValueError(f"coluna de conferência ausente: {', '.join(ausentes)}")


def extrair_arquivo(desc: DescricaoConjunto, caminho: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Linhas da usina (instante como publicado, valores numéricos sem arredondamento) e a auditoria do arquivo."""
    chave = periodo_do_arquivo(caminho.name)
    auditoria: Dict[str, Any] = {
        "arquivo": caminho.name, "formato": EXTENSOES.get(caminho.suffix.lower(), caminho.suffix.upper()),
        "periodo": rotulo_periodo(chave), "data_publicacao": "", "obtido": True, "linhas_lidas": 0,
        "linhas_formato_irregular": 0, "linhas_usina": 0, "linhas_so_identificador": 0, "linhas_so_conferencia": 0,
        "valores_invalidos": 0, "recursos_duplicados_catalogo": 0, "status": "PROCESSADO", "mensagem": "",
    }
    try:
        if caminho.suffix.lower() == ".parquet":
            disponiveis = set(pq.read_schema(caminho).names)
            _exigir_conferencias(desc, disponiveis)
            colunas = [c for c in desc.colunas_leitura if c in disponiveis]
            auditoria["linhas_lidas"] = pq.read_metadata(caminho).num_rows
            filtros = [list(grupo) for grupo in desc.filtro_parquet] if desc.filtro_parquet else None
            bruto = pd.read_parquet(caminho, columns=colunas, filters=filtros)
        else:
            bruto, irregulares = ler_csv_texto(caminho, desc.colunas_leitura)
            bruto.columns = [c.strip() for c in bruto.columns]
            auditoria["linhas_lidas"] = len(bruto) + len(irregulares)
            auditoria["linhas_formato_irregular"] = len(irregulares)
            avisar_linhas_irregulares(desc.pacote, caminho.name, irregulares)
            _exigir_conferencias(desc, bruto.columns)
        faltantes = [c for c in (desc.identificador.coluna, COLUNA_INSTANTE) if c not in bruto.columns]
        if faltantes:
            raise ValueError(f"colunas ausentes no arquivo: {faltantes}")
    except Exception as exc:
        logger.error("%s: não foi possível ler %s: %s", desc.pacote, caminho.name, exc)
        auditoria.update(status="FALHA", mensagem=str(exc))
        return pd.DataFrame(), auditoria

    ident = _corresponde(bruto, desc.identificador)
    conf = pd.Series(True, index=bruto.index)
    for regra in desc.conferencias:
        conf &= _corresponde(bruto, regra)
    auditoria["linhas_so_identificador"] = int((ident & ~conf).sum())
    auditoria["linhas_so_conferencia"] = int((~ident & conf).sum())
    usina = bruto[ident & conf].copy()
    auditoria["linhas_usina"] = len(usina)
    if auditoria["linhas_so_identificador"] or auditoria["linhas_so_conferencia"]:
        logger.warning("%s: arquivo %s com linhas que conferem só em parte (só identificador: %d; só conferência: "
                       "%d); verificar mudança de cadastro no ONS.", desc.pacote, caminho.name,
                       auditoria["linhas_so_identificador"], auditoria["linhas_so_conferencia"])

    dados = pd.DataFrame(index=usina.index)
    instantes = pd.to_datetime(usina[COLUNA_INSTANTE], errors="coerce")
    invalidos = pd.Series(0, index=usina.index)
    nao_numerico = instantes.isna()
    invalidos += instantes.isna().astype(int)
    for coluna in desc.colunas_valor:
        bruto_col = usina[coluna] if coluna in usina.columns else pd.Series(pd.NA, index=usina.index, dtype=object)
        numerico = numero_publicado(bruto_col)
        preenchido = bruto_col.notna() & (bruto_col.astype(str).str.strip() != "")
        ruim = numerico.isna() & preenchido
        invalidos += ruim.astype(int)
        nao_numerico |= ruim
        dados[coluna] = numerico.astype(float)
    auditoria["valores_invalidos"] = int(invalidos.sum())
    dados.insert(0, COLUNA_INSTANTE, instantes)
    dados[COLUNA_NAO_NUMERICO] = nao_numerico.astype(bool)
    dados = dados[dados[COLUNA_INSTANTE].notna()].reset_index(drop=True)
    if auditoria["linhas_usina"] == 0:
        auditoria["status"] = "SEM_REGISTROS"
    return dados, auditoria


def arquivos_locais(desc: DescricaoConjunto, pasta_raw: Path, inicio: pd.Timestamp, fim: pd.Timestamp) -> List[Path]:
    """Arquivos de dados da pasta (sem subpastas) no período; um por período, no formato preferido."""
    if not pasta_raw.exists():
        return []
    por_chave: Dict[Tuple[int, Optional[int]], Dict[str, Path]] = {}
    for caminho in pasta_raw.iterdir():
        formato = EXTENSOES.get(caminho.suffix.lower())
        chave = periodo_do_arquivo(caminho.name)
        if caminho.is_file() and formato in desc.formatos_preferidos and chave and _sobrepoe(chave, inicio, fim):
            por_chave.setdefault(chave, {})[formato] = caminho
    escolhidos = []
    for formatos in por_chave.values():
        escolhidos.append(next(formatos[f] for f in desc.formatos_preferidos if f in formatos))
    return escolhidos


def extrair_conjunto(
    desc: DescricaoConjunto,
    pasta_raw: Path,
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
    falhas: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Linhas da usina em todos os arquivos locais do período e a auditoria da extração.

    Os arquivos são lidos em ordem de data de publicação (pelo manifesto) e de nome. As linhas extraídas trazem o
    arquivo de origem; a auditoria traz o período e a data de publicação de cada arquivo, e as falhas de download.
    """
    manifesto = load_manifest(pasta_raw / RAW_MANIFEST_FILE.name)
    arquivos = sorted(
        arquivos_locais(desc, pasta_raw, inicio, fim),
        key=lambda p: ((manifesto.get(p.name) or {}).get("ultima_modificacao") or "", p.name),
    )
    partes: List[pd.DataFrame] = []
    auditorias: List[Dict[str, Any]] = []
    for caminho in arquivos:
        dados, auditoria = extrair_arquivo(desc, caminho)
        entrada = manifesto.get(caminho.name) or {}
        auditoria["data_publicacao"] = entrada.get("ultima_modificacao") or ""
        auditoria["recursos_duplicados_catalogo"] = int(entrada.get("recursos_duplicados_catalogo", 0))
        if len(dados):
            dados["arquivo_origem"] = caminho.name
            partes.append(dados)
        auditorias.append(auditoria)
    auditorias += [{**f, "obtido": False} for f in (falhas or [])]
    auditoria_df = pd.DataFrame(auditorias, columns=COLUNAS_AUDITORIA_COLETA)
    for coluna in ("linhas_lidas", "linhas_formato_irregular", "linhas_usina", "linhas_so_identificador",
                   "linhas_so_conferencia", "valores_invalidos", "recursos_duplicados_catalogo"):
        auditoria_df[coluna] = pd.to_numeric(auditoria_df[coluna], errors="coerce").fillna(0).astype(int)
    for coluna in ("data_publicacao", "mensagem"):
        auditoria_df[coluna] = auditoria_df[coluna].fillna("")
    auditoria_df["obtido"] = auditoria_df["obtido"].astype(bool)
    colunas = [COLUNA_INSTANTE, *desc.colunas_valor, COLUNA_NAO_NUMERICO, "arquivo_origem"]
    extraido = pd.concat(partes, ignore_index=True)[colunas] if partes else pd.DataFrame(columns=colunas)
    logger.info("%s: %d linhas da usina em %d arquivos.", desc.pacote, len(extraido), len(arquivos))
    return extraido, auditoria_df
