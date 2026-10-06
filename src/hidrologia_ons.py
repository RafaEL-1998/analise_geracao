"""Dados hidrológicos horários do ONS: afluência, vertimento e nível do reservatório (spec 006, US4).

Conjunto "dados_hidrologicos_ho": um arquivo Parquet por mês. A usina é identificada pelo cod_usina e
conferida pelo nome e pelo código do reservatório (constituição 1.2.0, princípio IV). O conjunto marca o
FIM da hora (01:00 representa 00:00–00:59; a última hora do dia vem como 23:59); a série é convertida
para a hora de início da base de EVT e o alinhamento é confirmado pela coincidência das vazões turbinada
e vertida, presentes nas duas fontes (FR-022). Os dados são informados pelos agentes e não são
consistidos pelo ONS: valores impossíveis são sinalizados e excluídos, nunca corrigidos.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from src.config import (
    AUDITORIA_HIDROLOGIA_FILE,
    COD_USINA_ONS,
    CONJUNTO_HIDROLOGIA,
    CONSOLIDATED_FILE,
    DESVIO_MAXIMO_NIVEL_M,
    ENGOLIMENTO_MAXIMO_USINA_M3S,
    ENGOLIMENTO_NOMINAL_UG_M3S,
    HIDROLOGIA_ALINHAMENTO_FILE,
    HIDROLOGIA_AUSENCIAS_FILE,
    HIDROLOGIA_HORARIA_FILE,
    HIDROLOGIA_RAW_DIR,
    ID_RESERVATORIO_ONS,
    LIMIAR_GERACAO_PARADA_MW,
    META_ALINHAMENTO_HIDROLOGIA_PCT,
    NOME_RESERVATORIO_REFERENCIA,
    PROCESSED_DATA_DIR,
    TOLERANCIA_COINCIDENCIA_VAZAO_M3S,
    TREATED_FILE_PARQUET,
)
from src.conjuntos_ons import (
    DescricaoConjunto,
    Regra,
    SerieConjunto,
    carregar_serie_processada,
    exportar_serie,
    montar_serie,
    sincronizar_conjunto,
)
from src.dicionarios_ons import atualizar_dicionarios
from src.indicadores_ons import periodo_base_evt
from src.logger import NIVEIS_LOG, configurar_nivel_log, setup_logger
from src.persistencia import gravar_csv

logger = setup_logger("hidrologia_ons")

VAZOES = ("val_vazaoafluente", "val_vazaodefluente", "val_vazaoturbinada", "val_vazaovertida",
          "val_vazaovertidanaoturbinavel", "val_vazaooutrasestruturas")
DESCRICAO = DescricaoConjunto(
    pacote=CONJUNTO_HIDROLOGIA,
    pasta=HIDROLOGIA_RAW_DIR.name,
    identificador=Regra("cod_usina", COD_USINA_ONS),
    conferencias=(Regra("nom_reservatorio", NOME_RESERVATORIO_REFERENCIA, "contem"),
                  Regra("id_reservatorio", ID_RESERVATORIO_ONS)),
    colunas_valor=(*VAZOES, "val_nivelmontante", "val_niveljusante", "val_volumeutil"),
    convencao_hora="fim",
)

ACIMA_ENGOLIMENTO_USINA = "ACIMA_ENGOLIMENTO_USINA"
ENTRE_UMA_E_DUAS_UNIDADES = "ENTRE_UMA_E_DUAS_UNIDADES"
ATE_UMA_UNIDADE = "ATE_UMA_UNIDADE"
SEM_DADO_HIDROLOGICO = "SEM_DADO_HIDROLOGICO"
FAIXAS_AFLUENCIA = (ATE_UMA_UNIDADE, ENTRE_UMA_E_DUAS_UNIDADES, ACIMA_ENGOLIMENTO_USINA, SEM_DADO_HIDROLOGICO)
DESCRICAO_FAIXAS: Dict[str, str] = {
    ATE_UMA_UNIDADE: f"afluência até {ENGOLIMENTO_NOMINAL_UG_M3S:g} m³/s (cabia em uma unidade)",
    ENTRE_UMA_E_DUAS_UNIDADES: f"afluência acima de {ENGOLIMENTO_NOMINAL_UG_M3S:g} e até {ENGOLIMENTO_MAXIMO_USINA_M3S:g} m³/s "
                               "(cabia nas duas unidades)",
    ACIMA_ENGOLIMENTO_USINA: f"afluência acima de {ENGOLIMENTO_MAXIMO_USINA_M3S:g} m³/s (acima do engolimento máximo)",
    SEM_DADO_HIDROLOGICO: "sem dado hidrológico",
}
COM_PARADA_EVT = "COM_PARADA_EVT"
DEMAIS_DIAS = "DEMAIS"
DESCRICAO_QUALIDADE: Dict[str, str] = {
    "H1": "vazão negativa",
    "H2": "volume útil fora de 0 a 100%",
    "H3": "valor não numérico",
    "H4": f"nível de montante ou de jusante a mais de {DESVIO_MAXIMO_NIVEL_M:g} m da mediana da série",
}


def arquivos_saida(pasta_saida: Path = PROCESSED_DATA_DIR) -> Dict[str, Path]:
    pasta = Path(pasta_saida)
    return {"horaria": pasta / HIDROLOGIA_HORARIA_FILE.name,
            "ausencias": pasta / HIDROLOGIA_AUSENCIAS_FILE.name,
            "auditoria": pasta / AUDITORIA_HIDROLOGIA_FILE.name}


# ---------------------------------------------------------------------------
# Etapa de dados
# ---------------------------------------------------------------------------


def _nivel_implausivel(horaria: pd.DataFrame, coluna: str) -> pd.Series:
    """Nível afastado mais de DESVIO_MAXIMO_NIVEL_M da mediana da própria série (leitura trocada ou corrompida)."""
    if coluna not in horaria.columns:
        return pd.Series(False, index=horaria.index)
    nivel = horaria[coluna]
    return (nivel - nivel.median()).abs() > DESVIO_MAXIMO_NIVEL_M


def qualidade(horaria: pd.DataFrame) -> pd.Series:
    """"OK" ou as regras violadas (H1 a H4); campo vazio não é erro nem zero."""
    vazoes = horaria[[c for c in VAZOES if c in horaria.columns]]
    volume = horaria["val_volumeutil"] if "val_volumeutil" in horaria.columns else pd.Series(np.nan, index=horaria.index)
    regras = {
        "H1": (vazoes < 0).any(axis=1),
        "H2": (volume < 0) | (volume > 100),
        "H3": horaria["_nao_numerico"].astype(bool) if "_nao_numerico" in horaria.columns else pd.Series(False, index=horaria.index),
        "H4": _nivel_implausivel(horaria, "val_nivelmontante") | _nivel_implausivel(horaria, "val_niveljusante"),
    }
    codigos = pd.Series("", index=horaria.index, dtype=object)
    for codigo, violada in regras.items():
        codigos = codigos.where(~violada.fillna(False), codigos + "," + codigo)
    codigos = codigos.str.strip(",")
    return codigos.where(codigos != "", "OK")


def _limpos(hid: pd.DataFrame) -> pd.DataFrame:
    """Cópia com os valores fisicamente impossíveis excluídos campo a campo (FR-026).

    Vazão negativa (H1), volume útil fora de 0 a 100% (H2) e nível implausível (H4) viram vazios só no campo afetado; a hora continua
    nas demais análises (ex.: em 2019 o volume útil negativo coincide com a parada total, e as vazões seguem válidas).
    Valores não numéricos (H3) já chegam vazios do motor. Nenhum valor é corrigido.
    """
    h = hid.copy()
    for coluna in VAZOES:
        if coluna in h.columns:
            h[coluna] = h[coluna].where(~(h[coluna] < 0))
    if "val_volumeutil" in h.columns:
        h["val_volumeutil"] = h["val_volumeutil"].where(h["val_volumeutil"].between(0, 100) | h["val_volumeutil"].isna())
    for coluna in ("val_nivelmontante", "val_niveljusante"):
        if coluna in h.columns:
            h[coluna] = h[coluna].where(~_nivel_implausivel(hid, coluna))
    return h


def alinhar_com_evt(
    hid: pd.DataFrame,
    evt: pd.DataFrame,
    tolerancia: float = TOLERANCIA_COINCIDENCIA_VAZAO_M3S,
    meta: float = META_ALINHAMENTO_HIDROLOGIA_PCT,
) -> pd.DataFrame:
    """Coincidência das vazões turbinada e vertida (hidrologia × base de EVT) nas horas comuns (uma linha)."""
    colunas = ["din_instante", "val_vazaoturbinada", "val_vazaovertida"]
    j = _limpos(hid)[colunas].merge(evt[colunas], on="din_instante", how="inner", suffixes=("_hid", "_evt")).dropna()
    turbinada = (j["val_vazaoturbinada_hid"] - j["val_vazaoturbinada_evt"]).abs() <= tolerancia
    vertida = (j["val_vazaovertida_hid"] - j["val_vazaovertida_evt"]).abs() <= tolerancia
    ambas = int((turbinada & vertida).sum())
    pct = 100.0 * ambas / len(j) if len(j) else float("nan")
    return pd.DataFrame([{
        "horas_comuns": len(j),
        "coincidentes_turbinada": int(turbinada.sum()),
        "coincidentes_vertida": int(vertida.sum()),
        "coincidentes_ambas": ambas,
        "pct_coincidencia": pct,
        "meta_pct": meta,
        "tolerancia_m3s": tolerancia,
        "deslocamento_aplicado_h": -1,
        "confirmado": bool(len(j)) and pct >= meta,
    }])


def _vazoes_da_base_evt(pasta_saida: Path) -> pd.DataFrame:
    tratada = Path(pasta_saida) / TREATED_FILE_PARQUET.name
    colunas = ["din_instante", "val_vazaoturbinada", "val_vazaovertida"]
    if tratada.exists():
        evt = pd.read_parquet(tratada, columns=colunas)
    else:
        evt = pd.read_csv(Path(pasta_saida) / CONSOLIDATED_FILE.name, sep=";", usecols=colunas)
    evt["din_instante"] = pd.to_datetime(evt["din_instante"])
    return evt


def executar_hidrologia_ons(
    baixar: bool = True,
    force: bool = False,
    periodo: Optional[Tuple[pd.Timestamp, pd.Timestamp]] = None,
    pasta_raw: Path = HIDROLOGIA_RAW_DIR,
    pasta_saida: Path = PROCESSED_DATA_DIR,
    dicionarios: bool = True,
) -> int:
    """Baixa, extrai, converte a hora e confere o alinhamento dos dados hidrológicos no período da base de EVT.

    Retorna 0 em caso de sucesso, 1 em erro, 2 se algum arquivo não pôde ser obtido ou lido e 3 se o
    alinhamento com a base de EVT ficar abaixo da meta (os cruzamentos hidrológicos não são publicados).
    """
    try:
        inicio, fim = periodo or periodo_base_evt(pasta_saida)
        logger.info("Período da base de EVT: %s a %s", inicio, fim)
        falhas = []
        if baixar:
            falhas = sincronizar_conjunto(DESCRICAO, inicio, fim, Path(pasta_raw), force)
            if dicionarios:
                atualizar_dicionarios([CONJUNTO_HIDROLOGIA], raiz_raw=Path(pasta_raw).parent, pasta_saida=pasta_saida)
        serie = montar_serie(DESCRICAO, Path(pasta_raw), inicio, fim, falhas)
        serie.horaria.insert(serie.horaria.columns.get_loc("arquivo_origem"), "qualidade", qualidade(serie.horaria))
        exportar_serie(serie, arquivos_saida(pasta_saida))

        alinhamento = alinhar_com_evt(serie.horaria, _vazoes_da_base_evt(pasta_saida))
        gravar_csv(alinhamento, Path(pasta_saida) / HIDROLOGIA_ALINHAMENTO_FILE.name)
        a = alinhamento.iloc[0]
        sinalizadas = serie.horaria["qualidade"].ne("OK").sum()
        if sinalizadas:
            logger.warning("%d horas hidrológicas sinalizadas (valores excluídos só no campo afetado): %s", sinalizadas,
                           serie.horaria.loc[serie.horaria["qualidade"] != "OK", "qualidade"].value_counts().to_dict())
        if not a["confirmado"]:
            logger.error(
                "Alinhamento da hidrologia com a base de EVT abaixo da meta: %.2f%% de %d horas comuns (meta %.0f%%); "
                "os cruzamentos hidrológicos não serão publicados.", a["pct_coincidencia"], a["horas_comuns"], a["meta_pct"],
            )
            return 3
        logger.info("Alinhamento da hidrologia confirmado: %.2f%% de %d horas comuns.", a["pct_coincidencia"],
                    a["horas_comuns"])
        falhas_auditoria = serie.auditoria[serie.auditoria["status"] == "FALHA"]
        if len(falhas_auditoria):
            logger.error("Arquivos hidrológicos não obtidos ou não lidos: %s", falhas_auditoria["arquivo"].tolist())
            return 2
        return 0
    except Exception as exc:
        logger.exception("Erro ao processar os dados hidrológicos do ONS: %s", exc)
        return 1


def carregar_hidrologia_processada(pasta: Path = PROCESSED_DATA_DIR) -> Optional[Tuple[SerieConjunto, pd.DataFrame]]:
    """(série, alinhamento) gravados; None se a etapa ainda não foi executada."""
    serie = carregar_serie_processada(arquivos_saida(pasta))
    caminho = Path(pasta) / HIDROLOGIA_ALINHAMENTO_FILE.name
    if serie is None or not caminho.exists():
        return None
    alinhamento = pd.read_csv(caminho, sep=";")
    alinhamento["confirmado"] = alinhamento["confirmado"].astype(str).str.lower().isin(["true", "1"])
    return serie, alinhamento


# ---------------------------------------------------------------------------
# Análises (cruzamento com a base de EVT)
# ---------------------------------------------------------------------------


def _no_periodo_da_hidrologia(df: pd.DataFrame, hid: pd.DataFrame) -> pd.DataFrame:
    if hid.empty:
        return df.iloc[0:0]
    return df[(df["din_instante"] >= hid["din_instante"].min()) & (df["din_instante"] <= hid["din_instante"].max())]


def classificar_faixas(hid: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Horas com EVT do período comum, classificadas pela afluência em relação ao engolimento das unidades."""
    evt = _no_periodo_da_hidrologia(df, hid)
    evt = evt.loc[evt["val_energiavertidaturbinavel"] > 0, ["din_instante", "val_geracao", "val_energiavertidaturbinavel"]]
    m = evt.merge(_limpos(hid)[["din_instante", "val_vazaoafluente"]], on="din_instante", how="left")
    afluencia = m["val_vazaoafluente"]
    m["faixa_afluencia"] = np.select(
        [afluencia > ENGOLIMENTO_MAXIMO_USINA_M3S, afluencia > ENGOLIMENTO_NOMINAL_UG_M3S, afluencia <= ENGOLIMENTO_NOMINAL_UG_M3S],
        [ACIMA_ENGOLIMENTO_USINA, ENTRE_UMA_E_DUAS_UNIDADES, ATE_UMA_UNIDADE],
        default=SEM_DADO_HIDROLOGICO,
    )
    return m.sort_values("din_instante").reset_index(drop=True)[
        ["din_instante", "val_vazaoafluente", "faixa_afluencia", "val_energiavertidaturbinavel", "val_geracao"]]


