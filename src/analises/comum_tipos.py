"""Seções comuns das usinas sem EVT, calculadas sobre a base horária comum (plano das Análises, D16, D17 e D19).

Parte de ``base_horaria.csv`` do Tratamento (geração da série de referência com o nível de cada hora, disponibilidade,
programação, trecho e sinalizações) e devolve o campo ``comum`` de ``ResultadosAnalise``, com as omissões e os níveis.
Nenhum número mistura níveis: as tabelas por ano e por mês têm uma linha por nível, e a disponibilidade (sempre da
usina) só é comparada com a geração da usina (princípio VIII). Nada é preenchido: hora sem valor fica fora das médias e
é contada na qualidade dos dados (princípio V).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.analises.comum import _media, _pct
from src.analises.evt import identificar_eventos
from src.coleta import registro
from src.coleta.registro import HIDRELETRICAS, TERMICAS
from src.comum.regras import (
    DATAS_SENTINELA,
    LIMIAR_DESVIO_PROGRAMACAO_MW,
    LIMIAR_GERACAO_PARADA_MW,
    LIMIAR_INDISPONIBILIDADE_TOTAL_MW,
    LIMIAR_SINCRONIZADA_MW,
    PERIODO_MINIMO_SAZONALIDADE_MESES,
    TIPOS_COM_FATOR_CAPACIDADE,
)
from src.tratamento.disponibilidade import DESCRICAO_QUALIDADE as DESCRICAO_QUALIDADE_DISPONIBILIDADE

NOME_NIVEL: Dict[str, str] = {"usina": "usina", "conjunto": "conjunto de usinas", "agregado": "agregado"}
DESCRICAO_SINALIZACOES: Dict[str, str] = {
    "G1": "geração com valor não numérico",
    **{codigo: f"disponibilidade: {texto}" for codigo, texto in DESCRICAO_QUALIDADE_DISPONIBILIDADE.items()},
    "R7": "geração acima da disponibilidade declarada",
}
# Seções do caminho sem EVT, na ordem da FR-041 da Geração do relatório, para as omissões (só as que dependem de base)
TITULO_SAZONALIDADE = "Sazonalidade (distribuição por mês do ano)"


def _ano_parcial(g: pd.DataFrame, ano: int) -> bool:
    return bool(g["din_instante"].min() > pd.Timestamp(ano, 1, 1, 0) or g["din_instante"].max() < pd.Timestamp(ano, 12, 31, 23))


# ---------------------------------------------------------------------------
# Cobertura
# ---------------------------------------------------------------------------


def cobertura_comum(base: pd.DataFrame, ausencias: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """Período da série de referência, horas, ausências, anos parciais e horas por nível."""
    inicio, fim = base["din_instante"].min(), base["din_instante"].max()
    grade = pd.date_range(inicio, fim, freq="h") if len(base) else pd.DatetimeIndex([])
    anos = base["din_instante"].dt.year
    parciais = [int(a) for a, g in base.groupby(anos) if _ano_parcial(g, int(a))]
    aus = ausencias if ausencias is not None else pd.DataFrame()
    return {
        "inicio": inicio,
        "fim": fim,
        "horas_observadas": len(base),
        "horas_esperadas": len(grade),
        "horas_ausentes": int(pd.to_numeric(aus.get("horas", pd.Series(dtype=int))).sum()) if len(aus) else 0,
        "horas_sem_valor": int(base["geracao_mw"].isna().sum()),
        "anos_parciais": parciais,
        "anos_completos": sorted(int(a) for a in anos.unique() if int(a) not in parciais),
        "meses_distintos": int(base["din_instante"].dt.month.nunique()),
        "meses": int(base["din_instante"].dt.to_period("M").nunique()),
        "niveis": {str(k): int(v) for k, v in base["nivel"].value_counts().sort_index().items()},
        "trechos": int(base["trecho"].nunique()) if "trecho" in base.columns else 0,
    }


# ---------------------------------------------------------------------------
# Indicadores anuais, série diária, geração mensal, sazonalidade e perfil horário
# ---------------------------------------------------------------------------


def indicadores_anuais_comum(base: pd.DataFrame, tipo: str, potencia_instalada_mw: float) -> pd.DataFrame:
    """Uma linha por ano e nível: horas, geração média, energia, máxima, horas paradas, fator de capacidade (EOL e
    UFV, só no nível da usina) e disponibilidade operacional média (só da usina, quando há)."""
    colunas = ["ano", "nivel", "ano_parcial", "horas", "horas_com_valor", "geracao_media_mw", "energia_mwh",
               "geracao_maxima_mw", "horas_paradas", "pct_horas_paradas", "fator_capacidade_pct",
               "disponibilidade_media_mw", "disponibilidade_relativa_pct"]
    linhas = []
    for (ano, nivel), g in base.groupby([base["din_instante"].dt.year, "nivel"], sort=True):
        valores = g["geracao_mw"].dropna()
        da_usina = nivel == "usina"
        disp = g["disponibilidade_operacional_mw"].dropna() if da_usina else pd.Series(dtype=float)
        paradas = int((valores <= LIMIAR_GERACAO_PARADA_MW).sum())
        media = _media(valores)
        linhas.append({
            "ano": int(ano), "nivel": nivel, "ano_parcial": _ano_parcial(g, int(ano)), "horas": len(g),
            "horas_com_valor": len(valores), "geracao_media_mw": media, "energia_mwh": float(valores.sum()),
            "geracao_maxima_mw": float(valores.max()) if len(valores) else math.nan,
            "horas_paradas": paradas, "pct_horas_paradas": _pct(paradas, len(valores)),
            "fator_capacidade_pct": (_pct(media, potencia_instalada_mw)
                                     if tipo in TIPOS_COM_FATOR_CAPACIDADE and da_usina else math.nan),
            "disponibilidade_media_mw": _media(disp),
            "disponibilidade_relativa_pct": _pct(_media(disp), potencia_instalada_mw) if len(disp) else math.nan,
        })
    return pd.DataFrame(linhas, columns=colunas)


def serie_diaria_comum(base: pd.DataFrame) -> pd.DataFrame:
    """Médias diárias da geração (por nível) e da disponibilidade operacional (da usina), para a série temporal."""
    dia = base["din_instante"].dt.normalize()
    geracao = base.groupby([dia, "nivel"])["geracao_mw"].mean().rename("geracao_mw").reset_index()
    disp = base[base["nivel"] == "usina"].groupby(dia)["disponibilidade_operacional_mw"].mean()
    geracao["disponibilidade_operacional_mw"] = geracao["din_instante"].map(disp)
    geracao.loc[geracao["nivel"] != "usina", "disponibilidade_operacional_mw"] = math.nan
    return geracao


def geracao_mensal(base: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por mês e nível: horas, horas com valor, geração média e energia."""
    mes = base["din_instante"].dt.to_period("M").dt.to_timestamp()
    tabela = base.groupby([mes, "nivel"]).agg(horas=("din_instante", "size"),
                                              horas_com_valor=("geracao_mw", "count"),
                                              geracao_media_mw=("geracao_mw", "mean"),
                                              energia_mwh=("geracao_mw", "sum")).reset_index()
    return tabela.rename(columns={"din_instante": "mes"})


