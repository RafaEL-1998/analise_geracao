"""Anexo da fiscalização: eventos das unidades geradoras pelo SAGER do ONS (fora do fluxo de cinco etapas).

O relatório "SAGER – Mudança de Estado Operativo de UGE" não é publicado nos dados abertos do ONS: ele é entregue pelo
agente fiscalizado em resposta a ofício da AGEMS. Por isso fica fora do pipeline, como anexo da fiscalização
(decisão do usuário de 23/10/2026; avaliação em `.specify/assessments/sager-eventos-ug/`).

O script lê o arquivo do SAGER e os dados que o pipeline já tratou para a usina (`data/usinas/<slug>/tratamento/`:
horas por estado operativo publicadas pelo ONS, energia vertida turbinável e programação diária) e grava em
`usinas/<slug>/documentos/anexo_sager/` (fora do git):
- `anexo_sager.md` e `anexo_sager.pdf`, com o mesmo conteúdo;
- `anexo_sager.xlsx`, com os eventos e as tabelas;
- `figures/`, com as figuras em seaborn.

Os comentários do SAGER trazem nomes, logins e e-mails de pessoas; o anexo guarda só o texto do evento, e o script
para com erro se sobrar algum e-mail ou login.

Regras de cálculo (constituição, princípio X):
- cada evento vale do seu início até o evento seguinte da mesma unidade; o último vai até o fim do arquivo;
- horas por estado, por mês e por ano; os forçados são DAU, DUR e DEM;
- restrição equivalente = duração × (potência da unidade − disponibilidade) ÷ potência, na condição RFO com a
  unidade ligada ou em reserva (LIG ou DCO);
- conferência mês a mês com as horas dos Parâmetros das taxas TEIFa e TEIP (LIG × HS, DCO × HRD, DPR × HDP,
  forçados × HDF, restrição equivalente × HEDF), nos meses que as duas bases têm;
- cruzamento horário com a EVT e a programação tratadas: vale o estado de cada unidade no meio da hora; usina parada
  é geração de até 1 MW.

Uso (na raiz do projeto, com o venv):
    python anexos/sager/gerar_anexo_sager.py --usina sao_domingos \
        --arquivo "usinas/sao_domingos/documentos/SAGER_MUG_20210101 a 20261010.xlsx" --recebido-em 23/10/2026
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.utils import ImageReader  # noqa: E402
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer  # noqa: E402
from xml.sax.saxutils import escape  # noqa: E402

from src.comum.formatacao import fmt_data, fmt_int, fmt_num, fmt_pct  # noqa: E402
from src.comum.perfil import carregar_perfil  # noqa: E402
from src.relatorio.figuras import _tema_graficos  # noqa: E402
from src.relatorio.pdf import MARGEM_INFERIOR, MARGEM_LATERAL, MARGEM_SUPERIOR, _canvas_numerado, _registrar_fontes  # noqa: E402
from src.relatorio.resumo_pdf import LARGURA_UTIL, _estilos, _tabela  # noqa: E402

ESTADOS = {
    "LIG": "ligada (em serviço)",
    "DCO": "desligada por conveniência operativa (reserva)",
    "DPR": "desligada para manutenção programada ou testes",
    "DUR": "desligada em urgência, com autorização do ONS",
    "DEM": "desligada em emergência, manualmente",
    "DAU": "desligamento automático",
    "DCA": "desligada (significado do código a confirmar com o ONS)",
}
FORCADOS = ("DAU", "DUR", "DEM")
GRUPO = {"LIG": "LIG", "DCO": "DCO", "DPR": "DPR", "DAU": "FOR", "DUR": "FOR", "DEM": "FOR", "DCA": "DCA"}
SITUACOES = ("as duas ligadas", "alguma em reserva, nenhuma indisponível", "alguma em manutenção programada",
             "alguma em desligamento forçado")
CORES_SITUACOES = dict(zip(SITUACOES, ("#2a78d6", "#eb6834", "#1baf7a", "#eda100")))  # ordem categórica validada
LARGURA_FIGURA = 7.5
LIMIAR_PARADA_MW = 1.0
RE_SGI = re.compile(r"SGI[^0-9]{0,25}?(\d{1,3}[.\s]?\d{3})\s*[/-]\s*(\d{2,4})", re.IGNORECASE)
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
RE_LOGIN = re.compile(r"\b(?:ons|age)(?:\\[\w.@-]+)+|\\[a-z][\w.@-]*", re.IGNORECASE)  # "ONS\ons\nome.sobrenome"
# Registro do sistema com o nome de quem agiu: "… por Fulana de Tal em 13/03/2024 16:13:46"
RE_POR_NOME = re.compile(r"\bpor [A-ZÁÉÍÓÚ][^\n]{0,80}? em \d\d/\d\d/\d{4} \d\d:\d\d(?::\d\d)?")


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------


def texto_do_evento(comentario: str) -> str:
    """O texto do evento, sem marcas de migração, consistência, inclusão e sem nomes, logins e e-mails."""
    t = str(comentario).replace("_x000D_", " ")
    t = re.sub(r"\[[^\]]*\]", " ", t)  # [Consistido …], [Disponibilizado …], [Não Acordado no Prazo …]
    t = re.sub(r"(Novo Evento Inclu[ií]do|Verificado e Disponibilizado|Evento Alterado|Solicita[cç][aã]o de "
               r"(Inclus[aã]o|Altera[cç][aã]o|Exclus[aã]o)) por .*? em \d\d/\d\d/\d{4} \d\d:\d\d(:\d\d)?", " ", t)
    t = re.sub(r"(Migrado do SAMUG|Novo Evento Inclu[ií]do|Solicita[cç][aã]o de (Inclus[aã]o|Altera[cç][aã]o|"
               r"Exclus[aã]o)|Verificado e Disponibilizado|Evento Alterado)\s*-\s*(AGE|ONS)?\\?\S*\s*"
               r"(\d\d/\d\d/\d{4} \d\d:\d\d)?\s*-?", " ", t)
    # marcas automáticas do sistema ("Não Consistido no prazo - SAGER\ 27/01/2023 00:00 - … por (SAGER) em …")
    t = re.sub(r"(?:SAGER|ONS|AGE)\\\s*\d\d/\d\d/\d{4} \d\d:\d\d\s*-?", " ", t)
    t = re.sub(r"(?:Não Consistido no prazo )?por \((?:SAGER|ONS|AGE)\) em \d\d/\d\d/\d{4} \d\d:\d\d(?::\d\d)?", " ", t)
    t = RE_POR_NOME.sub(" ", t)
    t = RE_LOGIN.sub(" ", t)
    t = RE_EMAIL.sub(" ", t)
    t = re.sub(r"\(\s*(ONS|AGE|GTE)\s*\)", " ", t)
    return re.sub(r"\s+", " ", t).strip(" -")


def resumo(texto: str, limite: int) -> str:
    """O texto até o limite de caracteres, cortado no fim de uma palavra e com reticências."""
    if len(texto) <= limite:
        return texto
    return texto[:limite].rsplit(" ", 1)[0].rstrip(" -;,.:") + "…"


def ler_sager(caminho: Path) -> pd.DataFrame:
    """Eventos do arquivo do SAGER (cabeçalho na linha 6), um por linha, com o texto do evento limpo."""
    bruto = pd.read_excel(caminho, header=None, dtype=str)
    linha_cab = next(i for i in range(min(20, len(bruto))) if str(bruto.iat[i, 0]).startswith("Unidade Geradora"))
    df = bruto.iloc[linha_cab + 1:, :12].copy()
    df.columns = ["unidade", "estado", "condicao", "origem", "disp", "data", "hora", "excluir", "novo", "numero",
                  "status", "comentario"]
    df = df.dropna(subset=["unidade", "estado", "data"])
    df["ug"] = df["unidade"].str.extract(r"(UG\d+)")[0]
    df["inicio"] = pd.to_datetime(df["data"].str.strip() + " " + df["hora"].str.strip(), format="%d/%m/%Y %H:%M")
    df["disp"] = df["disp"].str.replace(",", ".").astype(float)
    df["status"] = df["status"].fillna("").str.replace("-", "").str.strip()
    df["numero"] = df["numero"].fillna("").str.strip()
    df["evento"] = df["comentario"].map(texto_do_evento)
    sobra = (df["evento"].str.contains(RE_EMAIL) | df["evento"].str.contains(RE_LOGIN)
             | df["evento"].str.contains(RE_POR_NOME))
    if sobra.any():
        raise ValueError(f"{int(sobra.sum())} eventos ainda com e-mail, login ou nome de pessoa depois da limpeza")
    return df.drop(columns=["excluir", "novo", "comentario", "data", "hora"]).sort_values(["ug", "inicio", "numero"])


def intervalos(ev: pd.DataFrame, fim_arquivo: pd.Timestamp, potencia: Dict[str, float]) -> pd.DataFrame:
    """Cada evento vale até o seguinte da mesma unidade; o último, até o fim do período do arquivo."""
    ev = ev.copy()
    ev["fim"] = ev.groupby("ug")["inicio"].shift(-1).fillna(fim_arquivo)
    ev["horas"] = (ev["fim"] - ev["inicio"]).dt.total_seconds() / 3600
    p = ev["ug"].map(potencia)
    restringe = ev["estado"].isin(["LIG", "DCO"]) & (ev["condicao"] == "RFO")
    ev["horas_equiv_restricao"] = np.where(restringe, ev["horas"] * (p - ev["disp"]).clip(lower=0) / p, 0.0)
    ev["ano"] = ev["inicio"].dt.year
    return ev.reset_index(drop=True)


def por_mes(ev: pd.DataFrame) -> pd.DataFrame:
    """Horas de cada evento cortadas nas viradas de mês."""
    linhas = []
    for r in ev.itertuples():
        ini = r.inicio
        while ini < r.fim:
            prox = min(r.fim, (ini.to_period("M") + 1).to_timestamp())
            dur = (prox - ini).total_seconds() / 3600
            linhas.append({"ug": r.ug, "mes": ini.to_period("M"), "estado": r.estado, "origem": r.origem,
                           "horas": dur, "equiv": dur * (r.horas_equiv_restricao / r.horas if r.horas else 0.0)})
            ini = prox
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# Análises
# ---------------------------------------------------------------------------


def horas_por_ano(mensal: pd.DataFrame) -> pd.DataFrame:
    m = mensal.assign(ano=mensal["mes"].dt.year, classe=mensal["estado"].map(GRUPO))
    t = m.pivot_table(index=["ug", "ano"], columns="classe", values="horas", aggfunc="sum", fill_value=0)
    t["RESTRICAO_EQUIV"] = m.groupby(["ug", "ano"])["equiv"].sum()
    return t.reindex(columns=["LIG", "DCO", "DPR", "FOR", "DCA", "RESTRICAO_EQUIV"], fill_value=0).reset_index()


def conferencia_ons(mensal: pd.DataFrame, horas_ons: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """SAGER × horas por estado operativo publicadas pelo ONS (parâmetros das taxas TEIFa e TEIP), por ano."""
    if horas_ons is None or horas_ons.empty:
        return None
    o = horas_ons.copy()
    o["mes"] = pd.to_datetime(o["mes"]).dt.to_period("M")
    o["ug"] = "UG" + o["ug"].astype(str).str.extract(r"(\d+)")[0]
    s = mensal.assign(classe=mensal["estado"].map(GRUPO)).pivot_table(
        index=["ug", "mes"], columns="classe", values="horas", aggfunc="sum", fill_value=0)
    s["EQUIV"] = mensal.groupby(["ug", "mes"])["equiv"].sum()
    s["GIM"] = mensal[(mensal["estado"] == "DPR") & (mensal["origem"] == "GIM")].groupby(["ug", "mes"])["horas"].sum()
    s["DUR"] = mensal[mensal["estado"] == "DUR"].groupby(["ug", "mes"])["horas"].sum()
    s = s.fillna(0).reset_index()
    c = s.merge(o, on=["ug", "mes"], how="inner")
    c["ano"] = c["mes"].dt.year
    cols = ["LIG", "HS", "DCO", "HRD", "DPR", "HDP", "FOR", "HDF", "EQUIV", "HEDF", "GIM", "DUR"]
    c = c.reindex(columns=["ug", "mes", "ano", *cols], fill_value=0)
    return c


def restricoes(ev: pd.DataFrame) -> pd.DataFrame:
    """Restrição forçada (RFO) por unidade e ano: horas, potência mais frequente e horas equivalentes."""
    r = ev[ev["condicao"] == "RFO"]
    if r.empty:
        return pd.DataFrame(columns=["ug", "ano", "horas", "disp_mais_frequente_mw", "horas_equivalentes"])
    moda = r.groupby(["ug", "ano"]).apply(lambda g: g.groupby("disp")["horas"].sum().idxmax(), include_groups=False)
    t = r.groupby(["ug", "ano"]).agg(horas=("horas", "sum"), horas_equivalentes=("horas_equiv_restricao", "sum"))
    t["disp_mais_frequente_mw"] = moda
    return t.reset_index()[["ug", "ano", "horas", "disp_mais_frequente_mw", "horas_equivalentes"]]


def sgis(ev: pd.DataFrame) -> pd.DataFrame:
    x = ev.assign(sgi=ev["evento"].map(lambda t: sorted({f"{int(a.replace('.', '').replace(' ', ''))}/{b[-2:]}"
                                                          for a, b in RE_SGI.findall(t)})))
    x = x.explode("sgi").dropna(subset=["sgi"])
    if x.empty:
        return pd.DataFrame(columns=["sgi", "ug", "eventos", "horas", "horas_equiv_restricao", "primeiro", "ultimo",
                                     "descricao"])
    t = x.groupby(["sgi", "ug"]).agg(eventos=("horas", "size"), horas=("horas", "sum"),
                                     horas_equiv_restricao=("horas_equiv_restricao", "sum"),
                                     primeiro=("inicio", "min"), ultimo=("fim", "max")).reset_index()
    t["descricao"] = [max(x.loc[x["sgi"] == s, "evento"], key=len) for s in t["sgi"]]
    return t.sort_values("horas", ascending=False).reset_index(drop=True)


def desligamentos_longos(ev: pd.DataFrame, minimo_h: float = 24.0) -> pd.DataFrame:
    d = ev[ev["estado"].isin(["DPR", *FORCADOS, "DCA"]) & (ev["horas"] >= minimo_h)]
    return d[["ug", "estado", "origem", "inicio", "fim", "horas", "evento"]].sort_values("inicio").reset_index(drop=True)


def cruzamento_horario(ev: pd.DataFrame, tratamento: Path, inicio: pd.Timestamp,
                       fim: pd.Timestamp) -> Optional[pd.DataFrame]:
    """Estado de cada unidade no meio de cada hora, com a EVT, a geração e a programação (só com a base de EVT)."""
    arq_evt = tratamento / "evt_tratado.parquet"
    if not arq_evt.exists():
        return None
    base = pd.read_parquet(arq_evt, columns=["din_instante", "val_geracao", "val_energiavertidaturbinavel"])
    base["din_instante"] = pd.to_datetime(base["din_instante"])
    h = pd.DataFrame({"din_instante": pd.date_range(inicio.floor("h"), fim - pd.Timedelta(hours=1), freq="h")})
    meio = (h["din_instante"] + pd.Timedelta(minutes=30)).to_numpy()
    for ug, g in ev.groupby("ug"):
        pos = np.searchsorted(g["inicio"].to_numpy(), meio, side="right") - 1
        h[ug] = np.where(pos >= 0, g["estado"].to_numpy()[pos.clip(0)], None)
    h = h.merge(base, on="din_instante", how="inner")
    arq_prog = tratamento / "programacao_horaria.csv"
    if arq_prog.exists():
        prog = pd.read_csv(arq_prog, sep=";", parse_dates=["din_instante"])
        h = h.merge(prog[["din_instante", "geracao_programada_mw"]], on="din_instante", how="left")
    ugs = sorted(ev["ug"].unique())

    def situacao(linha) -> str:
        estados = [linha[u] for u in ugs]
        if any(e in (*FORCADOS, "DCA") for e in estados):
            return SITUACOES[3]
        if "DPR" in estados:
            return SITUACOES[2]
        if "DCO" in estados:
            return SITUACOES[1]
        return SITUACOES[0]

    h["situacao"] = h.apply(situacao, axis=1)
    h["todas_em_reserva"] = h[ugs].eq("DCO").all(axis=1)
    h["ano"] = h["din_instante"].dt.year
    return h


# ---------------------------------------------------------------------------
# Documento
# ---------------------------------------------------------------------------


class Documento:
    """Blocos na ordem do anexo; o Markdown e o PDF saem deles, com o mesmo conteúdo."""

    def __init__(self, titulo: str, subtitulo: str) -> None:
        self.titulo, self.subtitulo = titulo, subtitulo
        self.blocos: List[Tuple[str, object]] = []

    def secao(self, texto: str) -> None:
        self.blocos.append(("secao", texto))

    def paragrafo(self, texto: str) -> None:
        self.blocos.append(("paragrafo", texto))

    def lista(self, itens: List[str]) -> None:
        self.blocos.append(("lista", itens))

    def tabela(self, cabecalho: List[str], linhas: List[List[str]], larguras: Tuple[float, ...],
               numericas: Tuple[int, ...] = (), fonte: str = "") -> None:
        self.blocos.append(("tabela", (cabecalho, linhas, larguras, numericas, fonte)))

    def figura(self, caminho: Path, legenda: str, fonte: str) -> None:
        self.blocos.append(("figura", (caminho, legenda, fonte)))


class _T:
    def __init__(self, cabecalho, linhas):
        self.cabecalho, self.linhas = cabecalho, linhas


def gravar_md(doc: Documento, destino: Path) -> None:
    md = [f"# {doc.titulo}", "", doc.subtitulo, ""]
    celula = lambda v: str(v).replace("|", "\\|")  # noqa: E731
    for tipo, conteudo in doc.blocos:
        if tipo == "secao":
            md += [f"## {conteudo}", ""]
        elif tipo == "paragrafo":
            md += [conteudo, ""]
        elif tipo == "lista":
            md += [f"- {i}" for i in conteudo] + [""]
        elif tipo == "tabela":
            cab, linhas, _, num, fonte = conteudo
            md += ["| " + " | ".join(cab) + " |",
                   "| " + " | ".join("---:" if i in num else "---" for i in range(len(cab))) + " |"]
            md += ["| " + " | ".join(celula(c) for c in linha) + " |" for linha in linhas] + [""]
            if fonte:
                md += [fonte, ""]
        elif tipo == "figura":
            caminho, legenda, fonte = conteudo
            md += [f"![{legenda}](figures/{caminho.name})", "", f"*{legenda}*", "", fonte, ""]
    destino.write_text("\n".join(md), encoding="utf-8")


def gravar_pdf(doc: Documento, destino: Path) -> None:
    fonte, negrito = _registrar_fontes()
    est = _estilos(fonte, negrito)
    for nome in ("cab", "cab_dir", "celula", "celula_dir"):
        est[nome] = ParagraphStyle(nome, parent=est[nome], fontSize=7.5, leading=9)
    p = lambda texto, estilo="corpo": Paragraph(escape(str(texto)), est[estilo])  # noqa: E731
    story = [p(doc.titulo, "titulo"), p(doc.subtitulo, "subtitulo")]
    for tipo, conteudo in doc.blocos:
        if tipo == "secao":
            story.append(p(conteudo, "secao"))
        elif tipo == "paragrafo":
            story.append(p(conteudo))
        elif tipo == "lista":
            story += [p(f"• {i}", "item") for i in conteudo]
        elif tipo == "tabela":
            cab, linhas, larguras, num, fonte_txt = conteudo
            story.append(_tabela(_T(cab, linhas), [f * LARGURA_UTIL for f in larguras], num, est))
            if fonte_txt:
                story.append(p(fonte_txt, "aviso"))
            story.append(Spacer(1, 4))
        elif tipo == "figura":
            caminho, legenda, fonte_txt = conteudo
            lpx, apx = ImageReader(str(caminho)).getSize()
            largura = LARGURA_UTIL
            story.append(KeepTogether([Image(str(caminho), width=largura, height=largura * apx / lpx),
                                       p(legenda, "aviso"), p(fonte_txt, "aviso")]))
    pdf = SimpleDocTemplate(str(destino), pagesize=A4, leftMargin=MARGEM_LATERAL, rightMargin=MARGEM_LATERAL,
                            topMargin=MARGEM_SUPERIOR, bottomMargin=MARGEM_INFERIOR, title=doc.titulo)
    pdf.build(story, canvasmaker=_canvas_numerado(doc.titulo, fonte))


# ---------------------------------------------------------------------------
# Figuras (seaborn, tema e paleta do projeto)
# ---------------------------------------------------------------------------


def figura_evt_por_situacao(t: pd.DataFrame, destino: Path) -> None:
    """``t``: ano × situação, EVT em MWh. Barras empilhadas (a primeira situação na base)."""
    longo = t.reset_index().melt(id_vars="ano", var_name="situacao", value_name="mwh")
    longo["gwh"] = longo["mwh"] / 1000.0
    presentes = [s for s in SITUACOES if s in set(longo.loc[longo["gwh"] > 0, "situacao"])]
    fig, ax = plt.subplots(figsize=(LARGURA_FIGURA, 3.4))
    # o seaborn empilha o último nível da ordem embaixo: a ordem invertida deixa "as duas ligadas" na base
    sns.histplot(data=longo[longo["situacao"].isin(presentes)], x="ano", weights="gwh", hue="situacao",
                 hue_order=presentes[::-1], palette=CORES_SITUACOES, multiple="stack", discrete=True, shrink=0.75,
                 alpha=1, edgecolor="white", linewidth=0.6, legend=False, ax=ax)
    ax.set_xticks(sorted(longo["ano"].unique()))
    ax.set_xlabel("")
    ax.set_ylabel("Energia vertida turbinável (GWh)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: fmt_num(v, 0)))
    ax.grid(axis="x", visible=False)
    ax.set_title("EVT por situação das unidades geradoras")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=CORES_SITUACOES[s], label=s) for s in presentes],
              loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False)
    fig.subplots_adjust(left=0.1, right=0.97, top=0.9, bottom=0.3)
    fig.savefig(destino, dpi=300)
    plt.close(fig)


def figura_paradas_por_hora(contagem: pd.Series, anos: str, destino: Path) -> None:
    dados = pd.DataFrame({"hora": range(24)}).merge(contagem.rename("horas").reset_index(), on="hora", how="left")
    dados["horas"] = dados["horas"].fillna(0)
    fig, ax = plt.subplots(figsize=(LARGURA_FIGURA, 3.0))
    sns.barplot(data=dados, x="hora", y="horas", color="#2a78d6", ax=ax)
    ax.set_xlabel("Hora do dia")
    ax.set_ylabel("Horas")
    ax.grid(axis="x", visible=False)
    ax.set_title(f"Usina parada com EVT e todas as unidades em reserva, por hora do dia ({anos})")
    fig.subplots_adjust(left=0.1, right=0.97, top=0.88, bottom=0.17)
    fig.savefig(destino, dpi=300)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Montagem
# ---------------------------------------------------------------------------


def gerar(slug: str, arquivo: Path, recebido_em: str, fim: Optional[str]) -> Path:
    perfil = carregar_perfil(slug)
    par = perfil.parametros
    ev = ler_sager(arquivo)
    ugs = sorted(ev["ug"].unique(), key=lambda u: int(u[2:]))
    pot = {u: (par.potencias_unidades_mw[i] if par.potencias_unidades_mw else par.potencia_unitaria_mw)
           for i, u in enumerate(ugs)}
    m = re.search(r"(\d{8})\s*a\s*(\d{8})", arquivo.name)
    fim_arquivo = (pd.Timestamp(datetime.strptime(fim, "%d/%m/%Y")) if fim else
                   pd.Timestamp(datetime.strptime(m.group(2), "%Y%m%d")) if m else ev["inicio"].max().normalize())
    fim_arquivo = fim_arquivo + pd.Timedelta(days=1)
    ev = intervalos(ev, fim_arquivo, pot)
    mensal = por_mes(ev)
    tratamento = RAIZ / "data" / "usinas" / slug / "tratamento"
    arq_horas = tratamento / "horas_estado_mensal.csv"
    horas_ons = pd.read_csv(arq_horas, sep=";") if arq_horas.exists() else None
    conf = conferencia_ons(mensal, horas_ons)
    anos_tab = horas_por_ano(mensal)
    rest = restricoes(ev)
    tab_sgi = sgis(ev)
    longos = desligamentos_longos(ev)
    h = cruzamento_horario(ev, tratamento, ev["inicio"].min(), fim_arquivo)

    pasta = RAIZ / "usinas" / slug / "documentos" / "anexo_sager"
    (pasta / "figures").mkdir(parents=True, exist_ok=True)
    periodo = f"{fmt_data(ev['inicio'].min())} a {fmt_data(fim_arquivo - pd.Timedelta(days=1))}"
    nome = perfil.usina.nome
    doc = Documento(f"Anexo — Eventos das unidades geradoras da {nome} (SAGER)",
                    f"Análise complementar ao relatório de desempenho, de {periodo}; fonte fora dos dados abertos do "
                    "ONS")
    fonte_sager = (f"Fonte dos dados: SAGER do ONS, relatório \"Mudança de Estado Operativo de UGE\" de {periodo}, "
                   f"entregue pelo agente em resposta a ofício da AGEMS (recebido em {recebido_em}).")
    fonte_cruz = ("Calculado neste anexo a partir de: SAGER (como acima) e dados abertos do ONS tratados pelo fluxo do "
                  "projeto (Energia vertida turbinável e Programação diária da usina).")

    doc.secao("Fonte e método")
    doc.paragrafo(f"O SAGER é o sistema do ONS em que o agente registra e consiste as mudanças de estado operativo de "
                  f"cada unidade geradora. Ele não é publicado nos dados abertos: o arquivo foi entregue pelo agente em "
                  f"resposta a ofício da AGEMS (recebido em {recebido_em}). Ele traz {fmt_int(len(ev))} eventos das "
                  f"unidades {', '.join(ugs)}, de {periodo}.")
    doc.paragrafo("Cada evento vale até o seguinte da mesma unidade. A restrição equivalente é a duração × (potência "
                  "da unidade − disponibilidade) ÷ potência, na condição de restrição forçada (RFO). No cruzamento com "
                  "os dados horários, vale o estado de cada unidade no meio da hora. Os comentários foram reduzidos "
                  "ao texto do evento, sem nomes, logins nem e-mails.")
    doc.tabela(["Estado", "Significado"], [[k, v] for k, v in ESTADOS.items()], (0.15, 0.85),
               fonte="Fonte: ONS, Manual de Procedimentos da Operação, IO-CG.BR.01, Anexo 1 (classificação de estado "
                     "operativo, condição operativa e origens de restrições de unidades geradoras).")

    if conf is not None:
        doc.secao("Conferência com os dados abertos do ONS")
        doc.paragrafo("As horas do SAGER foram comparadas com as horas por estado operativo que o ONS publica nos "
                      "parâmetros das taxas TEIFa e TEIP (dados abertos), mês a mês, nos meses publicados "
                      f"({conf['mes'].min().strftime('%m/%Y')} a {conf['mes'].max().strftime('%m/%Y')}). O SAGER é a "
                      "origem dessas horas; a comparação confere o arquivo recebido.")
        a = conf.groupby(["ug", "ano"])[["LIG", "HS", "DCO", "HRD", "DPR", "HDP", "FOR", "HDF", "EQUIV", "HEDF"]].sum()
        par_txt = lambda s, o: f"{fmt_int(s)} / {fmt_int(o)}"  # noqa: E731
        linhas = [[ug, str(ano), par_txt(r.LIG, r.HS), par_txt(r.DCO, r.HRD), par_txt(r.DPR, r.HDP),
                   par_txt(r.FOR, r.HDF), par_txt(r.EQUIV, r.HEDF)] for (ug, ano), r in a.iterrows()]
        doc.tabela(["UG", "Ano", "Em serviço (LIG / HS)", "Reserva (DCO / HRD)", "Programado (DPR / HDP)",
                    "Forçado (DAU, DUR, DEM / HDF)", "Restrição forçada equiv. (RFO / HEDF)"], linhas,
                   (0.07, 0.07, 0.17, 0.17, 0.17, 0.17, 0.18), numericas=(2, 3, 4, 5, 6),
                   fonte=f"Horas: SAGER / dados abertos do ONS (Parâmetros das taxas TEIFa e TEIP). {fonte_sager}")
        gim, dur = conf[conf["GIM"] > 0], conf[conf["DUR"] > 0]
        itens = []
        if len(gim):
            meses = ", ".join(f"{r.ug} {r.mes.strftime('%m/%Y')}" for r in gim.itertuples())
            itens.append(f"As paradas programadas de origem GIM (modernização ou reforma) somam {fmt_int(gim['GIM'].sum())} "
                         f"horas ({meses}). Nos dados abertos, esses meses têm {fmt_int(gim['HDP'].sum())} horas de "
                         f"desligamento programado (HDP) e {fmt_int(gim['HRD'].sum())} de reserva (HRD): a modernização "
                         "fica fora da TEIP, como permitem os Procedimentos de Rede (intervenções de modernização ou "
                         "reforma com ganho operativo desconsideradas até 12 meses por unidade).")
        if len(dur):
            itens.append(f"Os desligamentos de urgência (DUR) somam {fmt_int(dur['DUR'].sum())} horas e aparecem nos dados "
                         "abertos como desligamento programado (HDP), e não forçado (HDF): ficam fora da TEIFa.")
        if itens:
            doc.paragrafo("Regras de contagem observadas na comparação:")
            doc.lista(itens)

    doc.secao("Horas por estado e por ano")
    doc.tabela(["UG", "Ano", "Em serviço", "Reserva", "Programado", "Forçado", "DCA",
                "Restrição forçada equiv."],
               [[r.ug, str(r.ano), fmt_int(r.LIG), fmt_int(r.DCO), fmt_int(r.DPR), fmt_int(r.FOR), fmt_int(r.DCA),
                 fmt_int(r.RESTRICAO_EQUIV)] for r in anos_tab.itertuples()],
               (0.07, 0.07, 0.15, 0.13, 0.14, 0.13, 0.13, 0.18), numericas=(2, 3, 4, 5, 6, 7), fonte=fonte_sager)

    if len(rest):
        doc.secao("Restrições forçadas de potência")
        doc.paragrafo("Horas em restrição forçada (RFO), a disponibilidade mais frequente no ano e as horas equivalentes "
                      f"de restrição, por unidade (potência de cada unidade: {', '.join(f'{u} {fmt_num(v, 1)} MW' for u, v in pot.items())}).")
        doc.tabela(["UG", "Ano", "Horas em RFO", "Disponibilidade mais frequente (MW)", "Horas equivalentes"],
                   [[r.ug, str(r.ano), fmt_int(r.horas), fmt_num(r.disp_mais_frequente_mw, 1), fmt_int(r.horas_equivalentes)]
                    for r in rest.itertuples()], (0.1, 0.1, 0.2, 0.35, 0.25), numericas=(2, 3, 4), fonte=fonte_sager)
        if len(tab_sgi):
            top = tab_sgi.head(10)
            doc.paragrafo("Intervenções (SGI) mais citadas nos eventos, com as horas dos eventos que as citam:")
            doc.tabela(["SGI", "UG", "Horas", "Período", "Descrição (texto do evento mais longo que o cita)"],
                       [[r.sgi, r.ug, fmt_int(r.horas), f"{fmt_data(r.primeiro)} a {fmt_data(r.ultimo)}",
                         resumo(r.descricao, 220)] for r in top.itertuples()], (0.1, 0.06, 0.08, 0.18, 0.58),
                       numericas=(2,), fonte=fonte_sager)

    if len(longos):
        doc.secao("Desligamentos de 24 horas ou mais")
        doc.tabela(["UG", "Estado", "Origem", "Início", "Horas", "Texto do evento"],
                   [[r.ug, r.estado, r.origem or "", r.inicio.strftime("%d/%m/%Y %H:%M"), fmt_int(r.horas),
                     resumo(r.evento, 200)] for r in longos.itertuples()], (0.06, 0.07, 0.07, 0.15, 0.07, 0.58),
                   numericas=(4,), fonte=fonte_sager)

    planilha_extra: Dict[str, pd.DataFrame] = {}
    if h is not None:
        com_evt = h[h["val_energiavertidaturbinavel"] > 0]
        parada = com_evt[com_evt["val_geracao"] <= LIMIAR_PARADA_MW]
        t = com_evt.pivot_table(index="ano", columns="situacao", values="val_energiavertidaturbinavel", aggfunc="sum",
                                fill_value=0).reindex(columns=list(SITUACOES), fill_value=0)
        doc.secao("Energia vertida turbinável e situação das unidades")
        reserva = parada[parada["todas_em_reserva"]]
        prog_zero = int((reserva.get("geracao_programada_mw", pd.Series(dtype=float)) <= LIMIAR_PARADA_MW).sum())
        doc.paragrafo(f"No período do arquivo, houve {fmt_int(len(com_evt))} horas com EVT ({fmt_num(com_evt['val_energiavertidaturbinavel'].sum(), 0)} MWh) "
                      f"e {fmt_int(len(parada))} horas de usina parada (geração até {fmt_num(LIMIAR_PARADA_MW, 0)} MW) com EVT "
                      f"({fmt_num(parada['val_energiavertidaturbinavel'].sum(), 0)} MWh). Em {fmt_int(len(reserva))} dessas horas "
                      f"({fmt_pct(len(reserva) / len(parada) * 100 if len(parada) else float('nan'), 0)}), todas as unidades estavam "
                      f"desligadas por conveniência operativa (reserva), isto é, disponíveis; a programação do ONS era de até "
                      f"{fmt_num(LIMIAR_PARADA_MW, 0)} MW em {fmt_int(prog_zero)} delas. O SAGER não traz o motivo da reserva.")
        linhas = [[str(ano), *[fmt_num(r[s], 0) for s in SITUACOES], fmt_num(r.sum(), 0)] for ano, r in t.iterrows()]
        doc.tabela(["Ano", "As duas ligadas", "Reserva, nenhuma indisponível", "Manutenção programada",
                    "Desligamento forçado", "Total (MWh)"], linhas, (0.1, 0.17, 0.2, 0.18, 0.18, 0.17),
                   numericas=(1, 2, 3, 4, 5), fonte=fonte_cruz)
        fig1 = pasta / "figures" / "01_evt_por_situacao_das_unidades.png"
        with _tema_graficos():
            figura_evt_por_situacao(t, fig1)
        doc.figura(fig1, "Figura 1 – EVT anual por situação das unidades geradoras.", fonte_cruz)
        anos_res = sorted(reserva["ano"].unique())
        if len(reserva):
            recentes = reserva[reserva["ano"] >= (anos_res[-1] - 1)]
            rotulo = f"{min(recentes['ano'])} e {max(recentes['ano'])}" if recentes["ano"].nunique() > 1 else str(anos_res[-1])
            fig2 = pasta / "figures" / "02_paradas_com_evt_em_reserva_por_hora.png"
            with _tema_graficos():
                figura_paradas_por_hora(recentes.groupby(recentes["din_instante"].dt.hour).size().rename_axis("hora"),
                                        rotulo, fig2)
            doc.figura(fig2, f"Figura 2 – Horas de usina parada com EVT e todas as unidades em reserva, por hora do dia "
                             f"({rotulo}).", fonte_cruz)
        planilha_extra["EVT_SITUACAO"] = t.reset_index()
        planilha_extra["PARADAS_EVT"] = parada.drop(columns=["todas_em_reserva"])

    doc.secao("Pontos para confirmar")
    pontos = []
    ultimo_ano = int(ev["ano"].max())
    for r in rest[rest["ano"] == ultimo_ano].itertuples():
        citados = tab_sgi[tab_sgi["ug"] == r.ug]["sgi"].head(3).tolist()
        pontos.append(f"Causa e prazo da restrição forçada da {r.ug} em {ultimo_ano} ({fmt_int(r.horas)} horas, "
                      f"disponibilidade mais frequente de {fmt_num(r.disp_mais_frequente_mw, 1)} MW)"
                      + (f"; intervenções citadas: {', '.join(citados)}" if citados else "") + ".")
    if h is not None and len(reserva):
        recentes_txt = " e ".join(str(a) for a in anos_res[-2:])
        n_recentes = int(reserva["ano"].isin(anos_res[-2:]).sum())
        pontos.append(f"Motivo das reservas por conveniência operativa nas horas de usina parada com EVT "
                      f"({fmt_int(len(reserva))} horas, {fmt_int(n_recentes)} delas em {recentes_txt}): o SAGER "
                      "não registra o motivo, a confirmar com o ONS.")
    if conf is not None and (conf["GIM"] > 0).any():
        pontos.append("Uso da franquia de modernização ou reforma nas paradas de origem GIM e o saldo de meses de "
                      "cada unidade.")
    pontos.append("Significado oficial do estado DCA, das origens (GUM, GAC, GIM, GOT, GRE e as demais) e das situações dos eventos "
                  "(CON, NAC, REV e as demais), para a leitura do arquivo.")
    doc.lista(pontos)

    doc.secao("Notas")
    doc.lista([
        "O SAGER não é dado aberto: os números deste anexo valem para o arquivo recebido e para o período dele; o "
        "relatório de desempenho segue só com os dados abertos do ONS.",
        "Os estados seguem a IO-CG.BR.01 (Anexo 1); as regras das taxas, os Procedimentos de Rede (apuração da geração e "
        "de indisponibilidade de empreendimentos de geração) e a Resolução Normativa ANEEL nº 1.033/2022 (modernização).",
        "Este anexo descreve fatos dos registros; não afirma causa além do texto do evento nem atribui nota ou parecer.",
    ])

    gravar_md(doc, pasta / "anexo_sager.md")
    gravar_pdf(doc, pasta / "anexo_sager.pdf")
    abas = {
        "EVENTOS": ev[["ug", "estado", "condicao", "origem", "disp", "inicio", "fim", "horas", "horas_equiv_restricao",
                       "status", "numero", "evento"]],
        "HORAS_ANO": anos_tab,
        **({"CONFERENCIA_ONS": conf.assign(mes=conf["mes"].astype(str))} if conf is not None else {}),
        "RESTRICOES": rest,
        "SGI": tab_sgi,
        "DESLIGAMENTOS_24H": longos,
        **planilha_extra,
        "FONTES": pd.DataFrame({"aba": ["EVENTOS", "HORAS_ANO", "CONFERENCIA_ONS", "RESTRICOES", "SGI",
                                        "DESLIGAMENTOS_24H", "EVT_SITUACAO", "PARADAS_EVT"],
                                "origem": [fonte_sager] * 6 + [fonte_cruz] * 2}),
    }
    with pd.ExcelWriter(pasta / "anexo_sager.xlsx", engine="openpyxl") as w:
        for nome_aba, tabela in abas.items():
            tabela.to_excel(w, sheet_name=nome_aba, index=False)
    return pasta


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--usina", required=True, help="slug da usina (pasta em usinas/)")
    p.add_argument("--arquivo", required=True, type=Path, help="arquivo xlsx do SAGER entregue pelo agente")
    p.add_argument("--recebido-em", required=True, help="data em que a AGEMS recebeu o arquivo (DD/MM/AAAA)")
    p.add_argument("--fim", help="último dia do período do arquivo (DD/MM/AAAA), se o nome do arquivo não o trouxer")
    a = p.parse_args()
    pasta = gerar(a.usina, a.arquivo, a.recebido_em, a.fim)
    print(f"Anexo gravado em {pasta}")


if __name__ == "__main__":
    main()
