"""Motor comum dos conjuntos horários do ONS (spec 006): disponibilidade, hidrologia e geração por usina.

Fluxo: catálogo CKAN → arquivos que se sobrepõem ao período da base de EVT → um formato por período
(o preferido que estiver publicado; FR-003) → download com cache por versão e preservação de versões
(spec 005) → leitura só das linhas da usina, com contagem da identificação parcial (princípio IV) →
uma hora por instante (a do arquivo publicado por último) → recorte no período → meses e horas
ausentes listados, nunca interpolados (princípio III).
"""

from __future__ import annotations

import concurrent.futures
import csv
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd
import pyarrow.parquet as pq

from src.collector import (
    _local_filename,
    download_resource,
    fetch_ckan_package_metadata,
    load_manifest,
    parse_ckan_resources,
    save_manifest,
)
from src.config import ONS_CKAN_PACKAGE_SHOW_URL, RAW_MANIFEST_FILE
from src.logger import setup_logger
from src.models import RecursoONS
from src.persistencia import ResultadoGravacao, gravar_csv

logger = setup_logger("conjuntos_ons")

DOWNLOADS_SIMULTANEOS = 8
COLUNA_INSTANTE = "din_instante"
COLUNA_INSTANTE_PUBLICADO = "din_instante_publicado"
_RE_PERIODO = re.compile(r"_(\d{4})(?:_(\d{2}))?\.[A-Za-z0-9]+$")
_EXTENSOES = {".parquet": "PARQUET", ".csv": "CSV"}

COLUNAS_AUDITORIA: List[str] = [
    "arquivo", "formato", "periodo", "linhas_lidas", "linhas_formato_irregular", "linhas_usina",
    "linhas_so_identificador", "linhas_so_conferencia", "horas_usina", "valores_invalidos", "duplicatas_conflitantes",
    "recursos_duplicados_catalogo", "status", "mensagem",
]
COLUNAS_AUSENCIAS: List[str] = ["tipo", "inicio", "fim", "horas"]


@dataclass(frozen=True)
class Regra:
    """Condição sobre uma coluna: ``igual`` (texto normalizado ou número) ou ``contem`` (texto normalizado)."""

    coluna: str
    valor: Any
    modo: str = "igual"


@dataclass(frozen=True)
class DescricaoConjunto:
    """Descrição declarativa de um conjunto horário do ONS."""

    pacote: str
    pasta: str
    identificador: Regra
    conferencias: Tuple[Regra, ...]
    colunas_valor: Tuple[str, ...]
    convencao_hora: str = "inicio"  # "inicio" ou "fim" (hora de fim; a última hora do dia vem como 23:59)
    formatos_preferidos: Tuple[str, ...] = ("PARQUET", "CSV")
    # Filtro empurrado à leitura do Parquet (DNF do pyarrow), útil nos arquivos grandes com todas as usinas
    filtro_parquet: Optional[Tuple[Tuple[Tuple[str, str, Any], ...], ...]] = None

    @property
    def colunas_leitura(self) -> List[str]:
        colunas = [self.identificador.coluna, *(r.coluna for r in self.conferencias), COLUNA_INSTANTE,
                   *self.colunas_valor]
        return list(dict.fromkeys(colunas))


@dataclass
class SerieConjunto:
    """Série horária da usina, meses e horas ausentes e auditoria por arquivo."""

    horaria: pd.DataFrame
    ausencias: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=COLUNAS_AUSENCIAS))
    auditoria: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=COLUNAS_AUDITORIA))


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


def _rotulo_periodo(chave: Optional[Tuple[int, Optional[int]]]) -> str:
    if chave is None:
        return ""
    return f"{chave[0]:04d}" if chave[1] is None else f"{chave[0]:04d}-{chave[1]:02d}"


def _meses_do_periodo(chave: Tuple[int, Optional[int]]) -> Set[Tuple[int, int]]:
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
        escolhido = max(candidatos, key=lambda r: (bool(r.ultima_modificacao), r.tamanho_bytes))
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
                           "periodo": _rotulo_periodo(periodo_do_arquivo(nome)), "status": "FALHA",
                           "mensagem": str(exc)})

    try:
        with concurrent.futures.ThreadPoolExecutor(DOWNLOADS_SIMULTANEOS) as executor:
            list(executor.map(baixar, escolhidos))
    finally:
        for nome, quantidade in duplicados.items():
            if nome in manifesto:
                manifesto[nome]["recursos_duplicados_catalogo"] = quantidade
        save_manifest(manifesto, manifesto_path)
    resumo: Dict[str, int] = {}
    for r in escolhidos:
        resumo[r.status_sincronizacao] = resumo.get(r.status_sincronizacao, 0) + 1
    logger.info("%s: sincronização concluída %s", desc.pacote, resumo)
    return sorted(falhas, key=lambda f: f["arquivo"])


