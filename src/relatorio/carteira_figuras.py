"""Figuras do relatório de carteira, em seaborn (spec da Geração do relatório, FR-049; plano, D22).

- ``ordenacao``: itens da conclusão por usina, na ordem da ordenação, em barras horizontais empilhadas pelas quatro
  listas, na ordem da conclusão;
- ``panorama`` (só na carteira com estado): energia mensal dos agregados, em barras empilhadas por modalidade e tipo.

Mesmo tema e mesmas cores das figuras da usina (``src/relatorio/figuras.py``). As duas paletas seguem a ordem categórica
fixa, validada com o script da skill de visualização sobre fundo branco (contraste abaixo de 3:1 em algumas cores,
compensado pela legenda e pela tabela de cada figura); a cor segue a lista ou a série, nunca a posição.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.ticker import MaxNLocator

from src.analises.conclusao import LISTAS_CONCLUSAO
from src.comum.formatacao import MESES_ABREVIADOS
from src.comum.logger import setup_logger
from src.comum.regras import LARGURA_FIGURA_CARTEIRA as LARGURA_FIGURA
from src.relatorio.figuras import COR_CONTEXTO, COR_TINTA_SECUNDARIA, _tema_graficos
from src.relatorio.figuras_comum import _eixo_mensal, _legenda_retangulos, _limites_dos_meses

logger = setup_logger("relatorio")

NOMES_FIGURAS_CARTEIRA: Dict[str, str] = {
    "ordenacao": "01_itens_da_conclusao_por_usina.png",
    "panorama": "02_panorama_agregados_mensal.png",
}
ORDEM_CATEGORICA = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6")
CORES_LISTAS: Dict[str, str] = {titulo: cor for (_, titulo), cor in zip(LISTAS_CONCLUSAO, ORDEM_CATEGORICA)}
TEXTO_SEM_REGRA = "sem regra avaliada com dado da usina"


def _grafico_ordenacao(itens: Sequence[Tuple[str, Dict[str, object]]], caminho: Path, dpi: int) -> None:
    """``itens``: (nome, contagens) na ordem da ordenação; contagens None ficam sem barra, com o texto."""
    nomes = [nome for nome, _ in itens]
    linhas = [{"usina": nome, "lista": titulo, "itens": float(c.get(chave) or 0)}
              for nome, c in itens for chave, titulo in LISTAS_CONCLUSAO]
    longo = pd.DataFrame(linhas)
    longo["usina"] = pd.Categorical(longo["usina"], categories=nomes, ordered=True)
    titulos = [titulo for _, titulo in LISTAS_CONCLUSAO]
    altura = max(2.6, 0.42 * len(nomes) + 1.6)
    fig, ax = plt.subplots(figsize=(LARGURA_FIGURA, altura))
    # o seaborn empilha o último nível da ordem primeiro: a ordem invertida deixa a primeira lista junto do eixo
    sns.histplot(data=longo, y="usina", weights="itens", hue="lista", hue_order=titulos[::-1], palette=CORES_LISTAS,
                 multiple="stack", discrete=True, shrink=0.7, alpha=1, edgecolor="white", linewidth=0.8,
                 legend=False, ax=ax)
    for nome, c in itens:
        if c.get("regras_avaliadas") == 0:
            ax.text(0.05, nomes.index(nome), TEXTO_SEM_REGRA, va="center", ha="left", fontsize=8,
                    color=COR_TINTA_SECUNDARIA)
    ax.set_yticks(range(len(nomes)), nomes)
    ax.set_ylim(len(nomes) - 0.5, -0.5)  # a primeira da ordenação em cima
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlim(0, max(1.0, longo.groupby("usina", observed=True)["itens"].sum().max()) * 1.08)
    ax.set_xlabel("Quantidade de itens")
    ax.set_ylabel("")
    ax.grid(axis="y", visible=False)
    ax.set_title("Itens da conclusão por usina")
    # legenda no pé da figura, a uma distância fixa em polegadas, qualquer que seja a quantidade de usinas
    fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=cor, label=nome) for nome, cor in CORES_LISTAS.items()],
               loc="lower center", bbox_to_anchor=(0.5, 0.08 / altura), ncol=len(CORES_LISTAS))
    fig.subplots_adjust(left=0.27, right=0.97, top=1 - 0.45 / altura, bottom=1.05 / altura)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def _grafico_panorama(mensal: pd.DataFrame, series: Sequence[str], titulo: str, caminho: Path, dpi: int) -> None:
    """``mensal``: mês (início), série e energia em GWh; ``series`` na ordem categórica fixa (a cor segue a série)."""
    cores = {s: (ORDEM_CATEGORICA[i] if i < len(ORDEM_CATEGORICA) else COR_CONTEXTO) for i, s in enumerate(series)}
    presentes = [s for s in series if mensal.loc[mensal["serie"] == s, "gwh"].sum() > 0]
    dados = mensal[mensal["serie"].isin(presentes)]
    meses: List[pd.Timestamp] = sorted(pd.to_datetime(mensal["mes"]).unique())
    fig, ax = plt.subplots(figsize=(LARGURA_FIGURA, 3.4))
    # o seaborn empilha o último nível da ordem embaixo: a ordem invertida deixa a primeira série na base
    sns.histplot(data=dados, x="mes", weights="gwh", hue="serie", hue_order=presentes[::-1],
                 palette={s: cores[s] for s in presentes}, multiple="stack", bins=_limites_dos_meses(meses),
                 shrink=0.85, alpha=1, edgecolor="white", linewidth=0.3, legend=False, ax=ax)
    _eixo_mensal(ax, meses, "Energia mensal (GWh)", titulo)
    # na largura da página retrato, o rótulo curto no centro de cada barra ("out/25")
    centros = [pd.Timestamp(m) + pd.Timedelta(days=15) for m in meses]
    ax.set_xticks(mdates.date2num(centros),
                  [f"{MESES_ABREVIADOS[m.month - 1]}/{m.year % 100:02d}" for m in map(pd.Timestamp, meses)])
    ax.xaxis.set_minor_locator(plt.NullLocator())
    _legenda_retangulos(ax, {s: cores[s] for s in presentes}, colunas=2)
    fig.subplots_adjust(left=0.1, right=0.97, top=0.9, bottom=0.27)
    fig.savefig(caminho, dpi=dpi)
    plt.close(fig)


def gerar_figuras_carteira(ordenacao: Sequence[Tuple[str, Dict[str, object]]], panorama: pd.DataFrame,
                           series: Sequence[str], titulo_panorama: str, pasta: Path, dpi: int) -> Dict[str, Path]:
    """Desenha as figuras com base: a ordenação, quando alguma usina tem item; o panorama, quando tem energia."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    figuras: Dict[str, Path] = {}
    with _tema_graficos():
        if any(sum(int(c.get(chave) or 0) for chave, _ in LISTAS_CONCLUSAO) for _, c in ordenacao):
            figuras["ordenacao"] = pasta / NOMES_FIGURAS_CARTEIRA["ordenacao"]
            _grafico_ordenacao(ordenacao, figuras["ordenacao"], dpi)
        if panorama is not None and len(panorama) and panorama["gwh"].sum() > 0:
            figuras["panorama"] = pasta / NOMES_FIGURAS_CARTEIRA["panorama"]
            _grafico_panorama(panorama, series, titulo_panorama, figuras["panorama"], dpi)
    for chave, caminho in figuras.items():
        logger.info("Figura da carteira gravada: %s", caminho.name)
    return figuras
