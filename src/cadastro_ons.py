"""Ficha cadastral da usina no ONS: modalidade de operação, centro de operação e ponto de conexão (spec 006, US6).

Conjunto "modalidade-usina": um único arquivo, sem série histórica (o ONS o regrava diariamente). A ficha
é localizada pelo CEG da ANEEL, identificador regulatório único (constituição 1.2.0, princípio IV); id ONS
e estado são conferidos e, se diferirem, aparecem como divergências da ficha, assim como a potência
autorizada diferente da potência instalada do projeto (FR-030). Os homônimos são contados, não extraídos.
As versões anteriores do cadastro ficam preservadas pelo coletor (spec 005), o que dá o histórico.
A leitura do arquivo tem auditoria própria (FR-005): linhas lidas, linhas de formato irregular (não extraídas
e avisadas no log, princípio IV), linhas da usina, identificação parcial e situação.
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from src.collector import _local_filename, download_resource, fetch_ckan_package_metadata, load_manifest, save_manifest
from src.config import (
    AUDITORIA_CADASTRO_FILE,
    CADASTRO_FILE,
    CADASTRO_RAW_DIR,
    CEG_USINA,
    CONJUNTO_CADASTRO,
    ESTADO_USINA,
    ID_ONS_USINA,
    NOME_RESERVATORIO_REFERENCIA,
    ONS_CKAN_PACKAGE_SHOW_URL,
    POTENCIA_AUTORIZADA_ESPERADA_MW,
    PROCESSED_DATA_DIR,
    RAW_MANIFEST_FILE,
)
from src.conjuntos_ons import avisar_linhas_irregulares, ler_csv_texto
from src.dicionarios_ons import atualizar_dicionarios
from src.formatacao import fmt_num
from src.logger import NIVEIS_LOG, configurar_nivel_log, setup_logger
from src.models import RecursoONS
from src.persistencia import gravar_csv

logger = setup_logger("cadastro_ons")

COLUNAS_FICHA: List[str] = [
    "nom_usina", "ceg", "id_ons", "nom_modalidadeoperacao", "sgl_centrooperacao", "nom_pontoconexao",
    "val_potenciaautorizada", "id_estado", "sts_aneel", "data_consulta_utc", "arquivo_origem", "homonimos",
    "linhas_so_identificador", "linhas_so_conferencia", "divergencias",
]
COLUNAS_AUDITORIA_CADASTRO: List[str] = [
    "arquivo", "formato", "linhas_lidas", "linhas_formato_irregular", "linhas_usina", "linhas_so_identificador",
    "linhas_so_conferencia", "status", "mensagem",
]
COLUNAS_OBRIGATORIAS: Tuple[str, ...] = ("nom_usina", "ceg", "id_ons", "id_estado")


def _normalizar(serie: pd.Series) -> pd.Series:
    def _sem_acento(valor: str) -> str:
        return "".join(c for c in unicodedata.normalize("NFKD", valor) if not unicodedata.combining(c))

    return serie.fillna("").astype(str).map(_sem_acento).str.strip().str.upper()


def selecionar_recurso(metadados: Dict[str, Any]) -> Optional[RecursoONS]:
    """Recurso CSV do cadastro (o dicionário de dados é tratado em dicionarios_ons)."""
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


def sincronizar_cadastro(pasta_raw: Path = CADASTRO_RAW_DIR, force: bool = False) -> Optional[str]:
    """Baixa o cadastro se a versão publicada mudou; devolve o nome do arquivo local (None se falhar)."""
    pasta_raw = Path(pasta_raw)
    pasta_raw.mkdir(parents=True, exist_ok=True)
    recurso = selecionar_recurso(fetch_ckan_package_metadata(f"{ONS_CKAN_PACKAGE_SHOW_URL}{CONJUNTO_CADASTRO}"))
    if recurso is None:
        logger.error("Cadastro de modalidade das usinas: nenhum recurso CSV publicado no catálogo.")
        return None
    manifesto_path = pasta_raw / RAW_MANIFEST_FILE.name
    manifesto = load_manifest(manifesto_path)
    try:
        download_resource(recurso, destination_dir=pasta_raw, force=force, manifest=manifesto)
    except Exception as exc:
        logger.error("Cadastro de modalidade das usinas não obtido (%s); a cópia local, se houver, será usada.", exc)
    finally:
        save_manifest(manifesto, manifesto_path)
    return _local_filename(recurso)


def ler_cadastro(caminho: Path) -> Tuple[pd.DataFrame, List[int]]:
    """Cadastro completo, com textos sem espaços nas pontas, e os números das linhas de formato irregular.

    O arquivo do ONS completa campos com espaços. Linhas com nº de campos diferente do cabeçalho ficam fora da
    tabela e são avisadas no log (princípio IV); uma linha irregular de outra usina não interrompe a etapa.
    """
    tabela, irregulares = ler_csv_texto(Path(caminho))
    avisar_linhas_irregulares(CONJUNTO_CADASTRO, Path(caminho).name, irregulares)
    tabela.columns = [c.strip() for c in tabela.columns]
    faltantes = [c for c in COLUNAS_OBRIGATORIAS if c not in tabela.columns]
    if faltantes:
        raise ValueError(f"colunas ausentes no cadastro: {faltantes}")
    return tabela.apply(lambda coluna: coluna.str.strip()), irregulares


def _mascaras(cadastro: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Linhas com o CEG do projeto, linhas com a conferência (id ONS e estado) e homônimos (nome sem o CEG)."""
    ceg = _normalizar(cadastro["ceg"]) == CEG_USINA.upper()
    conferencia = (_normalizar(cadastro["id_ons"]) == ID_ONS_USINA.upper()) & (_normalizar(cadastro["id_estado"]) == ESTADO_USINA)
    homonimos = _normalizar(cadastro["nom_usina"]).str.contains(NOME_RESERVATORIO_REFERENCIA, regex=False) & ~ceg
    return ceg, conferencia, homonimos


