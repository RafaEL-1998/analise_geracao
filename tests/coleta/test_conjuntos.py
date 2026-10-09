"""Testes da extração dos conjuntos horários do ONS na Coleta de dados (FR-017 a FR-019, FR-034 a FR-040, FR-044)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List
from unittest.mock import patch

import pandas as pd
import pytest

from src.coleta.conjuntos import (
    COLUNAS_AUDITORIA_COLETA,
    DescricaoConjunto,
    Regra,
    descricoes,
    extrair_arquivo,
    extrair_conjunto,
    periodo_do_arquivo,
    selecionar_recursos,
    sincronizar_conjunto,
)
from src.comum.modelos import RecursoONS
from src.comum.perfil import carregar_perfil

DESC = DescricaoConjunto(
    pacote="conjunto_teste",
    pasta="conjunto_teste",
    identificador=Regra("id_ons", "MSUHSD"),
    conferencias=(Regra("ceg", "UHE.PH.MS.028761-0.01"), Regra("id_estado", "MS")),
    colunas_valor=("val_a", "val_b"),
)


def _linhas_usina(inicio: str, horas: int, valor: float = 10.0) -> List[dict]:
    instantes = pd.date_range(inicio, periods=horas, freq="h")
    return [{"id_ons": "MSUHSD", "ceg": "UHE.PH.MS.028761-0.01", "id_estado": "MS", "nom_usina": "São Domingos",
             "din_instante": t.strftime("%Y-%m-%d %H:%M:%S"), "val_a": f"{valor:.2f}", "val_b": "1.00"} for t in instantes]


def _homonimos(instante: str) -> List[dict]:
    return [
        # identificador confere, estado não (só identificador)
        {"id_ons": "MSUHSD", "ceg": "UHE.PH.MS.028761-0.01", "id_estado": "GO", "nom_usina": "X",
         "din_instante": instante, "val_a": "1", "val_b": "1"},
        # conferência confere, identificador não (só conferência)
        {"id_ons": "OUTRO", "ceg": "UHE.PH.MS.028761-0.01", "id_estado": "MS", "nom_usina": "Y",
         "din_instante": instante, "val_a": "1", "val_b": "1"},
        # outra usina
        {"id_ons": "GOUSD", "ceg": "UHE.PH.GO.027665-0.01", "id_estado": "GO", "nom_usina": "São Domingos I",
         "din_instante": instante, "val_a": "1", "val_b": "1"},
    ]


def _gravar(pasta: Path, nome: str, linhas: List[dict], encoding: str = "utf-8") -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / nome
    tabela = pd.DataFrame(linhas)
    if caminho.suffix == ".parquet":
        tabela.to_parquet(caminho, index=False)
    else:
        tabela.to_csv(caminho, sep=";", index=False, encoding=encoding)
    return caminho


def _recurso(nome: str, formato: str, ultima_modificacao: str = "2026-10-01T10:00:00", tamanho: int = 100) -> RecursoONS:
    return RecursoONS(id_recurso=nome, nome_recurso=nome, url_download=f"https://ons/x/{nome}", formato=formato,
                      tamanho_bytes=tamanho, ultima_modificacao=ultima_modificacao)


def _manifesto(pasta: Path, entradas: dict) -> None:
    (pasta / "_manifesto_ons.json").write_text(json.dumps(entradas), encoding="utf-8")


def test_descricoes_com_os_identificadores_do_perfil() -> None:
    perfil = carregar_perfil("sao_domingos")
    d = descricoes(perfil)
    assert set(d) == {"disponibilidade", "hidrologia", "geracao"}
    assert d["disponibilidade"].identificador == Regra("id_ons", perfil.identificacao.id_ons)
    assert Regra("ceg", perfil.identificacao.ceg) in d["geracao"].conferencias
    assert d["hidrologia"].identificador == Regra("cod_usina", perfil.identificacao.cod_usina)
    assert Regra("nom_reservatorio", perfil.identificacao.nome_ons, "contem") in d["hidrologia"].conferencias
    assert d["hidrologia"].convencao_hora == "fim" and d["geracao"].convencao_hora == "inicio"


def test_periodo_pelo_nome_do_arquivo() -> None:
    assert periodo_do_arquivo("DISPONIBILIDADE_USINA_2023_01.parquet") == (2023, 1)
    assert periodo_do_arquivo("GERACAO_USINA-2_2018.parquet") == (2018, None)
    assert periodo_do_arquivo("DADOS_HIDROLOGICOS_HO_2026_10.csv") == (2026, 10)
    assert periodo_do_arquivo("DicionarioDados_GeracaoPorUsina.pdf") is None


def test_formato_preferido_por_mes_e_recorte_do_periodo() -> None:
    recursos = [_recurso(f"D_{a}_{m:02d}.csv", "CSV") for a in (2018, 2022, 2023) for m in (7, 8, 12, 1, 2)]
    recursos += [_recurso("D_2023_01.parquet", "PARQUET"), _recurso("D_2023_02.parquet", "PARQUET")]
    escolhidos, duplicados = selecionar_recursos(DESC, recursos, pd.Timestamp("2018-08-28 00:00"),
                                                 pd.Timestamp("2023-01-31 23:00"))
    nomes = [r.nome_recurso for r in escolhidos]
    assert nomes == ["D_2018_08.csv", "D_2018_12.csv", "D_2022_01.csv", "D_2022_02.csv", "D_2022_07.csv",
                     "D_2022_08.csv", "D_2022_12.csv", "D_2023_01.parquet"]
    assert duplicados == {}


def test_arquivos_anuais_se_sobrepoem_pelo_ano() -> None:
    recursos = [_recurso("G_2017.parquet", "PARQUET"), _recurso("G_2018.parquet", "PARQUET"),
                _recurso("G_2022_01.parquet", "PARQUET"), _recurso("G_2022_02.parquet", "PARQUET")]
    escolhidos, _ = selecionar_recursos(DESC, recursos, pd.Timestamp("2018-08-28"), pd.Timestamp("2022-01-15"))
    assert [r.nome_recurso for r in escolhidos] == ["G_2018.parquet", "G_2022_01.parquet"]


def test_recurso_duplicado_no_catalogo() -> None:
    sem_data = _recurso("H_2026_09.parquet", "PARQUET", ultima_modificacao="", tamanho=14698)
    com_data = _recurso("H_2026_09.parquet", "PARQUET", ultima_modificacao="2026-10-05T12:53:43", tamanho=278680)
    escolhidos, duplicados = selecionar_recursos(DESC, [sem_data, com_data], pd.Timestamp("2026-09-01"),
                                                 pd.Timestamp("2026-09-28"))
    assert escolhidos == [com_data]
    assert duplicados == {"H_2026_09.parquet": 1}
    # sem data em nenhum dos dois: fica o maior
    menor = _recurso("H_2026_09.parquet", "PARQUET", ultima_modificacao="", tamanho=10)
    maior = _recurso("H_2026_09.parquet", "PARQUET", ultima_modificacao="", tamanho=20)
    escolhidos, _ = selecionar_recursos(DESC, [menor, maior], pd.Timestamp("2026-09-01"), pd.Timestamp("2026-09-28"))
    assert escolhidos == [maior]


@pytest.mark.parametrize("nome", ["D_2025_01.csv", "D_2025_01.parquet"])
def test_extracao_conta_identificacao_parcial_e_invalidos(tmp_path: Path, nome: str) -> None:
    linhas = _linhas_usina("2025-01-01 00:00", 3) + _homonimos("2025-01-01 00:00:00")
    linhas[1]["val_a"] = "abc"
    caminho = _gravar(tmp_path, nome, linhas)
    dados, auditoria = extrair_arquivo(DESC, caminho)
    assert len(dados) == 3
    assert auditoria["linhas_lidas"] == 6
    assert auditoria["linhas_usina"] == 3
    assert auditoria["linhas_so_identificador"] == 1
    assert auditoria["linhas_so_conferencia"] == 1
    assert auditoria["valores_invalidos"] == 1
    assert auditoria["status"] == "PROCESSADO"
    assert auditoria["periodo"] == "2025-01"
    assert "horas_usina" not in auditoria  # horas da usina e duplicatas são do Tratamento de dados
    assert dados["_nao_numerico"].tolist() == [False, True, False]
    assert pd.isna(dados["val_a"].iloc[1]) and dados["val_b"].tolist() == [1.0, 1.0, 1.0]


def test_extracao_mantem_o_instante_como_publicado(tmp_path: Path) -> None:
    """A Coleta não converte a convenção de hora (FR-040): o instante sai como publicado."""
    linhas = _linhas_usina("2025-01-01 01:00", 2)
    linhas[1]["din_instante"] = "2025-01-01 23:59:00"
    dados, _ = extrair_arquivo(DESC, _gravar(tmp_path, "D_2025_01.csv", linhas))
    assert dados["din_instante"].dt.strftime("%H:%M").tolist() == ["01:00", "23:59"]


def test_extracao_csv_em_latin1(tmp_path: Path) -> None:
    caminho = _gravar(tmp_path, "D_2025_02.csv", _linhas_usina("2025-02-01 00:00", 2), encoding="latin-1")
    dados, auditoria = extrair_arquivo(DESC, caminho)
    assert auditoria["status"] == "PROCESSADO" and len(dados) == 2


def test_linhas_de_formato_irregular_contadas_avisadas_e_nao_extraidas(tmp_path: Path, caplog) -> None:
    caminho = _gravar(tmp_path, "D_2025_05.csv", _linhas_usina("2025-05-01 00:00", 4))
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    linhas[2] = ";".join(linhas[2].split(";")[:-1])  # 01:00 sem o último campo (linha 3 do arquivo)
    linhas[4] = linhas[4] + ";excedente"  # 03:00 com um campo a mais
    linhas.insert(4, "")  # linha em branco antes dela: a linha longa passa a ser a 6
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    with caplog.at_level(logging.WARNING):
        dados, auditoria = extrair_arquivo(DESC, caminho)
    assert auditoria["linhas_formato_irregular"] == 2
    assert auditoria["linhas_lidas"] == 4 and auditoria["linhas_usina"] == 2
    assert dados["din_instante"].dt.strftime("%H:%M").tolist() == ["00:00", "02:00"]
    assert dados["val_a"].tolist() == [10.0, 10.0] and dados["val_b"].tolist() == [1.0, 1.0]
    avisos = " ".join(r.getMessage() for r in caplog.records if r.levelno == logging.WARNING)
    assert "D_2025_05.csv" in avisos and "2 linhas de formato irregular" in avisos and "3, 6" in avisos


def test_csv_regular_sem_linhas_irregulares(tmp_path: Path, caplog) -> None:
    caminho = _gravar(tmp_path, "D_2025_06.csv", _linhas_usina("2025-06-01 00:00", 3))
    with caplog.at_level(logging.WARNING):
        dados, auditoria = extrair_arquivo(DESC, caminho)
    assert auditoria["linhas_formato_irregular"] == 0 and auditoria["linhas_lidas"] == 3 and len(dados) == 3
    assert not [r for r in caplog.records if "formato irregular" in r.getMessage()]


def test_extracao_sem_registros_e_falha(tmp_path: Path) -> None:
    caminho = _gravar(tmp_path, "D_2025_03.csv", _homonimos("2025-03-01 00:00:00"))
    assert extrair_arquivo(DESC, caminho)[1]["status"] == "SEM_REGISTROS"
    corrompido = tmp_path / "D_2025_04.parquet"
    corrompido.write_bytes(b"isto nao e parquet")
    dados, auditoria = extrair_arquivo(DESC, corrompido)
    assert auditoria["status"] == "FALHA" and dados.empty and auditoria["mensagem"]


def test_extracao_do_conjunto_em_ordem_de_publicacao_sem_juntar_duplicatas(tmp_path: Path) -> None:
    pasta = tmp_path / "conjunto_teste"
    _gravar(pasta, "D_2025_01.csv", _linhas_usina("2025-01-01 00:00", 2))
    _gravar(pasta, "D_2025_02.csv", _homonimos("2025-02-01 00:00:00"))
    _gravar(pasta, "D_2025_01_revisao.csv", [])  # nome sem período válido: ignorado
    _gravar(pasta, "D_2024_12.csv", _linhas_usina("2024-12-31 23:00", 1))  # fora do período
    # publicado antes do de janeiro e repetindo a última hora de janeiro
    _gravar(pasta, "D_2025_04.csv", _linhas_usina("2025-01-01 01:00", 1, valor=99.0))
    _manifesto(pasta, {
        "D_2025_01.csv": {"ultima_modificacao": "2025-05-01T00:00:00", "recursos_duplicados_catalogo": 1},
        "D_2025_02.csv": {"ultima_modificacao": "2025-03-01T00:00:00"},
        "D_2025_04.csv": {"ultima_modificacao": "2025-02-01T00:00:00"},
    })
    falhas = [{"arquivo": "D_2025_03.csv", "formato": "CSV", "periodo": "2025-03", "status": "FALHA",
               "mensagem": "HTTP 500"}]
    extraido, auditoria = extrair_conjunto(DESC, pasta, pd.Timestamp("2025-01-01"), pd.Timestamp("2025-04-30 23:00"),
                                           falhas)
    assert list(auditoria.columns) == COLUNAS_AUDITORIA_COLETA
    assert auditoria["arquivo"].tolist() == ["D_2025_04.csv", "D_2025_02.csv", "D_2025_01.csv", "D_2025_03.csv"]
    aud = auditoria.set_index("arquivo")
    assert aud.loc["D_2025_01.csv", "data_publicacao"] == "2025-05-01T00:00:00"
    assert aud.loc["D_2025_01.csv", "recursos_duplicados_catalogo"] == 1
    assert aud.loc["D_2025_02.csv", "status"] == "SEM_REGISTROS"
    assert aud.loc["D_2025_03.csv", "status"] == "FALHA" and not aud.loc["D_2025_03.csv", "obtido"]
    assert aud.loc["D_2025_01.csv", "obtido"]
    # a hora repetida fica duas vezes, com o arquivo de origem; a escolha é do Tratamento de dados
    repetida = extraido[extraido["din_instante"] == pd.Timestamp("2025-01-01 01:00")]
    assert repetida["arquivo_origem"].tolist() == ["D_2025_04.csv", "D_2025_01.csv"]
    assert list(extraido.columns) == ["din_instante", "val_a", "val_b", "_nao_numerico", "arquivo_origem"]


def test_sincronizacao_registra_falhas_e_duplicados(tmp_path: Path) -> None:
    pasta = tmp_path / "conjunto_teste"
    metadados = {"result": {"resources": [
        {"id": "1", "name": "D_2025_01.parquet", "url": "https://ons/x/D_2025_01.parquet", "format": "PARQUET",
         "size": 10, "last_modified": "2026-10-01T00:00:00"},
        {"id": "2", "name": "D_2025_01.parquet", "url": "https://ons/x/D_2025_01.parquet", "format": "PARQUET",
         "size": 5, "last_modified": None},
        {"id": "3", "name": "D_2025_02.csv", "url": "https://ons/x/D_2025_02.csv", "format": "CSV",
         "size": 10, "last_modified": "2026-10-01T00:00:00"},
    ]}}

    def baixar(recurso, destination_dir, force, manifest):
        if recurso.nome_recurso.endswith(".csv"):
            raise OSError("HTTP 500")
        (destination_dir / recurso.nome_recurso).write_bytes(b"x")
        manifest[recurso.nome_recurso] = {"ultima_modificacao": recurso.ultima_modificacao}
        return "DOWNLOADED"

    with patch("src.coleta.conjuntos.fetch_ckan_package_metadata", return_value=metadados), \
            patch("src.coleta.conjuntos.download_resource", side_effect=baixar):
        falhas = sincronizar_conjunto(DESC, pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-28"), pasta)
    assert [f["arquivo"] for f in falhas] == ["D_2025_02.csv"] and falhas[0]["status"] == "FALHA"
    manifesto = json.loads((pasta / "_manifesto_ons.json").read_text(encoding="utf-8"))
    assert manifesto["D_2025_01.parquet"]["recursos_duplicados_catalogo"] == 1
