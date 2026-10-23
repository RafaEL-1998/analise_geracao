"""Catálogo de usinas: ``python -m src usinas`` (plano da Coleta de dados, D19 a D21 e D33;
contrato cli-usinas da Coleta de dados).

Os brutos sintéticos de ``tests/fixtures/brutos_catalogo.py`` formam um pequeno Brasil fictício. Nenhum teste usa a
rede: a sincronização com o portal é simulada por um catálogo CKAN falso que copia os arquivos de uma pasta.
"""

from __future__ import annotations

import io
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pytest

from src.coleta import catalogo_usinas as cu
from src.comum.caminhos import ARQUIVOS_CATALOGO
from tests.fixtures import brutos_catalogo as bc

COLUNAS_USINAS = [
    "ceg", "id_ons", "nom_usina", "tipo", "modalidade", "id_estado", "sgl_centrooperacao", "nom_pontoconexao",
    "sts_aneel", "subsistema", "potencia_autorizada_mw", "id_conjunto", "nom_conjunto", "unidades_geradoras",
    "potencia_efetiva_mw", "potencias_unidades_mw", "combustivel", "entrada_operacao", "cod_usina", "nom_reservatorio",
    "id_reservatorio", "cobertura_resumo", "divergencias",
]


@pytest.fixture
def mundo(tmp_path: Path) -> Dict[str, Path]:
    raw = tmp_path / "data" / "raw"
    bc.gerar_brutos_catalogo(raw)
    usinas = tmp_path / "usinas"
    (usinas / "uhe_ficticia").mkdir(parents=True)
    (usinas / "uhe_ficticia" / "perfil.toml").write_text(
        f'[usina]\nslug = "uhe_ficticia"\n\n[identificacao]\nceg = "{bc.UHE["ceg"]}"\n', encoding="utf-8")
    (usinas / "quebrado").mkdir()
    (usinas / "quebrado" / "perfil.toml").write_text("isto não é TOML [", encoding="utf-8")
    return {"raw": raw, "catalogo": tmp_path / "data" / "catalogo", "usinas": usinas}


def _executar(mundo: Dict[str, Path], **opcoes: Any) -> tuple:
    saida = io.StringIO()
    opcoes.setdefault("sem_portal", True)
    codigo = cu.executar_usinas(raiz_raw=mundo["raw"], pasta_catalogo=mundo["catalogo"], raiz_usinas=mundo["usinas"],
                                hoje=bc.HOJE, saida=saida, **opcoes)
    return codigo, saida.getvalue()


def _ler(mundo: Dict[str, Path], chave: str) -> pd.DataFrame:
    return pd.read_csv(mundo["catalogo"] / ARQUIVOS_CATALOGO[chave], sep=";", dtype=str, keep_default_na=False)


@pytest.fixture
def montado(mundo: Dict[str, Path]) -> Dict[str, Any]:
    codigo, texto = _executar(mundo)
    assert codigo == 0
    return {"mundo": mundo, "texto": texto, **{c: _ler(mundo, c) for c in ARQUIVOS_CATALOGO if c != "catalogo"},
            "json": json.loads((mundo["catalogo"] / ARQUIVOS_CATALOGO["catalogo"]).read_text(encoding="utf-8"))}


def _usina(montado: Dict[str, Any], ceg: str) -> pd.Series:
    linhas = montado["usinas"][montado["usinas"]["ceg"] == ceg]
    assert len(linhas) == 1, ceg
    return linhas.iloc[0]


def _cobertura(montado: Dict[str, Any], ceg: str) -> Dict[str, pd.Series]:
    c = montado["cobertura"]
    return {linha["conjunto_ons"]: linha for _, linha in c[c["ceg"] == ceg].iterrows()}


# ---------------------------------------------------------------------------
# Tipo pelo prefixo do CEG (D19)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ceg, tipo", [
    ("UHE.PH.MS.028761-0.01", "UHE"), ("pch.ph.ms.032163-0.01", "PCH"), ("UFV.RS.MS.052257-0.01", "UFV"),
    ("", "conjunto"), ("  ", "conjunto"), ("-", "conjunto"), ("UTX.XX.GO.000050-0.01", "outro"),
])
def test_tipo_pelo_prefixo_do_ceg(ceg: str, tipo: str) -> None:
    assert cu.tipo_do_ceg(ceg) == tipo


