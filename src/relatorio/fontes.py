"""Fonte de cada figura, tabela e aba do relatório (spec da Geração do relatório).

Mapa único e declarativo usado pelo Markdown, pelo PDF e pela planilha (FR-027):

- ``CONJUNTOS``: os conjuntos do ONS usados no relatório (nome, identificador da usina, preenchido com o perfil, e
  id no catálogo), mais os parâmetros do projeto, que não são dado do ONS;
- ``CONFERENCIAS``: as conferências entre fontes refeitas pela Conferência a cada execução;
- ``MAPA_FONTES`` e as regras das abas: de onde vêm os dados de cada figura, tabela ou aba e com o que foram
  conferidos.

Os textos são gerados a partir dos resultados da análise (``ResultadosAnalise``), com as datas de obtenção
gravadas pela Coleta; nenhum resultado de conferência é fixo (FR-026). As conferências manuais com outras
instituições ficam fora (decisão do usuário em 06/10/2026).

Nas usinas sem EVT (spec 006, decisão R15), a legenda de um dado de conjunto cita o identificador dele com o nível
escrito ("conjunto de usinas, id ONS CJU_..."); a da usina continua como hoje. O conjunto ``referencia`` é a série de
referência da usina: a Geração por usina ou, nas eólicas e solares em conjunto com série própria, a restrição com
detalhe (fase C); as restrições citam o pacote da variante do tipo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from src.coleta import registro
from src.comum.formatacao import fmt_data, fmt_int, fmt_lista, fmt_num, fmt_pct
from src.comum.logger import setup_logger
from src.comum.perfil import perfil_ativo
from src.analises.resultados import sem_evt
from src.comum.regras import (
    CONJUNTO_CADASTRO,
    CONJUNTO_CAPACIDADE,
    CONJUNTO_CMO,
    CONJUNTO_COMPOSICAO,
    CONJUNTO_CVU,
    CONJUNTO_DESPACHO,
    CONJUNTO_DISPONIBILIDADE,
    CONJUNTO_EVT,
    CONJUNTO_FATOR_CAPACIDADE,
    CONJUNTO_GERACAO,
    CONJUNTO_HIDROLOGIA,
    CONJUNTO_PROGRAMACAO_DIARIA,
    META_ALINHAMENTO_HIDROLOGIA_PCT,
    TOLERANCIA_REPRODUCAO_TAXAS_PP,
)
from src.conferencia.resultado import diferenca_absoluta
from src.relatorio.secoes_renovavel import pacote_variante, referencia_restricao

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
GERACAO = "geração"
MOTIVOS_DESPACHO = "motivos de despacho"
CVU_CMO = "CVU e CMO"
ESTIMADA = "geração estimada e marca de restrição"
RECURSO = "vento ou irradiância"


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
    "composicao": Conjunto("Composição dos conjuntos de usinas", "conjunto de usinas, id ONS {id_conjunto}",
                           CONJUNTO_COMPOSICAO),
    "capacidade": Conjunto("Capacidade de geração", "CEG {ceg}", CONJUNTO_CAPACIDADE),
    # Térmicas (fase B)
    "despacho": Conjunto("Geração térmica por motivo de despacho", "CEG {ceg}; códigos de planejamento {planejamento}",
                         CONJUNTO_DESPACHO),
    "cvu": Conjunto("CVU das usinas térmicas", "códigos de planejamento {planejamento}", CONJUNTO_CVU),
    "cmo": Conjunto("CMO semanal", "subsistema {subsistema}, agregado", CONJUNTO_CMO),
    # Eólicas e solares (fase C): as restrições na variante do tipo (pacote em ``catalogo_do_conjunto``)
    "fator_capacidade": Conjunto("Fator de capacidade", "id ONS {id_ons}", CONJUNTO_FATOR_CAPACIDADE),
    "restricao_detalhe": Conjunto("Restrição com detalhe (constrained-off)", "id ONS {id_ons}; CEG {ceg}", "variante"),
    "restricao_razao": Conjunto("Restrição com a razão (constrained-off)", "id ONS {id_ons}", "variante"),
    "projeto": Conjunto("parâmetros do projeto", ""),
}


def catalogo_do_conjunto(cid: str) -> str:
    """Id no catálogo do ONS; nas restrições, o pacote da variante do tipo da usina ativa (vazio nos demais tipos)."""
    catalogo = CONJUNTOS[cid].catalogo
    return pacote_variante(cid) if catalogo == "variante" else catalogo


def _resolver(cid: str) -> str:
    """``referencia``: a série de referência da usina ativa (Geração por usina ou restrição com detalhe);
    ``geracao_programacao``: a geração comparada com a programação, a Geração por usina do conjunto quando a programação é
    do conjunto e a referência é a restrição com detalhe da usina (T157)."""
    if cid == "geracao_programacao":
        if referencia_restricao() and registro.nivel_coletado(perfil_ativo(), "programacao") == "conjunto":
            return "geracao"
        cid = "referencia"
    if cid != "referencia":
        return cid
    return "restricao_detalhe" if referencia_restricao() else "geracao"


def identificador_da_usina(cid: str) -> str:
    """Identificador da usina no conjunto ``cid``, com os valores do perfil ativo."""
    p = perfil_ativo()
    i = p.identificacao
    planejamento = ", ".join(str(c.codigo) for c in getattr(i, "planejamento", ()) or ())
    return CONJUNTOS[cid].identificador.format(cod_usina=i.cod_usina, ceg=i.ceg, id_ons=i.id_ons,
                                               cod_programacao=i.cod_programacao, id_reservatorio=i.id_reservatorio,
                                               id_conjunto=getattr(i, "id_conjunto", "") or "",
                                               planejamento=planejamento,
                                               subsistema=getattr(p.usina, "subsistema", "") or "")


def identificador_com_nivel(res: Any, cid: str) -> Optional[str]:
    """Identificador do dado com o nível escrito, nas usinas sem EVT (decisão R15); None no caminho de hoje."""
    if not sem_evt(res):
        return None
    niveis = getattr(res, "niveis", {}) or {}
    if cid == "geracao" and referencia_restricao():  # fase C: a geração não é a série de referência
        nivel = registro.nivel_coletado(perfil_ativo(), "geracao")
        i = perfil_ativo().identificacao
        return f"conjunto de usinas, id ONS {i.id_conjunto}" if nivel == "conjunto" else f"id ONS {i.id_ons}"
    if cid in ("fator_capacidade", "restricao_razao") and cid in niveis:
        n = niveis[cid]
        return f"conjunto de usinas, id ONS {n['identificador']}" if n["nivel"] == "conjunto" else \
            f"id ONS {n['identificador']}"
    if cid == "geracao" and "geracao" in niveis:
        g = niveis["geracao"]
        partes = [f"id ONS {g['identificador_usina']}"] if g.get("identificador_usina") else []
        if g.get("identificador_conjunto"):
            partes.append(f"conjunto de usinas, id ONS {g['identificador_conjunto']}")
        return "; ".join(partes)
    if cid == "programacao" and "programacao" in niveis:
        n = niveis["programacao"]
        return f"conjunto de usinas, {n['identificador']}" if n["nivel"] == "conjunto" else n["identificador"]
    return None
INDICADORES = ("dispf_mensal", "dispf_anual", "teif_teip", "teif_teip_parametro")


@dataclass(frozen=True)
class Conferencia:
    """Conferência de um dado entre duas fontes, refeita pelo pipeline a cada execução."""

    dado: str
    base: str  # conjunto cuja presença permite a conferência
    texto: Callable[[Any], str]
    texto_curto: Callable[[Any], str]  # forma curta, com os mesmos números, para o resumo executivo


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


def _reproducao_taxas(res: Any) -> Optional[Tuple[Any, Any, Any]]:
    """Meses reproduzidos, meses comparados e diferença máxima (p.p.) da TEIFa e da TEIP; None sem conferência."""
    rr = res.ons.get("recalculo_resumo") or {}
    if "reproduzidos" in rr:  # contagem da Conferência, levada pelas Análises
        if not rr["meses"]:
            return None
        return rr["reproduzidos"], rr["meses"], rr["diferenca_maxima_pp"]
    recalculo = res.ons.get("recalculo_taxas")
    completos = recalculo.dropna(subset=["teifa_recalculada"]) if recalculo is not None else pd.DataFrame()
    if completos.empty:
        return None
    diferencas = completos[["diferenca_teifa_pp", "diferenca_teip_pp"]].abs()
    reproduzidos = int((diferenca_absoluta(diferencas) <= TOLERANCIA_REPRODUCAO_TAXAS_PP).all(axis=1).sum())
    return reproduzidos, len(completos), float(diferencas.max().max())


def _conf_teifa_teip(res: Any) -> str:
    reproducao = _reproducao_taxas(res)
    if reproducao is None:
        return "TEIFa e TEIP: conferência com Taxas TEIFa e TEIP não feita nesta execução"
    reproduzidos, meses, maxima = reproducao
    return (f"TEIFa e TEIP recalculadas conferidas com as publicadas em Taxas TEIFa e TEIP: {fmt_int(reproduzidos)} de "
            f"{fmt_int(meses)} meses reproduzidos (diferença máxima de {fmt_num(maxima, 3)} p.p.)")


def _divergencias_dispf(res: Any) -> int:
    divergencias = res.ons.get("divergencias")
    return 0 if divergencias is None else len(divergencias)


def _conf_dispf_horas(res: Any) -> str:
    n = _divergencias_dispf(res)
    texto = "DISPF conferido com as horas por estado operativo (Parâmetros das taxas TEIFa e TEIP): "
    return texto + (f"{fmt_int(n)} divergências (meses-unidade), listadas na aba ONS_DIVERGENCIAS" if n
                    else "sem divergência")


def _conf_cadastro(res: Any) -> str:
    divergencias = str(res.cadastro.get("divergencias") or "").strip()
    texto = "potência autorizada e estado conferidos com os parâmetros do projeto: "
    return texto + (f"divergências ({divergencias})" if divergencias else "sem divergência")


# Formas curtas, para o bloco "Sobre os dados" do resumo executivo: os mesmos resultados e números das longas


def _curto_horas(c: Dict[str, Any], base: str) -> str:
    texto = f"coincidente com {base} em {fmt_pct(c['pct_coincidentes'])} das horas"
    if c.get("divergentes"):
        texto += f", com {fmt_int(c['divergentes'])} divergências"
    return texto


def _curto_geracao(res: Any) -> str:
    return "geração " + _curto_horas(res.geracao_oficial["conferencia"], "Geração por usina")


def _curto_disponibilidade(res: Any) -> str:
    return "disponibilidade declarada " + _curto_horas(res.disponibilidade["conferencia"], "Disponibilidade por usina")


def _curto_vazoes(res: Any) -> str:
    a = res.hidrologia["alinhamento"].iloc[0]
    texto = (f"vazões turbinada e vertida coincidentes com Dados hidrológicos horários em "
             f"{fmt_pct(a['pct_coincidencia'])} das horas")
    if not bool(a["confirmado"]):
        texto += f", abaixo da meta de {fmt_num(META_ALINHAMENTO_HIDROLOGIA_PCT, 0)}%"
    return texto


def _curto_teifa_teip(res: Any) -> str:
    reproducao = _reproducao_taxas(res)
    if reproducao is None:
        return "TEIFa e TEIP: conferência não feita nesta execução"
    reproduzidos, meses, _ = reproducao
    return f"TEIFa e TEIP refeitas em {fmt_int(reproduzidos)} de {fmt_int(meses)} meses"


def _curto_dispf_horas(res: Any) -> str:
    n = _divergencias_dispf(res)
    return "DISPF e horas por estado operativo " + (f"com {fmt_int(n)} divergências (meses-unidade)" if n
                                                    else "sem divergência")


def _conferencia_termica(res: Any, cid: str) -> Optional[Dict[str, Any]]:
    c = ((getattr(res, "termica", None) or {}).get("conferencias") or {}).get(cid)
    return c if c and c.get("aplicavel") else None


def _conf_programacao_despacho(res: Any) -> str:
    c = _conferencia_termica(res, "programacao_despacho")
    if c is None:
        return "programação diária: conferência com o despacho não feita nesta execução"
    return ("programação diária conferida com o programado da Geração térmica por motivo de despacho (G3): "
            + _texto_horas(c, "CONF_G3_DIVERGENCIAS", "so_a"))


def _conf_verificada_despacho(res: Any) -> str:
    c = _conferencia_termica(res, "verificada_despacho")
    if c is None:
        return "geração verificada do despacho: conferência com Geração por usina não feita nesta execução"
    return ("geração verificada da Geração térmica por motivo de despacho conferida com Geração por usina (G4): "
            + _texto_horas(c, "CONF_G4_DIVERGENCIAS", "so_a"))


def _curto_programacao_despacho(res: Any) -> str:
    c = _conferencia_termica(res, "programacao_despacho")
    return ("programação diária: conferência com o despacho não feita nesta execução" if c is None
            else "programação diária " + _curto_horas(c, "o programado do despacho"))


def _curto_verificada_despacho(res: Any) -> str:
    c = _conferencia_termica(res, "verificada_despacho")
    return ("geração do despacho: conferência não feita nesta execução" if c is None
            else "geração verificada do despacho " + _curto_horas(c, "Geração por usina"))


def _conferencia_renovavel(res: Any, cid: str) -> Optional[Dict[str, Any]]:
    c = ((getattr(res, "renovavel", None) or {}).get("conferencias") or {}).get(cid)
    return c if c and c.get("aplicavel") else None


def _conf_geracao_fontes(res: Any) -> str:
    c = _conferencia_renovavel(res, "geracao_fontes")
    if c is None:
        return "geração da usina entre fontes: conferência não feita nesta execução"
    n = len(c["pares"])
    texto = (f"geração conferida entre as fontes, duas a duas e no mesmo nível (G1): {fmt_int(c['coincidentes'])} de "
             f"{fmt_int(c['comparados'])} horas coincidentes ({fmt_pct(c['coincidentes'] / c['comparados'] * 100)}) em "
             f"{fmt_int(n)} {'par' if n == 1 else 'pares'} de fontes, detalhados na aba CONF_G1_PARES")
    if c["divergentes"]:
        texto += f"; {fmt_int(c['divergentes'])} divergências, listadas na aba CONF_G1_DIVERGENCIAS"
    return texto


def _curto_geracao_fontes(res: Any) -> str:
    c = _conferencia_renovavel(res, "geracao_fontes")
    if c is None:
        return "geração entre fontes: conferência não feita nesta execução"
    texto = (f"geração coincidente entre as fontes em {fmt_pct(c['coincidentes'] / c['comparados'] * 100)} das horas "
             "comparadas")
    return texto + (f", com {fmt_int(c['divergentes'])} divergências" if c["divergentes"] else "")


def _conf_soma_conjunto(res: Any) -> str:
    c = _conferencia_renovavel(res, "soma_conjunto")
    if c is None:
        return "soma das usinas do conjunto: conferência não feita nesta execução"
    texto = ("soma das usinas do conjunto (Restrição com detalhe) conferida com a Geração por usina do conjunto (G2): "
             + _texto_horas(c, "CONF_G2_DIVERGENCIAS", "so_a"))
    if c.get("horas_incompletas"):
        texto += f"; {fmt_int(c['horas_incompletas'])} horas sem todas as usinas, fora da soma"
    return texto


def _curto_soma_conjunto(res: Any) -> str:
    c = _conferencia_renovavel(res, "soma_conjunto")
    return ("soma das usinas do conjunto: conferência não feita nesta execução" if c is None
            else "soma das usinas do conjunto " + _curto_horas(c, "a Geração por usina do conjunto"))


def _conf_programacao_renovaveis(res: Any) -> str:
    c = _conferencia_renovavel(res, "programacao_renovaveis")
    if c is None:
        return "programação diária: conferência com o Fator de capacidade não feita nesta execução"
    return ("programação diária conferida com o programado do Fator de capacidade (G5): "
            + _texto_horas(c, "CONF_G5_DIVERGENCIAS", "so_a"))


def _curto_programacao_renovaveis(res: Any) -> str:
    c = _conferencia_renovavel(res, "programacao_renovaveis")
    return ("programação diária: conferência com o Fator de capacidade não feita nesta execução" if c is None
            else "programação diária " + _curto_horas(c, "o programado do Fator de capacidade"))


def _curto_cadastro(res: Any) -> str:
    divergencias = str(res.cadastro.get("divergencias") or "").strip()
    return "cadastro " + (f"com divergências ({divergencias})" if divergencias else "sem divergência")


CONFERENCIAS: Dict[str, Conferencia] = {
    "geracao": Conferencia("geração", "geracao", _conf_geracao, _curto_geracao),
    "disponibilidade": Conferencia("disponibilidade declarada", "disponibilidade", _conf_disponibilidade,
                                   _curto_disponibilidade),
    "vazoes": Conferencia("vazões turbinada e vertida", "hidrologia", _conf_vazoes, _curto_vazoes),
    "teifa_teip": Conferencia("TEIFa e TEIP", "teif_teip", _conf_teifa_teip, _curto_teifa_teip),
    "dispf_horas": Conferencia("DISPF", "teif_teip_parametro", _conf_dispf_horas, _curto_dispf_horas),
    "cadastro": Conferencia("potência autorizada e estado", "cadastro", _conf_cadastro, _curto_cadastro),
    "programacao_despacho": Conferencia("programação diária", "despacho", _conf_programacao_despacho,
                                        _curto_programacao_despacho),
    "verificada_despacho": Conferencia("geração verificada do despacho", "despacho", _conf_verificada_despacho,
                                       _curto_verificada_despacho),
    # Eólicas e solares (fase C)
    "geracao_fontes": Conferencia("geração da usina entre fontes", "geracao", _conf_geracao_fontes,
                                  _curto_geracao_fontes),
    "soma_conjunto": Conferencia("soma das usinas do conjunto", "restricao_detalhe", _conf_soma_conjunto,
                                 _curto_soma_conjunto),
    "programacao_renovaveis": Conferencia("programação diária", "fator_capacidade", _conf_programacao_renovaveis,
                                          _curto_programacao_renovaveis),
}


# ---------------------------------------------------------------------------
# Mapa das figuras, tabelas e blocos (PDF e Markdown)
# ---------------------------------------------------------------------------

CONFERENCIAS_RENOVAVEIS: Tuple[str, ...] = ("geracao_fontes", "soma_conjunto", "programacao_renovaveis")


def conferencia_feita(res: Any, cid: str) -> bool:
    """A conferência tem base nesta execução: o conjunto da base carregado e, nas das eólicas e solares, aplicável à
    usina (a não aplicável fica nas notas, com o motivo; decisão R13)."""
    if CONFERENCIAS[cid].base not in _carregados(res):
        return False
    return cid not in CONFERENCIAS_RENOVAVEIS or _conferencia_renovavel(res, cid) is not None


CONFERENCIAS_SEM_EVT: Tuple[str, ...] = ("teifa_teip", "dispf_horas", "cadastro", "programacao_despacho",
                                         "verificada_despacho",  # G3 e G4 só com o despacho (fase B)
                                         "geracao_fontes", "soma_conjunto", "programacao_renovaveis")  # fase C
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
    # Usinas sem EVT (spec 006, decisões R14 e R15): a série de referência (Geração por usina) no lugar da EVT
    "bloco_identificacao_comum": _e(["cadastro", "referencia", "capacidade", "despacho"]),
    "tab_capa_indicadores_comum": _e(["referencia", "disponibilidade", "dispf_mensal", "teif_teip", "restricao_detalhe"],
                                     ["dispf_horas", "teifa_teip"], [GERACAO], calculado=True),
    "tab_fonte_cobertura": _e(["referencia"]),
    "tab_niveis": _e(["referencia", "geracao", "programacao", "disponibilidade", "dispf_mensal", "cadastro",
                      "composicao", "fator_capacidade", "restricao_detalhe", "restricao_razao"]),
    "tab_trechos": _e(["referencia", "composicao"], calculado=True),
    "tab_anuais_comum": _e(["referencia", "disponibilidade", "restricao_detalhe", "projeto"], ["soma_conjunto"],
                           [GERACAO], calculado=True),
    "tab_disponibilidade_anual_comum": _e(["disponibilidade", "referencia"], (), [SINCRONIZADA, GERACAO],
                                          calculado=True),
    "tab_eventos_indisponibilidade_comum": _e(["disponibilidade", "referencia"], calculado=True),
    "tab_ons_disp_anual_comum": _e(["disponibilidade", "dispf_mensal"], ["dispf_horas"], calculado=True),
    "tab_programacao_mensal_comum": _e(["programacao", "geracao_programacao"], ["programacao_renovaveis"],
                                       [PROGRAMACAO, GERACAO], calculado=True),
    "tab_programacao_eventos_comum": _e(["programacao", "geracao_programacao"], ["programacao_renovaveis"],
                                        [PROGRAMACAO, GERACAO], calculado=True),
    "tab_sinalizacoes": _e(["referencia", "disponibilidade"], calculado=True),
    "tab_ausencias": _e(["referencia"]),
    "tab_omitidos": _e(["projeto"], calculado=True),
    "tab_nao_aplicaveis": _e(["projeto"], calculado=True),
    "tab_parametros_comum": _e(["projeto"]),
    "serie_temporal_comum": _e(["referencia", "disponibilidade"], (), [GERACAO], calculado=True),
    "geracao_mensal": _e(["referencia"], (), [GERACAO], calculado=True),
    "sazonalidade": _e(["referencia"], (), [GERACAO], calculado=True),
    "perfil_horario_comum": _e(["referencia"], (), [GERACAO], calculado=True),
    "disponibilidade_comum": _e(["disponibilidade", "referencia"], (), [SINCRONIZADA], calculado=True),
    # Térmicas (fase B)
    "tab_motivos_termica": _e(["despacho"], ["verificada_despacho"], [MOTIVOS_DESPACHO], calculado=True),
    "tab_despacho_anual": _e(["despacho"], ["programacao_despacho", "verificada_despacho"], calculado=True),
    "tab_atendimento_anual": _e(["despacho"], ["programacao_despacho", "verificada_despacho"], calculado=True),
    "tab_maiores_desvios": _e(["despacho"], ["verificada_despacho"]),
    "tab_disponivel_anual": _e(["disponibilidade", "despacho"], ["verificada_despacho"], calculado=True),
    "tab_cvu_cmo": _e(["cvu", "cmo", "despacho"], (), [CVU_CMO], calculado=True),
    "despacho_motivo_mensal": _e(["despacho"], ["verificada_despacho"], [MOTIVOS_DESPACHO], calculado=True),
    "inflexibilidade_mensal": _e(["despacho"], (), [MOTIVOS_DESPACHO], calculado=True),
    "desvios_despacho": _e(["despacho"], ["programacao_despacho", "verificada_despacho"], calculado=True),
    "cvu_cmo": _e(["cvu", "cmo"], (), [CVU_CMO], calculado=True),
    # Eólicas e solares (fase C)
    "tab_fc_anual": _e(["fator_capacidade", "referencia", "projeto"], ["geracao_fontes", "programacao_renovaveis"],
                       calculado=True),
    "tab_corte_anual": _e(["restricao_detalhe"], ["geracao_fontes", "soma_conjunto"], [ESTIMADA], calculado=True),
    "tab_corte_razao": _e(["restricao_detalhe", "restricao_razao"], ["geracao_fontes"], [ESTIMADA], calculado=True),
    "tab_recurso_faixas": _e(["restricao_detalhe"], ["geracao_fontes"], [RECURSO], calculado=True),
    "tab_desvios_programacao_renovavel": _e(["programacao", "geracao_programacao"], ["programacao_renovaveis"]),
    "fc_mensal": _e(["fator_capacidade", "referencia", "projeto"], ["geracao_fontes", "programacao_renovaveis"],
                    calculado=True),
    "corte_razao_mensal": _e(["restricao_detalhe", "restricao_razao"], ["geracao_fontes"], [ESTIMADA],
                             calculado=True),
    "recurso_geracao": _e(["restricao_detalhe"], ["geracao_fontes"], [RECURSO], calculado=True),
    "desvio_programacao": _e(["programacao", "geracao_programacao"], ["programacao_renovaveis"], calculado=True),
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
    # Usinas sem EVT (spec 006)
    "BASE_ANUAL": MAPA_FONTES["tab_anuais_comum"],
    "BASE_MENSAL": MAPA_FONTES["geracao_mensal"],
    "BASE_MES_DO_ANO": MAPA_FONTES["sazonalidade"],
    "BASE_HORA_DO_DIA": MAPA_FONTES["perfil_horario_comum"],
    "BASE_SINALIZACOES": MAPA_FONTES["tab_sinalizacoes"],
    "TRECHOS": MAPA_FONTES["tab_trechos"],
    "OMITIDOS": MAPA_FONTES["tab_omitidos"],
    "CONF_NAO_APLICAVEIS": MAPA_FONTES["tab_nao_aplicaveis"],
    "DISP_EVENTOS_INDISP_TOTAL": MAPA_FONTES["tab_eventos_indisponibilidade_comum"],
    # Térmicas (fase B)
    "TERM_MOTIVOS_ANUAL": MAPA_FONTES["tab_motivos_termica"],
    "TERM_MOTIVOS_MENSAL": MAPA_FONTES["despacho_motivo_mensal"],
    "TERM_INFLEXIBILIDADE": MAPA_FONTES["inflexibilidade_mensal"],
    "TERM_ATENDIMENTO_ANUAL": MAPA_FONTES["tab_atendimento_anual"],
    "TERM_ATENDIMENTO_MENSAL": MAPA_FONTES["desvios_despacho"],
    "TERM_MAIORES_DESVIOS": MAPA_FONTES["tab_maiores_desvios"],
    "TERM_DISP_SEM_DESPACHO": MAPA_FONTES["tab_disponivel_anual"],
    "TERM_CVU_CMO_SEMANAL": MAPA_FONTES["cvu_cmo"],
    "TERM_CVU_CMO_RESUMO": MAPA_FONTES["tab_cvu_cmo"],
    "CONF_G3_MENSAL": _e(["programacao", "despacho"], ["programacao_despacho"]),
    "CONF_G3_DIVERGENCIAS": _e(["programacao", "despacho"], ["programacao_despacho"]),
    "CONF_G4_MENSAL": _e(["despacho", "geracao"], ["verificada_despacho"]),
    "CONF_G4_DIVERGENCIAS": _e(["despacho", "geracao"], ["verificada_despacho"]),
    # Eólicas e solares (fase C)
    "REN_FC_ANUAL": MAPA_FONTES["tab_fc_anual"],
    "REN_FC_MENSAL": MAPA_FONTES["fc_mensal"],
    "REN_CORTE_ANUAL": MAPA_FONTES["tab_corte_anual"],
    "REN_CORTE_MENSAL": MAPA_FONTES["corte_razao_mensal"],
    "REN_CORTE_RAZAO": MAPA_FONTES["tab_corte_razao"],
    "REN_RECURSO_FAIXAS": MAPA_FONTES["tab_recurso_faixas"],
    "REN_DESVIOS_PROGRAMACAO": MAPA_FONTES["tab_desvios_programacao_renovavel"],
    "CONF_G1_PARES": _e(["geracao", "fator_capacidade", "restricao_detalhe", "restricao_razao"], ["geracao_fontes"]),
    "CONF_G1_MENSAL": _e(["geracao", "fator_capacidade", "restricao_detalhe", "restricao_razao"], ["geracao_fontes"]),
    "CONF_G1_DIVERGENCIAS": _e(["geracao", "fator_capacidade", "restricao_detalhe", "restricao_razao"],
                               ["geracao_fontes"]),
    "CONF_G2_MENSAL": _e(["restricao_detalhe", "geracao"], ["soma_conjunto"]),
    "CONF_G2_DIVERGENCIAS": _e(["restricao_detalhe", "geracao"], ["soma_conjunto"]),
    "CONF_G5_MENSAL": _e(["programacao", "fator_capacidade"], ["programacao_renovaveis"]),
    "CONF_G5_DIVERGENCIAS": _e(["programacao", "fator_capacidade"], ["programacao_renovaveis"]),
}
# Abas das usinas sem EVT com o mesmo nome de uma aba de hoje, mas sem a EVT na origem
_ABAS_SEM_EVT: Dict[str, Entrada] = {
    "PROG_RESUMO_MENSAL": MAPA_FONTES["tab_programacao_mensal_comum"],
    "PROG_EVENTOS_DESVIO": MAPA_FONTES["tab_programacao_eventos_comum"],
    "DISP_MENSAL": MAPA_FONTES["disponibilidade_comum"],
    "DISP_ANUAL": MAPA_FONTES["tab_disponibilidade_anual_comum"],
    "ONS_DISP_ANUAL_USINA": MAPA_FONTES["tab_ons_disp_anual_comum"],
    "GER_AUSENCIAS": MAPA_FONTES["tab_ausencias"],  # as horas ausentes da série de referência
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


def _carregados_sem_evt(res: Any) -> List[str]:
    """Usinas sem EVT: a série de referência sempre entra; os demais, quando entraram nas seções comuns."""
    carregados = ["geracao"]
    if res.ons:
        carregados += list(INDICADORES)
    if res.comum.get("programacao_coletada"):
        carregados.append("programacao")
    if res.comum.get("disponibilidade"):
        carregados.append("disponibilidade")
    if res.cadastro:
        carregados.append("cadastro")
    if getattr(perfil_ativo().identificacao, "id_conjunto", None):
        carregados.append("composicao")
    if res.comum.get("agentes"):
        carregados.append("capacidade")
    t = getattr(res, "termica", None) or {}
    if t:
        carregados.append("despacho")
        if t.get("cvu_coletado"):
            carregados.append("cvu")
        if t.get("cmo_coletado"):
            carregados.append("cmo")
    for chave in ("fator_capacidade", "restricao_detalhe", "restricao_razao"):  # fase C
        if registro.nivel_coletado(perfil_ativo(), chave):
            carregados.append(chave)
    return carregados


def conjuntos_carregados(res: Any) -> List[str]:
    """Conjuntos do ONS cujos dados entraram nesta análise; a base de EVT sempre entra (N do rodapé)."""
    if sem_evt(res):
        return _carregados_sem_evt(res)
    carregados = ["evt"]
    if res.ons:
        carregados += list(INDICADORES)
    for cid, campo in (("programacao", "programacao"), ("disponibilidade", "disponibilidade"),
                       ("hidrologia", "hidrologia"), ("geracao", "geracao_oficial"), ("cadastro", "cadastro")):
        if getattr(res, campo):
            carregados.append(cid)
    return carregados


def datas_obtencao(res: Any) -> Dict[str, str]:
    """Data (UTC) de obtenção mais recente de cada conjunto, gravada pela Coleta; vazia se não houver registro."""
    registradas = getattr(res, "datas_obtencao", None) or {}
    datas: Dict[str, str] = {}
    for cid in CONJUNTOS:
        catalogo = catalogo_do_conjunto(cid)
        if catalogo:
            datas[cid] = str((registradas.get(catalogo) or {}).get("obtencao_mais_recente") or "")
    return datas


def origem_dos_dados(res: Any) -> Dict[str, Any]:
    """Conteúdo de ``res.fontes``: datas de obtenção e conjuntos carregados."""
    return {"obtencao": datas_obtencao(res), "carregados": conjuntos_carregados(res)}


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
    return f"{conjunto.nome} ({identificador_com_nivel(res, cid) or identificador_da_usina(cid)}), {quando}"


def texto_conferencia(res: Any, cid: str) -> str:
    """Resultado da conferência nesta execução, ou o aviso de que não foi feita (FR-026)."""
    conferencia = CONFERENCIAS[cid]
    if conferencia.base not in _carregados(res):
        return f"{conferencia.dado}: conferência com {CONJUNTOS[conferencia.base].nome} não feita nesta execução"
    return conferencia.texto(res)


def texto_conferencia_curto(res: Any, cid: str) -> str:
    """Forma curta do resultado da conferência, para o resumo executivo, ou o aviso de que não foi feita."""
    conferencia = CONFERENCIAS[cid]
    if conferencia.base not in _carregados(res):
        return f"{conferencia.dado}: conferência não feita nesta execução"
    return conferencia.texto_curto(res)


def fontes_resumo(res: Any) -> List[str]:
    """Conjuntos carregados nesta execução, agrupados por identificador da usina e data de obtenção (resumo executivo).

    Cada texto: "<nomes> (<identificador>), obtido(s) em dd/mm/aaaa", na ordem em que os conjuntos são carregados.
    """
    obtencao = (getattr(res, "fontes", None) or {}).get("obtencao") or {}
    grupos: Dict[Tuple[str, str], List[str]] = {}
    for cid in _carregados(res):
        if cid not in CONJUNTOS or not catalogo_do_conjunto(cid):
            continue
        data = str(obtencao.get(cid) or "")
        grupos.setdefault((identificador_da_usina(cid), fmt_data(data) if data else ""), []).append(CONJUNTOS[cid].nome)
    textos = []
    for (identificador, data), nomes in grupos.items():
        quando = f"{'obtidos' if len(nomes) > 1 else 'obtido'} em {data}" if data else SEM_REGISTRO
        textos.append(f"{fmt_lista(nomes)} ({identificador}), {quando}")
    return textos


def _textos_entrada(res: Any, entrada: Entrada) -> Tuple[List[str], List[str]]:
    carregados = _carregados(res)
    citados = list(dict.fromkeys(_resolver(c) for c in entrada.conjuntos))
    conjuntos = citados if entrada.todos else (
        [c for c in citados if c == "projeto" or c in carregados] or citados)
    conferencias = list(entrada.conferencias)
    if sem_evt(res):  # sem a base, a conferência não se aplica e fica nas notas, não "não feita" (decisão R13)
        conferencias = [c for c in conferencias if conferencia_feita(res, c)]
    else:  # no caminho de hoje, as conferências das eólicas e solares nunca entram
        conferencias = [c for c in conferencias if c not in CONFERENCIAS_RENOVAVEIS]
    return [texto_conjunto(res, c) for c in conjuntos], [texto_conferencia(res, c) for c in conferencias]


def _sem_outra_fonte(res: Any, entrada: Entrada) -> List[str]:
    """Dados sem outra fonte conferida; a programação diária sai quando a G5 a conferiu nesta execução (eólicas e
    solares)."""
    conferidos = {PROGRAMACAO} if ("programacao_renovaveis" in entrada.conferencias
                                   and conferencia_feita(res, "programacao_renovaveis")) else set()
    return [d for d in entrada.sem_outra_fonte if d not in conferidos]


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
    sem_outra = _sem_outra_fonte(res, entrada)
    if sem_outra:
        partes.append(f"Sem outra fonte para conferir: {', '.join(sem_outra)}.")
    return " ".join(partes)


# ---------------------------------------------------------------------------
# Aba FONTES
# ---------------------------------------------------------------------------


def _entrada_aba(res: Any, aba: str) -> Optional[Entrada]:
    if aba in ("CONSTATACOES", "CONCLUSAO"):
        carregados = _carregados(res)
        # nas usinas sem EVT, só as conferências que não dependem da EVT (spec 006, decisão R13)
        candidatas = CONFERENCIAS_SEM_EVT if sem_evt(res) else tuple(CONFERENCIAS)
        return _e(carregados, [c for c in candidatas if conferencia_feita(res, c)], calculado=True)
    if aba == "PARAMETROS":
        return _e(["projeto", *_carregados(res)])
    if aba == "DICIONARIOS":  # só os conjuntos do tipo e da cobertura da usina (spec 006, decisão R8)
        da_usina = registro.pacotes(registro.conjuntos_da_usina(perfil_ativo()), registro.tipo_da_usina(perfil_ativo()))
        return _e([c for c in CONJUNTOS if catalogo_do_conjunto(c) and catalogo_do_conjunto(c) in da_usina],
                  todos=True)
    if sem_evt(res) and aba in _ABAS_SEM_EVT:
        return _ABAS_SEM_EVT[aba]
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
                       ", ".join(_sem_outra_fonte(res, entrada)) or "—", "sim" if entrada.calculado else "não"])
    return pd.DataFrame(linhas, columns=COLUNAS_FONTES)


__all__ = [
    "CONFERENCIAS", "CONJUNTOS", "MAPA_FONTES", "PREFIXO_CALCULADO", "PREFIXO_FONTE", "conjuntos_carregados",
    "datas_obtencao", "fontes_resumo", "identificador_da_usina", "legenda_fonte", "origem_dos_dados",
    "tabela_fontes_abas", "texto_conferencia", "texto_conferencia_curto", "texto_conjunto",
]
