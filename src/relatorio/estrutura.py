"""Estrutura do relatório (spec da Geração do relatório): seções em ordem, constatação → seção e sumário.

Declarada uma vez e usada pelo PDF e pelo Markdown, para que as duas saídas tenham as mesmas seções, na mesma
ordem, e cada constatação apareça uma única vez, no início da seção a que se refere (FR-009, FR-010 e FR-017).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple

from src.comum.logger import setup_logger

logger = setup_logger("relatorio")


def _sempre(res: Any) -> bool:
    return True


@dataclass(frozen=True)
class Secao:
    """Seção do relatório: chave estável, título exibido e condição de presença."""

    chave: str
    titulo: str
    presente: Callable[[Any], bool] = _sempre


SECOES: Tuple[Secao, ...] = (
    Secao("cobertura", "Fonte e cobertura dos dados"),
    Secao("indicadores_anuais", "Indicadores anuais"),
    Secao("disponibilidade_geracao", "Disponibilidade e geração por ano"),
    Secao("indicadores_ons", "Indicadores oficiais do ONS por unidade geradora", lambda res: bool(res.ons)),
    Secao("serie_temporal", "Série temporal de disponibilidade, geração e EVT"),
    Secao("evt_mensal", "Energia vertida turbinável mensal"),
    Secao("perfil_horario", "Perfil horário da geração e da EVT"),
    Secao("eventos", "EVT por nível de geração e eventos de usina parada"),
    Secao("programacao", "Operação verificada e programação diária do ONS", lambda res: bool(res.programacao)),
    Secao("disponibilidade_sincronizada", "Disponibilidade operacional e sincronizada (ONS)",
          lambda res: bool(res.disponibilidade)),
    Secao("hidrologia", "Afluência, vertimento e nível do reservatório (ONS)", lambda res: bool(res.hidrologia)),
    Secao("geracao_zero", "Horas com geração zero por mês"),
    Secao("vazoes", "Vazões defluentes por ano"),
    Secao("geracao_oficial", "Conferência da geração com a série oficial (ONS)", lambda res: bool(res.geracao_oficial)),
    Secao("qualidade", "Qualidade dos dados"),
    Secao("conclusao", "Conclusão"),  # spec da Geração do relatório, US4: sempre presente, antes das notas
    Secao("notas", "Notas metodológicas e limitações"),
)
SECAO_PADRAO = "cobertura"

# Título da constatação (fixo em analyzer.montar_achados) → chave da seção onde ela é apresentada
MAPA_CONSTATACOES: Dict[str, str] = {
    "Cobertura dos dados": "cobertura",
    "Cadastro da usina no ONS": "cobertura",  # a ficha do cadastro fica na capa (FR-012)
    "Disponibilidade": "indicadores_anuais",
    "Indicadores oficiais de disponibilidade (ONS)": "indicadores_ons",
    "Estados operativos das unidades geradoras (ONS)": "indicadores_ons",
    "Indisponibilidades": "disponibilidade_geracao",
    "Geração e garantia física": "disponibilidade_geracao",
    "Energia vertida turbinável": "evt_mensal",
    "EVT e nível de geração": "eventos",
    "EVT com a usina parada": "eventos",
    "Programação diária do ONS": "programacao",
    "Disponibilidade sincronizada": "disponibilidade_sincronizada",
    "Afluência e vertimento": "hidrologia",
    "Horas com geração zero": "geracao_zero",
    "Concentração diurna": "perfil_horario",
    "Distribuição ao longo do ano": "evt_mensal",
    "Mudança de classificação do vertimento pelo ONS": "evt_mensal",
    "Conferência da geração": "geracao_oficial",
    "Qualidade dos dados": "qualidade",
}


def secoes_presentes(res: Any) -> List[Tuple[int, Secao]]:
    """Seções presentes nesta execução, numeradas 1, 2, 3, … sem lacunas, na ordem do relatório."""
    return list(enumerate((s for s in SECOES if s.presente(res)), start=1))


def _destino(titulo: str, presentes: set) -> str:
    destino = MAPA_CONSTATACOES.get(titulo)
    return destino if destino in presentes else SECAO_PADRAO


def constatacoes_da_secao(res: Any, chave: str) -> List[Tuple[str, str]]:
    """Constatações (título, texto) apresentadas no início da seção, na ordem de ``res.achados``.

    Constatação sem seção no mapa, ou cuja seção não está presente, vai para a primeira seção, com aviso no log;
    nenhuma constatação desaparece.
    """
    presentes = {s.chave for _, s in secoes_presentes(res)}
    saida = []
    for titulo, texto in res.achados:
        destino = _destino(titulo, presentes)
        if destino == SECAO_PADRAO and MAPA_CONSTATACOES.get(titulo) != SECAO_PADRAO and chave == SECAO_PADRAO:
            logger.warning("Constatação sem seção no relatório, apresentada em '%s': %s", SECAO_PADRAO, titulo)
        if destino == chave:
            saida.append((titulo, texto))
    return saida


def sumario(res: Any) -> List[Tuple[int, str]]:
    """Itens do sumário: número e título de cada seção presente."""
    return [(n, s.titulo) for n, s in secoes_presentes(res)]
