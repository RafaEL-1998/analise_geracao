"""Indicadores oficiais de disponibilidade por unidade geradora publicados pelo ONS.

Complementa a base de Energia Vertida Turbinável com quatro conjuntos do Portal de Dados
Abertos do ONS, filtrados pelo CEG da usina e recortados no período da base de EVT:

- ind_disponibilidade_fgeracao_uge_mensal e _anual: DISPF, INDISPPF, INDISPFF, DMDFF, FDFF e
  TDFF por unidade geradora (Submódulo 9.2 dos Procedimentos de Rede);
- taxa_teif_teip_parametro: horas mensais de cada unidade geradora por estado operativo,
  usadas pelo ONS no cálculo da TEIFa e da TEIP;
- taxa_teif_teip: TEIFa e TEIP da usina (janela de 60 meses, versão mais recente).

Nenhum desses conjuntos traz eventos individuais (início, fim e causa de cada desligamento);
eles informam quanto tempo cada unidade passou em cada estado, não o motivo.

Os arquivos brutos ficam em data/raw/indicadores_ons/<conjunto>/, fora da pasta varrida pelo
filtro da base de EVT, cada conjunto com seu manifesto de versões.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.collector import (
    download_resource,
    fetch_ckan_package_metadata,
    load_manifest,
    parse_ckan_resources,
    save_manifest,
)
from src.config import (
    AUDITORIA_INDICADORES_FILE,
    CEG_USINA,
    CONJUNTOS_INDICADORES_ONS,
    CONSOLIDATED_FILE,
    DIVERGENCIAS_INDICADORES_FILE,
    HORAS_ESTADO_UG_FILE,
    ID_ONS_USINA,
    INDICADORES_RAW_DIR,
    INDICADORES_UG_ANUAL_FILE,
    INDICADORES_UG_MENSAL_FILE,
    INDICADORES_XLSX_FILE,
    ONS_CKAN_PACKAGE_SHOW_URL,
    PROCESSED_DATA_DIR,
    RAW_MANIFEST_FILE,
    TAXAS_TEIFA_TEIP_FILE,
    TOLERANCIA_DIVERGENCIA_HORAS,
    TREATED_FILE_PARQUET,
)
from src.logger import NIVEIS_LOG, configurar_nivel_log, setup_logger
from src.models import RecursoONS
from src.persistencia import gravar_csv, gravar_planilha
from src.dicionarios_ons import atualizar_dicionarios

logger = setup_logger("indicadores_ons")

MENSAL = "ind_disponibilidade_fgeracao_uge_mensal"
ANUAL = "ind_disponibilidade_fgeracao_uge_anual"
PARAMETROS = "taxa_teif_teip_parametro"
TAXAS = "taxa_teif_teip"

# Coluna que traz o CEG em cada conjunto
COLUNA_CEG: Dict[str, str] = {MENSAL: "ceg", ANUAL: "ceg", PARAMETROS: "cod_ceg", TAXAS: "cod_ceg"}

INDICADORES_UG: List[str] = ["val_dispf", "val_indisppf", "val_indispff", "val_dmdff", "val_fdff", "val_tdff"]

# Siglas das horas publicadas em taxa_teif_teip_parametro. O dicionário de dados do ONS não as
# define; as descrições seguem a nomenclatura da metodologia de apuração da TEIFa e da TEIP.
INSUMOS_HORAS: Dict[str, str] = {
    "HP": "horas do período",
    "HS": "horas em serviço",
    "HRD": "horas em reserva desligada (unidade disponível, parada)",
    "HDP": "horas de desligamento programado",
    "HDF": "horas de desligamento forçado",
    "HDCE": "horas de desligamento por causa externa",
    "HEDP": "horas equivalentes de desligamento programado (limitação de potência)",
    "HEDF": "horas equivalentes de desligamento forçado (limitação de potência)",
}
# Parcelas que somam as horas do período (identidade conferida na validação)
PARCELAS_HP: List[str] = ["HS", "HRD", "HDP", "HDF", "HDCE", "HEDP", "HEDF"]
# Diferença máxima (h) aceita na identidade HP = soma das parcelas
TOLERANCIA_IDENTIDADE_HORAS: float = 0.1

_RE_ANO_ARQUIVO = re.compile(r"_(\d{4})\.csv$", re.IGNORECASE)
_RE_NUMERO_UG = re.compile(r"(\d+)\s+[A-Z]{2}$")


@dataclass
class IndicadoresONS:
    """Tabelas tratadas dos indicadores oficiais, já recortadas no período da base de EVT."""

    ug_mensal: pd.DataFrame
    ug_anual: pd.DataFrame
    horas_estado: pd.DataFrame
    taxas: pd.DataFrame
    divergencias: pd.DataFrame = field(default_factory=pd.DataFrame)
    auditoria: pd.DataFrame = field(default_factory=pd.DataFrame)


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------


def url_pacote(conjunto: str) -> str:
    return f"{ONS_CKAN_PACKAGE_SHOW_URL}{conjunto}"


def ano_do_recurso(recurso: RecursoONS) -> Optional[int]:
    """Ano no nome do arquivo (ex.: ..._MENSAL_2024.csv); None para arquivos únicos."""
    nome = recurso.url_download.split("/")[-1].split("?")[0]
    achado = _RE_ANO_ARQUIVO.search(nome)
    return int(achado.group(1)) if achado else None


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
    destino: Path = INDICADORES_RAW_DIR,
    force: bool = False,
) -> Dict[str, List[RecursoONS]]:
    """Baixa os CSVs dos quatro conjuntos que cobrem os anos informados (cache por versão)."""
    resultado: Dict[str, List[RecursoONS]] = {}
    for conjunto in CONJUNTOS_INDICADORES_ONS:
        pasta = destino / conjunto
        pasta.mkdir(parents=True, exist_ok=True)
        recursos = selecionar_recursos(
            parse_ckan_resources(fetch_ckan_package_metadata(url_pacote(conjunto))), ano_inicio, ano_fim
        )
        manifesto_path = pasta / RAW_MANIFEST_FILE.name
        manifesto = load_manifest(manifesto_path)
        try:
            for idx, r in enumerate(recursos, start=1):
                logger.info("[%s %d/%d] Sincronizando %s", conjunto, idx, len(recursos), r.nome_recurso)
                download_resource(r, destination_dir=pasta, force=force, manifest=manifesto)
        finally:
            save_manifest(manifesto, manifesto_path)
        resultado[conjunto] = recursos
    return resultado


# ---------------------------------------------------------------------------
# Leitura e filtragem
# ---------------------------------------------------------------------------


def _ler_csv(caminho: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(caminho, sep=";", dtype=str, encoding="utf-8", keep_default_na=False)
    except UnicodeDecodeError:
        logger.info("Arquivo %s não é UTF-8 válido; relendo como Latin-1.", caminho.name)
        return pd.read_csv(caminho, sep=";", dtype=str, encoding="latin-1", keep_default_na=False)


def filtrar_csv(caminho: Path, conjunto: str, ceg: str = CEG_USINA) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """Lê um CSV do conjunto e devolve as linhas da usina (texto sem espaços nas bordas)."""
    coluna = COLUNA_CEG[conjunto]
    auditoria: Dict[str, object] = {"conjunto": conjunto, "arquivo": caminho.name}
    try:
        bruto = _ler_csv(caminho)
    except Exception as e:  # arquivo corrompido ou vazio
        logger.error("Falha ao ler %s: %s", caminho.name, e)
        return pd.DataFrame(), {**auditoria, "linhas_lidas": 0, "linhas_usina": 0, "status": "FALHA"}
    if coluna not in bruto.columns:
        logger.error("Arquivo %s sem a coluna %s.", caminho.name, coluna)
        return pd.DataFrame(), {**auditoria, "linhas_lidas": len(bruto), "linhas_usina": 0, "status": "FALHA"}
    bruto.columns = [c.strip() for c in bruto.columns]
    linhas = bruto[bruto[coluna].str.strip() == ceg].copy()
    for c in linhas.columns:
        linhas[c] = linhas[c].str.strip()
    linhas["arquivo_origem"] = caminho.name
    status = "PROCESSADO" if len(linhas) else "SEM_REGISTROS"
    return linhas, {**auditoria, "linhas_lidas": len(bruto), "linhas_usina": len(linhas), "status": status}


def carregar_conjunto(conjunto: str, pasta_raiz: Path = INDICADORES_RAW_DIR) -> Tuple[pd.DataFrame, List[Dict[str, object]]]:
    """Filtra todos os CSVs baixados de um conjunto, em ordem de nome."""
    arquivos = sorted((pasta_raiz / conjunto).glob("*.csv"))
    partes, auditorias = [], []
    for arquivo in arquivos:
        linhas, auditoria = filtrar_csv(arquivo, conjunto)
        auditorias.append(auditoria)
        if len(linhas):
            partes.append(linhas)
    logger.info("%s: %d arquivos lidos, %d linhas da usina.", conjunto, len(arquivos),
                sum(int(a["linhas_usina"]) for a in auditorias))
    return (pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()), auditorias


# ---------------------------------------------------------------------------
# Tratamento
# ---------------------------------------------------------------------------


def _numerico(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def _deduplicar(df: pd.DataFrame, chave: List[str], nome: str) -> pd.DataFrame:
    """Mantém a última ocorrência de cada chave (arquivo lido por último) e registra conflitos."""
    duplicadas = df.duplicated(chave, keep=False)
    if duplicadas.any():
        logger.warning("%s: %d linhas com chave repetida %s; prevalece o arquivo lido por último.",
                       nome, int(duplicadas.sum()), chave)
    return df.drop_duplicates(chave, keep="last")


def tratar_indicadores_ug(df: pd.DataFrame, anual: bool) -> pd.DataFrame:
    """Tipagem dos indicadores por unidade geradora (mensal ou anual)."""
    if df.empty:
        return pd.DataFrame()
    t = pd.DataFrame({
        "ug": _numerico(df["num_unidadegeradora"]).astype("Int64"),
        "cod_equipamento": df["cod_equipamento"],
        "potencia_mw": _numerico(df["val_potencia"]),
    })
    if anual:
        t.insert(0, "ano", _numerico(df["din_ano"]).astype("Int64"))
    else:
        t.insert(0, "mes", pd.to_datetime(df["dat_mesreferencia"], errors="coerce"))
    for coluna in INDICADORES_UG:
        t[coluna.removeprefix("val_")] = _numerico(df[coluna])
    t["id_usina"] = df["id_usina"]
    t["agente"] = df["nom_agenteproprietario"]
    t["modalidade"] = df["nom_modalidadeoperacao"]
    t["arquivo_origem"] = df["arquivo_origem"]
    periodo = "ano" if anual else "mes"
    t = _deduplicar(t, [periodo, "ug"], "indicadores anuais" if anual else "indicadores mensais")
    return t.sort_values([periodo, "ug"]).reset_index(drop=True)


def numero_ug(nome_unidade: str) -> Optional[int]:
    """Número da unidade em nomes como 'UG   24 MW SAO DOMINGOS              1 MS'."""
    achado = _RE_NUMERO_UG.search(str(nome_unidade).strip())
    return int(achado.group(1)) if achado else None


def tratar_horas_estado(df: pd.DataFrame) -> pd.DataFrame:
    """Horas por estado operativo, por unidade e mês (versão mais recente de cada parâmetro)."""
    if df.empty:
        return pd.DataFrame()
    longo = pd.DataFrame({
        "mes": pd.to_datetime(df["dat_periodo"], format="%m/%Y", errors="coerce"),
        "ug": df["nom_unidadegeradora"].map(numero_ug).astype("Int64"),
        "insumo": df["nom_tpinsumo"].str.upper(),
        "horas": _numerico(df["val_parametro"]),
        "num_versao": _numerico(df["num_versao"]),
    })
    longo = longo.sort_values("num_versao").drop_duplicates(["mes", "ug", "insumo"], keep="last")
    largo = longo.pivot_table(index=["mes", "ug"], columns="insumo", values="horas", aggfunc="first")
    largo = largo.reindex(columns=list(INSUMOS_HORAS))
    largo["num_versao"] = longo.groupby(["mes", "ug"])["num_versao"].max()
    largo = largo.reset_index()
    largo.columns.name = None
    largo["residuo_identidade_h"] = largo["HP"] - largo[PARCELAS_HP].sum(axis=1, min_count=1)
    return largo.sort_values(["mes", "ug"]).reset_index(drop=True)


def tratar_taxas(df: pd.DataFrame) -> pd.DataFrame:
    """TEIFa e TEIP por mês (versão mais recente), como fração entre 0 e 1."""
    if df.empty:
        return pd.DataFrame()
    longo = pd.DataFrame({
        "mes": pd.to_datetime(df["din_mes"], errors="coerce"),
        "taxa": df["nom_taxa"].str.upper(),
        "valor": _numerico(df["val_taxa"]),
        "num_versao": _numerico(df["num_versao"]),
        "din_calculo": pd.to_datetime(df.get("din_calculo", df.get("din_instante")), errors="coerce"),
    })
    longo = longo.sort_values("num_versao").drop_duplicates(["mes", "taxa"], keep="last")
    largo = longo.pivot_table(index="mes", columns="taxa", values="valor", aggfunc="first")
    largo = largo.rename(columns={"TEIFA": "teifa", "TEIP": "teip"}).reindex(columns=["teifa", "teip"])
    largo["num_versao"] = longo.groupby("mes")["num_versao"].max()
    largo["din_calculo"] = longo.groupby("mes")["din_calculo"].max()
    return largo.reset_index().sort_values("mes").reset_index(drop=True)


def recortar_periodo(ind: IndicadoresONS, inicio: pd.Timestamp, fim: pd.Timestamp) -> IndicadoresONS:
    """Mantém os meses e anos que se sobrepõem ao período [inicio, fim] da base de EVT."""
    mes_ini = pd.Timestamp(inicio).to_period("M").to_timestamp()
    mes_fim = pd.Timestamp(fim).to_period("M").to_timestamp()

    def _meses(t: pd.DataFrame) -> pd.DataFrame:
        if t.empty:
            return t
        return t[(t["mes"] >= mes_ini) & (t["mes"] <= mes_fim)].reset_index(drop=True)

    anual = ind.ug_anual
    if not anual.empty:
        anual = anual[(anual["ano"] >= mes_ini.year) & (anual["ano"] <= mes_fim.year)].reset_index(drop=True)
    return IndicadoresONS(
        ug_mensal=_meses(ind.ug_mensal),
        ug_anual=anual,
        horas_estado=_meses(ind.horas_estado),
        taxas=_meses(ind.taxas),
        divergencias=ind.divergencias,
        auditoria=ind.auditoria,
    )


def comparar_indicadores_e_horas(ug_mensal: pd.DataFrame, horas: pd.DataFrame,
                                  tolerancia_h: float = TOLERANCIA_DIVERGENCIA_HORAS) -> pd.DataFrame:
    """Meses em que INDISPPF/INDISPFF (em horas) e as horas HDP/HDF do TEIP não conferem."""
    colunas = ["mes", "ug", "HP", "HS", "HRD", "HDP", "horas_programadas_indisppf", "HDF",
               "horas_forcadas_indispff", "diferenca_programada_h", "diferenca_forcada_h"]
    if ug_mensal.empty or horas.empty:
        return pd.DataFrame(columns=colunas)
    m = horas.merge(ug_mensal[["mes", "ug", "indisppf", "indispff"]], on=["mes", "ug"], how="inner")
    m["horas_programadas_indisppf"] = m["indisppf"] / 100.0 * m["HP"]
    m["horas_forcadas_indispff"] = m["indispff"] / 100.0 * m["HP"]
    m["diferenca_programada_h"] = m["horas_programadas_indisppf"] - m["HDP"]
    m["diferenca_forcada_h"] = m["horas_forcadas_indispff"] - m["HDF"]
    fora = (m["diferenca_programada_h"].abs() > tolerancia_h) | (m["diferenca_forcada_h"].abs() > tolerancia_h)
    return m.loc[fora, colunas].reset_index(drop=True)


def _janela(horas: pd.DataFrame, mes_fim: pd.Timestamp, meses: int) -> pd.DataFrame:
    inicio = pd.Timestamp(mes_fim) - pd.DateOffset(months=meses - 1)
    return horas[(horas["mes"] >= inicio) & (horas["mes"] <= mes_fim)]


def _peso(h: pd.DataFrame) -> pd.Series:
    """Potência de cada unidade (ponderação das taxas); 1 se a potência não estiver disponível."""
    if "potencia_mw" in h.columns:
        return h["potencia_mw"].fillna(1.0)
    return pd.Series(1.0, index=h.index)


def _taxas_da_janela(h: pd.DataFrame) -> Tuple[float, float]:
    """TEIFa = Σ P·(HDF + HEDF) ÷ Σ P·(HP − HDP − HEDP); TEIP = Σ P·(HDP + HEDP) ÷ Σ P·HP."""
    p = _peso(h)
    base_teifa = float((p * (h["HP"] - h["HDP"] - h["HEDP"])).sum())
    base_teip = float((p * h["HP"]).sum())
    teifa = float((p * (h["HDF"] + h["HEDF"])).sum()) / base_teifa if base_teifa else float("nan")
    teip = float((p * (h["HDP"] + h["HEDP"])).sum()) / base_teip if base_teip else float("nan")
    return teifa, teip


def recalcular_taxas(horas: pd.DataFrame, taxas: pd.DataFrame, janela_meses: int = 60) -> pd.DataFrame:
    """Recalcula TEIFa e TEIP de cada mês publicado a partir das horas por estado operativo.

    Só há recálculo quando as horas cobrem a janela inteira; nos demais meses as colunas
    recalculadas ficam vazias.
    """
    colunas = ["mes", "meses_na_janela", "teifa_publicada", "teifa_recalculada", "teip_publicada",
               "teip_recalculada", "diferenca_teifa_pp", "diferenca_teip_pp"]
    if horas.empty or taxas.empty:
        return pd.DataFrame(columns=colunas)
    primeiro_mes = horas["mes"].min()
    linhas = []
    for r in taxas.itertuples():
        janela = _janela(horas, r.mes, janela_meses)
        completa = r.mes - pd.DateOffset(months=janela_meses - 1) >= primeiro_mes
        teifa, teip = _taxas_da_janela(janela) if completa else (float("nan"), float("nan"))
        linhas.append({
            "mes": r.mes,
            "meses_na_janela": int(janela["mes"].nunique()),
            "teifa_publicada": r.teifa,
            "teifa_recalculada": teifa,
            "teip_publicada": r.teip,
            "teip_recalculada": teip,
            "diferenca_teifa_pp": (teifa - r.teifa) * 100.0,
            "diferenca_teip_pp": (teip - r.teip) * 100.0,
        })
    return pd.DataFrame(linhas, columns=colunas)


def decompor_taxas(horas: pd.DataFrame, mes_fim: pd.Timestamp, janela_meses: int = 60) -> pd.DataFrame:
    """Contribuição de cada unidade e de cada parcela de horas para a TEIFa e a TEIP do mês."""
    colunas = ["taxa", "ug", "parcela", "horas", "contribuicao_pp", "participacao_pct"]
    janela = _janela(horas, mes_fim, janela_meses)
    if janela.empty:
        return pd.DataFrame(columns=colunas)
    p = _peso(janela)
    bases = {
        "TEIFa": (float((p * (janela["HP"] - janela["HDP"] - janela["HEDP"])).sum()), ["HDF", "HEDF"]),
        "TEIP": (float((p * janela["HP"]).sum()), ["HDP", "HEDP"]),
    }
    linhas = []
    for taxa, (base, parcelas) in bases.items():
        total = sum(float((p * janela[c]).sum()) for c in parcelas) / base * 100.0 if base else float("nan")
        for ug, g in janela.groupby("ug"):
            pg = _peso(g)
            for parcela in parcelas:
                contribuicao = float((pg * g[parcela]).sum()) / base * 100.0 if base else float("nan")
                linhas.append({
                    "taxa": taxa,
                    "ug": int(ug),
                    "parcela": parcela,
                    "horas": float(g[parcela].sum()),
                    "contribuicao_pp": contribuicao,
                    "participacao_pct": contribuicao / total * 100.0 if total else float("nan"),
                })
    return pd.DataFrame(linhas, columns=colunas)


# ---------------------------------------------------------------------------
# Período da base de EVT e orquestração
# ---------------------------------------------------------------------------


def periodo_base_evt(pasta: Path = PROCESSED_DATA_DIR) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Início e fim da base de EVT (base tratada, ou a consolidada se a tratada não existir)."""
    tratada = pasta / TREATED_FILE_PARQUET.name
    consolidada = pasta / CONSOLIDATED_FILE.name
    if tratada.exists():
        instantes = pd.read_parquet(tratada, columns=["din_instante"])["din_instante"]
    elif consolidada.exists():
        instantes = pd.read_csv(consolidada, sep=";", usecols=["din_instante"])["din_instante"]
    else:
        raise FileNotFoundError("Base de EVT não encontrada; execute a coleta (src.main) antes dos indicadores.")
    instantes = pd.to_datetime(instantes)
    return instantes.min(), instantes.max()


