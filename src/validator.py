"""Módulo de validação física, checagem do dicionário de dados e sinalização de anomalias.

Regras R1 a R5 verificam a consistência interna das grandezas publicadas pelo ONS
(não-negatividade e identidades de cálculo). Regras R6 a R9 verificam a plausibilidade
física dos registros frente aos parâmetros técnicos da usina. Registros que violam R6 a
R9 são mantidos na base e sinalizados na coluna ``qualidade_registro``.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.config import (
    CONSOLIDATED_FILE,
    DATA_DICTIONARY_JSON,
    FAIXA_PRODUTIVIDADE_RELATIVA,
    LIMIAR_GERACAO_PARADA_MW,
    LIMITES_FISICOS_SUPERIORES,
    OPERATIONAL_METRIC_COLUMNS,
    PHYSICAL_AUDIT_REPORT_CSV,
    PHYSICAL_AUDIT_REPORT_MD,
    PHYSICAL_TOLERANCE_EPSILON,
    PRODUTIVIDADE_NOMINAL_MW_M3S,
    TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW,
    COD_USINA_ONS,
)
from src.formatacao import fmt_data_hora, fmt_int, fmt_num, fmt_pct
from src.persistencia import gravar_csv, gravar_texto

logger = logging.getLogger("validator")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [validator] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

GRUPO_CONSISTENCIA = "Consistência interna ONS"
GRUPO_PLAUSIBILIDADE = "Plausibilidade física"

# Regras de plausibilidade e as colunas booleanas que sinalizam cada uma
COLUNAS_ANOMALIA: Dict[str, str] = {
    "R6": "anomalia_limite_fisico",
    "R7": "anomalia_geracao_acima_disponibilidade",
    "R8": "anomalia_produtividade",
    "R9": "anomalia_geracao_sem_vazao_turbinada",
}
DESCRICAO_ANOMALIA: Dict[str, str] = {
    "R6": "Valor acima do limite físico da usina",
    "R7": "Geração acima da disponibilidade declarada",
    "R8": "Produtividade fora da faixa física",
    "R9": "Geração com vazão turbinada nula",
}
COLUNA_QUALIDADE = "qualidade_registro"
QUALIDADE_OK = "OK"


@dataclass
class RegraResultado:
    """Resultado da avaliação de uma regra sobre o dataset."""

    codigo_regra: str
    grupo: str
    nome_regra: str
    expressao: str
    total_linhas: int
    conformes: int
    violacoes: int
    taxa_conformidade: float
    desvio_maximo: float
    desvio_medio: float
    status: str


def carregar_dicionario_dados(
    caminho_json: Optional[Path] = None,
) -> Dict[str, str]:
    """Lê DicionarioDados_EnergiaVertidaTurbinavel.json e mapeia coluna -> descrição oficial."""
    caminho = caminho_json or DATA_DICTIONARY_JSON
    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo de dicionário de dados não encontrado em: {caminho}"
        )

    logger.info("Carregando dicionário oficial ONS de: %s", caminho)
    with open(caminho, mode="r", encoding="utf-8") as f:
        dados = json.load(f)

    dicionario: Dict[str, str] = {}
    itens = dados.get("dicionario_simplificado", [])
    for item in itens:
        codigo = item.get("codigo", "").strip()
        descricao = item.get("descricao", "").strip()
        # Ignora metadados de versão/data no final da lista
        if codigo and not codigo[0].isdigit():
            dicionario[codigo] = descricao

    logger.info("Dicionário ONS carregado com sucesso: %d colunas mapeadas.", len(dicionario))
    return dicionario


def versao_dicionario_dados(caminho_json: Optional[Path] = None) -> str:
    """Retorna a versão declarada no dicionário (ex.: 'Versão 2.0 (06-06-2024)')."""
    caminho = caminho_json or DATA_DICTIONARY_JSON
    try:
        with open(caminho, mode="r", encoding="utf-8") as f:
            itens = json.load(f).get("dicionario_simplificado", [])
    except (OSError, json.JSONDecodeError):
        return "não identificada"
    for item in itens:
        codigo = str(item.get("codigo", "")).strip()
        if codigo and codigo[0].isdigit():
            return f"{str(item.get('descricao', '')).strip()} ({codigo})"
    return "não identificada"


def verificar_colunas_no_dicionario(colunas: List[str], dicionario: Dict[str, str]) -> List[str]:
    """Lista as colunas do dataset que não constam no dicionário oficial."""
    ausentes = [c for c in colunas if c not in dicionario]
    if ausentes:
        logger.warning("Colunas ausentes no dicionário de dados do ONS: %s", ausentes)
    return ausentes


def carregar_base_consolidada(
    caminho_csv: Optional[Path] = None,
) -> pd.DataFrame:
    """Carrega o dataset consolidado com checagem de colunas obrigatórias e de rastreabilidade."""
    caminho = caminho_csv or CONSOLIDATED_FILE
    if not caminho.exists():
        raise FileNotFoundError(
            f"Base consolidada não encontrada em: {caminho}. Execute a coleta e extração prévia."
        )

    logger.info("Carregando base consolidada de: %s", caminho)
    df = pd.read_csv(caminho, sep=";", low_memory=False)

    colunas_obrigatorias = [
        "id_subsistema",
        "nom_subsistema",
        "nom_bacia",
        "nom_rio",
        "nom_agente",
        "nom_reservatorio",
        "cod_usina",
        "din_instante",
    ] + OPERATIONAL_METRIC_COLUMNS

    colunas_presentes = set(df.columns)
    faltantes = [c for c in colunas_obrigatorias if c not in colunas_presentes]
    if faltantes:
        raise ValueError(f"A base consolidada não contém as colunas obrigatórias: {faltantes}")

    # Checagem de metadados de rastreabilidade (Constituição Princípio IV)
    if "arquivo_origem" not in df.columns:
        logger.warning("Coluna de rastreabilidade 'arquivo_origem' ausente no arquivo.")
    if "tipo_match" not in df.columns:
        logger.warning("Coluna de rastreabilidade 'tipo_match' ausente no arquivo.")

    logger.info(
        "Base consolidada carregada com sucesso: %d linhas e %d colunas.",
        len(df),
        len(df.columns),
    )
    return df


def _coagir_metricas(df: pd.DataFrame) -> pd.DataFrame:
    """Converte as métricas para número sem preencher ausentes (NaN não viola regra)."""
    df_calc = df.copy()
    for col in OPERATIONAL_METRIC_COLUMNS:
        if col in df_calc.columns:
            df_calc[col] = pd.to_numeric(df_calc[col], errors="coerce")
        else:
            df_calc[col] = float("nan")
    return df_calc


def faixa_produtividade() -> Tuple[float, float]:
    """Limites inferior e superior aceitos para a produtividade, em MW/(m³/s)."""
    inferior, superior = FAIXA_PRODUTIVIDADE_RELATIVA
    return inferior * PRODUTIVIDADE_NOMINAL_MW_M3S, superior * PRODUTIVIDADE_NOMINAL_MW_M3S


def mascaras_plausibilidade(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """Máscaras booleanas das regras R6 a R9 (fonte única para validação e sinalização)."""
    d = _coagir_metricas(df)

    acima_limite = pd.Series(False, index=d.index)
    for coluna, limite in LIMITES_FISICOS_SUPERIORES.items():
        acima_limite |= d[coluna] > limite

    geracao_acima_disp = d["val_geracao"] > d["val_disponibilidade"] + TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW

    prod_min, prod_max = faixa_produtividade()
    com_vazao = d["val_vazaoturbinada"] > 0
    produtividade_fora = com_vazao & ((d["val_produtividade"] < prod_min) | (d["val_produtividade"] > prod_max))

    geracao_sem_vazao = (d["val_vazaoturbinada"] <= 0) & (d["val_geracao"] > LIMIAR_GERACAO_PARADA_MW)

    return {
        "R6": acima_limite.fillna(False),
        "R7": geracao_acima_disp.fillna(False),
        "R8": produtividade_fora.fillna(False),
        "R9": geracao_sem_vazao.fillna(False),
    }


def sinalizar_anomalias(df: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta as colunas de anomalia (R6 a R9) e o resumo ``qualidade_registro``."""
    df_saida = df.copy()
    mascaras = mascaras_plausibilidade(df_saida)
    for codigo, coluna in COLUNAS_ANOMALIA.items():
        df_saida[coluna] = mascaras[codigo].astype(bool)

    codigos = pd.Series("", index=df_saida.index, dtype="object")
    for codigo in COLUNAS_ANOMALIA:
        codigos = codigos.where(~mascaras[codigo], codigos + ";" + codigo)
    df_saida[COLUNA_QUALIDADE] = codigos.str.lstrip(";").replace("", QUALIDADE_OK)

    total = int((df_saida[COLUNA_QUALIDADE] != QUALIDADE_OK).sum())
    logger.info("Registros sinalizados com anomalia de plausibilidade física: %d de %d.", total, len(df_saida))
    return df_saida


