"""Rascunho do perfil: ``python -m src perfil --ceg <CEG> [--slug <slug>]`` (plano da Coleta de dados, D23 e D33;
contratos cli-perfil e perfil-usina da Coleta de dados).

O catálogo vem dos brutos sintéticos de ``tests/fixtures/brutos_catalogo.py``. O comando lê só ``data/catalogo/``:
nos testes, ``data/raw/`` é apagada depois de montado o catálogo.
"""

from __future__ import annotations

import io
import shutil
import tomllib
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pytest

from src.coleta import catalogo_usinas as cu
from src.coleta import perfil_rascunho as pr
from src.comum.caminhos import ARQUIVOS_CATALOGO
from src.comum.perfil import PerfilInvalido, carregar_perfil
from tests.fixtures import brutos_catalogo as bc


@pytest.fixture
def ambiente(tmp_path: Path) -> Dict[str, Path]:
    raw = tmp_path / "data" / "raw"
    bc.gerar_brutos_catalogo(raw)
    catalogo, usinas = tmp_path / "data" / "catalogo", tmp_path / "usinas"
    assert cu.executar_usinas(raiz_raw=raw, pasta_catalogo=catalogo, raiz_usinas=usinas, sem_portal=True, hoje=bc.HOJE,
                              saida=io.StringIO()) == 0
    shutil.rmtree(raw)  # o comando perfil não lê os brutos
    return {"raiz": tmp_path, "catalogo": catalogo, "usinas": usinas}


def _perfil(ambiente: Dict[str, Path], ceg: str, slug: str = None) -> tuple:
    saida = io.StringIO()
    codigo = pr.executar_perfil(ceg, slug, pasta_catalogo=ambiente["catalogo"], raiz_usinas=ambiente["usinas"],
                                saida=saida)
    return codigo, saida.getvalue()


def _toml(ambiente: Dict[str, Path], slug: str) -> Dict[str, Any]:
    return tomllib.loads((ambiente["usinas"] / slug / "perfil.toml").read_text(encoding="utf-8"))


def _completar(ambiente: Dict[str, Path], slug: str, trocas: Dict[str, str]) -> None:
    """Simula o fiscal: troca a situação, esvazia os pendentes e preenche linhas com a fonte."""
    arquivo = ambiente["usinas"] / slug / "perfil.toml"
    texto = arquivo.read_text(encoding="utf-8").replace('situacao = "rascunho"', 'situacao = "conferido"')
    linhas = [("pendentes = []" if linha.startswith("pendentes = ") else linha) for linha in texto.splitlines()]
    texto = "\n".join(linhas) + "\n"
    for antigo, novo in trocas.items():
        assert antigo in texto, antigo
        texto = texto.replace(antigo, novo)
    arquivo.write_text(texto, encoding="utf-8")


# ---------------------------------------------------------------------------
# Conteúdo do rascunho
# ---------------------------------------------------------------------------


def test_rascunho_da_termica_com_dado_proprio(ambiente, caplog) -> None:
    codigo, _ = _perfil(ambiente, bc.UTE["ceg"])
    assert codigo == 0
    d = _toml(ambiente, "ute_beta")  # slug derivado do nome
    u, i, c, p = d["usina"], d["identificacao"], d["cobertura"], d["parametros"]
    assert (u["slug"], u["tipo"], u["modalidade"], u["estado"], u["situacao"]) == ("ute_beta", "UTE", "TIPO I", "GO",
                                                                                   "rascunho")
    assert u["inicio_operacao_comercial"] == 2021  # primeira unidade ativa
    assert (i["ceg"], i["id_ons"], i["codigos_programacao"]) == (bc.UTE["ceg"], bc.UTE["id_ons"], [bc.UTE["id_ons"]])
    assert c == {"indicadores": "proprio", "programacao": "proprio", "disponibilidade": "proprio", "geracao": "proprio",
                 "despacho": "proprio", "cvu": "proprio"}
    # o subsistema (CMO) e os códigos de planejamento do despacho, com o período; o vigente sem fim
    assert u["subsistema"] == "SE"
    assert i["planejamento"] == [{"codigo": 7, "inicio": "2018-01", "fim": "2018-08"},
                                 {"codigo": 70, "inicio": "2026-09", "fim": ""},
                                 {"codigo": 71, "inicio": "2026-09", "fim": "2026-09"}]
    assert (p["potencia_instalada_mw"], p["unidades_geradoras"], p["potencia_unitaria_mw"]) == (150.0, 2, 75.0)
    assert p["combustivel"] == "GÁS"
    assert "parametros.fontes.geral" in u["pendentes"]
    texto = (ambiente["usinas"] / "ute_beta" / "perfil.toml").read_text(encoding="utf-8")
    assert "Capacidade de geração" in texto and "Modalidade das usinas" in texto  # a origem em comentário
    assert "cod_usina" not in texto  # campo que não se aplica à térmica não aparece
    assert any("Rascunho do perfil gravado em usinas/ute_beta/perfil.toml" in r.getMessage() and "pendentes" in
               r.getMessage() for r in caplog.records)


