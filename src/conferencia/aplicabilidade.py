"""Catálogo das conferências e a aplicabilidade de cada uma à usina (spec 006, decisão R13; data-model 6.3).

Cada conferência declara os tipos de usina, os conjuntos do registro que ela compara e as condições de nível.
A que não se aplica à usina (tipo, conjunto não coletado, base ainda fora do pipeline, conjunto sem membros no
perfil, níveis diferentes, ou resultado sem base) vai para ``nao_aplicaveis.csv``, com o motivo (FR-019, princípio
VI). As seis de hoje são feitas como hoje; G3 e G4 nas térmicas com o despacho (fase B); G1, G2 e G5 nas eólicas e
solares com as bases da fase C, sempre no mesmo nível; o alinhamento da hidrologia pela geração nas hidrelétricas sem
EVT (fase D; rascunho 003, FR-026). Este último só é registrado como não aplicável nas hidrelétricas: nos demais
tipos, a conferência das vazões já registra que a hidrologia não se aplica, e os relatórios aprovados não mudam.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

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
    "despacho": "Geração térmica por motivo de despacho",
    "cvu": "CVU das usinas térmicas",
    "cmo": "CMO semanal",
    "fator_capacidade": "Fator de capacidade",
    "restricao_detalhe": "Restrição com detalhe (constrained-off)",
    "restricao_razao": "Restrição com a razão (constrained-off)",
}
FONTES_DA_GERACAO: Tuple[str, ...] = ("geracao", "fator_capacidade", "restricao_detalhe", "restricao_razao")  # G1


@dataclass(frozen=True)
class ConferenciaCatalogo:
    """Conferência do catálogo: tipos, conjuntos comparados e condições (decisão R13)."""

    id: str
    descricao: str
    tipos: Tuple[str, ...]
    conjuntos: Tuple[str, ...]  # chaves do registro que precisam ter sido coletadas para a usina
    geracao_da_usina: bool = False  # só com a Geração por usina no nível da usina (pares do mesmo nível)
    exige_membros: bool = False  # só em conjunto, com os membros no perfil
    programacao_da_usina: bool = False  # só com a Programação diária no nível da usina
    fontes_no_mesmo_nivel: bool = False  # G1: duas fontes da geração em um mesmo nível
    geracao_do_conjunto: bool = False  # G2: a Geração por usina no nível do conjunto
    programacao_no_nivel_do_fc: bool = False  # G5: a Programação diária no nível do Fator de capacidade
    so_sem_evt: bool = False  # só na usina sem EVT (na hidrelétrica com EVT, a conferência das vazões faz o mesmo)
    registrada_so_nos_tipos: bool = False  # fora dos tipos, nenhuma linha em nao_aplicaveis.csv


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
    ConferenciaCatalogo("geracao_fontes", "G1. geração da usina entre fontes", RENOVAVEIS, (),
                        fontes_no_mesmo_nivel=True),
    ConferenciaCatalogo("soma_conjunto", "G2. soma das usinas do conjunto × geração do conjunto", RENOVAVEIS,
                        ("geracao", "restricao_detalhe"), exige_membros=True, geracao_do_conjunto=True),
    ConferenciaCatalogo("programacao_despacho", "G3. Programação diária × geração programada do despacho", TERMICAS,
                        ("programacao", "despacho"), programacao_da_usina=True),
    ConferenciaCatalogo("verificada_despacho", "G4. geração verificada do despacho × Geração por usina", TERMICAS,
                        ("geracao", "despacho"), geracao_da_usina=True),
    ConferenciaCatalogo("programacao_renovaveis", "G5. Programação diária × geração programada do Fator de capacidade",
                        RENOVAVEIS, ("programacao", "fator_capacidade"), programacao_no_nivel_do_fc=True),
    ConferenciaCatalogo("alinhamento_hidrologia", "hora dos Dados hidrológicos conferida pela geração da usina",
                        HIDRELETRICAS, ("hidrologia", "geracao"), geracao_da_usina=True, so_sem_evt=True,
                        registrada_so_nos_tipos=True),
)


def _lista(itens: Tuple[str, ...]) -> str:
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def niveis_coletados(perfil: Any, chave: str) -> Set[str]:
    """Níveis em que a Coleta obtém o conjunto ``chave`` para a usina (os dois, com a lista ``["proprio",
    "conjunto"]``); vazio quando não o obtém."""
    if chave not in {e.chave for e in registro.conjuntos_da_usina(perfil)}:
        return set()
    valor = registro.cobertura_da_usina(perfil).get(chave)
    valores = valor if isinstance(valor, (list, tuple)) else [valor]
    niveis = {registro.NIVEL_DA_COBERTURA[v] for v in valores if v in registro.NIVEL_DA_COBERTURA}
    return niveis or {registro.entrada(chave).niveis[0]}


def _motivo_estatico(c: ConferenciaCatalogo, perfil: Any) -> Optional[str]:
    """Motivo pelo qual a conferência não se aplica à usina, antes de rodar; None quando se aplica."""
    tipo = registro.tipo_da_usina(perfil)
    if tipo not in c.tipos:
        return f"não se aplica a {tipo}: conferência de {_lista(c.tipos)}"
    if c.so_sem_evt and "evt" in {e.chave for e in registro.conjuntos_da_usina(perfil)}:
        return "na hidrelétrica com EVT, a hora da hidrologia é conferida pelas vazões da base de EVT"
    ident = perfil.identificacao
    if c.exige_membros:
        if not getattr(ident, "id_conjunto", None):
            return "a usina não está em conjunto de usinas"
        if not getattr(ident, "membros", None):
            return "sem os membros do conjunto no perfil"
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
    if c.programacao_da_usina and registro.nivel_coletado(perfil, "programacao") != "usina":
        return "Programação diária só no nível do conjunto: não se compara com o despacho da usina"
    if c.fontes_no_mesmo_nivel:
        niveis = [n for chave in FONTES_DA_GERACAO for n in niveis_coletados(perfil, chave)]
        if not any(niveis.count(n) >= 2 for n in ("usina", "conjunto")):
            return ("sem duas fontes da geração no mesmo nível (Geração por usina, Fator de capacidade e restrições): "
                    "par de níveis diferentes não se compara")
    if c.geracao_do_conjunto and "conjunto" not in niveis_coletados(perfil, "geracao"):
        return "Geração por usina sem o nível do conjunto: a soma das usinas não tem com o que se comparar"
    if c.programacao_no_nivel_do_fc:
        prog, fc = registro.nivel_coletado(perfil, "programacao"), registro.nivel_coletado(perfil, "fator_capacidade")
        if prog != fc:
            return f"Programação diária ({prog}) e Fator de capacidade ({fc}) em níveis diferentes: não se comparam"
    return None


def aplicaveis(perfil: Any) -> List[str]:
    """Conferências do catálogo que se aplicam à usina, na ordem do catálogo."""
    return [c.id for c in CATALOGO_CONFERENCIAS if _motivo_estatico(c, perfil) is None]


def tabela_nao_aplicaveis(perfil: Any, resultados: Dict[str, ResultadoConferencia]) -> pd.DataFrame:
    """``nao_aplicaveis.csv``: as conferências do catálogo que não se aplicam à usina, com o motivo, na ordem do
    catálogo; as que rodaram sem base entram com o motivo do resultado."""
    linhas = []
    tipo = registro.tipo_da_usina(perfil)
    for c in CATALOGO_CONFERENCIAS:
        if c.registrada_so_nos_tipos and tipo not in c.tipos:
            continue
        motivo = _motivo_estatico(c, perfil)
        r = resultados.get(c.id)
        if motivo is None and r is not None and not r.aplicavel:
            motivo = r.motivo
        if motivo is not None:
            linhas.append({"conferencia": c.id, "motivo": motivo})
    return pd.DataFrame(linhas, columns=COLUNAS_NAO_APLICAVEIS)
