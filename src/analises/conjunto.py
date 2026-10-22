"""Composição e geração do conjunto de usinas (spec 006, fase D; decisão R20; rascunho 004, FR-060).

Na usina em conjunto, com a Geração por usina do conjunto: a composição em cada trecho de composição (os trechos
consecutivos da Coleta com a mesma composição, juntos), com o nome, o tipo (pelo CEG) e a potência de cada usina no
trecho (unidades da Capacidade de geração em operação em algum momento do trecho), a geração do conjunto por trecho e por
mês e o tipo que o ONS publica na série do conjunto comparado com os tipos da composição. Nenhum número do conjunto é
dividido entre as usinas nem entra na conclusão (princípio VIII), e a geração do conjunto não é dividida pela potência
somada: nenhum fator de capacidade do conjunto é calculado.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.analises.comum import _media
from src.coleta.registro import normalizar_texto
from src.comum.formatacao import fmt_data, fmt_int, fmt_lista, fmt_num, plural
from src.comum.regras import DATAS_SENTINELA, TIPOS_ONS

TITULO_CONJUNTO = "Composição e geração do conjunto"
COLUNAS_TRECHOS = ["trecho", "inicio", "fim", "usinas", "tipos", "horas", "horas_com_valor", "energia_mwh",
                   "geracao_media_mw", "geracao_maxima_mw", "potencia_somada_mw", "usinas_sem_potencia"]
COLUNAS_COMPOSICAO = ["trecho", "ceg", "usina", "tipo", "entrada", "saida", "unidades", "potencia_mw"]
COLUNAS_TIPO_PUBLICADO = ["trecho", "inicio", "fim", "tipo_publicado", "combustivel_publicado", "horas",
                          "tipos_composicao", "corresponde"]


def _data(valor: Any) -> Optional[pd.Timestamp]:
    """Data de um cadastral; vazia, inválida ou sentinela vale None."""
    texto = str(valor if valor is not None else "").strip()[:10]
    if not texto or texto in DATAS_SENTINELA or texto.lower() in ("nan", "none", "nat"):
        return None
    data = pd.to_datetime(texto, errors="coerce", dayfirst="/" in texto)
    return None if pd.isna(data) else pd.Timestamp(data)


def trechos_de_composicao(trechos: pd.DataFrame) -> pd.DataFrame:
    """Os trechos da Coleta (``trechos.csv``) juntos quando a composição não muda: ``trecho`` (1, 2, ...), ``inicio``,
    ``fim``, ``composicao`` (CEGs) e ``tipos``."""
    colunas = ["trecho", "inicio", "fim", "composicao", "tipos"]
    if trechos is None or not len(trechos) or "composicao" not in trechos.columns:
        return pd.DataFrame(columns=colunas)
    t = trechos.sort_values("inicio", key=lambda s: pd.to_datetime(s), kind="stable").reset_index(drop=True)
    grupo = t["composicao"].astype(str).ne(t["composicao"].astype(str).shift()).cumsum()
    linhas = [{"trecho": int(n), "inicio": pd.Timestamp(g["inicio"].iloc[0]), "fim": pd.Timestamp(g["fim"].iloc[-1]),
               "composicao": str(g["composicao"].iloc[0]), "tipos": str(g["tipos_composicao"].iloc[0])}
              for n, g in t.groupby(grupo, sort=True)]
    return pd.DataFrame(linhas, columns=colunas)


def _trecho_de_cada_hora(instantes: pd.Series, composicoes: pd.DataFrame) -> pd.Series:
    saida = pd.Series(pd.NA, index=instantes.index, dtype="Int64")
    for linha in composicoes.to_dict("records"):
        saida[(instantes >= linha["inicio"]) & (instantes <= linha["fim"]) & saida.isna()] = int(linha["trecho"])
    return saida


def _unidades_no_trecho(capacidade: Optional[pd.DataFrame], ceg: str, inicio: pd.Timestamp,
                        fim: pd.Timestamp) -> Tuple[int, float]:
    """Unidades da usina em operação em algum momento do trecho e a soma da potência efetiva delas."""
    if capacidade is None or not len(capacidade):
        return 0, math.nan
    u = capacidade[[normalizar_texto(c) == normalizar_texto(ceg) for c in capacidade["ceg"]]]
    entradas = [_data(d) for d in u.get("dat_entradaoperacao", pd.Series([None] * len(u)))]
    saidas = [_data(d) for d in u.get("dat_desativacao", pd.Series([None] * len(u)))]
    ativas = [(e is None or e <= fim) and (s is None or s > inicio) for e, s in zip(entradas, saidas)]
    potencias = pd.to_numeric(u.loc[ativas, "val_potenciaefetiva"].astype(str).str.replace(",", "."), errors="coerce")
    return int(sum(ativas)), (float(potencias.sum()) if any(ativas) else math.nan)


def _composicao(composicoes: pd.DataFrame, membros: pd.DataFrame,
                capacidade: Optional[pd.DataFrame]) -> pd.DataFrame:
    linhas = []
    for c in composicoes.to_dict("records"):
        cegs = [x for x in str(c["composicao"]).split(";") if x]
        for ceg in cegs:
            m = membros[membros["ceg"].map(normalizar_texto) == normalizar_texto(ceg)]
            m = m.iloc[0] if len(m) else {}
            unidades, potencia = _unidades_no_trecho(capacidade, ceg, c["inicio"], c["fim"])
            linhas.append({"trecho": c["trecho"], "ceg": ceg, "usina": str(m.get("nom_usina", "") or ""),
                           "tipo": str(m.get("tipo", "") or ""), "entrada": str(m.get("inicio", "") or ""),
                           "saida": str(m.get("fim", "") or ""), "unidades": unidades, "potencia_mw": potencia})
    tabela = pd.DataFrame(linhas, columns=COLUNAS_COMPOSICAO)
    # dentro do trecho: hidrelétricas, térmicas e as demais, como a composição as traz; depois pelo nome
    return tabela.sort_values(["trecho", "tipo", "usina"], kind="stable").reset_index(drop=True)


def _geracao_por_trecho(serie: pd.DataFrame, composicoes: pd.DataFrame, tabela_composicao: pd.DataFrame,
                        com_capacidade: bool) -> pd.DataFrame:
    linhas = []
    for c in composicoes.to_dict("records"):
        g = serie[serie["trecho_composicao"] == c["trecho"]]
        valores = g["geracao_mw"].dropna()
        membros = tabela_composicao[tabela_composicao["trecho"] == c["trecho"]]
        sem_potencia = int(membros["potencia_mw"].isna().sum())
        linhas.append({
            "trecho": c["trecho"], "inicio": g["din_instante"].min() if len(g) else c["inicio"],
            "fim": g["din_instante"].max() if len(g) else c["fim"], "usinas": len(membros), "tipos": c["tipos"],
            "horas": len(g), "horas_com_valor": len(valores), "energia_mwh": float(valores.sum()),
            "geracao_media_mw": _media(valores), "geracao_maxima_mw": float(valores.max()) if len(valores) else math.nan,
            "potencia_somada_mw": (float(membros["potencia_mw"].sum(min_count=1)) if com_capacidade else math.nan),
            "usinas_sem_potencia": sem_potencia if com_capacidade else len(membros),
        })
    return pd.DataFrame(linhas, columns=COLUNAS_TRECHOS)


def _tipo_publicado(tipo_publicado: Optional[pd.DataFrame], trechos: pd.DataFrame,
                    composicoes: pd.DataFrame) -> pd.DataFrame:
    """O tipo publicado de cada trecho da Coleta, levado ao trecho de composição, e se corresponde a algum tipo da
    composição (pelo CEG, decisão R1)."""
    if tipo_publicado is None or not len(tipo_publicado):
        return pd.DataFrame(columns=COLUNAS_TIPO_PUBLICADO)
    inicio_de = dict(zip(trechos["trecho"].astype(int), pd.to_datetime(trechos["inicio"])))
    linhas = []
    for r in tipo_publicado.to_dict("records"):
        inicio = inicio_de.get(int(r["trecho"]))
        c = composicoes[(composicoes["inicio"] <= inicio) & (composicoes["fim"] >= inicio)] if inicio is not None \
            else composicoes.iloc[0:0]
        if not len(c):
            continue
        c = c.iloc[0]
        tipos = [t for t in str(c["tipos"]).split(";") if t]
        do_ons = TIPOS_ONS.get(normalizar_texto(r["nom_tipousina"]).replace(" ", ""), ())
        linhas.append({"trecho": int(c["trecho"]), "inicio": pd.Timestamp(r["inicio"]), "fim": pd.Timestamp(r["fim"]),
                       "tipo_publicado": str(r["nom_tipousina"]), "combustivel_publicado": str(r["nom_tipocombustivel"]),
                       "horas": int(r["horas"]), "tipos_composicao": ";".join(tipos),
                       "corresponde": (not do_ons) or any(t in do_ons for t in tipos)})
    tabela = pd.DataFrame(linhas, columns=COLUNAS_TIPO_PUBLICADO)
    if not len(tabela):
        return tabela
    # um registro por trecho de composição e tipo publicado, com o período e as horas somados
    return tabela.groupby(["trecho", "tipo_publicado", "combustivel_publicado", "tipos_composicao", "corresponde"],
                          as_index=False, sort=True).agg(inicio=("inicio", "min"), fim=("fim", "max"),
                                                         horas=("horas", "sum"))[COLUNAS_TIPO_PUBLICADO]


COLUNAS_PESO = ["trecho", "inicio", "fim", "potencia_usina_mw", "potencia_somada_mw", "peso_pct"]


def peso_da_usina(trechos: pd.DataFrame, composicao: pd.DataFrame, ceg: str) -> pd.DataFrame:
    """Peso da usina na potência do conjunto em cada trecho de composição (decisão do usuário de 22/10/2026): a
    potência das unidades dela em operação no trecho ÷ a potência somada. Nunca estima a geração da usina."""
    if not ceg or not len(trechos):
        return pd.DataFrame(columns=COLUNAS_PESO)
    da_usina = composicao[composicao["ceg"].map(normalizar_texto) == normalizar_texto(ceg)].set_index("trecho")
    linhas = []
    for r in trechos.itertuples():
        potencia = float(da_usina.loc[r.trecho, "potencia_mw"]) if r.trecho in da_usina.index else math.nan
        peso = potencia / r.potencia_somada_mw * 100.0 if pd.notna(potencia) and r.potencia_somada_mw else math.nan
        linhas.append({"trecho": r.trecho, "inicio": r.inicio, "fim": r.fim, "potencia_usina_mw": potencia,
                       "potencia_somada_mw": r.potencia_somada_mw, "peso_pct": peso})
    return pd.DataFrame(linhas, columns=COLUNAS_PESO)


def em_duas_partes(res: Any) -> bool:
    """Relatório em duas partes (rascunho 005, FR-048): a usina em conjunto em que todos os números de operação são
    do conjunto (série de referência = geração do conjunto), com a seção do conjunto calculada."""
    niveis = set(((getattr(res, "comum", None) or {}).get("cobertura") or {}).get("niveis", {}))
    return bool(getattr(res, "conjunto", None)) and niveis == {"conjunto"}


def analisar_conjunto(serie: Optional[pd.DataFrame], trechos: Optional[pd.DataFrame],
                      membros: Optional[pd.DataFrame], capacidade: Optional[pd.DataFrame] = None,
                      tipo_publicado: Optional[pd.DataFrame] = None, id_conjunto: str = "",
                      nome: str = "", ceg_usina: str = "") -> Dict[str, Any]:
    """Campo ``conjunto`` dos resultados (FR-060); vazio sem a geração do conjunto ou sem os trechos.

    ``serie``: a geração do conjunto hora a hora (``din_instante``, ``geracao_mw``), só as horas do nível do conjunto;
    ``trechos``: ``trechos.csv``; ``membros``: ``composicao_conjunto.csv``; ``capacidade``: ``capacidade_membros.csv``
    (ausente nas Coletas anteriores à fase D: a composição sai sem a potência); ``tipo_publicado``: ``tipo_publicado.csv``.
    """
    if serie is None or not len(serie) or trechos is None or not len(trechos) or membros is None or not len(membros):
        return {}
    composicoes = trechos_de_composicao(trechos)
    if not len(composicoes):
        return {}
    s = serie[["din_instante", "geracao_mw"]].assign(din_instante=pd.to_datetime(serie["din_instante"]))
    s = s.assign(trecho_composicao=_trecho_de_cada_hora(s["din_instante"], composicoes)).dropna(
        subset=["trecho_composicao"])
    if not len(s):
        return {}
    com_capacidade = capacidade is not None and "ceg" in getattr(capacidade, "columns", ())
    tabela_composicao = _composicao(composicoes, membros, capacidade if com_capacidade else None)
    por_trecho = _geracao_por_trecho(s, composicoes, tabela_composicao, com_capacidade)
    mes = s["din_instante"].dt.to_period("M").dt.to_timestamp()
    mensal = s.groupby([mes, "trecho_composicao"]).agg(
        horas_com_valor=("geracao_mw", "count"), geracao_media_mw=("geracao_mw", "mean"),
        energia_mwh=("geracao_mw", "sum")).reset_index().rename(columns={"din_instante": "mes",
                                                                         "trecho_composicao": "trecho"})
    mensal["trecho"] = mensal["trecho"].astype(int)
    tipos = _tipo_publicado(tipo_publicado, trechos, composicoes)
    return {
        "id": id_conjunto, "nome": nome, "nivel": "conjunto", "com_capacidade": com_capacidade,
        "trechos": por_trecho, "composicao": tabela_composicao, "mensal": mensal, "tipo_publicado": tipos,
        "peso_usina": peso_da_usina(por_trecho, tabela_composicao, ceg_usina) if com_capacidade else pd.DataFrame(
            columns=COLUNAS_PESO),
        "resumo": {"inicio": s["din_instante"].min(), "fim": s["din_instante"].max(), "composicoes": len(por_trecho),
                   "horas_com_valor": int(s["geracao_mw"].notna().sum()),
                   "trechos_tipo_divergente": int((~tipos["corresponde"].astype(bool)).sum()) if len(tipos) else 0},
    }


# ---------------------------------------------------------------------------
# Constatação
# ---------------------------------------------------------------------------

MAXIMO_TRECHOS_NA_CONSTATACAO = 5


def _tipos_texto(tipos: str) -> str:
    return fmt_lista([t for t in str(tipos).split(";") if t])


def achados_conjunto(c: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Constatação da seção do conjunto: a composição em cada trecho e a geração do conjunto, sempre "do conjunto";
    a divergência do tipo publicado, quando há (fatos, sem causa; princípio II)."""
    if not c:
        return []
    nome = f" {c['nome']}" if c.get("nome") else ""
    t = c["trechos"]
    partes = [f"de {fmt_data(r.inicio)} a {fmt_data(r.fim)}, {fmt_int(r.usinas)} "
              f"{plural(r.usinas, 'usina', 'usinas')} ({_tipos_texto(r.tipos)}), geração média do conjunto de "
              f"{fmt_num(r.geracao_media_mw, 1)} MWmed" for r in t.head(MAXIMO_TRECHOS_NA_CONSTATACAO).itertuples()]
    if len(t) > MAXIMO_TRECHOS_NA_CONSTATACAO:
        partes.append(f"e mais {fmt_int(len(t) - MAXIMO_TRECHOS_NA_CONSTATACAO)} composições, na planilha")
    texto = (f"O conjunto{nome} ({c['id']}) teve {fmt_int(len(t))} {plural(len(t), 'composição', 'composições')} no "
             f"período: {'; '.join(partes)}. Os números são do conjunto, sem divisão entre as usinas.")
    return [("Composição do conjunto", texto)]


