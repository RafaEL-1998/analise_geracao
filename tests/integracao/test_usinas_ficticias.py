"""Uma usina fictícia por tipo, de ponta a ponta (spec 006, decisão R23, SC-005; tarefas T052, T053, T067, T083 e T104).

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


@pytest.mark.parametrize("tipo", [t for t in TIPOS if t not in ("uhe", "pch")])
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
    # fase D: o período começa na entrada da PCH (10/01); o membro entra em 02/2024 e a térmica sai em 15/02
    assert list(trechos["inicio"]) == ["2024-01-10 00:00:00", "2024-02-01 00:00:00", "2024-02-15 00:00:00"]
    assert list(trechos["tipos_composicao"]) == ["PCH;UTE", "CGH;PCH;UTE", "CGH;PCH"]
    assert list(trechos["mostrar"]) == ["True", "True", "True"]
    assert bf.MEMBRO["ceg"] in trechos.iloc[1]["composicao"] and bf.MEMBRO_UTE["ceg"] not in trechos.iloc[2]["composicao"]
    resumo = json.loads((e["dados"] / "coleta" / "etapa.json").read_text(encoding="utf-8"))["resumo"]
    assert resumo["periodo"]["inicio"] == "2024-01-10 00:00:00"  # e não 01/01, o início da série do conjunto
    assert resumo["composicao_da_usina"] == [{"inicio": "2024-01-10 00:00:00", "fim": ""}]
    assert resumo["linhas_usina_sem_valor"] == 51 * 24  # só no período
    assert resumo["linhas_usina_sem_valor_periodo"] == {"inicio": "2024-01-10 00:00:00", "fim": "2024-02-29 23:00:00"}
    assert ("A Geração por usina traz 1.224 linhas próprias da usina sem valor, de 10/01/2024 a 29/02/2024; a série "
            "usada é a do conjunto.") in md
    assert "### Trechos do período" in md and "Sem itens: as regras da conclusão usam só dados do nível da usina" in md


# ---------------------------------------------------------------------------
# PCH e CGH (spec 006, fase D; tarefas T121 e T150)
# ---------------------------------------------------------------------------

SECAO_CONJUNTO = "Composição e geração do conjunto"
SECAO_AFLUENCIA = "Afluência, vertimento e nível do reservatório (ONS)"
PARTE_CONJUNTO = "Operação do conjunto CONJ. HIDRAULICO FICTICIO (CJU_GOCJFI)"


def _secao(md: str, titulo: str) -> str:
    return md.split(f"{titulo}\n", 1)[1].split("\n## ", 1)[0]


def test_pch_em_duas_partes_a_usina_e_o_conjunto(execucoes) -> None:
    """Decisões do usuário de 22/10/2026 (rascunho 005, FR-048): primeiro a usina, com o peso dela na potência do
    conjunto; depois, logo antes da conclusão, a parte do conjunto, com as análises do conjunto em subseções."""
    md = execucoes["pch"]["md"]
    assert _secoes(md) == ["Fonte e cobertura dos dados", "A usina no conjunto", "Qualidade dos dados", PARTE_CONJUNTO,
                           "Conclusão", "Notas metodológicas e limitações"]
    usina = _secao(md, "A usina no conjunto")
    assert usina.startswith("\n**A usina no conjunto.** O ONS publica a geração, a programação e os demais dados de "
                            "operação do conjunto CONJ. HIDRAULICO FICTICIO (CJU_GOCJFI), e não os da PCH Fictícia isolada.")
    assert "Peso da usina (16,0 MW) na potência das usinas do conjunto: 34,8% de 10/01/2024 a 31/01/2024" in usina
    assert "esse peso não estima a geração dela" in usina and "medição da CCEE" in usina
    assert "| 3 | 15/02/2024 | 29/02/2024 | 16,0 | 16,0 | 100,0% |" in usina  # a CGH membro sem unidade cadastrada
    assert "Os dados de operação são os do conjunto, na seção 4, antes da conclusão." in usina
    parte = _secao(md, PARTE_CONJUNTO)
    assert parte.lstrip().startswith("**Geração.** Geração média do conjunto CONJ. HIDRAULICO FICTICIO")
    subsecoes = [linha[4:] for linha in parte.splitlines() if linha.startswith("### ")]
    assert subsecoes[:4] == ["Indicadores anuais do conjunto", "Série temporal da geração do conjunto",
                             "Geração mensal e sazonalidade do conjunto", "Perfil horário da geração do conjunto"]
    assert "Programação diária × geração verificada do conjunto" in subsecoes
    resumo = _resumo(execucoes, "pch")
    assert "Colunas e definições na seção 4 do relatório completo." in resumo  # a tabela anual na parte do conjunto


def test_pch_com_a_secao_do_conjunto_por_trecho(execucoes) -> None:
    e = execucoes["pch"]
    md = e["md"]
    secao = _secao(md, PARTE_CONJUNTO)
    assert ("O conjunto CONJ. HIDRAULICO FICTICIO (CJU_GOCJFI) teve 3 composições no período: de 10/01/2024 a "
            "31/01/2024, 2 usinas (PCH e UTE), geração média do conjunto de 22,0 MWmed;") in secao
    divergencia = ("O ONS publica a série do conjunto como TÉRMICA (Biomassa) de 15/02/2024 a 29/02/2024, quando a "
                   "composição tem só CGH e PCH; o tipo das usinas vem do CEG.")
    assert divergencia not in secao and divergencia in _secao(md, "Qualidade dos dados")  # T160
    # potência somada: PCH 16 + térmica 30 enquanto ela está no conjunto; a CGH membro sem unidade ("—")
    assert "| 1 | 10/01/2024 00h | 31/01/2024 23h | 2 | PCH, UTE | 528 | 11.616 | 22,0 | 22,0 | 46,0 |" in secao
    assert "| 3 | 15/02/2024 00h | 29/02/2024 23h | 2 | CGH, PCH | 360 | 5.400 | 15,0 | 15,0 | 16,0 |" in secao
    assert "| CGH MEMBRO | CGH | CGH.PH.GO.000102-0.01 | 01/02/2024 | — | — |" in secao
    assert "| UTE MEMBRO | UTE | UTE.BI.GO.000109-0.01 | 01/03/2016 | 15/02/2024 | 30,0 |" in secao
    assert ("Calculado neste relatório a partir de: Geração por usina (conjunto de usinas, id ONS CJU_GOCJFI)"
            in secao and "Capacidade de geração (CEG das usinas do conjunto CJU_GOCJFI)" in secao)
    assert (e["relatorio"] / "figures" / "14_geracao_do_conjunto_por_trecho.png").stat().st_size > 1000
    # a composição com os nomes fica na seção do conjunto: a tabela de trechos da seção 1 sem os CEGs
    assert "| Trecho | Início | Fim | Modalidade | Nível | Tipos |" in md and "Composição (CEG)" not in md
    coleta = e["dados"] / "coleta"
    membros = pd.read_csv(coleta / "capacidade_membros.csv", sep=";", dtype=str, keep_default_na=False)
    assert set(membros["ceg"]) == {bf.FICTICIAS["pch"]["ceg"], bf.MEMBRO_UTE["ceg"]}  # a CGH membro sem unidade
    tipos = pd.read_csv(coleta / "tipo_publicado.csv", sep=";", dtype=str, keep_default_na=False)
    assert set(tipos["nom_tipousina"]) == {"TÉRMICA"} and list(tipos["trecho"]) == ["1", "2", "3"]


def test_pch_sem_a_usina_isolada_nas_notas_e_sem_itens(execucoes) -> None:
    md = execucoes["pch"]["md"]
    notas = md.split("Notas metodológicas e limitações\n")[-1]
    assert ("Granularidade: o ONS publica a geração do conjunto CONJ. HIDRAULICO FICTICIO (CJU_GOCJFI), e não a da "
            "usina isolada.") in notas
    assert "O período começa na entrada da usina no conjunto (Composição dos conjuntos)" in notas
    assert "| Disponibilidade e geração por ano | sem a Disponibilidade por usina (cobertura: ausente) |" in notas
    assert "| Indicadores oficiais do ONS por unidade geradora | sem os Indicadores de desempenho do ONS" in notas
    assert SECAO_CONJUNTO + " |" not in notas  # a seção não está mais entre as omitidas
    conclusao = _secao(md, "Conclusão")
    assert ("Sem itens: as regras da conclusão usam só dados do nível da usina, e o ONS publica para esta usina só os "
            "números do conjunto CONJ. HIDRAULICO FICTICIO") in conclusao
    analises = json.loads((execucoes["pch"]["dados"] / "analises" / "etapa.json").read_text(encoding="utf-8"))
    assert analises["resumo"]["conclusao"] == {} and analises["resumo"]["bases_complementares"]["conjunto"] is True


def test_cgh_sem_conjunto_com_a_afluencia_sem_evt(execucoes) -> None:
    e = execucoes["cgh"]
    md = e["md"]
    secoes = _secoes(md)
    assert SECAO_CONJUNTO not in secoes and "Granularidade" not in md  # a CGH tem geração própria
    assert secoes.index("Perfil horário da geração") < secoes.index(SECAO_AFLUENCIA) < secoes.index("Qualidade dos dados")
    secao = _secao(md, SECAO_AFLUENCIA)
    assert "a hora foi conferida pela geração da usina (correlação entre a vazão turbinada e a geração de 1,000" in secao
    assert "afluência acima do engolimento máximo da usina (20,0 m³/s) em 24 horas" in secao  # o dia de cheia
    assert "faixa de afluência" not in secao.lower() and "EVT" not in secao.replace("sem EVT", "")
    assert "### Afluência, vazões, nível e volume útil por ano" in secao
    assert "Conferência: hora dos Dados hidrológicos conferida pela geração da usina" in secao
    assert (e["relatorio"] / "figures" / "15_vazoes_mensais.png").stat().st_size > 1000
    conferencia = json.loads((e["dados"] / "conferencia" / "etapa.json").read_text(encoding="utf-8"))["resumo"]
    assert conferencia["alinhamento_hidrologia"]["coincidentes"] == conferencia["alinhamento_hidrologia"]["comparados"]
    assert "vazoes" in conferencia["nao_aplicaveis"]  # a conferência das vazões pede a EVT
    notas = md.split("Notas metodológicas e limitações\n")[-1]
    assert "e não pela EVT, que a usina não tem" in notas and SECAO_AFLUENCIA.split(" (")[0] + " |" not in notas


def test_secao_do_conjunto_tambem_na_solar_com_serie_propria(execucoes) -> None:
    """Decisão do usuário de 22/10/2026: a seção do conjunto em toda usina em conjunto, inclusive a eólica ou solar
    com série própria (a Seriemas 1); sem a nota do período recortado, que só vale com a série do conjunto."""
    md = execucoes["ufv"]["md"]
    assert SECAO_CONJUNTO in _secoes(md)
    assert "O conjunto CONJ. SOLAR FICTICIO (CJU_GOCJUF) teve 1 composição no período" in md
    assert "O período começa na entrada da usina no conjunto" not in md
    # as fontes do resumo com o nível, como nas legendas: o dado do conjunto não leva o id ONS da usina (decisão R15)
    fontes = next(linha for linha in _resumo(execucoes, "ufv").splitlines() if linha.startswith("Fontes:"))
    assert re.search(r"Fator de capacidade[^;]*\(conjunto de usinas, id ONS CJU_GOCJUF\)", fontes), fontes
    assert not re.search(r"Fator de capacidade[^;]*\(id ONS GOUFFI\)", fontes), fontes
    for tipo in ("ute", "utn", "eol", "uhe"):
        assert SECAO_CONJUNTO not in _secoes(execucoes[tipo]["md"]), tipo


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
    assert "25/01/2024 00h" in md  # o período começa na primeira semi-hora da série da usina (fase C)


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


# ---------------------------------------------------------------------------
# Eólicas e solares: fator de capacidade e restrições (spec 006, fase C; tarefa T104)
# ---------------------------------------------------------------------------

SECOES_RENOVAVEL = ("Fator de capacidade", "Energia cortada por restrição de operação (constrained-off)",
                    "Recurso × geração")


def _manifesto(e, etapa: str) -> dict:
    return json.loads((e["dados"] / etapa / "etapa.json").read_text(encoding="utf-8"))["resumo"]


@pytest.mark.parametrize("tipo", ["eol", "ufv"])
def test_secoes_de_renovaveis_na_eol_e_na_ufv(execucoes, tipo: str) -> None:
    e = execucoes[tipo]
    secoes = _secoes(e["md"])
    posicoes = [secoes.index(s) for s in ("Perfil horário da geração", *SECOES_RENOVAVEL)]
    assert posicoes == sorted(posicoes), secoes  # depois do perfil horário (FR-041, item 8)
    for nome in ("fator_capacidade_horario.csv", "restricao_semi_horaria.csv", "restricao_horaria.csv",
                 "restricao_razao_semi_horaria.csv"):
        assert (e["dados"] / "tratamento" / nome).exists(), (tipo, nome)
    for nome in ("10_fator_capacidade_mensal.png", "11_energia_cortada_por_razao_mensal.png",
                 "12_geracao_por_faixa_de_recurso.png"):
        assert (e["relatorio"] / "figures" / nome).stat().st_size > 1000, (tipo, nome)
    assert "nan" not in e["md"].lower().replace("nanosegundo", "")
    conferencias = _manifesto(e, "conferencia")
    assert conferencias["geracao_fontes"]["divergentes"] == 0  # G1: as fontes da geração coincidem
    assert conferencias["programacao_renovaveis"]["comparados"] == 72  # G5: os três dias da programação
    assert "| Energia cortada (MWh, % est.) |" in _cabecalho_tabela(_bloco(_resumo(execucoes, tipo), "Evolução anual"))


def test_eol_com_vento_invalido_corte_por_razao_e_regras(execucoes) -> None:
    e = execucoes["eol"]
    md = e["md"]
    restricao = _manifesto(e, "tratamento")["restricao_detalhe"]
    # 160 semi-horas restritas × 25 MW × 0,5 h; o erro da estimativa das 3h fica de fora; 6 dias de vento inválido
    assert (restricao["energia_cortada_mwh"], restricao["semi_horas_recurso_invalido"]) == (2000.0, 288)
    assert "| indisponibilidade externa (REL) | 48 | 600 | 30,0% |" in md
    assert "diferença bruta entre a estimada e a verificada de 2.046 MWh" in md
    analises = _manifesto(e, "analises")
    assert {"C16", "C17", "C19"} <= set(analises["regras_da_conclusao"]) and "C18" in analises["omitidos"]
    assert "### Maiores desvios entre a geração verificada e a programada" in md
    assert "4 semi-horas com vento acima de 40 m/s, acima do limite físico" in md  # sem a marca do ONS
    assert (e["relatorio"] / "figures" / "13_desvio_programacao_mensal.png").exists()
    nao_aplicaveis = pd.read_csv(e["dados"] / "conferencia" / "nao_aplicaveis.csv", sep=";", dtype=str,
                                 keep_default_na=False).set_index("conferencia")
    assert "não está em conjunto" in nao_aplicaveis.loc["soma_conjunto", "motivo"]


def test_ufv_em_conjunto_com_a_restricao_como_referencia(execucoes) -> None:
    e = execucoes["ufv"]
    md = e["md"]
    assert "Série de referência: Restrição com detalhe (id ONS GOUFFI; CEG UFV.RS.GO.000107-0.01)" in md
    tratamento = _manifesto(e, "tratamento")
    assert tratamento["restricao_detalhe"]["semi_horas_sem_marca"] == 336  # janeiro, no esquema antigo
    # estimada 0 com a usina gerando: estimativa ausente; nas duas restritas, o corte não é calculado
    assert (tratamento["restricao_detalhe"]["semi_horas_estimada_ausente"],
            tratamento["restricao_detalhe"]["semi_horas_restritas_sem_estimativa"]) == (6, 2)
    assert tratamento["restricao_detalhe"]["energia_cortada_mwh"] == 70.0  # 28 semi-horas × 5 MW × 0,5 h
    assert "Sem a estimativa do ONS (estimada 0 com a usina gerando) em 6 semi-horas, 2 delas" in md
    assert tratamento["membros_restricao"] == {bf.MEMBRO_UFV["id_ons"]: 864}
    auditoria = pd.read_csv(e["dados"] / "coleta" / "auditoria_restricao_detalhe.csv", sep=";", dtype=str,
                            keep_default_na=False)
    assert auditoria["mensagem"].str.contains("colunas ausentes no arquivo").sum() == 1
    soma = _manifesto(e, "conferencia")["soma_conjunto"]
    assert (soma["comparados"], soma["divergentes"]) == (864, 0)  # G2: a usina e o membro somam o conjunto
    assert "A razão é a do conjunto de usinas CONJ. SOLAR FICTICIO, id ONS CJU_GOCJUF" in md
    assert "| Fator de capacidade | conjunto | CJU_GOCJUF |" in md  # o número do conjunto, identificado
    for nome in ("fator_capacidade_extraido.parquet", "restricao_razao_extraido.parquet"):
        assert set(pd.read_parquet(e["dados"] / "coleta" / nome)["nivel"]) == {"conjunto"}, nome
    assert "A série do conjunto" not in md  # a base horária é da usina
    # T157: a programação do conjunto comparada com a geração do conjunto, identificada; a C19 não é avaliada
    secao = md.split("Programação diária × geração verificada\n", 1)[1].split("\n## ", 1)[0]
    assert "Programação diária do ONS (conjunto) × geração verificada" in secao
    assert "Geração por usina (conjunto de usinas, id ONS CJU_GOCJUF)" in secao and "MSSRI" not in secao
    assert "### Maiores desvios entre a geração verificada e a programada" in secao
    assert "C19" in _manifesto(e, "analises")["omitidos"]
    # a programação conferida pela G5 não fica como "sem outra fonte"
    assert "programado do Fator de capacidade (G5)" in secao and "conferir: programação diária" not in secao