def test_rascunho_e_recusado_pelas_etapas_e_vale_depois_de_conferido(ambiente) -> None:
    assert _perfil(ambiente, bc.UTE["ceg"])[0] == 0
    with pytest.raises(PerfilInvalido) as erro:
        carregar_perfil("ute_beta", ambiente["raiz"])
    problemas = "\n".join(erro.value.problemas)
    assert "usina.situacao: perfil em rascunho" in problemas and "pendente: parametros.fontes.geral" in problemas
    _completar(ambiente, "ute_beta", {"# geral = ": "geral = \"documento de teste, 01/10/2026\"  # "})
    perfil = carregar_perfil("ute_beta", ambiente["raiz"])
    assert perfil.usina.tipo == "UTE" and perfil.identificacao.codigos_programacao == (bc.UTE["id_ons"],)


def test_rascunho_da_hidreletrica_traz_os_codigos_dos_reservatorios(ambiente) -> None:
    assert _perfil(ambiente, bc.UHE["ceg"], "uhe_ficticia")[0] == 0
    d = _toml(ambiente, "uhe_ficticia")
    i = d["identificacao"]
    assert (i["cod_usina"], i["nome_ons"], i["id_reservatorio"]) == (999, "FICTICIO", "PNUHFI")  # D33
    assert d["cobertura"]["evt"] == "proprio" and d["cobertura"]["hidrologia"] == "proprio"
    assert d["parametros"]["potencia_unitaria_mw"] == 30.0
    pendentes = d["usina"]["pendentes"]
    for campo in ("parametros.garantia_fisica_mwmed", "parametros.tipo_turbina", "parametros.ip_referencia",
                  "analises.vertimento_minimo_m3s", "analises.faixas_geracao_mw"):
        assert campo in pendentes, campo


def test_rascunho_da_pch_em_conjunto_com_os_membros_vigentes(ambiente) -> None:
    assert _perfil(ambiente, bc.PCH["ceg"])[0] == 0
    d = _toml(ambiente, "pch_alfa")
    i = d["identificacao"]
    # também o código antigo do conjunto, com os períodos em comentário para o fiscal conferir
    assert (i["id_conjunto"], i["codigos_programacao"]) == (bc.PCH["conjunto"], ["GOCJA-100", "GOCJA-101", "GOCJA-102"])
    texto = (ambiente["usinas"] / "pch_alfa" / "perfil.toml").read_text(encoding="utf-8")
    assert ("#   períodos na Programação diária: GOCJA-100 de 17/10/2026 a 17/10/2026; GOCJA-101 desde 18/10/2026; "
            "GOCJA-102 desde 18/10/2026") in texto
    assert i["id_ons"] == bc.PCH["id_ons"]
    assert d["cobertura"]["geracao"] == "conjunto" and d["cobertura"]["programacao"] == "conjunto"
    assert d["cobertura"]["evt"] == "ausente"
    assert [(m["ceg"], m["inicio"], m["fim"]) for m in i["membros"]] == [(bc.PCH["ceg"], "2019-08-22", "")]
    assert "parametros.tipo_turbina" not in d["usina"]["pendentes"]  # sem EVT nem hidrologia
    _completar(ambiente, "pch_alfa", {"# geral = ": "geral = \"documento de teste, 01/10/2026\"  # "})
    assert carregar_perfil("pch_alfa", ambiente["raiz"]).identificacao.id_conjunto == bc.PCH["conjunto"]


def test_rascunho_da_solar_com_unidades_diferentes_e_divergencia_de_potencia(ambiente) -> None:
    assert _perfil(ambiente, bc.UFV["ceg"])[0] == 0
    d = _toml(ambiente, "ufv_gama")
    p = d["parametros"]
    assert (p["potencia_instalada_mw"], p["potencias_unidades_mw"]) == (50.0, [21.43, 28.57])
    assert "potencia_unitaria_mw" not in p
    texto = (ambiente["usinas"] / "ufv_gama" / "perfil.toml").read_text(encoding="utf-8")
    assert "Divergência" in texto and "2,507 MW" in texto
    assert d["identificacao"]["codigos_programacao"] == ["GOCJB"]
    assert d["identificacao"]["membros"][0]["id_ons"] == bc.UFV["id_ons_composicao"]


