"""Testes do motor comum dos conjuntos horários do ONS (spec 006, US3 a US5)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional
from unittest.mock import patch

import pandas as pd
import pytest

from src.conjuntos_ons import (
    DescricaoConjunto,
    Regra,
    carregar_serie_processada,
    data_obtencao,
    exportar_serie,
    hora_de_inicio,
    ler_arquivo,
    listar_ausencias,
    montar_serie,
    periodo_do_arquivo,
    selecionar_recursos,
    sincronizar_conjunto,
)
from src.models import RecursoONS

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
def test_leitura_conta_identificacao_parcial_e_invalidos(tmp_path: Path, nome: str) -> None:
    linhas = _linhas_usina("2025-01-01 00:00", 3) + _homonimos("2025-01-01 00:00:00")
    linhas[1]["val_a"] = "abc"
    caminho = _gravar(tmp_path, nome, linhas)
    dados, auditoria = ler_arquivo(DESC, caminho)
    assert len(dados) == 3
    assert auditoria["linhas_lidas"] == 6
    assert auditoria["linhas_usina"] == 3
    assert auditoria["linhas_so_identificador"] == 1
    assert auditoria["linhas_so_conferencia"] == 1
    assert auditoria["horas_usina"] == 3
    assert auditoria["valores_invalidos"] == 1
    assert auditoria["status"] == "PROCESSADO"
    assert auditoria["periodo"] == "2025-01"
    assert dados["_nao_numerico"].tolist() == [False, True, False]
    assert pd.isna(dados["val_a"].iloc[1]) and dados["val_b"].tolist() == [1.0, 1.0, 1.0]


def test_leitura_csv_em_latin1(tmp_path: Path) -> None:
    caminho = _gravar(tmp_path, "D_2025_02.csv", _linhas_usina("2025-02-01 00:00", 2), encoding="latin-1")
    dados, auditoria = ler_arquivo(DESC, caminho)
    assert auditoria["status"] == "PROCESSADO" and len(dados) == 2


def test_linhas_de_formato_irregular_contadas_avisadas_e_nao_extraidas(tmp_path: Path, caplog) -> None:
    """Princípio IV: linha curta e linha longa ficam fora da extração, na auditoria e no log (T054)."""
    caminho = _gravar(tmp_path, "D_2025_05.csv", _linhas_usina("2025-05-01 00:00", 4))
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    linhas[2] = ";".join(linhas[2].split(";")[:-1])  # 01:00 sem o último campo (linha 3 do arquivo)
    linhas[4] = linhas[4] + ";excedente"  # 03:00 com um campo a mais
    linhas.insert(4, "")  # linha em branco antes dela: a linha longa passa a ser a 6
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    with caplog.at_level(logging.WARNING):
        dados, auditoria = ler_arquivo(DESC, caminho)
    assert auditoria["linhas_formato_irregular"] == 2
    assert auditoria["linhas_lidas"] == 4 and auditoria["linhas_usina"] == 2
    assert dados["din_instante"].dt.strftime("%H:%M").tolist() == ["00:00", "02:00"]
    assert dados["val_a"].tolist() == [10.0, 10.0] and dados["val_b"].tolist() == [1.0, 1.0]
    avisos = " ".join(r.getMessage() for r in caplog.records if r.levelno == logging.WARNING)
    assert "D_2025_05.csv" in avisos and "2 linhas de formato irregular" in avisos and "3, 6" in avisos


def test_csv_regular_sem_linhas_irregulares(tmp_path: Path, caplog) -> None:
    caminho = _gravar(tmp_path, "D_2025_06.csv", _linhas_usina("2025-06-01 00:00", 3))
    with caplog.at_level(logging.WARNING):
        dados, auditoria = ler_arquivo(DESC, caminho)
    assert auditoria["linhas_formato_irregular"] == 0 and auditoria["linhas_lidas"] == 3 and len(dados) == 3
    assert not [r for r in caplog.records if "formato irregular" in r.getMessage()]


def test_leitura_sem_registros_e_falha(tmp_path: Path) -> None:
    caminho = _gravar(tmp_path, "D_2025_03.csv", _homonimos("2025-03-01 00:00:00"))
    assert ler_arquivo(DESC, caminho)[1]["status"] == "SEM_REGISTROS"
    corrompido = tmp_path / "D_2025_04.parquet"
    corrompido.write_bytes(b"isto nao e parquet")
    dados, auditoria = ler_arquivo(DESC, corrompido)
    assert auditoria["status"] == "FALHA" and dados.empty and auditoria["mensagem"]


def test_hora_de_inicio_na_convencao_de_fim_de_hora() -> None:
    publicados = pd.to_datetime(pd.Series(["2025-01-01 01:00:00", "2025-01-01 15:00:00", "2025-01-01 23:59:00"]))
    assert hora_de_inicio(publicados).dt.strftime("%Y-%m-%d %H:%M").tolist() == [
        "2025-01-01 00:00", "2025-01-01 14:00", "2025-01-01 23:00"]


def _manifesto(pasta: Path, entradas: dict) -> None:
    (pasta / "_manifesto_ons.json").write_text(json.dumps(entradas), encoding="utf-8")


def test_montagem_deduplica_e_lista_ausencias(tmp_path: Path) -> None:
    pasta = tmp_path / "conjunto_teste"
    # janeiro completo menos 3 horas; fevereiro com arquivo mas sem a usina; março sem arquivo
    janeiro = [l for i, l in enumerate(_linhas_usina("2025-01-01 00:00", 31 * 24)) if i not in (10, 11, 500)]
    _gravar(pasta, "D_2025_01.csv", janeiro)
    _gravar(pasta, "D_2025_02.csv", _homonimos("2025-02-01 00:00:00"))
    # arquivo publicado depois, repetindo a última hora de janeiro com outro valor
    _gravar(pasta, "D_2025_01_revisao.csv", [])  # nome sem período válido: ignorado
    _gravar(pasta, "D_2025_04.csv", _linhas_usina("2025-01-31 23:00", 1, valor=99.0) + _linhas_usina("2025-04-01 00:00", 2))
    _manifesto(pasta, {
        "D_2025_01.csv": {"ultima_modificacao": "2025-02-01T00:00:00", "recursos_duplicados_catalogo": 1},
        "D_2025_02.csv": {"ultima_modificacao": "2025-03-01T00:00:00"},
        "D_2025_04.csv": {"ultima_modificacao": "2025-05-01T00:00:00"},
    })
    serie = montar_serie(DESC, pasta, pd.Timestamp("2025-01-01 00:00"), pd.Timestamp("2025-04-01 01:00"))

    h = serie.horaria.set_index("din_instante")
    assert h.loc[pd.Timestamp("2025-01-31 23:00"), "val_a"] == 99.0  # prevalece o arquivo mais recente
    assert h.loc[pd.Timestamp("2025-01-31 23:00"), "arquivo_origem"] == "D_2025_04.csv"
    assert h.index.is_unique and h.index.min() >= pd.Timestamp("2025-01-01") and h.index.max() <= pd.Timestamp("2025-04-01 01:00")

    aud = serie.auditoria.set_index("arquivo")
    assert aud.loc["D_2025_01.csv", "duplicatas_conflitantes"] == 1
    assert aud.loc["D_2025_01.csv", "recursos_duplicados_catalogo"] == 1
    assert aud.loc["D_2025_02.csv", "status"] == "SEM_REGISTROS"
    assert "D_2025_01_revisao.csv" not in aud.index

    aus = serie.ausencias
    assert aus[aus["tipo"] == "HORAS"][["horas"]].squeeze().tolist() == [2, 1]
    assert aus[aus["tipo"] == "MES_SEM_USINA"]["inicio"].dt.month.tolist() == [2]
    sem_arquivo = aus[aus["tipo"] == "MES_SEM_ARQUIVO"]
    assert sem_arquivo["inicio"].dt.month.tolist() == [3] and sem_arquivo["horas"].tolist() == [31 * 24]


def test_falhas_de_download_entram_na_auditoria(tmp_path: Path) -> None:
    pasta = tmp_path / "conjunto_teste"
    _gravar(pasta, "D_2025_01.csv", _linhas_usina("2025-01-01 00:00", 2))
    falhas = [{"arquivo": "D_2025_02.csv", "formato": "CSV", "periodo": "2025-02", "status": "FALHA",
               "mensagem": "HTTP 500"}]
    serie = montar_serie(DESC, pasta, pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-01 01:00"), falhas=falhas)
    assert serie.auditoria.set_index("arquivo").loc["D_2025_02.csv", "status"] == "FALHA"


def test_listar_ausencias_agrupa_horas_continuas() -> None:
    presentes = pd.Series(pd.date_range("2025-01-01", "2025-01-01 23:00", freq="h").delete([5, 6, 7, 20]))
    aus = listar_ausencias(presentes, pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-01 23:00"), {(2025, 1)})
    assert aus[["inicio", "fim", "horas"]].astype(str).values.tolist() == [
        ["2025-01-01 05:00:00", "2025-01-01 07:00:00", "3"], ["2025-01-01 20:00:00", "2025-01-01 20:00:00", "1"]]


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

    with patch("src.conjuntos_ons.fetch_ckan_package_metadata", return_value=metadados), \
            patch("src.conjuntos_ons.download_resource", side_effect=baixar):
        falhas = sincronizar_conjunto(DESC, pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-28"), pasta)
    assert [f["arquivo"] for f in falhas] == ["D_2025_02.csv"] and falhas[0]["status"] == "FALHA"
    manifesto = json.loads((pasta / "_manifesto_ons.json").read_text(encoding="utf-8"))
    assert manifesto["D_2025_01.parquet"]["recursos_duplicados_catalogo"] == 1
    assert data_obtencao(pasta) == ""  # o simulador não registra a data; a função não falha


def test_exportar_e_carregar_ignorando_bak_e_tmp(tmp_path: Path) -> None:
    pasta = tmp_path / "conjunto_teste"
    _gravar(pasta, "D_2025_01.csv", _linhas_usina("2025-01-01 00:00", 2))
    serie = montar_serie(DESC, pasta, pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-01 01:00"))
    saida = tmp_path / "processed"
    arquivos = {"horaria": saida / "h.csv", "ausencias": saida / "a.csv", "auditoria": saida / "r.csv"}
    exportar_serie(serie, arquivos)
    (saida / "h.csv.bak").write_text("lixo", encoding="utf-8")
    (saida / "h.csv.tmp").write_text("lixo", encoding="utf-8")
    lida = carregar_serie_processada(arquivos)
    assert lida is not None and len(lida.horaria) == 2
    assert not any(c.startswith("_") for c in lida.horaria.columns)
    assert lida.horaria["din_instante"].dtype.kind == "M"
    assert carregar_serie_processada({"horaria": saida / "nao_existe.csv"}) is None
