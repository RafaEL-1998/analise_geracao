"""Catálogo de usinas: ``python -m src usinas`` (spec 006, decisões R1 a R3, R21 e R31; contracts/cli-usinas.md).

Comando da Coleta, o único além de ``coleta`` e ``completo`` que acessa o portal do ONS (princípio I). Sem
``--sem-portal``, sincroniza, com o catálogo CKAN, o cache e as versões de hoje:
- os quatro cadastrais: Modalidade das usinas, Composição dos conjuntos, Capacidade de geração e Reservatórios;
- o arquivo mais recente de cada conjunto de série já implementado (nos indicadores, o DISPF mensal);
- a Geração por usina dos últimos 12 meses completos, para o panorama dos agregados;
- todos os arquivos da Geração térmica por motivo de despacho, para os códigos de planejamento (``planejamento.csv``);
- todos os arquivos da Programação diária, para os códigos de exibição de todo o período (``programacao.csv``; fase D:
  um conjunto pode trocar os códigos, como o Conj. Chapadão em 07/2025);
- os dicionários de dados desses conjuntos (princípio IV).

Depois monta e grava ``data/catalogo/`` por inteiro, sem ``.bak``, numa pasta temporária conferida antes da troca, e
lista na tela as usinas do filtro, sempre a partir dos arquivos gravados. O tipo vem do prefixo do CEG (R1); a linha do
cadastro sem CEG é de conjunto de usinas. A cobertura de cada conjunto de série é verificada no arquivo mais recente
(R3), sempre pelos códigos, nunca pelo nome: o id ONS, o CEG, o id do conjunto, na EVT e nos dados hidrológicos o
``cod_usina`` dos Reservatórios (R31) e, no CVU, os códigos de planejamento vigentes do despacho (fase B).

Códigos: 0 catálogo montado e listado; 1 catálogo do ONS inacessível, falha de gravação ou erro inesperado; 2 cadastral
não obtido (download sem sucesso ou, com ``--sem-portal``, arquivo local ausente).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tomllib
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, TextIO, Tuple

import pandas as pd
import pyarrow.parquet as pq

from src.coleta import registro
from src.coleta.catalogo import (
    _local_filename,
    download_resource,
    fetch_ckan_package_metadata,
    load_manifest,
    parse_ckan_resources,
    recurso_preferido,
    save_manifest,
)
from src.coleta.conjuntos import ler_csv_texto, numero_publicado
from src.coleta.dicionarios import sincronizar_dicionarios
from src.coleta.registro import normalizar_texto
from src.comum import caminhos
from src.comum.formatacao import fmt_num
from src.comum.logger import setup_logger
from src.comum.modelos import RecursoONS
from src.comum.persistencia import gravar_bytes, gravar_csv
from src.comum.regras import (
    CONJUNTO_CADASTRO,
    CONJUNTO_CAPACIDADE,
    CONJUNTO_COMPOSICAO,
    CONJUNTO_RESERVATORIO,
    DATAS_SENTINELA,
    MESES_AGREGADOS_CATALOGO,
    MODALIDADES_AGREGADAS_GERACAO,
    MODALIDADES_PREVISAO_GERACAO,
    MODALIDADES_TIPO_III,
    ONS_CKAN_PACKAGE_SHOW_URL,
    PASTA_CADASTRO_RAW,
    PASTA_CAPACIDADE_RAW,
    PASTA_COMPOSICAO_RAW,
    PASTA_RESERVATORIO_RAW,
    PREFIXO_CONJUNTO,
    TIPOS_ONS,
    TIPOS_USINA,
    TOLERANCIA_POTENCIA_PERFIL_MW,
)

logger = setup_logger("coleta")

VERSAO_FORMATO_CATALOGO = 1
ARQ = caminhos.ARQUIVOS_CATALOGO
PASTA_TEMPORARIA = ".gravando"
CODIGO_SUCESSO, CODIGO_ERRO, CODIGO_NAO_OBTIDO = 0, 1, 2
NIVEIS_ORDEM = ("proprio", "conjunto", "agregado", "ausente")  # do melhor para o pior (cobertura_resumo)
LETRAS = {"proprio": "P", "conjunto": "C", "agregado": "A", "ausente": "-"}
_RE_DATA_ARQUIVO = re.compile(r"(\d{4})(?:_(\d{2}))?(?:_(\d{2}))?\.(?:csv|parquet)$", re.IGNORECASE)

COLUNAS_USINAS = [
    "ceg", "id_ons", "nom_usina", "tipo", "modalidade", "id_estado", "sgl_centrooperacao", "nom_pontoconexao",
    "sts_aneel", "subsistema", "potencia_autorizada_mw", "id_conjunto", "nom_conjunto", "unidades_geradoras",
    "potencia_efetiva_mw", "potencias_unidades_mw", "combustivel", "entrada_operacao", "cod_usina", "nom_reservatorio",
    "id_reservatorio", "cobertura_resumo", "divergencias",
]
COLUNAS_CONJUNTOS = ["id_conjunto", "nom_conjunto", "ceg", "id_ons_usina", "nom_usina", "tipo", "tipo_ons", "inicio",
                     "fim", "estado", "subsistema"]
COLUNAS_COBERTURA = ["ceg", "conjunto_ons", "nivel", "identificador", "linhas", "linhas_sem_valor", "arquivo",
                     "publicacao"]
COLUNAS_PLANEJAMENTO = ["ceg", "codigo", "primeiro_mes", "ultimo_mes", "nomes_publicados", "arquivos"]
COLUNAS_LEITURA_PLANEJAMENTO = ["ceg", "cod_usinaplanejamento", "din_instante", "nom_usina"]
COLUNAS_PROGRAMACAO = ["codigo_exibicao", "id_usina_ou_conjunto", "modalidade", "estado", "arquivo", "primeiro_dia",
                       "ultimo_dia"]
COLUNAS_LEITURA_PROGRAMACAO = ["cod_exibicaousina", "nom_modalidadeoperacao", "id_estado"]
COLUNAS_AGREGADOS = ["id_estado", "mes", "modalidade", "tipo_ons", "grupo", "energia_mwh", "horas", "horas_ausentes",
                     "previsao", "arquivo"]


class CadastralNaoObtido(Exception):
    """Modalidade, Composição, Capacidade ou Reservatórios não obtido (código 2)."""

    def __init__(self, pacote: str, motivo: str) -> None:
        super().__init__(f"{pacote}: {motivo}")
        self.pacote, self.motivo = pacote, motivo


@dataclass(frozen=True)
class Cadastral:
    """Conjunto cadastral do catálogo: pacote, pasta em ``data/raw/`` e formatos, na ordem de preferência."""

    pacote: str
    pasta: str
    formatos: Tuple[str, ...]


CADASTRAIS: Dict[str, Cadastral] = {
    "cadastro": Cadastral(CONJUNTO_CADASTRO, PASTA_CADASTRO_RAW, ("CSV",)),  # o formato que a Coleta já lê
    "composicao": Cadastral(CONJUNTO_COMPOSICAO, PASTA_COMPOSICAO_RAW, ("PARQUET", "CSV")),
    "capacidade": Cadastral(CONJUNTO_CAPACIDADE, PASTA_CAPACIDADE_RAW, ("PARQUET", "CSV")),
    "reservatorio": Cadastral(CONJUNTO_RESERVATORIO, PASTA_RESERVATORIO_RAW, ("PARQUET", "CSV")),
}


VARIANTES: Dict[str, Dict[str, Tuple[str, str]]] = {"restricao_detalhe": registro.VARIANTES_RESTRICAO_DETALHE,
                                                    "restricao_razao": registro.VARIANTES_RESTRICAO_RAZAO}


@dataclass(frozen=True)
class Serie:
    """Conjunto de série verificado na cobertura: chave do registro, pacote, pasta, formatos e prefixo do arquivo; nas
    restrições, uma série por variante (eólica e fotovoltaica), com o tipo em ``variante`` (fase C)."""

    chave: str
    formatos: Tuple[str, ...]
    prefixo: str = ""  # só a EVT fica na raiz de data/raw/, junto de outros arquivos
    variante: str = ""

    @property
    def id(self) -> str:
        return f"{self.chave}@{self.variante}" if self.variante else self.chave

    @property
    def pacote(self) -> str:
        if self.variante:
            return VARIANTES[self.chave][self.variante][0]
        return registro.entrada(self.chave).pacotes[0][0]  # nos indicadores, o DISPF mensal

    @property
    def pasta(self) -> str:
        if self.variante:
            return VARIANTES[self.chave][self.variante][1]
        return registro.entrada(self.chave).pacotes[0][1]

    def serve(self, tipo: str) -> bool:
        return tipo in registro.entrada(self.chave).tipos and self.variante in ("", tipo)


# Os conjuntos de série da [cobertura] já implementados, na ordem do registro, com os formatos que a Coleta lê
SERIES: Tuple[Serie, ...] = (
    Serie("evt", ("CSV",), prefixo="ENERGIA_VERTIDA_TURBINAVEL"),
    Serie("indicadores", ("CSV",)),
    Serie("programacao", ("PARQUET",)),
    Serie("disponibilidade", ("PARQUET", "CSV")),
    Serie("hidrologia", ("PARQUET", "CSV")),
    Serie("geracao", ("PARQUET", "CSV")),
    Serie("despacho", ("PARQUET", "CSV")),
    Serie("cvu", ("PARQUET", "CSV")),
    Serie("fator_capacidade", ("PARQUET", "CSV")),
    *(Serie("restricao_detalhe", ("PARQUET", "CSV"), variante=t) for t in registro.RENOVAVEIS),
    *(Serie("restricao_razao", ("PARQUET", "CSV"), variante=t) for t in registro.RENOVAVEIS),
)
SIGLAS_SERIES = {"evt": "EVT", "indicadores": "IND", "programacao": "PRG", "disponibilidade": "DSP",
                 "hidrologia": "HID", "geracao": "GER", "despacho": "DES", "cvu": "CVU", "fator_capacidade": "FC",
                 "restricao_detalhe": "RDT", "restricao_razao": "RRZ"}
CHAVES_SERIES: Tuple[str, ...] = tuple(dict.fromkeys(s.chave for s in SERIES))  # uma coluna por conjunto na listagem


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def tipo_do_ceg(ceg: Any) -> str:
    """Tipo pelas três primeiras letras do CEG (R1); sem CEG, linha de conjunto; prefixo fora da lista, "outro"."""
    texto = normalizar_texto(ceg)
    if not texto or texto == "-":
        return "conjunto"
    prefixo = texto.split(".", 1)[0]
    return prefixo if prefixo in TIPOS_USINA else "outro"


def _chave_arquivo(nome: str) -> Optional[Tuple[int, int, int]]:
    """(ano, mês, dia) do nome do arquivo; o mês e o dia ausentes valem 0."""
    m = _RE_DATA_ARQUIVO.search(nome)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0)


def _data(valor: Any) -> Optional[date]:
    """Data de um cadastral (AAAA-MM-DD ou DD/MM/AAAA); vazia ou sentinela vale None."""
    texto = str(valor if valor is not None else "").strip()[:10]
    if not texto or texto in DATAS_SENTINELA or texto.lower() in ("nan", "none", "nat"):
        return None
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


def _texto_data(valor: Optional[date]) -> str:
    return valor.isoformat() if valor else ""


def _meses_completos(hoje: date, quantidade: int = MESES_AGREGADOS_CATALOGO) -> List[pd.Period]:
    ultimo = pd.Period(hoje, freq="M") - 1
    return list(pd.period_range(ultimo - (quantidade - 1), ultimo, freq="M"))


def _ler_tabela(caminho: Path, colunas: Optional[Sequence[str]] = None) -> pd.DataFrame:
    """Parquet ou CSV ``;`` do ONS; com ``colunas``, só as que existirem no arquivo."""
    if caminho.suffix.lower() == ".parquet":
        presentes = pq.read_schema(caminho).names
        pedidas = None if colunas is None else [c for c in colunas if c in presentes]
        return pq.read_table(caminho, columns=pedidas).to_pandas()
    tabela, _ = ler_csv_texto(caminho, colunas)
    tabela.columns = [c.strip() for c in tabela.columns]
    return tabela


def _textos(serie: pd.Series) -> pd.Series:
    return serie.astype("string").fillna("").str.strip()


def _normalizados(serie: pd.Series) -> pd.Series:
    texto = serie.astype("string").fillna("").astype(str)
    return texto.map({v: normalizar_texto(v) for v in texto.unique()})


def _publicacao(pasta: Path, arquivo: str) -> str:
    return str((load_manifest(pasta / caminhos.RAW_MANIFEST_FILE.name).get(arquivo) or {}).get("ultima_modificacao")
               or "")


def _arquivos_locais(pasta: Path, formatos: Sequence[str], prefixo: str = "") -> List[Path]:
    if not pasta.is_dir():
        return []
    extensoes = {f".{f.lower()}" for f in formatos}
    return [p for p in pasta.iterdir() if p.is_file() and p.suffix.lower() in extensoes and p.name.startswith(prefixo)
            and _chave_arquivo(p.name) is not None]


def _mais_recente(arquivos: Iterable[Path], formatos: Sequence[str]) -> Optional[Path]:
    """O arquivo do período mais recente; entre formatos do mesmo período, o preferido."""
    ordem = {f".{f.lower()}": i for i, f in enumerate(formatos)}
    candidatos = sorted(arquivos, key=lambda p: (_chave_arquivo(p.name), -ordem.get(p.suffix.lower(), 99)))
    return candidatos[-1] if candidatos else None


def _arquivo_cadastral(pasta: Path, cadastral: Cadastral) -> Optional[Path]:
    """O arquivo local do cadastral (estático, um só): o do formato preferido."""
    if not pasta.is_dir():
        return None
    for formato in cadastral.formatos:
        locais = sorted(p for p in pasta.iterdir() if p.is_file() and p.suffix.lower() == f".{formato.lower()}")
        if locais:
            return locais[0]
    return None


# ---------------------------------------------------------------------------
# Sincronização com o portal
# ---------------------------------------------------------------------------


def _recursos(pacote: str, formatos: Sequence[str]) -> List[RecursoONS]:
    """Recursos publicados do pacote nos formatos pedidos (catálogo inacessível levanta a exceção: código 1)."""
    metadados = fetch_ckan_package_metadata(f"{ONS_CKAN_PACKAGE_SHOW_URL}{pacote}")
    recursos: List[RecursoONS] = []
    for formato in formatos:
        recursos += [r for r in parse_ckan_resources(metadados, formato)
                     if "DICIONARIO" not in normalizar_texto(r.nome_recurso)]
    return recursos


def _baixar(recursos: Sequence[RecursoONS], pasta: Path, force: bool) -> List[Tuple[str, str]]:
    """Baixa (ou reaproveita) os recursos na pasta, com o manifesto de versões; devolve (arquivo, motivo) das falhas."""
    pasta.mkdir(parents=True, exist_ok=True)
    manifesto_path = pasta / caminhos.RAW_MANIFEST_FILE.name
    manifesto = load_manifest(manifesto_path)
    falhas: List[Tuple[str, str]] = []
    try:
        for recurso in recursos:
            try:
                download_resource(recurso, destination_dir=pasta, force=force, manifest=manifesto)
            except Exception as exc:  # cada arquivo é tentado; a falha é contada e avisada
                falhas.append((_local_filename(recurso), str(exc)))
                logger.error("Catálogo de usinas: falha ao obter %s: %s", _local_filename(recurso), exc)
    finally:
        save_manifest(manifesto, manifesto_path)
    return falhas


def _escolher_por_periodo(recursos: Sequence[RecursoONS], formatos: Sequence[str],
                          prefixo: str = "") -> Dict[Tuple[int, int, int], RecursoONS]:
    """Um recurso por período (o formato preferido; entre repetidos, o de ``last_modified`` mais completo)."""
    grupos: Dict[Tuple[Tuple[int, int, int], str], List[RecursoONS]] = {}
    for r in recursos:
        nome = _local_filename(r)
        chave = _chave_arquivo(nome)
        if chave is None or not nome.startswith(prefixo):
            continue
        grupos.setdefault((chave, r.formato.upper()), []).append(r)
    escolhidos: Dict[Tuple[int, int, int], RecursoONS] = {}
    for chave in sorted({c for c, _ in grupos}):
        formato = next(f for f in formatos if (chave, f) in grupos)
        escolhidos[chave] = recurso_preferido(grupos[(chave, formato)])
    return escolhidos


def sincronizar_cadastral(chave: str, raiz_raw: Path, force: bool = False) -> None:
    """Baixa (ou reaproveita) o arquivo de um cadastral; sem sucesso, ``CadastralNaoObtido``. Usado também pela Coleta
    da usina (Composição e Capacidade)."""
    cadastral = CADASTRAIS[chave]
    recursos = _recursos(cadastral.pacote, cadastral.formatos)
    escolhido = None
    for formato in cadastral.formatos:
        do_formato = [r for r in recursos if r.formato.upper() == formato]
        if do_formato:
            escolhido = recurso_preferido(do_formato)
            break
    if escolhido is None:
        raise CadastralNaoObtido(cadastral.pacote, "nenhum arquivo publicado no catálogo do ONS")
    falhas = _baixar([escolhido], Path(raiz_raw) / cadastral.pasta, force)
    if falhas:
        raise CadastralNaoObtido(cadastral.pacote, falhas[0][1])


def ler_cadastral(chave: str, raiz_raw: Path) -> Tuple[pd.DataFrame, Path]:
    """O arquivo local de um cadastral, com os textos sem espaços nas pontas; ausente, ``CadastralNaoObtido``."""
    cadastral = CADASTRAIS[chave]
    pasta = Path(raiz_raw) / cadastral.pasta
    arquivo = _arquivo_cadastral(pasta, cadastral)
    if arquivo is None:
        raise CadastralNaoObtido(cadastral.pacote, f"arquivo local ausente em {pasta}")
    tabela = _ler_tabela(arquivo)
    tabela.columns = [str(c).strip() for c in tabela.columns]
    return tabela.apply(lambda c: _textos(c) if c.dtype == object or str(c.dtype) == "string" else c), arquivo


def sincronizar_catalogo(raiz_raw: Path, hoje: date, force: bool = False) -> None:
    """Sincroniza os arquivos do catálogo (R2). Cadastral sem sucesso levanta ``CadastralNaoObtido``."""
    for chave in CADASTRAIS:
        sincronizar_cadastral(chave, raiz_raw, force)
    meses = {(m.year, m.month) for m in _meses_completos(hoje)}
    for serie in SERIES:
        por_periodo = _escolher_por_periodo(_recursos(serie.pacote, serie.formatos), serie.formatos, serie.prefixo)
        if not por_periodo:
            logger.warning("Catálogo de usinas: nenhum arquivo publicado de %s.", serie.pacote)
            continue
        escolhidos = {max(por_periodo): por_periodo[max(por_periodo)]}
        if serie.chave == "geracao":  # panorama dos agregados: os últimos meses completos (R21)
            escolhidos.update({c: r for c, r in por_periodo.items() if (c[0], c[1]) in meses})
        if serie.chave in ("despacho", "programacao"):  # todos os arquivos: os códigos de cada usina no tempo
            escolhidos = dict(por_periodo)
        _baixar([escolhidos[c] for c in sorted(escolhidos)], raiz_raw / serie.pasta, force)
    pacotes = [c.pacote for c in CADASTRAIS.values()] + [s.pacote for s in SERIES]
    try:
        sincronizar_dicionarios(pacotes, raiz_raw)
    except Exception as exc:  # falha num dicionário não muda o código, como na Coleta
        logger.warning("Dicionários de dados do catálogo não obtidos (%s).", exc)


# ---------------------------------------------------------------------------
# Montagem
# ---------------------------------------------------------------------------


@dataclass
class Leituras:
    """Os cadastrais e o arquivo mais recente de cada conjunto de série, lidos dos arquivos locais."""

    cadastro: pd.DataFrame
    composicao: pd.DataFrame
    capacidade: pd.DataFrame
    reservatorio: pd.DataFrame
    arquivos_cadastrais: Dict[str, Tuple[Path, str]]  # chave -> (arquivo, publicação)
    series: Dict[str, Tuple[Path, str, pd.DataFrame]]  # chave -> (arquivo, publicação, tabela)
    planejamento: pd.DataFrame = None  # type: ignore[assignment]  # planejamento.csv, de todos os arquivos do despacho
    # Códigos de exibição de todos os arquivos da Programação diária, com o primeiro e o último dia (fase D)
    codigos_programacao: pd.DataFrame = None  # type: ignore[assignment]


COLUNAS_SERIES = {
    "evt": ["cod_usina", "val_geracao"],
    "indicadores": ["ceg"],
    "programacao": ["cod_exibicaousina", "val_geracaoprogramada", "nom_modalidadeoperacao", "id_estado"],
    "disponibilidade": ["id_ons", "val_dispoperacional"],
    "hidrologia": ["cod_usina", "val_vazaoturbinada", "val_vazaovertida", "val_nivelmontante"],
    "geracao": ["id_ons", "val_geracao"],
    "despacho": ["ceg", "val_proggeracao", "val_verifgeracao"],
    "cvu": ["cod_usinaplanejamento", "val_cvu"],
    "fator_capacidade": ["id_ons", "val_geracaoverificada"],
    "restricao_detalhe": ["id_ons", "val_geracaoverificada"],
    "restricao_razao": ["id_ons", "val_geracao"],
}


def ler_arquivos(raiz_raw: Path) -> Leituras:
    """Lê os quatro cadastrais (ausente levanta ``CadastralNaoObtido``) e as séries mais recentes que existirem."""
    tabelas: Dict[str, pd.DataFrame] = {}
    arquivos: Dict[str, Tuple[Path, str]] = {}
    for chave, cadastral in CADASTRAIS.items():
        tabelas[chave], arquivo = ler_cadastral(chave, raiz_raw)
        arquivos[chave] = (arquivo, _publicacao(raiz_raw / cadastral.pasta, arquivo.name))
    series: Dict[str, Tuple[Path, str, pd.DataFrame]] = {}
    for serie in SERIES:
        pasta = raiz_raw / serie.pasta if serie.pasta else raiz_raw
        arquivo = _mais_recente(_arquivos_locais(pasta, serie.formatos, serie.prefixo), serie.formatos)
        if arquivo is None:
            logger.warning("Catálogo de usinas: nenhum arquivo local de %s; cobertura ausente.", serie.pacote)
            continue
        series[serie.id] = (arquivo, _publicacao(pasta, arquivo.name), _ler_tabela(arquivo, COLUNAS_SERIES[serie.chave]))
    pasta_despacho = raiz_raw / registro.entrada("despacho").pacotes[0][1]
    pasta_programacao = raiz_raw / registro.entrada("programacao").pacotes[0][1]
    return Leituras(tabelas["cadastro"], tabelas["composicao"], tabelas["capacidade"], tabelas["reservatorio"],
                    arquivos, series, montar_planejamento(pasta_despacho), montar_codigos_programacao(pasta_programacao))


def _um_por_periodo(arquivos: Iterable[Path], formatos: Sequence[str]) -> List[Path]:
    """Um arquivo por período do nome (o formato preferido), em ordem de período."""
    ordem = {f".{f.lower()}": i for i, f in enumerate(formatos)}
    escolhidos: Dict[Tuple[int, int, int], Path] = {}
    for p in sorted(arquivos, key=lambda p: ordem.get(p.suffix.lower(), 99), reverse=True):
        escolhidos[_chave_arquivo(p.name)] = p
    return [escolhidos[c] for c in sorted(escolhidos)]


def montar_planejamento(pasta: Path) -> pd.DataFrame:
    """``planejamento.csv`` (data-model 2.5): os códigos de planejamento de cada CEG em todos os arquivos locais do
    despacho, com o primeiro e o último mês em que aparecem. O código é comparado como número (achado A4); o nome
    publicado só é exibido."""
    partes = []
    for arquivo in _um_por_periodo(_arquivos_locais(pasta, ("PARQUET", "CSV")), ("PARQUET", "CSV")):
        try:
            t = _ler_tabela(arquivo, COLUNAS_LEITURA_PLANEJAMENTO)
        except Exception as exc:  # arquivo ilegível: avisado e fora do planejamento
            logger.warning("Catálogo de usinas: despacho %s não lido (%s).", arquivo.name, exc)
            continue
        if t.empty or not {"ceg", "cod_usinaplanejamento", "din_instante"} <= set(t.columns):
            continue
        codigo = pd.to_numeric(t["cod_usinaplanejamento"], errors="coerce")
        mes = pd.to_datetime(t["din_instante"], errors="coerce").dt.to_period("M")
        nomes = _textos(t["nom_usina"]) if "nom_usina" in t.columns else pd.Series("", index=t.index)
        validas = codigo.notna() & mes.notna() & _textos(t["ceg"]).ne("")
        g = pd.DataFrame({"ceg": _normalizados(t["ceg"]), "codigo": codigo, "mes": mes, "nome": nomes})[validas]
        resumo = g.groupby(["ceg", "codigo"]).agg(primeiro=("mes", "min"), ultimo=("mes", "max"),
                                                    nomes=("nome", lambda s: sorted(set(s) - {""}))).reset_index()
        resumo["arquivo"] = arquivo.name
        partes.append(resumo)
    if not partes:
        return pd.DataFrame(columns=COLUNAS_PLANEJAMENTO)
    todos = pd.concat(partes, ignore_index=True)
    linhas = []
    for (ceg, codigo), g in todos.groupby(["ceg", "codigo"], sort=True):
        nomes = sorted({n for lista in g["nomes"] for n in lista})
        linhas.append({"ceg": ceg, "codigo": int(codigo) if float(codigo).is_integer() else float(codigo),
                       "primeiro_mes": str(g["primeiro"].min()), "ultimo_mes": str(g["ultimo"].max()),
                       "nomes_publicados": "; ".join(nomes), "arquivos": int(g["arquivo"].nunique())})
    return pd.DataFrame(linhas, columns=COLUNAS_PLANEJAMENTO)


def montar_codigos_programacao(pasta: Path) -> pd.DataFrame:
    """Códigos de exibição de todos os arquivos locais da Programação diária (um por dia), com o primeiro e o último dia
    em que aparecem, e a modalidade, o estado e o arquivo do último dia (fase D; rascunho 001, FR-051). O dia vem do nome
    do arquivo, como na Coleta."""
    colunas = ["codigo_exibicao", "modalidade", "estado", "arquivo", "primeiro_dia", "ultimo_dia"]
    partes = []
    for arquivo in _um_por_periodo(_arquivos_locais(pasta, ("PARQUET",)), ("PARQUET",)):
        ano, mes, dia = _chave_arquivo(arquivo.name)
        if not (mes and dia):
            continue
        try:
            t = _ler_tabela(arquivo, COLUNAS_LEITURA_PROGRAMACAO)
        except Exception as exc:  # arquivo ilegível: avisado e fora dos códigos
            logger.warning("Catálogo de usinas: programação %s não lida (%s).", arquivo.name, exc)
            continue
        if t.empty or "cod_exibicaousina" not in t.columns:
            continue
        codigos = pd.DataFrame({"codigo_exibicao": _textos(t["cod_exibicaousina"]),
                                "modalidade": _textos(t.get("nom_modalidadeoperacao", pd.Series("", index=t.index))),
                                "estado": _textos(t.get("id_estado", pd.Series("", index=t.index)))})
        codigos = codigos[codigos["codigo_exibicao"] != ""].drop_duplicates("codigo_exibicao")
        partes.append(codigos.assign(arquivo=arquivo.name, dia=date(ano, mes, dia).isoformat()))
    if not partes:
        return pd.DataFrame(columns=colunas)
    todos = pd.concat(partes, ignore_index=True).sort_values(["dia", "arquivo"], kind="stable")
    ultimos = todos.drop_duplicates("codigo_exibicao", keep="last").set_index("codigo_exibicao")
    dias = todos.groupby("codigo_exibicao")["dia"].agg(["min", "max"])
    tabela = ultimos[["modalidade", "estado", "arquivo"]].join(dias).rename(columns={"min": "primeiro_dia",
                                                                                   "max": "ultimo_dia"})
    return tabela.reset_index().sort_values(["primeiro_dia", "codigo_exibicao"], kind="stable")[colunas] \
        .reset_index(drop=True)


def codigos_vigentes(planejamento: pd.DataFrame) -> Dict[str, List[str]]:
    """{CEG normalizado: códigos (texto do número inteiro) presentes no último mês publicado do despacho}."""
    if planejamento is None or planejamento.empty:
        return {}
    ultimo = planejamento["ultimo_mes"].max()
    vigentes = planejamento[planejamento["ultimo_mes"] == ultimo]
    saida: Dict[str, List[str]] = {}
    for r in vigentes.itertuples():
        saida.setdefault(normalizar_texto(r.ceg), []).append(str(int(float(r.codigo))))
    return saida


def _contagens(tabela: pd.DataFrame, coluna: str, valores: Sequence[str]) -> Dict[str, Tuple[int, int]]:
    """{identificador normalizado: (linhas, linhas com valor)} no arquivo; valor = alguma coluna de valor preenchida."""
    if tabela.empty or coluna not in tabela.columns:
        return {}
    presentes = [v for v in valores if v in tabela.columns]
    com_valor = pd.Series(False, index=tabela.index)
    for v in presentes:
        com_valor |= numero_publicado(tabela[v]).notna()
    chaves = _normalizados(tabela[coluna].map(lambda x: str(int(float(x))) if _numero_inteiro(x) else x))
    agrupado = pd.DataFrame({"chave": chaves, "valor": com_valor}).groupby("chave")["valor"].agg(["size", "sum"])
    return {k: (int(r["size"]), int(r["sum"])) for k, r in agrupado.iterrows() if k}


def _numero_inteiro(valor: Any) -> bool:
    try:
        return float(valor) == int(float(valor))
    except (TypeError, ValueError):
        return False


def _composicao_vigente(composicao: pd.DataFrame, hoje: date) -> pd.DataFrame:
    if composicao.empty:
        return composicao
    inicio = composicao["dat_iniciorelacionamento"].map(_data)
    fim = composicao["dat_fimrelacionamento"].map(_data)
    vigente = inicio.map(lambda d: d is None or d <= hoje) & fim.map(lambda d: d is None or d > hoje)
    return composicao[vigente]


def montar_conjuntos(composicao: pd.DataFrame) -> pd.DataFrame:
    """``conjuntos.csv``: a composição com as datas normalizadas e o tipo pelo CEG de cada usina membro."""
    linhas = [{
        "id_conjunto": r.get("id_ons_conjunto", ""), "nom_conjunto": r.get("nom_conjunto", ""), "ceg": r.get("ceg", ""),
        "id_ons_usina": r.get("id_ons_usina", ""), "nom_usina": r.get("nom_usina", ""),
        "tipo": tipo_do_ceg(r.get("ceg", "")), "tipo_ons": r.get("id_tipousina", ""),
        "inicio": _texto_data(_data(r.get("dat_iniciorelacionamento"))),
        "fim": _texto_data(_data(r.get("dat_fimrelacionamento"))),
        "estado": r.get("estad_id", ""), "subsistema": r.get("id_subsistema", ""),
    } for _, r in composicao.iterrows()]
    return pd.DataFrame(linhas, columns=COLUNAS_CONJUNTOS)


def _unidades_ativas(capacidade: pd.DataFrame, hoje: date) -> pd.DataFrame:
    if capacidade.empty:
        return capacidade
    desativacao = capacidade["dat_desativacao"].map(_data)
    return capacidade[desativacao.map(lambda d: d is None or d > hoje)]


def _programacao(leituras: Leituras, cadastro: pd.DataFrame, conjuntos_ids: Sequence[str]) -> pd.DataFrame:
    """``programacao.csv``: os códigos de todos os arquivos da Programação diária, com o primeiro e o último dia,
    ligados pelo id ONS ou pelo id do conjunto (R5; fase D)."""
    codigos = leituras.codigos_programacao
    if codigos is None or codigos.empty:
        return pd.DataFrame(columns=COLUNAS_PROGRAMACAO)
    # o id sem os espaços das pontas, como na linha da usina (o cadastro do ONS traz ids com espaço no fim)
    ids_usina = {normalizar_texto(i): str(i).strip() for i in cadastro["id_ons"] if str(i).strip()}
    ids_conjunto = {normalizar_texto(c)[len(PREFIXO_CONJUNTO):]: str(c).strip() for c in conjuntos_ids
                    if normalizar_texto(c).startswith(PREFIXO_CONJUNTO)}
    chaves = codigos["codigo_exibicao"].map(normalizar_texto)
    ligados = [ids_usina.get(c) or ids_conjunto.get(c.split("-", 1)[0], "") for c in chaves]
    return codigos.assign(id_usina_ou_conjunto=ligados)[COLUNAS_PROGRAMACAO].reset_index(drop=True)


def _codigos_de(programacao: pd.DataFrame, valor: str) -> List[str]:
    """Códigos ligados à usina ou ao conjunto, em todo o período, na ordem do primeiro dia."""
    return list(programacao.loc[programacao["id_usina_ou_conjunto"] == valor, "codigo_exibicao"]) if valor else []


def _nivel_cobertura(serie: Any, u: Dict[str, Any], leituras: Leituras,
                     lookups: Dict[str, Dict[str, Tuple[int, int]]], programacao: pd.DataFrame,
                     vigentes: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
    """Nível, identificador e contagens de um conjunto de série para uma usina (R3, R31); ``serie`` é a série do
    catálogo (na variante do tipo, nas restrições) ou só a chave do registro."""
    chave, sid = (serie.chave, serie.id) if isinstance(serie, Serie) else (serie, serie)
    linha = {"ceg": u["ceg"], "conjunto_ons": chave, "nivel": "ausente", "identificador": "", "linhas": 0,
             "linhas_sem_valor": 0, "arquivo": "", "publicacao": ""}
    if sid in leituras.series:
        arquivo, publicacao, _ = leituras.series[sid]
        linha.update(arquivo=arquivo.name, publicacao=publicacao)
    if normalizar_texto(u["modalidade"]) in MODALIDADES_TIPO_III:
        return {**linha, "nivel": "agregado"}
    contagens = lookups.get(sid, {})

    def avaliar(coluna: str, valor: str, nivel: str) -> bool:
        linhas, com_valor = contagens.get(normalizar_texto(valor), (0, 0)) if valor else (0, 0)
        if valor and not linha["identificador"]:
            linha.update(identificador=f"{coluna}={valor}", linhas=linhas, linhas_sem_valor=linhas - com_valor)
        if com_valor:
            linha.update(nivel=nivel, identificador=f"{coluna}={valor}", linhas=linhas,
                         linhas_sem_valor=linhas - com_valor)
            return True
        return False

    if chave in ("evt", "hidrologia"):
        avaliar("cod_usina", u["cod_usina"], "proprio")
    elif chave in ("indicadores", "despacho"):
        avaliar("ceg", u["ceg"], "proprio")
    elif chave == "cvu":  # o CVU não tem CEG: pelos códigos de planejamento vigentes no despacho (decisão R9)
        codigos = (vigentes or {}).get(normalizar_texto(u["ceg"]), [])
        linhas = sum(contagens.get(c, (0, 0))[0] for c in codigos)
        com_valor = sum(contagens.get(c, (0, 0))[1] for c in codigos)
        if codigos:
            linha.update(identificador=f"cod_usinaplanejamento={';'.join(codigos)}", linhas=linhas,
                         linhas_sem_valor=linhas - com_valor, nivel="proprio" if com_valor else "ausente")
    elif chave == "disponibilidade":
        avaliar("id_ons", u["id_ons"], "proprio")
    elif chave in ("geracao", "fator_capacidade", "restricao_razao"):
        if not avaliar("id_ons", u["id_ons"], "proprio"):
            avaliar("id_ons", u["id_conjunto"], "conjunto")
    elif chave == "restricao_detalhe":  # só a usina: o id do conjunto não identifica (achado A7)
        avaliar("id_ons", u["id_ons"], "proprio")
    elif chave == "programacao":  # a verificação é no arquivo mais recente (R3): só os códigos presentes nele
        for valor, nivel in ((u["id_ons"], "proprio"), (u["id_conjunto"], "conjunto")):
            codigos = [c for c in _codigos_de(programacao, valor) if normalizar_texto(c) in contagens]
            if not codigos:
                continue
            linhas = sum(contagens.get(normalizar_texto(c), (0, 0))[0] for c in codigos)
            com_valor = sum(contagens.get(normalizar_texto(c), (0, 0))[1] for c in codigos)
            linha.update(nivel=nivel, identificador=f"cod_exibicaousina={';'.join(codigos)}", linhas=linhas,
                         linhas_sem_valor=linhas - com_valor)
            break
    return linha


def montar_usinas(leituras: Leituras, hoje: date) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """``usinas.csv``, ``cobertura.csv`` e ``programacao.csv``, uma linha por linha do cadastro (SC-002)."""
    cadastro = leituras.cadastro
    vigente = _composicao_vigente(leituras.composicao, hoje)
    conjunto_da_usina = {normalizar_texto(r["ceg"]): (r["id_ons_conjunto"], r["nom_conjunto"], r.get("id_subsistema", ""))
                         for _, r in vigente.iterrows() if str(r.get("ceg", "")).strip()}
    ativas = _unidades_ativas(leituras.capacidade, hoje)
    capacidade = {normalizar_texto(ceg): g for ceg, g in ativas.groupby("ceg")} if len(ativas) else {}
    tipos_ons = ({normalizar_texto(ceg): normalizar_texto(g["nom_tipousina"].iloc[0])
                  for ceg, g in leituras.capacidade.groupby("ceg")} if len(leituras.capacidade) else {})
    reservatorios = {normalizar_texto(r["ceg"]): r for _, r in leituras.reservatorio.iterrows()
                     if str(r.get("ceg", "")).strip()}
    programacao = _programacao(leituras, cadastro, list(leituras.composicao.get("id_ons_conjunto", [])))
    vigentes = codigos_vigentes(leituras.planejamento)
    lookups: Dict[str, Dict[str, Tuple[int, int]]] = {}
    for serie in SERIES:
        if serie.id not in leituras.series:
            continue
        _, _, tabela = leituras.series[serie.id]
        coluna = {"evt": "cod_usina", "hidrologia": "cod_usina", "indicadores": "ceg", "programacao": "cod_exibicaousina",
                  "disponibilidade": "id_ons", "geracao": "id_ons", "despacho": "ceg",
                  "cvu": "cod_usinaplanejamento", "fator_capacidade": "id_ons", "restricao_detalhe": "id_ons",
                  "restricao_razao": "id_ons"}[serie.chave]
        valores = [c for c in COLUNAS_SERIES[serie.chave] if c.startswith("val_")] or [coluna]
        if serie.chave == "indicadores":
            lookups[serie.id] = {k: (n, n) for k, (n, _) in _contagens(tabela, coluna, [coluna]).items()}
        else:
            lookups[serie.id] = _contagens(tabela, coluna, valores)

    usinas, coberturas = [], []
    for _, r in cadastro.iterrows():
        ceg = str(r.get("ceg", "")).strip()
        chave = normalizar_texto(ceg)
        tipo = tipo_do_ceg(ceg)
        conjunto = conjunto_da_usina.get(chave, ("", "", ""))
        unidades = capacidade.get(chave)
        reservatorio = reservatorios.get(chave)
        potencia_autorizada = numero_publicado(pd.Series([r.get("val_potenciaautorizada", "")])).iloc[0]
        u: Dict[str, Any] = {
            "ceg": ceg, "id_ons": str(r.get("id_ons", "")).strip(), "nom_usina": str(r.get("nom_usina", "")).strip(),
            "tipo": tipo, "modalidade": str(r.get("nom_modalidadeoperacao", "")).strip(),
            "id_estado": str(r.get("id_estado", "")).strip(), "sgl_centrooperacao": str(r.get("sgl_centrooperacao", "")).strip(),
            "nom_pontoconexao": str(r.get("nom_pontoconexao", "")).strip(), "sts_aneel": str(r.get("sts_aneel", "")).strip(),
            "subsistema": "", "potencia_autorizada_mw": potencia_autorizada, "id_conjunto": conjunto[0],
            "nom_conjunto": conjunto[1], "unidades_geradoras": "", "potencia_efetiva_mw": "",
            "potencias_unidades_mw": "", "combustivel": "",
            "entrada_operacao": "", "cod_usina": "", "nom_reservatorio": "", "id_reservatorio": "",
            "cobertura_resumo": "", "divergencias": "",
        }
        divergencias = []
        if unidades is not None and len(unidades):
            potencias = numero_publicado(unidades["val_potenciaefetiva"])
            entradas = sorted(d for d in unidades["dat_entradaoperacao"].map(_data) if d)
            ordem = pd.to_numeric(unidades["num_unidadegeradora"], errors="coerce").fillna(0).to_numpy().argsort(
                kind="stable")
            u.update(unidades_geradoras=len(unidades), potencia_efetiva_mw=round(float(potencias.sum()), 4),
                     potencias_unidades_mw=";".join(f"{round(float(p), 4):g}" for p in potencias.to_numpy()[ordem]),
                     combustivel="; ".join(dict.fromkeys(_textos(unidades["nom_combustivel"]))),
                     entrada_operacao=_texto_data(entradas[0]) if entradas else "",
                     subsistema=_textos(unidades["id_subsistema"]).iloc[0])
            if pd.notna(potencia_autorizada) and abs(potencia_autorizada - potencias.sum()) > TOLERANCIA_POTENCIA_PERFIL_MW:
                divergencias.append(f"potência autorizada de {fmt_num(potencia_autorizada, 3)} MW diferente da soma das "
                                    f"unidades ativas, {fmt_num(potencias.sum(), 3)} MW")
        if not u["subsistema"] and conjunto[2]:
            u["subsistema"] = conjunto[2]
        tipo_ons = tipos_ons.get(chave, "")
        if tipo in TIPOS_USINA and tipo_ons in TIPOS_ONS and tipo not in TIPOS_ONS[tipo_ons]:
            divergencias.append(f"tipo do ONS {tipo_ons} diferente do tipo do CEG {tipo}")
        if reservatorio is not None:
            cod = reservatorio.get("cod_resplanejamento", "")
            u.update(cod_usina=str(int(float(cod))) if _numero_inteiro(cod) else str(cod).strip(),
                     nom_reservatorio=str(reservatorio.get("nom_reservatorio", "")).strip(),
                     id_reservatorio=str(reservatorio.get("res_id", "")).strip())
        u["divergencias"] = "; ".join(divergencias)
        if tipo in TIPOS_USINA:
            linhas_cobertura = [_nivel_cobertura(s, u, leituras, lookups, programacao, vigentes) for s in SERIES
                                if s.serve(tipo)]
            coberturas += linhas_cobertura
            niveis = {c["nivel"] for c in linhas_cobertura}
            u["cobertura_resumo"] = next((n for n in NIVEIS_ORDEM if n in niveis), "")
        usinas.append(u)
    return (pd.DataFrame(usinas, columns=COLUNAS_USINAS), pd.DataFrame(coberturas, columns=COLUNAS_COBERTURA),
            programacao)


def montar_agregados(raiz_raw: Path, hoje: date) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """``agregados.csv``: Tipo III e MMGD por estado e mês, escolhidos pela modalidade, nunca pelo nome ou pelo id (R21).

    Um valor por hora em cada grupo (o último publicado, como no Tratamento) e as horas sem registro contadas. Devolve
    a tabela, os arquivos usados e os meses sem arquivo local.
    """
    serie = next(s for s in SERIES if s.chave == "geracao")
    pasta = raiz_raw / serie.pasta
    por_mes = {}
    for p in _arquivos_locais(pasta, serie.formatos):
        chave = _chave_arquivo(p.name)
        if chave and chave[1]:
            por_mes.setdefault((chave[0], chave[1]), []).append(p)
    linhas, arquivos, ausentes = [], [], []
    colunas = ["din_instante", "id_estado", "cod_modalidadeoperacao", "nom_tipousina", "nom_usina", "id_ons",
               "val_geracao"]
    for mes in _meses_completos(hoje):
        candidatos = por_mes.get((mes.year, mes.month))
        if not candidatos:
            ausentes.append(str(mes))
            continue
        arquivo = _mais_recente(candidatos, serie.formatos)
        arquivos.append(arquivo.name)
        tabela = _ler_tabela(arquivo, colunas)
        modalidade = _normalizados(tabela["cod_modalidadeoperacao"])
        tabela = tabela[modalidade.isin(MODALIDADES_AGREGADAS_GERACAO)].copy()
        if tabela.empty:
            continue
        tabela["din_instante"] = pd.to_datetime(tabela["din_instante"], errors="coerce")
        tabela["val_geracao"] = numero_publicado(tabela["val_geracao"])
        for coluna in ("id_estado", "cod_modalidadeoperacao", "nom_tipousina", "nom_usina", "id_ons"):
            tabela[coluna] = _textos(tabela[coluna])
        grupo = ["id_estado", "cod_modalidadeoperacao", "nom_tipousina", "nom_usina", "id_ons"]
        tabela = tabela.drop_duplicates(subset=[*grupo, "din_instante"], keep="last")
        horas_do_mes = int((mes.end_time.floor("h") - mes.start_time) / pd.Timedelta(hours=1)) + 1
        for chaves, g in tabela.groupby(grupo, sort=True):
            estado, modalidade_pub, tipo_ons, nome, _ = chaves
            linhas.append({
                "id_estado": estado, "mes": str(mes), "modalidade": modalidade_pub, "tipo_ons": tipo_ons, "grupo": nome,
                "energia_mwh": round(float(g["val_geracao"].sum()), 3), "horas": int(g["val_geracao"].notna().sum()),
                "horas_ausentes": horas_do_mes - int(g["din_instante"].nunique()),
                "previsao": normalizar_texto(modalidade_pub) in MODALIDADES_PREVISAO_GERACAO, "arquivo": arquivo.name,
            })
    return pd.DataFrame(linhas, columns=COLUNAS_AGREGADOS), arquivos, ausentes


@dataclass
class Catalogo:
    """O catálogo montado: as tabelas de ``data/catalogo/`` e o ``catalogo.json``."""

    usinas: pd.DataFrame
    conjuntos: pd.DataFrame
    cobertura: pd.DataFrame
    planejamento: pd.DataFrame
    programacao: pd.DataFrame
    agregados: pd.DataFrame
    json: Dict[str, Any]


def montar_catalogo(raiz_raw: Path, hoje: date, sem_portal: bool) -> Catalogo:
    """Monta o catálogo a partir dos arquivos locais (R2, R3, R21, R31)."""
    leituras = ler_arquivos(raiz_raw)
    usinas, cobertura, programacao = montar_usinas(leituras, hoje)
    agregados, arquivos_agregados, meses_ausentes = montar_agregados(raiz_raw, hoje)
    info = {
        "versao_formato": VERSAO_FORMATO_CATALOGO,
        "montado_em_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "sem_portal": bool(sem_portal),
        "cadastro": {CADASTRAIS[c].pacote: {"arquivo": a.name, "publicacao": p}
                     for c, (a, p) in leituras.arquivos_cadastrais.items()},
        "cobertura": [{"conjunto": s.chave, **({"variante": s.variante} if s.variante else {}), "pacote": s.pacote,
                       "arquivo": leituras.series[s.id][0].name, "publicacao": leituras.series[s.id][1]}
                      for s in SERIES if s.id in leituras.series],
        "agregados": {"meses": [str(m) for m in _meses_completos(hoje) if str(m) not in meses_ausentes],
                      "meses_sem_arquivo": meses_ausentes, "arquivos": arquivos_agregados},
        "contagens": {"por_tipo": {str(k): int(v) for k, v in usinas["tipo"].value_counts().sort_index().items()},
                      "por_estado": {str(k): int(v) for k, v in usinas["id_estado"].value_counts().sort_index().items()}},
    }
    planejamento = leituras.planejamento if leituras.planejamento is not None else pd.DataFrame(
        columns=COLUNAS_PLANEJAMENTO)
    return Catalogo(usinas, montar_conjuntos(leituras.composicao), cobertura, planejamento, programacao, agregados, info)


# ---------------------------------------------------------------------------
# Gravação e leitura
# ---------------------------------------------------------------------------


def gravar_catalogo(catalogo: Catalogo, pasta: Path) -> List[Path]:
    """Grava ``data/catalogo/`` por inteiro, sem ``.bak``: numa pasta temporária, conferida, e só então troca (RT3)."""
    pasta = Path(pasta)
    temporaria = pasta / PASTA_TEMPORARIA
    if temporaria.exists():
        shutil.rmtree(temporaria)
    temporaria.mkdir(parents=True)
    try:
        for chave in ("usinas", "conjuntos", "cobertura", "planejamento", "programacao", "agregados"):
            gravar_csv(getattr(catalogo, chave), temporaria / ARQ[chave], copia=False)
        gravar_bytes(json.dumps(catalogo.json, ensure_ascii=False, indent=1).encode("utf-8"), temporaria / ARQ["catalogo"],
                     copia=False)
        for nome in ARQ.values():
            caminho = temporaria / nome
            if not caminho.is_file() or caminho.stat().st_size == 0:
                raise OSError(f"arquivo do catálogo não gravado: {nome}")
        gravados = []
        for nome in ARQ.values():
            os.replace(temporaria / nome, pasta / nome)
            gravados.append(pasta / nome)
        return gravados
    finally:
        shutil.rmtree(temporaria, ignore_errors=True)


def ler_catalogo(pasta: Path) -> Optional[Dict[str, Any]]:
    """O catálogo gravado (tabelas como texto e ``catalogo.json``); None se ausente ou em formato antigo."""
    pasta = Path(pasta)
    caminho_json = pasta / ARQ["catalogo"]
    if not caminho_json.is_file():
        return None
    info = json.loads(caminho_json.read_text(encoding="utf-8"))
    if info.get("versao_formato") != VERSAO_FORMATO_CATALOGO:
        return None
    tabelas = {c: pd.read_csv(pasta / n, sep=";", dtype=str, keep_default_na=False)
               for c, n in ARQ.items() if c != "catalogo"}
    return {"json": info, **tabelas}


# ---------------------------------------------------------------------------
# Listagem
# ---------------------------------------------------------------------------


def perfis_por_ceg(raiz_usinas: Path) -> Dict[str, str]:
    """{CEG normalizado: slug} dos perfis em ``usinas/*/perfil.toml``; perfil ilegível é ignorado."""
    perfis: Dict[str, str] = {}
    if not Path(raiz_usinas).is_dir():
        return perfis
    for arquivo in sorted(Path(raiz_usinas).glob("*/perfil.toml")):
        try:
            dados = tomllib.loads(arquivo.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
            continue
        ceg = (dados.get("identificacao") or {}).get("ceg")
        if ceg:
            perfis[normalizar_texto(ceg)] = arquivo.parent.name
    return perfis


def filtrar(usinas: pd.DataFrame, estado: Optional[str], tipo: Optional[str], modalidade: Optional[str]) -> pd.DataFrame:
    filtro = pd.Series(True, index=usinas.index)
    if estado:
        filtro &= usinas["id_estado"].str.upper() == estado.upper()
    if tipo:
        filtro &= usinas["tipo"].str.upper() == tipo.upper()
    if modalidade:
        filtro &= usinas["modalidade"].map(normalizar_texto) == normalizar_texto(modalidade)
    return usinas[filtro].sort_values(["id_estado", "tipo", "nom_usina"], kind="stable")


def listar(catalogo: Dict[str, Any], filtradas: pd.DataFrame, raiz_usinas: Path, saida: TextIO) -> None:
    """Tabela das usinas do filtro, com uma coluna de cobertura por conjunto de série (``P``, ``C``, ``A`` ou ``-``)."""
    perfis = perfis_por_ceg(raiz_usinas)
    cobertura = catalogo["cobertura"]
    niveis = {(normalizar_texto(r["ceg"]), r["conjunto_ons"]): r["nivel"] for _, r in cobertura.iterrows()}
    cabecalho = ["UF", "TIPO", "USINA", "CEG", "ID ONS", "MODALIDADE", "MW", "CONJUNTO",
                 *[SIGLAS_SERIES[c] for c in CHAVES_SERIES], "PERFIL"]
    linhas = []
    for _, u in filtradas.iterrows():
        chave = normalizar_texto(u["ceg"])
        letras = [LETRAS.get(niveis.get((chave, c), ""), " ") for c in CHAVES_SERIES]
        potencia = fmt_num(u["potencia_autorizada_mw"], 1) if str(u["potencia_autorizada_mw"]).strip() else ""
        linhas.append([u["id_estado"], u["tipo"], u["nom_usina"][:40], u["ceg"], u["id_ons"], u["modalidade"],
                       potencia, u["id_conjunto"], *letras, perfis.get(chave, "")])
    larguras = [max([len(str(c)) for c in coluna] or [0]) for coluna in zip(cabecalho, *linhas)]
    alinhamento = ["<", "<", "<", "<", "<", "<", ">", "<", *["^"] * len(CHAVES_SERIES), "<"]
    for linha in [cabecalho, *linhas]:
        print("  ".join(f"{str(c):{a}{w}}" for c, a, w in zip(linha, alinhamento, larguras)).rstrip(), file=saida)
    contagem = filtradas["tipo"].value_counts().sort_index()
    print(f"Por tipo: {', '.join(f'{t} {n}' for t, n in contagem.items()) or 'nenhuma'}.", file=saida)


# ---------------------------------------------------------------------------
# Comando
# ---------------------------------------------------------------------------


def executar_usinas(estado: Optional[str] = None, tipo: Optional[str] = None, modalidade: Optional[str] = None,
                    sem_portal: bool = False, forcar_download: bool = False, raiz_raw: Optional[Path] = None,
                    pasta_catalogo: Optional[Path] = None, raiz_usinas: Optional[Path] = None,
                    hoje: Optional[date] = None, saida: Optional[TextIO] = None) -> int:
    """Executa o comando ``usinas`` e devolve o código de saída do contrato."""
    raiz_raw = Path(raiz_raw or caminhos.RAW_DATA_DIR)
    pasta_catalogo = Path(pasta_catalogo or caminhos.pasta_catalogo())
    raiz_usinas = Path(raiz_usinas or caminhos.USINAS_DIR)
    hoje = hoje or date.today()
    saida = saida or sys.stdout
    try:
        if not sem_portal:
            try:
                sincronizar_catalogo(raiz_raw, hoje, force=forcar_download)
            except CadastralNaoObtido:
                raise
            except Exception as exc:  # catálogo do ONS inacessível depois das tentativas
                logger.error("Catálogo do ONS inacessível: %s", exc)
                return CODIGO_ERRO
        catalogo = montar_catalogo(raiz_raw, hoje, sem_portal)
        pasta_catalogo.mkdir(parents=True, exist_ok=True)
        gravar_catalogo(catalogo, pasta_catalogo)
    except CadastralNaoObtido as exc:
        logger.error("Conjunto cadastral do ONS não obtido (%s): %s.", exc.pacote, exc.motivo)
        return CODIGO_NAO_OBTIDO
    except KeyboardInterrupt:
        logger.error("Catálogo de usinas interrompido pelo usuário.")
        return CODIGO_ERRO
    except Exception as exc:
        logger.exception("Catálogo de usinas: erro inesperado: %s", exc)
        return CODIGO_ERRO

    gravado = ler_catalogo(pasta_catalogo)  # a listagem sai sempre dos arquivos gravados
    if gravado is None:
        logger.error("Catálogo de usinas não encontrado em %s depois da gravação.", pasta_catalogo)
        return CODIGO_ERRO
    usinas = gravado["usinas"]
    divergentes = int(usinas["divergencias"].str.contains("tipo do ONS", regex=False).sum())
    if divergentes:
        logger.warning('%d usinas com o tipo publicado pelo ONS diferente do tipo do CEG; ver a coluna "divergencias" '
                       "de data/catalogo/usinas.csv.", divergentes)
    filtradas = filtrar(usinas, estado, tipo, modalidade)
    if filtradas.empty:
        descricao = ", ".join(f"{n} {v}" for n, v in (("estado", estado), ("tipo", tipo), ("modalidade", modalidade))
                              if v) or "sem filtro"
        logger.warning("Nenhuma usina no filtro (%s).", descricao)
    else:
        listar(gravado, filtradas, raiz_usinas, saida)
    publicado = gravado["json"]["cadastro"].get(CONJUNTO_CADASTRO, {}).get("publicacao") or "data não registrada"
    logger.info("Catálogo de usinas: %d linhas do cadastro (publicado em %s), %d no filtro. Pasta: data/catalogo/",
                len(usinas), publicado, len(filtradas))
    return CODIGO_SUCESSO