def test_codigo_de_programacao_sem_ligacao_fica_pendente_com_a_lista_do_estado(ambiente) -> None:
    caminho = ambiente["catalogo"] / ARQUIVOS_CATALOGO["programacao"]
    programacao = pd.read_csv(caminho, sep=";", dtype=str, keep_default_na=False)
    programacao.loc[programacao["codigo_exibicao"] == bc.UTE["id_ons"], "id_usina_ou_conjunto"] = ""
    programacao.to_csv(caminho, sep=";", index=False)
    assert _perfil(ambiente, bc.UTE["ceg"])[0] == 0
    d = _toml(ambiente, "ute_beta")
    assert "codigos_programacao" not in d["identificacao"]
    assert "identificacao.codigos_programacao" in d["usina"]["pendentes"]
    texto = (ambiente["usinas"] / "ute_beta" / "perfil.toml").read_text(encoding="utf-8")
    assert "GOOUTRO" in texto and "GOCJA-101" in texto and bc.EOL["id_ons"] not in texto  # só os códigos de GO


# ---------------------------------------------------------------------------
# Recusas e perfil existente
# ---------------------------------------------------------------------------


def test_catalogo_ausente_da_codigo_5(tmp_path, caplog) -> None:
    codigo = pr.executar_perfil(bc.UTE["ceg"], None, pasta_catalogo=tmp_path / "catalogo",
                                raiz_usinas=tmp_path / "usinas", saida=io.StringIO())
    assert codigo == 5
    assert any("O catálogo de usinas não foi montado. Execute antes: python -m src usinas" in r.getMessage()
               for r in caplog.records)
    assert not (tmp_path / "usinas").exists()


@pytest.mark.parametrize("ceg, trecho", [
    ("UTE.GN.GO.999999-0.01", "fora do catálogo"),
    (bc.CGH["ceg"], "só em agregado"),
    (bc.SEM_DADOS["ceg"], "só em agregado"),
    (bc.OUTRO["ceg"], "tipo"),
])
def test_recusas_com_codigo_2_sem_gravar(ambiente, caplog, ceg: str, trecho: str) -> None:
    assert _perfil(ambiente, ceg)[0] == 2
    assert any(trecho in r.getMessage() for r in caplog.records if r.levelname == "ERROR")
    assert not ambiente["usinas"].exists() or not any(ambiente["usinas"].iterdir())


def _trocar_cobertura(ambiente: Dict[str, Path], ceg: str, niveis: Dict[str, str]) -> None:
    """Muda, na cobertura.csv montada, o nível de conjuntos da usina (o catálogo não guarda hash das tabelas)."""
    arquivo = ambiente["catalogo"] / ARQUIVOS_CATALOGO["cobertura"]
    tabela = pd.read_csv(arquivo, sep=";", dtype=str, keep_default_na=False)
    for chave, nivel in niveis.items():
        tabela.loc[(tabela["ceg"] == ceg) & (tabela["conjunto_ons"] == chave), "nivel"] = nivel
    tabela.to_csv(arquivo, sep=";", index=False)


def test_usina_so_com_a_programacao_e_recusada_no_rascunho(ambiente, caplog) -> None:
    """Bug rascunho-sem-serie-referencia: a mesma regra da série de referência da Coleta, já no rascunho."""
    _trocar_cobertura(ambiente, bc.UTE["ceg"], {"geracao": "ausente", "indicadores": "ausente",
                                                "disponibilidade": "ausente", "despacho": "ausente", "cvu": "ausente"})
    assert _perfil(ambiente, bc.UTE["ceg"])[0] == 2
    erros = [r.getMessage() for r in caplog.records if r.levelname == "ERROR"]
    assert any(f"O ONS não publica a série de referência da usina UTE BETA ({bc.UTE['ceg']})" in m
               and 'o catálogo encontra só: programacao = "proprio"' in m and "não tem relatório individual" in m
               for m in erros), erros
    assert not ambiente["usinas"].exists() or not any(ambiente["usinas"].iterdir())


def test_usina_com_a_geracao_do_conjunto_continua_com_rascunho(ambiente) -> None:
    """Como a PCH Bandeirante: sem série própria, a Geração por usina do conjunto é a série de referência."""
    assert _toml_depois(ambiente, bc.PCH["ceg"], "pch_alfa")["cobertura"]["geracao"] == "conjunto"


