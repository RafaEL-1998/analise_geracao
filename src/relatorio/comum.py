"""Conteúdo do relatório das usinas sem EVT, comum ao PDF e ao Markdown (spec da Geração do relatório, FR-041;
plano, D15 e D16; data-model, seção 2.9).

Capa, linhas das tabelas, textos, legendas descritivas, notas e os blocos de cada seção do caminho sem EVT, todos
montados só a partir de ``ResultadosAnalise`` e do perfil. As hidrelétricas com EVT continuam com
``src/relatorio/conteudo.py``, sem mudança (D17).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd

from src.analises.comum import _rotulo_ano
from src.analises.comum_tipos import NOME_NIVEL
from src.analises.resultados import ResultadosAnalise
from src.comum.formatacao import (
    fmt_data,
    fmt_data_hora,
    fmt_int,
    fmt_lista,
    fmt_mes_ano,
    fmt_num,
    fmt_pct,
    fmt_pp,
    plural,
)
from src.comum.perfil import perfil_ativo
from src.comum.regras import (
    DURACAO_MINIMA_EVENTO_RELATORIO_H,
    LIMIAR_DESVIO_PROGRAMACAO_MW,
    LIMIAR_GERACAO_PARADA_MW,
    LIMIAR_INDISPONIBILIDADE_TOTAL_MW,
    LIMIAR_SINCRONIZADA_MW,
    NUMERO_EVENTOS_RELATORIO,
    ONS_PORTAL_DATASET_URL,
    CONJUNTO_CAPACIDADE,
    CONJUNTO_CMO,
    CONJUNTO_CVU,
    CONJUNTO_DESPACHO,
    CONJUNTO_FATOR_CAPACIDADE,
    CONJUNTO_GERACAO,
    CONJUNTO_HIDROLOGIA,
    LIMIAR_DESVIO_DESPACHO_MW,
    PERIODO_MINIMO_SAZONALIDADE_MESES,
    TIPOS_COM_FATOR_CAPACIDADE,
    TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW,
)
from src.coleta import registro
from src.conferencia.aplicabilidade import CATALOGO_CONFERENCIAS
from src.relatorio.conteudo import (
    linhas_tabela_hidrologia_anual,
    nota_conclusao_catalogo,
    linhas_tabela_ons_decomposicao,
    linhas_tabela_ons_divergencias,
    linhas_tabela_ons_horas,
    linhas_tabela_ons_ug_anual,
    titulo_capa_relatorio,
)
from src.relatorio import secoes_conjunto
from src.relatorio.secoes_renovavel import SECOES_RENOVAVEL, pacote_variante, referencia_restricao

ROTULO_NIVEL = {"usina": "usina", "conjunto": "conjunto", "agregado": "agregado"}
COLUNA_CORTE = "Energia cortada (MWh, % est.)"  # o indicador de perda das eólicas e solares (D27)
DESCRICAO_CONFERENCIAS = {c.id: c.descricao for c in CATALOGO_CONFERENCIAS}


# ---------------------------------------------------------------------------
# Blocos das seções (renderizados pelo PDF e pelo Markdown)
# ---------------------------------------------------------------------------


@dataclass
class Bloco:
    """Bloco de uma seção: ``chave_valor``, ``tabela``, ``figura``, ``texto``, ``subtitulo``, ``notas`` ou
    ``sem_linhas``."""

    tipo: str
    chave: str = ""
    cabecalho: List[str] = field(default_factory=list)
    linhas: List[List[str]] = field(default_factory=list)
    larguras: Sequence[float] = ()  # proporções das colunas no PDF
    numericas: Sequence[int] = ()
    intro: str = ""
    textos: List[str] = field(default_factory=list)
    pares: List[Tuple[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Níveis (D16)
# ---------------------------------------------------------------------------


def _g(res: ResultadosAnalise) -> Dict[str, str]:
    return res.niveis.get("geracao", {})


def niveis_da_base(res: ResultadosAnalise) -> List[str]:
    return sorted((res.comum.get("cobertura") or {}).get("niveis", {}))


def com_conjunto(res: ResultadosAnalise) -> bool:
    """Algum número do relatório é do conjunto (o parágrafo de granularidade entra só então)."""
    return "conjunto" in niveis_da_base(res) or any(n.get("nivel") == "conjunto" for n in res.niveis.values())


def nome_conjunto(res: ResultadosAnalise) -> str:
    g = _g(res)
    return g.get("nome") or g.get("identificador_conjunto") or ""


def pacote_referencia() -> str:
    """Pacote do ONS da série de referência: a Geração por usina ou, na eólica ou solar com série própria, a
    restrição com detalhe."""
    return pacote_variante("restricao_detalhe") if referencia_restricao() else CONJUNTO_GERACAO


def serie_referencia_texto(res: ResultadosAnalise) -> str:
    """"Geração por usina (id ONS X)" ou "Geração por usina (conjunto de usinas, id ONS CJU_...)"; na eólica ou solar
    com série própria, "Restrição com detalhe (id ONS X; CEG Y)"."""
    if referencia_restricao():
        ident = perfil_ativo().identificacao
        return f"Restrição com detalhe (id ONS {ident.id_ons}; CEG {ident.ceg})"
    g = _g(res)
    partes = []
    if g.get("identificador_usina"):
        partes.append(f"id ONS {g['identificador_usina']}")
    if g.get("identificador_conjunto"):
        partes.append(f"conjunto de usinas, id ONS {g['identificador_conjunto']}")
    return f"Geração por usina ({'; '.join(partes)})"


def _nivel_texto(nivel: str) -> str:
    return ROTULO_NIVEL.get(nivel, nivel)


# ---------------------------------------------------------------------------
# Capa
# ---------------------------------------------------------------------------


def titulo_relatorio() -> str:
    """O mesmo título da capa das hidrelétricas com EVT, que não cita a EVT (relatório aprovado em 19/10/2026)."""
    return titulo_capa_relatorio()


def subtitulo_capa(res: ResultadosAnalise, data_geracao: Optional[datetime]) -> str:
    c = res.cobertura
    return (f"Análise dos dados abertos do ONS · {fmt_data_hora(c['inicio'])} a {fmt_data_hora(c['fim'])} · "
            f"{fmt_int(c['horas_observadas'])} registros horários da série de referência, "
            f"{serie_referencia_texto(res)} · Gerado em {(data_geracao or datetime.now()).strftime('%d/%m/%Y %H:%M')}")


def cabecalho_paginas(res: ResultadosAnalise) -> str:
    c = res.cobertura
    return f"{perfil_ativo().usina.nome} — desempenho operacional (dados ONS) · {fmt_data(c['inicio'])} a {fmt_data(c['fim'])}"


def pares_identificacao(res: ResultadosAnalise) -> List[Tuple[str, str]]:
    """Bloco "Identificação nos dados do ONS": identificadores do perfil, tipo e modalidade e o conjunto."""
    p = perfil_ativo()
    ident = p.identificacao
    pares = [("Tipo · modalidade", f"{res.tipo} · {res.modalidade}"), ("CEG", str(ident.ceg))]
    if ident.id_ons:
        pares.append(("id ONS", str(ident.id_ons)))
    if getattr(ident, "id_conjunto", None):
        nome = f" ({nome_conjunto(res)})" if _g(res).get("nome") else ""
        pares.append(("Conjunto de usinas", f"{ident.id_conjunto}{nome}"))
    codigos = getattr(ident, "codigos_programacao", ()) or ()
    if codigos:
        pares.append(("Programação diária", "; ".join(codigos)))
    pares.append(("Estado", str(p.usina.estado)))
    if getattr(p.usina, "subsistema", None) and getattr(res, "termica", None):
        pares.append(("Subsistema", str(p.usina.subsistema)))
    if getattr(ident, "planejamento", None) and getattr(res, "termica", None):
        from src.relatorio.secoes_termica import codigos_texto

        pares.append(("Códigos de planejamento", codigos_texto(res)))
    agentes = texto_agentes(res)
    if agentes:
        pares.append(("Agente atual", agentes))
    return pares


def texto_agentes(res: ResultadosAnalise) -> str:
    """Agente atual das unidades, como a Capacidade de geração do ONS o traz hoje (sem o histórico dos agentes):
    "A (proprietário e operador)" ou "A (proprietário); B (operador)"; vazio sem a ficha."""
    a = res.comum.get("agentes") or {}
    proprietarios, operadores = a.get("proprietario", []), a.get("operador", [])
    if not proprietarios and not operadores:
        return ""
    if proprietarios == operadores:
        return f"{fmt_lista(proprietarios)} (proprietário e operador)"
    partes = []
    if proprietarios:
        partes.append(f"{fmt_lista(proprietarios)} (proprietário)")
    if operadores:
        partes.append(f"{fmt_lista(operadores)} (operador)")
    return "; ".join(partes)


def pares_parametros() -> List[Tuple[str, str]]:
    """Bloco "Parâmetros técnicos da usina": os parâmetros do tipo (data-model da Coleta de dados, seção 5.1), sem os
    hidráulicos."""
    pr = perfil_ativo().parametros
    unidades = perfil_ativo().potencias_das_unidades_mw if pr.potencias_unidades_mw or pr.potencia_unitaria_mw else ()
    if unidades and len(set(unidades)) == 1:
        composicao = f" ({pr.unidades_geradoras} × {fmt_num(unidades[0], 1)} MW)"
    elif unidades:
        composicao = f" ({pr.unidades_geradoras} unidades: {fmt_lista(fmt_num(u, 1) for u in unidades)} MW)"
    else:
        composicao = f" ({pr.unidades_geradoras} unidades)"
    pares = [("Potência instalada", f"{fmt_num(pr.potencia_instalada_mw, 1)} MW{composicao}")]
    if pr.combustivel:
        pares.append(("Combustível", str(pr.combustivel)))
    if pr.garantia_fisica_mwmed is not None:
        pares.append(("Garantia física", f"{fmt_num(pr.garantia_fisica_mwmed, 1)} MWmed"))
    if pr.ip_referencia is not None and pr.teif_referencia is not None:
        pares.append(("IP / TEIF de referência", f"{fmt_pct(pr.ip_referencia * 100, 3)} / "
                                                 f"{fmt_pct(pr.teif_referencia * 100, 3)}"))
    pares.append(("Início da operação comercial", str(perfil_ativo().usina.inicio_operacao_comercial)))
    return pares


def _do(res: ResultadosAnalise, nivel: str) -> str:
    return f" do conjunto {nome_conjunto(res)}" if nivel == "conjunto" else ""


def indicadores_capa(res: ResultadosAnalise) -> Tuple[List[Tuple[str, str, str]], str]:
    """Indicadores da capa (data-model, seção 2.9.1): geração média, fator de capacidade ou horas com geração até 1 MW,
    disponibilidade média e DISPF/TEIFa, quando há; os do conjunto identificados como tal."""
    anuais = res.comum["anuais"]
    tiles: List[Tuple[str, str, str]] = []
    for nivel, g in anuais.groupby("nivel", sort=True):
        horas = int(g["horas_com_valor"].sum())
        media = float(g["energia_mwh"].sum()) / horas if horas else math.nan
        tiles.append((f"Geração média{_do(res, nivel)}", f"{fmt_num(media, 1)} MWmed",
                      f"{fmt_num(g['energia_mwh'].sum() / 1000, 1)} GWh em {fmt_int(horas)} horas com valor"))
        if res.tipo in TIPOS_COM_FATOR_CAPACIDADE and nivel == "usina":
            pinst = perfil_ativo().parametros.potencia_instalada_mw
            tiles.append(("Fator de capacidade", fmt_pct(media / pinst * 100.0), "geração média ÷ potência instalada"))
            corte = ((getattr(res, "renovavel", None) or {}).get("restricao") or {}).get("resumo")
            if corte:  # eólicas e solares (data-model, seção 2.9.1)
                tiles.append(("Energia cortada", fmt_pct(corte["pct_estimada"]),
                              f"{fmt_num(corte['energia_cortada_mwh'], 0)} MWh por restrição de operação, da energia "
                              "estimada nas semi-horas com a marca"))
        elif getattr(res, "termica", None) and nivel == "usina":  # térmicas com o despacho (data-model, seção 2.9.1)
            t = res.termica
            tiles.append(("Horas com despacho", fmt_pct(t["horas_com_despacho"] / t["periodo"]["horas"] * 100.0
                                                        if t["periodo"]["horas"] else math.nan),
                          f"{fmt_int(t['horas_com_despacho'])} de {fmt_int(t['periodo']['horas'])} horas do despacho com "
                          f"geração programada acima de {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW"))
        else:
            paradas = int(g["horas_paradas"].sum())
            tiles.append((f"Horas com geração até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW{_do(res, nivel)}",
                          fmt_pct(paradas / horas * 100.0 if horas else math.nan),
                          f"{fmt_int(paradas)} de {fmt_int(horas)} horas com valor"))
    d = res.comum.get("disponibilidade")
    if d:
        r = d["resumo"]
        tiles.append(("Disponibilidade operacional média", fmt_pct(r["disponibilidade_relativa_pct"]),
                      f"da potência instalada ({fmt_num(r['disp_operacional_media_mw'], 1)} MW), nas "
                      f"{fmt_int(r['horas'])} horas com o dado"))
    p, t = res.ons.get("disp_periodo"), res.ons.get("taxa_ultima")
    if p:
        tiles.append(("Disponibilidade apurada pelo ONS (DISPF)", fmt_pct(p["dispf_pct"]),
                      f"média das unidades; TEIFa {fmt_pct(t['teifa_pct'], 2)} em {fmt_mes_ano(t['mes'])}" if t
                      else "média das unidades"))
    nota = ("Indicadores calculados a partir da série de referência e da disponibilidade publicadas pelo ONS; não "
            "substituem os índices regulatórios. ")
    if "conjunto" in niveis_da_base(res):
        nota += ("Os números do conjunto de usinas são da soma das usinas do conjunto, como o ONS publica, e não são "
                 "divididos entre elas. ")
    return tiles[:4], nota + "Ver notas metodológicas."


# ---------------------------------------------------------------------------
# Fonte e cobertura dos dados
# ---------------------------------------------------------------------------


def pares_cobertura(res: ResultadosAnalise) -> List[Tuple[str, str]]:
    c = res.cobertura
    q = res.comum["qualidade"]
    aus = q["ausencias"]
    pares = [
        ("Série de referência", f"{serie_referencia_texto(res)} — Portal de Dados Abertos do ONS "
                                f"({ONS_PORTAL_DATASET_URL}{pacote_referencia()})"),
        ("Período", f"{fmt_data_hora(c['inicio'])} a {fmt_data_hora(c['fim'])}"),
        ("Registros", f"{fmt_int(c['horas_observadas'])} de {fmt_int(c['horas_esperadas'])} horas do período; "
                      f"{fmt_int(c['horas_ausentes'])} horas ausentes em {fmt_int(len(aus))} "
                      f"{plural(len(aus), 'intervalo', 'intervalos')}; {fmt_int(c['horas_sem_valor'])} horas sem valor"),
        ("Níveis", "; ".join(f"{NOME_NIVEL.get(n, n)}: {fmt_int(h)} horas" for n, h in c["niveis"].items())),
        ("Anos parciais", fmt_lista(str(a) for a in c["anos_parciais"]) or "nenhum"),
    ]
    if c.get("trechos", 0) > 1:
        pares.append(("Trechos", f"{fmt_int(c['trechos'])} (tabela abaixo)"))
    return pares


def _datas(res: ResultadosAnalise, pacote: str) -> str:
    d = (res.datas_obtencao or {}).get(pacote) or {}
    data = str(d.get("obtencao_mais_recente") or "")
    return f"obtido em {fmt_data(data)}" if data else "data de obtenção não registrada"


def linhas_tabela_niveis(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Conjuntos do ONS usados no relatório, com o nível e o identificador de cada um (FR-041, seção 1)."""
    cabecalho = ["Conjunto do ONS", "Nível", "Identificador", "Obtenção"]
    ident = perfil_ativo().identificacao
    g = _g(res)
    if referencia_restricao():  # eólica ou solar: a restrição com detalhe da usina; a geração, do conjunto
        linhas = [["Restrição com detalhe (série de referência)", "usina", f"id ONS {ident.id_ons}; CEG {ident.ceg}",
                   _datas(res, pacote_referencia())]]
        nivel_geracao = registro.nivel_coletado(perfil_ativo(), "geracao")
        if nivel_geracao:
            linhas.append(["Geração por usina", _nivel_texto(nivel_geracao),
                           str(ident.id_conjunto if nivel_geracao == "conjunto" else ident.id_ons),
                           _datas(res, CONJUNTO_GERACAO)])
    else:
        linhas = [["Geração por usina (série de referência)", _nivel_texto(g.get("nivel", "")),
                   "; ".join(i for i in (g.get("identificador_usina"), g.get("identificador_conjunto")) if i),
                   _datas(res, CONJUNTO_GERACAO)]]
    for chave, nome, pacote in (("programacao", "Programação diária", "programacao_diaria"),
                                ("disponibilidade", "Disponibilidade por usina", "disponibilidade_usina")):
        n = res.niveis.get(chave)
        if n:
            linhas.append([nome, _nivel_texto(n["nivel"]), n["identificador"], _datas(res, pacote)])
    for chave, nome, pacote in (("fator_capacidade", "Fator de capacidade", CONJUNTO_FATOR_CAPACIDADE),
                                ("restricao_razao", "Restrição com a razão", pacote_variante("restricao_razao"))):
        n = res.niveis.get(chave)  # eólicas e solares
        if n:
            linhas.append([nome, _nivel_texto(n["nivel"]), n["identificador"], _datas(res, pacote)])
    if not referencia_restricao() and registro.nivel_coletado(perfil_ativo(), "restricao_detalhe"):
        linhas.append(["Restrição com detalhe", "usina", f"id ONS {ident.id_ons}; CEG {ident.ceg}",
                       _datas(res, pacote_variante("restricao_detalhe"))])
    if res.ons:
        linhas.append(["Indicadores de desempenho do ONS", "usina", f"CEG {ident.ceg}",
                       _datas(res, "ind_disponibilidade_fgeracao_uge_mensal")])
    if res.cadastro:
        linhas.append(["Modalidade das usinas", "usina", f"CEG {ident.ceg}", _datas(res, "modalidade-usina")])
    if getattr(ident, "id_conjunto", None):
        linhas.append(["Composição dos conjuntos de usinas", "conjunto", str(ident.id_conjunto),
                       _datas(res, "usina_conjunto")])
    if (getattr(res, "conjunto", None) or {}).get("com_capacidade"):  # a potência das usinas do conjunto
        linhas.append(["Capacidade de geração", "usinas do conjunto", f"CEG das usinas de {ident.id_conjunto}",
                       _datas(res, CONJUNTO_CAPACIDADE)])
    if getattr(res, "hidrologia", None):  # hidrelétrica sem EVT, com os Dados hidrológicos
        linhas.append(["Dados hidrológicos horários", "usina",
                       f"cod_usina {ident.cod_usina}, reservatório {ident.id_reservatorio}",
                       _datas(res, CONJUNTO_HIDROLOGIA)])
    return cabecalho, linhas


