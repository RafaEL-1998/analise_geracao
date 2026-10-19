"""Catálogo das conferências e a aplicabilidade de cada uma à usina (spec 006, decisão R13; data-model 6.3).

Cada conferência declara os tipos de usina, os conjuntos do registro que ela compara e as condições de nível.
A que não se aplica à usina (tipo, conjunto não coletado, base ainda fora do pipeline, conjunto sem membros no
perfil, ou resultado sem base) vai para ``nao_aplicaveis.csv``, com o motivo (FR-019, princípio VI). As seis de hoje
são feitas como hoje; G1 a G5 dependem de conjuntos das próximas fases e, por ora, só aparecem no arquivo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.coleta import registro
from src.coleta.registro import HIDRELETRICAS, TERMICAS
from src.comum.regras import TIPOS_USINA
from src.conferencia.resultado import ResultadoConferencia

COLUNAS_NAO_APLICAVEIS = ["conferencia", "motivo"]
RENOVAVEIS: Tuple[str, ...] = ("EOL", "UFV")

# Nome dos conjuntos do registro nos motivos
NOMES_CONJUNTOS: Dict[str, str] = {
    "evt": "Energia Vertida Turbinável",
    "indicadores": "Indicadores de desempenho do ONS",
    "programacao": "Programação diária",
    "disponibilidade": "Disponibilidade por usina",
    "hidrologia": "Dados hidrológicos",
    "geracao": "Geração por usina",
    "cadastro": "Modalidade das usinas",
}
# Bases das conferências novas que o pipeline ainda não coleta (fases B e C da spec 006)
BASES_FORA_DO_PIPELINE: Dict[str, str] = {
    "despacho": "Despacho térmico",
    "fator_capacidade": "Fator de capacidade",
    "restricao": "Restrição de operação (constrained-off)",
}


@dataclass(frozen=True)
class ConferenciaCatalogo:
    """Conferência do catálogo: tipos, conjuntos comparados e condições (decisão R13)."""

    id: str
    descricao: str
    tipos: Tuple[str, ...]
    conjuntos: Tuple[str, ...]  # chaves do registro que precisam ter sido coletadas para a usina
    bases_novas: Tuple[str, ...] = ()  # bases fora do pipeline (BASES_FORA_DO_PIPELINE)
    geracao_da_usina: bool = False  # só com a Geração por usina no nível da usina (pares do mesmo nível)
    exige_membros: bool = False  # só em conjunto, com os membros no perfil


CATALOGO_CONFERENCIAS: Tuple[ConferenciaCatalogo, ...] = (
    ConferenciaCatalogo("geracao", "geração da base de EVT × Geração por usina", HIDRELETRICAS, ("evt", "geracao"),
                        geracao_da_usina=True),
    ConferenciaCatalogo("disponibilidade", "disponibilidade declarada da base de EVT × Disponibilidade por usina",
                        HIDRELETRICAS, ("evt", "disponibilidade")),
    ConferenciaCatalogo("vazoes", "vazões da base de EVT × Dados hidrológicos", HIDRELETRICAS, ("evt", "hidrologia")),
    ConferenciaCatalogo("dispf_horas", "DISPF × horas por estado operativo", HIDRELETRICAS + TERMICAS,
                        ("indicadores",)),
    ConferenciaCatalogo("teifa_teip", "TEIFa e TEIP refeitas a partir das horas", HIDRELETRICAS + TERMICAS,
                        ("indicadores",)),
    ConferenciaCatalogo("cadastro", "ficha do cadastro × perfil da usina", TIPOS_USINA, ("cadastro",)),
    ConferenciaCatalogo("geracao_fontes", "G1. geração da usina entre fontes", RENOVAVEIS, ("geracao",),
                        ("fator_capacidade", "restricao"), geracao_da_usina=True),
    ConferenciaCatalogo("soma_conjunto", "G2. soma das usinas do conjunto × geração do conjunto", RENOVAVEIS,
                        ("geracao",), ("restricao",), exige_membros=True),
    ConferenciaCatalogo("programacao_despacho", "G3. Programação diária × geração programada do despacho", TERMICAS,
                        ("programacao",), ("despacho",)),
    ConferenciaCatalogo("verificada_despacho", "G4. geração verificada do despacho × Geração por usina", TERMICAS,
                        ("geracao",), ("despacho",)),
    ConferenciaCatalogo("programacao_renovaveis", "G5. Programação diária × geração programada do Fator de capacidade",
                        RENOVAVEIS, ("programacao",), ("fator_capacidade",)),
)


def _lista(itens: Tuple[str, ...]) -> str:
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def _motivo_estatico(c: ConferenciaCatalogo, perfil: Any) -> Optional[str]:
    """Motivo pelo qual a conferência não se aplica à usina, antes de rodar; None quando se aplica."""
    tipo = registro.tipo_da_usina(perfil)
    if tipo not in c.tipos:
        return f"não se aplica a {tipo}: conferência de {_lista(c.tipos)}"
    ident = perfil.identificacao
    if c.exige_membros:
        if not getattr(ident, "id_conjunto", None):
            return "a usina não está em conjunto de usinas"
        if not getattr(ident, "membros", None):
            return "sem os membros do conjunto no perfil"
    if c.bases_novas:
        nomes = tuple(BASES_FORA_DO_PIPELINE[b] for b in c.bases_novas)
        return f"{_lista(nomes)}: {'conjunto ainda não coletado' if len(nomes) == 1 else 'conjuntos ainda não coletados'} pelo pipeline"
    coletados = {e.chave for e in registro.conjuntos_da_usina(perfil)}
    cobertura = registro.cobertura_da_usina(perfil)
    for chave in c.conjuntos:
        if chave not in coletados:
            valor = cobertura.get(chave)
            declarada = ", ".join(valor) if isinstance(valor, (list, tuple)) else valor
            return (f"conjunto {NOMES_CONJUNTOS.get(chave, chave)} não coletado para a usina "
                    f"(cobertura: {declarada or 'não declarada'})")
    if c.geracao_da_usina and registro.descricoes(perfil)["geracao"].nivel != "usina":
        return "Geração por usina só no nível do conjunto: não se compara com uma série da usina"
    return None


def aplicaveis(perfil: Any) -> List[str]:
    """Conferências do catálogo que se aplicam à usina, na ordem do catálogo."""
    return [c.id for c in CATALOGO_CONFERENCIAS if _motivo_estatico(c, perfil) is None]


def tabela_nao_aplicaveis(perfil: Any, resultados: Dict[str, ResultadoConferencia]) -> pd.DataFrame:
    """``nao_aplicaveis.csv``: as conferências do catálogo que não se aplicam à usina, com o motivo, na ordem do
    catálogo; as que rodaram sem base entram com o motivo do resultado."""
    linhas = []
    for c in CATALOGO_CONFERENCIAS:
        motivo = _motivo_estatico(c, perfil)
        r = resultados.get(c.id)
        if motivo is None and r is not None and not r.aplicavel:
            motivo = r.motivo
        if motivo is not None:
            linhas.append({"conferencia": c.id, "motivo": motivo})
    return pd.DataFrame(linhas, columns=COLUNAS_NAO_APLICAVEIS)
