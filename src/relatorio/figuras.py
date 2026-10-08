"""Figuras do relatório, em seaborn, desenhadas só a partir dos resultados das Análises."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

from src.analises.comum import _rotulo_janela
from src.analises.hidrologia import (
    ACIMA_ENGOLIMENTO_USINA,
    ATE_UMA_UNIDADE,
    COM_PARADA_EVT,
    DEMAIS_DIAS,
    entre_unidades,
    faixas_afluencia,
    unidades_por_extenso,
    SEM_DADO_HIDROLOGICO,
)
from src.analises.resultados import ResultadosAnalise
from src.comum.formatacao import fmt_int, fmt_mes_ano, fmt_num, fmt_pct
from src.comum.logger import setup_logger
from src.comum.perfil import perfil_ativo
from src.comum.regras import (
    DEFAULT_PLOT_DPI,
    DURACAO_MINIMA_EVENTO_RELATORIO_H,
    HORAS_DIURNAS,
    TAMANHO_FIGURA_PADRONIZADA,
)

logger = setup_logger("relatorio")


# Paleta (validada com o script do skill de dataviz sobre superfície branca)
COR_GERACAO = "#2a78d6"


COR_EVT = "#eb6834"
COR_DISPONIBILIDADE = "#1baf7a"
COR_CONTEXTO = "#b5b3ac"
COR_TINTA = "#0b0b0b"
COR_TINTA_SECUNDARIA = "#52514e"
COR_TINTA_SUAVE = "#898781"
COR_GRADE = "#e1e0d9"
COR_EIXO = "#c3c2b7"
COR_FAIXA_INDISPONIBILIDADE = "#e7e5de"
RAMPA_AZUL = ["#f3f8fe", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
RAMPA_LARANJA = ["#fdf3ee", "#f9d6c4", "#f4b08f", "#ef8a5d", "#eb6834", "#c24f1f", "#8c3612"]


# Bases complementares. Cores validadas com o script da skill de visualização sobre fundo branco:
# disponibilidade sincronizada = posição 4 da ordem categórica (amarelo; contraste < 3:1 compensado por rótulo
# direto e tabela); vazão afluente = posição 7 (violeta), a única que passa em todos os pares com turbinada e
# vertida (linhas que se cruzam); faixas de afluência = rampa ordinal de laranja (horas com EVT), passos com
# contraste mínimo de 2,48:1 no passo claro.
COR_SINCRONIZADA = "#eda100"


COR_AFLUENCIA = "#4a3aa7"
RAMPA_FAIXAS_AFLUENCIA = [RAMPA_LARANJA[3], RAMPA_LARANJA[5], RAMPA_LARANJA[6]]
NOMES_FIGURAS: Dict[str, str] = {
    "serie_temporal": "01_serie_temporal_disponibilidade_geracao_evt.png",
    "evt_mensal": "02_evt_mensal.png",
    "perfil_horario": "03_perfil_horario_geracao_evt.png",
    "disponibilidade_anual": "04_disponibilidade_geracao_anual.png",
    "vazoes_defluentes": "05_vazoes_defluentes_anuais.png",
}


# Figuras das bases complementares: geradas só quando os dados correspondentes existem.
# Cada história acrescenta aqui a sua figura junto com a função _grafico_* correspondente.
NOMES_FIGURAS_OPCIONAIS: Dict[str, str] = {
    "disponibilidade_sincronizada": "06_disponibilidade_operacional_sincronizada_mensal.png",
    "faixas_afluencia": "07_evt_por_faixa_de_afluencia.png",
    "perfil_hidrologico": "08_perfil_horario_nivel_vazoes.png",
}


def _estilo_graficos() -> Dict[str, Any]:
    """Parâmetros visuais comuns às figuras (tipografia, eixos, grade e fundo)."""
    nomes = {f.name for f in font_manager.fontManager.ttflist}
    fonte = "Arial" if "Arial" in nomes else "DejaVu Sans"
    return {
        "font.family": fonte,
        "font.size": 9,
        "axes.titlesize": 10.5,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlecolor": COR_TINTA,
        "axes.titlepad": 10,
        "axes.labelsize": 9,
        "axes.labelcolor": COR_TINTA_SECUNDARIA,
        "axes.edgecolor": COR_EIXO,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": COR_GRADE,
        "grid.linewidth": 0.6,
        "grid.linestyle": "-",
        "xtick.color": COR_TINTA_SECUNDARIA,
        "ytick.color": COR_TINTA_SECUNDARIA,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "legend.frameon": False,
        "legend.fontsize": 8.5,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
    }


# Ordem categórica fixa (validada com o script da skill de visualização sobre fundo branco)
PALETA_CATEGORICA: List[str] = [COR_GERACAO, COR_DISPONIBILIDADE, COR_EVT]


# Intervalo na cor do fundo entre segmentos empilhados e barras vizinhas (pt)
LARGURA_INTERVALO_BARRAS = 0.8


@contextmanager
def _tema_graficos():
    """Tema único das figuras: seaborn com o estilo e a paleta do projeto; restaura o rc ao sair."""
    with plt.rc_context():
        sns.set_theme(style="ticks", palette=PALETA_CATEGORICA, rc=_estilo_graficos())
        yield


_FORMATADOR_PT = FuncFormatter(lambda v, _: fmt_num(v, 0))


def _rotulos_anos(anos: List[int], parciais: List[int]) -> List[str]:
    return [f"{int(a)}*" if int(a) in parciais else str(int(a)) for a in anos]


def _rotulo_referencia(ax: plt.Axes, y: float, texto: str) -> None:
    """Rótulo de linha de referência fora da área de plotagem, à direita."""
    ax.text(1.01, y, texto, transform=ax.get_yaxis_transform(), ha="left", va="center",
            fontsize=8, color=COR_TINTA_SECUNDARIA, clip_on=False)


def _grafico_serie_temporal(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    P = perfil_ativo().parametros.potencia_instalada_mw
    diario = res.serie_diaria  # médias diárias calculadas nas Análises
    nomes = {
        "val_disponibilidade": "Disponibilidade declarada",
        "val_geracao": "Geração",
        "val_energiavertidaturbinavel": "Energia vertida turbinável (EVT)",
    }
    cores = {nomes["val_disponibilidade"]: COR_DISPONIBILIDADE, nomes["val_geracao"]: COR_GERACAO,
             nomes["val_energiavertidaturbinavel"]: COR_EVT}
    longo = (
        diario.reset_index()
        .melt(id_vars="din_instante", var_name="serie", value_name="mw")
        .assign(serie=lambda d: d["serie"].map(nomes))
    )
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    eventos = res.eventos_indisponibilidade_total
    longos = eventos[eventos["duracao_h"] >= DURACAO_MINIMA_EVENTO_RELATORIO_H] if len(eventos) else eventos
    for ev in longos.itertuples():
        ax.axvspan(ev.inicio, ev.fim, color=COR_FAIXA_INDISPONIBILIDADE, lw=0, zorder=0)
    ax.fill_between(diario.index, 0, diario["val_energiavertidaturbinavel"], color=COR_EVT, alpha=0.22, lw=0, zorder=1)
    sns.lineplot(data=longo, x="din_instante", y="mw", hue="serie", hue_order=list(cores), palette=cores,
                 estimator=None, errorbar=None, linewidth=1.0, legend=False, ax=ax)
    ax.axhline(P, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax.axhline(perfil_ativo().parametros.garantia_fisica_mwmed, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (1, 2)), zorder=1)
    _rotulo_referencia(ax, P, f"Potência instalada\n{fmt_num(P, 0)} MW")
    _rotulo_referencia(ax, perfil_ativo().parametros.garantia_fisica_mwmed, f"Garantia física\n{fmt_num(perfil_ativo().parametros.garantia_fisica_mwmed, 1)} MWmed")

    ax.set_xlim(diario.index.min(), diario.index.max())
    ax.set_ylim(0, P * 1.15)
    ax.set_xlabel("")
    ax.set_ylabel("MW médios (média diária)")
    ax.yaxis.set_major_formatter(_FORMATADOR_PT)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_title("Disponibilidade declarada, geração e energia vertida turbinável (médias diárias)")

    legendas = [
        plt.Line2D([], [], color=COR_DISPONIBILIDADE, lw=2, label="Disponibilidade declarada"),
        plt.Line2D([], [], color=COR_GERACAO, lw=2, label="Geração"),
        Patch(facecolor=COR_EVT, alpha=0.6, label="Energia vertida turbinável (EVT)"),
    ]
    if len(longos):
        legendas.append(Patch(facecolor=COR_FAIXA_INDISPONIBILIDADE,
                              label=f"Indisponibilidade total ≥ {DURACAO_MINIMA_EVENTO_RELATORIO_H} h"))
    ax.legend(handles=legendas, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=len(legendas))
    fig.subplots_adjust(left=0.07, right=0.86, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_evt_mensal(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    m = res.evt_mensal
    rotulo_minimo = f"EVT em horas com vertimento de até {fmt_num(perfil_ativo().analises.vertimento_minimo_m3s, 0)} m³/s (patamar contínuo)"
    rotulo_demais = "EVT nas demais horas"
    cores = {rotulo_minimo: COR_CONTEXTO, rotulo_demais: COR_EVT}
    longo = pd.concat([
        pd.DataFrame({"mes": m["mes"], "parcela": rotulo_minimo, "mwh": m["evt_vertimento_minimo_mwh"]}),
        pd.DataFrame({"mes": m["mes"], "parcela": rotulo_demais, "mwh": m["evt_demais_horas_mwh"]}),
    ], ignore_index=True)
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    if len(m):
        limites = list(m["mes"]) + [m["mes"].max() + pd.offsets.MonthBegin(1)]
        # o seaborn empilha da última categoria (base) para a primeira (topo)
        sns.histplot(data=longo, x="mes", weights="mwh", hue="parcela", hue_order=[rotulo_demais, rotulo_minimo],
                     palette=cores, multiple="stack", bins=[float(b) for b in mdates.date2num(limites)],
                     shrink=0.85, alpha=1, edgecolor="white", linewidth=0.3, legend=False, ax=ax)

    mc = res.mudanca_classificacao
    topo = float((m["evt_mwh"]).max()) * 1.12 if len(m) else 1.0
    if mc.get("mes") is not None:
        x = mc["mes"].start_time
        ax.axvline(x, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (4, 3)))
        ax.text(x, topo * 0.98, f"  {fmt_mes_ano(mc['mes'])}: parte do vertimento contínuo passa a\n"
                                f"  ser registrada como não turbinável", ha="left", va="top", fontsize=8,
                color=COR_TINTA_SECUNDARIA)
    if len(m):
        ax.set_xlim(m["mes"].min() - pd.Timedelta(days=5), m["mes"].max() + pd.Timedelta(days=36))
    ax.set_ylim(0, topo)
    ax.set_xlabel("")
    ax.set_ylabel("EVT mensal (MWh)")
    ax.yaxis.set_major_formatter(_FORMATADOR_PT)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(axis="x", visible=False)
    ax.set_title("Energia vertida turbinável mensal")
    ax.legend(handles=[Patch(facecolor=COR_CONTEXTO, label=rotulo_minimo), Patch(facecolor=COR_EVT, label=rotulo_demais)],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=2)
    fig.subplots_adjust(left=0.07, right=0.97, top=0.9, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_perfil_horario(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    parciais = res.cobertura["anos_parciais"]
    fig, eixos = plt.subplots(1, 2, figsize=(11, 4.4))
    paineis = [
        (res.perfil_horario_geracao, RAMPA_AZUL, "Geração média por hora do dia (MW)"),
        (res.perfil_horario_evt, RAMPA_LARANJA, "EVT média por hora do dia (MWmed)"),
    ]
    for ax, (tabela, rampa, titulo) in zip(eixos, paineis):
        mapa = LinearSegmentedColormap.from_list(titulo, rampa)
        sns.heatmap(tabela, cmap=mapa, vmin=0, ax=ax, cbar=True, cbar_kws={"fraction": 0.046, "pad": 0.02},
                    linewidths=0, xticklabels=False, yticklabels=False)
        ax.set_yticks([i + 0.5 for i in range(len(tabela.index))])
        ax.set_yticklabels(_rotulos_anos(list(tabela.index), parciais), rotation=0)
        ax.set_xticks([h + 0.5 for h in range(0, 24, 3)])
        ax.set_xticklabels([f"{h}h" for h in range(0, 24, 3)], rotation=0)
        ax.set_xlabel("Hora do dia")
        ax.set_ylabel("")
        ax.grid(False)
        for lado in ("left", "bottom"):
            ax.spines[lado].set_visible(False)
        ax.set_title(titulo)
        barra = ax.collections[0].colorbar
        barra.outline.set_visible(False)
        barra.ax.tick_params(labelsize=8, length=0)
        barra.ax.yaxis.set_major_formatter(_FORMATADOR_PT)
    if parciais:
        fig.text(0.01, 0.015, "* ano parcial", fontsize=8, color=COR_TINTA_SUAVE)
    fig.subplots_adjust(left=0.06, right=0.97, top=0.9, bottom=0.14, wspace=0.28)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_disponibilidade_anual(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    a = res.indicadores_anuais
    parciais = res.cobertura["anos_parciais"]
    rotulos = _rotulos_anos(a["ano"].tolist(), parciais)
    nomes = {"disponibilidade_relativa_pct": "Disponibilidade média declarada",
             "fator_capacidade_pct": "Geração média (fator de capacidade)"}
    cores = {nomes["disponibilidade_relativa_pct"]: COR_DISPONIBILIDADE, nomes["fator_capacidade_pct"]: COR_GERACAO}
    longo = (
        a.assign(rotulo=rotulos)
        .melt(id_vars="rotulo", value_vars=list(nomes), var_name="indicador", value_name="pct")
        .assign(indicador=lambda d: d["indicador"].map(nomes))
    )
    fig, ax = plt.subplots(figsize=(11, 4.6))
    sns.barplot(data=longo, x="rotulo", y="pct", hue="indicador", order=rotulos, hue_order=list(cores),
                palette=cores, errorbar=None, width=0.76, gap=0.06, saturation=1, legend=False, ax=ax)
    referencia = perfil_ativo().disponibilidade_referencia * 100
    gf_rel = perfil_ativo().parametros.garantia_fisica_mwmed / perfil_ativo().parametros.potencia_instalada_mw * 100
    ax.axhline(referencia, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (4, 3)))
    ax.axhline(gf_rel, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (1, 2)))
    _rotulo_referencia(ax, referencia, f"Disponibilidade de\nreferência (GF): {fmt_pct(referencia)}")
    _rotulo_referencia(ax, gf_rel, f"Garantia física:\n{fmt_pct(gf_rel)} da potência")
    ax.set_ylim(0, 105)
    ax.set_xlabel("")
    ax.set_ylabel("% da potência instalada")
    ax.yaxis.set_major_formatter(_FORMATADOR_PT)
    ax.grid(axis="x", visible=False)
    ax.set_title("Disponibilidade média e geração média por ano (% da potência instalada)")
    ax.legend(handles=[Patch(facecolor=c, label=n) for n, c in cores.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
    if parciais:
        fig.text(0.01, 0.02, "* ano parcial", fontsize=8, color=COR_TINTA_SUAVE)
    fig.subplots_adjust(left=0.07, right=0.84, top=0.89, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_vazoes_defluentes(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    parciais = res.cobertura["anos_parciais"]
    nomes = {
        "val_vazaoturbinada": "Vazão turbinada",
        "val_vazaovertidaturbinavel": "Vazão vertida turbinável",
        "val_vazaovertidanaoturbinavel": "Vazão vertida não turbinável",
    }
    cores = {nomes["val_vazaoturbinada"]: COR_GERACAO, nomes["val_vazaovertidaturbinavel"]: COR_EVT,
             nomes["val_vazaovertidanaoturbinavel"]: COR_CONTEXTO}
    v = res.vazoes_anuais[list(nomes)]  # médias anuais calculadas nas Análises
    longo = (
        v.reset_index()
        .melt(id_vars="ano", var_name="componente", value_name="m3s")
        .assign(componente=lambda d: d["componente"].map(nomes))
    )
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    # o seaborn empilha da última categoria (base) para a primeira (topo): turbinada na base
    sns.histplot(data=longo, x="ano", weights="m3s", hue="componente", hue_order=list(reversed(list(cores))),
                 palette=cores, multiple="stack", discrete=True, shrink=0.6, alpha=1, edgecolor="white",
                 linewidth=LARGURA_INTERVALO_BARRAS, legend=False, ax=ax)
    ax.axhline(perfil_ativo().engolimento_maximo_m3s, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (4, 3)))
    _rotulo_referencia(ax, perfil_ativo().engolimento_maximo_m3s,
                       f"Engolimento máximo\n{perfil_ativo().parametros.unidades_geradoras} × {fmt_num(perfil_ativo().parametros.engolimento_nominal_ug_m3s, 1)} m³/s")
    ax.set_xticks(list(v.index))
    ax.set_xticklabels(_rotulos_anos(v.index.tolist(), parciais))
    topo = float(v.sum(axis=1).max()) if len(v) else 0.0
    ax.set_ylim(0, max(topo, perfil_ativo().engolimento_maximo_m3s) * 1.1)
    ax.set_xlabel("")
    ax.set_ylabel("m³/s (média anual)")
    ax.yaxis.set_major_formatter(_FORMATADOR_PT)
    ax.grid(axis="x", visible=False)
    ax.set_title("Vazões defluentes médias por ano: turbinada, vertida turbinável e vertida não turbinável")
    ax.legend(handles=[Patch(facecolor=c, label=n) for n, c in cores.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3)
    if parciais:
        fig.text(0.01, 0.02, "* ano parcial", fontsize=8, color=COR_TINTA_SUAVE)
    fig.subplots_adjust(left=0.07, right=0.84, top=0.89, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _rotulos_no_fim(ax: plt.Axes, pontos: List[Tuple[float, str]], x_fim: Any, folga_minima: float) -> None:
    """Rótulos diretos à direita do fim das linhas; omitidos se dois ficarem próximos demais (fica a legenda)."""
    valores = sorted(v for v, _ in pontos if pd.notna(v))
    if len(valores) < len(pontos) or any(b - a < folga_minima for a, b in zip(valores, valores[1:])):
        return
    for valor, texto in pontos:
        ax.annotate(texto, xy=(x_fim, valor), xytext=(6, 0), textcoords="offset points", ha="left", va="center",
                    fontsize=8, color=COR_TINTA_SECUNDARIA, annotation_clip=False)


def _grafico_disponibilidade_sincronizada(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    """Figura 06: médias mensais de disponibilidade operacional e sincronizada e de geração."""
    m = res.disponibilidade["mensal"].copy()
    m["mes"] = pd.PeriodIndex(m["periodo"], freq="M").to_timestamp()
    series = {
        "Disponibilidade operacional": ("disp_operacional_media_mw", COR_DISPONIBILIDADE),
        "Disponibilidade sincronizada": ("disp_sincronizada_media_mw", COR_SINCRONIZADA),
        "Geração": ("geracao_media_mw", COR_GERACAO),
    }
    longo = pd.concat(
        [pd.DataFrame({"mes": m["mes"], "serie": nome, "mw": m[coluna]}) for nome, (coluna, _) in series.items()],
        ignore_index=True,
    )
    fig, ax = plt.subplots(figsize=TAMANHO_FIGURA_PADRONIZADA)
    sns.lineplot(data=longo, x="mes", y="mw", hue="serie", hue_order=list(series),
                 palette={nome: cor for nome, (_, cor) in series.items()}, linewidth=1.4, legend=False, ax=ax)
    ax.axhline(perfil_ativo().parametros.potencia_instalada_mw, color=COR_TINTA_SUAVE, lw=0.9, ls=(0, (4, 3)), zorder=1)
    _rotulo_referencia(ax, perfil_ativo().parametros.potencia_instalada_mw, f"Potência instalada\n{fmt_num(perfil_ativo().parametros.potencia_instalada_mw, 0)} MW")
    if len(m):
        ultimo = m.iloc[-1]
        _rotulos_no_fim(ax, [(ultimo[c], n) for n, (c, _) in series.items()], ultimo["mes"], folga_minima=3.5)
        ax.set_xlim(m["mes"].min() - pd.Timedelta(days=20), m["mes"].max() + pd.Timedelta(days=20))
    ax.set_ylim(0, perfil_ativo().parametros.potencia_instalada_mw * 1.08)
    ax.set_xlabel("")
    ax.set_ylabel("MW (média mensal)")
    ax.yaxis.set_major_formatter(_FORMATADOR_PT)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(axis="x", visible=False)
    ax.set_title("Disponibilidade operacional e sincronizada e geração: médias mensais (ONS)")
    ax.legend(handles=[plt.Line2D([], [], color=cor, lw=2, label=nome) for nome, (_, cor) in series.items()],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=3)
    fig.subplots_adjust(left=0.07, right=0.80, top=0.89, bottom=0.2)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_faixas_afluencia(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    """Figura 07: horas com EVT por faixa de afluência, por ano (rampa ordinal de laranja)."""
    t = res.hidrologia["faixas_anual"].copy()
    t["ano"] = t["periodo"].astype(int)
    rotulos = {
        ATE_UMA_UNIDADE: f"Afluência até {fmt_num(perfil_ativo().parametros.engolimento_nominal_ug_m3s, 1)} m³/s (cabia em uma unidade)",
        entre_unidades(): f"{fmt_num(perfil_ativo().parametros.engolimento_nominal_ug_m3s, 1)} a "
                          f"{fmt_num(perfil_ativo().engolimento_maximo_m3s, 0)} m³/s (cabia nas {unidades_por_extenso()})",
        ACIMA_ENGOLIMENTO_USINA: f"Acima de {fmt_num(perfil_ativo().engolimento_maximo_m3s, 0)} m³/s (acima do engolimento máximo)",
        SEM_DADO_HIDROLOGICO: "Sem dado hidrológico",
    }
    cores = dict(zip([rotulos[f] for f in (ATE_UMA_UNIDADE, entre_unidades(), ACIMA_ENGOLIMENTO_USINA)],
                     RAMPA_FAIXAS_AFLUENCIA))
    cores[rotulos[SEM_DADO_HIDROLOGICO]] = COR_CONTEXTO
    t["faixa"] = t["faixa_afluencia"].map(rotulos)
    ordem_base_ao_topo = [rotulos[f] for f in faixas_afluencia()]
    fig, ax = plt.subplots(figsize=(11, 4.6))
    # o seaborn empilha da última categoria (base) para a primeira (topo): faixa de menor afluência na base
    sns.histplot(data=t, x="ano", weights="horas", hue="faixa", hue_order=list(reversed(ordem_base_ao_topo)),
                 palette=cores, multiple="stack", discrete=True, shrink=0.6, alpha=1, edgecolor="white",
                 linewidth=LARGURA_INTERVALO_BARRAS, legend=False, ax=ax)
    totais = t.groupby("ano")["horas"].sum()
    for ano, total in totais.items():
        ax.annotate(fmt_int(total), xy=(ano, total), xytext=(0, 3), textcoords="offset points", ha="center",
                    va="bottom", fontsize=8, color=COR_TINTA_SECUNDARIA)
    anos = totais.index.tolist()
    parciais = [int(a) for a in t.loc[t["ano_parcial"], "ano"].unique()]
    ax.set_xticks(anos)
    ax.set_xticklabels(_rotulos_anos(anos, parciais))
    ax.set_ylim(0, float(totais.max()) * 1.12 if len(totais) else 1)
    ax.set_xlabel("")
    ax.set_ylabel("Horas com EVT")
    ax.yaxis.set_major_formatter(_FORMATADOR_PT)
    ax.grid(axis="x", visible=False)
    ax.set_title("Horas com energia vertida turbinável por faixa de afluência ao reservatório")
    ax.legend(handles=[Patch(facecolor=cores[r], label=r) for r in ordem_base_ao_topo],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=2)
    if parciais:
        fig.text(0.01, 0.02, "* ano parcial", fontsize=8, color=COR_TINTA_SUAVE)
    fig.subplots_adjust(left=0.07, right=0.97, top=0.89, bottom=0.25)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_perfil_hidrologico(res: ResultadosAnalise, caminho: Path, dpi: int) -> None:
    """Figura 08: vazões e nível de montante médios por hora do dia, em dois painéis (sem eixo duplo)."""
    p = res.hidrologia["perfil"]
    grupos = {COM_PARADA_EVT: "Dias com parada com EVT", DEMAIS_DIAS: "Demais dias"}
    tracos = {grupos[COM_PARADA_EVT]: "", grupos[DEMAIS_DIAS]: (4, 2)}
    vazoes = {"afluencia_media_m3s": ("Vazão afluente", COR_AFLUENCIA),
              "turbinada_media_m3s": ("Vazão turbinada", COR_GERACAO),
              "vertida_media_m3s": ("Vazão vertida", COR_EVT)}
    longo = pd.concat([
        pd.DataFrame({"hora": p["hora"], "grupo": p["grupo_dias"].map(grupos), "variavel": nome, "m3s": p[coluna]})
        for coluna, (nome, _) in vazoes.items()
    ], ignore_index=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1.7, 1]})
    for ax in (ax1, ax2):
        ax.axvspan(min(HORAS_DIURNAS) - 0.5, max(HORAS_DIURNAS) + 0.5, color=COR_FAIXA_INDISPONIBILIDADE, lw=0, zorder=0)
    sns.lineplot(data=longo, x="hora", y="m3s", hue="variavel", style="grupo", palette={n: c for n, c in vazoes.values()},
                 dashes=tracos, hue_order=[n for n, _ in vazoes.values()], style_order=list(tracos), linewidth=1.4,
                 legend=False, ax=ax1)
    nivel = p.assign(grupo=p["grupo_dias"].map(grupos))
    sns.lineplot(data=nivel, x="hora", y="nivel_montante_medio_m", style="grupo", dashes=tracos,
                 style_order=list(tracos), color=COR_TINTA_SECUNDARIA, linewidth=1.4, legend=False, ax=ax2)
    for ax, titulo, rotulo_y in ((ax1, "Vazões médias por hora do dia", "m³/s"),
                                 (ax2, "Nível de montante médio por hora do dia", "m")):
        ax.set_title(titulo)
        ax.set_xlabel("Hora do dia")
        ax.set_ylabel(rotulo_y)
        ax.set_xticks(range(0, 24, 3))
        ax.set_xticklabels([f"{h}h" for h in range(0, 24, 3)])
        ax.set_xlim(-0.5, 23.5)
        ax.grid(axis="x", visible=False)
    ax1.set_ylim(bottom=0)
    ax1.yaxis.set_major_formatter(_FORMATADOR_PT)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_num(v, 2)))
    alcas = [plt.Line2D([], [], color=c, lw=2, label=n) for n, c in vazoes.values()]
    alcas += [plt.Line2D([], [], color=COR_TINTA_SECUNDARIA, lw=2, label="Nível de montante")]
    alcas += [plt.Line2D([], [], color=COR_TINTA_SUAVE, lw=1.6, ls="-", label=grupos[COM_PARADA_EVT]),
              plt.Line2D([], [], color=COR_TINTA_SUAVE, lw=1.6, ls=(0, (4, 2)), label=grupos[DEMAIS_DIAS]),
              Patch(facecolor=COR_FAIXA_INDISPONIBILIDADE, label=f"Janela das {_rotulo_janela(HORAS_DIURNAS)}")]
    fig.legend(handles=alcas, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 0.0), frameon=False)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.89, bottom=0.27, wspace=0.22)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def gerar_graficos(
    res: ResultadosAnalise,
    diretorio_figuras: Path,
    dpi: int = DEFAULT_PLOT_DPI,
) -> Dict[str, Path]:
    """Gera as figuras do relatório com seaborn, só a partir dos resultados, e retorna {chave: caminho}."""
    pasta = Path(diretorio_figuras)
    pasta.mkdir(parents=True, exist_ok=True)
    logger.info("Gerando gráficos analíticos (%d DPI) em: %s", dpi, pasta)
    caminhos = {chave: pasta / nome for chave, nome in NOMES_FIGURAS.items()}
    with _tema_graficos():
        _grafico_serie_temporal(res, caminhos["serie_temporal"], dpi)
        _grafico_evt_mensal(res, caminhos["evt_mensal"], dpi)
        _grafico_perfil_horario(res, caminhos["perfil_horario"], dpi)
        _grafico_disponibilidade_anual(res, caminhos["disponibilidade_anual"], dpi)
        _grafico_vazoes_defluentes(res, caminhos["vazoes_defluentes"], dpi)
        for chave, nome in NOMES_FIGURAS_OPCIONAIS.items():
            gerador, disponivel = _GERADORES_OPCIONAIS[chave]
            if disponivel(res):
                caminhos[chave] = pasta / nome
                gerador(res, caminhos[chave], dpi)
    for nome in NOMES_FIGURAS_OPCIONAIS.values():  # figura opcional de uma execução anterior, não gerada agora
        antiga = pasta / nome
        if antiga not in caminhos.values() and antiga.exists():
            antiga.unlink()
            logger.info("Figura de execução anterior removida: %s", nome)
    logger.info("Gráficos gerados: %d", len(caminhos))
    return caminhos


# Figuras opcionais: chave -> (função que gera, condição para gerar)
_GERADORES_OPCIONAIS: Dict[str, Tuple[Any, Any]] = {
    "disponibilidade_sincronizada": (_grafico_disponibilidade_sincronizada,
                                     lambda res: bool(res.disponibilidade) and len(res.disponibilidade["mensal"]) > 0),
    "faixas_afluencia": (_grafico_faixas_afluencia,
                         lambda res: bool(res.hidrologia.get("publicado")) and len(res.hidrologia["faixas_anual"]) > 0),
    "perfil_hidrologico": (_grafico_perfil_hidrologico,
                           lambda res: bool(res.hidrologia.get("publicado")) and len(res.hidrologia["perfil"]) > 0),
}
