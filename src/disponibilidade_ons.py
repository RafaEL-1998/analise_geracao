"""Disponibilidade horária por usina do ONS: operacional e sincronizada (spec 006, US3).

Conjunto "disponibilidade_usina": um arquivo por mês. O formato compacto (Parquet) só existe para
01–02/2015 e a partir de 01/2023; os demais meses vêm do CSV (o motor escolhe o formato por mês).
A usina é identificada pelo id ONS e conferida pelo CEG e pelo estado (constituição 1.2.0, princípio IV).

A disponibilidade operacional é a mesma disponibilidade declarada da base de EVT (conferência hora a
hora); a informação nova é a disponibilidade sincronizada, que separa a usina disponível e desligada
da usina com unidade sincronizada à rede.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from src.config import (
    AUDITORIA_DISPONIBILIDADE_FILE,
    CEG_USINA,
    CONJUNTO_DISPONIBILIDADE,
    DISPONIBILIDADE_AUSENCIAS_FILE,
    DISPONIBILIDADE_HORARIA_FILE,
    DISPONIBILIDADE_RAW_DIR,
    ESTADO_USINA,
    ID_ONS_USINA,
    LIMIAR_GERACAO_PARADA_MW,
    LIMIAR_SINCRONIZADA_MW,
    PROCESSED_DATA_DIR,
    TOLERANCIA_COINCIDENCIA_MW,
    TOLERANCIA_QUALIDADE_DISPONIBILIDADE_MW,
)
from src.conjuntos_ons import (
    DescricaoConjunto,
    Regra,
    SerieConjunto,
    carregar_serie_processada,
    exportar_serie,
    montar_serie,
    periodos_continuos,
    sincronizar_conjunto,
)
from src.dicionarios_ons import atualizar_dicionarios
from src.indicadores_ons import periodo_base_evt
from src.logger import NIVEIS_LOG, configurar_nivel_log, setup_logger

logger = setup_logger("disponibilidade_ons")

DESCRICAO = DescricaoConjunto(
    pacote=CONJUNTO_DISPONIBILIDADE,
    pasta=DISPONIBILIDADE_RAW_DIR.name,
    identificador=Regra("id_ons", ID_ONS_USINA),
    conferencias=(Regra("ceg", CEG_USINA), Regra("id_estado", ESTADO_USINA)),
    colunas_valor=("val_potenciainstalada", "val_dispoperacional", "val_dispsincronizada"),
)

SINCRONIZADA = "SINCRONIZADA"
NAO_SINCRONIZADA = "NAO_SINCRONIZADA"
COM_EVT = "COM_EVT"
SEM_EVT = "SEM_EVT"
SEM_PROGRAMACAO = "SEM_PROGRAMACAO"
DESCRICAO_QUALIDADE: Dict[str, str] = {
    "D1": f"sincronizada > operacional + {TOLERANCIA_QUALIDADE_DISPONIBILIDADE_MW} MW",
    "D2": f"operacional > instalada + {TOLERANCIA_QUALIDADE_DISPONIBILIDADE_MW} MW",
    "D3": "algum valor negativo",
    "D4": "algum valor não numérico",
}


def arquivos_saida(pasta_saida: Path = PROCESSED_DATA_DIR) -> Dict[str, Path]:
    pasta = Path(pasta_saida)
    return {"horaria": pasta / DISPONIBILIDADE_HORARIA_FILE.name,
            "ausencias": pasta / DISPONIBILIDADE_AUSENCIAS_FILE.name,
            "auditoria": pasta / AUDITORIA_DISPONIBILIDADE_FILE.name}


# ---------------------------------------------------------------------------
# Etapa de dados
# ---------------------------------------------------------------------------


def qualidade(horaria: pd.DataFrame) -> pd.Series:
    """"OK" ou as regras violadas (D1 a D4), separadas por vírgula; horas sinalizadas ficam fora das análises."""
    tol = TOLERANCIA_QUALIDADE_DISPONIBILIDADE_MW
    inst, oper, sinc = (horaria[c] for c in ("val_potenciainstalada", "val_dispoperacional", "val_dispsincronizada"))
    regras = {
        "D1": sinc > oper + tol,
        "D2": oper > inst + tol,
        "D3": (inst < 0) | (oper < 0) | (sinc < 0),
        "D4": horaria["_nao_numerico"].astype(bool) if "_nao_numerico" in horaria.columns else pd.Series(False, index=horaria.index),
    }
    codigos = pd.Series("", index=horaria.index, dtype=object)
    for codigo, violada in regras.items():
        codigos = codigos.where(~violada.fillna(False), codigos + "," + codigo)
    codigos = codigos.str.strip(",")
    return codigos.where(codigos != "", "OK")


def executar_disponibilidade_ons(
    baixar: bool = True,
    force: bool = False,
    periodo: Optional[Tuple[pd.Timestamp, pd.Timestamp]] = None,
    pasta_raw: Path = DISPONIBILIDADE_RAW_DIR,
    pasta_saida: Path = PROCESSED_DATA_DIR,
    dicionarios: bool = True,
) -> int:
    """Baixa, extrai e grava a disponibilidade horária no período da base de EVT.

    Retorna 0 em caso de sucesso, 1 em erro e 2 se algum arquivo não pôde ser obtido ou lido.
    """
    try:
        inicio, fim = periodo or periodo_base_evt(pasta_saida)
        logger.info("Período da base de EVT: %s a %s", inicio, fim)
        falhas = []
        if baixar:
            falhas = sincronizar_conjunto(DESCRICAO, inicio, fim, Path(pasta_raw), force)
            if dicionarios:
                atualizar_dicionarios([CONJUNTO_DISPONIBILIDADE], raiz_raw=Path(pasta_raw).parent, pasta_saida=pasta_saida)
        serie = montar_serie(DESCRICAO, Path(pasta_raw), inicio, fim, falhas)
        serie.horaria.insert(serie.horaria.columns.get_loc("arquivo_origem"), "qualidade", qualidade(serie.horaria))
        exportar_serie(serie, arquivos_saida(pasta_saida))

        sinalizadas = serie.horaria["qualidade"].ne("OK").sum()
        if sinalizadas:
            logger.warning("%d horas de disponibilidade sinalizadas (fora das análises): %s", sinalizadas,
                           serie.horaria.loc[serie.horaria["qualidade"] != "OK", "qualidade"].value_counts().to_dict())
        meses = serie.ausencias[serie.ausencias["tipo"] != "HORAS"]
        if len(meses):
            logger.warning("Meses sem a usina na disponibilidade: %s",
                           [f"{r.inicio:%Y-%m} ({r.tipo})" for r in meses.itertuples()])
        falhas_auditoria = serie.auditoria[serie.auditoria["status"] == "FALHA"]
        if len(falhas_auditoria):
            logger.error("Arquivos de disponibilidade não obtidos ou não lidos: %s", falhas_auditoria["arquivo"].tolist())
            return 2
        return 0
    except Exception as exc:
        logger.exception("Erro ao processar a disponibilidade do ONS: %s", exc)
        return 1


def carregar_disponibilidade_processada(pasta: Path = PROCESSED_DATA_DIR) -> Optional[SerieConjunto]:
    """Série gravada; None se a etapa ainda não foi executada."""
    return carregar_serie_processada(arquivos_saida(pasta))


# ---------------------------------------------------------------------------
# Análises (cruzamento com a base de EVT)
# ---------------------------------------------------------------------------


def _validas(disp: pd.DataFrame) -> pd.DataFrame:
    if "qualidade" in disp.columns:
        return disp[disp["qualidade"] == "OK"]
    return disp


def conferir_com_evt(
    disp: pd.DataFrame,
    df: pd.DataFrame,
    tolerancia: float = TOLERANCIA_COINCIDENCIA_MW,
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """Disponibilidade operacional (ONS) × disponibilidade declarada (base de EVT), hora a hora."""
    d = _validas(disp)[["din_instante", "val_dispoperacional"]].dropna()
    e = df[["din_instante", "val_disponibilidade"]].dropna()
    juntos = d.merge(e, on="din_instante", how="inner")
    juntos["diferenca_mw"] = (juntos["val_dispoperacional"] - juntos["val_disponibilidade"]).abs()
    divergentes = juntos[juntos["diferenca_mw"] > tolerancia]
    if len(d):
        e_no_periodo = e[(e["din_instante"] >= d["din_instante"].min()) & (e["din_instante"] <= d["din_instante"].max())]
    else:
        e_no_periodo = e.iloc[0:0]
    resumo = {
        "horas_comuns": len(juntos),
        "coincidentes": int(len(juntos) - len(divergentes)),
        "divergentes": int(len(divergentes)),
        "pct_coincidentes": float(100.0 * (len(juntos) - len(divergentes)) / len(juntos)) if len(juntos) else float("nan"),
        "so_ons_disponibilidade": int((~d["din_instante"].isin(e["din_instante"])).sum()),
        "so_base_evt": int((~e_no_periodo["din_instante"].isin(d["din_instante"])).sum()),
        "horas_sinalizadas_excluidas": int(len(disp) - len(_validas(disp))),
        "tolerancia_mw": tolerancia,
    }
    return resumo, periodos_continuos(divergentes, "diferenca_mw")


def classificar_horas_paradas(
    disp: pd.DataFrame,
    df: pd.DataFrame,
    classificadas_programacao: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Horas comuns com a usina parada (geração até 1 MW), por sincronização, EVT e classe da programação."""
    operacao = df[["din_instante", "val_geracao", "val_energiavertidaturbinavel"]]
    j = operacao.merge(_validas(disp)[["din_instante", "val_dispoperacional", "val_dispsincronizada"]],
                       on="din_instante", how="inner")
    paradas = j[j["val_geracao"] <= LIMIAR_GERACAO_PARADA_MW].copy()
    paradas["sincronizacao"] = (paradas["val_dispsincronizada"] > LIMIAR_SINCRONIZADA_MW).map(
        {True: SINCRONIZADA, False: NAO_SINCRONIZADA})
    paradas["evt"] = (paradas["val_energiavertidaturbinavel"] > 0).map({True: COM_EVT, False: SEM_EVT})
    if classificadas_programacao is not None and len(classificadas_programacao):
        classes = classificadas_programacao[["din_instante", "classe"]].rename(columns={"classe": "classe_programacao"})
        paradas = paradas.merge(classes, on="din_instante", how="left")
    else:
        paradas["classe_programacao"] = pd.NA
    paradas["classe_programacao"] = paradas["classe_programacao"].fillna(SEM_PROGRAMACAO)
    colunas = ["din_instante", "val_geracao", "val_dispoperacional", "val_dispsincronizada",
               "val_energiavertidaturbinavel", "sincronizacao", "evt", "classe_programacao"]
    return paradas.sort_values("din_instante").reset_index(drop=True)[colunas]