def _resultado(
    codigo: str,
    grupo: str,
    nome: str,
    expressao: str,
    total: int,
    violacoes: int,
    desvio_maximo: float = 0.0,
    desvio_medio: float = 0.0,
) -> RegraResultado:
    conformes = total - violacoes
    return RegraResultado(
        codigo_regra=codigo,
        grupo=grupo,
        nome_regra=nome,
        expressao=expressao,
        total_linhas=total,
        conformes=conformes,
        violacoes=violacoes,
        taxa_conformidade=(conformes / total * 100.0) if total > 0 else 100.0,
        desvio_maximo=desvio_maximo,
        desvio_medio=desvio_medio,
        status="CONFORME" if violacoes == 0 else "VIOLADA",
    )


def validar_regras_fisicas(
    df: pd.DataFrame,
    epsilon: float = PHYSICAL_TOLERANCE_EPSILON,
) -> Tuple[pd.DataFrame, List[RegraResultado]]:
    """Avalia as regras R1 a R9 sobre 100% dos registros.

    Consistência interna (identidades publicadas pelo ONS):
    - R1: não-negatividade das 10 grandezas (conta registros com ao menos um valor negativo).
    - R2: val_energiavertida >= val_energiavertidaturbinavel.
    - R3: val_vazaovertida >= val_vazaovertidaturbinavel + val_vazaovertidanaoturbinavel.
    - R4: val_energiavertidaturbinavel = val_vazaovertidaturbinavel x val_produtividade.
    - R5: val_folgadegeracao = max(0, val_disponibilidade - val_geracao).

    Plausibilidade física (parâmetros da usina em config.py):
    - R6: grandezas de potência e de vazão turbinável abaixo dos limites da usina.
    - R7: geração não superior à disponibilidade declarada (com tolerância).
    - R8: produtividade dentro da faixa física quando há vazão turbinada.
    - R9: geração relevante somente com vazão turbinada positiva.

    Valores ausentes não são contados como violação.
    """
    total = len(df)
    d = _coagir_metricas(df)
    resultados: List[RegraResultado] = []

    # R1 --------------------------------------------------------------------
    negativos = d[OPERATIONAL_METRIC_COLUMNS] < -epsilon
    linhas_r1 = negativos.any(axis=1)
    minimo = d[OPERATIONAL_METRIC_COLUMNS].min().min()
    resultados.append(
        _resultado(
            "R1", GRUPO_CONSISTENCIA, "Não-negatividade das grandezas",
            "val_x >= 0 para as 10 colunas val_*", total, int(linhas_r1.sum()),
            desvio_maximo=abs(float(minimo)) if linhas_r1.any() else 0.0,
        )
    )

    # R2 --------------------------------------------------------------------
    diff_r2 = d["val_energiavertida"] - d["val_energiavertidaturbinavel"]
    mask_r2 = diff_r2 < -epsilon
    resultados.append(
        _resultado(
            "R2", GRUPO_CONSISTENCIA, "Energia vertida turbinável contida na energia vertida",
            "val_energiavertida >= val_energiavertidaturbinavel", total, int(mask_r2.sum()),
            desvio_maximo=float(abs(diff_r2[mask_r2].min())) if mask_r2.any() else 0.0,
        )
    )

    # R3 --------------------------------------------------------------------
    diff_r3 = d["val_vazaovertida"] - (d["val_vazaovertidaturbinavel"] + d["val_vazaovertidanaoturbinavel"])
    mask_r3 = diff_r3 < -epsilon
    resultados.append(
        _resultado(
            "R3", GRUPO_CONSISTENCIA, "Parcelas da vazão vertida contidas no total",
            "val_vazaovertida >= val_vazaovertidaturbinavel + val_vazaovertidanaoturbinavel",
            total, int(mask_r3.sum()),
            desvio_maximo=float(abs(diff_r3[mask_r3].min())) if mask_r3.any() else 0.0,
        )
    )

    # R4 --------------------------------------------------------------------
    diff_r4 = (d["val_energiavertidaturbinavel"] - d["val_vazaovertidaturbinavel"] * d["val_produtividade"]).abs()
    mask_r4 = diff_r4 > epsilon
    resultados.append(
        _resultado(
            "R4", GRUPO_CONSISTENCIA, "Energia vertida turbinável = vazão x produtividade",
            "val_energiavertidaturbinavel = val_vazaovertidaturbinavel x val_produtividade",
            total, int(mask_r4.sum()),
            desvio_maximo=float(diff_r4.max()) if total > 0 else 0.0,
            desvio_medio=float(diff_r4.mean()) if total > 0 else 0.0,
        )
    )

    # R5 --------------------------------------------------------------------
    folga_esperada = (d["val_disponibilidade"] - d["val_geracao"]).clip(lower=0.0)
    diff_r5 = (d["val_folgadegeracao"] - folga_esperada).abs()
    mask_r5 = diff_r5 > epsilon
    resultados.append(
        _resultado(
            "R5", GRUPO_CONSISTENCIA, "Folga de geração = disponibilidade - geração",
            "val_folgadegeracao = max(0, val_disponibilidade - val_geracao)",
            total, int(mask_r5.sum()),
            desvio_maximo=float(diff_r5.max()) if total > 0 else 0.0,
            desvio_medio=float(diff_r5.mean()) if total > 0 else 0.0,
        )
    )

    # R6 a R9 ---------------------------------------------------------------
    mascaras = mascaras_plausibilidade(d)
    limites_txt = "; ".join(f"{c} <= {fmt_num(v, 1)}" for c, v in LIMITES_FISICOS_SUPERIORES.items())
    excesso = pd.concat(
        [d[c] - v for c, v in LIMITES_FISICOS_SUPERIORES.items()], axis=1
    ).max(axis=1)
    resultados.append(
        _resultado(
            "R6", GRUPO_PLAUSIBILIDADE, DESCRICAO_ANOMALIA["R6"], limites_txt, total,
            int(mascaras["R6"].sum()),
            desvio_maximo=float(excesso[mascaras["R6"]].max()) if mascaras["R6"].any() else 0.0,
        )
    )

    excesso_r7 = d["val_geracao"] - d["val_disponibilidade"]
    resultados.append(
        _resultado(
            "R7", GRUPO_PLAUSIBILIDADE, DESCRICAO_ANOMALIA["R7"],
            f"val_geracao <= val_disponibilidade + {fmt_num(TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW, 1)} MW",
            total, int(mascaras["R7"].sum()),
            desvio_maximo=float(excesso_r7[mascaras["R7"]].max()) if mascaras["R7"].any() else 0.0,
        )
    )

    prod_min, prod_max = faixa_produtividade()
    desvio_prod = (d["val_produtividade"] - PRODUTIVIDADE_NOMINAL_MW_M3S).abs()
    resultados.append(
        _resultado(
            "R8", GRUPO_PLAUSIBILIDADE, DESCRICAO_ANOMALIA["R8"],
            f"{fmt_num(prod_min, 3)} <= val_produtividade <= {fmt_num(prod_max, 3)} quando val_vazaoturbinada > 0",
            total, int(mascaras["R8"].sum()),
            desvio_maximo=float(desvio_prod[mascaras["R8"]].max()) if mascaras["R8"].any() else 0.0,
        )
    )

    resultados.append(
        _resultado(
            "R9", GRUPO_PLAUSIBILIDADE, DESCRICAO_ANOMALIA["R9"],
            f"val_geracao <= {fmt_num(LIMIAR_GERACAO_PARADA_MW, 1)} MW quando val_vazaoturbinada = 0",
            total, int(mascaras["R9"].sum()),
            desvio_maximo=float(d.loc[mascaras["R9"], "val_geracao"].max()) if mascaras["R9"].any() else 0.0,
        )
    )

    df_res = pd.DataFrame(
        [
            {
                "codigo_regra": r.codigo_regra,
                "grupo": r.grupo,
                "nome_regra": r.nome_regra,
                "expressao": r.expressao,
                "total_linhas": r.total_linhas,
                "conformes": r.conformes,
                "violacoes": r.violacoes,
                "taxa_conformidade_pct": round(r.taxa_conformidade, 4),
                "desvio_maximo": round(r.desvio_maximo, 6),
                "desvio_medio": round(r.desvio_medio, 6),
                "status": r.status,
            }
            for r in resultados
        ]
    )

    ausentes = int(d[OPERATIONAL_METRIC_COLUMNS].isna().sum().sum())
    if ausentes:
        logger.warning("Valores ausentes nas métricas (não avaliados pelas regras): %d", ausentes)

    return df_res, resultados


