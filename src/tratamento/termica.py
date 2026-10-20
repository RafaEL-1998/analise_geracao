"""Térmicas no Tratamento de dados: despacho, CVU e CMO (spec 006, fase B; decisão R11; rascunho 002, FR-037 a FR-040).

- **Despacho** (horário, hora de início do intervalo): uma linha por hora e unidade de planejamento, a do arquivo publicado
  por último (as repetições com valores diferentes são contadas na auditoria), recortada no período e, em cada código,
  no período dele no perfil; ``despacho_unidades_horario.csv`` por unidade e ``despacho_horario.csv`` com a soma das
  unidades por hora, por motivo, programado e verificado. Horas ausentes de cada código, no período dele, são listadas,
  nunca preenchidas.
- **CVU** (semanal): um valor por unidade e semana operativa, o da revisão mais recente (``num_revisao``); entre arquivos
  com a mesma revisão, o publicado por último. ``sinal_cvu`` marca o CVU ausente, zero ou negativo, sem descarte
  (FR-017; o zero, por decisão do usuário de 20/10/2026: o ONS publica 0,00 nas semanas sem CVU da unidade).
- **CMO** (semanal, contexto do subsistema): um valor por semana operativa, o da publicação mais recente; as duplicatas
  são contadas. A data publicada fica ao lado da semana operativa (sábado a sexta) que a contém.
- **Semanais em hora**: ``semanal_em_horas`` leva o CVU e o CMO à hora pelo intervalo da semana operativa, só para os
  cruzamentos das Análises; nenhum arquivo horário é gravado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import pandas as pd

from src.coleta.conjuntos import COLUNA_INSTANTE, COLUNA_NAO_NUMERICO, meses_do_periodo, periodo_do_arquivo
from src.coleta.registro import COLUNAS_CMO, COLUNAS_DESPACHO_PROGRAMADO, COLUNAS_DESPACHO_VERIFICADO
from src.comum.caminhos import ARQUIVOS_TRATAMENTO
from src.comum.logger import setup_logger
from src.comum.persistencia import gravar_csv
from src.tratamento.series import COLUNAS_AUDITORIA, listar_ausencias

logger = setup_logger("tratamento")

COLUNAS_DESPACHO: Tuple[str, ...] = COLUNAS_DESPACHO_PROGRAMADO + COLUNAS_DESPACHO_VERIFICADO
COLUNAS_UNIDADES: List[str] = [COLUNA_INSTANTE, "codigo", "nom_tipopatamar", *COLUNAS_DESPACHO, "tip_restricaoeletrica",
                               "arquivo_origem"]
COLUNAS_HORARIO: List[str] = [COLUNA_INSTANTE, "unidades", "codigos", *COLUNAS_DESPACHO]
COLUNAS_AUSENCIAS_DESPACHO: List[str] = ["codigo", "tipo", "inicio", "fim", "horas"]
COLUNAS_CVU: List[str] = ["codigo", "semana_inicio", "semana_fim", "num_revisao", "val_cvu", "sinal_cvu", "revisoes",
                          "arquivo_origem"]
COLUNAS_CMO_SEMANAL: List[str] = ["subsistema", "semana_inicio", "semana_fim", "din_instante_publicado", *COLUNAS_CMO,
                                  "arquivo_origem"]
COLUNAS_AUSENCIAS_SEMANAIS: List[str] = ["codigo", "inicio", "fim", "semanas"]
COLUNAS_AUDITORIA_SEMANAL: List[str] = [("semanas_usina" if c == "horas_usina" else c) for c in COLUNAS_AUDITORIA]
SINAL_CVU_AUSENTE = "ausente"
SINAL_CVU_ZERO = "zero"
SINAL_CVU_NEGATIVO = "negativo"
SABADO = 5  # a semana operativa vai de sábado a sexta


# ---------------------------------------------------------------------------
# Comuns
# ---------------------------------------------------------------------------


def _ordem_dos_arquivos(auditoria_coleta: pd.DataFrame) -> Dict[str, int]:
    """Posição de cada arquivo lido na ordem de publicação (a ordem da auditoria da Coleta)."""
    if auditoria_coleta is None or not len(auditoria_coleta):
        return {}
    lidos = auditoria_coleta[auditoria_coleta["obtido"].astype(bool)]
    return {arquivo: i for i, arquivo in enumerate(lidos["arquivo"])}


def _meses_com_arquivo(auditoria_coleta: pd.DataFrame) -> Set[Tuple[int, int]]:
    meses: Set[Tuple[int, int]] = set()
    for arquivo in _ordem_dos_arquivos(auditoria_coleta):
        chave = periodo_do_arquivo(arquivo)
        if chave is not None:
            meses |= meses_do_periodo(chave)
    return meses


def _sem_repeticoes(tabela: pd.DataFrame, chaves: List[str], valores: Sequence[str],
                    ordem: Dict[str, int]) -> Tuple[pd.DataFrame, pd.Series]:
    """Uma linha por ``chaves``, a do arquivo publicado por último; devolve também, por arquivo, as linhas
    descartadas com valores diferentes dos mantidos (duplicatas conflitantes)."""
    if tabela.empty:
        return tabela, pd.Series(dtype=int)
    t = tabela.assign(_ordem=tabela["arquivo_origem"].map(ordem).fillna(-1))
    t = t.sort_values([*chaves, "_ordem"], kind="stable").reset_index(drop=True)
    repetidas = t.duplicated(chaves, keep="last")
    conflitos = pd.Series(dtype=int)
    if repetidas.any():
        mantidas = t[~repetidas].set_index(chaves)
        descartadas = t[repetidas]
        ref = mantidas.loc[pd.MultiIndex.from_frame(descartadas[chaves]) if len(chaves) > 1
                           else descartadas[chaves[0]], list(valores)].to_numpy()
        atual = descartadas[list(valores)].to_numpy()
        diferentes = ~((ref == atual) | (pd.isna(ref) & pd.isna(atual))).all(axis=1)
        conflitos = descartadas.loc[diferentes, "arquivo_origem"].value_counts()
    return t[~repetidas].drop(columns="_ordem").reset_index(drop=True), conflitos


def _auditoria(auditoria_coleta: pd.DataFrame, registros_por_arquivo: Dict[str, int], conflitos: pd.Series,
               coluna_registros: str, colunas: List[str]) -> pd.DataFrame:
    """Auditoria por arquivo: a da extração, com os registros da usina e as duplicatas conflitantes."""
    if auditoria_coleta is None or not len(auditoria_coleta):
        return pd.DataFrame(columns=colunas)
    auditoria = auditoria_coleta.drop(columns=["data_publicacao", "obtido"], errors="ignore").copy()
    obtidos = auditoria_coleta["obtido"].astype(bool)
    auditoria[coluna_registros] = [int(registros_por_arquivo.get(a, 0)) if o else 0
                                   for a, o in zip(auditoria_coleta["arquivo"], obtidos)]
    auditoria["duplicatas_conflitantes"] = [int(conflitos.get(a, 0)) for a in auditoria_coleta["arquivo"]]
    auditoria = auditoria.reindex(columns=colunas)
    for coluna in colunas:
        if coluna not in ("arquivo", "formato", "periodo", "status", "mensagem"):
            auditoria[coluna] = pd.to_numeric(auditoria[coluna], errors="coerce").fillna(0).astype(int)
    auditoria["mensagem"] = auditoria["mensagem"].fillna("")
    return auditoria.reset_index(drop=True)


def _limites_do_codigo(inicio_codigo: str, fim_codigo: str, inicio: pd.Timestamp,
                       fim: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Interseção do período do código (AAAA-MM, meses inteiros; fim vazio: vigente) com o período da usina."""
    a = max(pd.Timestamp(inicio), pd.Timestamp(f"{inicio_codigo}-01"))
    b = pd.Timestamp(fim)
    if fim_codigo:
        b = min(b, pd.Timestamp(f"{fim_codigo}-01") + pd.offsets.MonthBegin(1) - pd.Timedelta(hours=1))
    return a, b