def montar_indicadores(pasta_raiz: Path = INDICADORES_RAW_DIR) -> IndicadoresONS:
    """Lê e trata os quatro conjuntos baixados (sem recorte de período)."""
    auditorias: List[Dict[str, object]] = []
    tabelas: Dict[str, pd.DataFrame] = {}
    for conjunto in CONJUNTOS_INDICADORES_ONS:
        tabelas[conjunto], aud = carregar_conjunto(conjunto, pasta_raiz)
        auditorias += aud
    mensal = tratar_indicadores_ug(tabelas[MENSAL], anual=False)
    anual = tratar_indicadores_ug(tabelas[ANUAL], anual=True)
    for nome, t in (("mensal", mensal), ("anual", anual)):
        if not t.empty and set(t["id_usina"]) != {ID_ONS_USINA}:
            logger.warning("Indicadores %s com id_usina diferente de %s: %s", nome, ID_ONS_USINA, sorted(set(t["id_usina"])))
    return IndicadoresONS(
        ug_mensal=mensal,
        ug_anual=anual,
        horas_estado=tratar_horas_estado(tabelas[PARAMETROS]),
        taxas=tratar_taxas(tabelas[TAXAS]),
        auditoria=pd.DataFrame(auditorias),
    )


def exportar_indicadores(ind: IndicadoresONS, pasta_saida: Path = PROCESSED_DATA_DIR) -> None:
    """Grava cada tabela em CSV (';', ponto decimal) e todas juntas em uma planilha."""
    saidas = {
        pasta_saida / INDICADORES_UG_MENSAL_FILE.name: ind.ug_mensal,
        pasta_saida / INDICADORES_UG_ANUAL_FILE.name: ind.ug_anual,
        pasta_saida / HORAS_ESTADO_UG_FILE.name: ind.horas_estado,
        pasta_saida / TAXAS_TEIFA_TEIP_FILE.name: ind.taxas,
        pasta_saida / DIVERGENCIAS_INDICADORES_FILE.name: ind.divergencias,
        pasta_saida / AUDITORIA_INDICADORES_FILE.name: ind.auditoria,
    }
    for caminho, tabela in saidas.items():
        gravar_csv(tabela, caminho, sep=";", index=False, encoding="utf-8", date_format="%Y-%m-%d %H:%M:%S")
        logger.info("Gravado: %s (%d linhas)", caminho.name, len(tabela))
    abas = {
        "UG_MENSAL": ind.ug_mensal,
        "UG_ANUAL": ind.ug_anual,
        "HORAS_ESTADO_UG_MENSAL": ind.horas_estado,
        "TEIFA_TEIP_MENSAL": ind.taxas,
        "TEIFA_TEIP_RECALCULO": recalcular_taxas(ind.horas_estado, ind.taxas),
        "DIVERGENCIAS": ind.divergencias,
        "AUDITORIA_ARQUIVOS": ind.auditoria,
        "SIGLAS_HORAS": pd.DataFrame(list(INSUMOS_HORAS.items()), columns=["sigla", "descricao"]),
    }
    planilha = pasta_saida / INDICADORES_XLSX_FILE.name

    def formatar(writer) -> None:
        for nome in abas:
            writer.sheets[nome].freeze_panes = "A2"

    gravar_planilha(abas, planilha, formatar=formatar)
    logger.info("Planilha gravada: %s", planilha)


