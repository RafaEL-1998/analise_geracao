"""Série de referência, período e trechos da Coleta (spec 006, decisões R6 e R7; data-model, seções 5.1 e 5.2).

A série de referência define o período da análise (princípio IV), pelo tipo e pela cobertura da usina:
- hidrelétrica com Energia Vertida Turbinável: a EVT, pelo caminho de hoje, sem trechos;
- usina com geração própria (``[cobertura] geracao = "proprio"``): a Geração por usina, pelo id ONS;
- usina em conjunto sem série própria (``geracao = "conjunto"``): a Geração por usina do conjunto, pelo id do conjunto;
- com a lista ``["proprio", "conjunto"]``: as duas séries; o período é a união, e cada hora vale pelo nível dela;
- eólica ou solar em conjunto, com série própria na restrição com detalhe (fase C): a geração verificada da usina nessa
  base, semi-horária, pelo id ONS; o complemento e os trechos ficam por hora.

A série é varrida em todos os arquivos publicados, com o filtro do identificador na leitura do Parquet. O período vai
da primeira à última hora com valor preenchido.

Fora das hidrelétricas com EVT, o período é dividido em trechos quando muda a modalidade (hora a hora, na Geração por
usina), o nível do dado, a composição do conjunto ou o código de planejamento da térmica. Só os trechos que mudam o
nível ou a composição são mostrados no relatório (``mostrar``); a mudança só de modalidade ou de código fica na planilha.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from src.coleta import conjuntos, registro
from src.coleta.registro import DescricaoConjunto, normalizar_texto

INICIO_VARREDURA = pd.Timestamp("1990-01-01")  # antes do primeiro arquivo publicado: a varredura não recorta o período
COLUNA_MODALIDADE = "cod_modalidadeoperacao"
COLUNAS_TRECHOS = ["trecho", "inicio", "fim", "modalidade", "id_conjunto", "composicao", "tipos_composicao",
                   "codigos_planejamento", "nivel_geracao", "mostrar"]
FORMATO = "%Y-%m-%d %H:%M:%S"
MOTIVOS = {
    "evt": "UHE, PCH ou CGH com Energia Vertida Turbinável",
    "usina": "geração própria: Geração por usina, pelo id ONS da usina",
    "conjunto": "usina em conjunto, sem série própria: Geração por usina, pelo id do conjunto",
    "usina_conjunto": "a usina mudou de nível no período: Geração por usina, da usina e do conjunto",
    "restricao_detalhe": ("usina em conjunto, com série própria na restrição com detalhe: geração verificada da usina, "
                          "pelo id ONS"),
}
# Coluna da geração na série de referência de cada conjunto
COLUNA_VALOR: Dict[str, str] = {"geracao": "val_geracao", "restricao_detalhe": "val_geracaoverificada"}
COLUNA_MODALIDADE_RESTRICAO = "nom_modalidadeoperacao"


@dataclass(frozen=True)
class Escolha:
    """A série de referência escolhida: o conjunto do registro, os níveis e a linha da decisão R6 que se aplicou."""

    conjunto: str
    niveis: Tuple[str, ...]
    motivo: str


def escolher(perfil: Any) -> Escolha:
    """Série de referência pelo tipo e pela cobertura (decisão R6). Sem nenhuma, ``ValueError``."""
    chaves = [e.chave for e in registro.conjuntos_da_usina(perfil)]
    if "evt" in chaves:
        return Escolha("evt", ("usina",), MOTIVOS["evt"])
    valor = registro.cobertura_da_usina(perfil).get("geracao")
    valores = valor if isinstance(valor, (list, tuple)) else [valor]
    niveis = tuple(registro.NIVEL_DA_COBERTURA[v] for v in ("proprio", "conjunto") if v in valores)
    if ("usina" not in niveis and "restricao_detalhe" in chaves
            and registro.nivel_coletado(perfil, "restricao_detalhe") == "usina"):  # linha da fase C da decisão R6
        return Escolha("restricao_detalhe", ("usina",), MOTIVOS["restricao_detalhe"])
    if "geracao" not in chaves or not niveis:
        raise ValueError(f"a usina '{perfil.usina.slug}' não tem série de referência: nem a Energia Vertida Turbinável "
                         "nem a Geração por usina (da usina ou do conjunto) na [cobertura]")
    return Escolha("geracao", niveis, MOTIVOS["_".join(niveis)])


def descricoes_referencia(perfil: Any, escolha: Escolha) -> Dict[str, DescricaoConjunto]:
    """Descrições da série em cada nível, com a modalidade por hora (para os trechos): a Geração por usina ou, na linha
    da fase C, a restrição com detalhe da usina."""
    if escolha.conjunto == "restricao_detalhe":
        return {"usina": replace(registro.descricao_restricao_detalhe(perfil), chave="restricao_detalhe",
                                 nivel="usina", referencia=True, resolucao="semi_horaria")}
    if escolha.conjunto != "geracao":
        return {}
    return {nivel: replace(registro.descricao_geracao(perfil, nivel), chave="geracao", nivel=nivel, referencia=True,
                           colunas_texto=(COLUNA_MODALIDADE,))
            for nivel in escolha.niveis}


def extrair_referencia(perfil: Any, escolha: Escolha, pasta_raw: Path,
                       falhas: Optional[List[Dict[str, Any]]] = None) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
    """Linhas da série em todos os arquivos locais (sem recorte de período), por nível, e a auditoria da varredura."""
    series: Dict[str, pd.DataFrame] = {}
    auditorias = []
    fim = pd.Timestamp.today().normalize() + pd.DateOffset(years=1)
    for nivel, desc in descricoes_referencia(perfil, escolha).items():
        pasta = Path(pasta_raw) / desc.pasta
        extraido, auditoria = conjuntos.extrair_conjunto(desc, pasta, INICIO_VARREDURA, fim, falhas)
        series[nivel] = extraido
        auditorias.append(auditoria.assign(nivel=nivel))
    auditoria = pd.concat(auditorias, ignore_index=True) if auditorias else pd.DataFrame()
    return series, auditoria


def periodo(series: Dict[str, pd.DataFrame], coluna: str = "val_geracao") -> Tuple[Optional[pd.Timestamp],
                                                                                    Optional[pd.Timestamp]]:
    """Primeira e última hora com valor, na união das séries; (None, None) sem nenhuma hora com valor."""
    instantes = [pd.to_datetime(t.loc[t[coluna].notna(), "din_instante"]) for t in series.values()
                 if len(t) and coluna in t.columns]
    instantes = [i for i in instantes if len(i)]
    if not instantes:
        return None, None
    todos = pd.concat(instantes)
    return pd.Timestamp(todos.min()), pd.Timestamp(todos.max())


def complemento(series: Dict[str, pd.DataFrame], coluna: str = "val_geracao", semi_horaria: bool = False
                ) -> pd.DataFrame:
    """Modalidade e nível de cada hora: o da usina quando ela tem valor; senão, o do conjunto (decisão R7). Na série
    semi-horária (restrição com detalhe), uma linha por hora cheia, a da primeira meia-hora com valor."""
    partes = []
    for ordem, nivel in enumerate(("usina", "conjunto")):
        t = series.get(nivel)
        if t is None or not len(t):
            continue
        modalidade = t[COLUNA_MODALIDADE] if COLUNA_MODALIDADE in t.columns else \
            t.get(COLUNA_MODALIDADE_RESTRICAO, pd.Series("", index=t.index))
        instantes = pd.to_datetime(t["din_instante"])
        partes.append(pd.DataFrame({"din_instante": instantes.dt.floor("h") if semi_horaria else instantes,
                                    COLUNA_MODALIDADE: modalidade.fillna(""),
                                    "nivel": nivel, "_com_valor": t[coluna].notna(), "_ordem": ordem}))
    if not partes:
        return pd.DataFrame(columns=["din_instante", COLUNA_MODALIDADE, "nivel"])
    todas = pd.concat(partes, ignore_index=True)
    todas = todas.sort_values(["din_instante", "_com_valor", "_ordem"], ascending=[True, False, True], kind="stable")
    return todas.drop_duplicates("din_instante", keep="first")[["din_instante", COLUNA_MODALIDADE, "nivel"]] \
        .reset_index(drop=True)


def combinar(series: Dict[str, pd.DataFrame], inicio: Optional[pd.Timestamp], fim: Optional[pd.Timestamp],
             coluna: str = "val_geracao") -> pd.DataFrame:
    """``geracao_extraido.parquet`` das usinas sem EVT: uma linha por hora do período, a da usina quando ela tem valor,
    senão a do conjunto, com as colunas de hoje (sem as colunas de texto)."""
    partes = []
    for ordem, nivel in enumerate(("usina", "conjunto")):
        t = series.get(nivel)
        if t is not None and len(t):
            partes.append(t.assign(_com_valor=t[coluna].notna(), _ordem=ordem))
    colunas = ["din_instante", coluna, conjuntos.COLUNA_NAO_NUMERICO, "arquivo_origem"]
    if not partes or inicio is None:
        return pd.DataFrame(columns=colunas)
    todas = pd.concat(partes, ignore_index=True)
    todas["din_instante"] = pd.to_datetime(todas["din_instante"])
    todas = todas[(todas["din_instante"] >= inicio) & (todas["din_instante"] <= fim)]
    todas = todas.sort_values(["din_instante", "_com_valor", "_ordem"], ascending=[True, False, True], kind="stable")
    return todas.drop_duplicates("din_instante", keep="first")[colunas].reset_index(drop=True)


def recortar(serie: pd.DataFrame, inicio: Optional[pd.Timestamp], fim: Optional[pd.Timestamp]) -> pd.DataFrame:
    """A série no período, com todas as colunas extraídas (a restrição com detalhe como série de referência)."""
    if serie is None or not len(serie) or inicio is None:
        return serie.iloc[0:0] if serie is not None else pd.DataFrame()
    instantes = pd.to_datetime(serie["din_instante"])
    return serie[(instantes >= inicio) & (instantes <= fim)].reset_index(drop=True)


def resumo(escolha: Escolha, perfil: Any, inicio: Optional[pd.Timestamp], fim: Optional[pd.Timestamp],
           auditoria: pd.DataFrame) -> Dict[str, Any]:
    """Resumo da série de referência para o ``etapa.json`` da Coleta (data-model 5.1)."""
    ident = perfil.identificacao
    if escolha.conjunto == "evt":
        identificador = f"cod_usina={ident.cod_usina}"
    elif escolha.conjunto == "restricao_detalhe":
        identificador = f"id_ons={ident.id_ons}"
    else:
        valores = [ident.id_ons if nivel == "usina" else ident.id_conjunto for nivel in escolha.niveis]
        identificador = "id_ons=" + ";".join(str(v) for v in valores)
    arquivos = int(auditoria["arquivo"].nunique()) if "arquivo" in auditoria.columns else 0
    return {"conjunto": escolha.conjunto, "identificador": identificador,
            "inicio": inicio.strftime(FORMATO) if inicio is not None else "",
            "fim": fim.strftime(FORMATO) if fim is not None else "", "arquivos_varridos": arquivos,
            "motivo": escolha.motivo}


# ---------------------------------------------------------------------------
# Trechos
# ---------------------------------------------------------------------------


def _data(texto: Any) -> Optional[pd.Timestamp]:
    texto = str(texto or "").strip()
    if not texto:
        return None
    try:
        return pd.Timestamp(texto)
    except ValueError:
        return None


def _membros_em(composicao: pd.DataFrame, t: pd.Timestamp) -> pd.DataFrame:
    if composicao.empty:
        return composicao
    inicio = composicao["inicio"].map(_data)
    fim = composicao["fim"].map(_data)
    ativo = inicio.map(lambda d: pd.isna(d) or d <= t) & fim.map(lambda d: pd.isna(d) or t < d)  # vazio vira NaT
    return composicao[ativo]


def _mes(texto: Any) -> Optional[pd.Period]:
    texto = str(texto or "").strip()
    return pd.Period(texto, freq="M") if texto else None


def _codigos_em(planejamento: Sequence[Any], t: pd.Timestamp) -> List[str]:
    mes = pd.Period(t, freq="M")
    vigentes = []
    for p in planejamento:
        inicio, fim = _mes(getattr(p, "inicio", "")), _mes(getattr(p, "fim", ""))
        if (inicio is None or inicio <= mes) and (fim is None or mes <= fim):
            vigentes.append(str(getattr(p, "codigo")))
    return sorted(dict.fromkeys(vigentes), key=lambda c: (len(c), c))


def trechos(complemento_horario: pd.DataFrame, composicao: pd.DataFrame, planejamento: Sequence[Any],
            id_conjunto: str) -> pd.DataFrame:
    """``trechos.csv``: um trecho por intervalo sem mudança de modalidade, nível, composição nem código (data-model 5.2).

    ``mostrar`` é verdadeiro no trecho cujo nível ou composição difere do anterior ou do seguinte.
    """
    if complemento_horario.empty:
        return pd.DataFrame(columns=COLUNAS_TRECHOS)
    comp = complemento_horario.sort_values("din_instante").reset_index(drop=True)
    instantes = pd.to_datetime(comp["din_instante"])
    inicio, fim = instantes.iloc[0], instantes.iloc[-1]
    composicao = composicao if composicao.empty or not id_conjunto else \
        composicao[composicao["id_conjunto"].astype(str) == id_conjunto]
    cortes = {inicio}
    chave = comp[COLUNA_MODALIDADE].map(normalizar_texto) + "|" + comp["nivel"].astype(str)
    mudou = chave.ne(chave.shift())
    cortes |= set(instantes[mudou])
    for coluna in ("inicio", "fim"):
        for d in composicao[coluna].map(_data) if not composicao.empty else []:
            if not pd.isna(d) and inicio < d <= fim:
                cortes.add(d.normalize())
    for p in planejamento:  # o código vale do primeiro dia do mês de início ao último do mês de fim
        comeco, termino = _mes(getattr(p, "inicio", "")), _mes(getattr(p, "fim", ""))
        for d in (comeco.start_time if comeco is not None else None,
                  (termino + 1).start_time if termino is not None else None):
            if d is not None and inicio < d <= fim:
                cortes.add(d)
    ordenados = sorted(cortes)
    linhas = []
    for i, corte in enumerate(ordenados):
        proximo = ordenados[i + 1] if i + 1 < len(ordenados) else None
        no_trecho = comp[(instantes >= corte) & ((instantes < proximo) if proximo is not None else True)]
        if no_trecho.empty:
            continue
        membros = _membros_em(composicao, corte)
        linhas.append({
            "inicio": pd.Timestamp(no_trecho["din_instante"].iloc[0]).strftime(FORMATO),
            "fim": pd.Timestamp(no_trecho["din_instante"].iloc[-1]).strftime(FORMATO),
            "modalidade": str(no_trecho[COLUNA_MODALIDADE].iloc[0]),
            "id_conjunto": id_conjunto or "",
            "composicao": ";".join(sorted(membros["ceg"].astype(str))) if len(membros) else "",
            "tipos_composicao": ";".join(sorted(set(membros["tipo"].astype(str)))) if len(membros) else "",
            "codigos_planejamento": ";".join(_codigos_em(planejamento, corte)),
            "nivel_geracao": str(no_trecho["nivel"].iloc[0]),
        })
    tabela = pd.DataFrame(linhas)
    assinatura = tabela["nivel_geracao"] + "|" + tabela["composicao"]
    tabela["mostrar"] = assinatura.ne(assinatura.shift()).where(tabela.index > 0, False) | \
        assinatura.ne(assinatura.shift(-1)).where(tabela.index < len(tabela) - 1, False)
    tabela["mostrar"] = tabela["mostrar"].astype(bool)
    tabela.insert(0, "trecho", range(1, len(tabela) + 1))
    return tabela[COLUNAS_TRECHOS]