# ---------------------------------------------------------------------------
# Despacho
# ---------------------------------------------------------------------------


@dataclass
class DespachoTratado:
    """Despacho por unidade e hora, a soma por hora, as horas ausentes de cada código e a auditoria."""

    unidades: pd.DataFrame
    horario: pd.DataFrame
    ausencias: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=COLUNAS_AUSENCIAS_DESPACHO))
    auditoria: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=COLUNAS_AUDITORIA))


def somar_unidades(unidades: pd.DataFrame) -> pd.DataFrame:
    """Soma das unidades de planejamento por hora, por motivo; coluna sem valor em todas as unidades fica ausente."""
    if unidades.empty:
        return pd.DataFrame(columns=COLUNAS_HORARIO)
    g = unidades.groupby(COLUNA_INSTANTE, sort=True)
    horario = g[list(COLUNAS_DESPACHO)].sum(min_count=1)
    horario.insert(0, "codigos", g["codigo"].agg(lambda s: ";".join(str(int(c)) for c in sorted(set(s)))))
    horario.insert(0, "unidades", g["codigo"].nunique())
    return horario.reset_index()[COLUNAS_HORARIO]


def montar_despacho(extraido: pd.DataFrame, auditoria_coleta: pd.DataFrame, planejamento: Iterable[Any],
                    inicio: pd.Timestamp, fim: pd.Timestamp) -> DespachoTratado:
    """Despacho tratado a partir da extração da Coleta (decisão R11): ``planejamento`` são os códigos do perfil, com o
    período de cada um."""
    ordem = _ordem_dos_arquivos(auditoria_coleta)
    if len(extraido):
        t = extraido.rename(columns={"cod_usinaplanejamento": "codigo"}).copy()
        t[COLUNA_INSTANTE] = pd.to_datetime(t[COLUNA_INSTANTE])
        t = t[t["codigo"].notna()]
    else:
        t = pd.DataFrame(columns=[*COLUNAS_UNIDADES, COLUNA_NAO_NUMERICO])
    registros = t.groupby("arquivo_origem")[COLUNA_INSTANTE].nunique().to_dict() if len(t) else {}
    t, conflitos = _sem_repeticoes(t, [COLUNA_INSTANTE, "codigo"], [*COLUNAS_DESPACHO, "tip_restricaoeletrica"], ordem)
    if int(conflitos.sum()):
        logger.warning("Despacho: %d horas-unidade repetidas com valores diferentes; mantido o arquivo publicado por "
                       "último.", int(conflitos.sum()))
    codigos = list(planejamento)
    partes, ausencias = [], []
    meses = _meses_com_arquivo(auditoria_coleta)
    for p in codigos:
        a, b = _limites_do_codigo(p.inicio, p.fim, inicio, fim)
        if a > b:
            continue
        do_codigo = t[(t["codigo"] == float(p.codigo)) & (t[COLUNA_INSTANTE] >= a) & (t[COLUNA_INSTANTE] <= b)]
        partes.append(do_codigo)
        faltam = listar_ausencias(do_codigo[COLUNA_INSTANTE], a, b, meses)
        if len(faltam):
            ausencias.append(faltam.assign(codigo=int(p.codigo)))
    unidades = (pd.concat(partes, ignore_index=True) if partes else t.iloc[0:0])
    unidades = unidades.sort_values([COLUNA_INSTANTE, "codigo"], kind="stable").reset_index(drop=True)
    unidades["codigo"] = unidades["codigo"].astype(int)
    unidades = unidades.reindex(columns=COLUNAS_UNIDADES)
    ausentes = (pd.concat(ausencias, ignore_index=True)[COLUNAS_AUSENCIAS_DESPACHO] if ausencias
                else pd.DataFrame(columns=COLUNAS_AUSENCIAS_DESPACHO))
    auditoria = _auditoria(auditoria_coleta, registros, conflitos, "horas_usina", COLUNAS_AUDITORIA)
    logger.info("Despacho: %d horas-unidade de %d códigos; %d intervalos ausentes.", len(unidades),
                unidades["codigo"].nunique(), len(ausentes))
    return DespachoTratado(unidades=unidades, horario=somar_unidades(unidades), ausencias=ausentes,
                           auditoria=auditoria)


