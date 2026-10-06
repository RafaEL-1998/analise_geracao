"""Geração por usina do ONS: conferência independente da geração da base de EVT (spec 006, US5).

Conjunto "geracao-usina-2": arquivos Parquet anuais até 2021 e mensais a partir de 2022, com todas as
usinas do SIN. A leitura empurra ao Parquet o filtro pelo id ONS e pelo CEG (os arquivos anuais têm
milhões de linhas); a usina é conferida pelo CEG e pelo estado (constituição 1.2.0, princípio IV).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from src.config import (
    AUDITORIA_GERACAO_FILE,
    CEG_USINA,
    CONJUNTO_GERACAO,
    ESTADO_USINA,
    GERACAO_AUSENCIAS_FILE,
    GERACAO_HORARIA_FILE,
    GERACAO_RAW_DIR,
    ID_ONS_USINA,
    PROCESSED_DATA_DIR,
    TOLERANCIA_COINCIDENCIA_MW,
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

logger = setup_logger("geracao_ons")

DESCRICAO = DescricaoConjunto(
    pacote=CONJUNTO_GERACAO,
    pasta=GERACAO_RAW_DIR.name,
    identificador=Regra("id_ons", ID_ONS_USINA),
    conferencias=(Regra("ceg", CEG_USINA), Regra("id_estado", ESTADO_USINA)),
    colunas_valor=("val_geracao",),
    filtro_parquet=((("id_ons", "==", ID_ONS_USINA),), (("ceg", "==", CEG_USINA),)),
)


def arquivos_saida(pasta_saida: Path = PROCESSED_DATA_DIR) -> Dict[str, Path]:
    pasta = Path(pasta_saida)
    return {"horaria": pasta / GERACAO_HORARIA_FILE.name,
            "ausencias": pasta / GERACAO_AUSENCIAS_FILE.name,
            "auditoria": pasta / AUDITORIA_GERACAO_FILE.name}


def qualidade(horaria: pd.DataFrame) -> pd.Series:
    """"OK" ou "G1" (valor não numérico); horas sinalizadas ficam fora da conferência."""
    nao_numerico = horaria["_nao_numerico"].astype(bool) if "_nao_numerico" in horaria.columns \
        else pd.Series(False, index=horaria.index)
    return nao_numerico.map({True: "G1", False: "OK"})


def executar_geracao_ons(
    baixar: bool = True,
    force: bool = False,
    periodo: Optional[Tuple[pd.Timestamp, pd.Timestamp]] = None,
    pasta_raw: Path = GERACAO_RAW_DIR,
    pasta_saida: Path = PROCESSED_DATA_DIR,
    dicionarios: bool = True,
) -> int:
    """Baixa, extrai e grava a geração horária oficial no período da base de EVT.

    Retorna 0 em caso de sucesso, 1 em erro e 2 se algum arquivo não pôde ser obtido ou lido.
    """
    try:
        inicio, fim = periodo or periodo_base_evt(pasta_saida)
        logger.info("Período da base de EVT: %s a %s", inicio, fim)
        falhas = []
        if baixar:
            falhas = sincronizar_conjunto(DESCRICAO, inicio, fim, Path(pasta_raw), force)
            if dicionarios:
                atualizar_dicionarios([CONJUNTO_GERACAO], raiz_raw=Path(pasta_raw).parent, pasta_saida=pasta_saida)
        serie = montar_serie(DESCRICAO, Path(pasta_raw), inicio, fim, falhas)
        serie.horaria.insert(serie.horaria.columns.get_loc("arquivo_origem"), "qualidade", qualidade(serie.horaria))
        exportar_serie(serie, arquivos_saida(pasta_saida))
        falhas_auditoria = serie.auditoria[serie.auditoria["status"] == "FALHA"]
        if len(falhas_auditoria):
            logger.error("Arquivos de geração não obtidos ou não lidos: %s", falhas_auditoria["arquivo"].tolist())
            return 2
        return 0
    except Exception as exc:
        logger.exception("Erro ao processar a geração por usina do ONS: %s", exc)
        return 1


def carregar_geracao_processada(pasta: Path = PROCESSED_DATA_DIR) -> Optional[SerieConjunto]:
    """Série gravada; None se a etapa ainda não foi executada."""
    return carregar_serie_processada(arquivos_saida(pasta))


def conferir_geracao(
    ger: pd.DataFrame,
    df: pd.DataFrame,
    tolerancia: float = TOLERANCIA_COINCIDENCIA_MW,
) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """Geração da base de EVT × série oficial de geração por usina: resumo, tabela mensal e divergências."""
    g = ger[ger["qualidade"] == "OK"] if "qualidade" in ger.columns else ger
    g = g[["din_instante", "val_geracao"]].dropna()
    e = df[["din_instante", "val_geracao"]].dropna()
    if len(g):
        e = e[(e["din_instante"] >= g["din_instante"].min()) & (e["din_instante"] <= g["din_instante"].max())]
    juntos = g.merge(e, on="din_instante", how="outer", suffixes=("_ons", "_evt"), indicator=True)
    comuns = juntos[juntos["_merge"] == "both"].copy()
    comuns["diferenca_mw"] = (comuns["val_geracao_ons"] - comuns["val_geracao_evt"]).abs()
    divergentes = comuns[comuns["diferenca_mw"] > tolerancia]
    resumo = {
        "horas_comuns": len(comuns),
        "coincidentes": int(len(comuns) - len(divergentes)),
        "divergentes": int(len(divergentes)),
        "pct_coincidentes": float(100.0 * (len(comuns) - len(divergentes)) / len(comuns)) if len(comuns) else float("nan"),
        "so_ons_geracao": int((juntos["_merge"] == "left_only").sum()),
        "so_base_evt": int((juntos["_merge"] == "right_only").sum()),
        "energia_ons_geracao_mwh": float(g["val_geracao"].sum()),
        "energia_base_evt_mwh": float(e["val_geracao"].sum()),
        "tolerancia_mw": tolerancia,
    }
    juntos["mes"] = juntos["din_instante"].dt.to_period("M").astype(str)
    juntos["so_ons"] = juntos["_merge"] == "left_only"
    juntos["so_evt"] = juntos["_merge"] == "right_only"
    mensal = juntos.groupby("mes").agg(
        energia_base_evt_mwh=("val_geracao_evt", "sum"),
        energia_ons_geracao_mwh=("val_geracao_ons", "sum"),
        horas_so_base_evt=("so_evt", "sum"),
        horas_so_ons_geracao=("so_ons", "sum"),
    ).reset_index()
    mensal["diferenca_mwh"] = mensal["energia_ons_geracao_mwh"] - mensal["energia_base_evt_mwh"]
    for coluna in ("horas_so_base_evt", "horas_so_ons_geracao"):
        mensal[coluna] = mensal[coluna].astype(int)
    mensal = mensal[["mes", "energia_base_evt_mwh", "energia_ons_geracao_mwh", "diferenca_mwh",
                     "horas_so_base_evt", "horas_so_ons_geracao"]]
    return resumo, mensal, periodos_continuos(divergentes, "diferenca_mw")


def main() -> None:
    parser = argparse.ArgumentParser(description="Geração horária oficial da UHE São Domingos (ONS, geração por usina).")
    parser.add_argument("--no-download", action="store_true", help="Usa apenas os arquivos já baixados.")
    parser.add_argument("--force-download", action="store_true", help="Baixa novamente todos os arquivos do período.")
    parser.add_argument("--log-level", choices=NIVEIS_LOG, default="INFO", help="Nível de log de todos os módulos.")
    args = parser.parse_args()
    configurar_nivel_log(args.log_level)
    sys.exit(executar_geracao_ons(baixar=not args.no_download, force=args.force_download))


if __name__ == "__main__":
    main()
