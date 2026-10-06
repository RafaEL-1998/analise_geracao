"""Programação diária do ONS para a UHE São Domingos (spec 004, US1).

Conjunto "Dados dos Valores da Programação Diária" do Portal de Dados Abertos do ONS: um
arquivo por dia (desde 01/10/2024) com a geração programada de cada usina em 48 patamares de
30 minutos. O módulo baixa os arquivos do período da base de EVT, extrai a usina, converte a
programação para base horária e oferece as funções que cruzam a programação com a operação
verificada (classificação das horas, resumo mensal, eventos de desvio e perfil por hora).

Limites do dado: é a programação do dia (não registra reprogramações em tempo real) e, para
usinas hidráulicas, os campos de motivo (ordem de mérito, inflexibilidade, razão elétrica) e
a disponibilidade programada vêm vazios ou zerados.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import pyarrow.parquet as pq

from src.collector import download_resource, fetch_ckan_package_metadata, load_manifest, parse_ckan_resources, save_manifest
from src.config import (
    AUDITORIA_PROGRAMACAO_FILE,
    COD_EXIBICAO_USINA_PROGRAMACAO,
    CONJUNTO_PROGRAMACAO_DIARIA,
    ESTADO_USINA,
    FORMATO_PROGRAMACAO_DIARIA,
    LIMIAR_DESVIO_PROGRAMACAO_MW,
    LIMIAR_GERACAO_PARADA_MW,
    NOME_RESERVATORIO_REFERENCIA,
    PATAMARES_POR_DIA,
    PROCESSED_DATA_DIR,
    PROGRAMACAO_DIAS_AUSENTES_FILE,
    PROGRAMACAO_HORARIA_FILE,
    PROGRAMACAO_RAW_DIR,
    RAW_MANIFEST_FILE,
)
from src.filter import normalize_text
from src.indicadores_ons import periodo_base_evt, url_pacote
from src.logger import NIVEIS_LOG, configurar_nivel_log, setup_logger
from src.models import RecursoONS
from src.persistencia import gravar_csv
from src.dicionarios_ons import atualizar_dicionarios

logger = setup_logger("programacao_ons")

_RE_DATA_ARQUIVO = re.compile(r"_(\d{4})_(\d{2})_(\d{2})\.", re.IGNORECASE)
_RE_DATA_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
_RE_DATA_BR = re.compile(r"^(\d{2})/(\d{2})/(\d{4})")
COLUNAS_LIDAS = ["din_programacaodia", "num_patamar", "cod_exibicaousina", "nom_usina", "id_estado", "val_geracaoprogramada"]
DOWNLOADS_SIMULTANEOS = 8

# Classes das horas comuns à base de EVT e à programação
PARADA_EVT_PROGRAMACAO_ZERO = "PARADA_EVT_PROGRAMACAO_ZERO"
PARADA_EVT_PROGRAMACAO_POSITIVA = "PARADA_EVT_PROGRAMACAO_POSITIVA"
PARADA_SEM_EVT = "PARADA_SEM_EVT"
GERANDO_PROGRAMACAO_ZERO = "GERANDO_PROGRAMACAO_ZERO"
GERANDO_COM_PROGRAMACAO = "GERANDO_COM_PROGRAMACAO"
DESCRICAO_CLASSES: Dict[str, str] = {
    PARADA_EVT_PROGRAMACAO_ZERO: "usina parada com EVT e programação de até 1 MW",
    PARADA_EVT_PROGRAMACAO_POSITIVA: "usina parada com EVT e programação acima de 1 MW",
    PARADA_SEM_EVT: "usina parada sem EVT",
    GERANDO_PROGRAMACAO_ZERO: "usina gerando com programação de até 1 MW",
    GERANDO_COM_PROGRAMACAO: "usina gerando com programação acima de 1 MW",
}


@dataclass
class ProgramacaoONS:
    """Programação horária da usina, dias sem arquivo e auditoria dos arquivos lidos."""

    horaria: pd.DataFrame
    dias_ausentes: pd.DataFrame = field(default_factory=pd.DataFrame)
    auditoria: pd.DataFrame = field(default_factory=pd.DataFrame)


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
    destino: Path = PROGRAMACAO_RAW_DIR,
    force: bool = False,
) -> List[RecursoONS]:
    """Baixa (ou reaproveita, se a versão local for a publicada) os arquivos diários do período."""
    destino.mkdir(parents=True, exist_ok=True)
    metadados = fetch_ckan_package_metadata(url_pacote(CONJUNTO_PROGRAMACAO_DIARIA))
    recursos = selecionar_recursos_periodo(parse_ckan_resources(metadados, FORMATO_PROGRAMACAO_DIARIA), inicio, fim)
    manifesto_path = destino / RAW_MANIFEST_FILE.name
    manifesto = load_manifest(manifesto_path)
    logger.info("Programação diária: %d arquivos publicados no período.", len(recursos))
    try:
        with concurrent.futures.ThreadPoolExecutor(DOWNLOADS_SIMULTANEOS) as executor:
            list(executor.map(
                lambda r: download_resource(r, destination_dir=destino, force=force, manifest=manifesto), recursos
            ))
    finally:
        save_manifest(manifesto, manifesto_path)
    resumo: Dict[str, int] = {}
    for r in recursos:
        resumo[r.status_sincronizacao] = resumo.get(r.status_sincronizacao, 0) + 1
    logger.info("Sincronização da programação concluída: %s", resumo)
    return recursos


# ---------------------------------------------------------------------------
# Leitura, extração e base horária
# ---------------------------------------------------------------------------


def _numerico(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie.astype(str).str.strip().str.replace(",", ".", regex=False), errors="coerce")


def ler_arquivo(caminho: Path) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """Extrai os patamares da usina de um arquivo diário e devolve a auditoria do arquivo."""
    dia = dia_do_arquivo(caminho.name)
    auditoria: Dict[str, object] = {"arquivo": caminho.name, "dia": dia}
    vazio = pd.DataFrame(columns=["dia", "num_patamar", "geracao_programada_mw", "arquivo_origem"])
    try:
        bruto = pq.read_table(caminho, columns=COLUNAS_LIDAS).to_pandas()
    except Exception as e:  # arquivo corrompido ou sem as colunas esperadas
        logger.error("Falha ao ler %s: %s", caminho.name, e)
        return vazio, {**auditoria, "linhas_lidas": 0, "linhas_usina": 0, "linhas_codigo_sem_conferencia": 0,
                       "patamares": 0, "data_interna_confere": False, "status": "FALHA"}

    codigo = bruto["cod_exibicaousina"].astype(str).str.strip() == COD_EXIBICAO_USINA_PROGRAMACAO
    candidatas = bruto[codigo]  # nome e estado só são conferidos nas linhas com o código da usina
    conferida = (
        candidatas["nom_usina"].astype(str).map(normalize_text).str.contains(NOME_RESERVATORIO_REFERENCIA, regex=False)
        & (candidatas["id_estado"].astype(str).str.strip() == ESTADO_USINA)
    )
    sel = candidatas[conferida]
    patamares = _numerico(sel["num_patamar"]).astype("Int64")
    linhas = pd.DataFrame({
        "dia": dia,
        "num_patamar": patamares.to_numpy(),
        "geracao_programada_mw": _numerico(sel["val_geracaoprogramada"]).to_numpy(),
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
    return linhas.reset_index(drop=True), {
        **auditoria,
        "linhas_lidas": len(bruto),
        "linhas_usina": len(sel),
        "linhas_codigo_sem_conferencia": int((~conferida).sum()),
        "patamares": n_patamares,
        "data_interna_confere": confere,
        "status": status,
    }


def programacao_horaria(patamares: pd.DataFrame) -> pd.DataFrame:
    """Média dos patamares de cada hora; hora = (patamar − 1) ÷ 2, convenção de hora de início."""
    if patamares.empty:
        return pd.DataFrame(columns=["din_instante", "geracao_programada_mw", "patamares"])
    p = patamares.dropna(subset=["num_patamar"]).copy()
    p["din_instante"] = p["dia"] + pd.to_timedelta((p["num_patamar"].astype(int) - 1) // 2, unit="h")
    horaria = p.groupby("din_instante").agg(
        geracao_programada_mw=("geracao_programada_mw", "mean"),
        patamares=("num_patamar", "size"),
    )
    return horaria.reset_index()


def montar_programacao(
    pasta: Path,
    inicio: pd.Timestamp,
    fim: pd.Timestamp,
) -> ProgramacaoONS:
    """Lê os arquivos do período, monta a programação horária e lista os dias sem arquivo."""
    d0, d1 = pd.Timestamp(inicio).normalize(), pd.Timestamp(fim).normalize()
    arquivos = []
    for caminho in sorted(pasta.glob(f"*.{FORMATO_PROGRAMACAO_DIARIA.lower()}")):
        dia = dia_do_arquivo(caminho.name)
        if dia is not None and d0 <= dia <= d1:
            arquivos.append(caminho)
    partes, auditorias = [], []
    for caminho in arquivos:
        linhas, auditoria = ler_arquivo(caminho)
        auditorias.append(auditoria)
        if len(linhas):
            partes.append(linhas)
    patamares = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(
        columns=["dia", "num_patamar", "geracao_programada_mw", "arquivo_origem"])
    horaria = programacao_horaria(patamares)
    if len(horaria):
        horaria = horaria[(horaria["din_instante"] >= inicio) & (horaria["din_instante"] <= fim)].reset_index(drop=True)

    dias_com_arquivo = pd.DatetimeIndex([dia_do_arquivo(a.name) for a in arquivos])
    if len(dias_com_arquivo):
        grade = pd.date_range(dias_com_arquivo.min(), d1, freq="D")
        ausentes = grade.difference(dias_com_arquivo)
    else:
        ausentes = pd.DatetimeIndex([])
    auditoria = pd.DataFrame(auditorias)
    logger.info(
        "Programação: %d arquivos lidos, %d horas, %d dias sem arquivo, %d arquivos com status diferente de PROCESSADO.",
        len(arquivos), len(horaria), len(ausentes),
        int((auditoria["status"] != "PROCESSADO").sum()) if len(auditoria) else 0,
    )
    return ProgramacaoONS(horaria=horaria, dias_ausentes=pd.DataFrame({"dia": ausentes}), auditoria=auditoria)


# ---------------------------------------------------------------------------
# Exportação e leitura das tabelas tratadas
# ---------------------------------------------------------------------------


def exportar_programacao(prog: ProgramacaoONS, pasta_saida: Path = PROCESSED_DATA_DIR) -> None:
    saidas = {
        pasta_saida / PROGRAMACAO_HORARIA_FILE.name: prog.horaria,
        pasta_saida / PROGRAMACAO_DIAS_AUSENTES_FILE.name: prog.dias_ausentes,
        pasta_saida / AUDITORIA_PROGRAMACAO_FILE.name: prog.auditoria,
    }
    for caminho, tabela in saidas.items():
        gravar_csv(tabela, caminho, sep=";", index=False, encoding="utf-8", date_format="%Y-%m-%d %H:%M:%S")
        logger.info("Gravado: %s (%d linhas)", caminho.name, len(tabela))


def carregar_programacao_processada(pasta: Path = PROCESSED_DATA_DIR) -> Optional[ProgramacaoONS]:
    """Lê as tabelas tratadas; None se a programação ainda não foi gerada."""
    horaria_path = pasta / PROGRAMACAO_HORARIA_FILE.name
    if not horaria_path.exists():
        return None

    def _ler(caminho: Path, datas: List[str]) -> pd.DataFrame:
        if not caminho.exists():
            return pd.DataFrame()
        try:
            t = pd.read_csv(caminho, sep=";")
        except pd.errors.EmptyDataError:  # tabela gravada sem colunas (ex.: nenhum dia ausente)
            return pd.DataFrame()
        for coluna in datas:
            if coluna in t.columns:
                t[coluna] = pd.to_datetime(t[coluna])
        return t

    return ProgramacaoONS(
        horaria=_ler(horaria_path, ["din_instante"]),
        dias_ausentes=_ler(pasta / PROGRAMACAO_DIAS_AUSENTES_FILE.name, ["dia"]),
        auditoria=_ler(pasta / AUDITORIA_PROGRAMACAO_FILE.name, ["dia"]),
    )


# ---------------------------------------------------------------------------
# Cruzamento com a operação verificada
# ---------------------------------------------------------------------------


def classificar_horas(operacao: pd.DataFrame, horaria: pd.DataFrame) -> pd.DataFrame:
    """Cruza a operação verificada (base de EVT) com a programação nas horas comuns e classifica cada hora."""
    colunas = ["din_instante", "val_geracao", "val_energiavertidaturbinavel", "val_disponibilidade"]
    m = operacao[colunas].merge(horaria[["din_instante", "geracao_programada_mw"]], on="din_instante", how="inner")
    m = m.dropna(subset=["geracao_programada_mw"])
    parada = m["val_geracao"] <= LIMIAR_GERACAO_PARADA_MW
    evt = m["val_energiavertidaturbinavel"] > 0
    prog_zero = m["geracao_programada_mw"] <= LIMIAR_GERACAO_PARADA_MW
    m["classe"] = GERANDO_COM_PROGRAMACAO
    m.loc[~parada & prog_zero, "classe"] = GERANDO_PROGRAMACAO_ZERO
    m.loc[parada & ~evt, "classe"] = PARADA_SEM_EVT
    m.loc[parada & evt & ~prog_zero, "classe"] = PARADA_EVT_PROGRAMACAO_POSITIVA
    m.loc[parada & evt & prog_zero, "classe"] = PARADA_EVT_PROGRAMACAO_ZERO
    m["desvio_programacao"] = parada & (m["geracao_programada_mw"] > LIMIAR_DESVIO_PROGRAMACAO_MW)
    return m.sort_values("din_instante").reset_index(drop=True)


def resumo_mensal(classificadas: pd.DataFrame) -> pd.DataFrame:
    """Horas por classe, EVT e desvios por mês (horas comuns às duas fontes)."""
    if classificadas.empty:
        return pd.DataFrame()
    c = classificadas.assign(mes=classificadas["din_instante"].dt.to_period("M").dt.to_timestamp())
    linhas = []
    for mes, g in c.groupby("mes"):
        gz = g[g["classe"] == PARADA_EVT_PROGRAMACAO_ZERO]
        evt = float(g["val_energiavertidaturbinavel"].sum())
        evt_zero = float(gz["val_energiavertidaturbinavel"].sum())
        linha = {"mes": mes, "horas_comuns": len(g)}
        for classe in DESCRICAO_CLASSES:
            linha[f"horas_{classe.lower()}"] = int((g["classe"] == classe).sum())
        linha.update({
            "horas_parada_com_evt": int(g["classe"].isin([PARADA_EVT_PROGRAMACAO_ZERO, PARADA_EVT_PROGRAMACAO_POSITIVA]).sum()),
            "evt_mwh": evt,
            "evt_parada_programacao_zero_mwh": evt_zero,
            "participacao_evt_programacao_zero_pct": evt_zero / evt * 100.0 if evt else float("nan"),
            "horas_desvio_programacao": int(g["desvio_programacao"].sum()),
            "disponibilidade_media_parada_programacao_zero_mw": float(gz["val_disponibilidade"].mean()) if len(gz) else float("nan"),
            "desvio_medio_absoluto_mw": float((g["val_geracao"] - g["geracao_programada_mw"]).abs().mean()),
        })
        linhas.append(linha)
    return pd.DataFrame(linhas)


def eventos_desvio(classificadas: pd.DataFrame) -> pd.DataFrame:
    """Horas consecutivas com a usina parada e programação acima do limiar de desvio."""
    colunas = ["inicio", "fim", "duracao_h", "programacao_media_mw", "disponibilidade_media_mw", "evt_mwh"]
    if classificadas.empty:
        return pd.DataFrame(columns=colunas)
    c = classificadas.sort_values("din_instante")
    m = c["desvio_programacao"].astype(bool)
    continuidade = c["din_instante"].diff().eq(pd.Timedelta(hours=1))
    inicio_evento = m & ~(m.shift(fill_value=False) & continuidade)
    grupo = inicio_evento.cumsum()
    sel = c[m].assign(_evento=grupo[m])
    if sel.empty:
        return pd.DataFrame(columns=colunas)
    eventos = sel.groupby("_evento").agg(
        inicio=("din_instante", "min"),
        fim=("din_instante", "max"),
        duracao_h=("din_instante", "size"),
        programacao_media_mw=("geracao_programada_mw", "mean"),
        disponibilidade_media_mw=("val_disponibilidade", "mean"),
        evt_mwh=("val_energiavertidaturbinavel", "sum"),
    )
    return eventos.reset_index(drop=True)[colunas]


def perfil_hora_do_dia(classificadas: pd.DataFrame) -> pd.DataFrame:
    """Horas de usina parada com EVT e programação zero (e a EVT correspondente) por hora do dia."""
    z = classificadas[classificadas["classe"] == PARADA_EVT_PROGRAMACAO_ZERO]
    horas = z.groupby(z["din_instante"].dt.hour).agg(
        horas=("din_instante", "size"), evt_mwh=("val_energiavertidaturbinavel", "sum")
    )
    horas = horas.reindex(range(24), fill_value=0)
    horas.index.name = "hora"
    return horas.reset_index()


# ---------------------------------------------------------------------------
# Orquestração
# ---------------------------------------------------------------------------


def executar_programacao_ons(
    baixar: bool = True,
    force: bool = False,
    periodo: Optional[Tuple[pd.Timestamp, pd.Timestamp]] = None,
    pasta_raw: Path = PROGRAMACAO_RAW_DIR,
    pasta_saida: Path = PROCESSED_DATA_DIR,
    dicionarios: bool = True,
) -> int:
    """Baixa, extrai e exporta a programação no período da base de EVT.

    Quando baixa os dados, obtém também os dicionários de dados do conjunto (spec 006, US2).

    Retorna 0 em caso de sucesso, 1 em erro e 2 se algum arquivo não pôde ser lido.
    """
    try:
        inicio, fim = periodo or periodo_base_evt(pasta_saida)
        logger.info("Período da base de EVT: %s a %s", inicio, fim)
        if baixar:
            sincronizar_programacao(inicio, fim, destino=pasta_raw, force=force)
            if dicionarios:
                atualizar_dicionarios([CONJUNTO_PROGRAMACAO_DIARIA], raiz_raw=pasta_raw.parent,
                                      pasta_saida=pasta_saida)
        prog = montar_programacao(pasta_raw, inicio, fim)
        exportar_programacao(prog, pasta_saida)
        a = prog.auditoria
        if len(a):
            for status in ("INCOMPLETO", "SEM_REGISTROS"):
                dias = a.loc[a["status"] == status, "arquivo"].tolist()
                if dias:
                    logger.warning("Arquivos com status %s: %s", status, dias)
            if (~a["data_interna_confere"].astype(bool)).any():
                logger.warning("Arquivos com data interna diferente do nome: %s",
                               a.loc[~a["data_interna_confere"].astype(bool), "arquivo"].tolist())
            falhas = a.loc[a["status"] == "FALHA", "arquivo"].tolist()
            if falhas:
                logger.error("Arquivos não lidos: %s", falhas)
                return 2
        return 0
    except Exception as exc:
        logger.exception("Erro ao processar a programação diária do ONS: %s", exc)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Programação diária do ONS para a UHE São Domingos (spec 004).")
    parser.add_argument("--no-download", action="store_true", help="Usa apenas os arquivos já baixados.")
    parser.add_argument("--force-download", action="store_true", help="Baixa novamente todos os arquivos.")
    parser.add_argument("--log-level", choices=NIVEIS_LOG, default="INFO", help="Nível de log de todos os módulos.")
    args = parser.parse_args()
    configurar_nivel_log(args.log_level)
    sys.exit(executar_programacao_ons(baixar=not args.no_download, force=args.force_download))


if __name__ == "__main__":
    main()