def test_tipos_e_divergencias(montado) -> None:
    u = montado["usinas"]
    assert list(u.columns) == COLUNAS_USINAS
    assert len(u) == len(bc.LINHAS_CADASTRO)  # uma linha por linha do cadastro, sem filtro (SC-015)
    assert dict(zip(u["nom_usina"], u["tipo"])) == {
        "UHE FICTICIA": "UHE", "PCH ALFA": "PCH", "UTE BETA": "UTE", "UFV GAMA": "UFV", "CGH DELTA": "CGH",
        "CONJUNTO ALFA": "conjunto", "USINA EPSILON": "outro", "EOL ZETA": "EOL", "UHE SEM DADOS": "UHE"}
    assert "tipo do ONS" in _usina(montado, bc.EOL["ceg"])["divergencias"]
    assert "soma das unidades" in _usina(montado, bc.UFV["ceg"])["divergencias"]
    assert _usina(montado, bc.UHE["ceg"])["divergencias"] == ""


# ---------------------------------------------------------------------------
# usinas.csv: cadastro, composição, capacidade e reservatórios
# ---------------------------------------------------------------------------


def test_unidades_ativas_composicao_vigente_e_reservatorio(montado) -> None:
    ute = _usina(montado, bc.UTE["ceg"])
    assert (ute["unidades_geradoras"], float(ute["potencia_efetiva_mw"])) == ("2", 150.0)  # só as ativas
    assert ute["potencias_unidades_mw"] == "75;75"
    assert _usina(montado, bc.UFV["ceg"])["potencias_unidades_mw"] == "21.43;28.57"
    assert ute["entrada_operacao"] == "2021-07-10" and ute["combustivel"] == "GÁS" and ute["subsistema"] == "SE"
    ufv = _usina(montado, bc.UFV["ceg"])
    assert float(ufv["potencia_autorizada_mw"]) == 2.507  # vírgula decimal aceita (correção P2)
    assert (ufv["id_conjunto"], ufv["nom_conjunto"]) == (bc.UFV["conjunto"], "CONJ. FOTOVOLTAICO BETA")
    assert ufv["id_ons"] == ""  # como publicado no cadastro
    pch = _usina(montado, bc.PCH["ceg"])
    assert pch["id_conjunto"] == bc.PCH["conjunto"]
    uhe = _usina(montado, bc.UHE["ceg"])
    assert (uhe["cod_usina"], uhe["id_reservatorio"], uhe["nom_reservatorio"]) == ("999", "PNUHFI", "FICTICIO")
    assert _usina(montado, bc.UTE["ceg"])["cod_usina"] == ""


def test_conjuntos_com_datas_e_tipo_pelo_ceg(montado) -> None:
    c = montado["conjuntos"]
    assert list(c.columns) == ["id_conjunto", "nom_conjunto", "ceg", "id_ons_usina", "nom_usina", "tipo", "tipo_ons",
                               "inicio", "fim", "estado", "subsistema"]
    antiga = c[c["ceg"] == bc.UTE_ANTIGA["ceg"]].iloc[0]
    assert (antiga["tipo"], antiga["tipo_ons"], antiga["inicio"], antiga["fim"]) == ("UTE", "UTE", "2019-08-22",
                                                                                      "2025-07-01")
    pch = c[c["ceg"] == bc.PCH["ceg"]].iloc[0]
    assert (pch["tipo"], pch["tipo_ons"], pch["fim"]) == ("PCH", "UHE", "")  # sentinela = vigente
    assert c[c["ceg"] == bc.UFV["ceg"]].iloc[0]["inicio"] == "2026-04-13"  # data dd/mm/aaaa


# ---------------------------------------------------------------------------
# Cobertura (D21 e D33)
# ---------------------------------------------------------------------------