# ---------------------------------------------------------------------------
# Leitura e filtragem
# ---------------------------------------------------------------------------


def _normalizar(serie: pd.Series) -> pd.Series:
    def _sem_acento(valor: str) -> str:
        return "".join(c for c in unicodedata.normalize("NFKD", valor) if not unicodedata.combining(c))

    return serie.fillna("").astype(str).map(_sem_acento).str.strip().str.upper()


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


def hora_de_inicio(instantes: pd.Series) -> pd.Series:
    """Converte a convenção de fim de hora para a de início: (instante arredondado para cima) − 1 h.

    Ex.: 01:00 → 00:00; 15:00 → 14:00; 23:59 (última hora do dia) → 23:00 do mesmo dia.
    """
    return instantes.dt.ceil("h") - pd.Timedelta(hours=1)


def linhas_formato_irregular(caminho: Path, codificacao: str) -> List[int]:
    """Números (o cabeçalho é a linha 1) das linhas não vazias com nº de campos diferente do cabeçalho.

    Mesmo critério da filtragem da EVT (spec 005, FR-009; princípio IV): essas linhas não são extraídas,
    são contadas na auditoria e avisadas no log.
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


def ler_arquivo(desc: DescricaoConjunto, caminho: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Linhas da usina (valores numéricos, hora de início) e a auditoria do arquivo."""
    chave = periodo_do_arquivo(caminho.name)
    auditoria: Dict[str, Any] = {
        "arquivo": caminho.name, "formato": _EXTENSOES.get(caminho.suffix.lower(), caminho.suffix.upper()),
        "periodo": _rotulo_periodo(chave), "linhas_lidas": 0, "linhas_formato_irregular": 0, "linhas_usina": 0,
        "linhas_so_identificador": 0, "linhas_so_conferencia": 0, "horas_usina": 0, "valores_invalidos": 0,
        "duplicatas_conflitantes": 0, "recursos_duplicados_catalogo": 0, "status": "PROCESSADO", "mensagem": "",
    }
    try:
        if caminho.suffix.lower() == ".parquet":
            disponiveis = set(pq.read_schema(caminho).names)
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

    dados = pd.DataFrame(index=usina.index)
    instantes = pd.to_datetime(usina[COLUNA_INSTANTE], errors="coerce")
    invalidos = pd.Series(0, index=usina.index)
    nao_numerico = instantes.isna()
    invalidos += instantes.isna().astype(int)
    for coluna in desc.colunas_valor:
        bruto_col = usina[coluna] if coluna in usina.columns else pd.Series(pd.NA, index=usina.index, dtype=object)
        numerico = pd.to_numeric(bruto_col, errors="coerce")
        preenchido = bruto_col.notna() & (bruto_col.astype(str).str.strip() != "")
        ruim = numerico.isna() & preenchido
        invalidos += ruim.astype(int)
        nao_numerico |= ruim
        dados[coluna] = numerico.astype(float)
    auditoria["valores_invalidos"] = int(invalidos.sum())

    if desc.convencao_hora == "fim":
        dados.insert(0, COLUNA_INSTANTE_PUBLICADO, instantes)
        dados.insert(0, COLUNA_INSTANTE, hora_de_inicio(instantes))
    else:
        dados.insert(0, COLUNA_INSTANTE, instantes)
    dados["_nao_numerico"] = nao_numerico.astype(bool)
    dados = dados[dados[COLUNA_INSTANTE].notna()].reset_index(drop=True)
    auditoria["horas_usina"] = int(dados[COLUNA_INSTANTE].nunique())
    if auditoria["linhas_usina"] == 0:
        auditoria["status"] = "SEM_REGISTROS"
    return dados, auditoria


# ---------------------------------------------------------------------------
# Série horária, duplicatas e ausências
# ---------------------------------------------------------------------------