def sazonalidade(base: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Geração média por mês do ano, por nível, só no nível com os 12 meses distintos (decisão D19).

    Devolve a tabela e os níveis omitidos por falta de meses."""
    linhas, omitidos = [], []
    for nivel, g in base.groupby("nivel", sort=True):
        meses = g["din_instante"].dt.month
        if meses.nunique() < PERIODO_MINIMO_SAZONALIDADE_MESES:
            omitidos.append(str(nivel))
            continue
        tabela = g.groupby(meses).agg(geracao_media_mw=("geracao_mw", "mean"),
                                      anos=("din_instante", lambda s: s.dt.year.nunique()))
        for mes, linha in tabela.iterrows():
            linhas.append({"mes_do_ano": int(mes), "nivel": nivel, "geracao_media_mw": float(linha["geracao_media_mw"]),
                           "anos": int(linha["anos"])})
    return pd.DataFrame(linhas, columns=["mes_do_ano", "nivel", "geracao_media_mw", "anos"]), omitidos


def perfil_horario_comum(base: pd.DataFrame) -> pd.DataFrame:
    """Geração média por hora do dia e nível, no período."""
    tabela = base.groupby([base["din_instante"].dt.hour, "nivel"]).agg(
        geracao_media_mw=("geracao_mw", "mean"), horas=("geracao_mw", "count")).reset_index()
    return tabela.rename(columns={"din_instante": "hora"})


# ---------------------------------------------------------------------------
# Disponibilidade (sempre da usina)
# ---------------------------------------------------------------------------


def _com_disponibilidade(base: pd.DataFrame) -> pd.DataFrame:
    return base[(base["nivel"] == "usina") & base["disponibilidade_operacional_mw"].notna()].copy()


def _resumo_disponibilidade(j: pd.DataFrame, freq: str) -> pd.DataFrame:
    j = j.assign(periodo=j["din_instante"].dt.to_period(freq).astype(str))
    parada = j["geracao_mw"] <= LIMIAR_GERACAO_PARADA_MW
    j["_indisponivel"] = j["disponibilidade_operacional_mw"] <= LIMIAR_INDISPONIBILIDADE_TOTAL_MW
    j["_parada_disponivel"] = parada & ~j["_indisponivel"]
    j["_parada_sincronizada"] = parada & (j["disponibilidade_sincronizada_mw"] > LIMIAR_SINCRONIZADA_MW)
    j["_acima"] = j["sinalizacoes"].fillna("").str.split(",").map(lambda c: "R7" in c)
    j["_nao_sincronizada"] = j["disponibilidade_operacional_mw"] - j["disponibilidade_sincronizada_mw"]
    resumo = j.groupby("periodo").agg(
        horas_comuns=("din_instante", "size"),
        disp_operacional_media_mw=("disponibilidade_operacional_mw", "mean"),
        disp_sincronizada_media_mw=("disponibilidade_sincronizada_mw", "mean"),
        geracao_media_mw=("geracao_mw", "mean"),
        capacidade_nao_sincronizada_media_mw=("_nao_sincronizada", "mean"),
        horas_indisponibilidade_total=("_indisponivel", "sum"),
        horas_paradas_disponivel=("_parada_disponivel", "sum"),
        horas_paradas_sincronizadas=("_parada_sincronizada", "sum"),
        horas_geracao_acima_disponibilidade=("_acima", "sum"),
    ).reset_index()
    for coluna in ("horas_indisponibilidade_total", "horas_paradas_disponivel", "horas_paradas_sincronizadas",
                   "horas_geracao_acima_disponibilidade"):
        resumo[coluna] = resumo[coluna].astype(int)
    return resumo


def disponibilidade_comum(base: pd.DataFrame, potencia_instalada_mw: float,
                          anos_parciais: List[int]) -> Dict[str, Any]:
    """Disponibilidade operacional e sincronizada × geração da usina: resumos mensal e anual, eventos de
    indisponibilidade total (base da C10) e horas com geração acima da disponibilidade (regra R7, base da C8)."""
    j = _com_disponibilidade(base)
    if j.empty:
        return {}
    anual = _resumo_disponibilidade(j, "Y")
    anual["ano_parcial"] = anual["periodo"].isin({str(a) for a in anos_parciais})
    anual["disponibilidade_relativa_pct"] = anual["disp_operacional_media_mw"] / potencia_instalada_mw * 100.0
    eventos = identificar_eventos(
        j, j["disponibilidade_operacional_mw"] <= LIMIAR_INDISPONIBILIDADE_TOTAL_MW,
        {"geracao_media_mw": ("geracao_mw", "mean")})
    return {
        "resumo": {
            "inicio": j["din_instante"].min(), "fim": j["din_instante"].max(), "horas": len(j),
            "disp_operacional_media_mw": _media(j["disponibilidade_operacional_mw"]),
            "disp_sincronizada_media_mw": _media(j["disponibilidade_sincronizada_mw"]),
            "disponibilidade_relativa_pct": _pct(_media(j["disponibilidade_operacional_mw"]), potencia_instalada_mw),
            "horas_indisponibilidade_total": int(anual["horas_indisponibilidade_total"].sum()),
            "horas_geracao_acima_disponibilidade": int(anual["horas_geracao_acima_disponibilidade"].sum()),
            "eventos_indisponibilidade_total": len(eventos),
        },
        "mensal": _resumo_disponibilidade(j, "M"),
        "anual": anual,
        "eventos_indisponibilidade_total": eventos,
    }


# ---------------------------------------------------------------------------
# Programação diária × geração verificada (no mesmo nível)
# ---------------------------------------------------------------------------


def base_programacao_conjunto(geracao: pd.DataFrame, programada: pd.DataFrame) -> pd.DataFrame:
    """Geração verificada e programada do conjunto, hora a hora, para a comparação com a Programação diária quando a base
    horária é da usina (EOL e UFV com a restrição com detalhe como série de referência): os números do
    conjunto ficam fora da base da usina e levam o nível."""
    g = geracao[["din_instante", "val_geracao"]].assign(din_instante=pd.to_datetime(geracao["din_instante"]))
    p = programada[["din_instante", "geracao_programada_mw"]].assign(
        din_instante=pd.to_datetime(programada["din_instante"])).drop_duplicates("din_instante")
    j = g.merge(p, on="din_instante", how="left")
    return pd.DataFrame({"din_instante": j["din_instante"], "nivel": "conjunto",
                         "geracao_mw": pd.to_numeric(j["val_geracao"], errors="coerce"),
                         "geracao_programada_mw": pd.to_numeric(j["geracao_programada_mw"], errors="coerce")})


def programacao_comum(base: pd.DataFrame, nivel_programacao: str, dias_ausentes: Optional[pd.DataFrame] = None
                      ) -> Dict[str, Any]:
    """Geração programada × verificada nas horas comuns do mesmo nível; vazio sem horas comuns."""
    j = base[(base["nivel"] == nivel_programacao) & base["geracao_programada_mw"].notna()
             & base["geracao_mw"].notna()].copy()
    if j.empty:
        return {}
    j["desvio_mw"] = j["geracao_mw"] - j["geracao_programada_mw"]
    j["desvio_programacao"] = ((j["geracao_mw"] <= LIMIAR_GERACAO_PARADA_MW)
                               & (j["geracao_programada_mw"] > LIMIAR_DESVIO_PROGRAMACAO_MW))
    mes = j["din_instante"].dt.to_period("M").dt.to_timestamp()
    mensal = j.groupby(mes).agg(
        horas_comuns=("din_instante", "size"),
        geracao_media_mw=("geracao_mw", "mean"),
        programada_media_mw=("geracao_programada_mw", "mean"),
        desvio_medio_mw=("desvio_mw", "mean"),
        desvio_medio_absoluto_mw=("desvio_mw", lambda s: float(s.abs().mean())),
        horas_desvio_programacao=("desvio_programacao", "sum"),
    ).reset_index().rename(columns={"din_instante": "mes"})
    mensal["horas_desvio_programacao"] = mensal["horas_desvio_programacao"].astype(int)
    eventos = identificar_eventos(j, j["desvio_programacao"], {"programacao_media_mw": ("geracao_programada_mw", "mean")})
    dias = dias_ausentes if dias_ausentes is not None else pd.DataFrame()
    return {
        "nivel": nivel_programacao,
        "resumo": {
            "inicio": j["din_instante"].min(), "fim": j["din_instante"].max(), "horas_comuns": len(j),
            "geracao_media_mw": _media(j["geracao_mw"]), "programada_media_mw": _media(j["geracao_programada_mw"]),
            "desvio_medio_mw": _media(j["desvio_mw"]), "desvio_medio_absoluto_mw": _media(j["desvio_mw"].abs()),
            # série constante (desvio padrão nulo): correlação indefinida, sem divisão por zero
            "correlacao": float(j["geracao_mw"].corr(j["geracao_programada_mw"]))
            if len(j) > 1 and j["geracao_mw"].std() > 0 and j["geracao_programada_mw"].std() > 0 else math.nan,
            "horas_desvio_programacao": int(j["desvio_programacao"].sum()), "eventos_desvio": len(eventos),
            "dias_ausentes": len(dias),
        },
        "mensal": mensal,
        "eventos": eventos,
    }


# ---------------------------------------------------------------------------
# Qualidade dos dados
# ---------------------------------------------------------------------------


def qualidade_comum(base: pd.DataFrame, ausencias: Optional[pd.DataFrame], linhas_usina_sem_valor: int,
                    linhas_usina_sem_valor_periodo: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Horas sinalizadas por código, horas sem valor, ausências listadas e linhas próprias sem valor (plano da Coleta
    de dados, D21), com o período delas."""
    codigos = base["sinalizacoes"].fillna("").str.split(",").explode()
    contagem = codigos[codigos != ""].value_counts()
    sinalizacoes = pd.DataFrame([{"codigo": c, "descricao": DESCRICAO_SINALIZACOES.get(c, c), "horas": int(n)}
                                 for c, n in sorted(contagem.items())], columns=["codigo", "descricao", "horas"])
    return {
        "sinalizacoes": sinalizacoes,
        "horas_sinalizadas": int((base["sinalizacoes"].fillna("") != "").sum()),
        "horas_sem_valor": int(base["geracao_mw"].isna().sum()),
        "ausencias": ausencias if ausencias is not None else pd.DataFrame(columns=["tipo", "inicio", "fim", "horas"]),
        "linhas_usina_sem_valor": int(linhas_usina_sem_valor),
        "linhas_usina_sem_valor_periodo": dict(linhas_usina_sem_valor_periodo or {}),
    }


# ---------------------------------------------------------------------------
# Agente atual (decisão do usuário de 19/10/2026; spec da Geração do relatório, FR-057)
# ---------------------------------------------------------------------------


def _ativa_em(desativacao: object, fim: pd.Timestamp) -> bool:
    texto = str(desativacao if desativacao is not None else "").strip()[:10]
    if not texto or texto in DATAS_SENTINELA or texto.lower() in ("nan", "none", "nat"):
        return True
    data = pd.to_datetime(texto, errors="coerce", dayfirst="/" in texto)
    return pd.isna(data) or data > fim


def agentes_atuais(capacidade: Optional[pd.DataFrame], fim: pd.Timestamp) -> Dict[str, List[str]]:
    """Agentes proprietário e operador das unidades ativas no fim do período, como a Capacidade de geração os traz
    hoje (sem período: não é o histórico dos agentes); vazio sem a ficha."""
    if capacidade is None or not len(capacidade) or "nom_agenteproprietario" not in capacidade.columns:
        return {}
    ativas = capacidade[capacidade["dat_desativacao"].map(lambda d: _ativa_em(d, fim))] \
        if "dat_desativacao" in capacidade.columns else capacidade
    saida = {}
    for papel, coluna in (("proprietario", "nom_agenteproprietario"), ("operador", "nom_agenteoperador")):
        if coluna in ativas.columns:
            nomes = [str(n).strip() for n in ativas[coluna] if str(n).strip() and str(n).lower() != "nan"]
            saida[papel] = list(dict.fromkeys(nomes))
    return saida if any(saida.values()) else {}


# ---------------------------------------------------------------------------
# Montagem
# ---------------------------------------------------------------------------


def _omitido(item: str, motivo: str, tipo: str = "secao") -> Dict[str, str]:
    return {"item": item, "tipo": tipo, "motivo": motivo}


def _cobertura_texto(perfil: Any, chave: str) -> str:
    valor = (getattr(perfil, "cobertura", None) or {}).get(chave)
    valor = ", ".join(valor) if isinstance(valor, (list, tuple)) else valor
    return f"cobertura: {valor or 'não declarada'}"


def omissoes(perfil: Any, tipo: str, comum: Dict[str, Any], indicadores: bool, hidrologia: bool,
             niveis_sem_sazonalidade: List[str], conjunto: bool = False,
             hidrologia_presente: bool = False) -> List[Dict[str, str]]:
    """Seções da decisão D16 sem base para a usina, com o motivo (FR-005), na ordem do relatório.

    ``conjunto`` e ``hidrologia_presente``: a seção do conjunto e a de afluência têm base."""
    saida: List[Dict[str, str]] = []
    com_disponibilidade = tipo in HIDRELETRICAS + TERMICAS
    if com_disponibilidade and not comum.get("disponibilidade"):
        saida.append(_omitido("Disponibilidade e geração por ano",
                              f"sem a Disponibilidade por usina ({_cobertura_texto(perfil, 'disponibilidade')})"))
    if com_disponibilidade and not indicadores:
        saida.append(_omitido("Indicadores oficiais do ONS por unidade geradora",
                              f"sem os Indicadores de desempenho do ONS ({_cobertura_texto(perfil, 'indicadores')})"))
    for nivel in niveis_sem_sazonalidade:
        meses = comum["cobertura"]["meses_distintos"]
        saida.append(_omitido(TITULO_SAZONALIDADE,
                              f"a série do nível {NOME_NIVEL.get(nivel, nivel)} tem menos de "
                              f"{PERIODO_MINIMO_SAZONALIDADE_MESES} meses distintos ({meses})"))
    if tipo in TERMICAS:  # as seções de térmica dependem do despacho; o CVU × CMO, também do CVU e do CMO
        if registro.nivel_coletado(perfil, "despacho") is None:
            saida.append(_omitido("Seções de térmica", "sem a Geração térmica por motivo de despacho "
                                                       f"({_cobertura_texto(perfil, 'despacho')})"))
        elif registro.nivel_coletado(perfil, "cvu") is None:
            saida.append(_omitido("CVU × CMO", f"sem o CVU das usinas térmicas ({_cobertura_texto(perfil, 'cvu')})"))
        elif registro.nivel_coletado(perfil, "cmo") is None:
            saida.append(_omitido("CVU × CMO", "sem o CMO semanal: o perfil não traz o subsistema"))
    if getattr(perfil.identificacao, "id_conjunto", None) and not conjunto:  # usina em conjunto (decisão D22)
        saida.append(_omitido("Composição e geração do conjunto",
                              "sem a Geração por usina do conjunto, ou sem a usina na composição, no período"))
    if not comum.get("programacao"):
        if not comum.get("programacao_coletada"):
            motivo = f"sem a Programação diária ({_cobertura_texto(perfil, 'programacao')})"
        elif not comum.get("programacao_horas"):
            motivo = "a Programação diária não tem horas no período da série de referência"
        else:
            motivo = "sem horas com a programação e a geração verificada no mesmo nível"
        saida.append(_omitido("Programação diária × geração verificada", motivo))
    if com_disponibilidade and not comum.get("disponibilidade"):
        saida.append(_omitido("Disponibilidade operacional e sincronizada",
                              f"sem a Disponibilidade por usina ({_cobertura_texto(perfil, 'disponibilidade')})"))
    if tipo in HIDRELETRICAS and not hidrologia_presente:  # a seção sem os cruzamentos com a EVT (decisão D23)
        saida.append(_omitido("Afluência, vertimento e nível do reservatório",
                              "os Dados hidrológicos não têm horas no período da série de referência" if hidrologia
                              else f"sem os Dados hidrológicos ({_cobertura_texto(perfil, 'hidrologia')})"))
    if tipo in TERMICAS and registro.nivel_coletado(perfil, "despacho") is not None:
        saida.append(_omitido("Conferência da geração entre fontes",
                              "seção ainda não gerada pelo pipeline; os resultados da G3 e da G4 estão nas legendas de "
                              "fonte das seções de térmica e nas abas CONF_G3 e CONF_G4 da planilha"))
    elif tipo in TIPOS_COM_FATOR_CAPACIDADE and any(registro.nivel_coletado(perfil, c) for c in (
            "fator_capacidade", "restricao_detalhe", "restricao_razao")):  # eólicas e solares
        saida.append(_omitido("Conferência da geração entre fontes",
                              "seção ainda não gerada pelo pipeline; os resultados da G1, da G2 e da G5, quando "
                              "aplicáveis, estão nas legendas de fonte das seções de eólica e solar e nas abas CONF_G1, "
                              "CONF_G2 e CONF_G5 da planilha"))
    else:
        saida.append(_omitido("Conferência da geração entre fontes",
                              "nenhuma conferência entre fontes de geração se aplica à usina (ver as conferências não "
                              "aplicáveis)"))
    return saida


def analisar_comum(
    base: pd.DataFrame,
    perfil: Any,
    tipo: str,
    ausencias: Optional[pd.DataFrame] = None,
    linhas_usina_sem_valor: int = 0,
    nivel_programacao: Optional[str] = None,
    dias_ausentes_programacao: Optional[pd.DataFrame] = None,
    horas_programacao: int = 0,
    indicadores: bool = False,
    hidrologia: bool = False,
    base_programacao: Optional[pd.DataFrame] = None,
    linhas_usina_sem_valor_periodo: Optional[Dict[str, str]] = None,
    conjunto: bool = False,
    hidrologia_presente: bool = False,
) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """Campo ``comum`` de ``ResultadosAnalise`` e as omissões das seções (decisões D16 e D19).

    ``nivel_programacao``: nível da Programação diária coletada (None quando não foi coletada); ``horas_programacao``,
    as horas da programação tratada no período; ``base_programacao``, a base da comparação com a programação quando não é
    a base horária (a do conjunto).
    """
    potencia = float(perfil.parametros.potencia_instalada_mw)
    cobertura = cobertura_comum(base, ausencias)
    tabela_sazonal, sem_sazonalidade = sazonalidade(base)
    comum: Dict[str, Any] = {
        "cobertura": cobertura,
        "anuais": indicadores_anuais_comum(base, tipo, potencia),
        "serie_diaria": serie_diaria_comum(base),
        "mensal": geracao_mensal(base),
        "sazonalidade": tabela_sazonal,
        "perfil_horario": perfil_horario_comum(base),
        "disponibilidade": disponibilidade_comum(base, potencia, cobertura["anos_parciais"]),
        "programacao": (programacao_comum(base if base_programacao is None else base_programacao, nivel_programacao,
                                          dias_ausentes_programacao) if nivel_programacao else {}),
        "programacao_coletada": nivel_programacao is not None,
        "programacao_horas": int(horas_programacao),
        "qualidade": qualidade_comum(base, ausencias, linhas_usina_sem_valor, linhas_usina_sem_valor_periodo),
    }
    return comum, omissoes(perfil, tipo, comum, indicadores, hidrologia, sem_sazonalidade, conjunto,
                           hidrologia_presente)