def test_cobertura_propria_pelo_codigo_e_pelos_reservatorios(montado) -> None:
    uhe = _cobertura(montado, bc.UHE["ceg"])
    assert {k: v["nivel"] for k, v in uhe.items()} == {
        "evt": "proprio", "indicadores": "proprio", "programacao": "proprio", "disponibilidade": "proprio",
        "hidrologia": "proprio", "geracao": "proprio"}
    assert uhe["evt"]["identificador"] == "cod_usina=999"
    assert (uhe["evt"]["linhas"], uhe["evt"]["linhas_sem_valor"]) == ("24", "0")
    assert uhe["evt"]["arquivo"] == "ENERGIA_VERTIDA_TURBINAVEL_2026_09.csv"
    assert uhe["geracao"]["arquivo"] == "GERACAO_USINA-2_2026_09.parquet"
    assert _usina(montado, bc.UHE["ceg"])["cobertura_resumo"] == "proprio"


def test_cobertura_do_conjunto_inclusive_com_linhas_proprias_sem_valor(montado) -> None:
    pch = _cobertura(montado, bc.PCH["ceg"])
    assert pch["geracao"]["nivel"] == "conjunto" and pch["geracao"]["identificador"] == f"id_ons={bc.PCH['conjunto']}"
    assert pch["programacao"]["nivel"] == "conjunto"
    assert pch["programacao"]["identificador"] == "cod_exibicaousina=GOCJA-101;GOCJA-102"
    assert (pch["programacao"]["linhas"], pch["programacao"]["linhas_sem_valor"]) == ("96", "24")
    assert {pch[k]["nivel"] for k in ("evt", "hidrologia", "disponibilidade", "indicadores")} == {"ausente"}
    ufv = _cobertura(montado, bc.UFV["ceg"])
    assert set(ufv) == {"programacao", "geracao", "fator_capacidade", "restricao_detalhe", "restricao_razao"}
    assert (ufv["geracao"]["nivel"], ufv["programacao"]["nivel"]) == ("conjunto", "conjunto")
    # o fator de capacidade e a razão pelo conjunto; a restrição com detalhe só pelo id ONS da usina, que a UFV
    # não tem no cadastro (D21)
    assert (ufv["fator_capacidade"]["nivel"], ufv["restricao_razao"]["nivel"]) == ("conjunto", "conjunto")
    assert ufv["restricao_detalhe"]["nivel"] == "ausente"
    eol = _cobertura(montado, bc.EOL["ceg"])
    assert {eol[k]["nivel"] for k in ("fator_capacidade", "restricao_detalhe", "restricao_razao")} == {"proprio"}
    assert eol["restricao_detalhe"]["arquivo"] == "RESTRICAO_COFF_EOLICA_DETAIL_2026_09.parquet"  # a variante do tipo


def test_cobertura_agregada_ausente_e_so_do_arquivo_mais_recente(montado) -> None:
    assert {v["nivel"] for v in _cobertura(montado, bc.CGH["ceg"]).values()} == {"agregado"}  # Tipo III
    sem = _cobertura(montado, bc.SEM_DADOS["ceg"])
    assert {v["nivel"] for v in sem.values()} == {"ausente"}  # a EVT de 08/2026 não conta: só o arquivo mais recente
    assert _usina(montado, bc.SEM_DADOS["ceg"])["cobertura_resumo"] == "ausente"
    ute = _cobertura(montado, bc.UTE["ceg"])
    assert set(ute) == {"indicadores", "programacao", "disponibilidade", "geracao", "despacho", "cvu"}
    assert (ute["despacho"]["nivel"], ute["despacho"]["identificador"]) == ("proprio", f"ceg={bc.UTE['ceg']}")
    # o CVU não tem CEG: pelos códigos vigentes no despacho (D27); o 71 saiu em 09/2026
    assert (ute["cvu"]["nivel"], ute["cvu"]["identificador"], ute["cvu"]["linhas"]) == (
        "proprio", "cod_usinaplanejamento=70", "2")
    c = montado["cobertura"]
    assert set(c["ceg"]) == {bc.UHE["ceg"], bc.PCH["ceg"], bc.UTE["ceg"], bc.UFV["ceg"], bc.CGH["ceg"],
                             bc.EOL["ceg"], bc.SEM_DADOS["ceg"]}  # sem a linha de conjunto e o tipo "outro"
    assert list(c.columns) == ["ceg", "conjunto_ons", "nivel", "identificador", "linhas", "linhas_sem_valor",
                               "arquivo", "publicacao"]


