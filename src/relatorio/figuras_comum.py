"""Figuras das usinas sem EVT, em seaborn, desenhadas a partir das seções comuns e das seções do tipo (plano da
Geração do relatório, D15, D16, D18 e D19; nas térmicas, as quatro figuras da FR-044; nas eólicas e solares, as
quatro da FR-045).

Mesmo tema, paleta e tamanho das figuras de hoje (``src/relatorio/figuras.py``). Cada série leva o nível no rótulo
quando não é da usina ("do conjunto ..."); níveis diferentes nunca são somados na mesma barra ou linha.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.analises.renovavel import RAZOES, SEM_RAZAO
from src.analises.resultados import ResultadosAnalise
from src.comum.formatacao import MESES_ABREVIADOS, fmt_num
from src.comum.logger import setup_logger
from src.comum.perfil import perfil_ativo
from src.comum.regras import TAMANHO_FIGURA_PADRONIZADA
from src.relatorio.figuras import (
    COR_CONTEXTO,
    COR_DISPONIBILIDADE,
    COR_EVT,
    COR_GERACAO,
    COR_SINCRONIZADA,
    COR_TINTA,
    COR_TINTA_SECUNDARIA,
    COR_TINTA_SUAVE,
    RAMPA_LARANJA,
    _rotulo_referencia,
    _tema_graficos,
)

logger = setup_logger("relatorio")

NOMES_FIGURAS_COMUM: Dict[str, str] = {
    "serie_temporal_comum": "01_serie_temporal_geracao_disponibilidade.png",
    "geracao_mensal": "02_geracao_mensal.png",
    "perfil_horario_comum": "04_perfil_horario_geracao.png",
}
# Geradas só com a base: sazonalidade com 12 meses distintos (FR-041) e disponibilidade da usina
NOMES_FIGURAS_COMUM_OPCIONAIS: Dict[str, str] = {
    "sazonalidade": "03_geracao_por_mes_do_ano.png",
    "disponibilidade_comum": "05_disponibilidade_operacional_sincronizada_mensal.png",
    # Térmicas: só com o despacho; o CVU × CMO, só com o CVU e o CMO
    "despacho_motivo_mensal": "06_despacho_por_motivo_mensal.png",
    "inflexibilidade_mensal": "07_inflexibilidade_mensal.png",
    "desvios_despacho": "08_desvios_despacho_mensal.png",
    "cvu_cmo": "09_cvu_cmo_semanal.png",
    # Eólicas e solares: cada uma só com a sua base
    "fc_mensal": "10_fator_capacidade_mensal.png",
    "corte_razao_mensal": "11_energia_cortada_por_razao_mensal.png",
    "recurso_geracao": "12_geracao_por_faixa_de_recurso.png",
    "desvio_programacao": "13_desvio_programacao_mensal.png",
    # Fase D: a geração do conjunto por trecho de composição e as vazões da hidrelétrica sem EVT
    "conjunto_mensal": "14_geracao_do_conjunto_por_trecho.png",
    "hidrologia_mensal_comum": "15_vazoes_mensais.png",
    # Spec da Geração do relatório, FR-071: só com diferença de pelo menos 1 p.p. em algum mês
    "taxas_operativas": "16_taxas_oficiais_e_operativas.png",
}
COR_CONJUNTO = "#184f95"  # azul escuro da rampa: a série do conjunto, ao lado da azul da usina
# Motivos do despacho: cada motivo com a sua posição fixa na ordem categórica (validada com o script da skill de
# visualização sobre fundo branco; contraste abaixo de 3:1 em três cores, compensado pela tabela e pela legenda); os
# demais motivos juntos, em cinza
CORES_MOTIVOS: Dict[str, str] = {
    "Ordem de mérito": "#2a78d6", "Inflexibilidade": "#eb6834", "Razão elétrica": "#1baf7a",
    "Garantia energética": "#eda100", "Unit commitment": "#e87ba4", "Geração fora da ordem de mérito (GFOM)": "#008300",
    "Demais motivos": COR_CONTEXTO,
}
CORES_UNIDADES = ["#2a78d6", "#1baf7a", "#eda100", "#e87ba4"]  # CVU de cada unidade, na ordem dos códigos
# Razões da restrição: as três primeiras posições da ordem categórica, validadas com o script da skill de
# visualização sobre fundo branco (contraste do verde abaixo de 3:1, compensado pela tabela por razão e pela legenda);
# a semi-hora restrita sem razão publicada, em cinza
CORES_RAZOES: Dict[str, str] = {**dict(zip(RAZOES.values(), ("#2a78d6", "#eb6834", "#1baf7a"))),
                                SEM_RAZAO: COR_CONTEXTO}
# Trechos de composição do conjunto: a ordem categórica fixa, validada com o script da skill de visualização
# sobre fundo branco (contraste abaixo de 3:1 em três cores, compensado pela legenda e pela tabela por trecho); a partir
# do sexto trecho, cinza ("demais composições"), nunca uma cor nova
CORES_TRECHOS = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4")
DEMAIS_COMPOSICOES = "Demais composições"


def rotulo_nivel(res: ResultadosAnalise, nivel: str) -> str:
    """Rótulo da série no nível: "Geração" (usina) ou "Geração do conjunto <nome>"."""
    if nivel != "conjunto":
        return "Geração"
    g = res.niveis.get("geracao", {})
    return f"Geração do conjunto {g.get('nome') or g.get('identificador_conjunto') or ''}".rstrip()


def _cores(res: ResultadosAnalise, niveis: List[str]) -> Dict[str, str]:
    return {rotulo_nivel(res, n): (COR_GERACAO if n == "usina" else COR_CONJUNTO) for n in niveis}


def _potencia_se_usina(ax: plt.Axes, res: ResultadosAnalise, niveis: List[str]) -> None:
    if "usina" in niveis:
        p = perfil_ativo().parametros.potencia_instalada_mw
        ax.axhline(p, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (4, 3)), zorder=1)
        _rotulo_referencia(ax, p, f"Potência instalada\n{fmt_num(p, 0)} MW")


# Valores do eixo y sem arredondar a fração (2,5 não vira "2")
_FORMATADOR_Y = plt.FuncFormatter(lambda v, _: fmt_num(v, 0 if float(v).is_integer() else 1))
ANOS_COM_MARCA_ANUAL = 3  # séries a partir de 3 anos: uma marca por ano; mais curtas, por mês
DIAS_COM_MARCA_DIARIA = 62  # séries de até dois meses: marcas por dia


def _rotulo_mes(valor: float, _: object = None) -> str:
    data = mdates.num2date(valor)
    return f"{MESES_ABREVIADOS[data.month - 1]}/{data.year}"


def _eixo_tempo(ax: plt.Axes, inicio: pd.Timestamp, fim: pd.Timestamp, diario: bool = True) -> None:
    """Marcas por ano nas séries longas; nas curtas, por mês ("set/2025"); nas de até dois meses de dados diários,
    por dia ("10/02"), como as séries das UFV. Os dados mensais nunca têm marcas por dia."""
    dias = (pd.Timestamp(fim) - pd.Timestamp(inicio)).days
    if dias >= ANOS_COM_MARCA_ANUAL * 365:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        return
    if diario and dias <= DIAS_COM_MARCA_DIARIA:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, int(round(dias / 8)))))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        return
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=max(1, int(round(dias / 30.4 / 8)))))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(_rotulo_mes))


def _grafico_serie_temporal(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    diario = res.comum["serie_diaria"]
    niveis = sorted(diario["nivel"].unique())
    cores = _cores(res, niveis)
    longo = diario.assign(serie=diario["nivel"].map(lambda n: rotulo_nivel(res, n)))[["din_instante", "serie",
                                                                                      "geracao_mw"]]
    longo = longo.rename(columns={"geracao_mw": "mw"})
    disp = diario[diario["disponibilidade_operacional_mw"].notna()]
    if len(disp):
        cores["Disponibilidade operacional"] = COR_DISPONIBILIDADE
        longo = pd.concat([longo, pd.DataFrame({"din_instante": disp["din_instante"],
                                                "serie": "Disponibilidade operacional",
                                                "mw": disp["disponibilidade_operacional_mw"]})], ignore_index=True)
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    poucos_dias = longo["din_instante"].nunique() <= 62  # série curta: os pontos também, para dias isolados
    sns.lineplot(data=longo, x="din_instante", y="mw", hue="serie", hue_order=list(cores), palette=cores,
                 estimator=None, errorbar=None, linewidth=1.0, legend=False, ax=ax,
                 marker="o" if poucos_dias else None, markersize=3)
    _potencia_se_usina(ax, res, niveis)
    if len(diario):
        ax.set_xlim(diario["din_instante"].min(), diario["din_instante"].max())
    ax.set_ylim(bottom=0)
    ax.set_xlabel("")
    ax.set_ylabel("MW médios (média diária)")
    ax.yaxis.set_major_formatter(_FORMATADOR_Y)
    _eixo_tempo(ax, diario["din_instante"].min(), diario["din_instante"].max())
    ax.set_title("Geração e disponibilidade (médias diárias)" if len(disp) else "Geração (médias diárias)")
    ax.legend(handles=[plt.Line2D([], [], color=cor, lw=2, label=nome) for nome, cor in cores.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=len(cores))
    fig.subplots_adjust(left=0.07, right=0.86, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_geracao_mensal(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    m = res.comum["mensal"]
    niveis = sorted(m["nivel"].unique())
    cores = _cores(res, niveis)
    longo = m.assign(serie=m["nivel"].map(lambda n: rotulo_nivel(res, n)), gwh=m["energia_mwh"] / 1000.0)
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    if len(m):
        meses = sorted(m["mes"].unique())
        limites = list(meses) + [pd.Timestamp(meses[-1]) + pd.offsets.MonthBegin(1)]
        sns.histplot(data=longo, x="mes", weights="gwh", hue="serie", hue_order=list(cores), palette=cores,
                     multiple="dodge" if len(niveis) > 1 else "layer",
                     bins=[float(b) for b in mdates.date2num(limites)], shrink=0.85, alpha=1, edgecolor="white",
                     linewidth=0.3, legend=False, ax=ax)
        ax.set_xlim(pd.Timestamp(meses[0]) - pd.Timedelta(days=5), pd.Timestamp(meses[-1]) + pd.Timedelta(days=36))
    ax.set_xlabel("")
    ax.set_ylabel("Energia mensal (GWh)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: fmt_num(v, 1)))
    if len(m):
        _eixo_tempo(ax, m["mes"].min(), m["mes"].max(), diario=False)
    ax.grid(axis="x", visible=False)
    ax.set_title("Energia gerada por mês")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=cor, label=nome) for nome, cor in cores.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=len(cores))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_sazonalidade(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    s = res.comum["sazonalidade"]
    niveis = sorted(s["nivel"].unique())
    cores = _cores(res, niveis)
    longo = s.assign(serie=s["nivel"].map(lambda n: rotulo_nivel(res, n)),
                     mes=s["mes_do_ano"].map(lambda i: MESES_ABREVIADOS[int(i) - 1]))
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    sns.barplot(data=longo, x="mes", y="geracao_media_mw", hue="serie", order=MESES_ABREVIADOS,
                hue_order=list(cores), palette=cores, legend=False, ax=ax, width=0.8, saturation=1)
    _potencia_se_usina(ax, res, niveis)
    ax.set_xlabel("")
    ax.set_ylabel("Geração média (MWmed)")
    ax.yaxis.set_major_formatter(_FORMATADOR_Y)
    ax.grid(axis="x", visible=False)
    ax.set_title("Geração média por mês do ano")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=cor, label=nome) for nome, cor in cores.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=len(cores))
    fig.subplots_adjust(left=0.07, right=0.86, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_perfil_horario(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    p = res.comum["perfil_horario"]
    niveis = sorted(p["nivel"].unique())
    cores = _cores(res, niveis)
    longo = p.assign(serie=p["nivel"].map(lambda n: rotulo_nivel(res, n)))
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    sns.lineplot(data=longo, x="hora", y="geracao_media_mw", hue="serie", hue_order=list(cores), palette=cores,
                 linewidth=1.6, marker="o", markersize=3.5, legend=False, ax=ax)
    _potencia_se_usina(ax, res, niveis)
    ax.set_xticks(range(0, 24, 3))
    ax.set_xticklabels([f"{h}h" for h in range(0, 24, 3)])
    ax.set_xlim(-0.5, 23.5)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Hora do dia")
    ax.set_ylabel("Geração média (MW)")
    ax.yaxis.set_major_formatter(_FORMATADOR_Y)
    ax.set_title("Geração média por hora do dia, no período")
    ax.legend(handles=[plt.Line2D([], [], color=cor, lw=2, label=nome) for nome, cor in cores.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=len(cores))
    fig.subplots_adjust(left=0.07, right=0.86, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_disponibilidade(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    m = res.comum["disponibilidade"]["mensal"].copy()
    m["mes"] = pd.PeriodIndex(m["periodo"], freq="M").to_timestamp()
    series = {
        "Disponibilidade operacional": ("disp_operacional_media_mw", COR_DISPONIBILIDADE),
        "Disponibilidade sincronizada": ("disp_sincronizada_media_mw", COR_SINCRONIZADA),
        "Geração": ("geracao_media_mw", COR_GERACAO),
    }
    longo = pd.concat([pd.DataFrame({"mes": m["mes"], "serie": nome, "mw": m[coluna]})
                       for nome, (coluna, _) in series.items()], ignore_index=True)
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    sns.lineplot(data=longo, x="mes", y="mw", hue="serie", hue_order=list(series),
                 palette={nome: cor for nome, (_, cor) in series.items()}, linewidth=1.4, marker="o", markersize=3,
                 legend=False, ax=ax)
    _potencia_se_usina(ax, res, ["usina"])
    if len(m):
        ax.set_xlim(m["mes"].min() - pd.Timedelta(days=20), m["mes"].max() + pd.Timedelta(days=20))
    ax.set_ylim(0, perfil_ativo().parametros.potencia_instalada_mw * 1.08)
    ax.set_xlabel("")
    ax.set_ylabel("MW (média mensal)")
    ax.yaxis.set_major_formatter(_FORMATADOR_Y)
    if len(m):
        _eixo_tempo(ax, m["mes"].min(), m["mes"].max(), diario=False)
    ax.grid(axis="x", visible=False)
    ax.set_title("Disponibilidade operacional, sincronizada e geração da usina (MW)")
    ax.legend(handles=[plt.Line2D([], [], color=cor, lw=2, label=nome) for nome, (_, cor) in series.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=3)
    fig.subplots_adjust(left=0.07, right=0.86, top=0.89, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _limites_dos_meses(meses: List[pd.Timestamp]) -> List[float]:
    limites = list(meses) + [pd.Timestamp(meses[-1]) + pd.offsets.MonthBegin(1)]
    return [float(b) for b in mdates.date2num(limites)]


def _eixo_mensal(ax: plt.Axes, meses: List[pd.Timestamp], rotulo_y: str, titulo: str) -> None:
    ax.set_xlim(pd.Timestamp(meses[0]) - pd.Timedelta(days=5), pd.Timestamp(meses[-1]) + pd.Timedelta(days=36))
    ax.set_xlabel("")
    ax.set_ylabel(rotulo_y)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: fmt_num(v, 1)))
    _eixo_tempo(ax, meses[0], meses[-1], diario=False)
    ax.grid(axis="x", visible=False)
    ax.set_title(titulo)


def _legenda_retangulos(ax: plt.Axes, cores: Dict[str, str], extra: tuple = (), colunas: int = 4) -> None:
    alcas = [plt.Rectangle((0, 0), 1, 1, color=cor, label=nome) for nome, cor in cores.items()] + list(extra)
    ax.legend(handles=alcas, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=min(colunas, len(alcas)))


def _grafico_despacho_motivo(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    todos = res.termica["motivos_mensal"]
    m = todos[todos["grupo"] == "motivo"].copy()
    m["mes"] = pd.PeriodIndex(m["periodo"], freq="M").to_timestamp()
    m["serie"] = m["motivo"].where(m["motivo"].isin(CORES_MOTIVOS), "Demais motivos")
    m["gwh"] = m["verificado_mwh"].fillna(0.0).clip(lower=0.0) / 1000.0
    longo = m.groupby(["mes", "serie"], as_index=False)["gwh"].sum()
    presentes = [s for s in CORES_MOTIVOS if s in set(longo.loc[longo["gwh"] > 0, "serie"])]
    cores = {s: CORES_MOTIVOS[s] for s in presentes}
    longo = longo[longo["serie"].isin(presentes)]
    total = todos[todos["grupo"] == "total"]
    meses = list(pd.PeriodIndex(total["periodo"], freq="M").to_timestamp())
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    if len(longo):
        # o seaborn empilha o último nível da ordem embaixo: a ordem invertida deixa a ordem de mérito na base
        sns.histplot(data=longo, x="mes", weights="gwh", hue="serie", hue_order=presentes[::-1], palette=cores,
                     multiple="stack", bins=_limites_dos_meses(meses), shrink=0.85, alpha=1, edgecolor="white",
                     linewidth=0.3, legend=False, ax=ax)
    centros = [pd.Timestamp(x) + pd.Timedelta(days=15) for x in meses]
    sns.scatterplot(x=centros, y=(total["verificado_mwh"].fillna(0.0) / 1000.0).to_numpy(), color=COR_TINTA, s=10,
                    zorder=3, legend=False, ax=ax)
    _eixo_mensal(ax, meses, "Energia mensal (GWh)", "Geração verificada por motivo de despacho")
    _legenda_retangulos(ax, cores, (plt.Line2D([], [], color=COR_TINTA, marker="o", lw=0, markersize=4,
                                               label="Geração verificada total"),))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.9, bottom=0.24)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_inflexibilidade(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    i = res.termica["inflexibilidade"]
    cores = {"Inflexibilidade programada": RAMPA_LARANJA[2], "Inflexibilidade verificada": COR_EVT}
    longo = pd.concat([pd.DataFrame({"mes": i["mes"], "serie": nome, "gwh": i[coluna].fillna(0.0) / 1000.0})
                       for nome, coluna in zip(cores, ("programada_mwh", "verificada_mwh"))], ignore_index=True)
    meses = sorted(i["mes"])
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    sns.histplot(data=longo, x="mes", weights="gwh", hue="serie", hue_order=list(cores), palette=cores,
                 multiple="dodge", bins=_limites_dos_meses(meses), shrink=0.85, alpha=1, edgecolor="white",
                 linewidth=0.3, legend=False, ax=ax)
    _eixo_mensal(ax, meses, "Energia mensal (GWh)", "Inflexibilidade programada e verificada")
    _legenda_retangulos(ax, cores)
    fig.subplots_adjust(left=0.07, right=0.97, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_desvios(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    m = res.termica["atendimento"]["mensal"]
    series = (("Verificada acima da programada", "energia_acima_mwh", 1.0, COR_GERACAO),
              ("Verificada abaixo da programada", "energia_abaixo_mwh", -1.0, COR_EVT))
    meses = sorted(m["mes"])
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    for nome, coluna, sinal, cor in series:  # abaixo para baixo, acima para cima, sem somar os dois lados
        sns.histplot(x=m["mes"], weights=sinal * m[coluna] / 1000.0, color=cor, alpha=1,
                     bins=_limites_dos_meses(meses), shrink=0.85, edgecolor="white", linewidth=0.3, ax=ax)
    ax.axhline(0, color=COR_TINTA_SECUNDARIA, lw=0.8)
    _eixo_mensal(ax, meses, "Energia mensal do desvio (GWh)", "Desvios da geração verificada em relação à programada")
    _legenda_retangulos(ax, {nome: cor for nome, _, _, cor in series})
    fig.subplots_adjust(left=0.07, right=0.97, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_cvu_cmo(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    s = res.termica["cvu_cmo"]["semanal"]
    codigos = sorted(s["codigo"].unique())
    cores = {f"CVU da unidade {c}": CORES_UNIDADES[n % len(CORES_UNIDADES)] for n, c in enumerate(codigos)}
    cores["CMO médio semanal"] = COR_TINTA_SECUNDARIA
    cvu = pd.DataFrame({"semana_inicio": s["semana_inicio"], "serie": s["codigo"].map(lambda c: f"CVU da unidade {c}"),
                        "valor": s["cvu"].where(s["sinal_cvu"].fillna("") == "")})
    semanas = s.drop_duplicates("semana_inicio")
    cmo = pd.DataFrame({"semana_inicio": semanas["semana_inicio"], "serie": "CMO médio semanal",
                        "valor": semanas["cmo"]})
    longo = pd.concat([cvu, cmo], ignore_index=True).sort_values(["serie", "semana_inicio"])
    # a linha se interrompe na semana sem valor (CVU ausente ou negativo): um trecho por sequência de semanas com valor
    longo["trecho"] = (longo["valor"].isna() | (longo["semana_inicio"].diff() != pd.Timedelta(days=7))
                       | (longo["serie"] != longo["serie"].shift())).cumsum()
    longo = longo.dropna(subset=["valor"])
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    sns.lineplot(data=longo, x="semana_inicio", y="valor", hue="serie", hue_order=list(cores), palette=cores,
                 units="trecho", estimator=None, errorbar=None, linewidth=1.2, legend=False, ax=ax,
                 marker="o" if s["semana_inicio"].nunique() <= 30 else None, markersize=3)
    inicio, fim = s["semana_inicio"].min(), s["semana_inicio"].max()
    ax.set_xlim(inicio, fim + pd.Timedelta(days=6))
    ax.set_ylim(bottom=0)
    ax.set_xlabel("")
    ax.set_ylabel("R$/MWh")
    ax.yaxis.set_major_formatter(_FORMATADOR_Y)
    _eixo_tempo(ax, inicio, fim, diario=False)
    ax.set_title("CVU das unidades e CMO do subsistema, por semana operativa")
    ax.legend(handles=[plt.Line2D([], [], color=cor, lw=2, label=nome) for nome, cor in cores.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=min(4, len(cores)))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Eólicas e solares
# ---------------------------------------------------------------------------


def _grafico_fc_mensal(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    fc = res.renovavel["fator_capacidade"]
    m = fc["mensal"]
    nome = (res.niveis.get("geracao") or {}).get("nome") or ""
    publicado = f"Publicado pelo ONS ({f'conjunto {nome}'.strip() if fc['nivel'] == 'conjunto' else 'usina'})"
    cores = {publicado: COR_CONJUNTO if fc["nivel"] == "conjunto" else COR_GERACAO}
    partes = [pd.DataFrame({"mes": pd.to_datetime(m["periodo"]), "serie": publicado, "pct": m["fator_capacidade_pct"]})]
    mensal = res.comum["mensal"]
    usina = mensal[mensal["nivel"] == "usina"]
    if len(usina):  # o calculado neste relatório, da série própria e da potência do perfil
        calculado = "Calculado neste relatório (usina)"
        cores[calculado] = COR_EVT
        pinst = perfil_ativo().parametros.potencia_instalada_mw
        partes.append(pd.DataFrame({"mes": usina["mes"], "serie": calculado,
                                    "pct": usina["geracao_media_mw"] / pinst * 100.0}))
    longo = pd.concat(partes, ignore_index=True)
    # o calculado tracejado: as duas linhas continuam visíveis quando coincidem (codificação além da cor)
    tracos = {s: ("" if s == publicado else (4, 2)) for s in cores}
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    meses = sorted(longo["mes"].unique())
    poucos = len(meses) <= 36  # série longa: só as linhas, sem um ponto por mês
    sns.lineplot(data=longo, x="mes", y="pct", hue="serie", hue_order=list(cores), palette=cores, style="serie",
                 style_order=list(cores), dashes=tracos, linewidth=1.6 if poucos else 1.2,
                 marker="o" if poucos else None, markersize=4, legend=False, ax=ax)
    ax.set_xlim(pd.Timestamp(meses[0]) - pd.Timedelta(days=20), pd.Timestamp(meses[-1]) + pd.Timedelta(days=20))
    ax.set_ylim(bottom=0)
    ax.set_xlabel("")
    ax.set_ylabel("Fator de capacidade (%)")
    ax.yaxis.set_major_formatter(_FORMATADOR_Y)
    _eixo_tempo(ax, meses[0], meses[-1], diario=False)
    ax.grid(axis="x", visible=False)
    ax.set_title("Fator de capacidade mensal")
    ax.legend(handles=[plt.Line2D([], [], color=cor, lw=2, marker="o" if poucos else None,
                                  ls="-" if nome == publicado else (0, (4, 2)),
                                  label=nome) for nome, cor in cores.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=len(cores))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_corte_razao(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    from src.analises.renovavel import COLUNA_RAZAO

    m = res.renovavel["restricao"]["mensal"]
    meses = list(pd.to_datetime(m["periodo"]))
    rotulos = {**RAZOES, SEM_RAZAO: SEM_RAZAO}
    longo = pd.concat([pd.DataFrame({"mes": meses, "serie": rotulos[razao], "mwh": m[coluna].fillna(0.0).to_numpy()})
                       for razao, coluna in COLUNA_RAZAO.items()], ignore_index=True)
    presentes = [s for s in CORES_RAZOES if s in set(longo.loc[longo["mwh"] > 0, "serie"])]
    cores = {s: CORES_RAZOES[s] for s in presentes}
    longo = longo[longo["serie"].isin(presentes)]
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    if len(longo):
        # o seaborn empilha o último nível da ordem embaixo: a ordem invertida deixa REL na base
        sns.histplot(data=longo, x="mes", weights="mwh", hue="serie", hue_order=presentes[::-1], palette=cores,
                     multiple="stack", bins=_limites_dos_meses(meses), shrink=0.85, alpha=1, edgecolor="white",
                     linewidth=0.3, legend=False, ax=ax)
    _eixo_mensal(ax, meses, "Energia cortada (MWh)", "Energia cortada por restrição de operação, por razão")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: fmt_num(v, 0)))
    _legenda_retangulos(ax, cores)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_recurso(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    rec = res.renovavel["recurso"]
    f = rec["faixas"]
    casas = 0 if float(rec["largura"]).is_integer() else 1
    rotulos = [f"{fmt_num(a, casas)}–{fmt_num(b, casas)}" for a, b in zip(f["faixa_inicio"], f["faixa_fim"])]
    tabela = f.assign(rotulo=rotulos)
    cores = {"Geração verificada média": COR_GERACAO, "Geração estimada média": COR_EVT}
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    sns.barplot(data=tabela, x="rotulo", y="geracao_media_mw", order=rotulos, color=COR_GERACAO, width=0.75,
                saturation=1, ax=ax)
    sns.lineplot(x=np.arange(len(tabela)), y=tabela["estimada_media_mw"].to_numpy(), color=COR_EVT, linewidth=1.4,
                 marker="o", markersize=4, ax=ax)
    ax.set_ylim(bottom=0)
    ax.set_xlabel(f"Faixa de {rec['grandeza']} ({rec['unidade']})")
    ax.set_ylabel("Geração média (MW)")
    ax.yaxis.set_major_formatter(_FORMATADOR_Y)
    ax.grid(axis="x", visible=False)
    ax.set_title(f"Geração média por faixa de {rec['grandeza']}")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=COR_GERACAO, label="Geração verificada média"),
                       plt.Line2D([], [], color=COR_EVT, lw=2, marker="o", label="Geração estimada média")],
              loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=len(cores))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.9, bottom=0.24)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_desvio_programacao(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    m = res.comum["programacao"]["mensal"]
    meses = list(pd.to_datetime(m["mes"]))
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    sns.histplot(x=meses, weights=m["desvio_medio_absoluto_mw"].to_numpy(), color=COR_GERACAO, alpha=1,
                 bins=_limites_dos_meses(meses), shrink=0.85, edgecolor="white", linewidth=0.3, ax=ax)
    centros = [pd.Timestamp(x) + pd.Timedelta(days=15) for x in meses]
    sns.scatterplot(x=centros, y=m["desvio_medio_mw"].to_numpy(), color=COR_EVT, s=30, zorder=3, legend=False, ax=ax)
    ax.axhline(0, color=COR_TINTA_SECUNDARIA, lw=0.8)
    _eixo_mensal(ax, meses, "Desvio (MW)", "Desvio da geração verificada em relação à programada")
    _legenda_retangulos(ax, {"Desvio médio absoluto": COR_GERACAO},
                        (plt.Line2D([], [], color=COR_EVT, marker="o", lw=0, markersize=5,
                                    label="Desvio médio (verificada − programada)"),))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Usina em conjunto e hidrelétrica sem EVT
# ---------------------------------------------------------------------------


def _grafico_conjunto(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    """Geração média mensal do conjunto, uma cor por trecho de composição, a potência somada de cada trecho tracejada e
    uma linha vertical em cada mudança de composição (um só eixo, em MW)."""
    from src.relatorio.secoes_conjunto import rotulo_trecho

    c = res.conjunto
    trechos = c["trechos"]
    rotulos = {int(r.trecho): (f"Composição {rotulo_trecho(r)}" if i < len(CORES_TRECHOS) else DEMAIS_COMPOSICOES)
               for i, r in enumerate(trechos.itertuples())}
    cores = {}
    for i, rotulo in enumerate(dict.fromkeys(rotulos.values())):
        cores[rotulo] = CORES_TRECHOS[i] if rotulo != DEMAIS_COMPOSICOES else COR_CONTEXTO
    # cada média mensal no meio do mês: a mudança de composição (no dia dela) fica entre os pontos dos dois trechos
    m = c["mensal"].assign(serie=c["mensal"]["trecho"].map(rotulos),
                           meio=pd.to_datetime(c["mensal"]["mes"]) + pd.Timedelta(days=14))
    meses = sorted(pd.to_datetime(m["mes"]).unique())
    poucos = len(meses) <= 36
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    sns.lineplot(data=m, x="meio", y="geracao_media_mw", hue="serie", hue_order=list(cores), palette=cores,
                 units="trecho", estimator=None, linewidth=1.6 if poucos else 1.3, marker="o",
                 markersize=6 if poucos else 2.5, legend=False, ax=ax)
    if c.get("com_capacidade"):  # a potência somada de cada trecho, nas datas do trecho
        for r in trechos.itertuples():
            if pd.notna(r.potencia_somada_mw):
                sns.lineplot(x=[pd.Timestamp(r.inicio), pd.Timestamp(r.fim)], y=[r.potencia_somada_mw] * 2,
                             color=cores[rotulos[int(r.trecho)]], linewidth=1.0, linestyle=(0, (4, 3)), ax=ax)
    for r in list(trechos.itertuples())[1:]:
        ax.axvline(pd.Timestamp(r.inicio), color=COR_TINTA_SUAVE, lw=0.8, ls=(0, (1, 2)), zorder=1)
    ax.set_xlim(pd.Timestamp(meses[0]) - pd.Timedelta(days=5),
                pd.Timestamp(meses[-1]) + pd.offsets.MonthBegin(1) + pd.Timedelta(days=5))
    topo = max(m["geracao_media_mw"].max(), trechos["potencia_somada_mw"].max() if c.get("com_capacidade") else 0)
    ax.set_ylim(0, (topo if pd.notna(topo) and topo > 0 else 1.0) * 1.1)
    ax.set_xlabel("")
    ax.set_ylabel("MW")
    ax.yaxis.set_major_formatter(_FORMATADOR_Y)
    _eixo_tempo(ax, meses[0], meses[-1], diario=False)
    ax.grid(axis="x", visible=False)
    ax.set_title(f"Geração média mensal do conjunto {c.get('nome') or c.get('id')}, por composição")
    alcas = [plt.Line2D([], [], color=cor, lw=2, marker="o", markersize=4, label=nome) for nome, cor in cores.items()]
    if c.get("com_capacidade"):
        alcas.append(plt.Line2D([], [], color=COR_TINTA_SECUNDARIA, lw=1.0, ls=(0, (4, 3)),
                                label="Potência somada do trecho"))
    ax.legend(handles=alcas, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=min(3, len(alcas)))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.9, bottom=0.26 if len(alcas) > 3 else 0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_hidrologia_comum(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    """Vazões afluente, turbinada e vertida médias por mês (um só eixo, em m³/s), com as cores da figura das vazões
    das hidrelétricas com EVT."""
    from src.relatorio.figuras import COR_AFLUENCIA

    m = res.hidrologia["mensal"]
    meses = pd.PeriodIndex(m["mes"], freq="M").to_timestamp()
    vazoes = {"afluencia_media_m3s": ("Vazão afluente", COR_AFLUENCIA),
              "turbinada_media_m3s": ("Vazão turbinada", COR_GERACAO),
              "vertida_media_m3s": ("Vazão vertida", COR_EVT)}
    longo = pd.concat([pd.DataFrame({"mes": meses, "serie": nome, "m3s": m[coluna].to_numpy()})
                       for coluna, (nome, _) in vazoes.items()], ignore_index=True)
    poucos = len(meses) <= 36
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    sns.lineplot(data=longo, x="mes", y="m3s", hue="serie", hue_order=[n for n, _ in vazoes.values()],
                 palette={n: c for n, c in vazoes.values()}, linewidth=1.6 if poucos else 1.2,
                 marker="o" if poucos else None, markersize=4, legend=False, ax=ax)
    ax.axhline(perfil_ativo().engolimento_maximo_m3s, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    _rotulo_referencia(ax, perfil_ativo().engolimento_maximo_m3s,
                       f"Engolimento máximo\n{fmt_num(perfil_ativo().engolimento_maximo_m3s, 0)} m³/s")
    ax.set_xlim(meses.min() - pd.Timedelta(days=20), meses.max() + pd.Timedelta(days=20))
    ax.set_ylim(bottom=0)
    ax.set_xlabel("")
    ax.set_ylabel("m³/s (média mensal)")
    ax.yaxis.set_major_formatter(_FORMATADOR_Y)
    _eixo_tempo(ax, meses.min(), meses.max(), diario=False)
    ax.grid(axis="x", visible=False)
    ax.set_title("Vazões médias mensais")
    ax.legend(handles=[plt.Line2D([], [], color=cor, lw=2, label=nome) for nome, cor in vazoes.values()],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=3)
    fig.subplots_adjust(left=0.07, right=0.86, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Taxas oficiais e operativas (spec da Geração do relatório, FR-071): a mesma figura nas duas trilhas
# ---------------------------------------------------------------------------


def grafico_taxas_operativas(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    """TEIFa e TEIP, oficial e operativa, por mês, em dois painéis; a operativa tracejada (identidade além da cor)."""
    s = res.ons["taxas_operativas"]["serie"]
    oficial, operativa = "Oficial (Taxas TEIFa e TEIP)", "Operativa (Taxas TEIFa Oper e TEIP Oper)"
    cores = {oficial: COR_GERACAO, operativa: COR_EVT}
    meses = sorted(s["mes"].unique())
    poucos = len(meses) <= 36  # série longa: só as linhas, sem um ponto por mês
    fig, eixos = plt.subplots(1, 2, figsize=TAMANHO_FIGURA_PADRONIZADA)
    for ax, (taxa, nome) in zip(eixos, (("teifa", "TEIFa"), ("teip", "TEIP"))):
        longo = pd.concat([pd.DataFrame({"mes": s["mes"], "serie": oficial, "pct": s[f"{taxa}_pct"]}),
                           pd.DataFrame({"mes": s["mes"], "serie": operativa, "pct": s[f"{taxa}_oper_pct"]})],
                          ignore_index=True).dropna(subset=["pct"])
        sns.lineplot(data=longo, x="mes", y="pct", hue="serie", hue_order=list(cores), palette=cores, style="serie",
                     style_order=list(cores), dashes={oficial: "", operativa: (4, 2)},
                     linewidth=1.6 if poucos else 1.3, marker="o" if poucos else None, markersize=4, legend=False,
                     ax=ax)
        ax.set_xlim(pd.Timestamp(meses[0]) - pd.Timedelta(days=20), pd.Timestamp(meses[-1]) + pd.Timedelta(days=20))
        ax.set_ylim(bottom=0)
        ax.set_xlabel("")
        ax.set_ylabel(f"{nome} (%)")
        ax.yaxis.set_major_formatter(_FORMATADOR_Y)
        _eixo_tempo(ax, meses[0], meses[-1], diario=False)
        ax.grid(axis="x", visible=False)
        ax.set_title(f"{nome}, janela de 60 meses")
    fig.legend(handles=[plt.Line2D([], [], color=cor, lw=2, ls="-" if nome == oficial else (0, (4, 2)),
                                   marker="o" if poucos else None, label=nome) for nome, cor in cores.items()],
               loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=2)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.9, bottom=0.22, wspace=0.22)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _renovavel(res: ResultadosAnalise, chave: str) -> dict:
    return (getattr(res, "renovavel", None) or {}).get(chave) or {}


def _com_inflexibilidade(res: ResultadosAnalise) -> bool:
    r = (getattr(res, "termica", None) or {}).get("inflexibilidade_resumo") or {}
    return (r.get("programada_mwh") or 0) > 0 or (r.get("verificada_mwh") or 0) > 0


_GERADORES = {
    "serie_temporal_comum": _grafico_serie_temporal,
    "geracao_mensal": _grafico_geracao_mensal,
    "perfil_horario_comum": _grafico_perfil_horario,
    "sazonalidade": _grafico_sazonalidade,
    "disponibilidade_comum": _grafico_disponibilidade,
    "despacho_motivo_mensal": _grafico_despacho_motivo,
    "inflexibilidade_mensal": _grafico_inflexibilidade,
    "desvios_despacho": _grafico_desvios,
    "cvu_cmo": _grafico_cvu_cmo,
    "fc_mensal": _grafico_fc_mensal,
    "corte_razao_mensal": _grafico_corte_razao,
    "recurso_geracao": _grafico_recurso,
    "desvio_programacao": _grafico_desvio_programacao,
    "conjunto_mensal": _grafico_conjunto,
    "hidrologia_mensal_comum": _grafico_hidrologia_comum,
    "taxas_operativas": grafico_taxas_operativas,
}
_CONDICOES = {
    "sazonalidade": lambda res: len(res.comum["sazonalidade"]) > 0,
    "disponibilidade_comum": lambda res: bool(res.comum.get("disponibilidade")),
    "despacho_motivo_mensal": lambda res: bool(getattr(res, "termica", None)) and not res.termica["sem_geracao"],
    "inflexibilidade_mensal": _com_inflexibilidade,
    "desvios_despacho": lambda res: bool(getattr(res, "termica", None))
    and len(res.termica["atendimento"]["maiores_desvios"]) > 0,
    "cvu_cmo": lambda res: bool((getattr(res, "termica", None) or {}).get("cvu_cmo")),
    "fc_mensal": lambda res: bool(_renovavel(res, "fator_capacidade")),
    "corte_razao_mensal": lambda res: bool(_renovavel(res, "restricao"))
    and len(_renovavel(res, "restricao")["por_razao"]) > 0,
    "recurso_geracao": lambda res: bool(_renovavel(res, "recurso")) and len(_renovavel(res, "recurso")["faixas"]) > 0,
    "desvio_programacao": lambda res: bool(_renovavel(res, "programacao"))
    and len(_renovavel(res, "programacao")["maiores_desvios"]) > 0,
    "conjunto_mensal": lambda res: bool(getattr(res, "conjunto", None)) and len(res.conjunto["mensal"]) > 0,
    "hidrologia_mensal_comum": lambda res: bool((getattr(res, "hidrologia", None) or {}).get("publicado"))
    and len(res.hidrologia.get("mensal", ())) > 0,
    "taxas_operativas": lambda res: bool(((res.ons or {}).get("taxas_operativas") or {}).get("figura")),
}


def gerar_graficos_comum(res: ResultadosAnalise, pasta: Path, dpi: int) -> Dict[str, Path]:
    """Figuras das usinas sem EVT; as opcionais só com a base. Remove as opcionais de uma execução anterior."""
    pasta.mkdir(parents=True, exist_ok=True)
    caminhos = {chave: pasta / nome for chave, nome in NOMES_FIGURAS_COMUM.items()}
    caminhos.update({chave: pasta / nome for chave, nome in NOMES_FIGURAS_COMUM_OPCIONAIS.items()
                     if _CONDICOES[chave](res)})
    with _tema_graficos():
        for chave, caminho in caminhos.items():
            _GERADORES[chave](res, caminho, dpi)
    for nome in NOMES_FIGURAS_COMUM_OPCIONAIS.values():
        antiga = pasta / nome
        if antiga not in caminhos.values() and antiga.exists():
            antiga.unlink()
            logger.info("Figura de execução anterior removida: %s", nome)
    logger.info("Gráficos gerados: %d", len(caminhos))
    return caminhos
