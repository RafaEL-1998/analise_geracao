"""Fonte de cada figura, tabela e aba do relatório (spec da Geração do relatório).

Mapa único e declarativo usado pelo Markdown, pelo PDF e pela planilha (FR-027):

- ``CONJUNTOS``: os conjuntos do ONS usados no relatório (nome, identificador da usina, preenchido com o perfil, e
  id no catálogo), mais os parâmetros do projeto, que não são dado do ONS;
- ``CONFERENCIAS``: as conferências entre fontes refeitas pela Conferência a cada execução;
- ``MAPA_FONTES`` e as regras das abas: de onde vêm os dados de cada figura, tabela ou aba e com o que foram
  conferidos.

Os textos são gerados a partir dos resultados da análise (``ResultadosAnalise``) e das datas de obtenção
registradas nos manifestos; nenhum resultado de conferência é fixo (FR-026). As conferências manuais com outras
instituições ficam fora (decisão do usuário em 06/10/2026).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from src.coleta.conjuntos import data_obtencao
from src.comum import caminhos
from src.comum.formatacao import fmt_data, fmt_int, fmt_num, fmt_pct
from src.comum.logger import setup_logger
from src.comum.perfil import perfil_ativo
from src.comum.regras import (
    CONJUNTO_CADASTRO,
    CONJUNTO_DISPONIBILIDADE,
    CONJUNTO_EVT,
    CONJUNTO_GERACAO,
    CONJUNTO_HIDROLOGIA,
    CONJUNTO_PROGRAMACAO_DIARIA,
    CONJUNTOS_PIPELINE,
    META_ALINHAMENTO_HIDROLOGIA_PCT,
    TOLERANCIA_REPRODUCAO_TAXAS_PP,
)
from src.conferencia.resultado import diferenca_absoluta

logger = setup_logger("relatorio")

PREFIXO_FONTE = "Fonte dos dados:"
PREFIXO_CALCULADO = "Calculado neste relatório a partir de:"
SEM_REGISTRO = "data de obtenção não registrada"
ORIGEM_NAO_MAPEADA = "origem não mapeada"
COLUNAS_FONTES = ["aba", "conjuntos_origem", "conferencias", "sem_outra_fonte", "calculado_no_relatorio"]

# Dados mostrados no relatório que não têm outra fonte pública conferida pelo pipeline (FR-024)
EVT = "energia vertida turbinável (EVT)"
SINCRONIZADA = "disponibilidade sincronizada"
AFLUENCIA = "afluência"
AFLUENCIA_NIVEL = "afluência e nível do reservatório"
AFLUENCIA_NIVEIS_VOLUME = "afluência, níveis e volume útil"
PROGRAMACAO = "programação diária"


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Conjunto:
    """Conjunto de origem: nome no relatório, identificador da usina e id no catálogo.

    ``identificador`` é um modelo preenchido com a identificação do perfil da usina (``identificador_da_usina``).
    """

    nome: str
    identificador: str
    catalogo: str = ""  # id no catálogo do ONS; vazio para os parâmetros do projeto


CONJUNTOS: Dict[str, Conjunto] = {
    "evt": Conjunto("Energia Vertida Turbinável", "cod_usina {cod_usina}", CONJUNTO_EVT),
    "dispf_mensal": Conjunto("Indicadores de disponibilidade por unidade geradora, base mensal", "CEG {ceg}",
                             "ind_disponibilidade_fgeracao_uge_mensal"),
    "dispf_anual": Conjunto("Indicadores de disponibilidade por unidade geradora, base anual", "CEG {ceg}",
                            "ind_disponibilidade_fgeracao_uge_anual"),
    "teif_teip": Conjunto("Taxas TEIFa e TEIP", "CEG {ceg}", "taxa_teif_teip"),
    "teif_teip_parametro": Conjunto("Parâmetros das taxas TEIFa e TEIP", "CEG {ceg}", "taxa_teif_teip_parametro"),
    "programacao": Conjunto("Programação diária", "{cod_programacao}", CONJUNTO_PROGRAMACAO_DIARIA),
    "disponibilidade": Conjunto("Disponibilidade por usina", "id ONS {id_ons}", CONJUNTO_DISPONIBILIDADE),
    "hidrologia": Conjunto("Dados hidrológicos horários", "cod_usina {cod_usina}, reservatório {id_reservatorio}",
                           CONJUNTO_HIDROLOGIA),
    "geracao": Conjunto("Geração por usina", "id ONS {id_ons}", CONJUNTO_GERACAO),
    "cadastro": Conjunto("Modalidade das usinas", "CEG {ceg}", CONJUNTO_CADASTRO),
    "projeto": Conjunto("parâmetros do projeto", ""),
}


def identificador_da_usina(cid: str) -> str:
    """Identificador da usina no conjunto ``cid``, com os valores do perfil ativo."""
    i = perfil_ativo().identificacao
    return CONJUNTOS[cid].identificador.format(cod_usina=i.cod_usina, ceg=i.ceg, id_ons=i.id_ons,
                                               cod_programacao=i.cod_programacao, id_reservatorio=i.id_reservatorio)
INDICADORES = ("dispf_mensal", "dispf_anual", "teif_teip", "teif_teip_parametro")


@dataclass(frozen=True)
class Conferencia:
    """Conferência de um dado entre duas fontes, refeita pelo pipeline a cada execução."""

    dado: str
    base: str  # conjunto cuja presença permite a conferência
    texto: Callable[[Any], str]


@dataclass(frozen=True)
class Entrada:
    """Origem de uma figura, tabela ou aba."""

    conjuntos: Tuple[str, ...]
    conferencias: Tuple[str, ...] = ()
    sem_outra_fonte: Tuple[str, ...] = ()
    calculado: bool = False
    todos: bool = False  # cita os conjuntos mesmo quando não carregados nesta execução


def _e(conjuntos: Sequence[str], conferencias: Sequence[str] = (), sem: Sequence[str] = (),
       calculado: bool = False, todos: bool = False) -> Entrada:
    return Entrada(tuple(conjuntos), tuple(conferencias), tuple(sem), calculado, todos)


# ---------------------------------------------------------------------------
# Textos das conferências (resultados da execução)
# ---------------------------------------------------------------------------


def _texto_horas(c: Dict[str, Any], aba: str, chave_so_ons: str) -> str:
    texto = (f"{fmt_int(c['coincidentes'])} de {fmt_int(c['horas_comuns'])} horas coincidentes "
             f"({fmt_pct(c['pct_coincidentes'])})")
    if c.get("divergentes"):
        texto += f", {fmt_int(c['divergentes'])} divergências, listadas na aba {aba}"
    so_uma = int(c.get(chave_so_ons, 0) or 0) + int(c.get("so_base_evt", 0) or 0)
    if so_uma:
        texto += f", {fmt_int(so_uma)} horas só numa das fontes"
    return texto


def _conf_geracao(res: Any) -> str:
    return ("geração conferida com Geração por usina: "
            + _texto_horas(res.geracao_oficial["conferencia"], "GER_DIVERGENCIAS", "so_ons_geracao"))


def _conf_disponibilidade(res: Any) -> str:
    return ("disponibilidade declarada conferida com Disponibilidade por usina (operacional): "
            + _texto_horas(res.disponibilidade["conferencia"], "DISP_DIVERGENCIAS", "so_ons_disponibilidade"))


def _conf_vazoes(res: Any) -> str:
    a = res.hidrologia["alinhamento"].iloc[0]
    texto = (f"vazões turbinada e vertida conferidas com Dados hidrológicos horários: {fmt_int(a['coincidentes_ambas'])} "
             f"de {fmt_int(a['horas_comuns'])} horas coincidentes ({fmt_pct(a['pct_coincidencia'])})")
    if not bool(a["confirmado"]):
        texto += f", abaixo da meta de {fmt_num(META_ALINHAMENTO_HIDROLOGIA_PCT, 0)}%"
    return texto


def _conf_teifa_teip(res: Any) -> str:
    rr = res.ons.get("recalculo_resumo") or {}
    if "reproduzidos" in rr:  # contagem da Conferência, levada pelas Análises
        if not rr["meses"]:
            return "TEIFa e TEIP: conferência com Taxas TEIFa e TEIP não feita nesta execução"
        return (f"TEIFa e TEIP recalculadas conferidas com as publicadas em Taxas TEIFa e TEIP: "
                f"{fmt_int(rr['reproduzidos'])} de {fmt_int(rr['meses'])} meses reproduzidos (diferença máxima de "
                f"{fmt_num(rr['diferenca_maxima_pp'], 3)} p.p.)")
    recalculo = res.ons.get("recalculo_taxas")
    completos = recalculo.dropna(subset=["teifa_recalculada"]) if recalculo is not None else pd.DataFrame()
    if completos.empty:
        return "TEIFa e TEIP: conferência com Taxas TEIFa e TEIP não feita nesta execução"
    diferencas = completos[["diferenca_teifa_pp", "diferenca_teip_pp"]].abs()
    reproduzidos = int((diferenca_absoluta(diferencas) <= TOLERANCIA_REPRODUCAO_TAXAS_PP).all(axis=1).sum())
    maxima = float(diferencas.max().max())
    return (f"TEIFa e TEIP recalculadas conferidas com as publicadas em Taxas TEIFa e TEIP: {fmt_int(reproduzidos)} de "
            f"{fmt_int(len(completos))} meses reproduzidos (diferença máxima de {fmt_num(maxima, 3)} p.p.)")


def _conf_dispf_horas(res: Any) -> str:
    divergencias = res.ons.get("divergencias")
    n = 0 if divergencias is None else len(divergencias)
    texto = "DISPF conferido com as horas por estado operativo (Parâmetros das taxas TEIFa e TEIP): "
    return texto + (f"{fmt_int(n)} divergências (meses-unidade), listadas na aba ONS_DIVERGENCIAS" if n
                    else "sem divergência")


def _conf_cadastro(res: Any) -> str:
    divergencias = str(res.cadastro.get("divergencias") or "").strip()
    texto = "potência autorizada e estado conferidos com os parâmetros do projeto: "
    return texto + (f"divergências ({divergencias})" if divergencias else "sem divergência")


CONFERENCIAS: Dict[str, Conferencia] = {
    "geracao": Conferencia("geração", "geracao", _conf_geracao),
    "disponibilidade": Conferencia("disponibilidade declarada", "disponibilidade", _conf_disponibilidade),
    "vazoes": Conferencia("vazões turbinada e vertida", "hidrologia", _conf_vazoes),
    "teifa_teip": Conferencia("TEIFa e TEIP", "teif_teip", _conf_teifa_teip),
    "dispf_horas": Conferencia("DISPF", "teif_teip_parametro", _conf_dispf_horas),
    "cadastro": Conferencia("potência autorizada e estado", "cadastro", _conf_cadastro),
}


# ---------------------------------------------------------------------------
# Mapa das figuras, tabelas e blocos (PDF e Markdown)
# ---------------------------------------------------------------------------

_CONF_EVT = ("geracao", "disponibilidade")
_CONF_EVT_VAZOES = ("geracao", "disponibilidade", "vazoes")

MAPA_FONTES: Dict[str, Entrada] = {
    # Capa e cobertura (PDF)
    "bloco_identificacao": _e(["evt"]),
    "bloco_parametros": _e(["projeto"]),
    "tab_capa_indicadores": _e(["evt", "dispf_mensal", "teif_teip"],
                               ["geracao", "disponibilidade", "dispf_horas", "teifa_teip"],
                               [EVT], calculado=True),
    "tab_cobertura": _e(["evt"]),
    "bloco_cadastro": _e(["cadastro"], ["cadastro"]),
    # Base de EVT
    "tab_indicadores_anuais": _e(["evt", "projeto"], _CONF_EVT, [EVT], calculado=True),
    "tab_eventos_indisponibilidade": _e(["evt"], ["disponibilidade", "vazoes"], calculado=True),
    "tab_perfil_horario": _e(["evt"], ["geracao"], [EVT], calculado=True),
    "tab_evt_por_nivel": _e(["evt"], _CONF_EVT, [EVT], calculado=True),
    "tab_eventos_parada_evt": _e(["evt"], _CONF_EVT_VAZOES, [EVT], calculado=True),
    "tab_geracao_zero": _e(["evt"], _CONF_EVT, calculado=True),
    "tab_regras_validacao": _e(["evt"], calculado=True),
    "tab_registros_sinalizados": _e(["evt"], calculado=True),
    "tab_extremos": _e(["evt"], _CONF_EVT_VAZOES, [EVT], calculado=True),
    "tab_parametros": _e(["projeto"]),
    # Indicadores oficiais do ONS
    "tab_ons_disp_anual": _e(["evt", "dispf_mensal"], ["disponibilidade", "dispf_horas"], calculado=True),
    "tab_ons_decomposicao": _e(["teif_teip_parametro", "teif_teip"], ["teifa_teip"], calculado=True),
    "tab_ons_ug_anual": _e(["dispf_anual"], ["dispf_horas"]),
    "tab_ons_horas": _e(["teif_teip_parametro"], ["dispf_horas"]),
    "tab_ons_divergencias": _e(["dispf_mensal", "teif_teip_parametro"], ["dispf_horas"]),
    # Programação diária
    "tab_programacao_mensal": _e(["programacao", "evt"], ["geracao"], [PROGRAMACAO, EVT], calculado=True),
    "tab_programacao_hora": _e(["programacao", "evt"], ["geracao"], [PROGRAMACAO, EVT], calculado=True),
    "tab_programacao_eventos": _e(["programacao", "evt"], ["geracao"], [PROGRAMACAO, EVT], calculado=True),
    # Bases complementares
    "tab_disponibilidade_anual": _e(["disponibilidade", "evt", "teif_teip_parametro"], ["disponibilidade", "geracao"],
                                    [SINCRONIZADA], calculado=True),
    "tab_disponibilidade_paradas": _e(["disponibilidade", "evt", "programacao"], ["disponibilidade", "geracao"],
                                      [SINCRONIZADA, EVT], calculado=True),
    "tab_disponibilidade_divergencias": _e(["disponibilidade", "evt"], ["disponibilidade"]),
    "tab_faixas_afluencia": _e(["hidrologia", "evt"], ["vazoes"], [AFLUENCIA, EVT], calculado=True),
    "tab_faixas_afluencia_evt": _e(["hidrologia", "evt"], ["vazoes"], [AFLUENCIA, EVT], calculado=True),
    "tab_hidrologia_anual": _e(["hidrologia"], ["vazoes"], [AFLUENCIA_NIVEIS_VOLUME], calculado=True),
    "tab_hidrologia_perfil": _e(["hidrologia", "evt"], ["vazoes"], [AFLUENCIA_NIVEL], calculado=True),
    "tab_geracao_oficial": _e(["geracao", "evt"], ["geracao"], calculado=True),
    # Figuras (chaves de NOMES_FIGURAS e NOMES_FIGURAS_OPCIONAIS)
    "serie_temporal": _e(["evt"], _CONF_EVT, [EVT], calculado=True),
    "evt_mensal": _e(["evt"], (), [EVT], calculado=True),
    "perfil_horario": _e(["evt"], ["geracao"], [EVT], calculado=True),
    "disponibilidade_anual": _e(["evt", "projeto"], _CONF_EVT, calculado=True),
    "vazoes_defluentes": _e(["evt"], ["vazoes"], calculado=True),
    "disponibilidade_sincronizada": _e(["disponibilidade", "evt"], ["disponibilidade", "geracao"], [SINCRONIZADA],
                                       calculado=True),
    "faixas_afluencia": _e(["hidrologia", "evt"], ["vazoes"], [AFLUENCIA, EVT], calculado=True),
    "perfil_hidrologico": _e(["hidrologia", "evt"], ["vazoes"], [AFLUENCIA_NIVEL], calculado=True),
}


# ---------------------------------------------------------------------------
# Mapa das abas da planilha
# ---------------------------------------------------------------------------

_ABA_EVT = _e(["evt"], _CONF_EVT_VAZOES, [EVT], calculado=True)
_ABAS_EXATAS: Dict[str, Entrada] = {
    "INDICADORES_ANUAIS": MAPA_FONTES["tab_indicadores_anuais"],
    "INDICADORES_GLOBAIS": MAPA_FONTES["tab_indicadores_anuais"],
    "COBERTURA_POR_ANO": _e(["evt"], calculado=True),
    "AGENTES": _e(["evt"]),
    "EVT_MENSAL": MAPA_FONTES["evt_mensal"],
    "EVT_MES_DO_ANO": MAPA_FONTES["evt_mensal"],
    "EVT_POR_FAIXA_GERACAO": MAPA_FONTES["tab_evt_por_nivel"],
    "PERFIL_HORARIO_GERACAO": _e(["evt"], ["geracao"], calculado=True),
    "PERFIL_HORARIO_EVT": _e(["evt"], (), [EVT], calculado=True),
    "EVENTOS_PARADA_COM_EVT": MAPA_FONTES["tab_eventos_parada_evt"],
    "HORAS_GERACAO_ZERO_MES": MAPA_FONTES["tab_geracao_zero"],
    "EVENTOS_INDISP_TOTAL": MAPA_FONTES["tab_eventos_indisponibilidade"],
    "ANOMALIAS": MAPA_FONTES["tab_registros_sinalizados"],
    "RESUMO_ANOMALIAS": MAPA_FONTES["tab_registros_sinalizados"],
    "VALIDACAO_REGRAS": MAPA_FONTES["tab_regras_validacao"],
    "EXTREMOS": MAPA_FONTES["tab_extremos"],
    "PERFIL_ESTATISTICO_ANUAL": _ABA_EVT,
    "ONS_DISP_ANUAL_USINA": MAPA_FONTES["tab_ons_disp_anual"],
    "ONS_UG_ANUAL": MAPA_FONTES["tab_ons_ug_anual"],
    "ONS_HORAS_UG_ANUAL": MAPA_FONTES["tab_ons_horas"],
    "ONS_HORAS_UG_MENSAL": MAPA_FONTES["tab_ons_horas"],
    "ONS_TEIFA_TEIP": _e(["teif_teip"], ["teifa_teip"]),
    "ONS_DECOMPOSICAO_TAXAS": MAPA_FONTES["tab_ons_decomposicao"],
    "ONS_DIVERGENCIAS": MAPA_FONTES["tab_ons_divergencias"],
    "PROG_DIAS_AUSENTES": _e(["programacao"]),
    "PROG_AUDITORIA_ARQUIVOS": _e(["programacao"]),
    "DISP_AUSENCIAS": _e(["disponibilidade"]),
    "DISP_AUDITORIA": _e(["disponibilidade"]),
    "DISP_CONFERENCIA": _e(["disponibilidade", "evt"], ["disponibilidade"]),
    "DISP_DIVERGENCIAS": MAPA_FONTES["tab_disponibilidade_divergencias"],
    "HID_ALINHAMENTO": _e(["hidrologia", "evt"], ["vazoes"]),
    "HID_ANUAL": MAPA_FONTES["tab_hidrologia_anual"],
    "HID_MENSAL": MAPA_FONTES["tab_hidrologia_anual"],
    "HID_PERFIL_HORA_DO_DIA": MAPA_FONTES["tab_hidrologia_perfil"],
    "HID_AUSENCIAS": _e(["hidrologia"]),
    "HID_AUDITORIA": _e(["hidrologia"]),
    "GER_AUSENCIAS": _e(["geracao"]),
    "GER_AUDITORIA": _e(["geracao"]),
    "CAD_FICHA": MAPA_FONTES["bloco_cadastro"],
    "CAD_AUDITORIA": _e(["cadastro"]),
}
_ABAS_POR_PREFIXO: List[Tuple[str, Entrada]] = [
    ("PROG_", MAPA_FONTES["tab_programacao_mensal"]),
    ("DISP_", MAPA_FONTES["tab_disponibilidade_paradas"]),
    ("HID_", MAPA_FONTES["tab_faixas_afluencia"]),
    ("GER_", MAPA_FONTES["tab_geracao_oficial"]),
]


# ---------------------------------------------------------------------------
# Origem dos dados carregados
# ---------------------------------------------------------------------------


def conjuntos_carregados(res: Any) -> List[str]:
    """Conjuntos do ONS cujos dados entraram nesta análise; a base de EVT sempre entra (N do rodapé)."""
    carregados = ["evt"]
    if res.ons:
        carregados += list(INDICADORES)
    for cid, campo in (("programacao", "programacao"), ("disponibilidade", "disponibilidade"),
                       ("hidrologia", "hidrologia"), ("geracao", "geracao_oficial"), ("cadastro", "cadastro")):
        if getattr(res, campo):
            carregados.append(cid)
    return carregados


def datas_obtencao(raiz_raw: Optional[Path] = None) -> Dict[str, str]:
    """Data (UTC) mais recente registrada no manifesto de cada conjunto; vazia se não houver registro."""
    datas: Dict[str, str] = {}
    for cid, conjunto in CONJUNTOS.items():
        if conjunto.catalogo:
            datas[cid] = data_obtencao(Path(raiz_raw or caminhos.RAW_DATA_DIR) / CONJUNTOS_PIPELINE[conjunto.catalogo])
    return datas


def origem_dos_dados(res: Any, raiz_raw: Optional[Path] = None) -> Dict[str, Any]:
    """Conteúdo de ``res.fontes``: datas de obtenção e conjuntos carregados."""
    return {"obtencao": datas_obtencao(raiz_raw), "carregados": conjuntos_carregados(res)}


# ---------------------------------------------------------------------------
# Textos
# ---------------------------------------------------------------------------


def _carregados(res: Any) -> List[str]:
    fontes = getattr(res, "fontes", None) or {}
    return fontes.get("carregados") or conjuntos_carregados(res)


def texto_conjunto(res: Any, cid: str) -> str:
    """"<nome> (<identificador>), obtido em dd/mm/aaaa"; os parâmetros do projeto remetem à tabela de parâmetros."""
    if cid == "projeto":
        return "parâmetros do projeto (origem na tabela de parâmetros)"
    conjunto = CONJUNTOS[cid]
    data = ((getattr(res, "fontes", None) or {}).get("obtencao") or {}).get(cid, "")
    quando = f"obtido em {fmt_data(data)}" if data else SEM_REGISTRO
    return f"{conjunto.nome} ({identificador_da_usina(cid)}), {quando}"


def texto_conferencia(res: Any, cid: str) -> str:
    """Resultado da conferência nesta execução, ou o aviso de que não foi feita (FR-026)."""
    conferencia = CONFERENCIAS[cid]
    if conferencia.base not in _carregados(res):
        return f"{conferencia.dado}: conferência com {CONJUNTOS[conferencia.base].nome} não feita nesta execução"
    return conferencia.texto(res)


def _textos_entrada(res: Any, entrada: Entrada) -> Tuple[List[str], List[str]]:
    carregados = _carregados(res)
    conjuntos = list(entrada.conjuntos) if entrada.todos else (
        [c for c in entrada.conjuntos if c == "projeto" or c in carregados] or list(entrada.conjuntos))
    return [texto_conjunto(res, c) for c in conjuntos], [texto_conferencia(res, c) for c in entrada.conferencias]


def _entrada(chave: str) -> Optional[Entrada]:
    entrada = MAPA_FONTES.get(chave)
    if entrada is None:
        logger.warning("Figura ou tabela sem entrada no mapa de fontes: %s", chave)
    return entrada


def legenda_fonte(res: Any, chave: str) -> str:
    """Legenda de fonte de uma figura, tabela ou bloco, no formato da spec da Geração do relatório (FR-024)."""
    entrada = _entrada(chave)
    if entrada is None:
        return f"{PREFIXO_FONTE} {ORIGEM_NAO_MAPEADA}."
    conjuntos, conferencias = _textos_entrada(res, entrada)
    prefixo = PREFIXO_CALCULADO if entrada.calculado else PREFIXO_FONTE
    partes = [f"{prefixo} {'; '.join(conjuntos)}."]
    if conferencias:
        partes.append(f"Conferência: {'; '.join(conferencias)}.")
    if entrada.sem_outra_fonte:
        partes.append(f"Sem outra fonte para conferir: {', '.join(entrada.sem_outra_fonte)}.")
    return " ".join(partes)


# ---------------------------------------------------------------------------
# Aba FONTES
# ---------------------------------------------------------------------------


def _entrada_aba(res: Any, aba: str) -> Optional[Entrada]:
    if aba in ("CONSTATACOES", "CONCLUSAO"):
        carregados = _carregados(res)
        return _e(carregados, [c for c, conf in CONFERENCIAS.items() if conf.base in carregados], calculado=True)
    if aba == "PARAMETROS":
        return _e(["projeto", *_carregados(res)])
    if aba == "DICIONARIOS":
        return _e([c for c in CONJUNTOS if c != "projeto"], todos=True)
    if aba in _ABAS_EXATAS:
        return _ABAS_EXATAS[aba]
    for prefixo, entrada in _ABAS_POR_PREFIXO:
        if aba.startswith(prefixo):
            return entrada
    return None


def tabela_fontes_abas(res: Any, abas: Sequence[str]) -> pd.DataFrame:
    """Aba FONTES: para cada aba exportada, os conjuntos de origem e as conferências (FR-028)."""
    linhas = []
    for aba in abas:
        entrada = _entrada_aba(res, aba)
        if entrada is None:
            logger.warning("Aba sem entrada no mapa de fontes: %s", aba)
            linhas.append([aba, ORIGEM_NAO_MAPEADA, "—", "—", "não"])
            continue
        conjuntos, conferencias = _textos_entrada(res, entrada)
        linhas.append([aba, "; ".join(conjuntos), "; ".join(conferencias) or "—",
                       ", ".join(entrada.sem_outra_fonte) or "—", "sim" if entrada.calculado else "não"])
    return pd.DataFrame(linhas, columns=COLUNAS_FONTES)


__all__ = [
    "CONFERENCIAS", "CONJUNTOS", "MAPA_FONTES", "PREFIXO_CALCULADO", "PREFIXO_FONTE", "conjuntos_carregados",
    "datas_obtencao", "identificador_da_usina", "legenda_fonte", "origem_dos_dados", "tabela_fontes_abas",
    "texto_conferencia", "texto_conjunto",
]