# ---------------------------------------------------------------------------
# CVU e CMO
# ---------------------------------------------------------------------------


@dataclass
class SemanalTratado:
    """Série semanal (CVU por unidade ou CMO do subsistema), semanas ausentes e auditoria."""

    semanal: pd.DataFrame
    ausencias: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=COLUNAS_AUSENCIAS_SEMANAIS))
    auditoria: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=COLUNAS_AUDITORIA_SEMANAL))
    resumo: Dict[str, Any] = field(default_factory=dict)


def inicio_da_semana_operativa(datas: pd.Series) -> pd.Series:
    """O sábado da semana operativa (sábado a sexta) que contém cada data."""
    d = pd.to_datetime(datas).dt.normalize()
    return d - pd.to_timedelta((d.dt.weekday - SABADO) % 7, unit="D")


def _semanas_ausentes(semanas: pd.Series, inicio: pd.Timestamp, fim: pd.Timestamp, codigo: Any) -> List[Dict[str, Any]]:
    """Semanas operativas de [início, fim] sem registro, agrupadas em intervalos contínuos."""
    primeira = inicio_da_semana_operativa(pd.Series([pd.Timestamp(inicio)])).iloc[0]
    esperadas = pd.date_range(primeira, pd.Timestamp(fim), freq="7D")
    faltam = esperadas.difference(pd.DatetimeIndex(pd.to_datetime(semanas).dropna().unique()))
    if not len(faltam):
        return []
    s = faltam.to_series()
    grupos = (s.diff() != pd.Timedelta(days=7)).cumsum()
    return [{"codigo": codigo, "inicio": bloco.iloc[0], "fim": bloco.iloc[-1] + pd.Timedelta(days=6),
             "semanas": len(bloco)} for _, bloco in s.groupby(grupos.values)]