def auditoria_cadastro(
    arquivo: str,
    cadastro: Optional[pd.DataFrame] = None,
    irregulares: Iterable[int] = (),
    erro: str = "",
) -> pd.DataFrame:
    """Auditoria da leitura do cadastro (uma linha), nas colunas da auditoria dos conjuntos horários (FR-005).

    ``linhas_usina`` conta as linhas com o CEG do projeto, que localiza a ficha. Sem ``cadastro`` (arquivo que não
    pôde ser lido), a situação é ``FALHA``; sem o CEG no arquivo, ``SEM_REGISTROS``.
    """
    irregulares = list(irregulares)
    linha: Dict[str, Any] = {
        "arquivo": arquivo, "formato": "CSV", "linhas_lidas": 0, "linhas_formato_irregular": len(irregulares),
        "linhas_usina": 0, "linhas_so_identificador": 0, "linhas_so_conferencia": 0, "status": "FALHA", "mensagem": erro,
    }
    if cadastro is not None:
        ceg, conferencia, _ = _mascaras(cadastro)
        linha.update(
            linhas_lidas=len(cadastro) + len(irregulares), linhas_usina=int(ceg.sum()),
            linhas_so_identificador=int((ceg & ~conferencia).sum()),
            linhas_so_conferencia=int((~ceg & conferencia).sum()),
            status="PROCESSADO" if ceg.any() else "SEM_REGISTROS",
        )
    return pd.DataFrame([linha], columns=COLUNAS_AUDITORIA_CADASTRO)


def extrair_ficha(cadastro: pd.DataFrame, data_consulta: str, arquivo: str) -> pd.DataFrame:
    """Ficha da usina (uma linha) com homônimos e divergências; vazia se o CEG do projeto não constar."""
    ceg, conferencia, homonimos = _mascaras(cadastro)
    if not ceg.any():
        return pd.DataFrame(columns=COLUNAS_FICHA)
    linha = cadastro[ceg].iloc[0]
    potencia = pd.to_numeric(pd.Series([linha.get("val_potenciaautorizada", "")]), errors="coerce").iloc[0]
    divergencias = []
    if pd.isna(potencia) or abs(potencia - POTENCIA_AUTORIZADA_ESPERADA_MW) > 0.001:
        divergencias.append(f"potência autorizada de {fmt_num(potencia, 1)} MW (projeto: "
                            f"{fmt_num(POTENCIA_AUTORIZADA_ESPERADA_MW, 0)} MW)")
    if linha.get("id_estado", "").upper() != ESTADO_USINA:
        divergencias.append(f"estado {linha.get('id_estado', '') or 'não informado'} (projeto: {ESTADO_USINA})")
    if linha.get("id_ons", "").upper() != ID_ONS_USINA:
        divergencias.append(f"id ONS {linha.get('id_ons', '') or 'não informado'} (projeto: {ID_ONS_USINA})")
    if int(ceg.sum()) > 1:
        divergencias.append(f"{int(ceg.sum())} linhas com o CEG do projeto (usada a primeira)")
    ficha = {coluna: linha.get(coluna, "") for coluna in COLUNAS_FICHA}
    ficha.update(
        val_potenciaautorizada=potencia, data_consulta_utc=data_consulta, arquivo_origem=arquivo,
        homonimos=int(homonimos.sum()), linhas_so_identificador=int((ceg & ~conferencia).sum()),
        linhas_so_conferencia=int((~ceg & conferencia).sum()), divergencias="; ".join(divergencias),
    )
    return pd.DataFrame([ficha], columns=COLUNAS_FICHA)