def carregar_indicadores_processados(pasta: Path = PROCESSED_DATA_DIR) -> Optional[IndicadoresONS]:
    """Lê as tabelas tratadas; None se os indicadores ainda não foram gerados."""
    arquivos = [pasta / a.name for a in (INDICADORES_UG_MENSAL_FILE, INDICADORES_UG_ANUAL_FILE,
                                         HORAS_ESTADO_UG_FILE, TAXAS_TEIFA_TEIP_FILE)]
    if not all(a.exists() for a in arquivos):
        return None

    def _ler(caminho: Path, datas: List[str]) -> pd.DataFrame:
        if not caminho.exists():
            return pd.DataFrame()
        try:
            t = pd.read_csv(caminho, sep=";")
        except pd.errors.EmptyDataError:  # tabela gravada sem colunas (ex.: nenhuma divergência)
            return pd.DataFrame()
        for coluna in datas:
            if coluna in t.columns:
                t[coluna] = pd.to_datetime(t[coluna])
        return t

    return IndicadoresONS(
        ug_mensal=_ler(pasta / INDICADORES_UG_MENSAL_FILE.name, ["mes"]),
        ug_anual=_ler(pasta / INDICADORES_UG_ANUAL_FILE.name, []),
        horas_estado=_ler(pasta / HORAS_ESTADO_UG_FILE.name, ["mes"]),
        taxas=_ler(pasta / TAXAS_TEIFA_TEIP_FILE.name, ["mes", "din_calculo"]),
        divergencias=_ler(pasta / DIVERGENCIAS_INDICADORES_FILE.name, ["mes"]),
        auditoria=_ler(pasta / AUDITORIA_INDICADORES_FILE.name, []),
    )


