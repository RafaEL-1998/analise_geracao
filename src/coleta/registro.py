"""Registro dos conjuntos do ONS (spec 006, decisão R8; data-model, seção 4).

Um só lugar diz o que se coleta para cada tipo de usina. Cada entrada declara o pacote no portal e a pasta em
``data/raw/``, os tipos de usina, os níveis do dado (usina, conjunto ou agregado), a resolução e se o conjunto pode ser a
série de referência. Os conjuntos horários (disponibilidade, hidrologia e geração) trazem também a descrição usada pelo
motor comum de ``src.coleta.conjuntos``, montada com a identificação do perfil. A EVT, os indicadores, a programação e o
cadastro mantêm os módulos próprios, mas ficam registrados para o filtro por tipo e os dicionários.

A Coleta, os dicionários e as fontes do relatório usam só os conjuntos do tipo e da cobertura da usina (FR-015). Na UHE
sem ``[cobertura]``, são os dez conjuntos de hoje, na mesma ordem.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, replace
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from src.comum.regras import (
    CONJUNTO_CADASTRO,
    CONJUNTO_DISPONIBILIDADE,
    CONJUNTO_EVT,
    CONJUNTO_GERACAO,
    CONJUNTO_HIDROLOGIA,
    CONJUNTO_PROGRAMACAO_DIARIA,
    CONJUNTOS_INDICADORES_ONS,
    PASTA_CADASTRO_RAW,
    PASTA_DISPONIBILIDADE_RAW,
    PASTA_GERACAO_RAW,
    PASTA_HIDROLOGIA_RAW,
    PASTA_INDICADORES_RAW,
    PASTA_PROGRAMACAO_RAW,
    TIPOS_USINA,
)

# Enumerações (data-model, seção 1)
HIDRELETRICAS: Tuple[str, ...] = ("UHE", "PCH", "CGH")
TERMICAS: Tuple[str, ...] = ("UTE", "UTN")
NIVEIS: Tuple[str, ...] = ("usina", "conjunto", "agregado")
RESOLUCOES: Tuple[str, ...] = ("horaria", "semi_horaria", "semanal", "mensal_anual", "estatica")
COBERTURA_AUSENTE = "ausente"
COBERTURAS_QUE_OBTEM: Tuple[str, ...] = ("proprio", "conjunto")
# Nível do dado para cada valor da cobertura do perfil
NIVEL_DA_COBERTURA: Dict[str, str] = {"proprio": "usina", "conjunto": "conjunto", "agregado": "agregado"}

VAZOES = ("val_vazaoafluente", "val_vazaodefluente", "val_vazaoturbinada", "val_vazaovertida",
          "val_vazaovertidanaoturbinavel", "val_vazaooutrasestruturas")
COLUNA_INSTANTE = "din_instante"


def normalizar_texto(valor: Any) -> str:
    """A normalização única da Coleta: sem acento, sem espaços nas pontas e em maiúsculas (correção P3)."""
    if valor is None:
        return ""
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", str(valor)) if not unicodedata.combining(c))
    return sem_acento.strip().upper()


@dataclass(frozen=True)
class Regra:
    """Condição sobre uma coluna: ``igual`` (texto normalizado ou número) ou ``contem`` (texto normalizado)."""

    coluna: str
    valor: Any
    modo: str = "igual"


@dataclass(frozen=True)
class DescricaoConjunto:
    """Descrição declarativa de um conjunto do ONS para uma usina, lida pelo motor de ``src.coleta.conjuntos``."""

    pacote: str
    pasta: str
    identificador: Regra
    conferencias: Tuple[Regra, ...]
    colunas_valor: Tuple[str, ...]
    convencao_hora: str = "inicio"  # "inicio" ou "fim" (aplicada no Tratamento de dados)
    formatos_preferidos: Tuple[str, ...] = ("PARQUET", "CSV")
    # Filtro empurrado à leitura do Parquet (DNF do pyarrow), útil nos arquivos grandes com todas as usinas
    filtro_parquet: Optional[Tuple[Tuple[Tuple[str, str, Any], ...], ...]] = None
    # Registro (spec 006, decisão R8)
    chave: str = ""
    tipos: Tuple[str, ...] = TIPOS_USINA
    nivel: str = "usina"
    resolucao: str = "horaria"
    referencia: bool = False
    variantes: Tuple[Tuple[str, str], ...] = ()  # (tipo, pacote) quando o pacote muda com o tipo

    @property
    def colunas_leitura(self) -> List[str]:
        colunas = [self.identificador.coluna, *(r.coluna for r in self.conferencias), COLUNA_INSTANTE,
                   *self.colunas_valor]
        return list(dict.fromkeys(colunas))


def _formas(valor: Any) -> Tuple[str, ...]:
    """O valor como no perfil e a forma normalizada, para o filtro empurrado à leitura do Parquet (correção P3)."""
    texto = str(valor)
    return tuple(dict.fromkeys([texto, normalizar_texto(texto)]))


# ---------------------------------------------------------------------------
# Descrições dos conjuntos horários, com a identificação do perfil
# ---------------------------------------------------------------------------


def _disponibilidade(perfil: Any) -> DescricaoConjunto:
    ident, estado = perfil.identificacao, perfil.usina.estado
    return DescricaoConjunto(
        pacote=CONJUNTO_DISPONIBILIDADE, pasta=PASTA_DISPONIBILIDADE_RAW,
        identificador=Regra("id_ons", ident.id_ons),
        conferencias=(Regra("ceg", ident.ceg), Regra("id_estado", estado)),
        colunas_valor=("val_potenciainstalada", "val_dispoperacional", "val_dispsincronizada"),
    )


def _hidrologia(perfil: Any) -> DescricaoConjunto:
    ident = perfil.identificacao
    return DescricaoConjunto(
        pacote=CONJUNTO_HIDROLOGIA, pasta=PASTA_HIDROLOGIA_RAW,
        identificador=Regra("cod_usina", ident.cod_usina),
        conferencias=(Regra("nom_reservatorio", ident.nome_ons, "contem"),
                      Regra("id_reservatorio", ident.id_reservatorio)),
        colunas_valor=(*VAZOES, "val_nivelmontante", "val_niveljusante", "val_volumeutil"),
        convencao_hora="fim",
    )


def _geracao(perfil: Any) -> DescricaoConjunto:
    ident, estado = perfil.identificacao, perfil.usina.estado
    return DescricaoConjunto(
        pacote=CONJUNTO_GERACAO, pasta=PASTA_GERACAO_RAW,
        identificador=Regra("id_ons", ident.id_ons),
        conferencias=(Regra("ceg", ident.ceg), Regra("id_estado", estado)),
        colunas_valor=("val_geracao",),
        filtro_parquet=((("id_ons", "in", _formas(ident.id_ons)),), (("ceg", "in", _formas(ident.ceg)),)),
    )


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EntradaRegistro:
    """O que o registro declara de um conjunto do ONS (data-model, seção 4)."""

    chave: str
    pacotes: Tuple[Tuple[str, str], ...]  # (pacote no portal, pasta em data/raw/), na ordem de coleta
    tipos: Tuple[str, ...]
    niveis: Tuple[str, ...]
    resolucao: str
    referencia: bool = False  # pode ser a série de referência (decisão R6)
    variantes: Tuple[Tuple[str, str], ...] = ()  # (tipo, pacote) quando o pacote muda com o tipo
    descricao: Optional[Callable[[Any], DescricaoConjunto]] = None  # conjuntos lidos pelo motor comum

    @property
    def na_cobertura(self) -> bool:
        """Conjunto de série, declarado na ``[cobertura]``; os cadastrais e os do subsistema são sempre obtidos."""
        return self.resolucao != "estatica" and self.niveis != ("agregado",)


REGISTRO: Tuple[EntradaRegistro, ...] = (
    EntradaRegistro("evt", ((CONJUNTO_EVT, ""),), HIDRELETRICAS, ("usina",), "horaria", referencia=True),
    EntradaRegistro("indicadores", tuple((c, f"{PASTA_INDICADORES_RAW}/{c}") for c in CONJUNTOS_INDICADORES_ONS),
                    HIDRELETRICAS + TERMICAS, ("usina",), "mensal_anual"),
    EntradaRegistro("programacao", ((CONJUNTO_PROGRAMACAO_DIARIA, PASTA_PROGRAMACAO_RAW),), TIPOS_USINA,
                    ("usina", "conjunto"), "semi_horaria"),
    EntradaRegistro("disponibilidade", ((CONJUNTO_DISPONIBILIDADE, PASTA_DISPONIBILIDADE_RAW),),
                    HIDRELETRICAS + TERMICAS, ("usina",), "horaria", descricao=_disponibilidade),
    EntradaRegistro("hidrologia", ((CONJUNTO_HIDROLOGIA, PASTA_HIDROLOGIA_RAW),), HIDRELETRICAS, ("usina",),
                    "horaria", descricao=_hidrologia),
    EntradaRegistro("geracao", ((CONJUNTO_GERACAO, PASTA_GERACAO_RAW),), TIPOS_USINA, ("usina", "conjunto"),
                    "horaria", referencia=True, descricao=_geracao),
    EntradaRegistro("cadastro", ((CONJUNTO_CADASTRO, PASTA_CADASTRO_RAW),), TIPOS_USINA, ("usina",), "estatica"),
)


def pacotes(entradas: Iterable[EntradaRegistro]) -> Dict[str, str]:
    """{pacote: pasta em data/raw/} das entradas, na ordem do registro."""
    return {pacote: pasta for entrada in entradas for pacote, pasta in entrada.pacotes}


# Todos os conjuntos registrados (pacote -> pasta), na ordem do registro
CONJUNTOS_PIPELINE: Dict[str, str] = pacotes(REGISTRO)
# Sem [cobertura] (só na UHE): os dez conjuntos de hoje, e mais nenhum (decisão R8)
CHAVES_SEM_COBERTURA: Tuple[str, ...] = ("evt", "indicadores", "programacao", "disponibilidade", "hidrologia", "geracao",
                                         "cadastro")


def entrada(chave: str) -> EntradaRegistro:
    """Entrada do registro pela chave."""
    for e in REGISTRO:
        if e.chave == chave:
            return e
    raise KeyError(f"conjunto não registrado: {chave!r}")


def tipo_da_usina(perfil: Any) -> str:
    """Tipo da usina: o do perfil ou, sem ele, o prefixo do CEG (decisão R1)."""
    tipo = getattr(perfil.usina, "tipo", None)
    if tipo:
        return str(tipo).upper()
    prefixo = str(perfil.identificacao.ceg).split(".", 1)[0].upper()
    if prefixo not in TIPOS_USINA:
        raise ValueError(f"tipo de usina desconhecido no CEG {perfil.identificacao.ceg!r}")
    return prefixo


def cobertura_da_usina(perfil: Any) -> Dict[str, Any]:
    """Tabela ``[cobertura]`` do perfil (chave do conjunto -> nível); vazia na UHE, que não a declara."""
    return dict(getattr(perfil, "cobertura", None) or {})


def chaves_da_cobertura(tipo: str) -> Tuple[str, ...]:
    """Chaves aceitas na ``[cobertura]`` de uma usina do tipo: os conjuntos de série que servem a ele."""
    return tuple(e.chave for e in REGISTRO if e.na_cobertura and tipo in e.tipos)


def _obtido(valor: Any) -> bool:
    valores = valor if isinstance(valor, (list, tuple)) else [valor]
    return any(v in COBERTURAS_QUE_OBTEM for v in valores)


def conjuntos_da_usina(perfil: Any) -> List[EntradaRegistro]:
    """Conjuntos que a Coleta obtém para a usina, na ordem do registro (FR-015; data-model 3.3).

    Sem ``[cobertura]`` (só na UHE), os dez de hoje. Com ela, os conjuntos de série com ``proprio`` ou ``conjunto``
    (ou a lista dos dois) e, sempre, os cadastrais e os do subsistema do tipo.
    """
    tipo, cobertura = tipo_da_usina(perfil), cobertura_da_usina(perfil)
    do_tipo = [e for e in REGISTRO if tipo in e.tipos]
    if not cobertura:
        return [e for e in do_tipo if e.chave in CHAVES_SEM_COBERTURA]
    return [e for e in do_tipo if not e.na_cobertura or _obtido(cobertura.get(e.chave))]


def _nivel(e: EntradaRegistro, cobertura: Dict[str, Any]) -> str:
    valor = cobertura.get(e.chave)
    valores = valor if isinstance(valor, (list, tuple)) else [valor]
    niveis = [NIVEL_DA_COBERTURA[v] for v in valores if v in NIVEL_DA_COBERTURA]
    return niveis[0] if niveis else e.niveis[0]


def descricoes(perfil: Any) -> Dict[str, DescricaoConjunto]:
    """Descrições, com a identificação do perfil, dos conjuntos da usina lidos pelo motor comum."""
    cobertura = cobertura_da_usina(perfil)
    return {
        e.chave: replace(e.descricao(perfil), chave=e.chave, tipos=e.tipos, nivel=_nivel(e, cobertura),
                         resolucao=e.resolucao, referencia=e.referencia, variantes=e.variantes)
        for e in conjuntos_da_usina(perfil) if e.descricao is not None
    }
