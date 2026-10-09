"""Correções P1 a P5 da Coleta de dados (spec 006, decisão R10; tarefa T027), com catálogo e arquivos sintéticos.

- P1: EVT, indicadores e programação escolhem um recurso entre os repetidos no catálogo; o arquivo temporário do
  download leva o id do recurso.
- P2: vírgula decimal aceita nos conjuntos horários e na potência da ficha.
- P3: uma normalização única (sem acento, sem espaços nas pontas, maiúsculas) na EVT, na programação e no filtro do
  Parquet da geração.
- P4: coluna de conferência ausente torna o arquivo ``FALHA``, com o motivo.
- P5: CSV vazio da EVT com o motivo "arquivo vazio" na auditoria.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List
from unittest.mock import patch

import pandas as pd

from src.coleta import catalogo
from src.coleta.cadastro import extrair_ficha
from src.coleta.conjuntos import DescricaoConjunto, Regra, descricoes, extrair_arquivo
from src.coleta.evt import filter_csv_file, sincronizar_evt
from src.coleta.indicadores import sincronizar_indicadores
from src.coleta.programacao import ler_arquivo, sincronizar_programacao
from src.comum.modelos import RecursoONS
from src.comum.regras import CONJUNTOS_INDICADORES_ONS

DESC = DescricaoConjunto(
    pacote="conjunto_teste",
    pasta="conjunto_teste",
    identificador=Regra("id_ons", "MSUHSD"),
    conferencias=(Regra("ceg", "UHE.PH.MS.028761-0.01"), Regra("id_estado", "MS")),
    colunas_valor=("val_a",),
)
COLUNAS_EVT = ["id_subsistema", "nom_subsistema", "nom_bacia", "nom_rio", "nom_agente", "nom_reservatorio", "cod_usina",
               "din_instante", "val_geracao", "val_disponibilidade", "val_vazaoturbinada", "val_vazaovertida",
               "val_vazaovertidanaoturbinavel", "val_produtividade", "val_folgadegeracao", "val_energiavertida",
               "val_vazaovertidaturbinavel", "val_energiavertidaturbinavel"]


def _recurso_ckan(id_: str, nome: str, formato: str, tamanho: int, publicado) -> Dict[str, object]:
    return {"id": id_, "name": nome, "url": f"https://ons/x/{nome}", "format": formato, "size": tamanho,
            "last_modified": publicado}


def _baixados() -> tuple:
    """Simulador de ``download_resource`` que registra (arquivo, id do recurso) de cada download pedido."""
    pedidos: List[tuple] = []

    def baixar(recurso, destination_dir, force=False, manifest=None):
        nome = catalogo._local_filename(recurso)
        pedidos.append((nome, recurso.id_recurso))
        (Path(destination_dir) / nome).write_bytes(b"x")
        if manifest is not None:
            manifest[nome] = {"ultima_modificacao": recurso.ultima_modificacao}
        return "DOWNLOADED"

    return pedidos, baixar


# ---------------------------------------------------------------------------
# P1 — recursos repetidos e arquivo temporário
# ---------------------------------------------------------------------------


def test_p1_evt_baixa_um_recurso_por_arquivo(tmp_path: Path) -> None:
    metadados = {"success": True, "result": {"resources": [
        _recurso_ckan("a", "ENERGIA_VERTIDA_TURBINAVEL_2024_01.csv", "CSV", 10, None),
        _recurso_ckan("b", "ENERGIA_VERTIDA_TURBINAVEL_2024_01.csv", "CSV", 5, "2024-02-05T10:00:00"),
        _recurso_ckan("c", "ENERGIA_VERTIDA_TURBINAVEL_2024_02.csv", "CSV", 10, "2024-03-05T10:00:00"),
    ]}}
    pedidos, baixar = _baixados()
    with patch("src.coleta.evt.fetch_ckan_package_metadata", return_value=metadados), \
            patch("src.coleta.evt.download_resource", side_effect=baixar):
        assert sincronizar_evt(tmp_path) == []
    assert sorted(pedidos) == [("ENERGIA_VERTIDA_TURBINAVEL_2024_01.csv", "b"),
                               ("ENERGIA_VERTIDA_TURBINAVEL_2024_02.csv", "c")]
    manifesto = json.loads((tmp_path / "_manifesto_ons.json").read_text(encoding="utf-8"))
    assert manifesto["ENERGIA_VERTIDA_TURBINAVEL_2024_01.csv"]["recursos_duplicados_catalogo"] == 1


def test_p1_indicadores_baixam_um_recurso_por_arquivo(tmp_path: Path) -> None:
    def metadados(url: str) -> dict:
        conjunto = url.rsplit("/", 1)[-1].rsplit("=", 1)[-1]
        nome = f"{conjunto.upper()}_2024.csv"
        return {"success": True, "result": {"resources": [
            _recurso_ckan(f"{conjunto}-1", nome, "CSV", 10, "2024-12-01T00:00:00"),
            _recurso_ckan(f"{conjunto}-2", nome, "CSV", 20, "2024-12-01T00:00:00"),
        ]}}

    pedidos, baixar = _baixados()
    with patch("src.coleta.indicadores.fetch_ckan_package_metadata", side_effect=metadados), \
            patch("src.coleta.indicadores.download_resource", side_effect=baixar):
        assert sincronizar_indicadores(2024, 2024, tmp_path) == []
    assert len(pedidos) == len(CONJUNTOS_INDICADORES_ONS)
    assert all(id_.endswith("-2") for _, id_ in pedidos)  # empate na publicação: fica o maior


def test_p1_programacao_baixa_um_recurso_por_dia(tmp_path: Path) -> None:
    metadados = {"success": True, "result": {"resources": [
        _recurso_ckan("a", "PROGRAMACAO_DIARIA_2024_10_01.parquet", "PARQUET", 10, "2024-10-02T00:00:00"),
        _recurso_ckan("b", "PROGRAMACAO_DIARIA_2024_10_01.parquet", "PARQUET", 10, None),
        _recurso_ckan("c", "PROGRAMACAO_DIARIA_2024_10_02.parquet", "PARQUET", 10, "2024-10-03T00:00:00"),
    ]}}
    pedidos, baixar = _baixados()
    with patch("src.coleta.programacao.fetch_ckan_package_metadata", return_value=metadados), \
            patch("src.coleta.programacao.download_resource", side_effect=baixar):
        assert sincronizar_programacao(pd.Timestamp("2024-10-01"), pd.Timestamp("2024-10-02 23:00"), tmp_path) == []
    assert sorted(pedidos) == [("PROGRAMACAO_DIARIA_2024_10_01.parquet", "a"),
                               ("PROGRAMACAO_DIARIA_2024_10_02.parquet", "c")]
    manifesto = json.loads((tmp_path / "_manifesto_ons.json").read_text(encoding="utf-8"))
    assert manifesto["PROGRAMACAO_DIARIA_2024_10_01.parquet"]["recursos_duplicados_catalogo"] == 1


def test_p1_arquivo_temporario_leva_o_id_do_recurso(tmp_path: Path) -> None:
    vistos: List[str] = []

    class Resposta:
        def __init__(self) -> None:
            self.partes = [b"abc", b""]

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def read(self, _n: int) -> bytes:
            vistos.extend(p.name for p in tmp_path.iterdir())
            return self.partes.pop(0)

    recurso = RecursoONS(id_recurso="9f1c-77", nome_recurso="A_2024.csv", url_download="https://ons/x/A_2024.csv",
                         formato="CSV", tamanho_bytes=3, ultima_modificacao="2024-01-01T00:00:00")
    with patch("src.coleta.catalogo.urllib.request.urlopen", return_value=Resposta()):
        assert catalogo.download_resource(recurso, destination_dir=tmp_path, manifest={}) == "DOWNLOADED"
    assert "A_2024.csv.9f1c-77.part" in vistos
    assert (tmp_path / "A_2024.csv").read_bytes() == b"abc"
    assert not list(tmp_path.glob("*.part"))


# ---------------------------------------------------------------------------
# P2 — vírgula decimal
# ---------------------------------------------------------------------------


def _linha_horaria(valor: str, **outros: str) -> dict:
    linha = {"id_ons": "MSUHSD", "ceg": "UHE.PH.MS.028761-0.01", "id_estado": "MS",
             "din_instante": "2024-01-01 00:00:00", "val_a": valor}
    linha.update(outros)
    return linha


def test_p2_virgula_decimal_nos_conjuntos_horarios(tmp_path: Path) -> None:
    caminho = tmp_path / "D_2024_01.csv"
    pd.DataFrame([_linha_horaria("10,50"), _linha_horaria("7.25", din_instante="2024-01-01 01:00:00")]).to_csv(
        caminho, sep=";", index=False)
    dados, auditoria = extrair_arquivo(DESC, caminho)
    assert dados["val_a"].tolist() == [10.5, 7.25]
    assert auditoria["valores_invalidos"] == 0 and not dados["_nao_numerico"].any()


def test_p2_virgula_decimal_na_potencia_da_ficha() -> None:
    cadastro = pd.DataFrame([{"nom_usina": "SAO DOMINGOS", "ceg": "UHE.PH.MS.028761-0.01", "id_ons": "MSUHSD",
                              "id_estado": "MS", "val_potenciaautorizada": "48,5"}])
    ficha = extrair_ficha(cadastro, "2026-10-05 13:00:00", "MODALIDADE_USINA.csv", "UHE.PH.MS.028761-0.01", "MSUHSD",
                          "MS", "SAO DOMINGOS")
    assert ficha.loc[0, "val_potenciaautorizada"] == 48.5


# ---------------------------------------------------------------------------
# P3 — normalização única
# ---------------------------------------------------------------------------


def _evt(caminho: Path, reservatorio: str) -> Path:
    linha = {c: "1.0" for c in COLUNAS_EVT}
    linha.update(id_subsistema="S", nom_subsistema="SUL", nom_bacia="URUGUAI", nom_rio="RIO", nom_agente="AGENTE",
                 nom_reservatorio=reservatorio, cod_usina="153", din_instante="2024-01-01 00:00:00")
    pd.DataFrame([linha], columns=COLUNAS_EVT).to_csv(caminho, sep=";", index=False, encoding="utf-8")
    return caminho


def test_p3_evt_nome_com_acento_no_arquivo(tmp_path: Path) -> None:
    caminho = _evt(tmp_path / "ENERGIA_VERTIDA_TURBINAVEL_2024_01.csv", "ITAÚBA")
    registros, auditoria = filter_csv_file(caminho, 153, "ITAUBA")
    assert len(registros) == 1 and auditoria.registros_codigo_sem_nome == 0


def test_p3_evt_nome_com_acento_no_perfil(tmp_path: Path) -> None:
    caminho = _evt(tmp_path / "ENERGIA_VERTIDA_TURBINAVEL_2024_01.csv", " itauba ")
    registros, _ = filter_csv_file(caminho, 153, "Itaúba")
    assert len(registros) == 1


def _programacao(caminho: Path, codigo: str, estado: str, nome: str = "SÃO DOMINGOS") -> Path:
    linhas = [{"din_programacaodia": "2024-10-01", "num_patamar": p, "cod_exibicaousina": codigo, "nom_usina": nome,
               "id_estado": estado, "val_geracaoprogramada": "22.00"} for p in range(1, 49)]
    linhas += [{"din_programacaodia": "2024-10-01", "num_patamar": 1, "cod_exibicaousina": "OUTRA",
                "nom_usina": "OUTRA USINA", "id_estado": "SP", "val_geracaoprogramada": "100.00"}]
    pd.DataFrame(linhas).to_parquet(caminho, index=False)
    return caminho


def test_p3_programacao_codigo_e_estado_com_caixa_e_acento(tmp_path: Path) -> None:
    caminho = _programacao(tmp_path / "PROGRAMACAO_DIARIA_2024_10_01.parquet", " prúhsd ", "ms ")
    linhas, auditoria = ler_arquivo(caminho, "PRUHSD", "SAO DOMINGOS", "MS")
    assert auditoria["status"] == "PROCESSADO" and auditoria["patamares"] == 48 and len(linhas) == 48
    assert auditoria["linhas_codigo_sem_conferencia"] == 0 and auditoria["linhas_so_conferencia"] == 0


def _perfil_geracao(id_ons: str, ceg: str) -> SimpleNamespace:
    ident = SimpleNamespace(id_ons=id_ons, ceg=ceg, cod_usina=153, nome_ons="SAO DOMINGOS", id_reservatorio="PRUHSD")
    return SimpleNamespace(identificacao=ident, usina=SimpleNamespace(estado="MS"))


def test_p3_filtro_do_parquet_com_o_valor_normalizado(tmp_path: Path) -> None:
    desc = descricoes(_perfil_geracao("msuhsd", "uhe.ph.ms.028761-0.01"))["geracao"]
    caminho = tmp_path / "GERACAO_USINA-2_2024_01.parquet"
    pd.DataFrame([
        {"id_ons": "MSUHSD", "ceg": "UHE.PH.MS.028761-0.01", "id_estado": "MS", "din_instante": "2024-01-01 00:00:00",
         "val_geracao": 30.0},
        {"id_ons": "GOUSD", "ceg": "UHE.PH.GO.027665-0.01", "id_estado": "GO", "din_instante": "2024-01-01 00:00:00",
         "val_geracao": 5.0},
    ]).to_parquet(caminho, index=False)
    dados, auditoria = extrair_arquivo(desc, caminho)
    assert auditoria["linhas_usina"] == 1 and dados["val_geracao"].tolist() == [30.0]


# ---------------------------------------------------------------------------
# P4 — coluna de conferência ausente
# ---------------------------------------------------------------------------


def test_p4_coluna_de_conferencia_ausente_e_falha(tmp_path: Path) -> None:
    caminho = tmp_path / "D_2024_01.csv"
    pd.DataFrame([_linha_horaria("1.0")]).drop(columns="id_estado").to_csv(caminho, sep=";", index=False)
    dados, auditoria = extrair_arquivo(DESC, caminho)
    assert dados.empty and auditoria["status"] == "FALHA"
    assert auditoria["mensagem"] == "coluna de conferência ausente: id_estado"


def test_p4_coluna_de_conferencia_ausente_no_parquet(tmp_path: Path) -> None:
    caminho = tmp_path / "D_2024_01.parquet"
    pd.DataFrame([_linha_horaria("1.0")]).drop(columns="ceg").to_parquet(caminho, index=False)
    _, auditoria = extrair_arquivo(DESC, caminho)
    assert auditoria["status"] == "FALHA" and auditoria["mensagem"] == "coluna de conferência ausente: ceg"


# ---------------------------------------------------------------------------
# P5 — CSV vazio da EVT
# ---------------------------------------------------------------------------


def test_p5_csv_vazio_da_evt_com_o_motivo(tmp_path: Path) -> None:
    caminho = tmp_path / "ENERGIA_VERTIDA_TURBINAVEL_2024_01.csv"
    caminho.write_bytes(b"")
    registros, auditoria = filter_csv_file(caminho, 153, "SAO DOMINGOS")
    assert registros == [] and auditoria.status_processamento == "FALHA"
    assert auditoria.mensagem == "arquivo vazio"
