"""Dados hidrológicos horários no Tratamento de dados: série na hora de início e sinalização de qualidade (H1 a H4).

O conjunto marca o fim da hora (01:00 representa 00:00–00:59; a última hora do dia vem como 23:59); a série é
convertida para a hora de início da base de EVT. Os dados são informados pelos agentes e não são consistidos pelo ONS:
valores impossíveis são sinalizados e excluídos campo a campo nas análises, nunca corrigidos.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from src.coleta.conjuntos import VAZOES
from src.comum.caminhos import ARQUIVOS_TRATAMENTO
from src.comum.logger import setup_logger
from src.comum.regras import DESVIO_MAXIMO_NIVEL_M
from src.tratamento.series import SerieConjunto, carregar_serie_processada, exportar_serie, montar_serie

logger = setup_logger("tratamento")

DESCRICAO_QUALIDADE: Dict[str, str] = {
    "H1": "vazão negativa",
    "H2": "volume útil fora de 0 a 100%",
    "H3": "valor não numérico",
    "H4": f"nível de montante ou de jusante a mais de {DESVIO_MAXIMO_NIVEL_M:g} m da mediana da série",
}


def arquivos_saida(pasta: Path) -> Dict[str, Path]:
    pasta = Path(pasta)
    return {"horaria": pasta / ARQUIVOS_TRATAMENTO["hidrologia_horaria"],
            "ausencias": pasta / ARQUIVOS_TRATAMENTO["hidrologia_ausencias"],
            "auditoria": pasta / ARQUIVOS_TRATAMENTO["auditoria_hidrologia"]}


def nivel_implausivel(horaria: pd.DataFrame, coluna: str) -> pd.Series:
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
        "H4": nivel_implausivel(horaria, "val_nivelmontante") | nivel_implausivel(horaria, "val_niveljusante"),
    }
    codigos = pd.Series("", index=horaria.index, dtype=object)
    for codigo, violada in regras.items():
        codigos = codigos.where(~violada.fillna(False), codigos + "," + codigo)
    codigos = codigos.str.strip(",")
    return codigos.where(codigos != "", "OK")


def limpos(hid: pd.DataFrame) -> pd.DataFrame:
    """Cópia com os valores fisicamente impossíveis excluídos campo a campo.

    Vazão negativa (H1), volume útil fora de 0 a 100% (H2) e nível implausível (H4) viram vazios só no campo afetado; a hora continua
    nas demais análises (ex.: em 2019 o volume útil negativo coincide com a parada total, e as vazões seguem válidas).
    Valores não numéricos (H3) já chegam vazios da Coleta. Nenhum valor é corrigido.
    """
    h = hid.copy()
    for coluna in VAZOES:
        if coluna in h.columns:
            h[coluna] = h[coluna].where(~(h[coluna] < 0))
    if "val_volumeutil" in h.columns:
        h["val_volumeutil"] = h["val_volumeutil"].where(h["val_volumeutil"].between(0, 100) | h["val_volumeutil"].isna())
    for coluna in ("val_nivelmontante", "val_niveljusante"):
        if coluna in h.columns:
            h[coluna] = h[coluna].where(~nivel_implausivel(hid, coluna))
    return h


def tratar_hidrologia(desc: Any, extraido: pd.DataFrame, auditoria: pd.DataFrame, inicio: pd.Timestamp,
                      fim: pd.Timestamp, pasta: Path) -> SerieConjunto:
    """Série horária na hora de início, com a qualidade de cada hora, gravada na pasta do tratamento."""
    serie = montar_serie(desc, extraido, auditoria, inicio, fim)
    serie.horaria.insert(serie.horaria.columns.get_loc("arquivo_origem"), "qualidade", qualidade(serie.horaria))
    exportar_serie(serie, arquivos_saida(pasta))
    sinalizadas = serie.horaria["qualidade"].ne("OK").sum()
    if sinalizadas:
        logger.warning("%d horas hidrológicas sinalizadas (valores excluídos só no campo afetado): %s", sinalizadas,
                       serie.horaria.loc[serie.horaria["qualidade"] != "OK", "qualidade"].value_counts().to_dict())
    return serie


def carregar_hidrologia_tratada(pasta: Path) -> Optional[SerieConjunto]:
    """Série gravada; None se o tratamento ainda não foi executado."""
    return carregar_serie_processada(arquivos_saida(pasta))
