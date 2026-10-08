"""Resultado de conferência: o registro comum das seis conferências entre fontes (spec da Conferência, FR-003).

Cada resultado traz as bases comparadas, o período, a unidade, as quantidades comparada, coincidente e divergente, a
tolerância e, nas vazões, a meta. As tabelas de detalhe são as que as Análises e o relatório já usam. Os seis
resultados ficam em ``conferencias.pkl``, com a versão do formato conferida na leitura.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from src.comum.persistencia import ResultadoGravacao, gravar_bytes

VERSAO_FORMATO = 1
CONFERENCIAS: Tuple[str, ...] = ("geracao", "disponibilidade", "vazoes", "dispf_horas", "teifa_teip", "cadastro")

# A diferença é arredondada antes da comparação com a tolerância: "até 0,01 MW" inclui 0,01 MW, sem o resíduo do
# ponto flutuante (30,01 − 30,00 dá 0,010000000000001563)
CASAS_COMPARACAO = 9


def diferenca_absoluta(diferenca: Any) -> Any:
    """|diferença| arredondada a ``CASAS_COMPARACAO`` casas (série ou tabela do pandas, ou número)."""
    if isinstance(diferenca, (pd.Series, pd.DataFrame)):
        return diferenca.abs().round(CASAS_COMPARACAO)
    return round(abs(float(diferenca)), CASAS_COMPARACAO)


@dataclass
class ResultadoConferencia:
    """Resultado de uma conferência entre duas fontes."""

    id: str
    bases: Tuple[str, str]
    unidade: str
    aplicavel: bool = True
    motivo: str = ""
    periodo: Optional[Tuple[Any, Any]] = None
    comparados: int = 0
    coincidentes: int = 0
    divergentes: int = 0
    tolerancia: Optional[float] = None
    meta: Optional[float] = None
    meta_atingida: Optional[bool] = None
    tabelas: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.id not in CONFERENCIAS:
            raise ValueError(f"conferência desconhecida: {self.id!r}")
        if self.aplicavel and self.comparados != self.coincidentes + self.divergentes:
            raise ValueError(f"{self.id}: comparados ({self.comparados}) ≠ coincidentes + divergentes")

    def resumo(self) -> Dict[str, Any]:
        """Situação da conferência para o ``resumo`` do ``etapa.json``."""
        if not self.aplicavel:
            return {"aplicavel": False, "motivo": self.motivo}
        resumo: Dict[str, Any] = {
            "aplicavel": True, "unidade": self.unidade, "comparados": self.comparados,
            "coincidentes": self.coincidentes, "divergentes": self.divergentes,
        }
        if self.meta is not None:
            resumo["pct_coincidencia"] = 100.0 * self.coincidentes / self.comparados if self.comparados else None
            resumo["meta_pct"] = self.meta
            resumo["meta_atingida"] = bool(self.meta_atingida)
        return resumo


def nao_aplicavel(id: str, bases: Tuple[str, str], unidade: str, motivo: str,
                  tabelas: Optional[Dict[str, Any]] = None, **campos: Any) -> ResultadoConferencia:
    """Conferência registrada como não aplicável, com o motivo (FR-004)."""
    return ResultadoConferencia(id=id, bases=bases, unidade=unidade, aplicavel=False, motivo=motivo,
                                tabelas=tabelas or {}, **campos)


def salvar_conferencias(resultados: Dict[str, ResultadoConferencia], destino: Path) -> ResultadoGravacao:
    """Grava os resultados em ``conferencias.pkl`` (sem cópia ``.bak``: são refeitos a partir dos dados tratados)."""
    conteudo = pickle.dumps({"versao_formato": VERSAO_FORMATO, "resultados": resultados},
                            protocol=pickle.HIGHEST_PROTOCOL)
    return gravar_bytes(conteudo, destino, copia=False)


def carregar_conferencias(caminho: Path) -> Dict[str, ResultadoConferencia]:
    """Resultados gravados pela Conferência; formato diferente do atual é recusado."""
    with open(caminho, "rb") as f:
        dados = pickle.load(f)
    if not isinstance(dados, dict) or dados.get("versao_formato") != VERSAO_FORMATO:
        raise ValueError(f"{Path(caminho).name}: formato diferente do atual ({VERSAO_FORMATO}); refaça a Conferência")
    return dados["resultados"]