def resumir(
    disp: pd.DataFrame,
    df: pd.DataFrame,
    horas_estado: Optional[pd.DataFrame],
    freq: str,
) -> pd.DataFrame:
    """Resumo por mês (``freq="M"``) ou ano (``"Y"``), com a comparação com a reserva desligada (HRD) do TEIFa/TEIP."""
    j = df[["din_instante", "val_geracao", "val_disponibilidade"]].merge(
        _validas(disp)[["din_instante", "val_dispoperacional", "val_dispsincronizada"]], on="din_instante", how="inner")
    j["periodo"] = j["din_instante"].dt.to_period(freq).astype(str)
    j["nao_sincronizada"] = j["val_dispoperacional"] - j["val_dispsincronizada"]
    parada = j["val_geracao"] <= LIMIAR_GERACAO_PARADA_MW
    sinc = j["val_dispsincronizada"] > LIMIAR_SINCRONIZADA_MW
    j["parada"] = parada
    j["parada_sem_sincronizacao"] = parada & ~sinc
    j["parada_sincronizada"] = parada & sinc
    resumo = j.groupby("periodo").agg(
        horas_comuns=("din_instante", "size"),
        disp_operacional_media_mw=("val_dispoperacional", "mean"),
        disp_declarada_media_mw=("val_disponibilidade", "mean"),
        disp_sincronizada_media_mw=("val_dispsincronizada", "mean"),
        geracao_media_mw=("val_geracao", "mean"),
        capacidade_nao_sincronizada_media_mw=("nao_sincronizada", "mean"),
        capacidade_nao_sincronizada_mwh=("nao_sincronizada", "sum"),
        horas_paradas=("parada", "sum"),
        horas_paradas_sem_sincronizacao=("parada_sem_sincronizacao", "sum"),
        horas_paradas_sincronizadas=("parada_sincronizada", "sum"),
    ).reset_index()
    if horas_estado is not None and len(horas_estado) and {"HRD", "potencia_mw"} <= set(horas_estado.columns):
        h = horas_estado.copy()
        h["periodo"] = pd.to_datetime(h["mes"]).dt.to_period(freq).astype(str)
        h["reserva_mwh"] = h["HRD"] * h["potencia_mw"]
        reserva = h.groupby("periodo")["reserva_mwh"].sum().rename("reserva_desligada_teif_mwh")
        resumo = resumo.merge(reserva, on="periodo", how="left")
    else:
        resumo["reserva_desligada_teif_mwh"] = float("nan")
    resumo["diferenca_mwh"] = resumo["capacidade_nao_sincronizada_mwh"] - resumo["reserva_desligada_teif_mwh"]
    for coluna in ("horas_paradas", "horas_paradas_sem_sincronizacao", "horas_paradas_sincronizadas"):
        resumo[coluna] = resumo[coluna].astype(int)
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description="Disponibilidade horária (operacional e sincronizada) da UHE São Domingos (ONS).")
    parser.add_argument("--no-download", action="store_true", help="Usa apenas os arquivos já baixados.")
    parser.add_argument("--force-download", action="store_true", help="Baixa novamente todos os arquivos do período.")
    parser.add_argument("--log-level", choices=NIVEIS_LOG, default="INFO", help="Nível de log de todos os módulos.")
    args = parser.parse_args()
    configurar_nivel_log(args.log_level)
    sys.exit(executar_disponibilidade_ons(baixar=not args.no_download, force=args.force_download))


if __name__ == "__main__":
    main()