def listar_ausencias(
    instantes: pd.Series,
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
    meses_com_arquivo: Set[Tuple[int, int]],
) -> pd.DataFrame:
    """Meses inteiros (sem arquivo ou sem a usina) e intervalos contínuos de horas ausentes."""
    esperado = pd.date_range(pd.Timestamp(inicio).floor("h"), pd.Timestamp(fim).floor("h"), freq="h")
    faltantes = esperado.difference(pd.DatetimeIndex(pd.Series(instantes).dropna().unique()))
    linhas: List[Dict[str, Any]] = []
    if len(faltantes):
        mes_esperado = esperado.to_period("M")
        mes_faltante = faltantes.to_period("M")
        for mes in mes_faltante.unique():
            horas_mes = esperado[mes_esperado == mes]
            faltam = faltantes[mes_faltante == mes]
            if len(faltam) == len(horas_mes):
                tipo = "MES_SEM_USINA" if (mes.year, mes.month) in meses_com_arquivo else "MES_SEM_ARQUIVO"
                linhas.append({"tipo": tipo, "inicio": horas_mes[0], "fim": horas_mes[-1], "horas": len(horas_mes)})
                continue
            serie = faltam.to_series()
            grupos = (serie.diff() != pd.Timedelta(hours=1)).cumsum()
            for _, bloco in serie.groupby(grupos.values):
                linhas.append({"tipo": "HORAS", "inicio": bloco.iloc[0], "fim": bloco.iloc[-1], "horas": len(bloco)})
    return pd.DataFrame(linhas, columns=COLUNAS_AUSENCIAS)


def _arquivos_locais(desc: DescricaoConjunto, pasta_raw: Path, inicio: pd.Timestamp,
                     fim: pd.Timestamp) -> List[Path]:
    """Arquivos de dados da pasta (sem subpastas) no período; um por período, no formato preferido."""
    if not pasta_raw.exists():
        return []
    por_chave: Dict[Tuple[int, Optional[int]], Dict[str, Path]] = {}
    for caminho in pasta_raw.iterdir():
        formato = _EXTENSOES.get(caminho.suffix.lower())
        chave = periodo_do_arquivo(caminho.name)
        if caminho.is_file() and formato in desc.formatos_preferidos and chave and _sobrepoe(chave, inicio, fim):
            por_chave.setdefault(chave, {})[formato] = caminho
    escolhidos = []
    for formatos in por_chave.values():
        escolhidos.append(next(formatos[f] for f in desc.formatos_preferidos if f in formatos))
    return escolhidos


def montar_serie(
    desc: DescricaoConjunto,
    pasta_raw: Path,
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
    falhas: Optional[List[Dict[str, Any]]] = None,
) -> SerieConjunto:
    """Lê os arquivos locais do período e monta a série horária da usina."""
    manifesto = load_manifest(pasta_raw / RAW_MANIFEST_FILE.name)
    arquivos = sorted(
        _arquivos_locais(desc, pasta_raw, inicio, fim),
        key=lambda p: ((manifesto.get(p.name) or {}).get("ultima_modificacao") or "", p.name),
    )
    partes: List[pd.DataFrame] = []
    auditorias: List[Dict[str, Any]] = []
    meses_com_arquivo: Set[Tuple[int, int]] = set()
    for ordem, caminho in enumerate(arquivos):
        dados, auditoria = ler_arquivo(desc, caminho)
        auditoria["recursos_duplicados_catalogo"] = int(
            (manifesto.get(caminho.name) or {}).get("recursos_duplicados_catalogo", 0))
        meses_com_arquivo |= _meses_do_periodo(periodo_do_arquivo(caminho.name))
        if len(dados):
            dados["arquivo_origem"] = caminho.name
            dados["_ordem"] = ordem
            partes.append(dados)
        auditorias.append(auditoria)
    auditorias += [dict(f) for f in (falhas or [])]
    auditoria_df = pd.DataFrame(auditorias, columns=COLUNAS_AUDITORIA)

    colunas = [COLUNA_INSTANTE, *([COLUNA_INSTANTE_PUBLICADO] if desc.convencao_hora == "fim" else []),
               *desc.colunas_valor, "_nao_numerico", "arquivo_origem", "_ordem"]
    horaria = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=colunas)
    if len(horaria):
        horaria = horaria.sort_values([COLUNA_INSTANTE, "_ordem"], kind="stable").reset_index(drop=True)
        repetidas = horaria.duplicated(COLUNA_INSTANTE, keep="last")
        if repetidas.any():
            mantidas = horaria[~repetidas].set_index(COLUNA_INSTANTE)
            descartadas = horaria[repetidas]
            valores = list(desc.colunas_valor)
            ref = mantidas.loc[descartadas[COLUNA_INSTANTE], valores].to_numpy()
            atual = descartadas[valores].to_numpy()
            diferentes = ~((ref == atual) | (pd.isna(ref) & pd.isna(atual))).all(axis=1)
            conflitos = descartadas.loc[diferentes, "arquivo_origem"].value_counts()
            for arquivo, quantidade in conflitos.items():
                auditoria_df.loc[auditoria_df["arquivo"] == arquivo, "duplicatas_conflitantes"] = int(quantidade)
            if int(diferentes.sum()):
                logger.warning("%s: %d horas repetidas com valores diferentes; mantido o arquivo publicado por último.",
                               desc.pacote, int(diferentes.sum()))
            horaria = horaria[~repetidas]
        dentro = (horaria[COLUNA_INSTANTE] >= inicio) & (horaria[COLUNA_INSTANTE] <= fim)
        horaria = horaria[dentro].reset_index(drop=True)
    ausencias = listar_ausencias(horaria[COLUNA_INSTANTE], inicio, fim, meses_com_arquivo)
    for coluna in ("linhas_lidas", "linhas_usina", "linhas_so_identificador", "linhas_so_conferencia", "horas_usina",
                   "valores_invalidos", "duplicatas_conflitantes", "recursos_duplicados_catalogo"):
        auditoria_df[coluna] = pd.to_numeric(auditoria_df[coluna], errors="coerce").fillna(0).astype(int)
    auditoria_df["mensagem"] = auditoria_df["mensagem"].fillna("")
    logger.info("%s: %d horas da usina em %d arquivos; %d intervalos ausentes.", desc.pacote, len(horaria),
                len(arquivos), len(ausencias))
    return SerieConjunto(horaria=horaria, ausencias=ausencias, auditoria=auditoria_df)


