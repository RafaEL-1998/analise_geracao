"""Série de referência, período e trechos da Coleta (plano da Coleta de dados, D24 e D25; data-model da Coleta de
dados, seções 7.1 e 7.2).

A série de referência define o período da análise (princípio IV), pelo tipo e pela cobertura da usina:
- hidrelétrica com Energia Vertida Turbinável: a EVT, pelo caminho de hoje, sem trechos;
- usina com geração própria (``[cobertura] geracao = "proprio"``): a Geração por usina, pelo id ONS;
- usina em conjunto sem série própria (``geracao = "conjunto"``): a Geração por usina do conjunto, pelo id do conjunto;
- com a lista ``["proprio", "conjunto"]``: as duas séries; o período é a união, e cada hora vale pelo nível dela;
- eólica ou solar em conjunto, com série própria na restrição com detalhe (FR-059): a geração verificada da usina nessa
  base, semi-horária, pelo id ONS; o complemento e os trechos ficam por hora.

A série é varrida em todos os arquivos publicados, com o filtro do identificador na leitura do Parquet. O período vai
da primeira à última hora com valor preenchido. Na usina em conjunto sem série própria (FR-054),
as horas do conjunto só contam enquanto a usina está na composição: antes da entrada dela, a geração do conjunto não a
inclui.

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
# Tipo e combustível que o ONS publica na série do conjunto (FR-061)
COLUNAS_TIPO_PUBLICADO = ("nom_tipousina", "nom_tipocombustivel")
COLUNAS_TABELA_TIPO_PUBLICADO = ["trecho", "inicio", "fim", "nom_tipousina", "nom_tipocombustivel", "horas"]
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
    """A série de referência escolhida: o conjunto do registro, os níveis e a linha da FR-054 que se aplicou."""

    conjunto: str
    niveis: Tuple[str, ...]
    motivo: str


def escolher_pela_cobertura(tipo: str, cobertura: Dict[str, Any]) -> Optional[Escolha]:
    """Série de referência pelo tipo e pela cobertura (D24); None sem nenhuma. Regra única da Coleta e do rascunho do
    perfil, que tem só a cobertura do catálogo (bug rascunho-sem-serie-referencia)."""
    chaves = [e.chave for e in registro.conjuntos_pela_cobertura(tipo, cobertura)]
    if "evt" in chaves:
        return Escolha("evt", ("usina",), MOTIVOS["evt"])
    valor = cobertura.get("geracao")
    valores = valor if isinstance(valor, (list, tuple)) else [valor]
    niveis = tuple(registro.NIVEL_DA_COBERTURA[v] for v in ("proprio", "conjunto") if v in valores)
    if ("usina" not in niveis and "restricao_detalhe" in chaves
            and registro.nivel_na_cobertura("restricao_detalhe", cobertura) == "usina"):  # FR-059 na tabela da FR-054
        return Escolha("restricao_detalhe", ("usina",), MOTIVOS["restricao_detalhe"])
    if "geracao" not in chaves or not niveis:
        return None
    return Escolha("geracao", niveis, MOTIVOS["_".join(niveis)])


def escolher(perfil: Any) -> Escolha:
    """Série de referência pelo tipo e pela cobertura (D24). Sem nenhuma, ``ValueError``."""
    escolha = escolher_pela_cobertura(registro.tipo_da_usina(perfil), registro.cobertura_da_usina(perfil))
    if escolha is None:
        raise ValueError(f"a usina '{perfil.usina.slug}' não tem série de referência: nem a Energia Vertida Turbinável "
                         "nem a Geração por usina (da usina ou do conjunto) na [cobertura]")
    return escolha


def descricoes_referencia(perfil: Any, escolha: Escolha) -> Dict[str, DescricaoConjunto]:
    """Descrições da série em cada nível, com a modalidade por hora (para os trechos): a Geração por usina ou, na linha
    da FR-059, a restrição com detalhe da usina."""
    if escolha.conjunto == "restricao_detalhe":
        return {"usina": replace(registro.descricao_restricao_detalhe(perfil), chave="restricao_detalhe",
                                 nivel="usina", referencia=True, resolucao="semi_horaria")}
    if escolha.conjunto != "geracao":
        return {}
    # no conjunto, também o tipo publicado, comparado depois com os tipos da composição (FR-061)
    return {nivel: replace(registro.descricao_geracao(perfil, nivel), chave="geracao", nivel=nivel, referencia=True,
                           colunas_texto=(COLUNA_MODALIDADE, *(COLUNAS_TIPO_PUBLICADO if nivel == "conjunto" else ())))
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
    """Modalidade e nível de cada hora: o da usina quando ela tem valor; senão, o do conjunto (D25). Na série
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
    """Resumo da série de referência para o ``etapa.json`` da Coleta (data-model da Coleta de dados, seção 7.1)."""
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
    """``trechos.csv``: um trecho por intervalo sem mudança de modalidade, nível, composição nem código (data-model da
    Coleta de dados, seção 7.2).

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


# ---------------------------------------------------------------------------
# Usina em conjunto (FR-054 e FR-061)
# ---------------------------------------------------------------------------


def intervalos_da_usina(composicao: pd.DataFrame, ceg: str) -> List[Tuple[pd.Timestamp, Optional[pd.Timestamp]]]:
    """Intervalos [entrada, saída) da usina na composição do conjunto (``composicao_conjunto.csv``), pelo CEG; a saída
    vazia é a usina ainda no conjunto. Sem a usina na composição, lista vazia."""
    if composicao is None or composicao.empty:
        return []
    alvo = normalizar_texto(ceg)
    da_usina = composicao[composicao["ceg"].map(normalizar_texto) == alvo]
    intervalos = []
    for linha in da_usina.to_dict("records"):
        inicio = _data(linha.get("inicio")) or INICIO_VARREDURA
        intervalos.append((inicio, _data(linha.get("fim"))))
    return sorted(intervalos, key=lambda i: i[0])


def membros_no_periodo(composicao: pd.DataFrame, inicio: pd.Timestamp, fim: pd.Timestamp) -> List[str]:
    """CEGs das usinas que estiveram na composição do conjunto em algum momento do período, na ordem da composição."""
    if composicao is None or composicao.empty:
        return []
    cegs = []
    for linha in composicao.to_dict("records"):
        entrada, saida = _data(linha.get("inicio")), _data(linha.get("fim"))
        if (entrada is None or entrada <= fim) and (saida is None or saida > inicio):
            cegs.append(str(linha.get("ceg") or "").strip())
    return list(dict.fromkeys(c for c in cegs if c))


def no_intervalo(serie: pd.DataFrame, intervalos: Sequence[Tuple[pd.Timestamp, Optional[pd.Timestamp]]]
                 ) -> pd.DataFrame:
    """Linhas da série com o instante em algum dos intervalos [entrada, saída)."""
    if serie is None or not len(serie):
        return serie
    instantes = pd.to_datetime(serie["din_instante"])
    dentro = pd.Series(False, index=serie.index)
    for inicio, fim in intervalos:
        dentro |= (instantes >= inicio) & ((instantes < fim) if fim is not None else True)
    return serie[dentro].reset_index(drop=True)


def trecho_de_cada_hora(instantes: pd.Series, tabela_trechos: pd.DataFrame) -> pd.Series:
    """Número do trecho de cada instante (a tabela de ``trechos``); vazio fora de todo trecho."""
    saida = pd.Series(pd.NA, index=instantes.index, dtype="Int64")
    for linha in tabela_trechos.to_dict("records"):
        dentro = (instantes >= pd.Timestamp(linha["inicio"])) & (instantes <= pd.Timestamp(linha["fim"]))
        saida[dentro & saida.isna()] = int(linha["trecho"])
    return saida


def tipos_publicados(serie_conjunto: pd.DataFrame, tabela_trechos: pd.DataFrame) -> pd.DataFrame:
    """``tipo_publicado.csv``: por trecho, o tipo e o combustível que o ONS publica na série do conjunto e as horas de
    cada um (o tipo da usina vem do CEG; a comparação com a composição fica com as Análises)."""
    if serie_conjunto is None or not len(serie_conjunto) or tabela_trechos is None or not len(tabela_trechos):
        return pd.DataFrame(columns=COLUNAS_TABELA_TIPO_PUBLICADO)
    s = serie_conjunto.assign(din_instante=pd.to_datetime(serie_conjunto["din_instante"]))
    s = s.assign(trecho=trecho_de_cada_hora(s["din_instante"], tabela_trechos)).dropna(subset=["trecho"])
    for coluna in COLUNAS_TIPO_PUBLICADO:
        s[coluna] = s[coluna].astype("string").fillna("").str.strip() if coluna in s.columns else ""
    limites = tabela_trechos.set_index("trecho")[["inicio", "fim"]]
    linhas = [{"trecho": int(trecho), "inicio": limites.loc[int(trecho), "inicio"],
               "fim": limites.loc[int(trecho), "fim"], "nom_tipousina": tipo, "nom_tipocombustivel": combustivel,
               "horas": len(g)}
              for (trecho, tipo, combustivel), g in s.groupby(["trecho", *COLUNAS_TIPO_PUBLICADO], sort=True)]
    return pd.DataFrame(linhas, columns=COLUNAS_TABELA_TIPO_PUBLICADO)