def executar_indicadores_ons(
    baixar: bool = True,
    force: bool = False,
    periodo: Optional[Tuple[pd.Timestamp, pd.Timestamp]] = None,
    pasta_raw: Path = INDICADORES_RAW_DIR,
    pasta_saida: Path = PROCESSED_DATA_DIR,
    dicionarios: bool = True,
) -> int:
    """Baixa, filtra, valida e exporta os indicadores no período da base de EVT.

    Quando baixa os dados, obtém também os dicionários de dados dos quatro conjuntos (spec 006, US2).

    Retorna 0 em caso de sucesso, 1 em erro e 2 se algum arquivo não pôde ser lido.
    """
    try:
        inicio, fim = periodo or periodo_base_evt(pasta_saida)
        logger.info("Período da base de EVT: %s a %s", inicio, fim)
        if baixar:
            sincronizar_indicadores(inicio.year, fim.year, destino=pasta_raw, force=force)
            if dicionarios:
                atualizar_dicionarios(list(CONJUNTOS_INDICADORES_ONS), raiz_raw=pasta_raw.parent,
                                      pasta_saida=pasta_saida)
        ind = recortar_periodo(montar_indicadores(pasta_raw), inicio, fim)
        if not ind.horas_estado.empty and not ind.ug_mensal.empty:
            ind.horas_estado = ind.horas_estado.merge(
                ind.ug_mensal[["mes", "ug", "potencia_mw"]], on=["mes", "ug"], how="left"
            )
        ind.divergencias = comparar_indicadores_e_horas(ind.ug_mensal, ind.horas_estado)

        h = ind.horas_estado
        if not h.empty:
            fora = h[h["residuo_identidade_h"].abs() > TOLERANCIA_IDENTIDADE_HORAS]
            if len(fora):
                logger.warning("%d meses-unidade em que HP difere da soma das parcelas: %s",
                               len(fora), fora[["mes", "ug", "residuo_identidade_h"]].to_dict("records"))
        if len(ind.divergencias):
            logger.warning("%d meses-unidade com divergência entre INDISPPF/INDISPFF e as horas HDP/HDF.",
                           len(ind.divergencias))
        recalculo = recalcular_taxas(ind.horas_estado, ind.taxas).dropna(subset=["teifa_recalculada"])
        if len(recalculo):
            logger.info(
                "TEIFa/TEIP recalculadas a partir das horas em %d meses; diferença máxima %.6f / %.6f p.p.",
                len(recalculo), recalculo["diferenca_teifa_pp"].abs().max(), recalculo["diferenca_teip_pp"].abs().max(),
            )

        exportar_indicadores(ind, pasta_saida)
        falhas = ind.auditoria[ind.auditoria["status"] == "FALHA"] if len(ind.auditoria) else ind.auditoria
        if len(falhas):
            logger.error("Arquivos não lidos: %s", falhas["arquivo"].tolist())
            return 2
        return 0
    except Exception as exc:
        logger.exception("Erro ao processar os indicadores do ONS: %s", exc)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Indicadores oficiais de disponibilidade por unidade geradora (ONS) da UHE São Domingos."
    )
    parser.add_argument("--no-download", action="store_true", help="Usa apenas os arquivos já baixados.")
    parser.add_argument("--force-download", action="store_true", help="Baixa novamente todos os arquivos.")
    parser.add_argument("--log-level", choices=NIVEIS_LOG, default="INFO", help="Nível de log de todos os módulos.")
    args = parser.parse_args()
    configurar_nivel_log(args.log_level)
    sys.exit(executar_indicadores_ons(baixar=not args.no_download, force=args.force_download))


if __name__ == "__main__":
    main()
