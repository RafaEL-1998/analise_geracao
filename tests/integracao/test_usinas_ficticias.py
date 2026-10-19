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

