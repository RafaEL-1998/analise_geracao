"""Estrutura do relatório (spec da Geração do relatório): seções em ordem, constatação → seção e sumário.

Declarada uma vez e usada pelo PDF e pelo Markdown, para que as duas saídas tenham as mesmas seções, na mesma
ordem, e cada constatação apareça uma única vez, no início da seção a que se refere (FR-009, FR-010 e FR-017).

Uma única lista, em ordem fixa, com os dois caminhos da spec 006 (decisão R14): a hidrelétrica com EVT vê exatamente as
17 seções de hoje; a usina sem EVT vê as seções comuns do seu tipo, com as seções sem base omitidas e a numeração
contínua.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from src.analises.resultados import sem_evt
from src.coleta.registro import HIDRELETRICAS, TERMICAS
from src.comum.logger import setup_logger
from src.comum.regras import PERIODO_MINIMO_SAZONALIDADE_MESES, TIPOS_USINA

logger = setup_logger("relatorio")


def _sempre(res: Any) -> bool:
    return True


# Caminhos do relatório (decisão R14)
COM_EVT = "evt"
SEM_EVT = "sem_evt"
COM_DISPONIBILIDADE: Tuple[str, ...] = HIDRELETRICAS + TERMICAS


@dataclass(frozen=True)
class Secao:
    """Seção do relatório (data-model 6.5): chave estável, título, condição de presença, caminhos e tipos.

    ``titulo`` é um texto ou um mapa tipo -> título (com a chave "" como padrão); ``periodo_minimo_meses`` é o
    período que a seção (ou parte dela) pede (decisão R17). Os tipos só filtram o caminho sem EVT. A legenda de fonte
    é de cada tabela e figura da seção (a chave vem com o bloco, em ``src/relatorio/comum.py``), não da seção.
    """

    chave: str
    titulo: Union[str, Dict[str, str]]
    presente: Callable[[Any], bool] = _sempre
    caminhos: Tuple[str, ...] = (COM_EVT,)
    tipos: Tuple[str, ...] = TIPOS_USINA
    periodo_minimo_meses: Optional[int] = None

    def titulo_para(self, tipo: str = "") -> str:
        if isinstance(self.titulo, dict):
            return self.titulo.get(tipo, self.titulo.get("", ""))
        return self.titulo


def _comum(chave: str, titulo: str, presente: Callable[[Any], bool] = _sempre,
           tipos: Tuple[str, ...] = TIPOS_USINA, **campos: Any) -> Secao:
    return Secao(chave, titulo, presente, (SEM_EVT,), tipos, **campos)


SECOES: Tuple[Secao, ...] = (
    Secao("cobertura", "Fonte e cobertura dos dados"),
    _comum("fonte_cobertura", "Fonte e cobertura dos dados"),
    Secao("indicadores_anuais", "Indicadores anuais"),
    _comum("anuais_comum", "Indicadores anuais"),
    Secao("disponibilidade_geracao", "Disponibilidade e geração por ano"),
    _comum("disponibilidade_geracao_comum", "Disponibilidade e geração por ano",
           lambda res: bool(res.comum.get("disponibilidade")), COM_DISPONIBILIDADE),
    Secao("indicadores_ons", "Indicadores oficiais do ONS por unidade geradora", lambda res: bool(res.ons)),
    _comum("indicadores_ons_comum", "Indicadores oficiais do ONS por unidade geradora", lambda res: bool(res.ons),
           COM_DISPONIBILIDADE),
    Secao("serie_temporal", "Série temporal de disponibilidade, geração e EVT"),
    # eólicas e solares não têm a disponibilidade no ONS: o título só com a geração
    _comum("serie_temporal_comum", {"": "Série temporal da geração e da disponibilidade",
                                    "EOL": "Série temporal da geração", "UFV": "Série temporal da geração"}),
    Secao("evt_mensal", "Energia vertida turbinável mensal"),
    _comum("geracao_mensal", "Geração mensal e sazonalidade",
           periodo_minimo_meses=PERIODO_MINIMO_SAZONALIDADE_MESES),  # o período mínimo vale para a sazonalidade
    Secao("perfil_horario", "Perfil horário da geração e da EVT"),
    _comum("perfil_horario_comum", "Perfil horário da geração"),
    Secao("eventos", "EVT por nível de geração e eventos de usina parada"),
    Secao("programacao", "Operação verificada e programação diária do ONS", lambda res: bool(res.programacao)),
    _comum("programacao_comum", "Programação diária × geração verificada",
           lambda res: bool(res.comum.get("programacao"))),
    Secao("disponibilidade_sincronizada", "Disponibilidade operacional e sincronizada (ONS)",
          lambda res: bool(res.disponibilidade)),
    _comum("disponibilidade_sincronizada_comum", "Disponibilidade operacional e sincronizada (ONS)",
           lambda res: bool(res.comum.get("disponibilidade")), COM_DISPONIBILIDADE),
    Secao("hidrologia", "Afluência, vertimento e nível do reservatório (ONS)", lambda res: bool(res.hidrologia)),
    Secao("geracao_zero", "Horas com geração zero por mês"),
    Secao("vazoes", "Vazões defluentes por ano"),
    Secao("geracao_oficial", "Conferência da geração com a série oficial (ONS)", lambda res: bool(res.geracao_oficial)),
    Secao("qualidade", "Qualidade dos dados"),
    _comum("qualidade_comum", "Qualidade dos dados"),
    # spec da Geração do relatório, US4: sempre presente, antes das notas; a mesma nos dois caminhos (decisão R16)
    Secao("conclusao", "Conclusão", caminhos=(COM_EVT, SEM_EVT)),
    Secao("notas", "Notas metodológicas e limitações"),
    _comum("notas_comum", "Notas metodológicas e limitações"),
)
SECAO_PADRAO = "cobertura"
SECAO_PADRAO_SEM_EVT = "fonte_cobertura"

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
# O mesmo nas usinas sem EVT (constatações de ``montar_achados_comum``)
MAPA_CONSTATACOES_SEM_EVT: Dict[str, str] = {
    "Cobertura dos dados": "fonte_cobertura",
    "Cadastro da usina no ONS": "fonte_cobertura",
    "Geração": "anuais_comum",
    "Disponibilidade": "disponibilidade_geracao_comum",
    "Programação diária do ONS": "programacao_comum",
    "Qualidade dos dados": "qualidade_comum",
}


def caminho(res: Any) -> str:
    """Caminho do relatório da usina: com EVT ou sem EVT (decisão R14)."""
    return SEM_EVT if sem_evt(res) else COM_EVT


def secoes_presentes(res: Any) -> List[Tuple[int, Secao]]:
    """Seções presentes nesta execução, numeradas 1, 2, 3, … sem lacunas, na ordem do relatório.

    Só as do caminho da usina; no caminho sem EVT, também só as do tipo da usina."""
    c = caminho(res)
    tipo = getattr(res, "tipo", "")
    return list(enumerate((s for s in SECOES if c in s.caminhos and (c == COM_EVT or tipo in s.tipos)
                           and s.presente(res)), start=1))


def _mapa(res: Any) -> Tuple[Dict[str, str], str]:
    return (MAPA_CONSTATACOES_SEM_EVT, SECAO_PADRAO_SEM_EVT) if sem_evt(res) else (MAPA_CONSTATACOES, SECAO_PADRAO)


def _destino(titulo: str, presentes: set, mapa: Dict[str, str] = MAPA_CONSTATACOES, padrao: str = SECAO_PADRAO) -> str:
    destino = mapa.get(titulo)
    return destino if destino in presentes else padrao


def constatacoes_da_secao(res: Any, chave: str) -> List[Tuple[str, str]]:
    """Constatações (título, texto) apresentadas no início da seção, na ordem de ``res.achados``.

    Constatação sem seção no mapa, ou cuja seção não está presente, vai para a primeira seção, com aviso no log;
    nenhuma constatação desaparece.
    """
    presentes = {s.chave for _, s in secoes_presentes(res)}
    mapa, padrao = _mapa(res)
    saida = []
    for titulo, texto in res.achados:
        destino = _destino(titulo, presentes, mapa, padrao)
        if destino == padrao and mapa.get(titulo) != padrao and chave == padrao:
            logger.warning("Constatação sem seção no relatório, apresentada em '%s': %s", padrao, titulo)
        if destino == chave:
            saida.append((titulo, texto))
    return saida


def titulo_da_secao(secao: Secao, res: Any) -> str:
    """Título da seção para o tipo da usina."""
    return secao.titulo_para(getattr(res, "tipo", ""))


def sumario(res: Any) -> List[Tuple[int, str]]:
    """Itens do sumário: número e título de cada seção presente."""
    return [(n, titulo_da_secao(s, res)) for n, s in secoes_presentes(res)]
