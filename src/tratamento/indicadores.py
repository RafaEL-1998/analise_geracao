"""Indicadores por unidade geradora e taxas TEIFa e TEIP no Tratamento de dados.

A partir das linhas extraídas pela Coleta (colunas como publicadas): conversão em número, versão mais recente de cada
parâmetro e de cada taxa, chave única por mês (ou ano) e unidade, recorte no período da base de EVT e potência da
unidade junto às horas por estado operativo. Nenhum desses conjuntos traz eventos individuais (início, fim e causa
de cada desligamento): eles informam quanto tempo cada unidade passou em cada estado, não o motivo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from src.coleta.indicadores import ANUAL, MENSAL, PARAMETROS, TAXAS, separar_conjuntos
from src.comum.caminhos import ARQUIVOS_TRATAMENTO
from src.comum.logger import setup_logger
from src.comum.persistencia import gravar_csv, gravar_planilha
from src.comum.regras import TOLERANCIA_IDENTIDADE_HORAS

logger = setup_logger("tratamento")

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
# Parcelas que somam as horas do período (identidade conferida no tratamento)
PARCELAS_HP: List[str] = ["HS", "HRD", "HDP", "HDF", "HDCE", "HEDP", "HEDF"]

_RE_NUMERO_UG = re.compile(r"(\d+)\s+[A-Z]{2}$")


@dataclass
class IndicadoresONS:
    """Tabelas tratadas dos indicadores oficiais, já recortadas no período da base de EVT.

    ``divergencias`` (DISPF × horas por estado) vem da Conferência e ``auditoria`` (arquivos lidos), da Coleta.
    """

    ug_mensal: pd.DataFrame
    ug_anual: pd.DataFrame
    horas_estado: pd.DataFrame
    taxas: pd.DataFrame
    divergencias: pd.DataFrame = field(default_factory=pd.DataFrame)
    auditoria: pd.DataFrame = field(default_factory=pd.DataFrame)


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
    """Número da unidade em nomes como 'UG   24 MW <USINA>              1 MS'."""
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


def montar_indicadores(extraido: pd.DataFrame, inicio: pd.Timestamp, fim: pd.Timestamp) -> IndicadoresONS:
    """Trata os quatro conjuntos extraídos, recorta no período e junta a potência às horas por estado."""
    tabelas = separar_conjuntos(extraido)
    ind = recortar_periodo(IndicadoresONS(
        ug_mensal=tratar_indicadores_ug(tabelas[MENSAL], anual=False),
        ug_anual=tratar_indicadores_ug(tabelas[ANUAL], anual=True),
        horas_estado=tratar_horas_estado(tabelas[PARAMETROS]),
        taxas=tratar_taxas(tabelas[TAXAS]),
    ), inicio, fim)
    if not ind.horas_estado.empty and not ind.ug_mensal.empty:
        ind.horas_estado = ind.horas_estado.merge(
            ind.ug_mensal[["mes", "ug", "potencia_mw"]], on=["mes", "ug"], how="left"
        )
    h = ind.horas_estado
    if not h.empty:
        fora = h[h["residuo_identidade_h"].abs() > TOLERANCIA_IDENTIDADE_HORAS]
        if len(fora):
            logger.warning("%d meses-unidade em que HP difere da soma das parcelas: %s",
                           len(fora), fora[["mes", "ug", "residuo_identidade_h"]].to_dict("records"))
    return ind


# ---------------------------------------------------------------------------
# Gravação e leitura
# ---------------------------------------------------------------------------

_TABELAS = {
    "indicadores_ug_mensal": ("ug_mensal", ["mes"]),
    "indicadores_ug_anual": ("ug_anual", []),
    "horas_estado_mensal": ("horas_estado", ["mes"]),
    "teifa_teip_mensal": ("taxas", ["mes", "din_calculo"]),
}


def exportar_indicadores(ind: IndicadoresONS, pasta: Path) -> List[Path]:
    """Grava cada tabela em CSV (';', ponto decimal) e as quatro, com as siglas das horas, em uma planilha."""
    gravados = []
    for chave, (atributo, _) in _TABELAS.items():
        caminho = Path(pasta) / ARQUIVOS_TRATAMENTO[chave]
        gravar_csv(getattr(ind, atributo), caminho, sep=";", index=False, encoding="utf-8",
                   date_format="%Y-%m-%d %H:%M:%S")
        gravados.append(caminho)
    abas = {
        "UG_MENSAL": ind.ug_mensal,
        "UG_ANUAL": ind.ug_anual,
        "HORAS_ESTADO_UG_MENSAL": ind.horas_estado,
        "TEIFA_TEIP_MENSAL": ind.taxas,
        "SIGLAS_HORAS": pd.DataFrame(list(INSUMOS_HORAS.items()), columns=["sigla", "descricao"]),
    }
    planilha = Path(pasta) / ARQUIVOS_TRATAMENTO["indicadores_xlsx"]

    def formatar(writer) -> None:
        for nome in abas:
            writer.sheets[nome].freeze_panes = "A2"

    gravar_planilha(abas, planilha, formatar=formatar)
    return [*gravados, planilha]


def carregar_indicadores_tratados(pasta: Path) -> Optional[IndicadoresONS]:
    """Tabelas tratadas; None se os indicadores ainda não foram tratados."""
    arquivos = {chave: Path(pasta) / ARQUIVOS_TRATAMENTO[chave] for chave in _TABELAS}
    if not all(a.exists() for a in arquivos.values()):
        return None

    def _ler(caminho: Path, datas: List[str]) -> pd.DataFrame:
        try:
            t = pd.read_csv(caminho, sep=";")
        except pd.errors.EmptyDataError:  # tabela gravada sem colunas
            return pd.DataFrame()
        for coluna in datas:
            if coluna in t.columns:
                t[coluna] = pd.to_datetime(t[coluna])
        return t

    tabelas = {atributo: _ler(arquivos[chave], datas) for chave, (atributo, datas) in _TABELAS.items()}
    return IndicadoresONS(**tabelas)
