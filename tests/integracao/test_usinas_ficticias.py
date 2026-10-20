"""Uma usina fictícia por tipo, de ponta a ponta (spec 006, decisão R23, SC-005; tarefas T052, T053 e T067).

As sete usinas (UHE, PCH, CGH, UTE, UTN, EOL e UFV) rodam ``completo --sem-portal`` sobre os mesmos arquivos brutos
sintéticos, sem rede, cada uma só com o seu perfil. Cada relatório tem as seções comuns do seu caminho, e nenhuma saída
traz o identificador de outra usina.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Dict

import pandas as pd
import pytest

from src.__main__ import main
from src.comum import caminhos
from src.comum import perfil as modulo_perfil
from tests.fixtures import brutos_ficticios as bf

PERFIS = Path(__file__).resolve().parents[1] / "fixtures" / "usinas_ficticias"
TIPOS = ("uhe", "pch", "cgh", "ute", "utn", "eol", "ufv")
IDENTIFICADORES: Dict[str, tuple] = {
    "uhe": (bf.CEG, bf.ID_ONS),
    **{tipo: (u["ceg"], u["id_ons"]) for tipo, u in bf.FICTICIAS.items()},
}
SECOES_COMUNS = ("Fonte e cobertura dos dados", "Indicadores anuais", "Geração mensal e sazonalidade",
                 "Perfil horário da geração", "Qualidade dos dados", "Conclusão", "Notas metodológicas e limitações")
SERIE_TEMPORAL = {"eol": "Série temporal da geração", "ufv": "Série temporal da geração"}  # título por tipo (R14)


@pytest.fixture(scope="module")
def execucoes(tmp_path_factory):
    """Os brutos de todos os tipos e o fluxo completo de cada usina fictícia, uma vez."""
    raiz = tmp_path_factory.mktemp("projeto")
    bf.gerar_brutos_tipos(raiz / "data" / "raw")
    slugs = {}
    for tipo in TIPOS:
        texto = (PERFIS / tipo / "perfil.toml").read_text(encoding="utf-8")
        slug = re.search(r'^slug = "(.+)"$', texto, flags=re.M).group(1)
        (raiz / "usinas" / slug).mkdir(parents=True)
        shutil.copy(PERFIS / tipo / "perfil.toml", raiz / "usinas" / slug / "perfil.toml")
        slugs[tipo] = slug
    mp = pytest.MonkeyPatch()
    mp.setattr(caminhos, "DATA_DIR", raiz / "data")
    mp.setattr(caminhos, "RAW_DATA_DIR", raiz / "data" / "raw")
    mp.setattr(caminhos, "REPORTS_DIR", raiz / "reports")
    mp.setattr(modulo_perfil, "RAIZ_PROJETO", raiz)
    saida = {}
    try:
        for tipo, slug in slugs.items():
            codigo = main(["completo", "--usina", slug, "--sem-portal", "--data-geracao", "19/10/2026 10:00"])
            relatorio = raiz / "reports" / slug
            md = relatorio / "relatorio_analise_estatistica.md"
            saida[tipo] = {"codigo": codigo, "slug": slug, "dados": raiz / "data" / "usinas" / slug,
                           "relatorio": relatorio, "md": md.read_text(encoding="utf-8") if md.exists() else ""}
    finally:
        mp.undo()
    return saida


def _secoes(md: str):
    return re.findall(r"^## \d+\. (.+)$", md, flags=re.M)


@pytest.mark.parametrize("tipo", TIPOS)
def test_completo_com_codigo_zero_e_as_saidas(execucoes, tipo: str) -> None:
    e = execucoes[tipo]
    assert e["codigo"] == 0, tipo
    for etapa in ("coleta", "tratamento", "conferencia", "analises"):
        manifesto = json.loads((e["dados"] / etapa / "etapa.json").read_text(encoding="utf-8"))
        assert (manifesto["status"], manifesto["codigo_saida"]) == ("concluida", 0), (tipo, etapa)
    for nome in ("relatorio_analise_estatistica.pdf", "relatorio_analise_estatistica.md",
                 "perfil_estatistico_anual.xlsx"):
        assert (e["relatorio"] / nome).stat().st_size > 1000, (tipo, nome)
    assert (e["relatorio"] / "perfil_estatistico_anual.csv").stat().st_size > 100, tipo  # um ano já basta


@pytest.mark.parametrize("tipo", [t for t in TIPOS if t != "uhe"])
def test_secoes_comuns_nas_usinas_sem_evt(execucoes, tipo: str) -> None:
    secoes = _secoes(execucoes[tipo]["md"])
    assert all(s in secoes for s in SECOES_COMUNS), (tipo, secoes)
    assert SERIE_TEMPORAL.get(tipo, "Série temporal da geração e da disponibilidade") in secoes, secoes
    assert not any("EVT" in s or "vertida" in s.lower() for s in secoes), secoes


def test_uhe_no_caminho_de_hoje(execucoes) -> None:
    md = execucoes["uhe"]["md"]
    assert md.startswith("# UHE Fictícia — energia vertida turbinável e desempenho operacional")
    assert len(_secoes(md)) == 16 and "Energia vertida turbinável mensal" in _secoes(md)
    assert (execucoes["uhe"]["relatorio"] / "resumo_executivo.pdf").exists()


@pytest.mark.parametrize("tipo", TIPOS)
def test_nenhuma_saida_com_identificador_de_outra_usina(execucoes, tipo: str) -> None:
    e = execucoes[tipo]
    outros = [i for t, ids in IDENTIFICADORES.items() if t != tipo for i in ids]
    arquivos = [p for pasta in (e["dados"], e["relatorio"]) for p in pasta.rglob("*")
                if p.suffix in (".csv", ".md", ".json")]
    assert arquivos
    for arquivo in arquivos:
        conteudo = arquivo.read_text(encoding="utf-8")
        for identificador in outros:
            assert identificador not in conteudo, (tipo, arquivo.name, identificador)


def test_pch_em_conjunto_com_trechos_e_linhas_sem_valor(execucoes) -> None:
    e = execucoes["pch"]
    md = e["md"]
    assert "Geração média do conjunto CONJ. HIDRAULICO FICTICIO" in md
    trechos = pd.read_csv(e["dados"] / "coleta" / "trechos.csv", sep=";", dtype=str, keep_default_na=False)
    assert len(trechos) == 2 and list(trechos["mostrar"]) == ["True", "True"]  # o membro entra em 02/2024: os dois
    assert bf.MEMBRO["ceg"] in trechos.iloc[1]["composicao"]
    resumo = json.loads((e["dados"] / "coleta" / "etapa.json").read_text(encoding="utf-8"))["resumo"]
    assert resumo["linhas_usina_sem_valor"] == 1440
    assert "### Trechos do período" in md and "Sem itens: as regras da conclusão usam só dados do nível da usina" in md


def test_ute_com_programacao_disponibilidade_e_regras_comuns(execucoes) -> None:
    md = execucoes["ute"]["md"]
    secoes = _secoes(md)
    assert "Programação diária × geração verificada" in secoes
    assert "Disponibilidade operacional e sincronizada (ONS)" in secoes
    assert "Geração acima da disponibilidade declarada em 140 h" in md  # C8, sobre a base horária comum


def test_utn_com_indicadores_do_onS(execucoes) -> None:
    md = execucoes["utn"]["md"]
    assert "Indicadores oficiais do ONS por unidade geradora" in _secoes(md)
    assert "NUCLEAR" in md


def test_ufv_com_serie_curta(execucoes) -> None:
    md = execucoes["ufv"]["md"]
    assert "Sazonalidade omitida" in md and "| Fator de capacidade |" in md
    assert "10/02/2024 00h" in md  # o período começa na primeira hora da série da usina


# ---------------------------------------------------------------------------
# Resumo executivo de cada tipo (spec 007, US3; tarefas T027 a T030 da 007 e T149 da 006)
# ---------------------------------------------------------------------------


def _resumo(execucoes, tipo: str) -> str:
    return (execucoes[tipo]["relatorio"] / "resumo_executivo.md").read_text(encoding="utf-8")


def _bloco(md: str, titulo: str) -> str:
    return md.split(f"## {titulo}\n", 1)[1].split("\n## ", 1)[0]


def _cabecalho_tabela(bloco: str) -> str:
    return next(linha for linha in bloco.splitlines() if linha.startswith("|"))


@pytest.mark.parametrize("tipo", TIPOS)
def test_resumo_executivo_de_cada_tipo(execucoes, tipo: str) -> None:
    from src.comum.regras import RESUMO_MAXIMO_PAGINAS, RESUMO_MAXIMO_PALAVRAS_DADOS
    from src.relatorio.resumo import COLUNAS_RESUMO_ANUAL, palavras

    e = execucoes[tipo]
    manifesto = json.loads((e["relatorio"] / "etapa.json").read_text(encoding="utf-8"))
    info = manifesto["resumo"]["resumo_executivo"]
    assert info and 1 <= info["paginas"] <= RESUMO_MAXIMO_PAGINAS, (tipo, info)
    assert {"resumo_executivo.pdf", "resumo_executivo.md"} <= {a["nome"] for a in manifesto["arquivos"]}
    md = _resumo(execucoes, tipo)
    assert md.startswith(f"# {e['md'].splitlines()[0][2:].split(' — ')[0]} — resumo executivo")
    caminho = "evt" if tipo == "uhe" else "sem_evt"
    if info["evolucao_anual"]:
        cabecalho = [c.strip() for c in _cabecalho_tabela(_bloco(md, "Evolução anual")).strip("|").split("|")]
        assert cabecalho[0] == "Ano" and set(cabecalho) <= set(COLUNAS_RESUMO_ANUAL[caminho]), cabecalho
        assert len(cabecalho) <= 6
    sobre = [linha for linha in _bloco(md, "Sobre os dados").splitlines() if linha.strip()]
    assert palavras(sobre) <= RESUMO_MAXIMO_PALAVRAS_DADOS
    if tipo != "uhe":
        assert "EVT" not in md and "energia vertida" not in md.lower(), tipo
    # todo número do resumo está no relatório completo (FR-014 e SC-003 da 007); exceção: as páginas do relatório
    for linha in md.splitlines():
        if not linha.startswith("Resume o relatório completo"):
            for numero in re.findall(r"\d[\d.]*(?:,\d+)?", linha):
                assert numero in e["md"], (tipo, numero, linha)


def test_agente_atual_da_capacidade_de_geracao(execucoes) -> None:
    """Decisão do usuário de 19/10/2026 (T043 da 007): nas usinas sem EVT, o agente atual das unidades, da Capacidade
    de geração, na capa e no resumo, identificado como tal."""
    capa = execucoes["ute"]["md"].split("\n## 1. ")[0]
    assert "| Agente atual | AGENTE FICTICIO (proprietário e operador) |" in capa
    assert "Capacidade de geração (CEG UTE.GN.GO.000104-0.01)" in capa
    assert "Agente atual (Capacidade de geração do ONS): AGENTE FICTICIO (proprietário e operador)" in \
        _resumo(execucoes, "ute")


def test_resumo_da_pch_com_os_numeros_do_conjunto(execucoes) -> None:
    md = _resumo(execucoes, "pch")
    assert "Geração média do conjunto CONJ. HIDRAULICO FICTICIO" in md
    anual = _bloco(md, "Evolução anual")
    assert "| Nível |" in _cabecalho_tabela(anual) and "| conjunto |" in anual
    assert "Sem itens: as regras da conclusão usam só dados do nível da usina" in md  # a conclusão do relatório


def test_resumo_da_termica_com_a_conclusao_do_relatorio(execucoes) -> None:
    md, relatorio = _resumo(execucoes, "ute"), execucoes["ute"]["md"]
    conclusao_relatorio = relatorio.split("Conclusão\n", 1)[1].split("\n## ", 1)[0]
    itens = [linha for linha in conclusao_relatorio.splitlines() if linha.startswith("- ")]
    assert itens and all(item in md for item in itens)
    assert "| Disp. (% Pinst) |" in _cabecalho_tabela(_bloco(md, "Evolução anual"))



# ---------------------------------------------------------------------------
# Térmicas: despacho, CVU e CMO (spec 006, fase B; tarefa T083)
# ---------------------------------------------------------------------------

SECOES_TERMICA = ("Geração por motivo de despacho e inflexibilidade", "Atendimento ao despacho",
                  "Disponível sem despacho e CVU × CMO")


@pytest.mark.parametrize("tipo", ["ute", "utn"])
def test_secoes_de_termica_na_ute_e_na_utn(execucoes, tipo: str) -> None:
    e = execucoes[tipo]
    secoes = _secoes(e["md"])
    posicoes = [secoes.index(s) for s in ("Perfil horário da geração", *SECOES_TERMICA)]
    assert posicoes == sorted(posicoes), secoes  # entre o perfil horário e a programação (FR-041, item 8)
    if "Programação diária × geração verificada" in secoes:
        assert posicoes[-1] < secoes.index("Programação diária × geração verificada")
    for nome in ("despacho_horario.csv", "despacho_unidades_horario.csv", "cvu_semanal.csv", "cmo_semanal.csv"):
        assert (e["dados"] / "tratamento" / nome).exists(), (tipo, nome)
    for nome in ("06_despacho_por_motivo_mensal.png", "07_inflexibilidade_mensal.png", "09_cvu_cmo_semanal.png"):
        assert (e["relatorio"] / "figures" / nome).stat().st_size > 1000, (tipo, nome)
    assert "nan" not in e["md"].lower().replace("nanosegundo", "")
    conferencias = json.loads((e["dados"] / "conferencia" / "etapa.json").read_text(encoding="utf-8"))["resumo"]
    assert conferencias["verificada_despacho"]["divergentes"] == 0  # G4


def test_ute_com_troca_de_codigo_ano_sem_geracao_e_regras_da_termica(execucoes) -> None:
    e = execucoes["ute"]
    md = e["md"]
    assert "| Códigos de planejamento | 901 (01/2023 a 12/2023); 902 (desde 01/2024); 903 (desde 01/2024) |" in md
    assert "| 2023 | 0 | 0 | 0 | 0 | 0 |" in md  # o ano sem geração, sem divisão por zero
    unidades = pd.read_csv(e["dados"] / "tratamento" / "despacho_unidades_horario.csv", sep=";")
    assert sorted(unidades["codigo"].unique()) == [901, 902, 903]
    assert set(unidades.loc[unidades["din_instante"] < "2024", "codigo"]) == {901}  # a troca de código
    tratamento = json.loads((e["dados"] / "tratamento" / "etapa.json").read_text(encoding="utf-8"))["resumo"]
    assert tratamento["despacho"]["duplicatas_conflitantes"] == 0  # o anual de 2024 repete os mensais
    assert tratamento["cvu"]["sinalizados"] == {"negativo": 1} and tratamento["cvu"]["revisoes_descartadas"] > 0
    assert (tratamento["cmo"]["duplicatas"], tratamento["cmo"]["duplicatas_conflitantes"]) == (1, 1)
    analises = json.loads((e["dados"] / "analises" / "etapa.json").read_text(encoding="utf-8"))["resumo"]
    assert {"C12", "C13", "C14", "C15"} <= set(analises["regras_da_conclusao"])
    conferencias = json.loads((e["dados"] / "conferencia" / "etapa.json").read_text(encoding="utf-8"))["resumo"]
    assert conferencias["programacao_despacho"]["comparados"] == 72  # G3: os três dias da programação
    resumo = _resumo(execucoes, "ute")
    assert "| Disp. sem despacho (h) |" in _cabecalho_tabela(_bloco(resumo, "Evolução anual"))
    assert "CVU: custo variável unitário" in resumo and "CMO: custo marginal de operação" in resumo


def test_utn_com_a_g3_nao_aplicavel_sem_a_programacao(execucoes) -> None:
    e = execucoes["utn"]
    nao_aplicaveis = pd.read_csv(e["dados"] / "conferencia" / "nao_aplicaveis.csv", sep=";", dtype=str,
                                 keep_default_na=False).set_index("conferencia")
    assert "Programação diária não coletado" in nao_aplicaveis.loc["programacao_despacho", "motivo"]
    assert "08_desvios_despacho_mensal.png" not in {p.name for p in (e["relatorio"] / "figures").iterdir()}