def _frase_regra(row: pd.Series) -> str:
    codigo = row["codigo_regra"]
    if row["violacoes"] == 0:
        return f"- **{codigo}** ({row['nome_regra']}): nenhuma violação em {fmt_int(row['total_linhas'])} registros."
    n = int(row["violacoes"])
    return (
        f"- **{codigo}** ({row['nome_regra']}): {fmt_int(n)} {'registro viola' if n == 1 else 'registros violam'} a regra "
        f"({fmt_pct(n / row['total_linhas'] * 100, 3)} do total); desvio máximo de {fmt_num(row['desvio_maximo'], 3)}."
    )


def gerar_relatorio_validacao_md(
    df_res: pd.DataFrame,
    df_sinalizado: Optional[pd.DataFrame] = None,
    caminho_md: Optional[Path] = None,
    limite_linhas_anomalias: int = 40,
) -> Path:
    """Gera o relatório de validação em Markdown; todo o texto deriva de ``df_res``."""
    destino = caminho_md or PHYSICAL_AUDIT_REPORT_MD
    destino.parent.mkdir(parents=True, exist_ok=True)

    prod_min, prod_max = faixa_produtividade()
    linhas_md: List[str] = [
        "# Relatório de Validação dos Dados - UHE São Domingos",
        "",
        f"**Usina**: UHE São Domingos (cod_usina {COD_USINA_ONS} nos arquivos do ONS)",
        f"**Dicionário de dados ONS**: {versao_dicionario_dados()}",
        f"**Tolerância das identidades (R2 a R5)**: {PHYSICAL_TOLERANCE_EPSILON}",
        f"**Faixa de produtividade aceita (R8)**: {fmt_num(prod_min, 3)} a {fmt_num(prod_max, 3)} MW/(m³/s) "
        f"({fmt_num(PRODUTIVIDADE_NOMINAL_MW_M3S, 4)} nominal teórica)",
        "",
        "---",
        "",
        "## 1. Resultado das regras",
        "",
        "| Regra | Grupo | Descrição | Expressão | Registros | Violações | % com violação | Status |",
        "| :---: | :--- | :--- | :--- | ---: | ---: | ---: | :---: |",
    ]
    for _, row in df_res.iterrows():
        linhas_md.append(
            f"| **{row['codigo_regra']}** | {row['grupo']} | {row['nome_regra']} | `{row['expressao']}` | "
            f"{fmt_int(row['total_linhas'])} | {fmt_int(row['violacoes'])} | "
            f"{fmt_pct(row['violacoes'] / row['total_linhas'] * 100 if row['total_linhas'] else 0, 3)} | **{row['status']}** |"
        )

    linhas_md += ["", "## 2. Leitura dos resultados", ""]
    linhas_md += [_frase_regra(row) for _, row in df_res.iterrows()]
    linhas_md += [
        "",
        "As regras R1 a R5 verificam apenas a consistência interna das grandezas publicadas pelo ONS; "
        "não atestam que os valores medidos estejam corretos. As regras R6 a R9 comparam os registros "
        "com os parâmetros técnicos da usina. Registros que violam R6 a R9 foram mantidos na base e "
        f"sinalizados na coluna `{COLUNA_QUALIDADE}`.",
    ]

    if df_sinalizado is not None and COLUNA_QUALIDADE in df_sinalizado.columns:
        anomalos = df_sinalizado[df_sinalizado[COLUNA_QUALIDADE] != QUALIDADE_OK]
        linhas_md += [
            "",
            f"## 3. Registros sinalizados ({fmt_int(len(anomalos))} no total; primeiros {min(limite_linhas_anomalias, len(anomalos))} em ordem cronológica)",
            "",
            "| Data/hora | Regras | Geração (MW) | Disponibilidade (MW) | Vazão turbinada (m³/s) | Produtividade |",
            "| :--- | :---: | ---: | ---: | ---: | ---: |",
        ]
        for _, r in anomalos.sort_values("din_instante").head(limite_linhas_anomalias).iterrows():
            linhas_md.append(
                f"| {fmt_data_hora(r['din_instante'])} | {r[COLUNA_QUALIDADE]} | {fmt_num(r['val_geracao'], 3)} | "
                f"{fmt_num(r['val_disponibilidade'], 3)} | {fmt_num(r['val_vazaoturbinada'], 1)} | "
                f"{fmt_num(r['val_produtividade'], 3)} |"
            )

    linhas_md.append("")
    gravar_texto("\n".join(linhas_md), destino)

    logger.info("Relatório de validação gerado em: %s", destino)
    return destino


def gerar_relatorio_validacao_csv(
    df_res: pd.DataFrame,
    caminho_csv: Optional[Path] = None,
) -> Path:
    """Exporta os resultados numéricos das regras em CSV."""
    destino = caminho_csv or PHYSICAL_AUDIT_REPORT_CSV
    gravar_csv(df_res, destino, sep=";", index=False, encoding="utf-8", date_format=None)
    logger.info("Métricas de validação exportadas em CSV: %s", destino)
    return destino