def _na_semana(semanal: pd.DataFrame, inicio: pd.Timestamp, fim: pd.Timestamp) -> pd.DataFrame:
    """Semanas que se sobrepõem a [início, fim]."""
    fim_semana = semanal["semana_fim"] + pd.Timedelta(days=1)
    return semanal[(fim_semana > pd.Timestamp(inicio)) & (semanal["semana_inicio"] <= pd.Timestamp(fim))]


def montar_cvu(extraido: pd.DataFrame, auditoria_coleta: pd.DataFrame, planejamento: Iterable[Any],
               inicio: pd.Timestamp, fim: pd.Timestamp) -> SemanalTratado:
    """CVU por unidade e semana operativa, o da revisão mais recente, com ``sinal_cvu`` para o CVU ausente, zero ou
    negativo (FR-038)."""
    ordem = _ordem_dos_arquivos(auditoria_coleta)
    if len(extraido):
        t = pd.DataFrame({
            "codigo": pd.to_numeric(extraido["cod_usinaplanejamento"], errors="coerce"),
            "semana_inicio": pd.to_datetime(extraido[COLUNA_INSTANTE]).dt.normalize(),
            "semana_fim": pd.to_datetime(extraido["dat_fimsemana"], errors="coerce").dt.normalize(),
            "num_revisao": pd.to_numeric(extraido["num_revisao"], errors="coerce"),
            "val_cvu": pd.to_numeric(extraido["val_cvu"], errors="coerce"),
            "arquivo_origem": extraido["arquivo_origem"],
        })
        t = t[t["codigo"].notna()]
    else:
        t = pd.DataFrame(columns=["codigo", "semana_inicio", "semana_fim", "num_revisao", "val_cvu", "arquivo_origem"])
    registros = t.groupby("arquivo_origem")["semana_inicio"].nunique().to_dict() if len(t) else {}
    revisoes = t.groupby(["codigo", "semana_inicio"])["num_revisao"].nunique() if len(t) else pd.Series(dtype=int)
    # a revisão mais recente de cada semana; entre arquivos com a mesma revisão, o publicado por último
    t, conflitos = _sem_repeticoes(t, ["codigo", "semana_inicio", "num_revisao"], ["val_cvu", "semana_fim"], ordem)
    if len(t):
        t = t.sort_values(["codigo", "semana_inicio", "num_revisao"], kind="stable")
        descartadas = int(t.duplicated(["codigo", "semana_inicio"], keep="last").sum())
        t = t.drop_duplicates(["codigo", "semana_inicio"], keep="last")
        t = _na_semana(t, inicio, fim)
        t["revisoes"] = [int(revisoes.get((c, s), 1)) for c, s in zip(t["codigo"], t["semana_inicio"])]
    else:
        descartadas = 0
        t = t.assign(revisoes=pd.Series(dtype=int))
    t["sinal_cvu"] = ""
    t.loc[t["val_cvu"].isna(), "sinal_cvu"] = SINAL_CVU_AUSENTE
    t.loc[t["val_cvu"] == 0, "sinal_cvu"] = SINAL_CVU_ZERO
    t.loc[t["val_cvu"] < 0, "sinal_cvu"] = SINAL_CVU_NEGATIVO
    semanal = t.reindex(columns=COLUNAS_CVU).sort_values(["semana_inicio", "codigo"], kind="stable")
    semanal["codigo"] = semanal["codigo"].astype(int)
    semanal = semanal.reset_index(drop=True)
    ausencias: List[Dict[str, Any]] = []
    for p in planejamento:
        a, b = _limites_do_codigo(p.inicio, p.fim, inicio, fim)
        if a <= b:
            ausencias += _semanas_ausentes(semanal.loc[semanal["codigo"] == int(p.codigo), "semana_inicio"], a, b,
                                           int(p.codigo))
    sinais = semanal["sinal_cvu"][semanal["sinal_cvu"] != ""].value_counts()
    resumo = {"semanas": int(semanal["semana_inicio"].nunique()), "registros": len(semanal),
              "codigos": sorted(int(c) for c in semanal["codigo"].unique()),
              "sinalizados": {str(k): int(v) for k, v in sinais.items()}, "revisoes_descartadas": descartadas,
              "duplicatas_conflitantes": int(conflitos.sum()) if len(conflitos) else 0,
              "semanas_ausentes": int(sum(a["semanas"] for a in ausencias))}
    return SemanalTratado(semanal=semanal, ausencias=pd.DataFrame(ausencias, columns=COLUNAS_AUSENCIAS_SEMANAIS),
                          auditoria=_auditoria(auditoria_coleta, registros, conflitos, "semanas_usina",
                                               COLUNAS_AUDITORIA_SEMANAL), resumo=resumo)