def _com_secao_conjunto(res: ResultadosAnalise) -> bool:
    return bool(getattr(res, "conjunto", None))


def linhas_tabela_trechos(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """Trechos do período (plano da Coleta de dados, D25) em que muda o nível ou a composição. Com a seção do conjunto,
    sem a coluna dos CEGs: a composição, com os nomes das usinas, fica naquela seção."""
    com_ceg = not _com_secao_conjunto(res)
    cabecalho = ["Trecho", "Início", "Fim", "Modalidade", "Nível", *(["Composição (CEG)"] if com_ceg else []), "Tipos"]
    t = res.trechos
    if t is None or not len(t):
        return cabecalho, []
    linhas = [[str(r["trecho"]), fmt_data_hora(r["inicio"]) if r["inicio"] else "",
               fmt_data_hora(r["fim"]) if r["fim"] else "", str(r["modalidade"]), str(r["nivel_geracao"]),
               *([str(r["composicao"]).replace(";", "; ")] if com_ceg else []),
               str(r["tipos_composicao"]).replace(";", "; ")]
              for r in t.to_dict("records")]
    return cabecalho, linhas


# ---------------------------------------------------------------------------
# Tabelas das seções
# ---------------------------------------------------------------------------


def _fc(res: ResultadosAnalise) -> bool:
    return res.tipo in TIPOS_COM_FATOR_CAPACIDADE


def linhas_tabela_anuais(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    a = res.comum["anuais"]
    com_disp = a["disponibilidade_media_mw"].notna().any()
    cabecalho = ["Ano", "Nível", "Horas", "Com valor", "Geração média (MWmed)", "Energia (MWh)", "Máxima (MW)",
                 f"Horas até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW", "% das horas"]
    if _fc(res):
        cabecalho.append("Fator de capacidade")
    if com_disp:
        cabecalho += ["Disp. média (MW)", "Disp. (% Pinst)"]
    sem_despacho = _sem_despacho_por_ano(res)
    if sem_despacho is not None:  # o indicador de perda das térmicas (D27)
        cabecalho.append("Disp. sem despacho (h)")
    corte = _corte_por_ano(res)
    if corte is not None:  # o das eólicas e solares
        cabecalho.append(COLUNA_CORTE)
    linhas = []
    for r in a.itertuples():
        linha = [_rotulo_ano(r.ano, r.ano_parcial), _nivel_texto(r.nivel), fmt_int(r.horas), fmt_int(r.horas_com_valor),
                 fmt_num(r.geracao_media_mw, 1), fmt_int(r.energia_mwh), fmt_num(r.geracao_maxima_mw, 1),
                 fmt_int(r.horas_paradas), fmt_pct(r.pct_horas_paradas)]
        if _fc(res):
            linha.append(fmt_pct(r.fator_capacidade_pct))
        if com_disp:
            linha += [fmt_num(r.disponibilidade_media_mw, 1), fmt_pct(r.disponibilidade_relativa_pct)]
        if sem_despacho is not None:
            horas = sem_despacho.get(int(r.ano)) if r.nivel == "usina" else None
            linha.append("—" if horas is None else fmt_int(horas))
        if corte is not None:
            c = corte.get(int(r.ano)) if r.nivel == "usina" else None
            linha.append("—" if c is None else f"{fmt_num(c[0], 0)} ({fmt_pct(c[1])})")
        linhas.append(linha)
    return cabecalho, linhas


def _corte_por_ano(res: ResultadosAnalise) -> Optional[Dict[int, Tuple[float, float]]]:
    """Energia cortada e % da estimada por ano (eólicas e solares com a restrição com detalhe); None nas demais."""
    c = ((getattr(res, "renovavel", None) or {}).get("restricao") or {}).get("anual")
    if c is None or not len(c):
        return None
    return {int(r.periodo): (float(r.energia_cortada_mwh), float(r.pct_estimada)) for r in c.itertuples()}


def _sem_despacho_por_ano(res: ResultadosAnalise) -> Optional[Dict[int, int]]:
    """Horas disponíveis sem despacho por ano (térmicas com o despacho e a disponibilidade); None nas demais."""
    d = (getattr(res, "termica", None) or {}).get("disponivel_sem_despacho")
    if not d:
        return None
    return {int(r.ano): int(r.horas_disponivel_sem_despacho) for r in d["anual"].itertuples()}


def linhas_tabela_disponibilidade_anual(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    a = res.comum["disponibilidade"]["anual"]
    cabecalho = ["Ano", "Horas com o dado", "Disp. operacional (MW)", "Disp. (% Pinst)", "Disp. sincronizada (MW)",
                 "Geração (MW)", "Horas indisp. total", "Horas paradas disponível", "Horas geração > disp."]
    linhas = [[_rotulo_ano(int(r.periodo), r.ano_parcial), fmt_int(r.horas_comuns), fmt_num(r.disp_operacional_media_mw, 1),
               fmt_pct(r.disponibilidade_relativa_pct), fmt_num(r.disp_sincronizada_media_mw, 1),
               fmt_num(r.geracao_media_mw, 1), fmt_int(r.horas_indisponibilidade_total),
               fmt_int(r.horas_paradas_disponivel), fmt_int(r.horas_geracao_acima_disponibilidade)]
              for r in a.itertuples()]
    return cabecalho, linhas


def linhas_tabela_eventos_indisponibilidade(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    cabecalho = ["Início", "Fim", "Duração (h)", "Geração média (MW)"]
    e = res.comum["disponibilidade"]["eventos_indisponibilidade_total"]
    longos = e[e["duracao_h"] >= DURACAO_MINIMA_EVENTO_RELATORIO_H] if len(e) else e
    longos = longos.sort_values("duracao_h", ascending=False).head(NUMERO_EVENTOS_RELATORIO) if len(longos) else longos
    linhas = [[fmt_data_hora(r.inicio), fmt_data_hora(r.fim), fmt_int(r.duracao_h), fmt_num(r.geracao_media_mw, 2)]
              for r in longos.itertuples()]
    return cabecalho, linhas


def linhas_tabela_programacao_mensal(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    m = res.comum["programacao"]["mensal"]
    cabecalho = ["Mês", "Horas comuns", "Verificada (MW)", "Programada (MW)", "Desvio médio (MW)",
                 "Desvio absoluto (MW)", "Horas parada c/ programação"]
    linhas = [[fmt_mes_ano(r.mes), fmt_int(r.horas_comuns), fmt_num(r.geracao_media_mw, 1),
               fmt_num(r.programada_media_mw, 1), fmt_num(r.desvio_medio_mw, 1), fmt_num(r.desvio_medio_absoluto_mw, 1),
               fmt_int(r.horas_desvio_programacao)] for r in m.itertuples()]
    return cabecalho, linhas


def linhas_tabela_programacao_eventos(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    cabecalho = ["Início", "Fim", "Duração (h)", "Programação média (MW)"]
    e = res.comum["programacao"]["eventos"]
    e = e.sort_values("duracao_h", ascending=False).head(NUMERO_EVENTOS_RELATORIO) if len(e) else e
    linhas = [[fmt_data_hora(r.inicio), fmt_data_hora(r.fim), fmt_int(r.duracao_h), fmt_num(r.programacao_media_mw, 1)]
              for r in e.itertuples()]
    return cabecalho, linhas


def linhas_tabela_sinalizacoes(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    s = res.comum["qualidade"]["sinalizacoes"]
    total = res.cobertura["horas_observadas"]
    return (["Código", "Descrição", "Horas", "% das horas"],
            [[r.codigo, r.descricao, fmt_int(r.horas), fmt_pct(r.horas / total * 100.0 if total else math.nan, 2)]
             for r in s.itertuples()])


def linhas_tabela_ausencias(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    a = res.comum["qualidade"]["ausencias"]
    cabecalho = ["Tipo", "Início", "Fim", "Horas"]
    if a is None or not len(a):
        return cabecalho, []
    maiores = a.sort_values("horas", ascending=False).head(NUMERO_EVENTOS_RELATORIO).sort_values("inicio")
    rotulos = {"HORAS": "horas", "MES_SEM_USINA": "mês sem a usina", "MES_SEM_ARQUIVO": "mês sem arquivo"}
    return cabecalho, [[rotulos.get(r.tipo, str(r.tipo)), fmt_data_hora(r.inicio), fmt_data_hora(r.fim), fmt_int(r.horas)]
                       for r in maiores.itertuples()]


def linhas_tabela_ons_disponibilidade(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    """DISPF da usina por ano, ao lado da disponibilidade operacional (Disponibilidade por usina), quando há."""
    cabecalho = ["Ano", "Disp. operacional (% Pinst)", "DISPF (média das UGs)", "Indisp. programada",
                 "Indisp. forçada", "Δ DISPF vs ref. GF"]
    t = res.ons.get("disp_anual", pd.DataFrame())
    linhas = [[_rotulo_ano(r.ano, r.ano_parcial), fmt_pct(r.disponibilidade_declarada_pct), fmt_pct(r.dispf_pct),
               fmt_pct(r.indisppf_pct), fmt_pct(r.indispff_pct), fmt_pp(r.desvio_dispf_referencia_pp)]
              for r in t.itertuples()]
    return cabecalho, linhas


def linhas_tabela_omitidos(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    return ["Seção ou regra", "Motivo"], [[o["item"], o["motivo"]] for o in res.omitidos]


def linhas_tabela_nao_aplicaveis(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    t = res.comum.get("conferencias_nao_aplicaveis", pd.DataFrame())
    return ["Conferência", "Motivo"], [[DESCRICAO_CONFERENCIAS.get(r["conferencia"], r["conferencia"]), r["motivo"]]
                                       for r in t.to_dict("records")]


def textos_tabelas(res: ResultadosAnalise) -> Dict[str, Tuple[str, str]]:
    """Subtítulo e nota de cada tabela do caminho sem EVT (chaves do mapa de fontes)."""
    granularidade = (" Nível: usina, ou conjunto de usinas quando o ONS publica só a soma do conjunto (decisão "
                     "de não dividir os números do conjunto entre as usinas)." if "conjunto" in niveis_da_base(res)
                     else "")
    return {
        "tab_niveis": ("Conjuntos do ONS, nível e identificador", ""),
        "tab_trechos": ("Trechos do período", "Trecho novo a cada mudança de modalidade, de composição do conjunto "
                                             "ou de código; " + ("as usinas de cada composição estão na seção do "
                                                                 "conjunto." if _com_secao_conjunto(res) else
                                                                 "composição pelos CEGs das usinas do conjunto.")),
        "tab_anuais_comum": ("", (
            f"* Ano parcial. Geração média = média das horas com valor; horas até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} "
            "MW = horas com geração até esse limiar, sobre as horas com valor"
            + ("; fator de capacidade = geração média ÷ potência instalada" if _fc(res) else "")
            + ("; disp. = disponibilidade operacional média da usina (Disponibilidade por usina)"
               if res.comum.get("disponibilidade") else "")
            + ("; disp. sem despacho = horas disponíveis, sem programação e sem geração no despacho"
               if _sem_despacho_por_ano(res) is not None else "")
            + ("; energia cortada = por restrição de operação, nas semi-horas com a marca de restrição, e % da "
               "energia estimada nelas" if _corte_por_ano(res) is not None else "") + "." + granularidade)),
        "tab_disponibilidade_anual_comum": ("Disponibilidade e geração da usina por ano", (
            f"* Ano parcial. Só as horas com a disponibilidade e a geração da usina. Indisponibilidade total = "
            f"disponibilidade operacional até {fmt_num(LIMIAR_INDISPONIBILIDADE_TOTAL_MW, 3)} MW; parada disponível = "
            f"geração até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW com disponibilidade acima desse valor; geração > "
            f"disp. = regra R7 (tolerância de {fmt_num(TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW, 1)} MW).")),
        "tab_eventos_indisponibilidade_comum": (
            f"Indisponibilidade total com pelo menos {DURACAO_MINIMA_EVENTO_RELATORIO_H} h",
            f"Até {NUMERO_EVENTOS_RELATORIO} eventos, os mais longos; a lista completa está na planilha."),
        "tab_programacao_mensal_comum": ("Geração programada × verificada por mês", (
            f"Horas comuns às duas fontes, no mesmo nível. Desvio = verificada − programada; horas parada c/ "
            f"programação = geração até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW com programação acima de "
            f"{fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 0)} MW.")),
        "tab_programacao_eventos_comum": (
            f"Horas consecutivas com geração até {fmt_num(LIMIAR_GERACAO_PARADA_MW, 0)} MW e programação acima de "
            f"{fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 0)} MW",
            f"Até {NUMERO_EVENTOS_RELATORIO} eventos, os mais longos; a lista completa está na planilha."),
        "tab_sinalizacoes": ("Horas sinalizadas na base horária",
                             "Sinalização não exclui o registro: as horas ficam na base e nos totais."),
        "tab_ausencias": ("Intervalos ausentes da série de referência",
                          f"Até {NUMERO_EVENTOS_RELATORIO} intervalos, os mais longos; nenhuma hora é preenchida. A "
                          "lista completa está na planilha."),
        "tab_ons_disp_anual_comum": (
            "Disponibilidade da usina por ano: operacional (Disponibilidade por usina) e DISPF apurado pelo ONS",
            "* Ano parcial. DISPF da usina = média das unidades ponderada pela potência e pelas horas da série de "
            "referência em cada mês; Δ = diferença para a disponibilidade de referência da garantia física, quando o "
            "perfil a informa."),
        "tab_ons_decomposicao": ("TEIFa e TEIP mais recentes: contribuição de cada unidade e parcela de horas", ""),
        "tab_ons_ug_anual": ("Indicadores anuais por unidade geradora (base anual do ONS)",
                             "* Ano parcial. DISPF, INDISPPF e INDISPFF em % do tempo; DMDFF = duração média dos "
                             "desligamentos forçados (h)."),
        "tab_ons_horas": ("Horas por estado operativo, por ano e unidade geradora", "* Ano parcial."),
        "tab_ons_divergencias": ("Meses em que o indicador DISPF e as horas do TEIP divergem", ""),
        "tab_omitidos": ("Seções e regras sem base para a usina", ""),
        "tab_nao_aplicaveis": ("Conferências que não se aplicam à usina", ""),
        "tab_parametros_comum": ("Parâmetros utilizados", ""),
        **_textos_termica(res),
        **_textos_renovavel(res),
        **secoes_conjunto.textos_tabelas(res),
        **_textos_hidrologia(res),
        "tab_usina_peso_potencia": ("Peso da usina na potência do conjunto, por composição", (
            "Potência das unidades da usina em operação no trecho ÷ potência somada das usinas do conjunto com unidade "
            "cadastrada (Capacidade de geração); «—» = unidades da usina ainda fora de operação. É um fato do "
            "cadastro, não uma estimativa da geração da usina: a geração do conjunto não é dividida entre as usinas.")),
    }


def _textos_hidrologia(res: ResultadosAnalise) -> Dict[str, Tuple[str, str]]:
    """A tabela anual da afluência na hidrelétrica sem EVT, com as mesmas colunas da de hoje."""
    if not getattr(res, "hidrologia", None):
        return {}
    return {"tab_hidrologia_anual_comum": (
        "Afluência, vazões, nível e volume útil por ano",
        "Médias sem os valores sinalizados, que saem só do campo afetado (a hora continua nos demais campos); horas acima "
        f"do engolimento = afluência acima do engolimento máximo da usina "
        f"({fmt_num(perfil_ativo().engolimento_maximo_m3s, 1)} m³/s). * ano parcial.")}


def _textos_termica(res: ResultadosAnalise) -> Dict[str, Tuple[str, str]]:
    if not getattr(res, "termica", None):
        return {}
    from src.relatorio import secoes_termica

    return secoes_termica.textos_tabelas(res)


def _textos_renovavel(res: ResultadosAnalise) -> Dict[str, Tuple[str, str]]:
    if not getattr(res, "renovavel", None):
        return {}
    from src.relatorio import secoes_renovavel

    return secoes_renovavel.textos_tabelas(res)


# ---------------------------------------------------------------------------
# Legendas das figuras
# ---------------------------------------------------------------------------


def legenda_figura(res: ResultadosAnalise, chave: str) -> str:
    c = res.cobertura
    pinst = fmt_num(perfil_ativo().parametros.potencia_instalada_mw, 0)
    conjunto = (f" A série do conjunto {nome_conjunto(res)} é a soma das usinas do conjunto, como o ONS publica."
                if "conjunto" in niveis_da_base(res) else "")
    if chave == "serie_temporal_comum":
        disp = " e da disponibilidade operacional da usina" if res.comum.get("disponibilidade") else ""
        linha = f" Linha tracejada: potência instalada da usina ({pinst} MW)." if "usina" in niveis_da_base(res) else ""
        return f"Médias diárias da geração{disp}, de {fmt_data(c['inicio'])} a {fmt_data(c['fim'])}.{linha}{conjunto}"
    if chave == "geracao_mensal":
        m = res.comum["mensal"]
        texto = "Energia gerada em cada mês (GWh), pela soma das horas com valor."
        if len(m):
            maior = m.loc[m["energia_mwh"].idxmax()]
            texto += f" Maior energia mensal: {fmt_num(maior['energia_mwh'] / 1000, 1)} GWh em {fmt_mes_ano(maior['mes'])}."
        return texto + conjunto
    if chave == "sazonalidade":
        return (f"Geração média por mês do ano, só com a série de pelo menos {PERIODO_MINIMO_SAZONALIDADE_MESES} meses "
                f"distintos; cada barra junta os anos do período com aquele mês.{conjunto}")
    if chave == "perfil_horario_comum":
        return f"Geração média por hora do dia, no período, sobre as horas com valor.{conjunto}"
    if chave == "disponibilidade_comum":
        return ("Médias mensais da disponibilidade operacional e sincronizada publicadas pelo ONS e da geração da usina, "
                f"nas horas com os dois dados. Linha tracejada: potência instalada ({pinst} MW).")
    if chave == "conjunto_mensal":  # usina em conjunto
        return secoes_conjunto.legenda_figura(res, chave)
    if chave == "hidrologia_mensal_comum":  # hidrelétrica sem EVT
        return ("Médias mensais da vazão afluente, da turbinada e da vertida publicadas pelo ONS (Dados hidrológicos "
                "horários), sem os valores sinalizados; a hora da série foi conferida pela geração da usina.")
    if getattr(res, "termica", None):
        from src.relatorio import secoes_termica

        return secoes_termica.legenda_figura(res, chave)
    if getattr(res, "renovavel", None):
        from src.relatorio import secoes_renovavel

        return secoes_renovavel.legenda_figura(res, chave)
    return ""


# ---------------------------------------------------------------------------
# Notas metodológicas e conclusão
# ---------------------------------------------------------------------------


def notas(res: ResultadosAnalise) -> List[str]:
    """Notas das usinas sem EVT: fonte, base horária, níveis, omissões e conferências não aplicáveis."""
    c = res.cobertura
    saida = [
        f"Fonte: Portal de Dados Abertos do ONS. Série de referência: {serie_referencia_texto(res)}, varrida em todos "
        "os arquivos publicados; o período vai da primeira à última hora com valor. Os dados passam por consistência "
        "recorrente e podem ser revisados pelo ONS após a publicação.",
        "Base horária comum: uma linha por hora da série de referência, com a disponibilidade e a programação do ONS "
        "na mesma hora, quando há. Os horários são os publicados pelo ONS (hora de início do intervalo).",
        ("Nenhum valor é preenchido: " + (f"as {fmt_int(c['horas_ausentes'])} horas ausentes estão listadas na "
                                          "planilha, e " if c["horas_ausentes"] else "")
         + "as horas sinalizadas ficam na base e nos totais, com o código da regra."),
    ]
    if com_conjunto(res) and referencia_restricao():  # eólica ou solar: a série de referência é da usina
        ident = perfil_ativo().identificacao
        saida.append(
            f"Granularidade: o ONS publica a geração, o fator de capacidade e a razão da restrição do conjunto "
            f"{nome_conjunto(res) or ident.id_conjunto} ({ident.id_conjunto}), e a restrição com detalhe de cada usina; "
            "a série de referência é a da usina. Os números do conjunto são identificados como tais e não são divididos "
            "entre as usinas; a conclusão da usina não usa números do conjunto.")
    elif com_conjunto(res):
        saida.append(
            f"Granularidade: o ONS publica a geração do conjunto {nome_conjunto(res)} ({_g(res).get('identificador_conjunto', '')}), "
            "e não a da usina isolada. Os números do conjunto são identificados como tais e não são divididos entre as "
            "usinas; a conclusão da usina não usa números do conjunto.")
    if getattr(res, "termica", None):
        from src.relatorio import secoes_termica

        saida.append(secoes_termica.nota(res))
    if getattr(res, "renovavel", None):
        from src.relatorio import secoes_renovavel

        texto = secoes_renovavel.nota(res)
        if texto:
            saida.append(texto)
    texto = secoes_conjunto.nota(res)  # só com a seção do conjunto
    if texto:
        saida.append(texto)
    if getattr(res, "hidrologia", None):  # hidrelétrica sem EVT
        saida.append("Dados hidrológicos: informados pelos agentes e não consistidos pelo ONS; a série publicada marca o fim "
                     "da hora, e a série foi convertida para a hora de início, conferida pela correlação entre a vazão "
                     "turbinada e a geração da usina, e não pela EVT, que a usina não tem. Valores fora da faixa física "
                     "são sinalizados e saem só do campo afetado; campos vazios não são tratados como zero.")
    saida.append(nota_conclusao_catalogo(res))
    if res.omitidos or len(res.comum.get("conferencias_nao_aplicaveis", ())):
        saida.append("As seções e as regras sem base para a usina e as conferências que não se aplicam a ela estão "
                     "nas tabelas abaixo, com o motivo de cada uma.")
    return saida


# ---------------------------------------------------------------------------
# Tabela de parâmetros
# ---------------------------------------------------------------------------


def tabela_parametros(res: ResultadosAnalise) -> pd.DataFrame:
    """Parâmetros da usina e da análise, com a origem, no caminho sem EVT."""
    p = perfil_ativo()
    pr = p.parametros
    rf = pr.fontes.geral
    analise = "Parâmetro de análise"
    linhas = [("Usina", "Tipo · modalidade", f"{res.tipo} · {res.modalidade}", "", "perfil da usina"),
              ("Usina", "Potência instalada", fmt_num(pr.potencia_instalada_mw, 1), "MW", rf),
              ("Usina", "Unidades geradoras", str(pr.unidades_geradoras), "", rf)]
    if pr.combustivel:
        linhas.append(("Usina", "Combustível", str(pr.combustivel), "", rf))
    if pr.garantia_fisica_mwmed is not None:
        linhas.append(("Usina", "Garantia física", fmt_num(pr.garantia_fisica_mwmed, 1), "MWmed",
                       pr.fontes.garantia_fisica or rf))
    linhas += [
        ("Usina", "Início da operação comercial", str(p.usina.inicio_operacao_comercial), "",
         pr.fontes.inicio_operacao_comercial or rf),
        ("Análise", "Geração até o limiar", f"geração ≤ {fmt_num(LIMIAR_GERACAO_PARADA_MW, 1)}", "MW", analise),
        ("Análise", "Indisponibilidade total", f"disponibilidade ≤ {fmt_num(LIMIAR_INDISPONIBILIDADE_TOTAL_MW, 3)}", "MW",
         analise),
        ("Análise", "Unidade sincronizada", f"disponibilidade sincronizada > {fmt_num(LIMIAR_SINCRONIZADA_MW, 1)}", "MW",
         analise),
        ("Análise", "Desvio da programação", f"geração ≤ {fmt_num(LIMIAR_GERACAO_PARADA_MW, 1)} e programação > "
                                             f"{fmt_num(LIMIAR_DESVIO_PROGRAMACAO_MW, 1)}", "MW", analise),
        ("Análise", "Sazonalidade", f"≥ {PERIODO_MINIMO_SAZONALIDADE_MESES} meses distintos", "", analise),
        *([("Análise", "Desvio do despacho", f"|verificada − programada| > {fmt_num(LIMIAR_DESVIO_DESPACHO_MW, 1)}",
            "MW", analise)] if getattr(res, "termica", None) else []),
        *([("Análise", f"Faixa de {recurso['grandeza']}", fmt_num(recurso["largura"], 0), recurso["unidade"], analise),
           ("Análise", f"Limite físico de {recurso['grandeza']}", f"≤ {fmt_num(recurso['limite'], 0)}",
            recurso["unidade"], analise)]
          if (recurso := (getattr(res, "renovavel", None) or {}).get("recurso")) else []),
        ("Validação", "Tolerância de geração acima da disponibilidade (R7)",
         fmt_num(TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW, 1), "MW", analise),
        ("Fonte", "Série de referência", serie_referencia_texto(res), "", f"{ONS_PORTAL_DATASET_URL}{pacote_referencia()}"),
    ]
    for chave, nome, pacote in (("programacao", "Programação diária", "programacao_diaria"),
                                ("disponibilidade", "Disponibilidade por usina", "disponibilidade_usina")):
        n = res.niveis.get(chave)
        if n:
            linhas.append(("Fonte", nome, f"{_nivel_texto(n['nivel'])}: {n['identificador']}", "",
                           f"{ONS_PORTAL_DATASET_URL}{pacote}"))
    if res.cadastro:
        linhas.append(("Fonte", "Modalidade das usinas", f"CEG {p.identificacao.ceg}", "",
                       f"{ONS_PORTAL_DATASET_URL}modalidade-usina"))
    t = getattr(res, "termica", None) or {}
    if t:
        from src.relatorio.secoes_termica import codigos_texto

        linhas.append(("Fonte", "Geração térmica por motivo de despacho",
                       f"CEG {p.identificacao.ceg}; códigos {codigos_texto(res)}", "",
                       f"{ONS_PORTAL_DATASET_URL}{CONJUNTO_DESPACHO}"))
        if t.get("cvu_coletado"):
            linhas.append(("Fonte", "CVU das usinas térmicas", f"códigos {codigos_texto(res)}", "",
                           f"{ONS_PORTAL_DATASET_URL}{CONJUNTO_CVU}"))
        if t.get("cmo_coletado"):
            linhas.append(("Fonte", "CMO semanal", f"subsistema {p.usina.subsistema} (agregado)", "",
                           f"{ONS_PORTAL_DATASET_URL}{CONJUNTO_CMO}"))
    for chave, nome, pacote in (("fator_capacidade", "Fator de capacidade", CONJUNTO_FATOR_CAPACIDADE),
                                ("restricao_razao", "Restrição com a razão", pacote_variante("restricao_razao"))):
        n = res.niveis.get(chave)  # eólicas e solares
        if n:
            linhas.append(("Fonte", nome, f"{_nivel_texto(n['nivel'])}: {n['identificador']}", "",
                           f"{ONS_PORTAL_DATASET_URL}{pacote}"))
    if not referencia_restricao() and registro.nivel_coletado(p, "restricao_detalhe"):
        linhas.append(("Fonte", "Restrição com detalhe", f"id ONS {p.identificacao.id_ons}; CEG {p.identificacao.ceg}",
                       "", f"{ONS_PORTAL_DATASET_URL}{pacote_variante('restricao_detalhe')}"))
    return pd.DataFrame(linhas, columns=["grupo", "parametro", "valor", "unidade", "origem"])


def linhas_tabela_parametros(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    return (["Grupo", "Parâmetro", "Valor", "Unidade", "Origem"],
            [[str(r.grupo), str(r.parametro), str(r.valor), str(r.unidade), str(r.origem)]
             for r in res.parametros.itertuples()])


# ---------------------------------------------------------------------------
# Seções
# ---------------------------------------------------------------------------


def _tabela(chave: str, cl: Tuple[List[str], List[List[str]]], larguras: Sequence[float] = (),
            numericas: Sequence[int] = (), intro: str = "") -> Bloco:
    cabecalho, linhas = cl
    return Bloco("tabela", chave, cabecalho, linhas, larguras or [1.0] * len(cabecalho), numericas, intro)


def _numericas(cabecalho: List[str], primeiras_texto: int) -> range:
    return range(primeiras_texto, len(cabecalho))


def linhas_tabela_peso_usina(res: ResultadosAnalise) -> Tuple[List[str], List[List[str]]]:
    peso = (getattr(res, "conjunto", None) or {}).get("peso_usina")
    cabecalho = ["Composição", "Início", "Fim", "Potência da usina (MW)", "Potência das usinas do conjunto (MW)",
                 "Peso da usina"]
    if peso is None or not len(peso):
        return cabecalho, []
    return cabecalho, [[str(r.trecho), fmt_data(r.inicio), fmt_data(r.fim),
                        "—" if pd.isna(r.potencia_usina_mw) else fmt_num(r.potencia_usina_mw, 1),
                        fmt_num(r.potencia_somada_mw, 1), "—" if pd.isna(r.peso_pct) else fmt_pct(r.peso_pct)]
                       for r in peso.itertuples()]


def _blocos_usina_no_conjunto(res: ResultadosAnalise) -> List[Bloco]:
    """A parte da usina (FR-048): o que o ONS publica da usina isolada, onde obter a geração dela e o peso dela na
    potência do conjunto (o peso e a falta da série própria estão na constatação)."""
    from src.relatorio.estrutura import secoes_presentes

    q = res.comum["qualidade"]
    periodo = q.get("linhas_usina_sem_valor_periodo") or {}
    vazias = (f" e, de {fmt_data(periodo['inicio'])} a {fmt_data(periodo['fim'])}, linhas próprias na Geração por usina, "
              "todas sem valor" if q.get("linhas_usina_sem_valor") and periodo.get("inicio") else "")
    numero = next((n for n, s in secoes_presentes(res) if s.chave == "parte_conjunto"), None)
    onde = f"na seção {numero}, antes da conclusão" if numero else "na parte do conjunto"
    texto = (f"Da usina isolada, o ONS publica só a ficha do cadastro (na capa), as unidades geradoras e a entrada no "
             f"conjunto{vazias}; não publica a geração, a disponibilidade nem os indicadores dela. Os dados de operação "
             f"são os do conjunto, {onde}. A geração da usina isolada consta da medição da CCEE e dos registros do "
             "agente, que este relatório não usa: ele se limita aos dados abertos do ONS.")
    b = [Bloco("texto", textos=[texto])]
    cab, linhas = linhas_tabela_peso_usina(res)
    if linhas:
        b.append(_tabela("tab_usina_peso_potencia", (cab, linhas), [0.8, 0.9, 0.9, 1.0, 1.3, 0.8], range(3, 6)))
    return b


def blocos_secao(res: ResultadosAnalise, chave: str) -> List[Bloco]:
    """Blocos de cada seção do caminho sem EVT, na ordem em que o PDF e o Markdown os mostram."""
    b: List[Bloco] = []
    if chave == "fonte_cobertura":
        b.append(Bloco("chave_valor", "tab_fonte_cobertura", pares=pares_cobertura(res)))
        b.append(_tabela("tab_niveis", linhas_tabela_niveis(res), [2.2, 0.8, 2.0, 1.2]))
        cab, linhas = linhas_tabela_trechos(res)
        if len(linhas) > 1 or (linhas and getattr(perfil_ativo().identificacao, "id_conjunto", None)):
            b.append(_tabela("tab_trechos", (cab, linhas), [0.5, 1.1, 1.1, 0.9, 0.7, 2.4, 1.0]))
    elif chave == "anuais_comum":
        cab, linhas = linhas_tabela_anuais(res)
        b.append(_tabela("tab_anuais_comum", (cab, linhas), [0.6, 0.8] + [1.0] * (len(cab) - 2), _numericas(cab, 2)))
    elif chave == "disponibilidade_geracao_comum":
        cab, linhas = linhas_tabela_disponibilidade_anual(res)
        b.append(_tabela("tab_disponibilidade_anual_comum", (cab, linhas), [0.6] + [1.0] * (len(cab) - 1),
                         _numericas(cab, 1)))
        cab, linhas = linhas_tabela_eventos_indisponibilidade(res)
        b.append(_tabela("tab_eventos_indisponibilidade_comum", (cab, linhas), [1.2, 1.2, 0.8, 1.0], range(2, 4))
                 if linhas else Bloco("sem_linhas", "tab_eventos_indisponibilidade_comum",
                                      textos=["Nenhum período com essa duração."]))
    elif chave == "indicadores_ons_comum":
        for c, funcao in (("tab_ons_disp_anual_comum", linhas_tabela_ons_disponibilidade),
                          ("tab_ons_decomposicao", linhas_tabela_ons_decomposicao),
                          ("tab_ons_ug_anual", linhas_tabela_ons_ug_anual), ("tab_ons_horas", linhas_tabela_ons_horas),
                          ("tab_ons_divergencias", linhas_tabela_ons_divergencias)):
            cab, linhas = funcao(res)
            if linhas:
                b.append(_tabela(c, (cab, linhas), numericas=_numericas(cab, 2)))
    elif chave == "serie_temporal_comum":
        b.append(Bloco("figura", "serie_temporal_comum"))
    elif chave == "geracao_mensal":
        b.append(Bloco("figura", "geracao_mensal"))
        if len(res.comum["sazonalidade"]):
            b.append(Bloco("figura", "sazonalidade"))
        else:
            meses = res.cobertura["meses_distintos"]
            b.append(Bloco("texto", textos=[f"Sazonalidade omitida: a série tem {fmt_int(meses)} "
                                            f"{plural(meses, 'mês distinto', 'meses distintos')}, abaixo dos "
                                            f"{PERIODO_MINIMO_SAZONALIDADE_MESES} necessários."]))
    elif chave == "perfil_horario_comum":
        b.append(Bloco("figura", "perfil_horario_comum"))
    elif chave == "programacao_comum":
        r = res.comum["programacao"]["resumo"]
        b.append(Bloco("texto", textos=[
            f"Programação diária do ONS ({_nivel_texto(res.comum['programacao']['nivel'])}) × geração verificada, de "
            f"{fmt_data(r['inicio'])} a {fmt_data(r['fim'])}: {fmt_int(r['horas_comuns'])} horas comuns; correlação de "
            f"{fmt_num(r['correlacao'], 2)}; {fmt_int(r['dias_ausentes'])} dias sem arquivo de programação."]))
        cab, linhas = linhas_tabela_programacao_mensal(res)
        b.append(_tabela("tab_programacao_mensal_comum", (cab, linhas), numericas=_numericas(cab, 1)))
        cab, linhas = linhas_tabela_programacao_eventos(res)
        if linhas:
            b.append(_tabela("tab_programacao_eventos_comum", (cab, linhas), [1.2, 1.2, 0.8, 1.0], range(2, 4)))
        if getattr(res, "renovavel", None):  # aderência à programação das eólicas e solares
            from src.relatorio import secoes_renovavel

            b.extend(secoes_renovavel.blocos_programacao(res))
    elif chave == "disponibilidade_sincronizada_comum":
        b.append(Bloco("figura", "disponibilidade_comum"))
    elif chave == "qualidade_comum":
        cab, linhas = linhas_tabela_sinalizacoes(res)
        b.append(_tabela("tab_sinalizacoes", (cab, linhas), [0.6, 3.0, 0.8, 0.8], range(2, 4)) if linhas
                 else Bloco("sem_linhas", "tab_sinalizacoes", textos=["Nenhuma hora sinalizada."]))
        cab, linhas = linhas_tabela_ausencias(res)
        b.append(_tabela("tab_ausencias", (cab, linhas), [1.0, 1.2, 1.2, 0.6], range(3, 4)) if linhas
                 else Bloco("sem_linhas", "tab_ausencias", textos=["Nenhuma hora ausente."]))
    elif chave in ("despacho_motivo", "atendimento_despacho", "disponivel_sem_despacho"):
        from src.relatorio import secoes_termica

        b.extend(secoes_termica.blocos(res, chave))
    elif chave in SECOES_RENOVAVEL:
        from src.relatorio import secoes_renovavel

        b.extend(secoes_renovavel.blocos(res, chave))
    elif chave in secoes_conjunto.SECOES_CONJUNTO:  # usina em conjunto
        b.extend(secoes_conjunto.blocos(res, chave))
    elif chave == "usina_no_conjunto":  # FR-048: a parte da usina
        b.extend(_blocos_usina_no_conjunto(res))
    elif chave == "parte_conjunto":  # FR-048: a parte do conjunto, com as seções do conjunto como subseções
        for titulo, secao in (("Indicadores anuais do conjunto", "anuais_comum"),
                              ("Série temporal da geração do conjunto", "serie_temporal_comum"),
                              ("Geração mensal e sazonalidade do conjunto", "geracao_mensal"),
                              ("Perfil horário da geração do conjunto", "perfil_horario_comum"),
                              ("", "conjunto"),  # as tabelas da composição já trazem os subtítulos
                              ("Programação diária × geração verificada do conjunto", "programacao_comum")):
            if secao == "programacao_comum" and not res.comum.get("programacao"):
                continue
            if titulo:
                b.append(Bloco("subtitulo", textos=[titulo]))
            b.extend(blocos_secao(res, secao))
    elif chave == "hidrologia_comum":  # a cobertura e o alinhamento estão na constatação
        if res.hidrologia.get("publicado"):
            cab, linhas = linhas_tabela_hidrologia_anual(res)
            b.append(_tabela("tab_hidrologia_anual_comum", (cab, linhas), [0.6] + [1.0] * (len(cab) - 1),
                             _numericas(cab, 1)))
            b.append(Bloco("figura", "hidrologia_mensal_comum"))
    elif chave == "notas_comum":
        b.append(Bloco("notas", textos=notas(res)))
        cab, linhas = linhas_tabela_omitidos(res)
        if linhas:
            b.append(_tabela("tab_omitidos", (cab, linhas), [1.5, 3.5]))
        cab, linhas = linhas_tabela_nao_aplicaveis(res)
        if linhas:
            b.append(_tabela("tab_nao_aplicaveis", (cab, linhas), [2.2, 2.8]))
        b.append(_tabela("tab_parametros_comum", linhas_tabela_parametros(res), [55, 190, 170, 50, 305]))
    return b