def resumir_faixas(classificadas: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Horas e EVT (MWh) por faixa de afluência, por mês (``"M"``) ou ano (``"Y"``), em formato longo."""
    c = classificadas.assign(periodo=classificadas["din_instante"].dt.to_period(freq).astype(str))
    resumo = c.groupby(["periodo", "faixa_afluencia"]).agg(
        horas=("din_instante", "size"), evt_mwh=("val_energiavertidaturbinavel", "sum")).reset_index()
    completo = pd.MultiIndex.from_product([sorted(c["periodo"].unique()), FAIXAS_AFLUENCIA],
                                          names=["periodo", "faixa_afluencia"])
    resumo = resumo.set_index(["periodo", "faixa_afluencia"]).reindex(completo, fill_value=0).reset_index()
    resumo["horas"] = resumo["horas"].astype(int)
    return resumo


def perfil_hora_do_dia(hid: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Médias por hora do dia, separando os dias com ao menos uma hora de parada com EVT dos demais dias."""
    evt = _no_periodo_da_hidrologia(df, hid)
    paradas = evt[(evt["val_geracao"] <= LIMIAR_GERACAO_PARADA_MW) & (evt["val_energiavertidaturbinavel"] > 0)]
    dias_com_parada = set(paradas["din_instante"].dt.normalize())
    h = _limpos(hid).copy()
    h["dia"] = h["din_instante"].dt.normalize()
    h["grupo_dias"] = np.where(h["dia"].isin(dias_com_parada), COM_PARADA_EVT, DEMAIS_DIAS)
    h["hora"] = h["din_instante"].dt.hour
    return h.groupby(["grupo_dias", "hora"]).agg(
        dias=("dia", "nunique"),
        nivel_montante_medio_m=("val_nivelmontante", "mean"),
        afluencia_media_m3s=("val_vazaoafluente", "mean"),
        turbinada_media_m3s=("val_vazaoturbinada", "mean"),
        vertida_media_m3s=("val_vazaovertida", "mean"),
    ).reset_index()


def resumo_mensal(hid: pd.DataFrame) -> pd.DataFrame:
    """Afluência, vazões, níveis e volume útil por mês (valores sinalizados excluídos só no campo afetado)."""
    return resumir(hid, "M", "mes")


def resumir(hid: pd.DataFrame, freq: str, coluna: str = "periodo") -> pd.DataFrame:
    """Afluência, vazões, níveis e volume útil por mês (``"M"``) ou ano (``"Y"``).

    Os valores sinalizados (H1 a H4) saem só do campo afetado (``_limpos``, FR-026); a hora continua nas médias
    dos demais campos.
    """
    h = _limpos(hid).copy()
    h[coluna] = h["din_instante"].dt.to_period(freq).astype(str)
    h["acima_engolimento"] = h["val_vazaoafluente"] > ENGOLIMENTO_MAXIMO_USINA_M3S
    resumo = h.groupby(coluna).agg(
        horas=("din_instante", "size"),
        afluencia_media_m3s=("val_vazaoafluente", "mean"),
        afluencia_maxima_m3s=("val_vazaoafluente", "max"),
        turbinada_media_m3s=("val_vazaoturbinada", "mean"),
        vertida_media_m3s=("val_vazaovertida", "mean"),
        vertida_nao_turbinavel_media_m3s=("val_vazaovertidanaoturbinavel", "mean"),
        nivel_montante_min_m=("val_nivelmontante", "min"),
        nivel_montante_medio_m=("val_nivelmontante", "mean"),
        nivel_montante_max_m=("val_nivelmontante", "max"),
        nivel_jusante_medio_m=("val_niveljusante", "mean"),
        volume_util_medio_pct=("val_volumeutil", "mean"),
        horas_afluencia_acima_engolimento=("acima_engolimento", "sum"),
    ).reset_index()
    resumo["horas_afluencia_acima_engolimento"] = resumo["horas_afluencia_acima_engolimento"].astype(int)
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description="Dados hidrológicos horários da UHE São Domingos (ONS).")
    parser.add_argument("--no-download", action="store_true", help="Usa apenas os arquivos já baixados.")
    parser.add_argument("--force-download", action="store_true", help="Baixa novamente todos os arquivos do período.")
    parser.add_argument("--log-level", choices=NIVEIS_LOG, default="INFO", help="Nível de log de todos os módulos.")
    args = parser.parse_args()
    configurar_nivel_log(args.log_level)
    sys.exit(executar_hidrologia_ons(baixar=not args.no_download, force=args.force_download))


if __name__ == "__main__":
    main()