def executar_cadastro_ons(
    baixar: bool = True,
    force: bool = False,
    periodo: Optional[Tuple[pd.Timestamp, pd.Timestamp]] = None,
    pasta_raw: Path = CADASTRO_RAW_DIR,
    pasta_saida: Path = PROCESSED_DATA_DIR,
    dicionarios: bool = True,
) -> int:
    """Obtém o cadastro, extrai a ficha da usina e grava a ficha e a auditoria da leitura.

    ``periodo`` é ignorado (o cadastro não tem série). Retorna 0 em caso de sucesso, 1 em erro e 2 se o cadastro
    não pôde ser obtido ou lido ou se a usina não consta dele.
    """
    try:
        pasta_raw, pasta_saida = Path(pasta_raw), Path(pasta_saida)
        nome: Optional[str] = None
        if baixar:
            nome = sincronizar_cadastro(pasta_raw, force)
            if dicionarios:
                atualizar_dicionarios([CONJUNTO_CADASTRO], raiz_raw=pasta_raw.parent, pasta_saida=pasta_saida)
        if nome is None:
            locais = sorted(pasta_raw.glob("*.csv")) if pasta_raw.exists() else []
            nome = locais[0].name if locais else None
        if nome is None or not (pasta_raw / nome).exists():
            logger.error("Cadastro de modalidade das usinas indisponível em %s.", pasta_raw)
            return 2
        entrada = load_manifest(pasta_raw / RAW_MANIFEST_FILE.name).get(nome) or {}
        try:
            cadastro, irregulares = ler_cadastro(pasta_raw / nome)
        except Exception as exc:
            logger.error("Cadastro de modalidade das usinas: não foi possível ler %s: %s", nome, exc)
            gravar_csv(auditoria_cadastro(nome, erro=str(exc)), pasta_saida / AUDITORIA_CADASTRO_FILE.name)
            return 2
        ficha = extrair_ficha(cadastro, str(entrada.get("registrado_em_utc", "")), nome)
        gravar_csv(ficha, pasta_saida / CADASTRO_FILE.name)
        gravar_csv(auditoria_cadastro(nome, cadastro, irregulares), pasta_saida / AUDITORIA_CADASTRO_FILE.name)
        if ficha.empty:
            logger.error("A usina (CEG %s) não consta do cadastro de modalidade das usinas do ONS.", CEG_USINA)
            return 2
        f = ficha.iloc[0]
        logger.info("Ficha cadastral: %s · %s · %s · %s · %s MW · %d homônimos.", f["nom_usina"],
                    f["nom_modalidadeoperacao"], f["sgl_centrooperacao"], f["nom_pontoconexao"],
                    fmt_num(f["val_potenciaautorizada"], 1), f["homonimos"])
        if f["divergencias"]:
            logger.warning("Ficha cadastral diverge dos parâmetros do projeto: %s", f["divergencias"])
        return 0
    except Exception as exc:
        logger.exception("Erro ao processar o cadastro de modalidade das usinas: %s", exc)
        return 1


def carregar_cadastro_processado(pasta: Path = PROCESSED_DATA_DIR) -> Optional[pd.DataFrame]:
    """Ficha gravada; None se a etapa ainda não foi executada ou a ficha está vazia."""
    caminho = Path(pasta) / CADASTRO_FILE.name
    if not caminho.exists():
        return None
    try:
        ficha = pd.read_csv(caminho, sep=";", keep_default_na=False)
    except pd.errors.EmptyDataError:
        return None
    return ficha if len(ficha) else None


def carregar_auditoria_cadastro(pasta: Path = PROCESSED_DATA_DIR) -> Optional[pd.DataFrame]:
    """Auditoria gravada da leitura do cadastro; None se a etapa ainda não a gerou."""
    caminho = Path(pasta) / AUDITORIA_CADASTRO_FILE.name
    if not caminho.exists():
        return None
    try:
        return pd.read_csv(caminho, sep=";", keep_default_na=False)
    except pd.errors.EmptyDataError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Ficha cadastral da UHE São Domingos no ONS (modalidade das usinas).")
    parser.add_argument("--no-download", action="store_true", help="Usa apenas o cadastro já baixado.")
    parser.add_argument("--force-download", action="store_true", help="Baixa novamente o cadastro.")
    parser.add_argument("--log-level", choices=NIVEIS_LOG, default="INFO", help="Nível de log de todos os módulos.")
    args = parser.parse_args()
    configurar_nivel_log(args.log_level)
    sys.exit(executar_cadastro_ons(baixar=not args.no_download, force=args.force_download))


if __name__ == "__main__":
    main()