def periodos_continuos(horas: pd.DataFrame, coluna_diferenca: str) -> pd.DataFrame:
    """Agrupa horas consecutivas (passo de 1 h) em períodos, com a diferença média e máxima de cada um."""
    colunas = ["inicio", "fim", "horas", "diferenca_media_mw", "diferenca_maxima_mw"]
    if horas.empty:
        return pd.DataFrame(columns=colunas)
    h = horas.sort_values("din_instante")
    grupo = (h["din_instante"].diff() != pd.Timedelta(hours=1)).cumsum()
    blocos = h.groupby(grupo.values).agg(
        inicio=("din_instante", "min"), fim=("din_instante", "max"), horas=("din_instante", "size"),
        diferenca_media_mw=(coluna_diferenca, "mean"), diferenca_maxima_mw=(coluna_diferenca, "max"),
    )
    return blocos.reset_index(drop=True)[colunas]


# ---------------------------------------------------------------------------
# Exportação e carga
# ---------------------------------------------------------------------------


def exportar_serie(serie: SerieConjunto, arquivos: Dict[str, Path]) -> Dict[str, ResultadoGravacao]:
    """Grava as tabelas da série via persistência; colunas internas (prefixo ``_``) ficam de fora."""
    tabelas = {
        "horaria": serie.horaria[[c for c in serie.horaria.columns if not str(c).startswith("_")]],
        "ausencias": serie.ausencias,
        "auditoria": serie.auditoria,
    }
    return {nome: gravar_csv(tabelas[nome], caminho) for nome, caminho in arquivos.items() if nome in tabelas}


_COLUNAS_DATA = (COLUNA_INSTANTE, COLUNA_INSTANTE_PUBLICADO, "inicio", "fim")


def _ler_processado(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        return pd.DataFrame()
    try:
        tabela = pd.read_csv(caminho, sep=";")
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    for coluna in _COLUNAS_DATA:
        if coluna in tabela.columns:
            tabela[coluna] = pd.to_datetime(tabela[coluna])
    return tabela


def carregar_serie_processada(arquivos: Dict[str, Path]) -> Optional[SerieConjunto]:
    """Lê as tabelas gravadas; None se a série horária ainda não foi gerada."""
    if "horaria" not in arquivos or not Path(arquivos["horaria"]).exists():
        return None
    serie = SerieConjunto(horaria=_ler_processado(Path(arquivos["horaria"])))
    if "ausencias" in arquivos and Path(arquivos["ausencias"]).exists():
        serie.ausencias = _ler_processado(Path(arquivos["ausencias"]))
    if "auditoria" in arquivos and Path(arquivos["auditoria"]).exists():
        serie.auditoria = _ler_processado(Path(arquivos["auditoria"]))
    return serie


def data_obtencao(pasta_raw: Path) -> str:
    """Data (UTC) mais recente registrada no manifesto da pasta; vazio se não houver."""
    manifesto = load_manifest(Path(pasta_raw) / RAW_MANIFEST_FILE.name)
    datas = [str(e.get("registrado_em_utc")) for e in manifesto.values() if isinstance(e, dict) and e.get("registrado_em_utc")]
    return max(datas) if datas else ""