def test_solar_em_conjunto_com_a_restricao_com_detalhe_propria_continua_com_rascunho(ambiente) -> None:
    """Como a Seriemas 1: sem a geração da usina, a série de referência é a restrição com detalhe dela."""
    _trocar_cobertura(ambiente, bc.UFV["ceg"], {"geracao": "conjunto", "restricao_detalhe": "proprio"})
    assert _toml_depois(ambiente, bc.UFV["ceg"], "ufv_gama")["cobertura"]["restricao_detalhe"] == "proprio"


def test_solar_so_com_a_razao_da_restricao_do_conjunto_e_recusada(ambiente, caplog) -> None:
    _trocar_cobertura(ambiente, bc.UFV["ceg"], {"geracao": "ausente", "restricao_detalhe": "ausente"})
    assert _perfil(ambiente, bc.UFV["ceg"])[0] == 2
    assert any("nem a restrição com detalhe da usina" in r.getMessage() for r in caplog.records
               if r.levelname == "ERROR")


def _toml_depois(ambiente: Dict[str, Path], ceg: str, slug: str) -> Dict[str, Any]:
    codigo, texto = _perfil(ambiente, ceg)
    assert codigo == 0, texto
    return _toml(ambiente, slug)


def test_tipo_iii_cita_a_carteira(ambiente, caplog) -> None:
    _perfil(ambiente, bc.CGH["ceg"])
    assert any("O ONS publica a usina CGH DELTA" in r.getMessage() and "python -m src carteira --estado GO" in
               r.getMessage() for r in caplog.records)


def test_perfil_existente_nao_e_alterado_e_mostra_as_diferencas(ambiente) -> None:
    assert _perfil(ambiente, bc.UTE["ceg"])[0] == 0
    arquivo = ambiente["usinas"] / "ute_beta" / "perfil.toml"
    codigo, texto = _perfil(ambiente, bc.UTE["ceg"])
    assert codigo == 0 and "sem diferença" in texto
    original = arquivo.read_text(encoding="utf-8").replace(f'id_ons = "{bc.UTE["id_ons"]}"', 'id_ons = "GOXXXX"')
    arquivo.write_text(original, encoding="utf-8")
    codigo, texto = _perfil(ambiente, bc.UTE["ceg"], "outro_nome")  # achado pelo CEG, em outra pasta
    assert codigo == 6
    assert "O perfil usinas/ute_beta/perfil.toml já existe e não foi alterado." in texto
    assert f"- identificacao.id_ons: perfil GOXXXX; catálogo {bc.UTE['id_ons']}" in texto
    assert arquivo.read_text(encoding="utf-8") == original
    assert not (ambiente["usinas"] / "outro_nome").exists()


def test_uhe_sem_cobertura_vale_os_conjuntos_de_hoje_com_proprio(ambiente) -> None:
    pasta = ambiente["usinas"] / "uhe_ficticia"
    pasta.mkdir(parents=True)
    (pasta / "perfil.toml").write_text(
        f'[usina]\nslug = "uhe_ficticia"\ntipo = "UHE"\nmodalidade = "TIPO II-B"\nestado = "GO"\n\n'
        f'[identificacao]\nceg = "{bc.UHE["ceg"]}"\nid_ons = "{bc.UHE["id_ons"]}"\ncod_usina = 999\n'
        f'nome_ons = "FICTICIO"\nid_reservatorio = "PNUHFI"\ncod_programacao = "{bc.UHE["id_ons"]}"\n',
        encoding="utf-8")
    codigo, texto = _perfil(ambiente, bc.UHE["ceg"])
    assert codigo == 0, texto


@pytest.mark.parametrize("slug", ["carteiras", "UTE-Beta", "com espaço"])
def test_slug_invalido_ou_reservado_da_codigo_2(ambiente, slug: str) -> None:
    assert _perfil(ambiente, bc.UTE["ceg"], slug)[0] == 2
    assert not (ambiente["usinas"] / slug).exists()


def test_linha_de_comando() -> None:
    from src.__main__ import construir_parser

    args = construir_parser().parse_args(["perfil", "--ceg", bc.UTE["ceg"], "--slug", "ute_beta"])
    assert (args.comando, args.ceg, args.slug) == ("perfil", bc.UTE["ceg"], "ute_beta")
    with pytest.raises(SystemExit) as saida:
        construir_parser().parse_args(["perfil"])
    assert saida.value.code == 2