def montar_cmo(extraido: pd.DataFrame, auditoria_coleta: pd.DataFrame, subsistema: str, inicio: pd.Timestamp,
               fim: pd.Timestamp) -> SemanalTratado:
    """CMO do subsistema por semana operativa, o da publicação mais recente; duplicatas contadas (FR-039)."""
    ordem = _ordem_dos_arquivos(auditoria_coleta)
    if len(extraido):
        publicado = pd.to_datetime(extraido[COLUNA_INSTANTE])
        t = pd.DataFrame({"subsistema": subsistema, "semana_inicio": inicio_da_semana_operativa(publicado),
                          "din_instante_publicado": publicado, "arquivo_origem": extraido["arquivo_origem"]})
        for coluna in COLUNAS_CMO:
            t[coluna] = pd.to_numeric(extraido[coluna], errors="coerce")
        t["semana_fim"] = t["semana_inicio"] + pd.Timedelta(days=6)
    else:
        t = pd.DataFrame(columns=COLUNAS_CMO_SEMANAL)
    registros = t.groupby("arquivo_origem")["semana_inicio"].nunique().to_dict() if len(t) else {}
    duplicatas = int(t.duplicated(["semana_inicio"]).sum()) if len(t) else 0
    t, conflitos = _sem_repeticoes(t, ["semana_inicio"], list(COLUNAS_CMO), ordem)
    if len(t):
        t = _na_semana(t, inicio, fim)
    semanal = t.reindex(columns=COLUNAS_CMO_SEMANAL).sort_values("semana_inicio", kind="stable").reset_index(drop=True)
    ausencias = _semanas_ausentes(semanal["semana_inicio"], inicio, fim, subsistema)
    if duplicatas:
        logger.info("CMO: %d semanas repetidas entre publicações; mantida a publicada por último.", duplicatas)
    resumo = {"semanas": len(semanal), "duplicatas": duplicatas,
              "duplicatas_conflitantes": int(conflitos.sum()) if len(conflitos) else 0,
              "semanas_ausentes": int(sum(a["semanas"] for a in ausencias))}
    return SemanalTratado(semanal=semanal, ausencias=pd.DataFrame(ausencias, columns=COLUNAS_AUSENCIAS_SEMANAIS),
                          auditoria=_auditoria(auditoria_coleta, registros, conflitos, "semanas_usina",
                                               COLUNAS_AUDITORIA_SEMANAL), resumo=resumo)