# ---------------------------------------------------------------------------
# Programação, planejamento e agregados
# ---------------------------------------------------------------------------


def test_codigos_de_programacao_ligados_pelo_id_ons_ou_pelo_conjunto(montado) -> None:
    """FR-051: os códigos de todos os arquivos da Programação diária, com o primeiro e o último
    dia; o conjunto que trocou de código fica com os dois."""
    p = montado["programacao"]
    assert list(p.columns) == ["codigo_exibicao", "id_usina_ou_conjunto", "modalidade", "estado", "arquivo",
                               "primeiro_dia", "ultimo_dia"]
    ligacao = dict(zip(p["codigo_exibicao"], p["id_usina_ou_conjunto"]))
    assert ligacao == {bc.UHE["id_ons"]: bc.UHE["id_ons"], bc.UTE["id_ons"]: bc.UTE["id_ons"],
                       "GOCJA-100": bc.PCH["conjunto"], "GOCJA-101": bc.PCH["conjunto"],
                       "GOCJA-102": bc.PCH["conjunto"], "GOCJB": bc.UFV["conjunto"], "GOOUTRO": "", "GOVELHO": "",
                       bc.EOL["id_ons"]: bc.EOL["id_ons"]}
    antigo = p.set_index("codigo_exibicao").loc["GOCJA-100"]
    assert (antigo["primeiro_dia"], antigo["ultimo_dia"], antigo["arquivo"]) == (
        "2026-10-17", "2026-10-17", "PROGRAMACAO_DIARIA_2026_10_17.parquet")
    atuais = p[~p["codigo_exibicao"].isin(["GOCJA-100", "GOVELHO"])]
    assert set(atuais["arquivo"]) == {"PROGRAMACAO_DIARIA_2026_10_18.parquet"}
    assert set(atuais["primeiro_dia"]) == {"2026-10-18"}
    assert list(p["codigo_exibicao"][:2]) == ["GOCJA-100", "GOVELHO"]  # na ordem do primeiro dia
    assert dict(zip(p["codigo_exibicao"], p["estado"]))[bc.EOL["id_ons"]] == "MT"


def test_planejamento_com_o_primeiro_e_o_ultimo_mes_de_cada_codigo(montado) -> None:
    """Todos os arquivos do despacho, o anual antigo e os mensais; código como número."""
    p = montado["planejamento"]
    assert list(p.columns) == ["ceg", "codigo", "primeiro_mes", "ultimo_mes", "nomes_publicados", "arquivos"]
    ute = p[p["ceg"] == bc.UTE["ceg"]]
    assert {int(r.codigo): (r.primeiro_mes, r.ultimo_mes) for r in ute.itertuples()} == bc.PLANEJAMENTO_UTE
    setenta = ute[ute["codigo"] == "70"].iloc[0]
    assert (setenta["arquivos"], setenta["nomes_publicados"]) == ("2", "UT BETA; UTE BETA")  # nomes só exibidos
    assert set(p["ceg"]) == {bc.UTE["ceg"], bc.UTE_ANTIGA["ceg"]}