def frases_tipo_publicado(c: Dict[str, Any]) -> List[str]:
    """A divergência entre o tipo que o ONS publica na série do conjunto e os tipos da composição, uma frase por
    trecho, para a constatação da qualidade dos dados (caso de borda da spec 006; rascunho 004, FR-060)."""
    tipos = (c or {}).get("tipo_publicado")
    if tipos is None or not len(tipos):
        return []
    return [f"O ONS publica a série do conjunto como {r.tipo_publicado.strip()} ({r.combustivel_publicado.strip()}) de "
            f"{fmt_data(r.inicio)} a {fmt_data(r.fim)}, quando a composição tem só {_tipos_texto(r.tipos_composicao)}; "
            "o tipo das usinas vem do CEG."
            for r in tipos[~tipos["corresponde"].astype(bool)].itertuples()]


def achado_usina_no_conjunto(c: Dict[str, Any], usina: str, potencia_mw: float) -> Tuple[str, str]:
    """Constatação da parte da usina no relatório em duas partes (rascunho 005, FR-048): o peso dela na potência do
    conjunto, por composição, sem estimar a geração dela."""
    nome = f" {c['nome']}" if c.get("nome") else ""
    texto = (f"O ONS publica a geração, a programação e os demais dados de operação do conjunto{nome} ({c['id']}), e "
             f"não os da {usina} isolada.")
    peso = c.get("peso_usina")
    partes = [f"{fmt_num(r.peso_pct, 1)}% de {fmt_data(r.inicio)} a {fmt_data(r.fim)}"
              for r in (peso.itertuples() if peso is not None else ()) if pd.notna(r.peso_pct)]
    if partes:
        texto += (f" Peso da usina ({fmt_num(potencia_mw, 1)} MW) na potência das usinas do conjunto: "
                  f"{fmt_lista(partes)}; esse peso não estima a geração dela.")
    return "A usina no conjunto", texto