def semanal_em_horas(semanal: pd.DataFrame, colunas: Sequence[str], chaves: Sequence[str] = ()) -> pd.DataFrame:
    """Uma linha por hora de cada semana operativa (de sábado 00h a sexta 23h), com as ``colunas`` da semana: o CVU e o
    CMO levados à hora só para os cruzamentos (FR-040)."""
    saida = [COLUNA_INSTANTE, *chaves, *colunas]
    if semanal is None or semanal.empty:
        return pd.DataFrame(columns=saida)
    partes = []
    for linha in semanal.itertuples(index=False):
        inicio = pd.Timestamp(getattr(linha, "semana_inicio"))
        horas = pd.date_range(inicio, inicio + pd.Timedelta(days=7) - pd.Timedelta(hours=1), freq="h")
        partes.append(pd.DataFrame({COLUNA_INSTANTE: horas,
                                    **{c: getattr(linha, c) for c in (*chaves, *colunas)}}))
    return pd.concat(partes, ignore_index=True)[saida]


# ---------------------------------------------------------------------------
# Gravação e leitura
# ---------------------------------------------------------------------------


def exportar_termica(pasta: Path, despacho: Optional[DespachoTratado] = None, cvu: Optional[SemanalTratado] = None,
                     cmo: Optional[SemanalTratado] = None) -> None:
    """Grava os arquivos do despacho, do CVU e do CMO tratados (data-model 6.2)."""
    pasta = Path(pasta)
    arq = ARQUIVOS_TRATAMENTO
    if despacho is not None:
        gravar_csv(despacho.horario, pasta / arq["despacho_horario"])
        gravar_csv(despacho.unidades, pasta / arq["despacho_unidades_horario"])
        gravar_csv(despacho.ausencias, pasta / arq["despacho_ausencias"])
        gravar_csv(despacho.auditoria, pasta / arq["auditoria_despacho"])
    for nome, tratado in (("cvu", cvu), ("cmo", cmo)):
        if tratado is not None:
            gravar_csv(tratado.semanal, pasta / arq[f"{nome}_semanal"])
            gravar_csv(tratado.ausencias, pasta / arq[f"{nome}_ausencias"])
            gravar_csv(tratado.auditoria, pasta / arq[f"auditoria_{nome}"])


def _ler(caminho: Path, datas: Sequence[str] = ()) -> Optional[pd.DataFrame]:
    if not caminho.exists():
        return None
    try:
        tabela = pd.read_csv(caminho, sep=";", keep_default_na=True)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    for coluna in datas:
        if coluna in tabela.columns:
            tabela[coluna] = pd.to_datetime(tabela[coluna])
    return tabela


def carregar_despacho_tratado(pasta: Path) -> Optional[DespachoTratado]:
    """Despacho gravado pelo Tratamento; None quando a usina não tem o despacho."""
    arq = ARQUIVOS_TRATAMENTO
    horario = _ler(Path(pasta) / arq["despacho_horario"], [COLUNA_INSTANTE])
    if horario is None:
        return None
    unidades = _ler(Path(pasta) / arq["despacho_unidades_horario"], [COLUNA_INSTANTE])
    ausencias = _ler(Path(pasta) / arq["despacho_ausencias"], ["inicio", "fim"])
    return DespachoTratado(unidades=unidades if unidades is not None else pd.DataFrame(columns=COLUNAS_UNIDADES),
                           horario=horario,
                           ausencias=ausencias if ausencias is not None
                           else pd.DataFrame(columns=COLUNAS_AUSENCIAS_DESPACHO))


def carregar_semanal_tratado(pasta: Path, nome: str) -> Optional[SemanalTratado]:
    """CVU (``nome="cvu"``) ou CMO (``"cmo"``) gravado pelo Tratamento; None quando a usina não o tem."""
    arq = ARQUIVOS_TRATAMENTO
    semanal = _ler(Path(pasta) / arq[f"{nome}_semanal"], ["semana_inicio", "semana_fim", "din_instante_publicado"])
    if semanal is None:
        return None
    if "sinal_cvu" in semanal.columns:
        semanal["sinal_cvu"] = semanal["sinal_cvu"].fillna("")
    ausencias = _ler(Path(pasta) / arq[f"{nome}_ausencias"], ["inicio", "fim"])
    return SemanalTratado(semanal=semanal, ausencias=ausencias if ausencias is not None
                          else pd.DataFrame(columns=COLUNAS_AUSENCIAS_SEMANAIS))