def test_agregados_pelo_estado_e_pela_modalidade(montado) -> None:
    a = montado["agregados"]
    assert list(a.columns) == ["id_estado", "mes", "modalidade", "tipo_ons", "grupo", "energia_mwh", "horas",
                               "horas_ausentes", "previsao", "arquivo"]
    assert sorted(set(a["mes"])) == [str(m) for m in pd.period_range("2025-10", "2026-09", freq="M")]
    assert set(a["grupo"]) == {"PQU GOGO MMGD", "PQU GOGO TIPO III", "CGH DELTA"}  # sem as usinas Tipo I e II
    assert set(a["id_estado"]) == {"GO"}
    mmgd = a[(a["grupo"] == "PQU GOGO MMGD") & (a["mes"] == "2026-09")].iloc[0]
    assert (int(mmgd["horas"]), float(mmgd["energia_mwh"]), mmgd["previsao"]) == (720, 720 * 30.0, "False")
    tipo3 = a[(a["grupo"] == "PQU GOGO TIPO III") & (a["mes"] == "2026-08")].iloc[0]
    assert (int(tipo3["horas"]), int(tipo3["horas_ausentes"]), tipo3["previsao"]) == (734, 10, "True")


def test_catalogo_json(montado) -> None:
    j = montado["json"]
    assert j["versao_formato"] == cu.VERSAO_FORMATO_CATALOGO == 1 and j["sem_portal"] is True
    assert set(j["cadastro"]) == {"modalidade-usina", "usina_conjunto", "capacidade-geracao", "reservatorio"}
    assert j["cadastro"]["modalidade-usina"]["arquivo"] == "MODALIDADE_USINA.csv"
    assert {c["conjunto"] for c in j["cobertura"]} == {"evt", "indicadores", "programacao", "disponibilidade",
                                                       "hidrologia", "geracao", "despacho", "cvu", "fator_capacidade",
                                                       "restricao_detalhe", "restricao_razao"}
    assert {c.get("variante") for c in j["cobertura"] if c["conjunto"] == "restricao_detalhe"} == {"EOL", "UFV"}
    assert len(j["agregados"]["meses"]) == 12
    assert j["contagens"]["por_tipo"]["UHE"] == 2 and j["contagens"]["por_estado"]["MT"] == 2


# ---------------------------------------------------------------------------
# Listagem e mensagens
# ---------------------------------------------------------------------------


def test_listagem_com_cobertura_por_conjunto_e_slug_do_perfil(mundo, caplog) -> None:
    codigo, texto = _executar(mundo, estado="go")
    assert codigo == 0
    linhas = texto.splitlines()
    cabecalho = next(linha for linha in linhas if "CEG" in linha)
    for coluna in ("EVT", "IND", "PRG", "DSP", "HID", "GER", "DES", "CVU", "FC", "RDT", "RRZ", "PERFIL"):
        assert coluna in cabecalho
    linha_uhe = next(linha for linha in linhas if bc.UHE["ceg"] in linha)
    assert "uhe_ficticia" in linha_uhe and linha_uhe.count(" P ") >= 5
    assert not any(bc.EOL["ceg"] in linha for linha in linhas)  # MT fora do filtro
    assert any("Catálogo de usinas: 9 linhas do cadastro" in r.getMessage() and "7 no filtro" in r.getMessage()
               for r in caplog.records)


def test_filtros_por_tipo_e_modalidade(mundo) -> None:
    _, texto = _executar(mundo, tipo="UFV")
    assert bc.UFV["ceg"] in texto and bc.UHE["ceg"] not in texto
    _, texto = _executar(mundo, modalidade="tipo ii-c")
    assert bc.PCH["ceg"] in texto and bc.UFV["ceg"] in texto and "CONJUNTO ALFA" in texto
    assert bc.UHE["ceg"] not in texto


def test_filtro_vazio_avisa_e_sai_com_zero(mundo, caplog) -> None:
    codigo, _ = _executar(mundo, estado="SP")
    assert codigo == 0
    assert any(r.levelname == "WARNING" and "Nenhuma usina no filtro" in r.getMessage() for r in caplog.records)


def test_aviso_das_divergencias_de_tipo(mundo, caplog) -> None:
    _executar(mundo)
    assert any(r.levelname == "WARNING" and "tipo publicado pelo ONS diferente do tipo do CEG" in r.getMessage()
               for r in caplog.records)


# ---------------------------------------------------------------------------
# Gravação e códigos de saída
# ---------------------------------------------------------------------------


def test_gravacao_por_inteiro_sem_bak_nem_pasta_temporaria(montado) -> None:
    pasta = montado["mundo"]["catalogo"]
    assert sorted(p.name for p in pasta.iterdir()) == sorted(ARQUIVOS_CATALOGO.values())
    (pasta / ARQUIVOS_CATALOGO["usinas"]).write_text("velho", encoding="utf-8")
    assert _executar(montado["mundo"])[0] == 0
    assert _ler(montado["mundo"], "usinas").shape[0] == len(bc.LINHAS_CADASTRO)
    assert not list(pasta.glob("*.bak")) and not (pasta / cu.PASTA_TEMPORARIA).exists()


@pytest.mark.parametrize("arquivo, conjunto", [
    ("reservatorio/RESERVATORIO.parquet", "reservatorio"),
    ("capacidade_geracao/CAPACIDADE_GERACAO.parquet", "capacidade-geracao"),
    ("modalidade_usina/MODALIDADE_USINA.csv", "modalidade-usina"),
])
def test_cadastral_ausente_sem_portal_da_codigo_2(mundo, caplog, arquivo: str, conjunto: str) -> None:
    (mundo["raw"] / arquivo).unlink()
    codigo, _ = _executar(mundo)
    assert codigo == 2
    assert any(r.levelname == "ERROR" and f"Conjunto cadastral do ONS não obtido ({conjunto})" in r.getMessage()
               for r in caplog.records)
    assert not mundo["catalogo"].exists()


def test_catalogo_do_ons_inacessivel_da_codigo_1(mundo, monkeypatch) -> None:
    def falhar(url: str) -> Dict[str, Any]:
        raise ConnectionError("portal fora do ar")
    monkeypatch.setattr(cu, "fetch_ckan_package_metadata", falhar)
    assert _executar(mundo, sem_portal=False)[0] == 1


def test_opcao_invalida_da_codigo_2() -> None:
    from src.__main__ import main

    with pytest.raises(SystemExit) as saida:
        main(["usinas", "--tipo", "XYZ"])
    assert saida.value.code == 2
    with pytest.raises(SystemExit) as saida:
        main(["usinas", "--estado", "Mato Grosso"])
    assert saida.value.code == 2


# ---------------------------------------------------------------------------
# Sincronização com o portal (simulada)
# ---------------------------------------------------------------------------


class _PortalFalso:
    """Catálogo CKAN falso: um recurso por arquivo da pasta ``origem``, com o pacote de cada pasta."""

    PACOTES = {"modalidade-usina": "modalidade_usina", "usina_conjunto": "usina_conjunto",
               "capacidade-geracao": "capacidade_geracao", "reservatorio": "reservatorio",
               "energia-vertida-turbinavel": "", "dados_hidrologicos_ho": "dados_hidrologicos_ho",
               "disponibilidade_usina": "disponibilidade_usina", "geracao-usina-2": "geracao_usina_2",
               "programacao_diaria": "programacao_diaria",
               "ind_disponibilidade_fgeracao_uge_mensal": "indicadores_ons/ind_disponibilidade_fgeracao_uge_mensal"}

    def __init__(self, origem: Path) -> None:
        self.origem = origem
        self.baixados: List[str] = []
        self.dicionarios: List[str] = []

    def metadados(self, url: str) -> Dict[str, Any]:
        pacote = url.rsplit("=", 1)[-1]
        pasta = self.origem / self.PACOTES.get(pacote, "__nada__")
        arquivos = [p for p in pasta.glob("*") if p.suffix.lower() in (".csv", ".parquet")] if pasta.exists() else []
        if pacote == "energia-vertida-turbinavel":
            arquivos = [p for p in arquivos if p.name.startswith("ENERGIA_VERTIDA")]
        return {"result": {"resources": [
            {"id": p.name, "name": p.stem, "url": f"https://portal/{pacote}/{p.name}", "format": p.suffix[1:].upper(),
             "size": p.stat().st_size, "last_modified": "2026-10-18T10:00:00"} for p in arquivos]}}

    def baixar(self, recurso: Any, destination_dir: Path, force: bool = False, manifest: Any = None, **_: Any) -> str:
        nome = recurso.url_download.rsplit("/", 1)[-1]
        pacote = recurso.url_download.split("/")[-2]
        destination_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.origem / self.PACOTES[pacote] / nome, destination_dir / nome)
        self.baixados.append(f"{pacote}/{nome}")
        recurso.status_sincronizacao = "DOWNLOADED"
        return str(destination_dir / nome)


def test_sincronizacao_baixa_os_cadastrais_o_mais_recente_de_cada_serie_e_12_meses_de_geracao(tmp_path, monkeypatch):
    origem = tmp_path / "portal"
    bc.gerar_brutos_catalogo(origem)
    portal = _PortalFalso(origem)
    monkeypatch.setattr(cu, "fetch_ckan_package_metadata", portal.metadados)
    monkeypatch.setattr(cu, "download_resource", portal.baixar)
    monkeypatch.setattr(cu, "sincronizar_dicionarios", lambda conjuntos, raiz: portal.dicionarios.extend(conjuntos) or [])
    mundo = {"raw": tmp_path / "data" / "raw", "catalogo": tmp_path / "data" / "catalogo", "usinas": tmp_path / "usinas"}
    codigo, _ = _executar(mundo, sem_portal=False)
    assert codigo == 0
    baixados = set(portal.baixados)
    assert {"modalidade-usina/MODALIDADE_USINA.csv", "usina_conjunto/USINA_CONJUNTO.parquet",
            "capacidade-geracao/CAPACIDADE_GERACAO.parquet", "reservatorio/RESERVATORIO.parquet"} <= baixados
    assert "energia-vertida-turbinavel/ENERGIA_VERTIDA_TURBINAVEL_2026_09.csv" in baixados
    assert "energia-vertida-turbinavel/ENERGIA_VERTIDA_TURBINAVEL_2026_08.csv" not in baixados
    # todos os arquivos da Programação diária, para os códigos de todo o período, como o despacho
    assert {"programacao_diaria/PROGRAMACAO_DIARIA_2026_10_18.parquet",
            "programacao_diaria/PROGRAMACAO_DIARIA_2026_10_17.parquet"} <= baixados
    geracao = sorted(b for b in baixados if b.startswith("geracao-usina-2/"))
    assert geracao == [f"geracao-usina-2/GERACAO_USINA-2_{m.year}_{m.month:02d}.parquet"
                       for m in pd.period_range("2025-10", "2026-09", freq="M")]
    assert set(portal.dicionarios) >= {"modalidade-usina", "usina_conjunto", "capacidade-geracao", "reservatorio",
                                       "geracao-usina-2", "programacao_diaria", "energia-vertida-turbinavel"}
    assert (mundo["raw"] / "reservatorio" / "RESERVATORIO.parquet").is_file()
    assert _ler(mundo, "usinas").shape[0] == len(bc.LINHAS_CADASTRO)


def test_download_cadastral_sem_sucesso_da_codigo_2(tmp_path, monkeypatch, caplog) -> None:
    origem = tmp_path / "portal"
    bc.gerar_brutos_catalogo(origem)
    portal = _PortalFalso(origem)

    def baixar(recurso: Any, destination_dir: Path, **kw: Any) -> str:
        if "usina_conjunto" in recurso.url_download:
            raise OSError("conexão interrompida")
        return portal.baixar(recurso, destination_dir, **kw)
    monkeypatch.setattr(cu, "fetch_ckan_package_metadata", portal.metadados)
    monkeypatch.setattr(cu, "download_resource", baixar)
    monkeypatch.setattr(cu, "sincronizar_dicionarios", lambda conjuntos, raiz: [])
    mundo = {"raw": tmp_path / "data" / "raw", "catalogo": tmp_path / "data" / "catalogo", "usinas": tmp_path / "usinas"}
    assert _executar(mundo, sem_portal=False)[0] == 2
    assert any("Conjunto cadastral do ONS não obtido (usina_conjunto)" in r.getMessage() for r in caplog.records)
